<!-- Source: 算子开发工具.md lines 9838-9969 | Section: 8.13 典型案例 -->

# 8.13 典型案例

# 8.13.1 采集 Ascend C 算子的性能数据

展示如何使用msProf工具来上板调优一个vector算子，该vector算子可实现两个向量相 加并输出结果的功能。 

# 说明

Kernel直调、单算子API调用和PyTorch框架三种算子调用场景下进行性能采集的操作步骤基本 一致，本示例以Kernel直调场景为例进行介绍。 

# 前提条件

单击Link获取样例工程，为进行算子上板和仿真调优做准备。 

# 说明

● 此样例工程不支持Atlas A3 训练系列产品。 

下载代码样例时，需执行以下命令指定分支版本。 git clone https://gitee.com/ascend/samples.git -b v1.5-8.2.RC1 

参考8.2 使用前准备完成相关环境变量配置。 

# 操作步骤

步骤1 基于样例工程的说明，并参考《Ascend C算子开发指南》中“Kernel直调算子开发 > Kernel直调”章节，完成算子编译前的准备工作。 

步骤2 构建单算子可执行文件。 

以Add算子为例，在样例工程的${git_clone_path}/samples/operator/ascendc/ 0_introduction/3_add_kernellaunch/AddKernelInvocationNeo目录下，执行以下命 令，构建可执行文件。 

```txt
bash run.sh -r npu -v <soc_version> # 运行在昇腾设备上的算子  
bash run.sh -r sim -v <soc_version> # 运行在仿真器上的算子 
```

一键式编译运行脚本完成后，在工程目录下生成NPU侧可执行文件 ascendc_kernels_bbit。 

# 说明

● 本示例中可执行文件的名称（ascendc_kernels_bbit）仅为示例，具体以当前工程中用户实 际编译的脚本为准。 

● 在安装昇腾AI处理器的服务器执行npu-smi info命令进行查询，获取Chip Name信息。实际 配置值为AscendChip Name，例如Chip Name取值为xxxyy，实际配置值为Ascendxxxyy。 

步骤3 导入环境变量。 

```javascript
export LD.Library_PATH=\$\{gitClone_path\}/samples/operator/ascendc/0_introduction/3_add_kernellaunch/AddKernellInvocationNeo/out/lib/:\$LD.Library_PATH 
```

步骤4 采集算子性能数据。 

对于运行在昇腾设备上的算子，使用如下命令完成msprof op性能数据和精细化调优 数据的采集。 

```txt
msprof op ascendc_kernels_bbit 
```

对于运行在仿真器上的算子，使用如下命令完成msprof op simulator性能数据、流 水图和热点图数据的采集。 

```txt
msprof op simulator --soc-version=Ascendxxxxy ascendc_kernels_bbit // xxxyy为用户实际使用的具体芯片类型 
```

步骤5 查看算子性能数据，具体请参见8.3 工具使用章节。 

----结束 

# 8.13.2 通过指令流水图优化算子

展示如何通过msProf工具的指令流水图特性，分析算子的瓶颈点，并实现vector算子 的性能优化。 

# 操作步骤

步骤1 参考msprof op simulator节点，将算子仿真性能数据采集得到的visualize_data.bin文 件导入MindStudio Insight，具体导入操作请参考《MindStudio Insight用户指南》 的“导入性能数据”章节。 

步骤2 查看算子指令流水图。 

可以发现MTE2流水在VADD计算时，没有执行搬运指令，且MTE2流水为该算子的性 能瓶颈，需提高MTE2的搬运效率以实现算子性能优化。 

![](images/c55647bf979399793f8440f46f1b272a32f94a6805106081f785ca1c315a68ce.jpg)


步骤3 对于MTE2搬运效率的提升有多种方式，此处以开启Ascend C算子的double buffer机 制为例。 

例如样例算子核函数中，可通过将TPipe中InitBuffer的第二个参数（BUFFER_NUM） 值从1修改为2，开启double buffer，InitBuffer的使用可参考《Ascend C算子开发接 口》中的“基础API > 内存管理与同步控制 > TPipe > InitBuffer”章节。 

```txt
constexpr int32_t BUFFER_NUM = 2; // tensor num for each queue  
...  
pipe.InitBuffer(inQueueY, BUFFER_NUM, 1024 * sizeof(half));  
... 
```

步骤4 重新执行步骤1，查看优化后的指令流水图。 

在VADD指令计算时，MTE2上的搬运指令也同步执行，实现了更高效的数据搬运。 

![](images/c607668da6957cfc75d90c64b47a57d905834530ce699d3cbb0675a1ae40c1e3.jpg)


----结束 

# 8.13.3 采集 MC2 算子的性能数据

展示如何使用msProf工具来上板调优一个MC2算子，并生成通算流水图。 

# 前提条件

完成MC2算子的开发。 

参考8.2 使用前准备完成相关环境变量配置。 

# 操作步骤

本示例以Ascend CL单算子调用为例，其他调用场景请参见《Ascend C算子开发指 南》。 

步骤1 请参考4.5 算子编译部署，完成算子的编译部署。 

1. 在算子编译文件op_kernel目录下的CMakeLists.txt中引入以下编译选项，使能 MC2算子的AIC打点和代码行映射功能。 add_ops_compile_options(ALL OPTIONS -DASCENDC_TIME_STAMP_ON, -g) 

2. 进入自定义算子工程目录下编译部署算子。 ./build_out/custom_opp_<target_os>_<target_architecture>.run 

步骤2 使用msProf采集MC2算子的性能数据。 

msprof op --output=$HOME/projects/output $HOME/projects/MyApp blockdim 1 // --output为可选参 数,$HOME/projects/MyApp为使用的app,blockdim 1为用户app的可选参数 

步骤3 界面生成以下目录结构和性能数据文件，具体请参见8.11.1 msprof op章节。 

步骤4 将trace.json或visualize_data.bin文件导入MindStudio Insight工具进行可视化呈现， 具体请参见8.4 计算内存热力图、8.7 通算流水图和8.5 Roofline瓶颈分析图。 

----结束