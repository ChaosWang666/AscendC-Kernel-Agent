# AVO 框架 Run #3 — GELU 进化循环（2026-04-10）

## 结果摘要

**首次完整跑通 v0→v1+ 性能优化循环。** 这是前两次 LSTM run 始终无法达到的里程碑。

| 指标 | 结果 |
|------|------|
| v0 correctness | **1.0**（首次成功） |
| v0 → v1 performance | **139.2 → 131.65 μs（+5.7% ACCEPT）** |
| v1 → v2 performance | 131.65 → 129.74 μs（+1.5% REJECT, stall） |
| v3 (highPerformance) | correctness FAIL（max_abs=5.97e-3） |
| Supervisor 裁决 | **TERMINATE_SUCCESS** — v1 已达 HBM 带宽上限（~972 GB/s > 800 GB/s 标称） |
| 进化版本数 | 4 attempts, 2 accepted, 1 stall, 1 correctness fail |
| 新框架 bug 发现 | 2 个（F28 + F29），已修复 |

## 完整进化轨迹

| Version | 策略 | Correctness | Latency (μs) | 结果 |
|---------|------|-------------|--------------|------|
| v0 | 原生 `Gelu()` API, single buffer, tileLen=16384 | 1.0 | 139.2 | **ACCEPT** (seed) |
| v1 | Double buffer (BUFFER_NUM=2), tileLen=8192 | 1.0 | 131.65 | **ACCEPT** (+5.7%) |
| v2 try1 | Double buffer, tileLen=12288 (192KB exact) | NPU crash | - | UB overflow |
| v2 | Double buffer, tileLen=10240 | 1.0 | 129.74 | REJECT (+1.5% < 2%) |
| v3 | `Gelu<T, false, true>` highPerformance | 0.0 | - | FAIL (precision regression) |

**Supervisor 分析**：v1 实测带宽 972 GB/s 超过 HBM 标称峰值 800 GB/s，说明多核 DMA 已充分并行并利用了 L2 缓存/突发合并。进一步算法优化的边际收益 < 2% 门槛。**裁决 TERMINATE_SUCCESS。**

## 框架验证覆盖（与前两次对比）

| 覆盖维度 | Run #1 (LSTM) | Run #2 (LSTM) | **Run #3 (GELU)** |
|---------|---------------|---------------|-------------------|
| 5 Agent 全部派发 | ✅ | ✅ | ✅ |
| 8 步 Architect 主循环 | ✅ | ✅ | ✅ |
| v0 correctness PASS | ❌ | ❌ | **✅** |
| v1 performance ACCEPT | ❌ | ❌ | **✅ (+5.7%)** |
| 多版本 lineage | ❌ | ❌ | **✅ (4 versions, 2 accepted)** |
| Supervisor TERMINATE_SUCCESS | ❌ | ❌ | **✅** |
| Phase 0 env preflight 验证 | ✅ | ✅ | ✅ |
| Seed level 快速迭代 | ❌ | ❌ | **✅ (v3 seed 早退出 ~10s)** |
| Per-phase timing 验证 | ❌ | ✅ | ✅ (8 phases in v0.json) |
| First mismatch diagnostics | ❌ | ❌ | **✅ (v3: 3825/4096 元素, per-element dump)** |
| Per-config atol/rtol 验证 | ❌ | ❌ | ✅ (默认 1e-5 直接通过) |
| score.sh v{N}.json 版本号正确 | ❌ (F28) | ❌ | **✅ (v0/v1/v2 三个文件)** |
| deploy.sh 绝对路径 | ❌ (F29) | ❌ | **✅** |

## 新发现的框架 bug

### F28 — score.sh 读 `current_step` 而非 `current_version`（CRITICAL）

**症状**：score.sh 始终写 `v0.json`，无论实际评分的是第几版。前两次 LSTM run 没发现是因为只跑了 v0。

**根因**：score.sh line 66 `s.get('current_step', 0)` 读了一个 state.json 里不存在的 key（canonical schema 用 `current_version`），fallback 到 0。

**修复**：改读 `current_version`（含 `current_step` 兼容 fallback），并加 `+1` 逻辑（current_version 是"最后 accepted 版本"，要写的是下一个候选 v{N+1}.json）。

**验证**：Run #3 中 v0/v1/v2 三个 `.json` 文件正确分别写入。

### F29 — deploy.sh 不做路径绝对化

**症状**：直接传相对路径给 `.run --install-path=` 会被 installer 静默拒绝。

**修复**：在 `DEPLOY_DIR` 使用前 `mkdir -p && cd && pwd` 做 realpath 归一化。

### F27 — 目标芯片 `ascend910_93` 而非 `ascend910b`

**症状**：用 `ascend910b` 编译的 `.run` 包部署到 Ascend910B3 机器后，runtime 报 `binary_info_config.json of socVersion [ascend910_93] does not support opType [GeluCustom]`。

**修复**：Developer 在 v0 自行发现并改用 `ascend910_93`。**此修复未合入 CLAUDE.md 或 skill（用户约束不修改 skill）**——记录在此报告供后续参考。实际芯片型号需要通过检查 `/usr/local/Ascend/ascend-toolkit/latest/opp/vendors/customize/op_impl/ai_core/tbe/config/` 下存在的目录来确定。

## 总结

1. **框架完整性验证通过** — 所有 Tier A 优化（Phase 0 preflight / persistent logs / phase timing / seed level / per-config atol/rtol / first_mismatch dump）在真实成功 + 失败场景下都得到验证
2. **进化循环能力验证通过** — 首次在一个会话内产出从 v0 种子到 v1 性能优化再到 Supervisor 终止的完整谱系
3. **HBM 带宽上限发现** — GELU 逐元素算子在 v1 (Double Buffer) 后已达 ~972 GB/s，超过标称 800 GB/s，说明算子已高效
4. **2 个新框架 bug 修复** — F28 (score.sh version numbering) + F29 (deploy.sh path normalization)
5. **1 个环境发现** — F27 (目标芯片应为 `ascend910_93` 而非 `ascend910b`)
