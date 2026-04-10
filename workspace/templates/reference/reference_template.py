"""
PyTorch 参考实现模板

此文件定义两个模型类：
- Model: PyTorch 原生实现（参考标准）
- ModelNew: 使用自定义 Ascend C 算子的实现

以及数据生成函数：
- get_inputs(config): 生成测试输入
- get_init_inputs(): 模型初始化参数
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
