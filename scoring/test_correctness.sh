#!/bin/bash
# test_correctness.sh — 正确性测试（支持分级）
# 用法: bash scoring/test_correctness.sh <op_path> <config_path> <golden_dir> <output_json> [levels]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

OP_PATH="${1:?用法: test_correctness.sh <op_path> <config_path> <golden_dir> <output_json> [levels]}"
CONFIG_PATH="${2:?}"
GOLDEN_DIR="${3:?}"
OUTPUT_JSON="${4:?}"
LEVELS="${5:-smoke,representative,stress}"

echo "正确性测试"
echo "  算子: $OP_PATH"
echo "  配置: $CONFIG_PATH"
echo "  Golden: $GOLDEN_DIR"
echo "  级别: $LEVELS"

# 获取可执行文件路径
EXECUTABLE=""
if [ -f "$OP_PATH/build/demo" ]; then
    EXECUTABLE="$OP_PATH/build/demo"
elif [ -f "$OP_PATH/build/main" ]; then
    EXECUTABLE="$OP_PATH/build/main"
else
    # 搜索 build 目录下的可执行文件
    EXECUTABLE=$(find "$OP_PATH/build" -maxdepth 2 -type f -executable 2>/dev/null | head -1 || true)
fi

if [ -z "$EXECUTABLE" ]; then
    echo "错误: 未找到可执行文件"
    echo '{"correctness_total": 0.0, "error": "executable not found", "configs": []}' > "$OUTPUT_JSON"
    exit 1
fi

# 读取配置并逐个测试
python3 "$SCRIPT_DIR/verify_correctness.py" \
    --executable "$EXECUTABLE" \
    --config "$CONFIG_PATH" \
    --golden-dir "$GOLDEN_DIR" \
    --levels "$LEVELS" \
    --output "$OUTPUT_JSON"

echo "正确性测试完成，结果: $OUTPUT_JSON"
