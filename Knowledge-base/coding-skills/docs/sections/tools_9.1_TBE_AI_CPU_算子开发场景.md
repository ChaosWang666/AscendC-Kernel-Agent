<!-- Source: 算子开发工具.md lines 10160-11528 | Section: 9.1 TBE&AI CPU 算子开发场景 -->

# 9.1 TBE&AI CPU 算子开发场景

# 9.1.1 基于 msOpGen 工具创建算子工程

# 功能描述

CANN开发套件包中提供了自定义算子工程生成工具msOpGen，可基于算子原型定义 输出算子开发相关交付件，包括算子代码实现文件、算子适配插件、算子原型定义、 算子信息库定义以及工程编译配置文件。 

# 须知

若开发者需要自定义多个AI CPU算子，需要在同一算子工程中进行实现，并将所有自 定义算子在同一工程中同时进行编译，将所有AI CPU自定义算子的实现文件编译成一 个动态库文件。 

# 使用前提

CANN组合包提供进程级环境变量设置脚本，供用户在进程中引用，以自动完成 环境变量设置。执行命令参考如下，以下示例均为root或非root用户默认安装路 径，请以实际安装路径为准。 

```shell
# 以root用户安装 toolkit包后配置环境变量
source /usr/local/Ascend/ascend-toolkit/set_env.sh
# 以非root用户安装 toolkit包后配置环境变量
source ${HOME}/Ascend/ascend-toolkit/set_env.sh 
```

安装依赖： 如下命令如果使用非root用户安装，需要在安装命令后加上--user。 pip3 install xlrd==1.2.0 

# 使用方法

步骤1 确认需要的输入文件。 

自定义算子工程生成工具支持输入三种类型的原型定义文件创建算子工程，分别为： 

适配昇腾AI处理器算子IR定义文件（.json） 

TensorFlow的原型定义文件（.txt） 

TensorFlow的原型定义文件可用于生成TensorFlow、Caffe、PyTorch框架的算子 工程。 

适配昇腾AI处理器算子IR定义文件（.xlsx） 

步骤2 请用户选择一种文件完成输入文件的准备工作。 

适配昇腾AI处理器算子IR定义的json文件的准备工作 

用户可从CANN软件安装后文件存储路径下的“python/site-packages/op_gen/ json_template”中获取模板文件IR_json.json，并进行修改，其文件参数配置说明 请参见表9-1。 


表 9-1 json 文件配置参数说明


<table><tr><td colspan="2">配置字段</td><td>类型</td><td>含义</td><td>是否必选</td></tr><tr><td>op</td><td>-</td><td>字符串</td><td>算子的Operator Type。</td><td>是</td></tr><tr><td rowspan="4">input_de sc</td><td>-</td><td>列表</td><td>输入参数描述。</td><td rowspan="4">否</td></tr><tr><td>name</td><td>字符串</td><td>算子输入参数的名称。</td></tr><tr><td>param_type</td><td>字符串</td><td>参数类型: - required - optional - dynamic 未配置默认为required。</td></tr><tr><td>format</td><td>列表</td><td>针对类型为Tensor的参数,配置为 Tensor支持的数据排布格式,具体请参考“概念原理和术语 &gt; 数据排布格式”《Ascend C算子开发指南》的 “附录 &gt; Tensor基础知识参考 &gt; 数据排布格式”章节。 包含如下取值: ND,NHWC,NCHW,HWCN,NC1HWC0,FRACTAL_Z等。 format与type的数量需保持一致。</td></tr><tr><td></td><td>type</td><td>列表</td><td>算子参数的类型。取值范围: float16 (fp16), float32 (fp32), int8, int16, int32, uint8, uint16, bffloat16 (bf16), bool等。说明不同计算操作支持的数据类型不同,详细请参见《TBE&amp;AI CPU算子开发接口》。format与type的数量需保持一致。</td><td></td></tr><tr><td rowspan="5">output_d esc</td><td>-</td><td>列表</td><td>输出参数描述。</td><td rowspan="5">是</td></tr><tr><td>name</td><td>字符串</td><td>算子输出参数的名称。</td></tr><tr><td>param_type</td><td>字符串</td><td>参数类型:- required- optional- dynamic未配置默认为required。</td></tr><tr><td>format</td><td>列表</td><td>针对类型为Tensor的参数,配置为Tensor支持的数据排布格式,具体请参考《Ascend C算子开发指南》的“附录 &gt; Tensor基础知识参考 &gt; 数据排布格式”章节。包含如下取值:ND,NHWC,NCHW,HWCN,NC1HWC0,FRACTAL_Z等。format与type的数量需保持一致。</td></tr><tr><td>type</td><td>列表</td><td>算子参数的类型。取值范围: float16 (fp16), float32 (fp32), int8, int16, int32, uint8, uint16, bffloat16 (bf16), bool等。说明不同计算操作支持的数据类型不同,详细请参见《TBE&amp;AI CPU算子开发接口》。format与type的数量需保持一致。</td></tr><tr><td rowspan="2">attr</td><td>-</td><td>列表</td><td>属性描述。</td><td rowspan="2">否</td></tr><tr><td>name</td><td>字符串</td><td>算子属性参数的名称。</td></tr><tr><td rowspan="3"></td><td>param_type</td><td>字符串</td><td>参数类型:- required- optional未配置默认为required。</td><td rowspan="3"></td></tr><tr><td>type</td><td>字符串</td><td>算子参数的类型。包含如下取值:int、bool、float、string、list_int、list_float等。</td></tr><tr><td>default_value</td><td>-</td><td>默认值</td></tr></table>

# 说明

– json文件可以配置多个算子，json文件为列表，列表中每一个元素为一个算子。 

– 若input_desc或output_desc中的name参数相同，则后一个会覆盖前一参数。 

input_desc，output_desc中的type需按顺序一一对应匹配，format也需按顺序一一对 应匹配。 

例如，第一个输入x的type配置为[“int8”,“int32”]，第二个输入y的type配置为 [“fp16”,“fp32”]，输出z的type配置为[“int32”,“int64”]，最终这个算子支持 输入(“int8”,“fp16”)生成int32，或者(“int32”,“fp32”)生成int64，即输入和输 出的type是垂直对应的，类型不能交叉。 

input_desc，output_desc中的type与format需一一对应匹配，数量保持一致。type的 数据类型为以下取值（"numbertype"、"realnumbertype"、"quantizedtype"、 "BasicType"、"IndexNumberType"、"all"）时，需识别实际的type数量是否与format 数量保持一致，若数量不一致，创建工程会收到报错提示，同时format按照type的个数 进行补齐，继续生成算子工程。若type的取值为基本数据类型（如：“int32”），且 与format无法一一对应时，创建工程会收到报错提示，并停止运行。 

TensorFlow的原型定义文件（.txt）的准备工作 

TensorFlow的原型定义文件（.txt）中内容可从TensorFlow开源社区获取，例 如，Add算子的原型定义在TensorFlow开源社区中/tensorflow/core/ops/ math_ops.cc文件中，在文件中搜索“Add”找到Add对应的原型定义，内容如下 所示： 

```txt
REGISTER_OP("Add")  
. Input("x: T")  
. Input("y: T")  
. Output("z: T")  
. Attr(  
  "T: {half, float, int32}")  
. SetShapeFn(shape_inference::BroadcastBinaryOpShapeFn); 
```

将以上内容另存为**.txt文件。 

# 注意

每个**.txt文件仅能包含一个算子的原型定义。 

自定义算子工程生成工具只解析算子类型、Input、Output、Attr中内容，其他内 容可以不保存在**.txt中。 

适配昇腾AI处理器算子IR定义的Excel文件准备工作 

用户可从CANN软件安装后文件存储路径下的“toolkit/tools/msopgen/ template”目录下获取模板文件Ascend_IR_Template.xlsx进行修改。请基于 “Op”页签进行修改，“Op”页签可以定义多个算子，每个算子都包含如下参 数： 


表 9-2 IR 原型定义参数说明


<table><tr><td>列名称</td><td>含义</td><td>是否必选</td></tr><tr><td>Op</td><td>算子的Operator Type。</td><td>是</td></tr><tr><td>Classify</td><td>算子相关参数的类别，包含：-输入：Input-动态输入：DYNAMIC_INPUT-输出：Output-动态输出：DYNAMIC_OUTPUT-属性：Attr</td><td>是</td></tr><tr><td>Name</td><td>算子参数的名称。</td><td>是</td></tr><tr><td>Type</td><td>算子参数的类型。包含如下取值：tensor、int、bool、float、ListInt、ListFloat等。</td><td>是</td></tr><tr><td>TypeRange</td><td>针对类型为Tensor的参数，需要配置Tensor支持的类型。包含如下取值：fp16,fp32,double,int8,int16,int32,int64,ui nt8,uint16,uint32,uint64,bf16,bool等。框架为MindSpore时，需要将Tensor的类型值转换为MindSpore所支持的值：I8 默认,I16 默认,I32 默认,I64_D default,U8 默认,U16 默认,U32 默认,U64 默认,B0UL 默认等。</td><td>否</td></tr><tr><td>Required</td><td>是否必须输入，有如下取值：-TRUE-FALSE</td><td>是</td></tr><tr><td>Doc</td><td>对应参数的描述。</td><td>否</td></tr><tr><td>Attr，默认_value</td><td>属性的默认值。</td><td>否</td></tr><tr><td>Format</td><td>针对类型为Tensor的参数，配置为Tensor支持的数据排布格式。
包含如下取值：
ND,NHWC,NCHW,HWCN,NC1HWC0,FRACTAL_Z等。</td><td>否</td></tr><tr><td>Group</td><td>算子分类。</td><td>否</td></tr></table>

配置示例如下所示： 


表 9-3 IR 原型定义表示例


<table><tr><td colspan="9">预留行</td></tr><tr><td>Op</td><td>Classif y</td><td>Name</td><td>Type</td><td>TypeRange</td><td>Required</td><td>Doc</td><td>Attr_ Default_value</td><td>For ma t</td></tr><tr><td rowspan="5">Resha pe</td><td>INPUT</td><td>x</td><td>tensor</td><td>fp16,fp32,double, int8,int16,int32,in t64,uint8,.uint16,u int32,.uint64,bf16, bool</td><td>TRU E</td><td>-</td><td>-</td><td>ND</td></tr><tr><td>INPUT</td><td>shape</td><td>tensor</td><td>int32,int64</td><td>FAL SE</td><td>-</td><td>-</td><td>-</td></tr><tr><td>DYNAMIC_O U TPUT</td><td>y</td><td>tensor</td><td>fp16,fp32,double, int8,int16,int32,in t64,uint8,.uint16,u int32,.uint64,bf16, bool</td><td>FAL SE</td><td>-</td><td>-</td><td>ND</td></tr><tr><td>ATTR</td><td>axis</td><td>int</td><td>-</td><td>FAL SE</td><td>-</td><td>0</td><td>-</td></tr><tr><td>ATTR</td><td>num _axes</td><td>int</td><td>-</td><td>FAL SE</td><td>-</td><td>-1</td><td>-</td></tr><tr><td>Resha peD</td><td>INPUT</td><td>x</td><td>tensor</td><td>fp16,fp32,double, int8,int16,int32,in t64,.uint8,.uint16,u int32,.uint64,bf16, bool</td><td>TRU E</td><td>-</td><td>-</td><td>ND</td></tr><tr><td rowspan="4"></td><td>OUTPUT</td><td>y</td><td>tensor</td><td>fp16,fp32,double,int8,int16,int32,int64,uint8,float16,uint32,float64,bf16, bool</td><td>TRUE</td><td>-</td><td>-</td><td>ND</td></tr><tr><td>ATTR</td><td>shape</td><td>list_int</td><td>-</td><td>FALSE</td><td>-</td><td>{}</td><td>-</td></tr><tr><td>ATTR</td><td>axis</td><td>int</td><td>-</td><td>FALSE</td><td>-</td><td>0</td><td>-</td></tr><tr><td>ATTR</td><td>num_axes</td><td>int</td><td>-</td><td>FALSE</td><td>-</td><td>-1</td><td>-</td></tr></table>

