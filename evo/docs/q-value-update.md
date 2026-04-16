# Q-Value Update（Eq. 3 + App A）

## 更新规则（Eq. 3）

$$Q(s, m) \leftarrow Q(s, m) + \alpha \cdot \bigl(r - Q(s, m)\bigr)$$

其中：
- $Q(s, m)$：在状态 $s$ 下 memory item $m$ 的价值估计
- $\alpha$：步长（默认 0.1）
- $r$：该步实际获得的 reward（stage-specific）

这是标准的 **incremental Monte Carlo mean** 估计，等价于：

$$Q_{n+1} = (1 - \alpha) Q_n + \alpha R_n$$

## 应用范围（哪些 m 被更新）

| 阶段 | 更新对象 | reward 类型 |
|------|---------|-----------|
| Stage 1 | $c_t$ 里所有 context item 的 $Q_1$ | $r_{1,t} \in \{-1, +1\}$ |
| Stage 2 | **start point $p_t$** + $c_t$ 里所有 item 的 $Q_2$ | $\hat r_{2,t}$（PopArt 归一化后） |

**关键**：Stage 2 的 reward 是 **PopArt 归一化后** 的 $\hat r_{2,t}$，不是原始 $r_{2,t}$。

## Clip（App A.2）

论文证明在 bounded rewards 假设下 $Q$ 自然有界。但实现中我们显式 clip 到 $[-R_{\max}, R_{\max}]$：

```python
Q_new = clip(Q_new, config.q_update.q_clip)   # default [-1, 1]
```

理由：
- 保证数值稳定（防浮点漂移）
- Stage 2 的 $\hat r_{2,t}$ 经 PopArt 归一化后可能短时间超过 1（when stats 未稳定），clip 防止 Q 瞬间爆炸

## 有界性证明（App A.2 要点）

假设 reward $r \in [-R, R]$，$\alpha \in (0, 1)$，$Q_0 \in [-R, R]$：

$$|Q_{n+1}| = |(1-\alpha)Q_n + \alpha r| \le (1-\alpha)|Q_n| + \alpha|r| \le (1-\alpha)R + \alpha R = R$$

归纳得 $|Q_n| \le R$ 恒成立。

对 Stage 1：$R = 1$，直接有界。

对 Stage 2：$r_{2,t} \in [-1, 1]$（tanh 有界），但 PopArt 归一化后 $\hat r \in \mathbb{R}$——**这就是为什么我们需要 clip**。

## 收敛性证明（App A.3 要点）

假设：
1. 每个 $m$ 被访问无穷多次（ergodic）
2. 学习率满足 Robbins-Monro 条件：$\sum \alpha_n = \infty$, $\sum \alpha_n^2 < \infty$
3. Reward 的条件期望 $\mathbb{E}[R_n | s] = q^*(s, m)$ 存在且不变

则 $Q_n(s, m) \to q^*(s, m)$（a.s.）

**实践**：我们用常数 $\alpha = 0.1$（不满足 Robbins-Monro），但：
- 对 tracking non-stationary target（memory 在扩张）更合适
- 实证上 30 步内就能区分高/低价值 item（论文 §4.5 value-driven vs heuristic 的差异）

## α adaptive schedule(Item 4/P6)

CP-2 实测发现 6 步后 PopArt σ 几乎没变(0.986→0.971),固定 $\alpha=0.1$ 在 30 步预算下 Q 演化过慢。

**P6 引入 visit-count-adaptive α**:

$$
\alpha_{\text{eff}}(v) = \max\bigl(\alpha_{\text{floor}},\ \frac{\alpha_{\text{init}}}{1 + v}\bigr)
$$

其中 $v = \text{visit\_k}$(本次更新后的 visit 计数,Stage 1 用 visit_1,Stage 2 用 visit_2)。默认 $\alpha_{\text{init}}=0.3, \alpha_{\text{floor}}=0.05$。

| visit | $\alpha_{\text{eff}}$ | 语义 |
|---|---|---|
| 0 | 0.30 | 首次观测占 30% 权重(相当于 MC bootstrap;避免 Q=0 主宰 greedy) |
| 1 | 0.15 | 第二次观测快速调整 |
| 2 | 0.10 | 经典值,等价老模式 |
| 5 | 0.05 | 触底,保持对漂移敏感 |
| 20 | 0.05 | 触底 |

