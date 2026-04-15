<!-- Source: 算子开发工具.md lines 9026-9074 | Section: 8.4 计算内存热力图 -->

# 8.4 计算内存热力图

通过msprof op生成的visualize_data.bin文件可通过MindStudio Insight进行可视化呈 现，界面将会以资源维度展示算子基础信息、计算负载分析和内存负载分析的数据， 协助开发者以全局视角识别资源瓶颈。 

# 说明

● 若要使用MindStudio Insight进行查看时，需要单独安装MindStudio Insight软件包，具体下 载链接请参见《MindStudio Insight工具用户指南》的“安装与卸载”章节。 

● 将visualize_data.bin文件导入MindStudio Insight的具体操作请参考导入性能数据 《MindStudio Insight工具用户指南》的“算子调优 $>$ 导入性能数据”章节。 

MindStudio Insight具体操作请参考《MindStudio Insight工具用户指南》的“算子调优 > 详情（Details）”章节。 


图 8-1 详情界面 1


![](images/6970d6cfce6b1b7fdd8cda6f4c1784be50f276a08aae5cdee1a2b51f1d28a94d.jpg)


![](images/06112aba61ac76f5ddcdf2b64ba164f9dee3779a4608cc3f97f1c797a54d6e6a.jpg)


![](images/e19f4dd5d8a50f149a5adabd80e028972afb295de43f8816611d45fd7ff37bc2.jpg)


![](images/61bc1b5768139edb0cc5dfef57656f7fdf7dbb9a3e2479e4cf0ab5c9fe002210.jpg)


![](images/221efa6efca8fdf37a911571a79370216ef592d5ac2641ca723177d429b9947b.jpg)


提供核间负载分析图（Core Occupancy），以数据窗格的方式呈现各物理单核的 耗时、总数据吞吐量及Cache命中率，帮助开发人员提升物理核的使用效率。 

# 说明

● 仅Atlas A3 训练系列产品/Atlas A3 推理系列产品和Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组件支持该功能。 

● 具体展示的核数与实际使用的硬件有关。 

Roofline瓶颈分析图（Roofline）：具体介绍请参见8.5 Roofline瓶颈分析图。 

提供计算负载分析（Compute Workload Analysis），以柱状图和数据表格的方 式呈现计算负载数据，帮助开发人员分析Cube/Vector计算资源是否得到了充分利 用。 

提供内存负载分析（Memory Workload Analysis），以内存热力图和数据窗格的 方式呈现各通路的请求数、搬运带宽与利用率，帮助开发人员分析可能存在瓶颈 的通路。 

# 说明

数据窗格呈现的内容会随算子类型而变化。