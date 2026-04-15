<!-- Source: 算子开发工具.md lines 6912-6993 | Section: 7.1 工具概述 -->

# 7.1 工具概述

msDebug是用于调试在NPU侧运行的算子程序的一个工具，该工具向算子开发人员提 供了在昇腾设备上调试算子的手段。调试手段包括了读取昇腾设备内存与寄存器、暂 停与恢复程序运行状态等。用户使用其他拉起算子的方式或msOpST工具在真实的硬 件环境中对算子的功能进行测试后，可根据实际测试情况选择是否使用msDebug工具 进行功能调试。 

# 说明

● 若要使能msDebug工具，需通过以下两种方法安装NPU驱动固件（CANN 8.1.RC1之后的版 本且驱动为25.0.RC1之后的版本，推荐使用方法一）： 

方法一：驱动安装时指定--full参数，然后再使用root用户执行echo 1 > /proc/ debug_switch命令打开调试通道，msDebug工具便可正常使用。 ./Ascend-hdk-<chip_type>-npu-driver_<version>_linux-<arch>.run --full 

方法二：驱动安装时指定--debug参数，具体安装操作请参见《CANN 软件安装指南》 中的“安装NPU驱动固件”章节。 ./Ascend-hdk-<chip_type>-npu-driver_<version>_linux-<arch>.run --debug 

● 调试通道权限较大，存在安全风险，请谨慎使用，生产环境不推荐使用，使用本调试工具即 代表认可并接受该风险。 

# 功能特性

msDebug工具支持调试所有的昇腾算子，包含Ascend C算子（Vector、Cube以及Mix 融合算子）程序，用户可根据实际情况进行选择，具体请参见表7-1。 


表 7-1 msDebug 工具功能介绍


<table><tr><td>功能</td><td>链接</td></tr><tr><td>断点设置</td><td>7.4 断点设置</td></tr><tr><td>打印变量和内存</td><td>7.5 内存与变量打印</td></tr><tr><td>单步调试</td><td>7.6 单步调试</td></tr><tr><td>中断运行</td><td>7.7 中断运行</td></tr><tr><td>核切换</td><td>7.8 核切换</td></tr><tr><td>检查程序状态</td><td>7.9 读取寄存器</td></tr><tr><td>调试信息展示</td><td>7.10 调试信息展示</td></tr><tr><td>解析Core dump文件</td><td>7.11 解析异常算子dump文件</td></tr></table>

# 命令汇总

# 说明

● 用户需自行保证可执行文件或用户程序（application）执行的安全性。 

建议限制对可执行文件或用户程序（application）的操作权限，避免提权风险。 

不建议进行高危操作（删除文件、删除目录、修改密码及提权命令等），避免安全风 险。 

● 通过键入help命令可查看msDebug工具支持的所有命令。表7-2之外的命令属于开源调试器 lldb实现，使用需注意相关风险，详细使用方法可参考lldb官方文档https://lldb.llvm.org/。 


表 7-2 命令参考说明


