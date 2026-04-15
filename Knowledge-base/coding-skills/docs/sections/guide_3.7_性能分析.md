<!-- Source: 算子开发指南.md lines 19351-19475 | Section: 3.7 性能分析 -->

# 3.7 性能分析

# 3.7.1 获取性能数据

在进行性能优化之前，需要拿到准确的性能数据，了解性能现状，并根据性能现状分 析下一步的优化方向。Ascend C提供了多种性能测试方法，包括上板Profiling、单算 子性能仿真流水图等手段。 

# 上板 Profiling

如下命令行是一个算子上板性能数据采集的示例，可以根据自身的需要灵活组合配置 参数。示例中--output为可选参数，用于指定收集到的性能数据的存放路径；$HOME/ projects/MyApp/out/main为算子可执行文件。 

msprof op --output $\equiv$ \ $HOME/projects/output \$ HOME/projects/MyApp/out/main 

如下示例则展示了部分性能数据文件的样例： 


图 3-82 PipeUtilization.csv（计算单元和搬运单元耗时占比）文件示例


<table><tr><td>block_id</td><td>sub block_id</td><td>alg</td><td>alc time(s)</td><td>alg total (s)</td><td>alg cubic time(s)</td><td>alg cubic ratio</td><td>alg scalar(time(s))</td><td>alg scalar_ratio</td><td>alg metric1time(s)</td><td>alg metric1 ratio</td><td>alg metric2time(s)</td><td>alg metric2 ratio</td><td>alg metric3time(s)</td><td>alg metric3 ratio</td><td>alg fioppi time(s)</td><td>alg fioppi ratio</td><td>alg cachexia time(s)</td><td>alg cachexia ratio</td><td>alg total (s)</td><td>alg vici time(s)</td><td>alg vici ratio</td><td>alg scalar(time(s))</td><td>alg scalar_ratio</td><td>alg scalar time(s)</td><td>alg scalar ratio</td><td>alg vici ratio</td><td>alg vici ratio</td><td>alg vici ratio</td><td>alg vici ratio</td><td>alg vici ratio</td><td>alg vici ratio</td><td>alg vici ratio</td><td>alg vici ratio</td><td>alg vici ratio</td><td>alg vici ratio</td></tr><tr><td>0</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>0.502772</td><td>8403</td><td>0.385485</td><td>0.075687</td><td>0.582443</td><td>1.037606</td><td>0.794545</td><td>0.584733</td><td>2.943818</td><td>0.459636</td><td>0.075687</td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>1</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>0.583844</td><td>8538</td><td>0.385485</td><td>0.075687</td><td>0.582443</td><td>1.037606</td><td>0.794545</td><td>0.584733</td><td>2.943818</td><td>0.459636</td><td>0.075687</td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>2</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>0.572185</td><td>8686</td><td>0.385485</td><td>0.075687</td><td>0.533333</td><td>0.582443</td><td>1.037606</td><td>0.794545</td><td>2.943818</td><td>0.459636</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>3</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>0.593333</td><td>8404</td><td>0.385485</td><td>0.074487</td><td>0.507879</td><td>0.693222</td><td>2.849687</td><td>0.554095</td><td>2.273515</td><td>0.445878</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>4</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>0.5412122</td><td>8403</td><td>0.385485</td><td>0.074473</td><td>0.500009</td><td>0.600016</td><td>0.897729</td><td>0.561594</td><td>2.413333</td><td>0.484009</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>5</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>0.590767</td><td>8407</td><td>0.385485</td><td>0.074487</td><td>0.500009</td><td>0.600016</td><td>0.897729</td><td>0.561594</td><td>2.413333</td><td>0.484009</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>6</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>0.581212</td><td>8516</td><td>0.379304</td><td>0.073509</td><td>0.587057</td><td>0.693222</td><td>2.849687</td><td>0.554095</td><td>2.317272</td><td>0.448009</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>7</td><td>vector0</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>N/A</td><td>0.542606</td><td>8686</td><td>0.391555</td><td>0.074708</td><td>0.527444</td><td>0.693251</td><td>0.554095</td><td>0.590947</td><td>2.400033</td><td>0.399948</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr></table>

详细的字段说明和性能分析工具的具体使用方法请参考上板性能数据采集。 

# 算子仿真流水图

算子调优工具msProf支持仿真环境下的性能数据采集和自动解析。使用msProf工具获 取仿真流水图的具体方式请参考指令流水图。 

