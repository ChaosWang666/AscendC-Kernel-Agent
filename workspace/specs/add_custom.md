# add_custom

## 基本信息

- **算子名称**：add_custom
- **目标芯片**：Ascend910B
- **数据类型**：fp32, fp16, bf16

## 数学定义

```
z = x + y  (逐元素加法)
```

## 输入张量

| 名称 | 形状 | 数据类型 | 说明 |
|------|------|---------|------|
| x | [N] | fp32/fp16/bf16 | 第一个输入 |
| y | [N] | fp32/fp16/bf16 | 第二个输入 |

## 输出张量

| 名称 | 形状 | 数据类型 | 说明 |
|------|------|---------|------|
| z | [N] | fp32/fp16/bf16 | 逐元素求和结果 |

## 计算特征

- **计算模式**：逐元素 (Elementwise)
- **计算复杂度**：N (FLOPs)
- **访存量**：3 * N * sizeof(dtype) bytes（读 2 个输入 + 写 1 个输出）
- **计算/访存比**：极低（访存密集型）

## 约束条件

- 输入 x 和 y 必须具有相同的形状和数据类型
- N 必须对齐到 32 字节边界
- 输出 z 与输入具有相同的形状和数据类型

## 自定义算子工程

工程名称：`AddCustom`

### 算子定义 JSON

```json
[{
    "op": "AddCustom",
    "language": "cpp",
    "input_desc": [
        {"name": "x", "param_type": "required", "format": ["ND"], "type": ["float", "float16", "bfloat16"]},
        {"name": "y", "param_type": "required", "format": ["ND"], "type": ["float", "float16", "bfloat16"]}
    ],
    "output_desc": [
        {"name": "z", "param_type": "required", "format": ["ND"], "type": ["float", "float16", "bfloat16"]}
    ]
}]
```

### PyTorch 参考实现

```python
class Model(nn.Module):
    def forward(self, x, y):
        return x + y

class ModelNew(nn.Module):
    def forward(self, x, y):
        import custom_ops_lib
        return custom_ops_lib.add_custom(x, y)
```

### CppExtension 绑定

```cpp
at::Tensor add_custom_impl_npu(const at::Tensor& x, const at::Tensor& y) {
    at::Tensor result = at::empty_like(x);
    EXEC_NPU_CMD(aclnnAddCustom, x, y, result);
    return result;
}
```

## 参考实现

```python
import numpy as np
z = x + y  # NumPy 逐元素加法
```

## 性能指标

- **主指标**：latency_us（延迟，越低越好）
- **辅助指标**：bandwidth_gbps（带宽利用率）
- 此算子为访存密集型，性能瓶颈在数据搬移而非计算
