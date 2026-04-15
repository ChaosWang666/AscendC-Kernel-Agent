<!-- Source: 算子开发工具.md lines 3066-3695 | Section: 3.5 自动调优 -->

# 3.5 自动调优

# 3.5.1 功能介绍

在进行模板库算子开发时，利用msKPP提供的接口在Python脚本中快速实现Kernel下 发代码生成、编译及运行Kernel。 

在对模板库算子进行性能调优时，通常需要对Kernel的模板参数（比如L0shape大小） 进行多次调整并对比性能结果。为提升调优效率，msKPP工具提供了3.5.4.1 autotune系列接口支持开发者可以高效地针对多个调优点进行代码替换、编译、运行 以及性能对比。 

# 说明

自动调优功能仅支持Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组件。 

# 使用约束

单Device仅支持使用单个msKPP工具进行自动调优，且不推荐同时运行其他算子 程序。 

需确保先import mskpp再import acl，否则需要在运行前设置环境变量。 export LD_PRELOAD=${INSTALL_DIR}/lib64/libmspti.so 

# 3.5.2 快速入门

本章节以单算子00_basic_matmul为例，帮助用户快速上手msKPP工具的Kernel级自 动调优功能。 

# 操作步骤

步骤1 执行以下命令，下载Link中的Ascend C模板库。 

```batch
git clone https://github.com/cann/catlass.git -b catlass-v1-stable 
```

步骤2 进入模板库中的00_basic_matmul样例代码目录。 

```txt
cd catlass/examples/00/basic_matmul 
```

步骤3 修改basic_matmul.cpp文件，在L1TileShape、L0TileShape变量声明的行末尾添加注 释 （// tunable）。 

```txt
// basic_matmul.cpp  
...  
51 using L1TileShape = GemmShape<128, 256, 256>; // tunable  
52 using L0TileShape = GemmShape<128, 256, 64>; // tunable 
```

步骤4 将附录中Python脚本文件3.5.5.1 basic_matmul_autotune.py与编译脚本文件3.5.5.2 jit_build.sh保存至00_basic_matmul目录中。 

步骤5 运行样例脚本basic_matmul_autotune.py。 

