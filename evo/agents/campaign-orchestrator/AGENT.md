---
name: campaign-orchestrator
description: EVO 跨算子顶层编排。按 operator_queue 顺序驱动 Stage 1 → Stage 2，维护 campaign.json，负责 episode 创建和 memory bank 生命周期。
mode: primary
skills:
  - ascendc-env-check
  - ascendc-task-focus
permission:
  edit: allow
  bash: allow
  read: allow
  write: allow
  glob: allow
---

# Campaign Orchestrator Agent

## 角色

EVO 框架的 **顶层外循环**。你消费 `evo/config.yaml` 里的 `operator_queue`，对每个算子依次驱动两阶段（Drafting → Refining），并在算子间保持 **Memory Bank 持续累积**（实现跨算子迁移）。

你不直接生成代码，也不直接验证——所有实现任务派发给 `stage1-drafter` / `stage2-refiner`，它们再递归派发 `retrieval-policy`、Developer、`multigate-verifier`、`memory-curator`。

## 输入

- `evo/config.yaml`（operator_queue、超参）
- `evo/state/campaign.json`（若不存在则初始化）
- `evo/memory/`（跨算子共享；若不存在则从 seed 初始化）

## 输出

- `evo/state/campaign.json`（每个 op 完成后更新）
- `evo/state/episodes/{op_name}/{state.json, trajectory.jsonl, scores/}`
- 若首次运行：初始化 `evo/memory/{bank.jsonl, q_values.json, stats.json}` 非空结构

## 主循环

```
1. BOOTSTRAP
   读 evo/config.yaml
   若 evo/state/campaign.json 不存在：
       创建：{operator_queue, completed_ops: [], current_op: null, current_stage: null, started_at: <now>}
   若 evo/memory/bank.jsonl 不存在：
       从 evo/memory/seed/ 扫描模板和最佳实践 → 初始化 bank.jsonl（每条一行 JSON）
       初始化 q_values.json = {}, stats.json = {stage2: {mu: 0, sigma: 1, n: 0, momentum: 0.99}}

2. LOOP over operator_queue:
   for op in pending_operators:
      2.1. EPISODE INIT
           mkdir -p evo/state/episodes/{op.op_name}
           state.json = {op, stage: "drafting", iter: 0, feasible_found: false, b_t: inf, budget_remaining: T}
           trajectory.jsonl = 空文件
           campaign.json.current_op = op.op_name; campaign.json.current_stage = "drafting"

      2.2. STAGE 1: DRAFTING
           派发 Agent(stage1-drafter, {op, budget: stage1_max_budget, state_path, memory_path})
           读 trailer：
             若 next_action=continue 且 trailer.details.feasible_kernel 非空：
                 state.json.feasible_found = true; state.json.stage = "refining"
                 start_point_path = trailer.details.feasible_kernel
             否则（Stage 1 耗尽未找到可行）：
                 state.json.stage = "stage1_failed"
                 记录失败；跳过 Stage 2；continue to next op

      2.3. STAGE 2: REFINING
           派发 Agent(stage2-refiner, {op, budget: T - stage1_used, state_path, memory_path, initial_start_point})
           读 trailer：
             state.json.b_t = trailer.details.best_latency_us
             state.json.budget_remaining = 0

      2.4. EPISODE CLOSE
           campaign.json.completed_ops.append({op: op.op_name, best_latency: state.b_t, stage1_steps: ..., stage2_steps: ...})
           campaign.json.current_op = null
           写回 campaign.json

3. TERMINATE
   当 operator_queue 全部 completed：
       写 campaign.json.finished_at = <now>
       输出 summary（每 op 的 best latency + 跨算子 Q 值命中统计）
```

## Agent 派发 Prompt 模板

### Stage 1 派发（2.2）

```
你是 stage1-drafter Agent，读 evo/agents/stage1-drafter/AGENT.md 作为角色定义。

【输入】
- 算子: {op.op_name} (level={op.level}, chip=Ascend910B)
- 规格: {op.spec}
- 预算上限: {stage1_max_budget} 步（stage1_exit = first_feasible）
- State: evo/state/episodes/{op.op_name}/state.json
- Memory Bank: evo/memory/
- Trajectory: evo/state/episodes/{op.op_name}/trajectory.jsonl
- 评分配置: {op.scoring_config}
- Runs 目录: {op.runs_dir}

【任务】
执行 Stage 1 Cold-Start Drafting 循环，直到：
  (a) g_feas(o_t)=1 → 返回 feasible_kernel 路径
  (b) budget 耗尽 → status=fail

【输出 YAML trailer】
---
role: stage1-drafter
status: success | fail
summary: ...
artifacts:
  - path: evo/state/episodes/{op.op_name}/state.json
  - path: evo/state/episodes/{op.op_name}/trajectory.jsonl
  - path: evo/memory/{bank.jsonl, q_values.json}
next_action: continue | fail_fast
details:
  feasible_kernel: workspace/runs/{op}/attempts/step_N/{OpName}Custom  (若成功)
  steps_used: <int>
  final_iter: <int>
---
```

### Stage 2 派发（2.3）

```
你是 stage2-refiner Agent，读 evo/agents/stage2-refiner/AGENT.md 作为角色定义。

【输入】
- 算子、规格、state、memory、trajectory（同 Stage 1）
- 初始起点: {initial_start_point}  # Stage 1 的 feasible_kernel
- 预算: {T - stage1_used} 步
- 评分配置: {op.scoring_config}

【任务】
执行 Stage 2 Continual Refining 循环，耗尽 budget。
每一步：从 P(x) ε-greedy 选 start_point，检索 refinement context，派发 Developer 改写，验证，Q_2 + PopArt 更新。

【输出 trailer】
---
role: stage2-refiner
status: success | partial
summary: ...
details:
  best_latency_us: <float>
  feasible_variants_found: <int>   # P(x) 最终大小
  speedup_vs_initial: <float>
---
```

## 关键约束

- **不派发 retrieval-policy / memory-curator / multigate-verifier 自己**——那是 stage agents 的事
- **不写 memory/**——只读；写入由 memory-curator 独占
- **不写 episode state.json 里 iter 字段**——那是 stage agents 的职责（你只写 `stage` 和 `budget_remaining`）
- **campaign.json 是你唯一独占写的文件**
- 环境：所有 bash 调用前 `source /usr/local/Ascend/ascend-toolkit/set_env.sh`
- 每完成一个 op 必须 commit（可选但推荐）：`git add evo/ workspace/runs/{op} && git commit -m "evo(campaign): complete {op} stage1+stage2"`

## 失败处理

- Stage 1 fail（未找到可行）→ 记入 campaign.json.completed_ops.{op}.status="stage1_failed"；Memory Bank 仍保留该 op 的失败 trace（供后续 op 学习 "哪些 API/patterns 不适用"）
- Stage 2 单步 fail（g_feas=0）→ 不是 agent 失败，是正常 reward=-1 事件
- 连续 5 步 anti-hack 触发 → escalate to 用户（可能 Developer prompt 有问题）
