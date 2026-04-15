<!-- Source: 算子开发指南.md lines 7435-13546 | Section: 2.10 附录 -->

# 2.10 附录

# 2.10.1 C++标准支持

# 2.10.1.1 概述

Host侧与clang15一致，支持完整的 ${ \mathsf { C } } / { \mathsf { C } } + +$ 标准。 

Device侧，默认支持 $\mathsf { C } + + 1 1$ 标准，支持指定 $C { + } { + } 1 4$ 、 $\mathsf { C } { + } { + } 1 7$ 、 $\mathsf { C } + + 2 0$ 。由于硬件限制， 部分 $\mathsf { C } { + + }$ 运行时能力无法支持。 

# 2.10.1.2 C/C++语法限制

# 2.10.1.2.1 特性

不支持虚函数 

不支持虚继承 

不支持运行时递归 

不支持动态malloc、new/free 

不支持STL 

不支持运行时typeid 

不支持文件系统IO 

● 不支持标准库下的tuple及算法类运算（相关库函数调用需要标记aicore） 

# 2.10.1.2.2 函数

__simt_vf__标记的SIMT VF函数需要遵循以下约束和限制： 

标量参数不允许使用指针和引用。 

不允许使用数组作为参数，以下为错误示例。 

```c
_simt_vf __launch_bounds_(1024) inline void foo(_gm__int\* a, _gm__int\* b, _gm__int\* c, int\* array) { int idx = blockIdx \* blockDim.x + threadIdx.x; // error: 不允许使用数组array a[ idx] = b[ idx] + c[ idx] + array[0]; } global __aicore__void foo(_gm__int\* a, _gm__int\* b, _gm__int\* c) { int array[5] = {0,1,2,3,4}; asc_vf_call<foo>(dim3{256}, a, b, c, array); } 
```

如果传参中出现多级指针，不允许使用内层栈地址指针访问，以下为错误示例。 

__simt_vf___launch_bounds_(1024) inline void foo(_gm__int\* a, _gm__int\* b, _gm__int\* c, __ubuf__uint64_t\*s) { int idx = blockIdx\*blockDim.x + threadIdx.x; int\* stack $=$ (int\*)(s[0]); //error:*stack表示从多级指针中读取，不允许使用 a[idx] $=$ b[idx] $^+$ c[idx] $^+$ \*stack;   
} global __aicore__void foo(_gm__int\* a, _gm__int\* b, _gm__int\*c){ int stack $= 0$ . __ubuf__uint64_t\*s $= \ldots$ .. s[0] $=$ &stack; asc_vf_call<foo>(dim3{256},a,b,c,s); 

不支持通过函数指针进行间接调用，被调用的__simt_vf__函数需要在编译期确 定。 

函数的inline行为由编译器决定，添加的always_inline或noinline将被忽略。 

不允许使用结构体作为参数，以下为错误示例。 

```c
__simt_vf____launch_bounds_(1024) inline void foo(_gm__int* a, _gm__int* b, _gm__int* c, struct S s) {
    // error: s表示结构体参数，不允许使用
} 
```

# 2.10.2 工程化算子开发

# 2.10.2.1 概述

工程化算子开发是指基于自动生成的自定义算子工程完成算子实现、编译部署、单算 子调用代码自动生成等一系列流程。 

该开发流程是标准的开发流程，建议开发者按照该流程进行算子开发。该方式下，算 子开发的代码会更规范、统一、易于维护；同时该方式考虑了单算子API调用、算子入 图、AI框架调用等功能的集成，使得开发者易于借助CANN框架实现上述功能。 

工程化算子开发流程如下图所示： 

![](images/a81b35266f23b89863f85bd7ead27b1f184565d2f8547322ecc4cf666ba32f68.jpg)


步骤1 环境准备。 

1. CANN软件安装请参考1.2 环境准备。 

2. 创建算子工程。使用msOpGen工具创建算子开发工程。 

步骤2 算子实现。 

算子原型定义。通过原型定义来描述算子输入输出、属性等信息以及算子在AI处 理器上相关实现信息，并关联tiling实现等函数。 

Kernel侧算子实现和host侧tiling实现请参考3.3 SIMD算子实现；工程化算子开 发，支持开发者调用Tiling API基于CANN提供的编程框架进行tiling开发，kernel 侧也提供对应的接口方便开发者获取tiling参数，具体内容请参考2.10.2.4 Kernel 侧算子实现和2.10.2.5 Host侧Tiling实现，由此而带来的额外约束也在上述章节 说明。 

步骤3 编译部署。通过工程编译脚本完成算子的编译部署，分为算子包编译和算子动态库编 译两种方式。 

步骤4 单算子API调用：调用单算子API接口，基于C语言的API执行算子。 

----结束 

# 2.10.2.2 创建算子工程

CANN开发套件包中提供了自定义算子工程生成工具msOpGen，可基于算子原型定义 输出算子工程：包括算子host侧代码实现文件、算子kernel侧实现文件以及工程编译 配置文件等。 

# 说明

使用msOpGen工具创建算子工程之前，需要参考1.2 环境准备章节安装驱动固件和CANN软件 包，完成开发环境和运行环境的准备。 

使用msOpGen工具创建算子开发工程的步骤如下： 

步骤1 编写算子的原型定义json文件，用于生成算子开发工程。json文件的配置参数详细说明 请参考表1。 

例如，AddCustom算子的json文件命名为add_custom.json，文件内容如下： 

```json
{
    "op": "AddCustom",
    "input_desc": [
        {
            "name": "x",
            "param_type": "required",
            "format": [
                "ND",
                "ND",
                "ND"
            ],
            "type": [
                "float16",
                "float",
                "int32"
            ]
        },
    {
        "name": "y",
        "param_type": "required",
        "format": [
            "ND",
            "ND",
            "ND"
        ],
            "type": [
                "float16",
                "float",
                "int32"
            ]
    }
},
"output_desc": [
        {
            "name": "z",
            "param_type": "required",
            "format": [
                "ND",
                "ND",
                "ND"
            ]
        ],
            "type": [
                "float16",
                "float",
                "int32"
            ]
    }
} 
```

例如，ReduceMaxCustom算子（包含属性）的json文件命名为 reduce_max_custom.json，文件内容如下： 

```json
{
    "op": "ReduceMaxCustom",
    "input_desc": [
        "name": "x",
        "param_type": "required",
        "format": ["ND],
        "type": ["float16"]
    ]
} 
```

```jsonl
} ], "output_desc": [ { "name": "y", "param_type": "required", "format": ["ND"], "type": ["float16"] } , { "name": "idx", "param_type": "required", "format": ["ND"], "type": ["int32"] } ], "attr": [ { "name": "reduceDim", "param_type": "required", "type": "int" } , { "name": "isKeepDim", "param_type": "optional", "type": "int", "default_value": 1 } ] } 
```

# 说明

原型定义json文件中的算子类型字段op需要采用大驼峰的命名方式，即采用大写字符区分不同的 语义。 

步骤2 使用msOpGen工具生成算子的开发工程。以生成AddCustom的算子工程为例，下文仅 针对关键参数进行解释，详细参数说明请参见算子工程创建（msOpGen）。 

```shell
{$INSTALL_DIR}/python/site-packages/bin/msopgen gen -i $HOME/sample/add_custom.json -c ai_core-
<soc_version> -lan cpp -out $HOME/sample/AddCustom 
```

${INSTALL_DIR}为CANN软件安装后文件存储路径，请根据实际环境进行替换。 

-i：指定算子原型定义文件add custom.json所在路径，请根据实际情况修改。 

-c：ai_core-<soc version>代表算子在AI Core上执行，<soc version>为AI处理器 的型号。 

# 说明

AI处理器的型号<soc version>请通过如下方式获取： 

– 针对如下产品：在安装AI处理器的服务器执行npu-smi info命令进行查询，获取Name 信息。实际配置值为AscendName，例如Name取值为xxxyy，实际配置值为 Ascendxxxyy。 

Atlas A2 训练系列产品/Atlas A2 推理系列产品 

Atlas 200I/500 A2 推理产品 

Atlas 推理系列产品 

Atlas 训练系列产品 

针对如下产品，在安装AI处理器的服务器执行npu-smi info -t board -i id -c chip id命 令进行查询，获取Chip Name和NPU Name信息，实际配置值为Chip Name_NPU Name。例如Chip Name取值为Ascendxxx，NPU Name取值为1234，实际配置值为 Ascendxxx 1234。其中： 

id：设备id，通过npu-smi info -l命令查出的NPU ID即为设备id。 

chip_id：芯片id，通过npu-smi info -m命令查出的Chip ID即为芯片id。 

Atlas 350 加速卡 

Atlas A3 训练系列产品/Atlas A3 推理系列产品 

基于同系列的AI处理器型号创建的算子工程，其基础功能（基于该工程进行算子开发、编 译和部署）通用。 

● -lan： 参数cpp代表算子基于Ascend C编程框架，使用 $\mathsf { C } / \mathsf { C } + +$ 编程语言开发。 

-out：生成文件所在路径，可配置为绝对路径或者相对路径，并且工具执行用户 对路径具有可读写权限。若不配置，则默认生成在执行命令的当前路径。 

步骤3 命令执行完后，会在-out指定目录或者默认路径下生成算子工程目录，工程中包含算 子实现的模板文件，编译脚本等，以AddCustom算子为例，目录结构如下所示： 

![](images/cecb85d3dfe063bf7348892def46a1e0780e40bf18bd8ba1235f858a82e3afb7.jpg)


# 说明

● 上述目录结构中的粗体文件为后续算子开发过程中需要修改的文件，其他文件无需修改。 

● kernel侧实现依赖的所有文件需全部放置在op_kernel目录下，不遵循该约束会导致源码发布 场景在线编译失败。因为在后续的算子源码发布时，只会打包发布op_kernel目录下的文件。 

# ----结束

工程目录中的op_kernel和op_host包含了算子的核心实现文件。op_kernel下存放 kernel侧算子实现。op_host下存放host侧代码实现，包括算子原型定义、host侧 tiling实现。其中kernel侧算子实现和host侧tiling实现在3.3 SIMD算子实现章节已经 介绍了其核心的实现方法，在该章节会侧重于介绍接入CANN框架后的编程模式和API 的使用。工程目录中的CMakePresets.json，用于开发者完成工程编译相关配置，之后 即可进行编译部署。 

# 2.10.2.3 算子原型定义

算子原型主要描述了算子的输入输出、属性等信息以及算子在AI处理器上相关实现信 息，并关联tiling实现等函数。算子原型通过自定义的算子类来承载，该算子类继承自 OpDef类。完成算子的原型定义等操作后，需要调用OP_ADD接口，传入算子类型 （自定义算子类的类名），进行算子原型注册。下面是一个简单的Add算子原型定义 和注册的例子。 

```cpp
namespace ops {
class AddCustom : public OpDef {
public:
AddCustom(const char* name) : OpDef(name)
{
    this->Input("x")
    .ParamType(REQUIRED)
    .DataType({ge::DT_FLOAT16, ge::DT_FLOAT, ge::DT_INT32})
    .Format({ge::FORMAT_ND, ge::FORMAT_ND, ge::FORMAT_ND});
    this->Input("y")
    .ParamType(REQUIRED)
    .DataType({ge::DT_FLOAT16, ge::DT_FLOAT, ge::DT_INT32})
    .Format({ge::FORMAT_ND, ge::FORMAT_ND, ge::FORMAT_ND});
    this->Output("z")
    .ParamType(REQUIRED)
    .DataType({ge::DT_FLOAT16, ge::DT_FLOAT, ge::DT_INT32})
    .Format({ge::FORMAT_ND, ge::FORMAT_ND, ge::FORMAT_ND});
    // 如下的shape/datatype推导函数仅在算子入图场景使用
    this->SetInferShape(ge::InferShape);
    this->SetInferDataType(ge::InferDataType);
    this->AlCore()
    .SetTiling(optiling::TilingFunc);
    // 请替换为实际的昇腾AI处理器型号
    this->AlCore().AddConfig("ascendxxx");
}
};
OP_ADD(AddCustom);
} // namespace ops 
```

# 说明

● 基于算子原型定义，自定义算子工程可以实现如下自动化能力： 

自动生成单算子API调用的实现和接口，开发者可以直接使用生成的API实现单算子调 用。 

自动生成图模式场景使用的算子原型定义REG_OP，开发者可以使用生成的算子原型进 行构图、图编译、图执行等操作。 

● 注册算子类型后，框架会根据算子类型获取算子注册信息，同时在编译和运行时按照一定的 规则匹配算子实现文件名称和kernel侧核函数名称。为了保证正确匹配，算子类型、算子实 现文件名称和核函数名称需要遵循如下定义规则。通常情况下，开发者只需要保证创建算子 工程时原型定义json文件中算子类型op的参数值为大驼峰命名方式即可，工程创建后自动生 成的代码即满足该规则。在手动编写算子原型定义和算子实现文件时需要按照如下规则定 义。 

算子类型需要采用大驼峰的命名方式，即采用大写字符区分不同的语义。 

算子实现文件名称、核函数名称需相同，均为算子类型转换为下划线命名方式后的值。 下文描述了通过算子类型转换成算子实现文件名称和核函数名称的过程： 

首字符的大写字符转换为小写字符。例如：Abc $- >$ abc。 

大写字符的前一个字符为小写字符或数字，则在大写字符前插一个下划线“_”， 并将该字符转换为小写字符。例如：AbcDef $- >$ abc_def。 

大写字符前一个字符为大写字符且后一个字符是小写字符，则在大写字符前插一 个下划线“_”，并将该字符转换为小写字符。例如：AbcAAc $^ { - > }$ abc_a_ac。 

其他大写字符转换为小写字符，小写字符保持不变。 

# 算子输入/输出/属性定义

算子原型定义描述了算子的输入输出、属性等信息。输入输出支持的datatype、 format格式的数量需要一致，并保持一一对应的关系。 

如下的代码片段呈现了Add算子输入x的描述信息。 

```cpp
this->Input("x") .ParamType(REQUIRED) .DataType({ge::DT_FLOAT16, ge::DT_FLOAT, ge::DT_INT32}) .Format({ge::FORMAT_ND, ge::FORMAT_ND, ge::FORMAT_ND}); 
```


表 2-36 输入输出参数说明


<table><tr><td>原型定义</td><td>参数</td><td>具体描述</td></tr><tr><td rowspan="3">Input/Output</td><td>ParamType</td><td>参数类型，Option取值为：OPTIONAL（可选）、REQUIRED（必选）、DYNAMIC（动态输入）。
·类似于上文中的Add样例，其输入输出是必选的。
·有些算子的输入或者输出个数是动态的，例如AddN，将N个输入Tensor累加到一起，输出一个Tensor；SplitV，将一个Tensor在某个轴上，拆分为N个Tensor输出。
·有些算子的输入/输出是可选的，例如BatchNorm算子，在训练的时候没有均值和方差输入，在推理的时候有均值和方差的输入。</td></tr><tr><td>DataType</td><td>算子输入输出支持的datatype。datatype的取值请参考DataType。</td></tr><tr><td>Format</td><td>算子输入输出支持的format。format的取值请参考Format。</td></tr></table>

从上文的原型定义中可以看出，列出了输入输出所有datatype和format的组合，保持 对应。使用如下接口，可以达到简化这种代码逻辑的目的。 

在指定输入/输出的datatype信息时，如果某个输入/输出的datatype支持和其他 所有输入/输出的datatype/format组合使用，其datatype可以通过DataTypeList来 表达；在指定输入/输出的format信息时，如果某个输入/输出的format支持和其 他所有输入/输出的datatype/format组合使用，其format可以通过FormatList来 表达。示例如下，以下两种代码表达含义相同。 

```cpp
// 列出所有一一对应的组合  
class XxxCustom : public OpDef {  
public:  
XxxCustom(const char* name) : OpDef(name)  
{  
    this->Input("x")  
    .ParamType(REQUIRED)  
    .DataType({ge::DT_FLOAT16, ge::DT_FLOAT16, ge::DT_FLOAT16})  
    .Format({ge::FORMAT_ND, ge::FORMAT_ND, ge::FORMAT_ND});  
    this->Input("y")  
    .ParamType(REQUIRED)  
    .DataType({ge::DT_FLOAT16, ge::DT_FLOAT, ge::DT_INT32})  
    .Format({ge::FORMAT_ND, ge::FORMAT_ND, ge::FORMAT_ND});  
    this->Output("z")  
    .ParamType(REQUIRED)  
    .DataType({ge::DT_FLOAT16, ge::DT_FLOAT, ge::DT_INT32}) 
```

```cpp
. Format({ge::FORMAT_ND, ge::FORMAT_ND, ge::FORMAT_ND});   
}   
};   
// 通过DataTypeList和FormatList来表达，无需重复列出   
class XxxCustom : public OpDef {   
public: XxxCustom(const char* name) : OpDef(name)   
{ this->Input("x") . ParamType(REQUIRED) . DataTypeList({ge::DT_FLOAT16}) . FormatList({ge::FORMAT_ND}); this->Input("y") . ParamType(REQUIRED) . DataType({ge::DT_FLOAT16, ge::DT_FLOAT, ge::DT_INT32}) . Format({ge::FORMAT_ND, ge::FORMAT_ND, ge::FORMAT_ND}); this->Output("z") . ParamType(REQUIRED) . DataType({ge::DT_FLOAT16, ge::DT_FLOAT, ge::DT_INT32}) . Format({ge::FORMAT_ND, ge::FORMAT_ND, ge::FORMAT_ND});   
}   
}; 
```

通过Follow接口指定当前输入/输出的datatype/format/shape信息与之前定义过 的某个输入一致。示例如下：输出“y1”Follow输入“x1”场景，此时“y1”的 datatype、format以及shape都将会和“x1”保持一致。使用Follow接口指定 shape一致时通常比shape推导函数逻辑更加简单，能用Follow表达的逻辑，建议 使用Follow接口，则无需再编写注册InferShape函数。 

```txt
this->Input("x1") .ParamType(REQUIRED) .DataType({ge::DT_FLOAT, ge::DT_FLOAT}) .Format({ge::FORMAT_ND, ge::FORMAT_ND}); this->Input("x2") .ParamType(REQUIRED) .DataType({ge::DT_FLOAT, ge::DT_FLOAT}) .Format({ge::FORMAT_ND, ge::FORMAT_ND}); this->Output("y1") .ParamType(REQUIRED) .Follow("x1") .OutputShape DependOnCompute(); 
```

原型定义中还包括算子属性信息，如下的代码片段呈现了ReduceMax算子的属性 reduceDim和isKeepDim的描述信息。 

```txt
this->Attr("reduceDim").AttrType(REQUIRED).Int();  
this->Attr("isKeepDim").AttrType(OPTIONAL).Int(1); 
```

具体参数说明如下： 


表2-37 属性参数说明


<table><tr><td>原型定义</td><td>注册方式</td><td>具体描述</td></tr><tr><td>Attr</td><td>AttrType</td><td>设置算子属性类型，取值为：OPTIONAL（可选）、REQUIRED（必选）。</td></tr><tr><td></td><td>Bool/Float/Int...</td><td>设置算子属性数据类型为Bool/Float/Int...。具体说明请参考OpAttrDef。</td></tr></table>

# AI 处理器上相关实现信息

通过AddConfig注册算子支持的AI处理器型号以及相关的配置信息。AddConfig接口原 型如下：soc参数表示AI处理器型号，aicore_config表示其他配置信息。 

```txt
void AddConfig(const char *soc);  
void AddConfig(const char *soc, OpAlCoreConfig &aicore_config); 
```

通过该接口注册AI处理器型号的样例如下，ascendxxx填写规则请参考算子工程目录下 编译配置项文件CMakePresets.json中的ASCEND_COMPUTE_UNIT字段，该字段取值 在使用msOpGen创建工程时自动生成。 

```javascript
this->AlCore().AddConfig("ascendxxx"); 
```

其他AI Core配置信息的配置方式请参考OpAICoreConfig。 

# 注册 Tiling 实现、Shape 推导等函数

通过SetInferShape、SetInferDataType、SetTiling接口来注册对应的Tiling实现和 Shape推导等函数，样例如下。注册的Tiling实现等函数由框架侧进行调用，并在调用 时传入对应的Context上下文，供开发者使用。Tiling函数的实现方法请参考2.10.2.5 Host侧Tiling实现，入图相关的Shape推导等函数实现请参考2.10.3 算子入图（GE 图）开发。 

```cpp
//如下的shape/datatype推导函数仅在算子入图场景使用  
this->SetInferShape(ge::InferShape);  
this->SetInferDataType(ge::InferDataType);  
this->AlCore()  
.SetTiling(optiling::TilingFunc); 
```

# 多硬件平台注册差异化的算子原型

算子类继承基类OpDef，使用Input、Output、Attr等注册算子原型信息，硬件平台支 持相同的算子原型的情况下，直接通过AICore().AddConfig添加支持的AI处理器型号即 可；不同的硬件形态算子原型定义不同的情况，可以通过新增OpAICoreConfig的方 式，针对不同的AI处理器型号注册差异化的算子原型。 

差异化的算子原型生效规则如下： 

对于算子类的输入输出原型信息，OpAICoreConfig未配置的会继承OpDef定义的 原型，比如算子类中定义了输出y，OpAICoreConfig中没有定义输出y， OpAICoreConfig会继承y的原型定义； 

对于算子类和新增OpAICoreConfig中定义的算子原型相同的情况，新增 OpAICoreConfig中定义的算子原型信息会覆盖OpDef定义的原型信息，比如算子 类中定义了输入x支持DT_FLOAT16数据类型，新增OpAICoreConfig中也定义了输 入x，但是支持DT_FLOAT16、DT_BF16数据类型，则以OpAICoreConfig新增定义 为准。 

如下样例中ascendxxx1、ascendxxx2（AI处理器型号）使用相同的算子原型，算子类 通过继承基类OpDef，使用Input、Output、Attr等注册算子原型信息，再通过 

AICore().AddConfig添加支持的AI处理器型号；对于ascendxxx3支持的算子原型需要 定制化处理，新增了DT_BF16的类型，通过新增OpAICoreConfig的方式进行注册，x， y，z的定义会覆盖算子类中对应定义的原型信息。 

```cpp
namespace ops {
class MyAdd : public OpDef {
public:
    MyAdd(const char* name) : OpDef(name)
{
        // ascendxxx1 ascendxxx2 AI处理器型号原型定义
        this->Input("x")
        .ParamType(REQUIRED)
        .DataType({ge::DT_FLOAT16})
        .Format({ge::FORMAT_ND});
        this->Input("y")
        .ParamType(OPTIONAL)
        .DataType({ge::DT_INT64})
        .Format({ge::FORMAT_ND});
        this->Output("z")
        .ParamType(REQUIRED)
        .DataType({ge::DT_FLOAT16})
        .Format({ge::FORMAT_ND});
        this->AlCore()
        .SetTiling(optiling::TilingFunc);
        this->AlCore().AddConfig("ascendingxx1");
        this->AlCore().AddConfig("ascendingxx2");
        // ascendxxx3 AI处理器定义OpAlCoreConfig变量，定制化原型
        OpAlCoreConfig config;
        config.Input("x")
        .ParamType(REQUIRED)
        .DataType({ge::DT_FLOAT16, ge::DT_BF16})
        .Format({ge::FORMAT_ND, ge::FORMAT_ND});
        config.Input("y")
        .ParamType(REQUIRED)
        .DataType({ge::DT_FLOAT16, ge::DT_BF16})
        .Format({ge::FORMAT_ND, ge::FORMAT_ND});
        config.Output("z")
        .ParamType(REQUIRED)
        .DataType({ge::DT_FLOAT16, ge::DT_BF16})
        .Format({ge::FORMAT_ND, ge::FORMAT_ND});
        this->AlCore().AddConfig("ascendingxx3", config);
    }
};
OP_ADD(MyAdd);
} 
```

如下的样例中，只有几个参数原型信息在不同硬件平台不一致，开发者也可以通过 OpAICoreConfig定制部分算子原型信息，复用OpDef定义的其他算子原型信息，达到 部分原型信息硬件平台定制化的目的。 

```cpp
class AddCustom : public OpDef {   
public: AddCustom(const char* name) : OpDef(name) { this->Input("x").DataType({ ge::DT_FLOAT16 }); paramType(OPTIONAL); this->Output("y").DataType({ ge::DT_FLOAT16 }); OpAlCoreConfig aicConfig1; OpAlCoreConfig aicConfig2; aicConfig1.Input("x") .ParamType(OPTIONAL) .DataType({ ge::DT_FLOAT }); .Format({ ge::FORMAT_ND }); aicConfig2.Input("x") .ParamType(REQUIRED) .DataType({ ge::DT_INT32 }); .Format({ ge::FORMAT_ND }); this->AlCore().AddConfig("ascendxxx1", aicConfig1); this->AlCore().AddConfig("ascendxxx2", aicConfig2); 
```

```txt
} 
```

# 2.10.2.4 Kernel 侧算子实现

在2.2.3.2 核函数章节已经介绍了kernel侧算子核心的实现方法，本章节侧重于介绍接 入CANN框架时编程模式和API的使用。 

# 自动生成 kernel 侧算子实现模板

在算子工程目录下的“op_kernel/xxx.cpp”文件中实现算子的核函数。核函数的定义 模板已通过msOpGen工具自动生成，样例如下所示。注意这里参数的顺序按照“输 入、输出、workspace、tiling”的顺序排布，开发者不要调整其顺序。 

```txt
include "kernel_operator.h"   
extern"C" global __aicore void addcustom(GM_ADDR x, GM_ADDR y, GM_ADDR z, GM_ADDR   
workspace, GM_ADDR tiling) { GET_TILING_DATA(tiling_data, tiling);//获取Tiling参数，详见下文介绍 //TODO:user kernel impl   
} 
```

# 说明

```txt
算子原型定义中的输入和输出同名的情况下，自动生成的核函数中，输出参数增加ref后缀予以区分。示例如下：  
extern "C" __global __aicore__ void addCustom(GM_ADDR x, GM_ADDR y, GM_ADDR x_ref, GM_ADDR workspace, GM_ADDR tiling) {  
} 
```

# GET_TILING_DATA 获取 Tiling 参数

提供GET_TILING_DATA，用于获取算子kernel入口函数传入的tiling信息，并填入注册 的Tiling结构体中，此函数会以宏展开的方式进行编译。注意，对应的算子host实现中 需要定义TilingData结构体，实现并注册计算TilingData的Tiling函数。具体请参考 2.10.2.5 Host侧Tiling实现。 

核函数中调用GET_TILING_DATA获取TilingData的样例如下： 

```txt
extern "C" __global __aicore__ void add/custom(GM_ADDR x, GM_ADDR y, GM_ADDR z, GM_ADDR workspace, GM_ADDR tiling)  
{  
    GET_TILING_DATA(tilingData, tiling);  
    KernelAdd op;  
    op.Add(x, y, z, tilingData.length, tilingData.size);  
    if (TILING_KEY_IS(1)) {  
        op.Process();  
    }  
} 
```

# 核函数内获取算子输入输出的数据类型和格式

算子工程在核函数内提供了DTYPE_<Arg>、ORIG_DTYPE_<Arg>、FORMAT_<Arg>三 种宏用于表示核函数入参（算子的输入输出）的数据类型、原始数据类型和数据格 式。其中<Arg>为入参的大写格式。 

DTYPE_<Arg>，入参的数据类型。是指在Device侧实际可使用的数据类型，比如 half、float等。 

ORIG_DTYPE_<Arg>，入参的原始数据类型。是指在Host侧进行原型定义时，指 定的数据类型（不包含命名空间），比如DT_FLOAT16、DT_FLOAT等。 

FORMAT_<Arg>，入参的数据格式。是指在Host侧进行原型定义时，指定的数据 格式（不包含命名空间），比如FORMAT_ND、FORMAT_NZ等。 


样例如下：


```txt
template<class T> func() {}
extern "C" __global __aicore__ void add_custom(GM_ADDR x, GM_ADDR y, GM_ADDR z, GM_ADDR workspace, GM_ADDR tiling)
{
    DTYPE_X temp;
    func<DTYPE_Z>(());
    if (FORMAT_Y == FORMAT_ND) {
        ...
    }
    if (ORIG_DTYPE_Y == DT_FLOAT) {
        ...
    }
} 
```

# 输出 shape 依赖计算的算子 kernel 实现

某些算子，比如NonZero（统计tensor中非零值的个数），计算完成前无法得知算子 输出的shape信息，算子计算完成后才能获取。该类算子在原型定义时，需要使用 OutputShapeDependOnCompute接口进行标识，同时在算子核函数中将实际输出 shape写入到出参中，便于框架侧基于该信息进行输出内存的管理。 

在核函数所有输出的最后增加一个GM_ADDR类型的输出参数，并在核函数计算完成 后，将输出shape信息写入到该出参中。shape信息的排布格式如下，大小为n * (8 + 1)，每个元素的数据类型为uint64_t。其中n表示待刷新shape信息的输出个数，每个 输出的shape信息都通过第1个元素来保存实际的shape维度（dim），后续的8个元素 来保存具体每个维度的shape信息。 

![](images/b2f2613166c9ab05dd07cbc6e3fa6817a87dfac2b44a7fc1d0df37bf56b447c2.jpg)



共n个输出（shape依赖计算的输出）


# 说明

● 输出的顺序和原型定义中输出的顺序保持一致。 

● 对于uint64_t的输出数据类型（对于tensor而言），需要将dim的uint32_t的高位设置为1， 表示以uint64_t类型解析该tensor。 

如下示例中，算子中有一个输出依赖计算得出，输出tensor的数据类型为 uint32_t，计算完成后，得到输出的shape为（32, 64），出参shape_out用于存 放该shape信息，值为（2, 32, 64）。代码示例如下： 

extern "C" __global__ __aicore__ void xxx_custom(GM_ADDR x, GM_ADDR y, GM_ADDR z, GM_ADDR shape_out, GM_ADDR workspace, GM_ADDR tiling) { 

```c
constexpr uint32_t SHAPEOUT_SIZE = 9;
// 输出数据为2维([32, 64]), tensor类型为uint32_t
// shapeoutGlobal_uint32用于存放输出Shape信息，数据类型固定为uint64_t
GlobalTensor<uint64_t> shapeoutGlobal_uint32;
shapeoutGlobal_uint32.SetGlobalBuffer(_gm uint64_t*) shape_out, SHAPEOUT_SIZE);
shapeoutGlobal_uint32SetValue(0, 2); 
```

```javascript
shapeoutGlobal_uint32SetValue(1, 32); shapeoutGlobal_uint32SetValue(2, 64); 
```

如下示例中，算子中有一个输出依赖计算得出，输出tensor的数据类型为 uint64_t，计算完成后，得到输出的shape为（1, 64, 128, 128），出参shape_out 用于存放该shape信息，值为（0x0000000080000000 | 4 , 1, 64, 128, 128）。代 码示例如下： 

```c
extern "C" __global__ __aicore__ void xxx/custom(GM_ADDR x, GM_ADDR y, GM_ADDR z, GM_ADDR shape_out, GM_ADDR workspace, GM_ADDR tiling) {  
    constexpr uint32_t SHAPEOUT_SIZE = 9;  
    // 输出数据为4维([1, 64, 128, 128]), tensor类型为uint64_t  
    // shapeoutGlobal_uint64用于存放输出Shape信息，数据类型固定为uint64_t  
    GlobalTensor<uint64_t> shapeoutGlobal_uint64;  
    shapeoutGlobal_uint64.SetGlobalBuffer((gm uint64_t*)shape_out, SHAPEOUT_SIZE);  
    shapeoutGlobal_uint64SetValue(0, 0x000000008000000 | 4);  
    shapeoutGlobal_uint64SetValue(1, 1);  
    shapeoutGlobal_uint64SetValue(2, 64);  
    shapeoutGlobal_uint64SetValue(3, 128);  
    shapeoutGlobal_uint64SetValue(4, 128);  
} 
```

如下示例中，算子中有两个输出依赖计算得出，输出tensor的数据类型为 uint64_t，计算完成后，得到输出的shape为（16, 32）和 （1, 16, 16, 32），出 参shape_out用于存放该shape信息。示例如下： 

```txt
extern "C" __global__ __aicore__ void xxxcustom(GM_ADDR x, GM_ADDR y, GM_ADDR z, GM_ADDR shape_out, GM_ADDR workspace, GM_ADDR tiling) { 
```

```txt
//有两个输出需要刷新shape，一个维度为2维[16,32]，一个维度为4维[1,16,16,32] //输出tensor类型为uint64_t constexpr uint32_t SHAPEOUT_SIZE_2 = 18; // shapeoutGlobal_uint64_2用于存放输出Shape信息，数据类型固定为uint64_t GlobalTensor<uint64_t> shapeoutGlobal_uint64_2; shapeoutGlobal_uint64_2.SetGlobalBuffer((gm uint64_t*)shape_out, SHAPEOUT_SIZE_2); shapeoutGlobal_uint64_2SetValue(0,0x000000080000000 | 2); shapeoutGlobal_uint64_2SetValue(1,16); shapeoutGlobal_uint64_2SetValue(2,32); // index[3]~index[8]数据为占位 shapeoutGlobal_uint64_2SetValue(9,0x000000080000000 | 4); shapeoutGlobal_uint64_2SetValue(10,1); shapeoutGlobal_uint64_2SetValue(11,16); shapeoutGlobal_uint64_2SetValue(12,16); shapeoutGlobal_uint64_2SetValue(13,32); 
```

# 2.10.2.5 Host 侧 Tiling 实现

# 2.10.2.5.1 基本流程

在3.3 SIMD算子实现章节已经介绍了host侧Tiling核心的实现方法，本章节侧重于介绍 接入CANN框架时编程模式和API的使用。 

大多数情况下，Local Memory的存储，无法完整的容纳算子的输入与输出，需要每次 搬运一部分输入进行计算然后搬出，再搬运下一部分输入进行计算，直到得到完整的 最终结果，这个数据切分、分块计算的过程称之为Tiling。根据算子的shape等信息来 确定数据切分算法相关参数（比如每次搬运的块大小，以及总共循环多少次）的计算 程序，称之为Tiling实现。 

Tiling实现完成后，获取到的Tiling切分算法相关参数，会传递给kernel侧，用于指导 并行数据的切分。由于Tiling实现中完成的均为标量计算，AI Core并不擅长，所以我 们将其独立出来放在host CPU上执行。 


图 2-46 Tiling 实现的输入输出


![](images/e974670cf320fe0aa2b6520fd22b84292963011faa24108f6c4bf2ae0768f58c.jpg)


如上图所示，Tiling实现即为根据算子shape等信息来确定切分算法相关参数的过程， 这里的算子shape等信息可以理解为是Tiling实现的输入，切分算法相关参数可以理解 为是Tiling实现的输出。输入和输出都通过Tiling函数的参数（TilingContext* context 上下文结构）来承载。也就是说，开发者可以从上下文结构中获取算子的输入、输出 以及属性信息，也就是Tiling实现的输入，经过Tiling计算后，获取到TilingData数据 结构（切分算法相关参数）、numBlocks变量、用于选择不同的kernel实现分支的 TilingKey、算子workspace的大小，也就是Tiling实现的输出，并将这些输出设置到上 下文结构中。 

TilingData、numBlocks、TilingKey、workspace这些概念的具体解释如下： 

TilingData：切分算法相关参数，比如每次搬运的块大小，以及总共循环多少 次，通过结构体存储，由开发者自行设计。 

TilingData结构定义支持单结构定义方法，也支持结构体嵌套： 

单结构定义方法，以平铺的形式定义： 

```c
namespace optingilng{   
BEGIN_TILING_DATADEF(MyAddTilingData) //声明tiling结构名字 TILING_DATA_FIELDDEF( uint32_t,field1); //结构成员的类型和名字 TILING_DATA_FIELDDEF( uint32_t, field2); TILING_DATA_FIELDDEF( uint32_t, field3);   
END_TILING_DATADEF;   
REGISTER_TILING_DATA_CLASS( MyAdd, MyAddTilingData) //tiling结构注册给算子   
} 
```

Tiling实现函数中对tiling结构成员赋值的方式如下： 

```txt
MyAddTilingData myTiling;  
myTiling.set_field1(1);  
myTiling.set_field2(2); 
```

支持结构体嵌套： 

```c
namespace optiling{   
BEGIN_TILING_DATADEF(MyStruct1）//声明结构1名字 TILING_DATA_FIELDDEF( uint32_t,field1)； //结构成员的类型和名字 TILING_DATA_FIELDDEF( uint32_t, field2); //结构成员的类型和名字   
END_TILING_DATADEF;   
REGISTER_TILING_DATA_CLASS( MyStruct1Op, MyStruct1) //注册结构体到<op_type>Op   
BEGIN_TILING_DATADEF( MyStruct2）//声明结构2名字 
```

```c
TILING_DATA_FIELD_REF uint32_t, field3); //结构成员的类型和名字  
TILING_DATA_FIELD_REF uint32_t, field4); //结构成员的类型和名字  
END_TILING_DATA_REF;  
REGISTER_TILING_DATA_CLASS (MyStruct2Op, MyStruct2) //注册结构体到<op_type>Op  
BEGIN_TILING_DATA_REF (MyAddTilingData) //声明tiling结构名字  
TILING_DATA_FIELD_REFSTRUCT (MyStruct1, st1); //结构成员的引用结构体  
TILING_DATA_FIELD_REFSTRUCT (MyStruct2, st2); //结构成员的引用结构体  
END_TILING_DATA_REF;  
REGISTER_TILING_DATA_CLASS (MyAdd, MyAddTilingData) //tiling结构注册给算子} 
```

Tiling实现函数中对tiling结构成员赋值的方式如下： 

```txt
MyAddTilingData myTiling;  
myTiling.st1.set_field1(1);  
myTiling.st1.set_field2(2);  
myTiling.st2.set_field3(3);  
myTiling.st2.set_field4(4); 
```

numBlocks：规定了核函数将会在几个核上执行。例如，需要计算8M的数据，每 个核上计算1M的数据，numBlocks设置为8，但是为了充分利用硬件资源，一般 将numBlocks设置为硬件平台的核数，根据核数进行数据切分。 

# 说明

numBlocks是逻辑核的概念，取值范围为[1,65535]。为了充分利用硬件资源，一般设置为 物理核的核数或其倍数。 

● 对于耦合模式和分离模式，numBlocks在运行时的意义和设置规则有一些区别，具体说 明如下： 

耦合模式：由于其Vector、Cube单元是集成在一起的，numBlocks用于设置启动 多个AI Core核实例执行，不区分Vector、Cube。AI Core的核数可以通过 GetCoreNumAiv或者GetCoreNumAic获取。 

分离模式 

针对仅包含Vector计算的算子，numBlocks用于设置启动多少个Vector （AIV）实例执行，比如某款AI处理器上有40个Vector核，建议设置为40。 

针对仅包含Cube计算的算子，numBlocks用于设置启动多少个Cube（AIC） 实例执行，比如某款AI处理器上有20个Cube核，建议设置为20。 

针对Vector/Cube融合计算的算子，启动时，按照AIV和AIC组合启动， numBlocks用于设置启动多少个组合执行，比如某款AI处理器上有40个 Vector核和20个Cube核，一个组合是2个Vector核和1个Cube核，建议设置 为20，此时会启动20个组合，即40个Vector核和20个Cube核。注意：该场 景下，设置的numBlocks逻辑核的核数不能超过物理核（2个Vector核和1 个Cube核组合为1个物理核）的核数。 

● AIC/AIV的核数分别通过GetCoreNumAic和GetCoreNumAiv接口获取。 

● 如果开发者使用了Device资源限制特性，那么算子设置的numBlocks不应超过 PlatformAscendC提供核数的API（GetCoreNum/GetCoreNumAic/GetCoreNumAiv 等）返回的核数。例如，使用aclrtSetStreamResLimit设置Stream级别的Vector核数为 8，那么GetCoreNumAiv接口返回值为8，针对Vector算子设置的numBlocks不应超过 8，否则会抢占其他Stream的资源，导致资源限制失效。 

TilingKey（可选）：TilingKey是一个算子内为了区分不同的实现而将kernel代码 进行区分的方法，该方法类似于C++的Template模板机制，可减少不必要的 icache miss以及scalar耗时，有助于优化单次调用kernel的性能。不同的kernel实 现分支可以通过TilingKey来标识，host侧设置TilingKey后，可以选择对应的分 支。例如，一个算子在不同的shape下，有不同的算法逻辑，kernel侧可以通过 TilingKey来选择不同的算法逻辑，在host侧Tiling算法也有差异，host/kernel侧通 过相同的TilingKey进行关联。 

假如有如下kernel代码： 

```javascript
if (condition) { ProcessA(); 
```

```javascript
} else {ProcessB();}如果函数ProcessA、ProcessB两个函数是个非常大的函数，那么上述代码在编译后会变得更大，而每次kernel运行只会选择1个分支，条件的判断和跳转在代码大到一定程度（16-32K，不同芯片存在差异）后会出现cache miss。通过TilingKey可以对这种情况进行优化，给2个kernel的处理函数设置不同的TilingKey 1和2：if (TILING_KEY_IS(1)) {ProcessA();} else if (TILING_KEY_IS(2)) {ProcessB();} 
```

这样device kernel编译时会自动识别到2个TilingKey并编译2个kernel入口函数， 将条件判断进行常量折叠。同时需要和host tiling函数配合，判断走ProcessA的场 景设置TilingKey为1，走ProcessB的场景设置TilingKey为2： 

```cpp
static ge::graphStatus TilingFunc(gert::TilingContext* context)   
{ // some code if (condition){ context->SetTilingKey(1); } else { context->SetTilingKey(2); } return ge::GRAPH_SUCCESS;   
} 
```

# 说明

编译时，可以通过设置--tiling_key编译选项指定TilingKey，编译时只编译指定TilingKey 相关的kernel代码，用于加速编译过程。 

WorkspaceSize：workspace是设备侧Global Memory上的一块内存。在Tiling函 数中可以设置workspace的大小。设置后：单算子API执行场景，可以通过单算子 API调用第一段接口获取workspace的大小，然后由开发者申请对应大小的Global Memory；入图场景，框架会根据设置的大小自动申请对应大小的Global Memory。申请workspace后，在算子Kernel实现时，可以使用这块workspace内 存。 

workspace内存分为两部分：Ascend C API需要的workspace内存和算子实现使用 到的workspace内存（按需）。 

– Ascend C API需要预留workspace内存 

API在计算过程需要一些workspace内存作为缓存，因此算子Tiling函数需要 为API预留workspace内存，预留内存大小通过GetLibApiWorkSpaceSize接口 获取。 

算子实现使用到的workspace内存（按需） 

算子内部需要通过额外的device内存进行数据交换或者缓存的时候才需要分 配，根据算子计算的空间自行分配。 

整体的workspace内存就是上述两部分之和，在Tiling函数中设置方法如下： 

auto workspaceSizes $=$ context->GetWorkspaceSizes(1); // 只使用1块workspace workspaceSizes[0] $=$ sysWorkspaceSize $^ +$ usrWorkspaceSize; 

# Tiling 实现基本流程

Tiling实现开发的流程图如下： 


图 2-47 Tiling 开发流程图


![](images/593486ff0a3e7a886a57991e570293c1c058efd7e9d48609f34cec1d00c76e39.jpg)


下面将从一个简单的Add算子为例介绍Tiling的实现流程。本样例中待处理数据的 Shape大小可以平均分配到每个核上，并且可以对齐到一个datablock（32B）的大 小。 

首先完成算子TilingData结构定义头文件的编写，该文件命名为 “算子名称 _tiling.h”，位于算子工程的op_host目录下。样例代码如下： 

```c
ifndef ADDcustomOM TilING_H   
#define ADDCUSTOM TILING_H   
#include"register/tilingdata_base.h"   
namespace optiling{ BEGIN_TILING_DATADEF(TilingData) //注册一个tiling的类，以tiling的名字作为入参 TILING_DATA_FIELDDEF uint32_t, totalLength); //添加tiling字段，总计算数据量 TILING_DATA_FIELDDEF uint32_t, tileNum); //添加tiling字段，每个核上总计算数据分块个数 END_TILING_DATADEF; //注册算子tilingdata类到对应的AddCustom算子 REGISTER_TILING_DATA_CLASS(AddCustom, TilingData) 
```

```txt
} #endif//ADDCustomTILING_H 
```

具体的编写步骤如下： 

步骤1 代码框架编写，需要增加#ifndef...的判断条件，防止头文件的重复包含；需要包含 register/tilingdata_base.h头文件，tilingdata_base.h中定义了多个用于tilingdata注册 的宏。样例代码如下： 

```c
#ifndef ADDcustom_TILING_H
#define ADDcustom_TILING_H
#include "register/tilingdata_base.h"
namespace optiling {
// tiling结构定义和注册代码
// ...
} 
```

步骤2 TilingData参数设计，TilingData参数本质上是和并行数据切分相关的参数，本示例算 子使用了2个tiling参数：totalLength、tileNum。totalLength是指需要计算的数据量 大小，tileNum是指每个核上总计算数据分块个数。比如，totalLength这个参数传递 到kernel侧后，可以通过除以参与计算的核数，得到每个核上的计算量，这样就完成 了多核数据的切分。 

步骤3 TilingData结构定义，通过BEGIN_TILING_DATA_DEF接口定义一个TilingData的类， 通过TILING_DATA_FIELD_DEF接口增加TilingData的两个字段totalLength、 tileNum，通过END_TILING_DATA_DEF接口结束TilingData定义。相关接口的详细说 明请参考TilingData结构定义。 

```c
BEGIN_TILING_DATADEF(TilingData) // 注册一个tiling的类，以tiling的名字作为入参  
TILING_DATA_FIELD_def uint32_t, totalLength); // 添加tiling字段，总计算数据量  
TILING_DATA_FIELD_def uint32_t, tileNum); // 添加tiling字段，每个核上总计算数据分块个数  
END_TILING_DATADEF; 
```

步骤4 注册TilingData结构，通过REGISTER_TILING_DATA_CLASS接口，注册TilingData类， 和自定义算子相关联。REGISTER_TILING_DATA_CLASS第一个参数为op_type(算子类 型)，本样例中传入AddCustom，第二个参数为TilingData的类名。 REGISTER_TILING_DATA_CLASS接口介绍请参考TilingData结构注册。 

```txt
// 注册算子tilingdata类到对应的AddCustom算子  
REGISTER_TILING_DATA_CLASS(AddCustom, TilingData) 
```

# ----结束

然后完成算子host实现cpp文件中Tiling函数实现，该文件命名为 “算子名称.cpp”， 位于算子工程的op_host目录下。Tiling函数的原型是固定的，接受一个TilingContext 作为输入，在此context上可以获取到输入、输出的Shape指针等内容。注册的Tiling函 数由框架调用，调用时会传入TilingContext参数。样例代码如下： 

namespace optingiling{ const uint32_t NUM_BLOCKS $= 8$ . const uint32_t TILE_NUM $= 8$ static ge::graphStatus TilingFunc(gert::TilingContext \*context) { TilingData tiling; uint32_t totalLength $=$ context->GetInputShape(0)->GetOriginShape().GetShapeSize(); context->SetBlockDim(NUM_BLOCKS); tiling.set_totalLength(totalLength); tiling.set_TILENum(TILE_NUM); tiling.SaveToBuffer(context->GetRawTilingData()->GetData(),context->GetRawTilingData()- >GetCapacity()); context->GetRawTilingData()->SetBlockSize(tiling.GetDataSize()); size_t \*currentWorkspace $=$ context->GetWorkspaceSizes(1); currentWorkspace[0] $= 0$ return ge::GRAPH_SUCCESS; 

```typescript
}   
} // namespace opting 
```

具体步骤如下： 

步骤1 获取TilingContext的上下文，即Tiling函数的入参gert::TilingContext* context。 

步骤2 设置TilingData。在步骤3中定义了TilingData类后，可以创建该类的一个实例，并通 过调用set_{field_name}方法来设置各个字段值（其中field_name是步骤3中定义的 tiling字段名）。设置完tiling字段后，通过调用SaveToBuffer方法完成TilingData实例 的序列化和保存。 

1. 通过上下文获取输入输出shape信息。本样例中通过TilingContext的 GetInputShape接口获取输入的shape大小。 // 获取输入shape信息 uint32_t totalLength $=$ context->GetInputShape(0)->GetOriginShape().GetShapeSize(); 

2. 设置TilingData。通过调用set_{field_name}方法来设置TilingData的字段值。 // 用TilingData定义一个具体的实例 TilingData tiling; // 设置TilingData tiling.set_totalLength(totalLength); tiling.set_tileNum(TILE_NUM); 

3. 调用TilingData类的SaveToBuffer接口完成序列化并保存至TilingContext上下文。 SaveToBuffer的第一个参数为存储Buffer的首地址，第二个参数为Buffer的长度。 通过调用GetRawTilingData获取无类型的TilingData的地址，再通过GetData获取 数据指针，作为Buffer的首地址；通过调用GetRawTilingData获取无类型的 TilingData的地址，再通过GetCapacity获取TilingData的长度，作为Buffer的长 度。完成SaveToBuffer操作后需要通过SetDataSize设置TilingData的长度，该长 度通过TilingData类的GetDataSize接口获取。 // 序列化并保存 tiling.SaveToBuffer(context->GetRawTilingData()->GetData(), context->GetRawTilingData()- >GetCapacity()); context->GetRawTilingData()->SetDataSize(tiling.GetDataSize()); 

步骤3 通过SetBlockDim接口设置numBlocks。 context->SetBlockDim(NUM_BLOCKS); 

步骤4 （可选）通过SetTilingKey设置TilingKey。 context->SetTilingKey(1); 

步骤5 （可选）通过GetWorkspaceSizes获取workspace size指针，并设置size大小。此处仅 作为举例，设置workspace的大小为0。 

```c
size_t *currentWorkspace = context->GetWorkspaceSizes(1);  
currentWorkspace[0] = 0; 
```

----结束 

# 2.10.2.5.2 通过 TilingData 传递属性信息

如果算子包含属性信息，该属性信息可以通过TilingData传递到kernel侧，参与kernel 侧算子核函数的计算。以ReduceMaxCustom算子为例，该算子用于对输入数据按维度 dim返回最大值，并且返回索引。ReduceMaxCustom算子有两个属性，reduceDim和 isKeepDim，reduceDim表示按照哪一个维度进行reduce操作；isKeepDim表示是否需 要保持输出的维度与输入一样。本样例仅支持对最后一维做reduce操作，输入数据类 型为half。 

1. ReduceMaxCustom算子TilingData的定义如下：这里我们重点关注 reduceAxisLen。参数reduceAxisLen表示获取reduceDim轴的长度，这里也就是 最后一维的长度。该参数后续会通过TilingData传递到kernel侧参与计算。 

```c
ifndefREDUCE_MAXCustomOM_TILING_H #defineREDUCE_MAXCUSTOM_TILING_H #include"register/tilingdata_base.h" namespaceoptiling{ BEGIN_TILING_DATADEF(ReduceMaxTilingData) TILING_DATA_FIELDDEF( uint32_t,reduceAxisLen); //添加tiling字段，reduceDim轴的长度 //其他TilingData参数的定义 END_TILING_DATADEF; //注册算子tilingdata类到对应的ReduceMaxCustom算子 REGISTER_TILING_DATA_CLASS(ReduceMaxCustom,ReduceMaxTilingData) } #endif//REDUCE_MAXCustomOM_TILING_H 
```

2. ReduceMaxCustom算子的Tiling实现如下。这里我们重点关注属性信息通过 TilingData传递的过程：首先通过TilingContext上下文从attr获取reduceDim属性值；然后根据reduceDim属性值获取reduceDim轴的长度并设置到TilingData中。namespace optiling{static ge::graphStatus TilingFunc(gert::TilingContext* context)ReduceMaxTilingData tiling; //从attr获取reduceDim属性值，因为reduceDim是第一个属性，所以GetAttrPointer传入的索引值为0 const gert::RuntimeAttributes\*attrs $=$ context->GetAttributes(); const uint32_t\* reduceDim $\equiv$ attrs->GetAttrPointer<uint32_t>(0); //获取reduceDim轴的长度 const gert::StorageShape\* xShapePtr $=$ context->GetInputShape(0); const gert::Shape& xShape $\equiv$ xShapePtr->GetStorageShape(); const uint32_t reduceAxisLen $\equiv$ xShape.GetDim(*reduceDim); //计算TilingData中除了reduceAxisLen之外其他成员变量的值 //将reduceAxisLen设置到tiling结构体中，传递到kernel函数使用 tiling.set.reduceAxisLen(reduceAxisLen); //设置TilingData中除了reduceAxisLen之外其他成员变量的值 //TilingData序列化保存 tiling.SaveToBuffer(context->GetRawTilingData()->GetData(),context->GetRawTilingData()- >GetCapacity()); context->GetRawTilingData()->Set的数据Size(tiling的数据Size()); return ge:GRAPH_SUCCESS; } // namespace optiling 

# 2.10.2.5.3 使用高阶 API 时配套的 Tiling 实现

```txt
1. 首先进行tiling结构定义：
namespace optingil {
BEGIN_TILING_DATADEF(MyAddTilingData) // 声明tiling结构名字
TILING_DATA_FIELDDEFSTRUCT(TCubeTiling, cubeTilingData); // 引用高阶API的tiling结构体
TILING_DATA_FIELDDEF uint32_t, field); // 结构成员的引用结构体
END_TILING_DATADEF;
REGISTER_TILING_DATA_CLASS(MyAdd, MyAddTilingData) // tiling结构注册给算子
} 
```

```cpp
2. 通过高阶API配套的tiling函数对tiling结构初始化：  
static ge::graphStatus TilingFunc(gert::TilingContext* context) {  
    int32_t M = 1024;  
    int32_t N = 640;  
    int32_t K = 256;  
    int32_t baseM = 128;  
    int32_t baseN = 128;  
    auto ascendcPlatform = platform_ascending::PlatformAscendC(context->GetPlatformInfo());  
    MultiCoreMatmulTiling cubeTiling(ascendingPlatform);  
    cubeTiling.SetDim(2);  
    cubeTiling.SetATOType(TPosition::GM, CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT16);  
    cubeTiling.SetBType(TPosition::GM, CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT16);  
    cubeTiling.SetCType(TPosition::LCM, CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT);  
    cubeTiling.SetBiasType(TPosition::GM, CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT);  
    cubeTiling.SetShape(M, N, K);  
    cubeTiling.SetOrgShape(M, N, K); 
```

```cpp
cubeTiling.SetFixSplit(baseM, baseN, -1); cubeTiling.SetBias(true); cubeTiling.SetBufferSpace(-1, -1, -1); MyAddTilingData tiling; if (cubeTiling.GetTiling(tiling.cubeTilingData) == -1){ return ge::GRAPH_FAILED; } // some code 
```

# 2.10.2.5.4 使用标准 ${ { \mathsf { C } } { + } { + } }$ 语法定义 Tiling 结构体

# 具体步骤

在定义Tiling结构体时，可以使用标准C++语法定义一个POD类型（Plain Old Data），即与C语言兼容的数据类型。具体步骤如下。完整样例请参考标准C++语法定 义Tiling结构体样例。 

步骤1 使用 ${ \mathsf { C } } { + } { + }$ 语法定义Tiling结构体。 

# 说明

该结构体定义所在的头文件应放置在算子工程的op_kernel目录下。由于只有该目录下的文件会 被打包进算子包，供在线编译场景中使用，若将文件放置在其他目录中，可能导致在线编译因找 不到相关文件而失败。 

用户在使用高阶API的Tiling结构体时，通过AscendC::tiling命名空间引用 "kernel_tiling/kernel_tiling.h"中预定义的Tiling结构体，如下代码所示。 

```c
ifndef MATMULCustomTILING_H
	#define MATMULCUSTOMTILING_H
#include <cstdint>
#include "kernel_tiling/kernel_tiling.h" // for TCubeTiling
struct MatmulCustomTilingData \{
 uint64_t localMemSize;
 AscendC::tiling::TCubeTiling cubeTilingData;
\};
#endif // MATMUL Custom TILING H 
```

步骤2 Host侧Tiling函数中对Tiling结构体赋值。 

需要包含Tiling结构体定义头文件。 

通过GetTilingData获取Tiling结构体指针，并对其成员变量进行赋值。 

include"../op_kernel/matmul(custom_tiling.h”//包含Tiling结构体定义头文件   
...   
namespace optiling{ static ge::graphStatus TilingFunc(gert::TilingContext \*context)   
{ ... MultiCoreMatmulTiling cubeTiling(ascendcPlatform); //获取Tiling结构体指针 MatmulCustomTilingData \*tiling $=$ context->GetTilingData<MatmulCustomTilingData>(); //对tiling的成员变量赋值 if (cubeTiling.GetTiling(tiling->cubeTilingData) $= = -1$ ）{ return ge::GRAPH_FAILED; } uint64_t localMemSize; ascendcPlatform.GetCoreMemSize platform_ascending::CoreMemType::UB,localMemSize); tiling->localMemSize $=$ localMemSize; return ge::GRAPH_SUCCESS;   
}   
} // namespace optiling 

步骤3 Kernel侧注册Tiling结构体，解析Tiling数据至TilingData结构并使用。 

需要包含Tiling结构体定义头文件。 

通过REGISTER_TILING_DEFAULT或者REGISTER_TILING_FOR_TILINGKEY注册 Tiling结构体；通过GET_TILING_DATA解析Tiling数据至TilingData结构并使用。 其中REGISTER_TILING_DEFAULT同时也用于标识使用标准C++语法定义 TilingData结构体。 

```cpp
include "kernel_operator.h" #include "matmulcustom_tiling.h" //包含Tiling结构体定义头文件 extern"C" _global _aicore_ void matmulcustom(GM_ADDR a, GM_ADDR b, GM_ADDR bias, GM_ADDR c, GM_ADDR workspace, GM_ADDR tiling) { REGISTER_TILING_DEFAULT(MatmulCustomTilingData); GET_TILING_DATA(tilingData, tiling); MatmulKernel< half, half, float, float> matmulKernel; AscendC::TPipe pipe; REGISTER_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), matmulKernel.matmulObj, &tilingData.cubeTilingData); // Initialize the matmul object. matmulKernelInit(a, b, bias, c, workspace, tilingData.localMemSize, tilingData.cubeTilingData); } 
```

----结束 

# 使用标准 $\mathsf { C } { \mathrel { + { + } } }$ 语法定义 Tiling 结构体的优势

相比较使用BEGIN_TILING_DATA_DEF等宏进行定义的方式，该方式不仅更符合 $\mathsf { C } { + + }$ 开 发者的开发习惯，并且提供了强大的灵活性。 

支持bool类型，支持数组、结构体数组及列表初始化。 

```txt
class A{   
public: bool xxx; uint32_t xxx[2][128] = {0};   
};   
class B{   
public: bool xxx = false; uint8_t xxx[2][2]{0}; A[10];   
}； 
```

不同算子可以支持定义同名但结构不同的Tiling结构体，通过算子引用对应的头文 件即可实现区分。这种方式允许每个算子使用符合自身需求的Tiling结构定义，而 不会与其他算子产生冲突。 

相比之下，使用BEGIN_TILING_DATA_DEF等宏方式定义同名但结构不同的Tiling 结构体时，由于这些结构体会被注册到全局的Tiling结构体管理变量中，可能导致 后续通过结构体名称访问时，无法准确获取当前算子实际使用的Tiling结构体，从 而引发未定义行为。 

算子A： 

```cpp
class TilingData{ public: uint32_t length; }; 
```

算子B： 

```txt
class TilingData{   
public: uint32_t length; uint16_t coreNum;   
}； 
```

支持自定义Tiling赋值，用户可以通过访问Tiling结构体成员变量直接赋值，或自 定义Tiling赋值函数（宏定义方式下，用户仅可通过框架生成的set_xx/get_xx方法 赋值/访问） 


Tiling结构体定义：


```cpp
class TilingData {
public:
    uint32_t xxx1;
    uint32_t xxx2;
    uint8_t xxx3;
    bool xxx4;
}; 
```

# 使用约束

使用标准C++语法定义Tiling结构体时存在如下约束限制： 

Tiling结构体内不支持定义成员函数，因为成员函数存在Device侧和Host侧的差异 （Device侧的函数需要__aicore__修饰符），而Tiling结构体Device侧和Host侧共 用，所以会在编译或执行时出现问题： 

```cpp
class TilingData {
public:
    uint32_t xxx;
    __aicore__funcA() { ... } // 错误，host侧编译时不支持__aicore__修饰符，会出现编译错误
    void func() { ... } // 错误，device侧缺少__aicore__修饰符，无法执行
}; 
```

Tiling结构体成员变量不支持指针、引用类型，此类数据类型会导致Host侧到 Device侧数据解析异常： 

```javascript
class TilingData { public: uint32_t\* totalLength; //指针场景不支持，Host无法传递指针到Device uint32_t& tileNum; //引用场景不支持，Host无法传递指针到Device }; 
```

Tiling结构体仅支持POD类型，没有虚函数、虚继承等面向对象特性，也不支持模 板类： 

```cpp
class A{   
public: uint32_t totalLength; uint32_t tileNum; 
```

};   
class B:public A{   
public: uint32_t xxx; uint32_t xxx;   
}；   
static ge::graphStatus TilingFunc(gert::TilingContext* context)   
{ //错误用法 B\*tiling $\equiv$ context->GetTilingData<A>();//不支持，会触发未知问题 //正确用法 B\*tiling $\equiv$ context->GetTilingData<B>(); ...... return ge::GRAPH_SUCCESS;   
} 

GetTilingData获取的Tiling不包含初值，需显式赋值或在Tiling结构体定义并调用 Tiling赋值函数； 

static ge::graphStatus TilingFunc(gert::TilingContext* context)   
{ TilingData \*tiling $=$ context->GetTilingData<TilingData>(); //获取Tiling结构体，此时totalLength、 tileNum为0，并不会带入初始值 /需显式赋值 tiling->totalLength $=$ totalLength; //赋值Tiling结构体成员变量 tiling->tileNum $=$ TILE_NUM; //赋值Tiling结构体成员变量 return ge::GRAPH_SUCCESS; 

host侧和kernel侧的Tiling结构体支持传入模板参数。由于宏函数中逗号运算符的 特殊性，在kernel侧宏函数（REGISTER_TILING_DEFAULT或者 

REGISTER_TILING_FOR_TILINGKEY）使用带逗号的模板类型（如： template<int32_t sizeA, int32_t sizeB>），存在编译异常，因此需要使用别名方 式来定义带逗号的模板类型（如：using size = template<int32_t sizeA, int32_t sizeB>）。具体示例如下： 

//模板参数个数大于1的场景  
template<int32_t sizeA,int32_t sizeB>  
class A{  
public: uint32_t totalLength; uint32_t tileNum; uint32_t dataArray[sizeA];  
};  
//模板参数个数等于1的场景  
template<int32_t sizeA>  
class B{  
public: uint32_t totalLength; uint32_t tileNum; uint32_t dataArray[sizeA];  
};  
//host侧可以直接传入Tiling结构体以及对应模板参数  
static ge::graphStatus TilingFunc(gert::TilingContext* context) { //模板参数个数等于1或者大于等于1的时候都可以直接传入 $\mathrm{A} < 3,5 >$ *tiling = context->GetTilingData<A<3,5>>(); $\mathrm{B} < 3 >$ *tiling = context->GetTilingData<B<3>>(); return ge::GRAPH_SUCCESS;  
}  
//kernel侧代码  
#include "kernel_operator.h" #include "addcustom_tiling.h" //包含Tiling结构体定义头文件 extern "C" __global __aicore __void addcustom(GM_ADDR x, GM_ADDR y, GM_ADDR z, GM_ADDR workspace, GM_ADDR tiling) 

```javascript
{ using aa = A<3,5>; REGISTER_TILING_DEFAULT(aa); //模板参数个数大于1时，一定要用using来指定 REGISTER_TILING_FOR_TILINGKEY("TILING_KEYVAR == 2", B<3>); //模板参数个数等于1时，可以直接写明模板参数 
```

# 如何将宏定义 Tiling 结构体修改为标准 $\mathsf { C } { \mathrel { + { + } } }$ 语法

本节介绍如何将使用BEGIN_TILING_DATA_DEF等宏进行定义的方式改造成使用标准C ++语法的方式。 

步骤1 首先将之前位于op_host目录下的Tiling结构体定义头文件移至op_kernel目录下，内容 前后对比如下，注意此时包含的头文件变化，不需要再包含宏定义相关的头文件。 


表 2-38 两种方式对比


<table><tr><td>宏定义方式</td><td>标准C++语法定义方式</td></tr><tr><td>#include &quot;register/tilingdata_base.h&quot; #include &quot;tiling/tilingApi.h&quot; // TCubeTiling结构体 通过宏定义 namespace optingil { BEGIN_TILING_DATA_REF(MatmulCustomTilingData a) TILING_DATA_FIELD_REF uint64_t, localMemSize); TILING_DATA_FIELD_REFSTRUCT(TCubeTiling, cubeTilingData); END_TILING_DATA_REF; REGISTER_TILING_DATA_CLASS(MatmulCustom, MatmulCustomTilingData) } // namespace optingil</td><td>#include &lt;cstdint&gt; #include &quot;kernel_tiling/kernel_tiling.h&quot; // TCubeTiling结构体通过C++语法定义 struct MatmulCustomTilingData { uint64_t localMemSize; AscendC::tiling::TCubeTiling cubeTilingData; };</td></tr></table>

步骤2 然后修改Host侧的Tiling函数实现，此时对Tiling结构体的成员变量赋值无需使用宏定 义生成的set方法，而是使用用户熟悉的C++指针赋值方式。 


表 2-39 两种方式对比


<table><tr><td>宏定义方式</td><td>标准C++语法定义方式</td></tr><tr><td>namespace optingilng{ static ge::graphStatus TilingFunc(gert::TilingContext *context) { ... MultiCoreMatmulTiling cubeTiling(ascendcPlatform); ... MatmulCustomTilingData tiling; if (cubeTiling.GetTiling(tiling.cubeTilingData) == -1) { // Get matmul tiling. return ge::GRAPH_FAILED; } uint64_t localMemSize; ascendcPlatform.GetCoreMemSize platform ascend dc::CoreMemType::UB, localMemSize); tiling.set_localMemSize(localMemSize); //需要使用宏定义方式生成的set方法 ... //需要将局部变量保存至context上下文 tiling.SaveToBuffer(context- &gt;GetRawTilingData()-&gt;GetData(), context-&gt;GetRawTilingData()-&gt;GetCapacity()); ... return ge::GRAPH_SUCCESS; } } // namespace optingilng</td><td>#include &quot;./op_kernel/matmulcustom_tiling.h&quot; //包含Tiling结构体定义头文件 ... namespace optingilng{ static ge::graphStatus TilingFunc(gert::TilingContext *context) { ... MultiCoreMatmulTiling cubeTiling(ascendcPlatform); ... MatmulCustomTilingData *tiling = context-&gt;GetTilingData&lt;MmatmCustomTilingData&gt;(); if (cubeTiling.GetTiling(tiling-&gt;cubeTilingData) == -1) { return ge::GRAPH_FAILED; } uint64_t localMemSize; ascendcPlatform.GetCoreMemSizeplatform ascend dc::CoreMemType::UB, localMemSize); tiling-&gt;localMemSize = localMemSize; //使用用户友好的C++指针方式赋值成员变量 ... return ge::GRAPH_SUCCESS; } } // namespace optingilng</td></tr></table>

步骤3 最后，在Kernel 函数入口处新增REGISTER_TILING_DEFAULT调用，用于注册Tiling结 构体。该注册操作的作用是：告知框架用户已使用标准 C++ 语法定义Tiling结构体， 并明确其类型，以便框架在进行Tiling数据解析时能够正确识别和使用该结构体。 

```c
include"matmul(custom_tiling.h"   
extern"C" global __aicore__voidmatmul/custom(GM_ADDR a, GM_ADDR b, GM_ADDR bias, GM_ADDR c, GM_ADDR workspace, GM_ADDR tiling)   
{ REGISTER_TILING_DEFAULT(MatmulCustomTilingData); //新增REGISTER_TILING_DEFAULT调用注册Tiling 结构体   
1 
```

----结束 

# 2.10.2.5.5 Tiling 模板编程

在TilingKey编程章节介绍的TilingKey编程方式中，TilingKey不易于记忆和理解，因为 它们通常是较长又没有明确含义的数字。 

在涉及多个TilingKey的场景中，开发者依赖TilingKey来管理kernel的实现，无论是在 管理还是使用上都会遇到相当大的复杂性。为了简化这一过程，可以采用模板编程的 方法来替代传统的TilingKey编程，从而减少对TilingKey数值标识的依赖，使kernel的 管理更加直观和高效。使用步骤如下，完整样例请参考Tiling模板编程样例。 

步骤1 在自定义算子工程的op_kernel目录下，新增定义模板参数和模板参数组合的头文件， 本示例中头文件命名为tiling_key_add_custom.h。 

该头文件中需要包含模板头文件ascendc/host_api/tiling/template_argument.h。 

定义模板参数ASCENDC_TPL_ARGS_DECL和模板参数组合 ASCENDC_TPL_ARGS_SEL（即可使用的模板）。具体API参考见模板参数定义。 


#include "ascendc/host_api/tiling/template_argument.h"


```c
//模板参数  
ASCENDC_TPL.ArgS_DECL(AddCustomTemplate, //算子OpType  
ASCENDC_TPL_DATATYPE_DECL(D_T_X,C_DT_FLOAT,C_DT_FLOAT16,ASCENDC_TPL_INPUT(O)),//  
DataType类型的模板参数定义：输入参数x的数据类型，取值范围为float16/float32,ASCENDC_TPL_INPUT(O)说明对应Kernel侧第0个输入  
ASCENDC_TPL_DATATYPE_DECL(D_T_Y,C_DT_FLOAT,C_DT_FLOAT16,ASCENDC_TPL_INPUT(1)),//  
DataType类型的模板参数定义：输入参数y的数据类型，取值范围为float16/float32,ASCENDC_TPL_INPUT(1)说明对应Kernel侧第1个输入  
ASCENDC_TPL_DATATYPE_DECL(D_T_Z,C_DT_FLOAT,C_DT_FLOAT16,ASCENDC_TPL_OUTPUT(O)),//  
DataType类型的模板参数定义：输入参数z的数据类型，取值范围为float16/float32,ASCENDC_TPL_OUTPUT(O)说明对应Kernel侧第0个输出  
ASCENDC_TPL_UID_DECL(TILE_NUM,ASCENDC_TPL_8_BW,ASCENDC_TPL_UL_MIX,2,0,2,3,5,10,12,13,9,8),//自定义UINT类型（无符号整形）的模板参数定义：模板参数为切分的块数，编码位宽为  
ASCENDC_TPL_8_BW即8比特，表示该模板参数的个数不超过8比特能表达的范围；ASCENDC_TPL_UL_MIX表示通过混合模式表达取值范围，有2组的数据{0-2}、{3-5}和穷举值10、12、13、9、8，最后结果为{0,1,2,3,4,5,10,12,13,9,8}  
ASCENDC_TPL BOOL_DECL(IS_SPLIT,0,1),//自定义bool类型的模板参数定义：模板参数为是否切分标志位，取值范围为0和1，1表示切分，0表示不切分  
）;  
//模板参数组合  
//用于调用GET_TPL_TILING_KEY获取TilingKey时，接口内部校验TilingKey是否合法  
ASCENDC_TPL_SEL(ASCENDC_TPL.ArgS_SEL(ASCENDC_TPL_KERNEL_TYPE_SEL(ASCENDC_TPL_AIV_ONLY),//Kernel类型选择，无需在模板参数声明中定义，在SEL中直接配置，所有ASCENDC_TPL.ArgS_SEL是否配置需要保持统一，如不配置将走自动推导流程ASCENDC_TPL_DATatype_SEL(D_T_X,C_DT_FLOAT16),ASCENDC_TPL_DATatype_SEL(D_T_Y,C_DT_FLOAT16),ASCENDC_TPL_DATatype_SEL(D_T_Z,C_DT_FLOAT16),ASCENDC_TPL_UID_SEL(TILE_NUM,ASCENDC_TPL_UL_LIST,1,8),ASCENDC_TPL Bool_SEL(IS_SPLIT,0,1))，ASCENDC_TPL.ArgS_SEL(ASCENDC_TPL_KERNEL_TYPE_SEL(ASCENDC_TPL_AIV_ONLY),ASCENDC_TPL_DATatype_SEL(D_T_X,C_DT_FLOAT),ASCENDC_TPL_DATatype_SEL(D_T_Y,C_DT_FLOAT),ASCENDC_TPL_DATatype_SEL(D_T_Z,C_DT_FLOAT),ASCENDC_TPL_UID_SEL(TILE_NUM,ASCENDC_TPL_UL_LIST,1,8),ASCENDC_TPL Bool_SEL(IS_SPLIT,0,1))， 
```

步骤2 host侧调用ASCENDC_TPL_SEL_PARAM接口自动生成并配置TilingKey。 

host实现文件中包含步骤1中定义模板参数和模板参数组合的头文件。 

调用ASCENDC_TPL_SEL_PARAM接口自动生成并配置TilingKey， ASCENDC_TPL_SEL_PARAM输入参数为模板参数的具体值，传入时需要与定义模 板参数和模板参数组合的头文件中的模板参数顺序保持一致。 

include "tiling_key_addcustom.h"   
static ge::graphStatus TilingFunc(gert::TilingContext *context)   
{ TilingData tiling; uint32_t totalLength $=$ context->GetInputShape(0)->GetOriginShape().GetShapeSize(); ge::DataType dtypex $=$ context->GetInputDesc(0)->GetDataType(); ge::DataType dtypery $=$ context->GetInputDesc(1)->GetDataType(); ge::DataType dtypz $=$ context->GetOutputDesc(1)->GetDataType(); uint32_t D_T_X $\equiv$ static cast<int>(dtypex),D_T_Y $\equiv$ static cast<int>(dtyp_y),D_T_Z $\equiv$ static cast<int>(dtyp_z), TILE_NUM $= 1$ ,IS_SPLIT $= 0$ if(totalLength< MIN_LENGTH_FOR_SPLIT){ IS_SPLIT $= 0$ . TILE_NUM $= 1$ 

}else{ IS_SPLIT $= 1$ TILE_NUM $\equiv$ DEFAULT_TILE_NUM; } context->SetBlockDim(NUM_BLOCKS); tiling.set_totalLength(totalLength); tiling.SaveToBuffer(context->GetRawTilingData()->GetData(),context->GetRawTilingData()- >GetCapacity()); context->GetRawTilingData()->SetBlockSize(tiling的数据Size()); ASCENDC_TPL_SEL_PARAM(context,D_T_X,D_T_Y,D_T_Z,TILE_NUM,IS_SPLIT); size_t\*currentWorkspace $\equiv$ context->GetWorkspaceSizes(1); currentWorkspace[0] $= 0$ return ge::GRAPH_SUCCESS; 

# 步骤3 kernel侧实现

kernel实现文件中包含步骤1中定义模板参数和模板参数组合的头文件。 

核函数添加template模板，以便支持模板参数的传入，参数顺序需要与定义模板 参数和模板参数组合的头文件中的模板参数顺序保持一致。 

通过对模板参数的分支判断，选择不同的kernel侧实现。 

```txt
include "tiling_key_addCustom.h"   
...   
template<typename D_T_X, typename D_T_Y, typename D_T_Z,int TILE_NUM,int IS_SPLIT> __global__aicore__void addcustom_template(GM_ADDR x,GM_ADDR y,GM_ADDR z,GM_ADDR workspace,GM_ADDR tiling)   
{ GET_TILING_DATA(tiling_data,tiling); KernelAdd<D_T_X,D_T_Y,D_T_Z> op; op.Initial(x,y,z,tiling_data.totalLength,TILE_NUM); if constexpr (std::is SAME_v<D_T_X,float>& std::is SAME_v<D_T_Y,float>& std::is SAME_v<D_T_Z, float>) { op.Process1(); } else if constexpr (std::is SAME_v<D_T_X, half>& std::is SAME_v<D_T_Y, half>& std::is SAME_v<D_T_Z, half>) { if(IS_SPLIT==0){ op.Process1(); } else if(IS_SPLIT==1){ op.Process2(); }   
} 
```

# ----结束

# 说明

Tiling模板编程场景下，编译时，可以通过--kernel-template-input编译选项配置仅编译指定 的模板参数组合相关的Kernel代码，用于加速编译过程。 

# 2.10.2.6 算子包编译

# 2.10.2.6.1 算子工程编译

算子kernel侧和host侧实现开发完成后，需要对算子工程进行编译，生成自定义算子安 装包*.run，详细的编译操作包括： 

编译Ascend C算子kernel侧代码实现文件*.cpp，分为源码发布和二进制发布两种 方式。 

源码发布：不对算子kernel侧实现进行编译，保留算子kernel源码文件 *.cpp。该方式可以支持算子的在线编译、通过ATC模型转换的方式编译算子 的场景。 

二进制发布：对算子kernel侧实现进行编译，生成描述算子相关信息的json文 件*.json和算子二进制文件*.o。算子调用时，如果需要直接调用算子二进制， 则使用该编译方式，比如通过2.10.2.9 单算子API调用的方式完成单算子的调 用，PyTorch框架中单算子调用的场景，动态网络中调用算子的场景。 

编译Ascend C算子host侧代码实现文件*.cpp、*.h。 

将原型定义和shape推导实现编译成算子原型定义动态库 libcust_opsproto_*.so，并生成算子原型对外接口op_proto.h。 

将Tiling实现编译成Tiling动态库liboptiling.so等。 

基于算子原型定义，自动生成单算子API调用代码和头文件aclnn_*.h，并编译 生成单算子API调用的动态库libcust_opapi.so。 

上述编译过程示意图如下： 


图 2-48 算子工程编译示意图


![](images/40abb54f8e67e3c0d62ea03757a6c35fd35882fe6f71a18ec4f308a8fa960024.jpg)


# 编译步骤

步骤1 完成工程编译相关配置。 

修改工程目录下的CMakePresets.json cacheVariables的配置项。 CMakePresets.json文件内容如下，需要配置的参数请参考表2-40，其他参数会 在工程创建时自动生成。 

```json
{
    "version": 1,
    "cmakeMinimumRequired": {
        "major": 3,
        "minor": 19,
        "patch": 0
   },
    "configurePresents": [
        "name": "default",
        "displayName": "Default Config",
        "description": "Default build using Unix Makefiles generator",
    }
} 
```

```txt
"generator": "Unix Makefiles",   
"binaryDir": "${sourceDir}/build_out",   
"cacheVariables": {   
"CMAKE-built_TYPE": {   
"type": "STRING",   
"value": "Release" },   
"ENABLE_SOURCE.Package": {   
"type": "BOOL",   
"value": "True" },   
"ENABLE_BINARY.Package": {   
"type": "BOOL",   
"value": "True" },   
"ASCEND計算U_TYPE": {   
"type": "STRING",   
"value": "ascendxxx" },   
"ENABLE_TEST": {   
"type": "BOOL",   
"value": "True" },   
"vendor_name": {   
"type": "STRING",   
"value": "customize" },   
"ASCEND_PYTHON_EXECUTEABLE": {   
"type": "STRING",   
"value": "python3" },   
"CMAKE_install_prefix": {   
"type": "PATH",   
"value": "${sourceDir}/build_out" },   
"ENABLE_CROSS_COMPILE": {   
"type": "BOOL",   
"value": "False" },   
"CMAKE_CROSS_PLATFORM_COMPILER": {   
"type": "PATH",   
"value": "/usr/bin/aarch64-linux-gnu-g++" },   
"ASCEND Packs_SHAREDLibrary": {   
"type": "BOOL",   
"value": "False" } } } } } } 
```


表 2-40 需要开发者配置的参数列表


<table><tr><td>参数名称</td><td>参数描述</td><td>默认值</td></tr><tr><td>CMAKE-built_TYPE</td><td>编译模式选项，可配置为：
- “Release”，Release版本，不包含调试信息，编译最终发布的版本。
- “Debug”，“Debug”版本，包含调试信息，便于开发者开发和调试。</td><td>“Release”</td></tr><tr><td>ENABLE_SOURCEPACKAGE</td><td>是否开启源码编译</td><td>“True”</td></tr><tr><td>ENABLE_BINARYPACKAGE</td><td>是否开启二进制编译</td><td>“True”</td></tr><tr><td>vendor_name</td><td>标识自定义算子所属厂商的名称。建议开发者自行指定所属厂商名称，避免和其他厂商提供的算子包冲突。</td><td>“customize”</td></tr><tr><td>ASCEND Packs_SHAREDLibrary</td><td>是否开启动态库编译功能。</td><td>“False”</td></tr></table>

配置编译相关环境变量（可选） 


表 2-41 环境变量说明


<table><tr><td>环境变量</td><td>配置说明</td></tr><tr><td>CMAKE_CXX_comPI LER-LaUNCHER</td><td>用于配置C++语言编译器（如g++）、毕昇编译器的启 动器程序为ccache，配置后即可开启cache缓存编译， 加速重复编译并提高构建效率。使用该功能前需要安装 ccache。 配置方法如下，在对应的CMakeLists.txt进行设置： set(CMAKE_CXX_comPILER_LAUNCHER &lt;launchersprogram&gt;) 其中&lt;launchersprogram&gt;是ccache的安装路径，比如 ccache的安装路径为/usr/bin/ccache，示例如下： set(CMAKE_CXX_comPILER_LAUNCHER /usr/bin/ccache)</td></tr></table>

步骤2 在算子工程目录下执行如下命令，进行算子工程编译。 

./build.sh 

编译成功后，会在当前目录下创建build_out目录，并在build_out目录下生成自定义算 子安装包custom_opp_<target os>_<target architecture>.run。 

用户如果需要编译过程日志存盘，可以使用环境变量ASCENDC_BUILD_LOG_DIR来控 制存储路径。用户设置该选项之后，如果编译过程中无错误产生，则对应的log文件后 缀会添加"_success"，若编译过程有错误产生，则会在屏幕打印对应的报错信息，以及 指示用户log文件的具体路径与文件名，同时，对应log文件后缀会添加“_error” 。 

# 如希望编译日志存储在/home/build_log/，则可以按照如下设置，默认不打开日志存储 export ASCENDC_BUILD_LOG_DIR=/home/build_log/ 

----结束 

# 算子包交叉编译

完成算子代码实现后，如果当前平台架构和运行环境一致则参考上一节的内容进行编 译即可，如果需要实现算子包的交叉编译，您可以参考如下流程。 

步骤1 交叉编译工具下载，下表以Ubuntu系列操作系统为例，展示了编译工具下载命令的样 例。其他操作系统，请替换为实际的下载命令。 


表 2-42 Ubuntu 系列操作系统交叉编译工具下载命令样例


<table><tr><td>当前平台架构</td><td>运行环境平台架构</td><td>编译工具下载命令</td></tr><tr><td>x86_64</td><td>aarch64</td><td>sudo apt-get install -y g++-aarch64-linux-gnu</td></tr><tr><td>aarch64</td><td>x86_64</td><td>sudo apt-get install g++-x86-64-linux-gnu</td></tr></table>

步骤2 自定义算子工程交叉编译，构建生成自定义算子包。 

1. 修改CMakePresets.json中ENABLE_CROSS_COMPILE为True，使能交叉编译。 "ENABLE_CROSS_COMPILE": { "type": "BOOL", "value": "True" } 

2. 修改CMakePresets.json中CMAKE_CROSS_PLATFORM_COMPILER为安装后的 交叉编译工具路径。 "CMAKE_CROSS_PLATFORM_COMPILER": { "type": "PATH", "value": "/usr/bin/aarch64-linux-gnu-g++" } 

3. 在算子工程目录下执行如下命令，进行算子工程交叉编译。 

./build.sh 

编译成功后，会在当前目录下创建build_out目录，并在build_out目录下生成自定 义算子安装包custom_opp_<target os>_<target architecture>.run 

----结束 

# 支持自定义编译选项

在算子工程中，如果开发者想对算子kernel侧代码增加一些自定义的编译选项，可以 参考如下内容进行编译选项的定制。 

修改算子工程op_kernel目录下的CMakeLists.txt，使用add_ops_compile_options来增 加编译选项，方法如下： 

```txt
addOps.compile-options(Opacity Compute_UNIT soc_version1 soc_version2 ... OPTIONS option1 option2...) 
```

具体参数的介绍如下： 


表2-43 具体参数介绍


<table><tr><td>参数名称</td><td>可选/必选</td><td>参数描述</td></tr><tr><td>OpType（算子类型）</td><td>必选</td><td>第一个参数应传入算子类型，如果需要对算子工程中的所有算子生效，需要配置为ALL。</td></tr><tr><td>COMPUTE_UNIT</td><td>可选</td><td>标识编译选项在哪些AI处理器型号上生效,多个型号之间通过空格间隔。不配置时表示对所有AI处理器型号生效。说明COMPUTE_UNIT具体配置如下:·针对如下产品:在安装AI处理器的服务器执行npu-smi info命令进行查询,获取Name信息。实际配置值为AscendName,例如Name取值为xxxx,实际配置值为Ascendxxxxy。Atlas A2训练系列产品/Atlas A2推理系列产品Atlas 2001/500 A2推理产品Atlas 推理系列产品Atlas 训练系列产品·针对如下产品,在安装AI处理器的服务器执行npu-smi info -t board -i id-c chip_id命令进行查询,获取Chip Name和NPU Name信息,实际配置值为Chip Name_NPU Name。例如Chip Name取值为Ascendxxx,NPU Name取值为1234,实际配置值为Ascendxxx_1234。其中:·id:设备id,通过npu-smi info -l命令查出的NPU ID即为设备id。·chip_id:芯片id,通过npu-smi info -m命令查出的Chip ID即为芯片id。Atlas 350加速卡Atlas A3训练系列产品/Atlas A3推理系列产品</td></tr><tr><td>OPTIONS</td><td>必选</td><td>自定义的编译选项。多个编译选项之间通过空格间隔。·增加-D编译选项,用于在编译时定义宏。OPTIONS -Dname=definition·增加-g -O0等调试用编译选项。·支持传入毕昇编译器编译选项:比如--cce-auto-sync=off,设置该选项可以关闭自动同步功能,自定义算子工程已默认开启,通常无需开发者手动设置。详细内容参见支持自动同步。更多编译选项可以参考毕昇编译器编译选项。·Ascend C框架提供的编译选项,具体内容参考下文详细介绍。</td></tr></table>

# 须知

编译选项是基于“算子类型+AI处理器型号系列”进行配置的，也就是说不同的 “算子类型 $+ \mathsf { A l }$ 处理器型号系列”可以配置不同的编译选项。 add_ops_compile_options(AddCustom COMPUTE_UNIT Ascendxxxyy ... OPTIONS -DNEW_MACRO1 $= \times \times$ ) add_ops_compile_options(AddCustom COMPUTE_UNIT Ascendxxxyy ... OPTIONS -DNEW_MACRO2=xx) add_ops_compile_options(AddCustom COMPUTE_UNIT Ascendxxxyy ... OPTIONS -DNEW_MACRO3=xx) 

● 对相同算子类型 $+ \mathsf { A l }$ 处理器型号系列，做多次编译选项配置，以后配置的为准。 

● 对ALL生效的编译选项和对单一算子生效的编译选项如果没有冲突，同时生效，如 果有冲突，以单一算子的编译选项为准。 

Ascend C框架提供的编译选项介绍如下： 

--tiling_key，设置该选项后，只编译指定的TilingKey相关的kernel代码，用于加 速编译过程。若不指定TilingKey编译，则默认编译所有的TilingKey。配置多个 TilingKey时，TilingKey之间不能有空格。示例如下，其中1、2为tiling_key。 --tiling_key=1,2 

编译宏开关请参考内置编译宏开关。 

--op_relocatable_kernel_binary，设置该选项为true时，会额外编译一份可被重 新链接的二进制文件；不配置或设置为false时该选项均不生效。该选项用于自定 义Tiling下沉算子使能SuperKernel的场景，配置该选项所生成的二进制文件，可 以使算子在SuperKernel编译时直接复用二进制文件，降低编译耗时。 

--kernel-template-input，用于算子工程模板编程，设置该选项后，只编译指定 的模板参数组合相关的Kernel代码，用于加速编译过程。若不设置该选项，则默 认编译所有的模板参数组合。传入的参数为键值对列表，整体需用双引号或单引 号包裹。不同模板参数之间用英文分号（;）分隔，相同模板参数配置多个值时用 英文逗号（,）分隔。配置时不能有空格。示例如下： 

--kernel-template-input="D_T_X=A1,A2;D_T_Y=B;D_T_Z=C" --kernel-template-input='D_T_X=A1,A2;D_T_Y=B;D_T_Z=C' 

配置模板参数组合时，模板参数名需要与Kernel入口处以及Host侧定义的模板参 数名匹配。对于模板参数组合的值，如果存在自定义类型，需要替换为其对应数 字值，如果为原生支持数据类型，则与Kernel入口处入参保持一致。示例如下： 

```c
// Host侧模板参数定义
#	define ADD_TPL_FP16 10
#	define ADD_TPL_FP32 20
ASCENDC_TPL_args_DECL(AddCustomTemplateNativeDtype,
ASCENDC_TPL_DATatype_DECL(D_T_X, C_DT_FLOAT, C_DT_FLOAT16, ASCENDC_TPL_INPUT(0)), ASCENDC_TPL_DTYPE_DECL(D_T_Y, ADD_TPL_FP16, ADD_TPL_FP32),
ASCENDC_TPL_DATatype_DECL(D_T_Z, C_DT_FLOAT, C_DT_FLOAT16, ASCENDC_TPL_OUTPUT(0)), ASCENDC_TPL_UID_DECL(TILE_NUM, ASCENDC_TPL_8_BW, ASCENDC_TPL_UID_MIX, 2, 0, 2, 3, 5, 10, 12, 13, 9, 8),
ASCENDC_TPLBool_DECL(IS_SPLIT, 0, 1), 
```

```txt
ASCENDC_TPL_SEL(  
ASCENDC_TPL_args_SEL(  
ASCENDC_TPL_DATatype_SEL(D_T_X, C_DT_FLOAT),  
ASCENDC_TPL_DTYPE_SEL(D_T_Y, ADD_TPL_FP32),  
ASCENDC_TPL_DATatype_SEL(D_T_Z, C_DT_FLOAT),  
ASCENDC_TPL_UID_SEL(TILE_NUM, ASCENDC_TPL_UID_LIST, 1, 8),  
ASCENDC_TPL Bool_SEL(IS_SPLIT, 0, 1),  
ASCENDC_TPL_DETERMINISTIC_SEL(true),  
ASCENDC_TPL_KERNEL_TYPE_SEL(ASCENDC_TPL_AIV_ONLY),  
),  
ASCENDC_TPL_args_SEL(  
ASCENDC_TPL_DATatype_SEL(D_T_X, C_DT_FLOAT16),  
ASCENDC_TPL_DTYPE_SEL(D_T_Y, ADD_TPL_FP16), 
```

```cpp
ASCENDC_TPL_DATATYPE_SEL(D_T_Z,C_DT_FLOAT16),   
ASCENDC_TPL_UID_SEL(TILE_NUM,ASCENDC_TPL_UL_LIST,1,8),   
ASCENDC_TPL BOOL_SEL(IS_SPLIT,0,1),   
ASCENDC_TPLDETERMINISTIC_SEL(false),   
ASCENDC_TPL_KERNEL_TYPE_SEL(ASCENDC_TPL_AIV_ONLY),   
}；   
endif   
//kernel入口   
if constexpr (std::is SAME_v<D_T_X,float> && std::is SAME_v<D_T_Z,float>) { KernelAdd<D_T_X,float,D_T_Z> op; op.Addx,y,z,tiling_data.totalLength,TILE_NUM); op.Process1(); } else if constexpr (std::is SAME_v<D_T_X, half> && std::is SAME_v<D_T_Z, half>){ KernelAdd<D_T_X, half,D_T_Z> op; op.Addx,y,z,tiling_data.totalLength,TILE_NUM); 
```

编译选项示例如下： 

```txt
--kernel-template-input="D_T_X=10;D_T_Y=half;D_T_Z=10"  
--kernel-template-input="D_T_X=10,20;D_T_Y=half,float;D_T_Z=10,20" 
```

# 2.10.2.6.2 算子包部署

算子包部署指执行自定义算子包的安装，算子工程的编译结果会自动部署到算子包安 装目录下。 

# 算子包部署

步骤1 自定义算子包安装部署。 

在自定义算子包所在路径下，执行如下命令，安装自定义算子包。 

```txt
./custom_opp_<target os>_<target architecture>.run --install-path=<path> 
```

--install-path为可选参数，用于指定自定义算子包的安装目录。支持指定绝对路径， 运行用户需要对指定的安装路径有可读写权限。 

下文描述中的<vendor name>为算子工程编译时CMakePresets.json配置文件中字段 “vendor_name”的取值，默认为“customize” 。 

默认安装场景，不配置--install-path参数，安装成功后会将编译生成的自定义算 子相关文件部署到${INSTALL_DIR}/opp/vendors/<vendor name>目录。$ {INSTALL_DIR}请替换为CANN软件安装后文件存储路径。以root用户安装为例， 安装后文件默认存储路径为：/usr/local/Ascend/cann。 

# 说明

自定义算子包默认安装路径${INSTALL_DIR}/opp/vendors的目录权限与CANN软件包安装 用户和安装配置有关。如果因权限不足导致自定义算子包安装失败，可使用--install- ath 参数并配置环境变量ASCEND_CUSTOM_OPP_PATH来指定安装目录（参考指定目录安 装）或者联系CANN软件包的安装用户修改vendors目录权限来解决。详细的案例请参考 2.10.10.7 调用算子时出现无法打开config.ini的报错和2.10.10.8 算子包部署时出现权限不 足报错。 

指定目录安装场景，配置--install-path参数，安装成功后会将编译生成的自定义 算子相关文件部署到<path>/vendors/<vendor name>目录，并在<path>/ vendors/<vendor name>/bin目录下新增set_env.bash，写入当前自定义算子包相 关的环境变量。 

# 须知

如果部署算子包时通过配置--install-path参数指定了算子包的安装目录，则在使 用自定义算子前，需要执行source <path>/vendors/<vendor_name>/bin/ set_env.bash命令，set_env.bash脚本中将自定义算子包的安装路径追加到环境 变量ASCEND_CUSTOM_OPP_PATH中，使自定义算子在当前环境中生效。 

命令执行成功后，自定义算子包中的相关文件将部署至当前环境中。 

步骤2 以默认安装场景为例，可查看部署后的目录结构，如下所示： 

![](images/5de4c7d5e81bd36b42dbf4b763ff2214656ae65a5a039fae9c2dc85ad5fe4d0f.jpg)


步骤3 配置自定义算子优先级。 

多算子包共存的情况下，若不同的算子包目录下存在相同OpType的自定义算子，则以 优先级高的算子包目录下的算子为准。下面介绍如何配置算子包优先级： 

默认安装场景 

当“opp/vendors”目录下存在多个厂商的自定义算子时，您可通过配置“opp/ vendors”目录下的“config.ini”文件，配置自定义算子包的优先级。 

“config.ini”文件的配置示例如下： 

load_priority=vendor name1,vendor name2,vendor name3 

“load_priority”：优先级配置序列的关键字，不允许修改。 

“vendor name1,vendor name2,vendor name3”：自定义算子厂商的优先 级序列，按照优先级从高到低的顺序进行排列。 

指定目录安装场景 

指定目录安装场景下，如果需要多个自定义算子包同时生效，分别执行各算子包 安装路径下的set_env.bash脚本即可。每次脚本执行都会将当前算子包的安装路 径追加到ASCEND_CUSTOM_OPP_PATH环境变量的最前面。因此可以按照脚本执 行顺序确定优先级：脚本执行顺序越靠后，算子包优先级越高。 

比如先执行source <path>/vendor_name1/bin/set_env.bash，后执行source <path>/vendor_name2/bin/set_env.bash，vendor_name2算子包的优先级高 于vendor_name1。ASCEND_CUSTOM_OPP_PATH示例如下： 

ASCEND_CUSTOM_OPP_PATH=<path>/vendor name2:<path>/vendor name1: 

指定目录安装场景下安装的算子包优先级高于默认方式安装的算子包。 

----结束 

# 多平台算子包部署

支持安装多平台的自定义算子包，安装时同样支持默认路径和自定义路径安装。 

以默认路径安装为例，在aarch64平台上分别安装aarch64平台和x86_64平台算子包， 安装成功后可查看目录结构兼容两种平台类型，如下所示： 

![](images/e8f206b72c864e8cec50038363375808892801cd1326da176b33cac593f4daa9.jpg)


# 2.10.2.7 算子动态库和静态库编译

# 算子库编译

算子动态库和静态库编译是将算子实现代码及相关文件编译为动态库和静态库的过 程。相比自定义算子包编译，动态库和静态库编译能够显著简化集成与部署流程。该 过程包括将算子Kernel实现、Host侧Tiling实现、入图适配文件以及自动生成的单算子 调用实现代码编译链接成动态库和静态库。 

同时会自动生成以下头文件： 

单算子调用aclnn头文件，用于单算子调用场景； 

算子原型定义头文件，用于算子入图场景。 

# 说明

算子动态库和静态库编译支持如下型号： 

● Atlas 350 加速卡 

● Atlas A3 训练系列产品/Atlas A3 推理系列产品 

● Atlas A2 训练系列产品/Atlas A2 推理系列产品 

● Atlas 推理系列产品 

算子动态库和静态库编译的具体步骤如下： 

步骤1 完成工程编译相关配置。 

除了上文介绍的基础配置，算子动态库和静态库编译需要在工程目录下的 CMakePresets.json cacheVariables的配置项中配置ASCEND_PACK_SHARED_LIBRARY 为True，默认为False（会生成run包）。 

```json
"ASCENDPACK_SHAREDLIBRARY":{ "type": "BOOL", "value": "True" } 
```

步骤2 在算子工程目录下执行如下命令，进行算子工程编译。 

```txt
./build.sh 
```

编译成功后，会在${CMAKE_INSTALL_PREFIX}/op_api目录生成以下文件： 

算子原型定义头文件，用于算子入图场景，定义算子的原型。 

单算子调用aclnn头文件，用于单算子调用场景，提供直接调用算子的接口。 

动态库libcust_opapi.so，用于动态链接。 

静态库lib${vendor_name}.a，用于静态链接。 

安装文件${vendor_name}-config.cmake和${vendor_name}-targets.cmake，方 便开发者将多个厂商的算子动态库或静态库集成到一个公共的动态库中，其中$ {vendor_name}是厂商名，也可以理解成同一个算子工程生成的算子package名 称。具体集成方式可以参考算子库集成和使用。 

具体目录结构如下： 

![](images/859ce2ffd5f0a0746076b36980403832e2aad068d3f7758fe67127788f24c99b.jpg)


----结束 

# 算子库集成和使用

# 单算子调用场景

单算子调用场景可以通过如下方式对算子库编译中生成的动态库和静态库进行集 成和使用。 

完整样例可参考静态库集成和使用样例。 

```txt
动态库集成
findpackage({vendor_name}REQUIRED # {vendor_name}为编译生成的算子package名称
PATHS ${CUST_PKG_PATH} # {CUST_PKG_PATH}为编译生成的算子package的存放路
径
NO_DEFAULT_PATH
)
target_linklibraries(op Runner PRIVATE
...
${vendor_name}:shared #已自动包含相关的target依赖
... 
```

静态库集成
findpackage(\${vendor_name} REQUIRED # \${vendor_name}为编译生成的算子package名称
PATHS ${CUST_PKG_PATH} # ${\{\mathrm{CUST\_PKG\_PATH}\}}$ 为编译生成的算子package的存放路
径
NO_DEFAULT_PATH
)
target_linklibraries(op Runner PRIVATE
...
${vendor_name}:static #已自动包含相关的target依赖
... 

```txt
静态库和动态库混合使用场景
findpackage(${vendor_name1} REQUIRED #{$vendor_name1}为编译生成的算子package名称
PATHS ${CUST_PKG_PATH_1} #{$CUST_PKG_PATH_1}为编译生成的算子package的存
放路径
NO_DEFAULT_PATH
)
findpackage(${vendor_name2} REQUIRED #{$vendor_name2}为编译生成的算子package名称
PATHS ${CUST_PKG_PATH_2} #{$CUST_PKG_PATH_2}为编译生成的算子package的存
放路径
NO_DEFAULT_PATH
)
target_linklibraries(op Runner PRIVATE
...
${vendor_name1}:static #已自动包含相关的静态库target依赖
${vendor_name2}:shared #已自动包含相关的动态库target依赖
... 
```

# 说明

● 上文中的算子package存放路径默认指算子工程${CMAKE_INSTALL_PREFIX}/op_api目录， 开发者可以自行将op_api目录下的文件拷贝到自己的目录下，此时${CUST_PKG_PATH}可以 设置为该自定义目录。 

● 由于不同算子工程生成的算子动态库名称相同，如果需要将多个动态库进行集成，需要对 libcust_opapi.so名称进行修改： 

编译前，修改op_host目录中的CMakeLists.txt文件，添加如下代码，设置不同的输出文件 名，从而可以区分不同动态库。 

```txt
set_target_propertysoncust_opapi PROPERTIES OUTPUT_NAME ${vendor_name} 
```

编译后，修改生成的op_api目录中的${vendor_name}-targets.cmake文件，将其中的 libcust_opapi.so修改为lib${vendor_name}.so。保证动态库名称的一致性。 

# 算子入图场景

配置ASCEND_CUSTOM_OPP_PATH环境变量，将动态库libcust_opapi.so的 绝对路径追加到该环境变量。由GE框架在图编译和执行时根据该环境变量搜 索算子动态库并使用。环境变量位置越靠前，算子的优先级越高。 export ASCEND_CUSTOM_OPP_PATH=${CMAKE_INSTALL_PREFIX}/op_api/lib/:$ {ASCEND_CUSTOM_OPP_PATH} 

# 说明

动态库编译和算子包编译功能同时使用时，前者生成的动态库优先级更高。 

如下示例中，path1和path3是算子包编译生成的目录，path2和path4是动态库编译 产物的存放目录，则编译产物的优先级为 $2 > 4 > 1 > 3$ 。 

```txt
ASCENDCustomCustom OPP_PATH=<path1>/vendor_name1:</op_api/lib/:<path3>/ vendor_name3:</path4>/op_api/lib/ 
```

如果开发者通过Ascend Graph进行图开发，除了配置环境变量的方式也可以 采用直接在应用程序的编译文件中链接动态库libcust_opapi.so的方式。 Ascend Graph图开发的相关信息请参考《图引擎开发指南》。动态库链接方 式的so加载优先级高于环境变量配置方式。 

# 2.10.2.8 算子工程编译拓展

使用msOpGen工具创建算子工程时，相关编译脚本被固化在本地，若需使用算子工程 提供的新特性（比如支持MC2算子等），需重新运行msOpGen工具生成工程。为了解 决开发者因功能更新而频繁重建工程的问题，将算子工程的cmake脚本打包到CANN软 件包中。开发者可通过find_package的形式来查找对应的cmake modules包，从而使 用算子工程对外提供的cmake函数接口。 

该开发方式下，开发者参考如下工程目录，自行组织算子工程。目录结构与通过 msOpGen生成的目录结构类似, 但无需再创建cmake与scripts目录，这些目录被打包 至CANN软件包中。以AddCustom算子为例，目录结构如下： 

```txt
AddCustom  
- CMakeLists.txt //算子工程顶层CMakeLists.txt  
- CMakePresents.json //编译配置项，cmake内置功能，若使能则需3.19及以上cmake版本  
- framework //AI框架适配时，算子插件实现文件目录  
- op_host //Host侧实现文件  
- addcustom.cpp //算子原型注册、Shape推导、Tiling实现等内容文件  
- addcustom_tiling.h //算子Tiling定义文件  
- CMakeLists.txt //Host侧CMakeLists文件  
- op_kernel //Kernel侧实现文件  
- Add  
- addcustom.cpp //算子代码实现文件  
- CMakeLists.txt //Kernel侧CMakeLists文件 
```

# CMakeLists.txt 编写方法

算子工程顶层CMakeLists.txt 

a. 使用find_package找到对应的编译库。 

b. 使用npu_op_package设置算子工程的编译产物形态，支持RUN/SHARED/ STATIC, 分别对应算子run包形式、算子动态库形式与算子静态库形式，同 时，该接口还可配置package（即编译产物）的内容和package的安装位置。 

c. 添加需要进行编译的子目录。 

```txt
cmake_minimum_required(VERSION 3.16.0) #指定所需的最低cmake版本号
project(opp)
#1、使用findpackage找到对应的编译库。
#{$ASCEND_CANN-package_PATH}为对应的CANN软件包路径,开发者可直接使用
findpackage(ASC REQUIRED HINTS ${ASCEND_CANN-package_PATH}/compiler/tikcpp/ 
```

```cmake
ascendc_kernel_cmake)
# 2、使用npu_oppackage设置算子工程的编译产物形态。
set.package_name ${vendor_name})
npu_oppackage${package_name} # package name
# RUN模式下会使用该name命名算子部署后的目录，静态库模式下输
出产物为lib${package_name}.a
TYPE RUN #指定编译产物形态，[RUN|STATIC|SHARED]
CONFIG
ENABLE_SOURCE.Package True #是否将源码打包到run包中
ENABLE_BINARY.Package True #是否编译Kernel二进制, SHARED/STATIC模式下必须
指定为True，默认值为True
INSTALL_PATH ${CMAKE_BINARY_DIR}/ #package的安装位置
)#3、添加需要进行编译的子目录。
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/op_host)
add_subdirectory(op_host) #添加子目录op_host进行编译
endif()
if(EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/op_kernel)
add_subdirectory(op_kernel) #添加子目录op_kernel进行编译
endif() 
```

# Host侧CMakeLists.txt

a. 使用npu_op_code_gen生成aclnn单算子调用代码、入图所需的原型定义代 码等。 

b. 单算子调用场景，使用npu_op_library编译aclnn单算子调用库。 

c. 算子入图场景，使用npu_op_library编译算子入图所需的算子原型库。 

d. 使用npu_op_library编译Tiling相关库。 

e. 使用npu_op_package_add添加上述Host侧库至对应package中。 

```cmake
aux_source_directory(\$\{CMAKE_CURRENT_SOURCE_DIR\} ops_srcs)
#1、使用npu_op_code_gen生成aclnn单算子调用代码、入图所需的原型定义代码等。
npu_op_code_gen(
SRC ${ops_srcs}
PACKAGE ${package_name}
package_name对应
COMPILE_OPTIONS -g #编译选项
OUT_DIR ${ASCEND_AUTOGEN_PATH}
JOIN_OP_REF False #可选参数，默认为False。设置为False，仅编译CMakePreset.json中设置的AI
处理器型号对应的算子；设置成True，则编译CMakePreset.json和算子原型注册中共有的AI处理器型号对应的
的算子。
)#2、单算子调用场景，使用npu_op_library编译aclnn单算子调用库。
file(GLOB autogen_aclnn_src ${ASCEND_AUTOGEN_PATH}/aclnn_*.cpp) #将通过
npu_op_code_gen生成的aclnn相关源文件添加至源文件列表中
set_source_files_propertyss({autogen_aclnn_src} PROPERTIES GENERATED TRUE) #设置对应的文件
属性为编译过程中生成的文件
npu_op_library(cust_opapi ACLNN #指定library名称与类型，以及参与
编译的源文件
${autogen_aclnn_src}
target.compile_options(cust_opapi PRIVATE #为对应library添加编译选项，与
通用的cmake语法一致
-fvisibility=hidden
)#3、算子入图场景，使用npu_op_library编译算子入图所需的算子原型库。
file(GLOB proto_src ${ASCEND_AUTOGEN_PATH}/op.proto.cc) #将通过
npu_op_code_gen生成的原型定义相关源文件添加至源文件列表中
set_source_files_propertyss({proto_src} PROPERTIES GENERATED TRUE) #设置对应的文件属性
为编译过程中生成的文件
npu_op_library(cust_op Proto GRAPH #指定library名称与类型，以及参
与编译的源文件
${ops_srcs}
${proto_srcs}
) 
```

```cmake
target.compile-options(cust_op.proto PRIVATE #为对应library添加编译选项,
与通用的cmake语法一致
-fvisibility=hidden
)
#4、使用npu_opLibrary编译Tiling相关库。
file(GLOB fallback_src ${ASCEND_AUTOGEN_PATH}/ fallback_*.cpp) #将通过
npu_op_code_gen生成的Tiling相关源文件添加至源文件列表中
#若算子配置了EnableFallBack会生成该文件
set_source_filesProperties({fallback_src} PROPERTIES GENERATED TRUE) #设置对应的文件属性
为编译过程中生成的文件
npu_op_library(cust_optiling TILING #指定library名称与类型,以及参与编
译的源文件
${ops_srcs}
${ fallback_src}
)
target.compile-options(cust_optiling PRIVATE #为对应library添加编译选项,与
通用的cmake语法一致
-fvisibility=hidden
)
#5、使用npu_oppackage_add添加上述Host侧库到对应package中。
npu_oppackage_add({package_name} #与npu_op-package的
package_name对应
LIBRARY #添加Host侧相关library, library名称与前述
步骤的library名称对应
cust_optiling
cust_opapi
cust_op.proto
) 
```

Kernel侧CMakeLists.txt 

a. 使用npu_op_kernel_options添加算子编译选项。支持的编译选项可参考编 译选项。 

b. 使用npu_op_kernel_sources指定算子特定目录与编译源文件。 

若算子的源码文件没有平铺在SRC_BASE目录（通过 npu_op_kernel_library设置）下，可以通过KERNEL_DIR指定特定目录。 

若算子的Kernel实现cpp文件需要自定义命名，需同时指定OP_TYPE（算 子类型）和KERNEL_FILE（Kernel实现cpp文件名），以配置两者之间的 对应关系。不配置时，Kernel实现cpp文件名和OpType之间需满足转换 规则。 

c. 使用npu_op_kernel_library编译Kernel库。 

d. 使用npu_op_package_add添加上述Kernel侧库到对应package中。 

```cmake
#1、使用npu_op_kernel_options添加算子编译选项。  
npu_op_kernel_options(ascendc_kernels ALL OPTIONS --save-temp-files -g)#为算子添加编译选项  
#2、使用npu_op_kernel_sources指定算子特定目录与编译源文件。  
npu_op_kernel sources(ascendc kernels #对应的Kernel库名称，与  
npu_op_kernel_library保持一致OP_TYPE AddCustom #若算子的Kernel实现cpp文件需要自定义命  
名，需配置算子类型KERNEL_DIR./Add #将KERNEL_DIR目录与SRC_BASE目录进行拼  
接，作为Kernel实现cpp文件所在的目录COMPUTE_UNIT Ascendxxxyy #设置KERNEL_FILE在Ascendxxxxy型号生  
效KERNEL_FILE add custom.cpp #若算子的Kernel实现cpp文件需要自定义  
命名，需配置Kernel实现cpp文件名）  
#3、使用npu_op_kernel_library编译Kernel库。  
npu_op_kernel_library(ascendc_kernels # Kernel库名称  
SRC_BASE ${CMAKE_SOURCE_DIR}/op_kernel/ #指定kernel侧源码的根目录 
```

```txt
TILING.Library cust_optiling #指定依赖的Tiling库
) #4、添加kernel侧library到package
npu_op.package_add({package_name} #与npu_op.package的
package_name对应
LIBRARY ascendc_kernels #添加Kernel侧相关library，library名称与前
述步骤的library名称对应 
```

# 编译环境选项说明

下表列出了供用户配置和使用的编译环境选项： 

# 说明

● 暂不支持设置Release、Debug版本相关选项。 

● 暂不支持交叉编译相关选项。 


表 2-44 编译环境选项


<table><tr><td>类型</td><td>环境选项</td><td>默认值</td><td>说明</td></tr><tr><td>STRING</td><td>vendor_name</td><td>customize</td><td>标识自定义算子所属厂商的名称。建议开发者自行指定所属厂商名称,避免和其他厂商提供的算子包冲突。</td></tr><tr><td>STRING</td><td>ASCEND_COMPUTE_UNIT</td><td>-</td><td>AI处理器型号。编译对应型号的package。</td></tr><tr><td>PATH</td><td>ASCEND_AUTOGEN_PATH</td><td>&lt;CMAKE_BINARY_DIR&gt;/autogen</td><td>通过npu_op_code_gen生成的aclnn单算调用、入图所需算子原型库等源文件存放路径。</td></tr><tr><td>BOOL</td><td>ENABLE_SOURCEPackage</td><td>TRUE</td><td>是否开启源码编译。如果使用npu_op-package配置了源码和二进制编译相关配置,npu_op-package配置的优先级更高。</td></tr><tr><td>BOOL</td><td>ENABLE_BINARY.Package</td><td>TRUE</td><td>是否开启二进制编译。package的类型配置为SHARED或STATIC时,必须指定为TRUE。如果使用npu_op-package配置了源码和二进制编译相关配置,npu_op-package配置的优先级更高。</td></tr><tr><td>PATH</td><td>ASCEND_CANNpackages_PATH</td><td>-</td><td>CANN软件包路径,默认情况下用户无需配置。开发者可以在编写cmake文件时直接使用。路径示例如下:/usr/local/Ascend/cann。</td></tr></table>

上述编译环境选项可通过两种方式进行配置： 

支持直接通过set命令进行设置。 

```txt
CMakeLists.txt直接使用  
set(vendor_name "customize")  
set(ASCEND.Compute_UNIT "ascendingxxxyy") 
```

通过CMakePresets.json进行设置，若通过该方式设置，则需要安装3.19及以上的 cmake。 

```json
{
    "version": 1,
    "cmakeMinimumRequired": {
        "major": 3,
        "minor": 19,
        "patch": 0
   },
    "configurePresents": [
        {
            "name": "default",
            "displayName": "Default Config",
            "description": "Default build using Unix Makefiles generator",
            "generator": "Unix Makefiles",
            "binaryDir": "${sourceDir}/build_out",
            "cacheVariables": {
                "ASCEND計算ABLE_UNIT": {
                    "type": "STRING",
                    "value": "ascendxxxyy"
            },
            "vendor_name": {
                "type": "STRING",
                "value": "customize"
            }
        }
    }
} 
```

然后使用如下命令进行构建，根据--preset指定的preset进行编译。 

```txt
// Shell环境中cmake构建编译  
cmake -S . -B build_out --preset=default // 在当前目录(.）中寻找CMakePresets.json 
```

# 编译命令说明

package的类型配置为RUN时，可参考如下编译命令进行编译，使用cmake的pack能 力生成run包。 

```shell
#工程根目录下执行  
mkdir -p build_out  
rm -rf build_out/*  
cmake -S . -B build_out --preset=default  
cmake --build build_out --target binary -j${nproc}  
cmake --build build_out --target package -j${nproc} 
```

package的类型配置为SHARED或STATIC时，可参考如下编译命令进行编译： 

```shell
#工程根目录下执行  
mkdir -p build_out  
rm -rf build_out/*  
cmake -S . -B build_out --preset=default  
cmake --build build_out --target binary -j${nproc}  
cmake --build build_out --target install -j${nproc} 
```

# cmake 函数说明

提供如下cmake函数供开发者使用： 

<table><tr><td>类型</td><td>接口</td><td>功能</td></tr><tr><td rowspan="2">package</td><td>npu_op-package</td><td>创建一个package。</td></tr><tr><td>npu_op-package_add</td><td>将目标或文件添加到package中。</td></tr><tr><td rowspan="5">library</td><td>npu_op_library</td><td>创建Host侧库。</td></tr><tr><td>npu_op_kernel_library</td><td>创建Kernel侧库。</td></tr><tr><td>npu_op_kernel_options</td><td>添加Kernel目标编译选项。</td></tr><tr><td>npu_op_kernel_sources</td><td>描述Kernel目标的源码信息。</td></tr><tr><td>npu_op_device_tiling_libRARY</td><td>创建Device侧Tiling库。</td></tr><tr><td>其他</td><td>npu_op_code_gen</td><td>执行代码生成过程，生成aclnn单算子调用代码和入图所需的原型定义代码。</td></tr></table>

# 1. npu_op_package

创建一个package。 

```cmake
npu_op-package(<package_name> TYPE <type> [CONFIG] [ENABLE_SOURCEPKG <value>]  
[ENABLE_BINARY-package <value>] [INSTALL_PATH <path>]) 
```

参数说明如下： 

– <package_name>：必选，package的名称。 

TYPE <type>：必选，package的类型，取值为RUN、SHARED、STATIC。分 别对应算子run包形式、算子动态库形式与算子静态库形式。 

[CONFIG]：可选，用于配置package的内容和安装位置。 

[ENABLE_SOURCE_PKG <value>]：可选，是否将源码打包到package 中，默认为True。 

[ENABLE_BINARY_PACKAGE <value>] ：可选，是否将二进制文件打包 到package中，默认为True。 

[INSTALL_PATH <path>]：可选，指定包的安装路径，默认为 CMAKE_BINARY_DIR。 

[ENABLE_CPACK <value>] ：可选，是否打包，默认为True。对于用户 需要定制打包的场景，可以设置为False，配置为False的情况下直接在 <path>路径下生成编译产物，不会打包为run包。 

# 2. npu_op_package_add

将目标或文件添加到package中。 

```txt
#添加目标  
npu_op-package_add(<package_name> LIBRARY <target_name1> [<target_name2>...])  
#添加文件，仅给run包模式使用  
npu_op-package_add(<package_name> FILES <file_name1> [<file_name2>...] [TYPE <target_type>]  
[PACKAGE_PATH <pkg_path>] 
```

# 参数说明如下：

– <package_name>：必选，package的名称。 

– LIBRARY：必选，指定需要添加到package中的目标名称。 

<target_name1> [<target_name2>...]：必选，目标名称列表。 

FILES：必选，指定需要添加到package中的文件名称。 

<file_name1> [<file_name2>...]：必选，文件名称列表。 

[TYPE <target_type>]：可选，指定文件类型，将文件安装到对应的目录中， 取值为ACLNN、GRAPH。配置为ACLNN，会将文件打包至run包目录下 aclnn单算子调用头文件所在目录，配置为GRAPH，会将文件打包至run包目 录下入图原型定义头文件目录下。 

[PACKAGE_PATH <pkg_path>]：可选，指定文件在包中的相对路径位置。 TYPE和PACKAGE_PATH参数互斥，即只能选择其中一个进行配置。 

# 3. npu_op_library

创建Host侧库。 

```cmake
npu_op_library(<library_name> TYPE <library_type><files>) 
```

参数说明如下： 

<library_name>：必选，Host侧库的名称。 

TYPE <library_type>：必选，Host库的类型，可选值为TILING、ACLNN、 GRAPH、TF_PLUGIN。 

TILING，Tiling相关库。 

ACLNN，aclnn单算子调用库。 

GRAPH，算子入图所需的算子原型库。 

TF_PLUGIN，TensorFlow框架适配相关库。 

– <files>：必选，设置参与编译的源文件。 

# 4. npu_op_kernel_library

创建Kernel侧库。 

```cmake
npu_op_kernel_library(<target_name> SRC_BASE <path> TILING.Library <tiling_target>) 
```

参数说明如下： 

<target_name>：必选，目标的名称。 

SRC_BASE <path>：必选，指定Kernel源码的base目录，要求配置绝对路 径。比如示例中的op_kernel目录的绝对路径。 

– TILING_LIBRARY <tiling_target>：必选，指定依赖的Tiling目标。 

# 5. npu_op_kernel_options

添加Kernel目标编译选项。 

```cmake
npu_op_kernel_options(<target_name> <op_type> [COMPUTE_UNIT <soc_version>] OPTIONS ...) 
```

参数说明如下： 

<target_name>：必选，目标的名称。 

<op_type>：必选，定义配置生效的范围，取值为ALL、OP_TYPE。ALL表示 对所有算子生效，OP_TYPE表示对特定算子生效。 

[COMPUTE_UNIT <soc_version>]：可选，用于设置算子在具体AI处理器型 号上的编译选项，不填写该选项时默认对所有型号生效。 

![](images/fff3ab63ac5f6f6978251d2191ad790ef738bb45c47072825b994bb6f0bbc47a.jpg)


# 说明

<soc_version>具体配置如下： 

● 针对如下产品：在安装AI处理器的服务器执行npu-smi info命令进行查询，获取 Name信息。实际配置值为AscendName，例如Name取值为xxxyy，实际配置值 为Ascendxxxyy。 

Atlas A2 训练系列产品/Atlas A2 推理系列产品 

Atlas 200I/500 A2 推理产品 

Atlas 推理系列产品 

Atlas 训练系列产品 

针对如下产品，在安装AI处理器的服务器执行npu-smi info -t board -i id -c chip_id命令进行查询，获取ChipName和NPUName信息，实际配置值为Chip Name_NPU Name。例如Chip Name取值为Ascendxxx，NPU Name取值为 1234，实际配置值为Ascendxxx 1234。其中： 

id：设备id，通过npu-smi info -l命令查出的NPU ID即为设备id。 

chip_id：芯片id，通过npu-smi info -m命令查出的Chip ID即为芯片id。 

Atlas 350 加速卡 

Atlas A3 训练系列产品/Atlas A3 推理系列产品 

– OPTION...： 必选，传递给编译器的编译选项。 

6. npu_op_kernel_sources 

描述Kernel目标的源码信息，包括设置算子的Kernel实现文件和源码路径等。 

```txt
npu_op_kernel_sources(<target_name> [OP_TYPE <op_type>] [KERNEL_DIR <path>] [COMPUTE_UNIT <soc_version>] [KERNEL_FILE <file>]) 
```

参数说明如下： 

<target_name>：必选，目标的名称。 

– [OP_TYPE <op_type>]：可选，算子类型，必须与KERNEL_FILE同时存在。 

[KERNEL_DIR <path>]：可选，指定Kernel源码相对于SRC_BASE的相对路 径。 

若算子的源码文件没有平铺在SRC_BASE目录（通过npu_op_kernel_library设 置）下，可以通过KERNEL_DIR指定特定目录。 

[COMPUTE_UNIT <soc_version>] ：可选，设置KERNEL_FILE在 <soc_version>型号生效。默认KERNEL_FILE对所有型号生效。 

[KERNEL_FILE <file>]：可选，指定算子入口的Kernel实现文件名。 

若算子的Kernel实现cpp文件需要自定义命名，需同时指定OP_TYPE（算子类 型）和KERNEL_FILE（Kernel实现cpp文件名），以配置两者之间的对应关 系。不配置时，Kernel实现cpp文件名和OpType之间需满足转换规则。 

7. npu_op_device_tiling_library 

创建Device侧Tiling库。使用该选项时，package的类型仅支持配置为RUN（run 包模式）。 

```cmake
npu_op_device_tiling_library(<target_name><type><files>) 
```

参数说明如下： 

<target_name>：必选，目标的名称。 

– <type>：必选，指定Tiling产物的类型。支持取值为SHARED、STATIC。 

<files>：必选，指定Tiling源码文件。 

8. npu_op_code_gen 

执行代码生成过程，生成aclnn单算子调用代码和入图所需的原型定义代码。 

```txt
npu_op_code_gen(SRC <src_files> OUT_DIR <output_dir> PACKAGE <pkg_name>
[COMPILE_OPTIONS ...]) 
```

参数说明如下： 

SRC <src_files>：必选，参与代码生成的源文件范围。 

– OUT_DIR <output_dir>：必选，生成代码的输出路径。 

PACKAGE <pkg_name>：必选，指定生成代码的package名称。 

[COMPILE_OPTIONS ...]：可选，自定义编译过程中的编译选项。 

# 2.10.2.9 单算子 API 调用

单算子API调用方式，是指直接调用单算子API接口，基于C语言的API执行算子。算子 工程创建完成后，基于工程代码框架完成算子原型定义、kernel侧算子实现、host侧 tiling实现，通过工程编译脚本完成算子的编译部署，之后再进行单算子API的调用。 

# 基本原理

完成自定义算子编译后，会自动生成单算子API，可以直接在应用程序中调用。 

单算子API的形式一般定义为“两段式接口”，形如： 

```c
aclnnStatus aclnnXxxGetWorkspaceSize(const aclTensor *src, ..., aclTensor *out, uint64_t *workspaceSize, aclOpExecutor **editor);  
aclnnStatus aclnnXxx(void *workspace, uint64_t workspaceSize, aclOpExecutor *editor, aclrtStream stream); 
```

其中aclnnXxxGetWorkspaceSize/aclnnXxxTensorGetWorkspaceSize为第一段接口， 主要用于计算本次API调用过程中需要多少workspace内存，获取到本次计算所需的 workspaceSize后，按照workspaceSize申请NPU内存，然后调用第二段接口aclnnXxx 执行计算。 Xxx代表算子原型注册时传入的算子类型。 

aclnnXxxGetWorkspaceSize接口的输入输出参数生成规则如下： 

可选输入的命名增加Optional后缀。如下样例中，x是可选输入。 

```javascript
aclnnStatus aclnnXxxGetWorkspaceSize(const aclTensor *xOptional, ..., aclTensor *out, uint64_t *workspaceSize, aclOpExecutor **executor); 
```

输入输出同名、使用同一个Tensor承载的情况下，生成的aclnn接口中只保留 input参数同时去掉input的const修饰，并以Ref作为后缀。如下样例中，原型定义 input、output都定义为x，xRef既作为输入，又作为输出。 

```javascript
aclnnStatus aclnnXxxGetWorkspaceSize(aclTensor *xRef, ..., uint64_t *workspaceSize, aclOpExecutor **executor); 
```

如果仅有一个输出，输出参数命名为out；如果存在多个输出，每个输出后面都以 Out作为后缀。 

```c
// 仅有一个输出  
aclnnStatus aclnnXxxGetWorkspaceSize(const aclTensor *src, ..., aclTensor *out, uint64_t *workspaceSize, aclExecutor **executor);  
// 存在多个输出  
aclnnStatus aclnnXxxGetWorkspaceSize(const aclTensor *src, ..., aclTensor *yOut, aclTensor *y1Out, ..., uint64_t *workspaceSize, aclExecutor **executor); 
```

如果算子包含属性，则属性参数的位置介于输入输出之间。如下示例中，x是算子 输入，negativeSlope是算子属性，out是算子输出。 

```javascript
aclnnStatus aclnnXxxGetWorkspaceSize(const aclTensor *x, double negativeSlope, aclTensor *out, uint64_t *workspaceSize, aclOpExecutor **executor); 
```

当算子原型注册时使用ValueDepend接口标识输入为数据依赖输入时，会额外生成一 个API，该API支持值依赖场景输入数据为空的一阶段计算。 

```javascript
aclnnStatus aclnnXxxTensorGetWorkspaceSize(const aclTensor *src, ..., aclTensor *out, uint64_t *workspace, aclOpExecutor **executor); 
```

在aclnnXxxTensorGetWorkspaceSize中，aclnnXxxGetWorkspaceSize参数的数据 类型（aclIntArray、aclFloatArray和aclBoolArray）将被转换为aclTensor数据类型， 其他输入输出参数生成规则与aclnnXxxGetWorkspaceSize一致。如下示例中，x0、 x1、x2是算子声明为数据依赖的输入，数据类型分别为DT_INT64、DT_BOOL、 DT_FLOAT，out是算子输出。 

aclnnStatus aclnnXxxGetWorkspaceSize(const aclIntArray $^ { \star } \times 0$ , const aclBoolArray $^ { \star } \times 1$ , const aclFloatArray *x2, aclTensor *out, uint64_t *workspaceSize, aclOpExecutor **executor); aclnnStatus aclnnXxxTensorGetWorkspaceSize(const aclTensor $^ { \star } \mathrm { x } 0 _ { i }$ , const aclTensor $^ { \star } \times 1$ , const aclTensor *x2, aclTensor *out, uint64_t *workspaceSize, aclOpExecutor **executor); 

# 前置步骤

参考2.10.2.2 创建算子工程完成自定义算子工程的创建。 

参考2.10.2.4 Kernel侧算子实现完成kernel侧实现的相关准备，参考2.10.2.5 Host侧Tiling实现、2.10.2.3 算子原型定义完成host侧实现相关准备。 

对于算子包编译场景，参考2.10.2.6.1 算子工程编译、2.10.2.6.2 算子包部署完成 算子的编译部署，编译部署时需要开启算子的二进制编译功能：修改算子工程中 的编译配置项文件CMakePresets.json，将ENABLE_BINARY_PACKAGE设置为 True。编译部署时可将算子的二进制部署到当前环境，便于后续算子的调用。 

```txt
"ENABLE_BINARY-package": { "type": "BOOL", "value": "True" }, 
```

算子编译部署后，会在算子包安装目录下的op_api目录生成单算子调用的头文件 aclnn_xx.h和动态库libcust_opapi.so。 

以默认安装场景为例，单算子调用的头文件.h和动态库libcust_opapi.so所在的目 录结构，如下所示： 

```txt
opp//算子库目录 vendors //自定义算子所在目录 config.ini vendor_name1//存储对应厂商部署的自定义算子，此名字为编译自定义算子安装包时配置的vendor_name，若未配置，默认值为customize op api include aclnn_xx.h lib libcust_opapi.so 
```

对于算子动态库编译场景，参考2.10.2.7 算子动态库和静态库编译完成算子的编 译。编译完成后会在如下路径生成单算子调用的头文件aclnn_xx.h和动态库 libcust_opapi.so。其中CMAKE_INSTALL_PREFIX为开发者在cmake文件中配置的 编译产物存放路径。 

动态库路径：${CMAKE_INSTALL_PREFIX}/op_api/lib/libcust_opapi.so 

头文件路径：${CMAKE_INSTALL_PREFIX}/op_api/include 

# 准备验证代码工程

代码工程目录结构如下，您可以单击LINK，获取样例工程的完整样例： 

CMakeLists.txt // 编译规则文件 main.cpp // 单算子调用主体流程实现文件 

# 单算子调用流程

单算子API执行流程如下： 


图 2-49 单算子 API 执行接口调用流程


![](images/2f0b0f53ae4c236ce30747056f0719f22cb003fb8e1b7095cb7784c7da6b3951.jpg)


本节以AddCustom自定义算子调用为例，介绍如何编写单算子调用的代码逻辑。其他 算子的调用逻辑与Add算子大致一样，请根据实际情况自行修改代码。 

以下是关键步骤的代码示例，不可以直接拷贝编译运行，仅供参考，调用接口后，需 增加异常处理的分支，并记录报错日志、提示日志，此处不一一列举。 

# 说明

因为单算子API执行方式，会自动在编译工程的build_out/autogen目录下生成.cpp和.h，编写单 算子的调用代码时，要包含自动生成的单算子API执行接口头文件。示例如下： 

```txt
include"aclnnaddcustom.h" 
```

```txt
//1.初始化  
CHECK_ACL(aclnnInit(nullptr));  
//2.运行管理资源申请  
const int32_t deviceld = 0;  
CHECK_ACL(aclrtSetDevice(deviceld));  
//3.申请内存存放算子的输入输出 
```

```txt
// 4.传输数据  
CHECK_ACL(aclstMemcpy(input0DeviceMem, bufferSize, input0HostData.data(), bufferSize, ACL_MEMCPY_HOST_TO_DEVICE));  
CHECK_ACL(aclstMemcpy(input1DeviceMem, bufferSize, input1HostData.data(), bufferSize, ACL_MEMCPY_HOST_TO_DEVICE)); 
```

```c
// 5.计算workspace大小并申请内存  
uint64_t workspaceSize = 0;  
aclOpExecutor* executor = nullptr;  
CHECK_ACL(aclnnAddCustomGetWorkspaceSize(input0, input1, output0, &workspaceSize, &executor));  
void* workspaceDeviceMem = nullptr;  
if (workspaceSize > 0) {  
    CHECK_ACL(aclstMalloc(&workspaceDeviceMem, workspaceSize, ACL_MEM_malloc Huge_FIRST));  
} 
```

```txt
// 6.执行算子  
CHECK_ACL(aclnnAddCustom WorkspaceDeviceMem, workspaceSize, executor, stream)); 
```

```javascript
// 7.同步等待  
CHECK_ACL(aclrtSynchronizeStreamstream)); 
```

```txt
// 8. 处理执行算子后的输出数据，例如在屏幕上显示、写入文件等，由用户根据实际情况自行实现 // .... 
```

```txt
// 9.释放运行管理资源  
CHECK_ACL(aclrtResetDevice(devicld));  
// ...  
// 10.去初始化  
CHECK_ACL(aclnnFinalize()); 
```

# CMakeLists 文件

算子编译后，会生成单算子调用的头文件aclnn_xx.h和动态库libcust_opapi.so。具体 路径请参考前置步骤。 

编译算子调用程序时，需要在头文件的搜索路径include_directories中增加单算子调用 的头文件目录，便于找到该头文件；同时需要链接cust_opapi动态库并在库文件的搜 索路径link_directories中增加libcust_opapi.so所在目录。 

在头文件的搜索路径include_directories中增加单算子调用的头文件目录。以下样 例仅为参考，请根据头文件的实际目录位置进行设置。 

```txt
target includeldirections execute_add_op PRIVATE $ENV{ASCEND_HOME_PATH}/include 
```

```txt
$ENV{ASCEND_OPP_PATH}/vendors/customize/op api/include 
```

链接cust_opapi链接库。 target_link_libraries(execute_add_op PRIVATE cust_opapi nnopbase acl_rt 

在库文件的搜索路径link_directories中增加libcust_opapi.so所在目录。以下样例 仅为参考，请根据库文件的实际目录位置进行设置。 target_link_directories(execute_add_op PRIVATE $ENV{ASCEND_HOME_PATH}/lib64 $ENV{ASCEND_OPP_PATH}/vendors/customize/op_api/lib 

# 编译与运行

1. 开发环境上，设置环境变量，配置单算子验证程序编译依赖的头文件与库文件路 径，如下为设置环境变量的示例。${INSTALL_DIR}请替换为CANN软件安装后文 件存储路径。以root用户安装为例，安装后文件默认存储路径为：/usr/local/ Ascend/cann。{arch-os}为运行环境的架构和操作系统，arch表示操作系统架 构，os表示操作系统，例如x86_64-linux或aarch64-linux。 export DDK_PATH=${INSTALL_DIR} export NPU_HOST_LIB=${INSTALL_DIR}/{arch-os}/devlib 

2. 编译样例工程，生成单算子验证可执行文件。 

a. 切换到样例工程根目录，然后在样例工程根目录下执行如下命令创建目录用于存放编译文件，例如，创建的目录为“build”。 mkdir -p build 

b. 进入build目录，执行cmake编译命令，生成编译文件 命令示例如下所示： cd build cmake ../src -DCMAKE_SKIP_RPATH=TRUE 

c. 执行如下命令，生成可执行文件。 make 会在工程目录的output目录下生成可执行文件execute_add_op。 

3. 执行单算子 

a. 以运行用户（例如HwHiAiUser）拷贝开发环境中样例工程output目录下的 execute_add_op到运行环境任一目录。 

说明： 若您的开发环境即为运行环境，此拷贝操作可跳过。 

b. 在运行环境中，执行execute_add_op文件： 

chmod $+ { \sf x }$ execute_add_op ./execute_add_op 

如果有test pass，表明执行成功。 

# 2.10.3 算子入图（GE 图）开发

# 2.10.3.1 概述

图模式是神经网络模型的一种运行模式，在图模式下用户首先将模型的计算过程构造 成一张图，然后通过GE将图下发到昇腾硬件执行。相对于单个算子依次下发的方式， 图模式下，GE可以通过计算图优化、多流并行、内存复用、模型下沉等技术手段，加 速模型执行效率，减少模型内存占用。 

算子入图的开发流程如下图所示：算子工程创建完成后，基于工程代码框架完成算子 原型定义、kernel侧算子实现、host侧tiling实现并完成算子入图开发，通过工程编译 脚本完成算子的编译部署，之后即可基于图IR执行算子，比如单算子模型执行或者IR构 图的方式调用自定义算子。该开发流程以2.10.2 工程化算子开发为基础，除了需要提 供工程化算子开发中的算子实现文件外，还需要额外交付算子入图的代码文件。 

![](images/a8c9e9e5ea5eb04c38560b46c8ac6dde95defc0eb4bde9d4bcc1dd447b9a6aa3.jpg)


步骤1 环境准备。 

1. CANN软件安装请参考1.2 环境准备。 

2. 创建算子工程。使用msOpGen工具创建算子开发工程。 

步骤2 算子实现。 

算子原型定义。通过原型定义来描述算子输入输出、属性等信息以及算子在AI处 理器上相关实现信息，并关联tiling实现等函数。 

Kernel侧算子实现和host侧tiling实现请参考3.3 SIMD算子实现；工程化算子开 发，支持开发者调用Tiling API基于CANN提供的编程框架进行tiling开发，kernel 侧也提供对应的接口方便开发者获取tiling参数，具体内容请参考2.10.2.4 Kernel 侧算子实现和2.10.2.5 Host侧Tiling实现，由此而带来的额外约束也在上述章节 说明。 

步骤3 算子入图（GE图）开发。算子入图场景下，需要提供shape推导等算子入图适配函数 的实现。 

步骤4 编译部署。通过工程编译脚本完成算子的编译部署，分为算子包编译和算子动态库编 译两种方式。 

步骤5 图编译和图执行：基于图IR执行算子，比如单算子模型执行或者IR构图的方式调用自定 义算子。 

----结束 

# 2.10.3.2 基本开发流程

该开发流程以2.10.2 工程化算子开发为基础，除了需要提供工程化算子开发中的算子 实现文件外，还需要额外交付算子入图的代码文件。本节仅提供算子入图代码文件的 开发指导。 

假设下图是我们需要使用的网络模型，您可能会想直接逐个算子调用，根据输入 tensor得到输出tensor就可以完成网络的运行，但在图模式场景下，实际的网络模型生 成过程中，会先进行tensor shape以及datatype的推导。这样可以让我们在图执行之 前，就知道各tensor的数据类型和形状，提前校验其正确性；同时提前推理出算子的 输出张量描述，包括张量的形状、数据类型及数据排布格式等信息，算子构图准备阶 段就可以为所有的张量静态分配内存，避免动态内存分配带来的开销。 

下面的网络模型经过shape和datatype推导之后，可以得到灰色底纹框中的推导信息： 


图 2-50 shape 与 datatype 推导示意图


![](images/a38a88eac91f59c450c7f584eaaf715f0604ef49c59b0d229dfa27676fefea5e.jpg)


除了tiling实现外，算子入图时需要额外提供的实现代码有以下几种： 

datatype推导：根据算子的输入datatype、算子逻辑及算子属性等信息，推理出 算子的输出张量datatype。 

shape推导：根据算子的输入shape、算子逻辑及算子属性等信息，推理出算子的 输出张量shape。 

ShapeRange推导：编译时无法推导输出shape，只能推导输出shape range，执 行完才能得出输出shape。 在下发时需要按照输出shape range来申请最大输出内 存，该类算子需要提供ShapeRange推导函数。 

声明数据依赖：部分算子在InferShape时，需要依赖某个输入的具体值才可以进 行，这类算子被称为“数据依赖算子”，对应的输入被称为“数据依赖输入”。 该类算子在注册时，需要声明其数据依赖输入。 

下表列出了不同类型的算子对上述实现代码的要求。 


表 2-45 不同的类型的算子对入图实现代码的要求


<table><tr><td>分类</td><td>对入图实现代码的要求</td></tr><tr><td>根据输入shape可以推导出输出shape。</td><td>· shape推导
· datatype推导</td></tr><tr><td>依赖输入的价值才能推导出输出shape，即数据依赖算子。如Reshape算子，依赖shape输入的价值才能推导出输出shape。</td><td>· shape推导
· datatype推导
· 声明数据依赖</td></tr><tr><td>编译时无法推导输出shape，只能推导输出shape range，执行完才能得出输出shape。</td><td>· Shape推导（必选）
· DataType推导（必选）
· ShapeRange推导（必选）
· 声明数据依赖（按需）</td></tr></table>

实际开发时通过固定的datatype和shape推导原型实现推导函数，然后再通过 SetInferShape、SetInferDataType接口来关联对应的shape推导函数，样例如下。 

```cpp
namespace ge{ static graphStatus InferShape(gert::InferShapeContext \*context) { ... return GRAPH_SUCCESS; } static graphStatus InferDataType(gert::InferDataTypeContext \*context) { ... return ge::GRAPH_SUCCESS; } } // namespace ge namespace ops { class AddCustom : public OpDef { public: AddCustom(const char\* name) : OpDef(name) { this->Input("x") .ParamType(REQUIRED) .DataType({ge::DT_FLOAT16, ge::DT_FLOAT, ge::DT_INT32}) .Format({ge::FORMAT_ND, ge::FORMAT_ND, ge::FORMAT_ND}); this->Input("y") .ParamType(REQUIRED) .DataType({ge::DT_FLOAT16, ge::DT_FLOAT, ge::DT_INT32}) .Format({ge::FORMAT_ND, ge::FORMAT_ND, ge::FORMAT_ND}); this->Output("z") .ParamType(REQUIRED) .DataType({ge::DT_FLOAT16, ge::DT_FLOAT, ge::DT_INT32}) .Format({ge::FORMAT_ND, ge::FORMAT_ND, ge::FORMAT_ND}); // 根据用户的算子调用方式决定需不需要注册图模式调用方式下需要 this->SetInferShape(ge::InferShape); this->SetInferShapeRange(ge::InferShapeRange); this->SetInferDataType(ge::InferDataType); this->AlCore() .SetTiling(optiling::TilingFunc); // 请替换为实际的昇腾AI处理器型号 this->AlCore().AddConfig("ascendxxx"); } }; OP_ADD(AddCustom); } // namespace ops 
```

# datatype 推导

以AddCustom算子为例，InferDataType的实现如下所示。该样例中输出tensor的数据 类型与输入tensor的数据类型相同，所以直接将任意一个输入tensor的数据类型赋给输 出tensor即可。 

namespace ge{   
static graphStatus InferDataType(gert::InferDataTypeContext\* context)   
{ const auto inputDataType $=$ context->GetInputDataType(0); context->SetOutputDataType(0, inputDataType); return ge::GRAPH_SUCCESS;   
}   
} // namespace ge 

如下示例则给出了更灵活的datatype推导样例，当输入的数据类型为DT_INT4时，其 输出的数据类型为DT_INT32。 

```cpp
ge::graphStatus InferDataTypeForFoo(gert::InferDataTypeContext* context) { if(context->GetInputDataType(0) == DT_INT4){ context->SetOutputDataType(0,DT_INT32); }   
} 
```

# shape 推导

简单的shape推导逻辑可以使用Follow接口来表达，比如输出shape和输入shape相同 的情况。示例如下：输出“y1”Follow输入“x1”场景，指定Follow模式为SHAPE， 此时“y1”的shape将会和“x1”保持一致。 

```txt
this->Input("x1") .ParamType(REQUIRED) .DataType({ge::DT_FLOAT, ge::DT_FLOAT}) .Format({ge::FORMAT_ND, ge::FORMAT_ND}); this->Input("x2") .ParamType(REQUIRED) .DataType({ge::DT_FLOAT, ge::DT_FLOAT}) .Format({ge::FORMAT_ND, ge::FORMAT_ND}); this->Output("y1") .ParamType(REQUIRED) .DataType({ge::DT_FLOAT, ge::DT_FLOAT}) .Format({ge::FORMAT_ND, ge::FORMAT_ND}) .Follow("x1", FollowType::SHAPE); 
```

无法在原型定义中通过Follow表达的情况需要开发者编写InferShape函数，InferShape 函数的原型是固定的，如下示例，接受一个InferShapeContext作为输入，从此context 上可以获取到输入、输出的shape指针等内容。输入shape为const类型，因此 InferShape时，输入shape是只读、不允许修改的。InferShape成功后，返回 ge::GRAPH_SUCCESS，其他返回值被认为推导失败。推导失败后，执行过程结束退 出。 

以ReShape算子为例，InferShape的实现如下所示。根据第1个输入（shape输入）的 值，Reshape算子将第0个输入（x输入）的shape做变换，并输出到其第0个输出（y输 出）上。Reshape的InferShape实现为： 

```cpp
ge::graphStatus InferShapeForReshape(InferShapeContext *context) { const gert::Shape *x_shape = context->GetInputShape(0); // 获取第0个输入的shape const gert::Tensor *shape_tensor = context->GetInputTensor(1); // 获取第1个输入的tensor gert::Shape *output_shape = context->GetOutputShape(0); if (x_shape == nullptr || shape_tensor == nullptr || output_shape == nullptr) { // 防御式编程，不应该出现的场景，打印错误并返回失败 return ge::GRAPH_FAILED; } 
```

```cpp
auto reshape_size = static_cast<int32_t>(shape_tensor->GetShapeSize());  
if (reshape_size < 1) {  
// 防御式编程，不应该出现的场景，打印错误并返回失败  
return ge::GRAPH_FAILED;  
}  
// 根据原型信息，Reshape的shape输入支持INT32与INT64两类，根据不同的类型进入对应的模板函数中做真正的 shape变换操作  
if (shape_tensor->GetDataType() == ge::DT_INT32) {  
int32_t *reshape_data = shape_tensor->GetData<int32_t>();  
return ReshapelnferShapeImpl<int32_t>(reshape_data, *x_shape, *output_shape, reshape_size);  
} else {  
int64_t *reshape_data = shape_tensor->GetData<int64_t>();  
return ReshapelnferShapeImpl<int64_t>(reshape_data, *x_shape, *output_shape, reshape_size);  
} 
```

InferShapeContext public继承自ExtendedKernelContext，因此 ExtendedKernelContext中提供的方法如获取算子type、name、属性等接口均可以在 InferShapeContext实例中调用。 

# 注意

InferShape推导函数和Follow接口不能混用，即不支持部分输出采用Infershape推 导、部分输出采用Follow推导的情况。若用户同时使用了InferShape函数和Follow 接口，以用户的InferShape函数为准，需要保证在InferShape函数中能够推导出所 有的输出shape。 

为了效率考虑，调用InferShape函数时，框架不会为输出shape做初始化，因此， 在InferShape函数中，可以认为输出是未初始化的状态。如果在InferShape时，希 望通过Append方式操作输出shape，需要先将输出shape的DimNum清零，以防止 出现未定义行为。 

# InferShapeRange 实现

某些算子的输出Shape在计算完成后才能确定。比如unique算子，其Shape的推导逻辑 如下： 

给定一维Tensor x，找到其中不重复的元素，返回去重后的Tensor y，输出idx与输入x 大小相同，保存x每个元素在y中的索引。 

```julia
tensor 'x' is [1, 1, 2, 4, 4, 4, 7, 8, 8] x shape[9]  
y, idx = unique(x)  
y => [1, 2, 4, 7, 8] y shape[5]  
idx => [0, 0, 1, 2, 2, 2, 3, 4, 4] idx shape[9] 
```

由此可知，y的shape在编译时为[-1]，unique执行后shape才确定。 

在入图场景执行时，需要在执行前分配输出内存，而内存的大小依赖于输出Shape和数 据类型。对于此类算子，由于输出Shape在执行后才能确定，因此需要根据输出Shape 的范围，按照最大范围申请输出内存，以确保有足够的空间供计算函数写入输出 Tensor。 

这种场景下，开发者需要自行实现InferShapeRange函数，来推导输出Shape的范围。 下面以unique算子为例子，介绍InferShapeRange函数的实现方法。 

```cpp
ge::graphStatus UniqueInferShapeRangeFunc(gert::InferShapeRangeContext *context) { //取输入的shape range auto x_shape_range = context->GetInputShapeRange(0U); 
```

OPS_CHECK_NULL_WITH_CONTEXT(context, x_shape_range);OPS_CHECK_NULL_WITH_CONTEXT(context, x_shape_range->GetMax());OPS_CHECK_NULL_WITH_CONTEXT(context, x_shape_range->GetMin());//开始计算y输出的shape rangeauto y_shape_range $=$ context->GetOutputShapeRange(0U);OPS_CHECK_NULL_WITH_CONTEXT(context, y_shape_range);y_shape_range->GetMax()->SetDimNum(1); //一维向量，rank为1y_shape_range->GetMin()->SetDimNum(1);auto x_max_shape $\equiv$ x_shape_range->GetMax();auto x_shape_dimnum $\equiv$ x_max_shape->GetDim(0); //x为一维Tensor，其shape为[n]，x_shape_dimnum表示x输入的元素个数nif (x_shape_dimnum == 1){//若x输入只有1个元素，不存在去重，y的shape轴最小最大均为1.因此range为[1~1]y_shape_range->GetMax()->SetDim(0,1);y_shape_range->GetMin()->SetDim(0,1);}else{//若x输入有0个元素，或者大于1个元素，去重后，y的元素个数最小为x的min，最大为x的maxy_shape_range->GetMax()->SetDim(0,x_shape_dimnum);y_shape_range->GetMin()->SetDim(0,x_shape_range->GetMin());}//开始计算输出idx的shape range//输出idx表示x元素在y中的索引，其元素个数与x相等，因此shape range与x一致auto idx_shape_range $=$ context->GetOutputShapeRange(1U);OPS_CHECK_NULL_WITH_CONTEXT(context,idx_shape_range);\*(idx_shape_range->GetMax()) $=$ \*(x_shape_range->GetMax()\* $(\mathrm{idx\_shape\_range - > GetMin()}) = \mathrm{*}(x\_shape\_range - > GetMin())$ return ge::GRAPH_SUCCESS; 

# InferShape 时获取属性、输入

在InferShape、Tiling时，可以通过context实例获取算子IR属性值，所谓IR属性，是指 在IR注册时定义的属性，以TransData算子为例： 

```cpp
namespace ops {
class TransData : public OpDef {
public:
    explicit TransData(const char *name) : OpDef(name)
    {
        this->Input("src")
        ...
        this->Output("dst")
        ...
        this->Attr("src_format")
        .AttrType(REQUIRED)
        .String();
        this->Attr("dst_format")
        .AttrType(REQUIRED)
        .String();
        this->Attr("group")
        .AttrType(OPTIONAL)
        .Int(1);
    }
}; 
```

其原型定义中声明了src_format、dst_format、group三个属性，可以通过如下方式获 取算子属性： 

```cpp
ge::graphStatus ExampleGetTransDataAttr(TilingContext *context) { // 获取所有属性 const RuntimeAttributes *attrs = context->GetAttributes(); 
```

```cpp
ASSERT_NOT_NULL(attributes); // 按照在原型定义中的顺序，使用index获取属性，index从0开始计数 const char *src_format = attrs->GetAttrPointer(char>(0); // 获取src_format，src_format是第一个属性，因此index为0 const char *dst_format = attrs->GetAttrPointer(char>(1); // 获取dst_format，dst_format是第二个属性，因此index为1 const int64_t group = attrs->GetAttrPointer<int64_t>(2); // 获取group，group是第三个属性，因此index为2 return ge::GRAPH_SUCCESS; } 
```

通过index而不是字符串name来索引输入输出，对于带有OPTIONAL、DYNAMIC类型 输入的算子，可能出现实例化后，单纯通过index无法索引到具体输入的问题，以 DynamicRNNV3算子为例： 

```cpp
namespace ops {
class DynamicRNNV3 : public OpDef {
public:
explicit DynamicRNNV3(const char *name) : OpDef(name)
{
    this->Input("x");
    .ParamType(REQUIRED)
    ...
    this->Input("w");
    .ParamType(REQUIRED)
    ...
    this->Input("b");
    .ParamType(REQUIRED)
    ...
    this->Input("seq_length");
    .ParamType(OPTIONAL)
    ...
    this->Input("init_h");
    .ParamType(OPTIONAL)
    ...
    this->Input("init_c");
    .ParamType(OPTIONAL)
    ...
    this->Input("wci");
    .ParamType(OPTIONAL)
    ...
    this->Input("wcf");
    .ParamType(OPTIONAL)
    ...
    this->Input("mask");
    .ParamType(OPTIONAL)
    ...
    this->Input("mask");
    .ParamType(OPTIONAL)
    ...
    this->Input("project");
    .ParamType(OPTIONAL)
    ...
} 
```

由于DynamicRNNV3算子有连续的多个optional输入，这导致init_h及其后面的输入的 实例化后index都是不确定的，对于这种类型的算子，可以通过 GetOptionalInputShape传入原型对应的index来获取对应的输入shape等数据，以 InferShape为例： 

```txt
ge::graphStatus InferShapeForDynamicRNNV3(InferShapeContext *context) { // 对于前两个输入，不受到optional或dynamic的影响，可以按照常规方法获取输入shape 
```

auto x_shape $=$ context->GetInputShape(0); auto w_shape $=$ context->GetInputShape(1); if (x_shape $= =$ nullptr || w_shape $= =$ nullptr){ return ge::GRAPH_FAILED; } int64_t state_size $= 0$ //在原型定义上，project是第11个输入(从0开始计数) constexpr int64_t kProjectInputIndex $= 11$ //受到前面optional输入影响的，project实例化后输入的index是不确定的，通过GetOptionallInputShape来获取对应的输入shape， //GetOptionallInputShape的入参为原型上对应的index auto project_shape $=$ context->GetOptionallInputShape(kProjectInputIndex); if (project_shape != nullptr){ if (project_shape->GetDimNum() < 2){ return ge::GRAPH_FAILED; } state_size $=$ project_shape->GetDim(1); } //更多的infershape逻辑... return ge::GRAPH_SUCCESS; } 

对于dynamic类型的输入，实例化后的输入可能是一到多个，对于此类输入，获取方 式为： 

```javascript
//ir_index：此输入在原型定义中的index，从0开始计数  
//relative_index：该输入实例化后的相对index，从0开始计数，例如某个DYNAMIC_INPUT实例化了3个，要取第二个，那么relative_index = 1  
auto shape = context->GetDynamicInputShape(ir_index, relative_index); 
```

本节举例的获取optional、dynamic输入的方式，在InferShape、Tiling函数中均可以 调用。 

# 数据依赖

一般来说，具备输入shape后，算子可以通过InferShape推导出输出shape。然而部分 算子在InferShape时，需要依赖某个输入的具体值才可以进行，这类算子被称为“数 据依赖算子”，对应的输入被称为“数据依赖输入”。以Reshape算子为例，其依据 shape输入的描述，对输入的shape做调整，因此Reshape算子依赖shape输入的值。这 类算子需要在原型定义时通过ValueDepend接口声明对应的输入为数据依赖输入。 

```cpp
namespace ops {
class Reshape : public OpDef {
public:
    explicit Reshape(const char *name) : OpDef(name)
    {
        ...
        this->Input("shape")
        .ParamType(REQUIRED)
        ...
        .ValueDepend(REQUIRED) // 声明 ReShape 算子的 shape 输入为数据依赖输入
        ...
    }
}; 
```

根据第1个输入（shape输入）的值，Reshape算子将第0个输入（x输入）的shape做变 换，并输出到其第0个输出（y输出）上。Reshape的InferShape实现为： 

```cpp
// shape变换具体实现  
template<typename T>  
ge::graphStatus ReshapeInferShapeImpl(const T *reshape_dims, const gert::Shape &x_shape, gert::Shape &output_shape, int32_t reshape_rank) {  
constexpr T UNKNOWN_DIM = -1; 
```

```cpp
//将算子输出的维度数设置为reshape后的维度数reshape_rank
output_shape.SetDimNum(reshape_rank);
auto x_shape_size = x_shape.GetShapeSize();
int64_t output_shapsize = 1;
size_t unknown_dimidx = std::numericlimits< size_t>::max(   );
for (int32_t i = 0; i < reshape_rank; i++) \{
	if (reshape_DIM[i] != UNKNOWN_DIM) \{ // reshape后某一轴的维度值不为-1
	.output_shape.SetDim(i, reshape_DIM[i]); // 设置输出的维度值为reshape后的维度值
	.output_shape * = reshape_DIM[i]; // 计算当前输出元素数量
	\} else \{
	(output_shape.SetDim(i, 1); // reshape后某一轴的维度值为-1，临时设置输出的维度值为1，后续计算
	后看是否可以推导出确定值，并记录未知维度的索引
	unknown_dimidx = i;
	\}
	if (unknown_dimidx == std::numericlimits< size_t>::max(   ) && output_shapesize == x_shape_size) \{
		return ge::GRAPH_SUCCESS; // 不存在未知维度，且输出shape size和输入x的shape size一致，直接返回
成功
	\} else if (unknown_dimidx != std::numericlimits< size_t>::max(   ) && x_shape_size % output_shapesize == 0) \{
	(output_shape.SetDim(unknown_dimidx, x_shape_size / output_shapesize); // 存在未知维度，根据输入
shape动态调整未知维度值保持总元素个数不变
		return ge::GRAPH_SUCCESS;
	\}
	return ge::GRAPH_FAILED;
\}
ge::graphStatus InferShapeForReshape(InferShapeContext *context) \{
 const gert::Shape *x_shape = context->GetInputShape(0); // 获取第0个输入的shape
 const gert::Tensor *shape=tensor = context->GetInputTensor(1); // 获取第1个输入的tensor
 gert::Shape *output_shape = context->GetOutputShape(0);
 if (x_shape == nullptr || shape_tensor == nullptr || output_shape == nullptr) \{
	// 防御式编程，不应该出现的场景，打印错误并返回失败
	return ge::GRAPH_FAILED;
	\}
auto reshape_size = static_cast<int32_t>(shape_tensor->GetShapeSize());
if (reshape_size < 1) \{
	// 防御式编程，不应该出现的场景，打印错误并返回失败
	return ge::GRAPH_FAILED;
\}
// 根据原型信息，Reshape的shape输入支持INT32与INT64两类，根据不同的类型进入对应的模板函数中做真
正的shape变换操作
if (shape_tensor->GetDataType() == ge::DT_INT32) \{
	int32_t *reshape_data = shape_tensor->GetData<int32_t>(   );
	return ReshapelnferShapelImpl< int32_t>(reshape_data, *x_shape, *output_shape, reshape_size);
\} else \{
		int64_t *reshape_data = shape_tensor->GetData<int64_t>(   );
	return ReshapelnferShapelImpl< int64_t>(reshape_data, *x_shape, *output_shape, reshape_size);
\} 
```

# 注意

● 只有声明过数据依赖的输入，才可以在InferShape时调用GetInputTensor等获取 tensor的接口获取其对应的tensor数据。若对一个未声明数据依赖的输入调用 GetInputTensor等获取tensor的接口，只能在tensor中获取到正确的shape、 format、datatype信息，无法获取到真实的tensor数据地址（获取到的地址为 nullptr）。 

从tensor中获取tensor_data时(GetData<int32_t>或GetData<int64_t>)，使用者需 要保证获取的数据类型是正确的，否则行为是未定义的。 

# 2.10.3.3 使能 Tiling 下沉

在静态图模式下，可以通过整图下沉优化调度性能。将完整的计算图一次性下发至 Device侧，后续执行则无需Host参与，由Device自主完成计算，从而减少Host-Device 交互开销，提升执行效率。部分算子的Tiling计算依赖运行时输入的具体数值（Tiling 值依赖），需在执行时动态计算Tiling参数。针对该场景，可采用Tiling下沉优化方 案：将Tiling计算下沉至Device侧的AI CPU上执行，从而实现计算全程在Device侧高效 完成。 

# 说明

● 基于新版本CANN包（支持Tiling下沉特性）编译生成的Tiling下沉算子，不兼容旧版CANN （不支持Tiling下沉特性）运行环境。 

● 当前仅融合算子（矢量计算和矩阵计算融合）支持进行Tiling下沉。 

● Tiling下沉功能仅支持如下产品型号： 

Atlas A3 训练系列产品/Atlas A3 推理系列产品 

Atlas A2 训练系列产品/Atlas A2 推理系列产品 

Atlas 350 加速卡，暂不支持 

自定义算子使能Tiling下沉的步骤如下，完整样例请参考Tiling下沉算子样例。 

Tiling下沉场景下，算子工程的op_host目录结构如下，Tiling实现文件需单独放在在一 个cpp文件中，示例中为add_custom_tiling_sink_tiling.cpp。 

```txt
op_host  
- addcustom_tiling_sink.cpp // 算子原型定义、InferShape、InferDataType实现  
- addcustom_tilingsink_sink.cpp // Tiling函数实现  
- addcustom_tiling_sink.h // TilingData结构体定义、Tiling函数声明  
- CMakeLists.txt 
```

以AddCustom算子为例，讲解关键代码文件的具体实现方法如下： 

在add_custom_tiling_sink_tiling.h中进行Tiling实现函数的声明 

```c
#ifndef ADDcustom_TILING_SINK_TILING_H
#define ADDcustom_TILING_SINK_TILING_H
#include "register/op_def registery.h"
namespace optingil {
    ge::graphStatus AddCustomSinkTilingFunc(gert::TilingContext* context); // Tiling函数声明
} // namespace optingil
#endif // ADDcustom_TILING_SINK_TILING_H 
```

算子原型定义、InferShape、InferDataType实现文件 

add_custom_tiling_sink.cpp，需包含add_custom_tiling_sink_tiling.h，进行 Tiling函数和算子原型定义的关联。 

Tiling下沉仅适用于存在Tiling值依赖（即当InferShape不依赖输入值，仅Tiling计 算需要输入值）且算子输入为非Const类型的场景，本示例中的输入y通过 ValueDepend配置了非Const类型的Tiling值依赖。 

```lisp
include"add_custom_tiling_sink_tiling.h”//包含头文件   
//...   
namespace ops{   
class AddCustomTilingSink:public OpDef{   
public: explicit AddCustomTilingSink(const char \*name) :OpDef(name) { this->Input("x") .ParamType(REQUIRED) .DataType({ge::DT_FLOAT}) .Format({ge::FORMAT_ND}); this->Input("y") 
```

```cpp
ParamType(REQUIRED)   
.DataType({ge::DT_FLOAT})   
.Format({ge::FORMAT_ND})   
.ValueDepend(OPTIONAL, DependScope::TILING); //表示输入y为Tiling值依赖 this->Output("z")   
.ParamType(REQUIRED)   
.DataType({ge::DT_FLOAT})   
.Format({ge::FORMAT_ND});   
this->SetInferShape(ge::InferShape).SetInferDataType(ge::InferDataType);   
this->AlCore().SetTiling(optiling:AddCustomSinkTilingFunc); //Tiling函数和算子原型定义的关联 //请替换为实际的昇腾AI处理器型号 this->AlCore().AddConfig("ascendxxx");   
}   
};   
OP_ADD(AddCustomTilingSink);   
} // namespace ops 
```

Tiling函数的实现文件add_custom_tiling_sink_tiling.cpp 

Tiling函数中通过判断值依赖InputTensor即输入y的数据指针是否为空指针来 确认当前是否处于编译期。Tiling下沉场景，编译期需要为算子分配内存，包 括其所需的workspace。为了保证运行时的高效性，编译期应根据算子的执 行需求，合理设置所需的workspace最大值，以避免内存不足或浪费。 AddCustomTilingSink样例不需要用户workspace，不涉及设置，此处设置为 固定值仅作为示例。 

完成下沉Tiling函数注册：包含device_op_impl_registry.h头文件，使用宏 DEVICE_IMPL_OP_OPTILING进行注册。 

include"..//op_kernel/addcustom_tiling_sink/addcustom_tiling_sink_tiling_struct.h" #include "add_custom_tiling_sink_tiling.h" #include"register/device_op_impl registery.h" #include "tiling/platform/platform ascendc.h" namespace optiling{ static constexpr uint32_t NUM_BLOCKS $= 8$ . static constexpr uint32_t TILE_NUM $= 3$ . static constexpr size_t MAX_WORKSPACE_SIZE $= 32$ //算子所需用户workspace空间最大值， AddCustomTilingSink算子本身逻辑无需用户workspace空间，此处设置为固定值仅作为示例 static constexpr size_t DEFAULT_WORKSPACE_SIZE $= 0$ . ge::graphStatus AddCustomSinkTilingFunc(gert::TilingContext \*context) { TilingSinkTilingData \*tiling $=$ context->GetTilingData<TilingSinkTilingData $\rightharpoondown$ ); uint32_t totalLength $=$ context->GetInputTensor(0)->GetShapeSize(); context->SetBlockDim(NUM_BLOCKS); tiling->totalLength $=$ totalLength; tiling->tileNum $=$ TILE_NUM; size_t \*currentWorkspace $=$ context->GetWorkspaceSizes(1); auto platform $=$ platform ascendc::PlatformAscendC(context->GetPlatformInfo()); size_t sysWorkspaceSize $=$ platform.GetLibApiWorkSpaceSize(); currentWorkspace[0] $=$ sysWorkspaceSize + DEFAULT_WORKSPACE_SIZE; //设置运行时workspace大 小，此处为系统workspace空间 $^+$ 用户workspace空间 if (context->GetInputTensor(1) != nullptr && context->GetInputTensor(1)->GetData<float $)\equiv$ nullptr){ //通过判断值依赖InputTensor的数据是否为空指针来确认当前是否处于编译期。 //Tiling下沉场景，编译期需要为算子分配内存，包括其所需的workspace。为了保证运行时的高效 性，编译期应根据算子的执行需求，合理设置所需的workspace最大值，以避免内存不足或浪费。 currentWorkspace[0] $=$ sysWorkspaceSize + MAX_WORKSPACE_SIZE; //设置编译期workspace大 小，此处为系统workspace空间 $^+$ 用户 workspace空间最大值 } return ge::GRAPH_SUCCESS; } DEVICE_IMPL_OP_OPTILING(AddCustomTilingSink).Tiling(optiling::AddCustomSinkTilingFunc); //下沉 tiling函数注册 } // namespace optiling 

算子核函数实现 

```cpp
当前Tiling下沉仅支持融合算子，为了模拟融合算子场景，通过  
KERNEL_TASK_TYPE_DEFAULT接口强制指定算子在AIC、AIV混合场景运行。  
extern "C" __global __aicore__void addCustom_tiling_sink(GM_ADDR x, GM_ADDR y, GM_ADDR z,  
GM_ADDR workspace, GM_ADDR tiling)  
{REGISTER_TILING_DEFAULT(TilingSinkTilingData);GET_TILING_DATA(tiling_data, tiling);KERNEL_TASK_TYPE_DEFAULT(Kernel_TYPE_MIX_AIC_1_2); //将算子强制指定在AIC、AIV混合场景  
运行，模拟融合算子场景if AscEND_IS_AIC{return;}AscendC::KernelAdd op;opInit(x, y, z, tiling_data.totalLength, tiling_datatileNum);op.Process();  
} 
```

修改op_host目录下的编译脚本CMakeLists.txt，添加Tiling下沉编译命令。具体代 码如下所示： npu_op_device_tiling_library(cust_opmaster SHARED # 任务名称，固定为cust_opmaster add_custom_tiling_sink/add_custom_tiling_sink_tiling.cpp # Tiling函数实现代码源文件 

# 2.10.3.4 SuperKernel 开发

SuperKernel是一种算子的二进制融合技术，与源码融合不同，它聚焦于内核函数 (Kernel) 的二进制的调度方案，展开深度优化，于已编译的二进制代码基础上融合创 建一个超级Kernel函数（SuperKernel），以调用子函数的方式调用多个其他内核函 数，也就是子Kernel。相对于单算子下发，SuperKernel技术可以减少任务调度等待时 间和调度开销，同时利用Task间隙资源进一步优化算子头开销。 

# 说明

● SuperKernel仅适用于静态图场景。 

● SuperKernel适用于如下型号： 

Atlas A3 训练系列产品/Atlas A3 推理系列产品 

Atlas 350 加速卡 

# 自定义算子支持 SuperKernel

自定义算子支持SuperKernel与普通算子在开发流程上并无显著差异，但需注意一些特 定约束（详见下文）。当前SuperKernel特性仅支持在Pytorch框架使用，所以完成算 子入图（GE图）开发开发后，还需要参考《PyTorch图模式使用指南(TorchAir)》中 的“自定义算子入图”章节，完成Pytorch入图。同时，TorchAir提供标定SuperKernel 范围的能力，用户可根据实际业务需求对融合范围内的算子进行标记和优化配置。具 体内容请参考《PyTorch图模式使用指南(TorchAir)》中的“max-autotune模式功能 >图内标定SuperKernel范围”章节。 

# 开发时的特定约束说明如下：

自定义算子若进行全核同步，需注意子Kernel（即该算子）启动的核数与 SuperKernel的核数一致。若子Kernel启动的核数少于SuperKernel的核数，全核 同步会等待所有核完成，导致卡住超时。 

注：SuperKernel启动核数为子Kernel的最大启动核数。假设SuperKernel包括算 子a（启动核数为4）和算子b（启动核数为2），此时SuperKernel启动核数为4。 

使用SyncAll时，为了解决该问题，可以通过在标定SuperKernel范围时开启 feed-sync-all功能，此时系统会在SuperKernel内子Kernel的其余核中插入 SyncAll指令，防止卡住超时。 

若使用CrossCoreSetFlag和CrossCoreWaitFlag硬同步接口实现全核同步，仅 支持子Kernel启动核数与SuperKernel核数相同。 

若自定义算子的Kernel类型设置为KERNEL_TYPE_MIX_AIC_1_1，因为 

SuperKernel会根据启动核数等信息调整SuperKernel的启动比例，此时需特别注 意该算子也可以适应SuperKernel的1:2启动比例，确保AIC与AIV之间的硬同步操 作正确执行。比如：算子内部使用了AIC与AIV之间的硬同步接口 

（CrossCoreSetFlag和CrossCoreWaitFlag），不要单独指定某些AIV核调用硬同 步接口，使所有AIV核均调用硬同步接口，防止因为硬同步数量不匹配而导致卡死 超时；使用Matmul高阶API时，算子逻辑应保证仅有一个AIV0核调用Matmul接 口，防止启动两个AIV核之后出现AIV1核消息无法接收导致卡死超时。 

在开发自定义算子时，开发者必须确保所有对GM的标量读写操作都按需正确插入 DataCacheCleanAndInvalid指令：在单算子编译场景下，毕昇编译器自动在算子 末尾添加DataCacheCleanAndInvalid指令，刷新整个DCache（数据缓存）。在 SuperKernel中，子Kernel被当做普通函数处理，编译器不会自动插入该指令来确 保数据缓存一致性，开发者需要自行保证避免因容错机制改变而导致错误。 

出于性能考虑，SuperKernel场景下Cache刷新机制如下： 

如果开发者调用GlobalTensor的GetValue和SetValue接口对GM进行标量读写， SuperKernel编译时会自动在两个接口内部插入DataCacheCleanAndInvalid指令 刷新单个Cache Line，保证一定的数据缓存一致性。不会在子Kernel调用前后插 入DataCacheCleanAndInvalid。 

但需要注意的是，过多调用GetValue和SetValue，在SuperKernel场景下会导致性 能劣化，开发者需要尽量减少该接口调用。对于劣化过多的算子，SuperKernel提 供了编译选项dcci-before-kernel-start、dcci-after-kernel-start、dcci-disableon-kernel，可以关闭指定算子内GetValue/SetValue中自动插入的缓存刷新指令 以提升模型性能，最终由模型用户决定是否在SuperKernel调用该算子前或后插入 整个DCache刷新，编译选项具体内容请参考图内标定SuperKernel范围中编译选 项说明。 

特别地，对于Tiling下沉场景，通常会涉及二进制复用优化，无法在线选择上述的 Cache刷新机制，SuperKernel框架统一在每个子Kernel调用前后都插入 DataCacheCleanAndInvalid指令，刷新整个DCache。不会在GetValue和 SetValue自动进行缓存刷新。 

Cache刷新机制示意图如下图所示： 

![](images/d87a9c4932630b517ec540e7029045ebdf413b279a6c50e4ba79ba35c2123f42.jpg)



大量调用调用GlobalTensor Get/SetValue，插入DCCI刷新单个CacheLine，会有性能损耗


在子Kernel中调用GetBlockNum接口获取核数时，无论是否融合SuperKernel，获 取的核数保持不变，不受SuperKernel启动核数的影响。因此，在使用该接口时， 开发者无需特别关注SuperKernel的启动核数，使用方法和开发普通算子时一样。 

针对Atlas A3 训练系列产品/Atlas A3 推理系列产品中，在不使能SuperKernel场 景下，TPipe::Destroy接口内部最后会插入AscendC::PipeBarrier<PIPE_ALL>()指 令，额外保障多个TPipe之间的流水同步；模型中绝大部分算子只会使用一个 TPipe对象，在对象析构时会调用Destroy，为不阻塞SetNextTaskStart和 

WaitPreTaskEnd性能提升，SuperKernel场景下默认关闭了TPipe::Destroy中插入 的AscendC::PipeBarrier<PIPE_ALL>()指令，所以当算子需要多个TPipe对象并手 动调用Destroy函数时，开发者需自行保障TPipe对象间流水的同步。 

# 性能优化建议

# 任务间同步

此外，开发者在进行Kernel侧编程时，可以通过调用SetNextTaskStart和 WaitPreTaskEnd两个任务间接口，进一步提升性能。 

调用SetNextTaskStart后的指令可以和后续其他的子Kernel实现并行，提升整 体性能。如图2-51所示，SuperKernel按序调用子Kernel，为保证子Kernel之 间数据互不干扰，会在子Kernel间插入算子间同步进行保序，子KernelN-1调 用该接口后，之后的指令会和后续子KernelN实现并行。 


图 2-51 通过 SetNextTaskStart 实现并行示意图


![](images/33acf5ab857075d1488441f1d20c09a9d7a976500352fc3f16596ad5a692772c.jpg)


调用WaitPreTaskEnd前的指令可以和前序其他的子Kernel实现并行，提升整 体性能。如图2-52所示，SuperKernel按序调用子Kernel，为保证子Kernel之 间数据互不干扰，会在子Kernel间插入算子间同步进行保序，子Kernel 调 用该接口之前的指令会和前序子KernelN实现并行。 


图 2-52 通过 WaitPreTaskEnd 实现并行示意图


![](images/77040529ca131400deef8fb2a5f5ff133dfae7435b91c96b9f1a485c8f452d2e.jpg)


Tiling下沉场景，可以通过--op_relocatable_kernel_binary编译选项，开启二进制 复用优化，提升编译性能，具体可参考LINK。 

# 2.10.3.5 图编译和图执行

本节通过单算子模型执行的样例来介绍图模式下图编译和图执行流程。单算子模型执 行是指基于图IR执行算子，先编译算子（例如，使用ATC工具将Ascend IR定义的单算 子描述文件编译成算子om模型文件），再调用acl接口加载算子模型，最后调用acl接 口执行算子。下文仅提供单算子模型执行的样例和基础内容讲解，详细内容请参考单 算子模型执行。 

# 环境要求

已参考1.2 环境准备，完成CANN驱动和软件的安装，配置CANN软件所需基本环 境变量。 

安装CANN软件后，使用CANN运行用户进行编译、运行时，需要以CANN运行用 户登录环境，执行source ${INSTALL DIR}/set_env.sh命令设置环境变量。$ {INSTALL_DIR}请替换为CANN软件安装后文件存储路径。以root用户安装为例， 安装后文件默认存储路径为：/usr/local/Ascend/cann。 

已参考2.10.2 工程化算子开发完成算子的开发和部署。 

# 准备验证代码工程

代码工程目录结构如下，您可以单击LINK，获取样例工程的完整样例： 

```txt
aclop_invocation  
addcustom.json //算子描述文件，用于构造单算子模型文件  
CMakeLists.txt  
main.cpp //将单算子编译为om文件并加载om文件执行 
```

# 生成单算子离线模型文件

步骤1 构造静态shape单算子描述文件add_custom_static_shape.json，描述算子的输入、输 出及属性等信息。 

AddCustom静态shape算子的描述文件示例如下： 

```json
{
    "op": "AddCustom",
    "input_desc": [
        {
            "name": "x",
            "param_type": "required",
            "format": "ND",
            "shape": [8, 2048],
            "type": "float16"
        },
    {
        "name": "y",
        "param_type": "required",
        "format": "ND",
        "shape": [8, 2048],
        "type": "float16"
    }
},
"output_desc": [
    {
        "name": "z",
        "param_type": "required",
        "format": "ND",
        "shape": [8, 2048],
        "type": "float16"
    }
] 
```

步骤2 使用ATC工具，将该算子描述文件编译成单算子模型文件（*.om文件） 

ATC工具的命令示例如下： 

```txt
atc --singleop=../addcustomstatic_shape.json --output=. --soc_version=<soc_version> 
```

关键参数解释如下（详细参数说明，请参见《ATC离线模型编译工具用户指 南》。）： 

--singleop：单算子描述文件（json格式）的路径。 

--output：存放om模型文件的目录。 

--soc_version：配置为AI处理器的型号，请根据实际环境进行替换。 

# 说明

AI处理器的型号请通过如下方式获取： 

– 针对如下产品：在安装AI处理器的服务器执行npu-smi info命令进行查询，获取Name 信息。实际配置值为AscendName，例如Name取值为xxxyy，实际配置值为 Ascendxxxyy。 

Atlas A2 训练系列产品/Atlas A2 推理系列产品 

Atlas 200I/500 A2 推理产品 

Atlas 推理系列产品 

Atlas 训练系列产品 

针对如下产品，在安装AI处理器的服务器执行npu-smi info -t board -i id -c chip id命 令进行查询，获取Chip Name和NPU Name信息，实际配置值为Chip Name_NPU Name。例如Chip Name取值为Ascendxxx，NPU Name取值为1234，实际配置值为 Ascendxxx 1234。其中： 

id：设备id，通过npu-smi info -l命令查出的NPU ID即为设备id。 

chip_id：芯片id，通过npu-smi info -m命令查出的Chip ID即为芯片id。 

Atlas 350 加速卡 

Atlas A3 训练系列产品/Atlas A3 推理系列产品 

以上命令执行后，会在output参数指定路径下生成*.om后缀的离线模型文件。 

# ----结束

# 编写验证代码

您可以参考如下样例编写单算子加载、执行的代码逻辑。 

以下是关键步骤的代码示例，不可以直接拷贝编译运行，仅供参考，调用接口后，需 增加异常处理的分支，并记录报错日志、提示日志，此处不一一列举。 

```txt
//1.初始化  
CHECK_ACL(acclInit(nullptr));  
//2.运行管理资源申请  
const int32_t deviceld = 0;  
CHECK_ACL(acltrSetDevice(deviceld));  
//3.加载单算子模型文件（*.om文件）  
CHECK_ACL(aclopModelDir("");  
//4.设置算子的输入，申请内存，然后读取输入数据保存至申请的内存中  
//……  
//5.创建Stream流  
acltrStream stream = nullptr;  
acltrCreateStream(&stream)  
//6.执行算子  
// opType表示算子类型名称，例如AddCustom  
//inputDesc.size()表示算子输入个数，例如AddCustom算子是2个输入  
//inputDesc.data()表示算子输入tensor描述的数组，描述每个输入的format、shape、数据类型  
//inputBuffers.data()表示算子输入tensor数据  
//outputDesc.size()表示算子输出个数，例如AddCustom算子是1个输出  
//outputDesc.data()表示算子输出tensor描述的数组，描述每个输出的format、shape、数据类型  
//outputBuffers.data()表示算子输出tensor数据  
//opAttr表示算子属性，如果算子没有属性，也需要调用aclopCreateAttr接口创建aclopAttr类型的数据  
//stream用于维护一些异步操作的执行顺序 
```

```txt
CHECK_ACL(aclopExecuteV2(opType, inputDesc.size(), inputDesc.data(), inputBuffers.data(), outputDesc.size(), outputDesc.data(), outputBuffers.data(), opAttr, stream));  
// 7.阻塞应用运行，直到指定Stream中的所有任务都完成  
aclrtSynchronizeStream(stream);  
// 8.处理执行算子后的输出数据，例如在屏幕上显示、写入文件等，由用户根据实际情况自行实现  
// ......  
// 9.释放stream流  
aclrtDestroyStream(stream);  
// 10.释放运行管理资源  
aclRet = aclrtResetDevice(deviceld);  
aclRet = aclFinalize();  
// ... 
```

# 运行和验证

1. 开发环境上，设置环境变量，配置单算子验证程序编译依赖的头文件与库文件路 径，如下为设置环境变量的示例。${INSTALL_DIR}请替换为CANN软件安装后文 件存储路径。以root用户安装为例，安装后文件默认存储路径为：/usr/local/ Ascend/cann。{arch-os}为运行环境的架构和操作系统，arch表示操作系统架 构，os表示操作系统，例如x86_64-linux。 export DDK_PATH=${INSTALL_DIR} export NPU_HOST_LIB=${INSTALL_DIR}/{arch-os}/devlib 

2. 编译样例工程，生成单算子验证可执行文件。 

a. 切换到样例工程根目录，然后在样例工程根目录下执行如下命令创建目录用 于存放编译文件，例如，创建的目录为“build” 。 

mkdir -p build 

b. 进入build目录，执行cmake编译命令，生成编译文件 

命令示例如下所示： 

cd build 

cmake ../src -DCMAKE_SKIP_RPATH=TRUE 

c. 执行如下命令，生成可执行文件。 

make 

会在工程目录的output目录下生成可执行文件execute_add_op。 

3. 执行单算子 

a. 以运行用户（例如HwHiAiUser）拷贝开发环境中样例工程output下的 execute_add_op到运行环境任一目录。 

说明： 若您的开发环境即为运行环境，此拷贝操作可跳过。 

b. 在运行环境中，执行execute_add_op文件，验证单算子模型文件。 

chmod $+ \pmb { \mathrm { x } }$ execute_add_op 

./execute_add_op 

如果有test pass，表明执行成功。 

# 2.10.4 AI 框架算子适配

# 2.10.4.1 概述

本章节内容介绍AI框架调用自定义算子的方法。如下图所示，Pytorch支持单算子和图 模式两种，TensorFlow仅支持图模式。 

AI框架调用时，除了需要提供CANN框架调用时需要的代码实现文件，还需要进行插件 适配开发。 

![](images/e5a476cd382967c41cc5c9202dd868b4631f54337fa7b9350433d6eccec4bb0b.jpg)


AI处理器 

# 2.10.4.2 PyTorch 框架

通过PyTorch框架进行模型的训练、推理时，会调用很多算子进行计算。开发者开发的 自定义算子如果需要集成部署到PyTorch框架，有如下几种方式： 

Kernel直调：通过适配torch.library或Pybind注册自定义算子，可以实现PyTorch 框架调用算子Kernel程序。 

单算子API调用：该模式下的适配插件开发流程和具体样例请参见《Ascend Extension for PyTorch 框架特性指南》中的“基于OpPlugin算子适配开发”章 节。 

图模式调用：自定义算子在Pytorch图模式下的适配开发指导请参见《PyTorch图 模式使用指南(TorchAir)》中的“自定义算子入图”章节。 


图 2-53 Pytorch 框架部署方式


![](images/e68923ae95ad2923004ddac62568a3c31fd05fe5a7ea46271834289c3fab7bcd.jpg)


本节主要提供通过torch.library与Pybind注册自定义算子并实现PyTorch框架调用算 子Kernel程序的指导。 

torch.library是用于扩展PyTorch核心算子库的API集合。它允许开发者创建新的算 子、并为其提供自定义实现。 

Pybind是一个开源的C++和Python之间的桥接工具，它旨在使C++代码能够无缝 地集成到Python环境中。 

Pybind适用于快速将C++函数暴露给Python，实现高效接口绑定。但其生成的算子无 法被PyTorch的算子系统识别，不具备schema定义与图追踪能力，因此不支持 torch.compile优化。相比之下，torch.library提供了与PyTorch核心算子系统深度集成 的机制，支持算子注册、schema定义和图追踪能力，是支持torch.compile的必要条 件。开发者可根据需求选择对应方式。 

# torch.library

下面代码以add_custom（Add自定义算子为例）算子为例，介绍通过torch.library如何 调用算子Kernel程序，文档中仅介绍核心步骤，完整样例请参考torch.library样例。 

步骤1 环境准备。 

除了按照1.2 环境准备进行CANN软件包的安装，还需要安装以下依赖： 

安装PyTorch框架 

安装torch_npu插件 

步骤2 实现NPU上的自定义算子。 

包括算子Kernel实现，并使用<<<>>>接口调用算子核函数完成指定的运算。样例中的 c10_npu::getCurrentNPUStream接口用于获取当前npu流，返回值类型NPUStream， 使用方式请参考《Ascend Extension for PyTorch 自定义API参考》中的“（beta） c10_npu::getCurrentNPUStream”章节。 

需要注意的是，本样例的输入x，y的内存是在外层的Python调用脚本中分配的。 

namespace ascendcOps{   
at::Tensor ascendc_add(const at::Tensor&x, const at::Tensor&y)   
{ //运行资源申请，通过c10_npu::GetCurrentNPUStream()的函数获取当前NPU上的流 auto aclStream $=$ c10_npu::GetCurrentNPUStream().stream(false); //分配Device侧输出内存 at::Tensorz $\equiv$ at::empty_like(x); uint32_t numBlocks $= 8$ . uint32_t totalLength $= 1$ · for (uint32_t size:x.size()) { totalLength $\ast =$ size; } 

```cpp
//用<<>>接口调用核函数完成指定的运算addcustom<<numBlocks，nullptr，aclStream>>=((uint8_t\*)(xadera_data_ptr)，(uint8_t\*)yadera_data_ptr()，(uint8_t\*)(zadera_data_ptr()，totalLength);//将Device上的运算结果拷贝回Host并释放申请的资源return z;1}//namespace ascendc ops 
```

步骤3 自定义算子的注册。 

PyTorch提供TORCH_LIBRARY宏作为自定义算子注册的核心接口，用于创建并初始化 自定义算子库，注册后在Python侧可以通过torch.ops.namespace.op_name方式进行 调用。TORCH_LIBRARY_IMPL用于将算子逻辑绑定到特定的DispatchKey（PyTorch设 备调度标识），针对NPU设备，需要将算子实现注册到PrivateUse1这一专属的 


DispatchKey上。


```cpp
//注册算子到torch.library  
TORCH.Library(Tensor x, Tensor y) -> Tensor");  
{  
    m.def("ascendc_add(Tensor x, Tensor y) -> Tensor");  
}  
//注册PrivateUse1实现，NPU设备  
TORCH.Library(IMPL(ascendc ops, PrivateUse1, m))  
{  
    m.impl("ascendc_add", TORCH_fn(ascendc ops::ascendc_add));  
} 
```

步骤4 编译生成算子动态库。 

步骤5 使用Python测试脚本进行测试。 

在add_custom_test.py中，首先通过torch.ops.load_library加载生成的自定义算子库， 调用注册的ascendc_add函数，并通过对比NPU输出与CPU标准加法结果来验证自定义 算子的数值正确性。 

----结束 

# Pybind

下面代码以add_custom算子为例，介绍通过Pybind方式实现Pytorch脚本中调用自定 义算子的流程。文档中仅介绍核心步骤，完整样例请参考Pybind样例。 

步骤1 环境准备。 

除了按照1.2 环境准备进行CANN软件包的安装，还需要安装以下依赖： 

安装PyTorch框架 

安装torch_npu插件 

安装pybind11 

pip3 install pybind11 expecttest 

步骤2 实现NPU上的自定义算子。 

包括算子Kernel实现，并使用<<<>>>接口调用算子核函数完成指定的运算。样例中的 c10_npu::getCurrentNPUStream接口用于获取当前npu流，返回值类型NPUStream， 使用方式请参考《Ascend Extension for PyTorch 自定义API参考》中的“（beta） c10_npu::getCurrentNPUStream”章节。 

需要注意的是，本样例的输入x，y的内存是在Python调用脚本中分配的。 

// Pybind和PyTorch调用所需的头文件 

#include <pybind11/pybind11.h> 

#include <torch/extension.h> 

include"torch_npu/csrc/core/npu/NPUsStream.h"   
// Kernel侧实现需要的头文件   
#include "kernel_operator.h"   
...   
namespace ascendcOps{   
at::Tensor ascendc_add(const at::Tensor&x, const at::Tensor&y)   
{ //运行资源申请，通过c10_npu::GetCurrentNPUsStream()的函数获取当前NPU上的流 auto aclStream $\equiv$ c10_npu::GetCurrentNPUsStream().stream(false); //分配Device侧输出内存 at::Tensorz $\equiv$ at::empty_like(x); uint32_t numBlocks $= 8$ . uint32_t totalLength $= 1$ . for (uint32_t size : x.size()) { totalLength $\ast =$ size; } //用<<>>>接口调用核函数完成指定的运算 addcustom<<numBlocks,nulptr,aclStream>>=((uint8_t*)(x.valid_data_ptr(),(uint8_t*)(y.valid_data_ptr(),(uint8_t*)(z.valid_data_ptr(),totalLength); //将Device上的运算结果拷贝回Host并释放申请的资源 return z;   
}   
} // namespace ascendc ops 

步骤3 定义Pybind模块，将C++函数封装成Python函数。PYBIND11_MODULE是Pybind11库 中的一个宏，用于定义一个Python模块。它接受两个参数，第一个参数是封装后的模 块名，第二个参数是一个Pybind11模块对象，用于定义模块中的函数、类、常量等。 通过调用m.def()方法，可以将上一步骤中函数ascendc_ops::ascendc_add转成Python 函数ascendc_add，使其可以在Python代码中被调用。 

PYBIND11MODULE(ascendingops, m)//模块名ascendingops，模块对象m  
{m.doc() $=$ "addcustom pybind11 interfaces";//optional module docstringm.def("ascending_add",&ascendingOps::ascending_add，""）;//将函数ascending_add与Pybind模块进行绑定} 

步骤4 编译生成算子动态库。 

步骤5 在Python调用脚本中，使用torch接口生成随机输入数据并分配内存，通过导入封装的 自定义模块ascendc_ops，调用自定义模块ascendc_ops中的run_add_custom函数，从 而在NPU上执行算子。 

----结束 

# 2.10.4.3 ONNX 框架

# 2.10.4.3.1 适配插件开发

# 说明

针对Atlas A3 训练系列产品/Atlas A3 推理系列产品，暂不支持ONNX框架算子调用。 

针对Atlas 350 加速卡，暂不支持ONNX框架算子调用。 

您可以参考本章节进行算子适配插件的开发，将ONNX框架的算子映射成适配AI处理 器的算子（下文简称CANN算子），从而完成从ONNX框架调用Ascend C自定义算子 的过程。 

完成算子工程创建后，会在算子工程目录下生成framework/onnx_plugin目录，用于 存放ONNX框架适配插件实现文件。以自定义CANN算子LeakyReluCustom为例，算子 工程目录如下： 

```txt
LeakyReluCustom build.sh //编译入口脚本 
```

![](images/8266c3e2344aaf93fb83bdbff3223451cf8ab6b4c1ce2769591a0edc151751dc.jpg)


下文主要讲解ONNX框架适配插件实现文件（leaky_relu_custom_plugin.cc ）的开发 流程。 

```cpp
include"register/register.h"   
#include"graph/parameter.h"   
#include"json.hpp"   
namespace domi{ Status ParseParamByOpFunc(const ge::Operator& op_src,ge::Operator& op_DEST){ //... 1   
REGISTERcustom_OP("OpType") .FrameworkType(ONNX) .Originotype("OriginOpType") .ParseParamsByOperatorFn(ParseParamByOpFunc//用来注册解析算子属性的函数 .ImplyType(ImplyType::TVM); //Ascend C算子实现类型设置为TVM   
} 
```

# 步骤1 包含所需头文件。

register.h，存储在CANN软件安装后文件存储路径的“include/register/”目录 下，包含该头文件，可使用算子注册相关类，调用算子注册相关的接口。 

operator.h（可选），存储在CANN软件安装后文件存储路径的“include/ graph/”目录下，包含该头文件，可以使用Operator类相关接口，获取算子输入 输出及属性等算子信息。 

json.hpp，用于进行ONNX数据定义的解析，将String类型的算子参数定义转换为 json格式。若样例工程中未提供“json.hpp”文件，用户可以自行下载，并将 “json.hpp”放在工程可以找到的任意路径下，然后包含此头文件即可，下载路 径可参见json.hpp。 

# 步骤2 使用REGISTER_CUSTOM_OP宏，完成CANN算子和ONNX框架的算子映射关系注册。 使用方法如下：

REGISTER_CUSTOM_OP：注册自定义算子，OpType为算子类型名称，需要与算 子原型注册中的OpType保持一致。 

FrameworkType：ONNX代表原始框架为ONNX。 

OriginOpType：算子在原始框架中的类型。例如自定义算子OpTypeA，对应 ONNX算子库版本opset_version=11，应传入“ai.onnx::11::OpTypeA”，当前支 持的ONNX版本范围为9~15。 

ParseParamsByOperatorFn(ParseParamByOpFunc)：用来注册解析算子参数实 现映射关系的回调函数，需要用户自定义实现回调函数ParseParamByOpFunc。 具体实现方式参考步骤3。 

● ImplyType：指定算子的实现方式。Ascend C算子实现类型设置为TVM。 

# 步骤3 实现回调函数ParseParamByOpFunc。其函数声明如下所示：

Status ParseParamByOpFunc(const ge::Operator& op_src, ge::Operator& op_dest) 

ParseParamByOpFunc：函数名称，用户自定义。 

op_src：ONNX框架定义的Operator类对象，包含ONNX模型中自定义的算子属性 信息，定义来源于ONNX框架的原始模型文件。 

op_dest：CANN算子数据结构，保存算子信息。 

开发者需要在回调函数中实现属性的解析和映射，具体实现方式如下： 

ONNX原始模型中，属性为repeated message类型，对于repeated message类型的参 数，可使用GetAttr(const char *name, ge::AscendString &attr_value)接口获取其 属性值，然后将AscendString类型的属性值转换为String类型，再将其转换为json格式 进行属性字段的解析。 


实现如下所示：


Status ParseOnnxParamsLeakyReluCustom(const ge::Operator& op_src, ge::Operator& opDest) { // trans op_src to op_DEST // if op_src get required attr failed, need to return Failed // if op_src get optional attr failed, need to return Failed or set a default value float negative_slope $= 0.01f$ . string negative_slope_str; AscendString attrs_string; //使用固定属性名称“attribute”获取ONNX算子中的属性，并赋值给AscendString类型对象 if (ge::GRAPH_SUCCESS $= =$ op_src.GetAttr("attribute", attrs_string)) { //转换为json格式 json attrs $=$ json::parseattrs_string.GetString(); for (json attr : attrs["attribute']) { if (attr["name"] $= =$ "alpha" && attr["type"] $= =$ kTypeFloat) { negative_slope_str $=$ attr["f"]; //float type in json has accuracy loss, so we use string type to store it negative_slope $=$ atoi(negative_slope_str.c_str()); } } } op_DEST.SetAttr("negative_slope", negative_slope); return SUCCESS;   
} 

# 须知

当前版本GetAttr与SetAttr接口不支持对原始文件中数据类型为double和uint64的 字段进行解析。 

● 使用ATC工具执行模型转换时，对属性的获取情况不会进行强校验。所以进行算子 适配插件实现时，若用户调用GetAttr失败，建议根据算子实际情况增加相应的处理 逻辑，例如，针对必选属性，可返回失败，针对可选属性，可设置默认值。 

# ----结束

# 2.10.4.3.2 调用样例

完成了ONNX框架的适配插件开发后，即可实现从ONNX框架调用Ascend C自定义算 子。下面以一个仅包含LeakyRelu算子的ONNX框架网络为例（该网络中的LeakyRelu 算子通过适配插件映射为自定义的LeakyRelu算子），呈现一个使用推理工具进行推理 的过程，目的在于让您快速体验推理场景下网络中自定义算子调用的过程。 

在完成如下步骤之前，您需要先参考上文内容完成自定义LeakyRelu算子kernel侧和 host侧的开发、ONNX适配插件的开发，并完成算子的编译部署。 

LeakyRelu算子实现的完整样例请参考LINK。ONNX框架调用的完整示例请参考 LINK。 

步骤1 通过如下命令获取ONNX框架网络模型。作为示例，该模型中仅包含一个LeakyRelu算 子。 

wget https://obs-9be7.obs.cn-east-2.myhuaweicloud.com/AscendC/leaky_relu.onnx 

步骤2 执行如下命令生成离线模型。（如下命令中使用的目录以及文件均为样例，请以实际 为准） 

```shell
atc --model=$HOME/module/leaky_relu.onnx --framework=5 --soc_version=<soc_version> --output=$HOME/module/out/leaky_relu --input_shape="X:8,16,1024" --input_format=ND 
```

关键参数的解释如下： 

--model：ONNX框架网络模型文件（*.onnx）的路径。 

--framework：原始框架类型。5表示ONNX。 

--output：转换后的离线模型的路径以及文件名。请注意，记录保存该om模型文 件的路径，后续开发应用时需要使用。 

--soc_version：AI处理器的型号。 

# 说明

AI处理器的型号请通过如下方式获取： 

– 针对如下产品：在安装AI处理器的服务器执行npu-smi info命令进行查询，获取Name 信息。实际配置值为AscendName，例如Name取值为xxxyy，实际配置值为 Ascendxxxyy。 

Atlas A2 训练系列产品/Atlas A2 推理系列产品 

Atlas 200I/500 A2 推理产品 

Atlas 推理系列产品 

Atlas 训练系列产品 

针对如下产品，在安装AI处理器的服务器执行npu-smi info -t board -i id -c chip id命 令进行查询，获取Chip Name和NPU Name信息，实际配置值为Chip Name_NPU Name。例如Chip Name取值为Ascendxxx，NPU Name取值为1234，实际配置值为 Ascendxxx 1234。其中： 

id：设备id，通过npu-smi info -l命令查出的NPU ID即为设备id。 

chip_id：芯片id，通过npu-smi info -m命令查出的Chip ID即为芯片id。 

Atlas 350 加速卡 

Atlas A3 训练系列产品/Atlas A3 推理系列产品 

--input_shape：指定模型输入数据的shape，请基于算子支持的shape范围和实际 使用场景进行设置，这里设置输入X为固定shape [8,16,1024]。 

--input_format：指定模型输入数据的格式，请基于算子支持的格式和实际使用场 景进行设置，这里配置为ND。 

步骤3 使用export ASCEND_GLOBAL_LOG_LEVEL=1改变日志级别为INFO，若出现如下提示 信息，则说明进入了Ascend C自定义算子编译流程且模型转换成功。 

```batch
start compile Ascend C operator LeakyReluCustom. kernel name is leaky_relu_custom   
compile Ascend C operator:LeakyReluCustom success!   
ATC run success 
```

成功执行命令后，在--output参数指定的路径下，可查看离线模型（如： leaky_relu.om）。 

步骤4 通过aclmdlExecute等接口在应用中加载模型执行推理。 

----结束 

# 2.10.4.4 TensorFlow 框架

# 说明

针对Atlas 350 加速卡，暂不支TensorFlow框架算子调用。 

本章节介绍TensorFlow框架算子适配的流程，用于将TensorFlow框架的算子映射成 CANN算子（开发者基于CANN框架自定义开发的算子），从而完成从TensorFlow框架 调用到CANN算子的过程。同时给出TensorFlow框架侧算子调用的示例，便于开发者 了解完整流程。 

下图展示了完整的开发流程，具体步骤如下： 

![](images/c39376fa3beeead7899b49380f1f962901866a68afb6e321f2bbaad86d8dbe6b.jpg)


步骤1 环境准备。 

1. CANN软件安装请参考1.2 环境准备。 

2. 安装框架插件包，请参考《TensorFlow 1.15模型迁移指南》或《TensorFlow 2.6.5模型迁移指南》中的环境准备 > 安装框架插件包章节，获取框架插件包详细 的安装步骤。 

3. 创建算子工程。使用msOpGen工具创建算子开发工程。TensorFlow框架算子适配 场景下，需要通过framework参数指定具体的框架为tf或者tensorflow，工具会自 动生成框架适配代码。以自定义CANN算子AddCustom为例，使用msOpGen工具 创建算子开发工程的具体命令如下： 

${INSTALL_DIR}/python/site-packages/bin/msopgen gen -i $HOME/sample/add_custom.json -f tf -c ai_core-<soc version> -lan cpp -out $HOME/sample/AddCustom 

步骤2 算子实现。 

算子原型定义。通过原型定义来描述算子输入输出、属性等信息以及算子在AI处 理器上相关实现信息，并关联tiling实现等函数。 

Kernel侧算子实现和host侧tiling实现请参考3.3 SIMD算子实现；工程化算子开 发，支持开发者调用Tiling API基于CANN提供的编程框架进行tiling开发，kernel 侧也提供对应的接口方便开发者获取tiling参数，具体内容请参考2.10.2.4 Kernel 侧算子实现和2.10.2.5 Host侧Tiling实现，由此而带来的额外约束也在上述章节 说明。 

步骤3 算子入图（GE图）开发。算子入图场景下，需要提供shape推导等算子入图适配函数 的实现。 

步骤4 TensorFlow框架适配插件开发。详细说明见适配插件开发。 

步骤5 编译部署。通过工程编译脚本完成算子的编译部署，分为算子包编译和算子动态库编 译两种方式。 

步骤6 TensorFlow框架算子调用。详细说明见TensorFlow原生算子映射到CANN算子和 TensorFlow自定义算子开发并映射到CANN算子。完整样例请参考LINK。 

----结束 

# 适配插件开发

完成算子工程创建后，会在算子工程目录下生成framework/tf_plugin目录，用于存放 TensorFlow框架适配插件实现文件。以自定义CANN算子AddCustom为例，算子工程 目录如下： 

![](images/454ec1e8b09abf7012cb47442163d7c6fae16c97d2841561d4c4c7382227dac3.jpg)


当TensorFlow算子与CANN算子原型定义一致时，TensorFlow框架适配插件实现代码 如下： 

```txt
include"register/register.h"   
namespace domi{   
REGISTERCustomOp("AddCustom") .FrameworkType(TENSORFLOW) .OriginOpType("AddCustom") .ParseParamsByOperatorFn(AutoMappingByOpFn);   
} 
```

当TensorFlow算子与CANN算子原型定义不一致时，TensorFlow框架适配插件实现代 码如下： 

```txt
include"register/register.h"   
REGISTERCustomOp("FlashAttentionScore") .FrameworkType(TENSORFLOW) .OriginOpType({"FlashAttentionScore"}） .ParseParamsByOperatorFn(FlashAttentionScoreMapping) .ParseOpToGraphFn(AddOptionalPHAForFA); 
```

包含插件实现函数相关的头文件。 

register.h存储在CANN软件安装后文件存储路径的“include/register/”目录下， 包含该头文件，可使用算子注册相关类，调用算子注册相关的接口。 

REGISTER_CUSTOM_OP：注册自定义算子，传入算子的OpType，需要与算子原 型注册中的OpType保持一致。 

– FrameworkType：TENSORFLOW代表原始框架为TensorFlow。 

OriginOpType：算子在原始框架中的类型。对于TensorFlow自定义算子，还 需要完成TensorFlow自定义算子的开发，这里的OriginOpType与 REGISTER_OP注册算子名相同，对于TensorFlow原生算子， 即为原生算子 名。 

ParseParamsByOperatorFn：用来注册解析算子参数实现映射关系的回调函 数，需要用户自定义实现回调函数ParseParamByOpFunc。原始TensorFlow 算子中参数与CANN算子中参数一一对应时，可直接使用自动映射回调函数 AutoMappingByOpFn自动实现映射。 

ParseOpToGraphFn：当TensorFlow算子与CANN算子原型定义不一致（比如 CANN算子原型定义原型中有可选输入，但TensorFlow原型定义中不支持可 选输入，没有可选输入）的情况时，用来注册调整算子原型映射关系的回调 函数。 

# TensorFlow 原生算子映射到 CANN 算子

以自定义算子AddCustom为例，将该算子映射到TensorFlow内置算子Add上，需要先 修改AddCustom自定义算子目录framework/tf_plugin下插件代码，完成算子名映射： 

```txt
include"register/register.h"   
namespace domi{   
REGISTERCustomOp("AddCustom")//当前AscendC自定义算子名 .ZF FrameworkType(TENSORFLOW) //第三方框架类型TENSORFLOW .OriginOpType("Add") //映射到TensorFlow原生算子Add .ParseParamsByOperatorFn(AutoMappingByOpFn);   
} 
```

完成算子工程的编译部署后，构造单算子的TensorFlow 1.15版本测试用例进行验证。 

步骤1 编写测试用例 “tf_add.py”。 

步骤2 导入python库。 

```txt
importlogging #Python标准库日志模块  
importtensorflow as tf #导入TensorFlow开源库  
fromnpu_bridge.estimator import npu ops #导入TensorFlow开源库中的npu OPS模块  
import numpy as np #导入Python的数学基础库 
```

步骤3 通过config()定义AI处理器和CPU上的运行参数。 

当“execute_type”为“ai_core”时，代表在AI处理器上运行单算子网络，最终会调 用到Ascend C算子。 

当“execute_type”为“cpu”时，代表在Host侧的CPU运行单算子网络，调用的是 TensorFlow算子。 

def configexecute_type): if execute_type $= =$ 'ai_core': session_config $\equiv$ tf.ConfigProto( allowsoft-placement $\equiv$ True, log_device-placement $\equiv$ False,) custom_op $\equiv$ session_config.graph_options rewrite_options(custom_optimizers.add() custom_op.name $\equiv$ "NpuOptimizer" custom_op.parameter_map["enable_data_pre_proc"].b $\equiv$ True #开启数据预处理下沉到Device侧执行 custom_op.parameter_map["mix.compile_mode"].b $\equiv$ True custom_op.parameter_map["use_off_line"].b $\equiv$ True #True表示在AI处理器上执行训练 elif execute_type $= =$ 'cpu': session_config $\equiv$ tf.ConfigProto( allowsoft-placement $\equiv$ True, log_device-placement $\equiv$ False) return session_config 

# 步骤4 单算子网络测试用例主函数。

算子输入请根据算子实际输入个数及shape进行构造。 

算子输出的计算，请根据算子逻辑调用TensorFlow相关接口进行实现。 

```python
#设置np.allclose比较函数的公差参数。  
#np.allclose比较函数的相对公差参数  
atol = 0.001  
#np.allclose比较函数的绝对公差参数  
rtol = 0.001  
def main(unused_arg):  
    shape_parameters = (8, 2048)  
    dtype_parameters = np.float16  
#构造Add算子的两个输入数据，shape为shape_parameters，范围在[-2,2]之间的随机数  
x_data = np.random.uniform(-2,2,size=shape_parameters).astypedtype_parameters)  
y_data = np.random.uniform(-2,2,size=shape_parameters).astypedtype_parameters)  
#分别对Add算子的两个输入数据进行占位  
x = tf compat.v1.placeholderdtype_parameters, shape=shape_parameters)  
y = tf compat.v1.placeholderdtype_parameters, shape=shape_parameters)  
#计算算子输出  
out = tf.math.add(x,y)  
#在Host侧CPU上运行单算子，得到期望运行结果  
with tf compat.v1.Session(config=config('cpu')) as session:  
    result_cpu = session.run(out, feed_dict={x:x_data, y:y_data})  
#在AI处理器上运行单算子，得到实际运行结果  
with tf compat.v1.Session(config='ai_core')) as session:  
    result.ai_core = session.run(out, feed_dict={x:x_data, y:y_data})  
np.array(result.ai_core).astypedtype_parameters)  
np.array(result_cpu).astypedtype_parameters)  
print([''])  
#通过np.allclose比较AI处理器上运行的实际结果和cpu上运行的期望结果，其中atol和rtol为np.allclose比较函数的相对公差参数和绝对公差参数  
cmp_result = np.allclose(result.ai_core, result_cpu, atol, rtol)  
print(cmp_result)  
print(['']) 
```

# 步骤5 运行单算子网络。

if_name $= =$ "main"tf.app.run() 

----结束 

# TensorFlow 自定义算子开发并映射到 CANN 算子

步骤1 适配插件代码开发。以自定义算子AddCustom为例，将该算子映射到TensorFlow自定 义算子AddCustom上，需要先修改CANN AddCustom自定义算子工程目录 framework/tf_plugin下插件代码，完成算子名映射： 

```txt
REGISTER/custom_OP("AddCustom") .FrameworkType(TENSORFLOW) .OriginOpType("AddCustom") .ParseParamsByOperatorFn(AutoMappingByOpFn); 
```

步骤2 TensorFlow自定义算子的开发。本节仅给出示例说明，详细内容请参考TensorFlow官 方文档。 

创建TensorFlow原型注册文件custom_assign_add_custom.cc，内容如下： 

```txt
include "tensorflow/core/framework/op.h" #include "tensorflow/core/framework/shape_inference.h" #include "tensorflow/core/framework/op_kernel.h" #include "tensorflow/core/framework/common_shape_fns.h" using namespace tensorflow; //通过 TensorFlow 提供的REGISTER_OP接口完成算子原型的注册 REGISTER_OP("AddCustom") // TensorFlow 注册算子名 .Input("x: T") //算子原型，输入参数x，类型为T .Input("y: T") //算子原型，输入参数y，类型为T .Output("z: T") //算子原型，输入参数z，类型为T .Attr("T: {half}") //T类型支持范围 .SetShapeFn(shape_inference::BroadcastBinaryOpShapeFn); //算子shape信息推导, BroadcastBinaryOpShapeFn为TensorFlow提供的内置函数，输出shape信息由输入shape传播推导，即输入和输出shape保持一致 //实现一个CPU版本的kernel函数，因为Tensorflow的计算图在构建时会检查所有的算子是否有任意设备上的 kernel函数（NPU Kernel无法被感知），如果没有将会报错。这里实现一个固定返回错误的CPU kernel函数： class AddCustomOp : public OpKernel { public: explicit AddCustomOp(OperationsConstruction* context): OpKernel(context) {} void Compute(OperationsContext* context) override { OP_REQUIRES_OK(context, errors::Unimplemented("AddCustomOp is not supported on CPU")); } }; REGISTER_KERNEL-builtName("AddCustom").Device(DEVICE_CPU), AddCustomOp); //注册 AddCustom算子的CPU实现内核，该函数当前仅打印日志提示CPU不支持 
```

使用如下命令对上述代码进行编译，产物为libcustom_ops.so，后续的算子调用脚本中 可通过load_op_library接口加载该so为python模块，从而调用自定义算子。 

TF_CFLAGS=(\( (python3 -c 'import tensorflow as tf; print("".join(tf.sysconfig.get_COMPILE_flags())))) //获取TensorFlow编译选项
TF_LFLAGS=(\) (python3 -c 'importtensorflow as tf; print("".join(tf.sysconfig.get_link_flags())))) //获取TensorFlow链接选项
SOURCE_FILES=custom_assign_add(custom.cc //包含
TensorFlow算子注册和CPU内核实现的cc文件
g++ -std=c++14 -shared $SOURCE_FILES -o ${Path}/libcustomOPS.so -fPIC ${TF_CFLAGS@[@]} $
{TF_LFLAGS@[@]} -O2 //编译命令,产物为libcustomOPS.so,TensorFlow即可通过load_op_library加载该so为python模块,调用自定义算子 

步骤3 测试脚本中加载上一步骤编译好的动态库，实现自定义算子的调用。 

TensorFlow 1.15.0调用代码示例 

```python
import os  
import tensorflow as tf  
import numpy as np  
from npu_bridge.npu_init import *  
tfenable_resource_variables()  
#np.allclose比较函数的相对公差参数  
atol = 0.001  
#np.allclose比较函数的绝对公差参数  
rtol = 0.001  
def main(unused_arg):  
    custom_op_lib = tf.load_op_library('/outputs/libcustomOps.so')  #加载so为python模块  
    shape_parameters = (8, 2048)  
    dtype_parameters = np.float16 
```

```python
x_data = np.random.uniform(-2, 2, size=shape_parameters).astypedtype_parameters)  
y_data = np.random.uniform(-2, 2, size=shape_parameters).astypedtype_parameters)  
x = tf compat.v1.placeholder dtype_parameters, shape=shape_parameters)  
y = tf compat.v1.placeholder dtype_parameters, shape=shape_parameters)  
tf_z = tf.math.add(x, y) #调用TensorFlow原生算子  
ac_z = custom_op_lib.addCustom(x, y) #调用AscendC AddCustom自定义算子；  
add/custom是将REGISTER_OP(AddCustom)中的AddCustom由大驼峰命名转为下划线格式  
config = tf.ConfigProto()  
custom_op = config.graph_optionsrewrite_options custom_optimizers.add()  
custom_op.name = "NpuOptimizer" #配置在AI处理器上运行单算子  
config.graph_optionsrewrite_options.remapping = RewriterConfig.OFF  
config.graph_optionsrewrite_options/memory_optimization = RewriterConfig.OFF  
with tf.Session(config=config) as sess:  
    sess.run(tf.global_variables_initializer())  
    tfgolden = sess.run(tf_z, feed_dict={x: x_data, y: y_data})  
with tf.Session(config=config) as sess:  
    sess.run(tf.global_variables_initializer())  
    ascend_out = sess.run(ac_z, feed_dict={x: x_data, y: y_data})  
np.array(tfgolden).astypedtype_parameters)  
np.array(ascending_out).astypedtype_parameters)  
print([''])  
#通过np.allclose比较AI处理器上运行的实际结果和使用TensorFlow原生算子运行的期望结果，其中atol和rtol为np.allclose比较函数的相对公差参数和绝对公差参数。  
cmp_result = np.allclose(tfgolden, ascending_out, atol, rtol)  
print(cmp_result)  
print([''])  
if __name__ == "_main_:":  
    tf.app.run() 
```

# TensorFlow 2.6.5调用代码

```python
import os  
import tensorflow as tf  
import numpy as np  
import npu_device  
from numpy_device compat.v1.npu_init import *  
npu_device compat enabling_v1()  
tf compat.v1.enableResource_variables()  
#np.allclose比较函数的相对公差参数  
atol = 0.001  
#np.allclose比较函数的绝对公差参数  
rtol = 0.001  
def main(unused_arg):  
    custom_op_lib = tf.load_op_library('/outputs/libcustomOps.so')  #加载so为python模块  
    shape_parameters = (8, 2048)  
    dtype_parameters = np.float16  
    x_data = np.random.uniform(-2, 2, size=shape_parameters).astypedtype_parameters)  
    y_data = np.random.uniform(-2, 2, size=shape_parameters).astypedtype_parameters)  
    x = tf compat.v1.placeholderdtype_parameters, shape=shape_parameters)  
    y = tf compat.v1.placeholderdtype_parameters, shape=shape_parameters)  
    tf_z = tf.math.add(x, y)  #调用TensorFlow原生算子  
    ac_z = custom_op_lib.add/custom(x, y)  #调用AscendC AddCustom自定义算子;  
add(custom是将REGISTER_OP(AddCustom)中的AddCustom由大驼峰命名转为下划线格式  
    config = tf compat.v1.ConfigProto()  
    custom_op = config.graph_options rewrite_options custom_optimizers.add()  
    custom_op.name = "NpuOptimizer"  
    config.graph_options rewrite_options.remapping = RewriterConfig.OFF  
    config.graph_options rewrite_options/memory_optimization = RewriterConfig.OFF  
    with tf compat.v1.Session(config) as sess:  
        sess.run(tf.global_variables_initializer())  
        tfgolden = sess.run(tf_z, feed_dict={x: x_data, y: y_data})  
    with tf compat.v1.Session(config=config) as sess:  
        sess.run(tf.global_variables_initializer())  
        ascend_out = sess.run(ac_z, feed_dict={x: x_data, y: y_data})  
    np.array(tfgolden).astypedtype_parameters)  
    np.array(ascending_out).astypedtype_parameters)  
print('************************')  
#通过np.allclose比较AI处理器上运行的实际结果和使用TensorFlow原生算子运行的期望结果，其中atol 
```

```python
和rtol为np.allclose比较函数的相对公差参数和绝对公差参数。cmp_result = np.allclose(tfgolden, ascend_out, atol, rtol) print(cmp_result) print('===') if __name__ == "_main_: tf.app.run() 
```

----结束 

# 可选输入算子映射关系开发

TensorFlow的原型定义中不支持可选输入，对于包含可选输入的算子，其从 TensorFlow到CANN的映射关系，不满足简单的一对一映射，需要在插件适配代码 中，将输入转换为可选输入，调整原型的映射关系。下文以CANN算子库中的 FlashAttentionScore算子为例，介绍针对此类算子的框架适配插件如何开发。 

# 步骤1 适配插件开发

和上文中介绍的简单的一对一映射不同，进行插件适配开发时，需要调用 ParseOpToGraphFn注册回调函数，回调函数中用于调整算子原型映射关系。此时： 

通过ParseParamsByOperatorFn注册回调函数，回调函数中将TensorFlow原生算 子映射到一个IR和TensorFlow一致的中间算子（调用AutoMappingByOpFn完成 属性映射）。 

通过ParseOpToGraphFn注册回调函数，调整算子原型映射关系，将中间算子最终 映射到CANN算子库中的算子，这里映射到Graph图的概念是指一个算子构成的单 算子图。 

需要注意：在ParseParamsByOperatorFn的回调函数中，需要将TensorFlow算子名称 设置到中间算子的original_type属性中，用于后续ParseOpToGraphFn回调函数的触 发。示例代码如下： 

```cpp
include <string>   
#include <vector>   
#include "register/register.h"   
#include "graph/operator.h"   
#include "graph/graph.h"   
#include "graph/managerFACTory.h"   
namespace domi {   
using namespace ge;   
static Status AddOptionalPLACEHolderForFA(const ge::Operator &tf_op, ge::Graph &graph) { //1.创建一个FlashAttentionScore算子npu_fa_op   
ge::AscendString op_name;   
tf_op.getName(op_name);   
auto npu_fa_op = OperatorFactory::CreateOperator(op_name.getString(), "FlashAttentionScore"); //2.将TensorFlow算子属性映射到npu_fa_op算子上 float scale_value = 1.0; (void)tf_op.GetAttr("scale_value", scale_value); (void)npu_fa_op.SetAttr("scale_value", scale_value);   
float keep_prob = 1.0; (void)tf_op.GetAttr("keep_prob", keep_prob); (void)npu_fa_op.SetAttr("keep_prob", keep_prob);   
int32_t pre_tokens = 2147483647; (void)tf_op.GetAttr("pre_tokens", pre_tokens); (void)npu_fa_op.SetAttr("pre_tokens", pre_tokens);   
int32_t next_tokens = 2147483647; (void)tf_op.GetAttr("next_tokens", next_tokens); (void)npu_fa_op.SetAttr("next_tokens", next_tokens);   
int32_t head_num = 0; 
```

```cpp
(void)tf_op.GetAttr("head_num", head_num);  
(void)npu_fa_op.SetAttr("head_num", head_num);  
std::string input.layout;  
(void)tf_op.GetAttr("input.layout", input.layout);  
(void)npu_fa_op.SetAttr("input.layout", input.layout);  
int32_t inner_precise = 0;  
(void)tf_op.GetAttr("inner_precise", inner_precise);  
(void)npu_fa_op.SetAttr("inner_precise", inner_precise);  
int32_t sparse_mode = 0;  
(void)tf_op.GetAttr("sparse_mode", sparse_mode);  
(void)npu_fa_op.SetAttr("sparse_mode", sparse_mode);  
int32_t pse_type = 1;  
(void)tf_op.GetAttr("pse_type", pse_type);  
(void)npu_fa_op.SetAttr("pse_type", pse_type);  
int32_t seed = 0;  
(void)tf_op.GetAttr("seed", seed);  
(void)npu_fa_op.SetAttr("seed", seed);  
int32_t offset = 0;  
(void)tf_op.GetAttr("offset", offset);  
(void)npu_fa_op.SetAttr("offset", offset);  
int32_t out_dtype = 0;  
(void)tf_op.GetAttr("out_dtype", out_dtype);  
(void)npu_fa_op.SetAttr("out_dtype", out_dtype);  
// 3.创建输入Data  
std::vector<Operator> inputs;  
for (size_t i = 0UL; i < tf_op.GetInputsSize(); i++) {  
    const std::string data_name = "Data_" + std::to_string(i);  
    Operator data_op = OperatorFactory::CreateOperator(data_name.c_str(), "Data");  
    (void)data_op.SetAttr(index", static_cast<int32_t>(i));  
    inputs'emplace_back(data_op);  
}  
size_t index = 0UL;  
//4.必选输入直接设置Data到算子输入  
(void)npu_fa_op.SetInput("query", inputs[index++]');  
(void)npu_fa_op.SetInput("key", inputs[index++]');  
(void)npu_fa_op.SetInput("value", inputs[index++]');  
//5.可选输入需要判断type属性的个数是否为0，不为0则表示可选输入已经使能  
std::vectorDataType> real_shift_type;  
(void)tf_op.GetAttr("real_shift_type", realhift_type);  
if (!real_shift_type.empty()) {  
    (void)npu_fa_op.SetInput("real_shift", inputs[index++]');  
}  
std::vectorDataType> drop_mask_type;  
(void)tf_op.GetAttr("drop_mask_type", drop_mask_type);  
if (!drop_mask_type.empty()) {  
    (void)npu_fa_op.SetInput("drop_mask", inputs[index++]');  
}  
std::vectorDataType> padding_mask_type;  
(void)tf_op.GetAttr("padding_mask_type", padding_mask_type);  
if (!padding_mask_type.empty()) {  
    (void)npu_fa_op.SetInput("padding_mask", inputs[index++]');  
}  
std::vectorDataType> attenu_mask_type;  
(void)tf_op.GetAttr("attenu_mask_type", attenu_mask_type);  
if (!attn_mask_type.empty()) {  
    (void)npu_fa_op.SetInput("attn_mask", inputs[index++]');  
}  
std::vectorDataType> prefix_type;  
(void)tf_op.GetAttr("prefix_type", prefix_type); 
```

```cpp
if(!prefix_type.empty()){ (void)npu_fa_op.SetInput("prefix",inputs[index++]); } std::vector<DataType> actual_seq_qlen_type; (void)tf_op.GetAttr("actual_seq_qlen_type",actual_seq_qlen_type); if(!actual_seq_qlen_type.empty()){ (void)npu_fa_op.SetInput("actual_seq_qlen",inputs[index++]); } std::vector<DataType> actual_seq_kvlen_type; (void)tf_op.GetAttr("actual_seq_kvlen_type",actual_seq_kvlen_type); if(!actual_seq_kvlen_type.empty()){ (void)npu_fa_op.SetInput("actual_seq_kvlen",inputs[index++]); } std::vector<DataType> q_startidx_type; (void)tf_op.GetAttr("q_startidx_type",q_startidx_type); if(!q_startidx_type.empty()){ (void)npu_fa_op.SetInput("q_startidx",inputs[index++]); } std::vector<DataType> kv_startidx_type; (void)tf_op.GetAttr("kv_startidx_type",kv_startidx_type); if(!kv_startidx_type.empty()){ (void)npu_fa_op.SetInput("kv_startidx",inputs[index++]); } std::vector<DataType>d_scale_q_type; (void)tf_op.GetAttr("d_scale_q_type",d_scale_q_type); if(!d_scale_q_type.empty()){ (void)npu_fa_op.SetInput("d_scale_q",inputs[index++]); } std::vector<DataType>d_scale_k_type; (void)tf_op.GetAttr("d_scale_k_type",d_scale_k_type); if(!d_scale_k_type.empty()){ (void)npu_fa_op.SetInput("d_scale_k",inputs[index++]); } std::vector<DataType>d_scale_v_type; (void)tf_op.GetAttr("d_scale_v_type",d_scale_v_type); if(!d_scale_v_type.empty()){ (void)npu_fa_op.SetInput("d_scale_v",inputs[index++]); } std::vector<DataType> query_ripe_type; (void)tf_op.GetAttr("query_ripe_type",query_ripe_type); if(!query_ripe_type.empty()){ (void)npu_fa_op.SetInput("queryRope",inputs[index++]); } std::vectorDTD��>key_ripe_type; (void)tf_op.GetAttr("key_ripe_type",key_ripe_type); if(!key_ripe_type.empty()){ (void)npu_fa_op.SetInput("keyRope",inputs[index++]); } //6.使用npu_fa_op算子的输出构造图的输出。 std::vector<std::pairOperator,std::vector<size_t>>outputIndices; std::vector<size_t>node_output_index; for(size_t i = 0UL;i < npu_fa_op.GetOutputsSize();i++) { node_output_index.emplace_back(i); } (void)outputIndices.emplace_back(std::makePair(npu_fa_op,node_output_index)); (void)graph.SetInputs(input).SetOutputs(outputIndices); return SUCCESS; } static Status FlashAttentionScoreMapping(const ge::Operator& op_src,ge::Operator& op_dst){ //1.调用默认映射函数即可 if(AutoMappingByOpFn(op_src,op_dst) != ge::GRAPH_SUCCESS){ returnFAILED; } //2.需要将TensorFlow算子名称设置到op_dst的original_type属性中，用于后续ParseOpToGraph 触发 
```

```txt
op.dst.SetAttr("original_type", "FlashAttentionScore"); return SUCCESS;   
}   
REGISTER/custom_OP("FlashAttentionScore") .FrameworkType(TENSORFLOW) .OriginOpType({"FlashAttentionScore"}) .ParseParamsByOperatorFn(FlashAttentionScoreMapping) // 注册此函数用于实现算子本身属性的映射 .ParseOpToGraphFn(AddOptionalPLACEHolderForFA); // 注册此函数用于实现将tf中的输入转化为可选输入，改变连边关系   
} // namespace domi 
```

步骤2 在TensorFlow开源框架里注册FlashAttentionScore算子的原型定义，由于TensorFlow 不支持可选输入，需要将其可选输入在TensorFlow原型中表示为动态输入，并通过属 性来标记动态输入的个数，这些可选输入需要放置在原型定义的最后。示例代码 （FlashAttentionScore.cc）如下： 

include <algorithm>   
#include <atomic>   
#include <map>   
#include "tensorflow/core/framework/common_shape_fns.h"   
#include "tensorflow/core/framework/op.h"   
#include "tensorflow/core/framework/op_kernel.h"   
using namespace tensorflow;   
using shape_inference::InferenceContext;   
using shape_inference::ShapeHandle;   
using namespace std;   
using namespace chrono;   
using OpKernelConstructionPtr $\equiv$ OpKernelConstruction\*;   
using OpKernelContextPtr $\equiv$ OpKernelContext\*;   
using InferenceContextPtr $\equiv$ :tensorflow::shape_inference::InferenceContext\*;   
namespace{   
classCustOps:publicOpKernel{   
public: explicitCustOps(OpKernelConstructionPtr context) :OpKernel(context){ void Compute(OpKernelContextPtr context) override { std::cout<< "Cust Ops not installed!!" << std::endl; } ~CustOps()override $=$ default;}   
} // namespace   
namespace TensorFlow{   
REGISTER_OP("FlashAttentionScore") .Input("query:T") .Input("key:T") .Input("value:T") .Input("real_shift:real_shift_type")//可选输入在TensorFlow原型中注册为动态输入 .Input("drop_mask:drop_mask_type") .Input("padding_mask:padding_mask_type") .Input("atten_mask:atten_mask_type") .Input("prefix:prefix_type") .Input("actual_seq_qlen:actual_seq_qlen_type") .Input("actual_seq_kvlen:actual_seq_kvlen_type") .Input("q_startidx:q_startidx_type") .Input("kv_startidx:kv_startidx_type") .Input("d_scale_q:d_scale_q_type") .Input("d_scale_k:d_scale_k_type") .Input("d_scale_v:d_scale_v_type") .Input("query_rope:query_rope_type") .Input("key_rope:key_rope_type") .Output("softmax_max:float32") .Output("softmax_sum:float32") .Output("softmax_out:T") .Output("attention_out:T") .Attr("scale_value:float $= 1.0$ " ) .Attr("keep_prob:float $= 1.0$ " ) .Attr("pre_tokens:int $= 2147483647$ " ) .Attr("next_tokens:int $= 2147483647$ " ) .Attr("head_num:int") 

```txt
.Attr("input.layout: string")   
.Attr("inner_precise: int = 0")   
.Attr("sparse_mode: int = 0")   
.Attr("pse_type: int = 1")   
.Attr("seed: int = 0")   
.Attr("offset: int = 0")   
.Attr("out_dtype: int = 0")   
.Attr("T: {float16, float32, bfloat16} = DT_FLOAT")   
.Attr("real_shift_type: list({float16, float32, bfloat16}) >= 0") //通过属性来标记动态输入个数   
.Attr("drop_mask_type: list({uint8}) >= 0")   
.Attr("padding_mask_type: list({float16, float32, bfloat16}) >= 0")   
.Attr("atten_mask_type: list({bool, uint8}) >= 0")   
.Attr("prefix_type: list(int64)) >= 0")   
.Attr("actual_seq_qlen_type: list(int64)) >= 0")   
.Attr("actual_seq_kvlen_type: list(int64)) >= 0")   
.Attr("q_startidx_type: list(int64)) >= 0")   
.Attr("kv_startidx_type: list(int64)) >= 0")   
.Attr("d_scale_q_type: list(float32)) >= 0")   
.Attr("d_scale_k_type: list(float32)) >= 0")   
.Attr("d_scale_v_type: list(float32)) >= 0")   
.Attr("query_ripe_type: list(float32)) >= 0")   
.Attr("key_ripe_type: list(float32)) >= 0")   
.SetShapeFn([](InferenceContext *c) { return Status::OK(); }；   
REGISTER_KERNEL-builtER(Name("FlashAttentionScore").Device(DEVICE_CPU), CustOps) 
```

使用如下命令对上述代码进行编译，产物为libcustom_ops.so，后续的算子调用脚本中 可通过load_op_library接口加载该so为python模块，从而调用自定义算子。 

TF_CFLAGS=( $(python3 -c 'import tensorflow as tf; print(" ".join(tf.sysconfig.get_compile_flags()))') ) // 获取TensorFlow编译选项 

TF_LFLAGS=( $(python3 -c 'import tensorflow as tf; print(" ".join(tf.sysconfig.get_link_flags()))') ) // 获 取TensorFlow链接选项 

SOURCE_FILES=FlashAttentionScore.cc // 包含TensorFlow 

算子注册和CPU内核实现的cc文件 g++ -std=c++14 -shared $SOURCE_FILES -o ${Path}/libflashattention.so -fPIC ${TF_CFLAGS[@]} $ 

{TF_LFLAGS[@]} -O2 // 编译命令，产物为libflashattention.so，${Path}为自定义的路径，后续TensorFlow可 通过load_op_library加载该so为python模块，调用自定义算子 

步骤3 封装一个TensorFlow的算子调用接口，在此接口中处理可选输入。在该脚本需要加载 上一步骤编译好的动态库。 

```python
from tensorflow.python-framework import ops  
import tensorflow as tf  
tfOpLib = tf.load_op_library("./build/tfOps/libflashattention.so")  
#假如外部未使能该可选输入，则给底层传入空列表  
def create_option_input_list(input):  
    input_list = []  
    if not input is None:  
        input_list.append(input)  
    return input_list  
# flash attention score封装函数  
def npuflash attention(query, key, value, head_num, input.layout, real_shift=None, drop_mask=None, padding_mask=None, attenuated=True, prefix=None, actual_seq_qlen=None, actual_seq_kvlen=None, q_start_idx=None, kv_start_idx=None, d_scale_q=None, d_scale_k=None, d_scale_v=None, query_ripe=None, key_ripe=None, scale_value=1.0, keep_prob=1.0, pre_tokens=2147483647, next_tokens=2147483647, inner_precise=0, sparse_mode=0, pse_type=1, seed=0, offset=0, outdtype=0)  
):  
    output = tfOpLibflashattention_score(query=query, key=key, value=value, realshift=createOptional_input_list(realshift), drop_mask=createOptional_input_list.drop_mask), padding_mask=createOptional_input_list(padding_mask),  
attn mask=createOptional_input_list(atten_mask), prefix=createOptional_input_list(prefix),  
actual_seq_qlen=createOptional_input_list(actual_seq_qlen), actual_seq_kvlen=createOptional_input_list(actual_seq_kvlen),  
q_start_idx=createOptional_input_list(q_start_idx), 
```

kv_start_idx $=$ create_option_input_listkv_start_idx),d_scale_q $=$ create_option_input_list(d_scale_q), d_scale_k $=$ create_option_input_list(d_scale_k),d_scale_v $=$ create_option_input_list(d_scale_v), query_ripe $=$ create_option_input_list(query_ripe),key_ripe $=$ create_option_input_list(key_ripe), scale_value $=$ scale_value,keep_prob $=$ keep_prob,pre_tokens $=$ pre_tokens,next_tokens $\equiv$ next_tokens, head_num $\equiv$ head_num, input.layout $\equiv$ input.layout, inner_precise $\equiv$ inner_precise,   
sparse_mode $\equiv$ sparse_mode, pse_type $\equiv$ pse_type,seed $\equiv$ seed,offset $\equiv$ offset,outdtype $\equiv$ outdtype   
return output 

步骤4 测试脚本中实现自定义算子的调用。假设上一步骤中代码文件保存为ops.py，从ops中 导入npu_flash_attention函数并使用。TensorFlow 2.6.5调用代码如下： 

import sys   
from ops import npuflashattention   
import tensorflow as tf   
import numpy as np   
tf compat.v1.disable_eager_execution()   
import npu_device   
from npu_device.compact.v1.npu_init import \*   
npu_device.compact.enabled_v1()   
def sess_config(): config $=$ tf compat.v1.ConfigProto() custom_op $=$ config.graph_optionsrewrite_options/custom_optimizers.add() custom_op.name $=$ "NpuOptimizer" config.graph_optionsrewrite_options.remapping $=$ RewriterConfig.OFF config.graph_optionsrewrite_options/memory_optimization $=$ RewriterConfig.OFF return config   
shape $= [1,32,32]$ query_np $=$ np.random.randint(*shape).astype(np.float16)   
key_np $=$ np.random.randint(*shape).astype(np.float16)   
value_np $=$ np.random.randint(*shape).astype(np.float16)   
query $=$ tf.Variable(query_np,tf.float16)   
key $=$ tf.Variable(key_np,tf.float16)   
value $=$ tf.Variable(value_np,tf.float16)   
mask $=$ tf.zeros(shape=(shape[0],1, shape[1], shape[1]),dtype=tf uint8)   
head_num $= 1$ input.layout $=$ "BSH"   
flash_result_t $=$ npuflashattention(query, key, value, head_num, input.layout,atten_mask $\equiv$ mask)   
with tf compat.v1.Session(config=sess_config()) as sess: sess.run(tf compat.v1.global_variables_initializer()) flash_result $=$ sess.run(flash_result_t) print(flash_result) 

----结束 

# 动态输入算子映射关系开发

对于存在动态输入/输出的算子，需要在插件的回调函数ParseParamByOpFunc中使用 AutoMappingByOpFnDynamic实现TensorFlow算子和CANN算子的匹配。通过 DynamicInputOutputInfo结构类描述动态输入/输出的信息，将动态输入/输出的名称 和描述其个数的属性名绑定，再传入AutoMappingByOpFnDynamic实现自动匹配。 

以ParseSingleExample算子为例，插件适配代码如下： 

include "register/register.h"   
namespace domi {   
Status ParseSingleExampleMapping(const ge::Operator& op_src, ge::Operator& op) { std::vector<DynamicInputOutputInfo> value; const std::string dynamic_input_namedense_defaultson $=$ "dense_default"; const std::string dynamic_input_attr_name_dense_defaultson $=$ "Tdense"; 

DynamicInputOutputInfo input(kInput, dynamic_input_namedense_defaultsc_str), dynamic_input_namedense_defaultsl.size(), dynamic_input_attr_namedense_defaultsc_str(), dynamic_input_attr_namedense_defaultsl.size());   
value.push_back(input);   
const std::string dynamic_output_nameSparse_values $=$ "sparse_values";   
const std::string dynamic_output_attr_nameSparse_values $=$ "numSparse";   
DynamicInputOutputInfo output(kOutput, dynamic_output_nameSparse_values.c_str(), dynamic_output_namesparse_values.size(), dynamic_output_attr_namesparse_values.c_str(), dynamic_output_attr_namesparse_values.size());   
value.push_back(output);   
const std::string dynamic_output_nameSparse_values $=$ "sparse_values";   
const std::string dynamic_output_attr_nameSparse_values $=$ "sparse_types";   
DynamicInputOutputInfo output1 (kOutput, dynamic_output_nameSparse_values.c_str(), dynamic_output_namesparse_values.size(), dynamic_output_attr_namesparse_values.c_str(), dynamic_output_attr_namesparse_values.size());   
value.push_back(output1);   
const std::string dynamic_output_nameSparse Shapes $=$ "sparse_shape";   
const std::string dynamic_output_attr_namesparse Shapes $=$ "sparse_types";   
DynamicInputOutputInfo output2 (kOutput, dynamic_output_namesparse Shapes.c_str(), dynamic_output_namesparse Shapes.size(), dynamic_output_attr_namesparse Shapes.c_str(), dynamic_output_attr_namesparse Shapes.size()));   
value.push_back(output2);   
const std::string dynamic_output_namedense_values $=$ "dense_values";   
const std::string dynamic_output_attr_namedense_values $=$ "Tdense";   
DynamicInputOutputInfo output3 (kOutput, dynamic_output_namedense_values.c_str(), dynamic_output_namedense_values.size(), dynamic_output_attr_namedense_values.c_str(), dynamic_output_attr_namedense_values.size()));   
value.push_back(output3);   
AutoMappingByOpFnDynamic(op_src, op, value);   
return SUCCESS;   
}   
//register ParseSingleExample op to GE   
REGISTER/custom_OP("ParseSingleExample") .FrameworkType(TENSORFLOW) .OriginOpType("ParseSingleExample") .ParseParamsByOperatorFn(ParseSingleExampleMapping)   
} 

# 说明

暂不支持同时有可选输入和动态输入的算子映射。 

# 2.10.5 show_kernel_debug_data 工具

在Ascend C算子程序代码中，用户可以使用AscendC::DumpTensor、 AscendC::printf、AscendC::PrintTimeStamp、ascendc_assert接口打印相关调试信 息，并通过“aclInit”或直接配置acl.json文件，启用Dump配置，导出Ascend C算子 Kernel的调测信息。本工具提供了对调测信息的离线解析能力，帮助用户获取并解析 调试信息，即将导出的bin文件解析成可读格式。本工具的使用示例可参考 show_kernel_debug_data样例。 

# 说明

show_kernel_debug_data支持多用户并发调用，但用户需要指定不同的落盘路径，否则可能出 现落盘内容被覆盖等问题。 

# 产品支持情况

<table><tr><td>产品</td><td>是否支持</td></tr><tr><td>Atlas 350 加速卡</td><td>✓</td></tr><tr><td>Atlas A3 训练系列产品/Atlas A3 推理系列产品</td><td>✓</td></tr><tr><td>Atlas A2 训练系列产品/Atlas A2 推理系列产品</td><td>✓</td></tr><tr><td>Atlas 200I/500 A2 推理产品</td><td>✓</td></tr><tr><td>Atlas 推理系列产品</td><td>✓</td></tr><tr><td>Atlas 训练系列产品</td><td>×</td></tr></table>

# 工具安装

# 步骤1 安装工具。

工具跟随CANN软件包发布（参考环境准备完成CANN安装），其路径默认为“$ {INSTALL_DIR}/tools/show_kernel_debug_data”，其中${INSTALL_DIR}请替换为 CANN软件安装后文件存储路径。以root用户安装为例，安装后文件默认存储路径 为：/usr/local/Ascend/cann。 

# 步骤2 设置环境变量。

root用户安装Ascend-cann-toolkit包时 source /usr/local/Ascend/cann/set_env.sh 

非root用户安装Ascend-cann-toolkit包时 source ${HOME}/Ascend/cann/set_env.sh 

# 步骤3 检查工具是否安装成功。

执行如下命令，若能正常显示--help或-h信息，则表示工具环境正常，功能可正常使 用。 

show_kernel_debug_data -h 

# ----结束

# 使用方法

# 命令行方式

show_kernel_debug_data <bin_file_path> [<output_path>] 

<table><tr><td>参数</td><td>可选/必选</td><td>说明</td></tr><tr><td>&lt;bin_file_path&gt;</td><td>必选</td><td>kernel侧调试信息落盘的bin文件或包含 bin文件的目录路径，例如“/input/dump Workspace.bin”。</td></tr><tr><td>&lt;output_path&gt;</td><td>可选</td><td>解析结果的保存路径，例如“/output_dir”。默认是当前命令行执行目录下。</td></tr></table>

# API方式

获取kernel侧调试信息并解析成可读文件。函数原型如下。 

def show_kernel_debug_data(bin_file_path: str, output_path: str $= \cdot /$ ') $- >$ None 

其中，输入参数说明如下。函数无输出参数和返回值。 

bin_file_path：kernel侧调试信息落盘的bin文件或包含bin文件的目录路径， 字符串类型。 

output_path：解析结果的保存路径，字符串类型，默认是当前接口调用脚本 所在目录下。 

调用示例参考如下代码。 

from show_kernel_debug_data import show_kernel_debug_data show_kernel_debug_data(./input/dump_workspace.bin) 

# 产物说明

工具解析结果文件目录结构如下。其中，dump_data目录是对DumpTensor、 PrintTimeStamp接口解析的结果，index0对应DumpTensor接口中第二个参数desc=0 时的打印，loop0表示切分后首个分块的数据打印。 

![](images/4a13facc7a5ab62450674905ed990941aa61f79e241cd4aac97b4cf2ec69cbd5.jpg)


# 2.10.6 msobjdump 工具

本工具主要针对Kernel直调工程（NPU模式）、标准自定义算子工程、简易自定义算 子工程编译生成的算子ELF文件（Executable and Linkable Format）提供解析和解压 功能，并将结果信息以可读形式呈现，方便开发者直观获得kernel文件信息。 

# 说明

ELF文件是一种用于二进制文件、可执行文件、目标代码、共享库和核心转储的文件格式， 包括常见的*.a、*.so文件等。ELF文件常见构成如下： 

ELF头部：描述了整个文件的组织结构，包括文件类型、机器类型、版本号等信息。 

程序头部表：描述了文件中各种段（segments）信息，包括程序如何加载到内存中执 行的信息。 

节区头部表：描述了文件中各个节（sections）信息，包括程序的代码、数据、符号表 等。 

● 工具使用过程中，若出现如下场景，请根据日志提示信息，分析排查问题。 

ELF文件未找到 

ELF文件权限错误 

ELF文件存在但不支持解析或解压 

# 产品支持情况

<table><tr><td>产品</td><td>是否支持</td></tr><tr><td>Atlas 350 加速卡</td><td>✓</td></tr><tr><td>Atlas A3 训练系列产品/Atlas A3 推理系列产品</td><td>✓</td></tr><tr><td>Atlas A2 训练系列产品/Atlas A2 推理系列产品</td><td>✓</td></tr><tr><td>Atlas 200I/500 A2 推理产品</td><td>✓</td></tr><tr><td>Atlas 推理系列产品</td><td>✓</td></tr><tr><td>Atlas 训练系列产品</td><td>✓</td></tr></table>

# 工具安装

步骤1 安装msobjdump工具。 

工具跟随CANN软件包发布（参考环境准备完成CANN安装），其路径默认为“$ {INSTALL_DIR}/tools/msobjdump”，其中${INSTALL_DIR}请替换为CANN软件安装 后文件存储路径。以root用户安装为例，安装后文件默认存储路径为：/usr/local/ Ascend/cann。 

步骤2 设置环境变量。 

root用户安装Ascend-cann-toolkit包时 source /usr/local/Ascend/cann/set_env.sh 

非root用户安装Ascend-cann-toolkit包时 source ${HOME}/Ascend/cann/set_env.sh 

步骤3 检查工具是否安装成功。 

执行如下命令，若能正常显示--help或-h信息，则表示工具环境正常，功能可正常使 用。 

msobjdump -h 

----结束 

# 命令格式

解析ELF文件的命令 

msobjdump --dump-elf <elf_file> [--verbose] 


表 2-46 参数说明


<table><tr><td>参数（区分大小写）</td><td>可选/必选</td><td>说明</td></tr><tr><td>--dumpelf&lt;elf_file&gt;, -d</td><td>必选</td><td>解析ELF文件中包含的device信息，如文件名、文件类型、文件长度、符号表等，并终端打屏显示。&lt;elf_file&gt;表示待解析ELF文件路径，如/home/op api/lib_api.so。支持两种打印模式：简单打印：默认仅打印部分device信息。全量打印：与--verbose配套使用，开启全量device信息打屏显示。不同工程打印字段信息不同，具体参见表2-49和表2-50。</td></tr><tr><td>--verbose, -V</td><td>可选</td><td>必须与--dumpelf配套使用，用于开启ELF文件中全量打印device信息功能。</td></tr></table>

# 解压ELF文件的命令

msobjdump --extract-elf <elf_file> [--out-dir <out_path>] 


表 2-47 参数说明


<table><tr><td>参数（区分大小写）</td><td>可选/必选</td><td>说明</td></tr><tr><td>--extract-elf&lt;elf_file&gt;, -e</td><td>必选</td><td>解压ELF文件中包含的device信息，并按原始文件夹规则落盘到输出路径下。&lt;elf_file&gt;表示待解压ELF文件路径，如/home/op api/lib_api.so。默认路径：解压结果文件默认落盘到当前执行路径下。自定义路径：可与--out-dir配套使用，设置落盘路径。</td></tr><tr><td>--out-dir&lt;out_path&gt;, -o</td><td>可选</td><td>必须与--extract-elf配套使用，用于设置解压文件的落盘路径。&lt;out_path&gt;为落盘文件目录，如/home/extract/。请注意：msobjdump支持多用户并发调用，但需要指定不同的--out-dir，否则可能出现落盘内容被覆盖的问题。</td></tr></table>

# 获取ELF文件列表的命令

msobjdump --list-elf <elf_file> 


表 2-48 参数说明


<table><tr><td>参数（区分大小写）</td><td>可选/必选</td><td>说明</td></tr><tr><td>--list-elf&lt;elf_file&gt;, -l</td><td>可选</td><td>获取ELF文件中包含的device信息文件列表，并打印显示。&lt;elf_file&gt;表示待打印的ELF文件路径，如/home/op api/lib_api.so。</td></tr></table>


表 2-49 ELF 解析字段说明（Kernel 直调工程）


<table><tr><td>字段名</td><td>含义</td><td>是否必选</td><td>打印说明</td></tr><tr><td>VERSION</td><td>表示版本号。</td><td>是</td><td>不设置--verbose,默认打印。</td></tr><tr><td>TYPECOUNT</td><td>表示ELF文件中包含的kernel文件个数。</td><td>是</td><td>不设置--verbose,默认打印。</td></tr><tr><td>ELF FILE{id}</td><td>表示ELF文件中包含的kernel文件名,\${id}表示kernel文件序号。kernel文件名的命名规则如下:按{\sec_prefix}_{\$\{file_index\}}{\{kernel_type\}.o拼接,其中{\sec_prefix}为section段名(工具根据“.ascend.kernel”关键字搜索获取),\${file_index}表示文件编号,\${kernel_type}表示kernel类型。</td><td>是</td><td>不设置--verbose,默认打印。</td></tr><tr><td>KERNELLEN</td><td>表示kernel文件的长度。</td><td>是</td><td>不设置--verbose,默认打印。</td></tr><tr><td>KERNELTYPE</td><td>表示kernel类型,映射关系为{0:&#x27;mix&#x27;,1:&#x27;aiv&#x27;,2:&#x27;aic&#x27;}。</td><td>否</td><td>不设置--verbose,默认打印。</td></tr><tr><td>ASCENDMETA</td><td>表示算子执行时核间同步、Cube/Vector核占比(task_ration)等信息。若没有获取到该信息,默认显示None。</td><td>否</td><td>不设置--verbose,默认打印。</td></tr><tr><td>elf heardinfos</td><td>包括ELF Header、Section Headers、Key to Flags、Program Headers、Symbol表等信息。</td><td>否</td><td>设置--verbose,开启全量打印。</td></tr></table>


表 2-50 ELF 解析字段说明（标准/简易自定义算子工程）


<table><tr><td>字段名</td><td>含义</td><td>是否必选</td><td>打印说明</td></tr><tr><td>.ascend.m eta.\$\{id\}</td><td>表示算子kernel函数名称,其中${id}表示meta信 息的索引值。</td><td>是</td><td>不设置-- verbose, 默认打 印。</td></tr><tr><td>VERSION</td><td>表示版本号。</td><td>是</td><td>不设置-- verbose, 默认打 印。</td></tr><tr><td>DEBUG</td><td>调试相关信息,包含如下两部分内容: debugBufSize: 调试信息需要的内存空间。 debugOptions: 调试开关状态。取值如下: 0: 调试开关关闭。 1: 通过DumpTensor、printf打印进行调试。 2: 通过assert断言进行调试。 4: 通过时间戳打点功能进行调试。 8: 通过内存越界检测进行调试。</td><td>否</td><td>不设置-- verbose, 默认打 印。</td></tr><tr><td>DYNAMIC_PARAMETER</td><td>算子kernel函数是否启用动态参数。取值分别 为: 0: 关闭动态参数模式。 1: 开启动态参数模式。</td><td>否</td><td>不设置--verbose, 默认打 印。</td></tr><tr><td>OPTIONAL_PARAMETER</td><td>可选参数信息,包含如下两部分内容: optionalInputMode: 可选输入在算子kernel函数 中是否需要占位。取值分别为: 0: 可选输入不占位。 1: 可选输入占位。 optionalOutputMode: 可选输出在算子kernel函 数中是否需要占位。取值分别为: 0: 可选输出不占位。 1: 可选输出占位。</td><td>否</td><td>不设置--verbose, 默认打 印。</td></tr><tr><td>KERNEL_TYPE</td><td>表示kernel函数运行时core类型,取值参见表表 2-51。</td><td>否</td><td>不设置--verbose, 默认打 印。</td></tr><tr><td>CROSS_CORE_SYNC C</td><td>表示硬同步syncall类型。 USE_SYNC: 使用硬同步。 NO_USE_SYNC: 不使用硬同步。</td><td>否</td><td>不设置--verbose, 默认打 印。</td></tr><tr><td>MIX_TASK_RATION</td><td>表示kernel函数运行时的Cube核/Vector核占比分配类型。</td><td>否</td><td>不设置--verbose,默认打印。</td></tr><tr><td>DETERMINITIC_INFO</td><td>表示算子是否为确定性计算。0:不确定计算。1:确定性计算。</td><td>否</td><td>不设置--verbose,默认打印。</td></tr><tr><td>BLOCK_NUM</td><td>表示算子执行核数,该字段当前暂不支持,只打印默认值0xFFFFFF。</td><td>否</td><td>不设置--verbose,默认打印。</td></tr><tr><td>FUNCTION_ENTRY</td><td>算子TilingKey的值。</td><td>否</td><td>不设置--verbose,默认打印。</td></tr><tr><td>elf heardinfos</td><td>包括ELF Header、Section Headers、Key to Flags、Program Headers、Symbol表等信息。</td><td>否</td><td>设置--verbose,开启全量打印。</td></tr></table>


表 2-51 kernel type 信息


<table><tr><td>KERNEL_TYPE</td><td>说明</td></tr><tr><td>AICORE</td><td>该参数为预留参数，当前版本暂不支持。算子执行时仅会启动AI Core，比如用户在host侧设置blocknum为5，则会启动5个AI Core。</td></tr><tr><td>AIC</td><td>算子执行时仅启动AI Core上的Cube核：比如用户在host侧设置blocknum为10，则会启动10个Cube核。</td></tr><tr><td>AIV</td><td>算子执行时仅启动AI Core上的Vector核：比如用户在host侧设置blocknum为10，则会启动10个Vector核。</td></tr><tr><td>MIX_AIC_MAIN</td><td>AIC、AIV混合场景下，设置核函数的类型为MIX，算子执行时会同时启动AI Core上的Cube核和Vector核，比如用户在host侧设置blocknum为10，且设置task_ration为1:2，则会启动10个Cube核和20个Vector核。</td></tr><tr><td>MIX_AIV_MAIN</td><td>AIC、AIV混合场景下，使用了多核控制相关指令时，设置核函数的类型为MIX，算子执行时会同时启动AI Core上的Cube核和Vector核，比如用户在host侧设置blocknum为10，且设置task_ration为1:2，则会启动10个Vector核和20个Cube核。</td></tr><tr><td>AIC_ROLLBACK</td><td>算子执行时会同时启动AI Core和Vector Core, 此时AI Core会当成Cube Core使用。</td></tr><tr><td>AIV_ROLLBACK</td><td>算子执行时会同时启动AI Core和Vector Core, 此时AI Core会当成Vector Core使用。</td></tr></table>

# 使用样例（Kernel 直调算子工程）

以MatMulInvocationNeo算子为例（NPU模式），假设${cmake_install_dir}为算子 Cmake编译产物根目录，目录结构如下（仅为示例，具体以实际算子工程为准），类 似CMake编译配置文件编写。 

![](images/a7147b4d2890646bcd6136fb996ca1599822ee9b7b637abecdaf3dae1d274341.jpg)


工具对编译生成的库文件（如*.so、*.a等）进行解析和解压，功能实现命令样例如下： 

# 解析包含device信息的库文件

支持两种打印方式，请按需选取，解析字段含义参见表2-49。 

简单打印 

```shell
msobjdump --dump-elf ${cmake_install_dir}/out/libascendc_kernels_npu.so 
```

执行上述命令，终端打印基础device信息，示例如下： 

[VERSION]: 1 

[TYPE COUNT]: 1 

```txt
[ELF FILE 0]: ascendxxxb1_ascending_kernels_npu_0_mix.o 
```

[KERNEL TYPE]: mix 

[KERNEL LEN]: 511560 

[ASCEND META]: None 

全量打印 

```shell
msobjdump --dump-elf ${cmake_install_dir}/out/libascendc_kernels_npu.so --verbose 
```

执行上述命令，终端打印所有device信息，示例如下： 

[VERSION]: 1 

[TYPE COUNT]: 1 

```txt
[ELF FILE 0]: ascendxxxb1_ascending_kernels_npu_0_mix.o 
```

[KERNEL TYPE]: mix 

[KERNEL LEN]: 511560 

[ASCEND META]: None 

```ini
[elfheardinfo] 
```

ELF Header: 

```txt
Magic: 7f 45 4c 46 02 01 01 00 00 00 00 00 00 00 00 00 
```

Class: ELF64 

Data: 2's complement, little endian 

Version: 1 (current) 

OS/ABI: UNIX - System V 

ABI Version: 0 

Type: EXEC (Executable file) 

Machine: <unknown>: 0x1029 

```txt
Version: 0x1  
Entry point address: 0x0  
Start of program headers: 64 (bytes into file)  
Start of section headers: 510280 (bytes into file)  
Flags: 0x940000  
Size of this header: 64 (bytes)  
Size of program headers: 56 (bytes)  
Number of program headers: 2  
Size of section headers: 64 (bytes)  
Number of section headers: 20  
Section header string table index: 18  
Section Headers:  
[Nr] Name Type Address Off Size ES Flg Lk Inf Al  
[0] NULL 000000000000000 000000 000000 00 0 0  
[1].text PROGBITS 000000000000000 000b0 01a08 00 AX 0 4  
[19].strtab STRTAB 000000000000000 071278 00b6cb 00 0 1  
Key to Flags:  
W (write), A (alloc), X (execute), M (merge), S (strings), I (info), L (link order), O (extra OS processing required), G (group), T (TLS), C (compressed), x (unknown), o (OS specific), E (exclude), D (mbind), p (processor specific)  
There are no section groups in this file.  
Program Headers:  
Type Offset VirtAddr PhysAddr FileSiz MemSiz Flg Align  
LOAD 0x000b0 0x00000000000000 0x00000000000000 0x01a8 0x01a8 R E  
x1000  
GNU_STACK 0x000000 0x0000000000000 0x0000000000000 0x00000 0x11111111 
```

# 解压包含device信息的库文件并落盘

msobjdump --extract-elf ${cmake_install_dir}/out/libascendc_kernels_npu.so 

执行上述命令，默认在当前执行路径下落盘 

ascendxxxb1_ascendc_kernels_npu_0_mix.o文件。 

# 获取包含device信息的库文件列表

msobjdump --list-elf ${cmake_install_dir}/out/libascendc_kernels_npu.so 

执行上述命令，终端会打印所有文件，屏显信息形如： 

ELF file 0: ascendxxxb1_ascendc_kernels_npu_0_mix.o 

# 使用样例（标准/简易自定义算子工程）

以下面的算子工程为例（仅为示例，具体以实际算子工程为准），假设$ {cmake_install_dir}为算子Cmake编译产物根目录，目录结构如下，类似算子编译。 

![](images/34737738bc737deb5a62239b499db5f3ee91899817febcd8c9a8828011c663d7.jpg)


工具对编译生成的库文件（如*.so、*.a等）进行解析和解压，功能实现命令样例如下： 

# 解析包含device信息的库文件

支持两种打印方式，请按需选取，解析字段含义参见表2-50。 

# 简单打印

msobjdump --dump-elf ${cmake_install_dir}/op_api/lib/libcust_opapi.so 

执行上述命令，终端打印基础device信息，示例如下： 

.ascend.meta INFO   
VERSION:1   
DEBUG: debugBufSize $= 0$ ,debugOptions $= 0$ DYNAMIC_PARAM: dynamicParamMode $= 0$ OPTIONAL_PARAM: optionalInputMode $= 1$ ,optionalOutputMode $= 1$ .ascend.meta. [0]: AcosCustom_dad9c8ca8fcbfd789010c8b1c0da8e26_1   
KERNEL_TYPE: AIV   
DETERMINISTIC_INFO: 1   
BLOCK_NUM: 0xFFFFFF   
FUNCTION_ENTRY: 1   
.ascend.meta. [0]: AcosCustom_dad9c8ca8fcbfd789010c8b1c0da8e26_2_mix_AIV   
KERNEL_TYPE: MIX_AIV_MAIN   
MIX_TASK_RATION: [0:1]   
DETERMINISTIC_INFO: 1   
BLOCK_NUM: 0xFFFFFF   
FUNCTION_ENTRY: 2   
ascend.meta. [0]: AcosCustom_dad9c8ca8fcbfd789010c8b1c0da8e26_3_mix_AIV   
KERNEL_TYPE: MIX_AIV_MAIN   
MIX_TASK_RATION: [0:1]   
DETERMINISTIC_INFO: 1   
BLOCK_NUM: 0xFFFFFF   
FUNCTION_ENTRY: 3   
ascend.meta. [0]: AcosCustom da824ede53d7e754f85c14b9446ec2fc_1   
KERNEL_TYPE: AIV   
DETERMINISTIC_INFO: 1   
BLOCK_NUM: 0xFFFFFF   
FUNCTION_ENTRY: 1   
ascend.meta. [0]: AcosCustom da824ede53d7e754f85c14b9446ec2fc_2_mix_AIV   
KERNEL_TYPE: MIX_AIV_MAIN   
MIX_TASK_RATION: [0:1]   
DETERMINISTIC_INFO: 1   
BLOCK_NUM: 0xFFFFFF   
FUNCTION_ENTRY: 2   
ascend.meta. [0]: AcosCustom da824ede53d7e754f85c14b9446ec2fc_3_mix_AIV   
KERNEL_TYPE: MIX_AIV_MAIN   
DETERMINISTIC_INFO: 1   
BLOCK_NUM: 0xFFFFFF   
FUNCTION_ENTRY: 3 

# 全量打印

msobjdump --dump-elf ${cmake_install_dir}/op_api/lib/libcust_opapi.so --verbose 

执行上述命令，终端打印基础device信息，示例如下： 

.ascend.meta INFO   
VERSION:1   
DEBUG: debugBufSize $= 0$ ,debugOptions $= 0$ DYNAMIC_PARAMETER: dynamicParamMode $= 0$ OPTIONAL_PARAMETER: optionalInputMode $= 1$ ,optionalOutputMode $= 1$ .ascend.meta. [O]: AcosCustom_dad9c8ca8fcbfd789010c8b1c0da8e26_1   
KERNEL_TYPE: AIV   
DETERMINISTIC_INFO: 1   
BLOCK_NUM: 0xFFFFFF   
FUNCTION_ENTRY: 1   
.ascend.meta. [O]: AcosCustom_dad9c8ca8fcbfd789010c8b1c0da8e26_2_mix_AIV   
KERNEL_TYPE: MIX_AIV_MAIN   
MIX_TASK_RATION: [O:1]   
DETERMINISTIC_INFO: 1   
BLOCK_NUM: 0xFFFFFF   
FUNCTION_ENTRY: 2   
ascend.meta. [O]: AcosCustom_dad9c8ca8fcbfd789010c8b1c0da8e26_3_mix_AIV   
KERNEL_TYPE: MIX_AIV_MAIN   
MIX_TASK_RATION: [O:1]   
DETERMINISTIC_INFO: 1   
BLOCK_NUM: 0xFFFFFF   
FUNCTION_ENTRY: 3   
ascend.meta. [O]: AcosCustom.da824ede53d7e754f85c14b9446ec2fc_1   
KERNEL_TYPE: AIV   
DETERMINISTIC_INFO: 1 

```txt
BLOCK_NUM: 0xFFFFFF   
FUNCTION_ENTRY: 1   
.ascend.meta. [0]: AcosCustom.da824ede53d7e754f85c14b9446ec2fc_2_mix_aiv   
KERNEL_TYPE: MIX_AIV_MAIN   
MIX_TASK_RATION: [0:1]   
DETERMINISTIC_INFO: 1   
BLOCK_NUM: 0xFFFFFF   
FUNCTION_ENTRY: 2   
.ascend.meta. [0]: AcosCustom.da824ede53d7e754f85c14b9446ec2fc_3_mix_aiv   
KERNEL_TYPE: MIX_AIV_MAIN   
DETERMINISTIC_INFO: 1   
BLOCK_NUM: 0xFFFFFF   
FUNCTION_ENTRY: 3   
\(= = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = = =   
ELF Header: Magic: 7f 45 4c 46 02 01 01 00 00 00 00 00 00 00 00 00 00 Class: ELF64 Data: 2's complement, little endian Version: 1 (current) OS/ABI: UNIX - System V Size of program headers: 56 (bytes) Number of program headers: 3 Size of section headers: 64 (bytes) Number of section headers: 9 Section header string table index: 7   
Section Headers: [Nr] Name Type Address Off Size ES Flg Lk Inf Al [0] NULL 000000000000000000000000000000000000000000000000 . .. ........ [8].strtab STRTAB 000000000000000000529b 000119 00 0 1 Key to Flags: W (write), A (alloc), X (execute), M (merge), S (strings), I (info), L (link order), O (extra OS processing required), G (group), T (TLS), C (compressed), x (unknown), o (OS specific), E (exclude), D (mbind), p (processor specific)   
\(= \equiv \equiv \equiv\) [elf heard infos] in ascendxxx_matmul_leakyrelu_custom_MatmulLeakyreluCustom_e052bee3255764ac983389.o \(= \equiv \equiv \equiv \equiv\) : ELF Header: Magic: 7f 45 4c 46 02 01 01 00 00 00 00 00 00 00 00 Class: ELF64 Data: 2's complement, little endian Version: 1 (current) Section header string table index: 6   
Section Headers: [Nr] Name Type Address Off Size ES Flg Lk Inf Al [O] NULL 0000000000000000 000000 000000 0o 1 MS O [1].text PROGBITS 00000000001111111111111111111111111111111111111111111111111111 
```

# 解压包含device信息的库文件并落盘

msobjdump --extract-elf ${cmake_install_dir}/op_api/lib/libcust_opapi.so 

执行上述命令，默认在当前执行路径下保存解压文件，产物目录如下： 

![](images/f787d1faba79d6809ff9261e6a43e6fe7b3986a5c5baca7d26021a5f38a167a2.jpg)


![](images/dec36026e42644dbbbf8e47de17dfd7354fec18fb7010e0581c5ee1d9f8d4c98.jpg)


以acos_custom算子编译产物解压为例： 

查看算子原型（acos_custom.json） 

```javascript
"binList": [   
{ "implMode": "high_performance", "int64Mode": false, "simplifiedKeyMode": 0, "simplifiedKey": [....], "staticKey": "96b2b4bb2e3xxx,ee37ce8796ef139dexx" inputs": [ { "name": "x", "index": 0, "dtype": "float32", "format": "ND", "paramType": "required", "shape": [ -2 ], "format_MATCH_mode": "FormatAgnostic" } ], "outputs": [ { "name": "y", "index": 0, "dtype": "float32", "format": "ND", "paramType": "required", "shape": [ -2 ], "format_MATCH_mode": "FormatAgnostic" } ], "attrs": [ { "name": "tmp", "dtype": "int", "value": 0 }, ......... ], "opMode": "dynamic", "optionalInputMode": "gen_placeholder", "deterministic": "ignore", "binInfo": { "jsonFilePath": "ascendxxx/acos_custom/ AcosCustom_DA824ede53d7e754f85c14b9446ec2fc.json" } }, { "implMode": "high_performance", 
```

```json
"int64Mode": false, "simplifiedKeyMode": 0, "simplifiedKey": [ ], "staticKey": "27d6f997f2f3551xxxx,1385590c47affa578eb429xxx", "inputs": [ { "name": "x", "index": 0, "dtype": "float16", "format": "ND", "paramType": "required", "shape": [ -2 ], "format_MATCH_mode": "FormatAgnostic" } ], "outputs": [ { "name": "y", "index": 0, "dtype": "float16", "format": "ND", "paramType": "required", "shape": [ -2 ], "format_MATCH_mode": "FormatAgnostic" } ], "attrs": [ { "name": "tmp", "dtype": "int", "value": 0 }, ......... ], "opMode": "dynamic", "optionallInputMode": "gen_placeholder", "deterministic": "ignore", "binInfo": { "jsonFilePath": "ascendxxx/acos_custom/AcosCustom_dad9c8ca8fbfd789010c8b1c0da8e26.json" } } ] 
```

解析${op_type}_${parm_info}.o文件获取.ascend.meta段信息。 

msobjdump --dump-elf ./AcosCustom_da824ede53d7e754f85c14b9446ec2fc.o 

执行上述命令，终端屏显如下，字段与库文件解析类似，参见表2-50。 

```txt
.ascend.meta. [0]: AcosCustom.da824ede53d7e754f85c14b9446ec2fc_1  
KERNEL_TYPE: AIV  
.ascend.meta. [0]: AcosCustom.da824ede53d7e754f85c14b9446ec2fc_2_mix_aiv  
KERNEL_TYPE: MIX_AIV_MAIN  
MIX_TASK_RATION: [0:1]  
.ascend.meta. [0]: AcosCustom.da824ede53d7e754f85c14b9446ec2fc_3_mix_aiv  
KERNEL_TYPE: MIX_AIV_MAIN  
MIX_TASK_RATION: [0:1] 
```

查看${op_type}_${parm_info}.json，直观获取device文件中算子信息。 

```javascript
{
"binFileName": "AcosCustom.da824ede53d7e754f85c14b9446ec2fc",
"binFileSuffix": ".o",
"blockDim": -1,
"coreType": "MIX", 
```

```json
"intercoreSync": 1,   
"kernelName": "AcosCustom da824ede53d7e754f85c14b9446ec2fc",   
"magic": "RT_DEV_BINARY_MAGELF",   
"memoryStamping": [],   
"opParaSize": 24,   
"parameters": [],   
"sha256": "94e32d04fcaf435411xxxxxxxxxx",   
"workspace": {   
    "num": 1,   
    "size": [ -1 ] ,   
    "type": [ 0 ]   
},   
"kernelList": [   
    "tilingKey": 1,   
    "kernelType": "MIX_AIC",   
    "taskRation": "0:1",   
    "crossCoreSync": 0,   
    "gpuName": "AcosCustom da824ede53d7e754f85c14b9446ec2fc_1" },   
...... ],   
"taskRation": "tilingKey",   
"optionalInputMode": "gen_placeholder",   
"debugOptions": "printf",   
"debugBufSize": 78643200,   
"compileInfo": {},   
"supportInfo": { // 算子原型信息  
    "implMode": "high_performance",  
    "int64Mode": false,  
    "simplifiedKeyMode": 0,  
    "simplifiedKey": [ ......],  
    "staticKey": "96b2b4bb2e35fa3cxx,ee37ce8796ef139dedxxxxxxxxxx",  
    "inputs": [  
        "name": "x",  
        "index": 0,  
        "dtype": "float32",  
        "format": "ND",  
        "paramType": "required",  
        "shape": [ -2 ] ,  
        "format_MATCH_mode": "FormatAgnostic" }  
],   
"outputs": [   
    "name": "y",  
    "index": 0,  
    "dtype": "float32",  
    "format": "ND",  
    "paramType": "required",  
    "shape": [ -2 ] ,  
    "format_MATCH_mode": "FormatAgnostic" }  
],   
"attrs": [   
    "name": "tmp",  
    "dtype": "int",  
    "value": 0 ] 
```

```json
......]，"opMode": "dynamic","optionallInputMode": "gen_placeholder","deterministic": "ignore"},"filePath": "ascendxxx/acos custom/AcosCustom da824ede53d7e754f85c14b9446ec2fc.json"} 
```

# 获取包含device信息的库文件列表

msobjdump --list-elf ${cmake_install_dir}/op_api/lib/libcust_opapi.so 

执行上述命令，终端会打印所有文件，屏显信息形如： 

ELF file 0: ascendxxx_acos_custom_AcosCustom_dad9c8ca8fcbfd789010c8b1c0da8e26.json 

ELF file 1: ascendxxx_acos_custom_AcosCustom_dad9c8ca8fcbfd789010c8b1c0da8e26.o 

ElE file2: ascendxxx acos custom AcosCustom da824ede53d7e754f85c14b9446ec2fc.json 

ELF file 3: ascendxxx_acos_custom_AcosCustom_da824ede53d7e754f85c14b9446ec2fc.o 

# 2.10.7 基于样例工程完成 Kernel 直调

# 说明

本章节介绍的基于样例工程完成Kernel直调的方式，后续不再演进。推荐开发者直接使用命令行 或者编写Cmake文件进行编译，详细内容请参考2.3.1 AI Core SIMD编译。 

下文将以Add矢量算子为例对Kernel直调算子开发流程进行详细介绍。 

# 环境准备

使用Kernel Launch算子工程之前，需要参考1.2 环境准备章节安装驱动固件和 CANN软件包，完成开发环境和运行环境的准备。 

使用该算子工程要求cmake版本为3.16及以上版本，如不符合要求，请参考如下 的命令示例更新cmake版本，如下示例以更新到3.16.0版本为例。 

```shell
wget https://cmake.org/files/v3.16/cmake-3.16.0.tar.gz  
tar -zxf cmake-3.16.0.tar.gz  
cd cmake-3.16.0  
./bootstrap --prefix=/usr  
sudo make  
sudo make install 
```

# 工程目录

您可以单击矢量算子样例，获取核函数开发和运行验证的完整样例。样例目录结构如 下所示： 

```txt
AddKernelInvocationNeo  
-- cmake // CMake编译文件  
-- scripts  
gen_data.py // 输入数据和真值数据生成脚本文件  
verify_result.py // 验证输出数据和真值数据是否一致的验证脚本  
-- CMakeLists.txt // CMake编译配置文件  
-- add(custom.cpp // 矢量算子kernel实现  
-- data_utils.h // 数据读入写出函数  
-- main.cpp // 主函数，调用算子的应用程序，含CPU域及NPU域调用  
-- run.sh // 编译运行算子的脚本 
```

基于该算子工程，开发者进行算子开发的步骤如下： 

完成算子kernel侧实现。 

编写算子调用应用程序main.cpp。 

编写CMake编译配置文件CMakeLists.txt。 

根据实际需要修改输入数据和真值数据生成脚本文件gen_data.py；验证输出数据 和真值数据是否一致的验证脚本verify_result.py。 

根据实际需要修改编译运行算子的脚本run.sh并执行该脚本，完成算子的编译运 行和结果验证。 

# 算子 Kernel 侧实现

请参考工程目录中的矢量算子、矩阵算子、融合算子的Kernel实现完成Ascend C算子 实现文件的编写。 

# 说明

一个算子Kernel实现文件中只支持定义一个核函数。 

# 算子调用应用程序

下面代码以固定shape的add_custom算子为例，介绍算子核函数调用的应用程序 main.cpp如何编写。您在实现自己的应用程序时，需要关注由于算子核函数不同带来 的修改，包括算子核函数名，入参出参的不同等，合理安排相应的内存分配、内存拷 贝和文件读写等，相关API的调用方式直接复用即可。 

步骤1 按需包含头文件，通过ASCENDC_CPU_DEBUG宏区分CPU/NPU侧需要包含的头文 件。需要注意的是，NPU侧需要包含对应的核函数调用接口声明所在的头文件 aclrtlaunch_{kernel_name}.h（该头文件为工程框架自动生成），kernel_name为算 子核函数的名称。 

```c
include "data_utils.h" #ifndef ASCENDC_CPU_DEBUG #include "acl/acl.h" #include "acrltlaunch_add_custom.h" #else #include "tikicpulib.h" extern "C" __global __aicore__ void add_custom(GM_ADDR x, GM_ADDR y, GM_ADDR z); #endif 
```

步骤2 应用程序框架编写。该应用程序通过ASCENDC_CPU_DEBUG宏区分代码逻辑运行于 CPU侧还是NPU侧。 

```c
int32_t main(int32_t argc, char* argv[])  
{  
    uint32_t numBlocks = 8;  
    size_t inputByteSize = 8 * 2048 * sizeof(xi16_t);  
    size_t outputByteSize = 8 * 2048 * sizeof(xi16_t);  
} 
```

步骤3 CPU侧运行验证。完成算子核函数CPU侧运行验证的步骤如下： 


图 2-54 CPU 侧运行验证步骤


![](images/ee813cb6b635679e4b7c1635d5ab54def498238571a3b62065f27ecfafddc591.jpg)


```cpp
// 使用GmAlloc分配共享内存，并进行数据初始化  
uint8_t* x = (uint8_t*)AscendC::GmAlloc(inputByteSize);  
uint8_t* y = (uint8_t*)AscendC::GmAlloc(inputByteSize);  
uint8_t* z = (uint8_t*)AscendC::GmAlloc(outputByteSize);  
ReadFile("\\input/output_x.bin", inputByteSize, x, inputByteSize);  
ReadFile("\\input/output_y.bin", inputByteSize, y, inputByteSize);  
// 矢量算子需要设置内核模式为AIV模式  
AscendC::SetKernelMode(KernelMode::AIV_MODE);  
// 调用ICPU Runs_KF调测宏，完成核函数CPU侧的调用  
ICPU Runs_KF(add_custom, numBlocks, x, y, z);  
// 输出数据写出  
WriteFile("\\output/output_z.bin", z, outputByteSize);  
// 调用GmFree释放申请的资源  
AscendC::GmFree((void *x);  
AscendC::GmFree((void *y);  
AscendC::GmFree((void *z); 
```

步骤4 NPU侧运行验证。完成算子核函数NPU侧运行验证的步骤如下： 


图 2-55 NPU 侧运行验证步骤


![](images/3129efcb29d7b5f05c1c60b54be969591619e43a7335ee3f5900d424d9bbdf86.jpg)


```c
//初始化  
CHECK_ACL(acclInit(nullptr));  
//运行管理资源申请  
int32_t deviceld = 0;  
CHECK_ACL(aclstSetDevice(deviceld));  
aclstStream stream = nullptr;  
CHECK_ACL(aclstCreateStream(&stream));  
//分配Host内存  
uint8_t *xHost, *yHost, *zHost;  
uint8_t *xDevice, *yDevice, *zDevice;  
CHECK_ACL(aclstMallocHost((void**)(&xHost), inputByteSize));  
CHECK_ACL(aclstMallocHost((void**)(&yHost), inputByteSize));  
CHECK_ACL(aclstMallocHost((void**)(&zHost), outputByteSize));  
//分配Device内存  
CHECK_ACL(aclstMalloc((void*))&xDevice, inputByteSize, ACL_MEM_MALLOC Huge_FIRST));  
CHECK_ACL(aclstMalloc((void*)&yDevice, inputByteSize, ACL_MEM_MALLOC Huge_FIRST));  
CHECK_ACL(aclstMalloc((void*)&zDevice, outputByteSize, ACL_MEM_MALLOC Huge_FIRST));  
// Host内存初始化  
ReadFile("\\input/input_x.bin", inputByteSize, xHost, inputByteSize);  
ReadFile("\\input/input_y_bin", inputByteSize, yHost, inputByteSize);  
//将数据从Host上拷贝到Device上  
CHECK_ACL(aclstMemcpy(xDevice, inputByteSize, xHost, inputByteSize, ACL_MEMCPY_HOST_TO_DEVICE));  
CHECK_ACL(aclstMemcpy(yDevice, inputByteSize, yHost, inputByteSize, ACL_MEMCPY_HOST_TO_DEVICE));  
//用内核调用符<<>>调用核函数完成指定的运算，addcustom_do中封装了<<>>调用addCustom_do(numBlocks, nullptr, stream, xDevice, yDevice, zDevice); 
```

```txt
//用ACLRT_LAUNCH_KERNEL接口调用核函数完成指定的运算 // ACLRT_LAUNCH_KERNEL(addcustom)(numBlocks, stream, xDevice, yDevice, zDevice); CHECK_ACL(aclrtSynchronizeStream(stream)); //将Device上的运算结果拷贝回Host CHECK_ACL(aclrtMemcpy(zHost, outputByteSize, zDevice, outputByteSize, ACL_MEMCPY_DEVICE_TO_HOST)); WriteFile("\\./output/output_z.bin",zHost,outputByteSize); //释放申请的资源 CHECK_ACL(aclrtFree(xDevice)); CHECK_ACL(aclrtFree(yDevice)); CHECK_ACL(aclrtFree(zDevice)); CHECK_ACL(aclrtFreeHost(xHost)); CHECK_ACL(aclrtFreeHost(yHost)); CHECK_ACL(aclrtFreeHost(zHost)); //去初始化 CHECK_ACL(aclrtDestroyStream(stream)); CHECK_ACL(aclrtResetDevice(deviceld)); CHECK_ACL(aclFinalize()); 
```

# 说明

针对<<<>>>调用方式在2.2.3.2 核函数章节已有说明，这里仅对ACLRT_LAUNCH_KERNEL调用 接口的使用方法介绍如下： 

ACLRT_LAUNCH_KERNEL(kernel_name)(numBlocks, stream, argument list); 

● kernel_name：算子核函数的名称。 

numBlocks：规定了核函数将会在几个核上执行。每个执行该核函数的核会被分配一个逻辑 ID，即block_idx，可以在核函数的实现中调用GetBlockIdx来获取block_idx。 

● stream，类型为aclrtStream，stream用于维护一些异步操作的执行顺序，确保按照应用程 序中的代码调用顺序在Device上执行。stream创建等管理接口请参考“Stream管理”章节。 

● argument list：参数列表，与核函数的参数列表保持一致。 

# ----结束

# CMake 编译配置文件编写

本节会介绍CMake文件中一些关键环境变量和Cmake命令参数的说明，通常情况下不 需要开发者修改，但是这些参数可以帮助开发者更好的理解编译原理，方便有能力的 开发者对Cmake进行定制化处理。 


表 2-52 环境变量说明


<table><tr><td>环境变量</td><td>配置说明</td></tr><tr><td>SOC_VERSION</td><td>AI处理器的型号。
·针对如下产品：在安装AI处理器的服务器执行npu-smi info命令进行查询，获取Name信息。实际配置值为AscendName，例如Name取值为xxxx，实际配置值为Ascendxxxxy。
Atlas A2训练系列产品/Atlas A2推理系列产品
Atlas 2001/500 A2推理产品
Atlas 推理系列产品
Atlas 训练系列产品
·针对如下产品，在安装AI处理器的服务器执行npu-smi info -t board -i id -c chip_id命令进行查询，获取Chip Name和NPU Name信息，实际配置值为Chip Name_NPU Name。例如Chip Name取值为Ascendxxx，NPU Name取值为1234，实际配置值为Ascendxxx_1234。其中：
- id: 设备id，通过npu-smi info -l命令查出的NPU ID即为设备id。
- chip_id: 芯片id，通过npu-smi info -m命令查出的Chip ID即为芯片id。
Atlas 350 加速卡
Atlas A3 训练系列产品/Atlas A3 推理系列产品</td></tr><tr><td>ASCEND_CANNPACKAGE_PATH</td><td>CANN软件包安装后的实际路径。</td></tr><tr><td>CMAKE-built_TYPE</td><td>编译模式选项，可配置为：
·“Release”，Release版本，不包含调试信息，编译最终发布的版本。
·“Debug”，Debug版本，包含调试信息，便于开发者开发和调试。</td></tr><tr><td>CMAKE_install_prefix</td><td>用于指定CMAKE执行install时，安装的路径前缀，执行install后编译产物（ascendc.library中指定的target以及对应的头文件）会安装在该路径下。默认路径为当前目录的out目录下。</td></tr><tr><td>CMAKE_CXX_COPIER_LAUNCHER</td><td>用于配置C++语言编译器（如g++）、毕昇编译器的启动器程序为ccache，配置后即可开启cache缓存编译，加速重复编译并提高构建效率。使用该功能前需要安装ccache。
配置方法如下，在对应的CMakeLists.txt进行设置：
set(CMAKE_CXX_COPIER_LAUNCHER &lt;launchersprogram&gt;)其中&lt;launchersprogram&gt;是ccache的安装路径，比如ccache的安装路径为/usr/bin/ccache，示例如下：
set(CMAKE_CXX_COPIER_LAUNCHER /usr/bin/ccache)</td></tr></table>


表 2-53 Cmake 命令语法说明


<table><tr><td>Cmake命令</td><td>语法说明</td></tr><tr><td>add_executable</td><td>使用指定的源文件将可执行文件添加到项目中。和Cmake通用的命令参数使用方法一致。</td></tr><tr><td>ascendc.library</td><td>使用指定的核函数源文件向项目（project）添加库。语法格式如下：ascendc.library[STATIC | SHARED][&lt;source&gt;...]其中&lt;target_name&gt;表示库文件的名字，该库文件会根据命令里列出的源文件来建立。STATIC、SHARED的作用是指定生成的库文件的类型。STATIC库是目标文件的归档文件，在连接其它目标的时候使用。SHARED库会被动态连接（动态连接库），在运行时会被加载。&lt;source&gt;表示核函数源文件。</td></tr><tr><td>ascendc_fatbin_libRARY</td><td>使用指定的核函数源文件编译生成一个Kernel二进制文件，供Kernel加载和执行接口使用。语法格式如下：ascendc_fatbin_libRARY[&lt;source&gt;...]·&lt;target_name&gt;表示库文件的名字，该库文件会根据命令里列出的核函数源文件编译生成-target_name&gt;.o文件，放置于${CMAKE.install_prefix}/fatbin/${target_name}/路径下。·&lt;source&gt;表示核函数源文件。说明·Kernel加载与执行接口的调用流程和上文介绍的&lt;&lt;...&gt;&gt;等调用流程有所差异，具体流程请参考《应用开发指南(C&amp;C++)》中的“Kernel加载与执行”章节。·该编译选项暂不支持printf、DumpTensor、DumpAccChkPoint、assert接口。</td></tr><tr><td>ascendc.compiledefinitions</td><td>添加编译宏。可以添加Ascend C提供的编译宏和开发者自定义的编译宏。语法格式如下:ascendc.compiledefinitions( [PRIVATE] [&lt;xxx&gt;...])Ascend C提供的编译宏介绍如下:· HAVE_WORKSPACE用于表示kernel入口是否包含workspace入参。默认情况下为不包含;增加该编译宏后,表示包含,此时框架会获取kernel入参的倒数第一个参数(未配置HAVE_TILING),或倒数第二个参数(配置HAVE_TILING),自动在kernel侧设置系统workspace,开发者在kernel侧入参处获取的workspace为偏移了系统workspace后的用户workspace。当开发者使用了Matmul Kernel侧接口等需要系统workspace的高阶API时,建议开启此参数,入参排布、系统workspace的设置逻辑与2.10.2工程化算子开发保持一致,可减少算子实现在不同开发方式间切换带来的修改成本。需要注意的是,host侧开发者仍需要自行申请workspace的空间,系统workspace大小可以通过PlatformAscendCManager的GetLibApiWorkSpaceSize接口获取。HAVE_WORKSPACE的设置样例如下:ascendc.compiledefinitions(ascendc_kernels${RUN_MODE} PRIVATE HAVE_WORKSPACE)· HAVE_TILING用于表示kernel入口是否含有tiling入参。在配置了HAVE_WORKSPACE之后,此编译宏才会生效。默认情况下为不包含,开关关闭;增加该编译宏后,表示包含,此时框架会将kernel入参的最后一个参数当做tiling,将倒数第二个参数当做workspace。框架不会对此tiling入参做任何处理,仅通过该入参来判断workspace参数的位置,使用此编译宏可以和2.10.2 工程化算子开发保持入参一致,减少算子实现在不同开发方式间切换带来的修改成本。设置样例如下:ascendc.compiledefinitions(ascendc_kernels${RUN_MODE} PRIVATE HAVE_WORKSPACE HAVE_TILING)</td></tr><tr><td>ascendc.compileoptions</td><td>添加编译选项。可以添加相应的编译选项用于host侧与device侧的编译过程。语法格式如下:ascendc.compile(options(&lt;target_name&gt; PRIVATE[&lt;xxx&gt;...])默认情况下,指定的编译选项都将传递给device侧编译器进行编译。若想传递编译选项给host侧编译器,则需要使用“-forward-options-to-host-compiler”编译选项,该选项后的编译选项将传递给host侧编译器,示例如下:ascendc.compile(options(&lt;target_name&gt; PRIVATE-g-forward-options-to-host-compiler-gdwarf-4)如上代码所示,在编译时,“-g”编译选项传递给device侧编译器,“-gdwarf-4”编译选项传递给host侧编译器。备注:host侧编译选项只支持g++与clang编译器共同支持的编译选项。</td></tr><tr><td>ascendc_INCLUDEdirectories</td><td>添加开发者自定义的头文件搜索路径。语法格式如下:ascendc_INCLUDEdirectories(&lt;target_name&gt;[PRIVATE][&lt;xxx&gt;...])</td></tr></table>

简化的编译流程图如下图所示：将算子核函数源文件编译生成kernel侧的库文件（*.so 或*.a库文件）；工程框架自动生成核函数调用接口声明头文件；编译main.cpp（算子 调用应用程序）时依赖上述头文件，将编译应用程序生成的目标文件和kernel侧的库 文件进行链接，生成最终的可执行文件。 


图 2-56 编译简化流程图


![](images/9a5a72ca7f02cb8c6b97f115c14ef11552f946b12c66f21a20ad2d887e3823d5.jpg)


编译安装结束后在CMAKE_INSTALL_PREFIX目录下生成的编译产物示例如下；最终的 可执行文件会生成在cmake命令的执行目录下。 

![](images/7b0286cde87e1de7d60c010ccb09cc431ef5ad3c685c42fa3a420cee8110fbc9.jpg)


```txt
-kernels1  
- aclrtlaunch_matmul_custom.h  
- aclrtlaunch_add_custom.h  
-kernels2  
- aclrtlaunch_xxx.h  
- ... 
```

对于lib目录下生成的库文件可通过msobjdump工具进一步解析得到kernel信息，具体 操作参见2.10.6 msobjdump工具。 

# 输入数据和真值数据生成以及验证脚本文件

以固定shape的add_custom算子为例，输入数据和真值数据生成的脚本样例如下：根 据算子的输入输出编写脚本，生成输入数据和真值数据。 

```python
#!/usr/bin/python3
# --coding:utf-8 --.
import numpy as np
def gengolden_data.simple():
    input_x = np.random.uniform(1, 100, [8, 2048]).astype(np.float16)
    input_y = np.random.uniform(1, 100, [8, 2048]).astype(np.float16)
    golden = (input_x + input_y).astype(np.float16)
    input_x.tif("./input/Input_x.bin")
    input_y.tif("./input/Input_y.bin")
    golden.tif("./output/golden.bin")
if __name__ == __main__ :
    gengolden_data-simple() 
```

验证输出数据和真值数据是否一致的验证脚本样例如下：当前使用numpy接口计算了 输出数据和真值数据的绝对误差和相对误差，误差在容忍偏差范围内，视为精度符合 要求，输出"test pass"字样。 

```python
import os
import sys
import numpy as np
loss = 1e-3 # 容忍偏差，一般fp16要求绝对误差和相对误差均不超过千分之一
minimum = 10e-10
def verify_result(real_result, golden):
    real_result = np.fromfile(real_result, dtype=np.float16) # 从bin文件读取实际运算结果
    golden = np.fromfile(golden, dtype=np.float16) # 从bin文件读取预期运算结果
    result = np.abs(real_result - golden) # 计算运算结果和预期结果偏差
    deno = np maximum(np.abs(real_result), np.abs(golden)) # 获取最大值并组成新数组
    result_atol = np.less_equal(result, loss) # 计算绝对误差
    result_rtol = np.less_equal(result / np.add(deno, minimum), loss) # 计算相对误差
    if not result_rtol.all() and not result_atol.all():
        if np.sum(result_rtol == False) > real_result.size * loss and np.sum(result_atol == False) > real_result.size * loss:
            print("[ERROR] result error")
            return False
            print("test pass")
            return True
if __name__ == '__main__':
    verify_result(sys.argv[1],sys.argv[2]) 
```

# 修改并执行一键式编译运行脚本

您可以基于样例工程中提供的一键式编译运行脚本进行快速编译，并在CPU侧和NPU 侧执行Ascend C算子。一键式编译运行脚本主要完成以下功能： 


图 2-57 一键式编译运行脚本流程图


![](images/3e153ea61d424d7120b8a1a93aa316eb2c17983eac380e0d1d814936f30045d0.jpg)


# 须知

样例中提供的一键式编译运行脚本并不能适用于所有的算子运行验证场景，使用时请 根据实际情况进行修改。 

● 根据Ascend C算子的算法原理的不同，自行实现输入和真值数据的生成脚本。 

完成上述文件的编写后，可以执行一键式编译运行脚本，编译和运行应用程序。 

脚本执行方式和脚本参数介绍如下： 

```batch
bash run.sh --run-mode=npu --soc-version=<soc_version> --install-path=<install_path> --build-type=Debug --install-prefix=<install-prefix> 
```

```batch
bash run.sh -r npu -v <soc_version> -i <install_path> -b Debug -p <install-prefix> 
```


表2-54 脚本参数介绍


<table><tr><td>参数名</td><td>参数简写</td><td>参数介绍</td></tr><tr><td>--run-mode</td><td>-r</td><td>表明算子以cpu模式或npu模式运行。取值为cpu或npu。</td></tr><tr><td>--soc-version</td><td>-v</td><td>算子运行的AI处理器型号。说明AI处理器的型号&lt;sup&gt;1&lt;/sup&gt;请通过如下方式获取:·针对如下产品:在安装AI处理器的服务器执行npu-smi info命令进行查询,获取Name信息。实际配置值为AscendName,例如Name取值为xxxx,实际配置值为Ascendxxxx。Atlas A2 训练系列产品/Atlas A2 推理系列产品Atlas 200I/500 A2 推理产品Atlas 推理系列产品Atlas 训练系列产品·针对如下产品,在安装AI处理器的服务器执行npu-smi info -tboard -i id -c chip_id命令进行查询,获取Chip Name和NPU Name信息,实际配置值为Chip Name_NPU Name。例如Chip Name取值为Ascendxxx,NPU Name取值为1234,实际配置值为Ascendxxx_1234。其中:·id:设备id,通过npu-smi info -l命令查出的NPU ID即为设备id。·chip_id:芯片id,通过npu-smi info -m命令查出的Chip ID即为芯片id。Atlas 350 加速卡Atlas A3 训练系列产品/Atlas A3 推理系列产品</td></tr><tr><td>--install-path</td><td>-i</td><td>配置为CANN软件的安装路径,请根据实际安装路径进行修改。默认值为$HOME/Ascend/ascend-toolkit/latest。</td></tr><tr><td>--build-type</td><td>-b</td><td>编译模式选项,可配置为:·Release, Release版本,不包含调试信息,编译最终发布的版本。·Debug, Debug版本,包含调试信息,便于开发者开发和调试。默认值为Debug。</td></tr><tr><td>--install-prefix</td><td>-p</td><td>用于指定CMAKE执行install时,安装的路径前缀,执行install后编译产物(ascendLibrary中指定的target以及对应的头文件)会安装在该路径下。默认路径为当前目录的out目录下。</td></tr></table>

脚本执行完毕输出"test pass"字样表示算子精度符合要求。 

# CPU 侧验证核函数

在非昇腾设备上，开发者可以利用CPU仿真环境先行进行算子开发和测试，并在准备 就绪后，利用昇腾设备进行加速计算。在2.3 编译与运行章节，我们已经介绍了算子 Kernel程序NPU域的编译运行。相比于NPU域的算子运行逻辑，CPU域调试，实际上 是通过标准的GCC编译器编译算子Kernel程序。此时算子Kernel程序链接CPU调测库， 

执行编译生成的可执行文件，可以完成算子CPU域的运行验证。CPU侧的运行程序， 通过GDB通用调试工具进行单步调试，可以精准验证程序执行流程是否符合预期。 


图 2-58 CPU 域和 NPU 域的核函数运行逻辑对比


![](images/8a97a16f86a35ba4fa20d010b3da60b9031203ff6df5b84b15603aa1a4648ab9.jpg)


![](images/f9cd61d2180fe1535224b0f9e89635a8b29fe74116f30242e08d2d9eb814c6a2.jpg)


基于Kernel直调样例工程，通过ACLRT_LAUNCH_KERNEL接口调用核函数时，可实现 CPU与NPU域的代码的统一，且该方式仅支持以下型号： 

● Atlas A3 训练系列产品/Atlas A3 推理系列产品 

● Atlas A2 训练系列产品/Atlas A2 推理系列产品 

Atlas 推理系列产品 

下面代码以add_custom算子为例，介绍算子核函数在CPU侧验证时，算子调用的应用 程序如何编写（通过ACLRT_LAUNCH_KERNEL接口调用核函数的方式）。您在实现自 己的应用程序时，需要关注由于算子核函数不同带来的修改，包括算子核函数名，入 参出参的不同等，合理安排相应的内存分配、内存拷贝和文件读写等，相关API的调用 方式直接复用即可。 

# 步骤1 按需包含头文件。

```txt
include "data_utils.h" #include "acl/acl.h" #include "aclrtlaunch_add_custom.h" 
```

# 步骤2 应用程序框架编写。

```c
int32_t main(int32_t argc, char* argv[])  
{  
    uint32_t numBlocks = 8;  
    size_t inputByteSize = 8 * 2048 * sizeof(xi16_t);  
    size_t outputByteSize = 8 * 2048 * sizeof(xi16_t);  
    // 运行算子的调用程序  
    return 0;  
} 
```

# 步骤3 运行验证。

```txt
//初始化  
CHECK_ACL(acclInit(nullptr));  
//运行管理资源申请 
```

```c
int32_t deviceld = 0;  
CHECK_ACL(aclrtSetDevice(deviceld));  
aclrtStream stream = nullptr;  
CHECK_ACL(aclrtCreateStream(&stream));  
//分配Host内存  
uint8_t *xHost, *yHost, *zHost;  
uint8_t *xDevice, *yDevice, *zDevice;  
CHECK_ACL(aclrtMallocHost((void**)&(xHost), inputByteSize));  
CHECK_ACL(aclrtMallocHost((void**)&(yHost), inputByteSize));  
CHECK_ACL(aclrtMallocHost((void**)&(zHost), outputByteSize));  
//分配Device内存  
CHECK_ACL(aclrtMalloc((void**)&xDevice, inputByteSize, ACL_MEM_MALLOC Huge_FIRST));  
CHECK_ACL(aclrtMalloc((void**)&yDevice, inputByteSize, ACL_MEM_MALLOC Huge_FIRST));  
CHECK_ACL(aclrtMalloc((void**)&zDevice, outputByteSize, ACL_MEM_MALLOC Huge_FIRST));  
// Host内存初始化  
ReadFile("\\input/input_x.bin", inputByteSize, xHost, inputByteSize);  
ReadFile("\\input/input_y.bin", inputByteSize, yHost, inputByteSize);  
//将数据从Host上拷贝到Device上  
CHECK_ACL(aclrtMemcpy(xDevice, inputByteSize, xHost, inputByteSize, ACL_MEMCPY_HOST_TO_DEVICE));  
CHECK_ACL(aclrtMemcpy(yDevice, inputByteSize, yHost, inputByteSize, ACL_MEMCPY_HOST_TO_DEVICE));  
//用ACLRT-LaUNCH_KERNEL接口调用核函数完成指定的运算  
ACLRT-LaUNCH_KERNEL(addcustom)(numBlocks, stream, xDevice, yDevice, zDevice);  
CHECK_ACL(aclrtSynchronizeStream(stream));  
//将Device上的运算结果拷贝回Host  
CHECK_ACL(aclrtMemcpy(zHost, outputByteSize, zDevice, outputByteSize, ACL_MEMCPY_DEVICE_TO_HOST));  
WriteFile("\\output/output_z.bin", zHost, outputByteSize);  
//释放申请的资源  
CHECK_ACL(aclrtFree(xDevice));  
CHECK_ACL(aclrtFree(yDevice));  
CHECK_ACL(aclrtFree(zDevice));  
CHECK_ACL(aclrtFreeHost(xHost));  
CHECK_ACL(aclrtFreeHost(yHost));  
CHECK_ACL(aclrtFreeHost(zHost));  
//去初始化  
CHECK_ACL(aclrtDestroyStream(stream));  
CHECK_ACL(aclrtResetDevice(deviceld));  
CHECK_ACL(aclFinalize())); 
```

# ----结束

# 说明

为了实现CPU域与NPU域代码归一，仅对部分acl接口进行适配，开发者在使用CPU域调测功能 时，仅支持使用如下acl接口： 

● 有实际功能接口，支持CPU域调用 

aclDataTypeSize、aclFloat16ToFloat、aclFloatToFloat16。 

aclrtMalloc、aclrtFree、aclrtMallocHost、aclrtFreeHost、aclrtMemset、 aclrtMemsetAsync、aclrtMemcpy、aclrtMemcpyAsync、aclrtMemcpy2d、 aclrtMemcpy2dAsync、aclrtCreateContext、aclrtDestroyContext。 

● 无实际功能接口，打桩实现。 

Profiling数据采集 aclprofInit、aclprofSetConfig、aclprofStart、aclprofStop、aclprofFinalize。 

系统配置 aclInit、aclFinalize、aclrtGetVersion。 

运行时管理 aclrtSetDevice、aclrtResetDevice、aclrtCreateStream、 aclrtCreateStreamWithConfig、aclrtDestroyStream、aclrtDestroyStreamForce、 aclrtSynchronizeStream、aclrtCreateContext、aclrtDestroyContext。 

# 2.10.8 简易自定义算子工程

本章节介绍的简易自定义算子工程，是上文中介绍的自定义算子工程的简化版，对算 子的编译、打包、部署过程进行简化，便于开发者将该工程集成到自己的算子工程。 

# 说明

● 使用该工程，支持在如下平台进行自定义算子开发： 

Atlas A2训练系列产品 

Atlas 推理系列产品 

● 使用本工程开发的算子，只支持通过单算子API执行（aclnn）方式进行调用。 

● 本工程暂不支持算子的交叉编译功能。 

基于简易自定义算子工程的算子开发流程图如下： 

![](images/e2b4c68aa40908bd0fbd0f41573b31fb41a4e5fda7e43c96a9728e248151d731.jpg)


# 创建算子工程

和2.10.2.2 创建算子工程类似，简易自定义算子工程通过msOpGen生成，基于算子原 型定义输出算子工程，包括算子host侧代码实现文件、算子kernel侧实现文件以及工 程编译配置文件等。主要差异点在于：创建简易算子工程需要通过-f参数配置 framework框架为aclnn。 

使用msOpGen工具创建简易算子开发工程的步骤如下： 

步骤1 编写算子的原型定义json文件，用于生成算子开发工程。 

例如，AddCustom算子的json文件命名为add_custom.json，文件内容如下： 

```json
{
    "op": "AddCustom",
    "input_desc": [
        "name": "x",
        "param_type": "required",
        "format": [
            "ND",
            "ND",
            "ND"
        ],
        "type": [
            "fp16",
            "float",
            "int32"
        ]
    ],
} 
```

```jsonl
"name": "y",  
"param_type": "required",  
"format": [  
"ND",  
"ND",  
"ND"  
],  
"type": [  
"fp16",  
"float",  
"int32"  
]  
}  
],  
"output_desc": [  
{"name": "z",  
"param_type": "required",  
"format": [  
"ND",  
"ND",  
"ND"  
],  
"type": [  
"fp16",  
"float",  
"int32"  
]  
}  
]} 
```

步骤2 使用msOpGen工具生成算子的开发工程。以生成AddCustom的算子工程为例，下文仅 针对关键参数进行解释，详细参数说明请参见msOpGen工具。 

```shell
{$INSTALL_DIR}/python/site-packages/bin/msopgen gen -i $HOME/sample/add_custom.json -c ai_core<soc_version> -lan cpp -out $HOME/sample/AddCustom -f aclnn 
```

${INSTALL_DIR}为CANN软件安装后文件存储路径，请根据实际环境进行替换。 

-i：指定算子原型定义文件add custom.json所在路径，请根据实际情况修改。 

-c：ai_core-<soc version>代表算子在AI Core上执行，<soc version>为昇腾AI处 理器的型号。 

# 说明

AI处理器的型号<soc version>请通过如下方式获取： 

– 针对如下产品：在安装AI处理器的服务器执行npu-smi info命令进行查询，获取Name 信息。实际配置值为AscendName，例如Name取值为xxxyy，实际配置值为 Ascendxxxyy。 

Atlas A2 训练系列产品/Atlas A2 推理系列产品 

Atlas 200I/500 A2 推理产品 

Atlas 推理系列产品 

Atlas 训练系列产品 

– 针对如下产品，在安装AI处理器的服务器执行npu-smi info -t board -i id -c chip id命 令进行查询，获取Chip Name和NPU Name信息，实际配置值为Chip Name_NPU Name。例如Chip Name取值为Ascendxxx，NPU Name取值为1234，实际配置值为 Ascendxxx 1234。其中： 

id：设备id，通过npu-smi info -l命令查出的NPU ID即为设备id。 

chip_id：芯片id，通过npu-smi info -m命令查出的Chip ID即为芯片id。 

Atlas 350 加速卡 

Atlas A3 训练系列产品/Atlas A3 推理系列产品 

基于同系列的AI处理器型号创建的算子工程，其基础功能（基于该工程进行算子开发、编 译和部署）通用。 

-lan：参数cpp代表算子基于Ascend C编程框架，使用 $\mathsf { C } / \mathsf { C } + +$ 编程语言开发。 

-out：生成文件所在路径，可配置为绝对路径或者相对路径，并且工具执行用户 对路径具有可读写权限。若不配置，则默认生成在执行命令的当前路径。 

-f：表示框架类型，aclnn表示生成简易工程。 

步骤3 命令执行完后，会在-out指定目录或者默认路径下生成算子工程目录，工程中包含算 子实现的模板文件，编译脚本等，以AddCustom算子为例，目录结构如下所示： 

![](images/0bff058a577e73f933ed53e06413427eef1c3f6ba04f4f9ba495d61eb3b6cdc4.jpg)


# 说明

上述目录结构中的粗体文件为后续算子开发过程中需要修改的文件，其他文件无需修改。 

# ----结束

# 算子实现

参考2.10.2.4 Kernel侧算子实现、2.10.2.5 Host侧Tiling实现、2.10.2.3 算子原型定 义完成算子实现。 

# 算子编译

算子kernel侧和host侧实现开发完成后，需要对算子进行编译，生成算子静态库；自动 生成aclnn调用实现代码和头文件，链接算子静态库生成aclnn动态库，以支持后续的 单算子API执行方式（aclnn）的算子调用。编译过程如下： 

根据host侧算子实现文件自动生成aclnn接口aclnn_*.h和aclnn实现文件 aclnn_.cpp。 

编译Tiling实现和算子原型定义生成Tiling动态库liboptiling.so （libcust_opmaster_rt2.0）。 

编译kernel侧算子实现文件，并加载Tiling动态库，生成kernel静态库 libkernels.a。 

编译aclnn实现文件，并链接kernel静态库libkernels.a生成单算子API调用的动态 库libcust_opapi.so。 

上述编译过程示意图如下： 


图 2-59 编译过程示意图


![](images/8962e45bca19b316d9482c8474bc9ce3b63ce964520a79e85d8b4ed795f3f252.jpg)


上文描述的过程都封装在编译脚本中，开发者进行编译时参考如下的步骤进行操作： 

步骤1 完成工程编译相关配置。 

```cmake
修改cmake目录下config.cmake中的配置项，config.cmake文件内容如下：set(CMAKE_CXX_FLAGS_DEBUG "") set(CMAKE_CXX_flags_RELEASE "") if (NOT DEFINED CMAKE Builds_TYPE) set(CMAKE Builds_TYPE Release Cache STRING "")endif() if (CMAKE_install_prefix Initialized_TO_DEFAULT) set(CMAKE_install_prefix "${CMAKE_SOURCE_DIR}/build_out" Cache PATH "" FORCE)endif() if (NOT DEFINED ASCEND_CANN-package_PATH) set(ASCEND_CANN.Package_PATH /usr/local/Ascend/cann_CACHE_PATH ")//请替换为CANN软件包安装后的实际路径 
```

```cmake
endif()
if (NOT DEFINED ASCEND_PYTHON_EXECTABLE)
set(ASCEND_PYTHON_EXECTABLE python3 Cache STRING "") 
```


表 2-55 需要开发者配置的常用参数列表


<table><tr><td>参数名称</td><td>参数描述</td><td>默认值</td></tr><tr><td>ASCEND_CANN-PackAGE_PATH</td><td>CANN软件包安装路径,请根据实际情况进行修改。</td><td>“/usr/local/Ascend/cann”</td></tr><tr><td>CMAKE Builds_TYPE</td><td>编译模式选项,可配置为:- “Release”, Release版本,不包含调试信息,编译最终发布的版本。- “Debug”, “Debug”版本,包含调试信息,便于开发者开发和调试。</td><td>“Release”</td></tr><tr><td>CMAKE_install_PREFIX</td><td>编译产物存放的目录,不指定则为默认值。</td><td>${CMAKE_SOURCE_DI} /build_out:算子工程目录下的build_out目录</td></tr></table>

配置编译相关环境变量（可选） 


表 2-56 环境变量说明


<table><tr><td>环境变量</td><td>配置说明</td></tr><tr><td>CMAKE_CXX_comPI LER-LaUNCHER</td><td>用于配置C++语言编译器（如g++）、毕昇编译器的启 动器程序为ccache，配置后即可开启cache缓存编译， 加速重复编译并提高构建效率。用法如下，在对应的 CMakeLists.txt进行设置： set(CMAKE_CXX_comPILER_LAUNCHER &lt;launchersprogram&gt;) 其中&lt;launchersprogram&gt;是ccache的安装路径，比如 ccache的安装路径为/usr/bin/ccache，示例如下： set(CMAKE_CXX_comPILER_LAUNCHER /usr/bin/ccache)</td></tr></table>

步骤2 （可选）如果需要编译多个算子，在op_kernel目录下的CMakeLists.txt中增加要编译 的算子。 

```cmake
# set custom compile options
if ("{\CMAKE-built_TYPE}x" STREQUAL "Debugx")
    addOps.compile_options(ALL OPTIONS -g -O0)
endif()
#多算子编译通过add_kernel.compile命令增加算子源码文件即可
add_kernel.compile(AddCustom ${CMAKE_CURRENT_SOURCE_DIR}/addcustom.cpp)
add_kernel.compile(SubCustom ${CMAKE_CURRENT_SOURCE_DIR}/subcustom.cpp)
if(ENABLE_TEST AND EXISTS ${CMAKE_CURRENT_SOURCE_DIR}/testcases)
    add_subdirectory(testcases)
endif() 
```

步骤3 （可选）在算子工程中，如果开发者想对算子kernel侧代码增加一些自定义的编译选 项，可以参考支持自定义编译选项进行编译选项的定制。 

步骤4 在算子工程目录下执行如下命令，进行算子工程编译。 

```txt
./build.sh 
```

编译成功后，会在CMAKE_INSTALL_PREFIX/op_api目录存放生成的aclnn头文件和lib 库，每一个算子都会对应一个单独的头文件。具体目录结构如下： 

![](images/c77758b8f76a0cb112e0868ea4d49fc3288decacc7895bb6f1f886d25fd2c13a.jpg)


对于lib目录下生成的库文件可通过msobjdump工具进一步解析得到kernel信息，具体 操作参见2.10.6 msobjdump工具。 

----结束 

# 算子调用

完成单算子API调用。 

# 2.10.9 常用操作

# 2.10.9.1 如何开发动态输入算子

动态输入算子是指算子的输入个数是动态的，例如AddN，将N个输入tensor累加到一 起，输出一个tensor，输入tensor的个数是不固定的。动态输入算子的开发在构造和解 

析输入数据方面有差异：核函数的入参采用ListTensorDesc的结构存储输入数据信息， 对应的，调用时需构造TensorList结构保存参数信息。下面基于kernel直调和工程化算 子开发两种开发方式分别介绍具体开发流程。 

# 说明

下文仅列出代码片段，完整样例请参考动态输入算子样例（工程化算子开发）和动态输入算子样 例（kernel直调）。 

kernel直调 

参考ListTensorDesc数据结构自行定义ListTensorDesc和TensorDesc结构体， 并将实际的输入数据保存至ListTensorDesc结构中。示例如下: 

ptrOffset传入为ListTensorDesc首地址和数据指针首地址dataPtr之间的偏移 量，tensorDesc中保存两个输入的tensor描述信息， dataPtr传入为保存输入 数据的地址指针。 

```c
constexpr uint32_t SHAPE_DIM = 2;   
struct TensorDesc { uint32_t dim{SHAPE_DIM}; uint32_t index; uint64_t shape[SHAPE_DIM] = \{8, 2048\}; };   
TensorDesc xDesc; xDesc.index = 0; TensorDesc yDesc; yDesc.index = 1;   
constexpr uint32_t TENSOR_DESC_NUM = 2; struct ListTensorDesc { uint64_t ptrOffset; TensorDesc tensorDesc[TENSOR_DESC_NUM]; uintptr_t dataPtr[TENSOR_DESC_NUM]; } inputDesc;   
...   
inputDesc = \{(1 + (1 + SHAPE_DIM) * TENSOR_DESC_NUM) * sizeof uint64_t), \{xDesc, yDesc\}, \{(\mathrm{uintptr\_t})\mathrm{xDevice}, (\mathrm{uintptr\_t})\mathrm{yDevice}\} \}; 
```

– kernel侧调用时，直接传入ListTensorDesc表达的输入信息。示例如下： 

```c
void *inputDesclnDevice = nullptr;  
CHECK_ACL(aclrtMalloc((void **) & inputDesclnDevice, sizeof(ListTensorDesc), ACL_MEM_MALLOC Huge_FIRST));  
CHECK_ACL(aclrtMemcpy(inputDesclnDevice, sizeof(ListTensorDesc), &inputDesc, sizeof(ListTensorDesc), ACL_MEMPY_HOST_TO_DEVICE));  
ACLRT-LaUNCH_KERNEL(addncustom)(numBlocks, stream, inputDesclnDevice, zDevice); 
```

kernel侧算子实现，通过ListTensorDesc和TensorDesc提供的接口解析 ListTensorDesc输入信息，并处理。示例如下： 

```cpp
uint64_t buf[SHAPE_DIM] = {0};  
AscendC::TensorDesc<int32_t> tensorDesc;  
tensorDesc.SetShapeAddr(buf);  
listTensorDesc.GetDesc(tensorDesc, 0);  
uint64_t totalLength = tensorDesc.GetShape(0) * tensorDesc.GetShape(1);  
__gm__ uint8_t *x = listTensorDescGetDataPtr __gm__ uint8_t>(0);  
__gm__ uint8_t *y = listTensorDescGetDataPtr __gm__ uint8_t>(1); 
```

工程化算子开发 

单算子调用时，构造List类型tensor并传入。 

使用aclCreateTensor创建tensor后，需调用aclCreateTensorList，将创建好 的tensor组成List形式，如下所示。 

inputTensorList $=$ aclCreateTensorList(inputTensor_.data(), inputTensor_.size()); 

获取算子使用的workspace空间大小接口的入参，也需使用aclTensorList结构 参数，用来计算workspace的大小，调用示例如下。 

```txt
// 获取算子使用的workspace空间大小  
aclnnStatus aclnnAddNCustomGetWorkspaceSize(const aclTensorList *srcList, const aclTensor *out, uint64_t *workspaceSize, aclOpExecutor **executor); 
```

算子原型定义中，输入数据的参数类型设置为动态，示例如下。 

```cpp
this->Input("srcList") .ParamType(DYNAMIC) .DataType({ge::DT_FLOAT16}) .Format({ge::FORMAT_ND}); 
```

– host侧算子实现，获取动态输入信息的接口，需使用对应的动态接口。 

例如，Tiling函数和InferShape函数中，GetDynamicInputShape接口用于获 取动态输入的shape信息，InferDataType函数中， 

GetDynamicInputDataType接口用于获取动态输入的数据类型，示例如下。 

```cpp
namespace ge {
static graphStatus InferShape(gert::InferShapeContext *context)
{
const gert::Shape *x1_shape = context->GetDynamicInputShape(0, 0);
gert::Shape *y_shape = context->GetOutputShape(0);
*y_shape = *x1_shape;
return GRAPH_SUCCESS;
}
static graphStatus InferDataType(gert::InferDataTypeContext *context)
{
const auto inputDataType = context->GetDynamicInputDataType(0, 0);
context->SetOutputDataType(0, inputDataType);
return ge::GRAPH_SUCCESS;
}
} // namespace ge 
```

kernel侧算子实现，入参需传入动态结构的数据，并使用 

AscendC::ListTensorDesc结构做解析。 

核函数入参需传入动态结构的数据，例如GM_ADDR srcList，示例如下。 

```txt
extern "C" __global__ __aicore__ void addn_custom(GM_ADDR srcList, GM_ADDR z, GM_ADDR workspace, GM_ADDR tiling) 
```

对传入的参数srcList，需使用AscendC::ListTensorDesc结构做解析，得到每个 tensor的具体信息，示例如下。 

```cpp
AscendC::ListTensorDesc keyListTensorDesclInit(_gm__void*)srcList);  
GM_ADDR x = (_gm__uint8_t*)keyListTensorDesclInitGetDataPtr<_gm__uint8_t>(0);  
GM_ADDR y = (_gm__uint8_t*)keyListTensorDesclInitGetDataPtr<_gm__uint8_t>(1); 
```

# 2.10.9.2 如何在矢量编程时使能 Vector Core

针对Atlas 推理系列产品，其硬件架构除了AI Core外，还额外设置了单独的Vector Core，作为AI Core中Vector计算单元的补充，从而缓解Vector计算瓶颈。Vector Core 只包括了两种基础计算资源：向量计算单元（Vector Unit）和标量计算单元（Scalar Unit），分别用于完成向量与标量的数据计算。矢量算子开发时，使能Vector Core， 算子执行时会同时启动AI Core和Vector Core，这些核并行执行相同的核函数代码。 

本节将重点介绍如何使能Atlas 推理系列产品中的Vector Core。学习本节内容之前， 建议您先熟悉算子实现、2.10.7 基于样例工程完成Kernel直调、2.10.2 工程化算子开 发的相关内容，掌握基于AI Core的算子端到端开发流程。在此基础上本章将重点阐述 使能Vector Core时的差异点。具体如下： 

1. 完成算子kernel侧开发时，需要通过宏KERNEL_TASK_TYPE_DEFAULT使能Vector Core，算子执行时会同时启动AI Core和Vector Core， 此时AI Core会当成Vector Core使用。如下的代码样例展示了使能Vector Core的方法： 

```c
extern "C" global __aicore__ void addCustom(_gm uint8_t *x, _gm uint8_t *y, _gm uint8_t *z, _gm uint8_t *workspace, _gm uint8_t *tiling)  
{  
    GET_TILING_DATA(tilingData, tiling); 
```

```javascript
if (workspace == nullptr) { return; } GM_ADDR usr = AscendC::GetUserWorkspace workspace); KernelAdd op; op.Initial(x, y, z, tilingData.numBlocks, tilingData.totalLength, tilingDatatileNum); KERNEL_TASK_TYPE_DEFAULT(Kernel_TYPE_MIX_VECTOR_CORE); //使能VectorCore if (TILING_KEY_IS(1)) { op.Process1(); } else if (TILING_KEY_IS(2)) { op.Process2(); } //... 
```

2. 完成host侧tiling开发时，设置的numBlocks代表的是AI Core和Vector Core的总 数，比如用户在host侧设置numBlocks为10，则会启动总数为10的AI Core和 Vector Core；为保证启动Vector Core，设置数值应大于AI Core的核数。您可以 通过GetCoreNumAic接口获取AI Core的核数，GetCoreNumVector接口获取 Vector Core的核数。 如下代码片段，分别为使用kernel直调工程和自定义算子工 程时的设置样例，此处设置为AI Core和Vector Core的总和，表示所有AI Core和 Vector Core都启动。 

```cpp
- kernel直调工程
  auto ascendcPlatform = platform_ascending::PlatformAscendingCManager::GetInstance();
  auto totalCoreNum = ascendcPlatform.GetCoreNumAic();
  // ASCENDXXX请替换为实际的版本型号
  if (ascendingPlatform.GetSocVersion() == platform_ascending::SocVersion::ASCENDXXX) {
    totalCoreNum = totalCoreNum + ascendcPlatform.GetCoreNumVector();
  }
  ...
  kernel_name<<totalCoreNum, l2ctrl, stream>>(argument list); 
```

自定义算子工程  
//配套的host侧tiling函数示例：  
ge::graphStatus TilingFunc(gert::TilingContext* context)  
{ //使能VectorCore，将numBlocks置为AI Core中vector核数 $^+$ Vector Core中的vector核数auto ascendcPlatform $\equiv$ platform_ascendingc::PlatformAscendC-platformInfo);auto totalCoreNum $\equiv$ ascendcPlatform.GetCoreNumAic();//ASCENDXXX请替换为实际的版本型号if(ascendingPlatform.GetSocVersion() $\equiv =$ platform_ascendingc::SocVersion::ASCENDXXX){totalCoreNum $\equiv$ totalCoreNum $^+$ ascendcPlatform.GetCoreNumVector();}context->SetBlockDim(totalCoreNum); 

# 说明

● 请参考Ascend C API中具体API支持的型号，来判断API接口是否支持Atlas 推理系列产品 Vector Core。 

● 支持Vector Core后，因为AI Core和Vector Core会分别执行，通过不同的任务进行调度，所 以不支持核间同步指令，如IBSet、IBWait、SyncAll等。 

● 算子计算溢出（输入inf/nan或计算结果超出范围）时，需注意AI Core和Vector Core结果表 现不一致，AI Core仅支持饱和模式，Vector Core仅支持inf/nan模式。 

# 2.10.9.3 如何使用 workspace

workspace是设备侧Global Memory上的一块内存。workspace内存分为两部分：系统 workspace和用户workspace。 

系统workspace：Ascend C API需要预留的workspace内存 API在计算过程需要一些workspace内存作为缓存，因此算子需要为API预留 workspace内存，预留内存大小通过GetLibApiWorkSpaceSize接口获取。 

用户workspace：算子实现使用到的workspace内存 

算子内部需要通过额外的device内存进行数据交换或者缓存的时候才需要分配， 根据实际情况自行分配。使用场景如下： 

需要使用Unified Buffer和L1 Buffer上的空间且空间不够用时，可以将数据暂 存至workspace上。 

调用SyncAll等API接口时，需要workspace作为入参。 

其他需要使用Global Memory上内存空间的场景。 

不同开发方式下，具体的使用方法如下： 

工程化算子开发方式 

在tiling函数中先通过GetWorkspaceSizes接口获取workspace大小的存放位置， 再设置workspace的大小，框架侧会为其申请对应大小的设备侧Global Memory，在对应的算子kernel侧实现时可以使用这块workspace内存。在使用 Matmul Kernel侧接口等需要系统workspace的高阶API时，设置的workspace空 间大小为系统workspace和用户workspace之和。 

```cpp
//用户自定义的tiling函数  
static ge::graphStatus TilingFunc(gert::TilingContext* context)  
{  
AddApiTiling tiling;  
...  
size_t usrSize = 256; //设置用户需要使用的workspace大小为256字节。  
//如需要使用系统workspace需要调用GetLibApiWorkSpaceSize获取系统workspace的大小。  
auto ascendcPlatform = platform_ascending::PlatformAscendC(context->GetPlatformInfo());  
uint32_t sysWorkspaceSize = ascendcPlatform.GetLibApiWorkSpaceSize();  
size_t *currentWorkspace = context->GetWorkspaceSizes(1); //通过框架获取workspace的指针，GetWorkspaceSizes入参为所需workspace的块数。当前限制使用一块。  
currentWorkspace[0] = usrSize + sysWorkspaceSize; //设置总的workspace的数值大小，总的workspace空间由框架来申请并管理。  
} 
```

在device侧kernel入口处的workspace为用户的workspace指针： 

```txt
//用户写的Kernel函数，核函数必须包括GM_ADDR workspace入参，位置需要放在tiling之前  
extern "C" __global __aicore__ void add_custom(GM_ADDR x, GM_ADDR y, GM_ADDR z, GM_ADDR workspace, GM_ADDR tiling)  
{  
    ...  
} 
```

Kernel直调算子开发场景 

需要使用workspace空间时，建议开启编译选项HAVE_WORKSPACE。host侧开 发者仍需要自行申请workspace的空间，并传入。在使用Matmul Kernel侧接口等 需要系统workspace的高阶API时，设置的workspace空间大小为系统workspace 和用户workspace之和。系统workspace大小可以通过PlatformAscendCManager 的GetLibApiWorkSpaceSize接口获取。开启HAVE_WORKSPACE后，开发者在 kernel侧入参处获取的workspace为偏移了系统workspace后的用户workspace。 

# 2.10.9.4 如何进行 Tiling 调测

在工程化算子开发过程中，开发者需实现Tiling函数，该函数原型是固定的，接受 TilingContext作为输入。框架负责构造TilingContext并调用Tiling函数。若需单独进行 Tiling调测，开发者可通过OpTilingRegistry加载编译后的Tiling动态库，获取Tiling函 数的指针并进行调用，调用时Tiling函数的TilingContext入参使用ContextBuilder构 建。 

以下是具体步骤： 

步骤1 参考工程化算子开发的开发步骤，完成算子实现，并通过算子包编译或算子动态库编 译获取对应的Tiling动态库文件。 

算子包编译：Tiling实现对应的动态库为算子包部署目录下的liboptiling.so。具体 路径可参考2.10.2.6.2 算子包部署。 

动态库编译：Tiling实现集成在算子动态库libcust_opapi.so中。具体路径可参考 2.10.2.7 算子动态库和静态库编译。 

步骤2 编写测试代码。 

使用ContextBuilder配置输入输出Tensor的形状、数据类型、格式及平台信息等， 构建TilingContext。 

通过OpTilingRegistry的LoadTilingLibrary接口加载Tiling动态库；使用 GetTilingFunc接口获取Tiling函数指针。 

执行Tiling函数，验证其正确性。 

```cpp
// test.cpp
#include <iostream>
#include "exe_graph/runtime/storage_shape.h"
#include "tiling/context/context_builders.h"
int main()
{
gert::StorageShape x_shape = {{2, 32}, {2, 32)};
gert::StorageShape y_shape = {{2, 32}, {2, 32)};
gert::StorageShape z_shape = {{2, 32}, {2, 32)};
auto param = gert::TilingData::CreateCap(4096);
auto workspace_size_holder = gert::ContinuousVector::Create<size_t>(4096);
auto ws_size = reinterpret_cast<gert::ContinuousVector *>(workspace_size_holder.get());
auto holder = context ascendc::ContextBuilder()
.NodeloNum(2, 1)
.lrInstanceNum({1, 1})
.AddInputTd(0, ge::DT_FLOAT, ge::FORMAT_ND, ge::FORMAT_ND, x_shape)
.AddInputTd(1, ge::DT_FLOAT, ge::FORMAT_ND, ge::FORMAT_ND, y_shape)
.AddOutputTd(0, ge::DT_FLOAT, ge::FORMAT_ND, ge::FORMAT_ND, z_shape)
.TilingData(param.get())
.Workspace(ws_size)
.AddPlatformInfo("Ascendxxxyy")
.BuildTilingContext();
auto tilingContext = holder->GetContext<gert::TilingContext>();
context ascendc::OpTilingRegistry tplIns;
bool flag = tplIns.LoadTilingLibrary("/your/path/to/so_path/liboptiling.so"); //加载对应的Tiling动态库文件
if (flag == false) {
std::cout << "Failed to load tiling so" << std::endl;
return -1;
}
context ascendc::TilingFunc tilingFunc = tplIns.GetTilingFunc("AddCustom"); //获取AddCustom算子对应的Tiling函数，此处入参为otypes
if (tilingFunc != nullptr) {
ge::graphStatus ret = tilingFunc(tilingContext); //执行Tiling函数
if (ret != ge::GRAPH_SUCCESS) {
std::cout << "Exec tiling func failed." << std::endl;
return -1;
}
} else {
std::cout << "Get tiling func failed." << std::endl;
return -1;
}
return 0; 
```

步骤3 编译测试代码。 

```shell
g++ test.cpp -l${INSTALL_DIR}/include -L${INSTALL_DIR}/lib64 -Wl,-rpath,\$\{INSTALL_DIR\}/lib64 -ltiling api -lc_sec -lgraph_base -lregister -unified_dlog -lplatform -o test 
```

${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。以root用户安装为 例，安装后文件默认存储路径为：/usr/local/Ascend/cann。 

开发者根据需要链接依赖的动态库，必需链接的动态库有： 

libtiling_api.so：Tiling功能相关的动态库，包含ContextBuilder类、 OpTilingRegistry类等。 

libc_sec.so：安全函数库，libtiling_api.so依赖该库。 

libgraph_base.so：基础数据结构与接口库，libtiling_api.so依赖该库。 

libregister.so：业务函数注册相关库（例如Tiling函数注册，算子原型注册 等）。 

libunified_dlog.so：log库，libtiling_api.so依赖该库。 

libplatform.so：平台信息库，libtiling_api.so依赖该库；Tiling函数中使用硬 件平台信息时，需要依赖该库。 

步骤4 执行可执行文件。 

./test 

----结束 

# 2.10.9.5 如何使用 Tensor 原地操作提升算子性能

Tensor原地操作（inplace接口）是一种优化技术，全局申请、保留LocalTensor内存， 避免了频繁创建和销毁LocalTensor对象。AllocTensor、FreeTensor、EnQue、DeQue 接口不产生新的LocalTensor，而是在该全局LocalTensor上反复申请、释放、入队、出 队。其实现原理如下图所示： 


图 2-60 Tensor 原地操作实现原理


![](images/7ca894becf4410dd826522f035f61b51c04bc1e779e6be17cafcb066da8c146f.jpg)


# Tensor 原地操作的优势

减少栈变换：相比构造新Tensor的方式，inplace接口减少了LocalTensor的栈变 换，允许Tensor被反复使用。 

减少入队/出队操作：在调用EnQue、DeQue的过程中，TQue对象没有存储该 Tensor对应的Buffer地址，实际没有真正入队、出队，减少了反复入队、出队的 Scalar指令。 

# 保留 EnQue 和 DeQue 的原因

既然Tensor原地操作没有执行真正的入队出队操作，为什么还需要保留EnQue和 DeQue接口呢？ 

编程兼容性：为了保持编程接口的一致性，inplace接口仍然需要调用EnQue和 DeQue，确保代码结构的统一性和可维护性。 

内存同步功能：EnQue和DeQue操作中实现了内存读写同步功能，确保数据的一 致性和正确性，即使没有实际的队列操作，这些同步机制仍然需要保留。 

# 适用场景

适合计算循环次数多的场景：如图2-60所示，inplace接口虽然增加了TQue对象 InitBuffer的初始化开销，但显著减少了每次循环中AllocTensor、EnQue、DeQue和 FreeTensor内部对LocalTensor和事件的操作次数，特别适合需要多次循环来完成计算 的场景。 

# 使用方法

配置TQue对象：在创建TQue对象时，设置深度（depth）为0，启用inplace操作 模式。 

调用原地操作接口：使用inplace接口直接操作LocalTensor。 

AllocTensor和DeQue区分non-inplace和inplace接口，详情请参考 AllocTensor、DeQue。 

– FreeTensor和EnQue不区分non-inplace和inplace接口。 

# 示例代码

```cpp
// ...
namespace AscendC {
class MyKernel {
public:
    __aicore__ inline MyKernel() {}
    __aicore__ inline void Init(_gm__ uint8_t* src0Gm, _gm__ uint8_t* src1Gm, _gm__ uint8_t* dstGm)
        {
            src0Global.SetGlobalBuffer(_gm__ half*)src0Gm);
            src1Global.SetGlobalBuffer(_gm__ half*)src1Gm);
            dstGlobal.SetGlobalBuffer(_gm__ half*)dstGm);
            pipeInitBuffer(srcQue0, 1, BLOCK_SIZE * sizeof(full));
            pipeInitBuffer(srcQue1, 1, BLOCK_SIZE * sizeof(full));
            pipeInitBuffer.dstQue0, 1, BLOCK_SIZE * sizeof(full));
        }
    __aicore__ inline void Process()
        {
            for (int i = 0; i < REPTIMES; i++) {
                Copyln(i);
                Compute(i);
                CopyOut(i);
            }
        }
} 
```

```txt
}   
private: __aicore__inline void Copyln(int32_t i) { srcQue0 AllocTensor<half>(src0Local); srcQue1 AllocTensor<half>(src1Local); DataCopy(src0Local, src0Global[i*BLOCK_SIZE], BLOCK_SIZE); DataCopy(src1Local, src1Global[i*BLOCK_SIZE], BLOCK_SIZE); srcQue0.EnQue(src0Local); srcQue1.EnQue(src1Local); } __aicore__inline void Compute(int32_t i) { srcQue0.DeQue<half>(src0Local); srcQue1.DeQue<half>(src1Local); dstQue0 AllocTensor<half>(dstLocal); Add.dstLocal, src0Local, src1Local, BLOCK_SIZE); dstQue0.EnQue<half>(dstLocal); srcQue0.FreeTensor(src0Local); srcQue1.FreeTensor(src1Local); } __aicore__inline void CopyOut(int32_t i) { dstQue0.DeQue<half>(dstLocal); DataCopy.dstGlobal[i*BLOCK_SIZE], dstLocal, BLOCK_SIZE); dstQue0.FreeTensor.dstLocal); }   
private: TPipe pipe; TQue<QuePosition::VECIN, 0> srcQue0, srcQue1; TQue<QuePosition::VECOUT, 0> dstQue0; GlobalTensor<half> src0Global, src1Global, dstGlobal; LocalTensor<half> src0Local; LocalTensor<half> src1Local; LocalTensor<half> dstLocal; }; } // namespace AscendC 
```

# 2.10.10 FAQ

# 2.10.10.1 核函数运行验证时算子存在精度问题

# 现象描述

在进行算子NPU域的运行验证时，实际数据和真值数据不一致，算子存在精度问题。 

# 问题根因

算子出现精度问题，一般是由于算子的实现逻辑有误。 

# 定位步骤

Ascend C提供孪生调试的功能，通过CPU域的功能验证、gdb单步调试、printf数值打 印来定位算子的实现逻辑问题。本样例仅展示了可能会出现的场景，便于演示定位步 骤。实际使用过程中，请根据代码情况进行调试。 

步骤1 进行CPU域的功能验证，观察是否有日志报错。 

参考2.10.7 基于样例工程完成Kernel直调章节，编写CPU侧的运行验证代码，并进行 运行验证，发现CPU域的精度比对也存在不一致的问题。 

观察打屏日志中是否有报错信息，可搜索关键词"failed"。比如，下图的报错示例指 示，错误出现在代码中调用LeakyRelu接口的地方。 

leakyrelucustom_cpu:/usr/local/Ascend/CANN-7.0/x86_64-linux/tikcpp/tikcfw/interface/ kernel_operator_vec_binary Spiral_intf.h:447:void AscendC::LeakyReLU(const AscendC::LocalTensor<T>&, const AscendC::LocalTensor<T>&, const T&, const int32_t&) [with $T =$ float16::Fp16T; int32_t = int]: Assertion `false && "check vlrelu instr failed" failed 

通过上述报错日志，一般只能定位到报错的代码行，无法明确具体错误，接下来需要 通过gdb调试的方式或者printf打印的方式进一步精确定位。 

步骤2 gdb调试。下面的样例展示了拉起leakyrelu算子CPU侧运行程序的样例，该样例程序会 直接抛出异常，直接gdb运行，查看调用栈信息分析定位即可。其他场景下您可以使用 gdb打断点等基本操作进行调试。使用gdb调试Ascend C程序的详细内容请参考2.7.2.1 CPU域孪生调试。 

1. 使用gdb拉起待调试程序，进入gdb界面进行debug。 gdb leakyrelu_custom_cpu 

2. 单独调试一个子进程。 (gdb) set follow-fork-mode child 

3. 运行程序。 (gdb) r 

4. 通过bt查看程序调用栈。 (gdb) bt 

5. 查看具体层的堆栈信息，打印具体变量的值。本示例中，打印了tileLength为 1024，该程序中表示需要处理1024个half类型的数，大小为 1024*sizeof(half)=2048字节；输入Tensor xLocal的值，其中dataLen表示 LocalTensor的size大小为1024字节，只能计算1024字节的数据。可以看出两者的 长度不匹配，由此可以定位问题。 (gdb) f 5 #5 0x000055555555d364 in KernelLeakyRelu::Compute (this=0x7fffffffd7d0, progress=0) at /root/ AscendC_DemoCode-master/precision-error/vector/leakyrelu_custom.cpp:59 59 LeakyRelu(yLocal, xLocal, scalar, tileLength); (gdb) p tileLength $\$ 1=1024$ (gdb) p xLocal $\$ 10$ {<AscendC::BaseTensor<float16::Fp16T>> $=$ {<No data fields>}, address_ $=$ {logicPos = 9 '\t', bufferHandle = 0x7fffffffd930 "\003\005\377\377", dataLen $=$ 1024,bufferAddr $=$ 0,absAddr = ...} 

步骤3 printf打印。在合适的位置增加变量打印。样例代码如下： 

```txt
printf("xLocal size: %d\n", xLocal.GetSize());  
printf("tileLength: %d\n", tileLength); 
```

可以看到有如下打屏日志输出，打印了tileLength为1024，该程序中表示需要处理 1024个half类型的数；输入Tensor xLocal的size大小，为512，表示只能计算512个 half类型的数。可以看出两者的长度不匹配，由此可以定位问题。 

```txt
xLocal size: 512  
tileLength: 1024 
```

----结束 

# 2.10.10.2 运行验证时 AllocTensor/FreeTensor 失败

# 现象描述

通过NPU进行核函数的运行验证时，出现挂死现象；通过CPU进行核函数的运行验证 时，出现AllocTensor/FreeTensor失败的报错，日志报错和调用栈打印如下： 

```txt
[ERROR][Core_0][/usr/local/Ascend/cann/x86_64-linux/tikcpp/tikcfw/interface/kernel_tpipe.h:730]  
[AllocEventID][321678] current size is 4, max buffer number in same queue position is 4  
[ERROR][CORE_0][pid 321674] error happened! ===============  
SIGABRT Signal (Abort Signal from abort) caught, backtrace info:  
[#0] 0x000000000001e7c0: handler(int) at /usr/local/Ascend/cann/tools/tikicpulib/lib/include/  
kern_fwk.h:105  
[#1] 0x0000000000017c4f: signed char AscendC::TPipe::AllocEventID<(AscendC::HardEvent)5>() at /usr/  
local/Ascend/cann/x86_64-linux/tikcpp/tikcfw/interface/kernel_tpipe.h:733  
[#2] 0x000000000001426d: AscendC::TQueBind<(AscendC::TPosition)0, (AscendC::TPosition)9, 4,  
0>>FreeBuffer(unsigned char*) at /usr/local/Ascend/cann/x86_64-linux/tikcpp/tikcfw/interface/  
kernel_tpipe.h:1217  
[#3] 0x000000000011058: void AscendC::TQueBind<(AscendC::TPosition)0, (AscendC::TPosition)9, 4,  
0>>FreeTensor<float16::Fp16T>(AscendC::LocalTensor<float16::Fp16T>&) at /usr/local/Ascend/cann/x86_64-  
linux/tikcpp/tikcfw/interface/kernel_tpipe.h:1237  
[#4] 0x000000000000dfde: KernelAdd::Compute(int) at /home/xxxx/xxxx.cpp:59  
[#5] 0x000000000000dd1c: KernelAdd::Process() at /home/xxxx/xxxx.cpp:37 (discriminator 2)  
... 
```

# 问题根因

根据日志信息“current size is 4, max buffer number in same queue position is 4”可以明确该问题是因为同一个TPosition上QUE Buffer的数量超出限制导致。 

同一个TPosition上的所有Queue，连续调用AllocTensor接口申请的Tensor数量，根据 AI处理器型号的不同，有数量约束。申请Buffer时，需要满足该约束。 

Atlas 训练系列产品不超过4个。 

Atlas 推理系列产品AI Core不超过8个。 

Atlas 推理系列产品Vector Core不超过8个。 

Atlas A2 训练系列产品/Atlas A2 推理系列产品不超过8个。 

Atlas A3 训练系列产品/Atlas A3 推理系列产品不超过8个。 

Atlas 200I/500 A2 推理产品不超过8个。 

不满足该约束，在后续使用AllocTensor/FreeTensor可能会出现分配资源失败。比如： 

```cpp
AscendC::TQue<TPosition::VECIN, 1> que0;  
AscendC::TQue<TPosition::VECIN, 1> que1;  
AscendC::TQue<TPosition::VECIN, 1> que2;  
AscendC::TQue<TPosition::VECIN, 1> que3;  
AscendC::TQue<TPosition::VECIN, 1> que4;  
AscendC::TQue<TPosition::VECIN, 1> que5;  
// 比如，算子有6个输入，需要申请6块buffer  
// 通过6个队列为其申请内存，分别为que0~que5，每个que分配1块，申请VECIN TPosition上的buffer总数为6  
// 假设，同一个Position上连续Alloc的Buffer数量限制为4，超出该限制后，使用AllocTensor/FreeTensor会出现分配资源失败  
// 在NPU上可能体现为卡死等异常行为，在CPU Debug场景会出现报错提示  
pipe InitBuffer(que0, 1, len);  
pipe InitBuffer(que1, 1, len);  
pipe InitBuffer(que2, 1, len);  
pipe InitBuffer(que3, 1, len);  
pipe InitBuffer(que4, 1, len);  
pipe InitBuffer(que5, 1, len); 
```

```rust
AscendC::LocalTensor<T> local1 = que0 AllocTensor<T>();  
AscendC::LocalTensor<T> local2 = que1 AllocTensor<T>();  
AscendC::LocalTensor<T> local3 = que2 AllocTensor<T>();  
AscendC::LocalTensor<T> local4 = que3 AllocTensor<T>();  
// 第5个AllocTensor会出现资源分配失败，同一个TPosition上同时Alloc出来的Tensor数量超出了4个的限制  
AscendC::LocalTensor<T> local5 = que4 AllocTensor<T>(); 
```

# 处理步骤

如果确实有多块buffer使用，可以将多个buffer合并到一块buffer，通过偏移使用。样 例如下： 

```cpp
//此时建议通过以下方法解决：  
//如果确实有多块buffer使用，可以将多个buffer合并到一块buffer，通过偏移使用  
pipe.InitialBuffer(que0,1,len \*3);  
pipe.InitialBuffer(que1,1,len \*3);  
/*  
*分配出3块内存大小的LocalTensor,local1的地址为que0中buffer的起始地址，  
*local2的地址为local1的地址偏移len后的地址，local3的地址为local1的地址偏移  
*len\*2的地址  
*/  
int32_t offset1 = len;  
int32_t offset2 = len\*2;  
AscendC::LocalTensor<T> local1 = que0 AllocTensor<T>();  
AscendC::LocalTensor<T> local2 = local1[offset1];  
AscendC::LocalTensor<T> local3 = local1[offset2]; 
```

# 2.10.10.3 kernel 侧获取 Tiling 信息不正确

# 现象描述

通过算子在kernel侧实现代码中添加PRINTF打印发现kernel侧获取的Tiling信息不正 确。 

比如下文样例，增加的打印代码如下： 

```txt
PRINTF("tiling_data.totalLength: %d tiling_datatileNum: %d.\n", tiling_data.totalLength, tiling_datatileNum); 
```

打印的Tiling数据如下，全为0： 

```yaml
tiling_data.totalLength: 0 tiling_datatileNum: 0. 
```

# 问题根因

kernel侧获取Tiling信息不正确的原因一般有以下两种： 

host侧计算Tiling的逻辑不正确 

kernel侧核函数的参数未按照正确顺序填写 

# 处理步骤

步骤1 参考如下示例，打印TilingData的数据，确认host侧序列化保存的TilingData是否正 确。如果此时打印值有误，说明Tiling的计算逻辑可能不正确，需要进一步检查host侧 Tiling实现代码，排查计算逻辑是否有误。 

```cpp
std::cout<<\*reinterpret_cast<uint32_t \*>(context->GetRawTilingData()->GetData())<<std::endl; //按照实际数据类型打印TilingData第一个参数值，如需确认其他值，取值指针向后偏移即可 
```

步骤2 如果上一步骤中打印的TilingData正确，需要排查kernel侧核函数的参数是否按照正确 顺序填写。 

使用msOpGen工具创建算子工程，并基于工程进行kernel侧算子开发时，核函数的定 义模板已通过msOpGen工具自动生成，样例如下所示。参数按照 “输入、输出、 workspace、tiling”的顺序排布。请检查是否调整过参数顺序导致和正确顺序不一 致。 

```txt
include "kernel_operator.h"   
extern"C" global __aicore void addcustom(GM_ADDR x, GM_ADDR y, GM_ADDR z, GM_ADDR   
workspace, GM_ADDR tiling) { GET_TILING_DATA(tiling_data, tiling);//获取Tiling参数 //Todo: user kernel impl   
} 
```

----结束 

# 2.10.10.4 Kernel 编译时报错“error: out of jump/jumpc imm range”

# 现象描述

使用工程化算子开发方式，基于自定义算子工程进行算子开发。编译算子时失败，报 如下错误： 

```txt
[ERROR] [ascendxxx] PowerCustom_88a695f03edfbc0af76b9eaae9e4556c error: out of jump/jumpc imm range 
```

# 问题根因

该编译错误的原因是算子kernel代码过大，导致在编译时跳转指令跳转的偏移值超过 了限定的大小(int16_t的数据范围)，可通过添加编译选项“-mllvm -cce-aicore-jumpexpand=true”通过间接跳转的方式来避免该问题，让编译器能够正常编译。 

# 处理步骤

步骤1 在kernel侧的CMakeLists中通过add_ops_compile_options针对报错算子添加编译选项 “-mllvm -cce-aicore-jump-expand=true”，示例如下： 

```txt
add ops.compile-options(PowerCustom OPTIONS -mlxvm -cee-aicore-jump-expand=true) 
```

add_ops_compile_options的具体使用方法请参考支持自定义编译选项。 

步骤2 重新编译该算子。正常编译无报错。 

----结束 

# 2.10.10.5 含有 Matmul 高阶 API 的算子精度问题

本节针对含有Matmul高阶API的算子，为排查算子精度问题是否为算子中Matmul高阶 API调用方式导致，提供初步的问题定界和定位指导。如未特殊说明，下面均以Atlas A2 训练系列产品/Atlas A2 推理系列产品上的案例为例。 

具体排查过程主要有如下六个步骤： 

1. CPU域调试，观察报错信息； 

2. Matmul Tiling是否有修改，修改是否合理； 

3. 算子隐藏Vector计算，仅调用Matmul API，算子功能是否正确； 

4. 单核执行，算子功能是否正确； 

5. 排查Matmul API的使用是否正确； 

# 6. 用于算子调测的golden脚本是否正确。

# 步骤1 CPU域调试，观察报错信息

在完成算子代码的开发后，优先通过Kernel直调中的CPU调测工程，调试算子的功 能。在CPU域调试时，若编译或执行报错，日志中一般会有明显的报错信息。根据报 错信息的提示内容，通常可以快速定位到问题所对应的代码位置。这种方法尤其对 DataCopy参数设置错误导致的地址越界、算子Tiling参数设置不正确、其他内存越界 访问等基础参数的使用问题，可以快速定位到具体原因。 

# 1. 案例：

以下为matmul算子核函数的代码片段。该段代码实现了根据Global Memory上的 A、B矩阵和Tiling信息，计算每个核要使用数据的地址偏移、创建Matmul对象， 计算得到Matmul结果。 

```cpp
extern "C" __global__ __aicore__ void matmul/custom(GM_ADDR a, GM_ADDR b, GM_ADDR c, GM_ADDR workspace, GM_ADDR tilingGm)  
{  
    using A_T = half;  
    using B_T = half;  
    using C_T = float;  
    AscendC::TPipe pipe;  
    TCubeTiling tiling;  
    CopyTiling(&tiling, tilingGm);  
    AscendC::GlobalTensor<A_T> aGlobal;  
    AscendC::GlobalTensor<B_T> bGlobal;  
    AscendC::GlobalTensor<C_T> cGlobal;  
    aGlobal.SetGlobalBuffer(reinterpret_cast<gm_A_T>(a), tiling.M * tiling.Ka);  
    bGlobal.SetGlobalBuffer(reinterpret_cast<gm_B_T>(b), tiling.Ka * tiling.N);  
    cGlobal.SetGlobalBuffer(reinterpret_cast<gm_C_T>(c), tiling.M * tiling.N);  
    int offsetA = 0;  
    int offsetB = 0;  
    int offsetC = 0;  
    bool isTransA = false;  
    bool isTransB = true;  
    int tailM = 0;  
    int tailN = 0;  
    CalcGMOffset(GetBlockIdx(), tiling, offsetA, offsetB, offsetC, tailM, tailN, isTransA, isTransB);  
    auto gmA = aGlobal[offsetA];  
    auto gmB = bGlobal[offsetB];  
    auto gmC = cGlobal[offsetC];  
    AscendC::Matmul<AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, A_T>, AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, B_T>, AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, C_T>> mm;  
    REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm, &tiling);  
    mm.SetTensorA(gmA, isTransA);  
    mm.SetTensorB(gmb, isTransB);  
    mm.setTail(tailM, tailN);  
    mm.IterateAll(gmc);  
    mm.End(); 
```

以下为上述代码在CPU域调试时输出的执行结果。以下示例中的路径请以实际情 况为准。 

[ASSERT] $HOME/Ascend/xxxxx/include/ascendc/highlevel_api/lib/matmul/matmul_client.h:268: Assertion `isTransposeB $< = |$ B_TYPE::isTrans && "It is not allowed to do B transpose when matmul B transpose is not defined."' 

[ASSERT] $HOME/Ascend/xxxxx/include/ascendc/highlevel_api/lib/matmul/matmul_client.h:268: Assertion `isTransposeB $< =$ B_TYPE::isTrans && "It is not allowed to do B transpose when matmul B transpose is not defined."' 

本案例中的算子有精度问题，于是使用CPU调测该算子功能，CPU运行后，根据 报错信息提示的矩阵B的transpose未定义，查看矩阵B的相关设置代码，发现 Matmul对象定义时未设置矩阵B的B_TYPE::isTrans，而SetTensorB接口设置了 isTransB = true，导致执行报错。所以，此问题的根因为SetTensorB设置的 isTransB值与B_TYPE不符。 

# 步骤2 Matmul Tiling是否有修改，修改是否合理

一般含有Matmul的算子Tiling实现中，通过调用GetTiling接口获取Matmul Tiling，其 数据类型为TCubeTiling结构体，这时这组Tiling值是合法的。某些情况下，用户自定 义了一组TCubeTiling参数值，或者，基于GetTiling接口返回的TCubeTiling，自行修改 了其中的部分值，这样的修改需要满足参数间的制约条件。 

为获取所有Tiling参数值，需要打印Tiling参数相关的日志。设置日志环境变量，获取 MatmulTiling参数值。设置环境变量的命令如下： 

```typescript
export ASCENDGLOBAL_LOG_LEVEL=1  
export ASCEND_SLOG_PRINT_TO_STDOUT=1 
```

在日志中搜索“MatmulTiling”关键字，参照TCubeTiling约束条件，检查Tiling取值 是否合法。若不满足某条约束条件，需要修改对应的相关参数，使该组TCubeTiling参 数值均合法。 

```ini
cat test_tiling.log |grep MatmulTiling // test_tiling.log为示例日志文件名  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.864  
[matmul_tiling_base.cpp:697][PrintTilingDataInfo]MatmulTiling:M = 1024  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.870  
[matmul_tiling_base.cpp:698][PrintTilingDataInfo]MatmulTiling:N = 640  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.873  
[matmul_tiling_base.cpp:699][PrintTilingDataInfo]MatmulTiling:Ka = 256  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.876  
[matmul_tiling_base.cpp:700][PrintTilingDataInfo]MatmulTiling:Kb = 256  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.879  
[matmul_tiling_base.cpp:701][PrintTilingDataInfo]MatmulTiling:singleCoreM = 512  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.882  
[matmul_tiling_base.cpp:702][PrintTilingDataInfo]MatmulTiling:singleCoreN = 640  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.884  
[matmul_tiling_base.cpp:703][PrintTilingDataInfo]MatmulTiling:singleCoreK = 256  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.887  
[matmul_tiling_base.cpp:704][PrintTilingDataInfo]MatmulTiling:baseM = 256  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.890  
[matmul_tiling_base.cpp:705][PrintTilingDataInfo]MatmulTiling:baseN = 128  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.893  
[matmul_tiling_base.cpp:706][PrintTilingDataInfo]MatmulTiling:baseK = 64  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.896  
[matmul_tiling_base.cpp:707][PrintTilingDataInfo]MatmulTiling:depthA1 = 10  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.899  
[matmul_tiling_base.cpp:708][PrintTilingDataInfo]MatmulTiling:depthB1 = 2  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.902  
[matmul_tiling_base.cpp:709][PrintTilingDataInfo]MatmulTiling:depthAL1CacheUB = 0  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.905  
[matmul_tiling_base.cpp:710][PrintTilingDataInfo]MatmulTiling:depthBL1CacheUB = 0  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.908  
[matmul_tiling_base.cpp:711][PrintTilingDataInfo]MatmulTiling:stepM = 2  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.912  
[matmul_tiling_base.cpp:712][PrintTilingDataInfo]MatmulTiling:stepN = 1  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.915  
[matmul_tiling_base.cpp:713][PrintTilingDataInfo]MatmulTiling:IsBias = 1  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.917  
[matmul_tiling_base.cpp:714][PrintTilingDataInfo]MatmulTiling:transLength = 0  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.920  
[matmul_tiling_base.cpp:715][PrintTilingDataInfo]MatmulTiling:updateOrder = 0  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.923  
[matmul_tiling_base.cpp:716][PrintTilingDataInfo]MatmulTiling-shareMode = 0  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.926  
[matmul_tiling_base.cpp:717][PrintTilingDataInfo]MatmulTiling-usedLSize = 295424 
```

```ini
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.929  
[matmul_tiling_base.cpp:718][PrintTilingDataInfo] MatmulTiling: usedLCSize = 131072  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.932  
[matmul_tiling_base.cpp:719][PrintTilingDataInfo] MatmulTiling: usedUBSize = 0  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.935  
[matmul_tiling_base.cpp:720][PrintTilingDataInfo] MatmulTiling: batchM = 1  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.938  
[matmul_tiling_base.cpp:721][PrintTilingDataInfo] MatmulTiling: batchN = 1  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.941  
[matmul_tiling_base.cpp:722][PrintTilingDataInfo] MatmulTiling: singleBatchN = 1  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.943  
[matmul_tiling_base.cpp:723][PrintTilingDataInfo] MatmulTiling: singleBatchN = 1  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.946  
[matmul_tiling_base.cpp:724][PrintTilingDataInfo] MatmulTiling: stepKa = 4  
[INFO] ASCENDCKKERNEL(1202803,ascendc_kernels_bbit):2024-10-12-08:53:59.636.949  
[matmul_tiling_base.cpp:725][PrintTilingDataInfo] MatmulTiling: stepKb = 1 
```

例如，根据如上打印出的TCubeTiling参数，对照TCubeTiling约束条件查看各个参数的 取值，depthA1的取值应该等于stepM*stepKa或者stepM*stepKa*2，而depthA1的取 值为10，既不等于stepM*stepKa=8，也不等于stepM*stepKa*2=16，不满足约束条 件，因此需要校正depthA1的值。 

# 步骤3 算子隐藏Vector计算，仅调用Matmul API，算子功能是否正确

融合算子的代码既包含Matmul API，也包含Vector计算API。通过在算子代码中删除 Vector计算API，只保留Matmul API，快速定界是否为Matmul API的错误使用导致了 融合算子的精度问题。具体排查过程为：修改算子代码逻辑，删除Vector计算的代 码，同步完成golden脚本相应修改，完成适配修改后，CPU域或NPU域上执行算子， 观察算子结果是否正确。若算子结果正确，说明代码中Matmul API的使用方式正确， 需要继续排查Vector计算是否正确；反之，若算子结果不正确，需要继续排查Matmul API的使用是否正确。 

# 案例：

以融合算子matmul_leakyrelu为例，执行算子后，出现如下图所示的精度问题。 

```txt
data index: 000195, expected: -0.693000019, actual: -69.300003052, rdiff: -99.000000  
data index: 000196, expected: -0.209000006, actual: -20.899999619, rdiff: -99.000000  
data index: 000197, expected: -0.517000020, actual: -51.700000763, rdiff: -99.000000  
data index: 000200, expected: -0.193000004, actual: -19.300001144, rdiff: -99.000000  
data index: 000202, expected: -0.684000015, actual: -68.400001526, rdiff: -99.000000  
data index: 000204, expected: -0.422000021, actual: -42.200000763, rdiff: -98.999992  
data index: 000209, expected: -0.109000005, actual: -10.900000572, rdiff: -99.000000  
error ratio: 0.4517, tolerance: 0.0001  
[ERROR] result error 
```

修改算子代码，注释屏蔽LeakyRelu API计算，同时，需要适配修改相应的内存分 配和涉及的同步等代码；然后，注释golden脚本中LeakyRelu计算，具体修改示例 如下。 

以下代码为算子核函数的代码片段。 

```cpp
template<typename aType, typename bType, typename cType, typename biasType> __aicore__ inline void MatmulLeakyKernel<aType, bType, cType, biasType>::Process(AscendC::TPipe *pipe) {
    uint32_t computeRound = 0;
    matmulObj.SetTensorA(aGlobal);
    matmulObj.SetTensorB(bGlobal);
    matmulObj.SetBias(biasGlobal);
    while (matmulObj.template Iterate(true)) {
        MatmulCompute();
        // LeakyReluCompute(); // 注释LeakyReluCompute Vector计算
        CopyOut(computeRound);
        computeRound++;
    }
    matmulObj.End();
} 
```

}   
template<typename aType, typename bType, typename cType, typename biasType> _aicore__inline void MatmulLeakyKernel<aType,bType,cType,biasType>::MatmulCompute() { reluOutLocal $=$ reluQueue_AllocTensor<cType>(); matmulObj.template GetTensorC<true>(reluOutLocal,false, true); reluOutQueue_EnQue(reluOutLocal); //将LeakyReluCompute()接口里的reluOutLocal结果输出提前到这里   
}   
template<typename aType, typename bType, typename cType, typename biasType> _aicore__inline void MatmulLeakyKernel<aType,bType,cType,biasType>::LeakyReluCompute() { LeakyRelu(reluOutLocal,reluOutLocal,(cType)0.1,tiling.baseM\*tiling.baseN); reluOutQueue_EnQue(reluOutLocal);   
}   
template<typename aType, typename bType, typename cType,typename biasType> _aicore__inline void MatmulLeakyKernel<aType,bType,cType,biasType>::CopyOut uint32_t count) { reluOutQueue_DeQue<cType>(); const uint32_t roundM $=$ tiling.singleCoreM / tiling.baseM; const uint32_t roundN $=$ tiling.singleCoreN / tiling.baseN; uint32_t startOffset $=$ (count $\%$ roundM\*tiling.baseM\*tiling.N $^+$ count / roundM\*tiling.baseN); AscendC::DataCopyParams copyParam $=$ {(uint16_t)tiling.baseM,(uint16_t)(tiling.baseN\* sizeof(cType)/ AscendC::DEFAULT_C0_SIZE),0, (uint16_t)((tiling.N - tiling.baseN)\*sizeof(cType)/ AscendC::DEFAULT_C0_SIZE);}； DataCopy(cGlobal[startOffset],reluOutLocal,copyParam); reluOutQueue_FreeTensor(reluOutLocal);   
} 


以下代码为golden生成脚本的代码片段。


```python
def gengolden_data():  
    M = 1024  
    N = 640  
    K = 256  
    input_a = np.random.randint(-10, 10, [M, K]).dtype(np.float16)  
    input_b = np.random.randint(-10, 10, [K, N]).dtype(np.float16)  
    input.bias = np.random.randint(-10, 10, [N]).dtype(np.float32)  
    alpha = 0.001  
    golden = (np/matmul(input_a.astype(np.float32), input_b.astype(np.float32)) + input.bias).dtype(np.float32)  
    # golden = np.where(golden >= 0, golden, golden * alpha) # 与kernel保持一致，golden生成也需注释相应的LeakyRelu计算  
    os.system("mkdir -p input")  
    os.system("mkdir -p output")  
    input_a.tofile("/input/x1_gm.bin")  
    input_b.tofile("/input/x2_gm.bin")  
    input.bias.tofile("\\/input/bias.bin")  
    golden.tofile("\\/output/golden.bin") 
```


删除LeakyRelu计算后，执行用例，算子结果比对正确，如下所示。


```txt
-- Installing: $HOME/samples/ Precision_Check_Guide/samples-master/operator/ MatmulLeakyReluCustomSample/KernelLaunch/MatmulLeakyRelulnovation_cube_vec/out/bin/ ascendc_kernels_bbit  
8901941eee314bcd64d24ff5f8d21247 output/golden.bin  
8901941eee314bcd64d24ff5f8d21247 output/output.bin  
error ratio: 0.0000, tolerance: 0.0001  
test pass 
```

由此可确定，算子代码中已正确使用Matmul API，并得到了正确的Matmul API 计算结果，需要继续定位LeakyReluCompute函数内LeakyRelu接口使用中存在的 问题。 

# 步骤4 单核执行，算子功能是否正确

验证单核场景下算子的功能是否正确，可以帮助快速定界是Matmul API的计算结果不 符合预期，还是算子代码中错误调用Matmul API导致。由于Matmul API内部实现的 是单核的计算逻辑，所以单核的计算结果正确，而多核的计算结果错误的情况，说明 单核上的Matmul API的使用及计算正确，这时需要排查与多核切分相关的代码逻辑是 否正确，比如每个核的输入和输出地址偏移是否正确，每个核上的尾块地址设置是否 正确。如果验证单核场景下，算子精度不正确，需要排查Matmul API的使用是否正 确，具体可参考步骤5。 

提示，包含Matmul的算子的Tiling实现中，Matmul的多核Tiling需要使用 MultiCoreMatmulTiling构造多核Tiling对象，通过SetDim接口设置Matmul计算所用 的核数。注意：这里设置的核数为Matmul计算所用的核数，仅在多核场景下设置，用 于计算tiling参数。如下两个案例为MIX模式的算子，SetDim的设置规则请参考MIX场 景核数设置规则。 

案例1：多核切分场景，输出地址偏移不正确 

以 $\mathtt { M } = 5 1 2$ ， $N { = } 1 0 2 4$ ， $\mathtt { K } = 5 1 2$ 的Matmul为例，MIX模式的算子代码中设置AIC核数 为4，AIV核数为8，因为本案例以分离模式为例，所以SetDim设置为AIV核数的取 值8。多核场景下执行该算子，计算结果精度错误。 

以下为算子Tiling计算的代码片段。 

```txt
int8_t *GenerateTiling(const char *socVersion)  
{  
    int M = 512;  
    int N = 1024;  
    int K = 512;  
    TPosition leftPosition = TPosition::GM;  
    CubeFormat leftFormat = CubeFormat::ND;  
    DataType leftDtype = DataType::DT_FLOAT16;  
    bool isTransA = false;  
    TPosition rightPosition = TPosition::GM;  
    CubeFormat rightFormat = CubeFormat::ND;  
    DataType rightDtype = DataType::DT_FLOAT16;  
    bool isTransB = false;  
    TPosition resultPosition = TPosition::GM;  
    CubeFormat resultFormat = CubeFormat::ND;  
    DataType resultDtype = DataType::DT_FLOAT;  
    bool isBias = false;  
    int usedCoreNum = 8;  
    int32_t baseM = 128;  
    int32_t baseN = 256;  
    optiling::TCubeTiling tilingData;  
    auto ascendcPlatform = platform_ascending::PlatformAscendCManager::GetInstance(socVersion);  
    MultiCoreMatmulTiling tilingApi(*ascendcPlatform);  
    tilingApi.SetDim(usedCoreNum); // 设置为AIV核数8  
    tilingApi.Set机型(leftPosition, leftFormat, leftDtype, isTransA);  
    tilingApi.SetBType(rightPosition, rightFormat, rightDtype, isTransB);  
    tilingApi.SetCType(resultPosition, resultFormat, resultDtype);  
    tilingApi.SetOrgShape(M, N, K);  
    tilingApi.SetShape(M, N, K);  
    tilingApi.SetFixSplit(baseM, baseN, -1);  
    tilingApi.SetBias(isBias);  
    tilingApi.SetBufferSpace(-1, -1, -1);  
    int64_t res = tilingApi.GetTiling(tilingData);  
    if (res == -1) {  
        std::cout << "gen tiling failed" << std::endl;  
    } 
```

```txt
return GetTilingBuf(&tilingData);   
}   
以下为算子核函数的代码片段。 _aicore__inline void CalcGMOffset(int blocIdx, const TCubeTiling &tiling, int &offsetA, int &offsetB, int &offsetC, int &tailM, int &tailN, bool isTransA, bool isTransB) { uint32_t mSingleBlocks = CeilDiv(tiling.M, tiling.singleCoreM); uint32_t mCoreIdx = blocIdx % mSingleBlocks; uint32_t nCoreIdx = blocIdx / mSingleBlocks; offsetA = mCoreIdx * tiling.Ka * tiling.singleCoreM; if (isTransA) { offsetA = mCoreIdx * tiling.singleCoreM; } offsetB = nCoreIdx * tiling.singleCoreN; if (isTransB) { offsetB = nCoreIdx * tiling.Kb * tiling.singleCoreN; } offsetC = mCoreIdx * tiling.singleCoreN * tiling.singleCoreM + nCoreIdx * tiling.singleCoreN; //此处的tiling.singleCoreN参数错误，应为tiling.N tailM = tiling.M - mCoreIdx * tiling.singleCoreM; tailM = tailM < tiling/singleCoreM ? tailM : tiling/singleCoreM; tailN = tiling.N - nCoreIdx * tiling.singleCoreN; tailN = tailN < tiling/singleCoreN ? tailN : tiling/singleCoreN;   
}   
extern "C" __global __aicore__void matmul_custom(GM_ADDR a, GM_ADDR b, GM_ADDR c, GM_ADDR workspace, GM_ADDR tilingGm)   
{ using A_T = half; using B_T = half; using C_T = float; AscendC::TPipe pipe; TCubeTiling tiling; CopyTiling(&tiling, tilingGm); AscendC::GlobalTensor<A_T> aGlobal; AscendC::GlobalTensor<B_T> bGlobal; AscendC::GlobalTensor<C_T> cGlobal; aGlobal.SetGlobalBuffer(reinterpret_cast<gm_A_T>(a), tiling.M * tiling.Ka); bGlobal.SetGlobalBuffer(reinterpret_cast<gm_B_T>(b), tiling.Ka * tiling.N); cGlobal.SetGlobalBuffer(reinterpret_cast<gm_C_T>(c), tiling.M * tiling.N); int offsetA = 0; int offsetB = 0; int offsetC = 0; bool isTransA = false; bool isTransB = false; int tailM = 0; int tailN = 0; CalcGMOffset(GetBlockIdx(), tiling, offsetA, offsetB, offsetC, tailM, tailN, isTransA, isTransB); auto gma = aGlobal[offsetA]; auto gmb = bGlobal[offsetB]; auto gmc = cGlobal[offsetC]; AscendC::Matmul<AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, A_T>, AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, B_T>, AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, C_T>> mm; REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm, &tiling); mm.SetTensorA(gma, isTransA); mm.SetTensorB(gmb, isTransB); 
```

```txt
mm.SetTail(tailM, tailN);  
mm.IterateAll(gmC);  
mm.End(); 
```

# 执行算子，精度校验失败：

```txt
data index: 000609, expected: 12979.000000000, actual: 0.000000000, rdiff: 1.000000  
data index: 000610, expected: 12931.000000000, actual: 0.000000000, rdiff: 1.000000  
data index: 000611, expected: 13120.000000000, actual: 0.000000000, rdiff: 1.000000  
data index: 000612, expected: 12275.000000000, actual: 0.000000000, rdiff: 1.000000  
error ratio: 0.8750, tolerance: 0.0001  
[ERROR] result error 
```

修改测试脚本和算子Tiling的代码，通过验证单核上的算子执行结果，快速定界。 具体如下： 

修改算子调测代码，只启动单核，CPU调测代码中将ICPU_RUN_KF宏接口中的 numBlocks设置为1（表示一组AIC和AIV）；算子的Tiling实现中，设置单核场 景，AIC核数为1，AIV核数为2，SetDim设置为AIV核数的取值2。如下代码所示。 

以下为调测脚本的代码片段。 

```txt
uint32_t numBlocks = 1;  
ICPU Runs_KF(matmulcustom, numBlocks, a, b, c, workspace, tiling); 
```

以下为算子Tiling计算的代码片段。 

```txt
int usedCoreNum = 2;  
tilingApi.SetDim(usedCoreNum); 
```

修改为单核场景后，执行算子： 

```txt
-- Installing: $HOME/samples/Precision_Guide/samples-master/operator/  
MatmulCustomSample/KernelLaunch/MatmullInvocationNeo-muticore/out/bin/ascendc_kernels_bbit  
efaf4dc1e484bc3778cac65f56244e59 output/golden.bin  
efaf4dc1e484bc3778cac65f56244e59 output/output.bin  
error ratio: 0.0000, tolerance: 0.0001  
test pass 
```

从上述比对结果可看出，单核验证结果正确，此时可以定界导致精度的问题与多 核逻辑相关。 

首先排查多核切分后的输入和输出地址偏移。分析CalcGMOffset函数，定位到矩 阵C的偏移地址offsetC计算错误，正确的偏移应该是mCoreIndx * tiling.N * tiling.singleCoreM $^ +$ nCoreIndx * tiling.singleCoreN。将offsetC修改为正确的偏 移地址后，执行算子，结果比对正确。 

提示，在上述单核场景的修改验证中，AIC核数为1，AIV核数为2；若想进一步验 证，不引入任何多核切分，AIC核数和AIV核数均修改为1，代码修改示例如下： 

在核函数中REGIST_MATMUL_OBJ接口后，利用判断代码，BlockIdx不为0的 AIV核退出。 

以下为算子核函数的代码片段。 

```cpp
extern "C" __global__ __aicore__ void matmul/custom(GM_ADDR a, GM_ADDR b, GM_ADDR c, GM_ADDR workspace, GM_ADDR tilingGm)  
{ using A_T = half; using B_T = half; using C_T = float; AscendC::TPipe pipe; TCubeTiling tiling; CopyTiling(&tiling, tilingGm); AscendC::GlobalTensor<A_T> aGlobal; AscendC::GlobalTensor<B_T> bGlobal; AscendC::GlobalTensor<C_T> cGlobal; aGlobal.SetGlobalBuffer(reinterpret_cast<__gm__A_T>(a), tiling.M * tiling.Ka); bGlobal.SetGlobalBuffer(reinterpret_cast<__gm__B_T>(b), tiling.Ka * tiling.N); 
```

cGlobal.SetGlobalBuffer(reinterpret_cast<__gm__C_T $\succ$ 0(c), tiling.M\*tiling.N);   
int offsetA $= 0$ int offsetB $= 0$ int offsetC $= 0$ bool isTransA $=$ false; bool isTransB $=$ false;   
int tailM $= 0$ int tailN $= 0$ CalcGMOffset(GetBlockIdx(), tiling, offsetA, offsetB, offsetC, tailM, tailN, isTransA, isTransB);   
auto gma = aGlobal[offsetA];   
auto gmb $=$ bGlobal[offsetB];   
auto gmc $=$ cGlobal[offsetC];   
AscendC::Matmul<AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, A_T>, AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, B_T>, AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, C_T>> mm; REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm, &tiling); if (GetBlockIdx() == 1) { return; }   
mm.SetTensorA(gmA, isTransA); mm.SetTensorB(gmB, isTransB); mm.setTail(tailM, tailN); mm.IterateAll(gmC); mm.End(); 

算子调测脚本的ICPU_RUN_KF中numBlocks和算子Tiling中SetDim的 usedCoreNum均设置为1。 

以下为算子调测代码片段。 

```txt
uint32_t numBlocks = 1;  
ICPU Runs_KF(matmul_custom, numBlocks, a, b, c, workspace, tiling); 
```

以下为算子Tiling计算的代码片段。 

```txt
int usedCoreNum = 1;  
tilingApi.SetDim(usedCoreNum); 
```

案例2：尾块设置不正确 

多核场景下，当最后一个核的singleCoreM/singleCoreN/singleCoreK值与前面的 核取值不同时，需要在最后一个核上，即尾核，调用SetTail接口，调整 singleCoreM/singleCoreN/singleCoreK为实际尾核上的对应取值；若尾核未设置 这些参数值，或者设置的参数值大小不正确，也会导致多核精度错误，单核精度 正确。 

```txt
data index: 100254, expected: 13605.000000000, actual: 13137.000000000, rdiff: 0.034399  
data index: 101277, expected: 13268.000000000, actual: 13419.000000000, rdiff: 0.011381  
data index: 102300, expected: 13509.000000000, actual: 13114.000000000, rdiff: 0.029240  
data index: 103323, expected: 13526.000000000, actual: 13400.000000000, rdiff: 0.009315  
error ratio: 0.0010, tolerance: 0.0001  
[ERROR] result error 
```

以下为算子核函数的代码片段。 

```txt
__aicore__ inline void CalcGMOffset(int blockIdx, const TCubeTiling &tiling, int &offsetA, int &offsetB, int &offsetC, int &tailM, int &tailN, bool isTransA, bool isTransB)  
{  
    uint32_t mSingleBlocks = CeilDiv(tiling.M, tiling.singleCoreM);  
    uint32_t mCoreIdx = blockIdx % mSingleBlocks;  
    uint32_t nCoreIdx = blockIdx / mSingleBlocks;  
    offsetA = mCoreIdx * tiling.Ka * tiling.singleCoreM;  
    if (isTransA) {  
        offsetA = mCoreIdx * tiling.singleCoreM;  
    } 
```

```txt
offsetB = nCoreIdx * tiling.singleCoreN; if (isTransB) { offsetB = nCoreIdx * tiling.Kb * tiling.singleCoreN; } offsetC = mCoreIdx * tiling.N * tiling.singleCoreM + nCoreIdx * tiling.singleCoreN; //尾核对应的M/N计算，此处为正确的计算方式 tailM = tiling.M - mCoreIdx * tiling.singleCoreM; tailM = tailM < tiling(singleCoreM ? tailM : tiling.singleCoreM; tailN = tiling.N - nCoreIdx * tiling.singleCoreN; tailN = tailN < tiling/singleCoreN ? tailN : tiling.singleCoreN; } extern "C" __global__aicore__void matmul_custom(GM_ADDR a, GM_ADDR b, GM_ADDR c, GM_ADDR workspace, GM_ADDR tilingGm) { using A_T = half; using B_T = half; using C_T = float; AscendC::TPipe pipe; TCubeTiling tiling; CopyTiling(&tiling, tilingGm); AscendC::GlobalTensor<A_T> aGlobal; AscendC::GlobalTensor<B_T> bGlobal; AscendC::GlobalTensor<C_T> cGlobal; aGlobal.SetGlobalBuffer(reinterpret_cast<gm_A_T>(a), tiling.M * tiling.Ka); bGlobal.SetGlobalBuffer(reinterpret_cast<gm_B_T>(b), tiling.Ka * tiling.N); cGlobal.SetGlobalBuffer(reinterpret_cast<gm_C_T>(c), tiling.M * tiling.N); int offsetA = 0; int offsetB = 0; int offsetC = 0; bool isTransA = false; bool isTransB = false; int tailM = 0; int tailN = 0; CalcGMOffset(GetBlockIdx(), tiling, offsetA, offsetB, offsetC, tailM, tailN, isTransA, isTransB); auto gma = aGlobal[offsetA]; auto gmb = bGlobal[offsetB]; auto gmc = cGlobal[offsetC]; AscendC::Matmul<AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, A_T>, AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, B_T>, AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, C_T>> mm; REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm, &tiling); mm.SetTensorA(gma, isTransA); mm.SetTensorB(gmb, isTransB); //mm.SetTail(tailM, tailN);尾核设置接口，若此处未更新尾块会导致单核精度正确，多核失败 mm.IterateAll(gmc); mm.End(); 
```

# 步骤5 排查Matmul API的使用是否正确

经过上述步骤，可定界出是否为Matmul API使用问题。如果由于Matmul API使用错 误导致了算子的精度问题，需要根据Matmul各接口的使用说明、约束条件等，检查接 口的使用是否正确。 

案例1：未遵循接口约束条件 

在Matmul MDL模板下，调用IterateBatch接口，导致算子执行失败。这是由于不 满足该接口的约束条件，IterateBatch接口仅支持Norm模板。 

此类问题，应仔细阅读Matmul各接口中的约束条件，并排查算子实现使用的相关 接口，是否满足对应接口的约束条件。 

案例2：未遵循模板约束条件 

在使能doMTE2Preload预加载模板时，若K方向非全载，不满足模板约束条件， 则会导致精度比对失败。 

除了满足函数接口约束条件外，也需要满足模板参数相应的约束条件，排查模板 参数的使用。 

# 步骤6 用于算子调测的golden脚本是否正确

算子的golden生成脚本，根据自定义算子的功能逻辑自行实现，用于比对算子执行结 果是否正确。因此，该golden脚本的逻辑需要与算子的实现逻辑保持一致，如果 golden脚本实现错误，会导致算子计算结果的精度比对失败，这种情况是golden数据 不可信。 

所以，在算子精度定界定位的过程中，用户需要自行根据自定义算子的逻辑，检查 golden脚本的正确性，尤其是对于复杂计算逻辑的算子，需重点排查该项。 

----结束 

# 2.10.10.6 算子工程编译时出现文件名过长报错

# 现象描述

工程化算子开发场景，在进行算子工程编译时，提示以下报错信息中的一种： 

file name is too long (cannot be split); not dumped 

ERROR: failed to create temporary archive: /tmp/mkself336430.tar 

CMake Error at /addcustom/cmake/makeself.cmake:12 (message): 

CPack Command error: 1 

Header is 672 lines long 

./packages/vendors/customize/op_proto/inc/ 

my_very_long_and_detailed_c_plus_plus_project_source_code_file_containing_advanced_features_and_i mplementations.h: 

file name is too long (cannot be split); not dumped 

tar: Exiting with failure status due to previous errors 

file name is too long (max 256); not dumped 

ERROR: failed to create temporary archive: /tmp/mkself133003.tar 

CMake Error at /root/r00882787/Customproj/addcustom/cmake/makeself.cmake:12 (message): 

CPack Command error: 1 

Header is 672 lines long 

./packages/vendors/ 

ProjectX_FeatureY_Z_20241118_Monday_Development_BranchA1_Commit56789_AlphaVersion_ABCDE 

FGHIJKLM/op_impl/ai_core/tbe/ 

ProjectX_FeatureY_Z_20241118_Monday_Development_BranchA1_Commit56789_AlphaVersion_ABCDE 

FGHIJKLM_impl/dynamic/add_custom.cpp: 

file name is too long (max 256); not dumped 

# 问题根因

在构建过程中，由于文件名或路径长度超出系统限制，使用tar命令打包算子工程生成 的文件时发生了错误。 

# 定位步骤

出现此类报错，需要根据提示的报错信息（通常包含超长的文件名或者路径），减少 对应的文件名长度或路径长度。 

下面列出了常见错误的解决方案： 

# 文件名过长报错

位于算子工程op_kernel目录下的kernel侧代码和位于op_host目录下的host侧 代码等文件，文件名是根据创建算子工程时传入的算子OpType自动生成的。 如果因为此类文件名过长报错，应减少OpType的长度。 

使用Comment接口设置算子分组名称后，会对应生成同名的供GE调用的原型 定义代码文件。如果因为此类文件导致文件名过长报错，应减少算子分组名 称的长度。 

# 文件路径过长报错

完成工程编译相关配置时，如果在CMakePresets.json文件中配置vendor_name， 编译时会在vendor目录下生成以vendor_name为名称的路径。如果因为此类文件 路径过长报错，应减少配置的vendor_name长度。 

# 2.10.10.7 调用算子时出现无法打开 config.ini 的报错

# 现象描述

自定义算子包安装部署后，在调用已部署的算子时，出现如下json文件获取失败的报 错信息： 

[INFO] Start get path and read binary_info_config.json. [WARNING] Get jsonfile path for */binary_info_config.json failed, errmsg:No such file or directory. [ERROR] Get path and read binary_info_config.json failed, please check if the opp_kernel package is installed! 

通过查询前文的报错信息，上述json文件获取失败的原因是前置流程中无法打开 config.ini，提示信息如下： 

[INFO] Start to get opp kernel base path, default custom opp kernel is in ASCEND_OPP_PATH. [INFO] The real path of config.ini is */opp/vendors/config.ini. [WARNING] Can not open file: */opp/vendors/config.ini. 

# 问题根因

根因在于当前调用算子的用户缺少对算子包部署目录下的config.ini（ */opp/vendors/ config.ini）文件的读权限。config.ini文件权限默认为640，仅允许部署用户和同属组 用户访问，当前执行用户与安装用户非同一属组，缺少读权限，导致算子调用失败。 

比如下述场景即会导致调用算子时出现执行报错：root用户安装部署自定义算子包， HwHiAiUser属组用户调用已部署的自定义算子。 

# 处理步骤

联系自定义算子包安装用户修改config.ini权限为644： chmod 644 config.ini 

# 2.10.10.8 算子包部署时出现权限不足报错

# 现象描述

部署自定义算子包时，出现如下报错信息： 

[WARNING] The directory /usr/local/Ascend/cann/opp does not have sufficient permissions. Please check and modify the folder permissions (e.g., using chmod), or use the --install-path option to specify an installation path and change the environment variable ASCEND_CUSTOM_OPP_PATH to the specified path. 

[ERROR] create /usr/local/Ascend/cann/opp/vendors/customize/framework failed 

# 问题根因

当前操作用户缺少对部署路径下vendors目录的写权限。 

自定义算子包默认安装路径${INSTALL_DIR}/opp/vendors的目录权限与CANN软件包 安装用户和安装配置有关：root用户安装CANN，${INSTALL_DIR}/opp/vendors权限 为755；非root用户携带--install for all参数安装CANN，该目录权限为755，非root用 户不带--install for all参数安装CANN时，该目录权限为750。 

例如，root用户安装CANN软件包后，HwHiAiUser属组用户在对应目录部署自定义算 子包，因为其他用户没有写权限，会出现上述报错信息，提示权限不足导致自定义算 子包部署失败。 

# 处理步骤

方法一：使用--install-path参数并配置环境变量ASCEND_CUSTOM_OPP_PATH来 指定安装目录（参考指定目录安装）。运行用户需要对指定的安装路径有可读写 权限。 

./custom_opp_<target os>_<target architecture>.run --install-path=<path> source <path>/vendors/<vendor name>/bin/set env.bash 

方法二：联系CANN软件包安装用户修改默认安装路径下的vendors目录权限，比 如修改为777： 

chmod 777 /usr/local/Ascend/cann/opp/vendors/ 

# 3 算子实践参考

3.1 本文档组织结构 

3.2 异构计算 

3.3 SIMD算子实现 

3.4 SIMT算子实现 

3.5 SIMD与SIMT混合算子实现 

3.6 功能调试 

3.7 性能分析 

3.8 SIMD算子性能优化 

3.9 SIMD与SIMT混合算子性能优化 

3.10 优秀实践