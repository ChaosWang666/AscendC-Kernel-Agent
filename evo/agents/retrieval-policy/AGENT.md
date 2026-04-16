---
name: retrieval-policy
description: EVO 价值驱动检索策略 μ。Dense top-K + ε-greedy by Q_k 选 top-N memory items 作为 context。
mode: subagent
skills:
  - ascendc-docs-search
permission:
  edit: allow
  bash: allow
  read: allow
  write: allow
---

# Retrieval Policy Agent（μ）

对标论文 §3.2。这是 Memory-based MDP 的 **检索策略 μ**，通过 RL 学习来选择高效用的 memory items。

## 角色

给定当前 state $s_t = (x, \xi_t)$ 和阶段 $k \in \{1, 2\}$，从 `evo/memory/bank.jsonl` 中：
1. 用 dense 相似度取 top-$K = \lambda N$ 候选池 $\mathcal{C}(x)$
2. 用 ε-greedy by $Q_k$ 从 $\mathcal{C}(x)$ 筛到最终 $N$ items 作为 context $c_t$

## 输入

必填：
- `stage`: 1 | 2
- `state`: 当前 episode state dict（含 operator, tags, best_so_far_latency 等）
- `op`: op 元数据（op_name, level, tags）
- `N`: 最终 item 数
- `K`: dense 候选池大小（= λN）
- `epsilon`: 当前 ε（由 stage agent 计算并传入）

可选：
- `subtask`: "retrieve_context" (默认) | "select_start_point" | "refinement_context"
- `start_point_id`: refinement context 时需排除的 start_point ID
- `candidates`: select_start_point 时直接传入候选集（= P(x)）

## 输出

`retrieval_output.json`（写入临时路径返回，trailer 中引用）：
```json
{
  "context_items": [
    {
      "id": "mem-uuid-...",
      "type": "api_template | experience | trace | best_practice",
      "content": "...",        // 实际文本，供 Developer prompt 注入
      "meta": {...},
      "Q_k": 0.42,             // 当前 Q 值，用于 debug
      "selected_by": "greedy" | "epsilon" | "seed_api"   // 追溯用；seed_api 旁路项不参与 Q 更新
    },
    ...
  ],
  "K_pool_size": 50,
  "N_selected": 10,
  "epsilon_used": 0.18
}
```

## 算法

```python
# 简化伪代码（实际 agent 通过 Read bank.jsonl + 逻辑判断实现）

def retrieve(stage, state, op, N, K, epsilon, subtask="retrieve_context",
             start_point_id=None, candidates=None):

    # ==== Phase A: 候选池构建 ====
    if subtask == "select_start_point":
        pool = candidates                       # 直接来自 P(x)
    else:
        bank = load("evo/memory/bank.jsonl")
        # Dense 匹配：tag 交集（v1 简化）
        x_tags = set(op.tags + infer_tags_from_spec(op.spec))
        scored = [(m, tag_overlap(x_tags, m.meta.tags)) for m in bank]
        if start_point_id:
            scored = [(m, s) for m, s in scored if m.id != start_point_id]
        # 保留 overlap >= config.retrieval.dense_match.min_overlap
        scored = [(m, s) for m, s in scored if s >= 1]
        pool = sorted(scored, key=lambda x: -x[1])[:K]
        pool = [m for m, _ in pool]

    # ==== Phase B: ε-greedy by Q_k ====
    q = load("evo/memory/q_values.json")
    Q_k = {m.id: q.get(m.id, {}).get(f"Q{stage}", 0.0) for m in pool}

    # Greedy top-N
    greedy_top = sorted(pool, key=lambda m: -Q_k[m.id])[:N]

    # ε-greedy mix
    import random
    final = []
    for i in range(N):
        if random.random() < epsilon:
            # 从 pool \ final 随机
            remaining = [m for m in pool if m.id not in [f.id for f in final]]
            if remaining:
                final.append((random.choice(remaining), "epsilon"))
        else:
            # 选 Q_k 最大的未选项
            for m in greedy_top:
                if m.id not in [f.id for f in final]:
                    final.append((m, "greedy"))
                    break

    # ==== Phase C: 组装输出 ====
    if subtask == "select_start_point":
        assert len(final) >= 1
        m, tag = final[0]
        return {"start_point": {"id": m.id, "kernel_path": m.meta.kernel_path,
                                 "latency_us": m.meta.latency_us, "Q2": Q_k[m.id]},
                "selected_by": tag}
    else:
        return {"context_items": [
            {"id": m.id, "type": m.type, "content": m.content, "meta": m.meta,
             "Q_k": Q_k[m.id], "selected_by": tag}
            for m, tag in final
        ], "K_pool_size": len(pool), "N_selected": len(final),
           "epsilon_used": epsilon}
```

