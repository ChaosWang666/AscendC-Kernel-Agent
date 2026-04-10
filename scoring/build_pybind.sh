#!/bin/bash
# build_pybind.sh — 构建 Python 绑定（CppExtension）
#
# 编译并安装 custom_ops_lib Python 包，
# 使得 PyTorch 可以通过 `import custom_ops_lib` 调用自定义算子。
#
# 用法: bash scoring/build_pybind.sh <cpp_extension_dir> [deploy_dir]
# 返回: 0=成功, 1=失败

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/env_setup.sh"

CPP_EXT_DIR="${1:?用法: build_pybind.sh <cpp_extension_dir> [deploy_dir]}"
ABS_CPP_EXT_DIR="$(cd "$CPP_EXT_DIR" && pwd)"

# 部署目录（用于设置 ASCEND_CUSTOM_OPP_PATH）
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DEPLOY_DIR="${2:-$PROJECT_ROOT/workspace/deploy/opp}"

echo "========================================"
echo "构建 Python 绑定 (CppExtension)"
echo "  目录: $ABS_CPP_EXT_DIR"
echo "  部署: $DEPLOY_DIR"
echo "========================================"

# 确保 setup.py 存在
if [ ! -f "$ABS_CPP_EXT_DIR/setup.py" ]; then
    echo "错误: 未找到 setup.py"
    exit 1
fi

# 设置环境变量（算子部署路径必须在编译时可见）
CUSTOM_OPP_PATH="$DEPLOY_DIR/vendors/customize"
if [ -d "$CUSTOM_OPP_PATH" ]; then
    export ASCEND_CUSTOM_OPP_PATH="$CUSTOM_OPP_PATH"
    export LD_LIBRARY_PATH="${CUSTOM_OPP_PATH}/op_api/lib:${LD_LIBRARY_PATH:-}"
fi

# 清除旧构建
rm -rf "$ABS_CPP_EXT_DIR/build" "$ABS_CPP_EXT_DIR/dist" "$ABS_CPP_EXT_DIR/custom_ops.egg-info"

# 构建 wheel 包
echo "编译 wheel 包..."
(cd "$ABS_CPP_EXT_DIR" && python3 setup.py build bdist_wheel 2>&1)

# 安装 wheel 包
echo "安装 wheel 包..."
WHEEL_FILE=$(find "$ABS_CPP_EXT_DIR/dist" -name "*.whl" 2>/dev/null | head -1)
if [ -z "$WHEEL_FILE" ]; then
    echo "错误: 未找到 .whl 文件"
    exit 1
fi

pip3 install "$WHEEL_FILE" --force-reinstall 2>&1

# 验证安装
echo "验证安装..."
python3 -c "import custom_ops_lib; print('custom_ops_lib 导入成功:', dir(custom_ops_lib))" 2>&1 || {
    echo "警告: custom_ops_lib 导入失败，但 wheel 已安装"
}

echo "Python 绑定构建完成"
