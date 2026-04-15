<!-- Source: 算子开发工具.md lines 4905-5029 | Section: 5.5 生成单算子上板测试框架 -->

# 5.5 生成单算子上板测试框架

通过指定Ascend C算子的ST测试用例定义文件（.json）和实现文件 kernel_name.cpp，自动生成调用核函数的上板测试框架，进行算子的测试验证，最终 查看输出结果确认算子功能是否正确。 

# 说明

● 该功能仅支持Atlas 推理系列产品和Atlas 训练系列产品，不支持Atlas A2 训练系列产品/ Atlas 800I A2 推理产品/A200I A2 Box 异构组件和Atlas A3 训练系列产品。 

● 所有参数不支持输入addr及tiling属性。 

● 支持使用#ifndef __CCE_KT_TEST__对核函数的调用进行封装的场景。 

步骤1 请用户完成以下输入文件的准备工作。 

算子ST测试用例定义文件（*.json文件）。 

Kernel侧算子实现文件（*.cpp文件），具体可参考《Ascend C算子开发指南》中 的“工程化算子开发 > 算子实现 > Kernel侧算子实现”章节。 

步骤2 生成调用Kernel函数的测试代码，执行如下命令，具体参数介绍请参见表5-3。 

msopst ascendc_test -i xx/OpType_case.json -kernel xx/add custom.cpp -out ./output data 

步骤3 查看执行结果。 

命令执行完成后，会屏显打印"Process finished!"提示信息，并会在-out指定的目录下 生成时间戳目录，时间戳目录下将生成以算子的OpType命名的存储测试用例及测试结 果的文件夹，目录结构如下所示： 

![](images/74a0e4af6a0f9e714d4dbda044078cf3258fe68f2e92f51b5b4c56a54c82343d.jpg)


命令运行成功后，会生成报表st_report.json，记录了测试的信息以及各阶段运行情 况，用户运行出问题以后，可基于报表查询运行信息，以便问题定位。同时， st_report.json报表可以对比测试结果。 

st_report.json保存在如下“The st_report saved in”路径中。 

2024-01-17 08:40:55 (3271037) - [INFO] Create 1 sub test cases for Test_AddCustom_001. 

2024-01-17 08:40:55 (3271037) - [INFO] [STEP2] [data_generator.py] Generate data for testcase. 

2024-01-17 08:40:55 (3271037) - [INFO] Start to generate the input data for 

Test_AddCustom_001_case_001_ND_float. 

2024-01-17 08:40:55 (3271037) - [INFO] Generate data for testcase in $HOME/AddCustom/output/ 20240117084055/AddCustom/data. 

2024-01-17 08:40:55 (3271037) - [INFO] [STEP3] [gen_ascendc_test.py] Generate test code of calling of kernel function for AscendC operator. 

2024-01-17 08:40:55 (3271037) - [INFO] Content appended to $HOME/AddCustom/output/ 

20240117084055/AddCustom/main.cpp successfully. 

2024-01-17 08:40:55 (3271037) - [INFO] AscendC operator test code files for kernel implement have been successfully generated. 

2024-01-17 08:40:55 (3271037) - [INFO] If you want to execute kernel function in Ascend aihost or cpu, please execute commands: cd $HOME/AddCustom/output/20240117084055/AddCustom && bash run.sh [KERNEL_NAME](add_custom) [SOC_VERSION](ascendxxxyy) [CORE_TYPE](AiCore/VectorCore) 

[RUN_MODE](cpu/npu). For example: cd $HOME/AddCustom/output/20240117084055/AddCustom && bash run.sh add_custom ascendxxxyy AiCore npu 

2024-01-17 08:40:55 (3271037) - [INFO] Process finished! 

2024-01-17 08:40:55 (3271037) - [INFO] The st report saved in: $HOME/AddCustom/output/ 

20240117084055/st_report.json. 


表 5-9 st_report.json 报表主要字段及含义


