# 优化实现 Prompt

## 上下文

你需要根据 Architect 的优化设计，在现有算子工程上实施修改。

### 优化设计
```
{{DESIGN_CONTENT}}
```

### 修改计划
```
{{PLAN_CONTENT}}
```

### 候选目录
`{{CANDIDATE_DIR}}/{{OP_CAPITAL}}Custom/`

### 基线（只读参考）
`workspace/runs/{{OP_NAME}}/best/{{OP_CAPITAL}}Custom/`

## 任务

按照新的 DESIGN.md 和 PLAN.md，增量修改候选目录中的算子工程代码。

## 要求

- 优先修改现有文件，不完全重写
- 所有修改仅在候选目录中进行
- 编译通过后报告完成
- 如发现设计问题，返回 `design_issue`
