# AscendC Kernel Agent — EVO Branch

## 项目概述

自主 Ascend C 算子生成与进化系统。本分支（`EVO`）承载 **EvoKernel 论文框架**——跨算子、价值驱动、两阶段流水线（Drafting → Refining）。AVO（Agentic Variation Operators）单算子框架位于 `main` 分支。

**EVO 入口**：`evo/README.md` → `evo/agents/AGENTS.md` → `evo/agents/campaign-orchestrator/AGENT.md`
**形式化规格**：`evo/spec.md`（M-MDP + Q 值更新方程）
**参考论文**：`./EVO-paper/main.tex`

核心公式（论文 Eq. 3）：`π(y_t | s_t, M_t) = G_θ(a_t | s_t, c_t) · μ(c_t | s_t, M_t)`
- **G_θ**：生成策略 = `evo/agents/developer/AGENT.md`（由 stage agents 派发）
- **μ**：价值驱动检索策略 = `evo/agents/retrieval-policy/AGENT.md`
- **M_t**：跨算子共享 Memory Bank = `evo/memory/`
- **V**：多门验证器 = `evo/agents/multigate-verifier/AGENT.md`（内调 `scoring/score.sh`）

工作区模型：自定义算子工程（非 Kernel 直调）
- `workspace/runs/{op_name}/test/`（PyTorch 测试基础设施，共享基建）
- `workspace/runs/{op_name}/attempts/step_{N}/`（候选目录，由 stage agents 按需 `mkdir -p`）
- `workspace/specs/{op}.md`（算子规格）

---

## Agent Team（EVO）

六核心角色（见 `evo/agents/AGENTS.md`）：

| Agent | 定义文件 | 职责 |
|-------|---------|------|
| campaign-orchestrator | `evo/agents/campaign-orchestrator/AGENT.md` | 消费 `operator_queue`，驱动 Stage 1 → Stage 2 |
| stage1-drafter | `evo/agents/stage1-drafter/AGENT.md` | Cold-Start Drafting：到首个 feasible 即退出 |
| stage2-refiner | `evo/agents/stage2-refiner/AGENT.md` | Continual Refining：耗尽预算降 latency |
| retrieval-policy | `evo/agents/retrieval-policy/AGENT.md` | μ 策略：dense top-K → ε-greedy by Q_k |
| memory-curator | `evo/agents/memory-curator/AGENT.md` | Memory R/W + MC Q-update + PopArt 归一化 |
| multigate-verifier | `evo/agents/multigate-verifier/AGENT.md` | V 验证器：anti-hack + score.sh → 四元组 |

辅助角色（由 stage / verifier 派发）：
- **developer**（G_θ 实现）：`evo/agents/developer/AGENT.md`
- **reviewer**（anti-hack auditor）：`evo/agents/reviewer/AGENT.md`

启动方式：用 Claude Code 加载 `evo/agents/AGENTS.md` 或直接派发 `campaign-orchestrator`。

---

## 自定义算子工程结构

```
{OpName}Custom/
├── {op_name}_custom.json          — 算子定义 JSON（输入/输出/类型/格式）
├── CMakeLists.txt                  — 根构建配置
├── CMakePresets.json               — 构建预设
├── build.sh                        — 构建编排脚本
├── op_host/                        — Host 侧
│   ├── CMakeLists.txt
│   ├── {op_name}_custom.cpp       — OpDef + TilingFunc + InferShape
│   └── {op_name}_custom_tiling.h  — TilingData 结构
├── op_kernel/                      — Device 侧
│   ├── CMakeLists.txt
│   └── {op_name}_custom.cpp       — AscendC Kernel 实现
└── build_out/                      — 构建产物
    └── custom_opp_*.run            — 自安装部署包
```

### 测试基础设施

```
workspace/runs/{op_name}/test/
├── CppExtension/                   — Python 绑定构建
│   ├── setup.py                    — NpuExtension 配置（模块名 custom_ops_lib）
│   ├── build_and_run.sh            — 手动调试脚本（框架流水线不用）
│   └── csrc/
│       ├── op.cpp                  — 算子绑定（EXEC_NPU_CMD）
│       └── pytorch_npu_helper.hpp  — NPU 辅助工具
└── reference.py                    — Model + ModelNew + get_inputs + get_init_inputs
                                      (见下方"reference.py 隐式契约"节)
```

---

