# gelu_custom

## 基本信息

- **算子名称**：gelu_custom
- **目标芯片**：Ascend910B
- **数据类型**：fp32, fp16

## 数学定义

GELU（tanh 近似）：
```
GELU(x) = 0.5 * x * (1 + tanh(sqrt(2/π) * (x + 0.044715 * x^3)))
```

## 输入张量

| 名称 | 形状 | 数据类型 | 说明 |
|------|------|---------|------|
| x | [N] 或 [M, N] | fp32/fp16 | 输入张量 |

## 输出张量

| 名称 | 形状 | 数据类型 | 说明 |
|------|------|---------|------|
| z | 与输入相同 | fp32/fp16 | GELU 激活结果 |

## 计算特征

- **计算模式**：逐元素 (Elementwise)
- **计算密集度**：中等（涉及 exp/tanh 操作）
- **访存量**：2 * N * sizeof(dtype) bytes（读 1 个输入 + 写 1 个输出）

## PyTorch 参考实现

```python
class Model(nn.Module):
    def forward(self, x):
        return torch.nn.functional.gelu(x, approximate='tanh')

class ModelNew(nn.Module):
    def forward(self, x):
        import custom_ops_lib
        return custom_ops_lib.gelu_custom(x)
```

## 性能指标

- **主指标**：latency_us（延迟，越低越好）
- 目标输入：[4096, 393216]（~1.6B 元素）
