<!-- Source: 算子开发工具.md lines 8583-8738 | Section: 8.1 工具概述 -->

# 8.1 工具概述

msProf工具用于采集和分析运行在昇腾AI处理器上算子的关键性能指标，用户可根据 输出的性能数据，快速定位算子的软、硬件性能瓶颈，提升算子性能的分析效率。 

当前支持基于不同运行模式（上板或仿真）和不同文件形式（可执行文件或算子二进 制.o文件）进行性能数据的采集和自动解析。 

# 说明

msProf工具的使用依赖CANN包中的msopprof可执行文件，该文件中的接口使用和msprof op一 致，该文件为CANN包自带，无需单独安装。 

# 功能特性

算子调优工具使用请参考8.3 工具使用，通过MindStudio Insight展示计算内存热力 图、Roofline瓶颈分析图、Cache热力图、通算流水图（通算融合算子）、指令流水 图、算子代码热点图、内存通路吞吐率波形图以及性能数据文件等单算子调优能力， 具体请参考表8-1。 


表 8-1 msProf 工具功能特性


<table><tr><td>功能</td><td>链接</td></tr><tr><td>计算内存热力图</td><td>8.4 计算内存热力图</td></tr><tr><td>Roofline瓶颈分析图</td><td>8.5 Roofline瓶颈分析图</td></tr><tr><td>Cache热力图</td><td>8.6 Cache热力图</td></tr><tr><td>通算流水图</td><td>8.7 通算流水图</td></tr><tr><td>指令流水图</td><td>8.8 指令流水图</td></tr><tr><td>算子代码热点图</td><td>8.9 算子代码热点图</td></tr><tr><td>内存通路吞吐率波形图</td><td>8.10 内存通路吞吐率波形图</td></tr><tr><td>性能数据文件</td><td>8.11 性能数据文件</td></tr></table>

# 说明

● 通过键盘输入“CTRL+C”后，算子执行将会被停止，工具会根据当前已有信息生成性能数 据文件。若不需要生成该文件，可再次键盘输入“CTRL+C”指令。 

● 若未指定--output参数，默认保存为当前工具执行的路径，需确保群组和其他组的用户不具 备当前路径的上一级目录的写入权限。 

# 命令汇总

# 说明

用户需自行保证可执行文件或用户程序（application）执行的安全性。 

建议限制对可执行文件或用户程序（application）的操作权限，避免提权风险。 

不建议进行高危操作（删除文件、删除目录、修改密码及提权命令等），避免安全风险。 

# msprof op模式

登录运行环境，使用msprof op 可选参数 app [arguments]格式调用，可选参数 的具体情况请参考表8-2。具体命令示例如下： 

msprof op --output=$HOME/projects/output $HOME/projects/MyApp/out/main blockdim 1 // -- output为可选参数,$HOME/projects/MyApp/out/main为使用的app,blockdim1为用户app的可选参数， xxxyy为用户实际使用的具体芯片类型 


表 8-2 msprof op 可选参数表


