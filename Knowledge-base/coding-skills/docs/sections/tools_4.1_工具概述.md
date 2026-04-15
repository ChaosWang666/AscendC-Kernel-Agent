<!-- Source: 算子开发工具.md lines 3739-3820 | Section: 4.1 工具概述 -->

# 4.1 工具概述

# 工具概述

完成算子分析&原型定义后，可使用msOpGen工具生成自定义算子工程，并进行编译 部署，具体流程请参考图4-1。 

# 说明

在TBE及AI CPU算子开发场景中，msOpGen工具的使用详情请参考9.1.1 基于msOpGen工具创 建算子工程及9.1.2 算子编译部署。 

具有如下功能： 

基于算子原型定义输出算子工程。 

基于性能仿真环境生成的dump数据文件输出算子仿真流水图文件。 


图 4-1 msOpGen 工具使用流程介绍


![](images/116eadb96abeb8deb98120d3752ecf30ff0444fac25e13b492085b20695159dc.jpg)


# 工具特性

msOpGen目前已支持的功能如下：包括算子工程创建、算子实现（Host侧&Kernel 侧）、算子工程编译部署以及解析算子仿真流水图文件等。 


表 4-1 msOpGen 工具功能


<table><tr><td>功能</td><td>链接</td></tr><tr><td>算子工程创建</td><td>4.3 创建算子工程</td></tr><tr><td>算子实现（Host侧&amp;Kernel侧）</td><td>4.4 算子开发</td></tr><tr><td>算子工程编译部署</td><td>4.5 算子编译部署</td></tr><tr><td>解析算子仿真流水图文件</td><td>4.6 查看算子仿真流水图</td></tr></table>

# 命令汇总

执行如下命令，参数说明请参见表4-2。 

# 说明

用户按照输入的配置参数生成算子模板后，建议在运行前确认算子工程代码的安全性。 

msopgen gen -i $\{^{*}j$ o n] -f {framework type}-c {Compute Resource}-lan cpp -out {Output Path} 


表 4-2 创建算子工程参数说明


<table><tr><td>参数名称</td><td>参数描述</td><td>是否必选</td></tr><tr><td>gen</td><td>用于生成算子开发交付件。</td><td>是</td></tr><tr><td>-i, --input</td><td>算子原型定义文件 (.json) 路径，可配置为绝对路径或者相对路径。工具执行用户需要有此路径的可读权限。</td><td>是</td></tr><tr><td>-f, --framework</td><td>框架类型。
·默认为TensorFlow框架，默认值：tf或者tensorflow
·Caffe框架，参数值：caffe
 说明
   自定义Ascend C算子不支持Caffe框架。
·PyTorch框架，参数值：pytorch
·MindSpore框架，参数值：ms或mindspore
·ONNX框架，参数值：onnx
说明
·所有参数值大小写不敏感。
·TBE&amp;TIK不支持单算子API调用，默认生成TensorFlow框架。
·Ascend C算子工程支持TensorFlow框架、PyTorch框架和单算子API调用，默认生成TensorFlow框架。
·当用户使用-f aclnn时，生成Ascend C简易算子工程，否则保持原功能特性生成。</td><td>否</td></tr><tr><td>-lan, --language</td><td>算子编码语言。
·cpp: 基于Ascend C编程框架，使用C/C++编程语言进行开发。
·py: 基于DSL和TIK算子编程框架，使用Python编程语言进行开发。
默认值：py。
说明
cpp仅适用于Ascend C算子开发场景。</td><td>否</td></tr><tr><td>-c, --compute_unit</td><td>·算子使用的计算资源。配置格式为:ai_core-{soc version},ai_core与{socversion}之间用中划线“-”连接。请根据实际昇腾AI处理器版本进行选择。说明AI处理器的型号&lt;soc_version&gt;请通过如下方式获取:·非Atlas A3训练系列产品/Atlas A3推理系列产品:在安装昇腾AI处理器的服务器执行npu-sminfo命令进行查询,获取Chip Name信息。实际配置值为AscendChip Name,例如Chip Name取值为xxxx,实际配置值为Ascendxxxx。当Ascendxxxx为代码样例的路径时,需要配置ascendxxxx。·Atlas A3训练系列产品/Atlas A3推理系列产品:在安装昇腾AI处理器的服务器执行npu-sminfo-t board-id-cchip_id命令进行查询,获取Chip Name和NPU Name信息,实际配置值为Chip Name_NPU Name。例如Chip Name取值为Ascendxxx,NPU Name取值为1234,实际配置值为Ascendxxx_1234。当Ascendxxx_1234为代码样例的路径时,需要配置ascendxxx_1234。其中:·id:设备id,通过npu-sminfo-l命令查出的NPU ID即为设备id。·chip_id:芯片id,通过npu-sminfo-m命令查出的Chip ID即为芯片id。基于同系列的AI处理器型号创建的算子工程,其基础功能(基于该工程进行算子开发、编译和部署)通用。·针对AI CPU算子,请配置为:aicpu。说明在Atlas A3训练系列产品/Atlas A3推理系列产品场景下,请勿在编译时使用以下编译选项,否则会导致机器异常。·-march=armv8-a+lse·-march=armv8.1-a·-march=armv8.2-a·-march=armv8.3-a</td><td>是</td></tr><tr><td>-out, --output</td><td>生成文件所在路径,可配置为绝对路径或者相对路径,并且工具执行用户具有可读写权限。若不配置,则默认生成在执行命令的当前路径。说明若用户指定的输出目录中存在与模板工程重名的文件,输出目录中的文件将会被模板工程的文件覆盖。</td><td>否</td></tr><tr><td>-m, --mode</td><td>生成交付件模式。·0:创建新的算子工程,若指定的路径下已存在算子工程,则会报错退出。·1:在已有的算子工程中追加算子。默认值:0。</td><td>否</td></tr><tr><td>-op, --operator</td><td>配置算子的类型，如：Conv2DTik。若不配置此参数，当算子原型定义文件中存在多个算子时，工具会提示用户选择算子。</td><td>否</td></tr><tr><td>-h, --help</td><td>输出帮助信息。</td><td>否</td></tr></table>

# 补充说明

msOpGen工具其他参数说明可参考表4-3和表4-4。 


表 4-3 mi 参数说明


<table><tr><td>参数名称</td><td>参数描述</td><td>说明</td></tr><tr><td>mi</td><td>仅供MindStudio侧使用。</td><td rowspan="2">机机接口，用户无需关注。</td></tr><tr><td>query</td><td>基于原型定义文件生成 json时，存放sheet所有 op。</td></tr><tr><td>-h，--help</td><td>输出帮助信息。</td><td>可选参数。</td></tr></table>


表 4-4 compile 参数说明


<table><tr><td>参数名称</td><td>参数描述</td><td>说明</td></tr><tr><td>compile</td><td>编译TBE&amp;AI CPU算子工程时使用。</td><td>具体请参见《TBE&amp;AI CPU算子开发指南》中“算子编译部署 &gt; 算子交付件独立编译”章节。</td></tr></table>