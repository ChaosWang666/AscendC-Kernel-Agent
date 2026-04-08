# AscendC Kernel Agent — 技术规格文档

## 1. 项目概述

### 1.1 目标

构建一个面向华为 Ascend NPU 的 **Ascend C 算子自动化生成与自我进化系统**。系统能够：
- 根据算子规格（数学公式、形状、数据类型、目标芯片）自动生成 Ascend C 内核代码
- 通过持续的 **Edit-Evaluate-Diagnose** 循环自主优化内核性能
- 在多日无人干预的运行中，积累数十个经过验证的优化版本

### 1.2 核心理念

借鉴 **AVO（Agentic Variation Operators）论文**（`./AVO-paper/`），核心公式为：

```
Vary(P_t) = Agent(P_t, K, f)
```

其中：
- **P_t**：历史版本谱系（所有已提交的内核版本及其评分）
- **K**：领域知识库（Ascend C 编程指南、API 文档、架构规格、参考实现）
- **f**：评分函数（正确性 + 性能）

关键设计决策：**用单一自主 Agent 替代传统的多 Agent 流水线**。现有的 5 个 Agent（architect/developer/reviewer 等）的领域知识被保留为参考资源，但不作为固定的执行阶段。Agent 自主决定何时查阅文档、何时编写代码、何时调试、何时提交。

### 1.3 与 AVO 论文的关键差异

| 维度 | AVO（CUDA/NVIDIA） | 本项目（Ascend C/NPU） |
|------|---------------------|------------------------|
| 目标硬件 | NVIDIA B200 (Blackwell) | Ascend 910B/950 |
| 编程语言 | CUDA + PTX | Ascend C (.asc) |
| 内存层级 | Global → L2 → L1 → Registers | GM → L2 → L1 → L0A/L0B/L0C → UB |
| 计算单元 | CUDA Cores / Tensor Cores | Vector / Cube / Scalar |
| 编译工具链 | nvcc / CUDA 13.1 | CANN (cmake + ascendc编译器) |
| 性能采集 | nsight / custom scripts | msprof op |
| 知识库 | CUDA guides, PTX ISA, FA4 源码 | Ascend C Skills (16个), 88K+ 源文件 |

---

## 2. 任务一：知识库完善

### 2.1 三层知识架构

```
Layer 1: CLAUDE.md（全局索引，<4000 tokens，每个 Agent 会话自动加载）
    ↓ 按需引用
Layer 2: 16 个 Skills（结构化领域知识，通过文件读取按需加载）
    ↓ 按需搜索
Layer 3: 88K+ 源文件（参考实现，通过 Grep/Glob 按需检索）
```

### 2.2 Layer 1 — CLAUDE.md

位置：项目根目录 `/CLAUDE.md`

内容结构：

```
# AscendC Kernel Agent

## 项目概述
- 目的、架构、进化循环

## 知识库地图
### Skills（Layer 2）— 按需加载
- ascendc-tiling-design: Tiling 策略设计 [路径]
- ascendc-api-best-practices: API 使用模式和禁忌 [路径]
- ascendc-npu-arch: 芯片架构代际 A2/A3/A5 [路径]
- ascendc-precision-debug: 精度问题诊断决策树 [路径]
- ops-profiling: 8 CSV 指标、msprof 使用 [路径]
- ascendc-direct-invoke-template: 直调工程骨架 [路径]
- ascendc-docs-search: API 文档索引 [路径]
- ascendc-env-check: 环境验证 [路径]
- ascendc-code-review: 代码审查清单 [路径]
- ascendc-runtime-debug: 运行时错误码和调试 [路径]
- ascendc-ut-develop: 单元测试 [路径]
- ascendc-st-design: 系统测试 [路径]
- ascendc-whitebox-design: 白盒测试 [路径]
- ops-precision-standard: 精度阈值标准 [路径]
- ascendc-task-focus: 任务聚焦管理 [路径]
- ascendc-registry-invoke-to-direct-invoke: 注册调用转直调 [路径]

### Sources（Layer 3）— 搜索访问
- asc-devkit/docs/api/context/: API 文档（权威来源）
- asc-devkit/examples/: 100+ 工作示例
- ops-transformer/attention/: 40+ Attention 算子实现
- ops-nn/: 激活、归一化、MatMul、量化
- ops-math/: 数学和随机算子
- ops-cv/: 计算机视觉算子

## Ascend C 快速参考
- 内存层级: GM → L2 → L1 → L0A/L0B/L0C → UB → Registers
- UB 容量: A2/A3: 192KB, A5: 248KB
- 内核文件扩展名: .asc
- 内核启动: <<<blockDim, nullptr, stream>>>
- Pipeline: CopyIn(GM→UB) → Compute(UB) → CopyOut(UB→GM)
- 同步: EnQue/DeQue（管线阶段间）, PipeBarrier（粗粒度）
- Double Buffering: BUFFER_NUM = 2
- 多核: GetBlockIdx(), ACL_DEV_ATTR_* 查询核数
- 架构代号: DAV_2201(910B, arch32), DAV_3510(950, arch35)

## 编译命令
## 测试标准
## 进化流程说明
```

