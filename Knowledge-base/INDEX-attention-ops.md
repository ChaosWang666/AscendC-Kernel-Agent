# Attention 算子导航索引

基础路径：`Knowledge-base/coding-sources/ops-coding-sources/ops-transformer/attention/`

## Flash Attention 系列

| 算子 | 路径 | 说明 |
|------|------|------|
| flash_attention_score | `attention/flash_attention_score/` | Flash Attention 前向（apt 实现） |
| flash_attention_score_grad | `attention/flash_attention_score_grad/` | Flash Attention 反向 |
| prompt_flash_attention | `attention/prompt_flash_attention/` | Prompt 阶段 Flash Attention |
| incre_flash_attention | `attention/incre_flash_attention/` | 增量推理 Flash Attention |

## Sparse Attention 系列

| 算子 | 路径 | 说明 |
|------|------|------|
| sparse_flash_attention | `attention/sparse_flash_attention/` | 稀疏 Flash Attention |
| sparse_flash_attention_grad | `attention/sparse_flash_attention_grad/` | 稀疏 Flash Attention 反向 |
| block_sparse_attention | `attention/block_sparse_attention/` | 块稀疏 Attention |
| block_sparse_attention_grad | `attention/block_sparse_attention_grad/` | 块稀疏 Attention 反向 |
| kv_quant_sparse_flash_attention | `attention/kv_quant_sparse_flash_attention/` | KV 量化稀疏 Flash Attention |
| kv_quant_sparse_flash_attention_pioneer | `attention/kv_quant_sparse_flash_attention_pioneer/` | KV 量化稀疏先锋版 |

## MLA (Multi-head Latent Attention) 系列

| 算子 | 路径 | 说明 |
|------|------|------|
| mla_preprocess | `attention/mla_preprocess/` | MLA 预处理 |
| mla_preprocess_v2 | `attention/mla_preprocess_v2/` | MLA 预处理 v2 |
| mla_prolog | `attention/mla_prolog/` | MLA 序章 |
| mla_prolog_v2 | `attention/mla_prolog_v2/` | MLA 序章 v2 |
| mla_prolog_v3 | `attention/mla_prolog_v3/` | MLA 序章 v3 |

## NSA (Native Sparse Attention) 系列

| 算子 | 路径 | 说明 |
|------|------|------|
| nsa_compress | `attention/nsa_compress/` | NSA 压缩 |
| nsa_compress_attention | `attention/nsa_compress_attention/` | NSA 压缩 Attention |
| nsa_compress_attention_infer | `attention/nsa_compress_attention_infer/` | NSA 压缩推理 |
| nsa_compress_grad | `attention/nsa_compress_grad/` | NSA 压缩反向 |
| nsa_compress_with_cache | `attention/nsa_compress_with_cache/` | NSA 压缩 + 缓存 |
| nsa_selected_attention | `attention/nsa_selected_attention/` | NSA 选择性 Attention |
| nsa_selected_attention_grad | `attention/nsa_selected_attention_grad/` | NSA 选择性反向 |
| nsa_selected_attention_infer | `attention/nsa_selected_attention_infer/` | NSA 选择性推理 |

## Lightning Indexer 系列

| 算子 | 路径 | 说明 |
|------|------|------|
| lightning_indexer | `attention/lightning_indexer/` | Lightning Indexer |
| lightning_indexer_grad | `attention/lightning_indexer_grad/` | Lightning Indexer 反向 |
| quant_lightning_indexer | `attention/quant_lightning_indexer/` | 量化 Lightning Indexer |
| dense_lightning_indexer_grad_kl_loss | `attention/dense_lightning_indexer_grad_kl_loss/` | 稠密 Lightning KL Loss 反向 |
| dense_lightning_indexer_softmax_lse | `attention/dense_lightning_indexer_softmax_lse/` | 稠密 Lightning Softmax LSE |
| sparse_lightning_indexer_grad_kl_loss | `attention/sparse_lightning_indexer_grad_kl_loss/` | 稀疏 Lightning KL Loss 反向 |

## KV Cache 管理

| 算子 | 路径 | 说明 |
|------|------|------|
| gather_pa_kv_cache | `attention/gather_pa_kv_cache/` | PagedAttention KV Cache 聚集 |
| scatter_pa_cache | `attention/scatter_pa_cache/` | PagedAttention Cache 散射 |
| scatter_pa_kv_cache | `attention/scatter_pa_kv_cache/` | PagedAttention KV Cache 散射 |

## 其他 Attention 变体

| 算子 | 路径 | 说明 |
|------|------|------|
| attention_pioneer | `attention/attention_pioneer/` | Attention 先锋实现 |
| attention_update | `attention/attention_update/` | Attention 更新 |
| attention_worker_combine | `attention/attention_worker_combine/` | Worker Combine |
| attention_worker_scheduler | `attention/attention_worker_scheduler/` | Worker 调度 |
| chunk_gated_delta_rule | `attention/chunk_gated_delta_rule/` | 分块门控 Delta Rule |
| fused_causal_conv1d | `attention/fused_causal_conv1d/` | 融合因果 Conv1D |
| fused_floyd_attention | `attention/fused_floyd_attention/` | 融合 Floyd Attention |
| fused_floyd_attention_grad | `attention/fused_floyd_attention_grad/` | 融合 Floyd Attention 反向 |
| fused_infer_attention_score | `attention/fused_infer_attention_score/` | 融合推理 Attention Score |
| rain_fusion_attention | `attention/rain_fusion_attention/` | Rain 融合 Attention |
| recurrent_gated_delta_rule | `attention/recurrent_gated_delta_rule/` | 循环门控 Delta Rule |
| ring_attention_update | `attention/ring_attention_update/` | Ring Attention 更新 |
| swin_attention_score_quant | `attention/swin_attention_score_quant/` | Swin Attention 量化 |

## 公共模块

| 路径 | 说明 |
|------|------|
| `attention/common/` | Attention 公共工具函数 |
| `experimental/attention/` | 实验性 Attention 实现 |

## 目录结构模式

每个算子目录通常包含：
```
{op_name}/
  op_host/          # Host 侧逻辑（Tiling、Shape 推导）
  op_kernel/        # Kernel 侧代码（.asc 内核实现）
  tests/            # 测试用例
  docs/             # 文档
  examples/         # 使用示例
  CMakeLists.txt    # 构建配置
```