<table><tr><td>可选参数</td><td>描述</td><td>是否必选</td></tr><tr><td>--application说明当前与./app[arguments]兼容,后期将修改为./app[arguments]。</td><td>建议使用msprof op [msprof op参数]./app进行拉取,其中app为指定的可执行文件,如果app未指定路径,默认为使用当前路径。说明使用./app时,需将msprof op的相关参数添加到./app前,以确保相关功能生效。</td><td rowspan="2">是,指定的可执行文件和--config二选一</td></tr><tr><td>--config</td><td>配置为输入算子编译得到的二进制文件*.o,可配置为绝对路径或者相对路径。具体可参考8.12 Json配置文件说明。说明进行算子调优之前,可通过以下两种方式获取算子二进制*.o文件。·参考《Ascend C算子开发指南》中的“Kernel直调算子开发 &gt; Kernel直调 &gt; 修改并执行一键式编译运行脚本”章节,获取NPU侧可执行文件,并需要用户自行从可执行文件中提取*.o文件。·参考4.5算子编译部署,算子编译时会自动生成*.o文件。·需确保群组和其他组的用户不具备--config指定的json文件及上一级目录的写入权限。同时,需要确保json文件的上一级目录属主为当前用户。</td></tr><tr><td>--kernel-name</td><td>指定要采集的算子名称,支持使用算子名前缀进行模糊匹配。如果不指定,则只对程序运行过程中调度的第一个算子进行采集。说明·需与--application配合使用,限制长度为1024,仅支持A-Za-z0-9中的一个或多个字符。·需要采集多个算子时,支持使用符号"|"进行拼接。例如,--kernel-name="add|abs"表示采集前缀名为add和abs的算子。·具体采集的算子数量由--launch-count参数值决定。</td><td>否</td></tr><tr><td>--launch-count</td><td>设置可以采集算子的最大数量,默认值为1,取值范围为1~100之间的整数。</td><td>否</td></tr><tr><td>--launch-skip-before-match</td><td>用于设置不需要采集数据的算子数量,从第一个算子开始到指定数目的算子不进行采集,仅对指定数目之后的算子开始采集。说明·无论--launch-skip-before-match参数是否命中kernel-name中指定的算子,该项的计数都会增加,且不采集该算子。·此参数的取值范围为0~1000之间的整数。</td><td>否</td></tr><tr><td>--aic-metrics</td><td>使能算子性能指标的采集能力和算子采集能力指标。·使能算子性能指标的采集能力（ArithmeticUtilization、L2Cache、Memory、MemoryL0、MemoryUB、PipeUtilization、ResourceConflictRatio和Default），可选其中的一项或多项性能指标，选多项时用英文逗号隔开，例如：--aic-metrics=Memory,MemoryL0。·默认使能Default，采集以下性能指标（ArithmeticUtilization、L2Cache、Memory、MemoryL0、MemoryUB、PipeUtilization、ResourceConflictRatio）。例如：--aic-metrics=Default。·使能算子Kernel侧指定代码段范围内的性能指标采集（KernelScale）。KernelScale可对算子Kernel侧指定代码段范围进行调优。需先配置--aic-metrics=KernelScale，然后选其中的一项或多项算子性能指标，选多项时用英文逗号隔开，例如：--aic-metrics=KernelScale,Memory,MemoryL0。默认选择全部算子性能指标进行采集，例如：--aic-metrics=KernelScale。说明·指定代码段范围时，需要在算子Kernel侧对应的代码段前后进行设置，具体设置请参见《Ascend C算子开发接口》的MetricsProfStart和MetricsProfStop接口。·仅Atlas A2训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组件和Atlas A3训练系列产品/Atlas A3 推理系列产品支持该功能。·Roofline：使能生成Roofline瓶颈分析图，并通过MindStudio Insight进行可视化呈现，例如：--aic-metrics=Roofline。具体请参见8.5 Roofline瓶颈分析图。·TimelineDetail：使能生成计算内存热力图、指令流水图和算子代码热点图，进行可视化呈现，例如：--aic-metrics=TimelineDetail。具体呈现内容请参见8.4 计算内存热力图、8.8 指令流水图和8.9 算子代码热点图。</td><td>否</td></tr><tr><td></td><td>说明
·若要使能此功能,需要参考msprof op simulator配置进行配置。
·此功能不支持采集二级指针类算子及通算类算子。
·仅Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组件和Atlas A3 训练系列产品/Atlas A3 推理系列产品支持该功能。
·此功能仅支持第三方框架算子调用: PyTorch 框架的场景且内部使用单算子API方式调起算子的场景。
·不支持与--replay-mode=application同时使能。
·若要生成csv文件,拉起算子时,需使能 Default,示例如下:
msprof op --aic-metrics=TimelineDetail,Default</td><td></td></tr><tr><td></td><td>·Occupancy:使能生成核间负载分析图,并通过MindStudio Insight进行可视化呈现,例如:--aic-metrics=Occupancy。具体请参见核间负载分析图。各物理核之间,会针对耗时、数据吞吐量及Cache命中率分别进行对比,若最大值和最小值的差距大于10%,则说明负载不均衡,命令行界面会给出相应的调优建议。
·MemoryDetail:使能该命令后,L2 Cache相关功能(计算内存热力图中的L2 Cache-LOA/LOB连线、Cache热力图、算子代码热点图中的L2Cache命中率以及与GM有关的数据搬运量)会开启。例如:--aic-metrics=MemoryDetail。
·不支持与--replay-mode=application同时使能。
·仅Atlas A3 训练系列产品/Atlas A3 推理系列产品和Atlas A2 训练系列产品/Atlas 800I A2推理产品/A200I A2 Box 异构组件支持该功能。
·Source:使能算子代码热点图。</td><td></td></tr><tr><td></td><td>说明
·仅Atlas A3 训练系列产品/Atlas A3 推理系列产品和Atlas A2 训练系列产品/Atlas 800I A2推理产品/A200I A2 Box 异构组件支持该功能。
·若需要查看代码调用栈,需在编译算子时添加-g编译选项,具体操作请参见编译选项需添加-g。</td><td></td></tr><tr><td>--kill</td><td>选项包括开启(on)和关闭(off),默认情况下设置为关闭(off),关闭该功能。
若用户配置--kill=on使能该功能,用户程序将会在采集完--launch-count设置的算子数量后,自动停止程序。
说明
·配置--kill=on后,可能会出现因用户程序提前结束而引发的错误日志,用户需自行评估是否使用该功能。
·若用户程序为多进程,--kill参数的配置只对子进程生效。
·使用该参数会造成最后一个被执行的通算融合算子无法正常获取接口调用流水,具体请参见8.7通算流水图。</td><td>否</td></tr><tr><td>--mstx</td><td>该参数决定算子调优工具是否使能用户代码程序中使用的mstx API。
默认为off,表示关闭对mstx API的使能。
若用户配置--mstx=on,算子调优工具将会使能用户代码程序中使用的mstx API。
具体举例如下:
msprof op --mstx=on ./addcustom
说明
当前已支持mstx API中的mstxRangeStartA和mstxRangeEnd接口,功能为使能算子调优的指定区间,具体参数介绍请参见mstxRangeStartA和mstxRangeEnd接口。</td><td>否</td></tr><tr><td>--mstx-include</td><td>该参数支持在算子调优工具使能mstx API的情况下,仅使能用户指定mstx API若不配置,则默认使能所有用户代码中使用的mstx API。若配置,--mstx-include只使能用户指定的mstx API。--mstx-include的输入为用户调用mstx函数时传入的消息字符串,使用"|"拼接多个字符串。具体举例如下:--mstx=on --mstx-include="hello|hi" //仅使能用户传入mstx函数中message参数为hello和hi的mstx API说明·不可单独配置,需要与--mstx配合使用。·仅支持message为A-Z a-z 0-9_这些字符,使用"|"进行拼接。</td><td>否</td></tr><tr><td>--replay-mode</td><td>算子数据采集的重放模式,可配置为kernel或application,默认为kernel。·若配置为application,则代表是应用级重放。·若配置为kernel,则代表是核函数级重放。说明多卡多算子的场景不支持配置为application。</td><td>否</td></tr><tr><td>--warm-up</td><td>当部分算子使用msprof op采集时,会达不到芯片提频的最小任务耗时产生降频,从而会对交付件的结果产生一定影响。在该情况下,可用--warm-up指定预热次数,提前提升昇腾AI处理器的运行频率,使上板数据更准确。说明·默认值为5,取值范围为[0,500]。·此参数对MC2算子不生效。·此参数不适用于--replay-mode=application模式。</td><td>否</td></tr><tr><td>--output</td><td>收集到的性能数据的存放路径,默认在当前目录下保存性能数据。说明需确保群组和其他组的用户不具备--output指定输出路径的上一级目录的写入权限。同时,需要确保--output指定目录的上一级目录属主为当前用户。</td><td>否</td></tr><tr><td>--dump</td><td>控制仿真器dump文件是否生成。选项包括开启(on)和关闭(off),默认情况下设置为关闭(off),即不生成仿真器dump文件。说明此参数仅在使用--aic-metrics=TimelineDetail选项时有效,且仅针对Atlas A2 训练系列产品/Atlas800I A2 推理产品/A200I A2 Box 异构组件及Atlas A3 训练系列产品/Atlas A3 推理系列产品生效,对Atlas 推理系列产品不生效。此参数仅适用于单进程场景,不支持两个算子同时运行的场景。</td><td>否</td></tr><tr><td>--core-id</td><td>该参数适用于算子分布均匀的情况时,可使用--core-id参数指定部分逻辑核的id,解析部分核的仿真数据。核id的取值范围为[0,49]。说明若要解析多个核的仿真数据时,需要使用符号"|"进行拼接。例如,--core-id="0|31"表示解析核id为0和31的仿真数据。此参数仅在使用--aic-metrics=TimelineDetail选项时有效,仅作用于8.8指令流水图和8.9算子代码热点图,仅适用于Atlas A2 训练系列产品/Atlas800I A2 推理产品/A200I A2 Box 异构组件及Atlas A3 训练系列产品/Atlas A3 推理系列产品。</td><td>否</td></tr><tr><td>-h, --help</td><td>输出帮助信息。</td><td>否</td></tr></table>

