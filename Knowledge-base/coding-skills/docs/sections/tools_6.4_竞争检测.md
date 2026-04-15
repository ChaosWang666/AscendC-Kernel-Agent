<!-- Source: 算子开发工具.md lines 5716-5769 | Section: 6.4 竞争检测 -->

# 6.4 竞争检测

竞争检测用于解决在并行计算环境中内存访问竞争的问题。在昇腾处理器架构下，外 部存储和内部存储通常被用作临时缓冲区保存正在处理的数据，外部存储或内部存储 可以同时被多个流水访问，外部存储还可以被多个核访问，算子程序若没有正确处理 核间、流水间或流水内的同步，就可能会导致数据竞争的问题。 

# 内存竞争类型

内存竞争是指两个内存事件（其中至少有一个为写事件）尝试访问同一块内存时，出 现不符合基于预期执行顺序的结果。这种异常会导致数据竞争，从而使程序的运行或 输出取决于内存事件的实际执行顺序。竞争检测功能可识别以下三种典型的内存竞 争： 


表 6-6 内存竞争类型


<table><tr><td>异常名</td><td>描述</td><td>位置</td><td>支持地址空间</td></tr><tr><td>Write-After-Write(WAW)</td><td>当两个内存事件尝试向同一块内存写入时，可能存在这种异常，导致内存结果值取决于两个内存事件的实际访问顺序。</td><td rowspan="3">Kernel</td><td rowspan="3">GM、UB、L0{A,B,C}、L1</td></tr><tr><td>Write-After-Read(WAR)</td><td>当两个内存事件（一个事件执行读取操作，另一个事件执行写入操作）尝试访问同一块内存时，可能存在这种异常，即写操作事件实际在读操作事件之前执行完毕，并导致读取到的内存值并非预期起始值。</td></tr><tr><td>Read-After-Write(RAW)</td><td>当两个内存事件（一个事件执行读取操作，另一个事件执行写入操作）尝试访问同一块内存时，可能存在这种异常，即读操作事件实际在写操作事件之前执行完毕，并导致读取到的内存值还未更新。</td></tr></table>

当竞争检测识别出异常，用户就可以修改程序以确保该异常不再存在。在出现先写后 读或先读后写的情况下，会根据serialNo大小顺序确定先后顺序，serialNo小的在 PIPE_S上先执行。 

# 启用竞争检测

运行msSanitizer工具时，执行如下命令，启用竞争检测功能（racecheck）。 mssanitizer --tool=racecheck application // application为用户程序 

# 说明

竞争检测不会执行内存错误检查，建议用户先运行6.3 内存检测，确保算子程序能够正常执 行，没有运行异常。 

● 当用户程序运行完成后，界面将会打印异常报告，异常的具体含义见竞争异常报告解析。 

● 启动工具后，将会在当前目录下自动生成工具运行日志文件 mssanitizer_{TIMESTAMP}_{PID}.log。 

# 竞争异常报告解析

竞争检测会输出一系列信息，详细说明有关算子各PIPE之间存在的内存数据竞争访问 风险。 

```txt
===ERROR: Potential RAW hazard detected at UB in add_custom_kernel: // 竞争事件类型、异常内存块信息、竞争发生的核函数名  
===PIPE_MTE2 Write at RAW()+0x0 in block 0 (aiv) on device 0 at pc current 0xa98 (serialNo:14) //竞争事件的详细信息,包含该事件所在的PIPE、操作类型、内存访问起始地址、核类型、AICore信息以及代码执行的pc指针和调用api行为的序列号  
===#0 {\ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/impl/dav_c220/  
kernel_operator_data_copy_impl.h:58:9 //以下为异常发生代码的调用栈，包含文件名、行号和列号  
===#1 {\ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/inner-interface/  
inner_kernel_operator_data_copy_intc.cppm:58:9  
===#2 {\ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/inner-interface/  
inner_kernel_operator_data_copy_intc.cppm:443:5  
===#3 Racecheck/addcustom.cpp:17:5  
===PIPE_MTE3 Read at RAW()+0x0 in block 0 (aiv) on device 0 at pc current 0xd4 (serialNo:17)  
===#0 {\ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/impl/dav_c220/  
kernel_operator_data_copy_impl.h:103:9  
===#1 {\ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/inner-interface/  
inner_kernel_operator_data_copy_intc.cppm:155:9  
===#2 {\ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/inner-interface/  
inner_kernel_operator_data_copy_intc.cppm:461:5  
===#3 Racecheck/addcustom.cpp:22:5 
```

以上示例中表示了AICore 0的vector核内部中存在对UB的先写后读竞争风险， PIPE_MTE2流水中存在对“0x0”地址的写入操作事件，该操作对应算子实现文件 add_custom.cpp中的第17行，PIPE_MTE3流水中存在对“0x0”地址的读取操作事 件，该操作对应算子实现文件add_custom.cpp中的第22行。