# AscendC Kernel Agent — 技术规格文档

## 1. 项目概述

### 1.1 目标

构建一个面向华为 Ascend NPU 的 **Ascend C 算子自动化生成与自我进化系统**。系统能够：
- 根据算子规格（数学公式、形状、数据类型、目标芯片）自动生成**完整的自定义算子工程**
- 通过 Agent Team 协作，完成从设计、编码、审查到测试的全流程
- 在持续的 **Edit-Review-Test** 循环中自主优化算子性能
- 通过 PyTorch 框架验证算子正确性和性能

### 1.2 核心理念

借鉴 **AVO（Agentic Variation Operators）论文**（`./AVO-paper/`），核心公式为：

```
Vary(P_t) = Agent(P_t, K, f)
```

其中：
- **P_t**：历史版本谱系（所有已提交的算子版本及其评分）
- **K**：领域知识库（Ascend C 编程指南、API 文档、架构规格、参考实现）
- **f**：评分函数（正确性 + 性能）

关键设计决策：**采用 Agent Team 架构**，由 5 个角色协作完成进化循环：
- **Architect Agent**（主 Agent）驱动流程
- **Developer / Reviewer / Tester** 分别负责编码、审查、测试
- **Supervisor Agent** 仅在停滞时非干预式介入

### 1.3 与 AVO 论文的关键差异

| 维度 | AVO（CUDA/NVIDIA） | 本项目（Ascend C/NPU） |
|------|---------------------|------------------------|
| 目标硬件 | NVIDIA B200 (Blackwell) | Ascend 910B/950 |
| 编程语言 | CUDA + PTX | Ascend C (.cpp) |
| 算子工程 | 单文件 Kernel | 完整自定义算子工程（op_host + op_kernel） |
| 内存层级 | Global → L2 → L1 → Registers | GM → L2 → L1 → L0A/L0B/L0C → UB |
| 计算单元 | CUDA Cores / Tensor Cores | Vector / Cube / Scalar |
| 编译工具链 | nvcc / CUDA 13.1 | CANN (msopgen + cmake + build.sh) |
| 性能采集 | nsight / custom scripts | msprof op / NPU Event timing |
| 测试方式 | Golden 数据对比 | PyTorch 框架测试（Model vs ModelNew） |
| 知识库 | CUDA guides, PTX ISA, FA4 源码 | Ascend C Skills (16个), 88K+ 源文件 |
| Agent 模式 | 单一自主 Agent | 5-Agent Team 协作 |
| Supervisor | 不干预，仅在停滞时介入 | 同 AVO |

---

## 2. Agent Team 架构

### 2.1 角色定义

| Agent | 定义文件 | 职责 | 模式 |
|-------|---------|------|------|
| **Architect** | `agents/architect/AGENT.md` | 主 Agent：需求分析、架构设计、任务分发、进化编排 | primary |
| **Developer** | `agents/developer/AGENT.md` | 代码编写：op_host / op_kernel / tiling 实现 | subagent |
| **Reviewer** | `agents/reviewer/AGENT.md` | 代码审查：7 维质量评分、独立构建验证 | subagent |
| **Tester** | `agents/tester/AGENT.md` | 测试验证：构建 → 部署 → PyTorch 框架测试 | subagent |
| **Supervisor** | `agents/supervisor/AGENT.md` | 进化监督：仅在停滞时生成重定向指令 | 条件触发 |

团队编排入口：`agents/AGENTS.md`

### 2.2 协作流程

```
Architect Agent 主循环:
  1. READ STATE    — 读取 evolution/state.json 和最新评分
  2. ANALYZE       — 分析谱系、profiling、停滞信号
  3. DESIGN        — 输出 DESIGN.md + PLAN.md
  4. DISPATCH DEV  — 启动 Developer 实现代码
  5. DISPATCH REV  — 启动 Reviewer 审查（通过/修复循环，最多 3 轮）
  6. DISPATCH TEST — 启动 Tester 构建/部署/测试（或直接运行 score.sh）
  7. EVALUATE      — 分析结果，决定接受/拒绝
  8. UPDATE STATE  — 更新 state.json，若接受则晋升 best/
  9. GOTO 1

Supervisor Agent（仅在停滞时触发）:
  - stall_counter >= threshold → 生成重定向指令
  - failed_attempts >= threshold → 诊断失败模式
  → 写入 evolution/redirects/step_{N}.md
  → Architect 在下轮 ANALYZE 中读取并采纳
```

