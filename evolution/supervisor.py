#!/usr/bin/env python3
"""supervisor.py — AscendC Kernel Agent 进化引擎

主循环编排：
  1. 加载/初始化状态
  2. 从 best/ 创建隔离的候选工作区
  3. 启动 Kernel Evolution Agent 会话
  4. 收集结果 → 满足提交准则则晋升为新 best/
  5. 检测停滞 → 生成重定向指令
  6. 循环直到停止条件

用法:
    python3 evolution/supervisor.py [--config evolution/config.yaml]
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import yaml
from datetime import datetime, timezone, timedelta
from pathlib import Path


# ========== 配置 ==========

DEFAULT_CONFIG = {
    "operator_name": "add_custom",
    "target_chip": "Ascend910B",
    "operator_spec_path": "workspace/specs/add_custom.md",
    "runs_dir": "",
    "max_wall_time": "168h",
    "max_versions": 100,
    "max_session_duration": "30m",
    "stall_threshold": 5,
    "max_failed_attempts": 5,
    "max_consecutive_redirects": 3,
    "scoring_config_path": "scoring/configs/default.json",
    "metric_type": "latency_us",
    "min_improvement_ratio": 0.02,
    "warmup_rounds": 10,
    "repeat_rounds": 5,
    "target_performance": None,
    "agent_definition": "agents/kernel-evolution-agent/AGENT.md",
}


def parse_duration(s: str) -> timedelta:
    """解析时间字符串 (如 '168h', '30m', '7d')"""
    s = s.strip()
    if s.endswith("d"):
        return timedelta(days=int(s[:-1]))
    elif s.endswith("h"):
        return timedelta(hours=int(s[:-1]))
    elif s.endswith("m"):
        return timedelta(minutes=int(s[:-1]))
    elif s.endswith("s"):
        return timedelta(seconds=int(s[:-1]))
    else:
        return timedelta(hours=int(s))


def get_runs_dir(config: dict) -> str:
    """获取 runs 目录路径"""
    runs_dir = config.get("runs_dir", "")
    if not runs_dir:
        runs_dir = f"workspace/runs/{config['operator_name']}"
    return runs_dir


# ========== 性能指标辅助 ==========

def is_improvement(new_val: float, best_val: float, metric_type: str,
                   min_ratio: float) -> bool:
    """判断新值是否优于 best（考虑指标方向）"""
    if best_val <= 0 or new_val <= 0:
        return new_val > 0
    if metric_type == "latency_us":
        # 延迟: 越低越好
        improvement = best_val / new_val - 1
    else:
        # 吞吐: 越高越好
        improvement = new_val / best_val - 1
    return improvement >= min_ratio


def is_target_met(best_score: float, target: float, metric_type: str) -> bool:
    """判断是否达到目标性能"""
    if metric_type == "latency_us":
        return best_score > 0 and best_score <= target  # 延迟达标 = 低于目标
    else:
        return best_score >= target


# ========== 状态管理 ==========

class EvolutionState:
    """进化状态，持久化到 evolution/state.json"""

    def __init__(self, state_path: str, config: dict):
        self.state_path = state_path
        self.config = config

        if os.path.exists(state_path):
            with open(state_path) as f:
                data = json.load(f)
        else:
            data = {}

        self.operator_name = data.get("operator_name", config["operator_name"])
        self.target_chip = data.get("target_chip", config["target_chip"])
        self.start_time = data.get("start_time", datetime.now(timezone.utc).isoformat())
        self.current_step = data.get("current_step", 0)
        self.current_version = data.get("current_version", -1)
        self.best_version = data.get("best_version", -1)
        self.best_score = data.get("best_score", 0.0)
        self.best_commit = data.get("best_commit", "")
        self.stall_counter = data.get("stall_counter", 0)
        self.failed_attempts = data.get("failed_attempts", 0)
        self.consecutive_redirects = data.get("consecutive_redirects", 0)
        self.total_attempts = data.get("total_attempts", 0)
        self.last_completed_step = data.get("last_completed_step", -1)
        self.active_attempt_dir = data.get("active_attempt_dir", None)
        self.redirect_count = data.get("redirect_count", 0)
        self.lineage = data.get("lineage", [])

    def save(self):
        """原子保存状态到磁盘（先写临时文件再 rename）"""
        data = {
            "operator_name": self.operator_name,
            "target_chip": self.target_chip,
            "start_time": self.start_time,
            "current_step": self.current_step,
            "current_version": self.current_version,
            "best_version": self.best_version,
            "best_score": self.best_score,
            "best_commit": self.best_commit,
            "stall_counter": self.stall_counter,
            "failed_attempts": self.failed_attempts,
            "consecutive_redirects": self.consecutive_redirects,
            "total_attempts": self.total_attempts,
            "last_completed_step": self.last_completed_step,
            "active_attempt_dir": self.active_attempt_dir,
            "redirect_count": self.redirect_count,
            "lineage": self.lineage,
        }
        os.makedirs(os.path.dirname(self.state_path), exist_ok=True)
        tmp_path = self.state_path + ".tmp"
        with open(tmp_path, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, self.state_path)

    def format_lineage(self) -> str:
        """格式化谱系为文本摘要"""
        if not self.lineage:
            return "(空谱系 — 需要生成种子版本 v0)"

        metric = self.config.get("metric_type", "tflops")
        lines = [f"版本 | 评分 ({metric}) | Git Commit | 描述",
                  "-----|---------------|------------|------"]
        for entry in self.lineage:
            v = entry["version"]
            s = entry["score"]
            c = entry.get("commit", "???")[:7]
            d = entry.get("description", "")
            lines.append(f"v{v}   | {s:<13} | {c}    | {d}")
        return "\n".join(lines)


# ========== 工作区隔离 ==========

def prepare_attempt_dir_from_best(state: EvolutionState, config: dict,
                                   project_root: str) -> str:
    """从 best/ 复制到 attempts/step_{N}/，确保隔离"""
    runs_dir = os.path.join(project_root, get_runs_dir(config))
    best_dir = os.path.join(runs_dir, "best")
    attempt_dir = os.path.join(runs_dir, "attempts", f"step_{state.current_step}")

    if os.path.exists(attempt_dir):
        shutil.rmtree(attempt_dir)

    if os.path.exists(best_dir) and any(
        f for f in os.listdir(best_dir) if f != ".gitkeep"
    ):
        shutil.copytree(best_dir, attempt_dir)
    else:
        os.makedirs(attempt_dir, exist_ok=True)

    return attempt_dir


def promote_attempt_to_best(attempt_dir: str, config: dict,
                             project_root: str):
    """用成功的候选替换 best/"""
    runs_dir = os.path.join(project_root, get_runs_dir(config))
    best_dir = os.path.join(runs_dir, "best")

    if os.path.exists(best_dir):
        shutil.rmtree(best_dir)
    shutil.copytree(attempt_dir, best_dir)


def cleanup_attempt(attempt_dir: str):
    """清理候选目录"""
    if attempt_dir and os.path.exists(attempt_dir):
        shutil.rmtree(attempt_dir, ignore_errors=True)


# ========== Agent 会话 ==========

def read_current_kernel(state: EvolutionState, config: dict,
                        project_root: str) -> str:
    """读取当前最佳内核源码"""
    runs_dir = os.path.join(project_root, get_runs_dir(config))
    kernel_path = os.path.join(runs_dir, "best", f"{state.operator_name}.asc")
    if os.path.exists(kernel_path):
        with open(kernel_path) as f:
            return f.read()
    return "(内核文件不存在 — 需要种子生成)"


def read_current_score(state: EvolutionState, project_root: str) -> dict:
    """读取当前版本的评分数据"""
    if state.current_version < 0:
        return {}
    score_path = os.path.join(
        project_root, "evolution", "scores",
        f"v{state.current_version}.json"
    )
    if os.path.exists(score_path):
        with open(score_path) as f:
            return json.load(f)
    return {}


def build_agent_prompt(state: EvolutionState, project_root: str,
                       config: dict, attempt_dir: str,
                       directive: str = None,
                       use_repair: bool = False) -> str:
    """构建 Agent 会话的 prompt"""
    runs_dir = os.path.join(project_root, get_runs_dir(config))
    best_dir = os.path.join(runs_dir, "best")

    # 读取算子规格
    spec_path = config.get("operator_spec_path", "")
    if spec_path and os.path.exists(os.path.join(project_root, spec_path)):
        with open(os.path.join(project_root, spec_path)) as f:
            operator_spec = f.read()
    else:
        operator_spec = f"算子名称: {state.operator_name}\n目标芯片: {state.target_chip}"

    # 选择 prompt 模板
    if state.current_version < 0:
        template_name = "seed-generation.md"
    elif use_repair:
        template_name = "repair-step.md"
    else:
        template_name = "optimize-step.md"

    template_path = os.path.join(
        project_root, "agents/kernel-evolution-agent/prompts", template_name
    )

    if os.path.exists(template_path):
        with open(template_path) as f:
            template = f.read()
    else:
        template = "请优化算子 {{OP_NAME}}"

    # 变量替换
    current_kernel = read_current_kernel(state, config, project_root)
    current_score = read_current_score(state, project_root)
    lineage_summary = state.format_lineage()
    scoring_config = config.get("scoring_config_path", "scoring/configs/default.json")

    replacements = {
        "{{OPERATOR_SPEC}}": operator_spec,
        "{{TARGET_CHIP}}": state.target_chip,
        "{{OP_NAME}}": state.operator_name,
        "{{CURRENT_VERSION}}": str(state.current_version),
        "{{NEXT_VERSION}}": str(state.current_version + 1),
        "{{CURRENT_SCORE}}": str(state.best_score),
        "{{PROFILING_SUMMARY}}": json.dumps(current_score.get("configs", []), indent=2),
        "{{LINEAGE_SUMMARY}}": lineage_summary,
        "{{DIRECTIVE}}": directive or "(无特殊指令)",
        "{{CONFIG}}": os.path.splitext(os.path.basename(scoring_config))[0],
        "{{TEST_CONFIGS}}": "",
        "{{LAST_CORRECT_VERSION}}": str(state.best_version),
        "{{CANDIDATE_DIR}}": attempt_dir,
        "{{BASELINE_DIR}}": best_dir,
        "{{FAILED_CONFIGS}}": json.dumps(current_score.get("configs", []), indent=2),
        "{{ERROR_DETAILS}}": "",
    }

    # 加载测试配置
    scoring_config_full = os.path.join(project_root, scoring_config)
    if os.path.exists(scoring_config_full):
        with open(scoring_config_full) as f:
            replacements["{{TEST_CONFIGS}}"] = f.read()

    prompt = template
    for key, value in replacements.items():
        prompt = prompt.replace(key, value)

    return prompt


def launch_agent_session(prompt: str, config: dict, project_root: str,
                         step_num: int, state: EvolutionState) -> dict:
    """启动 Claude Code Agent 会话

    返回: {
        "status": "committed" | "rejected" | "failed" | "timeout",
        "commit_hash": str,
        "score": dict,
        "description": str,
        "failure_type": str,
        "log": str,
    }
    """
    max_duration = config.get("max_session_duration", "30m")
    timeout_seconds = int(parse_duration(max_duration).total_seconds())
    metric_type = config.get("metric_type", "tflops")
    min_ratio = config.get("min_improvement_ratio", 0.02)

    log_path = os.path.join(project_root, "evolution", "logs", f"step_{step_num:03d}.md")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    print(f"\n{'='*60}")
    print(f"启动 Agent 会话 (Step {step_num})")
    print(f"超时: {max_duration}")
    print(f"{'='*60}\n")

    # 保存 prompt 到日志
    with open(log_path, "w") as f:
        f.write(f"# Step {step_num}\n\n")
        f.write(f"时间: {datetime.now(timezone.utc).isoformat()}\n\n")
        f.write(f"## Prompt\n\n```\n{prompt[:2000]}...\n```\n\n")

    # 启动 Claude Code 会话
    try:
        result = subprocess.run(
            ["claude", "--print", "--dangerously-skip-permissions", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=project_root,
        )
        agent_output = result.stdout
        agent_stderr = result.stderr

        # 追加 Agent 输出到日志
        with open(log_path, "a") as f:
            f.write(f"## Agent 输出\n\n```\n{agent_output[-5000:]}\n```\n\n")
            if agent_stderr:
                f.write(f"## Stderr\n\n```\n{agent_stderr[-2000:]}\n```\n\n")

    except subprocess.TimeoutExpired:
        with open(log_path, "a") as f:
            f.write(f"## 超时\n\nAgent 会话超时 ({max_duration})\n")
        return {"status": "timeout", "failure_type": "timeout",
                "description": "会话超时", "log": log_path,
                "commit_hash": "", "score": {}}

    except FileNotFoundError:
        print("错误: claude 命令未找到，请确保 Claude Code CLI 已安装")
        with open(log_path, "a") as f:
            f.write("## 错误\n\nclaude CLI 未找到\n")
        return {"status": "failed", "failure_type": "infra",
                "description": "claude CLI 未找到", "log": log_path,
                "commit_hash": "", "score": {}}

    # 检查是否有新的 git commit
    try:
        latest_commit = subprocess.run(
            ["git", "log", "-1", "--format=%H %s"],
            capture_output=True, text=True, cwd=project_root,
        ).stdout.strip()
        commit_hash = latest_commit.split(" ", 1)[0][:7] if latest_commit else ""
        commit_msg = latest_commit.split(" ", 1)[1] if " " in latest_commit else ""
    except Exception:
        commit_hash = ""
        commit_msg = ""

    # 检查是否有新的评分文件
    score = {}
    scores_dir = os.path.join(project_root, "evolution", "scores")
    if os.path.exists(scores_dir):
        score_files = sorted(Path(scores_dir).glob("v*.json"))
        if score_files:
            latest_score_file = score_files[-1]
            with open(latest_score_file) as f:
                score = json.load(f)

    # 判断提交状态
    correctness = score.get("correctness_total", 0.0)
    perf = score.get("performance_total", 0.0)

    if correctness < 1.0:
        failure_type = score.get("failure_type", "correctness")
        if "compile_error" in score:
            failure_type = "compile"
        return {"status": "failed", "failure_type": failure_type,
                "commit_hash": commit_hash, "score": score,
                "description": commit_msg, "log": log_path}

    # 正确性通过，检查性能提升
    if state.current_version < 0:
        # v0: 只要正确就算 committed
        committed = True
    elif is_improvement(perf, state.best_score, metric_type, min_ratio):
        committed = True
    else:
        committed = False

    if committed:
        return {"status": "committed", "failure_type": "",
                "commit_hash": commit_hash, "score": score,
                "description": commit_msg, "log": log_path}
    else:
        return {"status": "rejected", "failure_type": "performance",
                "commit_hash": commit_hash, "score": score,
                "description": commit_msg, "log": log_path}


# ========== 停滞检测与重定向 ==========

def generate_redirect_directive(state: EvolutionState, project_root: str,
                                config: dict) -> str:
    """生成重定向优化指令"""
    print("\n>>> 检测到停滞，生成重定向指令...")

    # 收集最近版本的 profiling 数据
    recent_profiles = []
    for entry in state.lineage[-5:]:
        v = entry["version"]
        score_path = os.path.join(project_root, "evolution", "scores", f"v{v}.json")
        if os.path.exists(score_path):
            with open(score_path) as f:
                recent_profiles.append(json.load(f))

    # 读取重定向 prompt 模板
    template_path = os.path.join(
        project_root, "evolution/prompts/redirect-directive.md"
    )
    if os.path.exists(template_path):
        with open(template_path) as f:
            template = f.read()
    else:
        template = DEFAULT_REDIRECT_PROMPT

    # 变量替换
    prompt = template.replace("{{N}}", str(state.current_version + 1))
    prompt = prompt.replace("{{ELAPSED}}", _elapsed_time(state.start_time))
    prompt = prompt.replace("{{BEST_SCORE}}", str(state.best_score))
    prompt = prompt.replace("{{BEST_VERSION}}", str(state.best_version))
    prompt = prompt.replace("{{STALL_COUNT}}", str(state.stall_counter))
    prompt = prompt.replace("{{METRIC_TYPE}}", config.get("metric_type", "tflops"))
    prompt = prompt.replace("{{PROFILING_SUMMARY}}", json.dumps(recent_profiles, indent=2)[:3000])
    prompt = prompt.replace("{{RECENT_FAILURES}}", _recent_failures(state, project_root))

    # 调用 Claude 生成指令
    try:
        result = subprocess.run(
            ["claude", "--print", "-p", prompt],
            capture_output=True, text=True,
            timeout=300,
            cwd=project_root,
        )
        directive = result.stdout.strip()
        if directive:
            print(f"重定向指令: {directive[:200]}...")
            return directive
    except Exception as e:
        print(f"重定向生成失败: {e}")

    return "尝试一个完全不同的优化方向。回顾 profiling 数据，找到之前未关注的瓶颈。"


DEFAULT_REDIRECT_PROMPT = """你正在审查一个 Ascend C 内核优化的进化轨迹。