## 知识库地图

### Skills — Claude Code 原生 Skills

已安装至 `.claude/skills/`，通过 Claude Code 原生技能系统自动加载。

| Skill | 用途 |
|-------|------|
| ascendc-tiling-design | Tiling 策略（归约/广播/逐元素/转换/MatMul/卷积） |
| ascendc-api-best-practices | API 参数限制、优化模式（Adds/Muls、Double Buffer） |
| ascendc-npu-arch | 芯片架构代际 A2/A3/A5、条件编译 |
| ascendc-precision-debug | 精度问题诊断决策树（症状→诊断→修复） |
| ascendc-runtime-debug | 运行时错误码 161xxx/361xxx/561xxx、Kernel 挂死 |
| ops-profiling | 性能采集（msprof / NPU Event）、指标分析 |
| ops-precision-standard | 精度阈值标准（按 dtype 的 atol/rtol） |
| ascendc-docs-search | 本地 + 在线 API 文档搜索 |
| ascendc-env-check | NPU 设备查询、CANN 环境验证 |
| ascendc-code-review | 假设检验法代码审查（7 维 100 分制） |
| ascendc-ut-develop | 单元测试开发与覆盖增强 |
| ascendc-st-design | 系统测试用例设计（aclnn 接口测试） |
| ascendc-whitebox-design | 白盒测试用例生成 |
| ascendc-task-focus | 长任务聚焦管理 |
| ascendc-direct-invoke-template | Kernel 直调工程骨架（参考） |
| ascendc-registry-invoke-to-direct-invoke | aclnn 注册调用转 Kernel 直调 |
| ascendc-msopgen-workflow | msopgen 自定义算子工程全链路（权限、芯片修正、TilingFunc 模板） |
| **ascendc-kb-docs** ⭐️ | **Ascend C 官方深度文档（编程指南 + 工具链 + 实践案例，84 个 section）** |

### KB Docs（Layer 3 深度）— 官方大型文档

相对路径前缀：`Knowledge-base/coding-skills/docs/`

**入口**：`Knowledge-base/coding-skills/docs/INDEX.md`（按章节 + 主题反向索引）
**Section 目录**：`Knowledge-base/coding-skills/docs/sections/`（84 个拆分文件，每个 100-2000 行）

| 前缀 | 覆盖 | 典型 section |
|------|------|-------------|
| `guide_1.*` / `guide_2.*` / `guide_3.*` | Ascend C 编程指南（入门/编程/实践） | `guide_2.2_编程模型.md`, `guide_3.8_SIMD_算子性能优化.md` |
| `tools_3.*` ~ `tools_8.*` | 工具链手册（msKPP/msOpGen/msOpST/msSanitizer/msDebug/msProf） | `tools_8.3_工具使用.md`（msProf 命令参考） |
| `guide2_3.10.*` | 优秀实践案例（FlashAttention / Matmul 14 子案例 / GroupedMatmul） | `guide2_3.10.1_FlashAttention_算子性能调优案例.md` |

**使用规则**：
1. 先 Read `INDEX.md` 定位章节，再 Read 单独 section 文件
2. ❌ 禁止直接 Read 原始大文件（`算子开发指南.md` 等 >10K 行）
3. Developer（G_θ）在生成 DESIGN.md 时 **必须** 引用至少 1 个 L3 section
4. `multigate-verifier` 的 model-based anti-hack 审计会顺带校验 L3 引用合规

### Sources（Layer 2）— 参考实现

相对路径前缀：`Knowledge-base/coding-sources/`

| 分类 | 路径 | 说明 |
|------|------|------|
| Attention 算子（48个） | `ops-coding-sources/ops-transformer/attention/` | flash_attention, sparse_attention, mla 等 |
| NN 算子 | `ops-coding-sources/ops-nn/` | 激活、归一化、MatMul、量化 |
| Math 算子 | `ops-coding-sources/ops-math/` | 数学运算、随机数 |
| CV 算子 | `ops-coding-sources/ops-cv/` | 计算机视觉 |
| ASC SDK 示例（100+） | `programming-coding-sources/asc-devkit/examples/` | SIMD C++/C、SIMT |
| API 文档（1711 文件） | `programming-coding-sources/asc-devkit/docs/api/context/` | 权威 API 参考 |
| 编程指南（220 文件） | `programming-coding-sources/asc-devkit/docs/guide/` | 教程、最佳实践 |
| Catlass 张量库 | `programming-coding-sources/catlass/` | 类 CUTLASS 的张量运算 |
| 通信算子 | `comm-coding-sources/hcomm/` | CCU 内核、集合通信 |

