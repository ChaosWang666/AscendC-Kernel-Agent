#!/bin/bash
# score.sh — 分级评分总编排
#
# 流程:
#   1. compile.sh
#   2. gen_golden.py (所有级别)
#   3. smoke correctness → 失败则提前退出
#   4. representative correctness → 失败则提前退出
#   5. 若 correctness_total < 1.0 → 结束
#   6. representative performance → 计算 improvement
#   7. 若满足提交门槛 → stress correctness + stress performance
#   8. compute_score.py → 聚合为最终 JSON
#
# 用法: bash scoring/score.sh <op_path> <config_path>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

OP_PATH="${1:?用法: score.sh <op_path> <config_path>}"
CONFIG_PATH="${2:?}"

# 读取配置
METRIC_TYPE=$(python3 -c "
import json
with open('$CONFIG_PATH') as f: cfg = json.load(f)
print(cfg.get('metric_type', 'tflops'))
" 2>/dev/null || echo "tflops")

MIN_IMPROVEMENT=$(python3 -c "
import json
with open('$CONFIG_PATH') as f: cfg = json.load(f)
print(cfg.get('min_improvement_ratio', 0.02))
" 2>/dev/null || echo "0.02")

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

GOLDEN_DIR="$OP_PATH/golden_data"
COMPILE_LOG="$TMPDIR/compile.log"
CORRECTNESS_SMOKE="$TMPDIR/correctness_smoke.json"
CORRECTNESS_REP="$TMPDIR/correctness_rep.json"
CORRECTNESS_STRESS="$TMPDIR/correctness_stress.json"
CORRECTNESS_ALL="$TMPDIR/correctness_all.json"
PERFORMANCE_REP="$TMPDIR/performance_rep.json"
PERFORMANCE_STRESS="$TMPDIR/performance_stress.json"
PERFORMANCE_ALL="$TMPDIR/performance_all.json"

LEVELS_RUN=""

echo "========================================"
echo "分级评分 (v${VERSION})"
echo "  算子: $OP_PATH"
echo "  配置: $CONFIG_PATH"
echo "  指标: $METRIC_TYPE"
echo "  最佳: $BEST_SCORE"
echo "========================================"

# ============ Step 1: 编译 ============
echo ""
echo ">>> Step 1: 编译"
if ! bash "$SCRIPT_DIR/compile.sh" "$OP_PATH" > "$COMPILE_LOG" 2>&1; then
    echo "编译失败"
    python3 "$SCRIPT_DIR/compute_score.py" \
        --version "$VERSION" \
        --compile-error "$COMPILE_LOG" \
        --metric-type "$METRIC_TYPE" \
        --output "$SCORE_JSON"
    echo "评分结果: $SCORE_JSON"
    exit 0
fi
echo "编译成功"

# ============ Step 2: 生成 Golden ============
echo ""
echo ">>> Step 2: 生成 Golden 数据"
if [ ! -d "$GOLDEN_DIR" ] || [ -z "$(ls -A "$GOLDEN_DIR" 2>/dev/null)" ]; then
    python3 "$SCRIPT_DIR/gen_golden.py" \
        --op-path "$OP_PATH" \
        --config "$CONFIG_PATH" \
        --output-dir "$GOLDEN_DIR"
fi

# ============ Step 3: Smoke 正确性 ============
echo ""
echo ">>> Step 3: Smoke 正确性测试"
bash "$SCRIPT_DIR/test_correctness.sh" \
    "$OP_PATH" "$CONFIG_PATH" "$GOLDEN_DIR" "$CORRECTNESS_SMOKE" "smoke"
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

# ============ Step 4: Representative 正确性 ============
echo ""
echo ">>> Step 4: Representative 正确性测试"
bash "$SCRIPT_DIR/test_correctness.sh" \
    "$OP_PATH" "$CONFIG_PATH" "$GOLDEN_DIR" "$CORRECTNESS_REP" "representative"
LEVELS_RUN="smoke,representative"

REP_PASS=$(python3 -c "
import json
with open('$CORRECTNESS_REP') as f: r = json.load(f)
print(r.get('correctness_total', 0.0))
" 2>/dev/null || echo "0.0")

if [ "$(python3 -c "print(1 if float('$REP_PASS') < 1.0 else 0)")" = "1" ]; then
    echo "Representative 正确性失败 ($REP_PASS)，提前退出"
    # 合并 smoke + representative 正确性结果
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

# ============ Step 5: 合并正确性结果 ============
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

# ============ Step 6: Representative 性能 ============
echo ""
echo ">>> Step 6: Representative 性能测试"
bash "$SCRIPT_DIR/test_performance.sh" \
    "$OP_PATH" "$CONFIG_PATH" "$PERFORMANCE_REP" "$METRIC_TYPE"

# 检查是否满足提交门槛
SHOULD_RUN_STRESS=$(python3 -c "
import json
with open('$PERFORMANCE_REP') as f: perf = json.load(f)
new_total = perf.get('performance_total', 0.0)
best = float('$BEST_SCORE')
min_ratio = float('$MIN_IMPROVEMENT')
metric = '$METRIC_TYPE'

if best <= 0 or new_total <= 0:
    # v0 或无性能数据: 跳过 stress
    print('no')
elif metric == 'latency_us':
    improvement = best / new_total - 1
    print('yes' if improvement >= min_ratio else 'no')
else:
    improvement = new_total / best - 1
    print('yes' if improvement >= min_ratio else 'no')
" 2>/dev/null || echo "no")

# ============ Step 7: Stress（可选）============
if [ "$SHOULD_RUN_STRESS" = "yes" ]; then
    echo ""
    echo ">>> Step 7: Stress 正确性 + 性能测试（满足提交门槛）"
    LEVELS_RUN="smoke,representative,stress"

    bash "$SCRIPT_DIR/test_correctness.sh" \
        "$OP_PATH" "$CONFIG_PATH" "$GOLDEN_DIR" "$CORRECTNESS_STRESS" "stress"

    STRESS_PASS=$(python3 -c "
import json
with open('$CORRECTNESS_STRESS') as f: r = json.load(f)
print(r.get('correctness_total', 0.0))
" 2>/dev/null || echo "0.0")

    if [ "$(python3 -c "print(1 if float('$STRESS_PASS') < 1.0 else 0)")" = "1" ]; then
        echo "Stress 正确性失败"
        # 更新 correctness_all 包含 stress 失败
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
        # Stress 通过，更新 correctness_all
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

        bash "$SCRIPT_DIR/test_performance.sh" \
            "$OP_PATH" "$CONFIG_PATH" "$PERFORMANCE_STRESS" "$METRIC_TYPE"
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

# ============ Step 8: 聚合评分 ============
echo ""
echo ">>> Step 8: 聚合评分"
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
