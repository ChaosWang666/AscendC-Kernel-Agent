---
name: ascendc-kb-docs
description: Ascend C 官方深度文档查询技能。访问 `Knowledge-base/coding-skills/docs/` 下的 84 个章节级文件（拆自 3 份华为官方大型文档），覆盖编程模型、API、Tiling、msKPP/msOpGen/msOpST/msSanitizer/msDebug/msProf 工具链、FlashAttention/MatMul 优秀实践。触发：查阅算子原理细节、工具链使用（msProf 等）、Ascend C API 完整规格、CANN 官方指南、性能调优案例（FlashAttention/Matmul 等）。
---

# Ascend C Knowledge Base Docs (KB Docs) 查询技能

## 何时使用本 Skill

当你需要查询以下内容时触发：

- **Ascend C 编程原理**：编程模型、TPipe/TQue/LocalTensor/GlobalTensor API、硬件层级
- **算子工具链使用**：msProf（性能分析）、msSanitizer（异常检测）、msDebug（调试）、msOpGen（工程生成）、msKPP（性能建模）、msOpST（测试）
- **性能调优案例**：FlashAttention、Matmul（14 个子案例）、GroupedMatmul、MC²
- **Tiling 深度资料**：极限性能分析、tiling 初步设计、切分策略
- **架构迁移**：220x → 351x
- Skill 其他子技能（ascendc-tiling-design、ops-profiling 等）**已经决策完方向**，但需要**官方原理和深度文档**作为进一步佐证或实现细节

## 核心结构

```
Knowledge-base/coding-skills/docs/
├── INDEX.md                    ⬅ 第一入口：按章节 + 按主题反向索引
├── sections/                   ⬅ 84 个章节级文件（100-2000 行）
│   ├── guide_1.*.md            入门教程
│   ├── guide_2.*.md            编程指南（核心）
│   ├── guide_3.*.md            算子实践参考
│   ├── tools_3.*.md            msKPP
│   ├── tools_4.*.md            msOpGen
│   ├── tools_5.*.md            msOpST
│   ├── tools_6.*.md            msSanitizer
│   ├── tools_7.*.md            msDebug
│   ├── tools_8.*.md            msProf ⭐
│   ├── guide2_3.9.*.md         混合算子优化
│   └── guide2_3.10.*.md        优秀实践案例（FlashAttention, Matmul）
└── 算子开发*.md                 原始 3 个大文件（不要直接 Read）
```

## 使用流程

### Step 1: 先 Read INDEX.md

```
Read: Knowledge-base/coding-skills/docs/INDEX.md
```

INDEX.md 提供两种视图：
- **按文档章节**：guide_1.x → guide_2.x → guide_3.x → tools_3-9.x → guide2_*
- **按主题反向索引**：Tiling / Buffer / Pipeline / Profiling / 调试 / 测试 / 迁移 等

### Step 2: 按关键词定位到 section 文件

**示例查询**：

| 关键词 | 优先 Read 的 section |
|--------|---------------------|
| "Tiling 策略" | `tools_3.3_性能建模.md`（极限性能分析）|
| "msProf 使用" | `tools_8.3_工具使用.md` + `tools_8.11_性能数据文件.md` |
| "TPipe/TQue API" | `guide_2.2_编程模型.md` + `guide_2.5_C_类库_API.md` |
| "UB 内存访问优化" | `guide2_3.9.1_内存访问.md` |
| "FlashAttention 调优" | `guide2_3.10.1_FlashAttention_算子性能调优案例.md` |
| "Matmul 性能" | `guide2_3.10.4_Matmul_性能调优案例.md`（14 个子案例）|
| "内存越界检测" | `tools_6.3_内存检测.md` |
| "Roofline 分析" | `tools_8.5_Roofline_瓶颈分析图.md` |
| "SIMT 编程" | `guide_3.4_SIMT_算子实现.md` + `guide_1.3_快速入门.md` |
| "msopgen 工程生成" | `tools_4.3_创建算子工程.md` |

### Step 3: Read 单独的 section 文件（或多个并行 Read）

```
Read: Knowledge-base/coding-skills/docs/sections/tools_8.3_工具使用.md
```

每个 section 文件 100-2000 行，可整体 load 到上下文。**禁止** Read 原始大文件（22K+ 行）。

## 与其他 Skill 的协同

| 相关 Skill | 在本 Skill 中的对应章节 |
|-----------|----------------------|
| `ascendc-tiling-design` | `guide_2.2`, `guide_3.3`, `guide_3.8`, `tools_3.3` |
| `ascendc-api-best-practices` | `guide_2.5`（C API 完整参考）|
| `ops-profiling` | `tools_8.*`（**msProf 完整手册**）|
| `ascendc-runtime-debug` | `tools_6.*`（msSanitizer）+ `tools_7.*`（msDebug）|
| `ascendc-st-design` | `tools_5.*`（msOpST 测试用例生成）|
| `ascendc-msopgen-workflow` | `tools_4.*`（msOpGen 完整流程）|
| `ascendc-npu-arch` | `guide_2.6_硬件实现.md`、`guide2_4.2.*` |

## 在 AVO 框架中的使用

本 skill 是 AVO 框架的**深度知识层**：

1. **Architect** 的 Step 2.5 KNOWLEDGE RETRIEVAL **必须**查询本 skill
   - 从 INDEX.md 找到至少 1 个相关 section
   - 在 DESIGN.md 的"知识检索结果"节引用该 section
2. **Developer** 实现前可查阅对应 API/工具使用章节
3. **Reviewer** 审查 DESIGN.md 时验证是否引用了本 skill 的 section
4. **Tester** 解读 profiling 结果时查阅 `tools_8.*`

## 示例：完整查询流程

**场景**：Architect 需要为 FlashAttention 算子设计 tiling 策略

1. Read `INDEX.md` → 在反向索引"FlashAttention / MatMul"找到 `guide2_3.10.1`
2. Read `sections/guide2_3.10.1_FlashAttention_算子性能调优案例.md` → 获取完整调优流程
3. 在 DESIGN.md 添加：
   ```
   ## 知识检索结果
   - 参考: sections/guide2_3.10.1_FlashAttention_算子性能调优案例.md
   - 关键发现: tiling 基本块调整 + CV 流水并行 + 核间负载均衡
   ```

## 关键约束

- ❌ **禁止 Read 原始大文档**（`算子开发指南.md` 等 > 10K 行，无法整体 load）
- ✅ **优先 Read INDEX.md**，再查 sections/
- ✅ **多个相关 section 并行 Read**（单消息多 Read 调用）
- ✅ **DESIGN.md 必须显式引用**本 skill 的某个 section（至少 1 个）

---

**维护说明**：若 `Knowledge-base/coding-skills/docs/` 下新增文档，请重跑 `/tmp/split_docs.py` 并更新 INDEX.md。
