<!-- Source: 算子开发工具.md lines 4530-4674 | Section: 5.3 生成测试用例定义文件 -->

# 5.3 生成测试用例定义文件

指导用户使用msOpST工具生成算子测试用例定义文件（*.json），作为算子ST测试用 例的输入。 

步骤1 获取并编辑待测试Host侧算子的实现文件（.cpp文件）。 

msOpST工具根据待测Host侧算子的实现文件生成算子ST测试用例定义文件，在算子 工程文件中Host侧算子的实现文件路径如下所示。 

可以单击Link获取文档中对应的Host侧算子实现文件add_custom.cpp进行参考。 

# 说明

![](images/ba931b489ac391388d67e356fe9fcef71a90281491393ddd2d03625b785a6877.jpg)


```txt
- addcustom_tiling.h //算子tiling定义文件
- addcustom.cpp //算子原型注册、shape推导、信息库、tiling实现等内容文件
- CMakeLists.txt
- op_kernel //Kernel侧实现文件
- CMakeLists.txt
- addcustom.cpp //算子代码实现文件 
```

步骤2 执行如下命令生成算子测试用例定义文件，详细参数说明请参见表5-1。 

```txt
msopst create -i {operator.cpp file} -out {output path} -m {pb file} -q 
```

# 说明

示例如下： 

```batch
以AddCustom算子为例，执行如下命令：  
msopst create -i Op_implementation/add(custom.cpp -out ./output 
```

请将Op_implementation更换为Host侧算子的实现文件所在路径。 

命令执行成功后，会在当前路径的output目录下生成算子测试用例定义文件： AddCustom_case_timestamp.json。 

步骤3 创建算子ST测试用例定义文件“AddCustom_case.json”。该文件的模板如下，您可 以基于如下模板进行修改，“*.json”文件支持的全量字段说明参见表5-5。不同场景 下的测试用例定义文件的样例可参见5.6.1 测试用例定义文件。 

```json
{
    "case_name": "Test_OptType_001",
    "op": "OptType",
    "input_desc": [
        "format": [], "type": [], "shape": [], "data_distribution": [
            "uniform"
        ],
            "value_range": [
                0.1,
                1.0
            ]
        ]
    ],
    "output_desc": [
        {"format": [], "type": [], "shape": []
    ]
} 
```


表 5-5 算子测试用例定义 json 文件


