#!/bin/bash
# compile.sh — 编译 Ascend C 算子
# 用法: bash scoring/compile.sh <op_path>
# 返回: 0=成功, 1=失败

set -euo pipefail

OP_PATH="${1:?用法: compile.sh <op_path>}"

# 确定芯片类型（从 environment.json 或默认）
ENV_FILE="$OP_PATH/docs/environment.json"
if [ -f "$ENV_FILE" ]; then
    CHIP=$(python3 -c "
import json
with open('$ENV_FILE') as f:
    env = json.load(f)
print(env.get('chip', 'Ascend910B'))
")
else
    CHIP="${ASCEND_PRODUCT_TYPE:-Ascend910B}"
fi

echo "编译算子: $OP_PATH"
echo "目标芯片: $CHIP"

# 方式 1: 使用 run.sh（如果存在且包含 build 逻辑）
if [ -f "$OP_PATH/run.sh" ]; then
    echo "使用 run.sh 编译..."
    cd "$OP_PATH"
    bash run.sh
    exit $?
fi

# 方式 2: 标准 cmake 构建
if [ -f "$OP_PATH/CMakeLists.txt" ]; then
    echo "使用 cmake 编译..."
    BUILD_DIR="$OP_PATH/build"
    mkdir -p "$BUILD_DIR"
    cd "$BUILD_DIR"

    cmake .. \
        -DASCEND_PRODUCT_TYPE="$CHIP" \
        -DASCEND_RUN_MODE=ONBOARD \
        2>&1

    make -j$(nproc) 2>&1

    echo "编译成功"
    exit 0
fi

echo "错误: 未找到 run.sh 或 CMakeLists.txt"
exit 1
