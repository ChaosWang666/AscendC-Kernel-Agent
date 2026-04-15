<!-- Source: 算子开发工具.md lines 8739-8845 | Section: 8.2 使用前准备 -->

# 8.2 使用前准备

# 环境准备

请参考2 环境准备，完成相关环境变量的配置。 

若要使用MindStudio Insight进行查看时，需要单独安装MindStudio Insight软件 包，具体下载链接请参见《MindStudio Insight工具用户指南》的“安装与卸 载”章节。 

若要使用模板库进行仿真，需将模板库用例examples/CMakeLists.txt下的- lruntime替换为-lruntime_camodel -L~/Ascend/ascend-toolkit/latest/tools/ simulator/Ascendxxyy/lib/，以链接仿真器运行时。 

# 说明

模板库场景仅适用于Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构 组件。 

# 使用约束

性能数据采集时间建议在5min以内，同时推荐用户设置的内存大小在20G以上 （例如容器配置：docker run --memory=20g 容器名）。 

请确保性能数据保存在不含软链接的当前用户目录下，否则可能引起安全问题。 

# msprof op 配置

若要实现Cache热力图跳转功能，需要执行以下操作： 

1. 在编译算子时添加-g编译选项，具体操作请参见编译选项需添加-g。 

2. 表8-2中的--aic-metrics参数使能Source选项。 

# msprof op simulator 配置

# 说明

msProf工具的仿真功能仅支持单卡场景，无法仿真多卡环境，代码中也只能设置0卡。若修改可 见卡号，则会导致仿真失败。 

msProf工具使用--config模式进行算子仿真调优之前，需执行如下命令配置环境变 量。 

export LD_LIBRARY_PATH=${INSTALL_DIR}/tools/simulator/Ascendxxxyy/lib:$LD_LIBRARY_PATH 

请根据CANN软件包实际安装路径和昇腾AI处理器的型号对以上环境变量进行修 改。 

编译选项需添加-g，使能算子代码热点图和代码调用栈功能。 

# 说明

● 添加-g编译选项会在生成的二进制文件中附带调试信息，建议限制带有调试信息的用户 程序的访问权限，确保只有授权人员可以访问该二进制文件。 

● 若不使用llvm-symbolizer组件提供的相关功能，输入msProf的程序编译时不包含-g即 可，msProf工具则不会调用llvm-symbolizer组件的相关功能。 

若参考msOpGen工具创建的算子工程，需编辑算子工程op_kernel目录下的 CMakeLists.txt文件，可参考4.3 创建算子工程。 add_ops_compile_options(ALL OPTIONS -g) 

若参考完整样例，以Link为例，需在样例工程目录下的“cmake/ npu_lib.cmake”文件中新增以下代码。 

# 说明

● 此样例工程不支持Atlas A3 训练系列产品。 

下载代码样例时，需执行以下命令指定分支版本。 git clone https://gitee.com/ascend/samples.git -b v1.5-8.2.RC1 

```txt
ascendc.compile-options(ascendc_kernels${RUN_MODE} PRIVATE
-g
-O2 
```

使用msProf工具对PyTorch脚本的算子进行仿真调优时，不支持Python内置的 print函数打印Device侧上的变量和值。 

8.0.RC2及后续版本的CANN支持了Atlas A3 训练系列产品/Atlas A3 推理系列产品 和Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组件仿真器 的配置线程提速以及L2Cache仿真增强，可以参照如下配置进行修改： 

可以通过配置config_stars.json实现仿真器多线程提速，config_stars.json文 件的路径为 


${INSTALL_DIR}/tools/simulator/Ascendxxxyy/lib/config_stars.json。


```txt
"stars": {
    "ftts_mode": 1
},
"model_top": {
    "sim_type": 0,
    "num_iaic": 24,
    "num_iaiv": 48
},
"pem": {
    "parsim": 1,
    "parsim_thd_limit": 24
} 
```

可以通过配置config.json实现L2Cache仿真增强，config.json文件的路径为 ${INSTALL_DIR}/tools/simulator/Ascendxxxyy/lib/config.json。 

```txt
"L2CACHE": { "cache_enable": 1, "cache_set_size": 24, "cache_way_size": 16384, "cache_line_size": 512, "cache_read_forency": 241, "cache_write_forency": 96 } 
```

Atlas A3 训练系列产品、Atlas A2 训练系列产品/Atlas 800I A2 推理产品/ A200I A2 Box 异构组件和Atlas 推理系列产品使用msProf工具进行算子仿真 调优时，需将config.json文件中的flush_level参数修改为info级，也就是将文 件中的flush_level = "3"修改为flush_level = "2"。config.json文件的路径为$ {INSTALL_DIR}/tools/simulator/Ascendxxxyy/lib/config.json。 

# 启动工具

请参见msprof op的操作步骤使能msProf工具的上板调优功能。 

请先参见msprof op simulator配置去配置部分仿真调优的功能，然后根据 msprof op simulator的操作步骤使能msProf工具的仿真调优功能。 

说明 

当前msProf不支持-O0编译选项。