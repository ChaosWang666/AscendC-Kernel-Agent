# EVO 框架形式化规格

> 本文件是 `evo/` 的权威数学规格，所有 Agent 实现必须与此一致（AVO 版本 `spec.md` 位于 `main` 分支）。
> 基于论文 `EVO-paper/main.tex` §3（Method）。

---

## 1. 问题形式化：Memory-based MDP

我们把跨算子 kernel 合成建模为 **M-MDP**，五元组 $(\mathcal{S}, \mathcal{A}, \mathcal{M}, \mathcal{P}, \mathcal{R})$：

### 1.1 状态空间 $\mathcal{S}$

$$s_t = (x, \xi_t)$$

- $x \in \mathcal{X}$：静态任务——PyTorch reference 算子 + 元数据（shapes、dtype、算子超参），对应 `workspace/specs/{op}.md` + `workspace/runs/{op}/test/reference.py`
- $\xi_t$：动态生成状态——`{best_so_far_latency, stage, iter, feasible_found, popart_running}`，持久化在 `evo/state/episodes/{op}/state.json`

### 1.2 动作空间 $\mathcal{A}$

$$a_t = y_t \in \mathcal{Y}$$

即生成的完整 kernel 源码，包括 `op_host/{op}_custom.cpp`、`op_host/{op}_custom_tiling.h`、`op_kernel/{op}_custom.cpp`。物理实体是 `workspace/runs/{op}/attempts/step_N/{OpName}Custom/`。

### 1.3 记忆 $\mathcal{M}$

$$\mathcal{M}_{t+1} \leftarrow \mathcal{M}_t \cup \{(s_t, a_t, r_t)\} \quad\text{(Eq. 1)}$$

$\mathcal{M}_0$ = 种子：API 模板 + 最佳实践（在 `evo/memory/seed/`）。
$\mathcal{M}$ 异质内容（§3.2）：
1. API 模板（backend-specific）
2. 成功 / 失败经验摘要
3. 生成 trace（draft + refined）
4. kernel refinement 最佳实践

### 1.4 转移 $\mathcal{P}$

任务 $x$ 在 episode 内不变，转移确定：

$$s_{t+1} = (x, \xi_{t+1}), \quad \xi_{t+1} = f(x, \xi_t, a_t, o_t) \quad\text{(Eq. 2)}$$

$f$ 的实现 = `memory-curator` 根据 verifier 输出 $o_t$ 更新 `state.json`。

### 1.5 策略分解

$$\pi(y_t \mid s_t, \mathcal{M}_t) = G_\theta(a_t \mid s_t, c_t) \cdot \mu(c_t \mid s_t, \mathcal{M}_t) \quad\text{(Eq. 3 — 论文 Eq. 2 编号)}$$

- $G_\theta$ 固定（预训练 LLM）= Claude Code 派发 `evo/agents/developer/AGENT.md`
- $\mu$ 通过 RL 学习 = `evo/agents/retrieval-policy/AGENT.md`

---

## 2. 价值驱动检索 $\mu$（§3.2）

### 2.1 Stage-specific Q 值

$$Q_k(s, m), \quad k \in \{1, 2\}$$

- $Q_1(s, m)$：在 Drafting 阶段，$m$ 贡献可行 kernel 的期望价值
- $Q_2(s, m)$：在 Refining 阶段，$m$ 贡献 latency 下降的期望价值

### 2.2 两阶段检索管线

给定 $s = (x, \xi_t)$、阶段 $k$、最终 context 数 $N$、过检倍率 $\lambda$（配置 $\lambda N = K$）：

1. **Dense top-K**：$\mathcal{C}(x) = \mathrm{TopK}_{K}\bigl(\mathrm{sim}(x, m)\bigr),\ m \in \mathcal{M}$
2. **ε-greedy Value filter**：以概率 $\varepsilon$ 从 $\mathcal{C}(x)$ 随机选 $N$；否则按 $Q_k$ 降序取 top-$N$

输出 $c_t \subset \mathcal{C}(x)$，传入 $G_\theta$。

**API 混合检索**（§3.2 末段）：Drafting 时，API 知识走 backend-aware 静态 bundle + 精确符号查找，不经 Q 过滤（API 价值主要由 backend coverage 决定）。

### 2.3 统一 MC 更新（Eq. 3，论文 Eq. 3）

$$Q(s, m) \leftarrow Q(s, m) + \alpha \cdot (r - Q(s, m))$$

$r$ 是阶段专属奖励，$\alpha$ 为步长（默认 0.1）。仅对 $m \in c_t$ 更新。有界性 / 收敛性证明见 `docs/q-value-update.md` 与论文 App A。

---

## 3. Stage 1：Cold-Start Drafting（§3.3）

### 3.1 目标

首次获得 **feasible kernel** 以 bootstrap 后续 refinement。

### 3.2 奖励（Eq. 4，论文 Eq. 4）

$$r_{1,t} = \begin{cases} +1, & g_{\text{feas}}(o_t) = 1 \\ -1, & \text{otherwise} \end{cases}$$

### 3.3 伪代码

```
Input: task x, memory M, retrieval N, λ, ε-schedule, budget T1
for t = 0, 1, ..., T1-1:
    C ← DenseRetrieval(x, M, K=λN)
    c_t ← EpsilonGreedyByQ1(C, N, ε_t)
    y_t ← G_θ(x, c_t)                    # 派发 Developer
    o_t ← V(x, y_t)                      # multigate-verifier
    r_{1,t} ← (+1 if g_feas(o_t) else -1)
    for m ∈ c_t: Q_1(s, m) ← Q_1(s, m) + α(r_{1,t} − Q_1(s, m))
    append (s_t, a_t, r_{1,t}, o_t) to trajectory
    if y_t is feasible:
        append y_t to bank.jsonl with type="trace", stage_when_added=1
        add y_t to P(x)                  # Stage 2 起点集
        return y_t                       # 切 Stage 2
return None                              # Stage 1 budget exhausted
```