msprof op simulator模式 

登录运行环境，使用msprof op simulator开启算子仿真调优功能，并配合使用仿 真可选参数和用户待调优程序（blockdim 1）进行调优，仿真可选参数请参考表 8-3。具体命令示例如下： 

msprof op simulator --soc-version=Ascendxxxyy --output=/home/projects/output /home/projects/ MyApp/out/main blockdim 1 // --output为可选参数,/home/projects/MyApp/out/main为使用的 app,blockdim 1为用户app的可选参数，xxxyy为用户实际使用的具体芯片类型 


表 8-3 msprof op simulator 可选参数说明


<table><tr><td>可选参数</td><td>描述</td><td>是否必选</td></tr><tr><td>--application说明当前与./app[arguments]兼容,后期将修改为./app[arguments]。</td><td>建议使用msprof op simulator --soc-version=Ascendxxxyy [msprof op simulator参数]./app进行拉取,其中app为用户指定的可执行文件,如果app未指定路径,默认为使用当前路径。说明使用./app时,需将msprof op simulator的相关参数添加到./app前,以确保相关功能生效。</td><td rowspan="3">是,指定的可执行文件、--config和--export三选一</td></tr><tr><td>--config</td><td>配置为算子编译得到的二进制文件*.o,可配置为绝对路径或者相对路径。具体可参考8.12 Json配置文件说明。说明进行算子调优之前,可通过以下两种方式获取算子二进制*.o文件。·参考《Ascend C算子开发指南》中的“Kernel直调算子开发 &gt; Kernel直调 &gt; 修改并执行一键式编译运行脚本”章节,获取NPU侧可执行文件,并需要用户自行从可执行文件中提取*.o文件。·参考4.5算子编译部署,算子编译时会自动生成*.o文件。·需确保群组和其他组的用户不具备--config指定的json文件及上一级目录的写入权限。同时,需要确保json文件的上一级目录属主为当前用户。·需要使用LD.Library_PATH环境变量设置仿真器类型。exportLD.Library_PATH=${\INSTALL_DIR}/tools/simulator/Ascendxxxxy/lib:$LD.Library_PATH // xxxxy为用户实际使用的具体芯片类型</td></tr><tr><td>--export</td><td>指定包含单算子仿真结果文件夹,直接对该仿真结果进行解析,并通过MindStudio Insight展示单算子单核或多核的指令流水图。说明·该指定文件夹只允许存放多核数据及算子核函数文件aicore_binary.o,所以需要将--config中配置的二进制文件名称(*.o)手动修改为aicore_binary.o。·若用户仅提供dump文件,则指令流水图中将无法生成代码行映射,如需查看代码行,则需要在dump中存放aicore_binary.o名称的算子核函数文件。·需确保群组和其他组的用户不具备--export指定目录以及--export指定目录内所有文件的写入权限。同时,需要确保指定目录属主为当前用户。</td></tr><tr><td>--kernel-name</td><td>指定要采集的算子名称,支持使用算子名前缀进行模糊匹配。如果不指定,则只对程序运行过程中调度的第一个算子进行采集。说明·需与--application配合使用,限制长度为1024,仅支持A-Za-z0-9中的一个或多个字符。·需要采集多个算子时,支持使用符号'|"进行拼接。例如,--kernel-name="add|abs"表示采集前缀名为add和abs的算子。·具体采集的算子数量由--launch-count参数值决定。</td><td>否</td></tr><tr><td>--launch-count</td><td>设置可以采集算子的最大数量,默认值为1,取值范围为1~100之间的整数。</td><td>否</td></tr><tr><td>--aic-metrics</td><td>使能算子性能指标采集。支持以下性能指标采集项。·PipeUtilization(默认采集)说明·PipeUtilization为计算单元和搬运单元指令耗时占比,且为必选项。例如:--aic-metrics=PipeUtilization。·当配置--aic-metrics=PipeUtilization时,关闭ResourceConflictRatio。·ResourceConflictRatio(默认采集)说明·ResourceConflictRatio为资源冲突占比,支持展示SET_FLAG/WAIT_FLAG指令,且仅适用于Atlas A2训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box异构组件。·ResourceConflictRatio为资源冲突占比。·Atlas A3训练系列产品/Atlas A3 推理系列产品和Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组件展示为SET_FLAG/WAIT_FLAG指令。·Atlas 推理系列产品展示为set_event/wait_event指令。·PMSampling:使能内存通路吞吐率波形图,并进行可视化呈现,例如:--aic-metrics=PMSampling。具体呈现内容请参见8.10内存通路吞吐率波形图。说明·--core-id设置对PMSampling参数不生效,PMSampling参数解析全部核。·此功能默认不开启。</td><td>否</td></tr><tr><td>--core-id</td><td>该参数适用于算子分布均匀的情况时,可使用--core-id参数指定部分逻辑核的id,解析部分核的仿真数据。核id的取值范围为[0,49]。说明·若要解析多个核的仿真数据时,需要使用符号"|"进行拼接。例如,--core-id="0|31"表示解析核id为0和31的仿真数据。·--core-id设置对PMSampling参数不生效,PMSampling参数解析全部核。</td><td>否</td></tr><tr><td>--timeout</td><td>该参数适用于数据量大且计算重复的算子,完整运行该类算子将会耗时很长,部分流水图即可获取必要信息。可通过设置--timeout参数缩短算子运行时长并获取必要流水信息。具体实现如下:·当仿真运行时间达到--timeout值时,msProf工具将会终止仿真进程并进入解析过程,只对已仿真的部分数据进行分析。同时,msProf工具将会展示以下打屏信息:[INFO] The timeout has reached and the application will be forcibly killed.·若进程正常结束时未达到timeout值时,正常结束仿真程序并进入解析过程。参数取值范围为1~2880之间的整数,单位分钟。具体示例如下:msprof op simulator --soc-version=Ascendxxxxy --timeout=1 ./add_custom// xxxxy为用户实际使用的具体芯片类型</td><td>否</td></tr><tr><td>--mstx</td><td>该参数决定算子调优工具是否使能用户代码程序中使用的mstx API。默认为off,表示关闭对mstx API的使能。当配置--mstx=on,算子调优工具将会使能用户代码程序中使用的mstx API。具体举例如下:msprof op simulator --soc-version=Ascendxxxxy --mstx=on ./add_custom // xxxxy为用户实际使用的具体芯片类型说明当前已支持mstx API中的mstxRangeStartA和mstxRangeEnd接口,功能为使能算子调优的指定区间,具体参数介绍请参见mstxRangeStartA和mstxRangeEnd接口。</td><td>否</td></tr><tr><td>--mstx-include</td><td>该参数支持在msProf工具使能用户指定mstx API。若不配置,则默认使能所有用户代码中使用的mstx API。若配置,--mstx-include仅使能用户指定的mstx API。--mstx-include的输入为用户调用mstx函数时传入的message字符串,多个字符串需使用"|"拼接。具体举例如下:--mstx=on --mstx-include="hello|hi" //仅使能用户传入mstx函数中message参数为hello和hi的mstx API说明·不可单独配置,需要与--mstx配合使用。·仅支持message为A-Z a-z 0-9_这些字符,使用"|"进行拼接。</td><td>否</td></tr><tr><td>--soc-version</td><td>可以通过--soc-version或设置LD librARY_PATH环境变量来指定仿真器类型,两者必须二选一,具体介绍如下:·--soc-version:用于在--application和--export模式下指定仿真器类型,选取范围可参考${INSTALL_DIR}/tools/simulator路径下的仿真器类型。·设置LD librARY_PATH环境变量:用于在--config的模式下或未使用--soc-version的情况下指定仿真器的类型。export LD librARY_PATH=$${INSTALL_DIR}/tools/simulator/Ascendxxxxy/lib:$LD librARY_PATH说明${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。若安装的Ascend-cann-toolkit软件包,以root安装举例,则安装后文件存储路径为:/usr/local/Ascend/ascend-toolkit/latest。</td><td>否</td></tr><tr><td>--output</td><td>收集到的性能数据的存放路径,默认在当前目录下保存性能数据。说明需确保群组和其他组的用户不具备--output指定输出路径的上一级目录的写入权限。同时,需要确保--output指定目录的上一级目录属主为当前用户。</td><td>否</td></tr><tr><td>--dump</td><td>控制仿真器dump文件是否生成。选项包括开启（on）和关闭（off），默认情况下设置为关闭（off），即不生成仿真器dump文件。说明·此参数仅对Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组件及Atlas A3 训练系列产品/Atlas A3 推理系列产品生效。对Atlas 推理系列产品不生效，dump文件会按照正常流程落盘。·此参数仅适用于单进程场景，不支持两个算子同时运行的场景。</td><td>否</td></tr><tr><td>-h，--help</td><td>输出帮助信息。</td><td>否</td></tr></table>

