# Ascend C Kernel 最佳实践（$\mathcal{M}_0$ 种子）

> 本文件为 `type: "best_practice"` 的种子内容，来自仓库 `ascendc-*` skills 精华 + AVO 历次进化（特别是 gelu_custom 15 轮）总结。memory-curator bootstrap 时会把每个 `## ` 节（二级标题）作为一条独立 best_practice 条目入库。

---

## Tiling：多核切分优先于 UB 切分

**Why**：NPU 核间并行 ROI 比单核内 UB 循环更高。Ascend910B 共 24–40 AI Cores（按 platform 不同），多核分发是首要并行化手段。

**How**：
- 在 TilingFunc 里计算 `coreNum`，调 `SetBlockDim(coreNum)`
- 按 batch × total_elements 粒度均分，小算子允许 < coreNum 核
- 复用 `GetBlockIdx()` 在 kernel 里区分自己核的 offset 和 length

**tags**: [tiling, multi_core, block_dim]

---

## Double Buffer：默认 BUFFER_NUM = 2

**Why**：一块 UB 在 DataCopy（GM→UB），另一块在 Compute，管线重叠。BUFFER_NUM=1 丢失 pipeline；BUFFER_NUM=4 把 UB tile 压得太小，tile effect 下降。

**How**：
```cpp
constexpr int32_t BUFFER_NUM = 2;
TPipe pipe;
TQue<QuePosition::VECIN, BUFFER_NUM> inQueue;
TQue<QuePosition::VECOUT, BUFFER_NUM> outQueue;
pipe.InitBuffer(inQueue, BUFFER_NUM, tileLength * sizeof(float));
```

**AVO gelu_custom 实证**：BUFFER_NUM ∈ {1, 4} 都回归，2 是 sweet spot。

**tags**: [double_buffer, pipeline, ub_mgmt]

---

## UB 分配：预留 RESERVE 给中间变量

**Why**：Vec compute（如 Exp/Gelu 近似）需要 tmpBuffer 做中间 tensor；如果全部 UB 都切给 I/O 队列，中间计算会把栈溢出或跳 tile。

**How**：
- RESERVE_BYTES 留 8–12 KB（gelu_custom 最优 12KB，8KB 也行）
- tileLength = (UB_SIZE - RESERVE) / (BUFFER_NUM × 2 × sizeof(dtype))

**tags**: [ub_slack, reserve_bytes, tile]

---

## Scalar 优化：用 Adds / Muls 代替 Duplicate

**Why**：`Duplicate(tmp, c); Add(dst, src, tmp, n);` 多一次 UB 写回 + 读取；`Adds(dst, src, c, n);` 直通 scalar register，少一次 DMA。

**How**：所有与常数相加/相乘的场景优先用 `Adds` / `Muls` / `Subs` / `Divs` 系列。

**tags**: [scalar_opt, vec_unary, micro_opt]

---

## Tile 大小优先 2 的幂

**Why**：Ascend C 的 SIMD 粒度（32B / 256B）对齐 2 的幂；8192 fp32 / 16384 fp16 是 gelu 这类 elementwise 的经验值。非 2 幂 tile（如 12032）eliminates UB slack margin，且对齐开销上升。

**How**：TilingFunc 里对齐 tile 到 `tileLength = AlignUp(raw, BLOCK_ALIGN_ELEMENTS)`，其中 BLOCK_ALIGN_ELEMENTS = 8（fp32） / 16（fp16）。

**tags**: [tile_pow2, alignment, elementwise]

---

## 精度：FP16 计算走 FP32 中间路径

**Why**：FP16 的 Exp/Log/Gelu 近似误差易超 1e-3 atol；先 Cast 到 FP32 计算，再 Cast 回 FP16 可把精度 offset 保持在 tolerance 内。

**How**：
```cpp
Cast(src_fp32, src_fp16, RoundMode::CAST_NONE, tileLength);
Exp(tmp, src_fp32, tileLength);         // FP32 计算
Cast(dst_fp16, tmp, RoundMode::CAST_ROUND, tileLength);
```

**Trade-off**：额外两次 Cast + 2× UB 占用；但必要时不可省。

