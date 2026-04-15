<!-- Source: 算子开发工具.md lines 9320-9395 | Section: 8.9 算子代码热点图 -->

# 8.9 算子代码热点图

通过msprof op或msprof op simulator生成的visualize_data.bin文件可通过 MindStudio Insight进行可视化呈现。界面支持查看算子源码与指令集的映射关系、耗 时情况等功能，可协助开发者识别热点代码分布，并分析热点函数优化的可行性。具 体特性支持情况请参见表8-11。 


表 8-11 msprof op 和 msprof op simulator 的热点图的功能介绍


<table><tr><td>特性名称</td><td>msprof op</td><td>msprof op simulator</td></tr><tr><td>查看core信息</td><td>不支持</td><td>支持</td></tr><tr><td>查看源码、指令PC地址、PIPE、Source</td><td>支持</td><td>支持</td></tr><tr><td>查看算子源码与指令集的映射关系</td><td>支持</td><td>支持</td></tr><tr><td>查看算子源码与指令的执行次数</td><td>支持</td><td>支持</td></tr><tr><td>查看算子源码与指令的耗时情况（cycles）</td><td>不支持</td><td>支持</td></tr><tr><td>查看寄存器使用情况(GPR Count)</td><td>不支持</td><td>支持</td></tr><tr><td>说明</td><td></td><td></td></tr><tr><td>不支持使用TRACE_START和TRACE_STOP接口查看部分算子的寄存器使用情况。</td><td></td><td></td></tr><tr><td>模拟代码行和指令维度的L2Cache命中率</td><td>支持</td><td>不支持</td></tr><tr><td>查看与GM有关的数据搬运量(Process Bytes)</td><td>支持</td><td>支持</td></tr><tr><td>Vector计算类指令在UB Bank上读和写的冲突情况</td><td>不支持</td><td>支持</td></tr><tr><td>Vector计算单元利用率</td><td>不支持</td><td>支持</td></tr></table>

# 说明

● 若要使用MindStudio Insight进行查看时，需要单独安装MindStudio Insight软件包，具体下 载链接请参见《MindStudio Insight工具用户指南》的“安装与卸载”章节。 

● 将visualize_data.bin文件导入MindStudio Insight的具体操作请参考导入性能数据 《MindStudio Insight工具用户指南》的“算子调优 $>$ 导入性能数据”章节。 

MindStudio Insight具体操作和详细字段解释请参考《MindStudio Insight工具用户指南》 的“算子调优 $>$ 源码（Source）”章节。 

● 添加-g编译选项会在生成的二进制文件中附带调试信息，建议限制带有调试信息的用户程序 的访问权限，确保只有授权人员可以访问该二进制文件。 

● 若不使用llvm-symbolizer组件提供的相关功能，输入msProf的程序编译时不包含-g即可， msProf工具则不会调用llvm-symbolizer组件的相关功能。 

● msprof op算子代码热点图功能不适用于Atlas 推理系列产品。 

● MC2算子和LCCL算子均不支持生成8.9 算子代码热点图。 

# msprof op 热点图


图 8-9 msprof op 源码界面


![](images/9c481d3d51e9e7262ae167d767e0aa1e5f28740f0dc4908f1a1fb94f3bb7ca80.jpg)


在界面顶部，可切换计算单元和核函数文件。 

在左侧界面，提供算子核函数各行代码模拟L2Cache命中率、与GM有关的数据搬 运量及对应的指令数，帮助开发者快速定位瓶颈代码行。 

在右侧界面，提供具体的指令维度模拟L2Cache命中率、与GM有关的数据搬运 量、执行次数及与代码相关联，帮助开发者进一步分析代码耗时长的原因。 

MindStudio Insight时间线和详情页面中L2Cache命中率的差异请参见表8-12。 


表 8-12 MindStudio Insight L2Cache 命中率对比表


<table><tr><td>页面位置</td><td>数据来源</td><td>维度</td></tr><tr><td>时间线</td><td>工具模拟</td><td>代码行和指令维度。</td></tr><tr><td>详情</td><td>真实存在</td><td>核维度。</td></tr></table>

# 说明

查看与GM有关的数据搬运量（Process Bytes）时，不涉及GM单元的情况都显示为NA。 

# msprof op simulator 热点图


图 8-10 msprof op simulator 源码界面


![](images/ad40f4fd5e872993d018f74a5ba4b5bed939c3cb82b8983a5c7e34a3e4ae7e95.jpg)


在界面顶部，可切换计算单元和核函数文件。 

在左侧界面，提供算子核函数各行代码对应的耗时、寄存器使用情况、Vector计 算类指令在UB Bank上读和写的冲突情况、Vector计算单元利用率、与GM有关的 数据搬运量及对应的指令数，帮助开发者快速定位瓶颈代码行。 

在右侧界面，提供具体的指令耗时、寄存器使用情况、与GM有关的数据搬运量、 Vector计算类指令在UB Bank上读和写的冲突情况、Vector计算单元利用率、执行 次数及与代码相关联，帮助开发者进一步分析代码耗时长的原因。 

# 说明

● 通用寄存器的最大数量为32，当寄存器的使用数量达到32时，仿真过程需等到使用中的寄存 器释放后才能运行。 

● 不支持使用TRACE_START和TRACE_STOP接口查看部分算子的寄存器使用情况。 

● 查看与GM有关的数据搬运量（Process Bytes）时，不涉及GM单元的情况都显示为NA。