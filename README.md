# AscendC Kernel Agent — EVO Branch

Autonomous, **value-driven, cross-operator** Ascend C kernel synthesis framework for Huawei Ascend NPUs. This branch reproduces the **EvoKernel** paper (`EVO-paper/main.tex`).

> The `main` branch hosts the separate **AVO** (Agentic Variation Operators) framework — a single-operator evolutionary loop. The two frameworks share scoring / knowledge base / workspace test infrastructure but are otherwise independent.

## Core Formula (paper Eq. 3)

```
π(y_t | s_t, M_t) = G_θ(a_t | s_t, c_t) · μ(c_t | s_t, M_t)
```

| Symbol | Role | Implementation |
|--------|------|---------------|
| **G_θ** | Generation policy (pretrained LLM) | `evo/agents/developer/AGENT.md` (dispatched by stage agents) |
| **μ** | Value-driven retrieval policy | `evo/agents/retrieval-policy/AGENT.md` |
| **M_t** | Cross-operator shared memory bank | `evo/memory/` |
| **V** | Multi-gate verifier | `evo/agents/multigate-verifier/AGENT.md` (wraps `scoring/score.sh`) |
| **Q_1, Q_2** | Stage-specific Q values (Drafting / Refining) | `evo/memory/q_values.json` |

## Architecture

```
campaign-orchestrator  ──consumes operator_queue──▶
    │
    ├── stage1-drafter (Cold-Start Drafting)
    │      retrieval-policy → developer (G_θ) → multigate-verifier → memory-curator
    │      exits on first feasible kernel (binary reward ±1)
    │
    └── stage2-refiner (Continual Refining)
           ε-greedy start_point + refinement context → developer → verifier → memory-curator
           reward = tanh(log b_t − log ℓ_lat), PopArt-normalized
```

See `evo/README.md` for full agent team, memory schema, and paper-to-repo mapping.

## Key Differentiators vs AVO (main branch)

| Dimension | AVO (main) | EVO (this branch) |
|-----------|-----------|-------------------|
| Scope | Single-operator evolution | Cross-operator campaigns (L1 → L2 transfer) |
| Retrieval | Architect heuristics | Dense top-K → ε-greedy Q filter |
| Reward | Implicit review scoring | Explicit Eq. 4 (±1) + Eq. 5 (tanh) + PopArt |
| Memory | Per-operator `evolution/state.json` | Global `evo/memory/bank.jsonl` + `q_values.json` |
| Loop | Single Edit-Review-Test cycle | Two-stage: Drafting → Refining |
| Intervention | Supervisor heuristics | Q-value auto-adjustment |

## Project Structure

```
├── evo/                            EVO framework (this branch's core)
│   ├── README.md                   Framework overview + paper mapping
│   ├── spec.md                     M-MDP formalization (all paper equations)
│   ├── config.yaml                 Hyperparameters + operator_queue
│   ├── agents/                     8 roles (6 EVO-specific + developer + reviewer)
│   ├── memory/                     bank.jsonl, q_values.json, stats.json, seed/, start_points/
│   ├── state/                      campaign.json + episodes/{op}/
│   ├── docs/                       Algorithm details (stage1, stage2, multi-gate, q-value)
│   └── benchmark/                  MultiKernelBench evaluation
│
├── scoring/                        Shared scoring pipeline (AVO + EVO)
│   ├── score.sh                    9-step orchestrator (exit codes 0-6)
│   ├── compile.sh / deploy.sh / build_pybind.sh
│   ├── test_correctness.py / test_performance.py
│   └── configs/                    Per-operator scoring configs
│
├── workspace/                      Shared workspace
│   ├── specs/                      Operator specifications
│   ├── templates/                  CppExtension + reference templates
│   ├── runs/{op_name}/test/        PyTorch reference + Python binding
│   └── deploy/opp/                 OPP deployment directory
│
├── Knowledge-base/                 Shared domain knowledge (88K+ files)
├── .claude/skills/                 16 Ascend C skills (auto-loaded)
├── EVO-paper/                      EvoKernel paper sources
├── CLAUDE.md                       Claude Code project instructions
└── README.md                       (this file)
```

Runtime directories created by `scoring/score.sh`:
- `evolution/scores/v{N}.json` — per-invocation score (also read by `multigate-verifier`)
- `evolution/logs/step_{N}/*.log` — per-phase build/deploy/correctness logs

## Quick Start

### Prerequisites

- Huawei CANN toolkit at `/usr/local/Ascend/ascend-toolkit/`
- Ascend NPU device available
- Python 3.8+ with PyTorch and `torch_npu`
- CMake

### Launch an EVO campaign

```bash
source /usr/local/Ascend/ascend-toolkit/set_env.sh

# One-shot
claude --print -p "读 evo/README.md 和 evo/config.yaml，派发 evo/agents/campaign-orchestrator/AGENT.md 开始 EVO campaign"

# Interactive (more stable)
claude
> 读取 evo/agents/AGENTS.md 作为团队协议，然后按 evo/config.yaml 的 operator_queue 依次派发 campaign-orchestrator
```

### Score a single candidate

```bash
bash scoring/score.sh workspace/runs/{op_name}/attempts/step_0 scoring/configs/{op_name}.json
```

Exit codes: `0` complete success · `1` environment · `2` compile · `3` deploy · `4` pybind · `5` correctness · `6` performance.

## Correctness Thresholds

Defaults (from `scoring/test_correctness.py`, per-config overridable):

| dtype | rtol | atol |
|-------|------|------|
| FP32  | 1e-5 | 1e-5 |
| FP16  | 1e-3 | 1e-3 |
| BF16  | 1e-2 | 1e-2 |

Paper §4.1 uses `atol=rtol=1e-2`; EVO config defaults to paper settings.

## Supported Hardware

| Codename | Chip | Architecture |
|----------|------|-------------|
| A2 | Ascend 910 | arch32 (DAV_1001) |
| A3 | Ascend 910B / 310P | arch32 (DAV_2201/3002) |
| A5 | Ascend 950 | arch35 (DAV_3510) — Regbase, SIMT, FP8 |

## References

- **EvoKernel paper**: `./EVO-paper/main.tex`
- **EVO framework overview**: `./evo/README.md`
- **Formal spec (M-MDP + proofs)**: `./evo/spec.md`
- **Paper → repo mapping**: `./evo/docs/paper-mapping.md`
- **AVO framework** (separate, single-operator): see `main` branch

## Branch Layout

```bash
git checkout main   # AVO framework (Architect + Developer + Reviewer + Tester + Supervisor + Reporter)
git checkout EVO    # this branch — EVO framework (campaign-orchestrator + 2 stages + retrieval + memory + verifier)
```
