# AscendC Kernel Agent Team

## 团队概览

自主 Ascend C 算子生成与进化系统，由 6 个 Agent 协作完成从需求理解到报告生成的全流程。

核心公式：`Vary(P_t) = Agent(P_t, K, f)`

## 角色定义

| Agent | 角色 | 职责 | 派发时机 |
|-------|------|------|---------|
| **Architect** | 主 Agent | 任务理解、架构设计、任务分发、流程编排 | 每轮主循环 |
| **Developer** | 代码编写 | op_host / op_kernel / tiling 实现，编译调试 | Architect Step 4 |
| **Reviewer** | 代码审查 | 独立静态审查、DESIGN.md 合规校验、7 维质量评分 | Architect Step 5 **（与 Tester 并行）**|
| **Tester** | 测试验证 | 自定义算子工程构建、部署、PyTorch 框架测试、性能采集 | Architect Step 6 **（与 Reviewer 并行）**|
| **Supervisor** | 进化监督 | 主动监测趋势 + 停滞/失败/方向重复干预 | 主动触发 + Architect Step 2 被动 |
| **Reporter** | 报告生成 | 综合所有进化痕迹生成最终 `report.md` | 收敛判定时触发（见下文）|

## 团队工作流（并行化）

```
用户提交算子需求
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│  Architect Agent（主 Agent，全流程编排）                       │
│                                                                │
│  Step 1: READ STATE                                            │
│  Step 2: ANALYZE（+ 消费 Supervisor 信号）                     │
│  Step 2.5: KNOWLEDGE RETRIEVAL（强制查 L3 docs + L2 sources）  │
│  Step 3: DESIGN（DESIGN.md + PLAN.md）                         │
│  Step 4: DISPATCH Developer（串行：必须先出代码）               │
│                                                                │
│  Step 5+6: 并行派发 Reviewer + Tester                          │
│  ┌─────────┐    ┌──────────────┐    ┌───────────────┐         │
│  │Developer│───►│   Reviewer    │    │    Tester     │         │
│  │         │    │ (静态检视+    │    │ (跑 score.sh) │         │
│  │op_host/ │    │  docs 合规+   │    │ 编译/部署/     │         │
│  │op_kernel│    │  独立编译)    │    │ PyTorch 测试)  │         │
│  └─────────┘    └──────┬───────┘    └───────┬───────┘         │
│                        │      合流           │                  │
│                        ▼  ─────────────────► ▼                 │
│  Step 7: EVALUATE（综合 REVIEW.md + v{N}.json）                │
│  Step 8: UPDATE STATE → 若收敛触发 Reporter                    │
└──────────────────────────────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────────────────────────────┐
│  Supervisor Agent（主动监测 + 停滞介入）                       │
│  每 3 轮自检趋势；stall/failure/direction_repeat 即 WARN/ALERT/BLOCK │
└──────────────────────────────────────────────────────────────┘
    │
    ▼ （收敛时）
┌──────────────────────────────────────────────────────────────┐
│  Reporter Agent（LLM 综合生成报告）                            │
│  读 state.json + scores + logs + DESIGN.md → 输出 report.md    │
└──────────────────────────────────────────────────────────────┘
```

---

## Agent 调用协议 ⭐️

### 派发方式

**首选**：Claude Code `Agent()` 工具（in-session subagent，最稳定，支持 tool 继承）

```python
Agent(
    description="<role>: <op_name> v{N}",
    subagent_type="general-purpose",
    prompt="<详见下方 Prompt 模板>"
)
```

**兜底**：CLI `claude --print`（独立进程；不共享工具权限，不推荐嵌套使用）

### Prompt 模板（所有派发必须包含）

```
你是 <Role> Agent，读取 agents/<role>/AGENT.md 作为角色定义。

【输入】
- 设计文档: {CANDIDATE_DIR}/docs/DESIGN.md
- 实现计划: {CANDIDATE_DIR}/docs/PLAN.md
- 算子工程: {CANDIDATE_DIR}/{OpName}Custom/
- 测试配置: scoring/configs/{op_name}.json
- 参考实现: workspace/runs/{op_name}/test/reference.py

【输出】
- <具体文件路径> + YAML trailer（status: success|fail, summary: ...）

【约束】
- 预算: max_session_duration=10m
- 环境: 所有 bash 调用必须先 `source /usr/local/Ascend/ascend-toolkit/set_env.sh`
- 禁止: <角色特定禁止动作>
```

### 并行派发规则

**独立任务 → 单消息多 Agent 调用**（一次消息内发多个 `Agent()` 工具块）

```python
# ✅ 正确：一次消息发两个 Agent 调用（Reviewer + Tester 并行）
[
    Agent(description="Reviewer: ...", prompt="..."),
    Agent(description="Tester: ...",   prompt="...")
]
```

**依赖任务 → 顺序调用**（前者完成后再启动）

