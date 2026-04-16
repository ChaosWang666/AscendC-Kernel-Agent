# Memory Bank 持久化 Schema

> 权威：memory-curator 是唯一写手；所有其他 agent 只读。

## 文件清单

```
evo/memory/
├── bank.jsonl           # 追加式记忆条目（每行一条 JSON）
├── q_values.json        # 每 memory_id 的 Q_1, Q_2 + 访问计数
├── stats.json           # PopArt 在线统计（Stage 2）
├── seed/                # M_0 种子
│   ├── api_templates/INDEX.md
│   └── best_practices.md
└── start_points/{op}/   # P(x)：可行 kernel snapshot
    └── {variant_id}/    # 完整 {OpName}Custom 工程 + meta.json
```

---

## `bank.jsonl`

**格式**：JSONL（每行一条 JSON，无数组包裹，append-only）

**单条 schema**：

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "api_template | experience | trace | failed_trace | best_practice",
  "operator": "gelu_custom",
  "stage_when_added": 1,
  "content": "<字符串：markdown or 代码片段 or 描述>",
  "meta": {
    "source": "seed | runtime | transfer",
    "tags": ["elementwise", "fp16", "ub_bound"],
    "kernel_path": "workspace/runs/gelu_custom/attempts/step_3/GeluCustom",
    "feasible": true,
    "latency_us": 35.64,
    "latency_measure_type": "median",              // Item 1/P6: 默认 median;旧数据可能含 "mean_legacy"
    "latency_cv": 0.08,                            // 测量 coefficient of variation
    "parent_trace_id": "<uuid of parent or null>",
    "reason": "compile_error | correctness_mismatch | ...",
    "token_count": 412
  },
  "created_at": "2026-04-15T03:20:17Z"
}
```

### `type` 语义

| type | 来源 | 典型 content |
|------|------|-------------|
| `api_template` | seed 或 transfer | Ascend C API 使用模板片段（如 "DataCopy 用法 + 对齐约束"） |
| `experience` | 运行时（可选）| Stage agents 显式入库的经验摘要（e.g., "BUFFER_NUM=2 在 elementwise 是 sweet spot"）|
| `trace` | 运行时，feasible=true | 成功 kernel 的关键片段（tiling 策略 + 核心 op_kernel 循环）|
| `failed_trace` | 运行时，feasible=false | 失败 kernel + 失败原因（用于未来 "别这么写" 的负例） |
| `best_practice` | seed | skills 精华摘要 |

### `meta.tags`

标签取自：
- 算子分类（`elementwise` / `reduction` / `matmul` / `conv` / `attention` / ...）
- 硬件特性（`fp16` / `bf16` / `fp32` / `vec` / `cube` / `ub_bound` / `bw_bound`）
- 技巧（`double_buffer` / `tile_pow2` / `scalar_opt` / `pipe_barrier`）
- 算子族（`gelu` / `relu` / `softmax` / ...）

**标签标注时机**：memory-curator 入库时从 state + reviewer/verifier 反馈中推断；可由 LLM 辅助。

### 增长策略

- 不主动删除；失败 trace 也保留（提供 "何不可" 信号）
- 超过 10k 条考虑归档（`bank.archive.jsonl`）——当前不实现
- 每条 `content` 限 2000 tokens（超长 truncate 并保留 `meta.truncated_original_path` 指针）

---

## `q_values.json`

**格式**：JSON dict，key = memory_id，value = Q 值元数据

```json
{
  "550e8400-e29b-41d4-a716-446655440000": {
    "Q1": 0.23,
    "Q2": -0.15,
    "visit_1": 12,
    "visit_2": 4,
    "last_updated_t": 87
  },
  "660f9511-...": {...}
}
```

### 字段含义

| 字段 | 含义 |
|------|------|
| `Q1` | 在 Drafting 阶段的累积 Q 值（期望 feasibility 贡献） |
| `Q2` | 在 Refining 阶段的累积 Q 值（期望 latency 改善贡献） |
| `visit_1` | Stage 1 被 retrieval 命中过多少次（被用于 context 或 start-point） |
| `visit_2` | 同上，Stage 2 |
| `last_updated_t` | 上次更新的全局 step（跨 episode 累计） |

### 初始化

- 新 item 首次出现在 `bank.jsonl` 时，memory-curator 会在下一次 Q 更新才创建条目
- 若检索时 item 尚无 Q 条目，retrieval-policy 按 `config.q_update.q_init`（默认 0）计算
- Seed 条目（来自 `bootstrap_seed`）全部初始化 Q=0

### 更新规则

严格遵循 Eq. 3：

$$Q_k \leftarrow Q_k + \alpha (r - Q_k)$$

Clip 到 `config.q_update.q_clip`（默认 [-1, 1]）。

---

## `stats.json`

**格式**：

```json
{
  "stage2": {
    "mu": 0.021,
    "sigma": 0.413,
    "n": 187,
    "momentum": 0.99,
    "updated_at_step": 187
  }
}
```

### PopArt 在线更新规则

给定新 raw reward $r$：

```
m = momentum
μ_new = m·μ + (1-m)·r
δ = r - μ_new
σ²_new = m·σ² + (1-m)·δ²
σ_new = max(√σ²_new, ε)        # ε = config.reward_stage2.popart_epsilon
```

归一后 $\hat{r} = (r - \mu_{\text{new}}) / \sigma_{\text{new}}$。

**细节**：我们用 EMA 的 σ² 估计（不是完整 Welford），因为 online 且 drift 可接受。

---

## `start_points/{op}/{variant_id}/`

**内容**：

```
evo/memory/start_points/gelu_custom/550e8400-.../
├── GeluCustom/                 完整自定义算子工程 snapshot（cp -r from attempts/step_N/GeluCustom）
└── meta.json
```

**`meta.json`**：

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "operator": "gelu_custom",
  "latency_us": 35.64,
  "discovered_at_step": 3,
  "discovered_at_stage": 1,
  "source_attempt_dir": "workspace/runs/gelu_custom/attempts/step_3",
  "bank_entry_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-04-15T03:20:17Z"
}
```

