# AscendC Kernel Agent — 技术规格文档

## 1. 项目概述

### 1.1 目标

构建一个面向华为 Ascend NPU 的 **Ascend C 算子自动化生成与自我进化系统**。系统能够：
- 根据算子规格（数学公式、形状、数据类型、目标芯片）自动生成 Ascend C 内核代码
- 通过持续的 **Edit-Evaluate-Diagnose** 循环自主优化内核性能
- 在多日无人干预的运行中，积累数十个经过验证的优化版本

### 1.1.1 非目标

本项目第一阶段**不**追求：
- 一次性支持任意复杂算子自动生成
- 在 Attention 等复杂算子上直接达到手写最优性能
- 无约束地长期自主探索（多日运行留待后续阶段验证）
- 覆盖所有调用方式（优先支持 Direct Invoke）

第一阶段目标是验证以下**最小闭环**：
1. 给定一个可定义 golden 的算子规格
2. Agent 能生成或修改 Ascend C 内核
3. 评分系统能稳定给出正确性和性能结果
4. Supervisor 能稳定驱动多轮尝试并保留谱系

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

校准和补充 3 个索引文件（已存在），辅助 Agent 快速定位参考代码：

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

采用**候选工作区模型**：Agent 在隔离的候选目录中工作，不直接修改当前最佳版本。

#### 输入

| 参数 | 说明 | 来源 |
|------|------|------|
| `operator_spec_path` | 算子规格文件路径 | `workspace/specs/{op_name}.md` |
| `baseline_dir` | 当前最佳版本的**只读**目录 | `workspace/runs/{op_name}/best/` |
| `candidate_dir` | 本轮候选版本的**可写**目录 | `workspace/runs/{op_name}/attempts/step_{N}/` |
| `lineage_summary` | 谱系摘要（压缩版） | `evolution/state.json` |
| `directive` | （可选）Supervisor 重定向指令 | Supervisor 停滞干预时生成 |
| `scoring_config_path` | 评分配置 | `scoring/configs/{op_name}.json` |

#### 输出

| 字段 | 说明 |
|------|------|
| `status` | `committed` / `rejected` / `failed` / `timeout` |
| `candidate_dir` | 本轮候选目录路径 |
| `score_json_path` | 本轮评分结果路径 |
| `summary` | 一句话总结本轮尝试 |
| `failure_type` | `compile` / `correctness` / `performance` / `infra` / `timeout`（仅失败时） |
| `commit_hash` | 成功提交时返回 |

#### 工作区约束

- Agent **不得**直接修改 `best/` 目录
- 所有编辑仅发生在 `candidate_dir`
- 只有当候选版本满足提交条件时，Supervisor 才将其晋升为新的 `best/`
- 推理日志保存到 `evolution/logs/step_{N}.md` 供后续分析

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

### 3.5.1 提交准则

候选版本必须同时满足以下条件才可提交：

1. **正确性门槛**：`correctness_total = 1.0`（全配置通过，不可妥协）
2. **性能门槛**：主性能指标优于当前 `best`，且超过最小改进阈值

```
improvement_over_best = primary(candidate) / primary(best) - 1
improvement_over_best >= min_improvement_ratio   # 默认 0.02 (2%)
```

**不满足条件的版本永不提交**——`correctness_total < 1.0` 的版本评分为 0，性能未提升的版本标记为 `rejected`。

> 注：第一阶段不保留 sidegrade（正确但未提升）版本作为谱系节点，以降低复杂度。后续阶段可扩展为保留 sidegrade 用于多样性探索。

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

对每个配置 `config_j`，使用 `allclose` 语义判定：

```python
pass_j = np.allclose(output, golden, rtol=rtol(dtype), atol=atol(dtype), equal_nan=True)
```

精度阈值（来源：ops-precision-standard）：

| dtype | rtol | atol |
|-------|------|------|
| FP32 | 1e-5 | 1e-5 |
| FP16 | 1e-3 | 1e-3 |
| BF16 | 1e-2 | 1e-2 |

```
correctness_total(x) = sum(pass_j for j in all_configs) / n_configs
```

