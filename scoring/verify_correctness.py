#!/usr/bin/env python3
"""verify_correctness.py — 验证内核输出与 golden 参考数据的一致性

使用 np.allclose 语义进行正确性判定：
  |a - b| <= atol + rtol * |b|

精度阈值标准（来源：ops-precision-standard）:
  FP32: rtol=1e-5, atol=1e-5
  FP16: rtol=1e-3, atol=1e-3
  BF16: rtol=1e-2, atol=1e-2

用法:
    python3 verify_correctness.py --executable <exe> --config <config.json> \
        --golden-dir <dir> --output <result.json> [--levels smoke,representative]
"""

import argparse
import json
import os
import subprocess
import numpy as np
from pathlib import Path


# 精度阈值
PRECISION_THRESHOLDS = {
    "fp32": {"rtol": 1e-5, "atol": 1e-5},
    "float32": {"rtol": 1e-5, "atol": 1e-5},
    "fp16": {"rtol": 1e-3, "atol": 1e-3},
    "float16": {"rtol": 1e-3, "atol": 1e-3},
    "bf16": {"rtol": 1e-2, "atol": 1e-2},
    "bfloat16": {"rtol": 1e-2, "atol": 1e-2},
}


def run_kernel(executable: str, config: dict, input_dir: str, output_dir: str) -> bool:
    """运行内核，生成输出数据"""
    os.makedirs(output_dir, exist_ok=True)

    env = os.environ.copy()
    env["INPUT_DIR"] = input_dir
    env["OUTPUT_DIR"] = output_dir

    # 传递配置参数作为环境变量
    for key, value in config.items():
        if key.startswith("_"):
            continue
        env[f"CONFIG_{key.upper()}"] = str(value)

    try:
        result = subprocess.run(
            [executable],
            env=env,
            capture_output=True,
            text=True,
            timeout=300,  # 5 分钟超时
        )
        if result.returncode != 0:
            print(f"  内核执行失败 (rc={result.returncode})")
            if result.stderr:
                print(f"  stderr: {result.stderr[:500]}")
            return False
        return True
    except subprocess.TimeoutExpired:
        print("  内核执行超时 (>300s)")
        return False
    except Exception as e:
        print(f"  内核执行异常: {e}")
        return False


def compare_outputs(golden_dir: str, output_dir: str, dtype: str) -> dict:
    """比较内核输出与 golden 数据，使用 allclose 语义"""
    thresholds = PRECISION_THRESHOLDS.get(dtype, {"rtol": 1e-3, "atol": 1e-3})
    rtol = thresholds["rtol"]
    atol = thresholds["atol"]

    result = {
        "passed": True,
        "max_abs_error": 0.0,
        "max_rel_error": 0.0,
        "mean_abs_error": 0.0,
        "mismatch_ratio": 0.0,
        "rtol": rtol,
        "atol": atol,
        "details": [],
    }

    # 找到所有 golden 输出文件
    golden_files = sorted(Path(golden_dir).glob("golden_*.npy"))

    if not golden_files:
        result["passed"] = False
        result["details"].append("未找到 golden 数据文件")
        return result

    total_elements = 0
    total_mismatches = 0

    for golden_file in golden_files:
        tensor_name = golden_file.stem.replace("golden_", "")
        output_file = Path(output_dir) / f"output_{tensor_name}.npy"

        if not output_file.exists():
            # 尝试其他命名格式
            output_file = Path(output_dir) / f"{tensor_name}.npy"

        if not output_file.exists():
            result["passed"] = False
            result["details"].append(f"缺少输出文件: {tensor_name}")
            continue

        golden = np.load(str(golden_file)).astype(np.float64)
        output = np.load(str(output_file)).astype(np.float64)

        if golden.shape != output.shape:
            result["passed"] = False
            result["details"].append(
                f"{tensor_name}: 形状不匹配 golden={golden.shape} output={output.shape}"
            )
            continue

        # 使用 allclose 语义判定通过/失败
        within_tol = np.allclose(output, golden, rtol=rtol, atol=atol, equal_nan=True)

        # 计算诊断指标
        abs_error = np.abs(output - golden)
        max_abs = float(np.nanmax(abs_error))
        mean_abs = float(np.nanmean(abs_error))

        # 相对误差：排除 golden=0 的位置（spec 要求不做除法形式的判定）
        nonzero_mask = np.abs(golden) > 0
        if np.any(nonzero_mask):
            rel_error_vals = np.abs(output[nonzero_mask] - golden[nonzero_mask]) / np.abs(golden[nonzero_mask])
            max_rel = float(np.max(rel_error_vals))
        else:
            max_rel = 0.0

        # mismatch_ratio: 逐元素 allclose 检查
        element_pass = np.abs(output - golden) <= (atol + rtol * np.abs(golden))
        # NaN 处理: 若双方均为 NaN 视为通过 (allclose equal_nan=True)
        both_nan = np.isnan(output) & np.isnan(golden)
        element_pass = element_pass | both_nan
        mismatch_count = int(np.sum(~element_pass))

        total_elements += golden.size
        total_mismatches += mismatch_count

        result["max_abs_error"] = max(result["max_abs_error"], max_abs)
        result["max_rel_error"] = max(result["max_rel_error"], max_rel)
        result["mean_abs_error"] = max(result["mean_abs_error"], mean_abs)

        if not within_tol:
            result["passed"] = False
            result["details"].append(
                f"{tensor_name}: {mismatch_count}/{golden.size} 元素超出阈值 "
                f"(max_abs={max_abs:.6e}, max_rel={max_rel:.6e})"
            )
        else:
            result["details"].append(
                f"{tensor_name}: PASS (max_abs={max_abs:.6e}, max_rel={max_rel:.6e})"
            )

    # 全局 mismatch_ratio
    result["mismatch_ratio"] = total_mismatches / total_elements if total_elements > 0 else 0.0

    return result