支持以下两种可视化呈现方式： 

Chrome浏览器 

在Chrome浏览器中输入“chrome://tracing”地址，并将通过msprof op simulator生成指令流水图文件（trace.json）拖到空白处打开，键盘上输入快捷键 （W：放大，S：缩小，A：左移，D：右移）可进行查看。 

![](images/f0f2b9f4182e1a0256a0914db9c1b4018747e6439224e3eedcc05a87abc71d98.jpg)


指令流水图支持MindStudio Insight可视化呈现，MindStudio Insight工具以时序 图方式为用户提供指令在昇腾AI处理器上的运行情况，用户可通过分析时序图中 的指令详情、指令执行时间、指令关联代码的调用栈及指令/流水间同步连线等信 息，识别微观指令的时序优化点。 


图3-83 时间线界面


![](images/b0581724605bc764c217eed153eab5752875e66a500bdb8ee4996a0337fb58a3.jpg)


# 说明

本文部分样例中展示的算子仿真流水图和上述两种可视化呈现方式不一致，但是其中的关键字段 含义是对应的，开发者可以参考指令流水图查看具体字段的含义。 

# 3.7.2 分析性能数据

# 理论参数

理论性能为算子实际性能的理想目标。不同的硬件平台的硬件规格各异，理论性能可 以帮助我们了解硬件的潜能，从而设定性能优化的目标。 

搬运相关流水（MTE1/MTE2/MTE3等）的理论耗时 $=$ 搬运数据量（单位： Byte） / 理论带宽。例如：某款AI处理器的GM峰值带宽约为1.8TB/s，想要进行 一次float数据类型、4096 * 4096大小的矩阵搬运，搬运的理论耗时是 sizeof(float) * 4096 * 4096 / 1.8TB/s = 37.28us（按照1TB =1012Byte来计算）。 

# 说明

● 搬运指令同时存在时，会存在共享带宽的情况，并不能每条都以接近理论带宽的速率搬 运数据。比如，当MTE2/MTE3同时进行GM读写时，搬运流水线的耗时应该是（MTE2 搬运量 $^ +$ MTE3搬运量）/ GM带宽。 

● 搬运不同大小的数据块时，对带宽的利用率（有效带宽/理论带宽）不一样。针对每次 搬运数据量较小的情况，实测性能达不到理论带宽。 

计算相关流水（Cube/Vector/Scalar等）的理论耗时 $=$ 计算数据量（单位： Element） / 理论算力。例如：某款AI处理器对float数据类型的Vector理论峰值算 力为11.06TOPS，想要进行一次32K float类型的Element单指令计算，计算的理 论耗时是32K / 11.06TOPS = 0.003us （按照1K =1000来计算）。 

# 查找瓶颈

获取性能数据后，和理论数值差异较大的地方、耗时较长的流程被认为是“瓶颈 点”。下文将介绍如何通过性能数据找到瓶颈点和对应的优化方向。 

# ● 方法一：通过上板Profiling分析流水情况

查看上板Profiling解析后的op_summary_*.csv文件分析流水情况。注：“*”表示 时间戳。 

# 说明

在SIMD与SIMT混合编程场景中，由于硬件架构的固有特性，所有计算任务均以VF （Vector Function）为基本调度执行单元。因此，在Profiling数据中，SIMT和SIMD的VF 整体执行时间均被统计为aiv_vec_time。特别地，SIMT VF执行过程中对Global Memory的 读写耗时，也会被统计至aic_vec_time指标内。 


图 3-84 op_summary_*.csv 示例一


