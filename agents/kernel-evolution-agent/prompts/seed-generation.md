# 种子生成 Prompt（v0）

## 上下文

你需要为以下算子创建第一个可工作的 Ascend C 内核实现。

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

## 任务

从零开始生成一个通过全部正确性测试的 Kernel v0。

## 步骤

1. **分析算子规格**
   - 识别计算模式（归约/广播/逐元素/转换/MatMul/卷积）
   - 确定输入输出张量形状和数据类型
   - 识别关键计算操作

2. **设计 Tiling 策略**
   - 读取 `Knowledge-base/coding-skills/skills/skills/ascendc-tiling-design/SKILL.md`
   - 根据计算模式选择合适的 Tiling 方法
   - 确定多核分发策略

3. **创建工程骨架**
   - 读取 `Knowledge-base/coding-skills/skills/skills/ascendc-direct-invoke-template/SKILL.md`
   - 在候选目录 `{{CANDIDATE_DIR}}/` 中创建目录结构
   - 生成 CMakeLists.txt、run.sh、gen_data.py、verify_result.py

4. **实现 Kernel**
   - 读取 `Knowledge-base/coding-skills/skills/skills/ascendc-api-best-practices/SKILL.md` 选择正确 API
   - 搜索 `Knowledge-base/coding-sources/programming-coding-sources/asc-devkit/examples/` 找类似示例
   - 实现 Init、Process（CopyIn/Compute/CopyOut）
   - 使用 EnQue/DeQue 同步

5. **编译验证**
   ```bash
   cd {{CANDIDATE_DIR}} && bash run.sh
   ```

6. **正确性测试**
   ```bash
   bash scoring/test_correctness.sh {{CANDIDATE_DIR}} scoring/configs/{{CONFIG}}.json
   ```

7. **如果失败，诊断修复并重试**

## 质量要求

- correctness_total = 1.0（全部配置通过）
- 不需要追求性能，v0 只要正确
- 代码清晰，便于后续优化
