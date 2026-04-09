#!/bin/bash
# score.sh — 评分函数总编排
# 用法: bash scoring/score.sh <op_path> <config_path>
# 输出: evolution/scores/v<N>.json
#
# 流程: compile → gen_golden → test_correctness → test_performance → compute_score

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

OP_PATH="${1:?用法: score.sh <op_path> <config_path>}"
CONFIG_PATH="${2:?用法: score.sh <op_path> <config_path>}"

# 从 evolution/state.json 获取下一个版本号，若不存在则默认 v0
STATE_FILE="$PROJECT_ROOT/evolution/state.json"
if [ -f "$STATE_FILE" ]; then
    NEXT_VERSION=$(python3 -c "
import json
with open('$STATE_FILE') as f:
    state = json.load(f)
print(state.get('current_version', 0) + 1)
")
else
    NEXT_VERSION=0
fi

SCORE_OUTPUT="$PROJECT_ROOT/evolution/scores/v${NEXT_VERSION}.json"
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo "=========================================="
echo "评分函数 v${NEXT_VERSION}"
echo "算子路径: $OP_PATH"
echo "配置文件: $CONFIG_PATH"
echo "=========================================="

# ========== Step 1: 编译 ==========
echo ""
echo "[Step 1/5] 编译..."
COMPILE_LOG="$TEMP_DIR/compile.log"

if ! bash "$SCRIPT_DIR/compile.sh" "$OP_PATH" > "$COMPILE_LOG" 2>&1; then
    echo "  ❌ 编译失败"
    python3 "$SCRIPT_DIR/compute_score.py" \
        --version "$NEXT_VERSION" \
        --compile-error "$COMPILE_LOG" \
        --output "$SCORE_OUTPUT"
    echo "评分已写入: $SCORE_OUTPUT"
    cat "$SCORE_OUTPUT"
    exit 1
fi
echo "  ✅ 编译成功"

# ========== Step 2: 生成 Golden 数据 ==========
echo ""
echo "[Step 2/5] 生成 Golden 参考数据..."
GOLDEN_DIR="$OP_PATH/golden_data"

if [ ! -d "$GOLDEN_DIR" ] || [ "$GOLDEN_DIR" -ot "$CONFIG_PATH" ]; then
    python3 "$SCRIPT_DIR/gen_golden.py" \
        --op-path "$OP_PATH" \
        --config "$CONFIG_PATH" \
        --output-dir "$GOLDEN_DIR"
    echo "  ✅ Golden 数据已生成"
else
    echo "  ⏭️  Golden 数据已存在，跳过"
fi

# ========== Step 3: 正确性测试 ==========
echo ""
echo "[Step 3/5] 正确性测试..."
CORRECTNESS_RESULT="$TEMP_DIR/correctness.json"

bash "$SCRIPT_DIR/test_correctness.sh" \
    "$OP_PATH" "$CONFIG_PATH" "$GOLDEN_DIR" "$CORRECTNESS_RESULT"

CORRECTNESS_TOTAL=$(python3 -c "
import json
with open('$CORRECTNESS_RESULT') as f:
    r = json.load(f)
print(r['correctness_total'])
")

echo "  正确性: $CORRECTNESS_TOTAL"

if [ "$(echo "$CORRECTNESS_TOTAL < 1.0" | bc -l)" -eq 1 ]; then
    echo "  ❌ 正确性未通过，跳过性能测试"
    python3 "$SCRIPT_DIR/compute_score.py" \
        --version "$NEXT_VERSION" \
        --correctness-result "$CORRECTNESS_RESULT" \
        --output "$SCORE_OUTPUT"
    echo "评分已写入: $SCORE_OUTPUT"
    cat "$SCORE_OUTPUT"
    exit 1
fi
echo "  ✅ 全部正确性测试通过"

# ========== Step 4: 性能测试 ==========
echo ""
echo "[Step 4/5] 性能测试..."
PERFORMANCE_RESULT="$TEMP_DIR/performance.json"

bash "$SCRIPT_DIR/test_performance.sh" \
    "$OP_PATH" "$CONFIG_PATH" "$PERFORMANCE_RESULT"

echo "  ✅ 性能测试完成"

# ========== Step 5: 聚合评分 ==========
echo ""
echo "[Step 5/5] 聚合评分..."
python3 "$SCRIPT_DIR/compute_score.py" \
    --version "$NEXT_VERSION" \
    --correctness-result "$CORRECTNESS_RESULT" \
    --performance-result "$PERFORMANCE_RESULT" \
    --output "$SCORE_OUTPUT"

echo ""
echo "=========================================="
echo "评分完成"
echo "结果: $SCORE_OUTPUT"
echo "=========================================="
cat "$SCORE_OUTPUT"