### 2.3 Layer 2 — 现有 Skills 清单

| 分类 | Skill 名称 | 用途 |
|------|-----------|------|
| 知识库 | ascendc-api-best-practices | API 参数限制、优化模式（Adds/Muls、Double Buffer 等） |
| 知识库 | ascendc-npu-arch | 芯片型号、架构特性、条件编译 |
| 知识库 | ascendc-docs-search | 本地+在线 API 文档搜索 |
| 知识库 | ascendc-tiling-design | 算子分类（归约/广播/逐元素/转换/MatMul/卷积）的 Tiling 方法论 |
| 调试 | ascendc-precision-debug | 精度问题排查（症状→诊断→修复） |
| 调试 | ascendc-runtime-debug | 运行时错误码（161xxx/361xxx/561xxx）和 Kernel 挂死诊断 |
| 测试 | ascendc-ut-develop | 单元测试开发与覆盖增强 |
| 测试 | ascendc-st-design | 系统测试用例设计 |
| 测试 | ascendc-code-review | 假设检验法代码审查 |
| 测试 | ascendc-whitebox-design | 白盒测试用例生成 |
| 工具 | ascendc-env-check | NPU 设备查询、CANN 环境验证 |
| 工具 | ascendc-task-focus | 长任务聚焦管理 |
| 模板 | ascendc-registry-invoke-to-direct-invoke | aclnn 注册调用转 Kernel 直调 |
| 模板 | ascendc-direct-invoke-template | Kernel 直调工程骨架（含验证示例） |
| 性能 | ops-profiling | NPU 性能采集与分析（8 CSV 指标） |
| 精度 | ops-precision-standard | 算子精度标准（按 dtype 的 atol/rtol） |

### 2.4 导航索引文件

创建 3 个索引文件辅助 Agent 快速定位参考代码：

- `Knowledage-base/INDEX-attention-ops.md`：40+ Attention 算子目录（名称、路径、关键模式）
- `Knowledage-base/INDEX-api-reference.md`：API 文档按类别索引（算术/归约/数据搬移/缓冲管理/精度转换/同步/比较）
- `Knowledage-base/INDEX-examples.md`：asc-devkit 示例目录（难度级别、演示的模式）

### 2.5 交付物

| 文件 | 说明 |
|------|------|
| `CLAUDE.md` | 项目根目录全局知识索引 |
| `Knowledage-base/INDEX-attention-ops.md` | Attention 算子导航 |
| `Knowledage-base/INDEX-api-reference.md` | API 文档导航 |
| `Knowledage-base/INDEX-examples.md` | 示例代码导航 |

---

## 3. 任务二：代码生成 Agent（Kernel Evolution Agent）

### 3.1 核心设计决策

**采用 AVO 的统一 Agent 模式**，而非现有的 5-Agent 流水线（architect → developer → reviewer）。

理由（来自 AVO 论文）：
- 固定流水线限制了 Agent 的自主探索能力
- 单一 Agent 可以灵活地在设计、编码、调试、优化之间切换
- Agent 自主决定何时查阅文档、何时重构、何时回退

现有 5 个 Agent 的领域知识被保留为 **知识资源**：
- **kernel-architect** 的设计流程 → 种子生成策略
- **kernel-developer** 的渐进开发策略 → 编译调试方法
- **kernel-reviewer** 的 7 维评分体系（100分制）→ 辅助质量信号
- **ops-reviewer** 的代码审查清单 → 提交前自检

### 3.2 Agent 定义

文件：`agents/kernel-evolution-agent/AGENT.md`

