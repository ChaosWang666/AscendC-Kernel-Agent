<!-- Source: 算子开发工具.md lines 5455-5556 | Section: 6.2 使用前准备 -->

# 6.2 使用前准备

# 环境准备

请参考2 环境准备，完成相关环境变量的配置。 

# 配置编译选项（可选）

用户可根据需求自行选择是否添加编译选项，具体请参见表6-4。 


表 6-4 编译场景介绍


<table><tr><td>是否添加编译选项</td><td>指令检测范围</td><td>异常检测范围</td><td>适用场景</td></tr><tr><td>不添加</td><td>与GM相关的搬运指令</td><td>·仅支持内存检测中的非法读写和非对齐访问。
·异常报告中不显示调用栈信息。
说明
·该场景算子的优化等级需为O2，并保证算子链接阶段增加-q选项，保留符号重定位信息，否则会导致检测功能失效。
·该场景不适用于Atlas推理系列产品。
·该场景仅适用于算子内核调用符场景。</td><td>该场景支持的功能上有限制，仅适用于对算子内存异常中的非法读写和非对齐访问异常的快速定界。</td></tr><tr><td>添加</td><td>全量指令</td><td>·支持全量检测。
·在编译选项中增加-g选项后，异常报告将会显示调用栈信息。</td><td>通过不添加编译选项的功能快速定位异常算子后，再添加编译选项对异常算子进行全量检测，具体操作请参见开启全量检测。</td></tr></table>

# 开启全量检测

如需要开启全量检测，需要在算子代码的编译阶段增加编译选项，不同算子工程添加 编译选项的位置不同，下面以模板库场景、内核调用符场景和msOpGen算子工程编译 场景为例进行介绍： 

模板库场景 

修改模板库中的/examples/CMakeLists.txt文件，新增-g --cce-enablesanitizer编译选项。 

set(BISHENG_COMPILER_OPTIONS -g --cce-enable-sanitizer) 

内核调用符场景 

a. 样例工程代码请参考Link，执行以下命令，下载分支版本的样例代码。 

git clone https://gitee.com/ascend/samples.git -b 8.0.RC2 

# 说明

此样例工程不支持Atlas A3 训练系列产品。 

b. 算子代码的编译选项需添加-g --cce-enable-sanitizer。 

编辑样例工程目录下的“cmake/npu/CMakeLists.txt”文件，参考核函数开 发和运行验证的完整样例。 

target_compile_options(${smoke_testcase}_npu PRIVATE -O2 -std=c++17 --cce-enable-sanitizer 

```txt
-g 
```

增加--cce-enable-sanitizer选项代表使能异常检测。 

增加-g选项使编译器生成定位信息，将会在异常报告输出时显示异常发生的 具体位置（文件名、行号以及调用栈等信息）。 

# 说明

--cce-enable-sanitizer和-O0同时开启的情况下，需要增加编译选项 --cceignore-always-inline=false。 

● 添加-g编译选项会在生成的二进制文件中附带调试信息，建议限制带有调试信息 的用户程序的访问权限，确保只有授权人员可以访问该二进制文件。 

● 增加--cce-enable-sanitizer编译选项生成的算子二进制，需与msSanitizer工具配 套使用。不建议单独使用该二进制，单独使用可能会导致不可预见的问题。 

因llvm-symbolizer开源软件限制，调用栈的异常信息可能会获取失败。此时，用 户可再次执行检测命令，就可以获取调用栈的异常信息。 

c. 链接阶段需增加target_link_options选项。 

编辑样例工程目录下的“cmake/npu/CMakeLists.txt”文件。target_link-options({smoke_testcase} $_npu$ PRIVATE--cce-fatobj-link--cce-enable-sanitizer） 

```txt
编辑样例工程目录下的“cmake/Modules/ CMakeCCEInformation.cmake”文件。 if(NOT CMAKE_CCE_LINK_executable) set(CMAKE_CCE_LINK_executable "<CMAKE_CCE_COMPILER>\$\{CMAKE.LibraryCreate_CCE_FLAGS\} \$\{CMAKE_COMPILE_AS_CCE_FLAG\}<FLAGS><CMAKE_CCE LINK FLAGS><LINK_FLAGS> <OBJECTS> -o <TARGET><LINK_LIBRARIES>\$\{__IMPLICITlinks}\}"endif() 
```

d. 启用msSanitizer检测工具时，需要加载NPU侧可执行文件 <kernel_name>_npu，该文件的获取可参考《AscendC算子开发指南》中的 “Kernel直调算子开发 $>$ Kernel直调”章节。 

msOpGen算子工程编译场景 

a. 单击Link，在${git_clone_path}/samples/operator/ascendc/0_introduction/ 1_add_frameworklaunch目录下运行install.sh脚本，生成自定义算子工程。 

# 说明

```txt
下载代码样例时，需执行以下命令指定分支版本。git clone https://gitee.com/ascend/samples.git -b v1.5-8.2.RC1 install.sh -v Ascendxxxxy # xxxxy为用户实际使用的具体芯片类型 
```

b. 切换至自定义算子工程目录。 cd CustomOp 

c. 编辑样例工程目录下的“op_kernel/CMakeLists.txt”文件，在编译选项中添 加-sanitizer选项，具体请参考支持自定义编译选项。 add_ops_compile_options(ALL OPTIONS -sanitizer) 

# 启动工具

完成环境准备和配置编译选项（可选）后，请参见启用内存检测、启用竞争检测和启 用未初始化检测章节使能msSanitizer工具的相关功能。 

# 说明

异常报告具有以下级别： 

● WARNING：此级别被定义为不确定性的风险，可能出现的异常现象由实际情况决定，如 多核踩踏、内存分配未使用等。其中，多核踩踏风险涉及多个核对同一块内存的操作，高 阶用户可以通过核间同步的手段来规避此风险，初级用户遇到此类异常，应该将其视为危 险源。目前，多核踩踏的WARNING级别的报告仅能识别atomic类的核间同步信息。 

ERROR：最高严重级别的异常，涉及针对内存操作的确定性错误，如非法读写、内存泄 漏、非对齐访问、内存未初始化、竞争异常等。强烈建议用户检查此严重级别的异常。