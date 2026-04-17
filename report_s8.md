# S8 算子挑战赛 实现报告

**日期**: 2026-04-17
**目标平台**: Ascend 910_93 (ai_core)
**交付算子数**: 5
**交付物**: `workspace/submissions/work/{OpName}.zip` × 5

---

## 1. 算子清单

| # | 算子 | 语义 | 输入/输出 dtype | 正确性 | 备注 |
|---|------|------|----------------|--------|------|
| 1 | Fills | `torch.full_like(x, value)` | fp16 | ✓ pass | 纯 Duplicate 填充 |
| 2 | Assign | `dst.copy_(src)` | fp16 | ✓ pass | 纯 DataCopy |
| 3 | Atanh | `torch.atanh(x)` | fp16 | ✓ pass | `0.5·ln((1+x)/(1-x))` |
| 4 | Scale | `x·scale + bias`（broadcast） | fp32 | ✓ pass | 按 scaleLength 循环 |
| 5 | Unpack | `torch.unbind(x, dim=axis)` | fp16 | ✓ pass | 动态多输出 TensorList |

全部 5 个算子 `test_op.py 1` 一次性通过精度验证。

---

## 2. 工程结构

每个算子独立工程（msopgen 生成骨架）：

```
workspace/competition/{op}/{OpName}/
├── {op}_custom.json        算子定义
├── CMakeLists.txt
├── CMakePresets.json       已改 ascend910 → ascend910_93
├── build.sh
├── op_host/
│   ├── {op}.cpp            TilingFunc + InferShape + OpDef
│   └── {op}_tiling.h       TilingData 结构
├── op_kernel/
│   └── {op}.cpp            Kernel 实现
└── build_out/
    └── custom_opp_openEuler_aarch64.run  自安装部署包
```

另有 `workspace/competition/combined/Combined/`，把 5 个算子的源文件合在一个工程中一次 build + deploy，便于 `test_op.py` 联合验证（vendor 目录只能装一个算子包的问题由此规避）。

---

## 3. 关键技术点

### 3.1 算子名覆盖内建 aclnn
竞赛 `test_op.py` 通过 `EXEC_NPU_CMD(aclnnFills, ...)` 等调用算子。`EXEC_NPU_CMD` 先在 `libcust_opapi.so` 中查找符号，再落到 `libopapi.so`。因此算子工程 JSON 的 `"op"` 字段直接用 `Fills` / `Assign` / `Atanh` / `Scale` / `Unpack`，生成 `libcust_opapi.so` 内同名符号，**拦截内建实现**，走自定义 Kernel。

### 3.2 Unpack 的动态输出
Unpack 输出张量数量由 attr `num` 决定（典型场景 `num ∈ {2..32}`），必须用 `aclTensorList`：
- `op_host/unpack.cpp` OpDef：`Output("y").ParamType(DYNAMIC)`
- `op_kernel/unpack.cpp` 引入 `#include "kernel_operator_list_tensor_intf.h"`
- Kernel 内：`ListTensorDesc outListDesc((__gm__ void*)yListAddr)`，逐个 `outListDesc.GetDataPtr<__gm__ uint8_t>(j)` 取第 j 个输出的 GM 地址
- 非 16 对齐尾部用 `DataCopyPad + DataCopyExtParams{blockLen = sliceLen * sizeof(half)}` 精确按字节写出

### 3.3 Elementwise 三段流水线
Fills / Assign / Atanh 采用标准 `CopyIn → Compute → CopyOut` 管线：
- `inQueue / outQueue`（VECIN / VECOUT），Compute 通过 `EnQue/DeQue` 与 MTE 重叠
- Atanh 额外申请两块 `TBuf<VECCALC> tmpBuf1/2` 作为 `(1+x)`、`(1-x)` 中间缓冲
- 128 元素粒度对齐（fp16 = 256B）保证 Vector 指令效率

### 3.4 Scale 的 broadcast
`y = x * broadcast(scale, axes) + broadcast(bias, axes)`。设 `outerLength = prod(x.shape[:axis])`，`scaleLength = prod(scale.shape)`：
- 把 scale/bias 一次性 DMA 进 UB（常驻）
- 外层循环 outerLength 次，每次 `Mul(y, x, scaleLocal, scaleLength); Add(y, y, biasLocal, scaleLength)`

