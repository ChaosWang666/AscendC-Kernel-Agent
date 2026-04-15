<!-- Source: 算子开发指南.md lines 6309-6694 | Section: 2.7 调试调优 -->

# 2.7 调试调优

# 2.7.1 概述

Ascend C算子调试的整体方案如下：开发者通过调用Ascend C类库编写Ascend C算子 Kernel侧源码，Kernel侧源码通过通用的GCC编译器进行编译，编译生成通用的CPU域 的二进制，可以通过gdb通用调试工具等调试手段进行调试；Kernel侧源码通过毕昇编 译器进行编译，编译生成NPU域的二进制文件，可使用printf/assert等接口进行数据打 印，也可通过仿真打点图或者Profiling工具进行上板数据采集等方式进行调试。 

![](images/9af444bae098f3e65611858fa531dad949db0e6ba8d9b401c9f2ea726f698ce6.jpg)


具体的调试调优方法和使用的工具列表如下： 


表 2-30 调试调优方法和使用的工具列表


<table><tr><td>分类</td><td>子分类</td><td>方法</td></tr><tr><td rowspan="4">功能调试</td><td>CPU域孪生调试</td><td>孪生调试:相同的算子代码可以在CPU域调试精度,NPU域调试性能。在CPU域可以进行gdb调试、使用printf命令打印。</td></tr><tr><td rowspan="3">NPU域上板调试</td><td>printf/assert:printf主要用于打印标量和字符串信息;assert主要用于在代码中设置检查点,当某个条件不满足时,程序会立即终止并报错。</td></tr><tr><td>DumpTensor:使用DumpTensor接口打印指定Tensor的数据,只支持SIMD编程场景。</td></tr><tr><td>上板调试工具:使用msDebug工具调试NPU侧运行的算子程序,在真实的硬件环境中,对算子的输入输出进行测试,以验证算子的功能是否正确。具体功能包括断点设置、打印变量和内存、单步调试、中断运行等。当前SIMT编程场景不支持。</td></tr><tr><td></td><td></td><td>内存检测工具: 使用msSanitizer工具进行内存检测, 可以检测并报告算子运行中对外部存储(Global Memory)和内部存储(Local Memory)的越界及未对齐等内存访问异常。</td></tr><tr><td>性能调优</td><td>-</td><td>msprof工具: msProf工具用于采集和分析运行在AI处理器上算子的关键性能指标, 用户可根据输出的性能数据, 快速定位算子的软、硬件性能瓶颈, 提升算子性能的分析效率。当前支持基于不同运行模式(上板或仿真)和不同文件形式(可执行文件或算子二进制.o文件)进行性能数据的采集和自动解析。</td></tr></table>

# 2.7.2 功能调试

# 2.7.2.1 CPU 域孪生调试

本节介绍CPU域调试的方法：CPU侧验证核函数，gdb调试、使用printf命令打印。当 前SIMT编程场景不支持。 

# 说明

CPU调测过程中，配置日志相关环境变量，可以记录程序的运行过程及异常信息，有助于开发者 进行功能调测。 

关于环境变量的使用约束以及详细说明，可参见日志。 

# CPU 侧验证核函数

在非昇腾设备上，开发者可以利用CPU仿真环境先行进行算子开发和测试，并在准备 就绪后，利用昇腾设备进行加速计算。在2.3 编译与运行章节，我们已经介绍了算子 Kernel程序NPU域的编译运行。相比于NPU域的算子运行逻辑，CPU域调试将算子 Kernel程序以Host程序的形式进行编译，此时算子Kernel程序链接CPU调测库，执行 编译生成的可执行文件，可以完成算子CPU域的运行验证。CPU侧的运行程序，通过 GDB通用调试工具进行单步调试，可以精准验证程序执行流程是否符合预期。 


图 2-37 CPU 域和 NPU 域的核函数运行逻辑对比


![](images/79d5cb13e12b2433747695bac2dc716cb9e54c78348bf2d875840a1f4bf85f0d.jpg)


![](images/2ee4b3c7b7607bd3da9d282b1c19c16deeaad54d28c929941f8e7c1f62ba6986.jpg)


