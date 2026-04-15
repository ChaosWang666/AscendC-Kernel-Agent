<!-- Source: 算子开发指南.md lines 642-723 | Section: 1.1 什么是 Ascend C -->

# 1.1 什么是 Ascend C

Ascend C是CANN针对算子开发场景推出的编程语言，原生支持C和C++标准规范，兼 具开发效率和运行性能。基于Ascend C编写的算子程序，通过编译器编译和运行时调 度，运行在昇腾AI处理器上。使用Ascend C，开发者可以基于昇腾AI硬件，高效的实 现自定义的创新算法。您可以通过Ascend C主页了解更详细的内容。 

Ascend C提供多层级API，满足多维场景算子开发诉求。 

语言扩展层 C API：开放芯片完备编程能力，支持数组分配内存，一般基于指针 编程，提供与业界一致的C语言编程体验。 

基础API：基于Tensor进行编程的 ${ \mathsf { C } } { + } { + }$ 类库API，实现单指令级抽象，为底层算子 开发提供灵活控制能力。 

高阶API：封装单核公共算法，涵盖一些常见的计算算法（如卷积、矩阵运算 等），显著降低复杂算法开发门槛。 

算子模板库：基于模板提供算子完整实现参考，简化Tiling（切分算法）开发，支 撑用户自定义扩展。 

Python前端：PyAsc编程语言基于Python原生接口，提供芯片底层完备编程能 力，支持基于Python接口开发高性能Ascend C算子。 

![](images/1a28f1ef964e3da3ce57bb93bc24b427b14a8ae8fee590792b58ae5b2617bdff.jpg)


# 快速入门

从一个简单的样例出发，带您体验Ascend C算子开发的基本流程。 

# 成长地图

![](images/9eb77a522ef1698c23af7a88d721daf7877b08939917c6b6f6c1c84c5e4c9a6b.jpg)


# 概念原理

既涵盖基础概念供开发者快速查阅与参考，又深入解析核心架构设计与关键技术原理，满足高阶用户的深度探索需求。 

![](images/08da6e193f82cdfec7477ab3522847e942a1dac2118d6ef7b0460b861e27bea9.jpg)


# API 参考

AscendC提供一组类库API，开发者使用标准C++语法和类库API进行编程 

![](images/7a9b3d06d62b515f26dbdf30463c556ecf56f5d57e9f55dd9d8a7d88a41e3680.jpg)


# 算子实践参考

结合经验总结的性能优化手段和性能优化案例 

查看更多 

![](images/e4a6762a09dfd7cb91236d1f22abb4970de33679303ccdeae23383eb1a0ea22c.jpg)


性能优化 建议 

![](images/d0ba19d2558a6887cf76355e1bf1537cc5a39927724d06fccc0872d5f950093e.jpg)


FlashAttention 算子性能调优案例 

![](images/2cd473059a5900623a57e2b0a4717f96c57ec9f916d5efe862ea7dbcc12b2d2b.jpg)


Matmul 算子性能调优案例 

![](images/250601829651acab9cdcedf7d868fe4875b095b90699685142cc89028417b0ea.jpg)


MC2 算子性能调优案例 

# Ascend C支持在如下AI处理器型号使用：

Atlas 350 加速卡 

Atlas A3 训练系列产品/Atlas A3 推理系列产品 

1 Atlas A2 训练系列产品/Atlas A2 推理系列产品 

Atlas 200I/500 A2 推理产品 

Atlas 推理系列产品 

Atlas 训练系列产品