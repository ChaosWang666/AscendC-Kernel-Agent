# AscendC Kernel Agent

## 项目概述

自主 Ascend C 算子生成与进化系统。核心公式：`Vary(P_t) = Agent(P_t, K, f)`
- **P_t**: 历史版本谱系（git commits + 评分）
- **K**: 领域知识库（本文件索引）
- **f**: 评分函数 `scoring/score.sh`（正确性 + 性能）

架构：`evolution/supervisor.py` → `Kernel Evolution Agent` → `scoring/score.sh` → git commit

工作区模型：`workspace/runs/{op_name}/best/`（只读基线） + `workspace/runs/{op_name}/attempts/step_{N}/`（候选目录）

参考论文：`./AVO-paper/`
技术规格：`./spec.md`

---

## 知识库地图

### Skills（Layer 2）— 按需加载

相对路径前缀：`Knowledge-base/coding-skills/skills/skills/`

| Skill | 用途 | 路径 |
|-------|------|------|
| ascendc-tiling-design | Tiling 策略（归约/广播/逐元素/转换/MatMul/卷积） | `ascendc-tiling-design/SKILL.md` |
| ascendc-api-best-practices | API 参数限制、优化模式（Adds/Muls、Double Buffer） | `ascendc-api-best-practices/SKILL.md` |
| ascendc-npu-arch | 芯片架构代际 A2/A3/A5、条件编译 | `ascendc-npu-arch/SKILL.md` |
| ascendc-precision-debug | 精度问题诊断决策树（症状→诊断→修复） | `ascendc-precision-debug/SKILL.md` |
| ascendc-runtime-debug | 运行时错误码 161xxx/361xxx/561xxx、Kernel 挂死 | `ascendc-runtime-debug/SKILL.md` |
| ops-profiling | 性能采集（msprof）、8 CSV 指标分析、perf_summary | `ops-profiling/SKILL.md` |
| ops-precision-standard | 精度阈值标准（按 dtype 的 atol/rtol） | `ops-precision-standard/SKILL.md` |
| ascendc-direct-invoke-template | Kernel 直调工程骨架（CMake + gen_golden + run.sh） | `ascendc-direct-invoke-template/SKILL.md` |
| ascendc-docs-search | 本地 + 在线 API 文档搜索 | `ascendc-docs-search/SKILL.md` |
| ascendc-env-check | NPU 设备查询、CANN 环境验证 | `ascendc-env-check/SKILL.md` |
| ascendc-code-review | 假设检验法代码审查（7 维 100 分制） | `ascendc-code-review/SKILL.md` |
| ascendc-ut-develop | 单元测试开发与覆盖增强 | `ascendc-ut-develop/SKILL.md` |
| ascendc-st-design | 系统测试用例设计（aclnn 接口测试） | `ascendc-st-design/SKILL.md` |
| ascendc-whitebox-design | 白盒测试用例生成 | `ascendc-whitebox-design/SKILL.md` |
| ascendc-task-focus | 长任务聚焦管理 | `ascendc-task-focus/SKILL.md` |
| ascendc-registry-invoke-to-direct-invoke | aclnn 注册调用转 Kernel 直调 | `ascendc-registry-invoke-to-direct-invoke/SKILL.md` |

### Agents（参考知识）

相对路径前缀：`Knowledge-base/coding-skills/skills/agents/`

| Agent | 角色 | 路径 |
|-------|------|------|
| ascendc-ops-architect | 算子架构师（需求分析 → 技术方案） | `ascendc-ops-architect/AGENT.md` |
| ascendc-kernel-architect | 内核架构师（需求 → API 映射 → 设计文档） | `ascendc-kernel-architect/ascendc-kernel-architect.md` |
| ascendc-kernel-developer | 内核开发者（代码实现 → 编译 → 测试 → 性能） | `ascendc-kernel-developer/ascendc-kernel-developer.md` |
| ascendc-kernel-reviewer | 内核审查者（7 维评分 + 精度 + 性能验证） | `ascendc-kernel-reviewer/ascendc-kernel-reviewer.md` |
| ascendc-ops-reviewer | 算子审查者（快速 / 完整审查模式） | `ascendc-ops-reviewer/AGENT.md` |

Team 工作流：`Knowledge-base/coding-skills/skills/teams/ops-direct-invoke/AGENTS.md`

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

详细导航索引：
- `Knowledge-base/INDEX-attention-ops.md`
- `Knowledge-base/INDEX-api-reference.md`
- `Knowledge-base/INDEX-examples.md`

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

### Kernel 基本结构
```cpp
// 内核文件扩展名：.asc
class OpKernel {
    __aicore__ inline void Init(...) { /* UB 分配 */ }
    __aicore__ inline void Process() {
        CopyIn();   // GM → UB (DataCopy/DataCopyPad)
        Compute();  // UB 上计算
        CopyOut();  // UB → GM
    }
};

// 启动
kernel<<<blockDim, nullptr, stream>>>(args...);
aclrtSynchronizeStream(stream);
```

### Pipeline 同步
- **EnQue/DeQue**：管线阶段间同步（推荐）
- **PipeBarrier<PIPE_*>()**：粗粒度全管线屏障（慎用）
- **SetFlag/GetFlag**：事件同步

### 关键模式
- **Double Buffering**：`BUFFER_NUM = 2`，一块加载一块计算
- **多核分发**：`GetBlockIdx()` 获取核 ID，`ACL_DEV_ATTR_*` 查询核数
- **Scalar 优化**：用 `Adds/Muls` 代替 `Duplicate + Add/Mul`

### 架构代号
- A2 (910): arch32, DAV_1001
- A3 (910B/310P): arch32, DAV_2201/DAV_3002
- A5 (950): arch35, DAV_3510（支持 Regbase、SIMT、FP8）

---

## 编译

### Direct Invoke（直调模式）
```bash
cd workspace/runs/{op_name}/best
mkdir -p build && cd build
cmake .. -DASCEND_PRODUCT_TYPE={chip} -DASCEND_RUN_MODE=ONBOARD
make -j
```

### 运行
```bash
cd workspace/runs/{op_name}/best
bash run.sh
```

---

## 测试标准

### 精度阈值
| dtype | rtol | atol |
|-------|------|------|
| FP32 | 1e-5 | 1e-5 |
| FP16 | 1e-3 | 1e-3 |
| BF16 | 1e-2 | 1e-2 |

### 性能采集
```bash
msprof op --warm-up=10 --output=./msprof_output ./demo
```

### 性能标准
| 指标 | 优秀 | 可改进 | 瓶颈 |
|------|------|--------|------|
| Task Duration vs 理论 | <20% gap | 20-50% | >50% |
| 多核负载均衡 | <10% 方差 | 10-30% | >30% |
| Double Buffer 重叠 | >30% | 10-30% | <10% |

---

## 进化流程

```
supervisor.py 主循环:
  1. 准备上下文 (谱系 P_t + 当前内核 x_t + 评分 f(x_t))
  2. 启动 Kernel Evolution Agent 会话
  3. Agent 执行 Edit-Evaluate-Diagnose 循环
  4. 通过正确性 + 性能提升 → git commit → 更新谱系
  5. 检测停滞 → 生成重定向指令
  6. 循环直到停止条件
```

评分函数：`scoring/score.sh workspace/runs/{op_name}/best scoring/configs/{op_name}.json` → `evolution/scores/v{N}.json`
