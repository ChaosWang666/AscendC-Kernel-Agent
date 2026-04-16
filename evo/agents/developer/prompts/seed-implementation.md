# 种子实现 Prompt（v0）

## 上下文

你需要根据 Architect 的设计文档，实现第一个可编译的自定义算子工程。

### 设计文档
```
{{DESIGN_CONTENT}}
```

### 实现计划
```
{{PLAN_CONTENT}}
```

### 工作目录
- 候选目录：`{{CANDIDATE_DIR}}/`
- 算子定义 JSON：`{{CANDIDATE_DIR}}/{{op_name}}_custom.json`
- 算子工程：`{{CANDIDATE_DIR}}/{{OP_CAPITAL}}Custom/`

### 目标芯片
{{TARGET_CHIP}}

## 任务

按照 DESIGN.md 和 PLAN.md 实现完整的自定义算子工程。

## 实现步骤

1. **编写算子定义 JSON**
   - `{{CANDIDATE_DIR}}/{{op_name}}_custom.json`

2. **生成工程骨架**
   ```bash
   cd {{CANDIDATE_DIR}}
   msopgen gen -i {{op_name}}_custom.json -c ai_core-{{TARGET_CHIP}} -lan cpp -out {{OP_CAPITAL}}Custom
   ```

3. **实现 TilingData**
   - `{{OP_CAPITAL}}Custom/op_host/{{op_name}}_custom_tiling.h`

4. **实现 Host 侧逻辑**
   - `{{OP_CAPITAL}}Custom/op_host/{{op_name}}_custom.cpp`
   - TilingFunc + InferShape + InferDataType + OpDef

5. **实现 Kernel**
   - `{{OP_CAPITAL}}Custom/op_kernel/{{op_name}}_custom.cpp`
   - Init + Process (CopyIn/Compute/CopyOut)

6. **编译验证**
   ```bash
   cd {{OP_CAPITAL}}Custom && ./build.sh
   ```

7. **创建测试基础设施**（仅 v0 需要）
   - `workspace/runs/{{OP_NAME}}/test/reference.py` — Model + ModelNew + get_inputs
   - `workspace/runs/{{OP_NAME}}/test/CppExtension/csrc/op.cpp` — Python 绑定
   - CppExtension 模板从 `workspace/templates/CppExtension/` 复制
   ```bash
   cp -r workspace/templates/CppExtension/* workspace/runs/{{OP_NAME}}/test/CppExtension/
   ```
   然后更新 `csrc/op.cpp` 中的算子绑定代码。

## 质量要求

- 编译必须通过
- 严格按 DESIGN.md 设计实现
- 测试基础设施文件必须创建（v0）
- 如有设计问题，返回 `design_issue` 给 Architect