### 2.3 Prompt 模板

| Agent | 模板文件 | 用途 |
|-------|---------|------|
| Architect | `agents/architect/prompts/seed-design.md` | v0 种子设计 |
| Architect | `agents/architect/prompts/optimize-design.md` | 优化方案设计 |
| Developer | `agents/developer/prompts/seed-implementation.md` | v0 种子实现 |
| Developer | `agents/developer/prompts/optimize-implementation.md` | 优化实现 |
| Developer | `agents/developer/prompts/repair-implementation.md` | 回归修复 |
| Tester | `agents/tester/prompts/test-plan.md` | 测试计划 |

### 2.4 工作模式

Agent Team 根据谱系状态自动选择工作模式：

| 模式 | 触发条件 | 行为 |
|------|---------|------|
| A: 种子生成 | `current_version < 0` | Architect 设计 → Developer 从零实现 v0 |
| B: 结构优化 | v1-v10，明显结构瓶颈 | Architect 分析 profiling → Developer 大范围重构 |
| C: 微架构调优 | v10+，结构已优化 | Architect 精细分析 → Developer 局部优化 |
| D: 回归修复 | 正确性失败 | Architect 诊断 → Developer 修复 → Reviewer 验证 |

### 2.5 提交准则

候选版本必须同时满足：
1. **正确性门槛**：`correctness_total = 1.0`（全配置通过，不可妥协）
2. **性能门槛**：主性能指标优于当前 best，且超过最小改进阈值（默认 2%）

不满足条件的版本永不提交。`correctness_total < 1.0` 的版本评分为 0。

---

## 3. 自定义算子工程

### 3.1 工程结构

本系统生成的是**完整的自定义算子工程**，而非 Kernel 直调：

```
{OpName}Custom/
├── {op_name}_custom.json          — 算子定义 JSON（输入/输出/类型/格式）
├── CMakeLists.txt                  — 根构建配置
├── CMakePresets.json               — 构建预设（芯片型号/路径）
├── build.sh                        — 构建编排脚本
├── op_host/                        — Host 侧
│   ├── CMakeLists.txt
│   ├── {op_name}_custom.cpp       — OpDef 注册 + TilingFunc + InferShape
│   └── {op_name}_custom_tiling.h  — TilingData 结构定义
├── op_kernel/                      — Device 侧
│   ├── CMakeLists.txt
│   └── {op_name}_custom.cpp       — AscendC Kernel 实现
└── build_out/                      — 构建产物
    ├── custom_opp_*.run            — 自安装部署包
    └── op_api/lib/libcust_opapi.so — 算子 API 库
```

### 3.2 算子定义 JSON

```json
[{
    "op": "{OpName}Custom",
    "language": "cpp",
    "input_desc": [
        {"name": "x", "param_type": "required", "format": ["ND"], "type": ["float", "float16"]}
    ],
    "output_desc": [
        {"name": "z", "param_type": "required", "format": ["ND"], "type": ["float", "float16"]}
    ]
}]
```

### 3.3 op_host: 算子注册 + Tiling

Host 侧包含三部分：
- **TilingData**：传递给 Kernel 的 tiling 参数结构
- **TilingFunc**：根据输入 shape 计算 blockDim、tileLength 等
- **OpDef**：算子注册（输入/输出 + InferShape + InferDataType + TilingFunc 绑定）

### 3.4 op_kernel: AscendC Kernel

标准三段式 Pipeline：

```cpp
#include "kernel_operator.h"

class KernelOp {
    __aicore__ inline void Init(GM_ADDR ..., GM_ADDR workspace, GM_ADDR tiling) {
        GET_TILING_DATA(tiling_data, tiling);
        // UB Buffer 分配
    }
    __aicore__ inline void Process() {
        for (int32_t i = 0; i < loopCount; i++) {
            CopyIn(i);    // GM → UB
            Compute(i);   // UB 上计算
            CopyOut(i);   // UB → GM
        }
    }
};

extern "C" __global__ __aicore__ void op_name_custom(
    GM_ADDR x, GM_ADDR z, GM_ADDR workspace, GM_ADDR tiling) {
    KernelOp op;
    op.Init(x, z, workspace, tiling);
    op.Process();
}
```

### 3.5 构建与部署流程

