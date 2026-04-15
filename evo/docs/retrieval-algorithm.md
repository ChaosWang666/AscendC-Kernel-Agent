# Value-Driven Retrieval（论文 §3.2）

## 总览

$\mu$ 是 **从 memory bank 选 context** 的可学策略。给定 $(x, \xi_t, \text{stage})$，它返回 $c_t \subset \mathcal{M}_t$ 喂给 $G_\theta$。

设计要点：
- **两阶段过滤**：dense top-$K$ 初筛 → ε-greedy by $Q_k$ 终选 top-$N$
- **Stage-specific**：$Q_1$ 管 Drafting；$Q_2$ 管 Refining
- **混合检索**（论文 §3.2 末段）：API 知识走静态 bundle + 精确查找，实验性记忆走 Q 值

## 算法（完整伪代码）

```python
def retrieval_policy(state, stage, N, K, epsilon, subtask="retrieve_context",
                     start_point_id=None, candidates=None):
    """
    Args:
      state: 当前 episode state, 含 op_name, tags, b_t, stage, iter
      stage: 1 (drafting) or 2 (refining)
      N: 最终 item 数
      K: dense 候选池大小
      epsilon: 探索率
      subtask: 选哪种检索:
        - "retrieve_context": 拿 N 个 context items（Stage 1/2 都用）
        - "select_start_point": 从 P(x) 选一个 start point（仅 Stage 2）
        - "refinement_context": 拿 N 个 refinement context，排除 start_point（仅 Stage 2）
      start_point_id: 若 subtask = refinement_context，排除此 id
      candidates: 若 subtask = select_start_point，直接用这个作为 pool
    """

    # ==== Phase A: 候选池 ====
    if subtask == "select_start_point":
        pool = candidates                              # = P(x) 展开
        # start point 的 dense 打分：读 meta.json 的 latency + 标签
    else:
        bank = load_jsonl("evo/memory/bank.jsonl")
        x_tags = infer_tags(state.op_name, state.spec_path)
        scored = []
        for m in bank:
            # 排除当前 start_point 自身
            if start_point_id and m.id == start_point_id:
                continue
            # Refinement 阶段优先 trace / best_practice（可调权重）
            type_weight = 1.0
            if stage == 2:
                if m.type in ["trace", "best_practice", "experience"]:
                    type_weight = 1.5
                elif m.type == "api_template":
                    type_weight = 0.3      # API 模板在 Refining 中不那么重要
            overlap = len(x_tags & set(m.meta.tags))
            score = overlap * type_weight
            if score >= config.retrieval.dense_match.min_overlap:
                scored.append((m, score))
        pool = [m for m, _ in sorted(scored, key=lambda p: -p[1])[:K]]

    # ==== Phase B: ε-greedy by Q_k ====
    q = load_json("evo/memory/q_values.json")
    q_field = f"Q{stage}"
    Q = {m.id: q.get(m.id, {}).get(q_field, config.q_update.q_init) for m in pool}

    if subtask == "select_start_point":
        import random
        if random.random() < epsilon:
            chosen = random.choice(pool)
            return {"start_point": entry(chosen, "epsilon"), "pool_size": len(pool)}
        chosen = max(pool, key=lambda m: Q[m.id])
        return {"start_point": entry(chosen, "greedy"), "pool_size": len(pool)}

    # subtask ∈ {retrieve_context, refinement_context}
    greedy_order = sorted(pool, key=lambda m: -Q[m.id])
    chosen = []
    used = set()
    for _ in range(N):
        if random.random() < epsilon and len(used) < len(pool):
            rem = [m for m in pool if m.id not in used]
            pick = random.choice(rem)
            chosen.append((pick, "epsilon"))
        else:
            for m in greedy_order:
                if m.id not in used:
                    chosen.append((m, "greedy"))
                    break
        used.add(chosen[-1][0].id)
        if len(chosen) == len(pool):
            break   # pool 小于 N，提前结束

    # ==== Phase C: API 混合检索（Stage 1 retrieve_context 专属） ====
    if stage == 1 and subtask == "retrieve_context":
        # 静态 API bundle（backend-aware）
        api_items = load_api_bundle(backend=config.backend)
        # 精确符号查找：从 chosen 里的 trace 提 API 名，去 bank 找对应 api_template
        api_items += exact_symbol_lookup(chosen, bank)
        # dedupe + 附在 context 头
        chosen = [(a, "api_bundle") for a in api_items] + chosen

    return {"context_items": [{"id": m.id, "type": m.type, "content": m.content,
                                "meta": m.meta, "Q_k": Q.get(m.id, 0.0),
                                "selected_by": tag} for m, tag in chosen],
            "pool_size": len(pool),
            "N_selected": len(chosen),
            "epsilon_used": epsilon}
```

