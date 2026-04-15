<!-- Source: 算子开发工具.md lines 4016-4220 | Section: 4.5 算子编译部署 -->

# 4.5 算子编译部署

# 编译前准备

编译Ascend C算子Kernel侧代码实现文件*.cpp，分为源码发布和二进制发布两种 方式。 

源码发布：不对算子Kernel侧实现进行编译，保留算子Kernel源码文件 *.cpp。该方式可以支持算子的在线编译、通过ATC模型转换的方式编译算子 的场景。 

二进制发布：对算子Kernel侧实现进行编译，生成描述算子相关信息的json文 件*.json和算子二进制文件*.o。如果需要直接调用算子二进制，则使用该编译 方式。 

编译Ascend C算子Host侧代码实现文件*.cpp、*.h。 

将原型定义和shape推导实现编译成算子原型定义动态库 libcust_opsproto_*.so，并生成算子原型对外接口op_proto.h。 

将算子信息库定义编译成信息库定义文件*.json。 

将tiling实现编译成tiling动态库liboptiling.so等。 

自动生成单算子API调用代码和头文件aclnn_*.h，并编译生成单算子API调用 的动态库libcust_opapi.so。 

# 编译流程

完成算子Kernel、Host侧的开发后，需要对算子工程进行编译，生成自定义算子安装 包*.run，具体编译操作流程请参考图4-2。 


图4-2 算子工程编译示意图


![](images/1f29027825e3533f69a383df2509dd4bb2632db4c402ab1d9838543691dc3a67.jpg)


# 操作步骤

