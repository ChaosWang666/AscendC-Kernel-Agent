<!-- Source: 算子开发工具.md lines 5557-5715 | Section: 6.3 内存检测 -->

# 6.3 内存检测

内存检测是针对用户程序运行时的一种异常检测，该工具可以检测并报告算子运行中 对外部存储（Global Memory）和内部存储（Local Memory）的越界及未对齐等内存 访问异常。 

# 支持的内存异常类型

内存检测能够检测并报告诸如内存非法读写、多核踩踏、非对齐访问、内存泄漏、非 法释放及分配内存未使用等异常操作，如下表所示。 


表 6-5 内存异常类型


<table><tr><td>异常名</td><td>描述</td><td>位置</td><td>支持地址空间</td></tr><tr><td>非法读写</td><td>由于访问了未分配的内存导致的异常。</td><td>Kernel、Host</td><td>GM、UB、L0{A,B,C}、L1</td></tr><tr><td>多核踩踏</td><td>AI Core核心访问了重叠的内存导致的踩踏问题。</td><td>Kernel</td><td>GM</td></tr><tr><td>非对齐访问</td><td>DMA（负责在Global Memory和LocalMemory之间搬运数据）搬运的地址与内存的最小访问粒度未对齐导致的异常。</td><td>Kernel</td><td>GM、UB、L0{A,B,C}、L1</td></tr><tr><td>非法释放</td><td>对未分配或已释放的地址进行释放导致的异常。</td><td>Host</td><td>GM</td></tr><tr><td>内存泄漏</td><td>申请内存使用后未释放，导致程序在运行过程中内存占用持续增加的异常。</td><td>Host</td><td>GM</td></tr><tr><td>分配内存未使用</td><td>对内存分配后未使用导致的异常。</td><td>Kernel、Host</td><td>GM</td></tr></table>

# 启用内存检测

运行msSanitizer工具时，默认启用内存检测功能（memcheck）。其中， application 为用户程序。 

执行如下命令可显式指定内存检测，默认会开启非法读写、多核踩踏、非对齐访 问和非法释放的检测功能： mssanitizer --tool=memcheck application 

执行如下命令，可在步骤一检测功能项的基础上，手动启用内存泄漏的检测功 能： mssanitizer --tool=memcheck --leak-check=yes application 

执行如下命令，可在步骤一检测功能项的基础上，手动启用分配内存未使用的检 测功能： mssanitizer --tool=memcheck --check-unused-memory=yes application 

# 说明

当用户程序运行完成后，界面将会打印异常报告，异常的具体含义请参见内存异常报告解 析。 

当用户使用PyTorch等框架接入算子时，框架内部可能会通过内存池管理GM内存，而内存池 通常会一次性分配大量GM内存，并在运行过程中复用。此时，若用户对算子进行检测并记 录GM上所有内存分配和释放的信息，会因为内存池的内存管理方式导致检测信息不准确。 因此检测工具提供了手动上报GM内存分配信息的接口，方便用户在算子调用时手动上报该 算子应当使用的GM内存范围，详细接口介绍请参见6.8.2.10 sanitizerReportMalloc和 6.8.2.11 sanitizerReportFree。 

msSanitizer工具也支持对Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异 构组件的AllReduce、AllGather、ReduceScatter、AlltoAll接口及Atlas A3 训练系列产品/ Atlas A3 推理系列产品的AllGather、ReduceScatter、AlltoAllV接口进行非法读写的检测， 具体介绍请参见《Ascend C算子开发接口》中的“高阶API > Hccl > Hccl”章节。 

● msSanitizer工具也支持对通算融合算子的非法读写检测。 

# 内存异常报告解析

内存检测异常报告会输出多种不同类型的异常信息，以下将对一些简单的异常信息示 例进行说明，帮助用户解读异常报告中的信息。 

# 非法读写

非法读写异常信息的产生是由于算子程序中，通过读或写的方式访问了一块未分 配的内存。此错误一般发生在GM或片上内存上，GM异常是由于GM分配的大小 与实际算子程序中访问的范围不一致导致，而片上内存的异常是由于算子程序的 访问范围超过硬件容量上限导致。 

