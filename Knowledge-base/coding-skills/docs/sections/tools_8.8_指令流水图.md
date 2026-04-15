<!-- Source: 算子开发工具.md lines 9255-9319 | Section: 8.8 指令流水图 -->

# 8.8 指令流水图

通过msprof op simulator生成的visualize_data.bin文件或trace.json文件，并进行可 视化呈现。指令流水图以指令维度展示时序关系，并关联调用栈快速定位瓶颈位置。 支持以下两种可视化呈现方式： 

# 说明

● 添加-g编译选项会在生成的二进制文件中附带调试信息，建议限制带有调试信息的用户程序 的访问权限，确保只有授权人员可以访问该二进制文件。 

● 若不使用llvm-symbolizer组件提供的相关功能，输入msProf的程序编译时不包含-g即可， msProf工具则不会调用llvm-symbolizer组件的相关功能。 

● 若用户仅需关注部分算子性能时，可在Atlas A3 训练系列产品/Atlas A3 推理系列产品、 Atlas 推理系列产品和Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组 件的单核内调用《Ascend C算子开发接口》中的“算子调测API”章节的TRACE_START和 TRACE_STOP接口。并在编译配置文件中添加-DASCENDC_TRACE_ON，具体操作请参见添 加-DASCENDC_TRACE_ON的方法。然后，才能生成该范围内的流水图信息，具体流水图显 示内容可参考8.8 指令流水图。 

● 用户需在编译配置文件中添加-DASCENDC_TRACE_ON，具体修改方法可参考以下样例工 程。 

AddKernelInvocationNeo算子工程，需在${git_clone_path}/samples/operator/ascendc/ 0_introduction/3_add_kernellaunch/AddKernelInvocationNeo/cmake/npu_lib.cmake文件 中新增以下代码。 

```batch
ascendc.compiledefinitions ( -DASCENDC_TRACE_ON 
```

# Chrome浏览器

在Chrome浏览器中输入“chrome://tracing”地址，并将通过msprof op simulator生成指令流水图文件（trace.json）拖到空白处打开，键盘上输入快捷 键（W：放大，S：缩小，A：左移，D：右移）可进行查看。关键字段说明如表 8-10。 


表 8-10 关键字段说明


<table><tr><td>字段名</td><td>字段含义</td></tr><tr><td>VECTOR</td><td>向量运算单元。</td></tr><tr><td>SCALAR</td><td>标量运算单元。</td></tr><tr><td>CUBE</td><td>矩阵乘运算单元。</td></tr><tr><td>MTE1</td><td>数据搬运流水,数据搬运方向为:L1-&gt;{LOA/LOB,UBUF}。</td></tr><tr><td>MTE2</td><td>数据搬运流水,数据搬运方向为:{DDR/GM,L2}-{L1,LOA/B,UBUF}。</td></tr><tr><td>MTE3</td><td>数据搬运流水,数据搬运方向为:UBUF-&gt;{DDR/GM,L2,L1},L1-&gt;{DDR/L2}。</td></tr><tr><td>FIXP</td><td>数据搬运流水,数据搬运方向为:FIXPIPE LOC-&gt;OUT/L1。(仅Atlas A2训练系列产品/Atlas 800I A2推理产品/A200I A2Box异构组件支持展示)</td></tr><tr><td>FLOWCTRL</td><td>控制流指令。</td></tr><tr><td>CAHEMISS</td><td>未命中ICache。</td></tr><tr><td>USEMASK</td><td>自定义打点范围。
说明
若同一个USEMASK内存在范围嵌套或只有TRACE_START无TRACE_STOP时,不能正常绘制指令流水图。</td></tr><tr><td>ALL</td><td>表示在这个通道的指令在所有通道都执行。</td></tr></table>

# MindStudio Insight

通过msprof op simulator生成的trace.json文件或visualize_data.bin文件可导入 MindStudio Insight进行可视化呈现。 

# 说明

● 若要使用MindStudio Insight进行查看时，需要单独安装MindStudio Insight软件包， 具体下载链接请参见《MindStudio Insight工具用户指南》的“安装与卸载”章节。 

● 将visualize_data.bin文件导入MindStudio Insight的具体操作请参考导入性能数据 《MindStudio Insight工具用户指南》的“算子调优 $>$ 导入性能数据”章节。 

MindStudio Insight具体操作和详细字段解释请参考《MindStudio Insight工具用户指 南》的“系统调优 $>$ 时间线（Timeline）”章节。 

添加-g编译选项会在生成的二进制文件中附带调试信息，建议限制带有调试信息的用户 程序的访问权限，确保只有授权人员可以访问该二进制文件。 

# 指令流水图介绍（以 MindStudio Insight 为例）

MindStudio Insight工具以时序图方式为用户提供指令在昇腾AI处理器上的运行情况， 用户可通过分析时序图中的指令详情、指令执行时间、指令关联代码的调用栈及指令/ 流水间同步连线等信息，识别微观指令的时序优化点。 


图 8-8 时间线界面


![](images/bdd2eaeb798f5f7bf5ff397532e7a72a63365f490217c6b73c46c2b8fd1eb8f7.jpg)


展示各PIPE中各指令的运行时长以及不同PIPE间的指令依赖关系，帮助用户分析 流水排布间可能存在的性能优化点。 

支持将流水指令信息与代码关联，指导用户如何基于代码去优化流水排布。 

# 说明

通过观察Timeline的流水排布等信息判断算子运行过程中可能存在的性能问题，如指令间未能有 效并行等。