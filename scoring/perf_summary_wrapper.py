#!/usr/bin/env python3
"""perf_summary_wrapper.py — 封装 msprof 输出解析

解析 msprof 生成的 CSV 文件，提取 8 大性能指标：
1. Task Duration (us)
2. VEC Ratio (向量计算占比)
3. MTE2 Ratio (数据搬移占比)
4. Cube Ratio (矩阵计算占比)
5. Scalar Ratio (标量计算占比)
6. MTE3 Ratio (输出搬移占比)
7. Block Dim (使用核数)
8. UB Usage (UB 使用量)

用法:
    python3 perf_summary_wrapper.py --msprof-output <dir> --config <config.json> --output <result.json>
"""

import argparse
import csv
import json
import os
from pathlib import Path


def parse_msprof_csv(msprof_dir: str) -> list:
    """解析 msprof 输出目录中的 CSV 文件"""
    results = []

    # msprof 通常输出到 device_*/summary/ 目录
    summary_dirs = list(Path(msprof_dir).rglob("summary"))

    for summary_dir in summary_dirs:
        # 解析 op_summary CSV
        for csv_file in summary_dir.glob("*.csv"):
            try:
                with open(csv_file, newline="", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        result = parse_op_row(row)
                        if result:
                            results.append(result)
            except Exception as e:
                print(f"  解析 {csv_file} 失败: {e}")

    return results


def parse_op_row(row: dict) -> dict:
    """从 CSV 行解析算子性能数据"""
    result = {}

    # 尝试不同的列名格式
    duration_keys = ["Task Duration(us)", "Duration(us)", "task_duration", "Task Duration"]
    for key in duration_keys:
        if key in row:
            try:
                result["task_duration_us"] = float(row[key])
                break
            except (ValueError, TypeError):
                continue

    if "task_duration_us" not in result:
        return None

    # Pipeline 利用率
    pipe_map = {
        "vec_ratio": ["VEC Ratio(%)", "Vec Ratio(%)", "vec_ratio"],
        "mte2_ratio": ["MTE2 Ratio(%)", "Mte2 Ratio(%)", "mte2_ratio"],
        "cube_ratio": ["Cube Ratio(%)", "cube_ratio"],
        "scalar_ratio": ["Scalar Ratio(%)", "scalar_ratio"],
        "mte3_ratio": ["MTE3 Ratio(%)", "mte3_ratio"],
    }

    for field, keys in pipe_map.items():
        for key in keys:
            if key in row:
                try:
                    val = float(row[key])
                    result[field] = val / 100.0 if val > 1.0 else val
                    break
                except (ValueError, TypeError):
                    continue

    # Block Dim
    for key in ["Block Dim", "block_dim", "BlockDim"]:
        if key in row:
            try:
                result["block_dim"] = int(row[key])
                break
            except (ValueError, TypeError):
                continue

    # 算子名
    for key in ["Op Name", "Name", "op_name"]:
        if key in row:
            result["op_name"] = row[key]
            break

    return result


def compute_tflops(config: dict, duration_us: float) -> float:
    """根据配置计算 TFLOPS

    不同算子有不同的 FLOPs 计算公式:
    - Attention: 4 * B * H * S^2 * D (forward)
    - MatMul: 2 * M * N * K
    - Elementwise: N (element count)
    """
    if duration_us <= 0:
        return 0.0

    duration_s = duration_us * 1e-6
    flops = 0.0

    op = config.get("operator", "")

    if "attention" in op:
        b = config.get("batch", 1)
        h = config.get("heads", 1)
        s = config.get("seq_len", 1024)
        d = config.get("dim", 128)
        # Forward: 2*B*H*S*S*D (QK^T) + 2*B*H*S*S*D (PV) = 4*B*H*S^2*D
        flops = 4.0 * b * h * s * s * d

    elif "matmul" in op:
        m = config.get("M", 1024)
        n = config.get("N", 1024)
        k = config.get("K", 1024)
        flops = 2.0 * m * n * k

    else:
        # Elementwise: count elements
        shape = config.get("shape", [1024])
        if isinstance(shape, list):
            count = 1
            for s in shape:
                count *= s
            flops = float(count)

    tflops = flops / duration_s / 1e12
    return round(tflops, 3)


def main():
    parser = argparse.ArgumentParser(description="msprof 结果解析")
    parser.add_argument("--msprof-output", required=True, help="msprof 输出目录")
    parser.add_argument("--config", required=True, help="测试配置 JSON")
    parser.add_argument("--output", required=True, help="结果输出 JSON")
    args = parser.parse_args()

    with open(args.config) as f:
        test_config = json.load(f)

    # 解析 msprof CSV
    msprof_results = parse_msprof_csv(args.msprof_output)

    configs = test_config.get("configs", [{}])
    output_configs = []

    for i, config in enumerate(configs):
        config_name = config.get("name", f"config_{i}")

        # 匹配 msprof 结果（按顺序或按名称）
        if i < len(msprof_results):
            mr = msprof_results[i]
        else:
            mr = {"task_duration_us": 0.0}

        duration = mr.get("task_duration_us", 0.0)
        tflops = compute_tflops(config, duration)

        output_configs.append({
            "name": config_name,
            "tflops": tflops,
            "task_duration_us": duration,
            "profiling": {
                "vec_ratio": mr.get("vec_ratio", 0.0),
                "mte2_ratio": mr.get("mte2_ratio", 0.0),
                "cube_ratio": mr.get("cube_ratio", 0.0),
                "scalar_ratio": mr.get("scalar_ratio", 0.0),
                "mte3_ratio": mr.get("mte3_ratio", 0.0),
                "block_dim": mr.get("block_dim", 0),
            },
        })

        print(f"  [{config_name}] {tflops} TFLOPS, duration={duration:.1f}us")

    # 几何平均
    tflops_values = [c["tflops"] for c in output_configs if c["tflops"] > 0]
    if tflops_values:
        import math
        log_sum = sum(math.log(v) for v in tflops_values)
        geo_mean = math.exp(log_sum / len(tflops_values))
    else:
        geo_mean = 0.0

    result = {
        "performance_total_tflops": round(geo_mean, 2),
        "configs": output_configs,
    }

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n性能几何平均: {geo_mean:.2f} TFLOPS")


if __name__ == "__main__":
    main()