<table><tr><td colspan="2">参数</td><td>说明</td></tr><tr><td>case_name</td><td>-</td><td>必选。
String类型。
测试用例的名称。</td></tr><tr><td>op</td><td>-</td><td>必选。
String类型。算子的类型。不允许为空。</td></tr><tr><td>error_threshold</td><td>-</td><td>可选。配置自定义精度标准,取值为含两个元素的列表:"[threshold1, threshold2]"·threshold1:算子输出结果与标杆数据误差阈值,若误差大于该值则记为误差数据。·threshold2:误差数据在全部数据占比阈值。若误差数据在全部数据占比小于该值,则精度达标,否则精度不达标。若未设置此参数,默认值为:"[0.01,0.05]".取值范围为:"[0.0,1.0]".说明·配置的列表需加引号以避免一些问题。例如配置为:-err_thr"[0.01,0.05]".·若测试用例json文件和执行msOpST命令时均配置该参数,以执行msOpST命令时配置的精度标准进行比对。·若均未配置,则以执行msOpST命令时默认精度标准[0.01,0.05]进行比对。</td></tr><tr><td>st_mode</td><td>-</td><td>可选。String类型。ST测试模式,其值为:"ms.python_train",表示Mindspore的算子工程(仅Atlas训练系列产品支持);"pt.python_train",表示PyTorch框架下的算子工程。</td></tr><tr><td>run_torch_api</td><td>-</td><td>可选。配置torch_api调用算子的接口,其值为:"torch(square","square"为接口名称,请根据实际情况配置。</td></tr><tr><td>expect</td><td>-</td><td>可选。用户期望的测试结果状态。属性支持以下两种类型,默认值为“success”。·success:表示期望测试用例运行成功。若模型转换失败,流程将提前终止,用户可查看ATC工具相关日志定位问题。·failed:表示期望测试用例运行失败。若用户需要运行异常用例,可修改expect字段为failed。若模型转换失败,流程将继续执行。在统计结果中,依据STCaseReport中的status和expect是否一致统计,一致则统计至“success count”,不一致则统计至“failed count”。</td></tr><tr><td>fuzz Impl</td><td>-</td><td>可选，String类型。若用户需要生成大量测试用例，可利用fuzz测试参数生成脚本辅助生成。此种场景下，用户需要手工添加此字段，配置fuzz测试参数生成脚本的绝对路径或者相对路径：函数名。说明不建议用户调用其它用户目录下的fuzz测试参数生成脚本，以避免提权风险。</td></tr><tr><td>fuzz(case_num</td><td>-</td><td>可选。int类型。在添加了“fuzz Impl”参数的情况下，需要手工添加此字段，配置利用fuzz测试参数生成脚本生成测试用例数量，范围为1~2000。</td></tr><tr><td>input_desc</td><td>-</td><td>必选。算子输入描述。须知所有input_desc中参数取值的个数都要一致，否则测试用例生成会失败。例如：input1的format支持的类型个数2，则input2的format支持的类型个数也需要为2。同理，所有inputx中的type、shape、data_distribution和value_range的取值个数也需要保持一致。</td></tr><tr><td>-</td><td>name</td><td>可选。算子为动态多输入场景时，“name”为必选配置，请配置为算子信息库中“inputx.name”参数的名称+编号，编号从“0”开始，根据输入的个数按照0，1，2……，依次递增。例如，算子信息文件中指定的输入个数为4个，则input_desc中需要配置4个输入描述，name分别为“xxx0”、“xxx1”、“xxx2”、“xxx3”，其中xxx为输入参数的名称。动态多输入场景的配置示例可参见若算子的输入个数不确定（动态多输入场景）。</td></tr><tr><td>-</td><td>format</td><td>必选。String或者String的一维数组。输入Tensor数据的排布格式，不允许为空。常见的数据排布格式如下：·NCHW·NHWC·ND：表示支持任意格式。·NC1HWC0：5维数据格式。其中，C0与微架构强相关，该值等于cube单元的size，例如16；C1是将C维度按照C0切分：C1=C/C0，若结果不整除，最后一份数据需要padding到C0。·FRACTAL_Z：卷积的权重的格式。·FRACTAL_NZ：分形格式，在cube单元计算时，输出矩阵的数据格式为NW1H1H0W0。整个矩阵被分为（H1*W1）个分形，按照column major排布，形状如N字形；每个分形内部有（H0*W0）个元素，按照row major排布，形状如z字形。考虑到数据排布格式，将NW1H1H0W0数据格式称为Nz格式。其中，H0,W0表示一个分形的大小，示意图如下所示：Fractal Matrix SizeMatrix C·RESERVED：预留，当format配置为该值，则type必须配置为“UNDEFINED”，代表算子的此输入可选。·fuzz：使用fuzz测试参数生成脚本自动批量生成值。</td></tr><tr><td>-</td><td>ori_format</td><td>可选。String或者String的一维数组，支持以下两种取值：·配置为输入数据的原始format。当算子实现的format与原始format不同时，需要配置此字段；若不配置此字段，默认算子实现的format与原始format相同。·配置为“fuzz”，表示使用fuzz测试参数生成脚本自动批量生成值。</td></tr><tr><td>-</td><td>type</td><td>必选。String或者String的一维数组。输入数据支持的数据类型。·bool·int8·uint8·int16·uint16·int32·int64·uint32·uint64·float16·float32·float·bfloat16（仅Atlas A3 训练系列产品/Atlas A3 推理系列产品和Atlas A2 训练系列产品/Atlas 800I A2 推理产品支持该数据类型）。·UNDEFINED：表示算子的输入类型为可选。·fuzz：使用fuzz测试参数生成脚本自动批量生成值。输入数据类型为复数场景的配置示例可参见若算子的输入输出类型为复数。</td></tr><tr><td>-</td><td>shape</td><td>必选。int类型。一维或者二维数组。输入Tensor支持的形状。- 支持静态shape输入的场景: shape维度以及取值都为固定值,该场景下不需要配置shape_range参数。- 支持动态shape输入的场景: shape中包含-1,例如:(200,-1)表示第二个轴长度未知。该场景下需要与shape_range参数配合使用,用于给出“-1”维度的取值范围。String类型,“fuzz”。支持fuzz,使用fuzz测试参数生成脚本自动批量生成值。空如果format和type为UNDEFINED时shape允许为空。需要注意,配置的shape需要与format相匹配。</td></tr><tr><td>-</td><td>ori_shape</td><td>可选。int类型。一维或者二维数组。输入数据的原始shape。当算子实现的shape与原始shape不同时,需要配置此字段。String类型,“fuzz”。支持fuzz,使用fuzz测试参数生成脚本自动批量生成值。若不配置此字段,默认算子实现的shape与原始shape一致。</td></tr><tr><td>-</td><td>typical_shape</td><td>可选。int类型。一维或者二维数组。实际用于测试的shape。若配置的“shape”字段中含有-1时,用户需要在算子测试用例定义文件中新增“typical_shape”字段,给定出固定shape值,用于实际测试。String类型,“fuzz”。支持fuzz,使用fuzz测试参数生成脚本自动批量生成值。</td></tr><tr><td>-</td><td>shape_range</td><td>可选。
• int类型。一维或者二维数组。
当算子支持动态shape时，此字段表示支持的shape范围。
默认值为：[[1,-1]]。表示shape可以取1到无穷。
例如：shape配置为(200,-1)，shape_range配置为[[1,-1]]时，则代表shape第二个维度的取值为1到无穷。
• String类型,“fuzz”。
支持fuzz,使用fuzz测试参数生成脚本自动批量生成值。</td></tr><tr><td>-</td><td>is_const</td><td>可选。
bool类型。
• true:若用户需要配置常量输入的用例，则配置该字段，其值为true。
• false:若该字段值为false，则需要配置张量输入用例。
输入为常量的配置示例可参见若算子的某个输入为常量。</td></tr><tr><td>-</td><td>data_distribute</td><td>必选。
String或者String的一维数组。
使用哪种数据分布方式生成测试数据，支持的分布方式有：
• uniform:返回均匀分布随机值。
• normal:返回正态分布（高斯分布）随机值。
• beta:返回Beta分布随机值。
• laplace:返回拉普拉斯分布随机值。
• triangular:返回三角形分布随机值。
• relu:返回均匀分布+Relu激活后的随机值。
• sigmoid:返回均匀分布+sigmoid激活后的随机值。
• softmax:返回均匀分布+softmax激活后的随机值。
• tanh:返回均匀分布+tanh激活后的随机值。
• fuzz:使用fuzz测试参数生成脚本自动批量生成值。</td></tr><tr><td>-</td><td>value_range</td><td>必选。int类型或者float类型。一维或者二维数组。取值范围,不能为空。为[min_value,max_value]且min_value&lt;=max_value。String类型,“fuzz”。支持fuzz,使用fuzz测试参数生成脚本自动批量生成值。</td></tr><tr><td>-</td><td>value</td><td>可选。String或者Tensor数组。若用户需要指定输入数据时,可通过增加“value”字段进行配置。有如下两种配置方式:直接输入Tensor数据,如Tensor的值为[1,2,3,4]。“value”:[1,2,3,4]输入二进制数据文件的路径,如数据文件为test.bin时。“value”:“../test.bin”二进制数据bin文件需用户自己准备。可以输入绝对路径,也可以输入测试用例定义文件的相对路径。配置为“fuzz”,使用fuzz测试参数生成脚本自动批量生成值。说明若用户添加了“value”字段,“data_distribution”和“value_range”字段将会被忽略。同时需要保证“format”,“type”,“shape”字段的值与“value”数据对应,且每个用例只能测试一种数据类型。配置示例可参见若指定固定输入。</td></tr><tr><td>output_desc</td><td>-</td><td>必选。算子输出描述。须知output_desc中参数取值的个数都要与input_desc一致,否则测试用例生成会失败。例如:inputx的format支持的类型个数2,则output的format支持的类型个数也需要为2。</td></tr><tr><td>-</td><td>name</td><td>可选。String类型。输出参数名称。算子为动态多输出场景时,“name”为必选配置,请配置为算子信息库中“outputx.name”参数的名称+编号,编号从“0”开始,根据输出的个数按照0,1,2......,依次递增。例如,算子信息文件中指定的输出个数为4个,则output_desc中需要配置4个输出描述,name分别为“xxx0”、“xxx1”、“xxx2”、“xxx3”,其中xxx为输出参数的名称。</td></tr><tr><td>-</td><td>format</td><td>必选。String或者String的一维数组。输出Tensor数据的排布格式，不允许为空。支持如下数据排布格式：·NCHW。·NHWC。·ND：表示支持任意格式。·NC1HWC0：5维数据格式。其中，C0与微架构强相关，该值等于cube单元的size，例如16；C1是将C维度按照C0切分：C1=C/C0，若结果不整除，最后一份数据需要padding到C0。·FRACTAL_Z：卷积的权重的格式。·FRACTAL_NZ：分形格式，在cube单元计算时，输出矩阵的数据格式为NW1H1H0W0。整个矩阵被分为（H1*W1）个分形，按照column major排布，形状如N字形；每个分形内部有（H0*W0）个元素，按照row major排布，形状如z字形。考虑到数据排布格式，将NW1H1H0W0数据格式称为Nz格式。其中，H0,W0表示一个分形的大小，示意图如下所示：Fractal Matrix SizeMatrix C·fuzz：使用fuzz测试参数生成脚本自动批量生成值。</td></tr><tr><td>-</td><td>ori_format</td><td>可选。String或者String的一维数组。·当算子实现的format与原始format不同时,需要配置此字段,配置为数据的原始format。·配置为“fuzz”,表示使用fuzz测试参数生成脚本自动批量生成值。若不配置此字段,默认算子实现的format与原始format相同。</td></tr><tr><td>-</td><td>type</td><td>必选。String或者String的一维数组或“fuzz”。输出数据支持的数据类型。·bool·int8·uint8·int16·uint16·int32·int64·uint32·uint64·float16·float32·float·bfloat16(仅Atlas A3 训练系列产品/Atlas A3 推理系列产品和Atlas A2 训练系列产品/Atlas 800I A2 推理产品支持该数据类型)。·fuzz:使用fuzz测试参数生成脚本自动批量生成值。</td></tr><tr><td>-</td><td>shape</td><td>必选。·int类型。一维或者二维数组。输入Tensor支持的形状。·String类型,“fuzz”。支持fuzz,使用fuzz测试参数生成脚本自动批量生成值。</td></tr><tr><td>-</td><td>ori_shape</td><td>可选。
• int类型。一维或者二维数组。
输入数据的原始shape。当算子实现的shape与原始 shape不同时，需要配置此字段。
• String类型,“fuzz”。
支持fuzz,使用fuzz测试参数生成脚本自动批量生成值。
若不配置此字段，默认算子实现的shape与原始shape一致。</td></tr><tr><td>attr</td><td>-</td><td>可选。</td></tr><tr><td>-</td><td>name</td><td>若配置attr,则为必选。
String类型。
属性的名称,不为空。</td></tr><tr><td>-</td><td>type</td><td>若配置attr,则为必选。
String类型。
属性支持的类型。
• bool
• int
• float
• string
• list_Bool
• list_int
• list_float
• list_string
• list_list_int
• data_type:如果attr中的value值为数据类型时， type值必须为data_type。</td></tr><tr><td>-</td><td>value</td><td>若配置attr,则为必选。属性值,根据type的不同,属性值不同。如果“type”配置为“bool”,“value”取值为true或者false。如果“type”配置为“int”,“value”取值为整形数据。如果“type”配置为“float”,“value”取值为浮点型数据。如果“type”配置为“string”,“value”取值为字符串,例如“NCHW”。如果“type”配置为“list bool”,“value”取值示例: [false, true]。如果“type”配置为“list_int”,“value”取值示例: [1, 224, 224, 3]。如果“type”配置为“list_float”,“value”取值示例: [1.0, 0.0]。如果“type”配置为“list_string”,“value”取值示例: ["str1", "str2"]。如果“type”配置为“list_list_int”,“value”取值示例: [[1, 3, 5, 7], [2, 4, 6, 8]]。如果“type”配置为“data_type”,“value”支持如下取值:int8、int32、int16、int64、uint8、uint16、uint32、uint64、float、float16、float32、bool、double、complex64、complex128、bfloat16。‘‘value”值配置为“fuzz”时,表示使用fuzz测试参数生成脚本自动批量生成值。</td></tr><tr><td>calc Expect_func_file</td><td>-</td><td>可选。String类型。算子期望数据生成函数对应的文件路径及算子函数名称,如: "/home/test/test_*.py:function"其中,/home/test/test_*.py为算子期望数据生成函数的实现文件, function为对应的函数名称。须知不建议用户调用其它用户目录下的期望数据生成脚本,以避免提权风险。</td></tr></table>

步骤4 （可选）如果您需要得到实际算子输出与期望输出的比对结果，需要参考此步骤自定 义期望数据生成函数。 

1. 自定义实现add算子期望数据生成函数。 

在Python文件中实现算子期望数据生成函数，文件目录和文件名称可自定义，如 “/home/test/test_add_st.py” 1 。 

例如Add算子的期望数据生成函数实现如下： 

```python
def calc Expect_func(x1, x2, y):
    res = x1["value"] + x2["value"]
    return [res, ] 
```

![](images/d265e79705072f43c79a4f4373d26c10389ee3572ce0c944968633a6f6b7a618.jpg)


用户需根据开发的自定义算子完成算子期望数据生成函数。测试用例定义文件中 的全部Input、Output、Attr的name作为算子期望数据生成函数的输入参数，若 Input是可选输入，请将该输入指定默认值传参。 

例如，某算子输入中的x3为可选输入时，定义该算子的期望数据生成函数如下。 def calc_expect_func(x1, x2, x3=None, y=None) 

2. 在ST测试用例定义文件“OpType_xx.json”中增加比对函数。配置算子测试用例 定义文件。 

```javascript
在步骤2中的算子测试用例定义文件AddCustom_case_timestamp.json增加"calc expect func file"参数，参数值为"/home/test/test_add_st.py:calc expect func"。  
[{"case_name":"Test_AddCustom_001","op":"AddCustom","calc expect func_file":"/home/test/test_add_st.py:calc expect func",//配置生成算子期望输出数据的实现文件"input_desc":[...]…} 
```

----结束