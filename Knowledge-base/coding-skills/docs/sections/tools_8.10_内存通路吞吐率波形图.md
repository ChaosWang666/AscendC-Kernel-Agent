<!-- Source: 算子开发工具.md lines 9396-9430 | Section: 8.10 内存通路吞吐率波形图 -->

# 8.10 内存通路吞吐率波形图

通过msprof op simulator生成的visualize_data.bin文件可通过MindStudio Insight进 行可视化呈现。界面支持查看算子MTE日志通路的内存带宽在时序上的统计分析能 力，可协助开发者识别算子各阶段的带宽使用状况，并分析带宽优化的可行性。具体 特性支持情况请参见图8-11。 

# 说明

● 若要使用MindStudio Insight进行查看时，需要单独安装MindStudio Insight软件包，具体下 载链接请参见《MindStudio Insight工具用户指南》的“安装与卸载”章节。 

● 将visualize_data.bin文件导入MindStudio Insight的具体操作请参考导入性能数据 《MindStudio Insight工具用户指南》的“算子调优 $>$ 导入性能数据”章节。 

MindStudio Insight具体操作和详细字段解释请参考《MindStudio Insight工具用户指南》 的“系统调优 $>$ 时间线（Timeline） ”章节。 

● 内存通路吞吐率波形图功能仅适用于Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组件和Atlas A3 训练系列产品/Atlas A3 推理系列产品。 

● 此功能默认不开启，--core-id设置对该功能不生效。 

# 内存通路吞吐率波形图


图 8-11 内存通路吞吐率波形图


![](images/3ecdba7291eaa8d7d917fe572ed7e1f203d3b6767fa5d8134d22cdd4206905ba.jpg)


展示各种类型内存通路（当前仅展示GM_TO_L1、GM_TO_TOTAL、 GM_TO_UB、L1_TO_GM、TOTAL_TO_GM、UB_TO_GM六个通路）的数据吞吐 率（单位为MB/s）。例如，GM_TO_UB表示从GM搬运到UB的吞吐率， GM_TO_TOTAL表示从GM搬运到各内存单元的吞吐率。 

结合MTE相关指令，观察执行相关命令时的吞吐率，协助用户识别算子性能问 题。 

# 说明

● 吞吐率计算所采用的数据是某一个指令多次请求结束时的数据。 

● 吞吐率波形图可能出现在某指令的起始时间和结束时间范围内（包含起始时间和结束时 间）。例如，持续时间为1~3微秒的指令，吞吐率数据可能分散在1~2微秒、2~3微秒 及3~4微秒三个柱状图内。