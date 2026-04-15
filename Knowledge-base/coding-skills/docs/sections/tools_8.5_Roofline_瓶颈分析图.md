<!-- Source: 算子开发工具.md lines 9075-9163 | Section: 8.5 Roofline 瓶颈分析图 -->

# 8.5 Roofline 瓶颈分析图

通过msprof op生成的visualize_data.bin文件可通过MindStudio Insight进行可视化呈 现，Roofline瓶颈分析图可构建出处理器的性能模型，然后利用该性能模型快速评估出 算子的理论性能极限，协助开发者快速识别瓶颈类型。 

# 说明

● 若要使用MindStudio Insight进行查看时，需要单独安装MindStudio Insight软件包，具体下 载链接请参见《MindStudio Insight工具用户指南》的“安装与卸载”章节。 

● 将visualize_data.bin文件导入MindStudio Insight的具体操作请参考导入性能数据 《MindStudio Insight工具用户指南》的“算子调优 > 导入性能数据”章节。 

MindStudio Insight具体操作请参考《MindStudio Insight工具用户指南》的“算子调优 > 详情（Details）”章节。 

# 硬件支持情况

通过msprof op生成的visualize_data.bin文件可导入MindStudio Insight进行可视化呈 现，并针对不同的硬件以及算子类型会生成不同的Roofline分析视图。 

● Atlas 推理系列产品的Roofline瓶颈分析图中仅有内存单元视图。 


图 8-2 Atlas 推理系列产品 Roofline 瓶颈分析图


![](images/930d2b5f473947d672c39d12c5dd141903fcf61e7b956647b12c005e9a666838.jpg)


Atlas A3 训练系列产品/Atlas A3 推理系列产品和Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组件根据算子类型不同而产生不同的视图， 具体请参见表8-7。 


图 8-3 Atlas A3 训练系列产品/Atlas A3 推理系列产品和 Atlas A2 训练系列产品/ Atlas 800I A2 推理产品/A200I A2 Box 异构组件 Roofline 瓶颈分析图


![](images/af5a1e4b7231428844cc78a2d01404a7b8ca98b3b73776d658a6182a46ebd3a2.jpg)



表 8-7 Atlas A3 训练系列产品/Atlas A3 推理系列产品和 Atlas A2 训练系列产品/ Atlas 800I A2 推理产品/A200I A2 Box 异构组件支持 Roofline 视图情况列表


<table><tr><td>Roofline视图类型</td><td>Vector算子</td><td>Cube算子</td><td>Mix算子</td></tr><tr><td>GM/L2视图</td><td>✓</td><td>✓</td><td>✓</td></tr><tr><td>Vector内存单元视图</td><td>✓</td><td>-</td><td>✓</td></tr><tr><td>Vector内存通路视图</td><td>✓</td><td>-</td><td>✓</td></tr><tr><td>Vector Pipeline视图</td><td>✓</td><td>-</td><td>✓</td></tr><tr><td>Cube内存单元视图</td><td>-</td><td>✓</td><td>✓</td></tr><tr><td>Cube内存通路视图</td><td>-</td><td>✓</td><td>✓</td></tr><tr><td>Cube Pipeline视图</td><td>-</td><td>✓</td><td>✓</td></tr></table>

# 功能介绍

每个单元/通路的Roofline性能分析结果由横轴、纵轴、屋顶线、带宽斜线和实际运行 坐标点组成，具体请参见图8-4。 


图 8-4 Roofline 示意图


![](images/ab7115d38bfcbd0b6e289fdcd3be637b9de21e4bce683906bfc832adb9acc25a.jpg)


横轴：代表算术强度（Arithmetic Intensity），即某一单元或通路中总的浮点运 算次数与总的访存数据量之比，单位为Ops/Byte。 

纵轴：表示计算性能（Performance），即每秒可执行的浮点操作数，单位为 TOps/s。 

屋顶线：指图中顶部的水平线，代表NPU的理论最大计算性能。无论算术强度如 何提高，应用的实际性能都不可能超过硬件上限。 

带宽斜线：指图中与屋顶线相交的斜线，其与纵轴的交点取决于理论最大带宽。 当理论最大带宽乘以算术强度小于NPU理论最大计算性能时，能达到的最大算力 随算术强度的增加而线性增长。 

# 说明

屋顶线和带宽斜线组合成算子能达到的理论最大算力，可以概括为min（NPU理论最大计 算性能，理论最大带宽*实际算术强度）。 

实际运行坐标点的参数构成请参见表8-8。 


表 8-8 实际运行坐标点简介


<table><tr><td>坐标参数</td><td>简介</td></tr><tr><td>带宽（Bandwidth）</td><td>该单元/通路的理论最大带宽。</td></tr><tr><td>算术强度（Arithmetic Intensity）</td><td>算子实际运行时的算术强度，即横轴坐标值。</td></tr><tr><td>性能（Performance）</td><td>算子实际运行时的计算性能，即纵轴坐标值。</td></tr><tr><td>性能百分比（Performance Ratio）</td><td>算子实际运行时的计算性能与当前数据量下的理论最大计算性能比值，即图中a/b的百分比。</td></tr></table>

Roofline分析视图分析算子的性能百分比，并提供以下客观分析结果： 

● 算子性能百分比大于 $80 \%$ 时，按照所在区域进行提示，有以下两种情况。 

Compute Bound：计算瓶颈。 

Memory Bound：内存瓶颈。 

算子性能百分比小于 $80 \%$ ，Bound类型为Latency Bound，有以下三种情况： 

– 若最大的pipeline ratio小于 $80 \%$ ，提示latency bound:pipeline caused。 

若最大的pipeline ratio大于 $80 \%$ ，需识别最大pipeline ratio的类型。 

若最大pipeline ratio的类型是compute pipeline (cube ratio、vector ratio、scalar ratio)，提示latency bound:compute caused。 

若最大pipeline ratio的类型是memory pipeline(MTE1 ratio、MTE2 ratio、MTE3 ratio)，提示latency bound:memory caused。