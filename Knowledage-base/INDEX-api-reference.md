# API 文档导航索引

## 文档总览

基础路径：`Knowledage-base/coding-sources/programming-coding-sources/asc-devkit/docs/`

| 目录 | 文件数 | 说明 |
|------|--------|------|
| `api/context/` | 1711 | API 详细参考（权威来源） |
| `api/README.md` | 1 | API 总索引 |
| `guide/` | 220 | 编程指南与教程 |
| 根目录 | 6 | 快速入门与 API 选择指南 |

## 快速入口

| 文件 | 用途 |
|------|------|
| `docs/quick_start.md` | 快速入门 |
| `docs/asc_how_to_choose_api.md` | 如何选择 API（SIMD C++ / SIMD C / SIMT） |
| `docs/asc_adv_api_contributing.md` | 高级 API 指南 |
| `docs/asc_basic_api_contributing.md` | 基础 API 指南 |
| `docs/asc_c_api_contributing.md` | C API 指南 |
| `docs/api/README.md` | API 完整索引 |

## 编程指南分类

路径前缀：`docs/guide/`

### 入门教程
- `guide/入门教程/快速入门/` — 从零开始

### 编程指南（核心）
- `guide/编程指南/概念原理和术语/` — 基本概念
- `guide/编程指南/编程模型/` — 编程模型
- `guide/编程指南/硬件实现/` — 硬件架构说明
- `guide/编程指南/语言扩展层/` — Ascend C 语言扩展
- `guide/编程指南/C++类库API/` — C++ 类库 API 详解
- `guide/编程指南/编译与运行/` — 编译和运行
- `guide/编程指南/调试调优/` — 调试与性能调优
- `guide/编程指南/附录/` — 附录

### 算子实践参考（实战）
- `guide/算子实践参考/SIMD算子实现/` — SIMD 算子实现指南
- `guide/算子实践参考/SIMD算子性能优化/` — SIMD 性能优化
- `guide/算子实践参考/SIMT算子实现/` — SIMT 算子实现指南
- `guide/算子实践参考/SIMD与SIMT混合算子实现/` — 混合实现
- `guide/算子实践参考/SIMD与SIMT混合算子性能优化/` — 混合性能优化
- `guide/算子实践参考/优秀实践/` — 最佳实践案例
- `guide/算子实践参考/功能调试/` — 功能调试方法
- `guide/算子实践参考/性能分析/` — 性能分析方法

### 兼容性迁移
- `guide/兼容性迁移指南/351x架构迁移指导/` — A5 架构迁移

## API Context 搜索建议

`docs/api/context/` 包含 1711 个 markdown 文件，覆盖所有 Ascend C API。搜索策略：

```bash
# 按关键词搜索 API
grep -rl "DataCopy" docs/api/context/
grep -rl "ReduceMax" docs/api/context/
grep -rl "EnQue" docs/api/context/
```

### 常用 API 类别速查

| 类别 | 搜索关键词 | 说明 |
|------|-----------|------|
| 算术运算 | `Add`, `Sub`, `Mul`, `Div`, `Adds`, `Muls` | 向量算术 |
| 归约运算 | `ReduceMax`, `ReduceSum`, `ReduceMean` | 归约操作 |
| 数据搬移 | `DataCopy`, `DataCopyPad`, `DataCopyExtParams` | GM ↔ UB |
| 缓冲管理 | `TBuf`, `TQue`, `LocalMemAllocator` | 内存分配 |
| 精度转换 | `Cast`, `CAST_NONE`, `CAST_ROUND` | 类型转换 |
| Pipeline 同步 | `EnQue`, `DeQue`, `PipeBarrier`, `SetFlag` | 同步原语 |
| 比较操作 | `Compare`, `Select`, `Max`, `Min` | 比较与选择 |
| MatMul | `Mmad`, `MatMul`, `SetTensorA` | 矩阵运算 |
| 标量操作 | `Duplicate`, `Scalar` | 标量广播 |
