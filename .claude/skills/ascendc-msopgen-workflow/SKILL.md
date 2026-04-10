---
name: ascendc-msopgen-workflow
description: msopgen 自定义算子工程生成工作流指南。触发：用户需要创建自定义算子工程、用 msopgen 生成骨架、遇到 msopgen 权限错误或 "should not be written by user group" 报错、发现生成的 CMakePresets 目标芯片错误（ascend910 而非 ascend910b）、或需要文档化自定义算子工程从 JSON 到 build_out/*.run 的完整流程时。
---

# msopgen 自定义算子工程工作流

本 skill 文档化了从算子定义 JSON 到 `build_out/custom_opp_*.run` 可部署包的完整流程，以及从多次实际运行中总结的已知坑点。

---

## 标准流程（HAPPY PATH）

```bash
# 1. 准备算子定义 JSON（注意 chmod）
cat > /path/to/work/<op_name>_custom_op.json <<'EOF'
[{
  "op": "<OpName>Custom",
  "language": "cpp",
  "input_desc":  [{"name": "x", "param_type": "required", "format": ["ND"], "type": ["float"]}],
  "output_desc": [{"name": "y", "param_type": "required", "format": ["ND"], "type": ["float"]}]
}]
EOF

# 2. 调整权限（msopgen 坑点 #1，见下）
chmod 750 /path/to/work                           # parent dir
chmod 640 /path/to/work/<op_name>_custom_op.json   # json file

# 3. 生成工程骨架
source /usr/local/Ascend/ascend-toolkit/set_env.sh
cd /path/to/work
msopgen gen -i <op_name>_custom_op.json -c ai_core-Ascend910B -lan cpp -out <OpName>Custom

# 4. 修正 msopgen 产物的目标芯片（坑点 #2）
sed -i 's/ascend910"/ascend910b"/g' <OpName>Custom/CMakePresets.json
sed -i 's/AddConfig("ascend910")/AddConfig("ascend910b")/g' <OpName>Custom/op_host/<op_name>_custom.cpp

# 5. 补齐 op_host TilingFunc + InferShape（msopgen 只给占位）
#    编辑 op_host/<op_name>_custom_tiling.h  — TilingData 字段
#    编辑 op_host/<op_name>_custom.cpp       — TilingFunc 逻辑

# 6. 实现 op_kernel
#    编辑 op_kernel/<op_name>_custom.cpp     — Kernel 类

# 7. 构建
cd <OpName>Custom
bash build.sh

# 8. 验证产物
ls build_out/custom_opp_openEuler_aarch64.run
```

---

## 已知坑点

### 坑点 #1 — 文件权限校验（错误信息极不友好）

**症状**：
```
msopgen gen ... 
ERROR: File /path/to/op.json should not be written by user group or others
```

**原因**：msopgen 对输入 JSON 要求 `chmod 640`（ugo: rw- r-- ---），对工作目录要求 `chmod 750`。默认的 `umask 022` 会产生 `644` 文件和 `755` 目录，都会被拒绝。

**修复**：
```bash
chmod 750 $(dirname /path/to/op.json)
chmod 640 /path/to/op.json
```

**推荐**：在脚本里**创建 JSON 后立即 chmod**：
```bash
printf '%s' "$json_content" > op.json && chmod 640 op.json
```

### 坑点 #2 — 默认生成的 CMakePresets.json 目标芯片错误

**症状**：使用 `-c ai_core-Ascend910B` 调用 msopgen 后，生成的 `CMakePresets.json` 里 `ASCEND_COMPUTE_UNIT` 仍然是 `ascend910`（不带 b）。op_host/.cpp 里的 `AICore().AddConfig("ascend910")` 也是错的。

**影响**：构建能通过但产出的 `.run` 包只包含 **ascend910** 的 kernel binary。部署到 Ascend910B 机器后 `aclnn` 调用会找不到 kernel，运行时报找不到 op（error code 161xxx）。

**修复**（在 msopgen 调用后立即执行）：
```bash
sed -i 's/"ascend910"/"ascend910b"/g' <OpName>Custom/CMakePresets.json
sed -i 's/AddConfig("ascend910")/AddConfig("ascend910b")/g' <OpName>Custom/op_host/*.cpp
```

**验证**：构建后检查 `build_out/autogen/aic-ascend910b-ops-info.ini` 存在（ascend910 那版会叫 `aic-ascend910-ops-info.ini`）。

### 坑点 #3 — TensorFlow plugin 冗余生成

**症状**：即使目标是 PyTorch 场景，msopgen 仍然生成 `framework/tf_plugin/tensorflow_<op>_plugin.cc` 并参与构建。

**影响**：
- 增加 ~20 秒构建时间
- 需要 TensorFlow header 存在（本仓库环境 OK，别处可能编译失败）
- 生成的 .run 包里多一个不需要的 TF 符号

**缓解**（可选）：留着它——移除需要编辑 `framework/CMakeLists.txt` 反而更脆弱。注意构建日志会显示编译 tf_plugin。

### 坑点 #4 — msopgen 生成代码的格式奇怪

**症状**：生成的 `op_host/<op>_custom.cpp` 有奇怪的空行、缩进不一致、偶尔出现 `tiling.set_size(data_sz)` 这种与实际 TilingData 不匹配的占位调用。

**修复**：把 msopgen 生成的 `TilingFunc` 当作"骨架注释"来看——只保留函数签名和 OpDef 注册，内部逻辑全部重写。

### 坑点 #5 — framework/tf_plugin 权限与 CANN 版本绑定

**症状**：在不同 CANN 版本里，`tf_plugin` 的 CMakeLists 引用的 TensorFlow 版本不一致，换机器后可能直接编译失败。

**缓解**：不用 TF 的项目可以在 msopgen 之后直接 `rm -rf framework/tf_plugin` 并移除 `framework/CMakeLists.txt` 里对它的引用。

---

## 最小 TilingFunc 模板

msopgen 生成的 TilingFunc 基本不能用，以下是已验证能编译运行的最小模板：

```cpp
static ge::graphStatus TilingFunc(gert::TilingContext* context)
{
    TilingData tiling;

    // 从输入 shape 派生维度
    auto xShape = context->GetInputShape(0)->GetStorageShape();
    uint32_t B = xShape.GetDim(0);
    uint32_t L = xShape.GetDim(1);
    uint32_t E = xShape.GetDim(2);

    // 从 PlatformInfo 获取 core 数
    auto ascendPlatform = platform_ascendc::PlatformAscendC(context->GetPlatformInfo());
    auto coreNum = ascendPlatform.GetCoreNumAic();  // 或 GetCoreNumAiv()

    // 按 batch 均分（最简策略）
    uint32_t batchPerCore = (B + coreNum - 1) / coreNum;

    // 填字段
    tiling.set_batchSize(B);
    tiling.set_seqLen(L);
    tiling.set_inputSize(E);
    tiling.set_coreNum(coreNum);
    tiling.set_batchPerCore(batchPerCore);

    // 写出
    tiling.SaveToBuffer(context->GetRawTilingData()->GetData(),
                        context->GetRawTilingData()->GetCapacity());
    context->GetRawTilingData()->SetDataSize(tiling.GetDataSize());

    // 关键：设置 block_dim（否则 kernel 只在 1 个 core 上跑）
    context->SetBlockDim(coreNum);
    return ge::GRAPH_SUCCESS;
}
```

---

## 最小 InferShape 模板

```cpp
static ge::graphStatus InferShape(gert::InferShapeContext* context)
{
    auto xShape = context->GetInputShape(0)->GetStorageShape();
    auto yShape = context->GetOutputShape(0);
    *yShape = xShape;  // 简单 copy；有变形的算子按需 SetDim
    return ge::GRAPH_SUCCESS;
}

static ge::graphStatus InferDataType(gert::InferDataTypeContext* context)
{
    context->SetOutputDataType(0, context->GetInputDataType(0));
    return ge::GRAPH_SUCCESS;
}
```

---

## 构建成功判断

构建成功的 3 个硬证据：

1. `build.sh` exit code 0
2. `build_out/custom_opp_<platform>_<arch>.run` 存在且大小 > 100 KB
3. `build_out/autogen/aclnn_<op>_custom.h` 存在（这个头文件被 CppExtension 的 `EXEC_NPU_CMD` 间接依赖）

若 3 个条件有任一不满足，构建算失败，不要继续部署。

---

## 自动化脚手架

本仓库提供 `scripts/bootstrap_operator.sh <op_name> <spec_file>`（如果存在）会自动完成：
1. 创建 `workspace/specs/<op>.md`
2. 创建 `workspace/runs/<op>/test/{reference.py, CppExtension/}`
3. 创建 `scoring/configs/<op>.json`
4. 应用坑点 #1、#2 的 chmod 和 sed 修正

推荐首选该脚本，而不是手动拷贝+编辑。

---

## 参考实现索引

若要开发新算子，先在这些路径下搜 PoC 级参考代码：

| 算子类别 | Knowledge-base 路径 |
|---------|--------------------|
| RNN/LSTM/GRU | `Knowledge-base/coding-sources/ops-coding-sources/ops-nn/rnn/` |
| Attention | `Knowledge-base/coding-sources/ops-coding-sources/ops-transformer/attention/` |
| Normalization (LayerNorm/BatchNorm) | `Knowledge-base/coding-sources/ops-coding-sources/ops-nn/normalization/` |
| 激活函数 | `Knowledge-base/coding-sources/ops-coding-sources/ops-nn/activation/` |
| MatMul | `Knowledge-base/coding-sources/ops-coding-sources/ops-nn/matmul/` |
| Elementwise/Math | `Knowledge-base/coding-sources/ops-coding-sources/ops-math/` |
| SDK 最小示例 | `Knowledge-base/coding-sources/programming-coding-sources/asc-devkit/examples/` |

每个目录通常有 `op_host/`, `op_kernel/` 子目录，直接对着读即可。
