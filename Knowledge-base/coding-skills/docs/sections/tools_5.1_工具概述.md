<!-- Source: 算子开发工具.md lines 4453-4513 | Section: 5.1 工具概述 -->

# 5.1 工具概述

使用msOpGen工具完成自定义算子包部署后，可选择使用msOpST工具进行ST （System Test）测试，在真实的硬件环境中，对算子的输入输出进行测试，以验证算 子的功能是否正确。 

测试用例通常包括各种不同类型的数据输入和预期输出，以及一些边界情况和异常情 况的测试。通过ST测试，可以确保算子功能的正确性，并且能够在实际应用中正常运 行。 

# 说明

在TBE及AI CPU算子开发场景中，msOpST工具的使用详情请参考9.1.3 基于msOpST工具进行 算子ST测试。 

# 功能描述

msOpST支持生成算子的ST测试用例并在硬件环境中执行。具有如下功能： 

根据用户定义并配置的算子期望数据生成函数，回显期望算子输出和实际算子输 出的对比测试结果，具体请参见5.3 生成测试用例定义文件。 

根据算子测试用例定义文件生成ST测试数据及测试用例执行代码，在硬件环境上 执行算子测试用例，具体请参见5.4 生成/执行测试用例。 

自动生成运行报表（st_report.json）功能，报表记录了测试用例信息及各阶段运 行情况，具体请参见5.4 生成/执行测试用例。 

自动生成算子调用核函数的上板测试框架，进行算子的测试验证，具体请参见5.5 生成单算子上板测试框架。 

# 命令汇总

生成算子测试用例定义文件。 


表 5-1 生成算子测试用例定义文件的参数说明


<table><tr><td>参数名称</td><td>参数描述</td><td>是否必选</td></tr><tr><td>create</td><td>用于生成算子测试用例定义文件(*.json)。</td><td>是</td></tr><tr><td>-i, --input</td><td>Host侧算子的实现文件路径(*.cpp文件),可配置为绝对路径或者相对路径。</td><td>是</td></tr><tr><td>-out, --output</td><td>生成文件所在路径,可配置为绝对路径或者相对路径,并且工具执行用户具有可读写权限。若不配置,则默认生成在执行命令的当前路径。</td><td>否</td></tr><tr><td>-m, --model</td><td>配置为TensorFlow模型文件的路径,可配置为绝对路径或者相对路径。若配置此参数,工具会从TensorFlow模型文件中获取首层算子的shape信息,并自动dump出算子信息库定义文件中算子的shape、dtype以及属性的value值,如果dump出的值在算子信息库定义文件所配置的范围内,则会自动填充到生成的算子测试用例定义文件中;否则会报错。须知若配置此参数,系统中需要安装1.15或2.6.5版本的TensorFlow。</td><td>否</td></tr><tr><td>-q, --quiet</td><td>当前版本仅针对-m参数生效,代表是否进行人机交互。若不配置-q参数,则会提示用户修改获取到的模型中的首层shape信息。若配置了-q参数,则不会提示用户更改首层shape信息。</td><td>否</td></tr><tr><td>-h, --help</td><td>输出帮助信息。</td><td>否</td></tr></table>

生成/执行测试用例。 


表 5-2 生成/执行测试用例的参数说明