<table><tr><td>命令</td><td>命令缩写</td><td>描述</td><td>示例</td></tr><tr><td>breakpoint set -f filename -l linenum</td><td>b</td><td>增加断点, filename为算子实现代码文件*.cpp, linenum为代码文件对应的具体行号。</td><td>b addCustom.cpp:85</td></tr><tr><td>run</td><td>r</td><td>运行程序。</td><td>r</td></tr><tr><td>continue</td><td>c</td><td>继续运行。</td><td>c</td></tr><tr><td>print variable</td><td>p</td><td>打印变量。</td><td>p zLocal</td></tr><tr><td>frame variable</td><td>var</td><td>显示当前作用域内的所有局部变量。</td><td>var</td></tr><tr><td>memory read</td><td>x</td><td>读内存。</td><td>x -m GM -f float16[0x00001240c0037000 -c 2 -s 128
- m: 指定内存位置, 支持GM/UB/LOA/LOB/LOC/L1/FB/STACK/DCACHE/ICACHE说明STACK/DCACHE/ICACHE仅在7.11解析异常算子dump文件时使用。
- s: 指定每行打印字节数
- c: 指定打印的行数
- f: 指定打印的数据类型
0x00001240c0037000: 需要读取的内存地址, 请根据实际环境进行替换</td></tr><tr><td>ascend info devices</td><td>-</td><td>查询Device信息。</td><td>ascend info devices</td></tr><tr><td>ascend info cores</td><td>-</td><td>查询算子所运行的aicore相关信息。</td><td>ascend info cores</td></tr><tr><td>ascend info tasks</td><td>-</td><td>查询算子所运行的task相关信息。</td><td>ascend info tasks</td></tr><tr><td>ascend info stream</td><td>-</td><td>查询算子所运行的stream相关信息。</td><td>ascend info stream</td></tr><tr><td>ascend info blocks</td><td>-</td><td>查询算子所运行的block相关信息。</td><td>显示所运行的blocks相关信息:
ascend info blocks
显示所运行的blocks在当前中断处的代码:
ascend info blocks -d</td></tr><tr><td>ascend aic id</td><td>-</td><td>切换调试器所聚焦的cube核。</td><td>ascend aic 1</td></tr><tr><td>ascend aiv id</td><td>-</td><td>切换调试器所聚焦的vector核。</td><td>ascend aiv 5</td></tr><tr><td>“CTRL+C”</td><td>-</td><td>手动中断算子运行程序并回显中断位置信息。</td><td>通过键盘输入。</td></tr><tr><td>register read</td><td>re r</td><td>读取寄存器值；-a读取所有寄存器值；$REG_NAME读取指定名称的寄存器值；</td><td>register read -a re r $PC</td></tr><tr><td>thread step-over</td><td>next或n</td><td>在同一个调用栈中，移动到下一个可执行的代码行。</td><td>n</td></tr><tr><td>thread step-in</td><td>step或s</td><td>使用step in命令可进入到函数内部进行调试。</td><td>s</td></tr><tr><td>thread step-out</td><td>finish</td><td>使用finish命令会执行完函数内剩余部分，并返回主程序继续执行。</td><td>finish</td></tr><tr><td>target modules add&lt;kernel.o&gt;</td><td>image add[kernel.o]</td><td>用于PyTorch框架调用算子时，导入算子调试信息。说明当程序执行run命令后，需先执行image add命令导入调试信息。然后，再执行image load命令使导入的调试信息生效。</td><td>image add xx.o</td></tr><tr><td>target modules load--file&lt;kernel.o&gt; --slide&lt;kernel.o&gt; --address&gt;</td><td>image load -f&lt;kernel.o&gt; -s&lt;address&gt;</td><td>用于PyTorch框架调用算子时，加载算子调试信息，使导入的调试信息生效。</td><td>image load -f xx.o -s 0</td></tr><tr><td>msdebug --core corefile</td><td>-</td><td>用于加载Core dump文件。</td><td>msdebug --core corefile</td></tr><tr><td>ascend info summary</td><td>-</td><td>用于查看Core dump文件信息。</td><td>ascend info summary</td></tr><tr><td>helpmsdebug_command</td><td>-</td><td>输出对应工具命令的帮助信息。说明打印信息将会展示该命令的功能描述、使用语法以及参数选项。如核切换命令的帮助信息如下所示:(msdebug) help ascend aicchange the id of the focused ascend acore.Syntax: ascend aic如 ascend info blocks命令的帮助信息如下所示:(msdebug) help ascend info blocksshow blocks overall info.Syntax: ascend info blocksCommand OptionsUsage:ascend info blocks [-d]-d ( --details )Show stoppedstates for all blocks.</td><td>help run</td></tr></table>

# 调用场景

支持如下调用算子的场景： 

Kernel直调算子开发：Kernel直调。 

# 说明

Kernel直调的场景，详细信息可参考《Ascend C算子开发指南》中“Kernel直调算子开发 $>$ Kernel直调”章节。具体操作请参见7.12.1 上板调试vector算子。 

工程化算子开发：单算子API调用。 

# 说明

单算子API调用的场景，详细信息可参考《Ascend C算子开发指南》中“工程化算子开发 > 单算子API调用”章节。具体操作请参见7.12.2 调用Ascend CL单算子。 

AI框架算子适配：PyTorch框架。 

# 说明

通过PyTorch框架进行单算子调用的场景，详细信息可参考《Ascend Extension for PyTorch 套件与三方库支持清单》中“昇腾自研插件 > 单算子适配OpPlugin插件开发”章 节。具体操作请参见7.12.3 调试PyTorch接口调用的算子。 

# 补充说明

msDebug工具还提供了以下扩展程序，具体请参考表7-3。 


表 7-3 扩展程序说明


<table><tr><td>程序名称</td><td>说明</td></tr><tr><td>msdebug-mi</td><td>提供机机交互接口用于实现数据解析，用户无需关注。</td></tr></table>