# EVO 框架（EvoKernel 论文复现）

## 概述

EVO 是 `AscendC-Kernel-Agent` 仓库里与 AVO 平级的 **跨算子、价值驱动** 的自主算子合成框架，复现论文：

> *EvoKernel: Value-Driven Memory Update for Kernel Evolution*（本仓 `EVO-paper/main.tex`）

核心公式（论文 Eq. 2）：

$$\pi(y_t \mid s_t, \mathcal{M}_t) \;=\; G_\theta(a_t \mid s_t, c_t)\cdot \mu(c_t \mid s_t, \mathcal{M}_t)$$

- $G_\theta$：生成策略 = Claude Code `Agent()` 派发 `evo/agents/developer/AGENT.md`
- $\mu$：价值驱动检索策略 = `evo/agents/retrieval-policy/AGENT.md`
- $\mathcal{M}_t$：跨算子共享 Memory Bank = `evo/memory/`
- $Q_1, Q_2$：阶段专属 Q 值（Drafting 看 correctness，Refining 看 latency）
- $V$：多门验证器 = `evo/agents/multigate-verifier/AGENT.md`（包 `scoring/score.sh`）

## 与 AVO 的本质差异

| 维度 | AVO | EVO |
|------|-----|-----|
| 目标 | 单算子 per-operator 进化 | 跨算子 campaign（L1→L2 迁移） |
| 检索 | 无（Architect 凭经验） | Dense top-K → ε-greedy Q 过滤 |
| 奖励 | 隐式（REVIEW 评分） | 显式：Stage 1 二值 $\pm 1$；Stage 2 $\tanh(\log b - \log \ell)$ + PopArt |
| 记忆 | per-operator `evolution/state.json` | 全局 `evo/memory/bank.jsonl` + `q_values.json` |
| 流程 | 单循环 Edit-Review-Test | 两阶段：Drafting（首次可行即切换）→ Refining（耗尽预算） |
| 干预 | Supervisor 启发式 | Q 值自动调节（无需 Supervisor） |

## 目录结构

```
evo/
├── README.md                       ← 你在这里
├── config.yaml                     超参 + operator queue
├── spec.md                         M-MDP 形式化 + 所有论文方程
├── agents/
│   ├── AGENTS.md                   团队协议 + YAML trailer 契约
│   ├── campaign-orchestrator/      顶层：消费 operator queue
│   ├── stage1-drafter/             Drafting 调度器
│   ├── stage2-refiner/             Refining 调度器
│   ├── retrieval-policy/           μ 策略（dense + ε-greedy）
│   ├── memory-curator/             Memory R/W + MC Q-update + PopArt
│   └── multigate-verifier/         V 包装器（anti-hack + score.sh）
├── memory/
│   ├── bank.jsonl                  追加式记忆条目
│   ├── q_values.json               Q_1 / Q_2 + visit count
│   ├── stats.json                  PopArt (μ_2, σ_2, n)
│   ├── seed/                       M_0 种子
│   │   ├── api_templates/INDEX.md  Ascend C 模板清单
│   │   └── best_practices.md       skill 精华
│   └── start_points/{op}/          P(x) 可行起点集
├── state/
│   ├── campaign.json               全局状态（队列、当前 op、当前 stage）
│   └── episodes/{op}/              per-op：state.json + trajectory.jsonl + scores/
└── docs/                           算法详细说明
    ├── memory-schema.md
    ├── retrieval-algorithm.md
    ├── stage1-drafting.md
    ├── stage2-refining.md
    ├── multi-gate-verification.md
    ├── q-value-update.md
    └── paper-mapping.md
```

## 启动方式（Agent 入口）

```bash
# 单次会话启动 campaign
claude --print -p "读 evo/README.md 和 evo/config.yaml，派发 evo/agents/campaign-orchestrator/AGENT.md 开始 EVO campaign"
```

交互式（更稳定）：

```bash
claude
> 读取 evo/agents/AGENTS.md 作为团队协议，然后按 evo/config.yaml 的 operator_queue 依次派发 campaign-orchestrator
```

## 论文章节 → 文件 速查

| 论文 | 本仓位置 |
|------|---------|
| §3 EvoKernel 框架总览 | `evo/spec.md` + 本文件 |
| §3.1 Problem Formulation（M-MDP）| `evo/spec.md` §1 |
| §3.2 Memory + Value-Driven Retrieval | `evo/docs/memory-schema.md` + `retrieval-algorithm.md` |
| §3.3 Stage 1 Cold-Start Drafting | `evo/docs/stage1-drafting.md` + `evo/agents/stage1-drafter/AGENT.md` |
| §3.4 Stage 2 Continual Refining | `evo/docs/stage2-refining.md` + `evo/agents/stage2-refiner/AGENT.md` |
| §3.5 Multi-gate Verification | `evo/docs/multi-gate-verification.md` + `evo/agents/multigate-verifier/AGENT.md` |
| Eq. 3（MC Q 更新）| `evo/docs/q-value-update.md` |
| App B Anti-Hacking | `evo/docs/multi-gate-verification.md` 后半 |
| App A Proofs（boundedness + convergence）| `evo/docs/q-value-update.md` 后半 |
| §4.1 实验 setup（T=30, atol=rtol=1e-2）| `evo/config.yaml` |
| 对照完整表 | `evo/docs/paper-mapping.md` |

## 共享基建（EVO 与 AVO 共用）

以下资源在 `main`（AVO）和 `EVO` 分支都存在，EVO 直接调用：

| 资源 | EVO 用法 |
|------|---------|
| `scoring/score.sh` | `multigate-verifier` 调用后解析退出码得 $(g_{\text{comp}}, g_{\text{corr}}, \ell_{\text{lat}})$ |
| `scoring/configs/{op}.json` | 不改；`multigate-verifier` 直接传递 |
| `workspace/runs/{op}/attempts/step_N/` | 每次 $G_\theta$ 生成仍写入此处（由 stage agents 按需 `mkdir -p`）；可行 snapshot 拷到 `evo/memory/start_points/{op}/` |
| `workspace/runs/{op}/test/reference.py` | $g_{\text{corr}}$ 比对源（PyTorch ref） |
| `workspace/{specs,templates,deploy}/` | 算子规格 / msopgen 模板 / 部署 OPP 目录 |
| `Knowledge-base/` | $\mathcal{M}_0$ 种子来源；种子索引见 `memory/seed/api_templates/INDEX.md` |
| `evolution/` | `scoring/score.sh` 在运行时 `mkdir -p` 生成的评分日志目录（仓内不保留） |

**EVO 不复用 AVO 的 Agent 角色**（以下角色仅在 `main` 分支）：
- `architect`：职责被 stage agents + retrieval-policy 分解
- `supervisor`：被 Q 值机制取代
- `reporter` / `tester`：EVO 用 `multigate-verifier` + 显式 Q 值记录代替

## 当前状态

- **阶段**：架构已搭，**未跑端到端**
- **分支**：`EVO`（已剥离 AVO 框架内容；仅保留共享基建 `scoring/`、`Knowledge-base/`、`workspace/{specs,templates,deploy,runs/*/test}`）
- **下一步**：在本分支按 `evo/config.yaml` 的 operator_queue 启动首次 campaign 做 smoke test
