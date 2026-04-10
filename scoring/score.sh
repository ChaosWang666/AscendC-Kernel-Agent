#!/bin/bash
# score.sh — 分级评分总编排
#
# 自定义算子工程评分流程:
#   1. compile.sh    — 构建自定义算子工程（msopgen + build.sh）
#   2. deploy.sh     — 部署算子包（.run 安装器）
#   3. build_pybind.sh — 构建 Python 绑定（CppExtension）
#   4. smoke correctness  — 通过 PyTorch 框架测试正确性
#   5. representative correctness
#   6. 若 correctness_total < 1.0 → 结束
#   7. representative performance — NPU Event 性能测试
#   8. 若满足提交门槛 → stress correctness + stress performance
#   9. compute_score.py → 聚合为最终 JSON
#
# 用法: bash scoring/score.sh <op_path> <config_path>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/env_setup.sh"

OP_PATH="${1:?用法: score.sh <op_path> <config_path>}"
CONFIG_PATH="${2:?}"

# 读取配置
METRIC_TYPE=$(python3 -c "
import json
with open('$CONFIG_PATH') as f: cfg = json.load(f)
print(cfg.get('metric_type', 'latency_us'))
" 2>/dev/null || echo "latency_us")

MIN_IMPROVEMENT=$(python3 -c "
import json
with open('$CONFIG_PATH') as f: cfg = json.load(f)
print(cfg.get('min_improvement_ratio', 0.02))
" 2>/dev/null || echo "0.02")

OP_NAME=$(python3 -c "
import json
with open('$CONFIG_PATH') as f: cfg = json.load(f)
print(cfg.get('operator', 'unknown'))
" 2>/dev/null || echo "unknown")

# 读取当前版本号和最佳评分
VERSION=$(python3 -c "
import json, os
state_path = os.path.join('$PROJECT_ROOT', 'evolution', 'state.json')
if os.path.exists(state_path):
    with open(state_path) as f: s = json.load(f)
    print(s.get('current_step', 0))
else:
    print(0)
" 2>/dev/null || echo "0")

BEST_SCORE=$(python3 -c "
import json, os
state_path = os.path.join('$PROJECT_ROOT', 'evolution', 'state.json')
if os.path.exists(state_path):
    with open(state_path) as f: s = json.load(f)
    print(s.get('best_score', 0.0))
else:
    print(0.0)
" 2>/dev/null || echo "0.0")

# 输出路径
SCORES_DIR="$PROJECT_ROOT/evolution/scores"
mkdir -p "$SCORES_DIR"
SCORE_JSON="$SCORES_DIR/v${VERSION}.json"

# 临时结果
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

COMPILE_LOG="$TMPDIR/compile.log"
DEPLOY_LOG="$TMPDIR/deploy.log"
PYBIND_LOG="$TMPDIR/pybind.log"
CORRECTNESS_SMOKE="$TMPDIR/correctness_smoke.json"
CORRECTNESS_REP="$TMPDIR/correctness_rep.json"
CORRECTNESS_STRESS="$TMPDIR/correctness_stress.json"
CORRECTNESS_ALL="$TMPDIR/correctness_all.json"
PERFORMANCE_REP="$TMPDIR/performance_rep.json"
PERFORMANCE_STRESS="$TMPDIR/performance_stress.json"
PERFORMANCE_ALL="$TMPDIR/performance_all.json"

LEVELS_RUN=""
DEPLOY_DIR="$PROJECT_ROOT/workspace/deploy/opp"
CPP_EXT_DIR="$PROJECT_ROOT/workspace/runs/$OP_NAME/test/CppExtension"
REFERENCE_PY="$PROJECT_ROOT/workspace/runs/$OP_NAME/test/reference.py"

echo "========================================"
echo "分级评分 (v${VERSION})"
echo "  算子: $OP_PATH"
echo "  配置: $CONFIG_PATH"
echo "  指标: $METRIC_TYPE"
echo "  最佳: $BEST_SCORE"
echo "  模式: 自定义算子工程"
echo "========================================"

# ============ Step 1: 构建自定义算子工程 ============
echo ""
echo ">>> Step 1: 构建自定义算子工程"
if ! bash "$SCRIPT_DIR/compile.sh" "$OP_PATH" > "$COMPILE_LOG" 2>&1; then
    echo "构建失败"
    cat "$COMPILE_LOG" | tail -20
    python3 "$SCRIPT_DIR/compute_score.py" \
        --version "$VERSION" \
        --compile-error "$COMPILE_LOG" \
        --metric-type "$METRIC_TYPE" \
        --output "$SCORE_JSON"
    echo "评分结果: $SCORE_JSON"
    exit 0
fi
echo "构建成功"

# ============ Step 2: 部署算子包 ============
echo ""
echo ">>> Step 2: 部署算子包"
if ! bash "$SCRIPT_DIR/deploy.sh" "$OP_PATH" "$DEPLOY_DIR" > "$DEPLOY_LOG" 2>&1; then
    echo "部署失败"
    cat "$DEPLOY_LOG" | tail -20
    python3 "$SCRIPT_DIR/compute_score.py" \
        --version "$VERSION" \
        --compile-error "$DEPLOY_LOG" \
        --metric-type "$METRIC_TYPE" \
        --output "$SCORE_JSON"
    echo "评分结果: $SCORE_JSON"
    exit 0
fi

# 设置部署后的环境变量
CUSTOM_OPP_PATH="$DEPLOY_DIR/vendors/customize"
if [ -d "$CUSTOM_OPP_PATH" ]; then
    export ASCEND_CUSTOM_OPP_PATH="$CUSTOM_OPP_PATH"
    export LD_LIBRARY_PATH="${CUSTOM_OPP_PATH}/op_api/lib:${LD_LIBRARY_PATH:-}"
fi
echo "部署成功"

# ============ Step 3: 构建 Python 绑定 ============
echo ""
echo ">>> Step 3: 构建 Python 绑定"
if [ -d "$CPP_EXT_DIR" ]; then
    if ! bash "$SCRIPT_DIR/build_pybind.sh" "$CPP_EXT_DIR" "$DEPLOY_DIR" > "$PYBIND_LOG" 2>&1; then
        echo "Python 绑定构建失败"
        cat "$PYBIND_LOG" | tail -20
        python3 "$SCRIPT_DIR/compute_score.py" \
            --version "$VERSION" \
            --compile-error "$PYBIND_LOG" \
            --metric-type "$METRIC_TYPE" \
            --output "$SCORE_JSON"
        echo "评分结果: $SCORE_JSON"
        exit 0
    fi
    echo "Python 绑定构建成功"
    USE_PYTORCH=true
else
    echo "未找到 CppExtension 目录，使用兼容模式"
    USE_PYTORCH=false
fi

# ============ Step 4: Smoke 正确性 ============
echo ""
echo ">>> Step 4: Smoke 正确性测试"
if [ "$USE_PYTORCH" = true ] && [ -f "$REFERENCE_PY" ]; then
    bash "$SCRIPT_DIR/test_correctness.sh" \
        "$OP_PATH" "$CONFIG_PATH" "$CORRECTNESS_SMOKE" "smoke" "$REFERENCE_PY"
else
    # 兼容模式
    GOLDEN_DIR="$OP_PATH/golden_data"
    if [ ! -d "$GOLDEN_DIR" ] || [ -z "$(ls -A "$GOLDEN_DIR" 2>/dev/null)" ]; then
        python3 "$SCRIPT_DIR/gen_golden.py" \
            --op-path "$OP_PATH" \
            --config "$CONFIG_PATH" \
            --output-dir "$GOLDEN_DIR"
    fi
    bash "$SCRIPT_DIR/test_correctness.sh" \
        "$OP_PATH" "$CONFIG_PATH" "$CORRECTNESS_SMOKE" "smoke"
fi
LEVELS_RUN="smoke"

SMOKE_PASS=$(python3 -c "
import json
with open('$CORRECTNESS_SMOKE') as f: r = json.load(f)
print(r.get('correctness_total', 0.0))
" 2>/dev/null || echo "0.0")

if [ "$(python3 -c "print(1 if float('$SMOKE_PASS') < 1.0 else 0)")" = "1" ]; then
    echo "Smoke 正确性失败 ($SMOKE_PASS)，提前退出"
    python3 "$SCRIPT_DIR/compute_score.py" \
        --version "$VERSION" \
        --correctness-result "$CORRECTNESS_SMOKE" \
        --metric-type "$METRIC_TYPE" \
        --test-levels "$LEVELS_RUN" \
        --output "$SCORE_JSON"
    echo "评分结果: $SCORE_JSON"
    exit 0
fi
echo "Smoke 正确性通过"

# ============ Step 5: Representative 正确性 ============
echo ""
echo ">>> Step 5: Representative 正确性测试"
if [ "$USE_PYTORCH" = true ] && [ -f "$REFERENCE_PY" ]; then
    bash "$SCRIPT_DIR/test_correctness.sh" \
        "$OP_PATH" "$CONFIG_PATH" "$CORRECTNESS_REP" "representative" "$REFERENCE_PY"
else
    bash "$SCRIPT_DIR/test_correctness.sh" \
        "$OP_PATH" "$CONFIG_PATH" "$CORRECTNESS_REP" "representative"
fi
LEVELS_RUN="smoke,representative"

REP_PASS=$(python3 -c "
import json
with open('$CORRECTNESS_REP') as f: r = json.load(f)
print(r.get('correctness_total', 0.0))
" 2>/dev/null || echo "0.0")

if [ "$(python3 -c "print(1 if float('$REP_PASS') < 1.0 else 0)")" = "1" ]; then
    echo "Representative 正确性失败 ($REP_PASS)，提前退出"
    python3 -c "
import json
with open('$CORRECTNESS_SMOKE') as f: s = json.load(f)
with open('$CORRECTNESS_REP') as f: r = json.load(f)
merged = {
    'correctness_total': (s['passed'] + r['passed']) / (s['total'] + r['total']) if (s['total'] + r['total']) > 0 else 0.0,
    'passed': s['passed'] + r['passed'],
    'total': s['total'] + r['total'],
    'configs': s.get('configs', []) + r.get('configs', [])
}
with open('$CORRECTNESS_ALL', 'w') as f: json.dump(merged, f, indent=2)
"
    python3 "$SCRIPT_DIR/compute_score.py" \
        --version "$VERSION" \
        --correctness-result "$CORRECTNESS_ALL" \
        --metric-type "$METRIC_TYPE" \
        --test-levels "$LEVELS_RUN" \
        --output "$SCORE_JSON"
    echo "评分结果: $SCORE_JSON"
    exit 0
fi
echo "Representative 正确性通过"

# ============ Step 6: 合并正确性结果 ============
python3 -c "
import json
with open('$CORRECTNESS_SMOKE') as f: s = json.load(f)
with open('$CORRECTNESS_REP') as f: r = json.load(f)
merged = {
    'correctness_total': 1.0,
    'passed': s['passed'] + r['passed'],
    'total': s['total'] + r['total'],
    'configs': s.get('configs', []) + r.get('configs', [])
}
with open('$CORRECTNESS_ALL', 'w') as f: json.dump(merged, f, indent=2)
"

# ============ Step 7: Representative 性能 ============
echo ""
echo ">>> Step 7: Representative 性能测试"
if [ "$USE_PYTORCH" = true ] && [ -f "$REFERENCE_PY" ]; then
    bash "$SCRIPT_DIR/test_performance.sh" \
        "$OP_PATH" "$CONFIG_PATH" "$PERFORMANCE_REP" "$METRIC_TYPE" "$REFERENCE_PY"
else
    bash "$SCRIPT_DIR/test_performance.sh" \
        "$OP_PATH" "$CONFIG_PATH" "$PERFORMANCE_REP" "$METRIC_TYPE"
fi

# 检查是否满足提交门槛
SHOULD_RUN_STRESS=$(python3 -c "
import json
with open('$PERFORMANCE_REP') as f: perf = json.load(f)
new_total = perf.get('performance_total', 0.0)
best = float('$BEST_SCORE')
min_ratio = float('$MIN_IMPROVEMENT')
metric = '$METRIC_TYPE'

if best <= 0 or new_total <= 0:
    print('no')
elif metric == 'latency_us':
    improvement = best / new_total - 1
    print('yes' if improvement >= min_ratio else 'no')
else:
    improvement = new_total / best - 1
    print('yes' if improvement >= min_ratio else 'no')
" 2>/dev/null || echo "no")

# ============ Step 8: Stress（可选）============
if [ "$SHOULD_RUN_STRESS" = "yes" ]; then
    echo ""
    echo ">>> Step 8: Stress 正确性 + 性能测试（满足提交门槛）"
    LEVELS_RUN="smoke,representative,stress"

    if [ "$USE_PYTORCH" = true ] && [ -f "$REFERENCE_PY" ]; then
        bash "$SCRIPT_DIR/test_correctness.sh" \
            "$OP_PATH" "$CONFIG_PATH" "$CORRECTNESS_STRESS" "stress" "$REFERENCE_PY"
    else
        bash "$SCRIPT_DIR/test_correctness.sh" \
            "$OP_PATH" "$CONFIG_PATH" "$CORRECTNESS_STRESS" "stress"
    fi

    STRESS_PASS=$(python3 -c "
import json
with open('$CORRECTNESS_STRESS') as f: r = json.load(f)
print(r.get('correctness_total', 0.0))
" 2>/dev/null || echo "0.0")

    if [ "$(python3 -c "print(1 if float('$STRESS_PASS') < 1.0 else 0)")" = "1" ]; then
        echo "Stress 正确性失败"
        python3 -c "
import json
with open('$CORRECTNESS_ALL') as f: prev = json.load(f)
with open('$CORRECTNESS_STRESS') as f: st = json.load(f)
prev['configs'].extend(st.get('configs', []))
prev['total'] += st['total']
prev['passed'] += st['passed']
prev['correctness_total'] = prev['passed'] / prev['total'] if prev['total'] > 0 else 0.0
with open('$CORRECTNESS_ALL', 'w') as f: json.dump(prev, f, indent=2)
"
    else
        python3 -c "
import json
with open('$CORRECTNESS_ALL') as f: prev = json.load(f)
with open('$CORRECTNESS_STRESS') as f: st = json.load(f)
prev['configs'].extend(st.get('configs', []))
prev['total'] += st['total']
prev['passed'] += st['passed']
prev['correctness_total'] = 1.0
with open('$CORRECTNESS_ALL', 'w') as f: json.dump(prev, f, indent=2)
"
        if [ "$USE_PYTORCH" = true ] && [ -f "$REFERENCE_PY" ]; then
            bash "$SCRIPT_DIR/test_performance.sh" \
                "$OP_PATH" "$CONFIG_PATH" "$PERFORMANCE_STRESS" "$METRIC_TYPE" "$REFERENCE_PY"
        else
            bash "$SCRIPT_DIR/test_performance.sh" \
                "$OP_PATH" "$CONFIG_PATH" "$PERFORMANCE_STRESS" "$METRIC_TYPE"
        fi
    fi

    # 合并性能结果
    python3 -c "
import json, os
rep_path = '$PERFORMANCE_REP'
stress_path = '$PERFORMANCE_STRESS'
with open(rep_path) as f: rep = json.load(f)
merged = dict(rep)
if os.path.exists(stress_path):
    with open(stress_path) as f: st = json.load(f)
    merged['configs'].extend(st.get('configs', []))
with open('$PERFORMANCE_ALL', 'w') as f: json.dump(merged, f, indent=2)
"
else
    echo ""
    echo ">>> 跳过 Stress 测试（未达到提交门槛或 v0）"
    cp "$PERFORMANCE_REP" "$PERFORMANCE_ALL"
fi

# ============ Step 9: 聚合评分 ============
echo ""
echo ">>> Step 9: 聚合评分"
python3 "$SCRIPT_DIR/compute_score.py" \
    --version "$VERSION" \
    --correctness-result "$CORRECTNESS_ALL" \
    --performance-result "$PERFORMANCE_ALL" \
    --metric-type "$METRIC_TYPE" \
    --best-score "$BEST_SCORE" \
    --test-levels "$LEVELS_RUN" \
    --output "$SCORE_JSON"

echo ""
echo "========================================"
echo "评分完成: $SCORE_JSON"
cat "$SCORE_JSON" | python3 -m json.tool 2>/dev/null || cat "$SCORE_JSON"
echo "========================================"