```
1. msopgen gen -i {op}_custom.json -c ai_core-{chip} -lan cpp -out {OpName}Custom
2. cd {OpName}Custom && ./build.sh → build_out/custom_opp_*.run
3. ./custom_opp_*.run → 部署到 OPP 目录
4. CppExtension: setup.py → custom_ops_lib.whl → pip install
5. Python: import custom_ops_lib → 通过 PyTorch 调用
```

---

## 4. 测试与评分（评分函数 f）

### 4.1 测试方式

**主测试路径：PyTorch 框架测试（参考 MultiKernelBench）**
- 通过 CppExtension 将自定义算子绑定为 Python 模块
- Model（PyTorch 原生实现）vs ModelNew（自定义算子实现）
- `torch.allclose(ref_output, new_output, atol, rtol)` 验证正确性
- NPU Event timing 测量性能

**兼容测试路径：Golden 数据测试**
- `gen_golden.py` 生成 NumPy 参考数据
- 运行可执行文件，对比 .bin 输出 vs golden
- 适用于无 PyTorch 环境的场景

### 4.2 评分函数设计

```
f(x) = (correctness_total, performance_total)
```

#### 正确性评分

| dtype | rtol | atol |
|-------|------|------|
| FP32 | 1e-5 | 1e-5 |
| FP16 | 1e-3 | 1e-3 |
| BF16 | 1e-2 | 1e-2 |

```
correctness_total(x) = passed_configs / total_configs
```

**硬性要求：`correctness_total = 1.0`（全部配置通过）才允许提交。**

#### 性能评分

| 算子类别 | 主指标 | 说明 |
|----------|--------|------|
| MatMul / Attention 等算力密集型 | TFLOPS | 有效 FLOPs / duration |
| Elementwise / Transpose / 数据搬移型 | latency_us | 越低越好 |
| Reduce / Norm 类 | latency_us | FLOPs 定义不稳定时以时延为主 |

### 4.3 测试配置矩阵

测试分**三级**执行，逐级递进：

| 级别 | 目标 | 运行时机 |
|------|------|---------|
| `smoke` | 小 shape，快速发现编译和基础功能错误 | 每轮必跑 |
| `representative` | 典型 shape，判断是否具备实际优化价值 | smoke 通过后 |
| `stress` | 极限 shape / 边界 case，提交前最终验证 | 仅候选达到提交门槛时 |

### 4.4 评分脚本集

| 脚本 | 功能 | 说明 |
|------|------|------|
| `score.sh` | 总编排（9 步流程） | 构建 → 部署 → 绑定 → 分级测试 → 聚合 |
| `compile.sh` | 构建自定义算子工程 | msopgen + build.sh，兼容 cmake 直接构建 |
| `deploy.sh` | 部署算子包 | 执行 custom_opp_*.run |
| `build_pybind.sh` | 构建 Python 绑定 | CppExtension → custom_ops_lib wheel |
| `test_correctness.py` | PyTorch 框架正确性测试 | Model vs ModelNew + torch.allclose |
| `test_performance.py` | NPU Event 性能测试 | warmup + 多轮测量 |
| `test_correctness.sh` | 正确性测试 shell 封装 | 优先 PyTorch 模式，兼容 golden 模式 |
| `test_performance.sh` | 性能测试 shell 封装 | 优先 NPU Event，兼容 msprof |
| `gen_golden.py` | golden 参考生成（兼容） | NumPy 参考实现 |
| `verify_correctness.py` | 输出对比（兼容） | allclose + 误差统计 |
| `compute_score.py` | 评分聚合 | 正确性 + 性能 → 最终 JSON |
| `perf_summary_wrapper.py` | msprof 输出解析（兼容） | 8 CSV 指标分析 |
| `env_setup.sh` | 环境初始化 | CANN + 自定义 OPP 路径 |

### 4.5 评分流程图

```
score.sh
  │
  ├── 1. compile.sh           — 构建自定义算子工程
  │     └── 失败 → score 0, exit
  │
  ├── 2. deploy.sh            — 部署算子包
  │     └── 失败 → score 0, exit
  │
  ├── 3. build_pybind.sh      — 构建 Python 绑定
  │     └── 失败 → score 0, exit
  │
  ├── 4. smoke correctness    — PyTorch 框架测试
  │     └── 失败 → early exit
  │
  ├── 5. representative correctness
  │     └── 失败 → early exit
  │
  ├── 6. correctness_total < 1.0 → 结束（不进入性能测试）
  │
  ├── 7. representative performance — NPU Event timing
  │     └── 计算 improvement_over_best
  │
  ├── 8. 若满足提交门槛 → stress correctness + performance
  │
  └── 9. compute_score.py → 聚合为最终 JSON
```

