<!-- Source: 算子开发工具.md lines 592-601 | Section: 3.1 工具概述 -->

# 3.1 工具概述

msKPP（MindStudio Kernel Performance Prediction）具有性能建模分析和基于 Ascend C模板库进行自动调优的功能，具体介绍如下： 

3.3 性能建模：在算子开发前，可根据算子的数学逻辑作为输入，基于msKPP的 DSL语言，写出一个算子实现方案的算子表达式，获得该方案的算子性能建模结 果。由于本身针对性能的预测不需要进行真实的计算，仅需要依据输入和输出的 规模，给出对应算法的执行时间，故而，可以在秒级给出性能建模结果。 

3.4 调用msOpGen算子工程：msKPP工具提供的3.4.3.1 mskpp.tiling_func和 3.4.3.2 mskpp.get_kernel_from_binary接口，可以直接调用msOpGen算子工 程。 

3.5 自动调优：msKPP提供模板库Kernel下发代码生成、编译、运行的能力，同时 提供Kernel内代码替换并自动调优的能力。