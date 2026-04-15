<!-- Source: 算子开发工具.md lines 4004-4015 | Section: 4.4 算子开发 -->

# 4.4 算子开发

# 操作步骤

步骤1 完成算子相关的开发适配，包括算子核函数的开发和tiling实现等，详细内容请参考 《Ascend C算子开发指南》中的“工程化算子开发 > 算子实现”章节。 

步骤2 可参考Link进行开发，完成op_host/add_custom_tiling.h、op_host/add_custom.cpp 和op_kernel/add_custom.cpp的实现。 

步骤3 算子实现完成后，进入4.5 算子编译部署。 

----结束