<!-- Source: 算子开发工具.md lines 9970-10159 | Section: 8.14 扩展接口（mstx） -->

# 8.14 扩展接口（mstx）

# 8.14.1 mstx 接口简介

mstx接口是MindStudio提供的一个性能分析接口，它允许用户在应用程序中插入特定 的标记，以便在性能分析时能够更精确地定位关键代码区域，具体接口明细请参见表 8-32和表8-33。 

# 说明

Kernel直调中的内核调用符场景暂不支持使用mstx接口。 


表 $8 - 3 2 \subset / \mathsf { C } + +$ mstx 接口列表


<table><tr><td>接口名称</td><td>接口说明</td><td>msProf工具支持情况</td></tr><tr><td>mstxMarkA</td><td>标识瞬时事件。</td><td>不支持。</td></tr><tr><td>mstxRangeStartA</td><td>标识时间段事件的开始。</td><td>支持。</td></tr><tr><td>mstxRangeEnd</td><td>标识时间段事件的结束。</td><td>支持。</td></tr></table>


表 8-33 Python mstx 接口列表


<table><tr><td>接口名称</td><td>接口说明</td><td>msProf工具支持情况</td></tr><tr><td>mstxMark</td><td>标识瞬时事件。</td><td>不支持。</td></tr><tr><td>mstx(range_start</td><td>标识时间段事件的开始。</td><td>支持。</td></tr><tr><td>mstx.range_end</td><td>标识时间段事件的结束。</td><td>支持。</td></tr></table>

# mstx 接口的使用

msProf工具允许用户通过mstx接口实现特定算子调优的功能，使用mstx接口可以 自定义采集代码段范围内或指定关键函数的开始和结束时间点，并识别关键函数 或计算API等信息，对性能问题快速定界。 

默认情况下mstx接口是不使能的。若用户在应用程序中调用mstx接口后，会根据 具体使用场景使能mstx打点功能。例如使用msProf工具进行命令行采集时，可配 置--mstx=on使能用户代码程序中使用的mstx API，或通过--mstx-include用户指 定的mstx API，具体请参见命令汇总中的--mstx和--mstx-include参数。 

mstx当前提供了两种API的使用方式：库文件和头文件，以Link为例： 

# 说明

● 此样例工程不支持Atlas A3 训练系列产品。 

在${git_clone_path}/samples/operator/ascendc/0_introduction/ 1_add_frameworklaunch/AclNNInvocation/src/CMakeLists.txt路径下新增 库文件libms_tools_ext.so，地址为：${INSTALL_DIR}/lib64/ libms_tools_ext.so。 # Header path include_directories( ... ${CUST_PKG_PATH}/include target_link_libraries( ... dl 

在${git_clone_path}/samples/operator/ascendc/0_introduction/ 1_add_frameworklaunch/AclNNInvocation/src/main.cpp路径下，将用户程 序编译链接dl库，对应的头文件ms_tools_ext.h地址：${INSTALL_DIR}/ include/mstx。 #include "mstx/ms_tools_ext.h" ... 

# 说明

● ${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。若安装的Ascendcann-toolkit软件包，以root安装举例，则安装后文件存储路径为：/usr/local/ Ascend/ascend-toolkit/latest。 

# 8.14.2 mstxRangeStartA

# 函数原型

$\mathbb { C } / \mathbb { C } { \mathrm { + + } }$ 函数原型：mstxRangeId mstxRangeStartA(const char *message, aclrtStream stream) 

Python函数：mstx.range_start(message, stream) 

# 功能说明

mstx指定范围能力的起始位置标记。 

# 参数说明


表 8-34 参数说明


<table><tr><td>参数</td><td>输入/输出</td><td>说明</td></tr><tr><td>message</td><td>输入</td><td>message为标记的文字，携带打点信息。
C/C++中数据类型：const char *。Python中，message为字符串。默认None。
传入的message字符串长度要求：
·MSPTI场景：不能超过255字节。
·非MSPTI场景（例如msprof命令行、Ascend PyTorch Profiler）：不能超过156字节。说明
message不能传入空指针。</td></tr><tr><td>stream</td><td>输入</td><td>stream表示使用mark的线程。
C/C++中数据类型：aclrtStream。Python中stream是aclrtStream对象。
默认None。</td></tr></table>

# 返回值

如果返回0，则表示失败。 

# 调用示例

$\mathsf { C } / \mathsf { C } + +$ 调用方法： 

```cpp
bool RunOp()
{
// create op desc
char message = "h1";
mstxRangeld id = mstxRangeStartA(message, NULL);
// Run op
if (!opRunner.RunOp())
{
ERROR_LOG("Run op failed");
return false;
} 
```

```txt
…} 
```

Python调用方法一： 

通过Python API接口，以 $\mathbb { C } / \mathbb { C } { + + }$ 语言实现相关接口内容并编译生成so，相关so在 PYTHONPATH中可以被python直接引用。 

```python
import mstx  
mstx range start("aaa")  
print(1)  
mstx range end(1)  
import torch  
import torch_npu  
a = torch.Tensor([[1,2,3,4]).npu()  
b = torch.Tensor([[1,2,3,4]).npu()  
hi_str = "hi"  
hello_str = "hello"  
hi_id = mstx范围 start(hi_str, None)  
c = a + b  
hello_id = mstx范围 start(hello_str, stream=None)  
d = a - b  
mstx范围 end(hi_id)  
e = a * b  
mstx范围 end(hello_id) 
```

Python调用方法二： 

直接使用Python开发，通过ctypes.CDLL("libms_tools_ext.so")直接引用原mstx的 so文件，并使用其中提供的API。 

```python
import mstx  
import torch  
import torch_npu  
import acl  
import sys  
import ctypes  
lib = ctypes.CDLL("libms.tools_ext.so")  
#定义函数的参数类型和返回类型  
lib.mstxRangeStartA.argtypes = [ctypes.c_char_p, ctypes.c Void_p]  
lib.mstxRangeStartActype = ctypes.c_uint64  
lib.mstxRangeEnd.argtypes = [ctypes.c_uint64]  
lib.mstxRangeEndctype = None  
a = torch.Tensor([1,2,3,4]).npu()  
b = torch.Tensor([1,2,3,4]).npu()  
#创建一个ctypes.c_char_p指针  
hi_str = b"hi"  
hi_ptr = ctypes.c_char_p(hi_str)  
hi_id = ctypes.c_uint64()  
#创建一个ctypes.c_char_p指针  
hello_str = b"hello"  
hello_ptr = ctypes.c_char_p(hello_str)  
hello_id = ctypes.c_uint64()  
#调用函数  
hi_id.value = lib.mstxRangeStartA(hi_ptr, None)  
c = a + b  
hello_id.value = lib.mstxRangeStartA(hello_ptr, None)  
d = a - b  
lib.mstxRangeEnd(hi_id)  
e = a * b  
lib.mstxRangeEnd(hello_id) 
```

# 8.14.3 mstxRangeEnd

# 函数原型

$\mathbb { C } / \mathbb { C } { \mathrm { + + } }$ 函数原型：void mstxRangeEnd(mstxRangeId id) 

Python函数：mstx.range_end(range_id) 

# 功能说明

mstx指定范围能力的结束位置标记。 

# 参数说明


表 8-35 参数说明


<table><tr><td>参数</td><td>输入/输出</td><td>说明</td></tr><tr><td>id (C/C++)</td><td>输入</td><td>通过mstxRangeStartA返回的id (C/C++)。</td></tr><tr><td>range_id (Python)</td><td>输入</td><td>通过mstx range start返回的 range_id (Python)。</td></tr></table>

# 返回值

如果返回0，则表示失败。 

# 调用示例

C/C++调用：mstxRangeEnd接口需要与mstxRangeStartA配合使用，具体示例请参考 C/C++调用方法。 

Python调用：mstx.range_end接口需要与mstx.range_start配合使用，具体示例请参 考Python调用方法。 

# 9 附录

TBE&AI CPU算子开发场景