**硬性要求：`correctness_total = 1.0`（全部配置通过）才允许提交。** 这是 AVO 的核心原则——正确性不可妥协，不正确的内核评分为 0。

补充要求：
- 当 golden 中存在 0、接近 0、Inf、NaN 时，按 `allclose` 语义处理，**不**单独做除法形式的相对误差判定
- 除通过/失败外，同时记录以下诊断指标：
  - `max_abs_error`
  - `max_rel_error`（排除 golden=0 的位置）
  - `mean_abs_error`
  - `mismatch_ratio`（不通过的元素占比）

**Golden 来源优先级：**
1. 权威框架参考实现（PyTorch / NumPy 等）
2. 已验证的 CPU 参考实现
3. 现有官方样例或参考算子输出
4. **禁止**使用"待测内核自身输出"生成 golden

#### 性能评分

性能评分按算子类别定义主指标：

| 算子类别 | 主指标 | 说明 |
|----------|--------|------|
| MatMul / Attention 等算力密集型 | TFLOPS | 使用有效 FLOPs / duration |
| Elementwise / Transpose / 数据搬移型 | GB/s 或 us | 使用有效字节数 / duration 或直接使用时延 |
| Reduce / Norm 类 | us + 辅助利用率指标 | FLOPs 定义不稳定时以时延为主 |

统一聚合规则：
- `performance_primary(x, config_j)` 为该算子类别的主指标值
- `performance_total(x)` 为各配置主指标的几何平均
- 对外比较采用 `improvement_over_best = primary(x) / primary(best) - 1`

评分配置中需指定：
```yaml
metric_type: tflops | bandwidth_gbps | latency_us
min_improvement_ratio: 0.02   # 最小提升门槛，默认 2%
```

### 4.2 测试配置矩阵

测试分**三级**执行，逐级递进：

| 级别 | 目标 | 运行时机 |
|------|------|---------|
| `smoke` | 小 shape，快速发现编译和基础功能错误 | 每轮必跑 |
| `representative` | 典型 shape，判断是否具备实际优化价值 | smoke 通过后运行 |
| `stress` | 极限 shape / 长序列 / 边界 case，提交前最终验证 | 仅候选版本达到提交门槛时运行 |

**Attention 算子示例：**
```json
{
  "operator": "flash_attention_ascend",
  "smoke": [
    {"batch": 8, "seq_len": 128, "heads": 16, "dim": 128, "dtype": "bf16", "causal": true},
    {"batch": 8, "seq_len": 256, "heads": 16, "dim": 128, "dtype": "bf16", "causal": false}
  ],
  "representative": [
    {"batch": 8, "seq_len": 1024, "heads": 16, "dim": 128, "dtype": "bf16", "causal": true},
    {"batch": 4, "seq_len": 2048, "heads": 16, "dim": 128, "dtype": "bf16", "causal": true},
    {"batch": 4, "seq_len": 2048, "heads": 16, "dim": 128, "dtype": "bf16", "causal": false}
  ],
  "stress": [
    {"batch": 2, "seq_len": 4096, "heads": 16, "dim": 128, "dtype": "bf16", "causal": true},
    {"batch": 1, "seq_len": 8192, "heads": 16, "dim": 128, "dtype": "bf16", "causal": true}
  ]
}
```

**简单算子（Elementwise Add）示例：**
```json
{
  "operator": "add_custom",
  "smoke": [
    {"shape": [1024], "dtype": "fp32"},
    {"shape": [1024], "dtype": "fp16"}
  ],
  "representative": [
    {"shape": [65536], "dtype": "fp32"},
    {"shape": [65536], "dtype": "fp16"},
    {"shape": [65536], "dtype": "bf16"}
  ],
  "stress": [
    {"shape": [1048576], "dtype": "fp32"},
    {"shape": [1048576], "dtype": "fp16"}
  ]
}
```

### 4.3 脚本集

