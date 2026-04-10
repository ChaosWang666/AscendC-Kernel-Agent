# 优化设计 Prompt

## 上下文

你正在设计下一轮优化方案，目标是在保持正确性的前提下提升性能。

### 算子规格
```
{{OPERATOR_SPEC}}
```

### 当前版本
版本号：v{{CURRENT_VERSION}}
评分：{{CURRENT_SCORE}}

### 当前算子工程
候选目录：`{{CANDIDATE_DIR}}/{{OP_CAPITAL}}Custom/`
基线（只读）：`workspace/runs/{{OP_NAME}}/best/{{OP_CAPITAL}}Custom/`

### Profiling 数据摘要
```json
{{PROFILING_SUMMARY}}
```

### 版本谱系
```
{{LINEAGE_SUMMARY}}
```

### Supervisor 指令（如有）
```
{{DIRECTIVE}}
```

## 任务

分析当前版本的性能瓶颈，设计一个优化方案，输出更新的 DESIGN.md + PLAN.md。

## 设计要求

1. **瓶颈分析**：基于 profiling 数据，定位主要性能瓶颈
2. **优化方向**：选择**一个**主要优化方向
3. **变更范围**：明确列出需要修改的文件和具体修改点
4. **风险评估**：评估优化可能引入的正确性风险

## 优化方向参考

| 瓶颈信号 | 可能的优化方向 |
|---------|-------------|
| VEC ratio 高 | 利用 Cube 单元、指令级优化 |
| MTE2 ratio 高 | 数据复用、Double Buffer、减少搬移次数 |
| Scalar ratio 高 | 向量化、Adds/Muls 替代 Duplicate+Op |
| Pipeline bubble | 调整 EnQue/DeQue 时机、增加 Buffer 数 |
| UB 利用率低 | 增大 tileLength、改进 Buffer 规划 |
| 多核负载不均 | 改进多核切分策略 |

## 约束

- 不要重复谱系中已失败的优化方向
- 如果 Supervisor 提供了指令，优先按指令探索
- 修改范围应尽可能小（增量优化）
- 必须同时更新 op_host（Tiling）和 op_kernel（Kernel）如有必要