```yaml
---
name: kernel-evolution-agent
description: 自主 Ascend C 内核优化 Agent。实现 AVO 变异算子：
  读取谱系、查阅知识库、提出/实现编辑、编译、测试、诊断、提交改进版本。
mode: subagent
skills:
  - ascendc-tiling-design
  - ascendc-api-best-practices
  - ascendc-npu-arch
  - ascendc-precision-debug
  - ops-profiling
  - ascendc-direct-invoke-template
  - ascendc-docs-search
  - ascendc-runtime-debug
  - ascendc-code-review
permission:
  edit: allow
  bash: allow
  read: allow
  write: allow
  glob: allow
---
```

### 3.3 输入/输出接口

**输入：**
| 参数 | 说明 | 来源 |
|------|------|------|
| `operator_spec` | 算子规格（数学公式、输入输出形状、dtype、目标芯片） | 用户定义 |
| `current_kernel` | 当前最优内核源码 x_t | `workspace/ops/{op_name}/{op_name}.asc` |
| `current_score` | 当前评分 f(x_t) | `evolution/scores/v{N}.json` |
| `lineage_summary` | 谱系摘要：(版本号, 评分, 一句话描述) 列表 | `evolution/state.json` |
| `directive` | （可选）Supervisor 优化指令 | Supervisor 停滞干预时提供 |

**输出：**
| 产物 | 说明 | 位置 |
|------|------|------|
| 内核代码 | 新版本 x_{t+1} | `workspace/ops/{op_name}/{op_name}.asc` |
| 编译状态 | pass/fail + 错误日志 | Agent 日志 |
| 测试结果 | 正确性 + 性能 | `evolution/scores/v{N+1}.json` |
| Git commit | 若通过正确性测试 | git log |
| 推理日志 | 尝试了什么、失败了什么、成功了什么 | `evolution/logs/step_{N}.md` |

### 3.4 工作模式

Agent 根据谱系状态自主选择工作模式：

#### 模式 A：种子生成（v0）
- 触发条件：无历史版本
- 流程：
  1. 解析算子规格（数学公式 → 计算模式分类）
  2. 加载 `ascendc-tiling-design` 选择 Tiling 策略（AR/ARA/Elementwise/...）
  3. 加载 `ascendc-direct-invoke-template` 创建工程骨架
  4. 加载 `ascendc-api-best-practices` 选择正确的 API
  5. 实现基础内核代码
  6. 编译 + 正确性测试 → 首个可工作版本

#### 模式 B：结构优化（早期版本 v1-v10）
- 触发条件：已有基础版本，profiling 显示明显结构性瓶颈
- 流程：
  1. 分析 profiling 数据，识别粗粒度瓶颈（Tiling 不合理、Pipeline 利用率低、多核负载不均）
  2. 搜索 `ops-transformer/attention/` 或类似参考实现，寻找结构灵感
  3. 实施大范围重构（改 Tiling 策略、加 Double Buffer、重组 Pipeline 阶段）
  4. 编译 + 测试 + 对比性能

#### 模式 C：微架构调优（后期版本 v10+）
- 触发条件：结构已优化，profiling 显示细粒度瓶颈
- 流程：
  1. 分析 8 CSV profiling 指标，定位具体瓶颈：
     - VEC ratio 高 → 向量计算密集，考虑利用 Cube 单元
     - MTE2 ratio 高 → 数据搬移密集，考虑更好的数据复用
     - Bank conflict 多 → 调整 UB 内存布局
     - Pipeline bubble 大 → 调整 EnQue/DeQue 时机
  2. 查阅 `ascendc-npu-arch` 了解硬件约束
  3. 实施精确的局部优化
  4. 编译 + 测试 + 对比

#### 模式 D：回归修复
- 触发条件：优化尝试导致正确性失败
- 流程：
  1. 加载 `ascendc-precision-debug` 诊断决策树
  2. 对比失败输出 vs golden，分析误差模式
  3. 常见原因检查：Pipeline 同步缺失、DataCopy 对齐、FP16 精度溢出、Cast RoundMode 错误
  4. 修复并重新测试

### 3.5 Edit-Evaluate-Diagnose 循环

