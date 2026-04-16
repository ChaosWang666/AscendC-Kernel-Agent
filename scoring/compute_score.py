#!/usr/bin/env python3
"""compute_score.py — 聚合正确性和性能结果为最终评分

输出格式:
{
    "version": "v23",
    "timestamp": "...",
    "git_commit": "...",
    "metric_type": "tflops",
    "correctness_total": 1.0,
    "performance_total": 856.3,
    "improvement_over_best": "+3.2%",
    "test_levels_run": ["smoke", "representative", "stress"],
    "configs": [...]
}

用法:
    python3 compute_score.py --version <N> \
        [--correctness-result <correctness.json>] \
        [--performance-result <performance.json>] \
        [--compile-error <compile.log>] \
        [--metric-type tflops] \
        [--best-score <float>] \
        [--test-levels smoke,representative] \
        --output <score.json>
"""

import argparse
import json
import subprocess
import math
from datetime import datetime, timezone


def get_git_commit() -> str:
    """获取当前 git commit hash"""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True,
        )
        return result.stdout.strip() if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def geometric_mean(values: list) -> float:
    """计算几何平均值（适用于 higher-is-better 指标如 tflops, bandwidth_gbps）"""
    if not values or any(v <= 0 for v in values):
        return 0.0
    log_sum = sum(math.log(v) for v in values)
    return math.exp(log_sum / len(values))


def harmonic_mean(values: list) -> float:
    """计算调和平均值（适用于 lower-is-better 指标如 latency_us）"""
    if not values or any(v <= 0 for v in values):
        return 0.0
    return len(values) / sum(1.0 / v for v in values)


def aggregate_performance(values: list, metric_type: str) -> float:
    """根据指标类型选择合适的聚合方式"""
    if metric_type == "latency_us":
        return round(harmonic_mean(values), 2)
    else:
        return round(geometric_mean(values), 2)


def compute_improvement(new_val: float, best_val: float, metric_type: str) -> str:
    """计算相对于 best 的改进比例"""
    if best_val <= 0 or new_val <= 0:
        return "N/A"
    if metric_type == "latency_us":
        # 延迟指标: 越低越好, best/new - 1
        improvement = best_val / new_val - 1
    else:
        # 吞吐指标: 越高越好, new/best - 1
        improvement = new_val / best_val - 1
    return f"{improvement:+.1%}"


