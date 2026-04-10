# AscendC Kernel Agent Team

## 团队概览

自主 Ascend C 算子生成与进化系统，由 5 个 Agent 协作完成从需求理解到性能优化的全流程。

核心公式：`Vary(P_t) = Agent(P_t, K, f)`

## 角色定义

| Agent | 角色 | 职责 |
|-------|------|------|
| **Architect** | 主 Agent | 任务理解、架构设计、任务分发、流程编排 |
| **Developer** | 代码编写 | op_host / op_kernel / tiling 实现，编译调试 |
| **Reviewer** | 代码审查 | 独立构建验证、7 维质量评分、精度验证 |
| **Tester** | 测试验证 | 自定义算子工程构建、部署、PyTorch 框架测试 |
| **Supervisor** | 进化监督 | 不干预主 Agent 执行，仅在停滞时介入重定向 |

## 团队工作流

```
用户提交算子需求
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  Architect Agent（主 Agent，全流程编排）              │
│                                                       │
│  1. ANALYZE  — 解析算子需求，确定计算模式              │
│  2. DESIGN   — 架构设计（Tiling / Buffer / Pipeline） │
│  3. DISPATCH — 分发任务给 Developer 和 Tester          │
│  4. ITERATE  — 根据反馈迭代优化                        │
│                                                       │
│  ┌─────────┐    ┌──────────┐    ┌─────────┐          │
│  │Developer│◄──►│ Reviewer │    │ Tester  │          │
│  │         │    │          │    │         │          │
│  │op_host/ │    │7维评分    │    │构建部署  │          │
│  │op_kernel│    │精度验证   │    │PyTorch  │          │
│  │tiling   │    │独立验证   │    │正确性   │          │
│  └─────────┘    └──────────┘    │性能采集  │          │
│                                  └─────────┘          │
└─────────────────────────────────────────────────────┘
    │
    │  进化循环（多版本迭代）
    ▼
┌─────────────────────────────────────────────────────┐
│  Supervisor Agent（仅在停滞时介入）                    │
│                                                       │
│  监控 state.json → 检测停滞 → 生成重定向指令           │
│  不控制 Architect 的决策，不参与日常执行                │
└─────────────────────────────────────────────────────┘
```

## 自定义算子工程结构

本系统生成的是**完整的自定义算子工程**，而非 Kernel 直调：

```
{OpName}Custom/
├── {op_name}_custom.json        — 算子定义 JSON（输入/输出/类型/格式）
├── CMakeLists.txt                — 根构建配置
├── CMakePresets.json             — 构建预设（芯片型号/路径配置）
├── build.sh                      — 构建编排脚本
├── op_host/                      — Host 侧（算子注册 + Tiling 策略）
│   ├── CMakeLists.txt
│   ├── {op_name}_custom.cpp     — OpDef 注册 + TilingFunc + InferShape
│   └── {op_name}_custom_tiling.h — TilingData 结构定义
├── op_kernel/                    — Device 侧（Ascend C 内核）
│   ├── CMakeLists.txt
│   └── {op_name}_custom.cpp     — AscendC Kernel 实现
└── build_out/                    — 构建产物
    ├── custom_opp_*.run          — 自安装部署包
    └── op_api/lib/libcust_opapi.so
```

## 测试流程（参考 MultiKernelBench）

```
1. 构建算子工程    → msopgen gen + build.sh → custom_opp_*.run
2. 部署算子包      → ./custom_opp_*.run → OPP 目录
3. 构建 Python 绑定 → CppExtension setup.py → custom_ops_lib wheel
4. 正确性测试      → PyTorch: Model vs ModelNew + torch.allclose
5. 性能测试        → NPU Event timing: warmup + 多轮测量
```

## 工作区模型

```
workspace/runs/{op_name}/
├── best/                           — 当前最佳版本（只读基线）
│   └── {OpName}Custom/
├── attempts/step_{N}/              — 候选版本（每步创建，评估后清理）
│   └── {OpName}Custom/
├── test/                           — 测试基础设施
│   ├── CppExtension/              — Python 绑定构建
│   │   ├── setup.py
│   │   ├── build_and_run.sh
│   │   └── csrc/
│   │       ├── op.cpp
│   │       └── pytorch_npu_helper.hpp
│   └── reference.py               — PyTorch 参考实现

workspace/deploy/opp/               — 算子部署目录（全局共享）
```

## 进化主循环

Architect Agent 驱动主循环，Supervisor 仅在停滞时介入：

```
EVOLUTION LOOP:
  1. Architect: 分析当前状态和 profiling 数据
  2. Architect: 设计优化方向，生成 DESIGN.md + PLAN.md
  3. Developer: 实现代码修改（op_host + op_kernel）
  4. Reviewer:  代码审查（通过/修复循环，最多 3 轮）
  5. Tester:    构建 → 部署 → 正确性测试 → 性能测试
  6. Architect: 评估结果，决定接受/拒绝/迭代
  7. 更新 state.json，若接受则晋升为 best/
  8. GOTO 1

SUPERVISOR INTERVENTION（仅在以下情况触发）:
  - stall_counter >= threshold（性能停滞）
  - failed_attempts >= threshold（连续失败）
  → 生成重定向指令，注入 Architect 的下一轮 ANALYZE
```

## 评分函数

`scoring/score.sh workspace/runs/{op_name}/attempts/step_{N} scoring/configs/{op_name}.json`

分级评分流程：
1. 构建自定义算子工程（compile + deploy + pybind）
2. Smoke 正确性测试 → 失败提前退出
3. Representative 正确性测试 → 失败提前退出
4. Representative 性能测试 → 检查提交门槛
5. Stress 测试（若满足门槛）
6. 聚合评分 → `evolution/scores/v{N}.json`

## 启动方式

直接用 Claude Code 加载本文件（`agents/AGENTS.md`），Architect Agent 读取后自主执行进化循环。

```bash
# 启动进化
claude --print -p "读取 agents/AGENTS.md 和 evolution/config.yaml，开始执行进化循环"
```
