# AscendC Kernel Agent

## 项目概述

自主 Ascend C 算子生成与进化系统。核心公式：`Vary(P_t) = Agent(P_t, K, f)`
- **P_t**: 历史版本谱系（git commits + 评分）
- **K**: 领域知识库（本文件索引）
- **f**: 评分函数 `scoring/score.sh`（正确性 + 性能）

架构：**Agent Team**（`agents/AGENTS.md`）
- **Architect Agent**（主 Agent）→ 任务理解、架构设计、流程编排
- **Developer Agent** → 代码编写（op_host + op_kernel + tiling）
- **Reviewer Agent** → 代码审查（7 维评分）
- **Tester Agent** → 构建、部署、PyTorch 框架测试
- **Supervisor Agent** → 仅在停滞时介入，不干预日常执行

启动方式：直接用 Claude Code 加载 `agents/AGENTS.md`，Architect Agent 自主执行进化循环

工作区模型：自定义算子工程（非 Kernel 直调）
- `workspace/runs/{op_name}/best/{OpName}Custom/`（只读基线）
- `workspace/runs/{op_name}/attempts/step_{N}/`（候选目录）
- `workspace/runs/{op_name}/test/`（PyTorch 测试基础设施）

参考论文：`./AVO-paper/`
技术规格：`./spec.md`

---

## Agent Team

| Agent | 定义文件 | 职责 |
|-------|---------|------|
| Architect | `agents/architect/AGENT.md` | 主 Agent：需求分析、架构设计、任务分发 |
| Developer | `agents/developer/AGENT.md` | 代码编写：op_host / op_kernel / tiling |
| Reviewer | `agents/reviewer/AGENT.md` | 代码审查：7 维质量评分、独立构建验证 |
| Tester | `agents/tester/AGENT.md` | 测试验证：构建 → 部署 → PyTorch 框架测试 |
| Supervisor | `agents/supervisor/AGENT.md` | 进化监督：仅在停滞时生成重定向指令 |

团队编排：`agents/AGENTS.md`

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

### Sources（Layer 3）— 搜索访问

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
#   0=完整成功, 2=compile, 3=deploy, 4=pybind, 5=correctness
# 无论成功失败都会写 evolution/scores/v{N}.json，failure_type 字段反映失败阶段
```

---

## reference.py 隐式契约

`test_correctness.py` / `test_performance.py` 对 `reference.py` 模块有几条不写在文档里但必须满足的约定：

1. **`get_init_inputs()` 被无参调用**：架构参数（hidden_size、num_layers 等）必须在 reference.py 中固定，**不能**随 scoring config 变化。per-config 只能变 tensor 形状/dtype（如 batch_size / seq_len / shape / dtype），架构参数由 `get_init_inputs()` 硬编码。
2. **`get_inputs(config)` 接受 dict 但 fallback 到无参调用**：`test_correctness.py` 先尝试 `get_inputs(config)`，若抛 TypeError 退化为 `get_inputs()`。建议 reference.py 显式 `def get_inputs(config=None)`。
3. **`Model` 与 `ModelNew` 的 `nn.Module` 参数创建顺序必须完全一致**：`test_correctness.py` 连续两次 `torch.manual_seed(SEED)` + 构造两个类，靠顺序一致来保证 weight 初始化一致。有状态算子（如 LSTM）的 `ModelNew` 必须保留对应的 `self.xxx = nn.Layer(...)` 成员作为权重容器，即便 forward 不调用它。
4. **`Model(*init_inputs).to(device)` 和 `ModelNew(*init_inputs).to(device)`**：init_inputs 的顺序和数量必须与两个类 `__init__` 的位置参数完全一致。
5. **`model(*inputs)`**：inputs 列表解包为 forward 的位置参数；支持多输入，但所有 `nn.Module` 输出必须是**单个 tensor**（不能是 tuple），以便 `ref_output.shape / torch.allclose` 比较。

## 精度标准

| dtype | rtol | atol |
|-------|------|------|
| FP32 | 1e-5 | 1e-5 |
| FP16 | 1e-3 | 1e-3 |
| BF16 | 1e-2 | 1e-2 |

---

## 进化流程

```
Architect Agent 主循环（agents/architect/AGENT.md）:
  1. READ STATE — 读取 evolution/state.json 和最新评分
  2. ANALYZE — 分析谱系和 profiling 数据
  3. DESIGN — 输出 DESIGN.md + PLAN.md
  4. DISPATCH DEV — 分发给 Developer 实现
  5. DISPATCH REV — 分发给 Reviewer 审查
  6. DISPATCH TEST — 分发给 Tester 构建/部署/测试
  7. EVALUATE — 分析结果，决定接受/拒绝
  8. UPDATE STATE — 更新 state.json、谱系、best/
  9. GOTO 1

Supervisor Agent（仅在停滞时介入）:
  - stall_counter >= threshold → 生成重定向指令
  - failed_attempts >= threshold → 诊断失败模式
  → 写入 evolution/redirects/，Architect 下轮读取
```

评分函数：`scoring/score.sh workspace/runs/{op_name}/attempts/step_{N} scoring/configs/{op_name}.json` → `evolution/scores/v{N}.json`