```python
# ✅ 正确：Dev 必须先完成，才能派发 Rev/Test
result_dev = Agent(description="Developer: ...", prompt="...")
# 等 Dev 返回后
[Agent(...Reviewer...), Agent(...Tester...)]  # 此时再并行
```

**依赖判定规则**：
- 若 agent B 读取 agent A 的输出文件 → 必须顺序
- 若 agent B 与 agent A 只读共享输入 → 可并行

### 返回契约（所有子 agent 必须遵守）

子 agent 产出文件**底部**写入 YAML trailer：

```yaml
---
role: reviewer | tester | developer | reporter | supervisor
status: success | partial | fail
summary: 一句话说明
artifacts:
  - path: {CANDIDATE_DIR}/docs/REVIEW.md
  - path: evolution/scores/v{N}.json
next_action: continue | fail_fast | escalate
details:
  # 角色特定字段
---
```

Architect 读取 trailer 判断是否合流成功，据此决定下一步。

### 并行多变体开发（高级）

当 Architect 对参数选择不确定时（如 RESERVE=4/8/12KB），可**同时派发 N 个 Developer**，每个尝试不同变体。完成后对比 A/B 挑最优。

参考 `superpowers:dispatching-parallel-agents` skill。

---

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

## 测试流程

```
1. 构建算子工程     → msopgen gen + build.sh → custom_opp_*.run
2. 部署算子包       → ./custom_opp_*.run → OPP 目录
3. 构建 Python 绑定 → CppExtension setup.py → custom_ops_lib wheel
4. Seed 正确性     → PyTorch 最小尺寸自测（秒级）
5. Boundary 正确性 → 边界/多秩/极值（诊断性，非阻塞）
6. Smoke 正确性    → 小尺寸验证
7. Representative  → 正确性 + 主性能测量
8. Stress（可选）  → 大尺寸目标规模（仅通过提交门槛时）
9. 聚合评分        → evolution/scores/v{N}.json（含 boundary_summary + test_coverage）
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
│   └── reference.py               — PyTorch 参考实现（支持 input_mode 极值注入）

workspace/deploy/opp/               — 算子部署目录（全局共享）
```

## 进化主循环

```
EVOLUTION LOOP:
  Step 1: READ STATE
  Step 2: ANALYZE
    - 消费 Supervisor redirect（若有）
    - 墙钟超时检查
  Step 2.5: KNOWLEDGE RETRIEVAL（强制）
    - L3 docs 查询（必需，ascendc-kb-docs skill）
    - L2 sources 查询
  Step 3: DESIGN → 输出 DESIGN.md + PLAN.md
  Step 4: DISPATCH Developer （串行）
  Step 5+6: DISPATCH Reviewer + Tester （并行）
  Step 7: EVALUATE
  Step 8: UPDATE STATE
    - 接受 → 晋升 best/，检测是否收敛 → 触发 Reporter
    - 拒绝 → stall_counter++
  Step 9: GOTO 1

SUPERVISOR MONITORING（主动，每 3 轮自检一次）:
  - stall_counter >= 3       → WARN（提示 paired A/B 重测）
  - failed_attempts >= 5     → ALERT + REDIRECT
  - direction_repeated >= 2  → BLOCK（禁止该方向）
  - variance_high            → ALERT（建议增加 trials）
  - knowledge_gap            → BLOCK（驳回补 L3 docs）
  - 3 轮无提升 mean           → hint redirect

REPORTER TRIGGER（收敛时）:
  - consecutive_redirects >= max
  - stall_counter >= threshold AND Supervisor TERMINATE_SUCCESS
  - total_attempts >= max_versions
  → 派发 Reporter 读所有进化痕迹 → 生成 report.md
```

## 评分函数

`scoring/score.sh workspace/runs/{op_name}/attempts/step_{N} scoring/configs/{op_name}.json`

退出码契约：
- `0` 完整成功（correctness_total == 1.0）
- `1` environment 预检失败
- `2` compile 失败
- `3` deploy 失败
- `4` pybind 失败
- `5` correctness 失败
- `6` performance 失败（仅记录）

## 启动方式

直接用 Claude Code 加载本文件（`agents/AGENTS.md`），Architect Agent 读取后自主执行进化循环。

```bash
claude --print -p "读取 agents/AGENTS.md 和 evolution/config.yaml，开始执行进化循环"
```

---

## 关键约束

- **Agent 调用必须遵守 YAML trailer 协议**
- **Reviewer 和 Tester 必须并行派发**（不是顺序）
- **Architect Step 2.5 KNOWLEDGE RETRIEVAL 是强制门槛**（无 L3 docs 引用则 Reviewer 判 FAIL）
- **Supervisor 主动监测 stall_threshold=3**（不是被动等 5）
- **收敛时必须派发 Reporter**（不写代码，用 LLM 综合）
