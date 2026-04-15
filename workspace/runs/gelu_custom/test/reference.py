"""
gelu_custom 算子 PyTorch 参考实现

Model: PyTorch tanh-approximate GELU（正确性参考标准，匹配 Ascend C 实现）
ModelNew: 使用自定义 Ascend C 算子的 GELU 实现
"""

import torch
import torch.nn as nn


class Model(nn.Module):
    """PyTorch 原生实现（正确性参考标准）"""

    def forward(self, x):
        return torch.nn.functional.gelu(x, approximate='tanh')


class ModelNew(nn.Module):
    """使用自定义 Ascend C 算子的实现"""

    def forward(self, x):
        import custom_ops_lib
        return custom_ops_lib.gelu_custom(x)


def get_inputs(config=None):
    """生成测试输入张量"""
    if config is None:
        config = {'shape': [4096], 'dtype': 'fp32'}

    shape = config.get('shape', [4096])
    if isinstance(shape, int):
        shape = [shape]

    dtype_str = config.get('dtype', 'fp32')
    dtype_map = {
        'fp32': torch.float32,
        'float32': torch.float32,
        'fp16': torch.float16,
        'float16': torch.float16,
    }
    dtype = dtype_map.get(dtype_str, torch.float32)

    x = torch.randn(*shape, dtype=dtype)
    return [x]


def get_init_inputs():
    """模型初始化参数（GELU 是无状态算子）"""
    return []
