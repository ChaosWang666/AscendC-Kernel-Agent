# 回归修复 Prompt

## 上下文

最近的优化尝试导致正确性回归。你需要诊断并修复。

### 算子规格
```
{{OPERATOR_SPEC}}
```

### 回归版本
候选目录：`{{CANDIDATE_DIR}}/{{OP_NAME}}.asc`

### 失败的测试配置
```json
{{FAILED_CONFIGS}}
```

### 误差信息
```
{{ERROR_DETAILS}}
```

### 上一个正确版本
版本号：v{{LAST_CORRECT_VERSION}}
可通过以下命令查看：
```bash
git show v{{LAST_CORRECT_VERSION}}:workspace/runs/{{OP_NAME}}/best/{{OP_NAME}}.asc
```

### 最近的代码变更
```bash
git diff v{{LAST_CORRECT_VERSION}}..HEAD -- workspace/runs/{{OP_NAME}}/
```

## 任务

1. **诊断**：确定正确性回归的根本原因
2. **修复**：在保留尽可能多的性能优化的前提下修复正确性
3. **验证**：确保全部配置通过正确性测试

## 诊断流程

1. 读取 `Knowledge-base/coding-skills/skills/skills/ascendc-precision-debug/SKILL.md` 的诊断决策树
2. 对比失败输出 vs golden 数据的误差模式：
   - 全零输出 → Pipeline 同步缺失
   - 大量 NaN/Inf → 精度溢出或除零
   - 系统性偏差 → Cast RoundMode 或算法错误
   - 随机误差增大 → 竞争条件或未初始化内存
3. 查看 `git diff` 定位导致回归的具体变更
4. 检查常见陷阱：
   - DataCopy 32B 对齐
   - EnQue/DeQue 配对
   - FP16 中间计算精度
   - Duplicate + 运算 vs Adds/Muls 等效性

## 约束

- 所有编辑在候选目录 `{{CANDIDATE_DIR}}` 中进行
- 优先保留性能优化，只回退必要的部分
- 如果无法在保留优化的前提下修复，可以完整回退到上一个正确版本
