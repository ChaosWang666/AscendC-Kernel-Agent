<!-- Source: 算子开发工具.md lines 4675-4904 | Section: 5.4 生成/执行测试用例 -->

# 5.4 生成/执行测试用例

指导用户根据算子测试用例定义文件生成ST测试数据及测试用例执行代码，在硬件环 境上执行算子测试用例。 

# 开发环境与运行环境合设场景

步骤1 ST测试用例执行时，会使用AscendCL接口加载单算子模型文件并执行，所以需要配置 AscendCL应用编译所需其他环境变量，如下所示。 

```txt
export DDK_PATH=\({INSTALL_DIR}\)  
export NPU_HOST_lib=\({INSTALL_DIR}/\{arch-os\}/devlib 
```

# 说明

● ${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。若安装的Ascend-cann-toolkit软 件包，以root安装举例，则安装后文件存储路径为：/usr/local/Ascend/ascend-toolkit/ latest。 

● {arch-os}中arch表示操作系统架构，os表示操作系统。 

步骤2 执行如下命令生成/执行测试用例，具体参数介绍请参见表5-2。 

msopst run -i {**.json} -soc{soc version} -out {output path} -c {case name} -d {device id} -conf {msopst.ini path}-err_thr "[threshold1,threshold2]" 

● msopst.ini文件的路径为：${INSTALL_DIR}/python/site-packages/bin/。 

● msopst.ini文件参数说明如下表所示。 

# 说明

msopst.ini文件默认使用FP16精度模式，如需使用其他精度模式需手动修改表5-6中 atc_singleop_advance_option的--precision_mode参数。 


表 5-6 msopst.ini 文件参数说明


<table><tr><td>参数</td><td>值</td><td>说明</td></tr><tr><td>only_gen_without_run</td><td>- True- False (默认)</td><td rowspan="2">msOpST工具运行模式。详情请参见表5-7。</td></tr><tr><td>only_run_without_gen</td><td>- True- False (默认)</td></tr><tr><td>performance_mode</td><td>- True- False</td><td>获取算子性能模式。若设置为True,运行成功后在run/out/prof/IOBxxx/summary目录下生成一系列性能结果文件,用户只需查看op.summary_0_1.csv即可。该功能需要配置CANN包安装环境变量,请根据实际安装路径修改。export install_path=${{INSTALL_DIR}}</td></tr><tr><td>ASCENDGLOBAL(LOG_LEVEL</td><td>- 0: DEBUG级别- 1: INFO级别- 2: WARNING级别- 3: ERROR级别 (默认)- 4: NULL级别,不输出日志</td><td>设置Host日志级别环境变量。</td></tr><tr><td>ASCEND_SLOG_PRIN T_TO_STDOUT</td><td>- 0: 屏幕不打印输出 (默认)- 1: 屏幕打印输出</td><td>日志屏幕打印控制。</td></tr><tr><td>atc_singleop.advanc
e_option</td><td>--log参数取值: 
- debug: 输出debug/info/
    warning,error/event级别的
    运行信息 
- info: 输出info/warning/
    error/event级别的运行信息 
- warning: 输出warning/
    error/event级别的运行信息 
- error: 输出error/event级别的
    运行信息 (默认) 
- null: 不输出日志信息 
--precision_mode参数取值: 
- force.fp16: 表示算子支持
    fp16和fp32时,强制选择
    fp16 (默认) 
- force.fp32: 表示算子支持
    fp16和fp32时,强制选择
    fp32 
- allow.fp32_to.fp16: 表示
    如果算子支持fp32,则保留
    原始精度fp32;如果不支持
    fp32,则选择fp16 
- must_keep_origin dtype: 
    表示保持原图精度 
- allow_mix_precision: 表示
    混合精度模式 
--host_env_os参数取值:
    linux: 表示设置操作系统类型
    为linux 
--host_env_cpu参数取值:
    x86_64,表示设置操作系统架
    构为x86_64 
- aarch64: 表示设置操作系
    统架构为aarch64 
示例:
    atcsingleopadvance_option="--
    log=info --host_env_os=linux 
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
的操作系统架构。</td></tr><tr><td>HOST_ARCH</td><td>- X86_64: X86_64架构
- aarch64: arm64架构
示例:
HOST_ARCH="aarch64"</td><td>执行机器的架构。
一般在分设场景下配
置该参数。</td></tr><tr><td>TOOLChain</td><td>g++ path: g++工具链路径示例: TOOLChain="/usr/bin/g++"</td><td>c++编译器路径，配置时以g++结尾。一般在分设场景下配置该参数。</td></tr></table>


表 5-7 msOpST 的运行模式


<table><tr><td>模式</td><td>only_gen_without_run</td><td>only_run_without_run</td><td>运行模式</td></tr><tr><td>1</td><td>False</td><td>False</td><td>既生成ST测试代码，又运行ST测试代码。</td></tr><tr><td>2</td><td>True</td><td>True/False</td><td>只生成ST测试代码，不运行ST测试代码。</td></tr><tr><td>3</td><td>False</td><td>True</td><td>不生成ST测试代码，只运行ST测试代码。</td></tr></table>

# 命令行执行示例：

不启用msOpST工具的高级功能，执行如下命令生成ST测试用例并执行。 msopst run -i xx/AddCustom_case_timestamp.json -soc{soc version} -out ./output 

启动msOpST工具的高级功能，仅生成ST测试用例，用户修改ST测试用例 后，再执行ST测试用例。 

i. 执行命令，编辑msopst.ini文件 vim ${INSTALL_DIR}/python/site-packages/bin/msopst.ini 

将msOpST工具的运行模式修改为模式2，按照表5-7修改 

“only_gen_without_run”和“only_run_without_gen”参数的取值。 只生成ST测试代码，不运行ST测试代码。 

ii. 执行如下命令生成ST测试源码。 

msopst run -i xx/AddCustom_case_timestamp.json -soc{soc version} -out ./output -conf xx/ msopst.ini 

-conf参数请修改为msopst.ini配置文件的实际路径。 

ST测试用例生成后，用户可根据需要自行修改ST测试用例代码。 

iii. 修改msopst.ini文件，修改运行模式为仅执行ST测试用例。 

执行命令，编辑msopst.ini文件 

vim ${INSTALL_DIR}/python/site-packages/bin/msopst.ini 

将msOpST工具的运行模式修改为模式3，按照表5-7修改 

“only_gen_without_run”和“only_run_without_gen”参数的取值。 不生成ST测试代码，只运行ST测试代码。 

iv. 执行如下命令运行已修改的ST测试源码。 

msopst run -i xx/AddCustom_case_timestamp.json -soc{soc version} -out ./output -conf xx/ msopst.ini 

# 说明

若执行失败。 

▪ 请参见《应用开发接口》手册中“acl API参考 $>$ 数据类型及其操作接口 > aclError”查看aclError的含义。 

▪ 请参见《故障处理》中的“错误码参考”章节内容。 

▪ 请参见《日志参考》查看日志进行分析。 

# 步骤3 查看执行结果。

若运行模式为仅生成ST测试用例代码，不执行ST测试用例，会在-out指定的目录 下生成时间戳目录，时间戳目录下将生成以算子的OpType命名的存储测试用例代 码的文件夹，目录结构如下所示： 

![](images/652fd4383863a1d9992161d2cae5439481d586da79773ce6754b9d1b6bcf49e3.jpg)


若运行模式为既生成ST测试代码，又运行ST测试代码，命令执行完成后，会屏显 打印测试用例执行结果，并会在-out指定的目录下生成时间戳目录，时间戳目录 下将生成以算子的OpType命名的存储测试用例及测试结果的文件夹，目录结构如 下所示： 

![](images/a3406a1f3b2a2e2664905064e0687907d9af797e71831f69dfa694b5d90bf31e.jpg)


![](images/f727a4ca19f589c704f3d79935d076e0b57a09802659c281639f4d679daba0e9.jpg)


命令运行成功后，会生成报表st_report.json，记录了测试的信息以及各阶段运行 情况，用户运行出问题以后，可基于报表查询运行信息，以便问题定位。同时， st_report.json报表可以对比测试结果。st_report.json保存在图5-1中“The st_report saved in”路径下。 


图 5-1 运行结果示例


![](images/683db88a2f7fb67a51a18e884fc73b4b8673876cbf235d3fdd9e4b751102fdf2.jpg)



表 5-8 st_report.json 报表主要字段及含义


<table><tr><td colspan="3">字段</td><td>说明</td></tr><tr><td>run_cmd</td><td>-</td><td>-</td><td>命令行命令。</td></tr><tr><td rowspan="3">report_list</td><td>-</td><td>-</td><td>报告列表，该列表中可包含多个测试用例的报告。</td></tr><tr><td rowspan="2">trace_detail</td><td>-</td><td>运行细节。</td></tr><tr><td>st(case_info</td><td>测试信息，包含如下内容。
- expect_data_path: 期望计算结果路径。
- case_name: 测试用例名称。
- input_data_path: 输入数据路径。
- planned_output_data Paths: 实际计算结果输出路径。
- op.params: 算子参数信息。</td></tr><tr><td rowspan="4"></td><td></td><td>stage_result</td><td>运行各阶段结果信息,包含如下内容。- status: 阶段运行状态,表示运行成功或者失败。- result: 输出结果-stage_name: 阶段名称。- cmd: 运行命令。</td></tr><tr><td>case_name</td><td>-</td><td>测试名称。</td></tr><tr><td>status</td><td>-</td><td>测试结果状态,表示运行成功或者失败。</td></tr><tr><td>expect</td><td>-</td><td>期望的测试结果状态,表示期望运行成功或者失败。</td></tr><tr><td rowspan="4">summary</td><td>-</td><td>-</td><td>统计测试用例的结果状态与期望结果状态对比的结果。</td></tr><tr><td>test case count</td><td>-</td><td>测试用例的个数。</td></tr><tr><td>success count</td><td>-</td><td>测试用例的结果状态与期望结果状态一致的个数。</td></tr><tr><td>failed count</td><td>-</td><td>测试用例的结果状态与期望结果状态不一致的个数。</td></tr></table>

# ----结束

# 开发环境与运行环境分设场景

步骤1 根据运行环境的架构在开发环境上搭建环境。 

1. ST测试用例执行时，会使用AscendCL接口加载单算子模型文件并执行，需要在开 发环境上根据运行环境的架构配置AscendCL应用编译所需其他环境变量。 

当开发环境和运行环境架构相同时，环境变量如下所示。 export DDK_PATH=${INSTALL_DIR} export NPU_HOST_LIB ${ \mathfrak { s } } { \mathfrak { s } }$ {INSTALL_DIR}/{arch-os}/devlib 

当开发环境和运行环境架构不同时，环境变量如下所示。 export DDK_PATH=${INSTALL_DIR}/{arch-os} export NPU_HOST_LIB=${INSTALL_DIR}/{arch-os}/devlib 

# 说明

${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。若安装的Ascend-canntoolkit软件包，以root安装举例，则安装后文件存储路径为：/usr/local/Ascend/ ascend-toolkit/latest。 

{arch-os}中arch表示操作系统架构（需根据运行环境的架构选择），os表示操作系统 （需根据运行环境的操作系统选择）。 

步骤2 在开发环境启动msOpST工具的高级功能，仅生成ST测试用例。 

1. 执行命令，编辑msopst.ini文件。 vim ${INSTALL_DIR}/python/site-packages/bin/msopst.ini 

2. 将msOpST工具的运行模式修改为模式2，按照表5-7修改 “only_gen_without_run”和“only_run_without_gen”参数的取值。只生成ST 测试代码，不运行ST测试代码。 

3. 若开发环境和运行环境架构不同，按照表5-6修改“HOST_ARCH”和 “TOOL_CHAIN”参数的取值。 

4. 执行如下命令生成ST测试源码。 msopst run -i xx/AddCustom_case_timestamp.json -soc{soc version} -out {output path} -conf xx/ msopst.ini 

-conf参数请修改为msopst.ini配置文件的实际路径。 ST测试用例生成后，用户可根据需要自行修改ST测试用例代码。 

5. 执行完成后，将在{outputpath}下生成ST测试用例，并使用g $^ { + + }$ 编译器生成可执 行文件main。同时，屏幕打印信息中展示此次一共运行几个用例，测试用例运行 的情况，并生成报表st_report.json，保存在屏显信息中“The st report saved in”所示路径下，报表具体信息请参见表5-8。 

步骤3 执行测试用例。 

1. 将开发环境的算子工程目录的run目录下的out文件夹拷贝至运行环境任一目录， 例如上传到${INSTALL_DIR}/Ascend_project/run_add/目录下。 

2. 在运行环境中执行out文件夹下的可执行文件。 进入out文件夹所在目录，执行如下命令： chmod $+ { \sf x }$ main ./main 

步骤4 查看运行结果。 

执行完成后，屏显信息显示此次用例运行的情况，如图5-2所示。 


图 5-2 运行结果


![](images/b886ad1f4d3d6d648e28b01ca5c830414260776d1b8b261c807a8b3be60e95ac.jpg)


----结束