步骤1 修改工程目录下的CMakePresets.json cacheVariables的配置项，完成工程编译相关 配置。CMakePresets.json文件内容如下，参数说明请参见表4-6。 

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
                "CMAKE Builds_TYPE": {
                    "type": "STRING",
                    "value": "Release"
            },
                "ENABLE_SOURCE.Package": {
                    "type": "BOOL",
                    "value": "True"
            }
            "ENABLE_BINARY.Package": {
                "type": "BOOL",
                "value": "True"
            }
        ]
    }
} 
```

```json
"ASCEND_COMPUTE_UNIT": { "type": "STRING", "value": "ascendxxx" }, "ENABLE_TEST": { "type": "BOOL", "value": "True" }, "vendor_name": { "type": "STRING", "value": "customize" }, "ASCEND_PYTHON_EXECUTEABLE": { "type": "STRING", "value": "python3" }, "CMAKE_install_prefix": { "type": "PATH", "value": "${sourceDir}/build_out" }, "ENABLE_CROSS_COMPILE": { //使能交叉编译，请根据实际环境进行配置 "type": "BOOL", "value": "False" }, "CMAKE_CROSSPLATFORM_COMPILER": { //请替换为交叉编译工具安装后的实际路径 "type": "PATH", "value": "/usr/bin/aarch64-linux-gnu-g++" } } } 
```


表 4-6 需要开发者配置的常用参数列表


<table><tr><td>参数名称</td><td>参数描述</td><td>默认值</td></tr><tr><td>CMAKE-built_TYPE</td><td>编译模式选项，可配置为：
·“Release”，Release版本，不包含调试信息，编译最终发布的版本。
·“Debug”，“Debug”版本，包含调试信息，便于开发者开发和调试。</td><td>&quot;Release&quot;</td></tr><tr><td>ENABLE_SOURCEPACKAGE</td><td>是否开启源码编译。</td><td>&quot;True&quot;</td></tr><tr><td>ENABLE_BINARYPACKAGE</td><td>是否开启二进制编译。</td><td>&quot;True&quot;</td></tr><tr><td>vendor_name</td><td>标识自定义算子所属厂商的名称。建议开发者自行指定所属厂商名称，避免和其他厂商提供的算子包冲突。</td><td>&quot;customize&quot;</td></tr></table>

步骤2 支持自定义编译选项。 

通过修改算子工程op_kernel目录下的CMakeLists.txt文件，使用 add_ops_compile_options来增加编译选项。 

add_ops_compile_options(OpType COMPUTE_UNIT soc_version1 soc_version2 ... OPTIONS option1 option2..) 


表 4-7 具体参数介绍


<table><tr><td>参数名称</td><td>可选/必选</td><td>参数描述</td></tr><tr><td>算子类型</td><td>必选</td><td>第一个参数应传入算子类型,如果需要对算子工程中的所有算子生效,需要配置为ALL。</td></tr><tr><td>COMPUTER UNIT</td><td>可选</td><td>标识编译选项在哪些AI处理器型号上生效,多个型号之间通过空格间隔。不配置时表示对所有AI处理器型号生效。说明COMPUTER_UNIT具体配置如下:·非Atlas A3 训练系列产品/Atlas A3 推理系列产品:在安装昇腾AI处理器的服务器执行npu-sminfo命令进行查询,获取Chip Name信息。实际配置值为AscendChip Name,例如Chip Name取值为xxxx,实际配置值为Ascendxxxx。当Ascendxxxx为代码样例的路径时,需要配置为ascendxxx。·Atlas A3 训练系列产品/Atlas A3 推理系列产品:在安装昇腾AI处理器的服务器执行npu-sminfo -t board -i id -c chip_id命令进行查询,获取Chip Name和NPU Name信息,实际配置值为Chip Name_NPU Name。例如Chip Name取值为Ascendxxx,NPU Name取值为1234,实际配置值为Ascendxxx_1234。当Ascendxxx_1234为代码样例的路径时,需要配置为ascendxxx_1234。其中:-id:设备id,通过npu-sminfo-l命令查出的NPU ID即为设备id。-chip_id:芯片id,通过npu-sminfo-m命令查出的Chip ID即为芯片id。</td></tr><tr><td>OPTIONS</td><td>必选</td><td>自定义的编译选项。多个编译选项之间通过空格间隔。说明·增加-sanitizer等调试用编译选项,使能msSanitizer工具的msOpGen算子工程编译场景。add ops.compile-options(ALL OPTIONS -sanitizer)·增加-g等调试用编译选项,使能msProf工具的msprof op simulator场景下的代码调用栈和热点图功能。add ops.compile-options(ALL COMPUTE_UNIT Ascendxxxx,yOPTIONS -g)·增加-g -O0等调试用编译选项,使能msDebug工具。add ops.compile-options(ALL OPTIONS -g -O0)</td></tr></table>

步骤3 在算子工程目录下执行如下命令，进行算子工程编译。 

./build.sh 

编译成功后，会在当前目录下创建build_out目录，并在build_out目录下生成自定义算 子安装包custom_opp_<target_os>_<target_architecture>.run。 

# 须知

注册算子类型后，框架会根据算子类型获取算子注册信息，同时在编译和运行时按照 一定的规则匹配算子实现文件名称和kernel侧核函数名称。为了保证正确匹配，算子 类型、算子实现文件名称和核函数名称需要遵循如下定义规则。通常情况下，开发者 只需要保证创建算子工程时原型定义json文件中算子类型op的参数值为大驼峰命名方 式即可，工程创建后自动生成的代码即满足该规则。在手动编写算子原型定义和算子 实现文件时需要按照如下规则定义。 

算子类型需要采用大驼峰的命名方式，即采用大写字符区分不同的语义。 

算子实现文件名称、核函数名称需相同，均为算子类型转换为下划线命名方式后的 值。下文描述了通过算子类型转换成算子实现文件名称和核函数名称的过程： 

● 首字符的大写字符转换为小写字符。例如：Abc -> abc。 

● 大写字符的前一个字符为小写字符或数字，则在大写字符前插一个下划线“_” 并将该字符转换为小写字符。例如：AbcDef $- >$ abc_def。 

大写字符前一个字符为大写字符且后一个字符是小写字符，则在大写字符前插一个 下划线“_”，并将该字符转换为小写字符。例如：AbcAAc $- >$ abc_a_ac。 

● 其他大写字符转换为小写字符，小写字符保持不变。 

步骤4 进行算子包部署。 

----结束 

# 算子包部署

步骤1 自定义算子安装包部署。 

在自定义算子包所在路径下，执行如下命令，安装自定义算子包。 

./custom_opp_<target_os>_<target_architecture>.run --install-path=<path> // 其中--install-path为可选参 数，用于指定自定义算子包的安装目录。支持指定绝对路径，运行用户需要具有指定安装路径的读写权限。 

下文描述中的<vendor name>为算子工程编译时CMakePresets.json配置文件中字段 “vendor_name”的取值，默认为"customize"。 

默认安装场景，不配置--install-path参数，安装成功后会将编译生成的自定义算 子相关文件部署到 

${INSTALL_DIR}/opp/vendors/<vendor name>目录。${INSTALL_DIR}请替换为 CANN软件安装后文件存储路径。例如，若安装的Ascend-cann-toolkit软件包， 安装后文件存储路径示例为：$HOME/Ascend/ascend-toolkit/latest。 

# 说明

自定义算子包默认安装路径${INSTALL_DIR}/opp/vendors的目录权限与CANN软件包安装 用户和安装配置有关。如果因权限不足导致自定义算子包安装失败，可使用--install-path 参数并配置环境变量ASCEND_CUSTOM_OPP_PATH来指定安装目录（参考指定目录安装 场景）或者联系CANN软件包的安装用户修改vendors目录权限来解决。详细的案例请参考 《Ascend C算子开发指南》中“FAQ > 调用算子时出现无法打开config.ini的报错及算子包 部署时出现权限不足报错”章节。 

指定目录安装场景，配置--install-path参数，安装成功后会将编译生成的自定义 算子相关文件部署到<path>/vendors/<vendor name>目录，并在<path>/ vendors/<vendor name>/bin目录下新增set_env.bash，写入当前自定义算子包相 关的环境变量。 

# 须知

如果部署算子包时通过配置--install-path参数指定了算子包的安装目录，则在使 用自定义算子前，需要执行source <path>/vendors/<vendor_name>/bin/ set_env.bash命令，set_env.bash脚本中将自定义算子包的安装路径追加到环境 变量ASCEND_CUSTOM_OPP_PATH中，使自定义算子在当前环境中生效。 

命令执行成功后，自定义算子包中的相关文件将部署至当前环境中。 

步骤2 以默认安装场景为例，可查看部署后的目录结构，如下所示： 

![](images/a05a5c4a93270b96d84eb8b139cc7504f08351bf4c4a18fdaf1fec086637d0ea.jpg)


# 说明

参数值：<soc version>，查询方法如下： 

● 非Atlas A3 训练系列产品/Atlas A3 推理系列产品：在安装昇腾AI处理器的服务器执行npusmi info命令进行查询，获取Chip Name信息。实际配置值为AscendChip Name，例如 Chip Name取值为xxxyy，实际配置值为Ascendxxxyy。当Ascendxxxyy为代码样例的路径 时，需要配置为ascendxxxyy。 

● Atlas A3 训练系列产品/Atlas A3 推理系列产品：在安装昇腾AI处理器的服务器执行npusmi info -t board -i id -c chip id命令进行查询，获取Chip Name和NPU Name信息，实 际配置值为Chip Name_NPU Name。例如Chip Name取值为Ascendxxx，NPU Name取值 为1234，实际配置值为Ascendxxx 1234。当Ascendxxx 1234为代码样例的路径时，需要配 置为ascendxxx 1234。 

其中： 

id：设备id，通过npu-smi info -l命令查出的NPU ID即为设备id。 

chip_id：芯片id，通过npu-smi info -m命令查出的Chip ID即为芯片id。 

步骤3 配置自定义算子优先级。 

多算子包共存的情况下，若不同的算子包目录下存在相同OpType的自定义算子，则以 优先级高的算子包目录下的算子为准。下面介绍如何配置算子包优先级： 

# 默认安装场景

当“opp/vendors”目录下存在多个厂商的自定义算子时，您可通过配置“opp/ vendors”目录下的“config.ini”文件，配置自定义算子包的优先级。 

“config.ini”文件的配置示例如下： 

```csv
loadpriority=vendor_name1,vendor_name2,vendor_name3 
```

“load_priority”：优先级配置序列的关键字，不允许修改。 

“vendor name1,vendor name2,vendor name3”：自定义算子厂商的优先 级序列，按照优先级从高到低的顺序进行排列。 

# 指定目录安装场景

指定目录安装场景下，如果需要多个自定义算子包同时生效，分别执行各算子包 安装路径下的set_env.bash脚本即可。每次脚本执行都会将当前算子包的安装路 径追加到ASCEND_CUSTOM_OPP_PATH环境变量的最前面。因此可以按照脚本执 行顺序确定优先级：脚本执行顺序越靠后，算子包优先级越高。 

比如先执行source <path>/vendor name1/bin/set env.bash，后执行source <path>/vendor_name2/bin/set_env.bash，vendor_name2算子包的优先级高 于vendor_name1。ASCEND_CUSTOM_OPP_PATH示例如下： 

```txt
ASCENDCustom_OPPATH=/vendor_name2:/vendor_name1 
```

指定目录安装场景下安装的算子包优先级高于默认方式安装的算子包。 

步骤4 基于msOpST工具，进行算子Kernel测试，验证算子的功能。 

步骤5 基于msSanitizer工具，进行算子内存和异常检测，定位算子精度异常。 

步骤6 基于msDebug工具，进行算子上板调试，逐步确认算子精度异常。 

步骤7 基于msProf工具，生成计算内存热力图、指令流水图、及算子指令热点图统计信息， 协助用户进一步优化算子性能。 

步骤8 经过以上操作步骤，确定算子精度和性能达到交付标准后，方可正常使用。 

----结束