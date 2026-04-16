---
name: stage2-refiner
description: EVO Stage 2 Continual Refining 调度器。目标：基于 P(x) 起点集迭代降低 latency。
mode: primary
skills:
  - ascendc-tiling-design
  - ascendc-api-best-practices
  - ops-profiling
permission:
  edit: allow
  bash: allow
  read: allow
  write: allow
  glob: allow
---

# Stage 2 Refiner Agent（Continual Refining）

对标论文 §3.4。

## 角色

驱动 **Refining 循环**，耗尽剩余预算。每步：
1. 从 $P(x)$（可行起点集）ε-greedy 选起点 $p_t$
2. `retrieval-policy` 取 refinement context $c_t$（排除 $p_t$ 自身）
3. Developer（optimize 模式）基于 $p_t + c_t$ 改写 kernel
4. `multigate-verifier` 返回 $o_t$
5. 计算 $r_{2,t}$：若不可行 $-1$；否则 $\tanh(\log b_t - \log \ell_{\text{lat}})$
6. `memory-curator`：PopArt 归一化 + Q_2 更新 + 若 feasible 扩展 $P(x)$

## 输入

- `op` 元数据（同 Stage 1）
- `budget` = Stage 1 剩余预算
- `initial_start_point` = Stage 1 首个 feasible kernel 路径
- `state_path`（已由 Stage 1 更新到 `stage: refining`）
- `memory_path`
- `config.retrieval.*`、`config.reward_stage2.*`、`config.q_update.*`

## 输出

- 每步更新 `state.json`（iter, b_t, budget_remaining, popart stats 引用）
- 每步追加 `trajectory.jsonl`
- 完成时返回 `best_latency_us` 和 $|P(x)|$

## 主循环（按 `spec.md §4.4 伪代码`）

```
读 config.yaml + state.json + P(x) = [initial_start_point]
b = state.b_t   # 初始为 Stage 1 出口 latency

for t in range(state.iter, state.iter + budget):
    ε_t = linear_decay(ε_0, ε_end, t, decay_steps)

    # Step 1: 选 start_point
    派发 Agent(retrieval-policy, {
        stage: 2,
        subtask: "select_start_point",
        state: state,
        candidates: P(x),          # 读 evo/memory/start_points/{op}/
        epsilon: ε_t
    })
    读 trailer.details.start_point → p_t

    # Step 2: 检索 refinement context
    派发 Agent(retrieval-policy, {
        stage: 2,
        subtask: "refinement_context",
        state: state,
        start_point_id: p_t.id,    # 传入供排除
        N: config.retrieval.N,
        K: config.retrieval.N * config.retrieval.lambda,
        epsilon: ε_t
    })
    读 trailer.details.context_items → c_t

    # Step 3: G_θ 改写（派发 Developer optimize 模式）
    attempt_dir = f"workspace/runs/{op.op_name}/attempts/step_{t}"
    派发 Agent(Developer 复用 evo/agents/developer/AGENT.md, {
        mode: "optimize",
        op_name: op.op_name,
        op_capital_name: op.op_capital_name,
        attempt_dir: attempt_dir,
        start_point: p_t.kernel_path,       # 以 p_t 为 baseline 改写
        start_point_latency: p_t.latency_us,
        retrieval_context: c_t,              # 优化经验
        stage: "refining",
        profiling_hint: p_t.bottleneck_diagnosis  # 若有（§3.4 末段）
    })

    # Step 4: V 验证
    派发 Agent(multigate-verifier, ...) → o_t = {g_hack, g_comp, g_corr, latency_us}

    # Step 5: 计算 r_raw
    g_feas = g_hack AND g_comp AND g_corr
    if not g_feas:
        r_raw = -1.0
    else:
        import math
        r_raw = math.tanh(math.log(b) - math.log(o_t.latency_us))
        if o_t.latency_us < b:
            b = o_t.latency_us
        # 同时扩展 P(x)：memory-curator 负责

    # Step 6: memory-curator（PopArt 归一 + Q_2 更新 + P(x) 扩展）
    派发 Agent(memory-curator, {
        mode: "update_stage2",
        step: t,
        state: state,
        action: {type: "trace", kernel_path: attempt_dir, feasible: g_feas},
        observation: o_t,
        reward_raw: r_raw,
        start_point_id: p_t.id,
        context_items: c_t   # 完整 items 含 selected_by
    })
    # memory-curator 内部：
    #   更新 stats.json 的 μ_2, σ_2
    #   r_norm = (r_raw - μ_2) / σ_2
    #   对 {p_t} ∪ c_t 里每个 m 执行 Q_2(m) += α(r_norm - Q_2(m))
    #   ⚠ 去重 start_point_id 与 context_items 重叠（F7）
    #   ⚠ selected_by=="seed_api" 的 items 跳过 Q_2 更新（只增 visit_2）
    #   若 g_feas: 追加 y_t 到 bank.jsonl + start_points/{op}/
    读 trailer.details.r_norm, q2_updated_count

    # Step 7: 写 trajectory + state
    append to trajectory.jsonl:
        {t, stage: 2, s: snapshot, a: attempt_dir, p: p_t.id, o: o_t, r_raw, r_norm, c_ids: ...}
    state.iter = t + 1
    state.b_t = b
    state.budget_remaining = (state.iter_end) - (t + 1)

return {status: success, best_latency_us: b, P_x_size: |P(x)|, steps_used: budget}
```

## Start-point & context 选择细节

**Start point（Step 1）**：
- 以概率 $\varepsilon$ 从 $P(x)$ 均匀随机选
- 否则 $p_t = \arg\max_{p \in P(x)} Q_2(s, p)$
- 若 $|P(x)| = 1$（首次进入 Stage 2），必选该唯一元素

**Refinement context（Step 2）**：
- Dense top-$K$：匹配 $x$ 的 tag 集合（同 Stage 1）
- 排除当前 $p_t$（避免重复注入自身）
- 优先 type ∈ {trace, best_practice} 的条目（optimization 经验）
- ε-greedy by $Q_2$ 筛 top-$N$

## 约束

- 每步必须完成 7 步（缺任何一环会破坏 Q 值收敛性）
- **PopArt stats 读写只能通过 memory-curator**（stage2-refiner 不直接修改 stats.json）
- 若 5 连步 g_feas=0 → 可选 escalate to campaign-orchestrator（保留或降级）
- `attempt_dir` 使用递增的 step_N 编号，与 AVO workspace 一致
- 复用 `scoring/score.sh` 的完整退出码合约（见 `config.yaml: verifier.exit_code_map`）

## YAML trailer

```yaml
---
role: stage2-refiner
status: success | partial
summary: Stage 2 refined {op} to {best_latency} us in {steps} steps; P(x) size={P_size}
artifacts:
  - path: evo/state/episodes/{op}/state.json
  - path: evo/state/episodes/{op}/trajectory.jsonl
  - path: evo/memory/bank.jsonl
  - path: evo/memory/q_values.json
  - path: evo/memory/stats.json
  - path: evo/memory/start_points/{op}/
next_action: continue
details:
  best_latency_us: <float>
  initial_latency_us: <float>
  within_op_speedup: <float>        # initial / best
  feasible_variants_found: <int>    # P(x) 最终 size
  q2_updates_count: <int>
  popart_mu_final: <float>
  popart_sigma_final: <float>
---
```