<table><tr><td>参数名称</td><td>参数描述</td><td>是否必选</td></tr><tr><td>run</td><td>用于执行算子的ST测试用例。</td><td>是</td></tr><tr><td>-i, --input</td><td>算子测试用例定义文件(*.json)的路径,可配置为绝对路径或者相对路径。说明json文件最多支持1000个用例。</td><td>是</td></tr><tr><td>-soc, --soc_version</td><td>配置为昇腾AI处理器的类型。说明·非Atlas A3训练系列产品/Atlas A3推理系列产品:在安装昇腾AI处理器的服务器执行npu-sminfo命令进行查询,获取Chip Name信息。实际配置值为AscendChip Name,例如Chip Name取值为xxxx,实际配置值为 Ascendxxxx。当Ascendxxxx为代码样例的路径时,需要配置为ascendxxxx。·Atlas A3训练系列产品/Atlas A3推理系列产品:在安装昇腾AI处理器的服务器执行npu-sminfo -t board -i id -c chip_id命令进行查询,获取Chip Name和NPU Name信息,实际配置值为Chip Name_NPU Name。例如Chip Name取值为Ascendxxx,NPU Name取值为1234,实际配置值为Ascendxxx_1234。当Ascendxxx_1234为代码样例的路径时,需要配置为ascendxxx_1234。其中:·id:设备id,通过npu-sminfo-l命令查出的NPU ID即为设备id。·chip_id:芯片id,通过npu-sminfo-m命令查出的Chip ID即为芯片id。</td><td>是</td></tr><tr><td>-out, --output</td><td>生成文件所在路径,可配置为绝对路径或者相对路径,并且工具执行用户具有可读写权限。若不配置该参数,则默认生成在执行命令的当前路径。</td><td>否</td></tr><tr><td>-c, --case_name</td><td>·配置为需要执行的case的名字,若需要同时运行多个case,多个case之间使用逗号分隔。·若配置为“all”,或者不配置此参数,代表执行所有case。</td><td>否</td></tr><tr><td>-d, --device_id</td><td>NPU设备ID,设置运行ST测试用例的昇腾AI处理器的ID。若未设置此参数,默认为:0。</td><td>否</td></tr><tr><td>-err_thr, --error_threshold</td><td>配置自定义精度标准，取值为含两个元素的列表："[threshold1, threshold2]”。·threshold1: 算子输出结果与标杆数据误差阈值，若误差大于该值则记为误差数据。·threshold2: 误差数据在全部数据占比阈值。若误差数据在全部数据占比小于该值，则精度达标，否则精度不达标。若未设置此参数，默认值为："[0.01,0.05]”。取值范围为："[0.0,1.0]”。说明·配置的列表需加引号以避免一些问题。例如配置为："err_thr"[0.01,0.05]”。·若测试用例json文件和执行msOpST命令时均配置该参数，以执行msOpST命令时配置的精度标准进行比对。·若均未配置，则以执行msOpST命令时默认精度标准[0.01,0.05]进行比对。</td><td>否</td></tr><tr><td>-conf, --config_file</td><td>ST测试高级功能配置文件（msopst.ini）存储路径，可配置为绝对路径或者相对路径。用户可通过修改msopst.ini配置文件，实现如下高级功能：·ST测试源码可编辑。·已编辑的ST测试源码可执行。·设置Host日志级别环境变量。·设置日志是否在控制台显示。·设置atc模型转换的日志级别。·设置atc模型转换运行环境的操作系统类型及架构。·设置模型精度。·读取算子在昇腾AI处理器上运行的性能数据。若未配置--config_file文件，模型将强制使用FP16类型精度，msopst.ini配置文件的详细说明请参见表5-6。</td><td>否</td></tr><tr><td>-err_report, --error_report</td><td>针对比对失败的用例，获取算子期望数据与实际用例执行结果不一致的数据。若未设置此参数，默认为："false"。true：针对比对失败的用例，将算子期望数据与实际用例执行结果不一致的数据保存在{case.name}-error_report.csv文件中。false：不保存比对失败的数据结果。说明设置此参数为“true”时，获取的比对数据会根据每个case_name生成独立的csv文件,{case.name}-error_report.csv文件所在目录为{output_path}/{time_stamp}//{op_type}/run/out/test_data/data/st_error_reports。单个csv文件保存数据的上限为5万行，超过则依次生成新的.csv文件，文件命名如:{case.name}-error_report0.csv。</td><td>否</td></tr><tr><td>-h, --help</td><td>输出帮助信息。</td><td>否</td></tr></table>

生成单算子上板测试框架。 


表 5-3 生成单算子上板测试框架参数说明


<table><tr><td>参数名称</td><td>参数描述</td><td>是否必选</td></tr><tr><td>ascendc_test</td><td>生成Ascend C算子调用Kernel函数的上板测试代码。</td><td>是</td></tr><tr><td>-i, --input</td><td>算子测试用例定义文件(*.json文件)的路径，可配置为绝对路径或者相对路径。
说明
·指定的算子ST测试用例定义文件(*.json文件)仅支持配置一个测试用例。
·测试用例中不支持配置多个type、format及shape。</td><td>是</td></tr><tr><td>-kernel, --kernel_file</td><td>Ascend C算子的Kernel侧实现文件(*.cpp文件)路径，可配置为绝对路径或者相对路径。</td><td>是</td></tr><tr><td>-out, --output</td><td>测试框架代码输出路径，可配置为绝对路径或者相对路径，并且工具执行用户具有可读写权限。</td><td>否</td></tr><tr><td>-h, --help</td><td>输出帮助信息。</td><td>否</td></tr></table>

# 补充说明

msOpST工具其他参数说明可参考表5-4。 


表 5-4 参数说明


<table><tr><td>参数名称</td><td>参数描述</td><td>说明</td></tr><tr><td>mi</td><td>仅供MindStudio侧使用。</td><td rowspan="7">机机接口，用户无需关注。</td></tr><tr><td>get_shape</td><td>获取shape。</td></tr><tr><td>change_shape</td><td>修改shape。</td></tr><tr><td>gen</td><td>生成acl_op.json。</td></tr><tr><td>gen_testcase</td><td>生成测试文件及数据。</td></tr><tr><td>compare</td><td>结果比对。</td></tr><tr><td>compare_by_path</td><td>指定路径文件结果比对。</td></tr><tr><td>-h, --help</td><td>输出帮助信息。</td><td>可选参数。</td></tr></table>