**与 R7 Q_2 bootstrap 的关系**:R7 是"新 feasible 条目直接 Q_2=r_norm"(一次性赋值,不走 TD),等价 MC n=1。α adaptive 是对**已有** experiential item 的 TD 更新曲线控制。两者正交互补。

**config 开关**:`q_update.alpha_mode: "visit_count_adaptive"`(默认,P6 启用)或 `"constant"`(回退旧行为,读 `alpha` 字段)。

**收敛性**:$\sum \alpha_n = \alpha_{\text{init}} \sum 1/(1+n)$ 在 floor 存在时发散(√),$\sum \alpha_n^2$ 收敛(√),Robbins-Monro 条件满足(若 floor → 0)。实际 floor=0.05 不严格满足 RM,但比固定 0.1 更接近。

## PopArt 归一化（Stage 2 专属）

$$\hat r_{2,t} = \frac{r_{2,t} - \mu_2}{\sigma_2}$$

### 在线更新（EMA，momentum $m$）

```
mu_new   = m * mu_old + (1-m) * r
delta    = r - mu_new
sigma²_new = m * sigma²_old + (1-m) * delta²
sigma_new  = max(sqrt(sigma²_new), epsilon)
```

默认 $m = 0.99$，$\epsilon = 10^{-8}$。

### 稳定性（App A.4）

PopArt 的经典证明：若 raw reward $r$ 分布有限方差，则 EMA $\mu_t, \sigma_t$ 收敛到 raw 分布的均值和方差，$\hat r$ 渐近标准正态。在 $\sigma^2 \to 0$ 的退化情形（raw reward 常数），$\epsilon$ 保证不除零。

### 为什么 Stage 1 不要 PopArt？

Stage 1 reward 已是 $\pm 1$，方差已知；归一化会扰乱二值信号（$+1$ 被 rescaled 到依赖过往分布的值，可能弱化 positive 信号）。

## 初始化

新 item 首次在 `bank.jsonl` 出现时：
- $Q_1 = Q_2 = $ `config.q_update.q_init`（默认 0.0）
- $\text{visit}_1 = \text{visit}_2 = 0$
- `last_updated_t = -1`（尚未更新）

首次 Q 更新才在 `q_values.json` 创建条目（lazy）。

## 调试与可观测性

### 查看 Top-K 高/低价值 items

```bash
# Q_1 top 5
jq -r 'to_entries | sort_by(.value.Q1) | reverse | .[0:5] |
       .[] | "\(.key) Q1=\(.value.Q1) v1=\(.value.visit_1)"' \
   evo/memory/q_values.json

# Q_2 bottom 5（反例，可能需从 retrieval 中逐步淘汰）
jq -r 'to_entries | sort_by(.value.Q2) | .[0:5] |
       .[] | "\(.key) Q2=\(.value.Q2) v2=\(.value.visit_2)"' \
   evo/memory/q_values.json
```

### 检查 Q 是否 clip 越界

```bash
jq 'to_entries | map(select(.value.Q1 < -1.01 or .value.Q1 > 1.01 or
                               .value.Q2 < -1.01 or .value.Q2 > 1.01))' \
   evo/memory/q_values.json
# 期望输出：[]
```

### PopArt stats 追踪

```bash
jq '.stage2' evo/memory/stats.json
# {"mu": 0.02, "sigma": 0.41, "n": 187, ...}
```

## 超参选择

| 超参 | 默认 | 调节原则 |
|------|------|---------|
| $\alpha$ | 0.1 | 更小（0.05）→ 平滑但学习慢；更大（0.3）→ 抖动但响应快。受 non-stationarity 影响大时偏大 |
| $Q_{\text{init}}$ | 0.0 | 设正值（e.g., 0.5）鼓励 optimistic exploration；负值惩罚新 item |
| Q clip | [-1, 1] | 匹配 reward 范围；PopArt 归一 reward 可能偶发超限，clip 是关键 |
| PopArt momentum | 0.99 | $\to 1$：mean/var 稳但适应慢；$\to 0$：响应快但抖动大 |

## 异常处理

- `q_values.json` 损坏（JSON 解析失败）：memory-curator 触发恢复——从最近 `q_values.{t}.json` 备份恢复（`config.logging.q_snapshot_every` 每 N 步备份）
- `stats.json` 损坏：重置为 `{mu: 0, sigma: 1, n: 0}`；前几步归一化会略偏但会很快 EMA 回正
- 内存爆炸（bank 过大）：当前版本不实现自动 GC；手动迁移到 `bank.archive.jsonl`
