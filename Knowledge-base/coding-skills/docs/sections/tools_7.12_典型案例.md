<!-- Source: 算子开发工具.md lines 7819-8428 | Section: 7.12 典型案例 -->

# 7.12 典型案例

# 7.12.1 上板调试 vector 算子

展示如何使用msDebug工具来上板调试一个vector算子，该vector算子可实现两个向 量相加并输出结果的功能。 

# 前提条件

单击Link获取样例工程，为进行算子调试做准备。 

参考7.2 使用前准备完成相关环境变量配置。 

# 操作步骤

步骤1 基于样例工程编译算子，获取可执行文件add.fatbin。 

1. 修改sample/normal_sample/vec_only/Makefile中的COMPILER_FLAG编译选 项，将 -O2修改为 -O0 -g --cce-ignore-always-inline=true，使能编译器调试功 能。 

```makefile
# Makefile
...
COMPILER := $(ASCEND_HOME_PATH)/compiler/ccec Compilerer/bin/ccec
COMPILER_FLAG := -xcce -O0 -g --cce-ignore-always-inline=true -std=c++17 # 使能编译器调试功能 
```

2. 执行以下命令完成算子编译。 

# 说明

非首次场景，可以使用make clean && make命令替代make命令。 

```txt
cd ./mntt/sample/normal_sample/vec_only/  
make clean && make 
```

# 步骤2 设置断点。

1. 启动msDebug工具拉起算子程序，进入调试界面。 

```txt
msdebug add.fatbin (msdebug) target create "add.fatbin" Current executable set to '/home/mindstudio/projects/mstt/sample/build/add.fatbin' (aarch64). (msdebug) 
```

2. 该sample中核函数的代码实现位于add_kernel.cpp中，在此文件中，为需要的代 码行设置NPU断点。 

```txt
(msdebug) b add_kernel.cpp:69  
Breakpoint 1: where = deviceDebugdata::addcustom uint8_t *, uint8_t *, uint8_t *) + 18804 [inlined]  
KernelAdd::Compute(int) + 5144 at add_kernel.cpp:69:9, address = 0x0000000000004974  
(msdebug) 
```

# 步骤3 运行算子程序。

程序会开始运行直到命中第一个断点（add_kernel.cpp:69）后停下，msDebug检测到 NPU核函数add_custom开始运行，运行在Device 0。 

(msdebug) run   
Process 730254 launched   
[Launch of Kernel add_custom on Device 0]   
Process 730254 stopped   
[Switching to focus on Kernel add_custom, Coreld 13, Type aiv]   
\* thread #1, name $=$ 'add.fatbin', stop reason $=$ breakpoint 2.1 frame #0: 0x0000000000004974 deviceDebugdata::addcustom( uint8_t \*, uint8_t \*, uint8_t \*) [inlined] KernelAdd::Compute(this=0x00000000019a930, progress=0) at add_kernel.cpp:69:9   
66 // call Add instr for computation   
67 Add(zLocal, xLocal, yLocal, TILE_LENGTH);   
68 // enque the output tensor to VECOUT queue   
-> 69 outQueueZ.EnQue<int16_t>(zLocal); # 断点位置   
70 // free input tensors for reuse   
71 inQueueX.FreeTensor(xLocal);   
72 inQueueY.FreeTensor(yLocal);   
(msdebug) 

# 步骤4 检视信息。

使用ascend info cores命令查询NPU核信息。 

```c
(msdebug) ascend info cores  
Coreld Type Device Stream Task Block PC Exception  
* 13 aiv 0 3 0 0 0x1240c0034974 f0000000  
14 aiv 0 3 0 1 0x1240c0034974 f0000000  
15 aiv 0 3 0 2 0x1240c0034974 f0000000  
20 aiv 0 3 0 3 0x1240c0034974 f0000000  
21 aiv 0 3 0 4 0x1240c0034974 f0000000 
```

<table><tr><td>22</td><td>aiv</td><td>0</td><td>3</td><td>0</td><td>5</td><td>0x1240c0034974</td><td>f0000000</td></tr><tr><td>23</td><td>aiv</td><td>0</td><td>3</td><td>0</td><td>6</td><td>0x1240c0034974</td><td>f0000000</td></tr><tr><td>24</td><td>aiv</td><td>0</td><td>3</td><td>0</td><td>7</td><td>0x1240c0034974</td><td>f0000000</td></tr><tr><td colspan="8">(msdebug)</td></tr></table>

使用print命令直接打印变量信息。 

