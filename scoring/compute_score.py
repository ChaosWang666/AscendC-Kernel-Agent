#!/usr/bin/env python3
"""compute_score.py — 聚合正确性和性能结果为最终评分

输出格式:
{
    "version": "v23",
    "timestamp": "...",
    "git_commit": "...",
    "correctness_total": 1.0,
    "performance_total_tflops": 856.3,
    "configs": [...]
}

用法:
    python3 compute_score.py --version <N> \
        [--correctness-result <correctness.json>] \
        [--performance-result <performance.json>] \
        [--compile-error <compile.log>] \
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
    """计算几何平均值"""
    if not values or any(v <= 0 for v in values):
        return 0.0
    log_sum = sum(math.log(v) for v in values)
    return math.exp(log_sum / len(values))


def main():
    parser = argparse.ArgumentParser(description="聚合评分")
    parser.add_argument("--version", required=True, help="版本号")
    parser.add_argument("--correctness-result", help="正确性结果 JSON")
    parser.add_argument("--performance-result", help="性能结果 JSON")
    parser.add_argument("--compile-error", help="编译错误日志")
    parser.add_argument("--output", required=True, help="输出评分 JSON")
    args = parser.parse_args()

    score = {
        "version": f"v{args.version}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_commit": get_git_commit(),
        "correctness_total": 0.0,
        "performance_total_tflops": 0.0,
        "improvement_over_prev": "N/A",
        "configs": [],
    }

    # 编译失败
    if args.compile_error:
        try:
            with open(args.compile_error) as f:
                error_log = f.read()[-2000:]  # 最后 2000 字符
        except Exception:
            error_log = "无法读取编译日志"

        score["compile_error"] = error_log
        with open(args.output, "w") as f:
            json.dump(score, f, indent=2, ensure_ascii=False)
        return

    # 加载正确性结果
    if args.correctness_result:
        with open(args.correctness_result) as f:
            correctness = json.load(f)
        score["correctness_total"] = correctness.get("correctness_total", 0.0)

        # 合并 config 级别结果
        for c in correctness.get("configs", []):
            score["configs"].append({
                "name": c.get("name", "unknown"),
                "correctness": c.get("correctness", 0),
                "max_abs_error": c.get("max_abs_error", 0.0),
                "max_rel_error": c.get("max_rel_error", 0.0),
            })

    # 如果正确性未通过，性能评分为 0
    if score["correctness_total"] < 1.0:
        with open(args.output, "w") as f:
            json.dump(score, f, indent=2, ensure_ascii=False)
        return

    # 加载性能结果
    if args.performance_result:
        with open(args.performance_result) as f:
            performance = json.load(f)

        tflops_values = []
        perf_configs = {c.get("name", f"config_{i}"): c
                        for i, c in enumerate(performance.get("configs", []))}

        for config in score["configs"]:
            name = config["name"]
            if name in perf_configs:
                pc = perf_configs[name]
                config["tflops"] = pc.get("tflops", 0.0)
                config["task_duration_us"] = pc.get("task_duration_us", 0.0)
                config["profiling"] = pc.get("profiling", {})
                if config["tflops"] > 0:
                    tflops_values.append(config["tflops"])

        # 几何平均 TFLOPS
        score["performance_total_tflops"] = round(geometric_mean(tflops_values), 2)

    with open(args.output, "w") as f:
        json.dump(score, f, indent=2, ensure_ascii=False)

    print(f"评分: correctness={score['correctness_total']}, "
          f"performance={score['performance_total_tflops']} TFLOPS")


if __name__ == "__main__":
    main()
