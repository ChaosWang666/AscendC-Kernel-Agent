<!-- Source: 算子开发工具.md lines 2883-3065 | Section: 3.4 调用 msOpGen 算子工程 -->

# 3.4 调用 msOpGen 算子工程

# 3.4.1 功能介绍

当前，部分算子开源仓中，采用了msOpGen提供的工程模板。然而，基于此模板进行 算子调用较为复杂，且难以实现算子的轻量化调测。为了解决此类问题，我们可以利 用msKPP工具提供的3.4.3.1 mskpp.tiling_func和3.4.3.2 mskpp.get_kernel_from_binary接口，直接调用msOpGen工程中的tiling函数以及用 户自定义的Kernel函数。 

# 说明

● 使用本功能时，算子输入输出仅支持numpy.Tensor、torch.Tensor。 

● 若CANN中曾经部署过相同类型的算子（op_type），用户修改了tiling函数并重新编译，则 需要在CANN环境中重新部署该算子。 

# 3.4.2 调用示例

本章节以matmulleakyrelu算子工程为例，介绍如何利用msKPP工具提供的3.4.3.1 mskpp.tiling_func和3.4.3.2 mskpp.get_kernel_from_binary接口调用msOpGen工 程中的tiling函数以及用户自定义的Kernel函数，其他类型的算子操作均可参考此流程 进行操作。 

# 环境准备

请参考2 环境准备，完成相关环境变量的配置。 

单击Link获取样例工程，为进行算子检测做准备。 

# 说明

● 本样例工程以Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组件 为例。 

下载代码样例时，需执行以下命令指定分支版本。 git clone https://gitee.com/ascend/samples.git -b v1.5-8.2. 

# 具体操作

```txt
步骤1 参见环境准备中的样例工程，运行${gitClone_path}/operator/ascendc/0_introduction/12_matmulleakyrelu_frameworklaunch目录下的install.sh脚本，生成自定义算子工程，并进行Host侧和Kernel侧的算子实现。bash install.sh -v Ascendxxxxy # xxxv为用户实际使用的具体芯片类型 
```

```txt
步骤2 切换至自定义算子工程目录。  
cd CustomOp 
```

```txt
步骤3 编辑算子拉起脚本matmulleakyrelu.py。 
```

import numpy as np   
import sklearnpp   
#这个函数的入参必须和Kernel函数的入参一致   
def run_kernel(input_a, input_b, input.bias, output, workspace, tiling_data): kernel_binary_file $\equiv$ "MatmullLeakyreluCustom.o" #不同的硬件和操作系统展示的.o文件的名称稍有不同， 具体路径请参考表4-8中的-reloc参数 kernel $=$ mskpp.get_kernel_from_binary(kernel_binary_file,'mix') return kernel(input_a, input_b, input.bias, output, workspace, tiling_data)   
if_name $= =$ ""_main_: #input/output tensor M $= 1024$ N $= 640$ K $= 256$ 

```python
input_a = np.random.randint(1, 10, [M, K]).astype(np.float16)  
input_b = np.random.randint(1, 10, [K, N]).astype(np.float16)  
input.bias = np.random.randint(1, 10, [N]).astype(np.float32)  
output = np.zeros([M, N]).astype(np.float32)  
# shape info  
inputs_info = ["shape": [M, K], "dtype": "float16", "format": "ND"], {"shape": [K, N], "dtype": "float16", "format": "ND"], {"shape": [N], "dtype": "float32", "format": "ND"]}  
outputs_info = ["shape": [M, N], "dtype": "float32", "format": "ND"]}  
attr = {}  
# 调用tiling函数  
tiling_output = mskpp.tiling_func(op_type="MatmulLeakyreluCustom", inputs_info=inputs_info, outputs_info=outputs_info, # 可选 inputs=[input_a, input_b, input.bias], outputs=[output], attr=attr, # 可选 lib_path="libopttiling.so", # tiling代码编译产物，具体位置可参考步骤2中的目录结构 # soc_version=True, # 可选)  
blockdim = tiling_output.blockdim  
workspace_size = tiling_output workspace_size  
tiling_data = tiling_output.tiling_data # numpy数组  
workspace = np.zeros Workspace_size).astype(np uint8) # workspace需要用户自行申请 # 调用Kernel函数 run_kernel(input_a, input_b, input.bias, output, workspace, tiling_data)  
# 校验输出 alpha = 0.001  
golden = (np.matmul(input_a.astype(np.float32), input_b.astype(np.float32)) + input.bias).astype(np.float32)  
golden = np.where(golden >= 0, golden, golden * alpha)  
isequal = np.arrayequal(output, golden)  
result = "success" if isequal else "failed"  
print("compare {}.".format(result)) 
```

