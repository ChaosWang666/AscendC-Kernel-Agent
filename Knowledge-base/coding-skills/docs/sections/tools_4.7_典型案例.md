<!-- Source: 算子开发工具.md lines 4347-4452 | Section: 4.7 典型案例 -->

# 4.7 典型案例

# 4.7.1 Ascend C 自定义算子开发实践

展示如何使用msOpGen工具进行Ascend C自定义算子的工程创建、编译和部署，并使 用msOpST工具对Ascend C自定义算子进行功能测试。 

# 前提条件

已参考4.2 使用前准备，完成msOpGen工具的使用准备。 

# 操作步骤

步骤1 参考以下json文件，准备算子原型文件（以MatmulCustom算子为例）。 

```json
{
    "op": "MatmulCustom",
    "language": "cpp",
    "input_desc": [
        "name": "a",
        "param_type": "required",
        "format": [ "ND"]
        ],
        "type": [ "float16"]
    ],
    {
        "name": "b",
        "param_type": "required",
        "format": [ "ND"]
        ],
        "type": [ "float16"]
    },
    {
        "name": "bias",
        "param_type": "required",
        "format": [ "ND"]
        ],
        "type": [ "float"]
    }
},
"output_desc": [
    "name": "c",
    "param_type": "required",
    "format": [ "ND"]
    ],
    "type": [ "float"]
} 
```

步骤2 使用msOpGen工具执行以下命令，创建算子工程。 

# 说明

msOpGen工具仅生成空的算子工程模板，需要用户自行添加算子实现，具体请参考《Ascend C 算子开发指南》中的“工程化算子开发 > 算子实现”章节。 

msopgen gen -i MatmulCustom.json -f tf -c ai_core-Ascendxxxyy -lan cpp -out MatmulCustom 

步骤3 命令执行完毕，会在指定目录下生成如下算子工程目录。 

![](images/39d5925a9696cbc93c4f924db61bcd3a2917745ed3d8ce565ded992be5403c3d.jpg)


步骤4 执行算子工程编译。 

./build.sh 

步骤5 进行自定义算子包部署。 

执行以下命令，将算子部署到CANN： 

./build_out/custom_opp_<target_os>_<target_architecture>.run 

执行以下命令，将算子部署到自定义路径（以xxx/MatmulCustom/installed为 例）： 

./build_out/custom_opp_<target_os>_<target_architecture>.run --install-path="xxx/MatmulCustom/ installed" 

步骤6 执行以下命令，生成ST测试用例。 

msopst create -i "xxx/MatmulCustom/op_host/matmul_custom.cpp" -out ./st // xxx需要修改为用户实际工 程路径 

步骤7 进行ST测试。 

1. 根据CANN包安装路径，配置以下环境变量： 

export DDK_PATH=${INSTALL_DIR} export NPU_HOST_LIB $\ L = \ L _ { \ P }$ ${INSTALL_DIR}/{arch-os}/devlib 

2. 执行以下命令，进行ST测试，并将输出结果到指定路径： 

msopst run -i ./st/xxx.json -soc Ascendxxxyy -out ./st/out //xxx.json为步骤6获得的测试用例 

----结束 

# 5 算子测试（msOpST）

工具概述 

使用前准备 

生成测试用例定义文件 

生成/执行测试用例 

生成单算子上板测试框架 

典型案例