---

## 4. Stage 2：Continual Refining（§3.4）

### 4.1 目标

基于 $P(x)$（可行起点集）迭代改写以 **降低 latency**。

### 4.2 奖励（Eq. 5，论文 Eq. 5）

$$r_{2,t} = \begin{cases} -1, & g_{\text{feas}}(o_t) = 0 \\ \tanh(\log b_t - \log \ell_{\text{lat}}(o_t)), & \text{otherwise} \end{cases}$$

其中 $b_t$ 为截至 $t$ 时的 best-so-far latency。

### 4.3 PopArt 在线归一化

$$\hat{r}_{2,t} = \frac{r_{2,t} - \mu_2}{\sigma_2}$$

$\mu_2, \sigma_2$ 用 EMA 在线估计（momentum 默认 0.99），见 `docs/stage2-refining.md`。

### 4.4 伪代码

```
Input: task x, P(x), memory M, budget T2, best b_0 = min(ℓ(p) for p ∈ P(x))
for t = 0, ..., T2-1:
    # ε-greedy 选 start point
    p_t ← EpsilonGreedyByQ2(P(x), ε_t)
    # 检索 refinement context（排除 p_t 自身）
    C ← DenseRetrieval(x, M \ {p_t}, K=λN)
    c_t ← EpsilonGreedyByQ2(C, N, ε_t)
    y_t ← G_θ(x, p_t, c_t)               # 派发 Developer：prompt 注入 p_t 和 c_t
    o_t ← V(x, y_t)
    if g_feas(o_t) = 0:
        r_raw ← -1
    else:
        r_raw ← tanh(log(b_t) − log(ℓ_lat(o_t)))
        b_{t+1} ← min(b_t, ℓ_lat(o_t))
        append y_t to bank.jsonl; P(x) ← P(x) ∪ {y_t}
    # PopArt 归一
    UpdatePopArt(r_raw) → (μ_2, σ_2)
    r_{2,t} ← (r_raw − μ_2) / σ_2
    # 对 start point 和 context 均更新 Q_2
    for m ∈ {p_t} ∪ c_t:
        Q_2(s, m) ← Q_2(s, m) + α(r_{2,t} − Q_2(s, m))
    append (s_t, a_t, r_{2,t}, o_t) to trajectory
return b_{T2}                            # 最优 latency
```

---

## 5. 多门验证器 $V$（§3.5）

### 5.1 输出结构

$$o_t = V(x, y_t) = (g_{\text{hack}}, g_{\text{comp}}, g_{\text{corr}}, \ell_{\text{lat}})$$

$g_* \in \{0, 1\}$ 三门布尔，$\ell_{\text{lat}} \in \mathbb{R}_+$。

### 5.2 feasibility 门

$$g_{\text{feas}}(o_t) \triangleq g_{\text{hack}} \wedge g_{\text{comp}} \wedge g_{\text{corr}}$$

### 5.3 Anti-Hacking（App B）

**Rule-based**（`config.yaml: anti_hack.rule_based`）：禁用 `torch.*`、`F.*` 等高层 API 在 `op_kernel/`；AST 检查；常量 tensor 返回检测。

**Model-based**：派发 `evo/agents/reviewer/AGENT.md` 做 LLM 审计（`prompt_mode: anti_hack_audit`）。

### 5.4 后端绑定

- **Compile** = `scoring/score.sh` 退出码 ∈ {0, 6} ⇒ $g_{\text{comp}}=1$
- **Correctness** = 退出码 ∈ {0, 6} ⇒ $g_{\text{corr}}=1$；5 则 0
- **Latency** = `evolution/scores/v{N}.json::performance_total`（退出码 0 或 6）

详见 `config.yaml: verifier.exit_code_map` 与 `docs/multi-gate-verification.md`。

---

## 6. 跨算子 Campaign（§4.2 transfer）

`campaign-orchestrator` 按 `config.yaml: operator_queue` 顺序消费算子。Memory Bank $\mathcal{M}$ **不随算子切换而清空**——L1 算子累积的 API 模板与经验直接作为 L2 算子的 $\mathcal{M}_0$ 扩展。

实证：论文 Table 2 L1→L2 stream 在 $t=17$ 即达 64% L2 correctness，显著高于 scratch 34%。

---

## 7. 终止条件

**Episode 级**（单算子）：
- Stage 1 budget 耗尽且无可行 → 记录失败，Stage 2 跳过（$P(x) = \emptyset$）
- Stage 2 budget 耗尽 → 记录最优 $b_T$

**Campaign 级**（跨算子）：operator_queue 全部消费完。

---

## 8. 超参默认值（取自论文 §4.1 + App）

| 符号 | 默认 | 来源 |
|------|------|------|
| $T$（per-op budget）| 30 | §4.1 |
| $N$（最终 context）| 10 | 合理推断（§3.2 Ablation §4.5 TopK） |
| $\lambda$（过检倍率）| 5 → K=50 | §4.5 Ablation "plateaus around K=50" |
| $\alpha$（Q 步长）| 0.1 | 通用 MC 默认 |
| $\varepsilon$ | 0.3 → 0.05 linear | ε-greedy 标配 |
| tolerance | atol=rtol=1e-2 | §4.1 |
| PopArt momentum | 0.99 | PopArt 原始论文 |
| Q clip | [-1, 1] | App A.2 boundedness |