<table><tr><td colspan="2">E</td><td colspan="2">F</td><td colspan="2">G</td><td colspan="2">H</td><td colspan="2">M</td><td>N</td><td>O</td><td>T</td><td>U</td><td>V</td><td>W</td><td>X</td><td>Y</td><td>Z</td><td>AA</td><td>AB</td><td>AC</td><td>AD</td><td>AE</td></tr><tr><td colspan="2">OP Type</td><td colspan="2">Task Type</td><td colspan="2">Task Start Time(s)</td><td colspan="2">Task Duration (s)</td><td>Back Dim</td><td>Input Shapes</td><td>Input Data types</td><td>Input Format</td><td>Format.T</td><td>acore温,ic,ac,total,ac,mac,bin,ac,arc,ac,scalar,ac,scalar, ratio</td><td>ac,temperature, ratio</td><td>ac,scalar, ratio</td><td>ac,temperature, ratio</td><td>ac,temperature, ratio</td><td>ac,temperature, ratio</td><td>ac,temperature, ratio</td><td>ac,temperature, ratio</td><td>ac,temperature, ratio</td><td>ac,temperature, ratio</td><td></td></tr><tr><td>1</td><td>MatMuV2</td><td colspan="2">AL Core</td><td colspan="2">1708651523293048 790</td><td colspan="2">1062.76</td><td colspan="2">24 &quot;2048.1288.12288.644.6144&quot;</td><td>DT.BF16DT.BF16FLOAT</td><td>FORMAT.T</td><td>10953.47302754</td><td>878.507</td><td>0.829</td><td>1195.905</td><td>0.109</td><td>765.658</td><td>0.723</td><td>1004.115</td><td>0.948</td><td>32.307</td><td>0.03</td><td></td></tr><tr><td>5</td><td>MatMuV2</td><td colspan="2">AL CORE</td><td colspan="2">1708651523295561 330</td><td colspan="2">1127</td><td colspan="2">24 &quot;2048.1288.12288.644.6144&quot;</td><td>DT.BF16DT.BF16FLOAT</td><td>FORMAT.T</td><td>1123.0949856177</td><td>878.274</td><td>0.782</td><td>1172.304</td><td>0.124</td><td>763.902</td><td>0.68</td><td>1058.137</td><td>0.942</td><td>32.252</td><td>0.029</td><td></td></tr><tr><td>7</td><td>MatMuV2</td><td colspan="2">AL CORE</td><td colspan="2">1708651523233103 040</td><td colspan="2">1057.58</td><td colspan="2">24 &quot;2048.1288.12288.644.6144&quot;</td><td>DT.BF16DT.BF16FLOAT</td><td>FORMAT.T</td><td>1052.2245671879</td><td>878.339</td><td>0.835</td><td>1154.622</td><td>0.111</td><td>766.424</td><td>0.728</td><td>1001.678</td><td>0.952</td><td>32.809</td><td>0.031</td><td></td></tr><tr><td>9</td><td>MatMuV2</td><td colspan="2">AL CORE</td><td colspan="2">1708651523266229 10</td><td colspan="2">1126.48</td><td colspan="2">24 &quot;2048.1288.12288.644.6144&quot;</td><td>DT.BF16DT.BF16FLOAT</td><td>FORMAT.T</td><td>1123.0949856177</td><td>878.274</td><td>0.782</td><td>1172.304</td><td>0.124</td><td>763.902</td><td></td><td>0.68</td><td>1058.137</td><td>0.942</td><td>32.252</td><td>0.029</td></tr><tr><td>13</td><td>MatMuV2</td><td colspan="2">AL CORE</td><td colspan="2">1708651523331327 790</td><td colspan="2">1061.56</td><td colspan="2">24 &quot;2048.1288.12288.644.6144&quot;</td><td>DT.BF16DT.BF16FLOAT</td><td>FORMAT.T</td><td>1057.7846965384</td><td>878.192</td><td>0.83</td><td>1153.902</td><td>0.111</td><td>765.658</td><td>0.724</td><td>1005.104</td><td>0.95</td><td>32.442</td><td>0.031</td><td></td></tr><tr><td>8</td><td>MatMuV2</td><td colspan="2">AL CORE</td><td colspan="2">1708651523315745 090</td><td colspan="2">1127.96</td><td colspan="2">24 &quot;2048.1288.12288.644.6144&quot;</td><td>DT.BF16DT.BF16FLOAT</td><td>FORMAT.T</td><td>1124.1244991394</td><td>878.061</td><td>0.781</td><td>1171.109</td><td>0.124</td><td>762.947</td><td>0.679</td><td>1064.691</td><td>0.947</td><td>33.504</td><td>0.03</td><td></td></tr><tr><td>9</td><td>MatMuV2</td><td colspan="2">AL CORE</td><td colspan="2">1708651523333238 590</td><td colspan="2">1057.5</td><td colspan="2">24 &quot;2048.1288.12288.644.6144&quot;</td><td>DT.BF16DT.BF16FLOAT</td><td>FORMAT.T</td><td>1054.8446834740</td><td>878.233</td><td>0.833</td><td>1153.788</td><td>0.111</td><td>766.915</td><td>0.727</td><td>999.274</td><td>0.947</td><td>32.26</td><td>0.031</td><td></td></tr><tr><td>10</td><td>MatMuV2</td><td colspan="2">AL CORE</td><td colspan="2">1708651523333334 10</td><td colspan="2">1128.48</td><td colspan="2">24 &quot;2048.1288.12288.644.6144&quot;</td><td>DT.BF16DT.BF16FLOAT</td><td>FORMAT.T</td><td>1055.1094675778</td><td>878.239</td><td>0.83</td><td>1153.902</td><td>0.124</td><td>764.09</td><td>0.724</td><td>1005.104</td><td>0.95</td><td>32.52</td><td>0.03</td><td></td></tr><tr><td>15</td><td>MatMuV2</td><td colspan="2">AL CORE</td><td colspan="2">1708651523333431 1670</td><td colspan="2">1055.94</td><td colspan="2">24 &quot;2048.1288.12288.644.6144&quot;</td><td>DT.BF16DT.BF16FLOAT</td><td>FORMAT.T</td><td>1052.9946752778</td><td>878.299</td><td>0.834</td><td>1153.867</td><td>0.111</td><td>766.441</td><td>0.728</td><td>1001.227</td><td>0.951</td><td>32.132</td><td>0.031</td><td></td></tr><tr><td>10</td><td>MatMuV2</td><td colspan="2">AL CORE</td><td colspan="2">1708651523333591 370</td><td colspan="2">1123.58</td><td colspan="2">24 &quot;2048.1288.12288.644.6144&quot;</td><td>DT.BF16DT.BF16FLOAT</td><td>FORMAT.T</td><td>1116.7849558249</td><td>877.94</td><td>0.786</td><td>1173.305</td><td>0.105</td><td>763.109</td><td>0.683</td><td>1057.014</td><td>0.946</td><td>33.679</td><td>0.03</td><td></td></tr><tr><td>11</td><td>MatMuV2</td><td colspan="2">AL CORE</td><td colspan="2">1708651523334446 170</td><td colspan="2">1065.36</td><td colspan="2">24 &quot;2048.1288.12288.644.6144&quot;</td><td>DT.BF16DT.BF16FLOAT</td><td>FORMAT.T</td><td>1060.6247100488</td><td>878.344</td><td>0.828</td><td>1154.457</td><td>0.109</td><td>765.631</td><td>0.722</td><td>1010.312</td><td>0.952</td><td>32.933</td><td>0.031</td><td></td></tr><tr><td>12</td><td>MatMuV2</td><td colspan="2">AL CORE</td><td colspan="2">170865152333533 170</td><td colspan="2">1065.36</td><td colspan="2">24 &quot;2048.1288.12288.644.6144&quot;</td><td>DT.BF16DT.BF16FLOAT</td><td>FORMAT.T</td><td>1060.6247100488</td><td>878.344</td><td>0.828</td><td>1154.457</td><td>-0.109</td><td>765.631</td><td>0.722</td><td>1010.312</td><td>0.952</td><td>32.933</td><td>0.031</td><td></td></tr><tr><td>7</td><td>MatMuV2</td><td colspan="2">AL CORE</td><td colspan="2">1708651523335353 870</td><td colspan="2">1051.32</td><td colspan="2">24 &quot;2048.1288.12288.644.6144&quot;</td><td>DT.BF16DT.BF16FLOAT</td><td>FORMAT.T</td><td>1046.5846647939</td><td>878.525</td><td>0.829</td><td>1153.776</td><td>0.111</td><td>766.089</td><td>0.734</td><td>982.836</td><td>0.939</td><td>30.83</td><td>0.029</td><td></td></tr><tr><td>2</td><td>MatMuV2</td><td colspan="2">AL CORE</td><td colspan="2">1708651523356021 330</td><td colspan="2">1122.78</td><td colspan="2">24 &quot;2048.1288.12288.644.6144&quot;</td><td>DT.BF16DT.BF16FLOAT</td><td>FORMAT.T</td><td>1118.8649775688</td><td>878.072</td><td>0.785</td><td>1174.402</td><td>0.105</td><td>763.139</td><td>0.682</td><td>1058.795</td><td>0.946</td><td>33.908</td><td>0.03</td><td></td></tr><tr><td>47</td><td>MatMuV2</td><td colspan="2">AL CORE</td><td colspan="2">1708651523356904 310</td><td colspan="2">1058.68</td><td colspan="2">24 &quot;2048.1288.12288.644.6144&quot;</td><td>DT.BF16DT.BF16FLOAT</td><td>FORMAT.T</td><td>1055.1084687482</td><td>878.444</td><td>0.833</td><td>1153.919</td><td>0.111</td><td>765.667</td><td>0.726</td><td>1004.538</td><td>0.952</td><td>32.453</td><td>0.031</td><td></td></tr><tr><td>10</td><td>MatMuV2</td><td colspan="2">AL CORE</td><td colspan="2">1708651523356904 310</td><td colspan="2">1058.68</td><td colspan="2">24 &quot;2048.1288.12288.644.6144&quot;</td><td>DT.BF16DT.BF16FLOAT</td><td>FORMAT.T</td><td>1055.1084687498</td><td>878.444</td><td>0.833</td><td>1153.919</td><td>0.111</td><td>765.667</td><td>0.726</td><td>1004.538</td><td>0.952</td><td>32.453</td><td>0.031</td><td></td></tr><tr><td>03</td><td>MatMuV2</td><td colspan="2">AL CORE</td><td colspan="2">1708651523571614 190</td><td colspan="2">1062.98</td><td colspan="2">24 &quot;2048.1288.12288.644.6144&quot;</td><td>DT.BF16DT.BF16FLOAT</td><td>FORMAT.T</td><td>1058.4346994158</td><td>878.487</td><td>0.83</td><td>1153.506</td><td>0.105</td><td>766.798</td><td>0.724</td><td>1003.207</td><td>0.948</td><td>32.579</td><td>0.031</td><td></td></tr><tr><td>08</td><td>MatMuV2</td><td colspan="2">AL CORE</td><td colspan="2">1708651523578616 070</td><td colspan="2">1125.08</td><td colspan="2">24 &quot;2048.1288.12288.644.6144&quot;</td><td>DT.BF16DT.BF16FLOAT</td><td>FORMAT.T</td><td>1121.1249777596</td><td>878.606</td><td>0.784</td><td>1173.308</td><td>0.105</td><td>764.251</td><td>0.682</td><td>104.86</td><td>0.935</td><td>33.713</td><td>0.03</td><td></td></tr><tr><td>59</td><td>MatMuV2</td><td colspan="2">AL CORE</td><td colspan="2">1708651523598211 630</td><td colspan="2">1058.36</td><td colspan="2">24 &quot;2048.1288.12288.644.6144&quot;</td><td>DT.BF16DT.BF16FLOAT</td><td>FORMAT.T</td><td>1055.7746874984</td><td>878.221</td><td>0.832</td><td>1153.916</td><td>0.111</td><td>766.252</td><td>0.726</td><td>1004.533</td><td>0.952</td><td>31.905</td><td>0.03</td><td></td></tr></table>

