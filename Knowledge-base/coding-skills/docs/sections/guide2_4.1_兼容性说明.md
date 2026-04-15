<!-- Source: 算子开发指南2.md lines 2914-2932 | Section: 4.1 兼容性说明 -->

# 4.1 兼容性说明

本兼容性说明仅适用于Ascend C算子开发的兼容性迁移指导。总体兼容性策略见表 4-1，兼容性范围不包含编译器BuiltIn API、Ascend C内部实现接口等。文档中涉及的 兼容性分为两类：一是功能兼容，包括数据类型兼容、接口原型兼容和常量兼容；二 是性能兼容，指对于同等数据量，新架构上执行API耗时不高于旧架构。 

若开发者希望在351x架构下运行原本在220x架构上开发的Ascend C程序，需在351x架 构上重新编译并运行，并可能需要根据迁移指导进行代码调整。 


图 4-1 Ascend C API 层次结构


![](images/55cd651fb208214530a958fefde6f21d3b227e5b9f9402a2075a02857016189d.jpg)



表 4-1 Ascend C API 兼容策略


<table><tr><td>API层级</td><td>兼容策略</td></tr><tr><td>高阶API</td><td>高阶API在所有架构上均兼容。</td></tr><tr><td>基础API</td><td>基础API分为可兼容的基础API和ISASI基础API；兼容的API在所有架构上均能兼容；ISASI API为体系架构相关的API，不保证跨架构版本的兼容性，例如CUBE侧的计算接口LoadData、Mmad等。</td></tr><tr><td>框架API</td><td>框架API为软件实现API，跨架构版本兼容。</td></tr><tr><td>编译器BuiltIn API</td><td>不保证兼容。</td></tr></table>