### 参考实现导航（算子分类 → Knowledge-base 路径）

Stage 1 Drafting 阶段，Developer 通过 `retrieval-policy` 注入的 context 或自主按算子分类定位参考实现：

| 算子分类 | Knowledge-base 路径（前缀 `ops-coding-sources/`） | 典型算子 |
|---------|--------------------------------------------------|---------|
| 激活类 | `ops-nn/activation/{op}/` | gelu, relu, silu, swish, sigmoid |
| RNN/LSTM/GRU | `ops-nn/rnn/` | dynamic_rnn, thnn_fused_lstm_cell |
| 归一化 | `ops-nn/normalization/` | layer_norm, batch_norm, group_norm |
| MatMul/GEMM | `ops-nn/matmul/` | matmul, batch_matmul |
| 量化 | `ops-nn/quantization/` | quant, dequant |
| Attention | `ops-transformer/attention/` | flash_attention（48 变体） |
| 数学/逐元素 | `ops-math/` | add, mul, div, pow, exp |
| CV | `ops-cv/` | resize, crop, nms, roi_align |

导航步骤：`ls` 目标目录 → 确认参考算子存在 → 读取 `op_kernel/` + `op_host/` → 记录到 DESIGN.md "知识检索结果" 节（EVO 通过 retrieval context 追踪 memory_id）。

---

## Ascend C 快速参考

### 内存层级
```
GM (Global Memory, 大容量慢速)
 → L2 Cache
  → L1 Buffer
   → L0A/L0B (Cube 输入) / L0C (Cube 输出)
   → UB (Unified Buffer, 快速本地缓存)
    → Registers
```
- UB 容量：A2/A3 = 192KB，A5 = 248KB
- 最小对齐：32B（基本）、256B（REPEAT 操作最优）

### Kernel 基本结构（自定义算子工程）
```cpp
// op_kernel/{op_name}_custom.cpp
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

### Pipeline 同步
- **EnQue/DeQue**：管线阶段间同步（推荐）
- **PipeBarrier<PIPE_*>()**：粗粒度全管线屏障（慎用）
- **SetFlag/GetFlag**：事件同步

### 关键模式
- **Double Buffering**：`BUFFER_NUM = 2`，一块加载一块计算
- **多核分发**：`GetBlockIdx()` 获取核 ID，TilingFunc 中设置 `SetBlockDim`
- **Scalar 优化**：用 `Adds/Muls` 代替 `Duplicate + Add/Mul`

### 架构代号
- A2 (910): arch32, DAV_1001
- A3 (910B/310P): arch32, DAV_2201/DAV_3002
- A5 (950): arch35, DAV_3510（支持 Regbase、SIMT、FP8）

---

## 构建与测试

### 构建自定义算子工程
```bash
# 生成工程骨架
msopgen gen -i {op}_custom.json -c ai_core-Ascend910B -lan cpp -out {OpName}Custom

# 构建
cd {OpName}Custom && ./build.sh

# 部署
cd build_out && ./custom_opp_*.run
```

### PyTorch 框架测试
```bash
# 构建 Python 绑定（框架流水线入口）
source /usr/local/Ascend/ascend-toolkit/set_env.sh
bash scoring/build_pybind.sh workspace/runs/{op_name}/test/CppExtension workspace/deploy/opp
# （手动调试也可 cd 进 CppExtension 跑 bash build_and_run.sh，但框架流水线不走这条路）

# 正确性测试
python3 scoring/test_correctness.py \
    --reference workspace/runs/{op_name}/test/reference.py \
    --config scoring/configs/{op_name}.json \
    --output result.json

# 性能测试
python3 scoring/test_performance.py \
    --reference workspace/runs/{op_name}/test/reference.py \
    --config scoring/configs/{op_name}.json \
    --output perf.json
