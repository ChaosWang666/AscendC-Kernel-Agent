# M-MDP 形式化（论文 §3.1）

## 定义

**Memory-based Markov Decision Process**：五元组 $(\mathcal{S}, \mathcal{A}, \mathcal{M}, \mathcal{P}, \mathcal{R})$

### $\mathcal{S}$：State Space

$$s_t = (x, \xi_t)$$

| 分量 | 物理含义 | 在本系统的体现 |
|------|---------|--------------|
| $x \in \mathcal{X}$ | 静态任务（PyTorch op + metadata）| `workspace/specs/{op}.md` + `workspace/runs/{op}/test/reference.py` |
| $\xi_t$ | 动态生成状态 | `evo/state/episodes/{op}/state.json` 字段 `{stage, iter, feasible_found, b_t, budget_remaining}` |

### $\mathcal{A}$：Action Space

$$a_t = y_t \in \mathcal{Y}$$

生成的完整 kernel 源码。物理实体：`workspace/runs/{op}/attempts/step_t/{OpName}Custom/`（含 `op_host/*.cpp`, `op_host/*_tiling.h`, `op_kernel/*.cpp`）。

### $\mathcal{M}$：Memory

$$\mathcal{M}_{t+1} \leftarrow \mathcal{M}_t \cup \{(s_t, a_t, r_t)\} \quad\text{(Eq. 1)}$$

持久化在 `evo/memory/bank.jsonl`。异质内容（论文 §3.2）：

1. **API 模板**（backend-specific；Ascend C API 权威模板）
2. **经验摘要**（成功/失败）
3. **生成 trace**（draft + refined 变体）
4. **最佳实践**

初始化 $\mathcal{M}_0$：读 `evo/memory/seed/` 填充（由 memory-curator 的 `bootstrap_seed` 模式执行）。

### $\mathcal{P}$：Transition

任务 $x$ 在 episode 内不变 ⇒ 确定性转移：

$$s_{t+1} = (x, \xi_{t+1}), \quad \xi_{t+1} = f(x, \xi_t, a_t, o_t) \quad\text{(Eq. 2)}$$

$f$ 的实现（`memory-curator` + stage agents 合作）：

```python
def f(x, xi, a, o):
    xi.iter += 1
    xi.budget_remaining -= 1
    if o.g_feas:
        xi.feasible_found = True
        xi.b_t = min(xi.b_t or inf, o.latency_us)
    if xi.stage == "drafting" and o.g_feas:
        xi.stage = "refining"
    return xi
```

### $\mathcal{R}$：Reward

两阶段分别定义，见 `stage1-drafting.md` Eq. 4 和 `stage2-refining.md` Eq. 5。

## 策略分解（Eq. Policy Factorization）

$$\pi(y_t \mid s_t, \mathcal{M}_t) = G_\theta(a_t \mid s_t, c_t) \cdot \mu(c_t \mid s_t, \mathcal{M}_t)$$

| 因子 | 可学习？ | 实现 |
|------|--------|------|
| $G_\theta$ | 冻结（预训练 LLM）| Claude Code `Agent()` 派发 `agents/developer/AGENT.md` |
| $\mu$ | **通过 RL 学** | `evo/agents/retrieval-policy/AGENT.md`，基于 $Q_k$ |

## 轨迹

$$\tau = (s_0, c_0, a_0, r_0, s_1, c_1, a_1, r_1, \dots, s_T)$$

持久化：每 $(s_t, c_t, a_t, r_t, o_t)$ 一行 JSON 追加到 `evo/state/episodes/{op}/trajectory.jsonl`。

## Episode 与 Campaign

| 概念 | 范围 | 周期 |
|-----|------|------|
| **Step** | 一次 $(s_t, a_t, r_t)$ 完整周期 | seconds–minutes（score.sh 主导） |
| **Episode** | 对一个算子 $x$ 的完整 Drafting + Refining | 30 步 × ~2 min = 1 小时 |
| **Campaign** | 遍历 `operator_queue` 所有算子 | hours–days |

$\mathcal{M}$ **跨 episode 持续累积**——这是 EVO 与 AVO 的本质差异（AVO 按单算子 state.json，EVO 共享 memory bank）。

## 与 AVO 概念映射（便于迁移理解）

| EVO（M-MDP）| AVO 对应 |
|------------|---------|
| $s_t = (x, \xi_t)$ | `evolution/state.json` + `workspace/specs/{op}.md` |
| $a_t = y_t$ | `workspace/runs/{op}/attempts/step_N` |
| $r_t$（显式）| REVIEW.md 评分 + v{N}.json 结果的启发式合成 |
| $\mathcal{M}$（共享）| 无（AVO 是 per-op） |
| $\mu$（检索策略）| 无（Architect 自己决策） |
| $G_\theta$ | Developer Agent |
| $V$（多门）| Reviewer + Tester（隐式合并） |

## 关键性质

1. **Partial observability**：$s_t$ 不是完全状态（实际硬件 NPU 的 memory/cache 状态不可观）——但足以做检索和选择
2. **Bounded reward**：$r_t \in [-1, 1]$（Stage 1 二值；Stage 2 tanh 天然有界）⇒ $Q$ 有界（App A.2）
3. **Markovian**：给定 $(x, \xi_t)$，$a_t$ 的选择仅依赖当前 retrieval；$\mathcal{M}$ 累积是 "side channel"
4. **非 stationary**：$\mathcal{M}_t$ 随时间扩张，导致 optimal policy 随 t 变——所以用在线 MC 更新而非 batch 训练

## 实例化要点

**Episode 开始**：`campaign-orchestrator` 创建 `evo/state/episodes/{op}/state.json`，初始 $\xi_0$：
```json
{"stage": "drafting", "iter": 0, "feasible_found": false, "b_t": null,
 "budget_remaining": 30, "last_failure_reason": null}
```

**Episode 结束**：
- Stage 1 failed → `xi.stage = "stage1_failed"`，Campaign 跳到下一算子
- Stage 2 耗尽 → 写回 campaign.json，下一算子

**Campaign 结束**：所有 op 跑完 → `campaign.json.finished_at` + 汇总报告（留给后续 Reporter-like agent，本版不实现）。