`bank_entry_id` 与 `id` 通常相同（entry ID 就是起点 ID）。

### $P(x)$ 的加载

Stage 2 启动时，stage2-refiner 从 `evo/memory/start_points/{op_name}/` 扫描所有子目录，组装成 $P(x)$ 列表。每次可行 kernel 加入后，新增一个子目录。

---

## 增长与 GC 策略

**预期规模**（100 算子 campaign × 30 步/算子）：
- `bank.jsonl`：3000 条 runtime trace + 24 条 seed ≈ 3k 条 ~5 MB
- `q_values.json`：~3k 条目 ~1 MB（RMW 每步 ~100 ms JSON 往返）
- `trajectory.jsonl`：per-op 30 条，总 3k 条 ~1 MB
- `start_points/{op}/{id}/`：partial snapshot（op_host + op_kernel 源）每份 ~40 KB；~500 份 ≈ 20 MB

**主动 GC（v1 未自动触发；memory-curator 预留 `archive_bank` mode）**：

- 阈值：`bank.jsonl` 行数 > 10k 时
- 策略：把 `visit_1 + visit_2 == 0` 且 `created_at < now - 30d` 的条目移到 `bank.archive.jsonl`；保留全部 seed + 最近 5k 条
- q_values 同步归档（删 archive 对应 id）

**q_values.json 优化路径（v2）**：

v1 每步 RMW 对 <5k 条 OK；更大规模可改成 append-only 日志 + 周期 compact：

- `q_values.log.jsonl`：每次更新 append `{id, stage, Q_new, visit, timestamp}`
- compact 每 100 步：replay log → rewrite `q_values.json`
- 读端 lazy load：active dict 从 snapshot + 追 log 末尾得最新值

v1 不实现；当 campaign 规模达到 1000+ 算子时再评估。

**bank.jsonl 线性扫描（retrieval）**：

v1 每次检索 O(n) 扫所有条目做 tag overlap。对 <5k 条 CPU <10 ms，可接受。
超过后 v2 方案：bootstrap 建 `bank_tag_index.json`（`{tag: [mem_id, ...]}`），
retrieval 先按 tag 求并集得候选，再精算 overlap——从 O(n) 降到 O(k)。

## 并发与原子性

- **写入单点化**：只有 memory-curator 写 `bank.jsonl` / `q_values.json` / `stats.json` / `start_points/`
- **Append-only bank**：`echo '{...}' >> bank.jsonl` 单行原子（系统保证）
- **RMW 文件**（q_values.json / stats.json）：写 `.tmp` → `mv` 原子替换
- **不加锁**：假设 stage agents 串行派发 memory-curator；如未来并发扩展，在 memory-curator 增加 `flock`

## `state.json` 与 `trajectory.jsonl`(episode 状态)

位于 `evo/state/episodes/{op_name}/`,由 stage agents 写入。