# msprof op 分段调优原则

步骤1 使用--launch-skip-before-match命令筛选算子调优范围，筛选原则如下： 

若已配置--launch-skip-before-match，从第一个算子开始到指定数目的算子不进 行采集，仅对指定数目之后的算子开始采集。 

若未配置，不进行筛选。 

步骤2 在步骤一的基础上，使用--mstx命令筛选算子调优范围，筛选原则如下： 

若已配置--mstx，只采集mstxRangeStartA和mstxRangeEnd接口使能范围内的算 子。 

若未配置，不进行筛选。 

步骤3 在步骤二的基础上，使用--kernel-name命令筛选算子调优范围，筛选原则如下： 

若已配置--kernel-name，只采集--kernel-name范围内的算子。 

若未配置--kernel-name，则只对程序运行过程中调度的第一个算子进行采集。 

步骤4 在步骤三的基础上，使用--aic-metrics命令筛选算子调优数据的采集项，筛选原则如 下： 

若已配置--aic-metrics，选择算子性能指标的采集项。 

若未配置--aic-metrics，默认采集Default部分的算子性能指标，KernelScale、 TimelineDetail、Roofline、Occupancy部分的算子性能指标将无法采集。 

步骤5 通过步骤一至步骤四逐层过滤，可获得实际的调优算子数量以及性能指标的采集范 围。 

