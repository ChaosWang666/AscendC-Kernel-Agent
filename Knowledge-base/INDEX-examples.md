# ASC 示例代码导航索引

基础路径：`Knowledage-base/coding-sources/programming-coding-sources/asc-devkit/examples/`

## 示例分类

### 01_simd_cpp_api — SIMD C++ API 示例

最常用的 API 层级，推荐作为 Kernel 开发的首选。

| 子目录 | 说明 | 适合场景 |
|--------|------|---------|
| `00_introduction/` | 入门示例（hello_world、基本向量运算） | 初学者、种子生成 v0 |
| `01_utilities/` | 工具类示例（数据搬移、Buffer 管理） | 数据搬移优化 |
| `02_features/` | 特性示例（高级计算模式、特殊指令） | 结构优化 |
| `03_libraries/` | 库使用示例（MatMul 库、Sort 库） | MatMul/卷积算子 |
| `04_best_practices/` | 最佳实践（性能优化模式） | 微架构调优 |
| `05_compatibility_guide/` | 兼容性指南（跨架构适配） | 多芯片支持 |

### 02_simd_c_api — SIMD C API 示例

底层 C 接口，提供更精细的硬件控制。

| 子目录 | 说明 | 适合场景 |
|--------|------|---------|
| `00_introduction/` | C API 入门 | 需要精细控制时参考 |
| `01_utilities/` | C API 工具 | 底层数据搬移 |
| `02_features/` | C API 特性 | 硬件特定指令 |

### 03_simt_api — SIMT API 示例

A5（950）架构专用的线程级并行 API。

| 子目录 | 说明 | 适合场景 |
|--------|------|---------|
| `00_introduction/` | SIMT 入门 | A5 芯片算子开发 |
| `01_utilities/` | SIMT 工具 | 线程管理 |
| `02_features/` | SIMT 特性 | 线程级并行优化 |
| `03_best_practices/` | SIMT 最佳实践 | A5 性能调优 |

## 使用建议

### 种子生成（v0）时查看
1. `01_simd_cpp_api/00_introduction/` — 基本 Kernel 结构
2. `01_simd_cpp_api/01_utilities/` — DataCopy、Buffer 管理模式

### 结构优化时查看
3. `01_simd_cpp_api/02_features/` — 高级计算特性
4. `01_simd_cpp_api/03_libraries/` — MatMul 库调用模式

### 微架构调优时查看
5. `01_simd_cpp_api/04_best_practices/` — 性能优化模式
6. `02_simd_c_api/02_features/` — 底层指令优化
7. `03_simt_api/03_best_practices/` — SIMT 性能（A5 only）

### 多芯片兼容时查看
8. `01_simd_cpp_api/05_compatibility_guide/` — 跨架构适配

## 示例代码结构

每个示例通常包含：
```
{example_name}/
  {example_name}.asc         # Kernel 源码
  CMakeLists.txt              # 构建配置
  scripts/
    gen_data.py               # 测试数据生成
    verify_result.py          # 结果验证
  run.sh                      # 一键构建运行
  README.md                   # 说明文档
```