推荐使用CMake编译方式，可在最小化修改的情况下快速开启CPU域孪生调试功能。 

步骤1 启用CPU域调试需包含"cpu_debug_launch.h"头文件。 

bisheng编译器在CPU调试模式下会对<<<>>>调用核函数的过程进行转义，实现核函 数在CPU域下的调用，相关调用函数定义在"cpu_debug_launch.h"中，在使用<<<>>> 语法调用核函数的源文件中，请通过以下方式包含必需的头文件： 

```cpp
ifdef ASCENDC_CPU_DEBUG #include "cpuDebug_launch.h" #endif 
```

步骤2 通过在CMake配置阶段传入变量CMAKE_ASC_RUN_MODE和 

CMAKE_ASC_ARCHITECTURES即可开启CPU域编译。命令示例如下： 

```batch
cmake -B build -DCMAKE_ASS.run_MODE=cpu -DCMAKE_ASS_archITECTURES=dav-2201 
```

cpu表示开启CPU域编译，dav-后为NPU架构版本号，请根据实际情况进行填写。 

其他CMakeLists.txt项目配置2.3.1.4 通过CMake编译进行编写。 

----结束 

# 说明

为了实现CPU域与NPU域代码归一，框架在CPU域中仅对部分acl接口进行适配，开发者在使用 CPU域调测功能时，仅支持使用如下acl接口，并且不支持用户自行链接ascendcl库： 

● 有实际功能接口，支持CPU域调用 

aclDataTypeSize、aclFloat16ToFloat、aclFloatToFloat16。 

aclrtMalloc、aclrtFree、aclrtMallocHost、aclrtFreeHost、aclrtMemset、 aclrtMemsetAsync、aclrtMemcpy、aclrtMemcpyAsync、aclrtMemcpy2d、 aclrtMemcpy2dAsync、aclrtCreateContext、aclrtDestroyContext。 

● 无实际功能接口，打桩实现。 

Profiling数据采集 

aclprofInit、aclprofSetConfig、aclprofStart、aclprofStop、aclprofFinalize。 

● 系统配置 

aclInit、aclFinalize、aclrtGetVersion。 

运行时管理 

aclrtSetDevice、aclrtResetDevice、aclrtCreateStream、 aclrtCreateStreamWithConfig、aclrtDestroyStream、aclrtDestroyStreamForce、 aclrtSynchronizeStream、aclrtCreateContext、aclrtDestroyContext。 

# gdb 调试

可使用gdb单步调试算子计算精度。由于cpu调测已转为多进程调试，每个核都会拉起 独立的子进程，故gdb需要转换成子进程调试的方式。针对耦合架构，每个AI Core会 拉起1个子进程。针对分离架构，默认每个AI Core会拉起3个子进程，1个Cube，2个 Vector。 

调试单独一个子进程 

启动gdb，示例中的add_custom_cpu为CPU域的算子可执行文件，参考修改并执 行一键式编译运行脚本，将一键式编译运行脚本中的run-mode设置成cpu，即可 编译生成CPU域的算子可执行文件。 

gdb启动后，首先设置跟踪子进程，之后再打断点，就会停留在子进程中，但是这 种方式只会停留在遇到断点的第一个子进程中，其余子进程和主进程会继续执行 直到退出。涉及到核间同步的算子无法使用这种方法进行调试。 

gdb --args add_custom_cpu // 启动gdb，add_custom_cpu为算子可执行文件 

(gdb) set follow-fork-mode child 

调试多个子进程 

如果涉及到核间同步，那么需要能同时调试多个子进程。 

在gdb启动后，首先设置调试模式为只调试一个进程，挂起其他进程。设置的命令 如下： 

(gdb) set detach-on-fork off 

查看当前调试模式的命令为： 

(gdb) show detach-on-fork 

中断gdb程序要使用捕捉事件的方式，即gdb程序捕捉fork这一事件并中断。这样 在每一次起子进程时就可以中断gdb程序。设置的命令为： 

(gdb) catch fork 