(msdebug) print progress 

(int32_t) $\$ 0=0$ 

● 使用print命令与memory read命令配合可打印出Tensor变量中存放的值。 

打印位于UB内存上的LocalTensor中存放的数据。 

# 说明

UB内存打印起始地址需参考LocalTensor变量展示的address_字段中的bufferAddr参 数。此处以变量xLocal为例，其内存起始地址为0。 

```txt
(msdebug) print xLocal
(AscendC::LocalTensor<short>) $0 = {
address_ = (dataLen = 256, bufferAddr = 0, bufferHandle = "", logicPos = '\t')
shapelInfo_ = {
shapeDim = '\0'
originalShapeDim = '\0'
shape = ([0] = 0, [1] = 0, [2] = 0, [3] = 0, [4] = 0, [5] = 0, [6] = 0, [7] = 0)
originalShape = ([0] = 0, [1] = 0, [2] = 0, [3] = 0, [4] = 0, [5] = 0, [6] = 0, [7] = 0)
dataFormat = ND
}
(msdebug) memory read -m UB -f int16_t[] 0 -s 256 -c 1
0x00000000: {0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27 28 29
30 31 32 33 34 35 36 37 38 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57 58 59
60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87 88 89
90 91 92 93 94 95 96 97 98 99 100 101 102 103 104 105 106 107 108 109 110 111 112 113 114
115 116 117 118 119 120 121 122 123 124 125 126 127}
(msdebug) 
```

打印位于GM内存上的GlobalTensor中存放的数据。 

# 说明

GM内存打印的起始地址需参考GlobalTensor变量展示的address_字段。此处以变量 xGm为例，其内存起始地址为0x00001240c0015000。 

```txt
(msdebug) print xGm
(AscendC::GlobalTensor<short>) $0 = {
bufferSize_ = 2048
shapelInfo_ = {
shapeDim = '\0'
originalShapeDim = '\0'
shape = ([0] = 0, [1] = 0, [2] = 0, [3] = 0, [4] = 0, [5] = 0, [6] = 0, [7] = 0)
originalShape = ([0] = 0, [1] = 0, [2] = 0, [3] = 0, [4] = 0, [5] = 0, [6] = 0, [7] = 0)
dataFormat = ND
}
address_ = 0x00001240c0015000
}
(msdebug) memory read -m GM -f int16_t[] 0x00001240c0015000 -s 256 -c 1
0x1240c0015000: {0 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26 27
28 29 30 31 32 33 34 35 36 37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55 56 57
58 59 60 61 62 63 64 65 66 67 68 69 70 71 72 73 74 75 76 77 78 79 80 81 82 83 84 85 86 87
88 89 90 91 92 93 94 95 96 97 98 99 100 101 102 103 104 105 106 107 108 109 110 111 112
113 114 115 116 117 118 119 120 121 122 123 124 125 126 127} 
```

进行核切换，切换至另一个aiv核，并打印需要的信息。 

```txt
(msdebug) ascend aiv 24 // ascend info cores中选择block7对应的coreld,此处为24  
[Switching to focus on Kernel add_custom, Coreld 24, Type aiv]  
* thread #1, name = 'add fatbin', stop reason = breakpoint 2.1  
frame #0: 0x0000000000004974 device_DEBUGdata::addcustom( uint8_t *, uint8_t *, uint8_t *)  
[INLINE] KernelAdd::Compute(this=0x00000000001c6930, progress=0) at add_kernel.cpp:69:9  
66 // call Add instr for computation  
67 Add(zLocal, xLocal, yLocal, TILE_LENGTH); 
```