```
┌─────────────────────────────────────────┐
│              ANALYZE                     │
│  读取 x_t, f(x_t), P_t                  │
│  识别最有希望的优化方向                    │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│              CONSULT                     │
│  按需加载 Skills / 搜索 Sources          │
│  - Tiling 变更 → ascendc-tiling-design   │
│  - API 问题 → ascendc-api-best-practices │
│  - 硬件约束 → ascendc-npu-arch           │
│  - Profiling → ops-profiling             │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│               EDIT                       │
│  实现优化编辑                             │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│             COMPILE                      │
│  cmake + make                            │
│  失败 → 诊断编译错误 → 回到 EDIT         │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│         TEST CORRECTNESS                 │
│  对比 golden 数据 (atol/rtol)            │
│  失败 → ascendc-precision-debug → EDIT   │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│         TEST PERFORMANCE                 │
│  msprof 采集 + 8 CSV 分析               │
│  对比 f(x_t)                             │
└──────────────┬──────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│              DECIDE                      │
│  正确 + 性能提升 → COMMIT (git)          │
│  正确 + 性能无改善 → 换方向 → ANALYZE    │
│  不正确 → 诊断修复 → EDIT                │
│  max_attempts 用尽 → 结束本轮            │
└─────────────────────────────────────────┘
```

### 3.6 Prompt 模板

| 模板文件 | 用途 |
|----------|------|
| `agents/kernel-evolution-agent/prompts/seed-generation.md` | 从算子规格生成初始 v0 |
| `agents/kernel-evolution-agent/prompts/optimize-step.md` | 单次变异步骤（含谱系上下文） |
| `agents/kernel-evolution-agent/prompts/repair-step.md` | 回归修复（含错误诊断上下文） |
| `agents/kernel-evolution-agent/templates/operator-spec.md` | 算子规格输入模板 |
| `agents/kernel-evolution-agent/templates/lineage-summary.md` | 谱系摘要格式模板 |

### 3.7 交付物

```
agents/
  kernel-evolution-agent/
    AGENT.md                    # Agent 定义
    prompts/
      seed-generation.md        # 种子生成 prompt
      optimize-step.md          # 优化步骤 prompt
      repair-step.md            # 回归修复 prompt
    templates/
      operator-spec.md          # 算子规格模板
      lineage-summary.md        # 谱系摘要模板
```

---

## 4. 任务三：编译与测试（评分函数 f）

### 4.1 评分函数设计

评分函数 `f(x)` 是连接代码生成 Agent 和进化循环的关键接口。

```
f(x) = (correctness_total, performance_total)
```

#### 正确性评分

二值判定，对比 golden 参考数据：

```
correctness(x, config_j) = 1  若 all(|output - golden| < atol) 且 all(|output - golden|/|golden| < rtol)
                          = 0  否则

精度阈值（来源：ops-precision-standard）：
  FP32: rtol=1e-5, atol=1e-5
  FP16: rtol=1e-3, atol=1e-3
  BF16: rtol=1e-2, atol=1e-2

correctness_total(x) = sum(correctness(x, config_j)) / n_configs
```

**硬性要求：`correctness_total = 1.0`（全部配置通过）才允许提交。** 这是 AVO 的核心原则——正确性不可妥协，不正确的内核评分为 0。

#### 性能评分

基于 msprof 采集的 Task Duration，换算为吞吐量：

```
performance(x, config_j) = compute_flops(config_j) / task_duration_seconds(x, config_j)

performance_total(x) = geometric_mean(performance(x, config_j) for j in all_configs)
```

使用几何平均而非算术平均，确保所有配置均衡优化。

### 4.2 测试配置矩阵

每个算子类型对应一组 JSON 测试配置：

**Attention 算子示例：**
```json
{
  "operator": "flash_attention_ascend",
  "configs": [
    {"batch": 8, "seq_len": 4096, "heads": 16, "dim": 128, "dtype": "bf16", "causal": true},
    {"batch": 4, "seq_len": 8192, "heads": 16, "dim": 128, "dtype": "bf16", "causal": true},
    {"batch": 2, "seq_len": 16384, "heads": 16, "dim": 128, "dtype": "bf16", "causal": true},
    {"batch": 1, "seq_len": 32768, "heads": 16, "dim": 128, "dtype": "bf16", "causal": true},
    {"batch": 8, "seq_len": 4096, "heads": 16, "dim": 128, "dtype": "bf16", "causal": false},
    {"batch": 4, "seq_len": 8192, "heads": 16, "dim": 128, "dtype": "bf16", "causal": false}
  ]
}
```

**简单算子（Elementwise Add）示例：**
```json
{
  "operator": "add_custom",
  "configs": [
    {"shape": [1024], "dtype": "fp32"},
    {"shape": [65536], "dtype": "fp32"},
    {"shape": [1048576], "dtype": "fp32"},
    {"shape": [65536], "dtype": "fp16"},
    {"shape": [65536], "dtype": "bf16"}
  ]
}
```

