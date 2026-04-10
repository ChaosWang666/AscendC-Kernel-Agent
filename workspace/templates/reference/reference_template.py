"""
PyTorch 参考实现模板

此文件定义两个模型类：
- Model: PyTorch 原生实现（参考标准）
- ModelNew: 使用自定义 Ascend C 算子的实现

以及数据生成函数：
- get_inputs(config): 生成测试输入
- get_init_inputs(): 模型初始化参数（无参调用）

=== test_correctness.py / test_performance.py 对本文件的隐式契约 ===

1. `get_init_inputs()` 被**无参数**调用，返回值会被 `Model(*init)` / `ModelNew(*init)`
   展开为位置参数。**架构参数**（如 hidden_size、num_layers）必须在这里硬编码，
   per-config 无法变化；scoring config 只能变 tensor 形状 / dtype。

2. `get_inputs(config)` 被**带 dict 参数**调用，若抛 TypeError 则 fallback 到
   `get_inputs()` 无参调用。建议显式签名 `def get_inputs(config=None)`。

3. `Model` 与 `ModelNew` 的 `nn.Module` 成员**创建顺序必须完全相同**。
   test_correctness.py 做 `manual_seed(SEED); Model(*init); manual_seed(SEED); ModelNew(*init)`
   以保证权重一致。有状态算子的 `ModelNew` 必须保留对应的 `self.xxx = nn.Layer(...)`
   作为权重容器，即便 forward 不调用它。

4. `Model.forward(*inputs)` 返回**单个 tensor**（不可是 tuple），因为后续会做
   `ref_output.shape` 与 `torch.allclose(ref_output, new_output)` 比较。

5. 同一个 Model 实例会被连续调用 5 次（NUM_TRIALS=5），每次使用新 `get_inputs()` 的
   张量。Model 的状态不应在 forward 间持有（可持有权重但不持有样本间状态）。
"""

import torch
import torch.nn as nn


class Model(nn.Module):
    """PyTorch 原生实现（正确性参考标准）"""

    def forward(self, x, y):
        # TODO: 替换为实际算子逻辑
        return x + y


class ModelNew(nn.Module):
    """使用自定义 Ascend C 算子的实现"""

    def forward(self, x, y):
        # TODO: 替换为自定义算子调用
        import custom_ops_lib
        return custom_ops_lib.add_custom(x, y)


def get_inputs(config=None):
    """
    生成测试输入张量

    Args:
        config: dict with 'shape' and 'dtype' keys
                e.g. {'shape': [4096], 'dtype': 'fp32'}
    """
    if config is None:
        config = {'shape': [4096], 'dtype': 'fp32'}

    shape = config.get('shape', [4096])
    dtype_str = config.get('dtype', 'fp32')

    dtype_map = {
        'fp32': torch.float32,
        'float32': torch.float32,
        'fp16': torch.float16,
        'float16': torch.float16,
        'bf16': torch.bfloat16,
        'bfloat16': torch.bfloat16,
    }
    dtype = dtype_map.get(dtype_str, torch.float32)

    x = torch.randn(*shape, dtype=dtype)
    y = torch.randn(*shape, dtype=dtype)
    return [x, y]


def get_init_inputs():
    """模型初始化参数（无状态算子返回空列表）"""
    return []
