<!-- Source: 算子开发工具.md lines 8846-9025 | Section: 8.3 工具使用 -->

# 8.3 工具使用

msProf工具包含msprof op和msprof op simulator两种使用方式，协助用户定位算子 内存、算子代码以及算子指令的异常，实现全方位的算子调优。两种使用方式的详细 说明请参考表8-4。 


表 8-4 msprof op 和 msprof op simulator 功能说明表


<table><tr><td>功能名称</td><td>适用场景</td><td>使用方式</td><td>展示的图形</td></tr><tr><td>mspr of op</td><td>适用于实际运行环境中的性能分析,可协助用户定位算子内存和性能瓶颈。</td><td>直接分析运行中的算子,无需额外配置,适合在板环境中快速定位算子性能问题。</td><td>8.4 计算内存热力图
8.5 Roofline瓶颈分析图
8.6 Cache热力图
8.7 通算流水图
8.9 算子代码热点图
说明
若要实现Cache热力图跳转功能,需参考mspr of op配置进行配置。</td></tr><tr><td>mspr of op simulator</td><td>适用于开发和调试阶段,进行详细仿真调优,可协助用户分析算子指令和代码热点问题。</td><td>需要参考mspr of op simulator配置,配置环境变量(如LDLibRARY_PATH)和编译选项(如添加-g生成调试信息),适合在仿真环境中详细分析算子行为。</td><td>8.8 指令流水图
8.9 算子代码热点图
8.10 内存通路吞吐率波形图
说明
资料中的mspr of op simulator的仿真结果仅供参考,算子真实的运行情况以用户的实际仿真数据为准。</td></tr></table>

# 说明

msProf工具的使用依赖CANN包中的msopprof可执行文件，该文件中的接口使用和msprof op一致，该文件为CANN包自带，无需单独安装。 

● 不支持在同一个Device侧同时拉起多个性能采集任务。 

● 使用msprof op和msprof op simulator之前，用户需保证app功能正常。 

# msprof op

步骤1 登录运行环境，使用msprof op 可选参数 app [arguments]格式开启算子上板调优， 可选参数的具体情况请参考表8-2。具体命令示例如下： 

msprof op --output=$HOME/projects/output $HOME/projects/MyApp/out/main // --output为可选参数 $HOME/projects/MyApp/out/main为使用的app 

步骤2 通过以下两种方式执行算子调优： 

基于可执行文件， 

单算子场景，以add custom npu为例。 

示例一： 

```batch
msprof op ./add(custom_npu 
```

示例二： 

```batch
msprof op --aic-metrics=<select_metric> --output=/output_data ./addcustom_npu 
```

# 多算子场景。

若test中有Add，MatlMul，Sub算子，可配合--launch-count和--kernelname使用，可以指定采集Add和Sub算子。 

msprof op --launch-count=10 --kernel-name="Add|Sub" --output=./output_data ./test // ./test为 用户二进制文件，需放置在命令末尾 

基于输入算子二进制文件*.o的配置文件.json，具体请参见8.12 Json配置文件说 明。 

```batch
msprof op --config=/add_test.json --aic-metrics=<select_metric> --output=/output_data 
```

步骤3 命令完成后，会在默认路径或指定的“--output”目录下生成以 

“OPPROF_{timestamp}_XXX”命名的文件夹，在“--aic-metrics”全部开启时，结 构示例如下： 

采集多卡多算子的场景。 

# 说明

对多卡并行的通算融合算子（MC2或LCCL算子）进行调优时，结果目录下会存在若干以 Device ID为名的子目录，这取决于定义时指定的NPU数量，每个NPU的调优结果会分别存 放在对应的Device ID目录下。 

![](images/3d5fe853fd73d4fe25ac26e679e4a9bed8c3ce69220aabcdc3ae2345ead6f0f5.jpg)


采集单卡多算子场景。 

![](images/9887d47962990e9095f698df338bbda31ed740d79a4ed211cbb73382ad706df2.jpg)


采集单卡单算子场景。 

```txt
OPPROF-{timestamp}XXX ——dump 
```

