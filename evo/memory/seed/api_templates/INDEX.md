# Ascend C API 模板种子索引

> 本文件为 $\mathcal{M}_0$ 的 API 模板种子清单。memory-curator 首次 bootstrap 时扫描这里的条目，把每条
> 转成 bank.jsonl 的 `type: "api_template"` 记录，`content` 由 Target 指向的文件片段填充。

**Backend**：ascend_c（当前唯一支持后端；CUDA / mHC 待 v2）

## 数据搬运类（Memory Ops）

| 名称 | Target（相对仓库根）| tags |
|------|-------------------|------|
| DataCopy UB↔GM | `Knowledge-base/coding-skills/docs/sections/guide_2.2_编程模型.md` | [data_copy, ub, gm, alignment_32b] |
| SetAtomicAdd / SetAtomicNone | `Knowledge-base/coding-skills/docs/sections/guide_2.2_编程模型.md` | [atomic, reduce_write] |
| BarrierMode 与 PipeBarrier | `Knowledge-base/coding-skills/docs/sections/guide_2.2_编程模型.md` | [pipe_barrier, sync] |

## 队列同步类（Queue Ops）

| 名称 | Target | tags |
|------|--------|------|
| EnQue / DeQue with TQue | `Knowledge-base/coding-skills/docs/sections/guide_2.2_编程模型.md` | [enque, deque, pipeline, double_buffer] |
| AllocTensor / FreeTensor | `Knowledge-base/coding-skills/docs/sections/guide_2.2_编程模型.md` | [tensor_alloc, ub_mgmt] |

## 计算类（Compute Ops）

| 名称 | Target | tags |
|------|--------|------|
| Vector binary (Add/Sub/Mul/Div) | `Knowledge-base/coding-skills/docs/sections/guide_3.8_SIMD_算子性能优化.md` | [vec_binary, elementwise] |
| Vector unary (Exp/Log/Sqrt/Gelu) | `Knowledge-base/coding-skills/docs/sections/guide_3.8_SIMD_算子性能优化.md` | [vec_unary, elementwise] |
| Scalar-Vector (Adds/Muls) | `Knowledge-base/coding-skills/docs/sections/guide_3.8_SIMD_算子性能优化.md` | [scalar, elementwise, opt] |
| Reduce (WholeReduceSum/Max/Min) | `Knowledge-base/coding-skills/docs/sections/guide_3.8_SIMD_算子性能优化.md` | [reduction, whole_reduce] |
| Cast 类型转换 | `Knowledge-base/coding-skills/docs/sections/guide_3.8_SIMD_算子性能优化.md` | [cast, fp16_fp32] |
| Matmul（MatmulImpl）| `Knowledge-base/coding-skills/docs/sections/guide2_3.10.1_FlashAttention_算子性能调优案例.md` | [matmul, cube] |

## Tiling 类（Host-side）

| 名称 | Target | tags |
|------|--------|------|
| TilingFunc 骨架 | `Knowledge-base/coding-skills/docs/sections/guide_2.2_编程模型.md` | [tiling, op_host] |
| SetBlockDim / core 分发 | `Knowledge-base/coding-skills/docs/sections/guide_2.2_编程模型.md` | [multi_core, block_dim] |
| SetUsrWorkspace | `Knowledge-base/coding-skills/docs/sections/guide_2.2_编程模型.md` | [workspace] |

## 格式（memory-curator bootstrap 读取方式）

bootstrap 时执行：

```python
for row in parse_markdown_table(this_file):
    target_path = row["Target"]
    tags = row["tags"]
    name = row["名称"]
    # 从 target_path 截取相关片段（未来可扩展；v1 读取整节作为 content）
    content = extract_section(target_path, name)
    append_bank({
        "id": uuid4(),
        "type": "api_template",
        "operator": None,
        "stage_when_added": 0,                  # 0 = seed
        "content": content,
        "meta": {
            "source": "seed",
            "backend": "ascend_c",
            "tags": tags,
            "target_path": target_path,
            "name": name
        },
        "created_at": now()
    })
```

## 扩展

用户可以：
1. 追加新行（新 API 模板）——memory-curator 下次 bootstrap 会吸纳
2. 改 Target 到更精准的 section 文件（当前大多指向 2.2 / 3.8 两节）
3. 添加新的 tag（只要 tag 命名空间统一）

## 与 AVO Knowledge-base 的关系

本索引 **不复制** Knowledge-base 的内容，仅登记 **指针**。每次检索时实际 content 从 target_path 读取，保证：
- 知识库更新 → EVO 自动受益
- 不重复占用仓库空间