**tags**: [precision, fp16, cast]

---

## Pipeline 同步：优先 EnQue/DeQue，慎用 PipeBarrier

**Why**：`EnQue/DeQue` 是 fine-grained event；`PipeBarrier<PIPE_ALL>` 全管线停摆，除非必须否则显著损失 overlap。

**How**：
- CopyIn → EnQue(inQueue)；Compute 前 DeQue(inQueue)
- Compute → EnQue(outQueue)；CopyOut 前 DeQue(outQueue)
- 仅在跨迭代依赖（如 atomic reduce）用 PipeBarrier<PIPE_V>

**tags**: [sync, enque, deque, pipe_barrier]

---

## 编译 Hint：AIV_ONLY / AIC_ONLY 按需

**Why**：`AIV_ONLY` 告诉编译器 kernel 只用 Vector Core 不用 Cube Core，适合 pure vector op（如 gelu）。但对 cross-core 混合 op 反而会损失调度灵活性。

**How**：在 op_host 的 OpDef 里：
```cpp
.AddConfig("ascend910b", ge::AscendQuantType::ASCEND_QUANT_NONE, true,
            1, ge::CUBE_OR_VECTOR_ONLY::AIV_ONLY)  // 仅 vec
```

**AVO gelu_custom 实证**：FP16 场景下 AIV_ONLY 反而劣化（可能 scheduler bias），慎用。

**tags**: [compile_hint, aiv_only]

---

## 测试：paired A/B 优于单次对比

**Why**：NPU 性能测量有 ±5μs 级别的系统抖动（cache、BW 拥塞）。单次跑 A vs 单次跑 B 可能 A 赢仅靠运气。

**How**：同一 attempt 重复 5 次取均值 / 中位；两组候选交替运行（A, B, A, B, A, B, ...）消除 trend。scoring/score.sh 已支持（num_correct_trials × warmup_rounds × repeat_rounds）。

**tags**: [performance, measurement, variance]

---

## Anti-Hacking：op_kernel 严格纯 C++

**Why**：op_kernel/*.cpp 跑在 NPU device 上，**不能** include torch / numpy / Python 任何 API。这既是技术约束（device 没有 Python runtime）也是 EVO 防作弊第一道门。

**How**：
- 只 `#include "kernel_operator.h"`
- 所有计算通过 AscendC namespace 的 API
- 若需要 fallback 到 host，走 op_host（不走 kernel）

**tags**: [anti_hack, op_kernel, constraints]

## 多 socVersion 注册：显式 AddConfig 覆盖本机芯片

**Why**：msopgen 默认命令 `msopgen gen -c ai_core-Ascend910B ...` 只生成注册 `ascend910b` 的 op_host 模板。**但本机 Ascend910 NPU 的 socVersion 实际可能是 `ascend910_93`（A3 芯片代际，DAV_2201/DAV_3002）**,aclnn 运行时找不到匹配注册,直接报 `socVersion [ascend910_93] does not support opType [OpName]` → score.sh correctness 阶段 exit_code=5。

首次 Drafting 如果遇到 `correctness: aclnnXxx unsupported on socVersion ascend910_93`,这是**环境注册不匹配**,不是算子逻辑错。

**How**：op_host/{op_name}_custom.cpp 的 `OpDef` 注册段落必须显式枚举本机所有可能 socVersion:

```cpp
// op_host/{op_name}_custom.cpp — OpDef 注册尾部
this->AICore()
    .SetTiling(optiling::TilingFunc)
    .AddConfig("ascend910b")
    .AddConfig("ascend910_93");   // ← A3 芯片;漏写导致 aclnn 查不到 kernel
```

同步更新 `CMakePresets.json`:

```json
{
  "cacheVariables": {
    "ASCEND_COMPUTE_UNIT": { "type": "STRING", "value": "ascend910b;ascend910_93" }
  }
}
```

首次运行前 `npu-smi info` 确认本机 Chip Name(看 `Chip:Phy-ID` 行);或直接 AddConfig 两个都带上成本极低,建议统一默认双注册。

**tags**: [msopgen, socversion, ascend910_93, op_registration, gotcha]
