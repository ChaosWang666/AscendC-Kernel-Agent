# EVO Agent Team

> 与 AVO `agents/AGENTS.md` 平级；复用其 `Agent()` 派发机制和 YAML trailer 协议，新增 EVO 专属角色。

## 团队构成

| Agent | 对标论文 | 职责 | 派发者 |
|-------|---------|------|--------|
| **campaign-orchestrator** | 顶层 M-MDP 外循环 | 消费 `config.yaml: operator_queue`；为每算子驱动 Stage 1 → Stage 2；维护 `state/campaign.json` | 用户首次启动 |
| **stage1-drafter** | §3.3 Cold-Start Drafting | Drafting 循环：调 retrieval-policy → 派 Developer → 调 multigate-verifier → 调 memory-curator 更新 Q_1；首个 $g_{\text{feas}}=1$ 即返回 | campaign-orchestrator |
| **stage2-refiner** | §3.4 Continual Refining | Refining 循环：从 $P(x)$ ε-greedy 选起点 → 派 Developer（注入起点+context）→ 验证 → Q_2 更新 + PopArt 归一化 | campaign-orchestrator |
| **retrieval-policy** | $\mu$（§3.2）| 接受 $(x, \xi_t, \text{stage})$；返回 $N$ 个 memory item：dense top-$K$ → ε-greedy by $Q_k$ 筛 top-$N$ | stage1-drafter / stage2-refiner |
| **memory-curator** | $\mathcal{M}$ 管理（§3.2 + Eq. 3）| 追加 `bank.jsonl`；执行 Eq. 3 更新 `q_values.json`；维护 PopArt `stats.json`；保存 `start_points/{op}/` | stage1-drafter / stage2-refiner（每步） |
| **multigate-verifier** | $V$（§3.5）| anti-hack 二级过滤 → 调 `scoring/score.sh` → 映射退出码 → 返回 $(g_{\text{hack}}, g_{\text{comp}}, g_{\text{corr}}, \ell_{\text{lat}})$ | stage1-drafter / stage2-refiner |

**复用 AVO 角色**（不在 `evo/agents/` 下重复定义）：

| 角色 | 来源 | 在 EVO 中的用法 |
|------|------|----------------|
| Developer（$G_\theta$）| `agents/developer/AGENT.md` | 由 stage agents 派发；prompt 注入 `retrieval_context` 和（Stage 2）`start_point` |
| Reviewer（anti-hack auditor）| `agents/reviewer/AGENT.md` | 由 multigate-verifier 在 model-based anti-hack 阶段派发（`prompt_mode: anti_hack_audit`） |

**不复用**：AVO `Architect / Supervisor / Reporter`（其职责被 EVO 结构替代）。

## 工作流图

```
用户启动
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│  campaign-orchestrator（顶层 M-MDP 外循环）                    │
│                                                                │
│  for op ∈ operator_queue:                                      │
│    读 evo/memory/ + evo/state/campaign.json                    │
│    创建 evo/state/episodes/{op}/                                │
│    ├─► stage1-drafter（Drafting 循环，first_feasible 即退出）  │
│    │     ├─► retrieval-policy（μ 取 N=10 context）              │
│    │     ├─► Agent(Developer, x, c_t)          [G_θ 生成]       │
│    │     ├─► multigate-verifier                [V: 四元组]      │
│    │     └─► memory-curator                    [Q_1 MC 更新]    │
│    │                                                            │
│    └─► stage2-refiner（Refining 循环，budget 剩余步数）         │
│          ├─► retrieval-policy（选 start_point + refinement ctx）│
│          ├─► Agent(Developer, x, p_t, c_t)                     │
│          ├─► multigate-verifier                                 │
│          └─► memory-curator                   [Q_2 + PopArt]    │
│    更新 state/campaign.json.completed_ops                      │
└──────────────────────────────────────────────────────────────┘
```

## 派发方式

**首选**：Claude Code `Agent()` 工具（同 AVO）

```python
Agent(
    description="<EVO role>: <op_name> stage<k> step<t>",
    subagent_type="general-purpose",
    prompt="<见对应 AGENT.md 的 Prompt 模板>"
)
```

## YAML Trailer 协议（继承 AVO）

所有 EVO 子 agent 产出文件底部写：

```yaml
---
role: campaign-orchestrator | stage1-drafter | stage2-refiner | retrieval-policy | memory-curator | multigate-verifier
status: success | partial | fail
summary: 一句话说明
artifacts:
  - path: evo/state/episodes/{op}/trajectory.jsonl
  - path: evo/memory/q_values.json
next_action: continue | fail_fast | escalate
details:
  # 角色特定字段（见各 AGENT.md）
---
```

## 并行派发规则（同 AVO）

- **独立 agent → 单消息多 `Agent()` 块**
- **依赖 agent → 顺序调用**
- EVO 典型并行点：Stage 2 内可 **同时派发多个不同 start_point + context 组合**（A/B 探索）；不常用，默认顺序串行

## 环境与约束

- 所有 bash 调用前：`source /usr/local/Ascend/ascend-toolkit/set_env.sh`
- Memory Bank 读写 **单线程**：只有 memory-curator 可写 `bank.jsonl` / `q_values.json` / `stats.json`
- Stage agents 读取 memory **无锁**（只读）；retrieval-policy 可缓存 K 候选以避免重复扫描
- `evo/state/campaign.json` 只由 campaign-orchestrator 写；episode state.json 由 stage agents 写

## 启动入口

```bash
# 用户首次启动（从根目录）
claude --print -p "读取 evo/agents/AGENTS.md 和 evo/config.yaml，派发 evo/agents/campaign-orchestrator/AGENT.md 开始 EVO campaign"
```

或交互：

```
> 读 evo/agents/campaign-orchestrator/AGENT.md，按 evo/config.yaml 的 operator_queue 驱动 EVO 跨算子循环
```