当执行r后，可以查看当前的进程信息： 

(gdb) info inferiors 

Num Description 

* 1 process 19613 

可以看到，当第一次执行fork的时候，程序断在了主进程fork的位置，子进程还未 生成。 

执行c后，再次查看info inferiors，可以看到此时第一个子进程已经启动。 

```txt
(gdb) info inferiors Num Description *1 process 19613 2 process 19626 
```

这个时候可以使用切换到第二个进程，也就是第一个子进程，再打上断点进行调 试，此时主进程是暂停状态： 

```txt
(gdb) inferior 2  
[Switching to inferior 2 [process 19626] ($HOME/demo)]  
(gdb) info inferiors  
Num Description  
1 process 19613  
* 2 process 19626 
```

请注意，inferior后跟的数字是进程的序号，而不是进程号。 

如果遇到同步阻塞，可以切换回主进程继续生成子进程，然后再切换到新的子进 程进行调试，等到同步条件完成后，再切回第一个子进程继续执行。 

如下是调试一个单独子进程的命令样例： 

```txt
gdb --args add(custom_cpu set follow-fork-mode child break add_custom.cpp:45 run list backtrace print i break add_custom.cpp:56 continue display xLocal quit 
```

# 使用 printf 打印命令打印

在代码中直接编写printf(...)来观察数值的输出。样例代码如下： 

printf("xLocal size: %d\n", xLocal.GetSize()); 

printf("tileLength: %d\n", tileLength); 

# 2.7.2.2 NPU 域上板调试

NPU域上板调试手段主要包含上板数据打印、msSanitizer内存异常检测和msDebug单 步调试等功能，数据打印包括printf、DumpTensor两种方式，其中，DumpTensor是 SIMD编程独有功能，用于打印指定Tensor的数据。 

# 通过 printf 打印数据

printf主要用于打印标量和字符串信息，SIMT编程及SIMD编程均支持。 

printf示例如下，printf接口的使用说明和具体约束请参考printf。 

```txt
printf("fmt string %d", 0x123); 
```

# 说明

printf接口打印功能会对算子实际运行的性能带来一定影响，通常在调测阶段使用。开发者可以 按需关闭打印功能。具体方法请参考printf。 

# SIMD 编程通过 DumpTensor 打印进行调试

DumpTensor是SIMD编程场景独有的打印功能，用于NPU域上板打印指定Tensor的数 据。 

# 具体的使用方法如下：

在算子kernel侧实现代码中需要输出日志信息的地方调用DumpTensor接口打印相关内 容。 

如下所示，srcLocal表示待打印的Tensor；5表示用户的自定义附加信息，比如当前的 代码行号；dataLen表示元素个数。DumpTensor接口的使用说明和具体约束请参考 DumpTensor。 DumpTensor(srcLocal,5, dataLen); 

Dump时，每个block核的dump信息前会增加对应信息头DumpHead（32字节大 小），用于记录核号和资源使用信息；每次Dump的Tensor数据前也会添加信息头 DumpTensorHead（32字节大小），用于记录Tensor的相关信息。打印结果的样例如 下： 

