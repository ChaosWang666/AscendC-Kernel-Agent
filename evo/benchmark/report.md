# MultiKernelBench × EVO 单轮编译准确率评测

- **日期**：2026-04-16 09:44
- **模型**：claude-opus-4-6
- **策略**：`ascendc_evo_shot`（EVO seed 检索 + add_shot few-shot 模板）
- **语言/后端**：AscendC / Ascend910B2
- **轮数**：1（单轮，无 refinement）
- **评测维度**：仅编译成功率（不跑 correctness / performance）
- **结果文件**：`../MultiKernelBench/output/ascendc/evo_shot/0.0-1.0/claude-opus-4-6/run0/compile_only_results.json`

## 总体

| 总算子数 | 编译成功 | 成功率 |
|---------|---------|-------|
| 8 | 8 | **100.0%** |

## 按类别编译准确率

| Category | Total | Compiled | Rate | Top Failure Modes |
|----------|-------|----------|------|-------------------|
| activation | 3 | 3 | 100.0% | - |
| arch | 4 | 4 | 100.0% | - |
| attention | 0 | 0 | 0.0% | - |
| broadcast | 0 | 0 | 0.0% | - |
| convolution | 0 | 0 | 0.0% | - |
| fuse | 0 | 0 | 0.0% | - |
| index | 0 | 0 | 0.0% | - |
| loss | 1 | 1 | 100.0% | - |
| math | 0 | 0 | 0.0% | - |
| matmul | 0 | 0 | 0.0% | - |
| normalization | 0 | 0 | 0.0% | - |
| optimizer | 0 | 0 | 0.0% | - |
| pooling | 0 | 0 | 0.0% | - |
| reduce | 0 | 0 | 0.0% | - |
| resize | 0 | 0 | 0.0% | - |

## 失败样本（每类抽 1 个）

## 原始数据

- 详细结果：`../MultiKernelBench/output/ascendc/evo_shot/0.0-1.0/claude-opus-4-6/run0/compile_only_results.json`
- 生成输出目录：`output/ascendc/evo_shot/0.0-1.0/claude-opus-4-6/run0`