## 当前状态
- 已提交 {{N}} 个版本
- 运行时间: {{ELAPSED}}
- 最佳评分: {{BEST_SCORE}} ({{METRIC_TYPE}}) (版本 v{{BEST_VERSION}})
- 最近 {{STALL_COUNT}} 个版本无改进

## Profiling 数据摘要
{{PROFILING_SUMMARY}}

## 最近的失败尝试
{{RECENT_FAILURES}}

## 任务
1. 分析当前瓶颈所在
2. 提出 3-5 个**未被尝试过的**优化方向
3. 选择最有希望的方向
4. 生成具体的优化指令（一段话，给 Kernel Evolution Agent）

只输出最终的优化指令，不要输出分析过程。
"""


def _elapsed_time(start_time_str: str) -> str:
    """计算已用时间"""
    try:
        start = datetime.fromisoformat(start_time_str)
        elapsed = datetime.now(timezone.utc) - start
        hours = int(elapsed.total_seconds() // 3600)
        minutes = int((elapsed.total_seconds() % 3600) // 60)
        return f"{hours}h {minutes}m"
    except Exception:
        return "未知"


def _recent_failures(state: EvolutionState, project_root: str) -> str:
    """收集最近的失败日志摘要"""
    logs_dir = os.path.join(project_root, "evolution", "logs")
    if not os.path.exists(logs_dir):
        return "(无失败记录)"

    log_files = sorted(Path(logs_dir).glob("step_*.md"))[-5:]
    summaries = []
    for lf in log_files:
        with open(lf) as f:
            content = f.read()
        summaries.append(f"--- {lf.name} ---\n{content[:500]}")

    return "\n".join(summaries) if summaries else "(无失败记录)"


# ========== 停止条件 ==========

def should_stop(state: EvolutionState, config: dict) -> tuple:
    """检查是否应该停止

    返回: (should_stop: bool, reason: str)
    """
    # 最大版本数
    if state.current_version >= config.get("max_versions", 100):
        return True, f"达到最大版本数 ({config['max_versions']})"

    # 最大运行时间
    max_wall = parse_duration(config.get("max_wall_time", "168h"))
    try:
        start = datetime.fromisoformat(state.start_time)
        elapsed = datetime.now(timezone.utc) - start
        if elapsed > max_wall:
            return True, f"超过最大运行时间 ({config['max_wall_time']})"
    except Exception:
        pass

    # 目标性能达成
    target = config.get("target_performance")
    metric_type = config.get("metric_type", "tflops")
    if target and state.best_score > 0 and is_target_met(state.best_score, target, metric_type):
        return True, f"目标性能已达成 ({state.best_score} {metric_type})"

    # 连续重定向失败
    max_redirects = config.get("max_consecutive_redirects", 3)
    if state.consecutive_redirects >= max_redirects:
        return True, f"连续 {max_redirects} 次重定向无效，等待人工介入"

    return False, ""


# ========== 会话上下文构建 ==========

def build_lineage_summary(state: EvolutionState) -> dict:
    """构建三段式谱系摘要（recent + best + strategy）"""
    summary = {
        "recent_history": [],
        "best_history": [],
        "strategy_summary": "",
    }

    # 最近 5 个版本
    summary["recent_history"] = state.lineage[-5:]

    # 历史最佳 3 个版本
    sorted_by_score = sorted(state.lineage, key=lambda x: x.get("score", 0), reverse=True)
    summary["best_history"] = sorted_by_score[:3]

    # 策略摘要
    if state.lineage:
        total = len(state.lineage)
        summary["strategy_summary"] = (
            f"共 {total} 个版本。"
            f"最佳: v{state.best_version} ({state.best_score})。"
            f"停滞计数: {state.stall_counter}。"
            f"失败计数: {state.failed_attempts}。"
        )

    return summary


# ========== 主循环 ==========

def main_loop(config: dict, project_root: str):
    """主进化循环"""
    state_path = os.path.join(project_root, "evolution", "state.json")
    state = EvolutionState(state_path, config)
    metric_type = config.get("metric_type", "tflops")

    print("========================================")
    print("AscendC Kernel Agent — 进化引擎")
    print("========================================")
    print(f"算子: {state.operator_name}")
    print(f"芯片: {state.target_chip}")
    print(f"指标: {metric_type}")
    print(f"当前版本: v{state.current_version}")
    print(f"最佳评分: {state.best_score} ({metric_type})")
    print(f"谱系长度: {len(state.lineage)}")
    print("========================================\n")

    # 恢复检查：清理中断的 attempt
    if state.active_attempt_dir and os.path.exists(state.active_attempt_dir):
        print(f"清理上次中断的候选目录: {state.active_attempt_dir}")
        cleanup_attempt(state.active_attempt_dir)
        state.active_attempt_dir = None
        state.save()

    while True:
        # 检查停止条件
        stop, reason = should_stop(state, config)
        if stop:
            print(f"\n停止: {reason}")
            break

        # 1. 从 best/ 创建隔离的候选工作区
        attempt_dir = prepare_attempt_dir_from_best(state, config, project_root)
        state.active_attempt_dir = attempt_dir
        state.save()

        directive = None
        use_repair = False

        # 2. 停滞检测 — 不同信号不同响应
        stall_threshold = config.get("stall_threshold", 5)
        max_failed = config.get("max_failed_attempts", 5)

        if state.failed_attempts >= max_failed:
            # 连续失败 → repair 模式
            print(f"\n>>> 连续 {state.failed_attempts} 次失败，切换到 repair 模式")
            use_repair = True
            state.failed_attempts = 0

        if state.stall_counter >= stall_threshold:
            # 正确但无提升 → 重定向
            directive = generate_redirect_directive(state, project_root, config)
            state.redirect_count += 1
            state.consecutive_redirects += 1
            state.stall_counter = 0

        # 3. 构建 prompt 并启动 Agent 会话
        prompt = build_agent_prompt(state, project_root, config, attempt_dir,
                                     directive, use_repair)
        result = launch_agent_session(prompt, config, project_root,
                                       state.current_step, state)

        # 4. 处理结果
        if result["status"] == "committed":
            state.current_version += 1
            new_score = result["score"].get("performance_total", 0.0)

            state.lineage.append({
                "version": state.current_version,
                "commit": result["commit_hash"],
                "score": new_score,
                "description": result["description"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })

            improved = is_improvement(
                new_score, state.best_score, metric_type,
                config.get("min_improvement_ratio", 0.02)
            ) if state.best_version >= 0 else True

            if improved:
                print(f"\n新最佳! v{state.current_version}: {new_score} ({metric_type})")
                state.best_version = state.current_version
                state.best_score = new_score
                state.best_commit = result["commit_hash"]
                state.stall_counter = 0
                state.consecutive_redirects = 0
                # 晋升候选为新 best
                promote_attempt_to_best(attempt_dir, config, project_root)
            else:
                print(f"\nv{state.current_version}: {new_score} ({metric_type})"
                      f" (未超越最佳 {state.best_score})")
                state.stall_counter += 1

            state.failed_attempts = 0

            # Git tag (简洁格式)
            try:
                tag = f"v{state.current_version}"
                subprocess.run(
                    ["git", "tag", tag],
                    cwd=project_root, capture_output=True,
                )
            except Exception:
                pass

        elif result["status"] in ("failed", "timeout"):
            failure_type = result.get("failure_type", "unknown")
            print(f"\nStep {state.current_step}: 失败 ({failure_type})")
            state.failed_attempts += 1

        elif result["status"] == "rejected":
            print(f"\nStep {state.current_step}: 正确但性能未提升，rejected")
            state.stall_counter += 1

        # 5. 清理并持久化
        state.total_attempts += 1
        state.last_completed_step = state.current_step
        state.current_step += 1
        state.active_attempt_dir = None
        cleanup_attempt(attempt_dir)
        state.save()

        # 简短间隔
        time.sleep(2)

    # 最终报告
    print("\n" + "=" * 60)
    print("进化完成")
    print("=" * 60)
    print(f"总步骤: {state.total_attempts}")
    print(f"提交版本: {state.current_version + 1}")
    print(f"最佳版本: v{state.best_version}")
    print(f"最佳评分: {state.best_score} ({metric_type})")
    print(f"重定向次数: {state.redirect_count}")
    print("=" * 60)

    state.save()


# ========== 入口 ==========

def main():
    parser = argparse.ArgumentParser(description="AscendC Kernel Agent 进化引擎")
    parser.add_argument(
        "--config",
        default="evolution/config.yaml",
        help="配置文件路径 (默认: evolution/config.yaml)",
    )
    args = parser.parse_args()

    # 确定项目根目录
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # 加载配置
    config_path = os.path.join(project_root, args.config)
    if os.path.exists(config_path):
        with open(config_path) as f:
            config = yaml.safe_load(f)
        for key, value in DEFAULT_CONFIG.items():
            config.setdefault(key, value)
    else:
        print(f"警告: 配置文件 {config_path} 不存在，使用默认配置")
        config = dict(DEFAULT_CONFIG)

    try:
        main_loop(config, project_root)
    except KeyboardInterrupt:
        print("\n\n手动中断。状态已保存。")
        sys.exit(0)


if __name__ == "__main__":
    main()