```yaml
- ArithmeticUtilization.csv
- L2Cache.csv
- Memory.csv
- MemoryL0.csv
- MemoryUB.csv
- OpBasicInfo.csv
- PipeUtilization.csv
- ResourceConflictRatio.csv
- visualize_data.bin 
```


表 8-5 msprof op 文件介绍


<table><tr><td>名称</td><td>说明</td></tr><tr><td>dump文件夹</td><td>原始的性能数据,用户无需关注。</td></tr><tr><td>ArithmeticUtilizati on.csv</td><td>cube和vector类型的指令耗时和占比,可参考8.11.1.1 ArithmeticUtilization ( cube及vector类型指令耗时和占 比)。</td></tr><tr><td>L2Cache.csv</td><td>L2 Cache命中率,可参考8.11.1.2 L2Cache ( L2 Cache命中 率)。</td></tr><tr><td>Memory.csv</td><td>UB/L1/L2/主存储器采集内存读写带宽速率,可参考8.11.1.3 Memory(内存读写带宽速率)。</td></tr><tr><td>MemoryL0.csv</td><td>L0A/L0B/L0C采集内存读写带宽速率,可参考8.11.1.4 MemoryL0 ( L0读写带宽速率)。</td></tr><tr><td>MemoryUB.csv</td><td>MTE/vector/scalar采集ub读写带宽速率,可参考8.11.1.5 MemoryUB ( UB读写带宽速率)。</td></tr><tr><td>PipeUtilization.csv</td><td>采集计算单元和搬运单元耗时和占比,可参考8.11.1.7 PipeUtilization(计算单元和搬运单元耗时占比)。</td></tr><tr><td>ResourceConflictR a tio.csv</td><td>UB上的bank group、bank conflict和资源冲突在所有指令中 的占比,可参考8.11.1.8 ResourceConflictRatio(资源冲突 占比)。</td></tr><tr><td>OpBasicInfo.csv</td><td>算子基础信息,包含算子名称、Block Dim和耗时等信息,可 参考8.11.1.6 OpBasicInfo(算子基础信息)。</td></tr><tr><td>visualize_data.bin</td><td>算子基础信息、计算单元负载、热点函数和Roofline瓶颈分析 等信息的可视化呈现文件,具体请参考8.4 计算内存热力图、 8.5 Roofline瓶颈分析图、8.6 Cache热力图、8.7 通算流水 图和8.9 算子代码热点图。 说明 · visualize_data.bin可通过MindStudio Insight工具进行可视化展 示,具体使用方法请参考《MindStudio Insight工具用户指 南》。 · msprof op的热点函数功能仅支持Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组件。 ·当前,仅支持生成MC2和LCCL类型通算融合算子的8.7 通算流水 图。 · MC2和LCCL类型通算融合算子不支持生成8.6 Cache热力图和8.9 算子代码热点图,且不支持Atlas 推理系列产品。</td></tr><tr><td>trace.json</td><td>通算流水可视化呈现文件，Chrome浏览器具体请参考8.7 通算流水图。</td></tr></table>

步骤4 将visualize_data.bin文件导入MindStudio Insight后，将会展示8.4 计算内存热力图、 8.5 Roofline瓶颈分析图、8.6 Cache热力图、8.7 通算流水图和8.9 算子代码热点图。 

步骤5 将trace.json文件导入Chrome浏览器或MindStudio Insight后，将会展示8.7 通算流水 图。 

----结束 

# msprof op simulator

算子调优工具支持仿真环境下的性能数据采集和自动解析。 

# 说明

● 仿真环境不支持采集MC2和HCCL类型的算子。 

● 用户设置的仿真核数不能超过物理核数。 

● 若用户仅需关注部分算子性能时，可在Atlas A3 训练系列产品/Atlas A3 推理系列产品、 Atlas 推理系列产品和Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组 件的单核内调用《Ascend C算子开发接口》中的“算子调测API”章节的TRACE_START和 TRACE_STOP接口。并在编译配置文件中添加-DASCENDC_TRACE_ON，具体操作请参见添 加-DASCENDC_TRACE_ON的方法。然后，才能生成该范围内的流水图信息，具体流水图显 示内容可参考8.8 指令流水图。 

