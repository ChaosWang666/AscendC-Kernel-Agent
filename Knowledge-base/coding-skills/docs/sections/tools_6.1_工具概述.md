<!-- Source: 算子开发工具.md lines 5337-5454 | Section: 6.1 工具概述 -->

# 6.1 工具概述

msSanitizer工具是基于昇腾AI处理器的一个异常检测工具，包含了单算子开发场景下 的内存检测、竞争检测和未初始化检测三个子功能。用户使用msOpST工具在真实的 硬件环境中对算子的功能进行测试后，可根据实际测试情况选择是否使用msSanitizer 工具进行异常检测。 

内存检测：工具可以在用户开发算子的过程中，协助定位非法读写、多核踩踏、 非对齐访问、内存泄漏以及非法释放等内存问题。同时工具也支持对CANN软件 栈的内存检测，帮助用户定界软件栈内存异常发生的模块。 

竞争检测：工具可以协助用户定位由于竞争风险可能导致的数据竞争问题，包含 核内竞争和核间竞争问题。其中，核内竞争包含流水间竞争和流水内竞争。 

未初始化检测：工具可以协助用户定位由于内存未初始化可能导致的脏数据读取 问题。 

# 说明

msSanitizer工具不支持对多线程算子及使用了掩码的向量类计算指令进行检测。 

# 工具特性

msSanitizer通过不同子功能提供了不同类型的异常检测功能，目前已支持的功能如 下： 


表 6-1 msSanitizer 工具功能


<table><tr><td>使用场景</td><td>使用说明</td><td>使用示例</td></tr><tr><td>算子内存检测</td><td>6.3 内存检测</td><td rowspan="2">·msSanitizer支持内核调用符调用的Ascend C 算子(包括Vector、Cube算子和Mix融合算 子)内存和竞争的检测,可参考6.3 内存检 测。 ·msSanitizer支持对单算子API调用的Ascend C算子(包括Vector、Cube算子和Mix融合 算子)内存和竞争的检测,可参考6.4 竞争 检测。</td></tr><tr><td>算子竞争检测</td><td>6.4 竞争检测</td></tr><tr><td>算子未初始化检测</td><td>6.5 未初始化 检测</td><td>msSanitizer支持Ascend CL调用的Ascend C算 子(包括Vector、Cube算子和Mix融合算子) 未初始化的检测,可参考6.5 未初始化检测。</td></tr><tr><td>CANN软件栈的内存检测</td><td>6.3 内存检测</td><td>支持CANN软件栈内存检测,详细可参考6.6.4 检测CANN软件栈的内存。</td></tr></table>

# 命令汇总

可以通过运行以下命令来调用msSanitizer工具。 

```xml
mssanitizer <options> -- <user_program> <user_options> 
```

# 说明

options为检测工具的命令行选项，详细的参数选项及其默认值，请参考表6-2和表6-3， user_program为用户算子程序，user_options为用户程序的命令行选项。 

● 如要加载的可执行文件或用户自定义程序本身带有命令行参数时，在可执行文件或用户程序 （application）之前使用“--”分隔检测工具和用户命令。 mssanitizer -- application parameter1 parameter2 ... 

● 用户需保证可执行文件及用户自定义程序的安全性。 

● 用户需自行保证可执行文件或用户程序（application）执行的安全性。 

建议限制对可执行文件或用户程序（application）的操作权限，避免提权风险。 

不建议进行高危操作（删除文件、删除目录、修改密码及提权命令等），避免安全风 险。 


表6-2 通用参数说明


<table><tr><td>参数名称</td><td>参数描述</td><td>参数取值</td><td>是否必选</td></tr><tr><td>-v, --version</td><td>查询msSanitizer工具版本。</td><td>-</td><td>否</td></tr><tr><td>-t, --tool</td><td>指定异常检测的子工具。</td><td>·memcheck: 内存检测 (默认) 
·racecheck: 竞争检测 
·initcheck: 未初始化检测</td><td>否</td></tr><tr><td>--log-file</td><td>指定检测报告输出到文件。</td><td>{file_name},如配置为test_log。说明仅支持数字、大小写字母和-./_四种符号。为避免日志泄漏风险,建议限制该文件权限,确保只有授权人员才能访问该文件。工具会以覆盖的方式将报告输出到test_log文件。若test_log文件中已有内容,这些内容将会被清空。因此,建议指定一个空文件用于输出报告。</td><td>否</td></tr><tr><td>--log-level</td><td>指定检测报告输出等级。</td><td>info:输出info/warn-error级别的运行信息。warn:输出warn-error级别的运行信息(默认)。error:输出error级别的运行信息。</td><td>否</td></tr><tr><td>--max-debuglog-size</td><td>指定检测工具调试输出日志中单个文件大小的上限。</td><td>可设定范围为1~10240之间的整数,单位为MB。默认值为1024。说明--max-debuglog-size=100就表示单个调试日志的大小上限为100MB。</td><td>否</td></tr><tr><td>--block-id</td><td>是否启用单block检测功能。</td><td>可设定范围为0~200之间的整数。启用前内存检测和未初始化检测:默认检测所有block。竞争检测:核间默认检测所有block,核内默认检测block 0的流水内及流水间的竞争。启用后内存检测和未初始化检测:检测指定block。竞争检测:核间不进行检测,检测指定block的流水内及流水间的竞争。</td><td>否</td></tr><tr><td>--cache-size</td><td>表示单block的GM内存大小。</td><td>单block可设定范围为1~8192之间的整数，单位为MB。单block默认值为100MB，表示单block可申请100MB的内存大小。说明
·启用单block检测时，--cache-size的最大值为8192MB。不启用单block检测时，--cache-size可设置的最大值为(24*1024 / block数量)。
·当--cache-size值不满足需求时，异常检测工具将会打屏提示用户重新设置--cache-size值，具体请参见6.7.3msSanitizer工具提示--cache-size异常。</td><td>否</td></tr><tr><td>--kernel-name</td><td>指定要检测的算子名称。</td><td>支持使用算子名中的部分字符串来进行模糊匹配。如果不指定，则系统默认会对整个程序执行期间所调度的所有算子进行检测。例如，需要同时检测名为"abcd"和"bcd"的算子时，可以通过配置--kernel-name="bc"来实现这一需求，系统会自动识别并检测所有包含"bc"字符串的算子。</td><td>否</td></tr><tr><td>-h, --help</td><td>输出帮助信息。</td><td>-</td><td>否</td></tr></table>


