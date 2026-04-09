# AscendC Kernel Agent

Autonomous Ascend C kernel generation and evolutionary optimization system for Huawei Ascend NPUs.

Inspired by **AVO (Agentic Variation Operators)**, the system uses a single autonomous agent to iteratively generate, evaluate, and evolve high-performance Ascend C kernel code — replacing traditional multi-agent pipelines with a unified Edit-Evaluate-Diagnose loop.

**Core formula:** `Vary(P_t) = Agent(P_t, K, f)`

| Symbol | Meaning |
|--------|---------|
| **P_t** | Version lineage — all committed kernel versions and their scores |
| **K** | Domain knowledge base — 16 skills, 88K+ source files, API docs |
| **f** | Scoring function — correctness + performance (`scoring/score.sh`) |

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Supervisor                         │
│              (evolution/supervisor.py)               │
│                                                      │
│  ┌───────────┐    ┌──────────────┐    ┌───────────┐ │
│  │  Lineage   │───▶│   Kernel     │───▶│  Scoring  │ │
│  │  (P_t)     │    │  Evolution   │    │  Pipeline │ │
│  │            │◀───│  Agent       │◀───│  (f)      │ │
│  └───────────┘    └──────────────┘    └───────────┘ │
│        │                │                    │       │
│        │          ┌─────▼─────┐              │       │
│        │          │ Knowledge │              │       │
│        │          │ Base (K)  │              │       │
│        │          └───────────┘              │       │
│        │                                     │       │
│        └──── git commit (on improvement) ────┘       │
└─────────────────────────────────────────────────────┘
```

The **Supervisor** orchestrates the evolution loop:
1. Prepares context (lineage P_t + current kernel + score)
2. Launches a Kernel Evolution Agent session in an isolated candidate workspace
3. Agent autonomously edits, compiles, tests, and diagnoses
4. If the candidate passes correctness and improves performance → commit + promote to `best/`
5. Detects stalls → generates redirection directives
6. Loops until stop condition (max time / max versions / target reached)

## Project Structure

```
├── agents/
│   └── kernel-evolution-agent/    # Agent definition & prompt templates
├── evolution/
│   ├── supervisor.py              # Main evolution loop orchestrator
│   ├── config.yaml                # Evolution parameters
│   ├── scores/                    # Per-version score JSONs
│   ├── logs/                      # Per-step reasoning logs
│   └── prompts/                   # Dynamic prompt generation
├── scoring/
│   ├── score.sh                   # Tiered scoring orchestrator
│   ├── compile.sh                 # Compilation step
│   ├── gen_golden.py              # Golden reference data generation
│   ├── test_correctness.sh        # Correctness testing (smoke/rep/stress)
│   ├── test_performance.sh        # Performance benchmarking
│   ├── compute_score.py           # Score aggregation
│   └── configs/                   # Per-operator scoring configs
├── workspace/
│   ├── specs/                     # Operator specifications
│   └── runs/{op_name}/
│       ├── best/                  # Current best version (read-only baseline)
│       └── attempts/step_{N}/     # Candidate workspaces (writable)
├── Knowledge-base/
│   ├── coding-skills/skills/      # 16 structured domain skills
│   └── coding-sources/            # 88K+ reference implementations & API docs
├── AVO-paper/                     # Reference paper (NeurIPS submission)
├── spec.md                        # Full technical specification
└── CLAUDE.md                      # Agent knowledge index
```

## Scoring Pipeline

The scoring system (`scoring/score.sh`) uses a **tiered early-exit** strategy:

```
Compile → Smoke Correctness → Representative Correctness
    → Representative Performance → [Stress Correctness + Performance]
```

- **Compile failure** → score 0, early exit
- **Smoke correctness failure** → early exit with partial score
- **Representative correctness failure** → early exit
- **Performance** → compared against current best; must exceed `min_improvement_ratio` (default 2%) to trigger stress tests
- **Stress tests** → only run when the candidate looks promising, to save compute

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

Key skills include: `ascendc-tiling-design`, `ascendc-api-best-practices`, `ascendc-npu-arch`, `ascendc-precision-debug`, `ops-profiling`, and more. See `CLAUDE.md` for the full skill map.

## Supported Hardware

| Codename | Chip | Architecture | Key Features |
|----------|------|-------------|--------------|
| A2 | Ascend 910 | arch32 (DAV_1001) | — |
| A3 | Ascend 910B / 310P | arch32 (DAV_2201/3002) | Production target |
| A5 | Ascend 950 | arch35 (DAV_3510) | Regbase, SIMT, FP8 |

## Quick Start

### Prerequisites

- Huawei CANN toolkit installed
- Ascend NPU device available
- Python 3.8+
- CMake

### Run the evolution loop

```bash
# Configure your operator in evolution/config.yaml, then:
python3 evolution/supervisor.py --config evolution/config.yaml
```

### Score a single kernel

```bash
bash scoring/score.sh workspace/runs/{op_name}/best scoring/configs/{op_name}.json
```

### Build and run a kernel manually

```bash
cd workspace/runs/{op_name}/best
mkdir -p build && cd build
cmake .. -DASCEND_PRODUCT_TYPE=Ascend910B -DASCEND_RUN_MODE=ONBOARD
make -j
cd .. && bash run.sh
```

## Configuration

Key parameters in `evolution/config.yaml`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `max_wall_time` | 168h (7 days) | Maximum evolution runtime |
| `max_versions` | 100 | Maximum committed versions |
| `max_session_duration` | 30m | Per-session agent time limit |
| `stall_threshold` | 5 | Consecutive no-improvement rounds before redirect |
| `min_improvement_ratio` | 0.02 | Minimum 2% performance gain to commit |

## Key Differences from AVO (CUDA/NVIDIA)

| Dimension | AVO (CUDA) | This Project (Ascend C) |
|-----------|------------|------------------------|
| Target hardware | NVIDIA B200 (Blackwell) | Ascend 910B / 950 |
| Language | CUDA + PTX | Ascend C (.asc) |
| Memory hierarchy | Global → L2 → L1 → Registers | GM → L2 → L1 → L0A/B/C → UB |
| Compute units | CUDA / Tensor Cores | Vector / Cube / Scalar |
| Toolchain | nvcc / CUDA 13.1 | CANN (cmake + ascendc compiler) |
| Profiling | nsight | msprof |
| Knowledge base | CUDA guides, PTX ISA | 16 Skills, 88K+ source files |

## References

- AVO paper: `./AVO-paper/`
- Technical specification: `./spec.md`
- Agent knowledge index: `./CLAUDE.md`
