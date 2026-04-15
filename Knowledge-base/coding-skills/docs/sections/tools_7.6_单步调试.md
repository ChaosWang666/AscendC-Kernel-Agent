<!-- Source: 算子开发工具.md lines 7356-7517 | Section: 7.6 单步调试 -->

# 7.6 单步调试

用户需要了解代码执行具体情况时，可使用thread step-over命令使用示例逐行执行 以进行单步调试，或执行step in命令可进入函数内部进行调试，或可执行finish命令返 回函数调用点的下一行继续调试。 

# 前提条件

算子编译时，使用--cce-ignore-always-inline=true的编译选项。 

# thread step-over 命令使用示例

步骤1 将断点设置在需要调试的位置，并运行。断点设置的具体操作请参见7.4 断点设置。 

```ini
(msdebug) r //运行
Process 177943 launched: '\$\{INSTALL_DIR\}/projects/mix/matmul_leakyrelu.fatbin' (aarch64)
[Launch of Kernel matmul_leakyrelu_custom on Device 1]
Process 177943 stopped
[Switching to focus on Kernel matmul_leakyrelu_custom, Coreld 44, Type aiv]
* thread #1, name = 'matmul_leakyrelu', stop reason = breakpoint 1.2 
```

```txt
frame #0: 0x000000000000f01c  
device_DEBUGdata_ZN17MatmulLeakyKernelDhDhffE10CalcOffsetEiiRK11TCubeTilingRiS4_S4_S4_mix_Aiv(t  
his=0x0000000000217b60, blockIdx=0, usedCoreNum=2, tiling=0x000000000217e28,  
offsetA=0x0000000002175c8, offsetB=0x0000000002175c4, offsetC=0x0000000002175c0,  
offsetBias=0x0000000002175bc) at matmul_leakyrelu_kernel.cpp:129:15  
126  
127 offsetA = mCoreIdx * tiling.Ka * tiling.singleCoreM;  
128 offsetB = nCoreIdx * tiling(singleCoreN;  
-> 129 offsetC = mCoreIdx * tiling.N * tiling.singleCoreM + nCoreIdx * tiling.singleCoreN; //断点位  
置  
130 offsetBias = nCoreIdx * tiling.singleCoreN;  
131}  
132  
(msdebug) 
```


步骤2 输入next或n命令后，开始单步执行。


