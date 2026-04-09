#!/bin/bash
# test_performance.sh — 性能测试（msprof 采集）
# 用法: bash scoring/test_performance.sh <op_path> <config_path> <output_json>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

OP_PATH="${1:?用法: test_performance.sh <op_path> <config_path> <output_json>}"
CONFIG_PATH="${2:?}"
OUTPUT_JSON="${3:?}"

WARMUP="${WARMUP_ROUNDS:-10}"
REPEAT="${REPEAT_ROUNDS:-5}"

echo "性能测试"
echo "  算子: $OP_PATH"
echo "  Warmup: $WARMUP, Repeat: $REPEAT"

# 获取可执行文件
EXECUTABLE=""
if [ -f "$OP_PATH/build/demo" ]; then
    EXECUTABLE="$OP_PATH/build/demo"
elif [ -f "$OP_PATH/build/main" ]; then
    EXECUTABLE="$OP_PATH/build/main"
else
    EXECUTABLE=$(find "$OP_PATH/build" -maxdepth 2 -type f -executable | head -1 || true)
fi

if [ -z "$EXECUTABLE" ]; then
    echo "错误: 未找到可执行文件"
    echo '{"performance_total_tflops": 0.0, "error": "executable not found", "configs": []}' > "$OUTPUT_JSON"
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
        --output "$OUTPUT_JSON"
else
    echo "警告: msprof 不可用，使用计时模式"
    # 降级方案：直接运行并计时
    python3 -c "
import json, subprocess, time

with open('$CONFIG_PATH') as f:
    cfg = json.load(f)

results = []
for config in cfg.get('configs', [{}]):
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
        'task_duration_us': avg_time * 1e6,
        'tflops': 0.0  # 需要 flops 公式才能计算
    })

output = {
    'performance_total_tflops': 0.0,
    'configs': results
}
with open('$OUTPUT_JSON', 'w') as f:
    json.dump(output, f, indent=2)
"
fi

echo "性能测试完成，结果: $OUTPUT_JSON"
