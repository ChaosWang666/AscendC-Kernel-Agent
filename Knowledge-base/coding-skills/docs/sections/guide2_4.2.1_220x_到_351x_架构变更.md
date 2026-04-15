<!-- Source: 算子开发指南2.md lines 2935-2999 | Section: 4.2.1 220x 到 351x 架构变更 -->

# 4.2.1 220x 到 351x 架构变更

351x架构图如图1所示，总体来看，351x架构新增了以下特性： 

新增多条数据通路。 

● AI Core核数增加。 

UB容量提升。 

新增SSBuffer核内存储单元，支持AIC核和AIV核通过Scalar访问。 

SIMD编程基础上，支持SIMT编程、SIMD与SIMT混合编程。 

AIV核采用Regbase架构，与220x的Membase架构相比，可以直接对芯片的 Vector寄存器Register进行操作，实现更大的灵活性和更好的性能。 


图 4-2 351x 架构图


![](images/2868e0168fabdee1298539611a82d97e0551fd708a93a99f5fbbbbe63aa02f90.jpg)


具体来说，351x架构的主要变更如下各表所示。除此之外，351x架构还扩展了支持的 数据类型，具体可参考数据类型介绍。 

搬运单元 


表 4-2 搬运单元变更


<table><tr><td>351x变更</td><td>产生的影响</td><td>影响的API接口</td></tr><tr><td>删除L1 Buffer到GM的数据通路。</td><td>现有接口不支持从L1 Buffer直接搬运数据到GM。开发者需要在L1 Buffer分配一块空间存放单位矩阵，利用MMAD矩阵乘法计算输出到LOC Buffer，从LOC Buffer通过FixPipe将数据搬运到GM。</td><td>DataCopy/DumpTensor</td></tr><tr><td>删除GM到L0ABuffer、L0B Buffer的数据通路。</td><td>原GM到L0A Buffer和L0BBuffer的数据搬运需要拆分为两步，即从GM到L1 Buffer的数据搬运和从L1 Buffer到L0ABuffer、L0B Buffer的数据搬运。</td><td>LoadData</td></tr><tr><td>新增UB到L1 Buffer的数据通路。</td><td>支持将数据直接从UB搬运到L1Buffer，而无需先从UB搬运到GM，再从GM搬运到L1Buffer，使用方式具体可参考基础数据搬运。</td><td>DataCopy</td></tr><tr><td>新增ND-DMA指令。</td><td>扩展DataCopy数据搬运接口的能力，相比基础数据搬运接口，可更加自由地配置搬入数据的维度信息及Stride，使用方式具体可参考多维数据搬运（ISASI）。</td><td>DataCopy</td></tr><tr><td>新增LOC Buffer到UB的单向数据通路。</td><td>支持将数据直接从LOC Buffer搬运到UB，而无需先从LOCBuffer搬运到GM，再从GM搬运到UB，使用方式具体可参考Fixpipe。</td><td>Fixpipe</td></tr><tr><td>扩展LoadData搬运指令。</td><td>新增支持MicroScaling（MX）场景的数据搬运，使用方式具体可参考LoadData。</td><td>LoadData</td></tr><tr><td>新增DN分型、L1Buffer-&gt;L0A Buffer不再支持transpose。</td><td>使用新特性具体可参考LoadDataWithTranspose。</td><td>LoadDataWithTranspose</td></tr><tr><td>Fixpipe新增NZ2DN随路转换（实现NZ到DN数据格式的随路变换）。</td><td>使用方式具体可参考Fixpipe。</td><td>Fixpipe</td></tr><tr><td>DataCopy搬运维度增强。</td><td>DataCopy支持L1 Buffer与GM之间，GM与UB之间通路的loop模式搬运，使用方式具体可参考SetLoopModePara。</td><td>DataCopy</td></tr><tr><td>351x架构版本中删除了与L0A Buffer和L0B Buffer初始化相关的硬件指令。</td><td>使用基础API InitConstValue将特定存储位置的LocalTensor初始化为某一具体数值，不支持直接初始化L0A Buffer、L0B Buffer上的LocalTensor。</td><td>InitConstValue</td></tr></table>

计算单元 


表 4-3 计算单元变更


<table><tr><td>351x变更</td><td>产生的影响</td><td>影响的API接口</td></tr><tr><td>Cube计算单元不支持s4类型。</td><td>对于int4b_t数据类型的矩阵乘计算，开发者需要先将int4b_t的数据Cast转换为int8_t类型，再进行Cube计算。</td><td>Mmad</td></tr><tr><td>Cube计算单元不支持LOA上ZZ到ZN的分形变化。</td><td>LOA切分场景下，矩阵乘需要重新计算左矩阵的LOA地址。</td><td>LoadData/LoadDataWithTranspose</td></tr><tr><td>Vector Core Membase架构切换到Regbase架构。</td><td>基础API部分场景性能降低。</td><td>基础API高维切分模式</td></tr><tr><td>硬件不支持Subnormal功能，当前使用软仿实现的Subnormal功能。</td><td>开发者需要通过设置config模板参数来配置Subnormal计算模式，具体请参考5.2.1-矢量计算。</td><td>Ln/_sqrt/Rsqrt/Div/Reciprocal/Exp</td></tr><tr><td>不支持4:2稀疏矩阵的计算。</td><td>开发者需要利用Vector Core的能力，进行矩阵稠密转稀疏操作。</td><td>LoadDataWithSparse/MmadWithSparse</td></tr></table>

# 存储单元


表4-4 存储单元变更


<table><tr><td>351x变更</td><td>产生的影响</td><td>影响的API接口</td></tr><tr><td>删除L1 Buffer空间的边界值设定。</td><td>351x架构硬件删除了L1 Buffer的边界值设定相关寄存器，不再支持SetLoadDataBoundary接口，具体请参考兼容方案。</td><td>SetLoadDataBoundary</td></tr><tr><td>UB结构变化。220x架构的UB结构和351x架构的UB结构对比请参考bank结构对比。</td><td>220x架构上UB分为16个bank group, 每个bank group包含3个bank, 每个bank大小为4KB。351x架构上UB分为8个bank group, 每个bank group包含2个bank, 每个bank大小为16KB。若发生UB冲突, 开发者可参考避免Unified Buffer的bank冲突解决UB冲突。</td><td>/</td></tr></table>

# 同步


表 4-5 同步变更


<table><tr><td>351x变更</td><td>产生的影响</td><td>影响的API接口</td></tr><tr><td>新增Mutex能力。</td><td>Mutex用于核内异步流水指令之间的同步处理，其功能类似于传统CPU中的锁机制。通过锁定指定流水再释放流水来完成流水间的同步依赖，使用方式具体可参考Mutex(ISASI)。</td><td>Mutex</td></tr><tr><td>新增核间同步控制模式。</td><td>对于AI Core内部的同步控制，AIV0与AIV1可单独触发AIC等待，使用方式具体可参考CrossCoreSetFlag(ISASI)。</td><td>CrossCoreSetFlag/CrossCoreWaitFlag</td></tr></table>

# 其它


表 4-6 其它变更


<table><tr><td>351x变更</td><td>产生的影响</td><td>影响的API接口</td></tr><tr><td>删除AIPP硬件级指令，采用软仿实现AIPP功能。</td><td>AIPP接口性能可能有所下降。</td><td>SetAippFunctions/LoadImageToLocal</td></tr><tr><td>由于351x架构版本中相关寄存器的删除，UB异常调试接口也被移除。</td><td>调测接口对功能无影响。</td><td>CheckLocalMemoryIA</td></tr></table>