```txt
===ERROR:illegal read of size 224 //异常的基本信息,包含非法读写的类型以及被非法访问的字节数,非法读写包括read(非法读取)和write(非法写入)  
===at 0x12c0c0015000 on GM in addcustom_kernel //异常发生的内存位置信息,包含发生的核函数名、地址空间与内存地址,此处的内存地址指一次内存访问中的首地址  
===in block aiv(0) on device 0 //异常代码对应vector核的block索引  
===code in pc current 0x77c (serialNo:10)//当前异常发生的pc指针和调用api行为的序列号  
===#0 ${ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/impl/dav_c220/  
kernel_operator_data_copy_impl.h:58:9 //以下为异常发生代码的调用栈,包含文件名、行号和列号  
===#1 ${ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/inner/interface/inner_kernel_operator_data_copy_intf.cppm:58:9  
===#2 ${ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/inner/interface/inner_kernel_operator_data_copy_intf.cppm:443:5  
===#3 illegal_read_and_write/addCustom.cpp:18:5 
```

以上示例中，对GM上的“0x12c0c0015000”地址存在非法读取，且导致异常发 生的指令对应于算子实现文件add_custom.cpp的第18行。 

# 说明

不添加编译选项的情况下，异常报告将不会出现以下调用栈信息： 

$= = = = = \# 0$ {\ASCEND_HOME_PATH}]/compiler/tikcpp/tikcfw/impl/dav_c220/  
kernel_operator_data_copy Impl.h:58:9 //以下为异常发生代码的调用栈，包含文件名、行号和列号 $= = = = = \# 1$ {\ASCEND_HOME_PATH}]/compiler/tikcpp/tikcfw/inner/interface/  
inner_kernel_operator_data_copy_intf.cppm:58:9 $= = = = = \# 2$ {\ASCEND_HOME_PATH}]/compiler/tikcpp/tikcfw/inner/interface/  
inner_kernel_operator_data_copy_intf.cppm:443:5 $= = = = = \# 3$ illegal_read_and_write/add/custom.cpp:18:5 

# 多核踩踏

AI Core是昇腾AI处理器中的计算核心，AI处理器内部有多个AI Core，算子运行就 在这些AI Core上。这些AI Core会在计算过程中从GM上搬入或搬出数据。当没有 显式地进行核间同步时，如果各个核之间访问的GM内存存在重叠并且至少有一个 核对重叠地址进行写入时，则会发生多核踩踏问题。这里我们通过所有者的概念 来保证多核之间不会发生踩踏问题，当一块内存被某一个核写入后，这块内存就 由该核所有。当其他核对这块内存进行访问时就会产生out of bounds异常。 

```txt
WARNING: out of bounds of size 256 // 异常的基本信息，包含发生踩踏的字节数
at 0x12c0c00150fc on GM when writing data in addcustom_kernel // 异常发生的内存位置
信息，包含发生的核函数名、地址空间与内存地址，此处的内存地址指一次内存访问中的首地址
in block aiv(9) on device 0 // 异常代码对应vector核的block索引
code in pc current 0x7b8 (serialNo:22) // 当前异常发生的pc指针和调用api行为的序列号
#0 ${ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/impl/dav_c220/
kernel_operator_data_copy_impl.h:103:9 // 以下为异常发生代码的调用栈，包含文件名、行号和列号
#1 ${ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/inner/interface/
inner_kernel_operator_data_copy_intf.cppm:155:9
#2 ${ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/inner/interface/
inner_kernel_operator_data_copy_intf.cppm:461:5
#3 out_ofbound/addcustom.cpp:21:5 
```

以上示例中，共有256个字节的访问发生踩踏，对GM上的“0x12c0c00150fc”地 址进行访问时存在多核踩踏，且导致异常发生的指令对应于算子实现文件 add_custom.cpp的第21行。 

# 非对齐访问

昇腾处理器上包含多种类型的内存，当通过DMA进行访问时，不同类型的内存在 不同处理器上有不同的最小访问粒度。当访问的内存地址与最小访问粒度不对齐 时，会发生数据异常或AI Core异常等问题。访问对齐检测可以在对齐问题发生时 输出对齐异常信息。 

