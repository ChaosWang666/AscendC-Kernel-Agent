<!-- Source: 算子开发工具.md lines 8429-8582 | Section: 7.13 FAQ -->

# 7.13 FAQ

# 7.13.1 msDebug 工具使用"-O0 -g"编译算子时，stack frame size 超出限制

# 现象描述

出现以下报错： 

```txt
[33%] Building CCE object cmake/npu/CMakeFiles/reduce_sumcustom_npu.dir/// reduce_sum(custom.cpp.o   
error: stack frame size (16024) exceeds limit (16000) in function 'ZN7AscendC9ReduceSumIDhEEvRKNS_11LocalTensorIT_EES5_S5_i'   
error: stack frame size (16024) exceeds limit (16000) in function 'ZN7AscendC9ReduceSumIDhEEvRKNS_11LocalTensorIT_EES5_S5_i'   
2 errors generated. 
```

# 原因分析

出现该错误代表核函数使用的栈空间过大，超过了硬件限制。 

# 解决措施

可通过以下两种方法进行解决： 

手动增加编译选项 --cce-ignore-always-inline=true ，解除Ascend C相关函数声 明时设置的inline属性，使函数运行正常跳转，减少栈空间使用大小。 

更新编译器版本，将编译选项设置为 -O0 -g时，编译器会自动使能 --cce-ignorealways-inline=true。 

说明 

使用ccec -v命令可查询编译器版本，建议使用2024-07及之后的编译器版本。 

# 7.13.2 msDebug 工具打印 Tensor 变量功能不可用，提示 “unavailable”或“memory read failed”

# 现象描述

提示“unavailable”或“Failed to dereference pointer from xxx for DW_OP_deref: memory read failed for xxx” 。 

# 原因分析

单步调试功能不支持Tensor按值传递的写法。 

# 解决措施

当打印对象a为Tensor类型且以值传递作为函数入参时会出现该问题。 

void Foo(const LocalTensor<float> a); // 该写法变量a打印失败 

若需打印该变量，可修改代码使对象a以引用传递作为函数入参，修复该问题。 

void Foo(const LocalTensor<float> &a); // 该写法变量a可正常打印 

# 7.13.3 msDebug 工具在容器环境中调试运行失败，提示需安装 HDK 驱动包

# 现象描述

提示msdebug failed to initialize. please install HDK with --debug before debugging。 

# 原因分析

未使用--debug选项安装HDK驱动包或msDebug工具依赖的驱动设备节点/dev/ drv_debug未映射至容器环境内。 

# 解决措施

步骤1 检查宿主机是否使用--debug选项安装HDK驱动包。 

若回显一致，则调试驱动已安装；否则需要使用--debug命令安装配套的HDK驱动包。 [mindstudio@localhost ~]$ ls /dev/drv_debug #查看是否存在/dev/drv_debug设备节点 /dev/drv_debug 

步骤2 若驱动包已安装，算子运行环境为容器环境，那么请检查该容器环境中是否满足以下 条件。 

能找到调试依赖的设备节点/dev/drv_debug。 

容器环境具有该设备节点的访问权限。 

# 说明

建议在容器启动命令中增加选项--privileged --device=/dev/drv_debug，可保证调试依赖的设备 节点被映射，且允许容器环境访问该节点。 

----结束 

# 7.13.4 msDebug 工具断点设置在核函数内，命中断点后执行 continue 命令，算子运行失败

# 现象描述

显示Synchronize stream failed. error code is 507035，查看plog显示aic error code=0x8000000000000000，并且在命中断点时使用ascend info cores命令可以看到 当前核的PC值与预期不符。 

# 原因分析

Kernel函数中workspace入参的空间大小在Tiling函数中被设置为0，经过单算子API调 用后变成一个非法地址。虽然workspace入参在Kernel函数未被使用，调试器展示 Kernel入参时也会对workspace指针进行解引用，导致算子运行错误。 

# 解决措施

参考《Ascend C算子开发指南》中的“工程化算子开发 > 算子实现 > Host侧tiling实 现”章节，将workspaceSize从0设置成预留内存大小。API在计算过程需要一些 workspace内存作为缓存，因此算子Tiling函数需要为API预留workspace内存，预留内 存大小通过GetLibApiWorkSpaceSize接口获取。参考如下代码： 

```cpp
include "tiling/platform/platform ascendc.h"  
auto ascendcPlatform = platform ascendc::PlatformAscendC(context->GetPlatformInfo());  
size_t systemWorkspaceSize = ascendcPlatform.GetLibApiWorkSpaceSize();  
size_t*currentWorkspace = context->GetWorkspaceSizes(1); //只使用1块Workspace  
currentWorkspace[0] = systemWorkspaceSize; 
```

# 7.13.5 msDebug 工具在 docker 中执行"run"命令运行程序后，提 示“'A' packet returned an error: 8”

# 现象描述

在docker中，msDebug工具在执行"run"命令运行程序后，出现以下报错。 

```python
(msdebug) run  
'A' packet returned an error: 8 (msdebug) 
```

# 原因分析

出现该错误，可能与“地址空间布局随机化”有关。 

# 解决措施

需输入并执行下列命令来规避此问题。 

```txt
... (msdebug) settings set target.disable-aslr false ... 
```

# 8 算子调优（msProf）

工具概述 

使用前准备 

工具使用 

计算内存热力图 

Roofline瓶颈分析图 

Cache热力图 

通算流水图 

指令流水图 

算子代码热点图 

内存通路吞吐率波形图 

性能数据文件 

Json配置文件说明 

典型案例 

扩展接口（mstx）