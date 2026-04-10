# AscendC Kernel Agent

Autonomous Ascend C operator generation and evolutionary optimization system for Huawei Ascend NPUs.

Inspired by **AVO (Agentic Variation Operators)**, the system uses an **Agent Team** to iteratively generate, evaluate, and evolve high-performance Ascend C custom operator projects — producing full engineering artifacts (op_host, op_kernel, CppExtension) that integrate with the PyTorch framework.

**Core formula:** `Vary(P_t) = Agent(P_t, K, f)`

| Symbol | Meaning |
|--------|---------|
| **P_t** | Version lineage — all committed operator versions and their scores |
| **K** | Domain knowledge base — 16 skills, 88K+ source files, API docs |
| **f** | Scoring function — correctness + performance (`scoring/score.sh`) |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              Architect Agent (主 Agent)               │
│           驱动进化循环，编排 Agent Team                │
│                                                       │
│  ┌───────────┐  ┌──────────┐  ┌─────────────────┐   │
│  │ Developer  │  │ Reviewer │  │    Tester        │   │
│  │            │  │          │  │                   │   │
│  │ op_host/   │  │ 7 维评分  │  │ 构建→部署→PyTorch │   │
│  │ op_kernel/ │  │ 独立验证  │  │ 正确性+性能      │   │
│  └───────────┘  └──────────┘  └─────────────────┘   │
│                                                       │
│  ┌─────────────────────────────────────────────────┐ │
│  │              Knowledge Base (K)                   │ │
│  │  16 Skills + 88K+ source files + API docs        │ │
│  └─────────────────────────────────────────────────┘ │
│                                                       │
│  git commit (on improvement) ←── scoring/score.sh    │
└─────────────────────────────────────────────────────┘
                        │
      ┌─────────────────▼─────────────────┐
      │  Supervisor Agent（仅在停滞时介入） │
      │  分析进化轨迹 → 生成重定向指令      │
      └───────────────────────────────────┘
```

The **Architect Agent** orchestrates the evolution loop:
1. Analyzes current state and profiling data
2. Designs optimization approach (DESIGN.md + PLAN.md)
3. Dispatches Developer to implement code changes
4. Dispatches Reviewer for quality verification
5. Dispatches Tester to build, deploy, and test via PyTorch framework
6. If the candidate passes correctness and improves performance → commit + promote to `best/`
7. Loops until stop condition

The **Supervisor Agent** only intervenes during stagnation (non-interfering, per AVO paper principles).

## Project Structure

```
├── agents/                            # Agent Team definitions
│   ├── AGENTS.md                      # Team orchestration entry point
│   ├── architect/                     # Main Agent: design + dispatch
│   ├── developer/                     # Code implementation
│   ├── reviewer/                      # Code review (7-dimension scoring)
│   ├── tester/                        # Build → Deploy → PyTorch testing
│   └── supervisor/                    # Non-interfering evolution oversight
├── scoring/                           # Scoring pipeline
│   ├── score.sh                       # 9-step orchestrator
│   ├── compile.sh                     # Custom operator project build
│   ├── deploy.sh                      # .run package deployment
│   ├── build_pybind.sh               # CppExtension Python binding
│   ├── test_correctness.py           # PyTorch framework correctness
│   ├── test_performance.py           # NPU Event-based timing
│   ├── compute_score.py              # Score aggregation
│   └── configs/                       # Per-operator scoring configs
├── evolution/
│   ├── config.yaml                    # Evolution parameters
│   ├── state.json                     # Persistent state (runtime)
│   ├── scores/                        # Per-version score JSONs
│   └── redirects/                     # Supervisor redirect directives
├── workspace/
│   ├── specs/                         # Operator specifications
│   ├── templates/                     # CppExtension + reference templates
│   ├── runs/{op_name}/
│   │   ├── best/                      # Current best (read-only baseline)
│   │   │   └── {OpName}Custom/        # Custom operator project
│   │   ├── attempts/step_{N}/         # Candidate workspaces
│   │   └── test/                      # PyTorch test infrastructure
│   └── deploy/opp/                    # Operator deployment directory
├── Knowledge-base/
│   └── coding-sources/                # 88K+ reference implementations & API docs
├── .claude/skills/                    # 16 structured domain skills
├── AVO-paper/                         # Reference paper
├── spec.md                            # Full technical specification
└── CLAUDE.md                          # Agent knowledge index
```

## Custom Operator Projects

The system generates **full custom operator engineering projects** (not simple kernel direct invocations):

```
{OpName}Custom/
├── {op_name}_custom.json      — Operator definition (inputs/outputs/types)
├── build.sh                    — Build orchestrator
├── op_host/                    — Host side (OpDef + TilingFunc + InferShape)
├── op_kernel/                  — Device side (AscendC Kernel)
└── build_out/
    └── custom_opp_*.run        — Self-extracting deployment package
