# 论文 → 本仓库 完整映射

> 对照论文 `EVO-paper/main.tex`（*EvoKernel: Value-Driven Memory Update for Kernel Evolution*）的章节、方程、图表到本仓库的文件 / 实现位置。

## §3 Method（核心框架）

| 论文元素 | 本仓位置 |
|---------|---------|
| §3（总览 Fig 1 pipeline）| `evo/README.md` + `evo/spec.md` |
| §3.1 Problem Formulation | `evo/spec.md` §1（权威） |
| §3.2 Memory Architecture + Value-Driven Retrieval | `evo/docs/memory-schema.md` + `evo/docs/retrieval-algorithm.md` + `evo/agents/retrieval-policy/AGENT.md` + `evo/agents/memory-curator/AGENT.md` |
| §3.3 Stage 1: Cold-Start Drafting | `evo/docs/stage1-drafting.md` + `evo/agents/stage1-drafter/AGENT.md` |
| §3.4 Stage 2: Continual Refining | `evo/docs/stage2-refining.md` + `evo/agents/stage2-refiner/AGENT.md` |
| §3.5 Multi-gate Verification | `evo/docs/multi-gate-verification.md` + `evo/agents/multigate-verifier/AGENT.md` |

## 方程映射

| 论文 Eq. | 含义 | 本仓实现位置 |
|---------|------|------------|
| **Eq. 1** | $\mathcal{M}_{t+1} \leftarrow \mathcal{M}_t \cup \{(s_t,a_t,r_t)\}$ | `memory-curator.update_stage{1,2}.append_to_bank` |
| **Eq. 2**（paper Eq. 2 转移）| $s_{t+1}=(x, f(x,\xi_t,a_t,o_t))$ | `stage{1,2}-refiner` 末尾更新 `state.json` |
| **Eq. 3**（paper Eq. 3 策略分解）| $\pi = G_\theta \cdot \mu$ | 系统架构：Developer = $G_\theta$，retrieval-policy = $\mu$ |
| **Eq. Unified Update** | $Q \leftarrow Q + \alpha(r - Q)$ | `memory-curator` 的 Q 更新 + `evo/docs/q-value-update.md` |
| **Eq. 4**（Stage 1 reward）| $r_{1,t} = \pm 1$ 基于 $g_{\text{feas}}$ | `stage1-drafter` Step 4 |
| **Eq. 5**（Stage 2 reward）| $r_{2,t} = \tanh(\log b - \log \ell)$ | `stage2-refiner` Step 5 + PopArt |
| **Eq. Feasibility**（§3.5）| $g_{\text{feas}} = g_{\text{hack}} \wedge g_{\text{comp}} \wedge g_{\text{corr}}$ | `multigate-verifier` Step 3 |
| **Eq. Verifier output**（§3.5）| $o_t = (g_{\text{hack}}, g_{\text{comp}}, g_{\text{corr}}, \ell_{\text{lat}})$ | `multigate-verifier` trailer.details.o_t |

## §4 Experiment（复现参数）

| 论文参数 | 默认值 | 本仓配置 |
|---------|-------|---------|
| Per-op budget $T$ | 30 | `evo/config.yaml: per_op_budget` |
| Correctness tolerance | atol=rtol=1e-2 | `verifier.tolerance_atol/rtol` |
| Latency 测量 | msprof 3 passes mean | 复用 `scoring/test_performance.py`（AVO 已实现） |
| Benchmark | KernelBench L1+L2 | `config.operator_queue`（当前预置 gelu_custom，用户按需扩充） |
| Generators 评估 | GPT-5.2 / DeepSeek / Qwen | 复用 Claude Code `Agent()` 派发 Developer（单 generator） |

## §4.2 Transfer 实验（跨算子迁移）

- 论文 "L1 → L2" stream：按 L1 全跑完后进入 L2，memory 保留 → 本仓 `operator_queue` 按 level 顺序排列实现
- Cross-backbone transfer：复用同一 `evo/memory/` 给不同 generator（仅切换 `config.generator.dispatch`）

## §4.5 Ablation（超参 ablation 的锚点）

