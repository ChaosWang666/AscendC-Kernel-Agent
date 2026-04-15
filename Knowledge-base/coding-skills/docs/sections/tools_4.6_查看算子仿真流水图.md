<!-- Source: 算子开发工具.md lines 4221-4346 | Section: 4.6 查看算子仿真流水图 -->

# 4.6 查看算子仿真流水图

msOpGen工具通过解析用户生成的dump文件，并生成算子仿真流水图文件 （trace.json）。 

步骤1 参考Link，在${git_clone_path}/samples/operator/ascendc/0_introduction/ 1_add_frameworklaunch路径下运行install.sh文件，并生成CustomOp文件夹。 

# 说明

此样例工程不支持Atlas A3 训练系列产品和Atlas 训练系列产品。 

```txt
./install.sh -v Ascendxxxxy # xxxyy为用户实际使用的具体芯片类型 
```

# 步骤2 编译算子工程。

1. 参考编译前准备章节，完成编译相关配置。 

2. 在算子工程目录CustomOp下，执行如下命令，进行算子工程编译。 

# 说明

若要生成算子仿真流水图，需要将当前目录下CMakePresets.json文件中 CMAKE_BUILD_TYPE修改为“Debug” 。 

编译完成后，将会在build_out目录生成.run算子包。 

./build.sh 

步骤3 在自定义算子包所在路径下，执行如下命令，部署算子包。 

./build_out/custom_opp_<target_os>_<target_architecture>.run 

步骤4 切换到AclNNInvocation仓的目录${git_clone_path}/samples/operator/ascendc/ 0_introduction/1_add_frameworklaunch/AclNNInvocation，执行以下命令。 

./run.sh 

步骤5 使能环境变量后，请参考msprof op simulator功能进行仿真，并生成dump数据。 

export LD_LIBRARY_PATH=${git_clone_path}/samples/operator/ascendc/0_introduction/ 1_add_frameworklaunch/CustomOp/build_out/op_host/:$LD_LIBRARY_PATH 

步骤6 生成算子仿真流水图文件。 

执行如下命令，参数说明请参见表4-8。 

msopgen sim -c core{id} -d xx/{path of dump data} -subc {sub core id} -out {output path} -reloc {path of .o file or executable file} 


表 4-8 参数说明


<table><tr><td>参数名称</td><td>参数描述</td><td>是否必选</td></tr><tr><td>sim</td><td>用于性能仿真相关操作。</td><td>是</td></tr><tr><td>-c, --core-id</td><td>核编号。
配置处理器号，如：core0。</td><td>是</td></tr><tr><td>-d, --dump-dir</td><td>dump文件所在路径，可配置为绝对路径或者相对路径。</td><td>是</td></tr><tr><td>-subc, --subcore_id</td><td>子核编号，支持展示单个子核。
dump文件名带有veccore{id}或cubecore{id}时，需配置此参数指定待解析的dump文件。如文件名为core0.veccore0.instr_log dump, “veccore0”即为subcore id。</td><td rowspan="2">二选一
说明
仅Atlas A3训练系列产品/Atlas A3 推理系列产品和Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box异构组件需配置该参数。</td></tr><tr><td>-mix, --mixcore-mode</td><td>支持展示Mix融合算子。</td></tr><tr><td>-reloc, --relocatable-file</td><td>配置为Kernel侧算子编译后生成的.o文件或可执行文件所在路径。进行流水图与代码行的映射，并生成代码行和指令耗时.csv文件。说明基于算子工程编译生成包含调试信息的.o文件（路径为${git cloned_path}/samples/operator/ascendc/0_introduction/1_add_frameworklaunch/CustomOp/build_out/op_kernel/binary/ ascendxxxy/add_custom/AddCustom*.o），即需要修改CMakePresents.json中CMAKE-built_TYPE为“Debug”，具体可参考编译操作。</td><td>否</td></tr><tr><td>-out, --output</td><td>输出文件的路径，可配置为绝对路径或者相对路径，并且工具执行用户具有可读写权限。</td><td>是</td></tr><tr><td>-h, --help</td><td>输出帮助信息。</td><td>否</td></tr></table>

执行以下命令。 

# 示例一：

msopgen sim -c core0 -d xx/{model}/ca/add_custom/add_custom_pre_static_add_custom -out ./output_data -subc cubecore0 -reloc xx/.o 

-c：指定待解析dump文件的core id，如：core0。 

-d：指定性能仿真环境下生成的dump文件所在路径。例如："{model}/ca/ add_custom/add_custom_pre_static_add_custom"。 

