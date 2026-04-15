"""
gelu_custom 算子 PyTorch 参考实现

Model: PyTorch tanh-approximate GELU（正确性参考标准，匹配 Ascend C 实现）
ModelNew: 使用自定义 Ascend C 算子的 GELU 实现

支持 extreme/neg_large/near_zero 等特殊输入模式（boundary tier）。
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


def _generate_extreme(shape, dtype):
    """混合极值输入：含 inf/nan/-inf/large/small 值"""
    t = torch.randn(*shape, dtype=dtype)
    flat = t.flatten()
    n = flat.numel()
    if n >= 10:
        flat[0] = float('inf')
        flat[1] = float('-inf')
        flat[2] = float('nan') if dtype != torch.float16 else 0.0  # fp16 nan 处理有差异
        flat[3] = 1e30 if dtype == torch.float32 else 6.5e4
        flat[4] = -1e30 if dtype == torch.float32 else -6.5e4
        flat[5] = 1e-30 if dtype == torch.float32 else 1e-7
        flat[6] = 0.0
        flat[7] = -0.0
    return flat.reshape(shape)


def _generate_neg_large(shape, dtype):
    """大负值：GELU 输出应趋近 0"""
    return torch.full(shape, -10.0, dtype=dtype) + torch.randn(*shape, dtype=dtype) * 0.1


def _generate_near_zero(shape, dtype):
    """接近 0 的小值：GELU 输出应约等于 0.5x"""
    return torch.randn(*shape, dtype=dtype) * 0.01


def get_inputs(config=None):
    """生成测试输入张量。支持 input_mode: extreme/neg_large/near_zero"""
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

    input_mode = config.get('input_mode', 'normal')
    generators = {
        'normal': lambda s, d: torch.randn(*s, dtype=d),
        'extreme': _generate_extreme,
        'neg_large': _generate_neg_large,
        'near_zero': _generate_near_zero,
    }
    gen = generators.get(input_mode, generators['normal'])
    x = gen(shape, dtype)
    return [x]


def get_init_inputs():
    """模型初始化参数（GELU 是无状态算子）"""
    return []