```csv
DumpTensor: desc=5, addr=0, data_type=float16, position=UB, dump_size=32  
[19.000000, 4.000000, 38.000000, 50.000000, 39.000000, 67.000000, 84.000000, 98.000000, 21.000000, 36.000000, 18.000000, 46.000000, 10.000000, 92.000000, 26.000000, 38.000000, 39.000000, 9.000000, 82.000000, 37.000000, 35.000000, 65.000000, 97.000000, 59.000000, 89.000000, 63.000000, 70.000000, 57.000000, 35.000000, 3.000000, 16.000000, 42.00000]  
DumpTensor: desc=5, addr=10o, data_type=float16, position=UB, dump_size=32  
[6.ooooo, 34.ooooo, 52.ooooo, 38.ooooo, 73.ooooo, 38.ooooo, 35.ooooo, 14.ooooo, 67.ooooo, 62.ooooo, 3o.oooo, 49.ooooo, 86.ooooo, 37.ooooo, 84.ooooo, 18.ooooo, 38.ooooo, 18.ooooo, 44.ooooo, 21.ooooo, 86.ooooo, 99.ooooo, 13.ooooo, 79.ooooo, 84.ooooo, 9.ooooo, 48.ooooo, 74.ooooo, 52.ooooo, 99.ooooo, 8O.ooooo, 53.ooooo]  
...  
DumpTensor: desc=5, addr=O, data_type=float16, position=UB, dump_size=32  
[35.ooooo, 41.ooooo, 41.ooooo, 22.ooooo, 84.ooooo, 49.ooooo, 6O.ooooO,O.ooooO,O.OoOOO O,O.oOOO O,O.oOOO O,O.oOOO O,O.oOOO O,O.oOOO O,O.oOOO O,O.oOOO O,O.oOOO O,O.oOOO O,O.oOOO O,O.oOOO O,O.oOOO O,O.oOOO O,O.oOOO O,O.oOOO O,O.oOOO O,O.oOOO O,O.oOOO O,O.oOOO O,O.oOOO O,O.eOOOO O,O.eOOOO O,O.eOOOO O,O.eOOOO O,O.eOOOO O,O.eOOOO O,O.eOOOO O,O.eOOOO O,O.eOOOO O,O.eOOOO O,O.eOOOO O,O.eOOOO O,O.eOOOO O,O.eOOOO O,O.eOOOO O,O.eOOOO O,O.eOOOO O,O.eOOOO O,O.eOOOO O,O.eOOOO O,O.eOOoo O,O.eOOOO O,O.eOOoo O,O.eOOoo O,O.eOOoo O,O.eOOoo O,O.eOOoo O,O.eOOoo O,O.eOOoo O,O.eOOoo O,O.eOOoo O,O.eOOoo O,O.eOOoo O,o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o.o o 
```

# 说明

DumpTensor接口打印功能会对算子实际运行的性能带来一定影响，通常在调测阶段使用。开发 者可以按需关闭打印功能。具体方法请参考DumpTensor。 

# 使用 msSanitizer 工具进行异常检测

msSanitizer工具是基于AI处理器的异常检测工具，包含了单算子开发场景下的内存检 测、竞争检测、未初始化检测和同步检测四个子功能。 

内存检测：工具可以在用户开发算子的过程中，协助定位非法读写、多核踩踏、 非对齐访问、内存泄漏以及非法释放等内存问题。同时工具也支持对CANN软件 栈的内存检测，帮助用户定界软件栈内存异常发生的模块。 

竞争检测：工具可以协助用户定位由于竞争风险可能导致的数据竞争问题，包含 核内竞争和核间竞争问题。其中，核内竞争包含流水间竞争和流水内竞争。 

未初始化检测：工具可以协助用户定位由于内存未初始化可能导致的脏数据读取 问题。 

同步检测：工具可以协助用户定位由于前序算子中的未配对同步指令导致的后续 算子同步失败的问题。 

具体使用方法请参考异常检测（msSanitizer）。 

# 该功能仅在如下场景支持：

通过2.10.7 基于样例工程完成Kernel直调方式调用算子。 

通过单算子API调用方式调用算子。 

间接调用单算子API(aclnnxxx)接口：Pytorch框架单算子直调的场景。 

# 使用 msDebug 工具进行算子调试

msDebug是一款面向昇腾设备的算子调试工具，用于调试NPU侧运行的算子程序，为 算子开发人员提供调试手段，当前只支持SIMD编程场景的程序调试，暂不支持SIMT编 程场景的程序调试。msDebug工具支持调试所有的昇腾算子，包含Ascend C算子 （Vector、Cube以及融合算子）程序。具体功能包括断点设置、打印变量和内存、单 步调试、中断运行、核切换、检查程序状态、调试信息展示、解析Core dump文件， 用户可根据实际情况进行选择。具体使用方法请参考算子调试（msDebug）。 

通过2.10.7 基于样例工程完成Kernel直调方式调用算子。 

通过单算子API调用方式调用算子。 

间接调用单算子API(aclnnxxx)接口：Pytorch框架单算子直调的场景。 

