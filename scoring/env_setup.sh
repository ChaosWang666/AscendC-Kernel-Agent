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

# Preflight: verify Python packaging toolchain actually imports (not as namespace package)
# 触发场景：site-packages/{setuptools,pip,_distutils_hack} 目录被设为 750 root:root 时，
# Python import 机制会把它们降级为空的隐式 namespace package，或进入 setuptools 的
# `__init__.py` 后 `import _distutils_hack.override` 链式失败。错误信息可能是：
#   - ImportError: cannot import name 'setup' from 'setuptools'
#   - ModuleNotFoundError: No module named '_distutils_hack.override'
# 若跳过预检，后续 build_pybind 会浪费 compile+deploy 周期后才报错。
# 本检查**不致命**（只警告），因为某些受限环境下可能不需要 pybind 阶段。
if [ -z "${ASCENDC_ENV_PREFLIGHT_SKIP:-}" ]; then
    # 完整链路：setuptools + _distutils_hack + pip
    if ! python3 -c "
from setuptools import setup, find_packages
import _distutils_hack
import pip
" >/dev/null 2>&1; then
        cat >&2 <<'EOF'
[env_setup.sh] WARNING: Python 打包工具链导入失败 (setuptools / _distutils_hack / pip)
  常见原因：/usr/local/lib/python3.11/site-packages/ 下相关目录被设为 750 root:root，
  Python import 降级为空 namespace package 或 ModuleNotFoundError。
  影响：scoring/build_pybind.sh 会在后续阶段失败。
  修复（需要 root）：
    sudo chmod -R o+rX \
      /usr/local/lib/python3.11/site-packages/setuptools \
      /usr/local/lib/python3.11/site-packages/pip \
      /usr/local/lib/python3.11/site-packages/pkg_resources \
      /usr/local/lib/python3.11/site-packages/_distutils_hack
  或在非 pybind 流程下设置 ASCENDC_ENV_PREFLIGHT_SKIP=1 跳过本检查。
EOF
    fi
fi
