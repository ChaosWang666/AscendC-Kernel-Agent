# Ascend C 文档知识库索引

本目录包含 3 份华为官方大型文档，按 N.M 章节级别拆分为 84 个 section 文件存放在 `sections/`。

## 文档构成

| 原文档 | 行数 | 主题 | Section 前缀 | 拆分文件数 |
|--------|------|------|--------------|-----------|
| `算子开发指南.md` | 22,293 | Ascend C 编程指南（入门/编程/实践）| `guide_*` | 21 |
| `算子开发工具.md` | 11,527 | msKPP/msOpGen/msOpST/msSanitizer/msDebug/msProf | `tools_*` | 54 |
| `算子开发指南2.md` | 3,474 | 混合算子性能优化 + 优秀实践案例 | `guide2_*` | 9 |

---

## 使用方式（给 Agent 的说明）

1. **先查本 INDEX**：根据关键词（如 "Tiling"、"msProf"、"双缓冲"）定位章节
2. **然后 Read 单独的 section 文件**：每个文件独立，通常 100-2000 行，可整体 load
3. **需要多文件时**：多个 Read 并行请求
4. **勿 Read 原始大文档**（22K 行），太大

---

## 按文档章节索引

### A. `guide_*` — Ascend C 算子开发指南（CANN 9.0.0-beta2）

#### 入门教程
- `guide_1.1_什么是_Ascend_C.md` — Ascend C 编程模型概述
- `guide_1.2_环境准备.md` — CANN Toolkit 安装、环境变量
- `guide_1.3_快速入门.md` — SIMD/SIMT 快速入门（HelloWorld、Add 算子开发）

#### 编程指南（核心）
- `guide_2.1_本文档组织结构.md`
- `guide_2.2_编程模型.md` — **异构并行编程模型**、SIMD/SIMT、核函数、Tensor、TPipe/TQue、MicroAPI
- `guide_2.3_编译与运行.md` — 编译工具链、Kernel 直调、aclnn 调用
- `guide_2.4_语言扩展层.md` — C API
- `guide_2.5_C_类库_API.md` — **LocalTensor/GlobalTensor/TPipe/TQue API**
- `guide_2.6_硬件实现.md` — Cube/Vector/Scalar 单元、UB/L1/L0 层级
- `guide_2.7_调试调优.md` — 调试工具链入口
- `guide_2.8_兼容性指南.md` — 跨架构迁移
- `guide_2.9_概念原理和术语.md` — 术语表
- `guide_2.10_附录.md`

#### 算子实践参考
- `guide_3.1_本文档组织结构.md`
- `guide_3.2_异构计算.md` — Host-Device 协同
- `guide_3.3_SIMD_算子实现.md` — SIMD 标准范式
- `guide_3.4_SIMT_算子实现.md` — SIMT 范式
- `guide_3.5_SIMD_与_SIMT_混合算子实现.md`
- `guide_3.6_功能调试.md` — 仿真 / 上板调试
- `guide_3.7_性能分析.md` — 性能瓶颈分析方法
- `guide_3.8_SIMD_算子性能优化.md` — **性能优化技术**（核心参考）

### B. `tools_*` — 算子开发工具（CANN 8.2.RC1）

#### msKPP（算子设计工具）
- `tools_3.1_工具概述.md`
- `tools_3.2_使用前准备.md`
- `tools_3.3_性能建模.md` — **原理概述、算子特性建模、极限性能分析**
- `tools_3.4_调用_msOpGen_算子工程.md`
- `tools_3.5_自动调优.md`
- `tools_3.6_FAQ.md`

#### msOpGen（算子工程生成）
- `tools_4.1_工具概述.md`
- `tools_4.3_创建算子工程.md` — **msopgen gen 完整流程**
- `tools_4.4_算子开发.md`
- `tools_4.5_算子编译部署.md` — build.sh / CMakePresets
- `tools_4.6_查看算子仿真流水图.md`
- `tools_4.7_典型案例.md`