# 2.7.3 性能调优

# 性能采集与分析工具

通过毕昇编译器编译生成可执行程序后，使用msProf工具运行NPU模式下生成的可执 行文件，可以采集Ascend C算子在AI处理器上执行的性能数据，进行性能精细调优。 

Profiling性能数据采集：使用msprof工具采集Ascend C算子在AI 处理器上执行的 性能数据。 

Roofline瓶颈分析：通过msprof op生成的visualize_data.bin文件可通过 MindStudio Insight进行可视化呈现，Roofline瓶颈分析图可构建出处理器的性能 模型，然后利用该性能模型快速评估出算子的理论性能极限，协助开发者快速识 别瓶颈类型。 

指令流水图分析：通过msprof op simulator生成visualize_data.bin文件或 trace.json文件，并进行可视化呈现。指令流水图以指令维度展示时序关系，并关 联调用栈快速定位瓶颈位置。 

性能调优工具的具体使用方法请参考算子调优（msProf）。 

# NPU 域上板性能调优

算子程序通过毕昇编译器编译生成可执行程序后，可以通过msprof op在NPU上完成性 能采集。 

步骤1 参考2.3.1 AI Core SIMD编译，编译add算子样例，生成可执行文件。 

dav-后为NPU架构版本号，请根据实际情况进行替换，各产品型号对应的架构版本号 请通过对应关系表进行查询。 

```batch
bisheng add(custom.asc -o add(custom --npu-arch=dav-2201 
```

步骤2 使用msprof op调用算子可执行文件进行性能采集。 

```batch
msprof op ./add(custom 
```

步骤3 查看性能数据，了解当前算子性能瓶颈。 

```txt
性能数据文件夹结构示例：  
——dump #原始的性能数据，用户无需关注  
——ArithmeticUtilization.csv # cube/vector指令cycle占比，建议优化算子逻辑，减少冗余计算指令  
——L2Cache.csv # L2 Cache命中率，影响MTE2，建议合理规划数据搬运逻辑，增加命中率  
——Memory.csv # UB，L1和主存储器读写带宽速率，单位GB/s  
——MemoryL0.csv # LOA，LOB，和LOC读写带宽速率，单位GB/s  
——MemoryUB.csv # Vector和Scalar到UB的读写带宽速率，单位GB/s  
——OpBasicInfo.csv # 算子基础信息  
——PipeUtilization.csv # pipe类指令耗时和占比，建议优化数据搬运逻辑，提高带宽利用率  
——ResourceConflictRatio.csv # UB上的bank group、bank conflict和资源冲突率在所有指令中的占比，建议减少/避免对于同一个bank读写冲突或bank group的读读冲突  
——visualize_data.bin # MindStudio Insight呈现文件 
```

# ----结束

对于SIMT编程场景，只需遵循AI Core SIMT编译指导进行算子编译，生成可执行文件 后，按照上述步骤2和步骤3使用msprof工具执行程序，以获取算子执行的性能数据。 

# NPU 域性能仿真

在非昇腾设备上，通过毕昇编译器仿真编译后生成可执行程序，可以通过msprof op simulator完成性能流水仿真。当前仅支持SIMD编程场景，SIMT编程场景不支持。 

# 通过CMake方式仿真编译算子

灵活控制不同的target是否开启仿真编译。修改CMakeList，使用 target_link_libraries与target_link_directories手动配置链接库与路径： 

```cmake
findpackage(ASCREQUIRED)  
project(kernel_samples LANGUAGE ASC CXX)  
add_executable demo  
    add_custom.asc  
)  
set_target_propertyssdemoPROPERTIESLINKFLAGS "-Wl,--disable-new-dtags" ## 由于仿真库会依赖当前目录的其他非链接的so，需要开启RPATH传递依赖目录  
）  
target_linklibrariesdemoPRIVATEruntimeCAModelnpu_drvCAModel##仿真编译需要链接的som  
）  
#{$INSTALL_DIR}请替换为CANN软件安装后文件存储路径。以root用户安装为例，安装后文件默认存储路径为：/usr/local/Ascend/cann。  
target_linkdirectoriesdemoPRIVATE{{INSTALL_DIR}/tools/simulator/dav_2201/lib##仿真库所在的目录，其中dav_2201目录名称与芯片版本相关  
）  
target.compile-optionsdemo PRIVATE$<$(COMPILE(Language:ASC>:_npu-arch=dav-2201> 
```

