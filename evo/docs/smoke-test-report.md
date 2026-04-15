# EVO 框架 Smoke Test 报告

**日期**：2026-04-15
**分支**：`EVO`
**范围**：Phase A 框架完整性（4 项） + Phase B 端到端单步（multigate-verifier ↔ score.sh ↔ memory-curator）

## Phase A：框架完整性（无 NPU）

| 验证项 | 结果 |
|-------|------|
| Memory Bank bootstrap（解析 seed → bank.jsonl）| ✓ 24 条（14 api_template + 10 best_practice） |
| 14 个 api_template 的 `target_path` 指向 Knowledge-base 实际存在 | ✓ 全部有效 |
| `config.yaml` 10 个顶层字段齐全（mode/queue/retrieval/q_update/...）| ✓ |
| `verifier.exit_code_map` 覆盖退出码 0-6 | ✓ |
| docs 交叉引用路径 | ✓（修复 README 3 处漏 `evo/` 前缀） |
| JSON 持久化文件（q_values.json/stats.json/campaign.json）有效 | ✓ |
| Retrieval-policy dry-run（dense top-K + ε-greedy top-N）| ✓（pool<N 时优雅降级到 \|pool\|） |
| Memory-curator Q-update dry-run（Eq.3 + PopArt + clip）| ✓ 数学对齐论文，原子写入，Q_clip 有界生效 |

## Phase B：端到端单步

### 环境
- NPU：16× Ascend910（Health=OK）
- CANN：8.5.0
- torch_npu：2.6.0.post6，`npu.is_available()=True`

### Multigate Verifier 真实调用

以 `workspace/runs/gelu_custom/best/GeluCustom`（AVO v14 best）为测试 kernel，复制到 `workspace/runs/gelu_custom/attempts/step_evo_smoke/`。

**Anti-hack rule-based**：扫 `op_kernel/*.{cpp,h}`（2 个文件），0 违规 → **g_hack = 1**

**score.sh 全链路**（共 8 步）：

| Step | 耗时 | 结果 |
|------|------|------|
| 0 env preflight | 4.9s | ✓ |
| 1 compile | 11.4s | ✓ |
| 2 deploy | 0.1s | ✓ |
| 3 pybind | 37.3s | ✓ |
| 3.5 seed correctness | 10.2s | ✓ |
| 3.7 boundary（非阻塞）| 9.7s | ✓ |
| 4 smoke correctness | 8.7s | ✓ |
| 5 representative correctness | 8.9s | ✓ |
| 7 representative performance | 8.6s | ✓ |
| 9 聚合评分 → v15.json | — | ✓ |

**退出码**：0（correctness=1.0, performance=38.07us, -2.0% vs AVO best 37.32—噪声范围内）

**EVO 四元组映射**：
```
o_t = (g_hack=1, g_comp=1, g_corr=1, ℓ_lat=38.07 us)
g_feas = 1 ∧ 1 ∧ 1 = 1
```

### Memory-curator 真实持久化

首次 Stage 1 step，r_1 = +1。

| 持久化产物 | 结果 |
|-----------|------|
| `bank.jsonl` | +1 条 type=trace（kernel snippet + tags）|
| `q_values.json` | 3 条 api_template 的 Q_1: 0.0 → +0.1 (α·r=0.1·1=0.1 符合 Eq.3) |
| `start_points/gelu_custom/{id}/` | ✓ 64 个源文件（op_host/op_kernel/CMake 等），跳过 build_out/ 中失效 symlink |
| `state/episodes/gelu_custom/trajectory.jsonl` | +1 行（t=0, stage=1, r=+1, ℓ=38.07）|
| `state/episodes/gelu_custom/state.json` | stage=refining, b_t=38.07, P_x=1, iter=1 |
| `state/campaign.json` | status=running, current_op=gelu_custom, current_stage=refining |
| `state/episodes/gelu_custom/anti_hack_log.jsonl` | +1 条（rule_based passed）|

## 验证意义

本次 smoke 覆盖的 EVO 关键衔接点：

1. **Multigate-verifier ↔ AVO score.sh**：退出码 0-6 → 四元组的映射真实生效
2. **Anti-hack rule-based** on 真实 kernel 文件扫描（禁 import / 禁 API 全部通过）
3. **Memory Bank 三文件原子持久化**（bank.jsonl append-only；q_values.json RMW；campaign.json RMW）
4. **Eq. 3 MC Q 更新** 在真实数值上符合公式（Q_1 = 0 + 0.1·(+1 - 0) = 0.1）
5. **P(x) 起点集构建**（把 feasible kernel 完整 snapshot 入池，排除 build_out）
6. **Trajectory + Episode state** 按 `evo/docs/` 定义的 schema 写入

## 未覆盖的部分（待下一轮）

1. **Developer 生成 kernel**（$G_\theta$ 派发未触发）—— 本 smoke 用的是 AVO 已验证 kernel 作为起点
2. **Stage 2 Refining 循环** —— 需要在 Stage 1 有 P(x) 后再跑 2+ 步才能验证：
   - `tanh(log b - log ℓ)` 相对奖励
   - PopArt μ/σ 在多次观测上的收敛
   - Q_2 更新对连续 start-point 选择的影响
3. **Retrieval-policy 真实 Agent 派发**（当前用 Python 模拟逻辑）
4. **跨算子迁移**（当前 queue 只有 gelu_custom）
5. **Anti-hack model-based LLM auditor** 未触发

## 推荐下一步

在 EVO 分支 基础上跑一次 **最小 Stage 2 循环（2 步）**：
1. 用当前 `P(x)`（有 1 个起点）触发 `stage2-refiner` Agent
2. 让它派发 Developer 做一次实际改写（e.g., 换 BUFFER_NUM 或 tileLength）
3. 跑 score.sh 得到新 ℓ_lat
4. 真实执行 Eq.5 tanh reward + PopArt 归一 + Q_2 更新
5. 观察 `stats.json` 的 μ/σ 变化，`q_values.json` Q_2 列首次非零

这会完整覆盖 Stage 2 全部数学。