| 论文 ablation | 复现方式（仅记录设计空间，本版不跑） |
|-------------|----------------------------------|
| Value-driven vs Heuristic-only | 把 retrieval-policy 里 `by=Q_k` 替换成 `by=similarity`（提供 flag）|
| Cross-task vs Per-task | 把 `evo/memory/` 改成 `evo/memory_{op}/` per-op 隔离 |
| Retrieval pool size $K$ ablation | 扫 `config.retrieval.lambda ∈ {1, 3, 5, 10}` |
| Top-N ablation | 扫 `config.retrieval.N ∈ {5, 10, 20}` |

## App A: Proofs for Value Update Stability

| 论文 | 本仓 |
|------|------|
| A.1 Notation | `evo/docs/q-value-update.md` 开头 |
| A.2 Boundedness | `evo/docs/q-value-update.md` §有界性 |
| A.3 Online Normalization Stability | 同上 §PopArt 稳定性 |
| A.4 Convergence of Bandit Update | 同上 §收敛性 |

## App B: Anti-Hacking Screening

| 论文 | 本仓 |
|------|------|
| B.1 Rule-based | `evo/docs/multi-gate-verification.md` §Anti-Hacking-第一层 + `config.yaml: anti_hack.rule_based` |
| B.2 Model-based LLM Auditor | `evo/docs/multi-gate-verification.md` §Anti-Hacking-第二层 + `agents/reviewer/AGENT.md` 的 `prompt_mode=anti_hack_audit`|

## App C: Baseline Methodologies

| 论文 Baseline | 对应 AVO/EVO 近似 |
|-------------|------------------|
| Pass@k | 纯 N 次无状态派发 Developer（对应 `evo/config.yaml: mode=pass_k`，未实现） |
| Iterative Refinement | 相当于 Stage 2 without cross-task memory（退化） |
| Codex by OpenAI | 参考基准，不在本仓复现 |
| **Ours (EVO)** | 本仓主路径 |

## 关键图表 → 运行产物映射

| 论文 Figure | 运行后应从哪里得到 |
|------------|------------------|
| Fig 1 Pipeline | `evo/README.md` 架构图 |
| Fig Set1 Transfer | `evo/state/campaign.json` + 汇总日志（Reporter-like agent 未来实现）|
| Fig Set2 Retrieval ablations | Ablation 运行后的 `q_values.json` 差异 |
| Fig Set3 Convergence curves | `trajectory.jsonl` 的 reward 曲线 |
| Fig Optimization outcomes | `start_points/{op}/meta.json` 的 latency 分布 |

## 本版 vs 论文：已知差距（记录但不实现）

| 项目 | 论文 | 本仓 v1 |
|------|------|--------|
| Dense retrieval 方法 | 语义 embedding | v1 简化为 tag overlap；v2 可升 embedding |
| Anti-hack model-based auditor | 独立 LLM | 复用 Reviewer agent（差异在独立性） |
| Bottleneck-guided refinement | profiler-derived | v1 可人工注记；v2 集成 msprof 自动诊断 |
| Multi-generator 评估 | GPT-5.2 / DeepSeek / Qwen | 单 generator（Claude Code Agent） |
| Transfer across backbones | Memory 可移植 | 架构支持，未实测 |
| Stress scale 运行 | KernelBench 全集 | 架构就绪，等用户填 operator_queue |

## 可执行的 "复现度检查"

本版声明 "完整算法复现" 的含义：

✓ 两阶段 pipeline（Drafting / Refining）结构化分离
✓ 跨算子共享 Memory Bank
✓ Stage-specific Q_1, Q_2 MC 更新
✓ Eq. 4 二值 + Eq. 5 tanh reward
✓ PopArt 归一化
✓ Multi-gate verifier 四元组
✓ Rule + Model-based anti-hacking
✓ ε-greedy exploration + linear decay
✓ Q clip 有界
✓ Dense top-K 候选 + ε-greedy top-N 终选

✗ 跑通端到端（留给下一轮 smoke test）
✗ Embedding-based retrieval（v2）
✗ Profiler-driven bottleneck（v2）
