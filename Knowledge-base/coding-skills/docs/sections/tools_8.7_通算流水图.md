<!-- Source: 算子开发工具.md lines 9206-9254 | Section: 8.7 通算流水图 -->

# 8.7 通算流水图

通过msprof op对通算融合算子进行调优后，生成的trace.json和visualize_data.bin文 件可通过MindStudio Insight进行可视化呈现，能够直观看到通算运行情况、指令耗时 等信息，协助开发者识别通算瓶颈。当前仅支持MC2和LCCL类型的通算融合算子。 

# 说明

● 若要使用MindStudio Insight进行查看时，需要单独安装MindStudio Insight软件包，具体下 载链接请参见《MindStudio Insight工具用户指南》的“安装与卸载”章节。 

● 将visualize_data.bin文件导入MindStudio Insight的具体操作请参考导入性能数据 《MindStudio Insight工具用户指南》的“算子调优 $>$ 导入性能数据”章节。 

MindStudio Insight具体操作和详细字段解释请参考《MindStudio Insight工具用户指南》 的“系统调优 $>$ 时间线（Timeline）”章节。 

● 添加-g编译选项会在生成的二进制文件中附带调试信息，建议限制带有调试信息的用户程序 的访问权限，确保只有授权人员可以访问该二进制文件。 

# Chrome浏览器

在Chrome浏览器中输入“chrome://tracing”地址，并将通过msprof op生成的 通算流水图文件（trace.json）拖到空白处打开，键盘上输入快捷键（W：放大， S：缩小，A：左移，D：右移）可进行查看。关键字段说明如表8-9。 


表 8-9 关键字段说明


<table><tr><td>字段名</td><td>字段功能</td><td>MC2算子</td><td>LCCL算子</td></tr><tr><td>AI CORE</td><td>算子在AI Core上的整体运行情况。</td><td>支持</td><td>支持</td></tr><tr><td>AI CPU</td><td>算子在AI CPU上的整体运行情况。</td><td>支持</td><td>不支持</td></tr><tr><td>TURN</td><td>算子在AI CPU上不同通信轮次的流水。</td><td>支持</td><td>不支持</td></tr><tr><td>AIC BLOCK</td><td>算子在AI Core各cube核上的整体运行情况和关键接口调用情况。</td><td>支持</td><td>支持</td></tr><tr><td>AIV BLOCK</td><td>算子在AI Core各vector核上的整体运行情况和关键接口调用情况。</td><td>支持</td><td>支持</td></tr><tr><td>HCCL</td><td>通过HCCL通信的算子在多卡间的集合通信流水。</td><td>支持</td><td>不支持</td></tr><tr><td>HCCL TASK</td><td>通过HCCL通信的算子在多卡间的集合通信任务执行流水。</td><td>支持</td><td>不支持</td></tr></table>

# MindStudio Insight

通过msprof op生成的trace.json文件或visualize_data.bin文件可导入MindStudio Insight进行可视化呈现。 


图8-7 通算流水图


![](images/1d73a1a33f8e96ac6f0608bc651f6115946c59ad7531c38e6d88701c744a8253.jpg)


展示算子在AI CPU和AI Core的耗时掩盖情况，用于评估通算融合算子的性 能。 

展示算子在AI CPU上的不同通信轮次的流水。 

展示算子在各BLOCK上的运行时间及关键接口调用流水。 

展示通过HCCL通信的算子在多卡间运行时的集合通信流水及集合通信任务流 水。 

# 说明

MC2算子支持对Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组件的AllReduce、AllGather、ReduceScatter、AlltoAll等接口及Atlas A3 训 练系列产品/Atlas A3 推理系列产品的AllGather、ReduceScatter、AlltoAllV等接 口进行调用，具体介绍请参见《Ascend C算子开发接口》中的“高阶API > Hccl > Hccl”章节，添加-g编译选项后，单击具体接口将会关联代码行调用栈。 

● MC2算子和LCCL算子的支持情况请参考表8-9