### 4.3 脚本集

| 脚本 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `score.sh` | 总编排 | 算子路径 + 配置文件 | 评分 JSON |
| `compile.sh` | 编译封装 | 算子路径 | 0/1 + 错误日志 |
| `test_correctness.sh` | 正确性测试 | 算子路径 + 配置 | 逐配置通过/失败 |
| `test_performance.sh` | 性能测试 | 算子路径 + 配置 | 逐配置 TFLOPS |
| `gen_golden.py` | 生成 golden 参考 | 算子规格 + 配置 | golden 数据文件 |
| `verify_correctness.py` | 对比输出 vs golden | 输出数据 + golden + 阈值 | 通过/失败 + 误差统计 |
| `compute_score.py` | 聚合评分 | 正确性 + 性能结果 | 最终评分 JSON |

### 4.4 评分输出格式

```json
{
  "version": "v23",
  "timestamp": "2026-04-08T15:30:00Z",
  "git_commit": "abc1234",
  "correctness_total": 1.0,
  "performance_total_tflops": 856.3,
  "improvement_over_prev": "+3.2%",
  "configs": [
    {
      "name": "b8_s4096_h16_d128_bf16_causal",
      "correctness": 1,
      "max_abs_error": 0.0023,
      "max_rel_error": 0.0018,
      "tflops": 823.1,
      "task_duration_us": 142.3,
      "profiling": {
        "vec_ratio": 0.65,
        "mte2_ratio": 0.22,
        "cube_ratio": 0.0,
        "scalar_ratio": 0.03,
        "mte3_ratio": 0.10,
        "block_dim": 20,
        "ub_usage_bytes": 163840,
        "bank_conflict_count": 0
      }
    }
  ]
}
```

### 4.5 性能基准线

来源：`ops-profiling` skill 中的性能标准。

| 指标 | 优秀 | 可改进 | 瓶颈 |
|------|------|--------|------|
| Task Duration vs 理论值 | <20% gap | 20-50% gap | >50% gap |
| 多核负载均衡 | <10% 方差 | 10-30% 方差 | >30% 方差 |
| Double Buffer 重叠率 | >30% | 10-30% | <10% |
| Bank Conflict | <5% 总量 | 5-15% | >15% |

### 4.6 流程图

```
score.sh
  │
  ├── 1. compile.sh
  │     ├── 成功 → 继续
  │     └── 失败 → 返回 {"correctness_total": 0, "compile_error": "..."}
  │
  ├── 2. gen_golden.py (若 golden 不存在)
  │     └── 生成参考数据
  │
  ├── 3. 对每个 config_j:
  │     ├── 运行内核，收集输出
  │     └── verify_correctness.py → correctness(x, config_j)
  │
  ├── 4. 若 correctness_total < 1.0:
  │     └── 返回 {"correctness_total": X, "performance_total_tflops": 0}
  │
  ├── 5. 对每个 config_j:
  │     ├── msprof op --warm-up=10 → 采集性能
  │     └── 解析 Task Duration → TFLOPS
  │
  └── 6. compute_score.py → 聚合为最终 JSON
```

### 4.7 复用现有资产

| 现有资产 | 复用方式 |
|----------|---------|
| `ops-profiling` 的 `perf_summary.py` | 封装为 `perf_summary_wrapper.py` |
| `ops-precision-standard` 的阈值表 | 内置到 `verify_correctness.py` |
| `ascendc-direct-invoke-template` 的构建流 | `compile.sh` 复用其 cmake 模式 |
| `ascendc-direct-invoke-template` 的 `gen_golden.py` 模式 | `gen_golden.py` 复用其框架 |

### 4.8 交付物

```
scoring/
  score.sh                         # 总编排
  compile.sh                       # 编译封装
  test_correctness.sh              # 正确性测试
  test_performance.sh              # 性能测试 (msprof)
  gen_golden.py                    # golden 参考生成
  verify_correctness.py            # 输出对比 (atol/rtol)
  compute_score.py                 # 评分聚合
  perf_summary_wrapper.py          # 封装现有 perf_summary.py
  configs/
    attention.json                 # Attention 测试配置
    softmax.json                   # Softmax 测试配置
    layernorm.json                 # LayerNorm 测试配置
    default.json                   # 默认 Elementwise 配置
```

