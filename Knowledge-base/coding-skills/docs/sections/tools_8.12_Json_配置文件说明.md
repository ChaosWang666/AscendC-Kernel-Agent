<!-- Source: 算子开发工具.md lines 9757-9837 | Section: 8.12 Json 配置文件说明 -->

# 8.12 Json 配置文件说明

编写算子的定义json文件，配置参数的具体说明请参考表8-30和表8-31。 

例如，json配置文件的命名为add_test.json，开发者可基于该模板修改测试数据及其他 配置参数。 

```txt
{
    "kernel_name": "addcustom",
    "kernel_path": "/add(custom.o",
    "blockdim": 8,
    "mode": "ca",
    "device_id": 0,
    "magic": "RT_DEV_BINARY_MAGEL_AIVEC",
    "test_cases": [ 
        "case_name": "Test_AddCustom_001",
        "param_desc": [ 
            "param_type": "input",
            "type": "float16",
            "shape": [ 
                8, 2048
            ], 
            "data_path": "./input_x.bin",
            "name": "x"
        ],
        {"param_type": "input",
            "type": "float16",
            "shape": [ 
                8, 2048
            ], 
            "data_path": "./input_y.bin",
            "name": "y"
        ],
        {"param_type": "output",
            "type": "float16",
            "shape": [ 
                8, 2048
            ], 
            "name": "z"
        ],
        {"param_type": "workspace",
            "user Workspace_size": 4096}
    ,
    {"param_type": "tiling", 
```

```txt
"tiling_data_size": 8, "tiling_data_path": ".tiling.bin" } ] } ] 
```


表 8-30 json 文件配置参数说明


<table><tr><td>参数名称</td><td>参数描述</td><td>类型</td><td>是否必选</td></tr><tr><td>kernel_name</td><td>核函数名称。</td><td>string</td><td>是</td></tr><tr><td>kernel_path</td><td>核函数二进制.o文件所在路径,可配置为绝对路径或者相对路径。</td><td>string</td><td>是</td></tr><tr><td>blockdim</td><td>核函数运行所需的核数,默认值:1。</td><td>int</td><td>否</td></tr><tr><td>mode</td><td>测试模式。
•上板: onboard
•性能仿真:ca</td><td>string</td><td>是</td></tr><tr><td>device_id</td><td>运行时使用昇腾AI处理器的ID,默认值:0。</td><td>int</td><td>否</td></tr><tr><td>tiling_key</td><td>当前动态算子的tiling key。
说明
该参数仅适用于动态算子。</td><td>uint64</td><td>否</td></tr><tr><td>magic</td><td>算子类型。
•cube算子:
RT_DEV_BINARYunchedIANIC_ELFL_AICUBE
•vector算子:
RT_DEV_BINARYunchedIANIC_ELFL_AIVEC
•Mix融合算子:RT_DEV_BINARYunchedIANIC_ELFL(仅Atlas A3训练系列产品/Atlas A3推理系列产品和Atlas A2训练系列产品/Atlas 800IA2推理产品/A200IA2 Box异构组件支持配置)
说明
Atlas推理系列产品需配置为RT_DEV_BINARYunchedIANIC_ELFL。</td><td>string</td><td>是</td></tr><tr><td>test Cases</td><td>测试数据,支持列表,每个元素包含一个用例。详细说明可参考表8-31。
说明
算子上板或仿真调优时仅支持配置单个用例。</td><td>map</td><td>是</td></tr></table>


表 8-31 test_case 参数字段说明


<table><tr><td colspan="3">参数</td><td>说明</td><td>类型</td><td>是否必选</td></tr><tr><td>case_name</td><td>-</td><td>-</td><td>测试用例的名称，需唯一。</td><td>string</td><td>是</td></tr><tr><td>para_m_desc</td><td>-</td><td>-</td><td>用例描述，支持列表，每个元素代表一个核函数参数。</td><td>list</td><td>是</td></tr><tr><td>-</td><td>param_type</td><td>input/output/workplace/tiling/fftAddr</td><td>参数类型。</td><td>string</td><td>是</td></tr><tr><td>-</td><td>type</td><td>-</td><td>输入输出数据支持的数据类型，例如：uint8、int16、int32、float16、float32、float等。说明当“param_type”为input、output时必选。</td><td>string</td><td>否</td></tr><tr><td>-</td><td>shape</td><td>-</td><td>输入输出Tensor支持的形状，所有输入输出Tensor需支持相同数量的形状。例如：[8,3,256,256]。若输入非法的形状会报错，例如：[0]。说明当“param_type”为input、output时必选。</td><td>list</td><td>否</td></tr><tr><td>-</td><td>data_path</td><td>-</td><td>输入数据bin文件的路径。说明·当“param_type”为input时必须输入data_path或value_range，且data_path优先级更高。·若json文件的“data_path”字段为空，需将json文件中设置为“data_path”:“null”。json文件具体内容请参见8.12 JSON配置文件说明。</td><td>string</td><td>否</td></tr><tr><td>-</td><td>name</td><td>-</td><td>参数名称，需唯一。说明当“param_type”为input、output时必选。</td><td>string</td><td>否</td></tr><tr><td>-</td><td>user Workspace_size</td><td>-</td><td>用户设置的workspace_size大小。说明当“param_type”为workspace时必选。</td><td>int</td><td>否</td></tr><tr><td>-</td><td>tiling_data_size</td><td>-</td><td>tiling数据大小。说明当“param_type”为tiling时必选。</td><td>int</td><td>否</td></tr><tr><td>-</td><td>tiling_data_path</td><td>-</td><td>tiling数据bin文件所在路径。说明当“param_type”为tiling时必选。</td><td>string</td><td>否</td></tr><tr><td>-</td><td>data_size</td><td>-</td><td>fftAddr的数据_size大小。说明当“param_type”为fftAddr时必选。</td><td>int</td><td>否</td></tr></table>

# 须知

“output”中参数取值的个数都要与“input”一致，否则测试用例生成会失败。 例如：“input”的type支持的类型个数2，则“output”的type支持的类型个数也 需要为2。 同理，所有input和output中的type、shape和value_range的取值个数也需要保持 一致。 

● 一个算子所有“input”中参数取值的个数都要一致，否则测试用例生成会失败。 所有“input”中的type、shape和value_range的取值个数也需要保持一致。