$ python3 basic_matmul_autotune.py
No.0: 22.562 $\mu$ s,{'L1TileShape': 'GemmShape<128, 256, 256>', 'L0TileShape': 'GemmShape<128, 256, 64>}'
No.1: 22.109 $\mu$ s,{'L1TileShape': 'GemmShape<128, 256, 128>', 'L0TileShape': 'GemmShape<128, 256, 64>}'
No.2: 17.778 $\mu$ s,{'L1TileShape': 'GemmShape<128, 128, 256>', 'L0TileShape': 'GemmShape<128, 128, 64>}'
No.3: 15.378 $\mu$ s,{'L1TileShape': 'GemmShape<64, 128, 128>', 'L0TileShape': 'GemmShape<64, 128, 128>}'
No.4: 14.982 $\mu$ s,{'L1TileShape': 'GemmShape<64, 128, 256>', 'L0TileShape': 'GemmShape<64, 128, 128>}'
No.5: 15.671 $\mu$ s,{'L1TileShape': 'GemmShape<64, 128, 512>', 'L0TileShape': 'GemmShape<64, 128, 128>}'
No.6: 19.592 $\mu$ s,{'L1TileShape': 'GemmShape<64, 64, 128>', 'L0TileShape': 'GemmShape<64, 64, 128>}'
No.7: 18.340 $\mu$ s,{'L1TileShape': 'GemmShape<64, 64, 256>', 'L0TileShape': 'GemmShape<64, 64, 128>}'
No.8: 18.541 $\mu$ s,{'L1TileShape': 'GemmShape<64, 64, 512>', 'L0TileShape': 'GemmShape<64, 64, 128>}'
No.9: 20.652 $\mu$ s,{'L1TileShape': 'GemmShape<128, 128, 128>', 'L0TileShape': 'GemmShape<128, 128, 128>}'
No.10: 17.728 $\mu$ s,{'L1TileShape': 'GemmShape<128, 128, 256>', 'L0TileShape': 'GemmShape<128, 128, 128>}'
No.11: 17.637 $\mu$ s,{'L1TileShape': 'GemmShape<128, 128, 512>', 'L0TileShape': 'GemmShape<128, 128, 128>}'
Best config: No.4
compare success. 

以上显示数据表示在算子代码basic_matmul.cpp中，L1TileShape定义为 GemmShape<64, 128, $2 5 6 >$ 且L0TileShape定义为GemmShape<64, 128, $\boldsymbol { 1 2 8 } \boldsymbol { > }$ 时，性 能最优。 

----结束 

# 3.5.3 自动调优示例

# 自动调优流程

自动调优流程包括Kernel级自动调优和应用级自动调优两种，具体流程请参见图3-7， 具体操作请参见Kernel级自动调优和应用级自动调优。 


图 3-7 自动调优流程示意图


![](images/0da145e0ee72b52f80e9142292f991a384ada3375128bd807e6d11ab448dae64.jpg)


# Kernel 级自动调优

本章节以模板库catlass-v1-dev分支的examples/00_basic_matmul为例，介绍如何利 用msKPP工具提供的Python接口实现Kernel级自动调优。 

# 说明

在运行过程中出现任何异常，可通过设置环境变量的方式来查看debug日志以及保留中间文件， 便于问题定位。 

```txt
export MSKPP_LOG_LEVEL=0 
```

步骤1 完成算子Kernel开发后，Kernel函数的定义与实现将会呈现在basic_matmul.cpp文件 中，如下所示。 

```cpp
// basic_matmul.cpp  
// ...  
template<class LayoutA, class LayoutB, class LayoutC>  
ACTGLOBAL void BasicMatmul(GemmCoord problemShape, GM_ADDR gmA, LayoutA layoutA, GM_ADDR gmB, LayoutB layoutB, 
```

```txt
GM_ADDR gmc, LayoutC layoutC  
}  
{  
// Kernel 实现  
}  
// ... 
```

步骤2 参考附录，在examples/00_basic_matmul目录中创建Python脚本文件3.5.5.1 basic_matmul_autotune.py与编译脚本文件3.5.5.2 jit_build.sh。 

按照如下要求，定义算子Kernel函数的Python接口：在Python脚本中定义 basic_matmul函数，其入参需与 $\mathsf { C } { + + }$ 代码中的Kernel函数保持一致。 

# basic_matmul_autotune.py   
import mskpp   
def get_kernel(): kernel_file $=$ "/basic_matmul.cpp" kernel_name $=$ "BasicMatmul" build_script $=$ "/jit_build.sh" # kernel compile script config $=$ mskpp.KernelInvokeConfig(kernel_file, kernel_name) gen_file $=$ mskpp.Launcher(config).code_gen() kernel $=$ mskpp.compile(build.script $\equiv$ build.script, launch_src_file $\equiv$ gen_file) return kernel   
def basic_matmul解决问题_shape, a, layout_a, b, layout_b, c, layout_c): # This function's input arguments must exactly match the kernel function. kernel $=$ get_kernel() blockdim $= 20$ # use the correct aic number that matches your hardware return kernel[blockdim](problem_shape, a, layout_a, b, layout_b, c, layout_c, device_id $\coloneqq 1$ ) # invoke the kernel 

步骤3 参考如下代码实现，构造Kernel入参，实现basic_matmul函数的正常运行。 

若算子Kernel函数入参是GM_ADDR，则构造入参需使用numpy.array类型。 

若算子Kernel函数入参是 $\cdot + +$ 结构体对象，则需依靠ctypes.Structure在Python中 构建一个相同的结构体。 

basic_matmul_autotune.py   
import numpy as np   
from ctypes import Structure, c_uint32, c_int32, c_int64   
class GemmCoord(Structure): _fields_ $=$ ["m",c_uint32), ("n",c_uint32), ("k",c_uint32)] def init_self,m,n,k): super().init_(self.m $=$ (c_uint32)(m) self.n $=$ (c_uint32)(n) self.k $=$ (c_uint32)(k) @staticmethod def getnamespace(): return "Catlass:"   
class RowMajor(Structure): _fields_ $=$ ["shape",c_int32*2), ("stride",c_int64*2)] def init_self,rows:int = 0,cols:int = 0,ldm:int $\equiv$ None): super().init_(self.shape $=$ (c_int32*2)(rows,cols) if ldm is None: self=stride $\equiv$ (c_int64*2)(cols,1) else: self.stride $\equiv$ (c_int64*2)((c_int64)(ldm),1) @staticmethod def get namespace(): return "Catlass::layout:"   
if_name $= = =$ ""main_: m=256 n=512 

```lua
k = 1024  
problem_shape = GemCoord(m, n, k)  
layout_a = RowMajor(m, k)  
layout_b = RowMajor(k, n)  
layout_c = RowMajor(m, n)  
a = np.random.randint(1, 2, [m, k]).subtype(np.full)  
b = np.random.randint(1, 2, [k, n]).subtype(np.full)  
c = np.zeros([m, n]).subtype(np.full)  
basic_matmul解决问题, a, layout_a, b, layout_b, c, layout_c  
# check if the output tensor c is consistent with the golden data  
golden = np/matmul(a, b)  
is unequal = np.array unequal(c, golden)  
result = "success" if is unequal else "failed"  
print("compare {}.".format(result)) 
```

步骤4 运行Python脚本，获得如下提示，说明算子Kernel已可正常通过Python接口拉起。 

```txt
$ python3 basic_matmul_autotune.py compare success. 
```

步骤5 在算子代码程序basic_matmul.cpp中标识需调优的参数。 

在模板参数的声明代码行末尾使用// tunable标记，用于替换"="号后的代码内容。 

```txt
using L1TileShape = GemmShape<128, 256, 256>; // tunable using L0TileShape = GemmShape<128, 256, 64>; // tunable 
```

# 说明

除tunable标识的方法之外，还可以通过换行，在需要整行替换的代码行末尾使用// tunable: 别 名（L0Shape）方式标记。其中，别名用于搜索空间索引。 

```txt
using L0TileShape = MatmulShape<128, 256, 64>; // tunable: L0Shape 
```

步骤6 通过3.5.4.1 autotune接口的configs入参定义参数搜索空间，每一类参数组合会替换 算子Kernel代码中被标记的代码行，然后进行编译、运行并完成Kernel性能采集。搜索 空间定义示例可参考如下所示。 

# 说明

● 参数替换需合理，不能造成编译或运行错误。 

● 参数替换原则如下（以configs中的第一行为例）： 

1. 先替换// tunable: L0Shape方式标记的参数，将标记代码行（MatmulShape<128, 256, 64>）整行替换为configs中的value字符串（MatmulShape<128, 256, 64>）。 

2. 再替换// tunable方式标记的代码行，将"="号后的MatmulShape<128, 256, $2 5 6 >$ 替换为 configs中value字符串MatmulShape<64, 64, $6 4 >$ 。 

不同作用域中，可能会有两个同名的变量被声明。若两个变量均符合匹配规则时， 仅第一个变量会被修改。 

若其中一个config未匹配成功，该config对应的任务会停止并报错。但其他匹配成 功的config将会成功进行参数替换。 

```jsonl
@mskpp.autotune(configs=[# add and try your own config here for a better kernel performance
{'L1TileShape': 'GemmShape<128, 256, 256>', 'L0TileShape': 'GemmShape<128, 256, 64>}#, #0 the same
config as in basic_matmul.cpp
{'L1TileShape': 'GemmShape<128, 256, 128>', 'L0TileShape': 'GemmShape<128, 256, 64>}',
{'L1TileShape': 'GemmShape<128, 128, 256>', 'L0TileShape': 'GemmShape<128, 128, 64>}',
{'L1TileShape': 'GemmShape<64, 128, 128>', 'L0TileShape': 'GemmShape<64, 128, 128>}',
{'L1TileShape': 'GemmShape<64, 128, 256>', 'L0TileShape': 'GemmShape<64, 128, 128>}',
{'L1TileShape': 'GemmShape<64, 128, 512>', 'L0TileShape': 'GemmShape<64, 128, 128>}',
{'L1TileShape': 'GemmShape<64, 64, 128>', 'L0TileShape': 'GemmShape<64, 64, 128>}'],
{'L1TileShape': 'GemmShape<64, 64, 256>', 'L0TileShape': 'GemmShape<64, 64, 128>}',
{'L1TileShape': 'GemmShape<64, 64, 512>', 'L0TileShape': 'GemmShape<64, 64, 128>}'],
{'L1TileShape': 'GemmShape<128, 128, 128>', 'L0TileShape': 'GemmShape<128, 128, 128>}',
{'L1TileShape': 'GemmShape<128, 128, 256>', 'L0TileShape': 'GemmShape<128, 128, 128>} 
```

```python
{'L1TileShape': 'GemmShape<128, 128, 512>', 'L0TileShape': 'GemmShape<128, 128, 128>} }, warmup=1000, repeat=10, device_ids=[0]) # set kernel warmup 1000us 
```

步骤7 执行3.5.5.1 basic_matmul_autotune.py文件运行算子，获得每种参数组合的耗时及 最佳调优参数集合。以下仅展示可能的一种命令行输出结果。 

# python3 basic_matmul_autotune.py  
No.0: 22.562 $\mu$ s,{'L1TileShape': 'GemmShape<128, 256, 256>', 'L0TileShape': 'GemmShape<128, 256, 64>}  
No.1: 22.109 $\mu$ s,{'L1TileShape': 'GemmShape<128, 256, 128>', 'L0TileShape': 'GemmShape<128, 256, 64>}  
No.2: 17.778 $\mu$ s,{'L1TileShape': 'GemmShape<128, 128, 256>', 'L0TileShape': 'GemmShape<128, 128, 64>}  
No.3: 15.378 $\mu$ s,{'L1TileShape': 'GemmShape<64, 128, 128>', 'L0TileShape': 'GemmShape<64, 128, 128>}  
No.4: 14.982 $\mu$ s,{'L1TileShape': 'GemmShape<64, 128, 256>', 'L0TileShape': 'GemmShape<64, 128, 128>}  
No.5: 15.671 $\mu$ s,{'L1TileShape': 'GemmShape<64, 128, 512>', 'L0TileShape': 'GemmShape<64, 128, 128>}  
No.6: 19.592 $\mu$ s,{'L1TileShape': 'GemmShape<64, 64, 128>', 'L0TileShape': 'GemmShape<64, 64, 128>}  
No.7: 18.340 $\mu$ s,{'L1TileShape': 'GemmShape<64, 64, 256>', 'L0TileShape': 'GemmShape<64, 64, 128>}  
No.8: 18.541 $\mu$ s,{'L1TileShape': 'GemmShape<64, 64, 512>', 'L0TileShape': 'GemmShape<64, 64, 128>}  
No.9: 20.652 $\mu$ s,{'L1TileShape': 'GemmShape<128, 128, 128>', 'L0TileShape': 'GemmShape<128, 128, 128>}  
No.10: 17.728 $\mu$ s,{'L1TileShape': 'GemmShape<128, 128, 256>', 'L0TileShape': 'GemmShape<128, 128, 128>}  
No.11: 17.637 $\mu$ s,{'L1TileShape': 'GemmShape<128, 128, 512>', 'L0TileShape': 'GemmShape<128, 128, 128>}  
Best config: No.4  
compare success. 

通过对比得知，No.4为最佳调优参数集合。 

----结束 

# 应用级自动调优

本章节以模板库master分支的examples/00_basic_matmul为例，介绍如何利用 msKPP工具提供的Python接口实现对应用级的自动调优。 

# 说明

在运行过程中出现任何异常，可通过设置环境变量的方式来查看debug日志以及保留中间文件， 便于问题定位。 

```txt
export MSKPP_LOG_LEVEL=0 
```

步骤1 参考examples/00_basic_matmul示例，使用模板库Device层接口完成算子实现，并 分别在115、117行末尾添加// tunable注释，用于替换"="号后的代码内容。 

```txt
115 using L1TileShape = GemmShape<128, 256, 256>; // tunable  
116  
117 using L0TileShape = GemmShape<128, 256, 64>; // tunable 
```

步骤2 在examples/00_basic_matmul目录中创建Python脚本文件3.5.5.3 basic_matmul_executable_autotune.py与编译脚本文件3.5.5.4 jit_build_executable.sh。 

可根据实际需要修改3.5.5.3 basic_matmul_executable_autotune.py脚本中3.5.4.4 autotune_v2接口传入的configs参数以搜索自定义tiling参数组合。 

步骤3 运行Python脚本basic_matmul_autotune_executable.py，获取每种参数组合的耗时及 最佳调优参数集合。以下仅展示可能的一种命令行输出结果。 

```txt
# python3 basic_matmul_autotune_executable.py  
No.0: 64.081 us, {'L1TileShape': 'GemmShape<128, 256, 256> ', 'L0TileShape': 'GemmShape<128, 256, 64>}  
No.1: 68.041 us, {'L1TileShape': 'GemmShape<256, 128, 256> ', 'L0TileShape': 'GemmShape<256, 128, 64>}  
No.2: 60.701 us, {'L1TileShape': 'GemmShape<128, 128, 256> ', 'L0TileShape': 'GemmShape<128, 128, 64>}  
No.3: 61.121 us, {'L1TileShape': 'GemmShape<128, 128, 512> ', 'L0TileShape': 'GemmShape<128, 128, 64>}  
No.4: 62.361 us, {'L1TileShape': 'GemmShape<64, 256, 128> ', 'L0TileShape': 'GemmShape<64, 256, 64>}  
No.5: 60.661 us, {'L1TileShape': 'GemmShape<64, 256, 256> ', 'L0TileShape': 'GemmShape<64, 256, 64>}  
No.6: 58.261 us, {'L1TileShape': 'GemmShape<64, 128, 256> ', 'L0TileShape': 'GemmShape<64, 128, 64>}  
No.7: 62.381 us, {'L1TileShape': 'GemmShape<128, 128, 256> ', 'L0TileShape': 'GemmShape<128, 128, 128>}  
No.8: 62.621 us, {'L1TileShape': 'GemmShape<128, 128, 512> ', 'L0TileShape': 'GemmShape<128, 128, 128>} 
```

```csv
No.9: 57.501 us,{'L1TileShape': 'GemmShape<64, 128, 256>', 'L0TileShape': 'GemmShape<64, 128, 128>}  
No.10: 59.281 us,{'L1TileShape': 'GemmShape<64, 128, 512>', 'L0TileShape': 'GemmShape<64, 128, 128>}  
No.11: 65.041 us,{'L1TileShape': 'GemmShape<128, 64, 512>', 'L0TileShape': 'GemmShape<128, 64, 128>}  
No.12: 63.561 us,{'L1TileShape': 'GemmShape<64, 64, 256>', 'L0TileShape': 'GemmShape<64, 64, 256>}  
No.13: 65.121 us,{'L1TileShape': 'GemmShape<64, 64, 512>', 'L0TileShape': 'GemmShape<64, 64, 256>}  
No.14: 65.081 us,{'L1TileShape': 'GemmShape<64, 64, 1024>', 'L0TileShape': 'GemmShape<64, 64, 256>}  
Best config: No.9  
autom tune results saved in MSKPP_AUTOTUNE_results_20250604195710.csv 
```

通过对比得知，No.9为最佳调优参数集合。 

----结束 

# 3.5.4 接口列表

# 3.5.4.1 autotune

# 功能说明

遍历搜索空间，尝试不同参数组合，展示每个组合的运行耗时与最优组合。 

# 函数原型

```python
def autotune(configs: List[Dict], warmup: int = 300, repeat: int = 1, device_ids = [0]): 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>说明</td></tr><tr><td>configs</td><td>输入</td><td>搜索空间定义。数据类型: list[dict]。必选参数。</td></tr><tr><td>warmup</td><td>输入</td><td>采集性能前的设备预热时间。通常情况下,预热时间越长,采集到的算子性能越稳定。单位:微秒。可选参数,默认值:1000,取值范围为1~100000之间的整数。</td></tr><tr><td>repeat</td><td>输入</td><td>重放次数,会根据多次重放取运行耗时的平均值作为算子耗时。可选参数,默认值:1,取值范围为1~10000之间的整数。</td></tr><tr><td>device_ids</td><td>输入</td><td>Device ID列表,目前仅支持单Device模式,如果填写多个Device ID,只有第一个会生效。可选参数,默认值:[0]。</td></tr></table>

# 返回值说明

无。 

# 调用示例

```python
@mskpp.autotune(configs=[  
{'L1TileShape': 'MatmulShape<64, 64, 64>', 'L0TileShape': 'MatmulShape<128, 256, 64>'},  
{'L1TileShape': 'MatmulShape<64, 64, 128>', 'L0TileShape': 'MatmulShape<128, 256, 64>'},  
{'L1TileShape': 'MatmulShape<64, 128, 128>', 'L0TileShape': 'MatmulShape<128, 256, 64>'},  
{'L1TileShape': 'MatmulShape<64, 128, 128>', 'L0TileShape': 'MatmulShape<64, 256, 64>'},  
{'L1TileShape': 'MatmulShape<128, 128, 128>', 'L0TileShape': 'MatmulShape<128, 256, 64>'},  
], warmup=500, repeat=10, device_ids=[0])  
def basic_matmul解决问题_shape, a, layout_a, b, layout_b, c, layout_c):  
    kernel = get_kernel()  
    blockdim = 20  
    return kernel[blockdim](problem_shape, a, layout_a, b, layout_b, c, layout_c) 
```

# 3.5.4.2 code_gen

# 功能说明

根据输入的模板库Kernel信息，生成Kernel下发代码。 

# 函数原型

```python
gen_file = mskpp.Launcher(config).code_gen() 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>说明</td></tr><tr><td>gen_file</td><td>输入</td><td>指定生成Kernel侧下发代码的文件路径。
数据类型: str。
可选参数，默认值为_gen_launch.cpp。</td></tr></table>

# 返回值说明

生成代码的文件路径。 

# 调用示例

```python
config = mskpp.KernelInvokeConfig(kernel_file, kernel_name)
gen_file = mskpp.Launcher(config).code_gen() 
```

# 相关类/结构体定义

```python
class KornellInvokeConfig: A configuration descriptor for a possible kernel developed based on an Act example def __init__(self, kernel_src_file : str, kernel_name : str): pass   
#用户仅能传KornellInvokeConfig类型   
class Launcher: def __init__(self, config: KornellInvokeConfig): a class that generates launch source code for a kernel Args: config (KornellInvokeConfig): A configuration descriptor for a kernel 
```

# 3.5.4.3 compile

# 功能说明

编译Kernel下发代码，返回一个可执行的Kernel对象。 

# 函数原型

kernel $=$ compile(build_script, gen_file) 

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>说明</td></tr><tr><td>build_script</td><td>输入</td><td>用于模板库Kernel编译的脚本。
数据类型: str。
必选参数。</td></tr><tr><td>gen_file</td><td>输入</td><td>由code_gen接口生成的Kernel下发代码文件路径，一般直接使用code_gen接口返回值。
数据类型: str。
必选参数。</td></tr><tr><td>output_bin_path</td><td>输入</td><td>指定编译生成的可执行文件路径。
数据类型: str。
可选参数，默认值：_gen_module.so。</td></tr><tr><td>use_cache</td><td>输入</td><td>开启后不执行编译，加载output_bin_path所指定的文件。
数据类型: bool。
可选参数，默认值：False。</td></tr></table>

# 返回值说明

可运行的Kernel对象，类型：CompiledKernel，支持如下方式调用kernel： kernel[blockdim](arg1, arg2, ..., timeout=-1, device_id=0, repeat=1)，其中arg1、 arg2、...是Kernel的入参。 

调用示例 

kernel $=$ compile(build_script, gen_file) kernel[blockdim](arg1, arg2,..., device_id=0) 


表 3-6 CompiledKernel 可选入参介绍


<table><tr><td>参数名</td><td>输入/输出</td><td>说明</td></tr><tr><td>device_id</td><td>输入</td><td>NPU设备ID，设置运行ST测试用例的昇腾AI处理器的ID。数据类型：int。若未设置此参数，默认为0。</td></tr><tr><td>timeout</td><td>输入</td><td>camodel仿真场景需要默认设置较长超时时间，设置为-1时表示不限制。数据类型：int。单位：ms，默认值为300000。</td></tr><tr><td>repeat</td><td>输入</td><td>重复运行次数，默认值为1。数据类型：int。</td></tr><tr><td>stream</td><td>输入</td><td>预留参数。</td></tr><tr><td>kernel_name</td><td>输入</td><td>预留参数。</td></tr></table>

# 3.5.4.4 autotune_v2

# 功能说明

遍历搜索空间，尝试不同参数组合，展示每个组合的运行耗时与最优组合。 

# 函数原型

```python
def autotune_v2(configs: List[Dict], warmup(times = 5) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>说明</td></tr><tr><td>configs</td><td>输入</td><td>搜索空间定义。
数据类型：list[dict]。
必选参数。</td></tr><tr><td>warmup(times</td><td>输入</td><td>采集性能前的设备预热次数。
可选参数，默认值：5，取值范围为1~500之间的整数。</td></tr></table>

# 返回值说明

无。 

# 调用示例

```txt
@mskpp.autotune_v2(configs=[  
{'L1TileShape': 'GemmShape<128, 256, 256>', 'L0TileShape': 'GemmShape<128, 256, 64>}  
,{L1TileShape': 'GemmShape<256, 128, 256>', 'L0TileShape': 'GemmShape<256, 128, 64>}  
,{L1TileShape': 'GemmShape<128, 128, 256>', 'L0TileShape': 'GemmShape<128, 128, 64>}  
,{L1TileShape': 'GemmShape<128, 128, 512>', 'L0TileShape': 'GemmShape<128, 128, 64>}  
,{L1TileShape': 'GemmShape<64, 256, 128>', 'L0TileShape': 'GemmShape<64, 256, 64>}  
], warmup(times=10)  
def run_executable(m, n, k, device_id):  
    src_file = "/basic_matmul.cpp"  
    build_script = "/.jit_build_executable.sh" # executable compile script  
    executable = mskpp.compile_executable(build Script=build Script, src_file=src_file, use_cache=False)  
    return executable(m, n, k, device_id) 
```

# 3.5.4.5 compile_executable

# 功能说明

编译代码，返回一个可执行的executable对象。 

# 函数原型

```txt
executable = compile_executable(build_script, src_file) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>说明</td></tr><tr><td>build_script</td><td>输入</td><td>用于编译被调优应用的脚本文件路径。
数据类型: str。
必选参数。</td></tr><tr><td>src_file</td><td>输入</td><td>代码文件路径。
数据类型: str。
必选参数。</td></tr><tr><td>output_bin_path</td><td>输入</td><td>指定编译生成的可执行文件路径。
数据类型: str。
可选参数，默认值：_gen_executable。</td></tr><tr><td>use_cache</td><td>输入</td><td>开启后不执行编译，加载output_bin_path所指定的文件。
数据类型: bool。
可选参数，默认值：False。
说明
当使用msDebug工具拉起compile接口时，需配置
use_cache=True。</td></tr><tr><td>profiling_cm
d</td><td>输入</td><td>预留参数。</td></tr></table>

# 返回值说明

可执行程序对象executable，类型：CompiledExecutable，支持如下方式调用： executable(arg1, arg2, ...)，其中arg1、arg2、...是程序自定义入参。 

# 调用示例

executable $=$ compile_executable(build_script,src_file) executable(a,b,c) 

# 3.5.5 附录

# 3.5.5.1 basic_matmul_autotune.py

import numpy as np   
from types import Structure, c_uint32, c_int32, c_int64   
import mkpp   
def get_kernel(): kernel_file = "/basic_matmul.cpp" kernel_name = "BasicMatmul" buildScript $=$ "/jit_build.sh" # kernel compile script config $\equiv$ mskpp.KernellInvokeConfig(kernel_file, kernel_name) gen_file $\equiv$ mskpp.Launcher(config).code_gen() kernel $=$ mskpp.compile(build.script $\equiv$ build.script, launch_src_file $\equiv$ gen_file) return kernel   
To enable the autotune feature, it is required to add the "/ tunable" marker to the code lines in "basic_matmul.cpp", e.g. 51 using L1TileShape $\equiv$ GemmShape<128, 256, 256>; // tunable 52 using L0TileShape $\equiv$ GemmShape<128, 256, 64>; // tunable   
@mkpp.autotune(config= [ {L1TileShape': 'GemmShape<128, 256, 256>', 'L0TileShape': 'GemmShape<128, 256, 64>}, #0 the same config as in basic_matmul.cpp {L1TileShape': 'GemmShape<128, 256, 128>', 'L0TileShape': 'GemmShape<128, 256, 64>}, {L1TileShape': 'GemmShape<128, 128, 128>', 'L0TileShape': 'GemmShape<64, 128, 128>}, {L1TileShape': 'GemmShape<64, 128, 256>', 'L0TileShape': 'GemmShape<64, 128, 128>}, {L1TileShape': 'GemmShape<64, 128, 512>', 'L0TileShape': 'GemmShape<64, 128, 128>}, {L1TileShape': 'GemmShape<64, 64, 128>', 'L0TileShape': 'GemmShape<64, 64, 128>}, {L1TileShape': 'GemmShape<64, 64, 256>', 'L0TileShape': 'GemmShape<64, 64, 128>}, {L1TileShape': 'GemmShape<64, 64, 512>', 'L0TileShape': 'GemmShape<64, 64, 128>} , {L1TileShape': 'GemmShape<128, 128, 128>', 'L0TileShape': 'GemmShape<128, 128, 128>} , {L1TileShape': 'GemmShape<128, 128, 256>', 'L0TileShape': 'GemmShape<128, 128, 128>} , {L1TileShape': 'GemmShape<128, 128, 512>', 'L0TileShape': 'GemmShape<128, 128, 128>} ], warmup=1000,repeat=10 device_id=[1]) def basic_matmul解决问题_shape,a,No layout_a,b,No layout_b,c,No layout_c): # This function's input arguments must exactly match the kernel function. kernel $\equiv$ get_kernel( blockdim $= 20$ # use the correct aic number that matches your hardware return kernel[blockdim](problem_shape,a,No layout_a,b,No layout_b,c,No layout_c device_id=1) # invoke the kernel   
class GemmCoordSTRUCTure: _fields_ $=$ ["m",c_uint32), ("n",c_uint32), ("k",c_uint32)] def init_self,m,n,k): super)_init_(self.m $=$ (c_uint32)(m) 

```python
self.n = (c_uint32)(n)  
self.k = (c_uint32)(k)  
@staticmethod  
def get namespace():  
return "Catlass:"  
class RowMajor(Structure):  
    _fields_ = ["shape", c_int32 * 2), ("stride", c_int64 * 2)]  
def __init__(self, rows: int = 0, cols: int = 0, lcm: int = None):  
    super().__init()  
    self.shape = (c_int32 * 2)(rows, cols)  
    if lcm is None:  
        self=stride = (c_int64 * 2)(cols, 1)  
    else:  
        self=stride = (c_int64 * 2)((c_int64)(ldm), 1)  
@staticmethod  
def get namespace():  
    return "Catlass::layout:"  
if __name__ == "_main":  
    # prepare kernel input/output  
    m = 256  
    n = 512  
    k = 1024  
    problem_shape = GemCoord(m, n, k)  
    layout_a = RowMajor(m, k)  
    layout_b = RowMajor(k, n)  
    layout_c = RowMajor(m, n)  
    a = np.random.randint(1, 2, [m, k]).astype(np.full)  
    b = np.random.randint(1, 2, [k, n]).astype(np.full)  
    c = np.zeros([m, n]).astype(np.full)  
# invoke kernel  
basic_matmul/problem_shape, a, layout_a, b, layout_b, c, layout_c)  
# check if the output tensor c is consistent with the golden data golden = np/matmul(a, b)  
isequal = np.arrayequal(c, golden)  
result = "success" if isequal else "failed"  
print("compare {}.".format(result)) 
```

# 3.5.5.2 jit_build.sh

```shell
#!/bin/bash
# default input file
LAUNCH SRC_FILE="__gen_launch.cpp"
OUTPUT/lib_FILE="__genModule.so"
if [\$# -ge 1] ; then
    LAUNCH SRC_FILE=$1
fi
if [\$# -ge 2] ; then
    OUTPUT/lib_FILE=$2
fi
LAUNCH_OBJ_FILE="${LAUNCH SRC_FILE%.cpp}.o"
PYTHON_INCLUDE=$(python3 -c "import sysconfig; print(sysconfig.get_path('include'))")
cd "$(dirname "$0)"'
bisheng -O2 -fPIC -std=c++17 -xcce --cce-aicore-arch=dav-c220 \
-DL2_CACHE_HINT \
-mllvm -cce-aicore-stack-size=0x8000 \
-mllvm -cce-aicore-function-stack-size=0x8000 \
-mllvm -cce-aicore-record-overflow=true \
-mllvm -cce-aicore-addr-transform \
-mllvm -cce-aicore-dcci-insert-for-scalar=false \
-I$ASCEND_HOME_PATH/compiler/tikcpp \
-I$ASCEND_HOME_PATH/include/aclnn \
-I$ASCEND_HOME_PATH/compiler/tikcpp/tikcfw \
-I$ASCEND_HOME_PATH/compiler/tikcpp/tikcfw/impl \ 
```

```shell
-I$ASCEND_HOME_PATH/compiler/tikcpp/tikcfw/interface \
-I$ASCEND_HOME_PATH/include \
-I$ASCEND_HOME_PATH/include/experiment/runtime \
-I$ASCEND_HOME_PATH/include/experiment/msprof \
-I$PYTHON_INCLUDE \
-I/.././include \
-I/../common \
-Wno-macro redefine -Wno-ignored-attributes \
-L$ASCEND_HOME_PATH/lib64 \
-lruntime -lplatform -lstdc++ -lascendcl -lm -ltiling_api -lc_sec -ldl -lnnopbase \
$LAUNCH SRC_FILE --shared -o $OUTPUT_lib_FILE
exit $? 
```

# 3.5.5.3 basic_matmul_executable_autotune.py

import mkpp   
@mskpp.autotune_v2(configs $\coloneqq$ [   
{L1TileShape': 'GemmShape<128, 256, 256>', 'L0TileShape': 'GemmShape<128, 256, 64>}#, #0 the same config as in basic_matmul.cpp   
{L1TileShape': 'GemmShape<256, 128, 256>', 'L0TileShape': 'GemmShape<256, 128, 64>}.,   
{L1TileShape': 'GemmShape<128, 128, 256>', 'L0TileShape': 'GemmShape<128, 128, 64>}.,   
{L1TileShape': 'GemmShape<64, 256, 128>', 'L0TileShape': 'GemmShape<64, 256, 64>}.,   
{L1TileShape': 'GemmShape<64, 256, 256>', 'L0TileShape': 'GemmShape<64, 256, 64>}.,   
{L1TileShape': 'GemmShape<64, 128, 256>', 'L0TileShape': 'GemmShape<64, 128, 64>}.,   
{L1TileShape': 'GemmShape<128, 128, 256>', 'L0TileShape': 'GemmShape<128, 128, 128>}.,   
{L1TileShape': 'GemmShape<64, 128, 256>', 'L0TileShape': 'GemmShape<64, 128, 128>}.,   
{L1TileShape': 'GemmShape<64, 128, 512>', 'L0TileShape': 'GemmShape<128, 64, 128>}.,   
{L1TileShape': 'GemmShape<128, 64, 512>', 'L0TileShape': 'GemmShape<128, 64, 128>}.,   
{L1TileShape': 'GemmShape<64, 64, 256>', 'L0TileShape': 'GemmShape<64, 64, 256>}.,   
{L1TileShape': 'GemmShape<64, 64, 512>', 'L0TileShape': 'GemmShape<64, 64, 256>}.,   
{L1TileShape': 'GemmShape<64, 64, 1024>', 'L0TileShape': 'GemmShape<64, 64, 256>}.,   
],warmup(times=10)   
def run_executable(m,n,k,device_id): kernel_file $=$ "...//00basic_matmul/basic_matmul.cpp" build Script $=$ "jit_build.sh" # executable compile script executable $=$ mskpp.compile_executable(build.script $\equiv$ build.Script,src_file $\equiv$ kernel_file,use_cache $\equiv$ False) return executable(m,n,k,device_id)   
if_name $= =$ "_main_: m = 256 n = 512 k = 1024 device_id = 0 run_executable(m,n,k,device_id) 

# 3.5.5.4 jit_build_executable.sh

```shell
#!/bin/sh
# default input file
LAUNCH SRC_FILE="__gen_launch.cpp"
# OUTPUTLIB_FILE="__genModule.so"
OUTPUTLIB_FILE="__gen_executable"
if[\# -ge 1] ; then
LAUNCH_SRC_FILE=\(1
fi
if[\)# -ge 2] ; then
OUTPUTLIB_FILE=\)2
fi
LAUNCH_OBJ_FILE="${LAUNCH_SRC_FILE%.cpp}.o"
PYTHON_INCLUDE=$(python3 -c "import sysconfig; print(sysconfig.get_path('include'))")
cd "${(dirname "$0")"
bisheng -O2 -std=c++17 -xcce --cce-aicore-arch=dav-c220 \
-mllvm -cce-aicore-stack-size=0x8000 \
-mllvm -cce-aicore-function-stack-size=0x8000 \
-mllvm -cce-aicore-record-overflow=true \
-mllvm -cce-aicore-addr-transform \
-mllvm -cce-aicore-dcci-insert-for-scalar=false \
-DL2_CACHE_HINT \ 
```

```shell
-1$ASCEND_HOME_PATH/compiler/tikcpp \
-1$ASCEND_HOME_PATH/compiler/tikcpp/tikcfw \
-1$ASCEND_HOME_PATH/compiler/tikcpp/tikcfw/impl \
-1$ASCEND_HOME_PATH/compiler/tikcpp/tikcfw/interface \
-1$ASCEND_HOME_PATH/include \
-1$ASCEND_HOME_PATH/include/experiment/runtime \
-1$ASCEND_HOME_PATH/include/experiment/msprof \
-1/.././include \
-1/../common \
-L$\{ASCEND_HOME_PATH\}/lib64 \
-Wno-macro redefine -Wno-ignored-attributes \
-lruntime -lstdc++ -lascendcl -lm -ltiling_api -lplatform -lc_sec -ldl -lnnopbase \
$LAUNCH SRC_FILE -o $OUTPUT.Lib_FILE
exit $? 
```