---

## 5. 任务四：Supervisor Agent

### 5.1 核心设计决策

**Supervisor 是 Python 脚本，不是 Claude Agent。**

理由：
- 多日连续运行会超出任何 Agent 的上下文窗口
- 主循环逻辑（启动会话、检查评分、管理谱系）是确定性的，不需要 LLM 推理
- 仅在"检测到停滞，需要重定向探索方向"时调用 Claude 进行 LLM 推理

### 5.2 架构

```
supervisor.py (Python 脚本, 长时间运行)
  │
  ├── 启动 → Kernel Evolution Agent (Claude Code 会话)
  │            │── 调用 → scoring/score.sh
  │            │── 读取 → Knowledage-base/
  │            │── 写入 → workspace/ops/{op_name}/
  │            └── 提交 → git commit
  │
  ├── 监控 → 评分历史, git log, 已用时间
  ├── 检测 → 停滞 (连续 N 步无改进)
  └── 干预 → 启动重定向会话 (轻量级 Claude)
```

### 5.3 状态持久化

文件：`evolution/state.json`

```json
{
  "operator_name": "flash_attention_ascend",
  "target_chip": "Ascend910B",
  "start_time": "2026-04-08T10:00:00Z",
  "current_version": 23,
  "best_version": 21,
  "best_score": 856.3,
  "stall_counter": 0,
  "total_attempts": 47,
  "redirect_count": 2,
  "lineage": [
    {
      "version": 0,
      "commit": "abc1234",
      "score": 0.0,
      "description": "seed: naive attention with basic tiling"
    },
    {
      "version": 1,
      "commit": "def5678",
      "score": 412.5,
      "description": "add multi-core distribution + double buffer"
    }
  ]
}
```

### 5.4 主循环逻辑

```python
def main_loop():
    state = load_or_init_state()

    while not should_stop(state):
        # 1. 准备 Agent 上下文
        lineage_summary = format_lineage(state.lineage)
        current_kernel = read_current_kernel(state)
        current_score = state.lineage[-1].score if state.lineage else None

        # 2. 检测停滞，决定是否干预
        if state.stall_counter >= STALL_THRESHOLD:
            directive = generate_redirect_directive(state)  # 调用 Claude LLM
            state.redirect_count += 1
            state.stall_counter = 0
        else:
            directive = None

        # 3. 启动 Kernel Evolution Agent 会话
        result = launch_agent_session(
            agent="agents/kernel-evolution-agent/AGENT.md",
            context={
                "operator_spec": state.operator_spec,
                "current_kernel": current_kernel,
                "current_score": current_score,
                "lineage_summary": lineage_summary,
                "directive": directive,
            },
            timeout=MAX_SESSION_DURATION
        )
        state.total_attempts += 1

        # 4. 处理结果
        if result.committed:
            state.current_version += 1
            state.lineage.append({
                "version": state.current_version,
                "commit": result.commit_hash,
                "score": result.score.performance_total_tflops,
                "description": result.description,
            })
            if result.score.performance_total_tflops > state.best_score:
                state.best_version = state.current_version
                state.best_score = result.score.performance_total_tflops
                state.stall_counter = 0
            else:
                state.stall_counter += 1
        else:
            state.stall_counter += 1

        # 5. 保存状态
        save_state(state)
        log_iteration(state, result)
```

### 5.5 停滞检测与干预

#### 停滞信号

| 条件 | 阈值 | 含义 |
|------|------|------|
| 连续 commit 但无性能提升 | `stall_counter >= 5` | Agent 陷入局部最优 |
| 连续尝试但无法成功 commit | `failed_attempts >= 10` | Agent 遇到编译或正确性障碍 |
| 连续重定向无效 | `redirect_count >= 3` (连续) | 可能已接近硬件极限 |

#### 重定向指令生成

当检测到停滞，Supervisor 启动一个轻量级 Claude 会话：

**输入：**
- 完整谱系及评分
- 最近 5 个版本的 profiling 数据
- 最近失败的优化尝试描述