-subc：指定待解析dump文件的subcore id，如文件名为 core0.cubecore0.instr_log.dump，“cubecore0”即为subcore id。（仅Atlas A3 训练系列产品/Atlas A3 推理系列产品和Atlas A2 训练系列产品/Atlas 800I A2 推 理产品/A200I A2 Box 异构组件需配置该参数） 

-reloc：指定Kernel侧算子编译生成的.o文件或可执行文件所在路径。 

# 示例二：

msopgen sim -c core0 -d xx/{model}/ca/add_custom/add_custom_pre_static_add_custom -out ./output_data -mix 

-c：指定待解析dump文件的core id，如：core0。 

-d：指定性能仿真环境下生成的dump文件所在路径。例如："{model}/ca/ add_custom/add_custom_pre_static_add_custom"。 

-mix ：配置此参数表示支持展示Mix融合算子。 

步骤7 查看算子仿真流水图文件。 

可以在Chrome浏览器中输入“chrome://tracing”地址，将输出路径下的 dump2trace_core*.json文件拖到空白处打开，通过键盘上的快捷键（W：放大，S： 缩小，A：左移，D：右移）进行查看，如下图所示。 


图 4-3 单个子核展示


![](images/b82e36bec8454dd719b204abb4074d6fae2cbee5806142680d3b79bb470b8b5f.jpg)



图 4-4 Mix 融合算子展示


![](images/27ee6dc1eef9d9ea34f7a0b94d66330eb1f3762d95f699cae0907982e969e630.jpg)



表 4-9 字段说明


<table><tr><td>字段名</td><td>字段含义</td></tr><tr><td>VECTOR</td><td>向量运算单元。</td></tr><tr><td>SCALAR</td><td>标量运算单元。</td></tr><tr><td>CUBE</td><td>矩阵乘运算单元。</td></tr><tr><td>MTE1</td><td>数据搬运流水,数据搬运方向为:L1 -&gt;{L0A/L0B, UBUF}。</td></tr><tr><td>MTE2</td><td>数据搬运流水,数据搬运方向为:{DDR/GM, L2} -&gt;{L1, L0A/B, UBUF}。</td></tr><tr><td>MTE3</td><td>数据搬运流水,数据搬运方向为:UBUF -&gt;{DDR/GM, L2, L1}。</td></tr><tr><td>FIXP</td><td>数据搬运流水,数据搬运方向为: FIXPIPE LOC -&gt; OUT/L1。(仅Atlas A3训练系列产品/Atlas A3推理系列产品和Atlas A2训练系列产品/Atlas 800I A2推理产品/A200I A2 Box异构组件支持展示)</td></tr><tr><td>FLOWCTRL</td><td>控制流指令。</td></tr><tr><td>ICmiss</td><td>未命中icache。</td></tr></table>

步骤8 查看代码行或指令耗时文件。 

在输出路径下打开代码行耗时文件{核编号}_code_exe_prof.csv，如下图所示。 


图 4-5 代码行耗时文件


