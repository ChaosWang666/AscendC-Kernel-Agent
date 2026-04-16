#!/usr/bin/env python3
"""test_performance.py — NPU Event-based 性能测试

通过 PyTorch NPU Event 精确测量自定义算子的执行时间，
参考 MultiKernelBench 的 performance.py 流程。

用法:
    python3 test_performance.py \
        --reference <reference.py> \
        --config <config.json> \
        --output <result.json> \
        --metric-type latency_us
"""

import argparse
import json
import os
import sys
import importlib.util
import statistics
import traceback


NUM_WARMUP = 10
NUM_TRIALS = 100


def load_reference_module(reference_path):
    """动态加载 reference.py 模块"""
    spec = importlib.util.spec_from_file_location("reference", reference_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LEVEL_ORDER = ["seed", "smoke", "representative", "stress"]


def extract_configs(test_config, levels=None):
    """从测试配置中提取配置列表（按 LEVEL_ORDER 稳定排序）

    注意：seed 级别通常不做性能测量（尺寸太小，噪声大），
    因此性能测试的默认 levels 不包含 seed。
    """
    all_configs = []
    if levels is None:
        levels = ["smoke", "representative", "stress"]
    ordered_levels = [lv for lv in LEVEL_ORDER if lv in levels]
    for level in ordered_levels:
        level_configs = test_config.get(level, [])
        for c in level_configs:
            c["_level"] = level
        all_configs.extend(level_configs)
    if not all_configs:
        all_configs = test_config.get("configs", [{}])
    return all_configs


def measure_performance(ref_module, config, device, synchronize, event_class):
    """
    使用 NPU Event 测量单个配置的算子执行时间

    返回:
        dict with 'mean', 'std', 'min', 'max', 'num_trials', 'times_ms'
    """
    import torch

    get_inputs = ref_module.get_inputs
    get_init_inputs = ref_module.get_init_inputs
    ModelNew = ref_module.ModelNew

    try:
        init_inputs = get_init_inputs()
        init_inputs = [
            x.to(device=device) if isinstance(x, torch.Tensor) else x
            for x in init_inputs
        ]

        try:
            inputs = get_inputs(config)
        except TypeError:
            inputs = get_inputs()
        inputs = [
            x.to(device) if isinstance(x, torch.Tensor) else x
            for x in inputs
        ]

        elapsed_times = []

        with torch.no_grad():
            custom_model = ModelNew(*init_inputs).to(device)

            # Warmup
            for _ in range(NUM_WARMUP):
                custom_model(*inputs)
                synchronize(device=device)

            # Measurement
            for _ in range(NUM_TRIALS):
                start_event = event_class(enable_timing=True)
                end_event = event_class(enable_timing=True)

                start_event.record()
                custom_model(*inputs)
                end_event.record()

                synchronize(device=device)
                elapsed_ms = start_event.elapsed_time(end_event)
                elapsed_times.append(elapsed_ms)

        return {
            "mean": statistics.mean(elapsed_times),
            "median": statistics.median(elapsed_times),
            "std": statistics.stdev(elapsed_times) if len(elapsed_times) > 1 else 0.0,
            "min": min(elapsed_times),
            "max": max(elapsed_times),
            "num_trials": len(elapsed_times),
            "times_ms": elapsed_times,
            "error": None,
        }

    except Exception as e:
        return {
            "mean": 0.0,
            "std": 0.0,
            "min": 0.0,
            "max": 0.0,
            "num_trials": 0,
            "times_ms": [],
            "error": f"Runtime error: {str(e)}\n{traceback.format_exc()}",
        }


def compute_performance_total(results, metric_type):
    """
    聚合多个配置的性能为单一指标

    latency_us: 使用调和平均（越低越好）
    tflops/bandwidth_gbps: 使用几何平均（越高越好）
    """
    primaries = [r["performance_primary"] for r in results if r["performance_primary"] > 0]
    if not primaries:
        return 0.0

    if metric_type == "latency_us":
        # 调和平均
        return len(primaries) / sum(1.0 / p for p in primaries)
    else:
        # 几何平均
        from functools import reduce
        import operator
        return reduce(operator.mul, primaries) ** (1.0 / len(primaries))


def main():
    global NUM_WARMUP, NUM_TRIALS
    parser = argparse.ArgumentParser(description="NPU Event-based 性能测试")
    parser.add_argument("--reference", required=True, help="reference.py 路径")
    parser.add_argument("--config", required=True, help="测试配置 JSON")
    parser.add_argument("--output", required=True, help="结果输出 JSON")
    parser.add_argument("--metric-type", default="latency_us",
                        help="性能指标类型: latency_us | tflops | bandwidth_gbps")
    parser.add_argument("--deploy-dir", default=None,
                        help="算子部署目录（ASCEND_CUSTOM_OPP_PATH）")
    parser.add_argument("--warmup", type=int, default=NUM_WARMUP, help="预热轮数")
    parser.add_argument("--trials", type=int, default=NUM_TRIALS, help="测量轮数")
    parser.add_argument("--levels", default="representative",
                        help="测试级别（逗号分隔）")
    args = parser.parse_args()

    NUM_WARMUP = args.warmup
    NUM_TRIALS = args.trials

    # 设置环境变量
    if args.deploy_dir:
        custom_opp = os.path.join(args.deploy_dir, "vendors", "customize")
        if os.path.exists(custom_opp):
            os.environ["ASCEND_CUSTOM_OPP_PATH"] = custom_opp
            lib_path = os.path.join(custom_opp, "op_api", "lib")
            os.environ["LD_LIBRARY_PATH"] = (
                f"{lib_path}:{os.environ.get('LD_LIBRARY_PATH', '')}"
            )

    # 延迟导入 torch
    import torch
    try:
        import torch_npu
        device = torch.device("npu:0")
        synchronize = torch_npu.npu.synchronize
        event_class = torch.npu.Event
        print("使用 NPU 设备")
    except ImportError:
        print("错误: 性能测试需要 torch_npu")
        sys.exit(1)

    # 加载参考实现
    ref_module = load_reference_module(args.reference)

    # 加载测试配置
    with open(args.config) as f:
        test_config = json.load(f)

    metric_type = args.metric_type
    levels = [l.strip() for l in args.levels.split(",") if l.strip()]
    configs = extract_configs(test_config, levels=levels or None)

    all_results = []

    for i, config in enumerate(configs):
        config_name = config.get("name", f"config_{i}")
        level = config.get("_level", "unknown")

        print(f"  [{level}/{config_name}] 性能测试中 (warmup={NUM_WARMUP}, trials={NUM_TRIALS})...")

        perf = measure_performance(ref_module, config, device, synchronize, event_class)

        # 根据 metric_type 计算 performance_primary
        # CP-2 R9 修复:用 median 而非 mean 聚合,避免 NPU thermal/contention 导致的
        # 单次 outlier 主导聚合值(smoke test 中单次 trials 的 max 可达 2x min)。
        # 同时暴露 cv = std/mean 供上游判断测量质量(cv > 0.15 视为可疑)。
        if metric_type == "latency_us":
            performance_primary = perf["median"] * 1000  # ms → us
        else:
            performance_primary = perf["median"]  # 原始值

        cv = (perf["std"] / perf["mean"]) if perf["mean"] > 0 else 0.0
        if cv > 0.15:
            print(f"  [{level}/{config_name}] ⚠ high variance: cv={cv:.3f} (std={perf['std']:.4f} mean={perf['mean']:.4f})")

        result = {
            "name": config_name,
            "level": level,
            "mean_ms": round(perf["mean"], 6),
            "median_ms": round(perf["median"], 6),
            "std_ms": round(perf["std"], 6),
            "cv": round(cv, 4),
            "min_ms": round(perf["min"], 6),
            "max_ms": round(perf["max"], 6),
            "num_trials": perf["num_trials"],
            "task_duration_us": round(perf["median"] * 1000, 3),
            "performance_primary": round(performance_primary, 3),
        }

        if perf.get("error"):
            result["error"] = perf["error"]

        all_results.append(result)
        print(f"  [{level}/{config_name}] mean={perf['mean']:.4f}ms, std={perf['std']:.4f}ms")

    # 聚合
    perf_total = compute_performance_total(all_results, metric_type)

    output = {
        "metric_type": metric_type,
        "performance_total": round(perf_total, 3),
        "test_method": "npu_event_timing",
        "warmup": NUM_WARMUP,
        "trials": NUM_TRIALS,
        "configs": all_results,
    }

    with open(args.output, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n性能总分: {perf_total:.3f} ({metric_type})")


if __name__ == "__main__":
    main()