def main():
    parser = argparse.ArgumentParser(description="聚合评分")
    parser.add_argument("--version", required=True, help="版本号")
    parser.add_argument("--correctness-result", help="正确性结果 JSON")
    parser.add_argument("--performance-result", help="性能结果 JSON")
    parser.add_argument("--compile-error", help="失败阶段的日志文件（与 --failure-stage 搭配使用）")
    parser.add_argument("--failure-stage",
                        choices=["environment", "compile", "deploy", "pybind", "correctness", "performance"],
                        help="失败发生的具体阶段")
    parser.add_argument("--phase-timings",
                        help="每阶段 wall-clock JSON 文件路径（score.sh 生成）")
    parser.add_argument("--metric-type", default="tflops",
                        help="tflops | bandwidth_gbps | latency_us")
    parser.add_argument("--best-score", type=float, default=0.0,
                        help="当前最佳评分（用于计算 improvement）")
    parser.add_argument("--test-levels", default="",
                        help="已运行的测试级别（逗号分隔）")
    parser.add_argument("--boundary-result", default=None,
                        help="boundary 测试结果 JSON（可选，诊断性）")
    parser.add_argument("--output", required=True, help="输出评分 JSON")
    args = parser.parse_args()

    test_levels = [l.strip() for l in args.test_levels.split(",") if l.strip()]

    # 读取阶段时间（如果提供）
    phase_timings = {}
    if args.phase_timings:
        try:
            with open(args.phase_timings) as f:
                phase_timings = json.load(f)
        except Exception:
            phase_timings = {}

    # Boundary 结果（诊断性，不阻塞主流程）
    boundary_summary = None
    if args.boundary_result:
        try:
            with open(args.boundary_result) as f:
                boundary_data = json.load(f)
            boundary_summary = {
                "boundary_total": boundary_data.get("correctness_total", 0.0),
                "boundary_configs_run": len(boundary_data.get("configs", [])),
                "boundary_failed_cases": [
                    c.get("name") for c in boundary_data.get("configs", [])
                    if c.get("correctness") != 1
                ],
            }
        except Exception:
            boundary_summary = {"boundary_total": "N/A", "error": "failed to load boundary result"}

    score = {
        "version": f"v{args.version}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": get_git_commit(),
        "metric_type": args.metric_type,
        "correctness_total": 0.0,
        "performance_total": 0.0,
        "improvement_over_best": "N/A",
        "test_levels_run": test_levels,
        "configs": [],
        "phase_timings": phase_timings,
    }
    if boundary_summary is not None:
        score["boundary_summary"] = boundary_summary

    # Pre-correctness 阶段性失败（environment / compile / deploy / pybind）
    # 这些阶段没有 correctness / performance 结果可解析，直接写 error_log 返回
    PRE_CORRECTNESS_STAGES = {"environment", "compile", "deploy", "pybind"}
    is_pre_correctness_failure = (
        args.compile_error is not None
        or (args.failure_stage in PRE_CORRECTNESS_STAGES)
    )
    if is_pre_correctness_failure:
        if args.compile_error:
            try:
                with open(args.compile_error) as f:
                    error_log = f.read()[-2000:]  # 最后 2000 字符
            except Exception:
                error_log = "无法读取失败阶段日志"
        else:
            error_log = ""

        stage = args.failure_stage or "compile"  # 默认 compile 保持向后兼容
        score["error_log"] = error_log
        score["failure_type"] = stage
        # 旧键 compile_error 保留为 alias 以便兼容既有消费者
        if stage == "compile":
            score["compile_error"] = error_log
        with open(args.output, "w") as f:
            json.dump(score, f, indent=2, ensure_ascii=False)
        return
    # correctness / performance 阶段的失败会继续向下流向正常的结果解析逻辑，
    # 由后续的 correctness_total / performance_total 分支决定最终 failure_type

    # 加载正确性结果
    if args.correctness_result:
        with open(args.correctness_result) as f:
            correctness = json.load(f)
        score["correctness_total"] = correctness.get("correctness_total", 0.0)

        # 合并 config 级别结果；保留诊断字段（atol/rtol/mismatch_details/ref_stats/new_stats）
        # 只有在失败时才存在，Architect 需要它们做定位
        diagnostic_keys = (
            "atol", "rtol", "error",
            "mismatch_details", "ref_stats", "new_stats",
            "mean_abs_error", "mismatch_ratio",
        )
        for c in correctness.get("configs", []):
            entry = {
                "name": c.get("name", "unknown"),
                "level": c.get("level", "unknown"),
                "shape": c.get("shape"),
                "dtype": c.get("dtype"),
                "correctness": c.get("correctness", 0),
                "max_abs_error": c.get("max_abs_error", 0.0),
                "max_rel_error": c.get("max_rel_error", 0.0),
            }
            if c.get("input_mode") and c.get("input_mode") != "normal":
                entry["input_mode"] = c["input_mode"]
            for k in diagnostic_keys:
                if k in c and c[k] is not None:
                    entry[k] = c[k]
            score["configs"].append(entry)

    # 如果正确性未通过，性能评分为 0
    if score["correctness_total"] < 1.0:
        score["failure_type"] = "correctness"
        with open(args.output, "w") as f:
            json.dump(score, f, indent=2, ensure_ascii=False)
        return

    # 加载性能结果
    if args.performance_result:
        with open(args.performance_result) as f:
            performance = json.load(f)

        primary_values = []
        perf_configs = {c.get("name", f"config_{i}"): c
                        for i, c in enumerate(performance.get("configs", []))}

        for config in score["configs"]:
            name = config["name"]
            if name in perf_configs:
                pc = perf_configs[name]
                config["performance_primary"] = pc.get("performance_primary", 0.0)
                config["task_duration_us"] = pc.get("task_duration_us", 0.0)
                config["profiling"] = pc.get("profiling", {})
                # R9 fix: propagate measurement-quality fields for downstream diagnosis.
                # test_performance.py computes these but they were dropped here.
                for key in ("median_ms", "mean_ms", "std_ms", "cv",
                            "min_ms", "max_ms", "num_trials"):
                    if key in pc:
                        config[key] = pc[key]
                if config["performance_primary"] > 0:
                    primary_values.append(config["performance_primary"])

        # 聚合性能指标
        score["performance_total"] = aggregate_performance(primary_values, args.metric_type)

    # 计算相对改进
    if args.best_score > 0:
        score["improvement_over_best"] = compute_improvement(
            score["performance_total"], args.best_score, args.metric_type
        )

    # 聚合 test_coverage（shape / dtype / level / rank 覆盖情况）
    # 合并主 configs 和 boundary configs 以获得完整覆盖视图
    shapes = set()
    dtypes = set()
    levels_covered = set()
    ranks = set()
    input_modes = set()
    coverage_sources = list(score["configs"])
    if args.boundary_result:
        try:
            with open(args.boundary_result) as f:
                boundary_data = json.load(f)
            coverage_sources.extend(boundary_data.get("configs", []))
        except Exception:
            pass

    for c in coverage_sources:
        if c.get("shape") is not None:
            shapes.add(str(c["shape"]))
            try:
                ranks.add(len(c["shape"]) if isinstance(c["shape"], list) else 1)
            except Exception:
                pass
        if c.get("dtype"):
            dtypes.add(c["dtype"])
        if c.get("level"):
            levels_covered.add(c["level"])
        if c.get("input_mode") and c.get("input_mode") != "normal":
            input_modes.add(c["input_mode"])

    score["test_coverage"] = {
        "shapes_tested": sorted(shapes),
        "dtypes_tested": sorted(dtypes),
        "levels_covered": sorted(levels_covered),
        "ranks_tested": sorted(ranks),
        "input_modes_tested": sorted(input_modes),
        "total_configs": len(coverage_sources),
        "boundary_attempted": boundary_summary is not None,
    }

    with open(args.output, "w") as f:
        json.dump(score, f, indent=2, ensure_ascii=False)

    print(f"评分: correctness={score['correctness_total']}, "
          f"performance={score['performance_total']} ({args.metric_type})")


if __name__ == "__main__":
    main()