## Dense 匹配（v1：tag overlap）

**为什么不用 embedding？** v1 目标是架构正确性；embedding 需要额外依赖（BGE / OpenAI 等）且维护成本高。tag overlap 在算子这种 "分类明确" 的领域对齐性足够。

**Tag 推断**（`infer_tags`）：

```python
def infer_tags(op_name, spec_path):
    tags = set()
    # 1. 从 op_name 映射算子族
    family_map = {"gelu": "elementwise", "relu": "elementwise",
                  "softmax": "reduction", "matmul": "matmul",
                  "attention": "attention", ...}
    for k, v in family_map.items():
        if k in op_name.lower():
            tags.add(v); tags.add(k)

    # 2. 读 spec.md 解析 dtype
    spec = open(spec_path).read()
    for dt in ["fp16", "bf16", "fp32"]:
        if dt in spec.lower(): tags.add(dt)

    # 3. 额外启发（可扩展）
    return tags
```

**升级路径（v2）**：
- 用 Claude embeddings API 给每条 `content` 生成 vec
- 存 `bank_embeddings.npy`（numpy array，index 与 bank.jsonl 行号对齐）
- Dense 打分 = cosine similarity
- 保留 tag 作为 filter 二级过滤（硬约束）

## ε-greedy Schedule

Linear decay：

$$\varepsilon_t = \max\bigl(\varepsilon_{\text{end}},\ \varepsilon_0 - \frac{t}{T_{\text{decay}}}(\varepsilon_0 - \varepsilon_{\text{end}})\bigr)$$

默认：$\varepsilon_0 = 0.3$, $\varepsilon_{\text{end}} = 0.05$, $T_{\text{decay}} = 20$。

**stage-specific**：
- Stage 1 早期探索很重要（memory 刚启动，Q 值信号弱）
- Stage 2 接近预算末端倾向利用（pure greedy）

## API 混合检索细节（论文 §3.2 末段）

**动机**：API 知识的价值主要取决于 *backend 覆盖度*（这个 op 是否有对应 API），而不是 *历史效用*——所以 API 不该被 Q 值主导。

**实现**：
1. **静态 bundle**：`evo/memory/seed/api_templates/INDEX.md` 分类列出 Ascend C 的核心 API（DataCopy、EnQue/DeQue、Compute 类等）。Drafting 默认全部注入。
2. **精确符号查找**：
   - 从 dense top-K 里的 trace 条目（type=trace）抽 kernel 代码里调用的 API 名（正则扫 `::`、`AscendC::*` 等）
   - 反查 bank 中对应 API 的 api_template 条目
3. **类别/语义搜索**：通过 `ascendc-docs-search` skill 直接查本地 API 文档

## 不变量

1. 输出的 `context_items` 不包含重复 id
2. 若 `subtask = refinement_context`，结果中 **不含** `start_point_id`
3. 若 pool 规模 < N，优雅降级（返回 |pool| 个 items，不报错）
4. `epsilon_used` 必须记录，trail 里可审计 exploration/exploitation 比例

## 实证期望（论文 §4.5 Ablation）

- **Value-driven vs Heuristic-only**（仅 similarity、无 Q）：iteration 30 时 77% vs 67% correctness（L2，L1→L2 setting）
- **K 敏感度**：K=50 左右达到 plateau（→ 我们 default $\lambda N = 50$）
- **Top-N 敏感度**：N=10 左右足够，继续增大边际收益下降