### 4.6 评分输出格式

```json
{
  "version": "v23",
  "timestamp": "2026-04-08T15:30:00Z",
  "git_commit": "abc1234",
  "metric_type": "latency_us",
  "correctness_total": 1.0,
  "performance_total": 142.3,
  "improvement_over_best": "+3.2%",
  "test_levels_run": ["smoke", "representative", "stress"],
  "test_method": "pytorch_framework",
  "configs": [
    {
      "name": "medium_fp32",
      "level": "representative",
      "correctness": 1,
      "max_abs_error": 1.2e-6,
      "mean_ms": 0.142,
      "task_duration_us": 142.3,
      "performance_primary": 142.3
    }
  ]
}
```

### 4.7 测试基础设施

每个算子需要以下测试文件：

```
workspace/runs/{op_name}/test/
├── CppExtension/                   — Python 绑定构建
│   ├── setup.py                    — NpuExtension 配置
│   ├── build_and_run.sh            — 构建安装脚本
│   └── csrc/
│       ├── op.cpp                  — 算子绑定（EXEC_NPU_CMD）
│       └── pytorch_npu_helper.hpp  — NPU 辅助工具
└── reference.py                    — Model + ModelNew + get_inputs
```

模板位于 `workspace/templates/`，Developer 在 v0 种子实现时创建。

### 4.8 性能基准线

| 指标 | 优秀 | 可改进 | 瓶颈 |
|------|------|--------|------|
| Task Duration vs 理论值 | <20% gap | 20-50% gap | >50% gap |
| 多核负载均衡 | <10% 方差 | 10-30% 方差 | >30% 方差 |
| Double Buffer 重叠率 | >30% | 10-30% | <10% |
| Bank Conflict | <5% 总量 | 5-15% | >15% |

---

## 5. Supervisor Agent

### 5.1 核心设计

**Supervisor 是非干预式 LLM Agent**（非 Python 脚本）。

按 AVO 论文原则：
> "The supervisor maintained forward progress by intervening during periods of stagnation."

Supervisor 不控制 Architect 的日常决策，仅在检测到停滞时被激活，提供方向性重定向指令。

### 5.2 激活条件

| 信号 | 含义 | 默认阈值 |
|------|------|---------|
| `stall_counter >= stall_threshold` | 连续正确但无性能提升 | 5 |
| `failed_attempts >= max_failed_attempts` | 连续编译/正确性/超时失败 | 5 |
| `consecutive_redirects >= max_consecutive_redirects` | 连续重定向后仍无提升 → 停止 | 3 |

**计数器规则：**
- `stall_counter`：正确但未提升时 +1；性能提升时清零
- `failed_attempts`：失败时 +1；成功提交时清零
- `consecutive_redirects`：redirect 后 +1；性能提升时清零

### 5.3 激活后行为

1. 分析进化轨迹（谱系走势、已探索方向、失败模式）
2. 生成重定向指令 → 写入 `evolution/redirects/step_{N}.md`
3. Architect 在下轮 ANALYZE 中读取并采纳

重定向指令提供**未探索的方向**，不重复已失败方向。

### 5.4 状态持久化

文件：`evolution/state.json`

```json
{
  "operator_name": "add_custom",
  "target_chip": "Ascend910B",
  "start_time": "2026-04-08T10:00:00Z",
  "current_step": 0,
  "current_version": -1,
  "best_version": -1,
  "best_score": 0.0,
  "best_commit": "",
  "stall_counter": 0,
  "failed_attempts": 0,
  "consecutive_redirects": 0,
  "total_attempts": 0,
  "lineage": []
}
```

### 5.5 停止条件

| 条件 | 默认值 | 配置项 |
|------|--------|--------|
| 最大运行时间 | 7 天 | `max_wall_time` |
| 最大提交版本数 | 100 | `max_versions` |
| 目标性能达成 | 无 | `target_performance` |
| 连续重定向失败 | 3 次 | `max_consecutive_redirects` |

### 5.6 Git 谱系管理

- 每个成功版本 commit 一次
- Tag 使用 `v{N}` 格式
- 分数和配置摘要写入 commit message 和 `evolution/scores/v{N}.json`