```

### 完整评分流程
```bash
source /usr/local/Ascend/ascend-toolkit/set_env.sh
bash scoring/score.sh workspace/runs/{op_name}/attempts/step_0 scoring/configs/{op_name}.json
# 退出码契约（scoring/score.sh 头部也有说明）：
#   0=完整成功, 1=environment, 2=compile, 3=deploy, 4=pybind, 5=correctness, 6=performance
# 无论成功失败都会写 evolution/scores/v{N}.json，failure_type 字段反映失败阶段
# v{N}.json 还包含 phase_timings（每阶段 wall-clock 秒数）和持久化日志（evolution/logs/step_{N}/*.log）
```

### 测试级别

scoring config JSON 支持四档测试级别（由快到慢）：

| 级别 | 用途 | 典型尺寸 |
|------|------|---------|
| `seed` | Developer 秒级自测迭代 | 极小（[32, 128]） |
| `smoke` | 基本正确性验证 | 小（[256, 2048]） |
| `representative` | 性能测量主基准 | 中（[1024, 16384]） |
| `stress` | 压力/边界测试（仅达门槛才跑） | 大（原始 test.md 尺度） |

`score.sh` 先跑 seed（如果 config 里有），失败则立即退出（Step 3.5 早退出），省去后续 smoke/representative 的时间。

---

## reference.py 隐式契约

`test_correctness.py` / `test_performance.py` 对 `reference.py` 模块有几条不写在文档里但必须满足的约定：

1. **`get_init_inputs()` 被无参调用**：架构参数（hidden_size、num_layers 等）必须在 reference.py 中固定，**不能**随 scoring config 变化。per-config 只能变 tensor 形状/dtype（如 batch_size / seq_len / shape / dtype），架构参数由 `get_init_inputs()` 硬编码。
2. **`get_inputs(config)` 接受 dict 但 fallback 到无参调用**：`test_correctness.py` 先尝试 `get_inputs(config)`，若抛 TypeError 退化为 `get_inputs()`。建议 reference.py 显式 `def get_inputs(config=None)`。
3. **`Model` 与 `ModelNew` 的 `nn.Module` 参数创建顺序必须完全一致**：`test_correctness.py` 连续两次 `torch.manual_seed(SEED)` + 构造两个类，靠顺序一致来保证 weight 初始化一致。有状态算子（如 LSTM）的 `ModelNew` 必须保留对应的 `self.xxx = nn.Layer(...)` 成员作为权重容器，即便 forward 不调用它。
4. **`Model(*init_inputs).to(device)` 和 `ModelNew(*init_inputs).to(device)`**：init_inputs 的顺序和数量必须与两个类 `__init__` 的位置参数完全一致。
5. **`model(*inputs)`**：inputs 列表解包为 forward 的位置参数；支持多输入，但所有 `nn.Module` 输出必须是**单个 tensor**（不能是 tuple），以便 `ref_output.shape / torch.allclose` 比较。

## 精度标准

默认阈值（按 dtype，来自 `test_correctness.py` 的 `PRECISION_THRESHOLDS`）：

| dtype | rtol | atol |
|-------|------|------|
| FP32 | 1e-5 | 1e-5 |
| FP16 | 1e-3 | 1e-3 |
| BF16 | 1e-2 | 1e-2 |

**Per-config 覆盖**：scoring config JSON 支持三级优先级覆盖精度阈值：
1. per-config `{"name": "...", "atol": 0.01, "rtol": 0.01}` — 最高优先级
2. 全局 `{"default_atol": 0.001, "default_rtol": 0.001}` — 次之
3. 上表的 dtype 默认值 — 兜底

用于算子本身带有近似误差的场景（如 GELU exact erf vs tanh 近似差 ~4.7e-4），避免因算法层面的合理偏差而卡死进化循环。

---

## EVO 进化流程

流程图：`evo/agents/AGENTS.md §工作流图`。算法细节：`evo/docs/{stage1-drafting,stage2-refining,multi-gate-verification,q-value-update}.md`。

状态与记忆：
- `evo/state/campaign.json`：全局队列 + 当前 op + stage
- `evo/state/episodes/{op}/`：per-op state.json + trajectory.jsonl
- `evo/memory/bank.jsonl`：跨算子共享 memory（追加式）
- `evo/memory/q_values.json`：Q_1 / Q_2 + visit count
- `evo/memory/stats.json`：PopArt (μ_2, σ_2, n)

评分函数：`scoring/score.sh workspace/runs/{op_name}/attempts/step_{N} scoring/configs/{op_name}.json` → 写入 `evolution/scores/v{N}.json`（`evolution/` 由 score.sh 运行时 `mkdir -p`）。