```txt
68 // enqueue the output tensor to VECOUT queue  
-> 69 outQueueZ.EnQue<int16_t>(zLocal);  
70 // free input tensors for reuse  
71 inQueueX.FreeTensor(xLocal);  
72 inQueueY.FreeTensor(yLocal);  
( Msdebug) p xLocal  
(AscendC::LocalTensor<short>) $0 = {  
address_ = (dataLen = 256, bufferAddr = 0, bufferHandle = "", logicPos = '\t')  
shapeInfo_ = {  
shapeDim = '\0'  
originalShapeDim = '\0'  
shape = ([0] = 0, [1] = 0, [2] = 0, [3] = 0, [4] = 0, [5] = 0, [6] = 0, [7] = 0)  
originalShape = ([0] = 0, [1] = 0, [2] = 0, [3] = 0, [4] = 0, [5] = 0, [6] = 0, [7] = 0)  
dataFormat = ND  
}  
}  
(msdebug) memory read -m UB -f int16_t[] 0 -s 256 -c 1  
0x00000000: {14336 14337 14338 14339 14340 14341 14342 14343 14344 14345 14346 14347 14348  
14349 14350 14351 14352 14353 14354 14355 14356 14357 14358 14359 14360 14361 14362 14363  
14364 14365 14366 14367 14368 14369 14370 14371 14372 14373 14374 14375 14376 14377 14378  
14379 14380 14381 14382 14383 14384 14385 14386 14387 14388 14389 14390 14391 14392 14393  
14394 14395 14396 14397 14398 14399 14400 14401 14402 14403 14404 14405 14406 14407 14408  
14409 14410 14411 14412 14413 14414 14415 14416 14417 14418 14419 14420 14421 14422 14423  
14424 14425 14426 14427 14428 14429 14430 14431 14432 14433 14435 14436 14437 14438  
14439 14440 14441 14442 14443 14445 14446 14447 14448 14450 14505 14552 14553  
14452 155555555555555555555555555555555555555555555555555555555555555555555555 
```

步骤5 查询并删除断点，恢复程序运行。 

```txt
(msdebug) breakpoint list  
Current breakpoints:  
1: name = 'main', locations = 1, resolved = 1, hit count = 1  
1.1: where = add.fatbin`main + 36 at main.cpp:39:12, address = 0x0000aaaaab0f568, resolved, hit count = 1  
2: file = 'add_kernel.cpp', line = 69, exact_MATCH = 0, locations = 1, resolved = 1, hit count = 1  
2.1: where = device_DEBUGdata`:add/custom( uint8_t *, uint8_t *, uint8_t *) + 18804 [inlined]  
KernelAdd::Compute(int) + 5144 at add_kernel.cpp:69:9, address = 0x00000000000004974, resolved, hit count = 1  
(msdebug) breakpoint delete 2  
1 breakpoints deleted; 0 breakpoint locations disabled.  
(msdebug) continue  
Process 730254 resuming  
0 2 4 6 8 10 12 14  
16 18 20 22 24 26 28 30  
Process 730254 exited with status = 0 (0x00000000) 
```

步骤6 调试完以后，执行q命令并输入Y或y结束调试。 

```txt
(msdebug) q Quitting LLDB will kill one or more processes. Do you really want to proceed: [Y/n] y 
```

----结束 

# 7.12.2 调用 Ascend CL 单算子

# 前提条件

单击Link获取算子样例工程，为进行算子调试做准备。 

# 说明

● 此样例工程不支持Atlas A3 训练系列产品。 

下载代码样例时，需执行以下命令指定分支版本。 git clone https://gitee.com/ascend/samples.git -b v1.5-8.2.RC1 

# 操作步骤

步骤1 切换到msOpGen脚本install.sh所在目录。 cd ${git_clone_path}/samples/operator/ascendc/0_introduction/1_add_frameworklaunch 

步骤2 执行以下命令，生成自定义算子工程，并进行Host侧和Kernel侧的算子实现。 

bash install.sh -v Ascendxxxyy # xxxyy为用户实际使用的具体芯片类型 

步骤3 在${git_clone_path}/samples/operator/ascendc/0_introduction/ 1_add_frameworklaunch/CustomOp目录下修改CMakePresets.json文件的 cacheVariables的配置项，将"Release"修改为"Debug"。 

```txt
"cacheVariables": { "CMAKE-built_TYPE": {"type": "STRING", "value": "Debug"} },   
} 
```

步骤4 参考4.5 算子编译部署完成算子的编译部署。 

步骤5 切换到msOpGen脚本install.sh所在目录，并参考README编译单算子调用应用并得到 可执行文件execute_add_op。 

cd ${git_clone_path}/samples/operator/ascendc/0_introduction/1_add_frameworklaunch/AclNNInvocation 

步骤6 导入算子动态加载路径。 

将自定义算子工程编译后输出在build_out目录下Kernel侧的.o文件路径导入环境变 量。 

export LAUNCH_KERNEL_PATH=/{path to kernel}/kernel name.o //{path to kernel}表示对算子Kernel侧实现 编译后生成的算子二进制文件*.o所在路径，请根据实际情况进行替换 

# 说明

算子的多个dtype在Kernel侧可能会编译出多个.o文件，请选择步骤3示例中所调用的.o文件进行 导入。 