每条流水线的利用率理想情况下应为100%，没有达到100%的流水就可能有提升 空间。上图示例中为某款AI处理器上获取的数据，可以看到Cube算子 

MatMulV2，Cube流水的利用率aic_mac_ratio在80%左右，初步判断没有充分发 挥算力；MTE2流水的利用率aic_mte2_ratio已经在95%左右，判断MTE2是最长 的流水。 

然后比较最长的流水和理论的差距：输入左右矩阵的shape分别为（2048， 12288）、（12288，6144），数据类型为bfloat16；Bias输入的shape为 （6144），数据类型为float。由此可以计算出总共需要搬运的数据量，继而通过 理论参数中介绍的搬运流水理论耗时计算方法计算出理论值为(sizeof(bfloat16) * (2048 * 12288 + 12288 * 6144) + sizeof(float) * 6144) / 1.8TB/s ≈ 111.8us （按 照1TB =1012Byte来计算），与实际性能数据aic_mte2_time存在比较大的差距。 经分析输入数据的总大小已经超过L1的空间（512KB），做MatMul计算会存在输 入矩阵数据重复搬运的情况，重复搬运的次数是否合理，需要结合流水优化和 Tiling优化手段进行优化，可参考方法三、查看仿真流水图分析各条流水的情况进 一步分析。 


