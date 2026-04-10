#!/bin/bash
# test_performance.sh — 性能测试
#
# 支持两种模式：
# 1. NPU Event 测试（推荐）：通过 PyTorch NPU Event 精确测量
# 2. msprof 测试（兼容）：通过 msprof op 采集详细 profiling 数据
#
# 用法: bash scoring/test_performance.sh <op_path> <config_path> <output_json> [metric_type] [reference_py]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/env_setup.sh"

OP_PATH="${1:?用法: test_performance.sh <op_path> <config_path> <output_json> [metric_type] [reference_py]}"
CONFIG_PATH="${2:?}"
OUTPUT_JSON="${3:?}"
REFERENCE_PY="${5:-}"

WARMUP="${WARMUP_ROUNDS:-10}"
REPEAT="${REPEAT_ROUNDS:-100}"

PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ABS_OP_PATH="$(cd "$OP_PATH" && pwd)"

# 读取 metric_type
METRIC_TYPE="${4:-}"
if [ -z "$METRIC_TYPE" ]; then
    METRIC_TYPE=$(python3 -c "
import json
with open('$CONFIG_PATH') as f:
    cfg = json.load(f)
print(cfg.get('metric_type', 'latency_us'))
" 2>/dev/null || echo "latency_us")
fi

echo "性能测试"
echo "  算子: $ABS_OP_PATH"
echo "  指标: $METRIC_TYPE"
echo "  Warmup: $WARMUP, Repeat: $REPEAT"

# 查找 reference.py
if [ -z "$REFERENCE_PY" ]; then
    OP_NAME=$(python3 -c "
import json
with open('$CONFIG_PATH') as f: cfg = json.load(f)
print(cfg.get('operator', ''))
" 2>/dev/null || echo "")

    for candidate in \
        "$ABS_OP_PATH/../test/reference.py" \
        "$ABS_OP_PATH/../../test/reference.py" \
        "$PROJECT_ROOT/workspace/runs/$OP_NAME/test/reference.py"; do
        if [ -f "$candidate" ]; then
            REFERENCE_PY="$candidate"
            break
        fi
    done
fi

# 模式 1: NPU Event 测试（有 reference.py）
if [ -n "$REFERENCE_PY" ] && [ -f "$REFERENCE_PY" ]; then
    echo "使用 NPU Event 测试 (reference: $REFERENCE_PY)"

    DEPLOY_DIR="$PROJECT_ROOT/workspace/deploy/opp"

    python3 "$SCRIPT_DIR/test_performance.py" \
        --reference "$REFERENCE_PY" \
        --config "$CONFIG_PATH" \
        --output "$OUTPUT_JSON" \
        --metric-type "$METRIC_TYPE" \
        --deploy-dir "$DEPLOY_DIR" \
        --warmup "$WARMUP" \
        --trials "$REPEAT"

    echo "性能测试完成（NPU Event 模式），结果: $OUTPUT_JSON"
    exit 0
fi

# 模式 2: msprof 测试（兼容模式）
echo "使用 msprof 测试（兼容模式）"

# 获取可执行文件
EXECUTABLE=""
if [ -f "$ABS_OP_PATH/build/demo" ]; then
    EXECUTABLE="$ABS_OP_PATH/build/demo"
elif [ -f "$ABS_OP_PATH/build/main" ]; then
    EXECUTABLE="$ABS_OP_PATH/build/main"
else
    EXECUTABLE=$(find "$ABS_OP_PATH/build" -maxdepth 2 -type f -executable 2>/dev/null | head -1 || true)
fi

if [ -z "$EXECUTABLE" ]; then
    echo "错误: 未找到可执行文件且无 reference.py"
    echo "{\"performance_total\": 0.0, \"metric_type\": \"$METRIC_TYPE\", \"error\": \"no executable or reference.py\", \"configs\": []}" > "$OUTPUT_JSON"
    exit 1
fi

KERNEL_DIR="$(dirname "$(dirname "$EXECUTABLE")")"
MSPROF_OUTPUT="$ABS_OP_PATH/msprof_output"
rm -rf "$MSPROF_OUTPUT"

if command -v msprof &> /dev/null; then
    echo "运行 msprof 采集..."
    (cd "$KERNEL_DIR" && msprof op \
        --warm-up="$WARMUP" \
        --output="$MSPROF_OUTPUT" \
        "$EXECUTABLE" 2>&1 || true)

    python3 "$SCRIPT_DIR/perf_summary_wrapper.py" \
        --msprof-output "$MSPROF_OUTPUT" \
        --config "$CONFIG_PATH" \
        --metric-type "$METRIC_TYPE" \
        --output "$OUTPUT_JSON"
else
    echo "警告: msprof 不可用，使用计时模式"
    python3 -c "
import json, subprocess, time

with open('$CONFIG_PATH') as f:
    cfg = json.load(f)

all_configs = []
for level in ['smoke', 'representative', 'stress']:
    for c in cfg.get(level, []):
        c['_level'] = level
        all_configs.append(c)
if not all_configs:
    all_configs = cfg.get('configs', [{}])

results = []
for config in all_configs:
    times = []
    for _ in range($WARMUP):
        subprocess.run(['$EXECUTABLE'], capture_output=True)
    for _ in range($REPEAT):
        start = time.perf_counter()
        subprocess.run(['$EXECUTABLE'], capture_output=True)
        elapsed = time.perf_counter() - start
        times.append(elapsed)
    avg_time = sum(times) / len(times) if times else 0
    results.append({
        'name': config.get('name', 'default'),
        'level': config.get('_level', 'unknown'),
        'task_duration_us': avg_time * 1e6,
        'performance_primary': round(avg_time * 1e6, 3)
    })

metric = '$METRIC_TYPE'
primaries = [r['performance_primary'] for r in results if r['performance_primary'] > 0]
if primaries:
    if metric == 'latency_us':
        perf_total = len(primaries) / sum(1.0/p for p in primaries)
    else:
        from functools import reduce
        import operator
        perf_total = reduce(operator.mul, primaries) ** (1.0/len(primaries))
else:
    perf_total = 0.0

output = {
    'metric_type': metric,
    'performance_total': round(perf_total, 3),
    'configs': results
}
with open('$OUTPUT_JSON', 'w') as f:
    json.dump(output, f, indent=2)
"
fi

echo "性能测试完成（兼容模式），结果: $OUTPUT_JSON"
