#!/bin/bash
# env_setup.sh — 加载 CANN 环境变量
# 所有 scoring 脚本在执行前 source 此文件

# 如果环境已设置，跳过
if [ -n "${ASCEND_HOME_PATH:-}" ]; then
    return 0 2>/dev/null || true
fi

# 使用官方 set_env.sh 导入环境
if [ -f /usr/local/Ascend/ascend-toolkit/set_env.sh ]; then
    source /usr/local/Ascend/ascend-toolkit/set_env.sh
else
    echo "警告: 未找到 /usr/local/Ascend/ascend-toolkit/set_env.sh" >&2
fi

# 如果有自定义算子部署目录，设置环境变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
CUSTOM_OPP_DIR="$PROJECT_ROOT/workspace/deploy/opp/vendors/customize"
if [ -d "$CUSTOM_OPP_DIR" ] && [ -z "${ASCEND_CUSTOM_OPP_PATH:-}" ]; then
    export ASCEND_CUSTOM_OPP_PATH="$CUSTOM_OPP_DIR"
    export LD_LIBRARY_PATH="${CUSTOM_OPP_DIR}/op_api/lib:${LD_LIBRARY_PATH:-}"
fi
