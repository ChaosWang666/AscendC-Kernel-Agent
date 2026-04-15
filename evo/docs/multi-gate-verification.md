# Multi-Gate Verification（论文 §3.5 + App B）

## 输出结构

$$o_t = V(x, y_t) = (g_{\text{hack}}, g_{\text{comp}}, g_{\text{corr}}, \ell_{\text{lat}}) \in \{0,1\}^3 \times \mathbb{R}_+$$

Feasibility 门：

$$g_{\text{feas}}(o_t) \triangleq g_{\text{hack}} \wedge g_{\text{comp}} \wedge g_{\text{corr}}$$

## 实现流程（multigate-verifier agent）

```
Step 1: Anti-hack
  1a. Rule-based scan (快速)
  1b. 若 1a 通过且 enabled → Model-based LLM audit (~30s)
  若 g_hack=0: 短路返回 o_t={0, 0, 0, null, reason="anti_hack_violation"}

Step 2: score.sh 运行 (~5-15 min, 取决于 op)
  source /usr/local/Ascend/ascend-toolkit/set_env.sh
  bash scoring/score.sh {attempt_dir} {op.scoring_config}
  exit_code = $?

Step 3: 映射退出码 → 四元组
  按 config.yaml: verifier.exit_code_map

Step 4: 若成功 (exit_code ∈ {0, 6})，读 latency
  score_json = evolution/scores/v{N}.json  # 最新一版
  latency_us = score_json.performance_total

Step 5: 返回 trailer
```

## 退出码映射表

源：`scoring/score.sh` 的退出码契约（CLAUDE.md / AGENTS.md 已定义）。

| exit_code | 含义 | g_comp | g_corr | latency | feasible |
|-----------|------|--------|--------|---------|----------|
| 0 | 完整成功（correctness=1.0 + perf 达标） | 1 | 1 | 有 | ✓ |
| 1 | environment 预检失败 | 0 | 0 | null | ✗ |
| 2 | compile 失败 | 0 | 0 | null | ✗ |
| 3 | deploy 失败（.run 安装） | 1 | 0 | null | ✗ |
| 4 | pybind 构建失败 | 1 | 0 | null | ✗ |
| 5 | correctness 失败 | 1 | 0 | null | ✗ |
| 6 | 正确但 performance_total 未达门槛 | 1 | 1 | 有 | ✓ |

**退出码 6 特殊**：正确性达标但性能规则不满足（比如 `min_improvement_ratio` 未满足）——对 **EVO 来说仍是 feasible**（correctness ok），因为 Stage 2 是用 tanh 的 relative reward 独立优化 latency，不依赖 score.sh 内部的 "达标" 判断。

退出码 3/4 的 g_corr = 0 是合理的：deploy/pybind 没跑，correctness 无法验证。

## Anti-Hacking（App B）

### 第一层：Rule-based Screening（§B.1）

扫描 `{attempt_dir}/{OpCapitalName}/op_kernel/*.cpp`、`*.h`：

**禁用 include**（在 op_kernel 里）：
- `torch`、`torch_npu`
- `numpy`

**禁用 API 子串**：
- `torch.nn.functional` / `F.gelu` / `F.relu` / ...
- `torch_npu.npu.*`
- 任何 Python 调用（op_kernel 是纯 C++）

**结构化检查**（可用正则或轻量 AST）：
- "Duplicate 后立即返回" 无实际 Compute：可能是伪造常量输出
- Input 与 output 相同地址的 memcpy：可能是 "返回输入即可" 作弊
- 硬编码特定 shape/dtype 的返回值

**作用范围**：仅 `op_kernel/*.{cpp,h}`。`op_host/*.cpp` 允许 torch include（它跑在 host，可能用于 reference 比对）。

### 第二层：Model-based Screening（§B.2）

若 rule-based 通过 + `config.anti_hack.model_based.enabled=true`：

派发 Reviewer Agent（复用 `agents/reviewer/AGENT.md`）以 `prompt_mode=anti_hack_audit`：

```
你是 Anti-Hacking Auditor。读 agents/reviewer/AGENT.md 作为角色框架。

【任务】
判断给定 kernel 是否存在 subtle harness manipulation（不是明显的 import/API 作弊，
那部分已被 rule-based 过滤）。

关注点：
1. 是否通过文件系统 / 环境变量 / temp 文件读答案？
2. 是否利用 test 数据的特定分布（e.g., 全零/全一）绕过计算？
3. 是否 hardcode 某些 shape/dtype 下的 golden 输出？
4. Kernel 内部是否做了 "fast path + fallback"，fast path 其实是 cheat？

【输入】
- Kernel 源码: {kernel_dir}/op_kernel/*.cpp
- Host 注册: {kernel_dir}/op_host/*.cpp
- Reference: {reference_py}
- 算子规格: {spec_md}

【输出】严格 JSON（无 markdown）
{
  "g_hack": 0 | 1,             # 1 = clean, 0 = violated
  "violations": [{"file": "...", "line": N, "type": "...", "explanation": "..."}],
  "confidence": 0.0-1.0
}
```

**何时跳过 model-based**：
- rule-based 已发现 violation（g_hack 已是 0）
- `config.anti_hack.model_based.enabled=false`（debug 或性能敏感时）

### Anti-Hack 日志

可选：记录到 `evo/state/episodes/{op}/anti_hack_log.jsonl`，便于事后审计：

```json
{"t": 3, "rule_based": {"passed": true}, "model_based": {"status": "clean", "confidence": 0.92}, "wall_time_sec": 28}
```

## Latency 提取细节

**文件位置**：`evolution/scores/v{N}.json`，N = 该次 score.sh 写入的版本号。

**提取逻辑**：

```python
import glob, json
score_files = sorted(glob.glob("evolution/scores/v*.json"),
                     key=lambda p: int(p.split("/v")[-1].split(".")[0]))
latest = score_files[-1]
data = json.load(open(latest))
latency = data.get("performance_total")  # us（latency_us）
```

**边界情况**：
- 若 `performance_total` 缺失（退出码 3/4/5 下）：`latency_us = null`
- 若 `performance_total` 是字符串（如 "35-42 (variance)"）：memory-curator 需解析，取中值或 median；v1 规范要求 score.sh 写 **数字**（float），v0 的历史字符串不再出现

**配置一致性**：score.sh 调用时传的 `scoring/configs/{op}.json` 决定了 `performance_total` 是哪个测试级别（smoke / representative）的数字——EVO v1 假定一致使用 `representative` 级别为 primary metric。

## 读写范围

| 资源 | 读 | 写 |
|------|-----|-----|
| `{attempt_dir}/` | ✓ | ✗ |
| `evo/config.yaml` | ✓ | ✗ |
| `scoring/*` | ✓（执行 score.sh） | ✗ |
| `evolution/scores/v*.json` | ✓ | 间接（score.sh 写） |
| `evo/state/episodes/{op}/anti_hack_log.jsonl` | ✓ | ✓（可选） |
| `evo/memory/` | ✗ | ✗（交由 memory-curator） |

## 超时处理

score.sh 单次执行最长 15 分钟（config 可调）。超时：
- 杀进程（`timeout 900 bash scoring/score.sh ...`）
- 返回 `o_t = {g_hack: 1, g_comp: 0, g_corr: 0, latency: null, reason: "timeout"}`