步骤6 使能--kill=on功能的情况下，将实际调优的算子数量与--launch-count值进行对比，从 而决定是否需要自动停止程序。 

若实际已调优算子数量小于等于--launch-count值，则继续执行。否则，实际已调优算 子数量达到--launch-count设置的算子数值时，会自动停止程序。 

----结束 

# 调用场景

支持如下调用算子的场景，具体操作请参见8.13.1 采集Ascend C算子的性能数据和 8.13.3 采集MC2算子的性能数据。 

Kernel直调算子开发：Kernel直调。 

# 说明

Kernel直调场景，详细信息可参考《Ascend C算子开发指南》中“Kernel直调算子开 发”章节。 

Kernel直调的场景，需先配置好前置条件，然后执行以下命令： msprof op simulator --soc-version=Ascendxxxyy ./main // main为用户算子程序名称，包含待 调优算子的程序名，xxxyy为用户实际使用的具体芯片类型 

● 可选: 若算子已在上板运行模式下，但用户又需要在不重新编译的情况下，对其进行仿 真调优，可通过以下操作步骤实现。 

在任意目录下，创建一个指向libruntime_camodel.so的软连接，名称为 libruntime.so。 ln -s /{simulator_path}/lib/libruntime_camodel.so /{so path}/libruntime.so //例如,若使 用root用户默认路径安装CANN包,simulator_path为/usr/local/Ascend/ascend-toolkit/ latest/tools/simulator/Ascendxxxyy 

