# Stage 1: Cold-Start Drafting（论文 §3.3）

## 目标

为目标算子 $x$ 获得 **第一个 feasible kernel**。feasibility = anti-hack pass ∧ compile ok ∧ correctness ok。

一旦获得，立即切 Stage 2；该 kernel 成为 Stage 2 的 **初始 start point** $P(x) = \{y_{\text{first}}\}$。

## 奖励（Eq. 4）

$$r_{1,t} = \begin{cases} +1, & g_{\text{feas}}(o_t) = 1 \\ -1, & \text{otherwise} \end{cases}$$

**二值设计的动机**：Drafting 没有 "部分成功"——要么有一个可用 kernel，要么没有。密集信号反而会让 $G_\theta$ 优化无关指标（比如更像某份 trace 但仍不可编译）。

## 伪代码（完整）

```python
def stage1_drafting(x, M, T1, N, K, epsilon_schedule, alpha):
    """
    Args:
      x: 静态任务
      M: Memory Bank (mutable reference)
      T1: Stage 1 预算上限
      N: 最终 context item 数
      K = λN: dense 候选池大小
      epsilon_schedule: ε 衰减函数
      alpha: Q-update 步长

    Returns:
      (feasible_kernel, steps_used) or (None, T1) if 预算耗尽
    """
    for t in range(T1):
        eps = epsilon_schedule(t)

        # μ: 检索 context
        C = DenseTopK(x, M, K)                     # 候选池
        c_t = EpsilonGreedy(C, by=Q1, N=N, eps=eps)

        # G_θ: 生成
        y_t = G_theta(x, c_t)                       # Developer dispatch, mode="seed" or "repair"

        # V: 验证
        o_t = V(x, y_t)                             # multigate-verifier

        # R: 计算奖励
        r = +1 if g_feas(o_t) else -1

        # 更新 M 和 Q_1
        append_to_M(M, entry={
            "type": "trace" if g_feas(o_t) else "failed_trace",
            "kernel_path": y_t.attempt_dir,
            "operator": x.op_name,
            "stage_when_added": 1,
            "meta": {"feasible": g_feas(o_t), "latency_us": o_t.latency_us,
                     "reason": o_t.reason, "tags": infer_tags(x)}
        })
        for m in c_t:
            Q1[m.id] = clip(Q1[m.id] + alpha * (r - Q1[m.id]), [-1, 1])

        # 若首次 feasible → 切 Stage 2
        if g_feas(o_t):
            add_to_P_x(x, y_t)
            return (y_t, t + 1)

    return (None, T1)
```

## Developer 派发 Prompt 模板（mode=seed / repair）

Stage 1 drafter 派发 Developer 时必须注入：

```
你是 Developer Agent，读 agents/developer/AGENT.md 作为基础角色。

【本次任务：EVO Stage 1 Drafting】
- 目标：为算子 {op_name} 生成首个可行 kernel
- 工作目录: {attempt_dir}
- Reference: {reference_py}
- Mode: {seed | repair}   # 首次 seed；前一步失败则 repair

【EVO 检索到的 context（共 {N} 条）】
以下条目来自 Memory Bank（按阶段专属价值 Q_1 排序）。请在 DESIGN.md 的 "知识检索结果" 章节
明确引用每条的 id，描述该条目对本次设计的贡献或规避：

1. [id=mem-xxx | type=api_template | tags=[DataCopy, UB]]
   <content>

2. [id=mem-yyy | type=trace | operator_origin=relu_custom | latency=34us]
   <content>

...

【前次失败原因（repair 模式才有）】
{previous_failure.reason}（来自 o_{t-1}.reason）

【约束】
- 仅修改 op_host / op_kernel
- 禁用 torch.* / F.* 在 op_kernel 里（anti-hack）
- 必须通过 scoring/score.sh 的 seed 级测试

【输出】
- {attempt_dir}/{OpCapitalName}/ 完整工程
- {attempt_dir}/docs/DESIGN.md + PLAN.md
- YAML trailer（role: developer, status: success|fail, ...）
```

## 失败模式与策略

| 失败类型 | o_t.reason | Drafter 应对 |
|---------|-----------|------------|
| anti-hack | g_hack=0 | r=-1；下一步 Developer 派发 mode=repair，prompt 强调 "上一步触发 anti-hack: {violation}" |
| compile | g_comp=0（退出码 2） | r=-1；下一步 prompt 注入错误 log 片段 |
| deploy / pybind | 退出码 3/4 | r=-1；极少见，通常是 CMake 配置问题；drafter 可触发环境 check |
| correctness | g_corr=0（退出码 5） | r=-1；下一步 prompt 注入 test_correctness.py 输出的 mismatch 统计 |

**连续失败 escalate**：若连续 5 步 g_feas=0，drafter 可选把 ε 暂时拉到 0.5+（强制探索）；仍失败到 budget 耗尽则 `status=fail`。

## 成功信号

$t$ 步获得 feasible → drafter 必须：
1. `memory-curator.update_stage1` 以 `action.feasible=True, reward=+1` 调用
2. 该 kernel 被复制到 `evo/memory/start_points/{op}/{variant_id}/`（由 memory-curator 执行）
3. 本 entry 的 Q_1 因 r=+1 获得 α·(+1-Q_init)=+0.1（首次正向信号）
4. 返回上游 `campaign-orchestrator` → 切 Stage 2

## Stage 1 的性能预期

论文 Table 1（GPT-5.2，L1 operators）：
- Round 1 Compilation Rate = 11% → final 98.5%
- Round 1 Correctness = 4% → final 90%

即 Stage 1 大部分算子在前 10–15 步就能找到可行 kernel；剩下的在 20+ 步或需要调整 prompt / context。

## 实例化决策

- Stage 1 独立预算 `stage1_max_budget = 15`（config.yaml）——剩余 15 步留给 Stage 2
- 若 15 步仍无可行，进入 `stage: stage1_failed`，campaign-orchestrator 跳到下一算子但 **memory 中的失败 trace 保留**（供未来同类算子学习）