图 3-85 op_summary_*.csv 示例二


<table><tr><td></td><td>G</td><td>H</td><td>J</td><td>M</td><td>N</td><td>O</td><td>P</td><td>Q</td><td>R</td><td>AG</td><td>AH</td><td>AI</td><td>AJ</td><td>AK</td><td>AL</td><td>AM</td><td>AN</td><td>AO</td><td>AP</td></tr><tr><td>t</td><td>Start Time(μs)</td><td>Duration(μs)</td><td>Block Dim</td><td>Input Shapes</td><td>Input Data Types</td><td>Input Formats</td><td>Output Shapes</td><td>Output Data Types</td><td>Output Formats</td><td>av_time(μs)</td><td>av_total cycles</td><td>av_vec_ti me(μs)</td><td>av_vec_taio</td><td>avScalar_time(μs)</td><td>avScalar_ratio</td><td>av_mte2(time(μs))</td><td>av_ratio2</td><td>av_mte3(time(μs))</td><td>av_mte3 ratio</td></tr><tr><td>0</td><td>1.7E+15</td><td>350.3</td><td>40</td><td>&quot;8192,1,8192&quot;</td><td>FLOAT</td><td>FORMAT &quot;8192,1,8192&quot;</td><td>DTBF16</td><td>FLOAT format</td><td>346.8</td><td>24971839</td><td>19.7136</td><td>0.0568</td><td>1.8592</td><td>0.0054</td><td>343.7998</td><td>0.9913</td><td>137.559</td><td>0.3966</td><td></td></tr><tr><td>1</td><td>1.7E+15</td><td>349.92</td><td>40</td><td>&quot;8192,1,8192&quot;</td><td>FLOAT</td><td>FORMAT &quot;8192,1,8192&quot;</td><td>DTBF16</td><td>FLOAT format</td><td>346.2</td><td>24926318</td><td>19.7137</td><td>0.0569</td><td>1.8618</td><td>0.0054</td><td>342.772</td><td>0.9913</td><td>137.6721</td><td>0.3977</td><td></td></tr></table>