● 用户需在编译配置文件中添加-DASCENDC_TRACE_ON，具体修改方法可参考以下样例工 程。 

AddKernelInvocationNeo算子工程，需在${git_clone_path}/samples/operator/ascendc/ 0_introduction/3_add_kernellaunch/AddKernelInvocationNeo/cmake/npu_lib.cmake文件 中新增以下代码。 

```batch
ascendc.compiledefinitions ( -DASCENDC_TRACE_ON 
```

步骤1 登录运行环境，需要使用msprof op simulator开启算子仿真调优，并配合使用仿真可 选参数和用户待调优程序（app [arguments]）进行调优，仿真可选参数请参考表 8-3。算子仿真调优可以通过以下两种方式执行： 

基于可执行文件。 

单算子场景，以add custom npu为例。 

_ _msprof op simulator --soc-version=Ascendxxxyy --output=./output_data ./add_custom_npu // xxxyy为用户实际使用的具体芯片类型 

– 多算子场景。 

若test中有Add，MatlMul，Sub算子，可配合--launch-count和--kernelname使用，可以指定采集Add和Sub算子。 

msprof op simulator --soc-version=Ascendxxxyy --launch-count=10 --kernel-name="Add|Sub" -- output=./output data ./test //xxxyy为用户实际使用的具体芯片类型，./test需要放置在命令末尾 

基于输入算子二进制文件*.o的配置文件.json。 

# 说明

--config场景下，仅支持使用LD_LIBRARY_PATH导入环境变量，不支持使用--soc-version 参数。 

export LD_LIBRARY_PATH=${INSTALL_DIR}/tools/simulator/Ascendxxxyy/lib:$LD_LIBRARY_PATH // xxxyy为用户实际使用的具体芯片类型 

msprof op simulator --config=./add test.json --output=./output data 

步骤2 命令完成后，会在指定的“--output”目录下生成以“OPPROF_{timestamp}_XXX” 命名的文件夹，结构示例如下： 

采集单个算子场景。 

![](images/a45fb1ba862eedfd3af18f9df3eba41766529d5f29c7f9a3e1db65b80f21a580.jpg)


采集多个算子场景。 

![](images/6ccbb228b34ce51b0593803f374f7cc13380a230a987843d24b3e9950c7540d3.jpg)



表 8-6 msprof op simulator 文件介绍


<table><tr><td colspan="2">名称</td><td>说明</td></tr><tr><td colspan="2">dump文件夹</td><td>原始仿真生成的dump数据存放文件夹。</td></tr><tr><td rowspan="2">simulator文件夹说明</td><td>core*_code_exe.csv</td><td>代码行耗时，*代表0~n核，以便用户快速确定编写的代码中最耗时的部分，可参考8.11.2.1 代码行耗时数据文件。</td></tr><tr><td>core*_instr_exe.csv</td><td>代码指令详细信息，*代表0~n核，以便用户快速确定最耗时的指令，可参考8.11.2.2 代码指令信息文件。</td></tr><tr><td rowspan="2"></td><td>visualize_data.bin</td><td>仿真流水图和仿真热点函数等信息可视化呈现文件,具体请参见8.8指令流水图、8.9算子代码热点图和8.10内存通路吞吐率波形图。说明生成仿真流水图以及仿真热点函数等信息可视化呈现文件visualize_data.bin,该文件可通过MindStudio Insight工具进行可视化展示,具体使用方法请参考《MindStudioInsight工具用户指南》。</td></tr><tr><td>trace.json</td><td>仿真指令流水图文件,包括每个核的子文件以及全部核的汇总文件,可参考8.8指令流水图和8.10内存通路吞吐率波形图。</td></tr></table>

步骤3 可选: 将visualize_data.bin文件导入MindStudio Insight后，将会展示8.8 指令流水 图、8.9 算子代码热点图和8.10 内存通路吞吐率波形图。 

步骤4 将trace.json文件导入Chrome浏览器或MindStudio Insight后，将会展示8.8 指令流水 图和8.10 内存通路吞吐率波形图。 

----结束