```txt
--------=ERROR: misaligned access of size 13 // 异常的基本信息，包含发生对齐异常操作的字节数
--------= at 0x6 on UB in add_custom_kernel // 异常发生的内存位置信息，包含发生的核函数名、地址
空间与内存地址
--------= in block aiv(0) on device 0 // 异常代码对应vector核的block索引
--------= code in pc current 0x780 (serialNo:33) // 当前异常发生的pc指针和调用api行为的序列号
--------= #0 ${ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/impl/dav_c220/
kernel_operator_data_copy_impl.h:103:9 // 以下为异常发生代码的调用栈，包含文件名、行号和列号
--------= #1 ${ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/inner/interface/
inner_kernel_operator_data_copy_intf.cppm:155:9
--------= #2 ${ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/inner/interface/
inner_kernel_operator_data_copy_intf.cppm:461:5
--------= #3 illegal_align/addCustom.cpp:18:5 
```

以上示例中，共有针对13个字节的对齐异常访问，对UB上的“0x6”地址进行访 问时存在对齐问题，且导致异常发生的指令对应于算子实现文件add_custom.cpp 的第18行。 

# 说明

不添加编译选项的情况下，异常报告将不会出现以下调用栈信息： 

```txt
=== #0 {\ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/impl/dav_c220/  
kernel_operator_data_copy_impl.h:103:9 //以下为异常发生代码的调用栈，包含文件名、行号和列号  
=== #1 {\ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/inner/interface/  
inner_kernel_operator_data_copy_intf.cppm:155:9  
=== #2 {\ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/inner/interface/  
inner_kernel_operator_data_copy_intf.cppm:461:5  
=== #3 illegal_align/add_custom.cpp:18:5 
```

# 内存泄漏

内存检测可以检测出Device侧的内存泄漏问题，这些问题通常是开发者没有正确 释放使用AscendCL接口申请的内存导致的，由于内部存储（Local Memory）目 前不存在内存分配的概念，因此内存泄漏只可能出现在GM上。通过指定命令行参 数“--leak-check=yes”可以开启内存泄漏检测。 

```txt
===ERROR: LeakCheck: detected memory leaks // 检测到内存泄漏  
===Direct leak of 100 byte(s) // 具体每次的内存泄漏信息  
===at 0x124080013000 on GM allocated in add_custom.cpp:14 (serialNo:37)  
===Direct leak of 1000 byte(s)  
===at 0x124080014000 on GM allocated in add_custom.cpp:15 (serialNo:55)  
===SUMMARY: 1100 byte(s) leaked in 2 allocation(s) // 全部内存泄漏的总结，包括发生泄漏的次数以及总共泄漏了多少字节等信息 
```

以上示例中，第一个内存泄漏信息包含了地址空间、内存地址、内存长度以及代 码定位信息，代码定位信息指向具体分配这块内存的调用所在的文件名和行号。 

# 非法释放

非法释放是指对一个未分配的地址或者已释放的地址进行了释放操作，一般发生 在GM上。 

```javascript
===ERROR:illegal free() //异常的基本信息，表明发生了非法释放异常  
===at 0x124080013000 on GM //异常发生的内存位置信息，包含发生的地址空间与内存地址  
===code in add_custom.cpp:84 (serialNo:63) //异常发生的代码定位信息,包含文件名、行号和调用api行为的序列号 
```

以上示例中，对GM上的“0x124080013000”地址进行了非法释放，且导致异常 发生的指令对应于算子实现文件add_custom.cpp的第84行。 

# 分配内存未使用

分配内存未使用是指算子运行时申请了内存，但直到算子运行完成，都没有使用 该内存。该异常场景一般是算子使用了错误的内存或算子逻辑存在问题，一般发 生在GM上。 

```txt
=WARNING: Unused memory of 1000 byte(s) //异常的基本信息，表明检测到内存分配未使用异常
=at 1240c0016000 on GM //异常发生的内存位置信息,包含发生的地址空间与内存地址
=code in addcustom.cpp:2 (serialNo:69) //异常发生的代码定位信息,包含文件名、行号和调用api行为的序列号
=SUMMARY: 1100byte(s) unused memory in 2 allocation(s) //内存分配未使用的总结信息，包括未使用内存块的个数及字节等信息 
```