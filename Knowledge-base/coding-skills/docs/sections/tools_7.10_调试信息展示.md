<!-- Source: 算子开发工具.md lines 7650-7759 | Section: 7.10 调试信息展示 -->

# 7.10 调试信息展示

# ascend info devices

输入以下命令查询算子运行的设备信息，*所在行代表当前聚焦的设备。 

```txt
(msdebug) ascend info devices Device Aic_Num Aiv_Num Aic_Mask Aiv_Mask * 1 1 2 0x10000 0x3 
```

# 说明

通算融合算子场景将会显示多个Device ID。 

关键信息说明如下表： 


表 7-5 信息说明


<table><tr><td>字段</td><td>释义</td></tr><tr><td>Device</td><td>设备逻辑ID。</td></tr><tr><td>Aic_Num</td><td>使用的cube核数量。</td></tr><tr><td>Aiv_Num</td><td>使用的vector核数量。</td></tr><tr><td>Aic_Mask</td><td>实际使用的cube的mask码，用64 bit位表示，如果第n位bit为1，表示使用了cube n。</td></tr><tr><td>Aiv_Mask</td><td>实际使用的vector的mask码，用64 bit位表示，如果第n位bit为1，表示使用了vector n。</td></tr></table>

# ascend info cores

输入以下命令查询算子运行的核信息，*所在行代表当前聚焦的核。如下所示当前聚焦 的核为aiv的“core 0”。 

<table><tr><td colspan="9">(msdebug) ascend info cores</td></tr><tr><td>Coreld</td><td>Type</td><td>Device</td><td>Stream</td><td>Task</td><td>Block</td><td>PC</td><td>stop reason</td><td></td></tr><tr><td>16</td><td>aic</td><td>1</td><td>3</td><td>0</td><td>0</td><td>0x12c0c00f1fc0</td><td>breakpoint 1.1</td><td></td></tr><tr><td>*</td><td>0</td><td>aiv</td><td>1</td><td>3</td><td>0</td><td>0</td><td>0x12c0c00f8fcc</td><td>breakpoint 1.1</td></tr><tr><td></td><td>1</td><td>aiv</td><td>1</td><td>3</td><td>0</td><td>0</td><td>0x12c0c00f8d3c</td><td>breakpoint 1.1</td></tr></table>

关键信息说明如下表： 


表 7-6 信息说明


<table><tr><td>字段</td><td>释义</td></tr><tr><td>Coreld</td><td>aiv或aic的核id，从0开始。</td></tr><tr><td>Type</td><td>核类型，包括aic或aiv。</td></tr><tr><td>Device</td><td>设备逻辑ID。</td></tr><tr><td>Stream</td><td>当前Kernel函数下发的Stream ID，Stream由一系列的Task组成。</td></tr><tr><td>Task</td><td>当前Stream里的Task ID。Task表示下发给Task schedulering处理的任务。</td></tr><tr><td>Block</td><td>表示核函数将会在几个核上执行。每个执行该核函数的核会被分配一个逻辑ID（Block_ID）。</td></tr><tr><td>PC</td><td>当前核上的pc逻辑绝对地址。</td></tr><tr><td>Stop Reason</td><td>表示程序执行停止原因，有breakpoint、step in、step over和ctrl+c等。</td></tr></table>

# ascend info tasks

输入以下命令查询算子运行的Task信息，*所在行代表当前聚焦的Task，包括Device ID、Stream ID、Task ID、Invocation（被调用的核函数名称）。 

```txt
(msdebug) ascend info tasks
Device Stream Task Invocation
* 1 3 0 matmul_leakyrelu/custom 
```

# ascend info stream

输入以下命令查询算子运行的Stream信息，*所在行代表当前聚焦的Stream，包括 Device ID、Stream ID、Type（核类型，包括aic或aiv）。 

```txt
(msdebug) ascend info stream Device Stream Type * 1 3 aiv 
```

# ascend info blocks

输入以下命令查询算子运行的Block信息，*所在行代表当前聚焦的Block，包括Device ID、Stream ID、Task ID、Block ID。 

```txt
(msdebug) ascend info blocks Device Stream Task Block 
```

```txt
1 3 0 0  
* 1 3 0 0  
1 3 0 0 
```

输入以下命令显示所运行的Block在当前中断处的代码。 

```txt
(msdebug) ascend info blocks -d
Current stop state of all blocks:
[Coreld 16, Block 0]
* thread #1, name = 'matmul_leakyrelu', stop reason = breakpoint 1.1
frame #0: 0x0000000000008fc0 device_DEBUGdata_ZN7AscendC14KfcMsgGetStateEj_mix_aicflag=0) at
kfc_comm.h:188
185 return static_cast<KFC_Enum>((flag & 0xfffff0000) >> KFC_MSG_BYTE_OFFSET);
186 }
187 __aicore__ inline uint32_t KfcMsgGetState uint32_t flag)
-> 188 {
189 return (flag & 0x00008000);
190 }
191 __aicore__ inline uint32_t KfcMsgMakeFlag(KFC_Enum funID, uint16_t instID)
[* Coreld 0, Block 0]
* thread #1, name = 'matmul_leakyrelu', stop reason = breakpoint 1.1
frame #0: 0x000000000000ffcc
device_DEBUGdata_ZN17MatmulLeakyKernelIDhDhffE7CopyOutEj_mix_aiv(this=0x0000000000167b60,
count=0) at matmul_leakyrelu_kernel.cpp:116:1
113 (uint16_t) ((tiling.N - tiling.baseN) * sizeof(cType) / DEFAULT_C0_SIZE));
114 DataCopy(cGlobal[startOffset], reluLocal,ropyaram);
115 reluQueue_.FreeTensor(reluOutLocal);
-> 116 }
117
118 template <typename aType, typename bType, typename cType, typename biasType>
119 __aicore__ inline void MatmulLeakyKernel<aType, bType, cType, biasType>::CalcOffset(int32_t
blockIdx,
[Coreld 1, Block 0]
* thread #1, name = 'matmul_leakyrelu', stop reason = breakpoint 1.1
frame #0: 0x0000000000000fd3c device_DEBUGdata_ZN7AscendC13WaitEventImplEt_mix_aiv flagld=1) at
kernel_operatorSync Impl.h:142:5
139
140 __aicore__ inline void WaitEventImpl uint16_t flagld)
141 {
-> 142 wait_flag_dev flagld);
143 }
144
145 __aicore__ inline void SetSyncBaseAddrImpl uint64_t config) 
```