```txt
(msdebug) n  
Process 177943 stopped  
[Switching to focus on Kernel matmul_leakyrelucustom, Coreld 44, Type aiv]  
* thread #1, name = 'matmul_leakyrelu', stop reason = step over // 通过回显可查看pc的位置，表示单步成功  
frame #0: 0x000000000000f048  
deviceDebugdata`_ZN17MatmulLeakyKernelDhDhffE10CalcOffsetEiiRK11TCubeTilingRiS4_S4_S4_mix_aiv(this=0x0000000000217b60, blockIdx=0, usedCoreNum=2, tiling=0x000000000217e28, offsetA=0x0000000002175c8, offsetB=0x0000000002175c4, offsetC=0x0000000002175c0, offsetBias=0x0000000002175bc) at matmul_leakyrelu_kernel.cpp:130:18  
127 offsetA = mCoreIdx * tiling.Ka * tiling.singleCoreM;  
128 offsetB = nCoreIdx * tiling.singleCoreN;  
129 offsetC = mCoreIdx * tiling.N * tiling.singleCoreM + nCoreIdx * tiling.singleCoreN;  
-> 130 offsetBias = nCoreIdx * tiling.singleCoreN;  
131 } 
```


步骤3 输入ascend info cores命令，查看所有核的PC信息和停止原因。


```txt
(msdebug) ascend info cores Coreld Type Device Stream Task Block PC stop reason 12 aic 1 3 0 0 0x12c0c00f03b0 breakpoint 1.2 * 44 aiv 1 3 0 0 0x12c0c00f8048 step over //*代表当前正在运行的核 45 aiv 1 3 0 0 0x12c0c00f801c breakpoint 1.2 
```

# 说明

● 当前核的停止原因既有单步调试又有断点时，将展示为breakpoint。 

● 若运行程序出现卡顿的现象，可以通过键盘输入“CTRL+C”中断运行程序。运行卡顿的原 因可能是以下情况： 

用户程序本身存在死循环，需要通过修复程序解决。 

算子使用了同步类指令。 


步骤4 调试完以后，执行q命令并输入Y或y结束调试。


```txt
(msdebug) q Quitting LLDB will kill one or more processes. Do you really want to proceed: [Y/n] y 
```

# ----结束

# thread step-in 和 thread step-out 命令使用示例


步骤1 将断点设置在需要调试的位置，并运行。断点设置的具体操作请参见7.4 断点设置。


```txt
(msdebug) r //运行
Process 180938 launched: '{INSTALL_DIR}/test/mstt/sample/normal_sample/mix/matmul_leakyrelu.fatbin'
(aarch64)
[Launch of Kernel matmul_leakyrelu_custom on Device 1]
Process 180938 stopped
[Switching to focus on Kernel matmul_leakyrelu_custom, Coreld 46, Type avr]
* thread #1, name = 'matmul_leakyrelu', stop reason = breakpoint 1.1
frame #0: 0x000000000000e948 
```

```txt
device-debugdata_ZN17MatmulLeakyKernelDhDhffE7ProcessEPN7AscendC5TPipeE_mix_aiv(this=0x000000 000021fb60, pipe=0x000000000021f6a8) at matmul_leakyrelu_kernel.cpp:83:9   
80 while (matmulObj.template Iterate(true>)) {   
81 MatmulCompute();   
82 LeakyReluCompute();   
-> 83 CopyOut(computeRound);   
84 computeRound++;   
85 }   
86 matmulObj.End(); 
```

步骤2 用户输入step或s后，开始进入函数内部进行执行。 

```txt
(msdebug) s  
Process 180938 stopped  
[Switching to focus on Kernel matmul_leakyrelucustom, Coreld 46, Type aiv]  
* thread #1, name = 'matmul_leakyrelu', stop reason = step in  
frame #0: 0x0000000000000febc  
device_DEBUGdata_ZN17MatmulLeakyKernelIDhDhffE7CopyOutEj_mix_aiv(this=0x000000000021fb60, count=0) at matmul_leakyrelu_kernel.cpp:106:5  
103 template <typename aType, typename bType, typename cType, typename biasType>  
104 __acore__ inline void MatmulLeakyKernel<aType, bType, cType, biasType>::CopyOut uint32_t count)  
105 {  
-> 106 reluOutQueue_.DeQue<cType>();  
107 const uint32_t roundM = tiling.singleCoreM / tiling.baseM;  
108 const uint32_t roundN = tiling.singleCoreN / tiling.baseN;  
109 uint32_t startOffset = (count % roundM * tiling.baseM * tiling.N + count / roundM * tiling.baseN); 
```

步骤3 输入ascend info cores命令，查看所有核的PC信息和停止原因。 

```txt
(msdebug) ascend info cores  
Coreld Type Device Stream Task Block PC stop reason  
13 aic 1 3 0 0 0x12c0c00f1f88 breakpoint 1.1  
* 46 aiv 1 3 0 0 0x12c0c00f8ebc step in /*代表当前正在运行的核  
47 aiv 1 3 0 0 0x12c0c00f8d3c breakpoint 1.1 
```

# 说明

当前核的停止原因既有调试函数又有断点时，将展示为breakpoint。 

步骤4 调试完CopyOut函数后，运行finish命令退出CopyOut函数，并返回主程序继续执行。 

(msdebug) finish   
Process 180938 stopped   
[Switching to focus on Kernel matmul_leakyrelucustom, Coreld 46, Type aiv]   
\* thread #1, name $=$ 'matmul_leakyrelu', stop reason $=$ step out frame #0: 0x0000000000000e950   
deviceDebugdata`_ZN17MatmulLeakyKernelIDhDhffE7ProcessEPN7AscendC5TPipeE_mix_aiv(this=0x000000   
000021fb60, pipe $= 0$ x000000000021f6a8) at matmul_leakyrelu_kernel.cpp:84:21   
81 MatmulCompute();   
82 LeakyReluCompute();   
83 CopyOut(computeRound);   
->84 computeRound++;   
85 }   
86 matmulObj.End();   
87} 

----结束