<table><tr><td>line</td><td>call count</td><td>cycles</td></tr><tr><td>/home/Ascend/ascend-toolkit/latest/compiler/tikcpp/tikcfw/impl/dav_c100/kernel_operator_data_copy_impl.h.16</td><td>16</td><td>4444</td></tr><tr><td>/home/Ascend/ascend-toolkit/latest/compiler/tikcpp/tikcfw/impl/dav_c100/kernel_operator_data_copy_impl.h.33</td><td>16</td><td>4272</td></tr><tr><td>/home/Ascend/ascend-toolkit/latest/compiler/tikcpp/tikcfw/interface/kernel_tpipe.h.172</td><td>16</td><td>3984</td></tr><tr><td>/home/Ascend/ascend-toolkit/latest/compiler/tikcpp/tikcfw/interface/kernel_tpipe.h.166</td><td>16</td><td>3871</td></tr><tr><td>/home/Ascend/ascend-toolkit/latest/compiler/tikcpp/tikcfw/interface/kernel_tpipe.h.253</td><td>16</td><td>2545</td></tr><tr><td>/home/Ascend/ascend-toolkit/latest/compiler/tikcpp/tikcfw/interface/kernel_tpipe.h.928</td><td>16</td><td>1344</td></tr><tr><td>/home/Ascend/ascend-toolkit/latest/compiler/tikcpp/tikcfw/interface/kernel_tpipe.h.945</td><td>16</td><td>1170</td></tr><tr><td>/home/Ascend/ascend-toolkit/latest/compiler/tikcpp/tikcfw/impl/dav_c100/kernel_operator_vec_binary.impl.h.52</td><td>16</td><td>991</td></tr><tr><td>/home/Ascend/ascend-toolkit/latest/compiler/tikcpp/tikcfw/interface/kernel_tpipe.h.1419</td><td>16</td><td>701</td></tr><tr><td>/home/Ascend/ascend-toolkit/latest/compiler/tikcpp/tikcfw/interface/kernel_tpipe.h.1295</td><td>16</td><td>577</td></tr><tr><td>/home/Ascend/ascend-toolkit/latest/compiler/tikcpp/tikcfw/interface/kernel_tpipe.h.660</td><td>1</td><td>571</td></tr><tr><td>/home/Ascend/ascend-toolkit/latest/compiler/tikcpp/tikcfw/interface/kernel_tpipe.h.1209</td><td>16</td><td>528</td></tr><tr><td>/home/Ascend/ascend-toolkit/latest/compiler/tikcpp/tikcfw/interface/kernel_tpipe.h.1352</td><td>16</td><td>511</td></tr><tr><td>/home/Ascend/ascend-toolkit/latest/compiler/tikcpp/tikcfw/interface/kernel_tpipe.h.259</td><td>14</td><td>501</td></tr><tr><td>/home/Ascend/ascend-toolkit/latest/compiler/tikcpp/tikcfw/interface/kernel_tpipe.h.1333</td><td>16</td><td>464</td></tr><tr><td>/home/Ascend/ascend-toolkit/latest/compiler/tikcpp/tikcfw/interface/kernel_tpipe.h.1234</td><td>16</td><td>448</td></tr><tr><td>/home/Ascend/ascend-toolkit/latest/compiler/tikcpp/tikcfw/interface/kernel_tpipe.h.1326</td><td>16</td><td>448</td></tr><tr><td>/home/Ascend/ascend-toolkit/latest/compiler/tikcpp/tikcfw/interface/kernel_tpipe.h.1274</td><td>16</td><td>432</td></tr></table>

在输出路径下打开指令耗时文件{核编号}_instr_exe_prof.csv，如下图所示。 


图4-6 指令耗时文件


