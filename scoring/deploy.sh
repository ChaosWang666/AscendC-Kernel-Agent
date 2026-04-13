#!/bin/bash
# deploy.sh — 部署自定义算子包
#
# 查找 build_out/ 下的 custom_opp_*.run 自安装包，
# 部署到指定的 OPP 目录。
#
# 用法: bash scoring/deploy.sh <op_path> [deploy_dir]
# 返回: 0=成功, 1=失败

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/env_setup.sh"

OP_PATH="${1:?用法: deploy.sh <op_path> [deploy_dir]}"
ABS_OP_PATH="$(cd "$OP_PATH" && pwd)"

# 默认部署目录
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEPLOY_DIR="${2:-$PROJECT_ROOT/workspace/deploy/opp}"

# The .run installer requires an ABSOLUTE path for --install-path (relative
# paths get rejected at install time). Normalize early so all later uses
# (mkdir, env exports, logging) see the canonical absolute form.
mkdir -p "$DEPLOY_DIR"
DEPLOY_DIR="$(cd "$DEPLOY_DIR" && pwd)"

echo "========================================"
echo "部署自定义算子包"
echo "  算子路径: $ABS_OP_PATH"
echo "  部署目录: $DEPLOY_DIR"
echo "========================================"

# 查找 .run 文件（在算子工程的 build_out/ 目录下）
RUN_FILE=""
for dir in "$ABS_OP_PATH"/*Custom/build_out "$ABS_OP_PATH"/*custom/build_out "$ABS_OP_PATH"/build_out; do
    if [ -d "$dir" ]; then
        found=$(find "$dir" -maxdepth 1 -name "custom_opp_*.run" 2>/dev/null | head -1)
        if [ -n "$found" ]; then
            RUN_FILE="$found"
            break
        fi
    fi
done

if [ -z "$RUN_FILE" ]; then
    echo "错误: 未找到 custom_opp_*.run 部署包"
    echo "请先运行 compile.sh 构建算子工程"
    exit 1
fi

echo "找到部署包: $RUN_FILE"

# DEPLOY_DIR 已在脚本开头 normalize 为绝对路径（.run installer 要求）
# 执行部署
echo "开始部署..."
chmod +x "$RUN_FILE"
"$RUN_FILE" --install-path="$DEPLOY_DIR" 2>&1 || {
    # 部分 .run 文件不支持 --install-path，尝试不带参数运行
    echo "尝试默认部署方式..."
    (cd "$(dirname "$RUN_FILE")" && ./$(basename "$RUN_FILE") 2>&1)
}

# 设置环境变量
CUSTOM_OPP_PATH="$DEPLOY_DIR/vendors/customize"
if [ -d "$CUSTOM_OPP_PATH" ]; then
    export ASCEND_CUSTOM_OPP_PATH="$CUSTOM_OPP_PATH"
    export LD_LIBRARY_PATH="${CUSTOM_OPP_PATH}/op_api/lib:${LD_LIBRARY_PATH:-}"
    echo "部署成功"
    echo "  ASCEND_CUSTOM_OPP_PATH=$ASCEND_CUSTOM_OPP_PATH"
else
    echo "警告: 部署目录结构异常，未找到 vendors/customize/"
    # 尝试检查其他可能的路径
    ls -la "$DEPLOY_DIR" 2>/dev/null || true
fi

echo "部署完成"
