#!/usr/bin/env python3
"""聚合 compile_only_results.json → evo/benchmark/report.md

按 15 个 category 分组统计 compile rate；附每类失败模式 top-3 和典型错误摘要。
"""
import argparse
import json
import os
from collections import Counter, defaultdict
from datetime import datetime


CATEGORIES_ORDER = [
    'activation', 'arch', 'attention', 'broadcast', 'convolution',
    'fuse', 'index', 'loss', 'math', 'matmul',
    'normalization', 'optimizer', 'pooling', 'reduce', 'resize',
]


def load_results(path):
    with open(path) as f:
        return json.load(f)


def aggregate(results):
    by_cat = defaultdict(list)
    for op, entry in results.items():
        by_cat[entry['category']].append((op, entry))
    return by_cat


def per_category_stats(by_cat):
    rows = []
    for cat in CATEGORIES_ORDER:
        items = by_cat.get(cat, [])
        total = len(items)
        compiled = sum(1 for _, e in items if e['compiled'])
        error_counts = Counter(e.get('error') for _, e in items if not e['compiled'])
        top_err = ', '.join(f"{k}×{v}" for k, v in error_counts.most_common(3) if k)
        rate = compiled / total * 100 if total > 0 else 0.0
        rows.append({
            'category': cat,
            'total': total,
            'compiled': compiled,
            'rate_pct': rate,
            'top_errors': top_err or '-',
        })
    return rows


def overall_stats(results):
    total = len(results)
    compiled = sum(1 for e in results.values() if e['compiled'])
    return {
        'total': total,
        'compiled': compiled,
        'rate_pct': compiled / total * 100 if total > 0 else 0.0,
    }


def sample_failures(by_cat, n_per_cat=2):
    out = {}
    for cat, items in by_cat.items():
        fails = [(op, e) for op, e in items
                 if not e['compiled'] and e.get('compile_info_preview')]
        out[cat] = fails[:n_per_cat]
    return out


def generate_report(results_path, output_path, run_meta=None):
    results = load_results(results_path)
    by_cat = aggregate(results)
    rows = per_category_stats(by_cat)
    overall = overall_stats(results)

    meta = run_meta or {}
    lines = []
    lines.append("# MultiKernelBench × EVO 单轮编译准确率评测")
    lines.append("")
    lines.append(f"- **日期**：{meta.get('date', datetime.now().strftime('%Y-%m-%d %H:%M'))}")
    lines.append(f"- **模型**：{meta.get('model', 'claude-opus-4-6')}")
    lines.append(f"- **策略**：`ascendc_evo_shot`（EVO seed 检索 + add_shot few-shot 模板）")
    lines.append(f"- **语言/后端**：AscendC / Ascend910B2")
    lines.append(f"- **轮数**：1（单轮，无 refinement）")
    lines.append(f"- **评测维度**：仅编译成功率（不跑 correctness / performance）")
    lines.append(f"- **结果文件**：`{os.path.relpath(results_path, os.getcwd())}`")
    lines.append("")
    lines.append("## 总体")
    lines.append("")
    lines.append(f"| 总算子数 | 编译成功 | 成功率 |")
    lines.append(f"|---------|---------|-------|")
    lines.append(f"| {overall['total']} | {overall['compiled']} | **{overall['rate_pct']:.1f}%** |")
    lines.append("")
    lines.append("## 按类别编译准确率")
    lines.append("")
    lines.append("| Category | Total | Compiled | Rate | Top Failure Modes |")
    lines.append("|----------|-------|----------|------|-------------------|")
    for row in rows:
        lines.append(f"| {row['category']} | {row['total']} | {row['compiled']} | "
                     f"{row['rate_pct']:.1f}% | {row['top_errors']} |")
    lines.append("")

    # 失败模式整体分布
    global_errors = Counter()
    for entry in results.values():
        if not entry['compiled']:
            global_errors[entry.get('error') or 'unknown'] += 1
    if global_errors:
        lines.append("## 全局失败模式分布")
        lines.append("")
        lines.append("| 失败类型 | 数量 | 说明 |")
        lines.append("|---------|-----|------|")
        error_desc = {
            'no_generation': '生成阶段 Claude CLI 超时或无输出',
            'no_code_block': '模型响应未含合法 code block',
            'msopgen_fail': 'msopgen 项目创建失败（JSON 定义错 / 权限 / 芯片配置）',
            'python_exec_fail': '生成的 Python string 变量 exec 失败（语法错误 / 未定义 src 变量）',
            'cmake_build_fail': 'CMake / Ninja 构建失败',
            'compile_error': 'AscendC 编译错误',
            'compile_fail': '其它编译失败',
            'segfault': '编译过程段错误',
            'compile_timeout': f'单 op 超过编译超时',
        }
        for err, count in global_errors.most_common():
            lines.append(f"| `{err}` | {count} | {error_desc.get(err, '-')} |")
        lines.append("")

    # 失败样本
    samples = sample_failures(by_cat, n_per_cat=1)
    if samples:
        lines.append("## 失败样本（每类抽 1 个）")
        lines.append("")
        for cat in CATEGORIES_ORDER:
            if cat not in samples or not samples[cat]:
                continue
            op, entry = samples[cat][0]
            lines.append(f"### {cat} — `{op}`")
            lines.append("")
            lines.append(f"- 错误类型：`{entry.get('error', '?')}`")
            preview = entry.get('compile_info_preview', '').strip()
            if preview:
                lines.append("- 错误摘要：")
                lines.append("```")
                lines.append(preview[:400])
                lines.append("```")
            lines.append("")

    lines.append("## 原始数据")
    lines.append("")
    lines.append(f"- 详细结果：`{os.path.relpath(results_path, os.getcwd())}`")
    lines.append(f"- 生成输出目录：`{meta.get('gen_dir', '?')}`")

    with open(output_path, 'w') as f:
        f.write('\n'.join(lines))
    print(f"✓ Report written: {output_path}")
    print(f"  Overall: {overall['compiled']}/{overall['total']} = {overall['rate_pct']:.1f}%")
    return rows, overall


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--results', required=True,
                    help='compile_only_results.json 路径')
    ap.add_argument('--output', required=True,
                    help='输出 report.md 路径')
    ap.add_argument('--model', default='claude-opus-4-6')
    ap.add_argument('--gen-dir', default='',
                    help='生成目录，用于报告引用')
    args = ap.parse_args()

    meta = {'model': args.model, 'gen_dir': args.gen_dir}
    generate_report(args.results, args.output, run_meta=meta)


if __name__ == '__main__':
    main()