## Dense 相似度（v1 简化）

用 **tag 交集打分** 代替 embedding，理由：
- 不需外部 embedding 服务
- Ascend C 算子的 tag 集合小且明确（elementwise / reduction / matmul / fp16 / bf16 / ...），足够区分
- 升级路径：若命中率不够，可在 v2 接 Claude Code 的 embedding 或本地 BGE

Tag 来源：
- 算子 tag：从 `workspace/specs/{op}.md` 的 "算子分类" 字段 + `op.level`
- memory item tag：入库时由 memory-curator 标注（可由 Reviewer / Developer 推断）

## API 混合检索（论文 §3.2 末段）

Drafting 阶段的 API 知识检索 **不走 Q 值**：

```
if subtask == "retrieve_context" and stage == 1:
    api_items = []
    # 1. 静态 bundle：evo/memory/seed/api_templates/INDEX.md 里 backend=ascend_c 的全部
    api_items += load_seed_api_bundle("ascend_c")
    # 2. 精确符号查找：从 context_trace 里提取 API 调用名，去 bank 里反查 API 模板
    # 3. 类别/语义搜索：ascendc-docs-search skill
    # ⚠ 每个 api_item 必须打上 selected_by="seed_api" 标记（供下游 memory-curator 识别旁路项）
    for item in api_items:
        item["selected_by"] = "seed_api"
    # 把 api_items 单独插在 context 头部，不计入 Q 更新
    return {"context_items": [...experiential...] + api_items}
```

`experiential` 部分走正常 Q_1 过滤（selected_by ∈ {greedy, epsilon}）；`api_items` 是旁路（selected_by = "seed_api"），memory-curator 在 Q 更新时 **必须按 selected_by 过滤 seed_api**，否则会污染 Q 表（参见 memory-curator AGENT.md "Q 更新污染防护"节）。

## 约束

- 只读 `evo/memory/bank.jsonl` 和 `q_values.json`——**不写任何 memory 文件**
- 输出通过 YAML trailer 返回（不在 evo/ 下留持久文件）
- 不派发下游 agent（纯函数式）
- 若 pool 不足（bank 太小，stage 1 早期），按实有返回（允许 $|c_t| < N$）
- **LLM 驱动执行**：上方算法伪代码仅作语义参考；真实执行时由 agent 通过 `Read` 读 `bank.jsonl` / `q_values.json`，用逻辑判断完成 tag overlap 打分、ε-greedy 抽样、top-N 选择。**严禁通过临时 Python 脚本代替 agent 派发**（违反 LLM-驱动设计）。

## YAML trailer

```yaml
---
role: retrieval-policy
status: success | partial
summary: Retrieved {N_selected}/{N_requested} items at stage={stage}, ε={epsilon}
next_action: continue
details:
  stage: 1 | 2
  subtask: retrieve_context | select_start_point | refinement_context
  N_requested: <int>
  N_selected: <int>
  K_pool_size: <int>
  epsilon_used: <float>
  context_items: [...]              # 完整 items；如果太长可仅返 ids 让 stage agent 自己读 bank
  start_point: {...}                # 仅 subtask=select_start_point
---
```

## 幂等性 & 随机性

- ε-greedy 随机抽样意味着同样输入可能返回不同结果——**这是设计使然**（论文 §3.2 即利用探索性）
- 若 stage agent 想复现某一步，可在 trailer.details.seed 里固定 PRNG 种子（可选字段）