<table><tr><td>instr name</td><td>addr</td><td>call count</td><td>cycles</td><td>instr detail</td></tr><tr><td>DMA_MOV</td><td>0x10cfa5b4</td><td>16</td><td>4364</td><td>Src:OUT, Dst:UB, XD:X18=0x300, XN:X16=0x10cea300, XM:X7=0x80010, CONV_RELU0, PAD:0</td></tr><tr><td>DMA_MOV</td><td>0x10cfa5a8</td><td>16</td><td>4336</td><td>Src:OUT, Dst:UB, XD:X16=0x100, XN:X19=0x10ce2100, XM:X7=0x80010, CONV_RELU0, PAD:0</td></tr><tr><td>DMA_MOV</td><td>0x10cfa43c</td><td>16</td><td>4272</td><td>Src:UB, Dst:OUT, XD:X13=0x10cf2500, XN:X15=0x500, XM:X7=0x80010, CONV_RELU0, PAD:0</td></tr><tr><td>SET_FLAG</td><td>0x10cfa460</td><td>16</td><td>3968</td><td>PIPE:MTE3, TRIGGER PIPE:VEC, FLAG ID:1</td></tr><tr><td>SET_FLAG</td><td>0x10cfa5e8</td><td>16</td><td>3852</td><td>PIPE:MTE2, TRIGGER PIPE:VEC, FLAG ID:1</td></tr><tr><td>SET_FLAG</td><td>0x10cfa640</td><td>16</td><td>2904</td><td>PIPE:MTE2, TRIGGER PIPE:VEC, FLAG ID:0</td></tr><tr><td>WAIT_FLAG</td><td>0x10cfa688</td><td>16</td><td>2511</td><td>PIPE:MTE2, TRIGGER PIPE:VEC, FLAG ID:1</td></tr><tr><td>WAIT_FLAG</td><td>0x10cfa6f8</td><td>16</td><td>1874</td><td>PIPE:MTE2, TRIGGER PIPE:VEC, FLAG ID:0</td></tr><tr><td>WAIT_FLAG</td><td>0x10cfa794</td><td>14</td><td>924</td><td>PIPE:MTE3, TRIGGER PIPE:VEC, FLAG ID:1</td></tr><tr><td>BAR</td><td>0x10cfa7d0</td><td>16</td><td>783</td><td>PIPE:VEC</td></tr><tr><td>SET_FLAG</td><td>0x10cfa808</td><td>16</td><td>404</td><td>PIPE:VEC, TRIGGER PIPE:MTE3, FLAG ID:0</td></tr><tr><td>DMA_MOV</td><td>0x10cfa058</td><td>1</td><td>270</td><td>Src:OUT, Dst:UB, XD:X0=0, XN:X1=0x1068be00, XM:X2=0x10012, CONV_RELU0, PAD:0</td></tr><tr><td>DMA_MOV</td><td>0x10cfa1a4</td><td>1</td><td>270</td><td>Src:OUT, Dst:UB, XD:X8=0x3ffe0, XN:X5=0x10cef8c, XM:X6=0x10010, CONV_RELU0, PAD:0</td></tr><tr><td>DMA_MOV</td><td>0x10cfa1d8</td><td>1</td><td>267</td><td>Src:UB, Dst:OUT, XD:X5=0x10cef8c, XN:X8=0x3ffe0, XM:X6=0x10010, CONV_RELU0, PAD:0</td></tr><tr><td>SET_FLAG</td><td>0x10cfa074</td><td>1</td><td>265</td><td>PIPE:MTE2, TRIGGER PIPE:SCALAR, FLAG ID:0</td></tr><tr><td>WAIT_FLAG</td><td>0x10cfa078</td><td>1</td><td>264</td><td>PIPE:MTE2, TRIGGER PIPE:SCALAR, FLAG ID:0</td></tr><tr><td>VADD</td><td>0x10cfa7d4</td><td>16</td><td>208</td><td>dtype:F16XD:0x500XN:0x100XM:0x300XT:0x0100080808010101</td></tr><tr><td>ST_XD_XNImm</td><td>0x10cfa12c</td><td>32</td><td>128</td><td>dtype:B8, XD:X0=0, XN:X1=0x439eb, IMM:0,</td></tr><tr><td>ST_XD_XNImm</td><td>0x10cfa130</td><td>32</td><td>128</td><td>dtype:B8, XD:X0=0, XN:X1=0x439eb, IMM:0x1,</td></tr><tr><td>ST_XD_XNImm</td><td>0x10cfa134</td><td>32</td><td>128</td><td>dtype:B8, XD:X5=0x1, XN:X1=0x439eb, IMM:0x2,</td></tr><tr><td>ST_XD_XNImm</td><td>0x10cfa138</td><td>32</td><td>128</td><td>dtype:B8, XD:X6=0x2, XN:X1=0x439eb, IMM:0x3,</td></tr><tr><td>ST_XD_XNImm</td><td>0x10cfa13c</td><td>32</td><td>128</td><td>dtype:B8, XD:X7=0x3, XN:X1=0x439eb, IMM:0x4,</td></tr><tr><td>ADD</td><td>0x10cfa124</td><td>32</td><td>64</td><td>dtype:S64, XD:X11=0x20, XN:X10=0x1f, XM:X5=0x1,</td></tr><tr><td>ZEROEXT</td><td>0x10cfa128</td><td>32</td><td>64</td><td>dtype:U32, XD:X10=0x1f, XN:X10=0x1f,</td></tr><tr><td>CMP</td><td>0x10cfa140</td><td>32</td><td>64</td><td>dtype:U64, XN:X10=0x1f, XM:X8=0x1f, cond_op:LT,</td></tr><tr><td>ADD</td><td>0x10cfa144</td><td>32</td><td>64</td><td>dtype:S64, XD:X1=0x439f0, XN:X1=0x439eb, XM:X9=0x5,</td></tr><tr><td>MOV_XD_XN</td><td>0x10cfa148</td><td>32</td><td>64</td><td>dtype:S64, XD:X10=0x20, XN:X11=0x20,</td></tr><tr><td>LD_XD_XNImm</td><td>0x10cfa47c</td><td>16</td><td>64</td><td>dtype:B64, XD:X12=0x439f0, XN:X30=0x43910, IMM:0x528,</td></tr><tr><td>LD_XD_XNImm</td><td>0x10cfa480</td><td>16</td><td>64</td><td>dtype:B8, XD:X15=0x2, XN:X30=0x43910, IMM:0x531,</td></tr></table>

通过文件中的“call count”及“cycles”字段可以分别查看代码行或指令的调用次数 和累计耗时。 

----结束