#### msOpST（算子系统测试）
- `tools_5.1_工具概述.md`
- `tools_5.2_使用前准备.md`
- `tools_5.3_生成测试用例定义文件.md` — **测试用例生成**
- `tools_5.4_生成_执行测试用例.md`
- `tools_5.5_生成单算子上板测试框架.md`
- `tools_5.6_典型案例.md`

#### msSanitizer（异常检测）
- `tools_6.1_工具概述.md`
- `tools_6.2_使用前准备.md`
- `tools_6.3_内存检测.md` — **越界/野指针检测**
- `tools_6.4_竞争检测.md` — **race condition**
- `tools_6.5_未初始化检测.md`
- `tools_6.6_典型案例.md`
- `tools_6.7_FAQ.md`
- `tools_6.8_对外接口使用说明.md`

#### msDebug（算子调试）
- `tools_7.1_工具概述.md`
- `tools_7.2_使用前准备.md`
- `tools_7.3_指定_Device_ID_通算融合算子场景.md`
- `tools_7.4_断点设置.md` — **核断点**
- `tools_7.5_内存与变量打印.md`
- `tools_7.6_单步调试.md`
- `tools_7.7_中断运行.md`
- `tools_7.8_核切换.md`
- `tools_7.9_读取寄存器.md`
- `tools_7.10_调试信息展示.md`
- `tools_7.11_解析异常算子_dump_文件.md` — **dump 分析**
- `tools_7.12_典型案例.md`
- `tools_7.13_FAQ.md`

#### msProf（性能调优） ⭐️ 核心
- `tools_8.1_工具概述.md`
- `tools_8.2_使用前准备.md`
- `tools_8.3_工具使用.md` — **msprof op 命令完整参考**
- `tools_8.4_计算内存热力图.md` — **UB 访问热点**
- `tools_8.5_Roofline_瓶颈分析图.md` — **识别瓶颈类型**
- `tools_8.6_Cache_热力图.md` — L2 cache 分析
- `tools_8.7_通算流水图.md`
- `tools_8.8_指令流水图.md`
- `tools_8.9_算子代码热点图.md`
- `tools_8.10_内存通路吞吐率波形图.md`
- `tools_8.11_性能数据文件.md` — **8 个 CSV 详解**
- `tools_8.12_Json_配置文件说明.md`
- `tools_8.13_典型案例.md` — **调优案例集**
- `tools_8.14_扩展接口_mstx.md`

#### 附录
- `tools_9.1_TBE_AI_CPU_算子开发场景.md`

### C. `guide2_*` — 补充：混合算子 + 优秀实践

#### SIMD 与 SIMT 混合算子
- `guide2_3.9.1_内存访问.md` — **UB 内存访问优化**
- `guide2_3.9.2_计算优化.md` — **SIMT 分支判断**

#### 优秀实践（真实案例 ⭐️⭐️）
- `guide2_3.10.1_FlashAttention_算子性能调优案例.md` — **完整调优流程**
- `guide2_3.10.2_GroupedMatmul_算子性能调优案例.md`
- `guide2_3.10.3_MC²算子性能调优案例.md`
- `guide2_3.10.4_Matmul_性能调优案例.md` — **14 个子案例（tiling/tiling常量化/L2切分/多核切K/NBuffer33/IBShare/MTE2 Preload 等）**

#### 兼容性迁移
- `guide2_4.1_兼容性说明.md`
- `guide2_4.2.1_220x_到_351x_架构变更.md`
- `guide2_4.2.2_220x_迁移_351x_指导.md`

---

## 按主题反向索引 ⭐️