上图示例中算子输入的shape为（8192，8192），数据类型为float。由此可以计 算出总共需要搬运的数据量，继而通过理论参数中介绍的搬运流水理论耗时计算 方法计算出理论值为sizeof(float) * (8192 * 8192) / 0.8TB/s ≈ 335.5us （按照 1TB =1012Byte来计算，不同的AI处理器其理论带宽有差异），与实际性能数据 aiv_mte2_time相符，可以判断该算子基本是一个搬运MTE2 bound（达到上限） 的算子。本示例中总体执行时间Duration为350us，和MTE2的实际耗时持平，说 明该算子已经调优完成。如果MTE2耗时和总体执行时间有较大差距，那么下一步 优化方向主要是流水优化结合Tiling优化，使得其他的流水尽量隐藏在MTE2的流 水中，可参考方法三、查看仿真流水图分析各条流水的情况进行进一步分析。 

# 方法二：通过上板Profiling分析Tiling情况

查看上板Profiling解析后的op_summary_*.csv文件分析Tiling情况。 


图 3-86 op_summary_*.csv 示例


<table><tr><td>OP Type</td><td>Task Type</td><td>Task Start Time(us)</td><td>Task Duration(US)</td><td>Block Dim</td><td>Input Shapes</td><td>Input Data Types</td><td>Input Form</td></tr><tr><td>Mul</td><td>AL_VECTOR_COR</td><td>1706851252899848.070</td><td>1122.96</td><td>48</td><td>&quot;14592,12288;&quot;</td><td>FLOAT,FLOAT</td><td>FOR</td></tr><tr><td>Mul</td><td>AL_VECTOR_COR</td><td>1706851252902039.430</td><td>3.24</td><td>12</td><td>&quot;12288;&quot;</td><td>FLOAT,FLOAT</td><td>FOR</td></tr><tr><td>Mul</td><td>AL_VECTOR_COR</td><td>1706851252902057.450</td><td>3.42</td><td>12</td><td>&quot;12288;&quot;</td><td>FLOAT,FLOAT</td><td>FOR</td></tr><tr><td>Mul</td><td>AL_VECTOR_COR</td><td>1706851252902076.310</td><td>3.06</td><td>12</td><td>&quot;12288;&quot;</td><td>FLOAT,FLOAT</td><td>FOR</td></tr><tr><td>Mul</td><td>AL_VECTOR_COR</td><td>1706851252902095.030</td><td>3</td><td>12</td><td>&quot;12288;&quot;</td><td>FLOAT,FLOAT</td><td>FOR</td></tr><tr><td>Mul</td><td>AL_VECTOR_COR</td><td>1706851252902113.930</td><td>2.98</td><td>12</td><td>&quot;12288;&quot;</td><td>FLOAT,FLOAT</td><td>FOR</td></tr><tr><td>Mul</td><td>AL_VECTOR_COR</td><td>1706851252902132.930</td><td>2.96</td><td>12</td><td>&quot;12288;&quot;</td><td>FLOAT,FLOAT</td><td>FOR</td></tr><tr><td>Mul</td><td>AL_VECTOR_COR</td><td>1706851252902286.730</td><td>31.72</td><td>48</td><td>&quot;1536,12288;&quot;</td><td>FLOAT,FLOAT</td><td>FOR</td></tr><tr><td>Mul</td><td>AL_VECTOR_COR</td><td>1706851252902361.790</td><td>3.3</td><td>12</td><td>&quot;12288;&quot;</td><td>FLOAT,FLOAT</td><td>FOR</td></tr><tr><td>Mul</td><td>AL_VECTOR_COR</td><td>1706851252902876.890</td><td>392.28</td><td>48</td><td>&quot;4608,12288;&quot;</td><td>FLOAT,FLOAT</td><td>FOR</td></tr><tr><td>Mul</td><td>AL_VECTOR_COR</td><td>1706851252903611.830</td><td>2.18</td><td>5</td><td>&quot;4608;&quot;</td><td>FLOAT,FLOAT</td><td>FOR</td></tr><tr><td>Mul</td><td>AL_VECTOR_COR</td><td>1706851252904186.570</td><td>492.82</td><td>48</td><td>&quot;12288,6144;&quot;</td><td>FLOAT,FLOAT</td><td>FOR</td></tr><tr><td>Mul</td><td>AL_VECTOR_COR</td><td>1706851252905129.550</td><td>1.92</td><td>6</td><td>&quot;6144;&quot;</td><td>FLOAT,FLOAT</td><td>FOR</td></tr><tr><td>Mul</td><td>AL_VECTOR_COR</td><td>1706851252905703.770</td><td>491.86</td><td>48</td><td>&quot;6144,12288;&quot;</td><td>FLOAT,FLOAT</td><td>FOR</td></tr><tr><td>Mul</td><td>AL_VECTOR_COR</td><td>1706851252906650.210</td><td>2.76</td><td>12</td><td>&quot;12288;&quot;</td><td>FLOAT,FLOAT</td><td>FOR</td></tr><tr><td>Mul</td><td>AL_VECTOR_COR</td><td>1706851252906667.790</td><td>2.96</td><td>12</td><td>&quot;12288;&quot;</td><td>FLOAT,FLOAT</td><td>FOR</td></tr></table>

