#!/usr/bin/env python3
"""gen_golden.py — 生成 golden 参考数据

根据算子规格和测试配置，使用 NumPy 生成参考输出。
每个算子需要在此注册其参考实现。

用法:
    python3 gen_golden.py --op-path <op_path> --config <config.json> --output-dir <dir>
"""

import argparse
import json
import os
import numpy as np
from pathlib import Path


# ========== 参考实现注册表 ==========

def golden_add(inputs: dict, config: dict) -> dict:
    """逐元素加法"""
    x = inputs["x"]
    y = inputs["y"]
    return {"z": x + y}


def golden_softmax(inputs: dict, config: dict) -> dict:
    """Softmax"""
    x = inputs["x"]
    axis = config.get("axis", -1)
    e_x = np.exp(x - np.max(x, axis=axis, keepdims=True))
    return {"y": e_x / np.sum(e_x, axis=axis, keepdims=True)}


def golden_layernorm(inputs: dict, config: dict) -> dict:
    """Layer Normalization"""
    x = inputs["x"]
    gamma = inputs["gamma"]
    beta = inputs["beta"]
    eps = config.get("eps", 1e-5)
    axis = config.get("axis", -1)
    mean = np.mean(x, axis=axis, keepdims=True)
    var = np.var(x, axis=axis, keepdims=True)
    x_norm = (x - mean) / np.sqrt(var + eps)
    return {"y": gamma * x_norm + beta}


def golden_flash_attention(inputs: dict, config: dict) -> dict:
    """Flash Attention (参考实现，非优化)"""
    q = inputs["q"]  # [B, H, S, D]
    k = inputs["k"]  # [B, H, S, D]
    v = inputs["v"]  # [B, H, S, D]
    causal = config.get("causal", False)
    scale = 1.0 / np.sqrt(q.shape[-1])

    # QK^T
    scores = np.matmul(q, k.transpose(0, 1, 3, 2)) * scale

    # Causal mask
    if causal:
        seq_len = scores.shape[-1]
        mask = np.triu(np.ones((seq_len, seq_len)), k=1) * (-1e9)
        scores = scores + mask

    # Softmax
    scores_max = np.max(scores, axis=-1, keepdims=True)
    exp_scores = np.exp(scores - scores_max)
    attn = exp_scores / np.sum(exp_scores, axis=-1, keepdims=True)

    # Attention output
    output = np.matmul(attn, v)
    return {"output": output}


# 算子注册表
GOLDEN_REGISTRY = {
    "add_custom": golden_add,
    "softmax": golden_softmax,
    "layernorm": golden_layernorm,
    "layer_norm": golden_layernorm,
    "flash_attention": golden_flash_attention,
    "flash_attention_score": golden_flash_attention,
    "flash_attention_ascend": golden_flash_attention,
}


# ========== 数据生成 ==========

DTYPE_MAP = {
    "fp32": np.float32,
    "float32": np.float32,
    "fp16": np.float16,
    "float16": np.float16,
    "bf16": np.float32,  # NumPy 不原生支持 bf16，用 fp32 生成后转换
    "bfloat16": np.float32,
    "int32": np.int32,
    "int8": np.int8,
}


def generate_input_data(config: dict) -> dict:
    """根据配置生成输入数据"""
    inputs = {}
    dtype_str = config.get("dtype", "fp32")
    np_dtype = DTYPE_MAP.get(dtype_str, np.float32)

    op_name = config.get("operator", "")

    if "attention" in op_name:
        batch = config.get("batch", 1)
        seq_len = config.get("seq_len", 1024)
        heads = config.get("heads", 16)
        dim = config.get("dim", 128)
        shape = (batch, heads, seq_len, dim)
        inputs["q"] = np.random.randn(*shape).astype(np_dtype) * 0.1
        inputs["k"] = np.random.randn(*shape).astype(np_dtype) * 0.1
        inputs["v"] = np.random.randn(*shape).astype(np_dtype) * 0.1

    elif "layernorm" in op_name or "layer_norm" in op_name:
        shape = tuple(config.get("shape", [1024]))
        inputs["x"] = np.random.randn(*shape).astype(np_dtype)
        norm_shape = shape[-1:]
        inputs["gamma"] = np.ones(norm_shape, dtype=np_dtype)
        inputs["beta"] = np.zeros(norm_shape, dtype=np_dtype)

    elif "softmax" in op_name:
        shape = tuple(config.get("shape", [1024]))
        inputs["x"] = np.random.randn(*shape).astype(np_dtype)

    else:
        # 默认：双输入逐元素运算
        shape = tuple(config.get("shape", [1024]))
        inputs["x"] = np.random.randn(*shape).astype(np_dtype)
        inputs["y"] = np.random.randn(*shape).astype(np_dtype)

    return inputs


def main():
    parser = argparse.ArgumentParser(description="生成 golden 参考数据")
    parser.add_argument("--op-path", required=True, help="算子路径")
    parser.add_argument("--config", required=True, help="测试配置 JSON")
    parser.add_argument("--output-dir", required=True, help="输出目录")
    args = parser.parse_args()

    with open(args.config) as f:
        test_config = json.load(f)

    op_name = test_config.get("operator", Path(args.op_path).name)
    golden_fn = GOLDEN_REGISTRY.get(op_name)

    if golden_fn is None:
        print(f"警告: 算子 '{op_name}' 未在 golden 注册表中，尝试使用算子自带的 gen_golden.py")
        op_gen = os.path.join(args.op_path, "scripts", "gen_data.py")
        if os.path.exists(op_gen):
            os.system(f"python3 {op_gen} --output-dir {args.output_dir}")
            return
        else:
            print(f"错误: 未找到 golden 生成方法")
            return

    os.makedirs(args.output_dir, exist_ok=True)

    # 支持分级配置格式（smoke/representative/stress）和旧格式（configs）
    all_configs = []
    for level in ["smoke", "representative", "stress"]:
        level_configs = test_config.get(level, [])
        for c in level_configs:
            c["_level"] = level
        all_configs.extend(level_configs)
    if not all_configs:
        all_configs = test_config.get("configs", [{}])

    for i, config in enumerate(all_configs):
        config["operator"] = op_name
        config_name = config.get("name", f"config_{i}")
        config_dir = os.path.join(args.output_dir, config_name)
        os.makedirs(config_dir, exist_ok=True)

        # 设置随机种子保证可复现
        np.random.seed(42 + i)

        # 生成输入
        inputs = generate_input_data(config)
        for name, data in inputs.items():
            np.save(os.path.join(config_dir, f"input_{name}.npy"), data)

        # 生成 golden 输出
        outputs = golden_fn(inputs, config)
        for name, data in outputs.items():
            np.save(os.path.join(config_dir, f"golden_{name}.npy"), data)

        print(f"  [{config_name}] 输入: {list(inputs.keys())}, 输出: {list(outputs.keys())}")

    print(f"Golden 数据已保存到: {args.output_dir}")


if __name__ == "__main__":
    main()
