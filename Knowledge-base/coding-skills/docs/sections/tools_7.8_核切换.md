<!-- Source: 算子开发工具.md lines 7567-7624 | Section: 7.8 核切换 -->

# 7.8 核切换

参考以下操作可将当前聚焦的核切换至指定的核，切核后会自动展示指定核代码中断 处的位置。 

● 如果当前运行的核为aiv的“core 2”，指定切换的核为aiv的“core 3”。 

```csv
(msdebug) ascend aiv 3  
[Switching to focus on Kernel matmul_leakyrelu_custom, Coreld 3, Type * thread #1, name = 'matmul_leakyrelu', stop reason = breakpoint 1.1 frame #0: 0x00000000000000fd3c  
deviceDebugdata_ZN7AscendC13WaitEventImplEt_mix_aivflagld=1) at kernel_operatorSyncImpl.h:142:5  
139  
140 __aicore__ inline void WaitEventImpl( uint16_t flagld)  
141 {  
-> 142 wait_flag_devflagld);  
143 }  
144  
145 __aicore__ inline void SetSyncBaseAddrImpl( uint64_t config) 
```

完成切换后，再次查询核信息可看到已切换至新指定的核id所在行。 

```txt
(msdebug) ascend info cores Coreld Type Device Stream Task Block PC stop reason 
```

```txt
17 aic 1 3 0 0 0x12c0c00f1f88 breakpoint 1.1  
2 aiv 1 3 0 0 0x12c0c00f8fbc breakpoint 1.1  
* 3 aiv 1 3 0 0 0x12c0c00f8d3c breakpoint 1.1 
```

如果当前运行的核为aiv的“core 3”，指定切换的核为aic的“core 17”。 

```txt
(msdebug) ascend aic 17  
[Switching to focus on Kernel matmul_leakyrelucustom, Coreld 17, Type aic]  
* thread #1, name = 'matmul_leakyrelu', stop reason = breakpoint 1.1  
frame #0: 0x0000000000008f88 deviceDebugdata'_ZN7AscendC7BarrierEv_mix_aic at  
kfc_comm.h:39  
36  
37 namespace AscendC {  
38 __aicore__ inline void Barrier()  
-> 39 {  
40 #if defined(_CCE_KT_TEST_) && _CCE_KT_TEST_ == 1  
41 __asm__ __volatile_(""::""memory");  
42 #else 
```

完成切换后，再次查询核信息可看到已切换至新指定的核id所在行。 

```txt
(msdebug) ascend info cores  
Coreld Type Device Stream Task Block PC stop reason  
* 17 aic 1 3 0 0 0x12c0c00f1f88 breakpoint 1.1  
2 aiv 1 3 0 0 0x12c0c00f8fbc breakpoint 1.1  
3 aiv 1 3 0 0 0x12c0c00f8d3c breakpoint 1.1 
```