**Prompt 模板（`evolution/prompts/redirect-directive.md`）：**
```
你正在审查一个 Ascend C 内核优化的进化轨迹。

## 当前状态
- 已提交 {N} 个版本，耗时 {elapsed}
- 最佳评分: {best_score} TFLOPS (版本 {best_version})
- 最近 {stall_count} 个版本无改进

## Profiling 数据摘要
{profiling_summary}

## 最近失败的优化尝试
{recent_failures}

## 任务
1. 分析当前瓶颈所在
2. 提出 3-5 个**未被尝试过的**优化方向
3. 对每个方向评估：可行性、预期收益、所需知识库资源
4. 选择最有希望的方向，生成具体的优化指令

输出格式：
- direction: 优化方向名称
- rationale: 为什么这个方向可能有效
- knowledge_refs: 需要查阅的知识库资源
- specific_instruction: 给 Kernel Evolution Agent 的具体指令
```

**输出：** 一个结构化的优化指令，传递给下一次 Agent 会话。

### 5.6 Git 谱系管理

```
# 每个成功版本的 commit
git commit -m "v{N}: {description}

Score: {score} TFLOPS
Correctness: PASS ({n_configs}/{n_configs} configs)
Best config: {best_config_name} @ {best_tflops} TFLOPS
Worst config: {worst_config_name} @ {worst_tflops} TFLOPS"

# 打 tag 便于快速检索
git tag v{N}-score-{score}

# Agent 可以查看任何历史版本
git show v{N}:workspace/ops/{op_name}/{op_name}.asc
git diff v{N-1}..v{N} -- workspace/ops/{op_name}/
```

### 5.7 停止条件

| 条件 | 默认值 | 可配置 |
|------|--------|--------|
| 最大运行时间 | 7 天 | `config.yaml: max_wall_time` |
| 最大提交版本数 | 100 | `config.yaml: max_versions` |
| 目标性能达成 | 无 | `config.yaml: target_tflops` |
| 连续重定向失败 | 3 次 | `config.yaml: max_consecutive_redirects` |
| 手动中断 | Ctrl+C | — |

### 5.8 会话管理

每个变异步骤是一个**全新的 Claude Code 会话**（避免上下文窗口溢出）。连续性通过以下方式保持：
- **谱系摘要**传递给每个新会话（一行一个版本，线性增长但紧凑）
- **完整代码和 profiling 数据**可通过文件读取在会话内访问
- **每个会话的推理日志**保存到 `evolution/logs/step_{N}.md` 供后续分析

### 5.9 配置文件

文件：`evolution/config.yaml`

```yaml
# 算子配置
operator_name: flash_attention_ascend
target_chip: Ascend910B
operator_spec_path: workspace/ops/flash_attention_ascend/spec.md

# 进化参数
max_wall_time: 168h        # 7 天
max_versions: 100
max_session_duration: 30m  # 单次 Agent 会话最大时长
stall_threshold: 5         # 连续无改进版本数触发重定向
max_failed_attempts: 10    # 连续失败尝试数触发重定向
max_consecutive_redirects: 3

# 评分配置
scoring_config_path: scoring/configs/attention.json
warmup_rounds: 10
repeat_rounds: 5

# 目标（可选）
target_tflops: null        # 设置后达标即停

# Agent 配置
agent_definition: agents/kernel-evolution-agent/AGENT.md
```

### 5.10 交付物

```
evolution/
  supervisor.py                    # 主循环编排
  config.yaml                      # 运行配置
  state.json                       # 持久化状态（运行时生成）
  prompts/
    redirect-directive.md          # 停滞重定向 prompt 模板
    session-init.md                # Agent 会话初始化 prompt 模板
  scores/                          # 逐版本评分 JSON（运行时生成）
  logs/                            # 逐步推理日志（运行时生成）
```

---

## 6. 完整目录结构

