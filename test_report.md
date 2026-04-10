# AVO 框架端到端验证报告（2026-04-10）

使用 PyTorch LSTM 模型作为"challenging operator"对 AVO 5-agent team 框架做了一次端到端走查。目的是**验证流程与定位潜在问题**，不追求 LSTM 算子本身跑通。

## 测试方法

- 从 `main` 拉 `test` 分支（测试期间）
- 主 Claude Code 会话扮演 Architect Agent
- 通过 `Agent` 工具（subagent_type=general-purpose）派发 Developer / Reviewer / Tester / Supervisor 子 agent
- 预算收紧：`max_versions=5, stall_threshold=2, max_failed_attempts=2`
- 逐步骤在 `evolution/logs/step_*.md` 记录决策，在 test_report.md 记录发现

## 覆盖情况

| 维度 | 覆盖 |
|------|------|
| 5 个 Agent 全部显式派发 | ✅ Architect + Developer + Reviewer + Tester + Supervisor |
| Architect 8 步主循环 | ✅ READ STATE / ANALYZE / DESIGN / DEV / REV / TEST / EVALUATE / UPDATE |
| Supervisor failure 触发路径 | ✅ `failed_attempts >= max_failed_attempts` 自然触发 |
| Supervisor ABORT verdict 路径 | ✅ Supervisor 识别环境级阻塞，输出 ABORT |

## v0 尝试运行结果

| 阶段 | 结果 | 备注 |
|------|------|------|
| DESIGN / PLAN | ✅ | Architect 写 DESIGN.md + PLAN.md |
| Developer | ✅ | 一次通过 `msopgen gen + build.sh`，`custom_opp_openEuler_aarch64.run` (398 KB) |
| Reviewer | ✅ | 独立 rebuild 成功，67/100 PASS WITH NOTES |
| Tester.compile | ✅ | 沿用 Developer build |
| Tester.deploy | ✅ | aclnn header 已安装 |
| **Tester.build_pybind** | ❌ | **环境级**阻塞：`setuptools`/`pip` 目录 `750 root:root`，非框架 bug |
| Tester.correctness/performance | - | 被 pybind 失败阻塞 |
| Supervisor | ✅ | 判定 ABORT，写入 `evolution/redirects/step_1.md` 并给出外部修复步骤 |

## 发现的框架问题

共发现 **25+** 个框架相关问题，分为代码级、文档级和环境级三类。下表只列有明确 action 的项，全部框架修复已作为独立 commit 合入 `main`：

### 代码级（CRITICAL → LOW）

| # | 严重度 | 文件 | 问题 | 修复 |
|---|--------|------|------|------|
| F4 | CRITICAL | `scoring/score.sh` | 所有子阶段失败都 `exit 0`，破坏 Architect 编排 contract | `fix(scoring): propagate failure stage through score.sh exit codes` — 退出码 0/2/3/4/5 |
| F5 | CRITICAL | `scoring/compute_score.py` | `failure_type` 超载为 `"compile"`，compile/deploy/pybind/correctness 无法区分 | 同上，新增 `--failure-stage` 参数 |
| F7 | HIGH | `scoring/env_setup.sh` | 缺 `from setuptools import setup` preflight，让 namespace-package 降级错误拖到 pybind 阶段才暴露 | `fix(scoring): add setuptools preflight warning` — 启动阶段立即警告 |
| F22 | LOW | `evolution/` 三个子目录 | fresh clone 后不存在，首次 Supervisor 调用必须 mkdir -p | `chore: bootstrap evolution/ directories and add .gitignore` — `.gitkeep` + `.gitignore` |

### 文档级（Agent AGENT.md 和 CLAUDE.md）