# 说明

– 请直接基于模板文件的第一个页签“Op”进行修改，实现算子的原型定义输入文件。 

– 请不要删除“Op”页签的前三行以及列。 

# 步骤3 创建算子工程。

执行如下命令，参数说明请参见表9-4。 

msopgen gen -i {operator define file} -f {framework type} -c {Compute Resource} -out {Output Path} 


表 9-4 参数说明


<table><tr><td>参数名称</td><td>参数描述</td><td>是否必选</td></tr><tr><td>gen</td><td>用于生成算子开发交付件。</td><td>是</td></tr><tr><td>-i,--input</td><td>算子定义文件路径，可配置为绝对路径或者相对路径。工具执行用户需要有此路径的可读权限。算子定义文件支持如下三种类型：·适配昇腾AI处理器算子IR定义文件 (.json)·TensorFlow的原型定义文件 (.txt)·适配昇腾AI处理器算子IR定义文件 (.xlsx)</td><td>是</td></tr><tr><td>-f,--framework</td><td>框架类型。·TensorFlow框架,参数值:tf或者tensorflow·Caffe框架,参数值:caffe·PyTorch框架,参数值:pytorch·MindSpore框架,参数值:ms或者mindspore·ONNX框架,参数值:onnx说明所有参数值大小写不敏感。</td><td>否</td></tr><tr><td>-c,--compute_unit</td><td>算子使用的计算资源。·针对TBE算子,配置格式为:ai_core-{Soc Version},ai_core与{Soc Version}之间用中划线“-”连接。{Soc Version}的取值请根据实际昇腾AI处理器版本进行选择。说明{Soc Version}请通过如下方式获取:-非Atlas A3训练系列产品/Atlas A3推理系列产品:在安装昇腾AI处理器的服务器执行npu-sminfo命令进行查询,获取Name信息。实际配置值为AscendName,例如Name取值为xxxxy,实际配置值为Ascendxxxxy。-Atlas A3训练系列产品/Atlas A3推理系列产品:在安装昇腾AI处理器的服务器执行npu-sminfo-t board -i id-c chip_id命令进行查询,获取Chip Name和NPU Name信息,实际配置值为Chip Name_NPU Name。例如Chip Name取值为Ascendxxx,NPU Name取值为1234,实际配置值为Ascendxxx_1234。其中:■id:设备id,通过npu-sminfo-l命令查出的NPU ID即为设备id。■chip_id:芯片id,通过npu-sminfo-m命令查出的Chip ID即为芯片id。基于同系列的AI处理器型号创建的算子工程,其基础功能(基于该工程进行算子开发、编译和部署)通用。·针对AI CPU算子,请配置为:aicpu。说明针对Atlas A3训练系列产品/Atlas A3推理系列产品,不支持增加如下编译选项:- -march=armv8-a+lse- -march=armv8.1-a- -march=armv8.2-a- -march=armv8.3-a</td><td>是</td></tr><tr><td>-out,--output</td><td>生成文件所在路径,可配置为绝对路径或者相对路径,并且工具执行用户具有可读写权限。若不配置,则默认生成在执行命令的当前路径。</td><td>否</td></tr><tr><td>-m, --mode</td><td>生成交付件模式。·0:创建新的算子工程,若指定的路径下已存在算子工程,则会报错退出。·1:在已有的算子工程中追加算子。默认值:0。</td><td>否</td></tr><tr><td>-op, --operator</td><td>此参数针对-i为算子IR定义文件的场景。配置算子的类型,如:Conv2DTik。若不配置此参数,当IR定义文件中存在多个算子时,工具会提示用户选择算子。</td><td>否</td></tr><tr><td>-lan, --language</td><td>算子编码语言。·py:基于DSL和TIK算子编程框架,使用Python编程语言进行开发。默认值:py。</td><td>否</td></tr><tr><td>-h, --help</td><td>输出帮助信息。</td><td>否</td></tr></table>

示例： 

使用IR_json.json模板作为输入创建原始框架为TensorFlow的算子工程。 

# 1. 创建算子工程。

TBE算子执行如下命令： msopgen gen -i json path/IR_json.json -f tf -c ai_core-{Soc Version} -out ./output data 

AI CPU算子执行如下命令： 

msopgen gen -i json path/IR_json.json -f tf -c aicpu -out ./output data 

-i参数请修改为IR_json.json文件的实际路径。例如："${INSTALL_DIR}/ python/site-packages/op_gen/json_template/IR_json.json"。 

– TBE算子工程的-c参数中{Soc Version}为昇腾AI处理器的型号。 

# 2. 选择算子（可选）：

若输入IR_json.json文件只有一个算子原型定义或使用-op参数指定算子类型 请跳过此步骤。 

若输入IR_json.json文件中包含多个原型定义，且没有使用-op参数指定算子 类型工具会提示输入选择的算子序号，选择算子。 

工具会提示输入选择的算子序号，输入：1。 

There is more than one operator in the .json file: 

1 O 1 

2 Op 2 

Input the number of the op: 1 

当命令行提示：Generation completed，则完成Op 1算子工程的创建。 Op_1为文件中"op"的值。 

# 3. 查看算子工程目录：

TBE算子工程目录生成在-out所指定的目录下：/output data 目录结构如 下所示： 

![](images/d45ec0db1fd9326bd0af50efda4ff23c78c2baff413f9df3fd33c2b20bcb7fde.jpg)


AI CPU算子工程目录生成在-out所指定的目录下：./output data， 目录结构 如下所示： 

![](images/016a34b39f357f132cdd80707507ce0cf060a49c408d5d014b92cf3c9ee55caa.jpg)


步骤4 可选: 在算子工程中追加算子。 

若需要在已存在的算子工程目录下追加其他自定义算子，命令行需配置“-m 1”参 数。 

执行如下命令。 

TBE算子命令示例： 

