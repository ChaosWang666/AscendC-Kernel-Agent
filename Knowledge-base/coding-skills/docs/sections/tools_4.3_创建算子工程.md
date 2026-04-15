<!-- Source: 算子开发工具.md lines 3825-4003 | Section: 4.3 创建算子工程 -->

# 4.3 创建算子工程

步骤1 编写算子的原型定义json文件，用于生成算子开发工程。json文件的配置参数详细说明 请参考表4-5。 

例如，AddCustom算子的json文件命名为add_custom.json，文件内容如下： 

```txt
[ "op": "AddCustom", "input_desc": [ { 
```

```csv
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
"fp16",   
"float",   
"int32"   
]   
}   
],   
"output_desc": [   
{name:"z",   
"param_type": "required",   
"format": [   
"ND",   
"ND",   
"ND"   
],   
"type": [   
"fp16",   
"float",   
'int32"   
} 
```

例如，ReduceMaxCustom算子（包含属性）的json文件命名为 reduce_max_custom.json，文件内容如下： 

```txt
{
    "op": "ReduceMaxCustom",
    "input_desc": [
        "name": "x",
        "param_type": "required",
        "format": ["ND],
        "type": ["float16"]
    ],
    "output_desc": [
        "name": "y",
        "param_type": "required",
        "format": ["ND],
        "type": ["float16"]
    ],
    "name": "idx",
} 
```

```jsonl
"param_type": "required",  
"format": ["ND"],  
"type": ["int32"]  
}  
],  
"attr": [  
{  
    "name": "reduceDim",  
    "param_type": "required",  
    "type": "int"  
},  
{  
    "name": "isKeepDim",  
    "param_type": "optional",  
    "type": "int",  
    "default_value": 1  
}  
} 
```


表4-5 json 文件配置参数说明