步骤7 使用msDebug工具加载步骤5中得到的单算子可执行文件execute_add_op。 

export LD.Library_PATH $\equiv$ \ $ASCEND_HOME_PATH/opp/vendors/customize/op api/lib:\$ LD.Library_PATH  
cd AclNNInvocation/output  
msdebug execute_add_op  
(msdebug) target create "execute_add_op"  
Current executable set to '/home/AclNNInvocation/output/execute_add_op' (aarch64).  
(msdebug) 

步骤8 断点设置。 

```python
b add_custom.cpp:55 
```

步骤9 运行算子程序，等待直到命中断点。 

```txt
(msdebug) r  
Process 1385976 launched: '\(HOME/shelltest/test/samples/operator/ascendc/0_introduction/1_add_frameworklaunch/AclNNInvocationNaive/build/execute_add_op' (aarch64)  
[Launch of Kernel anonymous on Device 0]  
Process 1385976 stopped  
[Switching to focus on Kernel anonymous, Coreld 24, Type avi]  
* thread #1, name = 'execute_add_op', stop reason = breakpoint 1.1  
frame #0: 0x00000000000001564  
AddCustom_1e04ee05ab491cc5ae9c3d5c9ee8950b.o`KernelAdd::Compute(this=0x000000000028f8a8, progress=0) (.vector) at add_custom.cpp:55:19  
52 LocalTensor<DTYPE_Y> yLocal = inQueueY.DeQue<DTYPE_Y>();  
53 LocalTensor<DTYPE_Z> zLocal = outQueueZ AllocTensor<DTYPE_Z>();  
54 Add(zLocal, xLocal, yLocal, this->tileLength);  
-> 55 outQueueZ.EnQue<DTYPE_Z>(zLocal); 
```

```txt
56 inQueueX.FreeTensor(xLocal);  
57 inQueueY.FreeTensor(yLocal);  
58}  
(msdebug) 
```

# 说明

后续调试过程可参考导入调试信息、7.5 内存与变量打印及7.8 核切换等，与其操作一致。 

# ----结束

# 7.12.3 调试 PyTorch 接口调用的算子

展示如何使用msDebug工具来上板调试一个PyTorch接口调用的add算子，该add算子 可实现两个向量相加并输出结果的功能。 

# 前提条件

单击Link获取样例工程，为进行算子调试做准备。 

# 说明

● 此样例工程仅支持Python3.9，若要在其他Python版本上运行，需要修改$ {git_clone_path}/samples/operator/ascendc/0_introduction/ 1_add_frameworklaunch/PytorchInvocation目录下run_op_plugin.sh文件中的Python 版本。 

● 此样例工程不支持Atlas A3 训练系列产品。 

下载代码样例时，需执行以下命令指定分支版本。 git clone https://gitee.com/ascend/samples.git -b v1.5-8.2.RC1 

已参考《Ascend Extension for PyTorch 软件安装指南》，完成PyTorch框架和 torch_npu插件的安装。 

参考7.2 使用前准备完成相关环境变量配置。 

# 操作步骤

步骤1 执行以下命令，可生成自定义算子工程，并进行Host侧和Kernel侧的算子实现。 

bash install.sh -v Ascendxxxyy # xxxyy为用户实际使用的具体芯片类型 

步骤2 在${git_clone_path}/samples/operator/ascendc/0_introduction/ 1_add_frameworklaunch/CustomOp目录下修改CMakePresets.json文件的 cacheVariables的配置项，将"Release"修改为"Debug"。 

```txt
"cacheVariables": { "CMAKE-built_TYPE": {"type": "STRING", "value": "Debug"} },   
} 
```

步骤3 参考4.5 算子编译部署，完成算子的编译部署。 

步骤4 进入到样例目录，以命令行方式下载样例代码。参考README使用PyTorch调用方式调 用AddCustom算子工程，并按照指导完成编译。 

# 说明

PyTorch接入工程的样例工程目录如下： 

```txt
PytorchInvocation  
op Plugin_batch  
run_op Plugin.sh // 5.执行样例时，需要使用  
testOpscustom.py //步骤7启动工具时，需要使用  
testOpscustom register_in_graph.py //执行torch.compile模式下用例脚本 
```

cd ${git_clone_path}/samples/operator/ascendc/0_introduction/1_add_frameworklaunch/PytorchInvocation 

步骤5 执行样例，样例执行过程中会自动生成测试数据，然后运行PyTorch样例，最后检验运 行结果。 

```txt
bash run_op Plugin.sh
-- CMAKE_CCE_COMPILER: ${INSTALL_DIR}/toolkit/tools/ccec_compiler/bin/ccec
-- CMAKE_CURRENT_LIST_DIR: ${INSTALL_DIR}/AddKernelInvocation/cmake/Mod
-- ASCEND_PRODUCT_TYPE:
    Ascendxxxyy
