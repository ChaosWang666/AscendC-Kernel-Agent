<!-- Source: 算子开发工具.md lines 9164-9205 | Section: 8.6 Cache 热力图 -->

# 8.6 Cache 热力图

针对用户程序Kernel函数内的L2 Cache访问情况，msProf工具可以记录并通过 MindStudio Insight工具进行可视化呈现Cache热力图，该热力图可显示对应指令信 息，以便用户优化L2Cache命中率，从而优化算子程序。 

# 说明

● 若要使用MindStudio Insight进行查看时，需要单独安装MindStudio Insight软件包，具体下 载链接请参见《MindStudio Insight工具用户指南》的“安装与卸载”章节。 

● 将visualize_data.bin文件导入MindStudio Insight的具体操作请参考导入性能数据 《MindStudio Insight工具用户指南》的“算子调优 $>$ 导入性能数据”章节。 

● MindStudio Insight具体操作和详细字段解释请参考《MindStudio Insight工具用户指南》 的“算子调优 $>$ 缓存（Cache）”章节。 

● 添加-g编译选项会在生成的二进制文件中附带调试信息，建议限制带有调试信息的用户程序 的访问权限，确保只有授权人员可以访问该二进制文件。 

● 若不使用llvm-symbolizer组件提供的相关功能，输入msProf的程序编译时不包含-g即可， msProf工具则不会调用llvm-symbolizer组件的相关功能。 

● Cache热力图功能不适用于Atlas 推理系列产品。 

● MC2算子和LCCL算子均不支持生成8.6 Cache热力图。 


图 8-5 Cache 热力图


![](images/290bcdb3c1b7ca2788dda7f4d3554387a60d3d9c5ced856000d18383f411f4fb.jpg)


Hit展示Cacheline的命中情况，Miss展示Cacheline未命中情况，以便用户分析 L2Cache的使用情况， 

在缓存（Cache）界面，选择命中和未命中事件图，单击放大，在放大的事件图中 右键单击所选内存单元格，选择“显示指令”，可跳转至源码（Source）界面， 并高亮显示相关指令行。 


图 8-6 Cacheline 对应的算子代码热点图


![](images/36c0099e2f8e06906fee4eb566c82e0eaadb0cdc1fbd2528d47af7b21b32bd3a.jpg)


# 说明

若要使用Cache热力图跳转至算子代码热点图功能，需参考msprof op配置，提前进行配 置。