| 脚本 | 功能 | 输入 | 输出 |
|------|------|------|------|
| `score.sh` | 总编排 | 算子路径 + 配置文件 | 评分 JSON |
| `compile.sh` | 编译封装 | 算子路径 | 0/1 + 错误日志 |
| `test_correctness.sh` | 正确性测试 | 算子路径 + 配置 | 逐配置通过/失败 |
| `test_performance.sh` | 性能测试 | 算子路径 + 配置 | 逐配置主指标值 |
| `gen_golden.py` | 生成 golden 参考 | 算子规格 + 配置 | golden 数据文件 |
| `verify_correctness.py` | 对比输出 vs golden | 输出数据 + golden + 阈值 | 通过/失败 + 误差统计 |
| `compute_score.py` | 聚合评分 | 正确性 + 性能结果 | 最终评分 JSON |

### 4.4 评分输出格式

```json
{
  "version": "v23",
  "timestamp": "2026-04-08T15:30:00Z",
  "git_commit": "abc1234",
  "metric_type": "tflops",
  "correctness_total": 1.0,
  "performance_total": 856.3,
  "improvement_over_best": "+3.2%",
  "test_levels_run": ["smoke", "representative", "stress"],
  "configs": [
    {
      "name": "b8_s1024_h16_d128_bf16_causal",
      "level": "representative",
      "correctness": 1,
      "max_abs_error": 0.0023,
      "max_rel_error": 0.0018,
      "mean_abs_error": 0.0004,
      "mismatch_ratio": 0.0,
      "performance_primary": 823.1,
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

### 4.6 流程图（分级评分）

```
score.sh
  │
  ├── 1. compile.sh
  │     ├── 成功 → 继续
  │     └── 失败 → 返回 {"correctness_total": 0, "failure_type": "compile", ...}
  │
  ├── 2. gen_golden.py (若 golden 不存在)
  │     └── 生成参考数据
  │
  ├── 3. smoke correctness
  │     ├── 通过 → 继续
  │     └── 失败 → 返回 {"correctness_total": X, "failure_type": "correctness", ...}
  │
  ├── 4. representative correctness
  │     ├── 通过 → 继续
  │     └── 失败 → 返回 {"correctness_total": X, "failure_type": "correctness", ...}
  │
  ├── 5. 若 correctness_total < 1.0 → 结束（不进入性能测试）
  │
  ├── 6. representative performance
  │     └── 计算 improvement_over_best
  │
  ├── 7. 若满足候选提交门槛（improvement >= min_improvement_ratio）：
  │     ├── stress correctness
  │     └── stress performance
  │
  └── 8. compute_score.py → 聚合为最终 JSON
```

短路逻辑的目的是加速反馈循环——前期迭代中，大部分候选版本在 smoke 阶段就能快速判定，避免在 stress 配置上浪费时间。

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
  │            │── 写入 → workspace/runs/{op_name}/attempts/step_{N}/
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
  "current_step": 47,
  "best_version": 21,
  "best_score": 856.3,
  "best_commit": "abc1234",
  "stall_counter": 3,
  "failed_attempts": 2,
  "consecutive_redirects": 1,
  "total_attempts": 47,
  "last_completed_step": 46,
  "active_attempt_dir": null,
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

**计数器规则：**
- `stall_counter`：仅"正确但未提升"时加一；出现性能提升时清零
- `failed_attempts`：编译失败、正确性失败、超时时加一；成功提交时清零
- `consecutive_redirects`：触发 redirect 后加一；一旦出现性能提升则清零

**恢复规则：**
- `active_attempt_dir` 非空表示上次运行中断，恢复时应清理该目录后继续
- `last_completed_step` 用于确定恢复起点，避免重复计数

### 5.4 主循环逻辑

```python
def main_loop():
    state = load_or_init_state()

    while not should_stop(state):
        # 1. 从当前 best 创建隔离的候选工作区
        attempt_dir = prepare_attempt_dir_from_best(state)
        state.active_attempt_dir = attempt_dir
        save_state_atomically(state)

        # 2. 检测停滞，决定是否生成重定向指令
        directive = maybe_generate_redirect(state)

        # 3. 启动 Kernel Evolution Agent 会话
        result = run_agent(
            operator_spec_path=state.operator_spec_path,
            baseline_dir=state.best_dir,
            candidate_dir=attempt_dir,
            lineage_summary=build_lineage_summary(state),
            directive=directive,
        )

        # 4. 加载评分结果
        score = load_score_if_exists(result.score_json_path)

        # 5. 处理结果
        if result.status == "committed":
            promote_attempt_to_best(attempt_dir, state)
            record_lineage(state, result, score)
            if score.improved:
                state.stall_counter = 0
                state.consecutive_redirects = 0
            else:
                state.stall_counter += 1
            state.failed_attempts = 0
        elif result.status in ("failed", "timeout"):
            state.failed_attempts += 1
        elif result.status == "rejected":
            state.stall_counter += 1

        # 6. 清理并持久化
        state.total_attempts += 1
        state.last_completed_step = state.current_step
        state.current_step += 1
        state.active_attempt_dir = None
        cleanup_or_archive_attempt(attempt_dir, result.status)
        save_state_atomically(state)