-- ASCEND_CORE_TYPE:
    VectorCore
-- ASCEND_install_PATH:
    /usr/local/Ascend/ascend-toolkit/latest
-- The CXX compiler identification is GNU 10.3.1
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/c++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done
-- Configuring done
-- Generating done
-- Build files have been written to: ${INSTALL_DIR}/AddKernelInvocation/build
Scanning dependencies of target add_npu
...
[100%] Built target add_npu
INFO: Ascend C Add Custom SUCCESS
...
INFO: Ascend C Add Custom in torch.compile graph SUCCESS 
```

步骤6 手动导入算子调试信息，示例如下。 

# 说明

● ${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。若安装的Ascend-cann-toolkit软 件包，以root安装举例，则安装后文件存储路径为：/usr/local/Ascend/ascend-toolkit/ latest。 

● 非Atlas A3 训练系列产品/Atlas A3 推理系列产品：在安装昇腾AI处理器的服务器执行npusmi info命令进行查询，获取Chip Name信息。实际配置值为AscendChip Name，例如 Chip Name取值为xxxyy，实际配置值为Ascendxxxyy。当Ascendxxxyy为代码样例的路径 时，需要配置为ascendxxxyy。 

● Atlas A3 训练系列产品/Atlas A3 推理系列产品：在安装昇腾AI处理器的服务器执行npusmi info -t board -i id -c chip id命令进行查询，获取Chip Name和NPU Name信息，实 际配置值为Chip Name_NPU Name。例如Chip Name取值为Ascendxxx，NPU Name取值 为1234，实际配置值为Ascendxxx 1234。当Ascendxxx 1234为代码样例的路径时，需要配 置为ascendxxx 1234。 

其中： 

id：设备id，通过npu-smi info -l命令查出的NPU ID即为设备id。 

chip_id：芯片id，通过npu-smi info -m命令查出的Chip ID即为芯片id。 

export LAUNCH_KERNEL_PATH=${INSTALL_DIR}/opp/vendors/customize/op_impl/ai_core/tbe/kernel/ SOC_VERSION/add_custom/AddCustom_1e04ee05ab491cc5ae9c3d5c9ee8950b.o 

步骤7 启动msDebug工具拉起Python程序，进入调试界面。 

msdebug python3 test_ops_custom.py (msdebug) target create "python3" 

```txt
Current executable set to '/home/mindstudio/miniconda3/envs/py39/bin/python3' (aarch64).  
(msdebug) settings set -- target.run-args "testOPS_custom.py"  
(msdebug) 
```

# 步骤8 设置断点。


根据指定源码文件与对应行号，在核函数中设置NPU断点。


```txt
(msdebug) b add_custom.cpp:60  
Breakpoint 1: where =  
AddCustom_1e04ee05ab491cc5ae9c3d5c9ee8950b.o::AddCustom_1e04ee05ab491cc5ae9c3d5c9ee8950b_1( uint8_t *, uint8_t *, uint8_t *, uint8_t *, uint8_t*) + 9912 [inlined] KernelAdd::Compute(int) + 3400 at  
add_custom.cpp:60:9, address = 0x000000000000026b8 
```

# 步骤9 运行程序，等待直到命中断点。

(msdebug) r   
Process 197189 launched: '/home/miniconda3/envs/py39/bin/python3'(aarch64)   
Process 197189 stopped and restarted: thread 1 received signal: SIGCHLD   
[Launch of Kernel anonymous on Device 0]   
Process 197189 stopped   
[Switching to focus on Kernel anonymous, Coreld 8, Type aiv]   
\* thread #1, name = 'python3', stop reason = breakpoint 2.1 frame #0: 0x00000000000026b8   
AddCustom_1e04ee05ab491cc5ae9c3d5c9ee8950b.o::AddCustom_1e04ee05ab491cc5ae9c3d5c9ee8950b_1( uint8_t *, uint8_t *, uint8_t *, uint8_t *, uint8_t *) [inlined] KernelAdd::Compute(this=0x000000000020efb8, progress $\equiv$ 1) at add_custom.cpp:60:9   
57 LocalTensory yLocal $=$ inQueueY.DeQue<DTYPE_Y>();   
58 LocalTensorz zLocal $=$ outQueueZ AllocTensor<DTYPE_Z>();   
59 Add(zLocal, xLocal, yLocal, this->tileLength);   
-> 60 outQueueZ.EnQue<DTYPE_Z>(zLocal);   
61 inQueueX.FreeTensor(xLocal);   
62 inQueueY.FreeTensor(yLocal);   
63 }   
(msdebug) 

# 说明

其他调试操作可参考导入调试信息、7.5 内存与变量打印、7.10 调试信息展示及7.8 核切换等， 与其操作一致。 

步骤10 删除断点，具体操作请参见删除断点。 

步骤11 调试完以后，执行q命令并输入Y或y结束调试。 

```txt
(msdebug) q Quitting LLDB will kill one or more processes. Do you really want to proceed: [Y/n] y 
```

----结束 

# 7.12.4 上板调试模板库的算子

展示如何使用msDebug工具来上板调试一个模板库算子（matmul），该算子可实现 两个矩阵相乘并输出结果的功能。 

# 前提条件

单击Link获取样例工程，为进行算子调试做准备。 

参考7.2 使用前准备完成相关环境变量配置。 

# 操作步骤

步骤1 基于前提条件中的样例工程编译算子，获取可执行文件00_basic_matmul。 

执行以下命令完成算子编译，编译完成后，在build/bin目录下生成可执行文件 00_basic_matmul。 

```batch
bash ./scripts/build.sh 00basic_matmul --debug --msdebug 
```

步骤2 启动msDebug工具拉起算子程序，进入调试界面。 

```txt
msdebug ./build/bin/00basic_matmul 256 512 1024 0 (msdebug) target create ".build/bin/00basic_matmul" Current executable set to '/home/mindstudio/projects/ascendc-templates/build/bin/00basic_matmul' (aarch64). (msdebug) 
```

步骤3 设置断点。 

该用例中核函数的代码实现位于basic_matmul.hpp中，在此文件中，为需要的代码行 设置NPU断点。 

```txt
(msdebug) b basic_matmul.hpp:121  
Breakpoint 1: 2 locations.  
(msdebug) 
```

步骤4 运行算子程序，等待直到命中断点。 

程序会开始运行直到命中第一个断点（basic_matmul.hpp:127）后停下，msDebug检 测到NPU核函数开始运行，运行在Device 0。 

# 说明

_ZN7Catlass13KernelAdapterINS_4Gemm6Kernel11BasicMatmulINS1_5Blo为模板库的 kernel名字，示例仅显示前面64位。 

(msdebug) run   
Process 3344307 launched: '/home/mindstudio/projects/ascendc-templates/build/bin/00basic_matmul' (aarch64)   
[Launch of Kernel_ZN7Catlass13KernelAdapterINS_4Gemm6Kernel11BasicMatmulINS1_5Blo on Device 0]   
Process 3344307 stopped   
[Switching to focus on Kernel_ZN7Catlass13KernelAdapterINS_4Gemm6Kernel11BasicMatmulINS1_5Blo, Coreld 21, Typeaic] \* thread #1, name $=$ '00/basic_matmul', stop reason $=$ breakpoint 1.1 frame #0: 0x0000000000001c38   
device_debugdata`_ZN7Catlass13KernelAdapterINS_4Gemm6Kernel11BasicMatmulINS1_5Block9BlockMmad INS1_19MmadAtlasA2PingpongILb1EEENS_9GemmShapeILj128ELj256ELj256EEENS8_ILj128ELj256ELj64EEEN S1_8GemmTypelDhNS_6layout8RowMajorELN7AscendC9TPositionE0EEESG_SVNS1_4Tile8TileCopyINS_4Ar ch7AtlasA2ESG_SG_SG_vEENSH_8TileMmadISK_SG_SG_vEEEEvNS4_24GemmldentityBlockSwizzleILj3ELj0EEE EEEEvNT_6ParamsE_mix_ac at basic_matmul.hpp:121:71   
118   
119 for (uint32_t loopIdx = AscendC::GetBlockIdx(); loopIdx < coreLoops; loopIdx += AscendC::GetBlockNum()) {   
120 // Compute block location   
-> 121 GemmCoord blockCoord $=$ matmulBlockScheduler.GetBlockCoord(lopldx);   
122 GemmCoord actualBlockShape $=$ matmulBlockScheduler但实际上BlockShape(blockCoord);   
123   
124 // Compute initial location in logical coordinates   
(msdebug) 

步骤5 检视信息。 

# 说明

其他调试操作可参考7.5 内存与变量打印、7.10 调试信息展示及7.8 核切换等，与其操作一致。 

使用ascend info cores命令查询NPU核信息。 

```txt
(msdebug) ascend info cores  
Coreld Type Device Stream Task Block PC stop reason  
* 21 aic 0 48 0 0 0x12c0c00d6c38 breakpoint 1.1  
22 aic 0 48 0 1 0x12c0c00d6c38 breakpoint 1.1  
23 aic 0 48 0 2 0x12c0c00d6c38 breakpoint 1.1  
24 aic 0 48 0 3 0x12c0c00d6c38 breakpoint 1.1  
(msdebug) 
```

使用print命令直接打印gmA变量信息。 

```txt
(msdebug) print gmA  
(AscendC::GlobalTensor<__fp16>) $0 = {  
    AscendC::BaseGlobalTensor<__fp16> = {  
        address_ = 0x000012c0c0013000  
        oriAddress_ = 0x000012c0c0013000  
    }  
bufferSize_ = 0  
cacheMode_ = Cache_MODE_NORMAL 
```

继续使用memory read命令可打印出gmA变量中存放的值。 

打印位于GM内存上的gmA中存放的数据。 

```txt
(msdebug) memory read -m GM 0x12c0c0013000 -f float16[] -s 256 -c 1  
0x12c0c0013000: {3.40234 -1.05664 2.83008 2.98438 4.11719 -3.02539 -1.64746 2.68164 -2.22266 0.539551 -0.226074 1.28906 -1.35254 0.134033 4.52344 4.16016 1.35742 2.17383 -3.58398 1.06934 -4.83594 -2.57031 -3.62695 3.04102 -3.43359 -0.990723 -3.70117 -3.91211 4.98828 -2.81836 0.129272 3.39062 1.12598 -2.03906 1.37598 0.24292 -0.0641479 4.72656 -2.07422 2.71289 0.267334 2.69922 -0.997559 3.91602 -2.16602 -1.47559 3.07812 4.19141 -4.30078 4.49219 0.26001 -4.14062 -3.07812 1.63184 3.90234 -1.51074 -4.35938 -4.80078 -0.423096 -4.36719 -2.61719 4.70703 4.02344 3.50977 -2.33398 0.397705 -1.24805 2.60156 0.125366 1.67676 0.316162 -4.60547 -0.623535 4.31641 4.30859 2.20898 -2.15625 2.38477 1.39941 -1.45996 1.87891 -3.33984 -0.599121 3.80078 3.29297 -1.69629 -2.71094 3.93359 -1.49609 1.86621 4.56641 0.88623 1.57324 3.58594 -0.604492 4.23828 -1.01562 3.14844 1.8418 4.10938 -0.175049 -2.8418 4.50391 4.20312 -3.52344 3.81055 1.41113 -0.680664 1.19629 -2.18945 2.85938 -1.92578 -0.529785 -2.73828 -3.125 -2.23828 0.564453 -0.834961 -3.30469 4.06641 -3.96875 -3.73828 -0.0455627 2.60547 4.84766 4.35156 1.84473 -1.16797} (msdebug) 
```

进行核切换，切换至另一个aic核，并打印需要的信息。 

```txt
(msdebug) ascend aic 24 // ascend info cores中选择block3对应的coreId,此处为24
[Switching to focus on Kernel
ZN7Catlass13KernelAdapterINS_4Gemm6Kernel11BasicMatmulINS1_5Blo, Coreld 24, Type aic]
* thread #1, name = '00basic_matmul', stop reason = breakpoint 1.1
frame #0: 0x000000000001c38
deviceDebugdata_ZN7Catlass13KernelAdapterINS_4Gemm6Kernel11BasicMatmulINS1_5Block9Block
MmadINS1_19MmadAtlasA2PingpongILb1EEENS_9GemmShapeILj128ELj256ELj256EEENS8_ILj128ELj2
56ELj64EEENS1_8GemmTypeDhNS_6layout8RowMajorELN7AscendC9TPositionE0EEESG_SG_vNS1_4Til
e8TileCopyINS_4Arch7AtlasA2ESG_SG_SG_vEENSH_8TileMmadISK_SG_SG_vEEEEvNS4_24GemmIdentit
yBlockSwizzleILj3ELj0EEMEEMEvNT_6ParamsE_mix_aic at basic_matmul.hpp:121:71
118
119 for (uint32_t loopIdx = AscendC::GetBlockIdx(); loopIdx < coreLoops; loopIdx += AscendC::GetBlockNum())
{
120 // Compute block location
-> 121 GemmCoord blockCoord = matmulBlockScheduler.GetBlockCoord(looplIdx);
122 GemmCoord actualBlockShape =
matmulBlockScheduler但实际上块
123
124 //Compute initial location in logical coordinates
(msdebug) p loopIdx
 uint32_t $1 = 0 
```

步骤6 查询并删除断点，恢复程序运行。 

(msdebug) breakpoint list 

Current breakpoints: 

1: file $=$ 'basic_matmul.hpp', line $= 1 2 1$ , exact_match $= 0$ , locations $^ { = 2 }$ , resolved $^ { = 2 }$ , hit count $= 1$ 

1.1: where $=$ 

device_debugdata`_ZN7Catlass13KernelAdapterINS_4Gemm6Kernel11BasicMatmulINS1_5Block9BlockMmad INS1_19MmadAtlasA2PingpongILb1EEENS_9GemmShapeILj128ELj256ELj256EEENS8_ILj128ELj256ELj64EEEN S1_8GemmTypeIDhNS_6layout8RowMajorELN7AscendC9TPositionE0EEESG_SG_vNS1_4Tile8TileCopyINS_4Ar ch7AtlasA2ESG_SG_SG_vEENSH_8TileMmadISK_SG_SG_vEEEEvNS4_24GemmIdentityBlockSwizzleILj3ELj0EEE EEEEvNT_6ParamsE_mix_aic $^ +$ 4748 [inlined] 

_ZN7Catlass4Gemm6Kernel11BasicMatmulINS0_5Block9BlockMmadINS0_19MmadAtlasA2PingpongILb1EEE NS_9GemmShapeILj128ELj256ELj256EEENS7_ILj128ELj256ELj64EEENS0_8GemmTypeIDhNS_6layout8RowMa jorELN7AscendC9TPositionE0EEESF_SF_vNS0_4Tile8TileCopyINS_4Arch7AtlasA2ESF_SF_SF_vEENSG_8TileMm adISJ_SF_SF_vEEEEvNS3_24GemmIdentityBlockSwizzleILj3ELj0EEEEclILi1EEEvRKNSQ_6ParamsE_mix_aic $^ +$ 4632 at basic_matmul.hpp:121:71, address = 0x0000000000001c38, resolved, hit count $= 1$ 1.2: where $=$ device_debugdata`_ZN7Catlass13KernelAdapterINS_4Gemm6Kernel11BasicMatmulINS1_5Block9BlockMmad 

```html
INS1_19MmadAtlasA2PingpongILb1EEENS_9GemmShapeILj128ELj256ELj256EEENS8_ILj128ELj256ELj64EEEN S1_8GemmTypeIDhNS_6layout8RowMajorELN7AscendC9TPositionE0EEESG_SG_vNS1_4Tile8TileCopyINS_4Ar ch7AtlasA2ESG_SG_SG_vEENSH_8TileMmadISK_SG_SG_vEEEEvNS4_24GemmIdentityBlockSwizzleILj3ELj0EEE EEEEvNT_6ParamsEm_mix_aic + 4772 [inlined] _ZN7Catlass4Gemm6Kernel11BasicMatmulINS0_5Block9BlockMmadINS0_19MmadAtlasA2PingpongILb1EEE NS_9GemmShapeILj128ELj256ELj256EEENS7_ILj128ELj256ELj64EEENS0_8GemmTypeIDhNS_6layout8RowMa jorELN7AscendC9TPositionE0EEESF_SF_vNS0_4Tile8TileCopyINS_4Arch7AtlasA2ESF_SF_SF_vEENSG_8TileMm adISJ_SF_SF_vEEEEvNS3_24GemmIdentityBlockSwizzleILj3ELj0EEEecllli1EEEvRKNSQ_6ParamsE_mix_aic + 4632 at basic_matmul.hpp:121:71, address = 0x000000000000dd54, resolved, hit count = 0 (msdebug) breakpoint delete 1 1 breakpoints deleted; 0 breakpoint locations disabled. (msdebug) continue Process 3344307 resuming Compare success. Process 3344307 exited with status = 0 (0x00000000) 
```

步骤7 调试完以后，执行q命令并输入Y或y结束调试。 

```txt
(msdebug) q 
```

----结束