<table><tr><td colspan="2">配置字段</td><td>类型</td><td>含义</td><td>是否必选</td></tr><tr><td>op</td><td>-</td><td>字符串</td><td>算子的Operator Type。</td><td>是</td></tr><tr><td rowspan="4">input_desc</td><td>-</td><td>列表</td><td>输入参数描述。</td><td rowspan="4">否</td></tr><tr><td>name</td><td>字符串</td><td>算子输入参数的名称。</td></tr><tr><td>param_type</td><td>字符串</td><td>参数类型:
· required
· optional
· dynamic
未配置默认为required。</td></tr><tr><td>format</td><td>列表</td><td>针对类型为Tensor的参数,配置为Tensor支持的数据排布格式。
包含如下取值:
ND、NHWC、NCHW、HWCN、NC1HWC0、FRACTAL_Z等。
说明
format与type需一一对应。若仅填充其中一项的唯一值,msOpGen工具将会以未填充项的唯一输入值为准自动补充至已填充项的长度。例如用户配置为format: ["ND"] /type: ["fp16","float","int32"], msOpGen工具将会以format的唯一输入值("ND")为准自动补充至type参数的长度,自动补充后的配置为format: ["ND","ND","ND"]
["fp16","float","int32"].</td></tr><tr><td></td><td>type</td><td>列表</td><td>算子参数的类型。Ascend C或TBE算子取值范围: float、half、float16 (fp16)、 float32 (fp32)、int8、int16、 int32、int64、uint8、uint16、 uint32、uint64、qint8、qint16、 qint32、quint8、quint16、 quint32、bool、double、string、 resource、complex64、 complex128、bf16、numbertype、 realnumbertype、quantizedtype、 all、BasicType、 IndexNumberOfType、bfloat16。MindSpore数据类型取值范围: None_None、BOOL_None、 BOOL 默认、BOOL_5HD、 BOOL_FracZ、BOOL_FracNZ、 BOOL_C1HWC0C0、 BOOL_NCHW、BOOL_NHWC、 BOOL_NDHWC、I8_None、 I8，默认、I8_5HD、I8_FracZ、 I8_FracNZ、I8_C1HWC0C0、 I8_NCHW、I8_NHWC、I8_HWCN、 I8_NDHWC、U8_None、 U8，默认、U8_5HD、U8_FracZ、 U8_FracNZ、U8_C1HWC0C0、 U8_NCHW、U8_NHWC、 U8_HWCN、U8_NDHWC、 I16_None、I16，默认、 I16_5HD、I16_FracZ、 I16_FracNZ、I16_C1HWC0C0、 I16_NCHW、I16_NHWC、 I16_HWCN、I16_NDHWC、 U16_None、U16，默认、 U16_5HD、U16_FracZ、 U16_FracNZ、U16_C1HWC0C0、 U16_NCHW、U16_NHWC、 U16_HWCN、U16_NDHWC、 I32_None、I32，默认、 I32_5HD、I32_FracZ、 I32_FracNZ、I32_C1HWC0C0、 I32_NCHW、I32_NHWC、 I32_HWCN、I32_NDHWC、 U32_None、U32，默认、 U32_5HD、U32_FracZ、 U32_FracNZ、U32_C1HWC0C0、 U32_NCHW、U32_NHWC、 U32_HWCN、U32_NDHWC、 I64_None、I64，默认、</td><td></td></tr><tr><td></td><td></td><td></td><td>I64_5HD、I64_FracZ、I64_FracNZ、I64_C1HWNCoC0、I64_NCHW、I64_NHWC、I64_HWCN、I64_NDHWC、U64_None、U64 默认、U64_5HD、U64_FracZ、U64_FracNZ、U64_C1HWNCoC0、U64_NCHW、U64_NHWC、U64_HWCN、U64_NDHWC、F16_None、F16 默认、F16_5HD、F16_FracZ、F16_FracNZ、F16_C1HWNCoC0、F16_NCHW、F16_NHWC、F16_HWCN、F16_NDHWC、F16_FracZNLSTM、F32_None、F32 默认、F32_5HD、F32_FracZ、F32_FracNZ、F32_C1HWNCoC0、F32_NCHW、F32_NHWC、F32_HWCN、F32_NDHWC、F32_FracZNLSTM、F64_None、F64 默认、F64_5HD、F64_FracZ、F64_FracNZ、F64_C1HWNCoC0、F64_NCHW、F64_NHWC、F64_HWCN、F64_NDHWC。说明·不同计算操作支持的数据类型不同,详细请参见《Ascend C算子开发接口》。·format与type需一一对应。若仅填充其中一项的唯一值,msOpGen工具将会以未填充项的唯一输入值为准自动补充至已填充项的长度。例如用户配置为format: ["ND"] /type: ["fp16","float","int32"], msOpGen工具将会以format的唯一输入值 ("ND")为准自动补充至type参数的长度,自动补充后的配置为format: ["ND","ND","ND"].type: ["fp16","float","int32"].</td><td rowspan="4">是</td></tr><tr><td rowspan="3">output_desc</td><td>-</td><td>列表</td><td>输出参数描述。</td></tr><tr><td>name</td><td>字符串</td><td>算子输出参数的名称。</td></tr><tr><td>param_type</td><td>字符串</td><td>参数类型: ·required ·optional ·dynamic 未配置默认为required。</td></tr><tr><td></td><td>format</td><td>列表</td><td>针对类型为Tensor的参数，配置为Tensor支持的数据排布格式。包含如下取值：ND、NHWC、NCHW、HWCN、NC1HWC0、FRACTAL_Z等。说明format与type需一一对应。若仅填充其中一项的唯一值，msOpGen工具将会以未填充项的唯一输入值为准自动补充至已填充项的长度。例如用户配置为format:"ND"/type:"fp16","float","int32"，msOpGen工具将会以format的唯一输入值（"ND"）为准自动补充至type参数的长度，自动补充后的配置为format:"ND","ND","ND"/type:"fp16","float","int32"。</td><td></td></tr><tr><td></td><td>type</td><td>列表</td><td>算子参数的类型。Ascend C或TBE算子取值范围: float、half、float16 (fp16)、 float32 (fp32)、int8、int16、 int32、int64、uint8、uint16、 uint32、uint64、qint8、qint16、 qint32、quint8、quint16、 quint32、bool、double、string、 resource、complex64、 complex128、bf16、numbertype、 realnumbertype、quantizedtype、 all、BasicType、 IndexNumberOfType、bfloat16。MindSpore数据类型取值范围: None_None、BOOL_None、 BOOL 默认、BOOL_5HD、 BOOL_FracZ、BOOL_FracNZ、 BOOL_C1HWC0C0、 BOOL_NCHW、BOOL_NHWC、 BOOL_NDHWC、I8_None、 I8，默认、I8_5HD、I8_FracZ、 I8_FracNZ、I8_C1HWC0C0、 I8_NCHW、I8_NHWC、I8_HWCN、 I8_NDHWC、U8_None、 U8，默认、U8_5HD、U8_FracZ、 U8_FracNZ、U8_C1HWC0C0、 U8_NCHW、U8_NHWC、 U8_HWCN、U8_NDHWC、 I16_None、I16，默认、 I16_5HD、I16_FracZ、 I16_FracNZ、I16_C1HWC0C0、 I16_NCHW、I16_NHWC、 I16_HWCN、I16_NDHWC、 U16_None、U16，默认、 U16_5HD、U16_FracZ、 U16_FracNZ、U16_C1HWC0C0、 U16_NCHW、U16_NHWC、 U16_HWCN、U16_NDHWC、 I32_None、I32，默认、 I32_5HD、I32_FracZ、 I32_FracNZ、I32_C1HWC0C0、 I32_NCHW、I32_NHWC、 I32_HWCN、I32_NDHWC、 U32_None、U32，默认、 U32_5HD、U32_FracZ、 U32_FracNZ、U32_C1HWC0C0、 U32_NCHW、U32_NHWC、 U32_HWCN、U32_NDHWC、 I64_None、I64，默认、</td><td></td></tr><tr><td></td><td></td><td></td><td>I64_5HD、I64_FracZ、I64_FracNZ、I64_C1HWNCoC0、I64_NCHW、I64_NHWC、I64_HWCN、I64_NDHWC、U64_None、U64 默认、U64_5HD、U64_FracZ、U64_FracNZ、U64_C1HWNCoC0、U64_NCHW、U64_NHWC、U64_HWCN、U64_NDHWC、F16_None、F16 默认、F16_5HD、F16_FracZ、F16_FracNZ、F16_C1HWNCoC0、F16_NCHW、F16_NHWC、F16_HWCN、F16_NDHWC、F16_FracZNLSTM、F32_None、F32 默认、F32_5HD、F32_FracZ、F32_FracNZ、F32_C1HWNCoC0、F32_NCHW、F32_NHWC、F32_HWCN、F32_NDHWC、F32_FracZNLSTM、F64_None、F64 默认、F64_5HD、F64_FracZ、F64_FracNZ、F64_C1HWNCoC0、F64_NCHW、F64_NHWC、F64_HWCN、F64_NDHWC。说明·不同计算操作支持的数据类型不同,详细请参见《Ascend C算子开发接口》。·format与type需一一对应。若仅填充其中一项的唯一值,msOpGen工具将会以未填充项的唯一输入值为准自动补充至已填充项的长度。例如用户配置为format: ["ND"] /type: ["fp16","float","int32"], msOpGen工具将会以format的唯一输入值 ("ND")为准自动补充至type参数的长度,自动补充后的配置为format: ["ND","ND","ND"]/type: ["fp16","float","int32"]。</td><td></td></tr><tr><td rowspan="3">attr</td><td>-</td><td>列表</td><td>属性描述。</td><td rowspan="3">否</td></tr><tr><td>name</td><td>字符串</td><td>算子属性参数的名称。</td></tr><tr><td>param_type</td><td>字符串</td><td>参数类型: ·required ·optional 未配置默认为required。</td></tr><tr><td rowspan="2"></td><td>type</td><td>字符串</td><td>算子参数的类型。
包含如下取值：
int、bool、float、string、list_int、list_float、list(bool、list_list_int，其他请自行参考《Ascend C算子开发接口》中的“Host API &gt; 原型注册与管理 &gt; OpAttrDef &gt; OpAttrDef”章节进行修改。</td><td rowspan="2"></td></tr><tr><td>default_value</td><td>-</td><td>默认值。</td></tr></table>

# 说明

● json文件可以配置多个算子，json文件为列表，列表中每一个元素为一个算子。 

● 若input_desc或output_desc中存在相同name参数，则后一个会覆盖前一参数。 

● input_desc，output_desc中的type需按顺序一一对应匹配，format也需按顺序一一对应匹 配。 

例如，第一个输入x的type配置为[“int8”,“int32”]，第二个输入y的type配置为 [“fp16”,“fp32”]，输出z的type配置为[“int32”,“int64”]，最终这个算子支持输入 (“int8”,“fp16”)生成int32，或者(“int32”,“fp32”)生成int64，即输入和输出的type 是垂直对应的，类型不能交叉。 

input_desc，output_desc中的type与format需一一对应匹配，数量保持一致。type的数据类 型为以下取值（"numbertype"、"realnumbertype"、"quantizedtype"、"BasicType"、 "IndexNumberType"、"all"）时，需识别实际的type数量是否与format数量保持一致，若数 量不一致，创建工程会收到报错提示，同时format按照type的个数进行补齐，继续生成算子 工程。若type的取值为基本数据类型（如：“int32”），且与format无法一一对应时，创建 工程会收到报错提示，并停止运行。 

● json文件可对“attr”算子属性进行配置，具体请参考编写原型定义文件。 

● 算子的Operator Type需要采用大驼峰的命名方式，即采用大写字符区分不同的语义，具体 请参见算子工程编译的须知内容。 

# 步骤2 生成算子的开发工程。

以生成AddCustom的算子工程为例，执行如下命令，参数说明请参见表4-2。 

```txt
msopgen gen -i \{*.json\} -f \{framework type\} -c \{Compute Resource\} -lan cpp -out \{Output Path\} 
```

步骤3 命令执行完后，会在指定目录下生成算子工程目录，工程中包含算子实现的模板文 件，编译脚本等。 

算子工程目录生成在-out所指定的目录下：./output data， 目录结构如下所示： 

```txt
output_data
- build.sh //编译入口脚本
- cmake
- config.cmake
- util //算子工程编译所需脚本及公共编译文件存放目录
- CMakeLists.txt //算子工程的CMakeLists.txt
- CMakePresents.json //编译配置项
- framework //算子插件实现文件目录，单算子模型文件的生成不依赖算子适配插件，无需关注
- op_host //Host侧实现文件
- addcustom_tiling.h //算子tiling定义文件
- addcustom.cpp //算子原型注册、shape推导、信息库、tiling实现等内容文件
- CMakeLists.txt 
```

```txt
op_kernel // Kernel侧实现文件  
CMakeLists.txt  
addcustom.cpp // 算子代码实现文件  
scripts // 自定义算子工程打包相关脚本所在目录 
```

步骤4 可选: 在算子工程中追加算子。若需要在已存在的算子工程目录下追加其他自定义算 子，命令行需配置“-m 1”参数。 

```batch
msopgen gen -i json_path/\*\*.json -f tf -c ai_core-\{Soc Version\} -out ./output_data -m 1 
```

-i：指定算子原型定义文件add_custom.json所在路径。 

-c：参数中{Soc Version}为昇腾AI处理器的型号。 

在算子工程目录下追加**.json中的算子。MindSpore算子工程不能够添加非 MindSpore框架的算子。 

步骤5 完成算子工程创建，进行4.4 算子开发。 

----结束