---

## 6. 知识库

### 6.1 三层知识架构

```
Layer 1: CLAUDE.md（全局索引，<4000 tokens，每个 Agent 会话自动加载）
    ↓ 按需引用
Layer 2: Skills（结构化领域知识，通过文件读取按需加载）
    ↓ 按需搜索
Layer 3: 88K+ 源文件（参考实现，通过 Grep/Glob 按需检索）
```

### 6.2 Skills 清单

| 分类 | Skill 名称 | 用途 |
|------|-----------|------|
| 知识库 | ascendc-tiling-design | Tiling 策略设计（归约/广播/逐元素/转换/MatMul/卷积） |
| 知识库 | ascendc-api-best-practices | API 参数限制、优化模式 |
| 知识库 | ascendc-npu-arch | 芯片架构代际 A2/A3/A5、条件编译 |
| 知识库 | ascendc-docs-search | 本地 + 在线 API 文档搜索 |
| 调试 | ascendc-precision-debug | 精度问题排查（症状→诊断→修复） |
| 调试 | ascendc-runtime-debug | 运行时错误码 161xxx/361xxx/561xxx、Kernel 挂死 |
| 测试 | ascendc-code-review | 假设检验法代码审查（7 维 100 分制） |
| 测试 | ascendc-ut-develop | 单元测试开发与覆盖增强 |
| 测试 | ascendc-st-design | 系统测试用例设计 |
| 测试 | ascendc-whitebox-design | 白盒测试用例生成 |
| 工具 | ascendc-env-check | NPU 设备查询、CANN 环境验证 |
| 工具 | ascendc-task-focus | 长任务聚焦管理 |
| 模板 | ascendc-direct-invoke-template | Kernel 直调工程骨架（参考） |
| 模板 | ascendc-registry-invoke-to-direct-invoke | aclnn 注册调用转 Kernel 直调 |
| 性能 | ops-profiling | NPU 性能采集与分析 |
| 精度 | ops-precision-standard | 精度阈值标准（按 dtype） |

### 6.3 Sources（Layer 3）

相对路径前缀：`Knowledge-base/coding-sources/`

| 分类 | 路径 | 说明 |
|------|------|------|
| Attention 算子（48个） | `ops-coding-sources/ops-transformer/attention/` | flash_attention 等 |
| NN 算子 | `ops-coding-sources/ops-nn/` | 激活、归一化、MatMul |
| Math 算子 | `ops-coding-sources/ops-math/` | 数学运算、随机数 |
| CV 算子 | `ops-coding-sources/ops-cv/` | 计算机视觉 |
| SDK 示例（100+） | `programming-coding-sources/asc-devkit/examples/` | SIMD C++/C |
| API 文档（1711 文件） | `programming-coding-sources/asc-devkit/docs/api/context/` | 权威 API 参考 |
| 编程指南（220 文件） | `programming-coding-sources/asc-devkit/docs/guide/` | 教程、最佳实践 |

---

## 7. 工作区模型

### 7.1 目录结构

```
workspace/
├── specs/
│   └── {op_name}.md                    — 算子规格文件
├── templates/                           — 项目模板
│   ├── CppExtension/                   — Python 绑定模板
│   └── reference/                      — 参考实现模板
├── runs/
│   └── {op_name}/
│       ├── best/                       — 当前最佳版本（只读基线）
│       │   └── {OpName}Custom/         — 自定义算子工程
│       ├── attempts/                   — 候选版本
│       │   └── step_{N}/              — 本轮候选（可写）
│       │       └── {OpName}Custom/
│       └── test/                       — 测试基础设施
│           ├── CppExtension/           — Python 绑定
│           └── reference.py            — PyTorch 参考实现
└── deploy/
    └── opp/                            — 算子部署目录（全局共享）
```

### 7.2 工作区约束

- Agent **不得**直接修改 `best/` 目录
- 所有编辑仅发生在 `attempts/step_{N}/`
- 只有满足提交条件时，Architect 将候选晋升为新的 `best/`
- 推理日志保存到 `evolution/logs/step_{N}.md`

---

## 8. 完整目录结构