```

Testing is done through the **PyTorch framework**:
1. Build operator project → deploy → build CppExtension Python binding
2. Compare `Model` (PyTorch native) vs `ModelNew` (custom operator) with `torch.allclose`
3. Measure performance via NPU Event timing

## Scoring Pipeline

The scoring system (`scoring/score.sh`) uses a **tiered early-exit** strategy:

```
Build → Deploy → Python Bind → Smoke Correctness → Representative Correctness
    → Representative Performance → [Stress Correctness + Performance]
```

- **Build/Deploy/Bind failure** → score 0, early exit
- **Smoke correctness failure** → early exit
- **Performance** → compared against current best; must exceed `min_improvement_ratio` (default 2%) to trigger stress tests
- **Stress tests** → only run when candidate looks promising

### Correctness Thresholds

| dtype | rtol | atol |
|-------|------|------|
| FP32  | 1e-5 | 1e-5 |
| FP16  | 1e-3 | 1e-3 |
| BF16  | 1e-2 | 1e-2 |

## Knowledge Base

Three-layer architecture for efficient knowledge retrieval:

| Layer | Content | Access |
|-------|---------|--------|
| **L1** | `CLAUDE.md` — global index (<4K tokens) | Auto-loaded every session |
| **L2** | 16 Skills — structured domain knowledge | On-demand file read |
| **L3** | 88K+ source files — reference implementations, API docs | Grep/Glob search |

## Supported Hardware

| Codename | Chip | Architecture | Key Features |
|----------|------|-------------|--------------|
| A2 | Ascend 910 | arch32 (DAV_1001) | — |
| A3 | Ascend 910B / 310P | arch32 (DAV_2201/3002) | Production target |
| A5 | Ascend 950 | arch35 (DAV_3510) | Regbase, SIMT, FP8 |

## Quick Start

### Prerequisites

- Huawei CANN toolkit installed (`/usr/local/Ascend/ascend-toolkit/`)
- Ascend NPU device available
- Python 3.8+ with PyTorch and torch_npu
- CMake

### Run the evolution loop

```bash
# Configure your operator in evolution/config.yaml, then:
claude --print -p "读取 agents/AGENTS.md 和 evolution/config.yaml，开始执行进化循环"
```

### Score a single candidate

```bash
bash scoring/score.sh workspace/runs/{op_name}/attempts/step_0 scoring/configs/default.json
```

### Build and test an operator manually

```bash
# Build custom operator project
cd workspace/runs/{op_name}/attempts/step_0/{OpName}Custom
./build.sh

# Deploy
cd build_out && ./custom_opp_*.run

# Build Python binding
cd workspace/runs/{op_name}/test/CppExtension
bash build_and_run.sh

# Test correctness
python3 scoring/test_correctness.py \
    --reference workspace/runs/{op_name}/test/reference.py \
    --config scoring/configs/default.json \
    --output result.json
```

## Configuration

Key parameters in `evolution/config.yaml`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `project_mode` | custom_operator | Project type (custom_operator / direct_invoke) |
| `max_wall_time` | 168h (7 days) | Maximum evolution runtime |
| `max_versions` | 100 | Maximum committed versions |
| `max_session_duration` | 15m | Per-session agent time limit |
| `stall_threshold` | 5 | Consecutive no-improvement rounds before redirect |
| `min_improvement_ratio` | 0.02 | Minimum 2% performance gain to commit |
| `warmup_rounds` | 10 | Performance test warmup rounds |
| `repeat_rounds` | 100 | Performance test measurement rounds |

## References

- AVO paper: `./AVO-paper/`
- Technical specification: `./spec.md`
- Agent knowledge index: `./CLAUDE.md`
- Agent Team definition: `./agents/AGENTS.md`
