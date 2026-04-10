#!/bin/bash
# compile.sh — 构建自定义算子工程
#
# 支持两种模式：
# 1. 已有工程目录（{OpName}Custom/build.sh 存在）→ 直接构建
# 2. 有算子定义 JSON（{op_name}_custom.json 存在）→ msopgen 生成工程 + 构建
#
# 用法: bash scoring/compile.sh <op_path>
# 返回: 0=成功, 1=失败

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/env_setup.sh"

OP_PATH="${1:?用法: compile.sh <op_path>}"
ABS_OP_PATH="$(cd "$OP_PATH" && pwd)"

# 确定芯片类型
ENV_FILE="$ABS_OP_PATH/docs/environment.json"
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

# 转换芯片型号为 msopgen 格式（Ascend910B → ai_core-Ascend910B）
MSOPGEN_DEVICE="ai_core-${CHIP}"

echo "========================================"
echo "构建自定义算子工程"
echo "  算子路径: $ABS_OP_PATH"
echo "  目标芯片: $CHIP"
echo "========================================"

# 查找自定义算子工程目录
OP_PROJECT_DIR=""
for dir in "$ABS_OP_PATH"/*Custom/ "$ABS_OP_PATH"/*custom/; do
    if [ -d "$dir" ] && [ -f "$dir/build.sh" ]; then
        OP_PROJECT_DIR="$dir"
        break
    fi
done

# 模式 1: 已有工程目录，直接构建
if [ -n "$OP_PROJECT_DIR" ]; then
    echo "找到算子工程: $OP_PROJECT_DIR"

    # 清除旧构建产物
    rm -rf "$OP_PROJECT_DIR/build_out"

    # 清除可能干扰构建的环境变量
    unset ASCEND_CUSTOM_OPP_PATH 2>/dev/null || true

    echo "开始构建..."
    (cd "$OP_PROJECT_DIR" && bash build.sh 2>&1)

    # 验证构建产物
    RUN_FILE=$(find "$OP_PROJECT_DIR/build_out" -maxdepth 1 -name "custom_opp_*.run" 2>/dev/null | head -1)
    if [ -z "$RUN_FILE" ]; then
        echo "错误: 构建完成但未找到 custom_opp_*.run 文件"
        exit 1
    fi

    echo "构建成功: $RUN_FILE"
    exit 0
fi

# 模式 2: 有算子定义 JSON，先生成工程再构建
JSON_FILE=$(find "$ABS_OP_PATH" -maxdepth 1 -name "*_custom.json" 2>/dev/null | head -1)
if [ -n "$JSON_FILE" ]; then
    echo "找到算子定义: $JSON_FILE"

    # 从 JSON 提取算子名（PascalCase）
    OP_CAPITAL=$(python3 -c "
import json
with open('$JSON_FILE') as f:
    data = json.load(f)
print(data[0]['op'])
")

    echo "生成算子工程: $OP_CAPITAL"

    # 删除已有工程（如果存在）
    if [ -d "$ABS_OP_PATH/$OP_CAPITAL" ]; then
        rm -rf "$ABS_OP_PATH/$OP_CAPITAL"
    fi

    # 使用 msopgen 生成工程骨架
    (cd "$ABS_OP_PATH" && msopgen gen \
        -i "$(basename "$JSON_FILE")" \
        -c "$MSOPGEN_DEVICE" \
        -lan cpp \
        -out "$OP_CAPITAL" 2>&1)

    if [ ! -d "$ABS_OP_PATH/$OP_CAPITAL" ]; then
        echo "错误: msopgen 生成工程失败"
        exit 1
    fi

    echo "工程骨架生成成功"

    # 检查是否有预写好的源文件需要覆盖到工程中
    # op_host/ 和 op_kernel/ 中的源文件会覆盖 msopgen 生成的默认文件
    for src_dir in "op_host" "op_kernel"; do
        SRC_PATH="$ABS_OP_PATH/$src_dir"
        if [ -d "$SRC_PATH" ]; then
            echo "覆盖 $src_dir/ 中的源文件..."
            cp -f "$SRC_PATH"/*.cpp "$ABS_OP_PATH/$OP_CAPITAL/$src_dir/" 2>/dev/null || true
            cp -f "$SRC_PATH"/*.h "$ABS_OP_PATH/$OP_CAPITAL/$src_dir/" 2>/dev/null || true
        fi
    done

    # 清除可能干扰构建的环境变量
    unset ASCEND_CUSTOM_OPP_PATH 2>/dev/null || true

    # 构建
    echo "开始构建..."
    (cd "$ABS_OP_PATH/$OP_CAPITAL" && bash build.sh 2>&1)

    # 验证构建产物
    RUN_FILE=$(find "$ABS_OP_PATH/$OP_CAPITAL/build_out" -maxdepth 1 -name "custom_opp_*.run" 2>/dev/null | head -1)
    if [ -z "$RUN_FILE" ]; then
        echo "错误: 构建完成但未找到 custom_opp_*.run 文件"
        exit 1
    fi

    echo "构建成功: $RUN_FILE"
    exit 0
fi

# 兼容旧模式：直接 cmake 构建（Kernel 直调）
if [ -f "$ABS_OP_PATH/CMakeLists.txt" ]; then
    echo "警告: 未找到自定义算子工程，使用 cmake 直接构建（兼容模式）"
    BUILD_DIR="$ABS_OP_PATH/build"
    mkdir -p "$BUILD_DIR"
    (
        cd "$BUILD_DIR"
        cmake .. \
            -DASCEND_PRODUCT_TYPE="$CHIP" \
            -DASCEND_RUN_MODE=ONBOARD \
            2>&1
        make -j$(nproc) 2>&1
    )
    echo "编译成功（兼容模式）"
    exit 0
fi

echo "错误: 未找到 build.sh、*_custom.json 或 CMakeLists.txt"
exit 1
