# Stage 2: Continual Refining（论文 §3.4）

## 目标

已获得可行 kernel 后，**迭代降低 latency**。维护 start-point 集合 $P(x)$，每步 ε-greedy 选 $p_t$，基于它改写。

## 奖励（Eq. 5）

$$r_{2,t} = \begin{cases} -1, & g_{\text{feas}}(o_t) = 0 \\ \tanh(\log b_t - \log \ell_{\text{lat}}(o_t)), & \text{otherwise} \end{cases}$$

设计要点：
- **不可行直接 -1**：避免 "回归可行性" 的优化被奖励
- **tanh 天然有界**：$r \in (-1, 1)$，与 Stage 1 奖励一致量纲
- **log-ratio**：对 latency 的 relative improvement 对称（2× 快奖励 = 2× 慢惩罚）

## PopArt 归一化

原始 reward $r_{2,t}$ 经 PopArt 归一：

$$\hat{r}_{2,t} = \frac{r_{2,t} - \mu_2}{\sigma_2}$$

在线更新（EMA，momentum $m = 0.99$）：

$$\mu_{\text{new}} = m\mu + (1-m)r, \quad \sigma^2_{\text{new}} = m\sigma^2 + (1-m)(r-\mu_{\text{new}})^2$$

$\sigma = \max(\sqrt{\sigma^2}, \epsilon)$，$\epsilon = 10^{-8}$ 防除零。

## 伪代码（完整）

```python
def stage2_refining(x, P_x, M, b0, T2, N, K, epsilon_schedule, alpha,
                    popart_stats):
    """
    Args:
      x: 静态任务
      P_x: 初始 start-point 集 (至少含 Stage 1 的 feasible kernel)
      M: Memory Bank (mutable)
      b0: 初始 best latency
      T2: Stage 2 预算
      popart_stats: {mu, sigma, n, momentum}

    Returns:
      (b_final, P_x_final, trajectory)
    """
    b = b0
    for t in range(T2):
        eps = epsilon_schedule(t)

        # 选 start point
        p_t = EpsilonGreedy(P_x, by=Q2, N=1, eps=eps)[0]

        # 检索 refinement context（排除 p_t）
        C = DenseTopK(x, M, K, exclude={p_t.id})
        c_t = EpsilonGreedy(C, by=Q2, N=N, eps=eps)

        # G_θ: 基于 p_t + c_t 改写
        y_t = G_theta(x, start_point=p_t, context=c_t, mode="optimize")

        # V: 验证
        o_t = V(x, y_t)

        # 计算 raw reward
        if not g_feas(o_t):
            r_raw = -1.0
        else:
            r_raw = tanh(log(b) - log(o_t.latency_us))
            if o_t.latency_us < b:
                b = o_t.latency_us
            add_to_P_x(x, y_t)                    # 扩展 start 集

        # PopArt 归一化
        popart_stats = update_popart(popart_stats, r_raw)
        r_norm = (r_raw - popart_stats.mu) / popart_stats.sigma

        # 更新 M + Q_2
        append_to_M(M, entry={
            "type": "trace" if g_feas(o_t) else "failed_trace",
            "kernel_path": y_t.attempt_dir,
            "parent_trace_id": p_t.id,
            "stage_when_added": 2,
            "meta": {...}
        })
        affected = [p_t.id] + [m.id for m in c_t]
        for mid in affected:
            Q2[mid] = clip(Q2[mid] + alpha * (r_norm - Q2[mid]), [-1, 1])

        trajectory.append({"t": t, "stage": 2, "p": p_t.id, "r_raw": r_raw,
                          "r_norm": r_norm, "latency_us": o_t.latency_us,
                          "g_feas": g_feas(o_t)})

    return (b, P_x, trajectory)
```

## Start-point 选择策略

$$p_t = \begin{cases} \text{Uniform}(P(x)), & \text{w.p. } \varepsilon_t \\ \arg\max_{p \in P(x)} Q_2(s, p), & \text{otherwise} \end{cases}$$

**为什么要 ε-greedy？** 因为当前 best (argmax $Q_2$) 可能陷入局部最优——新探索的 start point 即便目前 Q 低，也可能带来大幅突破（top 20% 算子出现 200× 加速，论文 §4.3）。

**$|P(x)|$ 增长**：每步若 $g_{\text{feas}}=1$ 则 $|P(x)| \mathrel{{+}{=}} 1$。论文观察：每个算子平均 3–8 个 feasible 变体入池。

## Refinement Context 检索

与 Stage 1 检索类似，但：
- 排除当前 $p_t$（避免给 Developer 看到自己的 baseline 作为 context）
- 优先级加权：trace / best_practice / experience > api_template（后者在 Refining 作用小）
- ε-greedy 按 $Q_2$（不是 $Q_1$）

**Profiler-derived bottleneck**（论文 §3.4 末段，可选增强）：
- 若 $p_t$ 的 meta 里有 `bottleneck_diagnosis`（e.g., "ub_bound" / "bw_bound"），优先检索 meta.tags 里含对应标签的条目
- bottleneck 诊断来源：可调 `msprof` 或 ops-profiling skill（EVO v1 暂不自动化；可由 Developer 在 DESIGN.md 里人工注记）

## Developer 派发 Prompt 模板（mode=optimize）

```
你是 Developer Agent，读 evo/agents/developer/AGENT.md 作为基础角色。

【本次任务：EVO Stage 2 Refining】
- 目标：基于 start point 降低 latency
- Start point: {p_t.kernel_path}  （当前 b_t={p_t.latency_us}us）
- 工作目录: {attempt_dir}
- Mode: optimize

【Start-point 诊断（若有）】
{p_t.meta.bottleneck_diagnosis}

【EVO 检索到的 refinement context（共 {N} 条）】
来自 Memory Bank，按 Q_2（latency 优化期望贡献）排序：

1. [id=mem-xxx | type=trace | operator=relu_custom | latency=32us]
   <content>

2. [id=mem-yyy | type=best_practice | tags=[double_buffer, tile_pow2]]
   <content>

...

【约束】
- 以 start point 为 baseline 改写（cp -r {p_t.kernel_path}/GeluCustom {attempt_dir}/）
- 仅允许一个聚焦方向（AVO 共识：增量进化）
- 保持正确性：若性能提升但 correctness 退化，不接受

【输出】
- {attempt_dir}/{OpCapitalName}/ 完整工程
- {attempt_dir}/docs/DESIGN.md 必须写明：
  * Baseline: <p_t.id> (<latency>us)
  * 本次优化假设
  * Context 中引用的 item ids 及其贡献
- YAML trailer
```

## 性能预期

论文 §4.3：对有 ≥1 个可行优化 beyond initial 的算子（159 个），中位 speedup 3.60×，IQR [1.38×, 10.05×]，top 20% 算子 >200×。

## 终止条件

Stage 2 **总是** 跑完剩余预算——不像 Stage 1 有 early exit。理由：只要还可探索，就可能突破。

## Stage 2 的不变量

1. $b_t$ **单调非增**：每步若 $o_t.\text{latency\_us} < b_t$ 则更新；否则保持
2. $|P(x)|$ **单调非减**：失败不踢出，可行即加入
3. Memory Bank 大小每步 +1（每步都有 new trace，不论可行与否）
4. PopArt stats.n 每步 +1
