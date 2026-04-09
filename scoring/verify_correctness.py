#!/usr/bin/env python3
"""verify_correctness.py — 验证内核输出与 golden 参考数据的一致性

精度阈值标准（来源：ops-precision-standard）:
  FP32: rtol=1e-5, atol=1e-5
  FP16: rtol=1e-3, atol=1e-3
  BF16: rtol=1e-2, atol=1e-2

用法:
    python3 verify_correctness.py --executable <exe> --config <config.json> \
        --golden-dir <dir> --output <result.json>
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
    """比较内核输出与 golden 数据"""
    thresholds = PRECISION_THRESHOLDS.get(dtype, {"rtol": 1e-3, "atol": 1e-3})
    rtol = thresholds["rtol"]
    atol = thresholds["atol"]

    result = {
        "passed": True,
        "max_abs_error": 0.0,
        "max_rel_error": 0.0,
        "mean_abs_error": 0.0,
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

        # 计算误差
        abs_error = np.abs(output - golden)
        max_abs = float(np.max(abs_error))
        mean_abs = float(np.mean(abs_error))

        # 相对误差（避免除零）
        denom = np.maximum(np.abs(golden), 1e-10)
        rel_error = abs_error / denom
        max_rel = float(np.max(rel_error))

        result["max_abs_error"] = max(result["max_abs_error"], max_abs)
        result["max_rel_error"] = max(result["max_rel_error"], max_rel)
        result["mean_abs_error"] = max(result["mean_abs_error"], mean_abs)

        # 检查是否在阈值内
        within_tol = np.all((abs_error <= atol) | (rel_error <= rtol))

        if not within_tol:
            result["passed"] = False
            exceed_count = int(np.sum(~((abs_error <= atol) | (rel_error <= rtol))))
            total = golden.size
            result["details"].append(
                f"{tensor_name}: {exceed_count}/{total} 元素超出阈值 "
                f"(max_abs={max_abs:.6e}, max_rel={max_rel:.6e})"
            )
        else:
            result["details"].append(
                f"{tensor_name}: ✅ (max_abs={max_abs:.6e}, max_rel={max_rel:.6e})"
            )

    return result


def main():
    parser = argparse.ArgumentParser(description="验证内核输出正确性")
    parser.add_argument("--executable", required=True, help="内核可执行文件")
    parser.add_argument("--config", required=True, help="测试配置 JSON")
    parser.add_argument("--golden-dir", required=True, help="Golden 数据目录")
    parser.add_argument("--output", required=True, help="结果输出 JSON")
    args = parser.parse_args()

    with open(args.config) as f:
        test_config = json.load(f)

    configs = test_config.get("configs", [{}])
    all_results = []
    pass_count = 0

    for i, config in enumerate(configs):
        config_name = config.get("name", f"config_{i}")
        dtype = config.get("dtype", "fp32")
        golden_config_dir = os.path.join(args.golden_dir, config_name)
        output_config_dir = os.path.join(args.golden_dir, f"{config_name}_output")

        print(f"  [{config_name}] 运行内核...")

        # 运行内核
        success = run_kernel(args.executable, config, golden_config_dir, output_config_dir)

        if not success:
            all_results.append({
                "name": config_name,
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
            "correctness": correctness,
            "max_abs_error": comparison["max_abs_error"],
            "max_rel_error": comparison["max_rel_error"],
            "mean_abs_error": comparison["mean_abs_error"],
            "rtol": comparison["rtol"],
            "atol": comparison["atol"],
            "details": comparison["details"],
        })

        status = "✅" if correctness else "❌"
        print(f"  [{config_name}] {status} max_abs={comparison['max_abs_error']:.6e}")

    total = len(configs)
    correctness_total = pass_count / total if total > 0 else 0.0

    result = {
        "correctness_total": correctness_total,
        "passed": pass_count,
        "total": total,
        "configs": all_results,
    }

    with open(args.output, "w") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"\n正确性: {pass_count}/{total} ({correctness_total:.1%})")


if __name__ == "__main__":
    main()
