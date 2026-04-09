# 优化步骤 Prompt

## 上下文

你正在持续优化一个 Ascend C 内核。以下是当前状态。

### 算子规格
```
{{OPERATOR_SPEC}}
```

### 当前版本
版本号：v{{CURRENT_VERSION}}
评分：{{CURRENT_SCORE}} TFLOPS

### 当前内核代码
文件：`workspace/ops/{{OP_NAME}}/{{OP_NAME}}.asc`

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

产生一个新版本 x_{t+1}，使其：
1. 通过全部正确性测试（correctness_total = 1.0）
2. 性能优于当前最优版本

## 要求

- 每次专注**一个**优化方向
- 基于 profiling 数据做出数据驱动的决策
- 不要重复谱系中已失败的方向
- 如果 Supervisor 提供了指令，优先按指令探索
- 编辑前先理解当前代码
- 提交前确保全部正确性配置通过

## 评分命令

```bash
bash scoring/score.sh workspace/ops/{{OP_NAME}} scoring/configs/{{CONFIG}}.json
```

结果写入：`evolution/scores/v{{NEXT_VERSION}}.json`