```

关键设计：
- `prepare_attempt_dir_from_best`：从 `best/` 复制到 `attempts/step_{N}/`，确保隔离
- `promote_attempt_to_best`：仅当满足提交准则时，用候选替换 `best/`
- `save_state_atomically`：原子写入（先写临时文件再 rename），防止中断导致状态损坏
- `cleanup_or_archive_attempt`：失败的候选可归档或直接清理，防止磁盘泄漏

### 5.5 停滞检测与干预

#### 停滞信号

| 信号 | 含义 | 默认阈值 |
|------|------|---------|
| `stall_counter` | 连续正确但无性能提升 | 5 |
| `failed_attempts` | 连续编译/正确性/超时失败 | 5 |
| `consecutive_redirects` | 连续重定向后仍无提升 | 3 |

**触发策略（不同失败原因对应不同响应）：**
- `stall_counter >= threshold`：生成新的搜索方向（redirect），引导 Agent 尝试不同优化路径
- `failed_attempts >= threshold`：切换到 repair/diagnostic 模式，使用 `repair-step.md` prompt
- `consecutive_redirects >= threshold`：停止运行，等待人工介入（可能已接近硬件极限或存在系统性问题）

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

- 每个成功版本 commit 一次
- Tag 使用稳定格式：`v{N}`（不含浮点分数）
- 分数和配置摘要写入 commit message 和 `evolution/scores/v{N}.json`

```
# commit message 格式
git commit -m "v{N}: {description}

Score: {score}
Correctness: PASS ({n_configs}/{n_configs} configs)
Best config: {best_config_name} @ {best_primary}
Worst config: {worst_config_name} @ {worst_primary}"

# tag 使用简洁格式
git tag v{N}

# Agent 可以查看任何历史版本
git show v{N}:workspace/runs/{op_name}/best/{op_name}.asc
git diff v{N-1}..v{N} -- workspace/runs/{op_name}/
```

**禁止**使用 `v{N}-score-{score}` 这类包含浮点数的 tag 名称——tag 名会变脆弱，不适合解析和比较。

### 5.7 停止条件

| 条件 | 默认值 | 可配置 |
|------|--------|--------|
| 最大运行时间 | 7 天 | `config.yaml: max_wall_time` |
| 最大提交版本数 | 100 | `config.yaml: max_versions` |
| 目标性能达成 | 无 | `config.yaml: target_performance` |
| 连续重定向失败 | 3 次 | `config.yaml: max_consecutive_redirects` |
| 手动中断 | Ctrl+C | — |

### 5.8 会话管理

每个变异步骤使用**全新的 Claude Code 会话**（避免上下文窗口溢出）。为防止谱系线性膨胀，传递给新会话的上下文分为三部分：

1. **`recent_history`**
   - 最近 5 个版本的摘要（版本号、分数、一句话描述、关键 profiling 指标）

2. **`best_history`**
   - 历史最佳 3 个版本的摘要（用于理解性能天花板演变）

3. **`strategy_summary`**
   - 从完整谱系自动生成的压缩总结：
     - 哪些优化方向有效（产生了 improving 版本）
     - 哪些方向失败（及失败原因类别）
     - 当前未覆盖的方向

补充：
- 完整代码和 profiling 数据可通过文件读取在会话内访问
- 每个会话的推理日志保存到 `evolution/logs/step_{N}.md` 供后续分析
- `strategy_summary` 由 Supervisor 在每轮开始前从 `state.json` 和 `evolution/logs/` 生成

### 5.9 配置文件

文件：`evolution/config.yaml`

```yaml
# 算子配置
operator_name: flash_attention_ascend
target_chip: Ascend910B
operator_spec_path: workspace/specs/flash_attention_ascend.md

