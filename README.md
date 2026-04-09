# AscendC Kernel Agent

中文优先 | Chinese First

面向华为 Ascend NPU 的 Ascend C 内核自动生成与进化优化系统。

An autonomous Ascend C kernel generation and evolutionary optimization system for Huawei Ascend NPUs.

项目灵感来自 **AVO（Agentic Variation Operators）**。系统使用单一自主 Agent，在统一的 Edit-Evaluate-Diagnose 循环中持续生成、评估、修复和优化 Ascend C 内核代码，而不是使用固定的多 Agent 流水线。

Inspired by **AVO (Agentic Variation Operators)**, the system uses a single autonomous agent to iteratively generate, evaluate, repair, and optimize Ascend C kernel code, instead of relying on a fixed multi-agent pipeline.

**核心公式 / Core Formula:** `Vary(P_t) = Agent(P_t, K, f)`

## 快速导航 / Quick Navigation

**中文**

- [项目概览](#项目概览--overview)
- [架构](#架构--architecture)
- [核心执行流程](#核心执行流程--execution-flow)
- [目录结构](#目录结构--project-structure)
- [评分流程](#评分流程--scoring-pipeline)
- [知识库](#知识库--knowledge-base)
- [快速开始](#快速开始--quick-start)
- [关键配置项](#关键配置项--key-configuration)
- [当前状态](#当前状态--current-status)
- [参考资料](#参考资料--references)

**English**

- [Overview](#项目概览--overview)
- [Architecture](#架构--architecture)
- [Execution Flow](#核心执行流程--execution-flow)
- [Project Structure](#目录结构--project-structure)
- [Scoring Pipeline](#评分流程--scoring-pipeline)
- [Knowledge Base](#知识库--knowledge-base)
- [Quick Start](#快速开始--quick-start)
- [Key Configuration](#关键配置项--key-configuration)
- [Current Status](#当前状态--current-status)
- [References](#参考资料--references)

| 符号 Symbol | 中文说明 | English |
|-------------|----------|---------|
| `P_t` | 版本谱系，包含所有已记录的内核版本与评分 | Version lineage, including recorded kernel versions and scores |
| `K` | 领域知识库，包含 Skills、参考实现、API 文档 | Domain knowledge base with skills, reference implementations, and API docs |
| `f` | 评分函数，负责正确性与性能评估 | Scoring function for correctness and performance |

## 项目概览 / Overview

这个项目的目标不是“一步到位自动写出最优内核”，而是先建立一个稳定、可恢复、可评估的演化闭环：

The goal is not to generate the final optimal kernel in one shot. The first objective is to build a stable, recoverable, and measurable evolution loop:

1. 输入算子规格  
   Input an operator specification
2. 生成或修改 Ascend C 内核候选版本  
   Generate or modify an Ascend C kernel candidate
3. 自动执行编译、正确性测试、性能测试  
   Automatically compile, validate correctness, and benchmark performance
4. 只有通过正确性且满足改进条件的版本才晋升为最佳版本  
   Promote a candidate to best only if it passes correctness and satisfies improvement criteria
5. 累积谱系、失败记录和优化轨迹，驱动后续搜索  
   Accumulate lineage, failure history, and optimization trajectories for future search

## 架构 / Architecture

```text
┌─────────────────────────────────────────────────────┐
│                    Supervisor                       │
│               evolution/supervisor.py               │
│                                                     │
│   ┌────────────┐   ┌────────────────┐   ┌────────┐ │
│   │  Lineage   │──▶│ Kernel Agent   │──▶│ Scoring│ │
│   │   (P_t)    │   │  Edit/Eval/    │   │  (f)   │ │
│   │            │◀──│  Diagnose Loop │◀──│        │ │
│   └────────────┘   └────────────────┘   └────────┘ │
│         │                  │                │       │
│         │            ┌─────▼─────┐          │       │
│         │            │ Knowledge │          │       │
│         │            │ Base (K)  │          │       │
│         │            └───────────┘          │       │
│         │                                   │       │
│         └──── promote + commit on success ──┘       │
└─────────────────────────────────────────────────────┘
```

**中文说明**

- `Supervisor` 负责长时运行、状态持久化、停滞检测和会话编排
- `Kernel Evolution Agent` 负责在候选工作区内自主编辑、编译、测试和诊断
- `Scoring Pipeline` 负责按分级策略执行正确性与性能评估
- `Knowledge Base` 提供 Skills、参考代码和 API 文档，支持按需检索

**English**

- The `Supervisor` handles long-running orchestration, persistent state, stall detection, and session management
- The `Kernel Evolution Agent` edits, compiles, tests, and diagnoses inside an isolated candidate workspace
- The `Scoring Pipeline` performs tiered correctness and performance evaluation
- The `Knowledge Base` provides skills, reference code, and API documentation for on-demand retrieval

## 核心执行流程 / Execution Flow

**中文**

1. Supervisor 读取当前最佳版本、谱系摘要和运行配置
2. 为本轮创建独立的 candidate 工作区
3. Agent 在 candidate 中进行 Edit-Evaluate-Diagnose 循环
4. 评分系统执行编译、正确性和性能评估
5. 若候选版本通过门槛，则晋升为新的 `best/`
6. 若连续停滞，则生成重定向指令，尝试新的优化方向

**English**

1. The Supervisor loads the current best version, lineage summary, and runtime configuration
2. It creates an isolated candidate workspace for the current round
3. The Agent runs the Edit-Evaluate-Diagnose loop inside the candidate workspace
4. The scoring system performs compilation, correctness validation, and performance benchmarking
5. If the candidate meets the acceptance criteria, it is promoted to the new `best/`
6. If the search stalls repeatedly, the Supervisor generates a redirection directive for a new optimization path

## 目录结构 / Project Structure

```text
├── agents/
│   └── kernel-evolution-agent/    # Agent definition and prompt templates
├── evolution/
│   ├── supervisor.py              # Main orchestration loop
│   ├── config.yaml                # Evolution configuration
│   ├── prompts/                   # Prompt templates for session init / redirect
│   ├── scores/                    # Per-version score JSONs
│   └── logs/                      # Per-step logs
├── scoring/
│   ├── score.sh                   # Tiered scoring entrypoint
│   ├── compile.sh                 # Build wrapper
│   ├── gen_golden.py              # Golden data generation
│   ├── test_correctness.sh        # Correctness validation
│   ├── test_performance.sh        # Performance benchmarking
│   ├── compute_score.py           # Score aggregation
│   └── configs/                   # Per-operator scoring configs
├── workspace/
│   ├── specs/                     # Operator specification files
│   └── runs/{op_name}/
│       ├── best/                  # Current best version
│       └── attempts/step_{N}/     # Candidate workspaces
├── Knowledge-base/
│   ├── coding-skills/skills/      # Structured skills and agent references
│   └── coding-sources/            # Large source corpus and docs
├── AVO-paper/                     # Reference paper
├── spec.md                        # Full technical specification
├── CLAUDE.md                      # Knowledge index
└── README.md                      # This file
```

**中文说明**

- `workspace/runs/{op_name}/best/` 是当前最佳版本，默认作为只读基线
- `workspace/runs/{op_name}/attempts/step_{N}/` 是单轮候选工作区
- `Knowledge-base/` 存放项目知识库与参考源代码

**English**

- `workspace/runs/{op_name}/best/` is the current best version and serves as the default read-only baseline
- `workspace/runs/{op_name}/attempts/step_{N}/` is the per-round candidate workspace
- `Knowledge-base/` stores the project knowledge base and reference source corpus

## 评分流程 / Scoring Pipeline

`scoring/score.sh` 采用分级、可提前退出的评分策略，用较低成本尽早过滤明显无效的候选版本。

`scoring/score.sh` uses a tiered early-exit strategy so clearly invalid candidates can be filtered out with lower cost.

```text
Compile
  → Smoke Correctness
  → Representative Correctness
  → Representative Performance
  → Stress Correctness + Stress Performance
```

**中文**

- 编译失败：立即退出，记为失败
- Smoke 正确性失败：立即退出，不进入后续性能阶段
- Representative 正确性失败：立即退出
- Representative 性能达不到最小改进阈值：不进入 Stress 阶段
- 只有看起来有希望的候选版本才执行完整 Stress 测试

**English**

- Compile failure: exit early and mark the attempt as failed
- Smoke correctness failure: exit before performance evaluation
- Representative correctness failure: exit early
- Representative performance below the minimum improvement threshold: skip stress tests
- Only promising candidates run the full stress stage

### 正确性阈值 / Correctness Thresholds

| dtype | rtol | atol |
|-------|------|------|
| FP32  | 1e-5 | 1e-5 |
| FP16  | 1e-3 | 1e-3 |
| BF16  | 1e-2 | 1e-2 |

### 评分输出 / Score Output

**中文**

评分结果会写入 `evolution/scores/`，用于：

- 判断是否可以晋升为 best
- 生成谱系摘要
- 分析停滞原因
- 支持后续人工审查

**English**

Score JSON files are written to `evolution/scores/` and are used to:

- decide whether a candidate can be promoted to best
- build lineage summaries
- analyze stall reasons
- support later manual review

## 知识库 / Knowledge Base

项目采用三层知识架构，以兼顾上下文成本和检索效率。

The project uses a three-layer knowledge architecture to balance context cost and retrieval efficiency.

| 层级 Layer | 中文 | English |
|------------|------|---------|
| L1 | `CLAUDE.md`：全局索引，面向每次会话的快速上下文 | `CLAUDE.md`: global index for fast per-session context |
| L2 | Skills：结构化领域知识，按需加载 | Skills: structured domain knowledge loaded on demand |
| L3 | Sources：参考实现、API 文档、样例代码，通过搜索访问 | Sources: reference implementations, API docs, and examples accessed via search |

**常见知识资源 / Key Resources**

- `ascendc-tiling-design`
- `ascendc-api-best-practices`
- `ascendc-npu-arch`
- `ascendc-precision-debug`
- `ascendc-runtime-debug`
- `ops-profiling`
- `ascendc-direct-invoke-template`

完整技能地图见 [CLAUDE.md](/Users/wangchao/Downloads/codex/AscendC-Kernel-Agent/CLAUDE.md)。

See [CLAUDE.md](/Users/wangchao/Downloads/codex/AscendC-Kernel-Agent/CLAUDE.md) for the full skill map.

## 支持硬件 / Supported Hardware

| 代号 Codename | 芯片 Chip | 架构 Architecture | 说明 Notes |
|---------------|-----------|-------------------|-------------|
| A2 | Ascend 910 | arch32 (DAV_1001) | 早期代际 / earlier generation |
| A3 | Ascend 910B / 310P | arch32 (DAV_2201/3002) | 当前主要目标平台 / current main target |
| A5 | Ascend 950 | arch35 (DAV_3510) | Regbase、SIMT、FP8 |

## 快速开始 / Quick Start

### 环境要求 / Prerequisites

- 已安装 Huawei CANN 工具链  
  Huawei CANN toolkit installed
- 可访问 Ascend NPU 设备  
  Access to an Ascend NPU device
- Python 3.8+  
  Python 3.8+
- CMake  
  CMake

### 启动进化循环 / Run the Evolution Loop

```bash
python3 evolution/supervisor.py --config evolution/config.yaml
```

**中文**

运行前请先根据目标算子修改：

- `evolution/config.yaml`
- `workspace/specs/{op_name}.md`
- `scoring/configs/{op_name}.json`

**English**

Before running, update:

- `evolution/config.yaml`
- `workspace/specs/{op_name}.md`
- `scoring/configs/{op_name}.json`

### 对单个内核评分 / Score a Single Kernel

```bash
bash scoring/score.sh workspace/runs/{op_name}/best scoring/configs/{op_name}.json
```

### 手动编译和运行 / Build and Run Manually

```bash
cd workspace/runs/{op_name}/best
mkdir -p build && cd build
cmake .. -DASCEND_PRODUCT_TYPE=Ascend910B -DASCEND_RUN_MODE=ONBOARD
make -j
cd .. && bash run.sh
```

## 关键配置项 / Key Configuration

`evolution/config.yaml` 中常见参数如下：

Common parameters in `evolution/config.yaml`:

| 参数 Parameter | 默认值 Default | 中文说明 | English |
|----------------|----------------|----------|---------|
| `max_wall_time` | `168h` | 最大运行时长 | Maximum wall-clock runtime |
| `max_versions` | `100` | 最大保留版本数 | Maximum committed versions |
| `max_session_duration` | `30m` | 单次 Agent 会话上限 | Per-agent-session time limit |
| `stall_threshold` | `5` | 连续无改进轮数阈值 | Consecutive no-improvement threshold |
| `max_failed_attempts` | `5` | 连续失败轮数阈值 | Consecutive failed-attempt threshold |
| `min_improvement_ratio` | `0.02` | 触发晋升的最小性能提升比例 | Minimum performance gain for promotion |

## 与 AVO 的差异 / Differences from AVO

| 维度 Dimension | AVO（CUDA） | 本项目 This Project |
|----------------|-------------|---------------------|
| 目标硬件 | NVIDIA B200 (Blackwell) | Ascend 910B / 950 |
| 编程语言 | CUDA + PTX | Ascend C (`.asc`) |
| 内存层级 | Global → L2 → L1 → Registers | GM → L2 → L1 → L0A/L0B/L0C → UB |
| 计算单元 | CUDA / Tensor Cores | Vector / Cube / Scalar |
| 工具链 | `nvcc` / CUDA 13.1 | CANN + Ascend C compiler |
| Profiling | `nsight` | `msprof` |
| 知识库 | CUDA guides, PTX ISA | Skills + large local source corpus |

## 当前状态 / Current Status

**中文**

仓库当前已经包含以下基础设施：

- `kernel-evolution-agent` 的定义与 prompt 模板
- `supervisor.py` 主循环骨架
- `scoring/` 目录下的评分脚本
- `workspace/specs/add_custom.md` 示例规格
- `workspace/runs/add_custom/` 的运行目录骨架

但这并不意味着所有路径都已经在真实 Ascend 环境中验证完成。落地前仍应优先验证：

- 构建链路是否可运行
- golden 生成是否权威可靠
- scoring config 是否与目标算子匹配
- 子模块和大知识库目录是否完整可用

**English**

The repository already contains:

- a `kernel-evolution-agent` definition and prompt templates
- the `supervisor.py` orchestration skeleton
- scoring scripts under `scoring/`
- an example operator spec at `workspace/specs/add_custom.md`
- a runtime workspace skeleton under `workspace/runs/add_custom/`

This does not mean every path has already been validated in a real Ascend environment. Before production use, you should still verify:

- whether the build pipeline works end to end
- whether golden generation is authoritative and stable
- whether the scoring config matches the target operator
- whether submodules and large knowledge-base directories are complete and usable

## 参考资料 / References

- 技术规格 / Technical specification: [spec.md](/Users/wangchao/Downloads/codex/AscendC-Kernel-Agent/spec.md)
- 知识索引 / Knowledge index: [CLAUDE.md](/Users/wangchao/Downloads/codex/AscendC-Kernel-Agent/CLAUDE.md)
- 参考论文 / Reference paper: `./AVO-paper/`