### `state.json` schema(Item 1/P6 + Item 5 扩展后)

```json
{
  "op_name": "gelu_custom",
  "stage": "drafting | refining | stage1_failed",
  "iter": 8,
  "feasible_found": true,
  "b_t": 37.86,                         // best latency observed so far (us)
  "b_t_measure_type": "median",         // Item 1/P6: 必填;历史数据可为 "mean_legacy"
  "b_t_cv": 0.084,                      // 该测量的 cv;null 表示未记录
  "b_t_retrofit_note": "<str|null>",   // 可选:数据迁移时的溯源说明
  "budget_remaining": 22,
  "stage1_steps_used": 2,
  "P_x_size": 7,
  "initial_feasible_at_step": 1,
  "last_failure_reason": "<str|null>",
  "consecutive_failure_count": 0,       // Item 5: ε-burst trigger 计数
  "last_epsilon_burst_at_step": -1,     // Item 5: 上次 burst 的 step(-1 表示从未)
  "updated_at": "2026-04-16T08:23:23Z"
}
```

**b_t 语义**:必须 median-canonical,从 `score_{t}.json.performance_primary` 取(自 R9+R12 起该字段即 median*1000)。每步 Stage 2 若 `latency < b_t` 则更新;`_measure_type="mean_legacy"` 的 b_t 不能直接用于 tanh reward(需先重测或迁移)。

**consecutive_failure_count 更新规则**(Item 5 / ε-burst):
- 每步末,若 g_feas=1 且 latency < b_t:`reset to 0`
- 否则:`+= 1`
- 当 `>= config.retrieval.epsilon_burst.threshold` 且 `(iter - last_epsilon_burst_at_step) >= cooldown_steps`:下一步 ε 重置到 `epsilon_burst.reset_to`,并更新 `last_epsilon_burst_at_step = iter`

### `trajectory.jsonl` schema(逐行 JSON)

```json
{
  "t": 2,
  "stage": 2,
  "s": { "iter": 2, "budget_remaining": 28, "feasible_found": true },
  "a": {
    "kernel_path": "workspace/runs/gelu_custom/attempts/step_2/GeluCustom",
    "attempt_dir": "workspace/runs/gelu_custom/attempts/step_2",
    "mode": "optimize",
    "optimization_hypothesis": [          // Item 3/P6: Developer Minimal-Change 列出的假设
      "UB_TILE_BYTES 8K->16K reduces tile-switch overhead (~5%)"
    ]
  },
  "o": {
    "g_hack": 1, "g_comp": 1, "g_corr": 1,
    "latency_us": 34.88,
    "_measure_type": "median",            // Item 1/P6: 必填;历史可为 "mean_legacy"
    "latency_cv": 0.084,                  // 可选
    "reason": null,
    "exit_code": 0,
    "g_feas": 1
  },
  "r": 1,                                 // Stage 1 reward (±1) 或 Stage 2 r_raw
  "r_norm": 0.0476,                       // Stage 2 only: PopArt-normalized reward
  "c_ids": ["mem-uuid-1", "mem-uuid-2"],
  "c_selected_by": ["greedy", "seed_api"],
  "start_point_id": "<uuid|null>",        // Stage 2 only
  "q_updated_count": 2,                   // memory-curator 实际更新 Q 的 items 数
  "visit_only_updated": 8,                // 仅 visit+1 的 seed items 数(F4 诊断)
  "epsilon_used": 0.275,
  "epsilon_burst_active": false,          // Item 5: 本步 ε 是否由 burst 机制提升
  "new_item_id": "<uuid>",
  "start_point_added": true,
  "timestamp": "2026-04-16T08:12:00Z"
}
```

**增长**:每步末追加一行,永不删除。

---

## 可读性 / 调试

查看 Memory Bank 状态：

```bash
# 条目数
wc -l evo/memory/bank.jsonl

# 按 type 分布
jq -r '.type' evo/memory/bank.jsonl | sort | uniq -c

# Q_1 top 5（看哪些 items 在 Drafting 阶段最有价值）
jq -r 'to_entries | sort_by(.value.Q1) | reverse | .[0:5] | .[] | "\(.key) Q1=\(.value.Q1)"' \
   evo/memory/q_values.json

# Stage 2 reward 分布
jq -s '. | group_by(.stage) | .[] | {stage: .[0].stage, count: length, avg_reward_raw: (map(.r_raw) | add / length)}' \
   evo/state/episodes/gelu_custom/trajectory.jsonl
```
