#!/usr/bin/env python3
"""test_correctness.py — PyTorch 框架级正确性测试

通过 PyTorch 框架调用自定义算子（而非直接运行可执行文件），
使用 Model vs ModelNew 对比验证正确性。

参考 MultiKernelBench 的 correctness.py 流程。

精度阈值标准（来源：ops-precision-standard）:
  FP32: rtol=1e-5, atol=1e-5
  FP16: rtol=1e-3, atol=1e-3
  BF16: rtol=1e-2, atol=1e-2

用法:
    python3 test_correctness.py \
        --reference <reference.py> \
        --config <config.json> \
        --output <result.json> \
        --levels smoke,representative
"""

import argparse
import json
import os
import sys
import importlib.util
import traceback

# 精度阈值
PRECISION_THRESHOLDS = {
    "fp32": {"rtol": 1e-5, "atol": 1e-5},
    "float32": {"rtol": 1e-5, "atol": 1e-5},
    "fp16": {"rtol": 1e-3, "atol": 1e-3},
    "float16": {"rtol": 1e-3, "atol": 1e-3},
    "bf16": {"rtol": 1e-2, "atol": 1e-2},
    "bfloat16": {"rtol": 1e-2, "atol": 1e-2},
}

DTYPE_MAP = {
    "fp32": "float32",
    "float32": "float32",
    "fp16": "float16",
    "float16": "float16",
    "bf16": "bfloat16",
    "bfloat16": "bfloat16",
}

NUM_TRIALS = 5
SEED = 42


