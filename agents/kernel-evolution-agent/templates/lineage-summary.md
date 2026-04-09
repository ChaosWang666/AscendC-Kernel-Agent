# 谱系摘要模板

## 格式

```
版本 | 评分 | Git Commit | 描述
-----|------|------------|------
v0   | 0.0  | abc1234    | seed: 基础实现，naive tiling
v1   | 42.5 | def5678    | 加 multi-core 分发 + double buffer
v2   | 38.3 | ghi9012    | 优化 tiling 策略，AR→ARA 模式（延迟降低）
v3   | 35.1 | jkl3456    | 调整 UB 分配，减少 bank conflict
...
```

## 使用方式

1. 谱系从旧到新排列
2. 评分为该版本在全部测试配置上的聚合主指标（具体类型见配置：tflops/bandwidth_gbps/latency_us）
3. 描述为一句话概括该版本的主要变更
4. Agent 可通过 `git show v{N}:workspace/runs/{op_name}/best/{op_name}.asc` 查看任意历史版本
5. Agent 可通过 `git diff v{N-1}..v{N}` 查看版本间差异
6. 详细评分数据在 `evolution/scores/v{N}.json`

## 注意

- 不要重复谱系中已尝试失败的方向（查看 `evolution/logs/` 了解失败详情）
- 关注评分跃升最大的版本，理解其优化技术
- 后期版本的收益递减是正常的
