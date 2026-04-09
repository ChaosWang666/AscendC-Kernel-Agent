#!/bin/bash
# test_performance.sh — 性能测试（msprof 采集，支持多指标类型）
# 用法: bash scoring/test_performance.sh <op_path> <config_path> <output_json> [metric_type]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

OP_PATH="${1:?用法: test_performance.sh <op_path> <config_path> <output_json> [metric_type]}"
CONFIG_PATH="${2:?}"
OUTPUT_JSON="${3:?}"

WARMUP="${WARMUP_ROUNDS:-10}"
REPEAT="${REPEAT_ROUNDS:-5}"

# 读取 metric_type: 优先使用第 4 个参数，否则从配置文件读取
METRIC_TYPE="${4:-}"
if [ -z "$METRIC_TYPE" ]; then
    METRIC_TYPE=$(python3 -c "
import json
with open('$CONFIG_PATH') as f:
    cfg = json.load(f)
print(cfg.get('metric_type', 'tflops'))
" 2>/dev/null || echo "tflops")
fi

echo "性能测试"
echo "  算子: $OP_PATH"
echo "  指标: $METRIC_TYPE"
echo "  Warmup: $WARMUP, Repeat: $REPEAT"

# 获取可执行文件
EXECUTABLE=""
if [ -f "$OP_PATH/build/demo" ]; then
    EXECUTABLE="$OP_PATH/build/demo"
elif [ -f "$OP_PATH/build/main" ]; then
    EXECUTABLE="$OP_PATH/build/main"
else
    EXECUTABLE=$(find "$OP_PATH/build" -maxdepth 2 -type f -executable 2>/dev/null | head -1 || true)
fi

if [ -z "$EXECUTABLE" ]; then
    echo "错误: 未找到可执行文件"
    echo "{\"performance_total\": 0.0, \"metric_type\": \"$METRIC_TYPE\", \"error\": \"executable not found\", \"configs\": []}" > "$OUTPUT_JSON"
    exit 1
fi

# msprof 性能采集
MSPROF_OUTPUT="$OP_PATH/msprof_output"
rm -rf "$MSPROF_OUTPUT"

echo "运行 msprof 采集..."
if command -v msprof &> /dev/null; then
    msprof op \
        --warm-up="$WARMUP" \
        --output="$MSPROF_OUTPUT" \
        "$EXECUTABLE" 2>&1 || true

    # 解析 msprof 结果
    python3 "$SCRIPT_DIR/perf_summary_wrapper.py" \
        --msprof-output "$MSPROF_OUTPUT" \
        --config "$CONFIG_PATH" \
        --metric-type "$METRIC_TYPE" \
        --output "$OUTPUT_JSON"
else
    echo "警告: msprof 不可用，使用计时模式"
    # 降级方案：直接运行并计时
    python3 -c "
import json, subprocess, time

with open('$CONFIG_PATH') as f:
    cfg = json.load(f)

# 提取所有级别配置
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
    # warmup
    for _ in range($WARMUP):
        subprocess.run(['$EXECUTABLE'], capture_output=True)
    # measure
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
        'performance_primary': round(avg_time * 1e6, 3) if '$METRIC_TYPE' == 'latency_us' else 0.0
    })

output = {
    'metric_type': '$METRIC_TYPE',
    'performance_total': 0.0,
    'configs': results
}
with open('$OUTPUT_JSON', 'w') as f:
    json.dump(output, f, indent=2)
"
fi

echo "性能测试完成，结果: $OUTPUT_JSON"
