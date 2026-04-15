# EVO × MultiKernelBench 单轮编译评测

用 EVO 的 seed 知识库（`evo/memory/bank.jsonl` 24 条 = 14 API 模板 + 10 最佳实践）作为 Claude 的 in-context 辅助，对 MultiKernelBench 300 个算子做 **单轮 Pass@1 编译成功率** 评测。

## 架构

```
MultiKernelBench/
├── prompt_generators/ascendc_evo_shot.py    ← 新增：EVO seed 注入策略
│   └── @register_prompt("ascendc", "evo_shot")
└── compile_only_eval.py                      ← 新增：仅编译批量评测
                                                （复用 AscendBackend.compile）

AscendC-Kernel-Agent/evo/benchmark/
├── run.sh          ← 端到端编排（generate → compile → report）
├── aggregate.py    ← 聚合 results.json → Markdown 报告
└── report.md       ← 最终产物
```

## 关键设计

- **检索**：`evo/docs/retrieval-algorithm.md` 描述的 dense tag-overlap → top-N 过滤。单轮 Pass@1 无迭代 → 无 Q-value、无 memory 更新，纯 deterministic。
- **默认 N=5**（3 条 api_template + 2 条 best_practice），prompt 13–17 KB。
- **API 模板 lazy fetch**：按 `meta.target_path` 实时读 `Knowledge-base/coding-skills/docs/sections/*.md` 对应段落，不预填 bank content。多条命中相同文件时按 section 位置 dedup。
- **仅编译**：调 `backends/ascendc_backend.py::AscendBackend.compile()`，跳过 correctness + performance；失败归入 `msopgen_fail / python_exec_fail / cmake_build_fail / compile_error / segfault / compile_timeout / no_generation / no_code_block`。
- **子进程隔离**：`compile_only_eval.py` 每个 op 起独立 Python 子进程，segfault / 死循环只影响当前 op，不中断 batch。
- **Checkpoint**：每 25 op 保存一次 `compile_only_results.json`；中断可续跑。

## 运行

```bash
# 后台跑完整 300 算子（2-4 小时）
cd /data/w00936672/AscendC-Kernel-Agent
nohup bash evo/benchmark/run.sh > /tmp/evo_bench.log 2>&1 &
tail -f /tmp/evo_bench.log

# 只跑 generate 或只跑 compile 或只生成 report
bash evo/benchmark/run.sh claude-opus-4-6 generate
bash evo/benchmark/run.sh claude-opus-4-6 compile
bash evo/benchmark/run.sh claude-opus-4-6 aggregate
```

Generate 阶段已存在的 .txt 会被跳过；compile 阶段已跑过的 op 会被跳过——两者都支持断点续跑。

## 产物

- `/data/w00936672/MultiKernelBench/output/ascendc/evo_shot/0.0-1.0/claude-opus-4-6/run0/{op}.txt` — 300 个生成结果
- `/data/w00936672/MultiKernelBench/output/ascendc/evo_shot/0.0-1.0/claude-opus-4-6/run0/compile_only_results.json` — 300 条 `{compiled, category, error, compile_info_preview}`
- `evo/benchmark/report.md` — 按 15 类的 compile rate 表 + 全局失败模式分布 + 失败样本摘要

## 依赖

- NPU 环境：16× Ascend910，CANN 8.5.0（已验证）
- Python: torch_npu 2.6.0.post6
- Claude CLI：`/usr/bin/claude` in path
- EVO seed：`evo/memory/bank.jsonl` 已 bootstrap（24 条）+ `Knowledge-base/coding-skills/docs/sections/*.md` 存在
