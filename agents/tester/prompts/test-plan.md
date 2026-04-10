# 测试计划 Prompt

## 上下文

你需要对以下算子工程进行完整的构建、部署和测试验证。

### 算子工程
`{{CANDIDATE_DIR}}/{{OP_CAPITAL}}Custom/`

### 测试配置
```json
{{TEST_CONFIGS}}
```

### 测试基础设施
- CppExtension：`workspace/runs/{{OP_NAME}}/test/CppExtension/`
- 参考实现：`workspace/runs/{{OP_NAME}}/test/reference.py`
- 部署目录：`workspace/deploy/opp/`

## 测试步骤

### 1. 构建自定义算子工程
```bash
bash scoring/compile.sh {{CANDIDATE_DIR}}
```

### 2. 部署算子包
```bash
bash scoring/deploy.sh {{CANDIDATE_DIR}} workspace/deploy/opp
```

### 3. 构建 Python 绑定
```bash
bash scoring/build_pybind.sh workspace/runs/{{OP_NAME}}/test/CppExtension workspace/deploy/opp
```

### 4. 正确性测试（分级）
```bash
# Smoke
python3 scoring/test_correctness.py \
    --reference workspace/runs/{{OP_NAME}}/test/reference.py \
    --config scoring/configs/{{CONFIG}}.json \
    --output correctness_smoke.json \
    --levels smoke

# Representative
python3 scoring/test_correctness.py \
    --reference workspace/runs/{{OP_NAME}}/test/reference.py \
    --config scoring/configs/{{CONFIG}}.json \
    --output correctness_rep.json \
    --levels representative
```

### 5. 性能测试
```bash
python3 scoring/test_performance.py \
    --reference workspace/runs/{{OP_NAME}}/test/reference.py \
    --config scoring/configs/{{CONFIG}}.json \
    --output performance.json
```

### 6. 或者使用完整评分流程
```bash
bash scoring/score.sh {{CANDIDATE_DIR}} scoring/configs/{{CONFIG}}.json
```

## 输出

- 测试报告：`{{CANDIDATE_DIR}}/docs/TEST_REPORT.md`
- 评分文件：`evolution/scores/v{{VERSION}}.json`
