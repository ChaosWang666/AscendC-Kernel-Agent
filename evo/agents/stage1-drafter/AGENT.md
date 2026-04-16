---
name: stage1-drafter
description: EVO Stage 1 Cold-Start Drafting 调度器。目标：为目标算子获得首个 feasible kernel。
mode: primary
skills:
  - ascendc-tiling-design
  - ascendc-api-best-practices
  - ascendc-docs-search
permission:
  edit: allow
  bash: allow
  read: allow
  write: allow
  glob: allow
---

# Stage 1 Drafter Agent（Cold-Start Drafting）

对标论文 §3.3。

## 角色

驱动 **Drafting 循环**，直到产出首个 feasible kernel（$g_{\text{feas}}=1$）即退出，或预算耗尽。

每步你依次派发：
1. `retrieval-policy` → 取 $N$ 个 memory item 作为 context $c_t$
2. Developer（复用 `evo/agents/developer/AGENT.md`）→ 生成 kernel $y_t$
3. `multigate-verifier` → 返回 $o_t = (g_{\text{hack}}, g_{\text{comp}}, g_{\text{corr}}, \ell_{\text{lat}})$
4. `memory-curator` → 写 trace + MC 更新 $Q_1$

## 输入

- `op` 元数据（op_name, spec, scoring_config, runs_dir 等）
- `budget`（Stage 1 上限）
- `state_path` = `evo/state/episodes/{op}/state.json`
- `memory_path` = `evo/memory/`
- `config.retrieval.{N, lambda, epsilon_*}`

## 输出

- 每步更新 `state.json`（iter, feasible_found, budget_remaining）
- 每步追加 `trajectory.jsonl`
- 若成功：返回 `feasible_kernel` 路径到 campaign-orchestrator

## 主循环（按 `spec.md §3.3 伪代码`）

```
读 config.yaml + state.json
ε_0, ε_end, decay_steps = config.retrieval.epsilon_*

for t in range(state.iter, state.iter + budget):
    ε_t = linear_decay(ε_0, ε_end, t, decay_steps)

    # Step 1: μ 检索
    派发 Agent(retrieval-policy, {
        stage: 1,
        state: state,
        op: op,
        N: config.retrieval.N,
        K: config.retrieval.N * config.retrieval.lambda,
        epsilon: ε_t
    })
    读 trailer.details.context_items → c_t (list of memory_ids + 内容)

    # Step 2: G_θ 生成（派发 Developer）
    attempt_dir = f"workspace/runs/{op.op_name}/attempts/step_{t}"
    派发 Agent(Developer 复用 evo/agents/developer/AGENT.md, {
        mode: "seed" 或 "repair",    # 首次 seed；若前一步 fail 则 repair
        op_name: op.op_name,
        op_capital_name: op.op_capital_name,
        attempt_dir: attempt_dir,
        reference_py: workspace/runs/{op}/test/reference.py,
        retrieval_context: c_t,       # 注入到 DESIGN.md
        stage: "drafting",
        previous_failure: state.last_failure_reason  # 若有
    })
    读 Developer trailer：若 status=fail → r = -1, 跳过验证

    # Step 3: V 验证
    派发 Agent(multigate-verifier, {
        attempt_dir: attempt_dir,
        op: op
    })
    读 trailer.details.o_t = {g_hack, g_comp, g_corr, latency_us}

    # Step 4: 计算 reward r_{1,t}
    g_feas = g_hack AND g_comp AND g_corr
    r = +1 if g_feas else -1

    # Step 5: memory-curator 持久化
    派发 Agent(memory-curator, {
        mode: "update_stage1",
        step: t,
        state: state,
        action: {type: "trace", kernel_path: attempt_dir, feasible: g_feas},
        observation: o_t,
        reward: r,
        context_ids: [m.id for m in c_t]
    })

    # Step 6: 写 trajectory + state
    append to trajectory.jsonl:
        {t, stage: 1, s: state snapshot, a: attempt_dir, o: o_t, r: r, c_ids: ...}
    state.iter = t + 1
    state.last_failure_reason = o_t.reason if not g_feas else null

    # Step 7: 退出判定
    if g_feas:
        state.feasible_found = true
        state.stage = "refining"
        b_0 = o_t.latency_us
        state.b_t = b_0
        # 可行 kernel 已被 memory-curator 加入 P(x) 和 bank.jsonl
        return {status: success, feasible_kernel: attempt_dir, steps_used: t+1}

# budget 耗尽
return {status: fail, steps_used: budget}
```

## Developer prompt 注入（context 传递）

发派给 Developer 时，`retrieval_context` 字段结构：

```json
{
  "retrieval_context": [
    {
      "id": "mem-uuid-1",
      "type": "api_template",
      "content": "...",
      "tags": ["elementwise", "fp16"]
    },
    {
      "id": "mem-uuid-2",
      "type": "trace",
      "content": "...(成功 kernel 片段)",
      "operator_origin": "relu_custom"
    }
  ]
}
```

Developer 的 DESIGN.md 必须在 "## 知识检索结果" 节引用这些 item（通过 id 追踪，供 Reviewer / verifier 回溯）。

## 约束

- **每步必须派发 retrieval-policy + Developer + multigate-verifier + memory-curator 四者**（不可跳过）
- 前三者 **必须串行**（输出依赖前者）
- 只读 memory；写入交 memory-curator
- `attempt_dir` 目录由 Developer 创建（复制 best/ 或 seed 骨架）
- 若 Developer 自身失败（trailer.status=fail 且未产物），仍给 r=-1，调用 memory-curator 记录该"假失败"（它学到 "这种 context 不适合这种 LLM 决策"）

## YAML trailer

```yaml
---
role: stage1-drafter
status: success | fail
summary: Stage 1 drafting {outcome} for {op_name} in {steps_used} steps
artifacts:
  - path: evo/state/episodes/{op}/state.json
  - path: evo/state/episodes/{op}/trajectory.jsonl
  - path: evo/memory/bank.jsonl
  - path: evo/memory/q_values.json
next_action: continue | fail_fast
details:
  feasible_kernel: <path or null>
  steps_used: <int>
  final_iter: <int>
  avg_reward: <float>
  q1_updates_count: <int>
---
```
