# 种子设计 Prompt（v0）

## 上下文

你需要为以下算子设计第一个可工作的自定义算子工程实现方案。

### 算子规格
```
{{OPERATOR_SPEC}}
```

### 目标芯片
{{TARGET_CHIP}}

### 测试配置
```json
{{TEST_CONFIGS}}
```

### 工作目录
- 候选目录：`{{CANDIDATE_DIR}}/`
- 算子工程：`{{CANDIDATE_DIR}}/{{OP_CAPITAL}}Custom/`
- 测试基础设施：`workspace/runs/{{OP_NAME}}/test/`

## 任务

设计完整的自定义算子工程方案，输出 DESIGN.md + PLAN.md，然后分发给 Developer 实现。

## 设计内容

### DESIGN.md 应包含

1. **算子分析**
   - 计算模式分类（归约/广播/逐元素/转换/MatMul/卷积）
   - 计算/访存比分析
   - 关键约束条件

2. **Tiling 策略**
   - 多核切分方案（blockDim、每核数据量）
   - UB 切分方案（tileLength、Buffer 数量）
   - 对齐处理策略（尾块、padding）

3. **自定义算子工程设计**

   **算子定义 JSON**:
   - 输入/输出描述（name、param_type、format、type）
   
   **op_host 设计**:
   - TilingData 结构字段定义
   - TilingFunc 计算逻辑
   - InferShape / InferDataType 逻辑
   - blockDim 设置策略
   
   **op_kernel 设计**:
   - Kernel 类成员变量
   - Pipeline 编排（CopyIn → Compute → CopyOut）
   - API 选型（DataCopy / Add / Mul / ...）
   - Buffer 队列数量和 BUFFER_NUM

4. **CppExtension 绑定**
   - op.cpp 中的函数签名
   - EXEC_NPU_CMD 调用参数

5. **PyTorch 参考实现**
   - Model 类（原生实现）
   - ModelNew 类（自定义算子调用）
   - get_inputs / get_init_inputs

### PLAN.md 应包含

1. Developer 实现步骤清单
2. 预期文件列表
3. 编译验证命令
4. 测试验收标准

## 质量要求

- v0 目标是正确性，不追求极致性能
- 代码结构清晰，便于后续优化
- 必须处理所有 dtype（fp32/fp16/bf16）
- 必须处理非对齐尾块
