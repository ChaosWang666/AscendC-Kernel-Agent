#!/bin/bash
# EVO × MultiKernelBench 端到端单轮编译评测
#
# 阶段：
#   1. 对 dataset.py 的 300 个算子用 ascendc_evo_shot 策略生成 kernel（.txt）
#   2. 调 compile_only_eval.py 批量编译
#   3. 聚合结果 → evo/benchmark/report.md
#
# 中间态：可重入（generate 跳过已存在 .txt，compile 跳过已跑 op）
#
# 用法：
#   bash evo/benchmark/run.sh [MODEL] [PHASE]
#     MODEL   默认 claude-opus-4-6
#     PHASE   默认 all；可选 generate | compile | aggregate
#
# 后台跑：
#   nohup bash evo/benchmark/run.sh > /tmp/evo_bench.log 2>&1 &

set -e

MODEL="${1:-claude-opus-4-6}"
PHASE="${2:-all}"
STRATEGY="evo_shot"
LANGUAGE="ascendc"
TEMP="0.0"
TOPP="1.0"

MKB=/data/w00936672/MultiKernelBench
EVO=/data/w00936672/AscendC-Kernel-Agent/evo
BENCH=$EVO/benchmark

RUN_DIR=$MKB/output/$LANGUAGE/$STRATEGY/$TEMP-$TOPP/$MODEL/run0
RESULTS_JSON=$RUN_DIR/compile_only_results.json
REPORT_MD=$BENCH/report.md

source /usr/local/Ascend/ascend-toolkit/set_env.sh > /dev/null

echo "=========================================="
echo "EVO × MultiKernelBench — single-shot eval"
echo "  Model:     $MODEL"
echo "  Strategy:  $STRATEGY"
echo "  Phase:     $PHASE"
echo "  Run dir:   $RUN_DIR"
echo "  Report:    $REPORT_MD"
echo "=========================================="

# ---------- Phase 1: generate ----------
if [[ "$PHASE" == "all" || "$PHASE" == "generate" ]]; then
  echo ""
  echo ">>> [1/3] Generate 300 ops via Claude Code CLI (strategy=$STRATEGY)"
  cd $MKB
  OPS=$(python3 -c "from dataset import dataset; print(' '.join(dataset.keys()))")
  # Claude CLI: single-shot, no tools
  python3 generate_claude_code.py \
      --strategy $STRATEGY \
      --model-name $MODEL \
      --runs 1 \
      --timeout 300 \
      --ops $OPS
  echo "<<< [1/3] Generation complete"
fi

# ---------- Phase 2: compile-only eval ----------
if [[ "$PHASE" == "all" || "$PHASE" == "compile" ]]; then
  echo ""
  echo ">>> [2/3] Compile-only eval on generated .txt files"
  cd $MKB
  python3 compile_only_eval.py --run-dir $RUN_DIR
  echo "<<< [2/3] Compile-only eval complete → $RESULTS_JSON"
fi

# ---------- Phase 3: aggregate → report ----------
if [[ "$PHASE" == "all" || "$PHASE" == "aggregate" ]]; then
  echo ""
  echo ">>> [3/3] Aggregate → Markdown report"
  python3 $BENCH/aggregate.py \
      --results $RESULTS_JSON \
      --output $REPORT_MD \
      --model $MODEL \
      --gen-dir $RUN_DIR
  echo "<<< [3/3] Report: $REPORT_MD"
fi

echo ""
echo "=========================================="
echo "  Done."
echo "=========================================="