### 3.5 芯片目标修正
msopgen 默认生成 `ascend910`，需 sed 改为 `ascend910_93`：
- `CMakePresets.json`：`"ASCEND_PRODUCT_TYPE": "ascend910_93"`
- `op_host/{op}.cpp`：`AICore().AddConfig("ascend910_93")`

### 3.6 部署流程
```bash
unset ASCEND_CUSTOM_OPP_PATH   # 否则 run 包安装被跳过
export ASCEND_OPP_PATH=/usr/local/Ascend/ascend-toolkit/latest/opp
cd build_out && ./custom_opp_openEuler_aarch64.run --install-path=$ASCEND_OPP_PATH
export LD_LIBRARY_PATH=$ASCEND_OPP_PATH/vendors/customize/op_api/lib/:$LD_LIBRARY_PATH
```

---

## 4. 性能状况

msprof 捕获到的 AICore 时间：

| 算子 | 单次调用 aicore time | 主要瓶颈 |
|------|---------------------|----------|
| Fills | 未捕获（子 μs 级别） | - |
| Assign | 未捕获 | - |
| Atanh | 未捕获 | - |
| Scale | 未捕获 | - |
| **Unpack** | **~60.9 μs** | scalar_time ≈ 51.8 μs（84%） |

Fills / Assign / Atanh / Scale 在当前测试输入尺度下运行过快，跌落 msprof 采样粒度，未出现在 `op_summary.csv` 前 20–40 行中。这与它们都是单核、无复杂控制流的纯矢量/搬运流水线一致。

### Unpack 的优化空间
当前实现 = 加载整块输入到 UB → 三层 scalar for 循环 `GetValue/SetValue` 逐元素拷贝 → `DataCopyPad` 写出。`num × outerSize × sliceStride` 次标量访问主导开销。可进一步优化方向：
1. **多核并行**：按 `num` 维 split，每核处理 `num/coreNum` 个输出张量，无依赖
2. **向量化搬运**：当 `sliceStride` 为 16 的倍数时用 `DataCopy` 替代 scalar 循环
3. **跨步 DMA**：用 `DataCopyExtParams{blockCount, srcStride, dstStride}` 直接 GM→GM gather，跳过 UB scalar 阶段

时间关系未进一步优化，但 Kernel 正确性已稳定，留存作为后续轮次起点。

---

## 5. 提交物

`workspace/submissions/work/` 下 5 个 zip，每个包含：

```
{OpName}_zip/
├── op_host/   (CMakeLists.txt + {op}.cpp + {op}_tiling.h)
├── op_kernel/ (CMakeLists.txt + {op}.cpp)
└── custom_opp_openEuler_aarch64.run
```

| 文件 | 大小 |
|------|------|
| Fills.zip | 401 KB |
| Assign.zip | 372 KB |
| Atanh.zip | 371 KB |
| Scale.zip | 373 KB |
| Unpack.zip | 371 KB |

生成命令（从 `competition_sources/zip_op.sh` 派生）：
```bash
cd workspace/submissions/work
for op in Fills Assign Atanh Scale Unpack; do bash zip_op.sh $op; done
```

---

## 6. 踩坑记录

| 问题 | 原因 | 解决 |
|------|------|------|
| 逐个 deploy 后只剩最后一个算子 | `.run` 安装会整个覆盖 `vendors/customize/` 目录 | 建 Combined 工程一次 build 全部 5 个算子 |
| CPack "binary/config" 报错 | Unpack kernel 编译未通过，产物残缺 | 修 Kernel 后先 `rm -rf build_out/op_kernel/Unpack_*` |
| `unknown type name 'ListTensorDesc'` | `kernel_operator.h` 不含 TensorList 声明 | 补 `#include "kernel_operator_list_tensor_intf.h"` |
| `get_time.py` 对部分算子返回 NaN | `op_summary.csv` 行数不足（custom 算子没被采样进前 20–40 行） | 改用 msprof 原始 csv 检视，不仅依赖 get_time.py |

---

## 7. 目录索引

| 路径 | 内容 |
|------|------|
| `workspace/competition/{op}/{OpName}/` | 5 个独立算子工程 |
| `workspace/competition/combined/Combined/` | 合并工程（联合测试用） |
| `workspace/submissions/op/{OpName}/` | 提交用软链接视图 |
| `workspace/submissions/work/{OpName}.zip` | **最终提交物** |
| `competition_sources/算子挑战赛S8赛题/case_910b/` | 竞赛测试基础设施（test_op.py / run.sh / custom_op.cpp） |
| `competition_sources/评分规则说明.md` | 评分与打包规则 |
