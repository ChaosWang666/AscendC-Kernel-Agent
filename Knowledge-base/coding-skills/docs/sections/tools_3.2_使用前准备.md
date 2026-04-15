<!-- Source: 算子开发工具.md lines 602-619 | Section: 3.2 使用前准备 -->

# 3.2 使用前准备

请参考2 环境准备，完成相关环境变量的配置。然后，可直接使用msKPP工具的 3.3 性能建模功能。 

# 说明

● 在任意目录下实现算子的DSL语言方案（ Domain-Specific Language ，领域特定语 言），实现中包括如下注意事项： 

实现模拟DSL算子前，需要导入Tensor、Chip以及算子实现所必要的指令（统一 以小写命名）。 

以with语句开启算子实现代码的入口，“enable_trace”和“enable_metrics”两 个接口可使能trace打点图和指令统计功能，具体请参见3.3.4 极限性能分析章节 的main.py。 

详细指令接口说明请参考3.3.6 对外接口使用说明。 

如果需要指令占比饼图（instruction_cycle_consumption.html），则需要安装生成饼 图所依赖的Python三方库plotly。 pip3 install plotly 

若要使用3.5 自动调优功能，需要下载Link中的Ascend C模板库。