你正在审查一个 Ascend C 内核优化的进化轨迹。

## 当前状态
- 已提交 {{N}} 个版本
- 运行时间: {{ELAPSED}}
- 最佳评分: {{BEST_SCORE}} ({{METRIC_TYPE}}) (版本 v{{BEST_VERSION}})
- 最近 {{STALL_COUNT}} 个版本无改进

## Profiling 数据摘要
```json
{{PROFILING_SUMMARY}}
```

## 最近的失败尝试
{{RECENT_FAILURES}}

## 可用知识资源
- ascendc-tiling-design: Tiling 策略（归约/广播/逐元素/转换/MatMul/卷积）
- ascendc-api-best-practices: API 优化模式（Adds/Muls、Double Buffer）
- ascendc-npu-arch: 芯片架构 A2/A3/A5、硬件约束
- ops-profiling: 8 CSV 性能指标分析
- 参考实现: Knowledge-base/coding-sources/ 中的算子源码

## 任务

基于以上信息：

1. 分析当前性能瓶颈的根本原因
2. 提出 3-5 个**尚未尝试过的**优化方向，每个方向包括：
   - 方向名称
   - 为什么可能有效（基于 profiling 数据的证据）
   - 需要查阅的知识库资源
   - 预期难度（低/中/高）
3. 从中选择最有希望的方向
4. 为该方向生成一段具体的优化指令，直接可以作为 Kernel Evolution Agent 的输入

**只输出最终选定方向的优化指令**（一段话），不要输出分析过程。指令需要足够具体，让 Agent 知道：
- 修改什么代码
- 为什么这样修改
- 查阅哪些文档