上图示例中为某款AI处理器上获取的数据，通过硬件平台可以查看该AI处理器有 48个Vector核，Mul算子是一个纯Vector算子，但是有些场景没有用满所有Vector 核（Block Dim < 48），造成算力浪费。那么下一步的主要优化方向为Tiling优 化。 

# 方法三：通过仿真流水图分析流水情况


图 3-87 仿真流水图示例


![](images/cccc58959d6135a58b8ac90b514ce2b4dbbfc3f4ae0cbae6318e98d37dce3f67.jpg)


上图示例中为某款AI处理器上获取的数据，可以看到Vector核的相关流水（vec0 的MTE2、MTE3，vec1的MTE2、MTE3等）有规律性的断流现象。可以结合算子 逻辑分析，是否存在数据依赖等因素导致断流。那么下一步的主要优化方向为流 水优化，其次结合Tiling优化和内存优化等手段进一步提升Vector流水利用率。 

# 方法四：通过上板Profiling查看头开销

头开销是算子执行计算前产生的时延，包含核启动、核取址TLB MISS、同地址访 问（由于硬件限制，多核同时访问相同内存地址冲突带来额外的时延）以及变量 资源初始化带来的时延。以Atlas A2 训练系列产品/Atlas A2 推理系列产品为例， 满核头开销约为20~21微秒。对于推理领域等本身延迟为微秒级别的算子，头开 销是一个值得优化的对象。 

通过上板Profiling数据（空Kernel时的TaskDuration数据）可以看到每个核的启 动开销耗时，继而通过使用恰当的核数和算子Kernel Type等方法来不断的实践， 尝试找到最优的配置，具体优化方向可以参考3.8.3 头尾开销优化。