```
AscendC-Kernel-Agent/
│
├── CLAUDE.md                              # Layer 1 全局知识索引
├── spec.md                                # 本技术规格文档
├── README.md                              # 项目简介
│
├── agents/                                # Agent 定义
│   └── kernel-evolution-agent/
│       ├── AGENT.md                       # 统一进化 Agent 定义
│       ├── prompts/
│       │   ├── seed-generation.md         # 种子生成 prompt
│       │   ├── optimize-step.md           # 优化步骤 prompt
│       │   └── repair-step.md             # 回归修复 prompt
│       └── templates/
│           ├── operator-spec.md           # 算子规格输入模板
│           └── lineage-summary.md         # 谱系摘要格式模板
│
├── scoring/                               # 评分函数 f
│   ├── score.sh                           # 总编排
│   ├── compile.sh                         # 编译封装
│   ├── test_correctness.sh                # 正确性测试
│   ├── test_performance.sh                # 性能测试 (msprof)
│   ├── gen_golden.py                      # golden 参考生成
│   ├── verify_correctness.py              # 输出对比
│   ├── compute_score.py                   # 评分聚合
│   ├── perf_summary_wrapper.py            # 封装现有 perf_summary.py
│   └── configs/
│       ├── attention.json                 # Attention 测试配置
│       ├── softmax.json                   # Softmax 测试配置
│       ├── layernorm.json                 # LayerNorm 测试配置
│       └── default.json                   # 默认 Elementwise 配置
│
├── evolution/                             # Supervisor + 进化状态
│   ├── supervisor.py                      # 主循环编排
│   ├── config.yaml                        # 运行配置
│   ├── state.json                         # 持久化状态（运行时）
│   ├── prompts/
│   │   ├── redirect-directive.md          # 停滞重定向模板
│   │   └── session-init.md                # 会话初始化模板
│   ├── scores/                            # 逐版本评分（运行时）
│   └── logs/                              # 推理日志（运行时）
│
├── workspace/                             # 内核开发工作区
│   └── ops/
│       └── {operator_name}/
│           ├── {operator_name}.asc        # 内核源码
│           ├── CMakeLists.txt             # 构建配置
│           ├── run.sh                     # 构建运行脚本
│           ├── scripts/
│           │   ├── gen_data.py            # 测试数据生成
│           │   └── verify_result.py       # 结果验证
│           └── docs/
│               └── environment.json       # 环境信息
│
├── Knowledage-base/                       # 知识库（已有 + 新增索引）
│   ├── INDEX-attention-ops.md             # [新增] Attention 算子导航
│   ├── INDEX-api-reference.md             # [新增] API 文档导航
│   ├── INDEX-examples.md                  # [新增] 示例代码导航
│   ├── coding-skills/                     # 16 Skills + 5 Agents + 1 Team
│   └── coding-sources/                    # 88K+ 源文件
│
└── AVO-paper/                             # 参考论文（不变）
```

---

## 7. 实施阶段

### Phase 1：基础设施（知识库 + 评分函数）
- [ ] 创建 `CLAUDE.md`（全局知识索引）
- [ ] 创建 3 个 `INDEX-*.md` 导航文件
- [ ] 创建 `scoring/` 目录及全部脚本
- [ ] 在 `asc-devkit/examples/` 中的一个示例算子上验证评分流程

### Phase 2：代码生成 Agent
- [ ] 创建 `agents/kernel-evolution-agent/AGENT.md`
- [ ] 创建 prompt 模板（seed/optimize/repair）和 operator-spec 模板
- [ ] 验证种子生成：给定简单算子规格 → 生成可工作的 v0
- [ ] 验证单次优化：给定 v0 → 生成改进的 v1

### Phase 3：Supervisor 进化引擎
- [ ] 实现 `evolution/supervisor.py` 主循环
- [ ] 实现停滞检测 + 重定向指令生成
- [ ] 实现 git 谱系管理（commit、tag、score metadata）
- [ ] 端到端测试：Supervisor 启动 Agent → Agent 生成内核 → 评分记录 → 谱系增长

### Phase 4：集成调优
- [ ] 在简单算子（Softmax 或 LayerNorm）上运行 10+ 版本进化
- [ ] 调优停滞阈值和重定向逻辑
- [ ] 验证完整循环可稳定运行
- [ ] 记录经验教训，优化 prompt

### Phase 5：挑战目标
- [ ] 应用于 Attention 算子（利用 `ops-transformer/attention/` 丰富参考）
- [ ] 运行多日连续进化
- [ ] 分析优化轨迹和发现的技术

---

## 8. 验证标准

| 验证类型 | 内容 | 通过标准 |
|----------|------|---------|
| 单元验证 | scoring 脚本能正确编译、测试、评分一个 asc-devkit 示例 | 评分 JSON 格式正确，正确性判定准确 |
| 集成验证 | Agent 能从算子规格生成 v0 并通过正确性测试 | 生成的 .asc 文件可编译，correctness_total = 1.0 |
| 端到端验证 | Supervisor 能自动运行 5+ 轮进化 | 谱系正确记录，评分单调不降（仅 commit 通过的版本） |
| 停滞恢复 | 人工制造停滞，验证重定向是否有效 | 重定向后 Agent 尝试新方向，非重复之前的失败尝试 |
| 长时间运行 | 连续运行 24+ 小时 | 无崩溃，状态正确持久化，可从中断恢复 |
