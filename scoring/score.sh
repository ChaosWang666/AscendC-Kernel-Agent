#!/bin/bash
# score.sh — 分级评分总编排
#
# 自定义算子工程评分流程:
#   0. env_preflight — 环境预检（python/torch_npu/setuptools/CANN 基础就绪）
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
#
# 退出码契约（供 Architect / Supervisor / CI 消费）:
#   0 — 完整 pipeline 成功（v{N}.json 已聚合，correctness_total == 1.0）
#   1 — environment 预检失败 (failure_type=environment) — 外部修复需要
#   2 — compile 阶段失败     (failure_type=compile)
#   3 — deploy 阶段失败      (failure_type=deploy)
#   4 — pybind 阶段失败      (failure_type=pybind)
#   5 — correctness 阶段失败 (failure_type=correctness)
#   6 — performance 阶段失败 (failure_type=performance, 未实现：当前仅记录不退出)
# 所有失败情况都会写 v{N}.json 供后续分析；Architect 可同时依赖退出码和 failure_type。
#
# 副产物：
#   - evolution/logs/step_{N}/{compile,deploy,pybind,preflight}.log — 按阶段落地
#   - evolution/scores/v{N}.json.phase_timings — 每阶段 wall-clock（秒）

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
# VERSION 是"本次评分要写到 v{N}.json 的 N"。语义：
#   - state.json.current_version = -1 (seed 阶段) → 写 v0.json
#   - state.json.current_version = N (已有 N+1 个 accepted 版本) → 写 v{N+1}.json
# 支持两个字段名：canonical 'current_version' (见 Architect AGENT.md bootstrap
# schema) 和 legacy 'current_step'（向后兼容）。
VERSION=$(python3 -c "
import json, os
state_path = os.path.join('$PROJECT_ROOT', 'evolution', 'state.json')
if os.path.exists(state_path):
    with open(state_path) as f: s = json.load(f)
    cv = s.get('current_version', s.get('current_step', -1))
    if cv is None or cv < 0:
        print(0)  # seed phase writes v0.json
    else:
        print(cv + 1)  # next attempt writes v{current_version+1}.json
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

# 持久化日志目录（按 version 分组，不随 trap 清理消失）
LOG_DIR="$PROJECT_ROOT/evolution/logs/step_${VERSION}"
mkdir -p "$LOG_DIR"

# 临时 JSON 中间结果（短生命周期，不需要留）
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

PREFLIGHT_LOG="$LOG_DIR/preflight.log"
COMPILE_LOG="$LOG_DIR/compile.log"
DEPLOY_LOG="$LOG_DIR/deploy.log"
PYBIND_LOG="$LOG_DIR/pybind.log"
CORRECTNESS_LOG="$LOG_DIR/correctness.log"
PERFORMANCE_LOG="$LOG_DIR/performance.log"
CORRECTNESS_SEED="$TMPDIR/correctness_seed.json"
CORRECTNESS_SMOKE="$TMPDIR/correctness_smoke.json"
CORRECTNESS_REP="$TMPDIR/correctness_rep.json"
CORRECTNESS_STRESS="$TMPDIR/correctness_stress.json"
CORRECTNESS_ALL="$TMPDIR/correctness_all.json"
PERFORMANCE_REP="$TMPDIR/performance_rep.json"
PERFORMANCE_STRESS="$TMPDIR/performance_stress.json"
PERFORMANCE_ALL="$TMPDIR/performance_all.json"
PHASE_TIMINGS_FILE="$TMPDIR/phase_timings.json"

LEVELS_RUN=""
DEPLOY_DIR="$PROJECT_ROOT/workspace/deploy/opp"
CPP_EXT_DIR="$PROJECT_ROOT/workspace/runs/$OP_NAME/test/CppExtension"
REFERENCE_PY="$PROJECT_ROOT/workspace/runs/$OP_NAME/test/reference.py"

# ==== Phase timing helpers ====
PHASE_START_TS=0
declare -A PHASE_TIMINGS_MAP
phase_begin() {
    PHASE_START_TS=$(date +%s%3N)
}
phase_end() {
    local phase="$1"
    local end_ts
    end_ts=$(date +%s%3N)
    local duration_ms=$((end_ts - PHASE_START_TS))
    local duration_sec
    duration_sec=$(python3 -c "print(round($duration_ms/1000.0, 3))")
    PHASE_TIMINGS_MAP["$phase"]=$duration_sec
    echo "  [timing] $phase: ${duration_sec}s"
}
dump_phase_timings() {
    python3 -c "
import json, sys
data = {}
$(for k in "${!PHASE_TIMINGS_MAP[@]}"; do echo "data['$k'] = ${PHASE_TIMINGS_MAP[$k]}"; done)
with open('$PHASE_TIMINGS_FILE', 'w') as f:
    json.dump(data, f)
"
}

echo "========================================"
echo "分级评分 (v${VERSION})"
echo "  算子: $OP_PATH"
echo "  配置: $CONFIG_PATH"
echo "  指标: $METRIC_TYPE"
echo "  最佳: $BEST_SCORE"
echo "  模式: 自定义算子工程"
echo "  日志目录: $LOG_DIR"
echo "========================================"

# ============ Step 0: 环境预检 ============
echo ""
echo ">>> Step 0: 环境预检（env preflight）"
phase_begin
# 检查 Python 打包工具链（setuptools / _distutils_hack / pip）
# 注意：env_setup.sh 上方已经 source 过，所以 LD_LIBRARY_PATH 等应当就绪
python3 -c "
import sys
errors = []
try:
    import torch
except Exception as e:
    errors.append(('torch', str(e)))
try:
    import torch_npu
    if not torch_npu.npu.is_available():
        errors.append(('torch_npu', 'NPU not available'))
except Exception as e:
    errors.append(('torch_npu', str(e)))
try:
    from setuptools import setup, find_packages
    import _distutils_hack
    import pip
except Exception as e:
    errors.append(('packaging', str(e)))
import os
if not os.environ.get('ASCEND_HOME_PATH'):
    errors.append(('cann', 'ASCEND_HOME_PATH not set'))

if errors:
    for name, msg in errors:
        print(f'PREFLIGHT FAIL [{name}]: {msg}', file=sys.stderr)
    sys.exit(1)
print('preflight OK')
" > "$PREFLIGHT_LOG" 2>&1
PREFLIGHT_RC=$?
phase_end "preflight"
if [ $PREFLIGHT_RC -ne 0 ]; then
    echo "环境预检失败"
    cat "$PREFLIGHT_LOG" | tail -20
    dump_phase_timings
    python3 "$SCRIPT_DIR/compute_score.py" \
        --version "$VERSION" \
        --failure-stage environment \
        --compile-error "$PREFLIGHT_LOG" \
        --phase-timings "$PHASE_TIMINGS_FILE" \
        --metric-type "$METRIC_TYPE" \
        --output "$SCORE_JSON"
    echo "评分结果: $SCORE_JSON"
    exit 1  # environment stage failure
fi
echo "环境预检通过"

# ============ Step 1: 构建自定义算子工程 ============
echo ""
echo ">>> Step 1: 构建自定义算子工程"
phase_begin
if ! bash "$SCRIPT_DIR/compile.sh" "$OP_PATH" > "$COMPILE_LOG" 2>&1; then
    phase_end "compile"
    echo "构建失败"
    cat "$COMPILE_LOG" | tail -20
    dump_phase_timings
    python3 "$SCRIPT_DIR/compute_score.py" \
        --version "$VERSION" \
        --failure-stage compile \
        --compile-error "$COMPILE_LOG" \
        --phase-timings "$PHASE_TIMINGS_FILE" \
        --metric-type "$METRIC_TYPE" \
        --output "$SCORE_JSON"
    echo "评分结果: $SCORE_JSON"
    exit 2  # compile stage failure
fi
phase_end "compile"
echo "构建成功"

# ============ Step 2: 部署算子包 ============
echo ""
echo ">>> Step 2: 部署算子包"
phase_begin
if ! bash "$SCRIPT_DIR/deploy.sh" "$OP_PATH" "$DEPLOY_DIR" > "$DEPLOY_LOG" 2>&1; then
    phase_end "deploy"
    echo "部署失败"
    cat "$DEPLOY_LOG" | tail -20
    dump_phase_timings
    python3 "$SCRIPT_DIR/compute_score.py" \
        --version "$VERSION" \
        --failure-stage deploy \
        --compile-error "$DEPLOY_LOG" \
        --phase-timings "$PHASE_TIMINGS_FILE" \
        --metric-type "$METRIC_TYPE" \
        --output "$SCORE_JSON"
    echo "评分结果: $SCORE_JSON"
    exit 3  # deploy stage failure
fi
phase_end "deploy"

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
phase_begin
if [ -d "$CPP_EXT_DIR" ]; then
    if ! bash "$SCRIPT_DIR/build_pybind.sh" "$CPP_EXT_DIR" "$DEPLOY_DIR" > "$PYBIND_LOG" 2>&1; then
        phase_end "pybind"
        echo "Python 绑定构建失败"
        cat "$PYBIND_LOG" | tail -20
        dump_phase_timings
        python3 "$SCRIPT_DIR/compute_score.py" \
            --version "$VERSION" \
            --failure-stage pybind \
            --compile-error "$PYBIND_LOG" \
            --phase-timings "$PHASE_TIMINGS_FILE" \
            --metric-type "$METRIC_TYPE" \
            --output "$SCORE_JSON"
        echo "评分结果: $SCORE_JSON"
        exit 4  # pybind stage failure
    fi
    phase_end "pybind"
    echo "Python 绑定构建成功"
    USE_PYTORCH=true
else
    phase_end "pybind"
    echo "未找到 CppExtension 目录，使用兼容模式"
    USE_PYTORCH=false
fi

# ============ Step 3.5: Seed 正确性（可选）============
# Seed 是最小尺寸级别（通常 batch=1, seq=2-4），用于 Developer 快速迭代。
# 如果 config 里有 seed 级别，先跑它——只要 seed 过，说明 kernel 逻辑基本
# 成型，值得做更大尺寸的 smoke 测试。如果 seed 不过，提前退出省 10+ 秒。
HAS_SEED_LEVEL=$(python3 -c "
import json
with open('$CONFIG_PATH') as f: cfg = json.load(f)
print('yes' if cfg.get('seed') else 'no')
" 2>/dev/null || echo "no")

if [ "$HAS_SEED_LEVEL" = "yes" ] && [ "$USE_PYTORCH" = true ] && [ -f "$REFERENCE_PY" ]; then
    echo ""
    echo ">>> Step 3.5: Seed 正确性测试（fast path）"
    phase_begin
    bash "$SCRIPT_DIR/test_correctness.sh" \
        "$OP_PATH" "$CONFIG_PATH" "$CORRECTNESS_SEED" "seed" "$REFERENCE_PY" \
        >> "$CORRECTNESS_LOG" 2>&1
    SEED_PASS=$(python3 -c "
import json
with open('$CORRECTNESS_SEED') as f: r = json.load(f)
print(r.get('correctness_total', 0.0))
" 2>/dev/null || echo "0.0")
    if [ "$(python3 -c "print(1 if float('$SEED_PASS') < 1.0 else 0)")" = "1" ]; then
        phase_end "correctness_seed"
        echo "Seed 正确性失败 ($SEED_PASS)，提前退出（跳过 smoke/representative/stress）"
        dump_phase_timings
        python3 "$SCRIPT_DIR/compute_score.py" \
            --version "$VERSION" \
            --failure-stage correctness \
            --correctness-result "$CORRECTNESS_SEED" \
            --phase-timings "$PHASE_TIMINGS_FILE" \
            --metric-type "$METRIC_TYPE" \
            --test-levels "seed" \
            --output "$SCORE_JSON"
        echo "评分结果: $SCORE_JSON"
        exit 5  # correctness stage failure
    fi
    phase_end "correctness_seed"
    echo "Seed 正确性通过（kernel 基本成型）"
fi

# ============ Step 4: Smoke 正确性 ============
echo ""
echo ">>> Step 4: Smoke 正确性测试"
phase_begin
if [ "$USE_PYTORCH" = true ] && [ -f "$REFERENCE_PY" ]; then
    bash "$SCRIPT_DIR/test_correctness.sh" \
        "$OP_PATH" "$CONFIG_PATH" "$CORRECTNESS_SMOKE" "smoke" "$REFERENCE_PY" \
        >> "$CORRECTNESS_LOG" 2>&1
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
        "$OP_PATH" "$CONFIG_PATH" "$CORRECTNESS_SMOKE" "smoke" \
        >> "$CORRECTNESS_LOG" 2>&1
fi
LEVELS_RUN="smoke"

SMOKE_PASS=$(python3 -c "
import json
with open('$CORRECTNESS_SMOKE') as f: r = json.load(f)
print(r.get('correctness_total', 0.0))
" 2>/dev/null || echo "0.0")

if [ "$(python3 -c "print(1 if float('$SMOKE_PASS') < 1.0 else 0)")" = "1" ]; then
    phase_end "correctness_smoke"
    echo "Smoke 正确性失败 ($SMOKE_PASS)，提前退出"
    dump_phase_timings
    python3 "$SCRIPT_DIR/compute_score.py" \
        --version "$VERSION" \
        --failure-stage correctness \
        --correctness-result "$CORRECTNESS_SMOKE" \
        --phase-timings "$PHASE_TIMINGS_FILE" \
        --metric-type "$METRIC_TYPE" \
        --test-levels "$LEVELS_RUN" \
        --output "$SCORE_JSON"
    echo "评分结果: $SCORE_JSON"
    exit 5  # correctness stage failure
fi
phase_end "correctness_smoke"
echo "Smoke 正确性通过"

# ============ Step 5: Representative 正确性 ============
echo ""
echo ">>> Step 5: Representative 正确性测试"
phase_begin
if [ "$USE_PYTORCH" = true ] && [ -f "$REFERENCE_PY" ]; then
    bash "$SCRIPT_DIR/test_correctness.sh" \
        "$OP_PATH" "$CONFIG_PATH" "$CORRECTNESS_REP" "representative" "$REFERENCE_PY" \
        >> "$CORRECTNESS_LOG" 2>&1
else
    bash "$SCRIPT_DIR/test_correctness.sh" \
        "$OP_PATH" "$CONFIG_PATH" "$CORRECTNESS_REP" "representative" \
        >> "$CORRECTNESS_LOG" 2>&1
fi
LEVELS_RUN="smoke,representative"

REP_PASS=$(python3 -c "
import json
with open('$CORRECTNESS_REP') as f: r = json.load(f)
print(r.get('correctness_total', 0.0))
" 2>/dev/null || echo "0.0")

if [ "$(python3 -c "print(1 if float('$REP_PASS') < 1.0 else 0)")" = "1" ]; then
    phase_end "correctness_representative"
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
    dump_phase_timings
    python3 "$SCRIPT_DIR/compute_score.py" \
        --version "$VERSION" \
        --failure-stage correctness \
        --correctness-result "$CORRECTNESS_ALL" \
        --phase-timings "$PHASE_TIMINGS_FILE" \
        --metric-type "$METRIC_TYPE" \
        --test-levels "$LEVELS_RUN" \
        --output "$SCORE_JSON"
    echo "评分结果: $SCORE_JSON"
    exit 5  # correctness stage failure
fi
phase_end "correctness_representative"
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
phase_begin
if [ "$USE_PYTORCH" = true ] && [ -f "$REFERENCE_PY" ]; then
    bash "$SCRIPT_DIR/test_performance.sh" \
        "$OP_PATH" "$CONFIG_PATH" "$PERFORMANCE_REP" "$METRIC_TYPE" "$REFERENCE_PY" \
        >> "$PERFORMANCE_LOG" 2>&1
else
    bash "$SCRIPT_DIR/test_performance.sh" \
        "$OP_PATH" "$CONFIG_PATH" "$PERFORMANCE_REP" "$METRIC_TYPE" \
        >> "$PERFORMANCE_LOG" 2>&1
fi
phase_end "performance_representative"

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
    phase_begin
    if [ "$USE_PYTORCH" = true ] && [ -f "$REFERENCE_PY" ]; then
        bash "$SCRIPT_DIR/test_correctness.sh" \
            "$OP_PATH" "$CONFIG_PATH" "$CORRECTNESS_STRESS" "stress" "$REFERENCE_PY" \
            >> "$CORRECTNESS_LOG" 2>&1
    else
        bash "$SCRIPT_DIR/test_correctness.sh" \
            "$OP_PATH" "$CONFIG_PATH" "$CORRECTNESS_STRESS" "stress" \
            >> "$CORRECTNESS_LOG" 2>&1
    fi

    STRESS_PASS=$(python3 -c "
import json
with open('$CORRECTNESS_STRESS') as f: r = json.load(f)
print(r.get('correctness_total', 0.0))
" 2>/dev/null || echo "0.0")

    if [ "$(python3 -c "print(1 if float('$STRESS_PASS') < 1.0 else 0)")" = "1" ]; then
        phase_end "correctness_stress"
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
        phase_end "correctness_stress"
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
        phase_begin
        if [ "$USE_PYTORCH" = true ] && [ -f "$REFERENCE_PY" ]; then
            bash "$SCRIPT_DIR/test_performance.sh" \
                "$OP_PATH" "$CONFIG_PATH" "$PERFORMANCE_STRESS" "$METRIC_TYPE" "$REFERENCE_PY" \
                >> "$PERFORMANCE_LOG" 2>&1
        else
            bash "$SCRIPT_DIR/test_performance.sh" \
                "$OP_PATH" "$CONFIG_PATH" "$PERFORMANCE_STRESS" "$METRIC_TYPE" \
                >> "$PERFORMANCE_LOG" 2>&1
        fi
        phase_end "performance_stress"
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
dump_phase_timings
python3 "$SCRIPT_DIR/compute_score.py" \
    --version "$VERSION" \
    --correctness-result "$CORRECTNESS_ALL" \
    --performance-result "$PERFORMANCE_ALL" \
    --phase-timings "$PHASE_TIMINGS_FILE" \
    --metric-type "$METRIC_TYPE" \
    --best-score "$BEST_SCORE" \
    --test-levels "$LEVELS_RUN" \
    --output "$SCORE_JSON"

echo ""
echo "========================================"
echo "评分完成: $SCORE_JSON"
echo "日志目录: $LOG_DIR"
cat "$SCORE_JSON" | python3 -m json.tool 2>/dev/null || cat "$SCORE_JSON"
echo "========================================"
