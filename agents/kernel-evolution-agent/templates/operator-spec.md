# 算子规格模板

## 基本信息

- **算子名称**：{{OP_NAME}}
- **目标芯片**：{{TARGET_CHIP}}（如 Ascend910B、Ascend950）
- **数据类型**：{{DTYPES}}（如 fp32, fp16, bf16）

## 数学定义

```
{{MATH_FORMULA}}
```

## 输入张量

| 名称 | 形状 | 数据类型 | 说明 |
|------|------|---------|------|
| {{INPUT_NAME}} | {{SHAPE}} | {{DTYPE}} | {{DESCRIPTION}} |

## 输出张量

| 名称 | 形状 | 数据类型 | 说明 |
|------|------|---------|------|
| {{OUTPUT_NAME}} | {{SHAPE}} | {{DTYPE}} | {{DESCRIPTION}} |

## 计算特征

- **计算模式**：{{MODE}}（归约/广播/逐元素/转换/MatMul/卷积）
- **计算复杂度**：{{FLOPS_FORMULA}}
- **访存量**：{{MEMORY_FORMULA}}
- **计算/访存比**：{{ARITHMETIC_INTENSITY}}

## 约束条件

- {{CONSTRAINT_1}}
- {{CONSTRAINT_2}}

## 参考实现（如有）

```python
# PyTorch/NumPy 参考
{{REFERENCE_CODE}}
```
