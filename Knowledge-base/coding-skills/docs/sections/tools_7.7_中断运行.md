<!-- Source: 算子开发工具.md lines 7518-7566 | Section: 7.7 中断运行 -->

# 7.7 中断运行

步骤1 Host侧或Device侧的算子运行程序卡顿时，用户可通过键盘输入“CTRL+C”，可手动 中断算子运行程序并回显中断位置信息。 

# 说明

若运行程序出现卡顿的现象，可以通过键盘输入“CTRL+C”中断运行程序。运行卡顿的原因可 能是以下情况： 

用户程序本身存在死循环，需要通过修复程序解决。 

算子使用了同步类指令。 

```txt
(msdebug) r  
Process 173221 launched: '\$\{INSTALL_DIR\}/projects/mix/matmul_leakyrelu.fatbin' (aarch64)  
[Launch of Kernel matmul_leakyrelu_custom on Device 1]  
// 键盘输入“CTRL+C”命令  
Process 173221 stopped  
[Switching to focus on Kernel matmul_leakyrelu_custom, Coreld 35, Type aiv]  
* thread #1, name = 'matmul_leakyrelu', stop reason = signal SIGSTOP  
frame #0: 0x000000000000ef5c  
deviceDebugdata`ZN17MatmulLeakyKernelDhDhffE10CalcOffsetEiiRK11TCubeTilingRiS4_S4_S4_mix_aiv(t  
his=<unavailable>, blockIdx=<unavailable>, usedCoreNum=<unavailable>, tiling=<unavailable>,  
offsetA=<unavailable>, offsetB=<unavailable>, offsetC=<unavailable>, offsetBias=<unavailable>) at  
matmul_leakyrelu_kernel.cpp:127:5  
124 auto mCoreIdx = blockIdx % mSingleBlocks;  
125 auto nCoreIdx = blockIdx / mSingleBlocks;  
126  
->127 while(true) {  
128 }  
129 offsetA = mCoreIdx * tiling.Ka * tiling.singleCoreM;  
130 offsetB = nCoreIdx * tiling.singleCoreN;  
(msdebug) 
```

步骤2 调试完以后，执行q命令并输入Y或y结束调试。 

```txt
(msdebug) q Quitting LLDB will kill one or more processes. Do you really want to proceed: [Y/n] y 
```

# ----结束

# 说明

● 此功能仅支持调试在msDebug工具内启动的算子程序，无法调试在msDebug工具外启动的 应用程序。 

中断生效后，支持7.10 调试信息展示和7.8 核切换功能，暂不支持7.6 单步调试，7.9 读取 寄存器、7.5 内存与变量打印和continue命令。