### Tiling 设计相关
- 基础：`guide_2.2_编程模型.md`、`guide_3.3_SIMD_算子实现.md`
- 性能建模：`tools_3.3_性能建模.md`（极限性能分析、tiling 初步设计）
- 优化案例：`guide_3.8_SIMD_算子性能优化.md`、`guide2_3.10.4_Matmul_性能调优案例.md`
- UB 切分：`guide2_3.9.1_内存访问.md`

### Buffer/UB 管理
- API：`guide_2.5_C_类库_API.md`
- 硬件：`guide_2.6_硬件实现.md`
- Cache/热力图：`tools_8.4_计算内存热力图.md`、`tools_8.6_Cache_热力图.md`

### Double Buffer / Pipeline
- 编程模型：`guide_2.2_编程模型.md`
- 案例：`guide2_3.10.1_FlashAttention_算子性能调优案例.md`

### 性能分析（profiling）
- 工具使用：`tools_8.3_工具使用.md`
- Roofline：`tools_8.5_Roofline_瓶颈分析图.md`
- CSV 字段：`tools_8.11_性能数据文件.md`
- 案例：`tools_8.13_典型案例.md`

### 调试（异常/崩溃/精度）
- 异常检测：`tools_6.3_内存检测.md`、`tools_6.4_竞争检测.md`、`tools_6.5_未初始化检测.md`
- 断点调试：`tools_7.4_断点设置.md`、`tools_7.5_内存与变量打印.md`
- Dump 分析：`tools_7.11_解析异常算子_dump_文件.md`

### 测试（ST/UT）
- msOpST 测试用例生成：`tools_5.3_生成测试用例定义文件.md`、`tools_5.4_生成_执行测试用例.md`

### 算子工程（msopgen 流程）
- 创建：`tools_4.3_创建算子工程.md`
- 编译：`tools_4.5_算子编译部署.md`

### FlashAttention / MatMul / Transformer 类
- FA 调优：`guide2_3.10.1_FlashAttention_算子性能调优案例.md`
- MatMul 14 子案例：`guide2_3.10.4_Matmul_性能调优案例.md`（tiling/L2/NBuffer/IBShare/MTE2 Preload）
- GroupedMatmul：`guide2_3.10.2_GroupedMatmul_算子性能调优案例.md`
- MC²：`guide2_3.10.3_MC²算子性能调优案例.md`

### SIMT 编程
- 入门：`guide_1.3_快速入门.md`（含 SIMT Add 算子）
- 实现：`guide_3.4_SIMT_算子实现.md`
- 混合：`guide_3.5_SIMD_与_SIMT_混合算子实现.md`
- 分支：`guide2_3.9.2_计算优化.md`

### 架构迁移
- 351x：`guide2_4.2.1_220x_到_351x_架构变更.md`、`guide2_4.2.2_220x_迁移_351x_指导.md`
- 指南：`guide_2.8_兼容性指南.md`

---

## 工具链映射

| 工具 | 职责 | 主要章节 |
|------|------|---------|
| **msOpGen** | 算子工程生成 | `tools_4.*` |
| **msKPP** | 算子设计 + 性能建模 | `tools_3.*` |
| **msOpST** | 系统测试（ST）用例生成 | `tools_5.*` |
| **msSanitizer** | 异常检测（内存/竞争/未初始化）| `tools_6.*` |
| **msDebug** | 运行时调试（断点/单步/dump）| `tools_7.*` |
| **msProf** | 性能采集与调优 | `tools_8.*` |

---

## 与现有知识库的关系

| 层级 | 位置 | 用途 |
|------|------|------|
| L1 - Skills | `.claude/skills/` | Claude Code 自动加载的触发式指南（简短、决策树）|
| L2 - Sources | `Knowledge-base/coding-sources/` | 参考实现代码（算子源码、SDK 示例）|
| **L3 - Docs** | **`Knowledge-base/coding-skills/docs/sections/` ⬅ 本索引** | **华为官方深度文档（原理、API、工具链）**|

**使用顺序**：Skill（决策） → Docs（原理） → Sources（代码范式）