```
AscendC-Kernel-Agent/
│
├── CLAUDE.md                              # Layer 1 全局知识索引
├── spec.md                                # 本技术规格文档
├── README.md                              # 项目简介
│
├── agents/                                # Agent Team 定义
│   ├── AGENTS.md                          # 团队编排入口
│   ├── architect/
│   │   ├── AGENT.md                       # 主 Agent 定义
│   │   └── prompts/                       # 设计 prompt 模板
│   ├── developer/
│   │   ├── AGENT.md                       # Developer 定义
│   │   └── prompts/                       # 实现 prompt 模板
│   ├── reviewer/
│   │   └── AGENT.md                       # Reviewer 定义
│   ├── tester/
│   │   ├── AGENT.md                       # Tester 定义
│   │   └── prompts/                       # 测试 prompt 模板
│   └── supervisor/
│       └── AGENT.md                       # Supervisor 定义（非干预式）
│
├── scoring/                               # 评分函数 f
│   ├── score.sh                           # 总编排（9 步）
│   ├── compile.sh                         # 构建自定义算子工程
│   ├── deploy.sh                          # 部署算子包
│   ├── build_pybind.sh                    # 构建 Python 绑定
│   ├── test_correctness.py                # PyTorch 框架正确性测试
│   ├── test_performance.py                # NPU Event 性能测试
│   ├── test_correctness.sh                # 正确性测试 shell 封装
│   ├── test_performance.sh                # 性能测试 shell 封装
│   ├── compute_score.py                   # 评分聚合
│   ├── env_setup.sh                       # 环境初始化
│   ├── gen_golden.py                      # Golden 参考生成（兼容）
│   ├── verify_correctness.py              # 输出对比（兼容）
│   ├── perf_summary_wrapper.py            # msprof 解析（兼容）
│   └── configs/
│       ├── default.json                   # Elementwise Add 配置
│       ├── attention.json                 # Attention 配置
│       ├── softmax.json                   # Softmax 配置
│       └── layernorm.json                 # LayerNorm 配置
│
├── evolution/                             # 进化状态
│   ├── config.yaml                        # 运行配置
│   ├── state.json                         # 持久化状态（运行时）
│   ├── scores/                            # 逐版本评分（运行时）
│   ├── logs/                              # 推理日志（运行时）
│   └── redirects/                         # Supervisor 重定向指令（运行时）
│
├── workspace/                             # 开发工作区
│   ├── specs/                             # 算子规格
│   ├── templates/                         # 项目模板
│   ├── runs/{op_name}/                    # 算子开发目录
│   └── deploy/opp/                        # 算子部署目录
│
├── Knowledge-base/                        # 知识库
│   └── coding-sources/                    # 88K+ 源文件
│
├── .claude/skills/                        # 16 Skills
│
└── AVO-paper/                             # 参考论文
```

---

## 9. 配置

文件：`evolution/config.yaml`

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `operator_name` | add_custom | 算子名称 |
| `target_chip` | Ascend910B | 目标芯片 |
| `project_mode` | custom_operator | 工程模式（custom_operator / direct_invoke） |
| `op_capital_name` | AddCustom | PascalCase 算子名 |
| `max_wall_time` | 168h | 最大运行时间 |
| `max_versions` | 100 | 最大提交版本数 |
| `max_session_duration` | 15m | 单次 Agent 会话时限 |
| `stall_threshold` | 5 | 停滞检测阈值 |
| `max_failed_attempts` | 5 | 连续失败阈值 |
| `min_improvement_ratio` | 0.02 | 最小提升门槛 2% |
| `metric_type` | latency_us | 性能指标类型 |
| `warmup_rounds` | 10 | 性能测试预热轮数 |
| `repeat_rounds` | 100 | 性能测试测量轮数 |
| `num_correct_trials` | 5 | PyTorch 正确性测试轮数 |

---

## 10. 启动方式

```bash
# 直接用 Claude Code 加载 Agent Team 入口
claude --print -p "读取 agents/AGENTS.md 和 evolution/config.yaml，开始执行进化循环"

# 单独评分一个候选版本
bash scoring/score.sh workspace/runs/{op_name}/attempts/step_0 scoring/configs/default.json

# 构建并测试算子
cd workspace/runs/{op_name}/attempts/step_0/{OpName}Custom
./build.sh
bash scoring/deploy.sh workspace/runs/{op_name}/attempts/step_0
bash scoring/build_pybind.sh workspace/runs/{op_name}/test/CppExtension
python3 scoring/test_correctness.py \
    --reference workspace/runs/{op_name}/test/reference.py \
    --config scoring/configs/default.json \
    --output result.json
```