def load_reference_module(reference_path):
    """动态加载 reference.py 模块"""
    spec = importlib.util.spec_from_file_location("reference", reference_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def extract_configs(test_config, levels):
    """从测试配置中提取指定级别的配置列表"""
    all_configs = []
    for level in levels:
        level_configs = test_config.get(level, [])
        for c in level_configs:
            c["_level"] = level
        all_configs.extend(level_configs)
    if not all_configs:
        all_configs = test_config.get("configs", [{}])
    return all_configs


def _resolve_thresholds(config, test_config):
    """Resolve rtol/atol for a single config in precedence order:
       1. per-config explicit rtol/atol
       2. test-config top-level default_rtol/default_atol
       3. dtype-based PRECISION_THRESHOLDS defaults
    """
    dtype_str = config.get("dtype", "fp32")
    defaults = PRECISION_THRESHOLDS.get(dtype_str, {"rtol": 1e-3, "atol": 1e-3})
    atol = config.get(
        "atol", test_config.get("default_atol", defaults["atol"])
    )
    rtol = config.get(
        "rtol", test_config.get("default_rtol", defaults["rtol"])
    )
    return float(atol), float(rtol)


def _first_mismatch_details(ref, new, atol, rtol, max_elements=5):
    """Return a small dict describing the first few element mismatches."""
    import torch

    diff = (ref - new).abs()
    tol = atol + rtol * ref.abs()
    mismatch_mask = diff > tol
    if not mismatch_mask.any():
        return None

    # Flatten, find first mismatching index in flattened space
    flat_mask = mismatch_mask.flatten()
    flat_ref = ref.flatten()
    flat_new = new.flatten()
    flat_diff = diff.flatten()

    mismatch_indices = torch.nonzero(flat_mask, as_tuple=False).flatten()
    n_mismatch = mismatch_indices.numel()
    sample = mismatch_indices[:max_elements].tolist()

    samples = []
    for flat_idx in sample:
        # Unravel flat_idx → multi-dim index in ref.shape
        multi_idx = []
        rem = int(flat_idx)
        for dim in reversed(ref.shape):
            multi_idx.append(rem % int(dim))
            rem //= int(dim)
        multi_idx.reverse()
        samples.append({
            "index": multi_idx,
            "ref": float(flat_ref[flat_idx].item()),
            "new": float(flat_new[flat_idx].item()),
            "abs_diff": float(flat_diff[flat_idx].item()),
        })

    return {
        "mismatch_count": int(n_mismatch),
        "total_elements": int(ref.numel()),
        "mismatch_ratio": float(n_mismatch / ref.numel()),
        "first_mismatches": samples,
    }


def test_single_config(ref_module, config, device, synchronize, test_config=None):
    """对单个配置运行正确性测试。

    test_config: 顶层 JSON dict（含 default_rtol / default_atol）可选 —
    若提供则传入 _resolve_thresholds 以支持全局默认覆盖。
    """
    import torch

    atol, rtol = _resolve_thresholds(config, test_config or {})

    get_inputs = ref_module.get_inputs
    get_init_inputs = ref_module.get_init_inputs
    Model = ref_module.Model
    ModelNew = ref_module.ModelNew

    result = {
        "passed": True,
        "max_abs_error": 0.0,
        "max_rel_error": 0.0,
        "atol": atol,
        "rtol": rtol,
        "error": None,
    }

    try:
        init_inputs = get_init_inputs()
        init_inputs = [
            x.to(device=device) if isinstance(x, torch.Tensor) else x
            for x in init_inputs
        ]

        with torch.no_grad():
            torch.manual_seed(SEED)
            original_model = Model(*init_inputs).to(device)
            synchronize(device=device)
            torch.manual_seed(SEED)
            custom_model = ModelNew(*init_inputs).to(device)
            synchronize(device=device)

            for trial in range(NUM_TRIALS):
                try:
                    inputs = get_inputs(config)
                except TypeError:
                    inputs = get_inputs()
                inputs = [
                    x.to(device) if isinstance(x, torch.Tensor) else x
                    for x in inputs
                ]
                synchronize(device=device)

                ref_output = original_model(*inputs)
                synchronize(device=device)
                new_output = custom_model(*inputs)
                synchronize(device=device)

                # Shape 检查
                if ref_output.shape != new_output.shape:
                    result["passed"] = False
                    result["error"] = (
                        f"Shape mismatch: expected {ref_output.shape}, "
                        f"got {new_output.shape}"
                    )
                    break

                # 数值检查
                if not torch.allclose(ref_output, new_output, atol=atol, rtol=rtol):
                    diff = (ref_output - new_output).abs()
                    max_abs = diff.max().item()
                    nonzero = ref_output.abs() > 0
                    if nonzero.any():
                        max_rel = (diff[nonzero] / ref_output.abs()[nonzero]).max().item()
                    else:
                        max_rel = 0.0

                    result["passed"] = False
                    result["max_abs_error"] = max_abs
                    result["max_rel_error"] = max_rel
                    result["error"] = (
                        f"Value mismatch at trial {trial}: "
                        f"max_abs={max_abs:.6e}, max_rel={max_rel:.6e}"
                    )
                    # Add detailed first-mismatch diagnostics for debugging
                    details = _first_mismatch_details(
                        ref_output, new_output, atol, rtol, max_elements=5
                    )
                    if details:
                        result["mismatch_details"] = details
                        result["mismatch_details"]["trial"] = trial
                    # Reference statistics help the Architect judge whether
                    # the kernel is "close" or "completely wrong"
                    result["ref_stats"] = {
                        "mean_abs": float(ref_output.abs().mean().item()),
                        "max_abs": float(ref_output.abs().max().item()),
                    }
                    result["new_stats"] = {
                        "mean_abs": float(new_output.abs().mean().item()),
                        "max_abs": float(new_output.abs().max().item()),
                    }
                    break
                else:
                    # 记录通过时的误差供诊断
                    diff = (ref_output - new_output).abs()
                    max_abs = diff.max().item()
                    result["max_abs_error"] = max(result["max_abs_error"], max_abs)

    except Exception as e:
        result["passed"] = False
        result["error"] = f"Runtime error: {str(e)}\n{traceback.format_exc()}"

    return result


def main():
    parser = argparse.ArgumentParser(description="PyTorch 框架级正确性测试")
    parser.add_argument("--reference", required=True, help="reference.py 路径")
    parser.add_argument("--config", required=True, help="测试配置 JSON")
    parser.add_argument("--output", required=True, help="结果输出 JSON")
    parser.add_argument("--levels", default="smoke,representative,stress",
                        help="测试级别（逗号分隔）")
    parser.add_argument("--deploy-dir", default=None,
                        help="算子部署目录（ASCEND_CUSTOM_OPP_PATH）")
    args = parser.parse_args()

    # 设置环境变量
    if args.deploy_dir:
        custom_opp = os.path.join(args.deploy_dir, "vendors", "customize")
        if os.path.exists(custom_opp):
            os.environ["ASCEND_CUSTOM_OPP_PATH"] = custom_opp
            lib_path = os.path.join(custom_opp, "op_api", "lib")
            os.environ["LD_LIBRARY_PATH"] = (
                f"{lib_path}:{os.environ.get('LD_LIBRARY_PATH', '')}"
            )

    # 延迟导入 torch（确保环境变量已设置）
    import torch
    try:
        import torch_npu
        device = torch.device("npu:0")
        synchronize = torch_npu.npu.synchronize
        print("使用 NPU 设备")
    except ImportError:
        device = torch.device("cpu")
        synchronize = lambda device=None: None
        print("警告: torch_npu 不可用，使用 CPU 设备")

    # 加载参考实现
    ref_module = load_reference_module(args.reference)

    # 加载测试配置
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

        print(f"  [{level}/{config_name}] 测试中...")

        result = test_single_config(ref_module, config, device, synchronize, test_config)

        correctness = 1 if result["passed"] else 0
        if correctness:
            pass_count += 1

        cfg_entry = {
            "name": config_name,
            "level": level,
            "dtype": dtype,
            "correctness": correctness,
            "atol": result.get("atol"),
            "rtol": result.get("rtol"),
            "max_abs_error": result.get("max_abs_error", 0.0),
            "max_rel_error": result.get("max_rel_error", 0.0),
            "error": result.get("error"),
        }
        # Optional diagnostic fields (only present on mismatch)
        if "mismatch_details" in result:
            cfg_entry["mismatch_details"] = result["mismatch_details"]
        if "ref_stats" in result:
            cfg_entry["ref_stats"] = result["ref_stats"]
        if "new_stats" in result:
            cfg_entry["new_stats"] = result["new_stats"]
        all_results.append(cfg_entry)

        status = "PASS" if correctness else "FAIL"
        error_info = f" ({result['error'][:100]})" if result.get("error") else ""
        print(f"  [{level}/{config_name}] {status}{error_info}")

    total = len(configs)
    correctness_total = pass_count / total if total > 0 else 0.0

    output = {
        "correctness_total": correctness_total,
        "passed": pass_count,
        "total": total,
        "levels_tested": levels,
        "test_method": "pytorch_framework",
        "configs": all_results,
    }

    with open(args.output, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\n正确性: {pass_count}/{total} ({correctness_total:.1%})")


if __name__ == "__main__":
    main()