def extract_configs(test_config: dict, levels: list) -> list:
    """从测试配置中提取指定级别的配置列表"""
    all_configs = []
    for level in levels:
        level_configs = test_config.get(level, [])
        for c in level_configs:
            c["_level"] = level
        all_configs.extend(level_configs)
    # 向后兼容旧格式
    if not all_configs:
        all_configs = test_config.get("configs", [{}])
    return all_configs


def main():
    parser = argparse.ArgumentParser(description="验证内核输出正确性")
    parser.add_argument("--executable", required=True, help="内核可执行文件")
    parser.add_argument("--config", required=True, help="测试配置 JSON")
    parser.add_argument("--golden-dir", required=True, help="Golden 数据目录")
    parser.add_argument("--output", required=True, help="结果输出 JSON")
    parser.add_argument("--levels", default="smoke,representative,stress",
                        help="要测试的级别（逗号分隔）")
    args = parser.parse_args()

    with open(args.config) as f:
        test_config = json.load(f)

    levels = [l.strip() for l in args.levels.split(",")]
    configs = extract_configs(test_config, levels)
    all_results = []
    pass_count = 0

    for i, config in enumerate(configs):
        config_name = config.get("name", f"config_{i}")
        dtype = config.get("dtype", "fp32")
        level = config.get("_level", "unknown")
        golden_config_dir = os.path.join(args.golden_dir, config_name)
        output_config_dir = os.path.join(args.golden_dir, f"{config_name}_output")

        print(f"  [{level}/{config_name}] 运行内核...")

        # 运行内核
        success = run_kernel(args.executable, config, golden_config_dir, output_config_dir)

        if not success:
            all_results.append({
                "name": config_name,
                "level": level,
                "correctness": 0,
                "error": "内核执行失败",
            })
            continue

        # 比较输出
        comparison = compare_outputs(golden_config_dir, output_config_dir, dtype)

        correctness = 1 if comparison["passed"] else 0
        if correctness:
            pass_count += 1

        all_results.append({
            "name": config_name,
            "level": level,
            "correctness": correctness,
            "max_abs_error": comparison["max_abs_error"],
            "max_rel_error": comparison["max_rel_error"],
            "mean_abs_error": comparison["mean_abs_error"],
            "mismatch_ratio": comparison["mismatch_ratio"],
            "rtol": comparison["rtol"],
            "atol": comparison["atol"],
            "details": comparison["details"],
        })

        status = "PASS" if correctness else "FAIL"
        print(f"  [{level}/{config_name}] {status} max_abs={comparison['max_abs_error']:.6e}")

    total = len(configs)
    correctness_total = pass_count / total if total > 0 else 0.0

    result = {
        "correctness_total": correctness_total,
        "passed": pass_count,
        "total": total,
        "levels_tested": levels,
        "configs": all_results,
    }

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n正确性: {pass_count}/{total} ({correctness_total:.1%})")


if __name__ == "__main__":
    main()
