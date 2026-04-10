#!/bin/bash
# test_correctness.sh — 正确性测试（支持分级）
#
# 支持两种模式：
# 1. PyTorch 框架测试（推荐）：通过 reference.py + custom_ops_lib 测试
# 2. 可执行文件测试（兼容）：通过 golden 数据 + verify_correctness.py 测试
#
# 用法: bash scoring/test_correctness.sh <op_path> <config_path> <output_json> [levels] [reference_py]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/env_setup.sh"

OP_PATH="${1:?用法: test_correctness.sh <op_path> <config_path> <output_json> [levels] [reference_py]}"
CONFIG_PATH="${2:?}"
OUTPUT_JSON="${3:?}"
LEVELS="${4:-smoke,representative,stress}"
REFERENCE_PY="${5:-}"

PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ABS_OP_PATH="$(cd "$OP_PATH" && pwd)"

echo "正确性测试"
echo "  算子: $ABS_OP_PATH"
echo "  配置: $CONFIG_PATH"
echo "  级别: $LEVELS"

# 查找 reference.py
if [ -z "$REFERENCE_PY" ]; then
    # 尝试在工作区中查找
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

# 模式 1: PyTorch 框架测试（有 reference.py）
if [ -n "$REFERENCE_PY" ] && [ -f "$REFERENCE_PY" ]; then
    echo "使用 PyTorch 框架测试 (reference: $REFERENCE_PY)"

    DEPLOY_DIR="$PROJECT_ROOT/workspace/deploy/opp"

    python3 "$SCRIPT_DIR/test_correctness.py" \
        --reference "$REFERENCE_PY" \
        --config "$CONFIG_PATH" \
        --output "$OUTPUT_JSON" \
        --levels "$LEVELS" \
        --deploy-dir "$DEPLOY_DIR"

    echo "正确性测试完成（PyTorch 模式），结果: $OUTPUT_JSON"
    exit 0
fi

# 模式 2: 可执行文件测试（兼容模式，使用 golden 数据）
echo "使用可执行文件测试（兼容模式）"

GOLDEN_DIR="${6:-$ABS_OP_PATH/golden_data}"

# 获取可执行文件路径
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
    echo '{"correctness_total": 0.0, "error": "no executable or reference.py found", "configs": []}' > "$OUTPUT_JSON"
    exit 1
fi

# 生成 golden 数据（如果不存在）
if [ ! -d "$GOLDEN_DIR" ] || [ -z "$(ls -A "$GOLDEN_DIR" 2>/dev/null)" ]; then
    python3 "$SCRIPT_DIR/gen_golden.py" \
        --op-path "$ABS_OP_PATH" \
        --config "$CONFIG_PATH" \
        --output-dir "$GOLDEN_DIR"
fi

python3 "$SCRIPT_DIR/verify_correctness.py" \
    --executable "$EXECUTABLE" \
    --config "$CONFIG_PATH" \
    --golden-dir "$GOLDEN_DIR" \
    --levels "$LEVELS" \
    --output "$OUTPUT_JSON"

echo "正确性测试完成（兼容模式），结果: $OUTPUT_JSON"
