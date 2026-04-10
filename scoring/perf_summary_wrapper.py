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

支持多种性能指标类型:
- tflops: 算力密集型算子 (MatMul, Attention)
- bandwidth_gbps: 数据搬移型算子 (Elementwise, Transpose)
- latency_us: 延迟敏感型算子 (Reduce, Norm)

用法:
    python3 perf_summary_wrapper.py --msprof-output <dir> --config <config.json> \
        --metric-type <tflops|bandwidth_gbps|latency_us> --output <result.json>
"""

import argparse
import csv
import json
import math
import os
from pathlib import Path


def parse_msprof_csv(msprof_dir: str) -> list:
    """解析 msprof 输出目录中的 CSV 文件

    支持两种输出格式:
    1. 旧格式: device_*/summary/*.csv
    2. 新格式 (msprof op): OPPROF_*/OpBasicInfo.csv + PipeUtilization.csv
    """
    results = []

    # 方式 1: 新格式 — 解析 OpBasicInfo.csv (全局信息) + PipeUtilization.csv (per-block)
    for basic_csv in Path(msprof_dir).rglob("OpBasicInfo.csv"):
        try:
            with open(basic_csv, newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    result = parse_op_row(row)
                    if result:
                        # 补充 PipeUtilization 数据（取所有 block 的均值）
                        pipe_csv = basic_csv.parent / "PipeUtilization.csv"
                        if pipe_csv.exists():
                            _merge_pipe_utilization(result, pipe_csv)
                        results.append(result)
        except Exception as e:
            print(f"  解析 {basic_csv} 失败: {e}")

    if results:
        return results

    # 方式 2: 旧格式 — device_*/summary/*.csv
    for summary_dir in Path(msprof_dir).rglob("summary"):
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


def _merge_pipe_utilization(result: dict, pipe_csv: Path):
    """从 PipeUtilization.csv 聚合 per-block 管线利用率到 result"""
    try:
        ratios = {"vec": [], "mte2": [], "mte3": [], "scalar": [], "cube": []}
        with open(pipe_csv, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # 新格式列名: aiv_vec_ratio, aiv_mte2_ratio, etc.
                for key_prefix, field in [
                    ("aiv_vec_ratio", "vec"), ("aiv_mte2_ratio", "mte2"),
                    ("aiv_mte3_ratio", "mte3"), ("aiv_scalar_ratio", "scalar"),
                    ("aic_cube_ratio", "cube"),
                ]:
                    val = row.get(key_prefix, "NA")
                    if val and val != "NA":
                        try:
                            ratios[field].append(float(val))
                        except ValueError:
                            pass

        for field, vals in ratios.items():
            if vals:
                avg = sum(vals) / len(vals)
                result[f"{field}_ratio"] = avg
    except Exception as e:
        print(f"  解析 PipeUtilization 失败: {e}")


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

    # UB Usage
    for key in ["UB Usage(Bytes)", "UB Usage", "ub_usage_bytes"]:
        if key in row:
            try:
                result["ub_usage_bytes"] = int(row[key])
                break
            except (ValueError, TypeError):
                continue

    # Bank Conflict Count
    for key in ["Bank Conflict Count", "Bank Conflict", "bank_conflict_count"]:
        if key in row:
            try:
                result["bank_conflict_count"] = int(row[key])
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
    """根据配置计算 TFLOPS"""
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
        flops = 4.0 * b * h * s * s * d

    elif "matmul" in op:
        m = config.get("M", 1024)
        n = config.get("N", 1024)
        k = config.get("K", 1024)
        flops = 2.0 * m * n * k

    else:
        shape = config.get("shape", [1024])
        if isinstance(shape, list):
            count = 1
            for s in shape:
                count *= s
            flops = float(count)

    tflops = flops / duration_s / 1e12
    return round(tflops, 3)


def compute_bandwidth(config: dict, duration_us: float) -> float:
    """根据配置计算带宽 (GB/s)"""
    if duration_us <= 0:
        return 0.0

    duration_s = duration_us * 1e-6

    dtype_bytes = {"fp32": 4, "float32": 4, "fp16": 2, "float16": 2,
                   "bf16": 2, "bfloat16": 2, "int8": 1, "int32": 4}
    elem_size = dtype_bytes.get(config.get("dtype", "fp32"), 4)

    shape = config.get("shape", [1024])
    n_elems = 1
    for s in (shape if isinstance(shape, list) else [shape]):
        n_elems *= s

    # 默认假设: 读 2 个输入 + 写 1 个输出 (逐元素二元运算)
    total_bytes = n_elems * elem_size * 3
    return round(total_bytes / duration_s / 1e9, 3)


def compute_primary(config: dict, duration_us: float, metric_type: str,
                    operator: str) -> float:
    """根据指标类型计算主性能指标"""
    config_with_op = dict(config)
    config_with_op["operator"] = operator

    if metric_type == "tflops":
        return compute_tflops(config_with_op, duration_us)
    elif metric_type == "bandwidth_gbps":
        return compute_bandwidth(config_with_op, duration_us)
    elif metric_type == "latency_us":
        return round(duration_us, 3) if duration_us > 0 else 0.0
    else:
        return compute_tflops(config_with_op, duration_us)


def aggregate_performance(values: list, metric_type: str) -> float:
    """根据指标类型选择聚合方式"""
    if not values or any(v <= 0 for v in values):
        return 0.0
    if metric_type == "latency_us":
        # 延迟: 用调和平均 (lower is better)
        return round(len(values) / sum(1.0 / v for v in values), 2)
    else:
        # 吞吐: 用几何平均 (higher is better)
        log_sum = sum(math.log(v) for v in values)
        return round(math.exp(log_sum / len(values)), 2)


def extract_configs(test_config: dict) -> list:
    """从测试配置中提取所有级别的配置"""
    all_configs = []
    for level in ["smoke", "representative", "stress"]:
        level_configs = test_config.get(level, [])
        for c in level_configs:
            c["_level"] = level
        all_configs.extend(level_configs)
    if not all_configs:
        all_configs = test_config.get("configs", [{}])
    return all_configs


def main():
    parser = argparse.ArgumentParser(description="msprof 结果解析")
    parser.add_argument("--msprof-output", required=True, help="msprof 输出目录")
    parser.add_argument("--config", required=True, help="测试配置 JSON")
    parser.add_argument("--metric-type", default="tflops",
                        help="tflops | bandwidth_gbps | latency_us")
    parser.add_argument("--output", required=True, help="结果输出 JSON")
    args = parser.parse_args()

    with open(args.config) as f:
        test_config = json.load(f)

    metric_type = args.metric_type or test_config.get("metric_type", "tflops")
    operator = test_config.get("operator", "")

    # 解析 msprof CSV
    msprof_results = parse_msprof_csv(args.msprof_output)

    configs = extract_configs(test_config)
    output_configs = []

    for i, config in enumerate(configs):
        config_name = config.get("name", f"config_{i}")
        level = config.get("_level", "unknown")

        # 匹配 msprof 结果（按顺序或按名称）
        if i < len(msprof_results):
            mr = msprof_results[i]
        else:
            mr = {"task_duration_us": 0.0}

        duration = mr.get("task_duration_us", 0.0)
        primary = compute_primary(config, duration, metric_type, operator)

        output_configs.append({
            "name": config_name,
            "level": level,
            "performance_primary": primary,
            "task_duration_us": duration,
            "profiling": {
                "vec_ratio": mr.get("vec_ratio", 0.0),
                "mte2_ratio": mr.get("mte2_ratio", 0.0),
                "cube_ratio": mr.get("cube_ratio", 0.0),
                "scalar_ratio": mr.get("scalar_ratio", 0.0),
                "mte3_ratio": mr.get("mte3_ratio", 0.0),
                "block_dim": mr.get("block_dim", 0),
                "ub_usage_bytes": mr.get("ub_usage_bytes", 0),
                "bank_conflict_count": mr.get("bank_conflict_count", 0),
            },
        })

        print(f"  [{level}/{config_name}] {primary} {metric_type}, duration={duration:.1f}us")

    # 聚合
    primary_values = [c["performance_primary"] for c in output_configs
                      if c["performance_primary"] > 0]
    total = aggregate_performance(primary_values, metric_type)

    result = {
        "metric_type": metric_type,
        "performance_total": total,
        "configs": output_configs,
    }

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n性能聚合: {total} ({metric_type})")


if __name__ == "__main__":
    main()
