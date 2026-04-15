<!-- Source: 算子开发工具.md lines 7132-7240 | Section: 7.4 断点设置 -->

# 7.4 断点设置

# 设置行断点

使用msDebug工具调试算子时，可在算子的运行程序上设置行断点，即在算子代码文 件的特定行号上设置断点。 

步骤1 输入以下命令，在核函数实现文件matmul_leakyrelu的第114行增加断点，出现回显 显示成功添加1个断点，如下所示。 

```txt
(msdebug) b matmul_leakyrelu_kernel.cpp:114  
Breakpoint 1: where = device_DEBUGdata_ZN17MatmulLeakyKernelIDhDhffE7CopyOutEj_mix_aiv + 240 at  
matmul_leakyrelu_kernel.cpp:114, address = 0x000000000000ff88 
```

关键信息说明如下表： 


表 7-4 信息说明


<table><tr><td>字段</td><td>释义</td></tr><tr><td>device_DEBUGdata</td><td>设备侧.o文件名。</td></tr><tr><td>matmul_leakyrelu_kernel.cpp</td><td>断点所在的Kernel函数名。</td></tr><tr><td>CopyOut</td><td>当前函数。</td></tr><tr><td>240</td><td>本次断点地址相对CopyOut函数的地址偏移量，即当前断点地址（0xff88）相对CopyOut函数所在地址的偏移量是240。</td></tr><tr><td>address = 0x0000000000000ff88</td><td>断点的地址，即逻辑相对地址。</td></tr></table>

# 说明

● 如果Host侧和Kernel侧存在同名的算子实现文件，在设置断点时，推荐采用绝对路径进行设 置，确保断点打在预期的文件上。 

在对源码文件进行打点时，可能会出现找不到实际位置的告警，类似如下提示： (msdebug) b /home/xx/op_host/matmul_leakyrelu_kernel.cpp:24 

Breakpoint 1: no locations (pending on future shared library load). 

WARNING: Unable to resolve breakpoint to any actual locations. (msdebug) 

在算子运行后，会自动找到实际位置，并自动设置断点。 

步骤2 输入如下命令，运行算子程序，等待直到命中断点。 

```txt
(msdebug) run  
Process 165366 launched: '\$\{INSTALL_DIR\}/projects/normal_sample/mix/matmul_leakyrelu.fatbin' (aarch64)  
[Launch of Kernel matmul_leakyrelu_custom on Device 1]  
Process 165366 stopped  
[Switching to focus on Kernel matmul_leakyrelu_custom, Coreld 14, Type av]  
* thread #1, name = 'matmul_leakyrelu', stop reason = breakpoint 1.1  
frame #0: 0x0000000000000ff88  
deviceDebugdata_ZN17MatmulLeakyKernelIDhDhffE7CopyOutEj_mix_avi(this=0x000000000019fb60, count=0) at matmul_leakyrelu_kernel.cpp:114:14  
111 (uint16_t)(tiling.baseN * sizeof(cType) / DEFAULT_C0_SIZE), 
```

```txt
112 0,  
113 (uint16_t)((tiling.N - tiling.baseN) * sizeof(cType) / DEFAULT_C0_SIZE);  
-> 114 DataCopy(cGlobal[ startOffset ], reluLocal, copyParam);  
115 reluOutQueue_.FreeTensor(reluOutLocal);  
116}  
117  
(msdebug) 
```

“0x000000000000ff88”代表该断点所在的pc地址。 

# ----结束

# 说明

若算子代码被编译进动态库中，通过算子调用符加载，当在运行run命令前设置断点时，回显会 告知暂时未找到断点位置（pending on future shared library load），动态库在程序运行后才 会被加载，算子调试信息在运行run命令后完成解析，此时断点会重新更新并完成设置 

```txt
(msdebug) b matmul_leakyrelu_kernel.cpp:55   
Breakpoint 1: no locations (pending on future shared library load).   
WARNING: Unable to resolve breakpoint to any actual locations.   
(msdebug) run   
1 location added to breakpoint 1 
```

# 显示断点

输入以下命令，将会显示所有已设置的断点位置以及序号。 

```cpp
(msdebug) breakpoint list  
Current breakpoints:  
1: file = 'add_custom.cpp', line = 85, exact_MATCH = 0, locations = 1, resolved = 1, hit count = 1  
1.1: where = deviceDebugdata::add_custom(uid8_t *__restrict, uint8_t *__restrict, uint8_t *__restrict) + 14348 [inlined] KernelAdd::CopyOut(int) + 1700 at add_custom.cpp:85:9, address = 0x000000000000380c, resolved, hit count = 1 
```

# 删除断点

步骤1 输入以下命令，删除对应序号的断点。 

```txt
(msdebug) breakpoint delete 1  
1 breakpoints deleted; 0 breakpoint locations disabled. 
```

步骤2 输入以下命令，恢复程序运行，因断点已被删除，则程序会一直运行直至结束。 

```txt
(msdebug) c  
Process 165366 resuming  
4096.00 4096.00 4096.00 4096.00 4096.00 4096.00 4096.00  
4096.00 4096.00 4096.00 4096.00 4096.00 4096.00 4096.00  
4096.00 4096.00 4096.00 4096.00 4096.00 4087.00  
4096.00 4096.00 4096.00 4096.00 4096.00 4096.00  
Process 165366 exited with status = 0 (0x123456789)  
(msdebug) 
```

# ----结束