# 工作区
runs_dir: workspace/runs/flash_attention_ascend

# 进化参数
max_wall_time: 168h        # 7 天
max_versions: 100
max_session_duration: 30m  # 单次 Agent 会话最大时长
stall_threshold: 5         # 连续"正确但无提升"触发重定向
max_failed_attempts: 5     # 连续失败触发 repair 模式
max_consecutive_redirects: 3

# 评分配置
scoring_config_path: scoring/configs/attention.json
metric_type: tflops        # tflops | bandwidth_gbps | latency_us
min_improvement_ratio: 0.02  # 最小提升门槛 2%
warmup_rounds: 10
repeat_rounds: 5

# 目标（可选）
target_performance: null   # 设置后达标即停

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
│   ├── specs/
│   │   └── {op_name}.md                   # 算子规格文件
│   └── runs/
│       └── {op_name}/
│           ├── best/                      # 当前最佳版本（只读基线）
│           │   ├── {op_name}.asc          # 内核源码
│           │   ├── CMakeLists.txt         # 构建配置
│           │   ├── run.sh                 # 构建运行脚本
│           │   └── scripts/
│           │       ├── gen_data.py        # 测试数据生成
│           │       └── verify_result.py   # 结果验证
│           └── attempts/                  # 候选版本（每轮一个子目录）
│               └── step_{N}/             # 本轮候选（可写）
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

### Phase 1：最小评分闭环
- [ ] 校准现有 `CLAUDE.md` 和 `INDEX-*.md`（文件已存在，补充缺失内容）
- [ ] 实现 `scoring/compile.sh`
- [ ] 实现 smoke correctness（`gen_golden.py` + `verify_correctness.py`）
- [ ] 在官方 `asc-devkit/examples/` 的 add/softmax 样例上跑通评分，生成稳定的评分 JSON

### Phase 2：最小 Supervisor 闭环
- [ ] 实现 `workspace/runs/{op_name}/best/` + `attempts/step_{N}/` 工作区模型
- [ ] 实现 `evolution/state.json` 持久化和中断恢复
- [ ] 用"固定 prompt + 单算子修改"跑通 3 轮迭代，验证 prepare/promote/archive 流程

### Phase 3：Agent 化
- [ ] 接入 `kernel-evolution-agent`（AGENT.md + prompt 模板）
- [ ] 实现 repair / optimize 两类 prompt
- [ ] 验证能稳定产出 v0（种子生成）和 v1（首次优化）

### Phase 4：分级测试和停滞恢复
- [ ] 补充 representative / stress 级别测试
- [ ] 实现 redirect 指令生成和分类停滞响应
- [ ] 验证状态机在各种失败场景下的稳定性

### Phase 5：复杂算子
- [ ] 迁移到 LayerNorm / Softmax，验证跨算子泛化能力
- [ ] 最后迁移到 Attention（利用 `ops-transformer/attention/` 丰富参考）
- [ ] 运行长时间进化，分析优化轨迹

---

## 8. 验证标准

| 验证类型 | 内容 | 通过标准 |
|----------|------|---------|
| 最小评分闭环 | 对一个官方样例完成编译、运行、正确性判定 | 生成稳定评分 JSON，结果可复现 |
| 工作区隔离 | 失败候选不会污染当前 best | best 目录内容和 commit 不变 |
| 状态恢复 | Supervisor 在中断后恢复 | 从 state.json 继续运行，无重复计数 |
| Agent 集成 | Agent 能在 candidate_dir 内完成一次修改和评分 | 返回结构化结果，Supervisor 可消费 |
| 迭代有效性 | 简单算子连续运行 5 轮 | 至少产生 1 个 improving 版本 |
| 长时间稳定性 | 连续运行 24h | 无状态损坏，无 attempt 目录泄漏，无死循环 |