其中仿真库所在目录与NPU架构版本号之间的关系如下，目录名使用下划线 连接“dav”和架构版本号。 


表 2-31 simulator 目录名称与 npu-arch 关系


<table><tr><td>npu-arch</td><td>simulator目录名称</td></tr><tr><td>dav-2002</td><td>dav_2002</td></tr><tr><td>dav-2201</td><td>dav_2201</td></tr><tr><td>dav-3510</td><td>dav_3510</td></tr></table>

其中仿真编译所依赖的库介绍如下，开启仿真编译时，需要优先链接，确保 优先使用仿真库的符号，防止出现运行时coredump等异常情况。 


表 2-32 仿真编译依赖库介绍


<table><tr><td>名称</td><td>作用描述</td></tr><tr><td>libruntime(camodel.so</td><td>camodel仿真运行时库，负责NPU算子仿真环境的运行时功能支持。</td></tr><tr><td>libnpu_drv(camodel.so</td><td>仿真驱动库，对真实的驱动接口打桩，模拟真实NPU驱动行为，提供硬件交付的接口仿真。</td></tr></table>

# 通过向CMake传入变量CMAKE_ASC_RUN_MODE和

CMAKE_ASC_ARCHITECTURES来统一开启仿真编译。命令示例如下： 

sim表示开启仿真编译，dav-后为NPU架构版本号，请根据实际情况进行填 写。 

cmake -B build -DCMAKE_ASC_RUN_MODE=sim -DCMAKE_ASC_ARCHITECTURES=dav-2201 

# 说明

使用命令行往CMake传入变量的方式全局生效，会对CMakeList中所有的target开启 sim模式。 

# 通过命令行方式仿真编译算子可执行程序

# ${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。以root用户安装为例，安装后文件默认存储路 径为：/usr/local/Ascend/cann。 

# 设置simulator目录名称 

export SIMULATOR_FOLDER=dav_2201 

# 编译算子object: bisheng -c [算子源文件] -o [输出产物名称] --npu-arch=[NPU架构版本号]，--runmode=sim 

bisheng -c add_custom.asc -o add_custom.asc.o --npu-arch=dav-2201 --run-mode=sim 

# 将add算子object转为可执行程序 

bisheng -Wl,--disable-new-dtags -L${INSTALL_DIR}/tools/simulator/${SIMULATOR_FOLDER}/lib -Wl,- rpath,${INSTALL_DIR}/tools/simulator/${SIMULATOR_FOLDER}/lib -lruntime_camodel - lnpu_drv_camodel -lm -lstdc $^ { + + }$ -lascendcl -lascendc_runtime -lprofapi -lunified_dlog -lmmpa - lascend_dump -lc_sec -lerror_manager -lnpu_drv add_custom.asc.o -o add_custom 

编译时除了需要连接仿真库libruntime_camodel.so和libnpu_drv.so，还需要链接 libascendc_runtime.a、libruntime.so、libprofapi.so、libunified_dlog.so、 libmmpa.so、libascend_dump.so、libc_sec.so、liberror_manager.so、 libascendcl.so（具体说明参考表2-12）和第三方库libstdc++.so、libm.so。 

# 性能流水仿真

使用msprof op simulator并获取仿真数据。 

msprof op simulator ./add_custom 

# 仿真数据说明

![](images/0eba688f585ad60c282c280d7e814ecbead328e6998624e5e0a340692df24504.jpg)


# 原始的性能数据，用户无需关注 # 算子基础信息 

```txt
core0.cubecore0
...
core23.cubecore0
...
trace.json # Edge/Chrome Trace Viewer/Perfetto呈现文件
visualize_data.bin # MindStudio Insight呈现文件 
```