<!-- Source: 算子开发工具.md lines 5030-5336 | Section: 5.6 典型案例 -->

# 5.6 典型案例

# 5.6.1 测试用例定义文件

● Less算子的测试用例定义文件“Less_case.json”如下所示。 

```json
{
"case_name": "Test_Less_001", //测试用例名称
"op": "Less", //算子的类型
"input_desc": [ //算子输入描述
{
//第一个输入
"format": ["ND"], "type": ["int32","float"]
"shape": [12,32],
"data_distribution": [ //生成测试数据时选择的分布方式
"uniform"
],
"value_range": [ //输入数据的取值范围
[ 1.0,
384.0 ]
]
},
{
//第二个输入
"format": ["ND"], "type": ["int32","float"]
"shape": [12,32],
"data_distribution": [ "uniform"
],
"value_range": [ [ 1.0,
384.0 ]
]
}
},
"output_desc": [ //算子的输出
{
"format": ["ND"], "type": ["bool","bool"]
"shape": [12,32]
}
}
{
"case_name": "Test_Less_002",
"op": "Less",
"input_desc": [ 
{
...
},
.
} 
```

```javascript
} ],"output_desc":[ { ... } ] 1 
```

若算子包含属性，测试用例定义文件如下所示。 

```json
{
"case_name":"Test_Conv2D_001", //测试用例名称
"op":"Conv2D", //算子的Type，唯一
"input_desc": [ //算子的输入描述
{
//算子的第一个输入
"format": [ //用户在此处配置待测试的输入Tensor的排布格式
"ND", "NCHW"
],
"type": [ //输入数据支持的数据类型
"float", "float16"
],
"shape": [8,512,7,7], //输入Tensor的shape,用户需要自行修改
"data_distribution": [ //生成测试数据时选择的分布方式
"uniform"
],
"value_range": [ //输入数据值的取值范围
[ 0.1, 200000.0 ]
]
},
{
//算子的第二个输入
"format": [ "ND", "NCHW"
],
"type": [ "float", "float16"
],
"shape": [512,512,3,3],
"data_distribution": [ "uniform"
],
"value_range": [ [ 0.1, 200000.0 ]
]
}
},
"output_desc": [ //必选,含义同输入Tensor描述
{
"format": [ "ND", "NCHW"
],
"type": [ "float", "float16"
],
"shape": [8,512,7,7]
] 
```

```json
"attr": [ //算子的属性
{
    "name": "strides", //属性的名称
    "type": "list_int", //属性的支持的类型
    "value": [1,1,1,1]
},
{
    "name": "pads",
    "type": "list_int",
    "value": [1,1,1,1]
},
{
    "name": "dilations",
    "type": "list_int",
    "value": [1,1,1,1]
}
] 
```

● 若指定固定输入，例如ReduceSum的axes参数，测试用例定义文件如下所示。 

```json
{
"case_name": "Test_ReducSum_001",
"op": "ReduceSum",
"input_desc": [ format": ["ND"], "type": ["int32"], //若需要设置value,则每个用例只能测试一种数据类型
"shape": [3,6,3,4],
"data_distribution": [ uniform ]
,"value_range": [ -384,
384 ]
] }, 
{
"format": ["ND"], "type": ["int32"], "shape": [2],
"data_distribution": [ uniform ]
,"value_range": [ -3,
1 ]
] ], 
"value": [0,2] //设置具体值,需要与shape对应 }
},
"output_desc": [ format": ["ND"], "type": ["int32"], "shape": [6,4] }
], 
"attr": [ name]: "keep_dims", type]: "bool", value": false } 
```

```txt
1 1 
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

若算子的输入个数不确定（动态多输入场景）。 

以AddN算子为例，属性“N”的取值为3，则需要配置3个输入描述，name分别 为x0、x1、x2，即输入个数需要与属性“N”的取值匹配。 

```txt
{
    "op": "AddN",
    "input_desc": [ 
        "name": "x0",
        "format": "NCHW",
        "shape": [1,3,166,166],
        "type": "float32"
    ],
    {
        "name": "x1",
        "format": "NCHW",
        "shape": [1,3,166,166],
        "type": "int32"
    },
    {
        "name": "x2",
        "format": "NCHW",
        "shape": [1,3,166,166],
        "type": "float32"
    }
},
"output_desc": [ 
    "format": "NCHW",
    "shape": [1,3,166,166],
    "type": "float32"
    ]
},
"attr": [ 
    "name": "N",
    "type": "int", 
```

```txt
"value": 3 } ] 1 
```

若算子的某个输入为常量，测试用例定义文件如下所示。 

```json
{ "case_name":"Test_OptType_001", "op":"OptType", "input_desc":[ { "format": ["ND"], "type": ["int32"], "shape": [1], "is_const":true, //标识此输入为常量 "data_distribution": [ "uniform" ], "value":[11], //常量的值 "value_range": [ //min_value与max_value都配置为常量的值 11, 11 ] } }, { ... } ], "output_desc":[ { ... } ] } 
```

若算子的输入输出类型为复数，测试用例定义文件如下所示。 

```json
{
    "case_name": "Test_ReduceSum_001",
    "op": "ReduceSum",
    "input_desc": [
        "format": ["ND],
        "type": [
            "complex64", //输入类型为复数
            "complex128" //输入类型为复数
        ],
        "shape": [3,6],
        "data_distribution": [
            "uniform"
        ],
        "value_range": [/实部取值范围
            1,
            10
        ]
    ],
}，
{
    "format": ["ND],
    "type": [
        "int32",
        "int64",
    ]
    ,
    "shape": [1],
    "data_distribution": [ 
```

```snap
"uniform"
],
"value_range": [
1,
1
]
]
}
],
"output_desc": [
{
"format": ["ND"]
,"type": [
"complex64", //输入类型为复数
"complex128" //输入类型为复数
],
"shape": [3]
}
],
"attr": [
{
"name":"keep_dims",
"type":"bool",
'value":false
}
]
] 
```

# 6 异常检测（msSanitizer）

工具概述 

使用前准备 

内存检测 

竞争检测 

未初始化检测 

典型案例 

FAQ 

对外接口使用说明