| # | 严重度 | 文件 | 问题 | 修复 |
|---|--------|------|------|------|
| F23 | HIGH | `agents/architect/AGENT.md` | dispatch 方式只写了 `claude --print -p`，在 Claude Code 内部无法用 | `docs(architect): ... dispatch patterns` — 补 `Agent` 工具派发路径 |
| F24 | HIGH | `agents/architect/AGENT.md` | state.json bootstrap 没有 schema，首次运行行为未定义 | 同上，补 bootstrap schema |
| F25 | MEDIUM | `agents/architect/AGENT.md` | Supervisor 触发条件只是散文 | 同上，补决策表 + 伪代码 |
| F14 | HIGH | `agents/reviewer/AGENT.md` | 80/100 PASS 阈值让 seed 版本数学上不可能 PASS | `docs(reviewer): stage-aware scoring...` — seed 阶段降 PASS 到 65 |
| F15 | LOW | `agents/reviewer/AGENT.md` | 缺独立构建 runbook | 同上 |
| F16 | LOW | `agents/reviewer/AGENT.md` | REVIEW.md 无结构化 trailer | 同上，强制 YAML `reviewer_trailer` |
| F19 | HIGH | `agents/supervisor/AGENT.md` | 无 ABORT verdict schema | `docs(supervisor): verdict schema, ABORT path...` — 三 verdict |
| F20 | MEDIUM | `agents/supervisor/AGENT.md` | Step 4 与 Constraint 段矛盾（state.json 写权） | 同上，明确 state.json 独归 Architect |
| F21 | MEDIUM | `agents/supervisor/AGENT.md` | 无 seed 阶段 playbook（1 次尝试做轨迹分析无意义） | 同上，新增 seed-phase post-mortem 分支 |
| F8 | MEDIUM | `agents/tester/AGENT.md` + `CLAUDE.md` | `build_and_run.sh` vs `build_pybind.sh` 命名漂移 | `docs: clarify build_pybind.sh vs build_and_run.sh...` |
| F1 | MEDIUM | `workspace/templates/reference/reference_template.py` | `get_init_inputs()` 无参调用契约未文档化 | 同上 + CLAUDE.md |
| F2 | MEDIUM | 同上 | Model/ModelNew seed 一致性契约未文档化 | 同上 |

### 环境级（非框架 bug，由 preflight 捕获）

| # | 症状 | 真因 | 框架层处理 |
|---|------|------|-----------|
| F10 | `ImportError: cannot import name 'setup' from 'setuptools'` | `/usr/local/lib/python3.11/site-packages/{setuptools,pip}` 被设为 `mode 750 root:root`，用户无法 import；Python 降级为空 namespace package | F7 preflight 捕获并打印修复命令：`sudo chmod -R o+rX /usr/local/lib/python3.11/site-packages/{setuptools,pip,pkg_resources}` |
| F0 | `torch_npu` 权限 warnings 污染 stdout | `/usr/local/Ascend/cann-8.5.0` owner mismatch，非致命 | 提示 scoring 脚本注意 stderr 隔离 |

### 未立即修复（待后续 ticket）

| # | 原因 | TODO |
|---|------|------|
| F6 | 误报：`gen_golden.py` 已有 registry + graceful fallback | 无需动作 |
| F11-F13 | 上游 msopgen 行为（默认 `ascend910` 而非 `ascend910b`、bizarre 权限校验、冗余 tf_plugin） | 在 Developer AGENT.md 增补"msopgen 已知注意事项"一节 |
| F3 | `workspace/runs/*/best/` 仅 .gitkeep 是框架设计 | README 里说明 |
| F9 | config 的 `operator` 字段与 `runs_dir` 名强耦合，未文档化 | 单独 ticket：schema 解耦 |
| F17 | `_stack_lstm_weights()` 算入 NPU 性能测量是 reference.py 写法问题 | 在 ops-profiling skill 补"有状态算子性能测量注意事项" |
| F18 | `failure_category` 枚举需配合 state.json schema 演进 | 单独 ticket |

## 运行环境恢复指引

本次测试最大的外部阻塞是 setuptools/pip 权限问题。下次运行框架前必须由运维执行：

```bash
sudo chmod -R o+rX /usr/local/lib/python3.11/site-packages/{setuptools,pip,pkg_resources}
# 验证
python3 -c "from setuptools import setup; import pip; print('ok')"
```

修复后 `scoring/env_setup.sh` 的 preflight 警告应消失。

## 测试结论

1. **框架结构完整**：5 agent 分工清晰，8 步主循环能端到端执行，子 agent 通过 `Agent` 工具派发稳定可观测
2. **最关键的 bug**：`scoring/score.sh` "exit 0 掩盖失败" 破坏了 orchestration contract，**已修复并端到端验证**（重跑 v0 后 exit=4, failure_type=pybind）
3. **主要文档 gap**：所有 AGENT.md 对失败路径（ABORT、seed 阶段、stage-aware 评分、dispatch 方式）的指引缺失，**已补齐**
4. **测试方法学**：LSTM 作为"challenging operator"合格——复杂度足够暴露 25+ 个框架问题，同时 Developer 能够在 seed 阶段产出可编译骨架证明 msopgen 流水线到 deploy 阶段是 working 的
5. **下一步**：运维修复 setuptools 权限 → 重跑一个简单算子（如 add_custom）做回归 → 验证 score.sh 新退出码契约在"完整成功"路径下也工作正常