表 6-3 内存检测参数说明


<table><tr><td>参数名称</td><td>参数描述</td><td>参数取值</td><td>是否必选</td></tr><tr><td>--check-unused-memory</td><td>使能分配内存未使用检测。</td><td>·yes
·no（默认）</td><td>否</td></tr><tr><td>--leak-check</td><td>使能内存泄漏检测。</td><td>·yes
·no（默认）</td><td>否</td></tr><tr><td>--check-device-heap</td><td>使能Device侧内存检测。</td><td>·yes
·no（默认）</td><td>否</td></tr><tr><td>--check-cann-heap</td><td>使能CANN软件栈内存检测。</td><td>·yes
·no（默认）</td><td>否</td></tr></table>

# 说明

● --check-device-heap或--check-cann-heap使能后，将不会对Kernel内进行检测。 

Device侧内存检测和CANN软件栈内存检测不能同时使能，若同时使能会提示“CANNOT enable both --check-cann-heap and --check-device-heap” 。 

● 使用msSanitizer工具提供的API头文件重新编译的待检测程序只能用于Ascend CL系列接口的 泄漏检测，无法用于Device接口的检测。 

# 异常检测功能启用原则

异常检测工具提供内存检测（memcheck）、竞争检测（racecheck）和未初始化检测 （initcheck）三种检测功能，多种检测功能可以组合开启，组合启用检测功能需满足 以下原则： 

多个检测功能可通过多次指定--tool参数同时开启。如执行以下命令可同时开启内 存检测和竞争检测： mssanitizer -t memcheck -t racecheck ./application 

若开启了检测功能对应的子选项，则对应的检测功能也会被默认开启。如开启了 内存检测对应的泄漏检测子选项，则内存检测功能会被自动开启： mssanitizer -t racecheck --leak-check=yes ./application 

以上命令等价于： mssanitizer -t racecheck -t memcheck --leak-check=yes ./application 

若不指定任何检测功能，则默认启用内存检测： mssanitizer ./application 以上命令等价于： 

mssanitizer -t memcheck ./application 

# 调用场景

支持如下调用算子的场景： 

Kernel直调算子开发：Kernel直调。 

# 说明

Kernel直调场景，详细信息可参考《Ascend C算子开发指南》中“Kernel直调算子开发 > Kernel直调”章节。具体操作请参见6.6.1 检测内核调用符方式的Ascend C算子。 

工程化算子开发：单算子API调用。 

# 说明

● 单算子API调用场景，详细信息可参考《Ascend C算子开发指南》中“工程化算子开发 > 单算子API调用”章节。具体操作请参见6.6.2 检测API调用的单算子。 

● 在调用含有aclnn前缀的API时，需执行以下命令，通过aclInit接口传入acl.json文件以 保证内存检测的准确性。 auto ret $=$ aclInit("./acl.json"); // acl.json文件内容为{"dump":{"dump_scene":"lite_exception"}} 

AI框架算子适配：PyTorch框架。 

# 说明

PyTorch图模式（TorchAir）下，仅支持在msSanitizer工具不添加编译选项的情况下进 行检测，具体请参见配置编译选项（可选）。 

PyTorch框架调用场景，详细信息可参考《Ascend Extension for PyTorch 套件与三方 库支持清单》中“昇腾自研插件 > 单算子适配OpPlugin插件开发”章节。具体操作请 参见6.6.3 检测PyTorch接口调用的算子。 

# 结果件说明

<table><tr><td>结果件名称</td><td>说明</td></tr><tr><td>mssanitizer.{TIMESTAMP}{PID}.log</td><td>msSanitizer工具运行过程中,在mindstudio-sanitizer_log目录下生成的工具日志,TIMESTAMP为当前时间戳,PID为当前检测工具的PID。</td></tr><tr><td>kernel.{PID}.o</td><td>msSanitizer工具运行过程中,会在当前路径下生成的算子缓存文件。其中,PID为当前使用的检测工具的PID,该算子缓存文件用于解析异常调用栈。正常情况下,msSanitizer工具退出时会自动清理该算子缓存文件。当msSanitizer工具异常退出(如被用户“CTRL+C”中止)时,该算子缓存文件会保留在文件系统中。因为该算子缓存文件包含算子的调试信息,建议限制其他用户对此文件的访问权限,并在检测工具运行完成后及时删除。</td></tr><tr><td>tmp.{PID}.{TIMESTAMP}</td><td>msSanitizer工具运行过程中,会在当前路径下生成的临时文件夹。其中,PID为当前使用的检测工具的PID,TIMESTAMP为当前时间戳,该文件夹用于生成算子Kernel二进制。正常情况下,msSanitizer工具退出时会自动清理该文件夹。当通过环境变量export INJ_LOG_LEVEL=0开启DEBUG等级日志,或工具异常退出(如被用户“CTRL+C”中止)时,该文件夹会保留在文件系统中,方便用户调测使用。因为该文件夹包含算子的调试信息,建议限制其他用户对此文件的访问权限,并在调测完成后及时删除。</td></tr></table>