msopgen gen -i json path/**.json -f tf -c ai_core-{Soc Version} -out ./output data -m 1 

AI CPU算子命令示例： 

msopgen gen -i json path/**.json -f tf -c aicpu -out ./output data -m 1 

-i参数请修改为IR_json.json文件的实际路径。例如："${INSTALL_DIR}/python/ site-packages/op_gen/json_template/IR_json.json"。 

TBE算子工程的-c参数中{Soc Version}为昇腾AI处理器的型号。 

在算子工程目录下追加**.json中的算子。MindSpore AICPU算子工程不能够添加非 MindSpore框架的算子，也不能添加MindSpore TBE的算子。 

----结束 

# 补充说明

msOpGen工具其他参数说明可参考表9-5。 


表 9-5 参数说明


<table><tr><td>参数名称</td><td>参数描述</td><td>说明</td></tr><tr><td>mi</td><td>仅供MindStudio侧使用。</td><td rowspan="2">机机接口，用户无需关注。</td></tr><tr><td>query</td><td>基于IR excel生成json时，存放sheet所有op。</td></tr><tr><td>-h，--help</td><td>输出帮助信息。</td><td>可选参数。</td></tr></table>

# 9.1.2 算子编译部署

# 9.1.2.1 简介

自定义算子开发完成后，需要对算子工程编译出可直接安装的自定义算子run包，然后 进行run包的安装，将自定义算子部署到CANN算子库。 

算子工程编译的具体内容为：将算子插件实现文件、算子原型定义文件、算子信 息库定义文件分别编译成算子插件、算子原型库、算子信息库，针对AI CPU算 子，还会将AI CPU算子的实现文件编译为动态库文件。 

算子包部署指执行自定义算子包的安装，自定义算子交付件会自动部署到算子包 安装目录下。 

详细的编译部署流程如下图所示： 


图 9-1 自定义算子编译部署流程


![](images/2bd6d652c5fd3830f0b81b9a55c5b2f376fa1976abf4732c97201b41d57251f5.jpg)


# 须知

所有的自定义算子需要在同一算子工程中进行编译，编译成唯一的自定义算子安装包 进行部署。 

# 9.1.2.2 算子工程编译

# 简介

算子交付件开发完成后，需要对算子工程进行编译，生成自定义算子安装包*.run，详 细的编译操作包括： 

将AI CPU算子代码实现文件*.h与*.cc编译成libcust_aicpu_kernels.so。 

将算子信息库定义文件*.ini编译成*.json。 

将原型定义文件*.h与*.cc编译成libcust_op_proto.so。 

将TensorFlow/Caffe/ONNX算子的适配插件实现文件*.h与*.cc编译成libcust_{tf| caffe/onnx]_parsers.so。 

# 命令行环境

# 须知

● 不建议对样例工程或自动生成的编译配置文件进行修改，否则可能会造成自定义算 子运行失败。 

● 编译生成算子包的操作系统版本与架构需要与执行算子包部署操作的操作系统版本 与架构相同。 

步骤1 在自定义算子工程的“custom.proto”文件中增加原始框架为Caffe的自定义算子的定 义。 

若开发其他框架的算子，此步骤无需操作，custom.proto文件如下所示： 

syntax $=$ "proto2";   
package domi.caffe;   
message NetParameter{ optional string name $= 1$ //LayerParameter定义，保持默认，用户无需修改 repeated LayerParameter layer $= 100$ //ID100solayersare printed last.   
}   
message LayerParameter{ optional string name $= 1$ //模型解析所需要定义，保持默认，用户无需修改。 optional string type $= 2$ //模型解析所需要定义，保持默认，用户无需修改。 //在LayerParameter中添加自定义算子层的定义，ID需要保持唯一，取值原则为：不与内置caffe.proto中编号重复，且小于5000。 //内置的caffe.proto存储路径为CANN软件安装后文件存储路径的“include/ proto/caffe.proto”。 optionalCustomTest1Parametercustom_test1 param $= 1000$ . optionalCustomTest2Parametercustom_test2 param $= 1001$ ·   
}   
//增加自定义算子层的定义   
message CustomTest1Parameter{ optional bool adj_x1 $= 1$ [default $=$ false]; optional bool adj_x2 $= 2$ [default $=$ false];   
}   
//若自定义算子中无属性进行解析映射，则message xxParameter定义保持空，如下所示：   
message CustomTest2Parameter{ 

# 须知

Parameter的类型（粗斜体部分）建议保持唯一，不与内置caffe.proto（CANN软件安 装后文件存储路径下的“include/proto/caffe.proto”）定义重复。 

步骤2 修改build.sh脚本，配置算子编译所需环境变量。 

● ASCEND_TENSOR_COMPILER_INCLUDE：CANN软件头文件所在路径。 

请取消此环境变量的注释，并修改为CANN软件头文件所在路径，例如： export ASCEND_TENSOR_COMPILER_INCLUDE=${INSTALL_DIR}/include 

${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。若安装的Ascendcann-toolkit软件包，以root安装举例，则安装后文件存储路径为：/usr/local/ Ascend/ascend-toolkit/latest。 

TOOLCHAIN_DIR：AI CPU算子使用的编译器路径，请取消此环境变量的注释， 并按照下述描述修改。 

针对Ascend EP场景，请配置为HCC编译器所在路径，例如： 

export TOOLCHAIN_DIR=${INSTALL_DIR}/toolkit/toolchain/hcc 

${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。若安装的Ascendcann-toolkit软件包，以root安装举例，则安装后文件存储路径为：/usr/ local/Ascend/ascend-toolkit/latest。 

针对Ascend RC场景，算子编译时build.sh文件中的“TOOLCHAIN_DIR”请 配置为g++交叉编译器所在bin文件夹的上级目录，例如，交叉编译器存储路 径为/usr/bin/aarch64-linux-gnu-g++，则TOOLCHAIN_DIR配置如下： 

export TOOLCHAIN_DIR=/usr 

● AICPU_KERNEL_TARGET：AI CPU算子实现文件编译生成的动态库文件名称。 

建议用户取消此环境变量的注释，并在动态库文件的名称中添加自定义唯一 后缀作为标识，例如使用软件版本号作为后缀，避免后续由于AI CPU软件升 级造成自定义AI CPU动态库文件的冲突。注意，配置的动态库文件的名称长 度不能超过84个字节。例如： 

```txt
export AICPU_KERNEL_TARGET=cust_acpu_kernels_3.3.0 
```

若不配置此环境变量，使用默认值：cust_aicpu_kernels。 

● AICPU_SOC_VERSION：请选择实际硬件平台对应的昇腾AI处理器的类型。 

vendor_name：标识自定义算子所属厂商的名称，默认值为"customize"。建议开 发者自行指定所属厂商名称，避免和其他厂商提供的算子包冲突。当前TBE自定义 算子工程中算子实现代码文件所在的目录名为impl，算子包部署后，为避免多厂 商的算子实现Python包名冲突，所在的目录名会修改为${vendor_name}_impl的 格式。 

步骤3 执行算子工程编译。 

若您是基于《TBE&AI CPU算子开发指南》的“算子开发准备 > 工程创建 > 基于 算子样例”创建的工程，编译方法如下： 

若您只需要编译TBE算子，请在算子工程目录下执行如下命令。 

chmod $+\mathrm{x}$ build.sh ./build.sh -t 

若您只需要编译AI CPU算子，请在算子工程目录下执行如下命令。 

chmod $^+$ x build.sh ./build.sh -c 

若您既需要编译TBE算子，又需要编译AI CPU算子，请在算子工程目录下执 行如下命令。 

chmod $+\mathrm{x}$ build.sh ./build.sh 

若您是算子工程创建（msOpGen）创建的工程，编译方法如下： 

在算子工程目录下执行如下命令： 

chmod $+\mathbf{x}$ build.sh ./build.sh 

编译成功后，会在当前目录下创建build_out目录，并在build_out目录下生成自定义算 子安装包custom_opp_<target_os>_<target_architecture>.run。 

# 须知

若重新进行工程编译，请先执行./build.sh clean命令进行编译文件的清理。 

----结束 

# 9.1.2.3 算子交付件独立编译

# 简介

获取算子开发相关交付件并按照目录结构要求存放后，可进行交付件独立编译，生成 自定义算子安装包*.run，详细的编译操作包括： 

将AI CPU算子代码实现文件*.h与*.cc编译成libcust_aicpu_kernels.so。 

将算子信息库定义文件*.ini编译成*.json 

将原型定义文件*.h与*.cc编译成libcust_op_proto.so。 

将TensorFlow/Caffe/ONNX算子的适配插件实现文件*.h与*.cc编译成libcust_{tf| caffelonnx}_parsers.so。 

自动新增编译相关文件，如CMakeLists.txt。 

# 操作步骤

步骤1 独立编译前需确保算子交付件的目录结构如下所示。 

TBE算子交付件目录结构： 

![](images/c540c8fbedaf2f655ce4b877ea746fed56ce370536dffd2b09e6a25d5b3598d8.jpg)


● AI CPU算子交付件目录结构： 

![](images/df534ea10a37a4a96bc3abec8860d47b70218b89244ebb1c7102403ada27e018.jpg)


步骤2 编译算子交付件。 

执行如下命令，参数说明请参见表9-6。 

msopgen compile -i {operator deliverables directory} -c {CANN installation paths 


表9-6 参数说明


<table><tr><td>参数名称</td><td>参数描述</td><td>是否必选</td></tr><tr><td>compile</td><td>用于编译算子交付件。</td><td>是</td></tr><tr><td>-i, --input</td><td>算子交付件所在路径，可配置为绝对路径或者相对路径。工具执行用户需要有此路径的可读权限。</td><td>是</td></tr><tr><td>-c, --cann</td><td>CANN软件的安装目录。</td><td>否</td></tr><tr><td>-h，
--help</td><td>帮助提示参数。</td><td>否</td></tr></table>

步骤3 编译成功后，会在算子交付件所在路径下创建build_out目录，并在build_out目录下生 成自定义算子安装包custom_opp_<target_os>_<target_architecture>.run。 

步骤4 查看算子交付件所在路径，新增独立编译相关文件。 

编译后TBE算子交付件目录结构如下所示： 

![](images/5d2945ed648b1f3a2e69e15fbe881b0d7222521949c885519e2061dfc367a114.jpg)


编译后AI CPU算子交付件目录结构如下所示： 

![](images/faacc9675be5bd17726e14e7d381c43002cb11d7e1450a5ad907d618dde10c59.jpg)


![](images/5d47bc36a76667f4a91b243b37a8f30a6eb325b73fac096342b9abf19888f492.jpg)


----结束 

# 9.1.2.4 算子包部署

# 简介

算子部署指将算子编译生成的自定义算子安装包（*.run）部署到CANN算子库中。 

推理场景下，自定义算子直接部署到开发环境的CANN算子库。 

训练场景下，自定义算子安装包需要部署到运行环境的CANN算子库中。 

# 须知

编译生成算子包的操作系统版本和架构需要与执行算子包部署操作的操作系统版本和 架构相同。 

# 命令行环境

步骤1 训练场景下，以用户身份运行，将算子工程编译生成的自定义算子包 （custom_opp_<target_os>_<target_architecture>.run）拷贝到运行环境下的任一路 径，然后参照如下步骤部署自定义算子安装包，如果您的开发环境即为运行环境，此 操作可跳过。 

步骤2 在自定义算子包所在路径下，执行如下命令，安装自定义算子包。 

```txt
./custom OPP_<target_os>.<target_architecture>.run --install-path=<path> 
```

--install-path为可选参数，用于指定自定义算子包的安装目录，运行用户需要对 指定的安装路径有可读写权限。下文描述中的<vendor name>为算子工程编译时 build.sh脚本中字段“vendor_name”的取值，默认为"customize"。 

默认安装场景，不配置--install-path参数，安装成功后会将编译生成的自定 义算子相关文件部署到${INSTALL_DIR}/opp/vendors/<vendor name>目 录。${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。例如，若安 装的Ascend-cann-toolkit软件包，安装后文件存储路径示例为：$HOME/ Ascend/ascend-toolkit/latest。 

# 说明

自定义算子包默认安装路径${INSTALL_DIR}/opp/vendors的目录权限与CANN软件包 安装用户和安装配置有关。如果因权限不足导致自定义算子包安装失败，可使用-- install-path参数并配置环境变量ASCEND_CUSTOM_OPP_PATH来指定安装目录（参 考指定目录安装）或者联系CANN软件包的安装用户修改vendors目录权限来解决。 

指定目录安装场景，配置--install-path参数，安装成功后会将编译生成的自 定义算子相关文件部署到<path>/<vendor name>目录，并在<path>/ <vendor_name>/bin目录下新增set_env.bash，写入当前自定义算子包相关 的环境变量。 

# 须知

▪ 如果部署算子包时通过配置--install-path参数指定了算子包的安装目录， 则在使用自定义算子前，需要执行source <path>/<vendor name>/bin/ set_env.bash命令，set_env.bash脚本中将自定义算子包的安装路径追加 到环境变量ASCEND_CUSTOM_OPP_PATH中，使自定义算子在当前环境 中生效。 

▪ 对算子样例工程进行编译生成的算子包，支持指定绝对路径和相对路径的 安装方式。 

▪ 对msOpGen工具创建的算子工程进行编译生成的算子包，支持指定绝对 路径的安装方式。 

▪ 对MindStudio创建的算子工程进行编译生成的算子包，暂不支持指定目录 安装方式。 

若同一安装目录下已存在相同“vendor_name”的自定义算子，会出现类似如下 提示信息（以更新framework为例）： 

```txt
[opscustom]upgrade framework  
caffe onnx tensorflow [INFO]: has old version in /usr/local/xxx/vendors/customize/framework:  
- Overlay Installation, please enter:[o]  
- Replace directory installation, please enter: [r]  
- Do not install, please enter:[n] 
```

输入“o”，代表覆盖安装，即若安装包中文件与已存在文件名称相同，使用 安装包中文件替换原文件；若安装包中不包含已存在文件，则已存在文件保 留。 

输入“r”，代表全新安装，即删除安装路径下的所有文件，然后使用安装包 全新安装。 

– 输入“n”，代表退出安装。 

说明：后续若存在“op proto”、“op impl”、“custom.proto”等文件的安装 模式选择，请分别根据提示信息输入相应的字符。 

以默认安装场景为例，部署后目录结构示例如下所示： 

![](images/06d90caeeb532969d83b4f8861f0425e4723627dfd013dc6e66d35006b42ea6a.jpg)


![](images/e61df754a2dd137c888ec0dd1febd24d45c04c970f06402631aa09c274af6578.jpg)



注：其他目录与文件，开发者无需关注。


步骤3 配置自定义算子优先级。 

多算子包共存的情况下，若不同的算子包目录下存在相同OpType的自定义算子，则以 优先级高的算子包目录下的算子为准。下面介绍如何配置算子包优先级： 

默认安装场景 

当“opp/vendors”目录下存在多个厂商的自定义算子时，您可通过配置“opp/ vendors”目录下的“config.ini”文件，配置自定义算子包的优先级。 

“config.ini”文件的配置示例如下： 

```csv
loadpriority=vendor_name1,vendor_name2,vendor_name3 
```

“load_priority”：优先级配置序列的关键字，不允许修改。 

“vendor name1,vendor name2,vendor name3”：自定义算子厂商的优先 级序列，按照优先级从高到低的顺序进行排列。 

指定目录安装场景 

指定目录安装场景下，如果需要多个自定义算子包同时生效，分别执行各算子包 安装路径下的set_env.bash脚本即可。每次脚本执行都会将当前算子包的安装路 径追加到ASCEND_CUSTOM_OPP_PATH环境变量的最前面。因此可以按照脚本执 行顺序确定优先级：脚本执行顺序越靠后，算子包优先级越高。 

比如先执行source <path>/vendor name1/bin/set env.bash，后执行source <path>/vendor_name2/bin/set_env.bash，vendor_name2算子包的优先级高 于vendor_name1。ASCEND_CUSTOM_OPP_PATH示例如下： 

```txt
ASCENDCustom OPP_PATH=<path>/vendor_name2</path>/vendor_name1 
```

指定目录安装场景下安装的算子包优先级高于默认方式安装的算子包。 

----结束 

# 9.1.3 基于 msOpST 工具进行算子 ST 测试

# 9.1.3.1 简介

# 功能描述

CANN开发套件包中提供了ST测试工具：msOpST，支持生成算子的ST测试用例并在硬 件环境中执行。具有如下功能： 

根据算子信息库定义文件（*.ini）生成算子测试用例定义文件（*.json），作为算 子ST测试用例的输入。 

根据算子测试用例定义文件生成ST测试数据及测试用例执行代码，在硬件环境上 执行算子测试用例。 

自动生成运行报表（st_report.json）功能，报表记录了测试用例信息及各阶段运 行情况。 

根据用户定义并配置的算子期望数据生成函数，回显期望算子输出和实际算子输 出的对比测试结果。 

# 使用前提

使用此工具生成算子测试用例前，需要将要测试的算子部署到算子库中。 

昇腾AI处理器类型为Atlas 200/300/500 推理产品时，不支持PyTorch框架下的ST 测试。 

# 补充说明

msOpST工具其他参数说明可参考表9-7。 


表9-7 参数说明


<table><tr><td>参数名称</td><td>参数描述</td><td>说明</td></tr><tr><td>mi</td><td>仅供MindStudio侧使用。</td><td rowspan="7">机机接口，用户无需关注。</td></tr><tr><td>get_shape</td><td>获取shape。</td></tr><tr><td>change_shape</td><td>修改shape。</td></tr><tr><td>gen</td><td>生成acl_op.json。</td></tr><tr><td>gen_testcase</td><td>生成测试文件及数据。</td></tr><tr><td>compare</td><td>结果比对。</td></tr><tr><td>compare_by_path</td><td>指定路径文件结果比对。</td></tr><tr><td>-h, --help</td><td>帮助提示参数。</td><td>可选参数。</td></tr></table>

# 9.1.3.2 生成测试用例定义文件

指导用户使用msOpST工具生成算子测试用例定义文件（*.json），作为算子ST测试用 例的输入。 

# 使用方法

步骤1 获取待测试算子的信息定义文件（.ini）路径。 

msOpST工具根据待测算子信息库定义文件（.ini）生成算子ST测试用例定义文件，在 算子工程文件中算子信息库定义文件路径如下所示。 

![](images/7e172db60d23176f61c19798c4aa7c57f55c782299d1a749d03134672a0b1f90.jpg)


![](images/ea97665a706f0f68ceee450fc85abb46708d3232d34e7887134d31067664c302.jpg)


ini文件在TBE算子工程下的路径为：“tbe/op_info_cfg/ai_core/{Soc Version}/ xx.ini”，{Soc Version}为昇腾AI处理器的类型。 

ini文件在AI CPU算子工程下的路径为：“cpukernel/op_info_cfg/aicpu_kernel/ xx.ini” 。 

# 说明

若进行AI CPU自定义算子ST测试，请不要改变算子工程的目录结构。因为该工具会根据算子信 息库定义文件所在算子工程的目录找到算子原型定义文件，并根据算子原型定义文件生成算子测 试用例定义文件。 

步骤2 执行如下命令生成算子测试用例定义文件，参数说明请参见表9-8。 

msopst create -i {operator define file} -out {output path} -m {pb file} -q 


表9-8 参数说明


<table><tr><td>参数名称</td><td>参数描述</td><td>是否必选</td></tr><tr><td>create</td><td>用于生成算子测试用例定义文件(*.json)。</td><td>是</td></tr><tr><td>-i, --input</td><td>算子信息库定义文件路径(*.ini文件),可配置为绝对路径或者相对路径。说明:输入的算子信息库定义文件(*.ini)仅能包含一个算子的定义。</td><td>是</td></tr><tr><td>-out, --output</td><td>生成文件所在路径,可配置为绝对路径或者相对路径,并且工具执行用户具有可读写权限。若不配置,则默认生成在执行命令的当前路径。</td><td>否</td></tr><tr><td>-m, --model</td><td>配置为TensorFlow模型文件的路径,可配置为绝对路径或者相对路径。若配置此参数,工具会从TensorFlow模型文件中获取首层算子的shape信息,并自动dump出算子信息库定义文件中算子的shape、dtype以及属性的value值,如果dump出的值在算子信息库定义文件所配置的范围内,则会自动填充到生成的算子测试用例定义文件中;否则会报错。须知若配置此参数,系统中需要安装1.15或2.6.5版本的TensorFlow。</td><td>否</td></tr><tr><td>-q, --quiet</td><td>当前版本仅针对-m参数生效，代表是否进行人机交互。若不配置-q参数，则会提示用户修改获取到的模型中的首层shape信息。若配置了-q参数，则不会提示用户更改首层shape信息。</td><td>否</td></tr><tr><td>-h, --help</td><td>输出帮助信息。</td><td>否</td></tr></table>

示例： 

以add算子为例，执行如下命令: 

```batch
msopst create -i OpInfoDefine/add.ini -out ./output 
```

请将OpInfoDefine更换为算子信息库定义文件所在路径，请参见步骤1。 

命令执行成功后，会在当前路径的output目录下生成算子测试用例定义文件： Add_case_timestamp.json。 

步骤3 修改测试用例定义模板文件“OpType_case_timestamp.json”。 

步骤2生成的json文件为模板文件，不满足直接作为ST测试用例生成输入的要求，所以 用户需要参考此步骤，修改算子测试用例定义文件（*.json），构造测试用例，以满足 ST测试覆盖的范围。 

```jsonl
{ "case_name":"Test_Add_001", "error_threshold":[0.1,0.1], "st_mode":"pt_PYthon_train", "run_torch_api":"torch(square", "op":"Add", "input_desc": [ { "name":"x1", "format": [ "ND" ], "type": [ "int32", "float", "float16" ], "shape": [32,16], "data_distribution": [ "uniform" ], "value_range": [ 0.1, 1.0 ] ] } { "name":"x2", "format": [ "ND" ], "type": [ 
```

```txt
"int32", "float", "float16" ], "shape": [32,16], "data_distribution": [ "uniform" ], "value_range": [ 0.1, 1.0 ] ] } ], "output_desc": [ { "name": "y", "format": [ "ND" ], "type": [ "int32", "float", "float16" ], "shape": [32,16] } ] 
```

测试用例定义文件其他配置项及说明。 

当TBE算子信息库定义文件（*.ini）中inputx.paramType=optional时，生成的算 子测试用例中inputx的"format"为"UNDEFINED"或"RESERVED"，"type"为 "UNDEFINED"。 

当TBE算子信息库定义文件（*.ini）中inputx.paramType=dynamic时，生成的算 子测试用例中inputx的"name"为“算子名称+编号”，编号根据dynamic_input的 个数确定，从0开始依次递增。 

当TBE算子信息库定义文件（*.ini）中Tensor的实现format与原始format不同时， 用户需手动添加"ori_format"和"ori_shape"字段，将origin_format与 origin_shape转成离线模型需要的format与shape。 

"ori_format"输入为原始算子支持的数据格式，个数必须与format个数保持 一致。 

"ori_shape"输入为shape根据format和ori_format转换的结果。 

用户可基于如上模板进行修改，“*.json”文件支持的全量字段说明如下表所示。不同 场景下的测试用例定义文件的样例可参见9.1.3.4 测试用例定义文件配置样例。 


表 9-9 算子测试用例定义 json 文件


<table><tr><td colspan="2">参数</td><td>说明</td></tr><tr><td>case_name</td><td>-</td><td>必选。
String类型。
测试用例的名称。</td></tr><tr><td>op</td><td>-</td><td>必选。String类型。算子的类型。不允许为空。</td></tr><tr><td>error_threshold</td><td>-</td><td>可选。配置自定义精度标准,取值为含两个元素的列表:"[threshold1, threshold2]"·threshold1:算子输出结果与标杆数据误差阈值,若误差大于该值则记为误差数据。·threshold2:误差数据在全部数据占比阈值。若误差数据在全部数据占比小于该值,则精度达标,否则精度不达标。取值范围为:"[0.0,1.0]".说明若测试用例json文件和执行msopst命令时均配置该参数,以执行msopst命令时配置的精度标准进行比对。若均未配置,则以执行msopst命令时默认精度标准[0.01,0.05]进行比对。</td></tr><tr><td>st_mode</td><td>-</td><td>可选。String类型。ST测试模式,其值为:"ms.python_train",表示Mindspore的算子工程(仅Atlas训练系列产品支持)；"pt.python_train",表示PyTorch框架下的算子工程。Atlas 200/300/500推理产品不支持此参数配置。</td></tr><tr><td>run_torch_api</td><td>-</td><td>可选。配置torch_api调用算子的接口,其值为："torch_square","square"为接口名称,请根据实际情况配置。Atlas 200/300/500推理产品不支持此参数配置。</td></tr><tr><td>expect</td><td>-</td><td>可选。用户期望的测试结果状态。属性支持以下两种类型,默认值为“success”。·success:表示期望测试用例运行成功。若模型转换失败,流程将提前终止,用户可查看ATC工具相关日志定位问题。·failed:表示期望测试用例运行失败。若用户需要运行异常用例,可修改expect字段为failed。若模型转换失败,流程将继续执行。在统计结果中,依据STCaseReport中的status和expect是否一致统计,一致则统计至“success count”,不一致则统计至“failed count”。</td></tr><tr><td>fuzz Impl</td><td>-</td><td>可选，String类型。若用户需要生成大量测试用例，可利用fuzz测试参数生成脚本辅助生成。此种场景下，用户需要手工添加此字段，配置fuzz测试参数生成脚本的绝对路径或者相对路径：函数名，fuzz测试参数生成脚本的实现方法请参见步骤4。说明不建议用户调用其它用户目录下的fuzz测试参数生成脚本，以避免提权风险。</td></tr><tr><td>fuzz(case_num</td><td>-</td><td>可选。int类型。在添加了“fuzz Impl”参数的情况下，需要手工添加此字段，配置利用fuzz测试参数生成脚本生成测试用例数量，范围为1~2000。</td></tr><tr><td>input_desc</td><td>-</td><td>必选。算子输入描述。须知所有input_desc中参数取值的个数都要一致，否则测试用例生成会失败。例如：input1的format支持的类型个数2，则input2的format支持的类型个数也需要为2。同理，所有inputx中的type、shape、data_distribution和value_range的取值个数也需要保持一致。</td></tr><tr><td>-</td><td>name</td><td>可选。算子为动态多输入场景时，“name”为必选配置，请配置为算子信息库中“inputx.name”参数的名称+编号，编号从“0”开始，根据输入的个数按照0，1，2……，依次递增。例如，算子信息文件中指定的输入个数为4个，则input_desc中需要配置4个输入描述，name分别为“xxx0”、“xxx1”、“xxx2”、“xxx3”，其中xxx为输入参数的名称。动态多输入场景的配置示例可参见·若算子的输入个数不确定（动态多输入场景）。</td></tr><tr><td>-</td><td>format</td><td>必选。String或者String的一维数组。输入Tensor数据的排布格式，不允许为空。常见的数据排布格式如下：·NCHW·NHWC·ND：表示支持任意格式。·NC1HWC0：5维数据格式。其中，C0与微架构强相关，该值等于cube单元的size，例如16；C1是将C维度按照C0切分：C1=C/C0，若结果不整除，最后一份数据需要padding到C0。·FRACTAL_Z：卷积的权重的格式。·FRACTAL_NZ：分形格式，在cube单元计算时，输出矩阵的数据格式为NW1H1H0W0。整个矩阵被分为（H1*W1）个分形，按照column major排布，形状如N字形；每个分形内部有（H0*W0）个元素，按照row major排布，形状如z字形。考虑到数据排布格式，将NW1H1H0W0数据格式称为Nz格式。其中，H0,W0表示一个分形的大小，示意图如下所示：Fractal Matrix SizeMatrix C·RESERVED：预留，当format配置为该值，则type必须配置为“UNDEFINED”，代表算子的此输入可选。·fuzz：使用fuzz测试参数生成脚本自动批量生成值。</td></tr><tr><td>-</td><td>ori_format</td><td>可选。String或者String的一维数组，支持以下两种取值：·配置为输入数据的原始format。当算子实现的format与原始format不同时，需要配置此字段；若不配置此字段，默认算子实现的format与原始format相同。·配置为“fuzz”，表示使用fuzz测试参数生成脚本自动批量生成值。</td></tr><tr><td>-</td><td>type</td><td>必选。String或者String的一维数组。输入数据支持的数据类型。·bool·int8·uint8·int16·uint16·int32·int64·uint32·uint64·float16·float32·float·bfloat16（仅Atlas A2 训练系列产品/Atlas 800I A2推理产品/A200I A2 Box 异构组件支持该数据类型）·double（仅AI CPU算子支持该数据类型）·complex64（仅AI CPU算子支持该数据类型）·complex128（仅AI CPU算子支持该数据类型）·UNDEFINED：表示算子的输入类型为可选。·fuzz：使用fuzz测试参数生成脚本自动批量生成值。输入数据类型为复数场景的配置示例可参见·若算子的输入输出类型为复数，测试用例定义文件如...。</td></tr><tr><td>-</td><td>shape</td><td>必选。int类型。一维或者二维数组。输入Tensor支持的形状。- 支持静态shape输入的场景: shape维度以及取值都为固定值,该场景下不需要配置shape_range参数。- 支持动态shape输入的场景: shape中包含-1,例如:(200,-1)表示第二个轴长度未知。该场景下需要与shape_range参数配合使用,用于给出“-1”维度的取值范围。String类型,“fuzz”。支持fuzz,使用fuzz测试参数生成脚本自动批量生成值。空如果format和type为UNDEFINED时shape允许为空。需要注意,配置的shape需要与format相匹配。</td></tr><tr><td>-</td><td>ori_shape</td><td>可选。int类型。一维或者二维数组。输入数据的原始shape。当算子实现的shape与原始shape不同时,需要配置此字段。String类型,“fuzz”。支持fuzz,使用fuzz测试参数生成脚本自动批量生成值。若不配置此字段,默认算子实现的shape与原始shape一致。</td></tr><tr><td>-</td><td>typical_shape</td><td>可选。int类型。一维或者二维数组。实际用于测试的shape。若配置的“shape”字段中含有-1时,用户需要在算子测试用例定义文件中新增“typical_shape”字段,给定出固定shape值,用于实际测试。String类型,“fuzz”。支持fuzz,使用fuzz测试参数生成脚本自动批量生成值。</td></tr><tr><td>-</td><td>shape_range</td><td>可选。
• int类型。一维或者二维数组。
当算子支持动态shape时，此字段表示支持的shape范围。
默认值为：[1,-1]。表示shape可以取1到无穷。
例如：shape配置为(200,-1)，shape_range配置为[1,-1]时，则代表shape第二个维度的取值为1到无穷。
• String类型,“fuzz”。
支持fuzz，使用fuzz测试参数生成脚本自动批量生成值。</td></tr><tr><td>-</td><td>is_const</td><td>可选。
bool类型。
• true: 若用户需要配置常量输入的用例，则配置该字段，其值为true。
• false: 若该字段值为false，则需要配置张量输入用例。
输入为常量的配置示例可参见·若算子的某个输入为常量，测试用例定义文件如下所...。</td></tr><tr><td>-</td><td>data_distribute</td><td>必选。
String或者String的一维数组。
使用哪种数据分布方式生成测试数据，支持的分布方式有：
• uniform: 返回均匀分布随机值
• normal: 返回正态分布（高斯分布）随机值
• beta: 返回Beta分布随机值
• laplace: 返回拉普拉斯分布随机值
• triangular: 返回三角形分布随机值
• relu: 返回均匀分布+ReLU激活后的随机值
• sigmoid: 返回均匀分布+sigmoid激活后的随机值
• softmax: 返回均匀分布+softmax激活后的随机值
• tanh: 返回均匀分布+tanh激活后的随机值
• fuzz: 使用fuzz测试参数生成脚本自动批量生成值</td></tr><tr><td>-</td><td>value_range</td><td>必选。int类型或者float类型。一维或者二维数组。取值范围,不能为空。为[min_value,max_value]且min_value&lt;=max_value。String类型,“fuzz”。支持fuzz,使用fuzz测试参数生成脚本自动批量生成值</td></tr><tr><td>-</td><td>value</td><td>可选。String或者Tensor数组。若用户需要指定输入数据时,可通过增加“value”字段进行配置。有如下两种配置方式:直接输入Tensor数据,如Tensor的值为[1,2,3,4]。“value”:[1,2,3,4]输入二进制数据文件的路径,如数据文件为test.bin时。“value”:“../test.bin”二进制数据bin文件需用户自己准备。可以输入绝对路径,也可以输入测试用例定义文件的相对路径。配置为“fuzz”,使用fuzz测试参数生成脚本自动批量生成值。说明若用户添加了“value”字段,“data_distribution”和“value_range”字段将会被忽略。同时需要保证“format”,“type”,“shape”字段的值与“value”数据对应,且每个用例只能测试一种数据类型。配置示例可参见·若指定固定输入,例如ReduceSum的axe...。</td></tr><tr><td>output_desc</td><td>-</td><td>必选。算子输出描述。须知output_desc中参数取值的个数都要与input_desc一致,否则测试用例生成会失败。例如:inputx的format支持的类型个数2,则output的format支持的类型个数也需要为2。</td></tr><tr><td>-</td><td>name</td><td>可选。String类型。输出参数名称。算子为动态多输出场景时,“name”为必选配置,请配置为算子信息库中“outputx.name”参数的名称+编号,编号从“0”开始,根据输出的个数按照0,1,2......,依次递增。例如,算子信息文件中指定的输出个数为4个,则output_desc中需要配置4个输出描述,name分别为“xxx0”、“xxx1”、“xxx2”、“xxx3”,其中xxx为输出参数的名称。</td></tr><tr><td>-</td><td>format</td><td>必选。String或者String的一维数组。输出Tensor数据的排布格式，不允许为空。支持如下数据排布格式：·NCHW·NHWC·ND：表示支持任意格式。·NC1HWC0：5维数据格式。其中，C0与微架构强相关，该值等于cube单元的size，例如16；C1是将C维度按照C0切分：C1=C/C0，若结果不整除，最后一份数据需要padding到C0。·FRACTAL_Z：卷积的权重的格式。·FRACTAL_NZ：分形格式，在cube单元计算时，输出矩阵的数据格式为NW1H1H0W0。整个矩阵被分为（H1*W1）个分形，按照column major排布，形状如N字形；每个分形内部有（H0*W0）个元素，按照row major排布，形状如z字形。考虑到数据排布格式，将NW1H1H0W0数据格式称为Nz格式。其中，H0,W0表示一个分形的大小，示意图如下所示：Fractal Matrix SizeMatrix C·fuzz：使用fuzz测试参数生成脚本自动批量生成值。</td></tr><tr><td>-</td><td>ori_format</td><td>可选。String或者String的一维数组。·当算子实现的format与原始format不同时,需要配置此字段,配置为数据的原始format。·配置为“fuzz”,表示使用fuzz测试参数生成脚本自动批量生成值。若不配置此字段,默认算子实现的format与原始format相同。</td></tr><tr><td>-</td><td>type</td><td>必选。String或者String的一维数组或“fuzz”。输出数据支持的数据类型。·bool·int8·uint8·int16·uint16·int32·int64·uint32·uint64·float16·float32·float·bfloat16(仅Atlas A2 训练系列产品/Atlas 800I A2推理产品/A200I A2 Box 异构组件支持该数据类型)·double(仅AI CPU算子支持该数据类型)·complex64(仅AI CPU算子支持该数据类型)·complex128(仅AI CPU算子支持该数据类型)·fuzz:使用fuzz测试参数生成脚本自动批量生成值。</td></tr><tr><td>-</td><td>shape</td><td>必选。·int类型。一维或者二维数组。输入Tensor支持的形状。·String类型,“fuzz”。支持fuzz,使用fuzz测试参数生成脚本自动批量生成值。</td></tr><tr><td>-</td><td>ori_shape</td><td>可选。int类型。一维或者二维数组。输入数据的原始shape。当算子实现的shape与原始 shape不同时,需要配置此字段。String类型,“fuzz”。支持fuzz,使用fuzz测试参数生成脚本自动批量生成值。若不配置此字段,默认算子实现的shape与原始shape一致。</td></tr><tr><td>attr</td><td>-</td><td>可选。</td></tr><tr><td>-</td><td>name</td><td>若配置attr,则为必选。String类型。属性的名称,不为空。</td></tr><tr><td>-</td><td>type</td><td>若配置attr,则为必选。String类型。属性支持的类型。boolintfloatstringlist boollist_intlist_floatlist_stringlist_list_intdata_type:如果attr中的value值为数据类型时,type值必须为data_type</td></tr><tr><td>-</td><td>value</td><td>若配置attr,则为必选。属性值,根据type的不同,属性值不同。如果“type”配置为“bool”,“value”取值为true或者false。如果“type”配置为“int”,“value”取值为整形数据。如果“type”配置为“float”,“value”取值为浮点型数据。如果“type”配置为“string”,“value”取值为字符串,例如“NCHW”。如果“type”配置为“list bool”,“value”取值示例: [false, true]。如果“type”配置为“list_int”,“value”取值示例: [1, 224, 224, 3]。如果“type”配置为“list_float”,“value”取值示例: [1.0, 0.0]。如果“type”配置为“list_string”,“value”取值示例: ["str1", "str2"]如果“type”配置为“data_type”,“value”支持如下取值:int8、int32、int16、int64、uint8、uint16、uint32、uint64、float、float16、float32、bool、double、complex64、complex128、bfloat16。“value”值配置为“fuzz”时,表示使用fuzz测试参数生成脚本自动批量生成值。</td></tr><tr><td>calc Expect_func_file</td><td>-</td><td>可选。String类型。算子期望数据生成函数对应的文件路径及算子函数名称,如: "/home/test/test_*.py:function"其中,/home/test/test_*.py为算子期望数据生成函数的实现文件, function为对应的函数名称。须知不建议用户调用其它用户目录下的期望数据生成脚本,以避免提权风险。</td></tr></table>

步骤4 若用户需要自动生成大量测试用例，请参考此步骤用实现fuzz测试参数生成脚本 （.py）并配置测试用例定义文件（.json）。 

1. 实现fuzz测试参数生成脚本。该脚本可以自动生成测试用例定义文件中 input_desc、output_desc、attr内除了name的任何参数。 

下面以随机生成shape和value参数为例，创建一个fuzz_shape.py供用户参考。该 示例会随机生成一个1-4维，每个维度取值范围在1-64的shape参数，用于ST测 试。 

a. 导入脚本所需依赖。 

```txt
import numpy as np 
```

b. 实现fuzz_branch()方法，若用户自定义随机生成待测试参数的方法名，需要 在算子测试用例定义文件中配置fuzz_impl字段。 

```python
def fuzz_branch():
    # 生成测试参数shape值
    dim = random.randint(1, 4)
    x_shape_0 = random.randint(1, 64)
    x_shape_1 = random.randint(1, 64)
    x_shape_2 = random.randint(1, 64)
    x_shape_3 = random.randint(1, 64)
    if dim == 1:
        shape = [x_shape_0]
    if dim == 2:
        shape = [x_shape_0, x_shape_1]
    if dim == 3:
        shape = [x_shape_0, x_shape_1, x_shape_2]
    if dim == 4:
        shape = [x_shape_0, x_shape_1, x_shape_2, x_shape_3]
    # 根据shape随机生成x1、x2的value
    fuzz_value_x1 = np.random.randint(1, 10, size=shape)
    fuzz_value_x2 = np.random.randint(1, 10, size=shape)
    # 用字典数据结构返回shape值，将生成的shape值返回给input_desc的x1、x2和output_desc的y的shape参数。其中x1、x2、y测试用例定义文件输入、输出的name。
    return {"input_desc": {"x1": {"shape": shape,"value": fuzz_value_x1},
                    "x2": {"shape": shape,"value": fuzz_value_x2"},
                    "output_desc": {"y": {"shape": shape}})} 
```

该方法生成测试用例定义文件input_desc、output_desc、attr内除了 name的任何参数，用户可自定义实现参数的生成方法，以满足算子测试 的需求。 

该方法的返回值为字典格式，将该方法生成的参数值以字典的方式赋值 给算子进行st测试。返回的字典结构与测试用例定义文件中参数结构相 同。 

# 2. 配置测试用例定义文件。

a. 添加“fuzz_impl”字段，值为“fuzz生成测试参数的脚本的相对路径或绝对 路径：函数名”，如：“conv2d_fuzz.py:fuzz_branch”若自定义的随机生成 待测试参数的方法，请将fuzz_branch配置为自定义方法名，若不配置默认使 用fuzz_branch方法。 

b. 添加“fuzz_case_num”字段，值为利用fuzz脚本生成多少条测试用例，如： 2000。 

c. 将需要自动生成的参数的值设为"fuzz"。 

详细的参数说明可参见表9-9。 

算子测试用例定义文件的示例如下所示： 

```txt
{
    "case_name":"Test_Add_001",
    "op":"Add",
    "fuzz_impl":"./fuzz_shape.py:fuzz_branch", //配置fuzz测试参数生成脚本路径:函数名
    "fuzz(case_num": 2000, //配置生成测试用例数量
    "input_desc": [ //算子的输入描述
        { //算子的第一个输入
            "name":"x1",
            "format": [ 
```

```txt
"ND" //删除多余值，保留一个与自动生成shape参数相匹配的值
],
"type": [
"float16" //删除多余值，保留一个与自动生成shape参数相匹配的值
],
"shape":"fuzz", //修改自动生成参数的值为“fuzz”
"data_distribution": [
uniform"
],
"value_range": [
0.1, 1.0
]
],
"value":"fuzz"
{
//算子的第二个输入
"name":"x2",
"format": [
"ND" //删除多余值，保留一个与自动生成shape参数相匹配的值
],
"type": [
float16" //删除多余值，保留一个与自动生成shape参数相匹配的值
],
"shape":"fuzz", //修改自动生成参数的值为“fuzz”
 data_distribution": [
uniform"
],
value_range": [
0.1, 1.0
]
],
"value":"fuzz"
}
},
"output_desc": [ //算子的输出描述，必选，含义同输入Tensor描述
{name:"y",
"format": [
"ND" //删除多余值，保留一个与自动生成shape参数相匹配的值
],
"type": [
float16" //删除多余值，保留一个与自动生成shape参数相匹配的值
],
shape":"fuzz" //修改自动生成参数的值为“fuzz” 
```

# 说明

测试用例定义文件中参数为“fuzz”的输入、输出或属性需要有“name”参数，若没 有请手动添加“name”参数，如： "name": "y"。 

若测试用例定义文件中存在参数值为“fuzz”的情况下，其他各参数取值需唯一，并且 与fuzz测试参数生成脚本生成的参数不矛盾，如：shape参数为“fuzz”，且生成的 shape为[1, 3, 16, 16]，对应的format也应该是支持4维的。 

步骤5 若用户需要得到实际算子输出与期望输出的比对结果，需要参考此步骤自定义期望数 据生成函数。 

1. 自定义实现add算子期望数据生成函数。 

在Python文件中实现算子期望数据生成函数，文件目录和文件名称可自定义，如 “/home/test/test_add_st.py” 。 

例如Add算子的期望数据生成函数实现如下： 

```python
def calc expects_func(x1, x2, y):
    res = x1["value"] + x2["value"]
    return [res, ] 
```

# 注意

用户需根据开发的自定义算子完成算子期望数据生成函数。测试用例定义文件中 的全部Input、Output、Attr的name作为算子期望数据生成函数的输入参数，若 Input是可选输入，请将该输入指定默认值传参。 

例如，某算子输入中的x3为可选输入时，定义该算子的期望数据生成函数如下。 

```txt
def calc expects_func(x1, x2, x3=None, y=None) 
```

2. 在ST测试用例定义文件“OpType_xx.json”中增加比对函数。配置算子测试用例 定义文件。 

```javascript
在步骤1中的算子测试用例定义文件Add(case_timestamp.json增加"calc expect func file"参数，参数值为"/home/test/test_add_st.py:calc expect func"。  
[{"case_name":"Test_Add_001","op":"Add","calc expect func file":"/home/test/test_add_st.py:calc expect func",//配置生成算子期望输出数据的实现文件"input_desc":[...]…} 
```

----结束 

# 9.1.3.3 生成/执行测试用例

指导用户根据算子测试用例定义文件生成ST测试数据及测试用例执行代码，在硬件环 境上执行算子测试用例。 

# 开发环境与运行环境合设场景

步骤1 请参见2 环境准备，配置CANN软件所需基本环境变量。 

步骤2 ST测试用例执行时，会使用AscendCL接口加载单算子模型文件并执行，所以需要配置 AscendCL应用编译所需其他环境变量，如下所示。 

```javascript
export DDK_PATH=\({INSTALL_DIR}\}
export NPU_HOST_lib=\({INSTALL_DIR}/\{arch-os\}/devlib 
```

# 说明

● ${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。若安装的Ascend-cann-toolkit软 件包，以root安装举例，则安装后文件存储路径为：/usr/local/Ascend/ascend-toolkit/ latest。 

● {arch-os}中arch表示操作系统架构，os表示操作系统。 

步骤3 执行如下命令生成/执行测试用例。 

```tcl
msopst run -i \*\*.json\} -soc{soc version} -out {output path} -c {case name} -d {device id} -conf {msopst.ini path} -err_thr ["threshold1,threshold2"] 
```


表 9-10 参数说明


<table><tr><td>参数名称</td><td>参数描述</td><td>是否必选</td></tr><tr><td>run</td><td>用于执行算子的ST测试用例。</td><td>是</td></tr><tr><td>-i, --input</td><td>算子测试用例定义文件(*.json)的路径,可配置为绝对路径或者相对路径。此处的json文件为执行msopst create命令后的输出,算子测试用例定义文件的详细说明请参见表9-9。</td><td>是</td></tr><tr><td>-soc, --soc_version</td><td>配置为昇腾AI处理器的类型。说明如果无法确定具体的&lt; Soc_version&gt;,则在安装昇腾AI处理器的服务器执行npu-sminfo命令进行查询,在查询到的“Name”前增加Ascend信息,例如“Name”对应取值为xxxxy,实际配置的&lt;Soc_version&gt;值为Ascendxxxxy。</td><td>是</td></tr><tr><td>-out, --output</td><td>生成文件所在路径,可配置为绝对路径或者相对路径,并且工具执行用户具有可读写权限。若不配置该参数,则默认生成在执行命令的当前路径。</td><td>否</td></tr><tr><td>-c, --case_name</td><td>• 配置为需要执行的case的名字,若需要同时运行多个case,多个case之间使用逗号分隔。• 若配置为“all”,或者不配置此参数,代表执行所有case。</td><td>否</td></tr><tr><td>-d, --device_id</td><td>NPU设备ID,设置运行ST测试用例的昇腾AI处理器的ID。若未设置此参数,默认为:0。</td><td>否</td></tr><tr><td>-err_thr, --error_threshold</td><td>配置自定义精度标准,取值为含两个元素的列表:"[threshold1, threshold2]"• threshold1:算子输出结果与标杆数据误差阈值,若误差大于该值则记为误差数据。• threshold2:误差数据在全部数据占比阈值。若误差数据在全部数据占比小于该值,则精度达标,否则精度不达标。默认值为:"[0.01,0.05]".取值范围为:"[0.0,1.0]".说明• 配置的列表需加引号以避免一些问题。例如配置为:-err_thr"[0.01,0.05]”。• 若测试用例json文件和执行msopst命令时均配置该参数,以执行msopst命令时配置的精度标准进行比对。若均未配置,则以执行msopst命令时默认精度标准[0.01,0.05]进行比对。</td><td>否</td></tr><tr><td>-conf, -- config_file</td><td>ST测试高级功能配置文件（msopst.ini）存储路径，可配置为绝对路径或者相对路径。msopst.ini配置文件的详细说明请参见表9-11。用户可通过修改msopst.ini配置文件，实现如下高级功能：·ST测试源码可编辑·已编辑的ST测试源码可执行·设置Host日志级别环境变量·设置日志是否在控制台显示·设置atc模型转换的日志级别·设置atc模型转换运行环境的操作系统类型及架构·设置模型精度·读取算子在昇腾AI处理器上运行的性能数据</td><td>否</td></tr><tr><td>-err_report, --error_report</td><td>针对比对失败的用例，获取算子期望数据与实际用例执行结果不一致的数据。若未设置此参数，默认为：“false”。·true：针对比对失败的用例，将算子期望数据与实际用例执行结果不一致的数据保存在{case.name}_error_report.csv文件中。·false：不保存比对失败的数据结果。说明- 设置此参数为“true”时，获取的比对数据会根据每个case_name生成独立的csv文件，{case.name}_error_report.csv文件所在目录为{output_path}/{time_stamp}/{op_type}/run/out/test_data/data/st_error_reports。- 单个csv文件保存数据的上限为5万行，超过则依次生成新的.csv文件，文件命名如：{case.name}_error_report0.csv。</td><td>否</td></tr><tr><td>-h, --help</td><td>输出帮助信息。</td><td>否</td></tr></table>

msopst.ini文件获取路径为：${INSTALL_DIR}/python/site-packages/bin/。 ${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。若安装的Ascendcann-toolkit软件包，以root安装举例，则安装后文件存储路径为：/usr/local/ Ascend/ascend-toolkit/latest。 

msopst.ini文件参数说明如下表所示。 


表 9-11 msopst.ini 文件参数说明


<table><tr><td>参数</td><td>值</td><td>说明</td></tr><tr><td>only_gen_without_run</td><td>- True- False (默认)</td><td rowspan="2">msOpST工具运行模式。详情请参见表9-12。</td></tr><tr><td>only_run_without_gen</td><td>- True- False (默认)</td></tr><tr><td>performance_mode</td><td>- True- False</td><td>获取算子性能模式。若设置为True,运行成功后在run/out/prof/JOBxxx/summary目录下生成一系列性能结果文件,用户只需查看op.summary_0_1.csv即可。该功能需要配置CANN包安装环境变量,请根据实际安装路径修改。export install_path=/home/HwHiAiUser/Ascend/ascend-toolkit/latest</td></tr><tr><td>ASCENDGLOBAL_LOG_LEVEL</td><td>- 0: DEBUG级别- 1: INFO级别- 2: WARNING级别- 3: ERROR级别(默认)- 4: NULL级别,不输出日志</td><td>设置Host日志级别环境变量。</td></tr><tr><td>ASCEND_SLOG_PRIN_TO_STDOUT</td><td>- 0: 屏幕不打印输出(默认)- 1: 屏幕打印输出</td><td>日志屏幕打印控制。</td></tr><tr><td>atc_singleop.advanc
e_option</td><td>--log参数取值:- debug:输出debug/info/
warning,error/event级别的
运行信息-- info:输出info/warning/
error/event级别的运行信息-- warning:输出warning/
error/event级别的运行信息-- error:输出error/event级别的
运行信息(默认)- null:不输出日志信息--precision_mode参数取值:- force.fp16:表示算子支持
fp16和fp32时,强制选择
fp16(默认)- force.fp32:表示算子支持
fp16和fp32时,强制选择
fp32- allow_fp32_to.fp16:表示
如果算子支持fp32,则保留
原始精度fp32;如果不支持
fp32,则选择fp16- must_keep_origin dtype:
表示保持原图精度- allow_mix_precision:表示
混合精度模式--host_env_os参数取值:
linux:表示设置操作系统类型
为linux--host_env_cpu参数取值:- x86_64:表示设置操作系统
架构为x86_64-aarch64:表示设置操作系
统架构为aarch64示例:
atcsingleopadvance_option="--log=info --host_env_os=linux--
host_env_cpu=aarch64--
precision_mode=force.fp16"</td><td>设置单算子模型转换
高级选项。
若模型编译环境的操
作系统及其架构与模
型运行环境不一致
时,则需使用--
host_env_os和--
host_env_cpu参数设
置模型运行环境的操
作系统类型。如果不
设置,则默认取模型
编译环境的操作系统
架构,即atc所在环境
的操作系统架构。</td></tr><tr><td>HOST_ARCH</td><td>-X86_64:X86_64架构-aarch64:arm64架构示例:HOST_ARCH="aarch64"</td><td>执行机器的架构。
一般在分设场景下配
置该参数。</td></tr><tr><td>TOOLChain</td><td>g++ path: g++工具链路径示例: TOOLChain="/usr/bin/g++"</td><td>c++编译器路径，配置时以g++结尾。一般在分设场景下配置该参数。</td></tr></table>


表 9-12 msOpST 的运行模式


<table><tr><td>模式</td><td>only_gen_without_run</td><td>only_run_without_run</td><td>运行模式</td></tr><tr><td>1</td><td>False</td><td>False</td><td>既生成ST测试代码，又运行ST测试代码。</td></tr><tr><td>2</td><td>True</td><td>True/False</td><td>只生成ST测试代码，不运行ST测试代码。</td></tr><tr><td>3</td><td>False</td><td>True</td><td>不生成ST测试代码，只运行ST测试代码。</td></tr></table>

# 命令行执行示例：

不启用msOpST工具的高级功能，执行如下命令生成ST测试用例并执行。 

```batch
msopst run -i xx/Add(case_timestamp.json -soc{soc version} -out ./output 
```

启动msOpST工具的高级功能，仅生成ST测试用例，用户修改ST测试用例 后，再执行ST测试用例。 

i. 执行命令，编辑msopst.ini文件 

vim ${INSTALL_DIR}/python/site-packages/bin/msopst.ini 

${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。若安装的 Ascend-cann-toolkit软件包，以root安装举例，则安装后文件存储路 为：/usr/local/Ascend/ascend-toolkit/latest。 

将msOpST工具的运行模式修改为模式2，按照表9-12修改 

“only_gen_without_run”和“only_run_without_gen”参数的取值。 只生成ST测试代码，不运行ST测试代码。 

ii. 执行如下命令生成ST测试源码。 

msopst run -i xx/Add_case_timestamp.json -soc{soc version} -out ./output -conf xx/ msopst.ini 

-conf参数请修改为msopst.ini配置文件的实际路径。 

ST测试用例生成后，用户可根据需要自行修改ST测试用例代码。 

iii. 修改msopst.ini文件，修改运行模式为仅执行ST测试用例。 

执行命令，编辑msopst.ini文件 

```txt
vim \(\\)[\(INSTALL_DIR]/python/site-packages/bin/msopst.ini 
```

将msOpST工具的运行模式修改为模式3，按照表9-12修改 

“only_gen_without_run”和“only_run_without_gen”参数的取值。 不生成ST测试代码，只运行ST测试代码。 

iv. 执行如下命令运行已修改的ST测试源码。 

```batch
msopst run -i xx/Add(case_timestamp.json -soc{soc version} -out ./output -conf xx/ msopst.ini 
```

# 步骤4 查看执行结果。

若运行模式为仅生成ST测试用例代码，不执行ST测试用例，会在-out指定的目录 下生成时间戳目录，时间戳目录下将生成以算子的OpType命名的存储测试用例代 码的文件夹，目录结构如下所示： 

![](images/2124a81afa64a1218a294aab4a3f31020e6c0e8ba3ece8ffcbd7d8d27af0abed.jpg)


若运行模式为既生成ST测试代码，又运行ST测试代码，命令执行完成后，会屏显 打印测试用例执行结果，并会在-out指定的目录下生成时间戳目录，时间戳目录 下将生成以算子的OpType命名的存储测试用例及测试结果的文件夹，目录结构如 下所示： 

![](images/dba156399a4adeb23072f87edc7b0fdaef41a4120cf68eea41e0d11dbacdc6a3.jpg)


```txt
src CMakeLists.txt //编译规则文件 common.cpp //公共函数，读取二进制文件函数的实现文件 main.cpp //初始化算子测试用例并执行用例 op_execute.cpp //针对单算子调用的AscendCL接口进行了封装 op Runner.cpp //加载单算子模型文件进行执行的接口进行了封装 op_test.cpp //定义了算子的测试类 op_test_desc.cpp //对算子测试用例信息的加载和读入 testcase.cpp //测试用例的定义文件 st_report.json //运行报表 
```

命令运行成功后会生成报表st_report.json，保存在“The st_report saved in”路 径下，记录了测试的信息以及各阶段运行情况。 

同时，st_report.json报表可以对比测试结果，如果用户运行出问题，也可基于报 表查询运行信息，以便问题定位。 


表 9-13 st_report.json 报表主要字段及含义


<table><tr><td colspan="3">字段</td><td>说明</td></tr><tr><td>run_cmd</td><td>-</td><td>-</td><td>命令行命令。</td></tr><tr><td rowspan="7">report_list</td><td>-</td><td>-</td><td>报告列表,该列表中可包含多个测试用例的报告。</td></tr><tr><td rowspan="3">trace_detail</td><td>-</td><td>运行细节。</td></tr><tr><td>st(case_info</td><td>测试信息,包含如下内容。- expect_data_path:期望计算结果路径。- case_name:测试用例名称。- input_data_path:输入数据路径。- planned_output_data Paths:实际计算结果输出路径。- op.params:算子参数信息。</td></tr><tr><td>stage_result</td><td>运行各阶段结果信息,包含如下内容。- status:阶段运行状态,表示运行成功或者失败。- result:输出结果-stage_name:阶段名称。- cmd:运行命令。</td></tr><tr><td>case_name</td><td>-</td><td>测试名称。</td></tr><tr><td>status</td><td>-</td><td>测试结果状态,表示运行成功或者失败。</td></tr><tr><td>expect</td><td>-</td><td>期望的测试结果状态,表示期望运行成功或者失败。</td></tr><tr><td rowspan="4">summary</td><td>-</td><td>-</td><td>统计测试用例的结果状态与期望结果状态对比的结果。</td></tr><tr><td>test case count</td><td>-</td><td>测试用例的个数。</td></tr><tr><td>success count</td><td>-</td><td>测试用例的结果状态与期望结果状态一致的个数。</td></tr><tr><td>failed count</td><td>-</td><td>测试用例的结果状态与期望结果状态不一致的个数。</td></tr></table>

----结束 

# 开发环境和运行环境分设场景

步骤1 根据运行环境的架构在开发环境上搭建环境。 

1. 请参见2 环境准备，根据运行环境架构安装对应的CANN开发套件包（开发环境和 运行环境架构相同时，无需重复安装CANN开发套件包）。 

2. ST测试用例执行时，会使用AscendCL接口加载单算子模型文件并执行，需要在开 发环境上根据运行环境的架构配置AscendCL应用编译所需其他环境变量。 

当开发环境和运行环境架构相同时，环境变量如下所示。 

```shell
export DDK_PATH=\$\{INSTALL_DIR\}
export NPU_HOST_lib=\$\{INSTALL_DIR\}/\{arch-os\}/devlib 
```

当开发环境和运行环境架构不同时，环境变量如下所示。 

```javascript
export DDK_PATH=\({INSTALL_DIR}/\{arch-os\}
export NPU_HOST_lib=\({INSTALL_DIR}/\{arch-os\}/devlib 
```

# 说明

– ${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。若安装的Ascend-canntoolkit软件包，以root安装举例，则安装后文件存储路径为：/usr/local/Ascend/ ascend-toolkit/latest。 

– {arch-os}中arch表示操作系统架构（需根据运行环境的架构选择），os表示操作系统 （需根据运行环境的操作系统选择）。 

步骤2 在开发环境启动msOpST工具的高级功能，仅生成ST测试用例。 

1. 执行命令，编辑msopst.ini文件。 

vim ${INSTALL_DIR}/python/site-packages/bin/msopst.ini 

${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。若安装的Ascendcann-toolkit软件包，以root安装举例，则安装后文件存储路径为：/usr/local/ Ascend/ascend-toolkit/latest。 

2. 将msOpST工具运行模式修改为模式2，按照表9-12修改 

“only_gen_without_run”和“only_run_without_gen”参数的取值。只生成ST 测试代码，不运行ST测试代码。 

3. 若开发环境和运行环境架构不同，按照表9-11修改“HOST_ARCH”和 

“TOOL_CHAIN”参数的取值。 

4. 执行如下命令生成ST测试源码。 

msopst run -i {**json} -soc{soc version} -out {outputpath} -conf xx/msopst.ini 

-conf参数请修改为msopst.ini配置文件的实际路径。ST测试用例生成后，用户可 根据需要自行修改ST测试用例代码。 

5. 执行完成后，将在{output path}下生成ST测试用例，并使用g++编译器生成可执 行文件main。同时，屏显信息结果中展示此次一共运行几个用例，测试用例运行 的情况，并生成报表st_report.json，保存在屏显信息中“The st report saved in”所示路径下，报表具体信息请参见表9-13。 

步骤3 请参见2 环境准备，在运行环境上安装CANN软件并配置所需基本环境变量。 

步骤4 执行测试用例。 

1. 将开发环境的算子工程目录的run目录下的out文件夹拷贝至运行环境任一目录， 例如上传到/home/HwHiAiUser/Ascend_project/run_add/目录下。 

2. 在运行环境中执行out文件夹下的可执行文件。 

进入out文件夹所在目录，执行如下命令： 

chmod $+\mathrm{x}$ main ./main 

步骤5 查看运行结果。 

执行完成后，屏显信息显示此次用例运行的情况，如图9-2所示。 


图 9-2 运行结果


![](images/a55714b6b5b700a2758750991e02861d7fef03c59c666062d5768ca1471d6a5c.jpg)


----结束 

# 9.1.3.4 测试用例定义文件配置样例

Less算子的测试用例定义文件“Less_case.json”如下所示。 

```json
{
    "case_name": "Test_Less_001", //测试用例名称
    "op": "Less", //算子的类型
    "input_desc": [ //算子输入描述
        { //第一个输入
            "format": ["ND"], "type": ["int32", "float"], "shape": [12,32],
            "data_distribution": [ //生成测试数据时选择的分布方式 "uniform"
            ],
            "value_range": [ //输入数据的取值范围
                [ 1.0,
684.0
            ]
        }
    }, //第二个输入
    "format": ["ND"], "type": ["int32", "float"]
    "shape": [12,32],
    "data_distribution": [ "uniform"]
    ],
    "value_range": [ 
        1.0,
384.0 
```

```jsonl
] ] } ], "output_desc": [ //算子的输出 { "format": ["ND"], "type": ["bool","bool"], "shape": [12,32] } ] }， { "case_name": "Test_Less_002", "op": "Less", "input_desc": [ { ... }， { ... } ] , "output_desc": [ { ... } ] } 
```

若算子包含属性，测试用例定义文件如下所示。 

```json
{
"case_name":"Test_Conv2D_001", //测试用例名称
"op":"Conv2D", //算子的Type，唯一
"input_desc": [ //算子的输入描述
{ //算子的第一个输入
"format": [ //用户在此处配置待测试的输入Tensor的排布格式
"ND",
"NCHW"
],
"type": [ //输入数据支持的数据类型
"float",
"float16"
],
"shape": [8,512,7,7], //输入Tensor的shape，用户需要自行修改
"data_distribution": [ //生成测试数据时选择的分布方式
"uniform"
],
"value_range": [ //输入数据值的取值范围
[ 0.1,
200000.0 ]
]
},
{
//算子的第二个输入
"format": [ "ND",
"NCHW"
],
"type": [ "float",
"float16"
],
"shape": [512,512,3,3],
"data_distribution": [ 
```

```txt
"uniform"
],
"value_range": [
0.1,
200000.0
]
]
},
"output_desc": [ //必选，含义同输入Tensor描述
{
"format": [
ND",
"NCHW"
],
"type": [
float",
float16"
]
]
},
"attr": [ //算子的属性
{
"name": "strides", //属性的名称
"type": "list_int", //属性的支持的类型
'value': [1,1,1,1] //属性值，跟type的类型对应
},
{
"name": "pads", //属性的名称
"type": "list_int", //属性的支持的类型
'value': [1,1,1,1] //属性值，跟type的类型对应
}
{
"name": "dilations", //属性的名称
[type]: "list_int", //属性支持的类型
'value': [1,1,1,1] //属性值，跟type的类型对应
}
}
] 
```

● 若指定固定输入，例如ReduceSum的axes参数，测试用例定义文件如下所示。 

```json
{
"case_name": "Test_ReduceSum_001",
"op": "ReduceSum",
"input_desc": [format]: ["ND"]
type: ["int32"], //若需要设置value,则每个用例只能测试一种数据类型
"shape": [3,6,3,4],
"data_distribution": [uniform],
value_range": [ -384, 384 ]
] 
```

```json
]， "value_range":[ -3, 1 ] ], "value":[0,2] //设置具体值，需要与shape对应 } ], "output_desc":[ { "format": ["ND"], "type": ["int32"], "shape": [6,4] } ], "attr":[ { "name":"keep_dims", "type":"bool", "value":false } ] } 
```

若算子属性的type为类型，测试用例定义文件如下所示。 

```json
{
    "case_name": "Test_ArgMin_001",
    "op": "ArgMin",
    "input_desc": [
        {
            ...
        },
    {
        ...
        }
    ],
    "output_desc": [
        {
            ...
        }
    ],
    "attr": [
        {
            "name":"dtype",
            "type":"data_type",
            "value":"int64"
        ]
    ]
} 
```

若算子的输入个数不确定（动态多输入场景）。 以AddN算子为例，属性“N”的取值为3，则需要配置3个输入描述，name分别 为x0、x1、x2，即输入个数需要与属性“N”的取值匹配。 

```json
{
    "op": "AddN",
    "input_desc": [
        "name": "x0",
        "format": "NCHW",
        "shape": [1,3,166,166],
        "type": "float32"
    ],
} 
```

```jsonl
"name":"x1", "format": "NCHW", "shape": [1,3,166,166], "type": "int32" }, { "name":"x2" "format": "NCHW", "shape": [1,3,166,166], "type": "float32", } ], "output_desc": [ {"format": "NCHW", "shape": [1,3,166,166], "type": "float32" } ], "attr": [ {"name": "N", "type": "int", "value": 3} ] } 
```

若算子的某个输入为常量，测试用例定义文件如下所示。 

```json
{ "case_name":"Test_OptType_007", "op":"OpType", "input_desc":[ { "format": ["ND"], "type": ["int32"], "shape": [1], "is_const":true, //标识此输入为常量 "data_distribution": [ "uniform" ], "value":[11], //常量的值 "value_range":[ //min_value与max_value都配置为常量的值 [ 11, 11 ] ] }， { ... } }, "output_desc":[ { ... } ] 
```

若算子的输入输出类型为复数，测试用例定义文件如下所示。 

```json
[ 
{ 
    "case_name": "Test_ReducSum_001", 
    "op": "ReduceSum", 
    "input_desc": [ 
        "name": "name", 
        "value": "value", 
        "class_name": "class", 
        "class_value": "value", 
        "class_op": "op", 
        "class_op_value": "op", 
        "class_op_value_op": "op", 
        "class_op_value_opValue": "opValue", 
        "class_op_value_opValueValue": "opValueValue", 
        "class_op_value_opValueValueValue": "opValueValueValue", 
        "class_op_value_opValueValueValueValue": "opValueValueValueValue", 
        "class_op_value_opValueValueValueValueValue": "opValueValueValueValueValue", 
        "class_op_value_opValueValueValueValueValueValue": "opValueValueValueValueValue", 
        "class_op_value_opValueValueValueValueValueValue": "opValueValueValueValueValue", 
        "class_op_value_opValueValueValueValueValueValue": "opValueValueValueValueValue", 
        "class_op_value_opValueValueValueValueValueValue": "opValueValueValueValueValue", 
        "class_op_value_opValueValueValueValueValueValue": "opValueValueValueValuable", 
        "class_op_value_opValuableValuable": "opValuableValuable", 
        "class_op_value_opValuableValuableValuable": "opValuableValuable", 
        "class_op_value_opValuableValuableValuableValuable": "opValuableValuableValuable", 
        "class_op_value_opValuableValuableValuableValuableValuable": "opValuableValuableValuableValuable", 
        "class_op_value_opValuableValuableValuableValuableValuable": "opValuableValuableValuableValuable", 
        "class_op_value_opValuableValuableValuableValuableValuable": "opValuableValuableValuableValuable", 
        "class_op_value_opValuableValuableValuableValuableValuable": "opValuableValuableValuableValuable", 
        "class_op-value-op-1": "op-1", 
        "class-oper-1": "oper-1", 
        "class-oper-2": "oper-2", 
        "class-oper-3": "oper-3", 
        "class-oper-4": "oper-4", 
        "class-oper-5": "oper-5", 
        "class-oper-6": "oper-6", 
        "class-oper-7": "oper-7", 
        "class-oper-8": "oper-8", 
        "class-oper-9": "oper-9", 
        "class-oper-10": "oper-10", 
        "class-oper-11": "oper-11", 
        "class-oper-12": "oper-12", 
        "class-oper-13": "oper-13", 
        "class-oper-14": "oper-14", 
        "class-oper-15": "oper-15", 
        "class-oper-16": "oper-16", 
        "class-oper-17": "oper-17", 
        "class-oper-18": "oper-18", 
        "class-oper-19": "oper-19", 
        "class-oper-20": "oper-20", 
        "class-oper-21": "oper-21", 
        "class-oper-22": "oper-22", 
        "class-oper-23": "oper-23", 
        "class-oper-24": "oper-24", 
        "class-oper-25": "oper-25", 
        "class-oper-26": "oper-26", 
        "class-oper-27": "oper-27", 
        "class-oper-28": "oper-28", 
        "class-oper-29": "oper-29", 
        "class-oper-30": "oper-30", 
        "class-oper-31": "oper-31", 
        "class-oper-32": "oper-32", 
        "class-oper-33": "oper-33", 
        "class-oper-34": "oper-34", 
        "class-oper-35": "oper-35", 
        "class-oper-36": "oper-36", 
        "class-oper-37": "oper-37", 
        “class-oper-38”: “oper-38”, 
        “class-oper-39”: “oper-39”, 
        “class-oper-40”: “oper-40”, 
        “class-oper-41”: “oper-41”, 
        “class-oper-42”: “oper-42”, 
        “class-oper-43”: “oper-43”, 
        “class-oper-44”: “oper-44”, 
        “class-oper-45”: “oper-45”, 
        “class-oper-46”: “oper-46”, 
        “class-oper-47”: “oper-47”, 
        “class-oper-48”: “oper-48”, 
        “class-oper-49”: “oper-49”, 
        “class-oper-50”: “oper-50”, 
        “class-oper-51”: “oper-51”, 
        “class-oper-52”: “oper-52”, 
        “class-oper-53”: “oper-53”, 
        “class-oper-54”: “oper-54”, 
        “class-oper-55”: “oper-55”, 
        “class-oper-56”: “oper-56”, 
        “class-oper-57”: “oper-57”, 
        “class-oper-58”: “oper-58”, 
        “class-oper-59”: “oper-59”, 
        “class-oper-60”: “oper-60”, 
        “class-oper-61”: “oper-61”, 
        “class-oper-62”: “oper-62”, 
        “class-oper-63”: “oper-63”, 
        “class-oper-64”: “oper-64”, 
        “class-oper-65”: “oper-65”, 
        “class-oper-66”: “oper-66”, 
        “class-oper-67”: “oper-67”, 
        “class-oper-68”: “oper-68”, 
        “class-oper-69”: “oper-69”, 
        “class-oper-70”: “oper-70”, 
        “class-oper-71”: “oper-71”, 
        “class-oper-72”: “oper-72”, 
        “class-oper-73”: “oper-73”, 
        “class-oper-74”: “oper-74”, 
        “class-oper-75”: “oper-75”, 
        “class-oper-76”: “oper-76”, 
        “class-oper-77”: “oper-77”, 
        “class-oper-78”: “oper-78”, 
        “class-oper-79”: “oper-79”, 
        “class-oper-80”: “oper-80”, 
        “class-oper-81”: “oper-81”, 
        “class-oper-82”: “oper-82”, 
        “class-oper-83”: “oper-83”, 
        “class-oper-84”: “oper-84”, 
        “class-oper-85”: “oper-85”, 
        “class-oper-86”: “oper-86”, 
        “class-oper-87”: “oper 87”， 
```

```json
{
    "format": ["ND"]
    "type": [
        "complex64", //输入类型为复数
        "complex128" //输入类型为复数
    ],
    "shape": [3,6],
    "data_distribution": [
        "uniform"
    ],
    "value_range": [ //实部取值范围
        [ 1, 10 ]
    ]
},
{
    "format": ["ND"]
    "type": [
        "int32",
        "int64",
    ],
    "shape": [1],
    "data_distribution": [
        "uniform"
    ],
    "value_range": [
        [ 1, 1]
    ]
}
},
"output_desc": [
    "format": ["ND"]
    "type": [
        "complex64", //输入类型为复数
        "complex128" //输入类型为复数
    ],
    "shape": [3]
}
],
"attr": [
    "name":"keep_dims",
    "type":"bool",
    "value":false
] 
```