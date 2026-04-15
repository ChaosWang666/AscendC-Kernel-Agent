<!-- Source: 算子开发工具.md lines 7080-7131 | Section: 7.3 指定 Device ID（通算融合算子场景） -->

# 7.3 指定 Device ID（通算融合算子场景）

用户在调试单进程多线程类型的通算融合算子时，根据自身需求执行ascend device ID命令（ID为Device ID的数字）指定Device ID，实现在特定的Device上进行调试。这 种调试方式具有以下优点： 

提高调试效率：通过选择特定的Device，可以更高效地利用硬件资源，加快调试 过程。 

针对性强：能够针对特定设备进行调试，有助于发现和解决与该设备相关的性能 瓶颈或兼容性问题。 

便于隔离问题：当遇到性能或功能问题时，可以通过指定不同的设备ID来确定问 题是否由特定设备引起，从而更容易定位问题所在。 

# 说明

● 如果不指定，则仅对用户程序运行时首次设置的Device ID进行调试。 

● Hccl接口不支持单步调试功能，具体接口明细请参见《Ascend C算子开发接口》中的“高阶 $\mathsf { A P l } > \mathsf { H c c l } > \mathsf { H c c l } ^ { \prime \prime }$ 章节。 

```txt
py38) [root@localhost MC2-master]# msdebug /home/xxx/MC2-master/bin/alltoallcustom_aarch64  
msdebug(MindStudio Debugger) is part of MindStudio Operator-dev Tools.  
The tool provides developers with a mechanism for debugging Ascend kernels running on actual hardware.  
This enables developers to debug Ascend kernels without being affected by potential changes brought by simulation and emulation environments.  
(msdebug) target create "/home/xxx/MC2-master/bin/alltoallcustom_aarch64"  
Current executable set to '/home/xxx/MC2-master/bin/alltoallcustom_aarch64' (aarch64).  
(msdebug) b all_to_allCustom_v3.cpp:58  
Breakpoint 1: 2 locations.  
(msdebug) ascend device 1  
(msdebug) run --x1_shape 72,17 --input_tensor_format ND --input_tensor_dtype fp16 --output_shape 72,17 --output_dtype fp16 --output_format ND --n_dev 2 --bin_path feature/acclnn/  
AllToAllCustom.fp16_ND_fuzz_000010 --loop_cnt 1 --platform 1971 --version 3 --tileM 128 | tee /home/shelltest/MC2-master/features/acclnn/AllToAllCustom.fp16_ND_fuzz_000010/mc2_memory.log  
Process 2625643 launched: '/home/xxx/MC2-master/bin/alltoallcustom_aarch64' (aarch64)  
[INFO] rank 0 hcom: 90.90.69.212%enp189s0f0_60000_0_1747739573633567 stream: 0xxxxac9e14610, context: 0xxxxac9daeda0  
[INFO] rank 1 hcom: 90.90.69.212%enp189s0f0_60000_0_1747739573633567 stream: 0xxxxaca8c8380, context: 0xxxxaca88f280  
before RunGraph : free :29837 M, total:30196 M, used :358 M, ret :0  
before RunGraph : free :29835 M, total:30196 M, used :360 M, ret :0  
Process 2625643 stopped and restarted: thread 19 received signal: SIGCHLD  
[INFO] M is 72, K is 17, tileM is 128, tileNum is 0, tailM is 36, tailNum is 1, useBufferType is 0  
[INFO] M is 72, K is 17, tileM is 128, tileNum is 0, tailM is 36, tailNum is 1, useBufferType is 0  
[Launch of Kernel AllToAllCustomV3_f1974b24a4ace3957d571b2712b3eadf_1000 on Device 1]  
[Launch of Kernel AllToAllCustomV3_f1974b24a4ace3957d571b2712b3eadf_1000 on Device 1]  
Process 2625643 stopped  
[Switching to focus on Kernel AllToAllCustomV3_f1974b24a4ace3957d571b2712b3eadf_1000, Coreld 0, Type avi]  
* thread #1, name = 'alltoall_custom', stop reason = breakpoint 1.2  
frame #0: 0x0000000000004e0c  
AllToAllCustomV3_f1974b24a4ace3957d571b2712b3eadf.o`all_to_all_custom_v3_1000_tilingkey.:vector(aGM= "\x8b2d3+\\xb5Θ\\xbe\\xb7\\xa94\\x87\\xa,b;\\xb6\\xf68\\U0000000e9\xc1\\xa9", cGM="", workspaceGM="", tilingGM="d") at all_to_all_custom_v3.cpp:58:28  
55 auto &&cfg = tilingData param;  
56 const uint8_t tileNum = cfgtileNum;  
57 const uint8_t tailNum =cfg.tailNum;  
-> 58 const uint64_t tileM =cfgtileM;  
59 const uint64_t tailM =cfg.tailM;  
60 const uint64_t M =cfg.M;  
61 const uint64_t K =cfg.K; 
```