<table><tr><td colspan="3">字段</td><td>说明</td></tr><tr><td>run_cmd</td><td>-</td><td>-</td><td>命令行命令。</td></tr><tr><td rowspan="2">report_list</td><td>-</td><td>-</td><td>报告列表，该列表中可包含多个测试用例的报告。</td></tr><tr><td>trace_detail</td><td>-</td><td>运行细节。</td></tr><tr><td rowspan="5"></td><td rowspan="2"></td><td>st(case_info</td><td>测试信息,包含如下内容。
· expect_data_path:期望计算结果路径。
· case_name:测试用例名称。
· input_data_path:输入数据路径。
· planned_output_data Paths:实际计算结果输出路径。
· op.params:算子参数信息。</td></tr><tr><td>stage_result</td><td>运行各阶段结果信息,包含如下内容:
· status:阶段运行状态,表示运行成功或者失败。
· result:输出结果。
· stage_name:阶段名称。
· cmd:运行命令。</td></tr><tr><td>case_name</td><td>-</td><td>测试名称。</td></tr><tr><td>status</td><td>-</td><td>测试结果状态,表示运行成功或者失败。</td></tr><tr><td>expect</td><td>-</td><td>期望的测试结果状态,表示期望运行成功或者失败。</td></tr><tr><td rowspan="4">summary</td><td>-</td><td>-</td><td>统计测试用例的结果状态与期望结果状态对比的结果。</td></tr><tr><td>test case count</td><td>-</td><td>测试用例的个数。</td></tr><tr><td>success count</td><td>-</td><td>测试用例的结果状态与期望结果状态一致的个数。</td></tr><tr><td>failed count</td><td>-</td><td>测试用例的结果状态与期望结果状态不一致的个数。</td></tr></table>

步骤4 修改run.sh文件中的ASCEND_HOME_DIR。 

ASCEND_HOME_DIR为CANN软件包安装路径，请根据实际情况进行修改。 

# 指向昇腾软件包安装地址，导出环境变量 

if [ ! $ASCEND_HOME_DIR ]; then 

export ASCEND_HOME_DIR=${INSTALL_DIR} 

fi 

source $ASCEND_HOME_DIR/bin/set_env.bash 

步骤5 进入执行测试框架的脚本文件所在目录，如下命令进行测试框架代码的上板验证。 

bash run.sh <kernel_name> <soc version> <core_type> <run_mode> 


表 5-10 脚本参数介绍


<table><tr><td>参数名</td><td>参数介绍</td><td>取值</td></tr><tr><td>&lt;kernel_name&gt;</td><td>Ascend C算子实现文件的文件名。</td><td>比如Add算子实现文件为add_custom.cpp,则应传入add_custom。</td></tr><tr><td>&lt;soc_version&gt;</td><td>算子运行的AI处理器型号。</td><td>Atlas训练系列产品和Atlas推理系列产品,需按照实际使用的型号配置“ascendxxxxy”。说明·非Atlas A3训练系列产品/Atlas A3推理系列产品:在安装昇腾AI处理器的服务器执行npu-smi info命令进行查询,获取Chip Name信息。实际配置值为AscendChip Name,例如Chip Name取值为xxxxy,实际配置值为Ascendxxxxy。当Ascendxxxxy为代码样例的路径时,需要配置为ascendxxxxy。·Atlas A3训练系列产品/Atlas A3推理系列产品:在安装昇腾AI处理器的服务器执行npu-smi info -t board -i id -c chip_id命令进行查询,获取Chip Name和NPU Name信息,实际配置值为Chip Name_NPU Name。例如Chip Name取值为Ascendxxx, NPU Name取值为1234,实际配置值为Ascendxxx_1234。当Ascendxxx_1234为代码样例的路径时,需要配置为ascendxxx_1234。其中:-id:设备id,通过npu-smi info -l命令查出的NPU ID即为设备id。-chip_id:芯片id,通过npu-smi info -m命令查出的Chip ID即为芯片id。</td></tr><tr><td>&lt;core_type&gt;</td><td>表明算子在AiCore上或者VectorCore上运行。</td><td>AiCore或VectorCore。</td></tr><tr><td>&lt;run_mode&gt;</td><td>表明算子以cpu模式或npu模式运行。</td><td>cpu或npu。</td></tr></table>

脚本执行完毕会出现类似如下打印，输出"succeed"字样表示完成上板验证。 

```objectivec
INFO: compile op on npu succeed!  
[INFO] Succeeded to exec acl api aclrtCreateContext(&context, deviceld)  
[INFO] Succeeded to exec acl api aclrtCreateStream(&stream)  
[INFO] Succeeded to exec acl api aclrtMalocHost((void**) &xHost), xByteSize)  
[INFO] Succeeded to exec acl api aclrtMaloc((void**)&xDevice, xByteSize, ACL_MEM_MALLOC Huge_FIRST)  
[INFO] Succeeded to exec acl api aclrtMemcpy(xDevice, xByteSize, xHost, xByteSize, ACL_MEMCPY_HOST_TO_DEVICE)  
[INFO] Succeeded to exec acl api aclrtMalocHost((void**) &yHost), yByteSize)  
[INFO] Succeeded to exec acl api aclrtMaloc((void**)&yDevice, yByteSize, ACL_MEM_MALLOC Huge_FIRST)  
[INFO] Succeeded to exec acl api aclrtMemcpy(yDevice, yByteSize, yHost, yByteSize, ACL_MEMCPY_HOST_TO_DEVICE)  
[INFO] Succeeded to exec acl api aclrtMalocHost((void**) &zHost), zByteSize) 
```

```objectivec
[INFO] Succeeded to exec acl api aclrtMalloc((void**)&zDevice, zByteSize, ACL_MEM_MALLOC Huge_FIRST)  
[INFO] Succeeded to exec acl api aclrtSynchronizeStream(stream)  
[INFO] Succeeded to exec acl api aclrtMemcpy(zHost, zByteSize, zDevice, zByteSize, ACL_MEMCPY_DEVICE_TO_HOST)  
[INFO] aclrtDestroyStreamsuccessfully.  
INFO: execute op on npu succeed! 
```

----结束