步骤4 运行脚本。 

```txt
python3matmulleakyrelu.py 
```

----结束 

# 3.4.3 接口列表

# 3.4.3.1 mskpp.tiling_func

# 功能说明

调用用户的tiling函数。目前仅该接口的部分参数支持输入list[tensor]，调用3.4.3.2 mskpp.get_kernel_from_binary返回的CompiledKernel不支持传入list[tensor]。 

# 说明

调用tiling_func函数时，会在当前目录生成_mskpp_gen_tiling.cpp和_mskpp_gen_tiling.so文 件，该文件仅用于开发问题定位，用户无需关注。 

# 函数原型

```python
def tiling_func(op_type: str, inputs: list, outputs: list, lib_path: str, inputs_info: list = None, outputs_info: list = None, attr=None, soc_version: str = None) -> TilingOutput 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>说明</td></tr><tr><td>op_type</td><td>输入</td><td>需根据tiling函数的实现填写，例如AddCustom、MatmulLeakyreliCustom等。msKPP工具查找tiling函数的唯一依据，查找逻辑请参见lib_path参数。数据类型：str。必选参数。说明若CANN中曾经部署过相同类型的算子（op_type），用户修改了tiling函数并重新编译，则需要在CANN环境中重新部署该算子。</td></tr><tr><td>inputs</td><td>输入</td><td>按Kernel函数入参顺序填入tensor信息，不使用某个参数的情况，对应位置请传入None占位。数据类型为list，每个元素必须是tensor或者list[tensor]，不在inputs_info中显式指定format或者ori_format时，所有tensor默认为ND格式。必选参数。</td></tr><tr><td>outputs</td><td>输入</td><td>按Kernel函数入参顺序填入tensor信息，不使用某个参数的情况，对应位置请传入None占位。数据类型：list，每个元素必须是tensor或者list[tensor]，不在inputs_info中显式指定format或者ori_format时，所有tensor默认为ND格式必选参数。</td></tr><tr><td>inputs_info</td><td>输入</td><td>按Kernel函数入参顺序填写info信息，不使用某个参数的情况，对应位置请传入空dict或者None占位。数据类型为list，inputs_info参数中元素的数据类型为dict或list[dict]，每个dict的元素说明如下：·ori_shape：输入tensor的原始维度信息。·shape：输入tensor运行时的维度信息。·dtype：输入tensor的数据类型。·ori_format：输入tensor的原始数据排布格式，默认为ND·format：输入tensor的数据排布格式，默认为ND。·data_path：值依赖场景下，输入tensor的bin文件路径。举例如下：{{{"ori_shape": [8, 2048], "shape": [8, 2048], "dtype": "float16", "ori_format": "ND", "format": "ND", {"ori_shape": [8, 2048], "shape": [8, 2048], "dtype": "float16", "ori_format": "ND", "format": "ND"}]可选参数。说明该输入参数和inputs存在约束关系：·inputs为tensor时，inputs_info必须是dict。·inputs为list[tensor]时，inputs_info必须是list[dict]。·inputs为None时，inputs_info必须是空dict或者None。</td></tr><tr><td>outputs_info</td><td>输入</td><td>存放输出的信息，不使用某个参数的情况，对应位置请传入空dict占位。数据类型为list，outputs_info参数中元素的数据类型为dict或list[dict]，每个dict的元素说明如下：· ori_shape: 输出tensor的原始维度信息。· shape: 输出Tensor的维度信息。· dtype: 输出Tensor的数据类型。· ori_format: 输出Tensor的原始数据排布格式，默认为ND· format: 输出Tensor的数据排布格式，默认为ND。· data_path: 保留参数，不生效。举例如下：{{{shape": [8, 2048], "dtype": "float16", "format": "ND"], {"shape": [8, 2048], "dtype": "float16", "format": "ND"]}可选参数。说明该输入参数和inputs存在约束关系：· outputs为tensor时，outputs_info必须是dict。· outputs为list[tensor]时，outputs_info必须是list[dict]。· outputs为None时，outputs_info必须是空dict或者None。</td></tr><tr><td>attr</td><td>输入</td><td>tiling函数使用到的算子属性。数据类型:dict或者list。说明·dict格式键值只能包含大小写英文字母、数字、下划线。{ "a1":1, "a2":False, "a3":"sss", "a4":1.2, "a5":[111,222,333], "a6":[111.111,111.222,111.333], "a7":[True,False], "a8":[ "asdf", "zxcv"], "a9":[[1,2,3,4],[5,6,7,8],[5646,2345]],} ·list格式,推荐使用。若某个attr需要传空列表时,必须用这种格式(例如下面的"a10")。·"name"和"value"的值只能包含大小写英文字母、数字、下划线。·"dtype":输入tensor的数据类型。[ {"name":"a1","dtype":"int","value":1}, {"name":"a2","dtype":"bool","value":False}, {"name":"a3","dtype":"str","value":"sss"}, {"name":"a4","dtype":"float","value":1.2}, {"name":"a5","dtype":"list_float","value":[111.111,111.222,111.333]}, {"name":"a6","dtype":"list bool","value":[True,False]}, {"name":"a7","dtype":"list_str","value":"asdf","zxcv"]} {"name":"a8","dtype":"list_list_int","value":[1,2,3,4],[5,6,7,8],[5646,2345]]}, {"name":"a9","dtype":"list_int","value":[111,222,333]}, {"name":"a10","dtype":"list_int","value":[]}, {"name":"a11","dtype":"int64","value":2}, {"name":"a12","dtype":"float32","value":1.3},] 可选参数。</td></tr><tr><td>lib_path</td><td>输入</td><td>msOpGen工程编译生成的liboptiling.so文件的路径,可在工程目录下通过find . -name 'liboptiling.so'进行查找。msKPP工具会按已部署算子、.so文件的查找顺序获取用户tiling函数。数据类型:str。可选参数。</td></tr><tr><td>soc_version</td><td>输入</td><td>配置为昇腾AI处理器的类型。可选参数。说明·非Atlas A3 训练系列产品/Atlas A3 推理系列产品：在安装昇腾AI处理器的服务器执行npu-smi info命令进行查询，获取Chip Name信息。实际配置值为AscendChip Name，例如Chip Name取值为xxxx，实际配置值为Ascendxxxx。当Ascendxxxx为代码样例的路径时，需要配置为ascendxxxx。·Atlas A3 训练系列产品/Atlas A3 推理系列产品：在安装昇腾AI处理器的服务器执行npu-smi info -t board -i id -c chip_id命令进行查询，获取Chip Name和NPU Name信息，实际配置值为Chip Name_NPU Name。例如Chip Name取值为Ascendxxx，NPU Name取值为1234，实际配置值为Ascendxxx_1234。当Ascendxxx_1234为代码样例的路径时，需要配置为ascendxxx_1234。其中：·id：设备id，通过npu-smi info -l命令查出的NPU ID即为设备id。·chip_id：芯片id，通过npu-smi info -m命令查出的Chip ID即为芯片id。</td></tr></table>

# 返回值说明

<table><tr><td>参数名</td><td>说明</td></tr><tr><td>blockdim</td><td>用户tiling函数配置的核数。数据类型: int。</td></tr><tr><td>workspace_size</td><td>用户申请的workspace大小。若用户未设置,msKPP工具默认配置为8。数据类型:int。</td></tr><tr><td>tiling_data</td><td>存放tiling_data,用于调用Kernel函数。数据类型: numpy.array。</td></tr><tr><td>tiling_key</td><td>用户tiling函数配置的tiling_key,若用户未设置,msKPP工具会默认设置为0。数据类型:int。</td></tr></table>

# 调用示例

```python
M = 1024  
N = 640  
K = 256  
input_a = np.random.randint(1, 10, [M, K]).dtype(np.float16)  
input_b = np.random.randint(1, 10, [K, N]).dtype(np.float16)  
input.bias = np.random.randint(1, 10, [N]).dtype(np.float32)  
output = np.zeros([M, N]).dtype(np.float32)  
# tiling data 
```

```python
tiling_output = sklearn.pp.tiling_func(  
op_type="MatmulLeakyreluCustom",  
inputs=[input_a, input_b, input.bias], outputs=[output],  
lib_path="liboptiling.so", # tiling代码编译产物 
```

# 3.4.3.2 mskpp.get_kernel_from_binary

# 功能说明

生成一个可以调用用户Kernel函数的实例。 

# 说明

● 需要保证调用get_kernel_from_binary的函数的入参和调用Kernel时的入参一致。 

● 调用get_kernel_from_binary函数时，会在当前目录生成_mskpp_gen_binary_launch.cpp和 _mskpp_gen_binary_module.so文件，该文件仅用于开发问题定位，用户无需关注。 

# 函数原型

```python
def get_kernel_from_binary(kernel_binary_file: str, kernel_type: str = None, tiling_key: int = None) ->  
CompiledKernel 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>说明</td></tr><tr><td>kernel_binarv_file</td><td>输入</td><td>算子kernel.o路径，可以在工程目录下执行find . -name*.o&#x27;命令进行查找。数据类型：str。必选参数。</td></tr><tr><td>kernel_type</td><td>输入</td><td>算子类型。可设置为vec、cube或mix。若不配置该参数，msKPP工具可能会获取失败。因此，建议手动赋值。数据类型：str。可选参数。</td></tr><tr><td>tiling_key</td><td>输入</td><td>调用用户Kernel函数时使用的tiling_key。若不配置该参数，msKPP工具将会使用最近一次调用3.4.3.1mskpp.tiling_func的结果。数据类型：int。可选参数。</td></tr></table>

# 返回值说明

可运行的Kernel对象。 


表 3-5 Kernel 入参介绍


<table><tr><td>参数名</td><td>输入/输出</td><td>说明</td></tr><tr><td>device_id</td><td>输入</td><td>NPU设备ID，设置运行ST测试用例的昇腾AI处理器的ID。数据类型：int。若未设置此参数，默认为0。</td></tr><tr><td>timeout</td><td>输入</td><td>camodel仿真场景需要默认设置较长超时时间，设置为-1时表示不限制。数据类型：int。单位：ms，默认值为300000。</td></tr><tr><td>repeat</td><td>输入</td><td>重复运行次数，默认值为1。数据类型：int。</td></tr><tr><td>stream</td><td>输入</td><td>预留参数。</td></tr><tr><td>kernel_name</td><td>输入</td><td>预留参数。</td></tr></table>

# 说明

Kernel对象类型为CompiledKernel，支持如下方式调用kernel：kernel[blockdim](arg1, arg2, ..., timeout=-1, device_id=0, repeat=1)。 

# 调用示例

示例一： 

```python
def run_kernel(input_a, input_b, input.bias, output, workspace, tiling_data):
    kernel_binary_file = "MatmulLeakyreluCustom.o" #不同的硬件和操作系统展示的.o文件的名称稍有不同
    kernel = mskpp.get_kernel_from_binary(kernel_binary_file)]
    return kernel(input_a, input_b, input.bias, output, workspace, tiling_data) 
```

示例二： 

```python
def run_kernel(input_a, input_b, input.bias, output, workspace, tiling_data, tiling_key, blockdim):
    kernel_binary_file = "MatmulLeakyreluCustom.o"  #不同的硬件和操作系统展示的.o文件的名称稍有不同
    kernel = mkpp.get_kernel_from_binary(kernel_binary_file, kernel_type='mix', tiling_key='tiling_key')
    return kernel[blockdim](input_a, input_b, input.bias, output, workspace, tiling_data, device_id=1, timeout=-1) #运行仿真时，需要手动将timeout参数设置为-1 
```