将创建的软链接的父目录加入到环境变量LD_LIBRARY_PATH中。 export LD_LIBRARY_PATH={so path}:$LD_LIBRARY_PATH 

工程化算子开发：单算子API调用。 

# 说明

● 单算子API调用的场景，可参考《Ascend C算子开发指南》中“工程化算子开发 $>$ 单算 子API调用”章节。 

● 单算子API执行的场景，需先配置好前置条件，然后执行以下命令： msprof op simulator --soc-version=Ascendxxxyy ./main // main为用户算子程序名称,包含待调 优算子的程序名，xxxyy为用户实际使用的具体芯片类型 

AI框架算子适配：PyTorch框架。 

# 说明

● 在Atlas 推理系列产品上使用msProf工具对PyTorch脚本的算子进行仿真调优时，仅支 持基于Kernels算子包调用方式。用户需参考《CANN 软件安装指南》中的“安装 CANN（物理机场景）> 安装CANN软件包 > 安装Kernels算子包”章节安装二进制 Kernels算子包，并修改脚本入口文件例如main.py文件，在import torch_npu下方添加 加粗字体信息，以确保使用的是Kernels算子包中算子。 

import torch import torch_npu torch_npu.npu.set_compile_mode(jit_compile=False) 

● 通过PyTorch框架进行单算子调用的场景，详细信息可参考《Ascend Extension for PyTorch 套件与三方库支持清单》中“昇腾自研插件 > 单算子适配OpPlugin插件开 发”章节。 

● 通过PyTorch框架进行单算子调用的场景，需先配置好前置条件，然后执行以下命令： msprof op simulator --soc-version=Ascendxxxyy python a.py // a.py为用户算子程序名称,包含 待调优算子的程序名，xxxyy为用户实际使用的具体芯片类型