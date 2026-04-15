<!-- Source: 算子开发指南.md lines 1468-3103 | Section: 2.2 编程模型 -->

# 2.2 编程模型

# 2.2.1 异构并行编程模型

# Host-Device 异构协同机制

Ascend C异构并行编程模型是为应对异构计算架构的挑战而设计的，旨在解决传统编 程模型在处理复杂计算任务时的效率和可扩展性问题。 

异构计算架构分为Host侧和Device侧（Device侧对应AI处理器），两者协同完成计算 任务。Host侧主要负责运行时管理，包括存储管理、设备管理以及Stream管理等，确 保任务的高效调度与资源的合理分配；Device侧，会执行开发者基于Ascend C语法编 写的Kernel核函数，主要完成批量数据的矩阵运算、向量运算等计算密集型的任务， 用于计算加速。 

如下图所示，当一个Kernel下发到AI Core（AI处理器的计算核心）上执行时，运行时 管理模块根据开发者设置的核数和任务类型启动对应的Task，该Task从Host加载到 Device的Stream运行队列，调度单元会把就绪的Task分配到空闲AI Core上执行。这里 将需要处理的数据拆分并同时在多个计算核心上运行的方式，可以获取更高的性能。 


图 2-1 Kernel 调度示意图


![](images/fb55fe95b82c97bca931786021a1b6fdfb957bd67a6b752c7c7099c8fbe0ed2b.jpg)


Host和Device拥有不同的内存空间，Host无法直接访问Device内存，反之亦然。所 以，输入数据需要从Host侧拷贝至Device侧内存空间，供Device侧进行计算，输出结 果需要从Device侧内存拷贝回Host侧，便于在Host侧继续使用。 

# 说明

关于运行时管理的详细介绍请参考“ 运行时管理”章节。 

# 2.2.2 编程模型概述

AI Core是AI处理器的计算核心，AI处理器通过多个AI Core实现并行计算。与传统CPU 相比，AI处理器由于其内部拥有更多的计算单元和相应的向量计算指令，更适合模型 训练和推理场景，这使得单个硬件指令能完成多组数据的计算。AI处理器提供了以下 两种编程模型： 

SIMD（Single Instruction Multiple Data）：单指令多数据。通过单条指令多个 数据的方式实现并行计算。 

SIMT（Single Instruction Multiple Thread）：单指令多线程。通过单条指令多 个线程的方式实现并行计算。 

AI CPU是位于Device侧的处理器，其具备与AI Core相同的内存访问能力，可直接访问 Device侧的内存资源；它也可以像Host侧的CPU一样进行数据计算。 


表 2-1 编程模型分类


<table><tr><td>编程模型</td><td>计算空间</td><td>特点</td></tr><tr><td>SIMD编程</td><td>AI CORE</td><td>适合矩阵计算、连续计算的矢量算子及融合算子场景，提供SIMD与SIMT混合的高级编程方式。</td></tr><tr><td>SIMT编程</td><td>AI CORE</td><td>适用于离散访问场景、复杂分支控制场景。</td></tr><tr><td>AI CPU编程</td><td>AI CPU</td><td>作为AI Core计算的补充。</td></tr></table>

SIMD编程： 

适合矩阵计算、连续计算的矢量算子及融合算子场景。此外，结合这两种编程方 式的SIMD与SIMT混合编程，可以充分利用两者的优点，实现更佳的性能和更高 的效率。若需详细了解SIMD编程、SIMD与SIMT混合编程，请查阅2.2.3 AI Core SIMD编程。算子开发基本流程请参阅3.3 SIMD算子实现。 

SIMT编程： 

适用于离散访问场景、矢量算子的复杂分支控制场景，也便于熟悉SIMT算子开发 的人员快速掌握AI处理器上的算子开发，目前仅支持Atlas 350 加速卡；关于 SIMT编程的进一步学习，用户可参阅2.2.4 AI Core SIMT编程，了解详细的SIMT 编程原理，或阅读3.4 SIMT算子实现，学习SIMT算子开发的基本流程。 

AI CPU编程： 

通常作为AI Core的补充，主要承担非矩阵类、逻辑比较复杂的分支密集型计算。 您可通过阅读2.2.5 AI CPU编程，掌握AI CPU编程模型基础知识。 

# 2.2.3 AI Core SIMD 编程

# 2.2.3.1 抽象硬件架构

AI Core是AI处理器的计算核心，AI处理器内部有多个AI Core。本章节将介绍AI Core 的并行计算架构抽象，该抽象架构屏蔽了不同硬件之间的差异。使用Ascend C进行编 程时，基于抽象硬件架构，可以简化硬件细节，显著降低开发门槛。如需了解更详细 的硬件架构信息或者原理，请参考2.6 硬件实现。 


图 2-2 抽象硬件架构


![](images/d6a4385169255c79c347666caaa85cf4c28d2a995952d188873c6b683e41aed7.jpg)


AI Core中包含计算单元、存储单元、搬运单元等核心组件。 

计算单元包括了三种基础计算资源：Cube计算单元、Vector计算单元和Scalar计 算单元。 

存储单元包括内部存储和外部存储： 

AI Core的内部存储，统称为Local Memory，对应的数据类型为 LocalTensor。 

AI Core能够访问的外部存储称之为Global Memory，对应的数据类型为 GlobalTensor。 

DMA（Direct Memory Access）搬运单元：负责数据搬运，包括Global Memory 和Local Memory之间的数据搬运，以及不同层级Local Memory之间的数据搬 运。 

AI Core内部核心组件及组件功能详细说明如下表。 


表 2-2 AI Core 内部核心组件


<table><tr><td>组件分类</td><td>组件名称</td><td>组件功能</td></tr><tr><td rowspan="3">计算单元</td><td>Scalar</td><td>执行地址计算、循环控制等标量计算工作，并把向量计算、矩阵计算、数据搬运、同步指令发射给对应单元执行。</td></tr><tr><td>Vector</td><td>负责执行向量运算。</td></tr><tr><td>Cube</td><td>负责执行矩阵运算。</td></tr><tr><td>存储单元</td><td>Local Memory</td><td>AI Core的内部存储。</td></tr><tr><td>搬运单元</td><td>DMA（Direct Memory Access）</td><td>负责数据搬运，包括Global Memory和Local Memory之间的数据搬运以及不同层级Local Memory之间的数据搬运。</td></tr></table>

开发者在理解硬件架构的抽象时，需要重点关注如下异步指令流、同步信号流、计算 数据流三个过程： 

AI Core内部的异步并行计算过程：Scalar计算单元读取指令序列，并把向量计 算、矩阵计算、数据搬运指令发射给对应单元的指令队列，向量计算单元、矩阵 计算单元、数据搬运单元异步的并行执行接收到的指令。该过程可以参考图1中蓝 色箭头所示的指令流。 

不同的指令间有可能存在依赖关系，为了保证不同指令队列间的指令按照正确的 逻辑关系执行，Scalar计算单元也会给对应单元下发同步指令。各单元之间的同步 过程可以参考图1中的绿色箭头所示的同步信号流。 

AI Core内部数据处理的基本过程：DMA搬入单元将数据从Global Memory搬运到 Local Memory，Vector/Cube计算单元完成数据计算，并把计算结果写回Local Memory，DMA搬出单元把处理好的数据从Local Memory搬运回Global Memory。该过程可以参考图1中的红色箭头所示的数据流。 

# 2.2.3.2 核函数

核函数（Kernel Function）是Ascend C算子设备侧实现的入口。Ascend C允许用户使 用C/C++函数的语法扩展来编写设备端的运行代码，用户在核函数中进行数据访问和计 算操作，由此实现该算子的所有功能。区别于普通的C++函数调用时仅执行一次，当核 函数被调用时，多个核都执行相同的核函数代码，具有相同的函数入参，并行执行。 

核函数定义时需要使用函数类型限定符__global__和__aicore__；其指针入参变量需要 增加变量类型限定符__gm__，表明该指针变量指向Global Memory上某处内存地址； 使用<<<...>>>内核调用符调用执行核函数，并指定调用时的执行核数。 

以下是一个Add算子的核函数示例（代码片段）。 

```c
//实现核函数
global __aicore__void add_custom(_gm_uint8_t* x, _gm_uint8_t* y, _gm_uint8_t* z)
{
//初始化算子类，算子类提供算子初始化和核心处理等方法
KernelAdd op;
//初始化函数，获取该核函数需要处理的输入输出地址，同时完成必要的内存初始化工作
op.init(x, y, z);
//核心处理函数，完成算子的数据搬运与计算等核心逻辑
op.Process();
}
//调用核函数
void add_custom_do uint32_t numBlocks, void* l2ctrl, void* stream, uint8_t* x, uint8_t* y, uint8_t* z)
{
add_custom<<<numBlocks, l2ctrl, stream>>>(x, y, z);
} 
```

# 核函数定义和调用

定义核函数时需要遵循以下规则。 

# 使用函数类型限定符

除了需要按照 $\mathsf { C } / \mathsf { C } { + } { + }$ 函数声明的方式定义核函数之外，还要为核函数加上额外的函 数类型限定符，包含__global__和__aicore__。 

使用__global__函数类型限定符来标识它是一个核函数，可以被<<<...>>>调用； 使用__aicore__函数类型限定符来标识该核函数在设备端AI Core上执行： 

```txt
.global __aicore__void kernel_nameargument list); 
```

编程中使用到的函数可以分为三类：核函数（device侧执行）、host侧执行函 数、device侧执行函数（除核函数之外）。下图以Kernel直调算子开发方式为例描 述三者的调用关系： 

host侧执行函数可以调用同类的host执行函数，也就是通用C/C++编程中的函 数调用；也可以通过<<<...>>>调用核函数。 

device侧执行函数（除核函数之外）可以调用同类的device侧执行函数。 

核函数可以调用device侧执行函数（除核函数之外）。 


图 2-3 核函数、host 侧执行函数、device 侧执行函数调用关系


![](images/3bb90342efb550921797852309429ede7b6147af6888e40565f79793989089f4.jpg)


# 使用变量类型限定符

指针入参变量需要增加变量类型限定符__gm__，表明该指针变量指向Global Memory上某处内存地址。 

# 其他规则或建议

a. 规则：核函数必须具有void返回类型。 

b. 规则：仅支持入参为指针或 $\subset / { \mathsf { C } } ^ { + + }$ 内置数据类型（Primitive data types）， 如：half* s0、float* s1、int32_t c。 

c. 建议：为了统一表达，建议使用GM_ADDR宏来修饰入参，GM_ADDR宏定义 如下： 

```m4
define GM_ADDR __gm__ uint8_t* 
```

使用GM_ADDR修饰入参的样例如下： 

```txt
extern "C" __global__ __aicore__ void addCustom(GM_ADDR x, GM_ADDR y, GM_ADDR z) 
```

这里统一使用uint8_t类型的指针，在后续的使用中需要将其转化为实际的指 针类型。 

常见的函数调用方式是如下的形式： 

```javascript
function_name(argoment list); 
```

核函数使用内核调用符<<<...>>>这种语法形式，来规定核函数的执行配置： 

```cpp
kernel_name<<<numBlocks, l2ctrl, stream>>>(argument list); 
```

内核调用符仅可在NPU侧编译时调用，CPU侧编译无法识别该符号。 

执行配置由3个参数决定： 

numBlocks，规定了核函数将会在几个核上执行。每个执行该核函数的核会被分 配一个逻辑ID，即block_idx，可以在核函数的实现中调用GetBlockIdx来获取 block_idx； 

# 说明

numBlocks是逻辑核的概念，取值范围为[1,65535]。为了充分利用硬件资源，一般设置为 物理核的核数或其倍数。 

● 对于耦合模式和分离模式，numBlocks在运行时的意义和设置规则有一些区别，具体说 明如下： 

耦合模式：由于其Vector、Cube单元是集成在一起的，numBlocks用于设置启动 多个AI Core核实例执行，不区分Vector、Cube。AI Core的核数可以通过 GetCoreNumAiv或者GetCoreNumAic获取。 

分离模式 

针对仅包含Vector计算的算子，numBlocks用于设置启动多少个Vector （AIV）实例执行，比如某款AI处理器上有40个Vector核，建议设置为40。 

针对仅包含Cube计算的算子，numBlocks用于设置启动多少个Cube（AIC） 实例执行，比如某款AI处理器上有20个Cube核，建议设置为20。 

针对Vector/Cube融合计算的算子，启动时，按照AIV和AIC组合启动， numBlocks用于设置启动多少个组合执行，比如某款AI处理器上有40个 Vector核和20个Cube核，一个组合是2个Vector核和1个Cube核，建议设置 为20，此时会启动20个组合，即40个Vector核和20个Cube核。注意：该场 景下，设置的numBlocks逻辑核的核数不能超过物理核（2个Vector核和1 个Cube核组合为1个物理核）的核数。 

AIC/AIV的核数分别通过GetCoreNumAic和GetCoreNumAiv接口获取。 

● 如果开发者使用了Device资源限制特性，那么算子设置的numBlocks不应超过 PlatformAscendC提供核数的API（GetCoreNum/GetCoreNumAic/GetCoreNumAiv 等）返回的核数。例如，使用aclrtSetStreamResLimit设置Stream级别的Vector核数为 8，那么GetCoreNumAiv接口返回值为8，针对Vector算子设置的numBlocks不应超过 8，否则会抢占其他Stream的资源，导致资源限制失效。 

l2ctrl，保留参数，暂时设置为固定值nullptr，开发者无需关注； 

stream，类型为aclrtStream，stream用于维护一些异步操作的执行顺序，确保按 照应用程序中的代码调用顺序在device上执行。stream创建等管理接口请参考 “Stream管理”章节。 

如下名为add_custom的核函数，实现两个矢量的相加，调用示例如下： 

```txt
// numBlocks设置为8表示在8个核上调用了addcustom核函数，每个核都会独立且并行地执行该核函数，该核函数的参数列表为x，y，z。  
add_custom<<8, nullptr, stream>>>(x, y, z); 
```

核函数的调用是异步的，核函数的调用结束后，控制权立刻返回给主机端，可以调用 以下aclrtSynchronizeStream函数来强制主机端程序等待所有核函数执行完毕。 

```txt
aclError aclrtSynchronizeStream(aclrtStream stream); 
```

# 模板核函数定义和调用

支持开发者使用模板定义核函数，核函数定义示例如下，它有两个模板参数：a和T。a 是一个非类型模板参数，T是一个类型模板参数。 

```cpp
template<int a, typename T> global __aicore__ void add_custom(GM_ADDR x, GM_ADDR y, GM_ADDR z) {
    AscendC::printf("Print Template a: %d\n", a);
    xGm.SetGlobalBuffer((gm_T*)x + BLOCK_LENGTH * AscendC::GetBlockIdx(), BLOCK_LENGTH);
    yGm.SetGlobalBuffer((gm_T*)y + BLOCK_LENGTH * AscendC::GetBlockIdx(), BLOCK_LENGTH);
    zGm.SetGlobalBuffer((gm_T*)z + BLOCK_LENGTH * AscendC::GetBlockIdx(), BLOCK_LENGTH);
} 
```

模板核函数的调用方式如下：add_custom<20, float>这部分代码调用了名为 add_custom的核函数，并为其模板参数提供了具体值。 

add_custom $<  20$ float $> <   <   <   \text{numBlocks}$ , nullptr, stream>>>(x,y,z); 

# 2.2.3.3 SIMD 编程

# 2.2.3.3.1 基于 TPipe 和 TQue 编程

编程范式描述了算子核函数实现的固定流程，基于编程范式进行编程，可以快速搭建 算子实现的代码框架。 

根据2.2.3.1 抽象硬件架构，AI Core内部的执行单元异步并行地执行接收到的指令，各 执行单元配合，以一种流水线的方式完成完整的算子执行过程。 

通过下图可以更直观地理解流水并行的概念。示意图中，从输入数据到输出数据需要 经过3个阶段任务的处理（T1、T2、T3），多个执行单元并行处理，每个执行单元只 会专注于一个任务的处理，会处理所有的数据分片；执行单元完成对某个数据分片的 处理后，将其加入到通信队列，下一个执行单元空闲时就会从队列中取出数据继续处 理；可以类比为生产流水线中的工人只完成某一项固定工序，完成后就交由下一项工 序负责人继续处理。 


图 2-4 流水线并行示意图


![](images/47d14ea5353da9a137ddc7ce7d83014ba127873f856ed3e4d7043e3c303efb5b.jpg)


Ascend C编程范式正是这样一种流水线式的编程范式，把算子核内的处理程序，分成 多个流水任务，通过队列（TQue）完成任务间通信和同步，并通过统一的资源管理模 块（TPipe）来统一管理内存、事件等资源。 

下文将从三种典型的算子类型出发，对这种基于TPipe和TQue的编程范式进行详细介 绍。 

矢量编程范式 

矩阵编程范式 

融合算子编程范式 

# 矢量编程范式

![](images/085d9f7c425acc8d6e37fee485234e2c668918cadeb6288bf665c16fea7cf2f5.jpg)


# 融合算子编程范式

如上图所示，矢量编程范式把算子的实现流程分为3个基本任务：CopyIn， Compute，CopyOut。 

CopyIn负责搬入操作：将输入数据从Global Memory搬运到Local Memory （VECIN用于表达矢量计算搬入数据的存放位置），完成搬运后执行入队列操 作； 

Compute负责矢量指令计算操作：完成队列出队后，从Local Memory获取数据 并计算，计算完成后执行入队操作； 

CopyOut负责搬出操作：完成队列出队后，将计算结果从Local Memory （VECOUT用于表达矢量计算搬出数据的存放位置）搬运到Global Memory。 

上文中提到的VECIN/VECOUT是TPosition的概念。Ascend C管理不同层级的物理内存 时，用一种抽象的逻辑位置（TPosition）来表达各级别的存储，代替了片上物理存储 的概念，达到隐藏硬件架构的目的。除了VECIN/VECOUT，矢量编程中还会使用到 VECCALC，一般在定义临时变量时使用此位置。TPosition与物理内存的映射关系请参 考表1。 

从编程的角度来讲，具体流程（如下文的伪代码）和流程图如下： 

![](images/bff0eecf8277631d9a6b688f68029ff072e0fd8a3f144f089a1f5f9cc5b75b92.jpg)


AscendC::TPipe pipe; //创建全局的资源管理  
AscendC::TQue<TPosition::VecIn,1>queln; //创建Copyln阶段的队列  
AscendC::TQue<TPosition::VecOut,1>queOut;//创建CopyOut阶段的队列  
//Init阶段  
pipe.InitBuffer(queIn,2,1024); //开启DoubleBuffer，将待处理的数据一分为二,实现流水并行  
pipe.InitBuffer(queOut,2,1024);  
for-loop{ //Copyln阶段  
{ auto tensor = queln AllocTensor<half>(); //从Que上申请资源，长度1024 AscendC::DataCopy(tensor,gm,1024); //搬运数据从GM到VECINqueln.EnQue(tensor); } //Compute阶段  
{ auto tensor $=$ queln.DeQue<half>(); auto tensorOut $=$ queOut AllocTensor<half>(); AscendC::Abs(tensorOut,tensor,1024); //计算queln.FreeTensor(tensor); queOut.EnQue(tensorOut); } //CopyOut阶段  
{ auto tensor $=$ queln.DeQue<half>(); AscendC::DataCopy(gmOut,tensor,1024); //搬运数据从VECOUT到GMqueOut.FreeTensor(tensor); //释放资源} 

任务间数据传递使用到的内存、事件等资源统一由管理模块Pipe进行管理。如下所示 的内存管理示意图，TPipe通过InitBuffer接口对外提供队列内存初始化功能，开发者可 以通过该接口为指定的队列分配内存。 

队列内存初始化完成后，需要使用内存时，通过调用AllocTensor来为LocalTensor分配 内存，当创建的LocalTensor完成相关计算无需再使用时，再调用FreeTensor来回收 LocalTensor的内存。 


图2-5 内存管理示意图


![](images/1fd7d20d1cfd5fa792a9bea61fe55f85d9b5bedcdd53c5f5f897c0e79a2a2ac2.jpg)


编程过程中使用到的临时变量内存同样通过Pipe进行管理。临时变量可以使用TBuf数 据结构来申请指定TPosition上的存储空间。使用TBuf申请的内存空间只能参与计算， 无法执行队列的入队出队操作。具体的接口使用说明请参考TBuf。 

按照上述编程范式进行编程即可实现单核上数据的并行处理。需要处理的数据被切分 成n片，每个并行任务需要依次完成n个数据切片的处理。任务间的箭头表达数据间的 依赖关系，比如CopyIn处理完第一个数据切片之后，Compute才能对该切片进行处 理。 


图 2-6 流水任务示意图


![](images/0d1a2495685bdc8060fd9c7887d2f67facb87527ccef7890a44b84ef52189b7f.jpg)


上图中的流水任务运行起来的示意图如下，从运行图中可以看出，对于同一片数据， CopyIn、Compute、CopyOut之间的处理具有依赖关系，需要串行处理；不同的数据 切片，同一时间点，可以有多个任务在并行处理，由此达到任务并行、提升性能的目 的。 


图 2-7 流水任务运行示意图


![](images/530bd569d269c8ddb2451fde0d174616a96fe6613a4967e15e7e84debaa16d59.jpg)


# 矩阵编程范式


Cube计算的典型数据流图如下所示：


![](images/1d217b2db1591411a78bf4ed1a9c94e9805ba50d7bf47781eb4908c3fd7c9635.jpg)


和矢量编程范式一样，同样也使用逻辑位置（TPosition）来表达数据流，Cube编程范 式中主要使用的逻辑位置定义如下： 

A1：代表设备上用于矩阵计算的逻辑内存，用于存放左矩阵，物理存储对应AI Core的L1 Buffer。 

B1：代表设备上用于矩阵计算的逻辑内存，用于存放右矩阵，物理存储对应AI Core的L1 Buffer。 

C1：代表设备上用于矩阵计算的逻辑内存，用于存放Bias（偏置）数据，物理存 储对应AI Core的L1 Buffer或Unified Buffer。 

A2：代表设备上用于矩阵计算的逻辑内存，用于存放小块左矩阵（如经过分割、 适配L0A Buffer容量的分块），物理存储对应AI Core的L0A Buffer。 

B2：代表设备上用于矩阵计算的逻辑内存，用于存放小块右矩阵（如经过分割、 适配L0B Buffer容量的分块），物理存储对应AI Core的L0B Buffer。 

C2：代表设备上用于矩阵计算的逻辑内存，用于存放小块Bias（偏置）数据（如 经过分割、适配BT Buffer容量的分块），物理存储对应AI Core的BT Buffer或L0C Buffer。 

CO1：代表设备上用于矩阵计算的逻辑内存，用于存放小块矩阵计算结果（如经 过分割的矩阵计算结果分块），物理存储对应AI Core的L0C Buffer。 

CO2：代表设备上用于矩阵计算的逻辑内存，用于存放矩阵计算结果（如原始矩 阵的最终计算结果），物理存储对应Global Memory或AI Core的Unified Buffer。 

VECIN：代表设备上用于矢量计算的逻辑内存，用于存放矢量计算的输入数据， 物理存储对应AI Core的Unified Buffer。 

VECCALC：代表设备上用于矢量计算的逻辑内存，用于存放临时变量，物理存储 对应AI Core的Unified Buffer。 

VECOUT：代表设备上用于矢量计算的逻辑内存，用于存放矢量计算的输出数 据，物理存储对应AI Core的Unified Buffer。 

TPosition与物理内存的映射关系请参考表1。 

Cube计算流程同样也可以理解为CopyIn、Compute、CopyOut这几个阶段，因为流程 相对复杂，Matmul高阶API提供对此的高阶封装，简化了编程范式。 

![](images/aa8bbef5b989cd654de8d07575c606759fb659327d481aec04f27505fba4c768.jpg)


如上图所示：CopyIn阶段对应SetTensorA、SetTensorB、SetBias接口；Compute阶段 对应Iterate接口；CopyOut阶段对应GetTensorC接口。具体流程可参考如下示例： 

// 创建Matmul对象 创建对象时需要传入A、B、C、Bias的参数类型信息， 类型信息通过MatmulType来定义， 包括：内存逻辑位置、数据格式、数据类型。 

typedef MatmulType<TPosition::GM, CubeFormat::ND, half> aType; typedef MatmulType<TPosition::GM, CubeFormat::ND, half> bType; typedef MatmulType<TPosition::GM, CubeFormat::ND, float> cType; typedef MatmulType<TPosition::GM, CubeFormat::ND, float> biasType; Matmul<aType, bType, cType, biasType> mm; 

```javascript
REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm, &tiling); // 初始化
// CopyIn阶段：完成从GM到LocalMemory的搬运
mm.SetTensorA(gm_a); // 设置左矩阵A
mm.SetTensorB(gm_b); // 设置右矩阵B
mm.SetBias(gm.bias); // 设置Bias
// Compute阶段：完成矩阵乘计算
while (mm.Iterate()) {
    // CopyOut阶段：完成从LocalMemory到GM的搬运
    mm.GetTensorC(gm_c);
}
//结束矩阵乘操作
mm.End(); 
```

# 融合算子编程范式

支持Vector与Cube混合计算的算子称之为融合算子。Ascend C提供融合算子的编程范 式，方便开发者基于该范式表达融合算子的数据流，快速实现自己的融合算子。 

融合算子数据流指融合算子的输入输出在各存储位置间的流向。以一个典型的Cube和 Vector融合算子为例，逻辑位置间的数据流向如下图所示（为了简化描述，没有列出 bias）： 

Cube的输出可以作为Vector的输入：CO2->VECIN 

● Vector的输出可以作为Cube的输入：VECOUT->A1->A2、VECOUT->B1->B2 

![](images/398dc003c685ab9056906c607cb25de7b08005a6e4da9f0c67bb3b874d202ea3.jpg)


基于Matmul高阶API的融合算子编程范式，对上述数据流简化表达如下： 


图2-8 融合算子编程范式


![](images/1cfd64e32dec2f82813df57f865918f5d41b176ced786c8f74293ef6660e0f17.jpg)


1. 初始化一个MatMul对象，将输入数据从Global Memory搬运到Cube核上。 

2. 进行MatMul内部的计算。 

3. 将MatMul的计算结果搬运到Vector核上。 

4. 进行Vector矢量计算。 

5. 将输出结果搬运到Global Memory上。 

# 整个过程的示例代码如下（伪代码）：

```cpp
template<typename aType, typename bType, typename cType, typename biasType> __aicore__ inline void MatmulLeakyKernel<aType, bType, cType, biasType>::Process()
{
    // 步骤1：初始化一个MatMul对象，将输入数据从Global Memory搬运到Cube核上。
    uint32_t computeRound = 0;
    REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), matmulObj);
    matmulObjInit(&tiling);
    matmulObj.SetTensorA(aGlobal);
    matmulObj.SetTensorB(bGlobal);
    matmulObj.SetBias(biasGlobal);
    while (matmulObj.template Iterate(true)) { // 步骤2：进行MatMul内部的计算。
        // 步骤3：将MatMul的计算结果搬运到Vector核上。
        reluOutLocal = reluOutQueue_AllocTensor<cType>();
        matmulObj.template GetTensorC(true)(reluOutLocal, false, true);
        // 步骤4：进行Vector矢量计算。
        AscendC::LeakyRelu(reluOutLocal, reluOutLocal, (cType)alpha, tiling.baseM * tiling.baseN);
        reluOutQueue_EnQue(reluOutLocal);
        // 步骤5：将输出结果搬运到Global Memory上
        reluOutQueue_.DeQue<cType>();
        ...
        AscendC::DataCopy(cGlobal[startOffset], reluOutLocal, copyParam);
        reluOutQueue_.FreeTensor(reluOutLocal);
        computeRound++;
    }
    matmulObj.End();
} 
```

# 2.2.3.3.2 静态 Tensor 编程

在基于Pipe进行算子开发的方式中，由Pipe（TPipe类）统一管理Device端内存等资 源，开发者无需感知内存管理、DoubleBuffer流水、同步等处理，只需要按照计算流 编写算子即可，但由此也带来了一些运行时开销（如TPipe创建、InitBuffer等）。 

基于以上原因，Ascend C提供了静态Tensor编程方式，相比基于Pipe的编程方式，这 种方式避免了TPipe内存管理初始化过程（约数百纳秒），从而减少了运行时开销，更 有助于开发者实现极致性能。通过直接构造指定地址和存储位置的LocalTensor，并将 其传递给计算、搬运等API进行编程，提供了更高的灵活性。然而，这种编程方式也带 来了更高的开发复杂性，需要开发者自行管理DoubleBuffer和同步流水，并且只能使 用Ascend C的基础API，而非全部功能。 

两种编程方式的对比如下： 

基于TPipe和TQue自动管理内存与同步 

Ascendc::TPpipe pipe；//创建全局的资源管理对象 AscendC:TQue<AscendC::TPosition:Vecln,1>queln; AscendC:ueeoiioVecut,1>uut; //初始化队列的内存 pipe.InitBuffer(queln,2, burze); pipe.Initt,2); 

auto xLocal $=$ queln.AllocTensor<half>(); 运 autoyLocal $\underline { { \underline { { \mathbf { \delta \pi } } } } }$ queOut.AllocTensor<half>(); AscendC:DtaCopy(xocal, Gm[ofset],bufrze); queln.EnQue(xLocal); xLoca $\equiv$ queln.DeQue<half>(); AscendC:Exp(yocal,ocal, burze); 

静态Tensor编程自主管理内存与同步 

//直接定义LocalTensor AscendC:LocalTensor<half> xLocal(AscendC:TPosition:VECIN, xAddr, bufferSize); AscendC:LocalTensor<half> yLocal(AscendC:TPosition:VECOUT, yAddr bufferSize) AscendC::DataCopy(xLocal, xGm[offset], bufferize); AscendC:SetFlag<AscendC:HardEvent:MTE2_V>(EVENT_ID0); AscendC:WaitFlag<AscendC:HardEvent:MTE2_V>(EVENT_ID0); AscendC:yal,al,); //. 

# 说明

● 静态Tensor编程的使用约束和限制请参考使用约束和限制。 

● 本节涉及的完整样例请参考静态Tensor编程样例。 

# 编程范式

AI Core包括多种内存单元，比如用于矢量计算的Unified Buffer和用于矩阵计算的 L1 Buffer、L0A Buffer、L0B Buffer、L0C Buffer等内存资源。开发者完全自主管 理AI Core上的所有内存资源，创建Tensor分配地址时管理内存大小、内存复用关 系并确保分配的地址有效性。 

AI Core包括多种指令流水类型，比如Vector/Cube/Scalar计算流水，MTE1、 MTE2、MTE3搬运流水等，每条流水并行执行，它们之间的依赖关系通过同步事 件来协调。开发者调用Ascend C提供的搬运或者计算类API编写算子并根据数据依 赖关系插入对应的同步事件，以达成最优性能。 

下图是一个典型矢量算子的示意图，开发者首先根据业务计算量进行数据分块处理， 之后根据核内的数据依赖关系完成同步事件的插入： 

根据核数和片上内存大小对数据进行切分 

输入数据 

![](images/e2ced016782204ce2d3704a813d2195690f2fbbec7c975f96ba8e77f25dacf9b.jpg)


![](images/ea4ce6fa9a9e365b9eb612b5fb218ccd77c4b455cb74ef54e28918310bdf9267.jpg)



Vector Core 0


![](images/555d05ca905df74ba6760f9a30134ee30fc0ff3c3790e7c106626e9f2d1015c1.jpg)



Vector Core n


输出数据 

![](images/5ba2b91111240df3aff1795ec3c17f246e84fd3efc335928331c8f19215574f0.jpg)


# 内存管理

静态Tensor编程方式下，开发者可以使用两种方式创建Tensor： 

通过LocalMemAllocator指定硬件位置进行Tensor分配。 

LocalMemAllocator是一种线性内存分配器，开发者可以调用Alloc方法进行内存 分配，地址分配从0开始，根据调用次序依次向后进行线性分配， 

LocalMemAllocator只是一个简单的线性分配器，并不提供内存释放以及其它内 存管理的能力。在不关注Bank冲突场景或者算子初始功能开发时，可以使用 

LocalMemAllocator简化算子编写，在后续性能优化时切换到使用LocalTensor进 行地址分配的方式。 

通过LocalTensor构造函数创建Tensor，极致性能场景推荐使用此方式。 

开发者可以使用LocalTensor构造函数直接指定内存地址，实现内存的完全自主管 理（本质上无需申请和释放内存）。使用时，需根据需求合理指定地址（不超过 物理存储上限），并在保证功能正确的前提下进行内存复用。如果需要通过规避 Bank冲突或者复用内存来获得极致性能时，推荐使用该方式。 

```cpp
//方式1：使用LocalMemAllocator进行内存分配  
AscendC::LocalMemAllocator<AscendC::Hardware::UB> ubAllocator;  
AscendC::LocalTensor<float> xLocalPing = ubAllocator Alloc<float, TILE_LENGTH>();  
AscendC::LocalTensor<float> yLocalPing = ubAllocator Alloc<float, TILE_LENGTH>();  
AscendC::LocalTensor<float> zLocalPing = ubAllocator Alloc<float, TILE_LENGTH>(); 
```

```cpp
//方式2：直接使用LocalTensor构造函数构造Tensor  
AscendC::LocalTensor<float> xLocalPing(AscendC::TPosition::VECCALC, xAddrPing, TILE_LENGTH);  
AscendC::LocalTensor<float> yLocalPing(AscendC::TPosition::VECCALC, yAddrPing, TILE_LENGTH);  
AscendC::LocalTensor<float> zLocalPing(AscendC::TPosition::VECCALC, zAddrPing, TILE_LENGTH); 
```

# 同步管理

根据前文介绍的硬件架构，AI Core内部异步并行计算存在多条流水（包括矢量计算、 矩阵计算、数据搬入、数据搬出等），多条流水之间存在数据依赖时，需要插入对应 的同步事件。静态Tensor编程方式下，开发者使用SetFlag/WaitFlag(ISASI)和 

PipeBarrier(ISASI)手动插入同步，事件的类型和事件ID由开发者自行管理，但需要注 

意事件ID不能使用6和7（可能与内部使用的事件ID出现冲突，进而出现未定义行 为）。另外由于需要使用SetFlag/WaitFlag/PipeBarrier底层同步接口（属于ISASI硬件 体系结构相关的接口），无法保证跨硬件版本兼容。 

在同步依赖中，根据数据依赖和指令执行关系，存在两种依赖关系，即正向同步（循 环内依赖）与反向同步（循环间依赖）： 

# 正向同步

在本次数据搬入和计算之间，插入MTE2_V（矢量计算流水等待MT2搬运流水）同 步事件，确保数据搬入之后再进行计算；在本次数据计算和搬出之间，插入 V_MTE3（MTE3搬运流水等待矢量计算流水）同步事件，确保数据计算完成后再 进行搬出。 

# 反向同步

在上一次的数据计算和本次数据搬入之间，插入V_MTE2（MT2搬运流水等待矢量 计算流水）同步事件，确保上一次的数据计算完成后，本次的数据再进行搬入。 防止本次的数据会覆盖掉上一次未计算完成的数据；在上一次的数据搬出和本次 数据计算之间，插入MTE3_V（矢量计算流水等待MT3搬运流水）同步事件，确保 上一次的数据搬出后，再进行本次数据的计算。防止本次的数据会覆盖掉上一次 未搬出的数据。 

上述的同步逻辑在使用Pipe编程框架时，框架会使用EnQue/DeQue/AllocTensor/ FreeTensor进行封装。您可以通过2.9.3 编程模型设计原理来了解应该如何在使用静态 Tensor编程方式时手动进行同步控制。 

```cpp
AscendC::LocalTensor<float> xLocal(AscendC::TPosition::VECCALC, xAddr, TILE_LENGTH); AscendC::LocalTensor<float> yLocal(AscendC::TPosition::VECCALC, yAddr, TILE_LENGTH); AscendC::LocalTensor<float> zLocal(AscendC::TPosition::VECCALC, zAddr, TILE_LENGTH); for (int i = 0; i < loopCount; i++) { // dependency of PIPE_V & PIPE_MTE2 caused by xLocal/yLocal between 2 sequential loops if (i != 0) { AscendC::WaitFlag<AscendC::HardEvent::V_MTE2>(EVENT_ID0); } AscendC::DataCopy(xLocal, xGm[i * TILE_LENGTH], TILE_LENGTH); AscendC::DataCopy(yLocal, yGm[i * TILE_LENGTH], TILE_LENGTH); // dependency of PIPE_MTE2 & PIPE_V caused by xLocal/yLocal in one single loop AscendC::SetFlag<AscendC::HardEvent::MTE2_V>(EVENT_ID0); AscendC::WaitFlag<AscendC::HardEvent::MTE2_V>(EVENT_ID0); if (i != 0) { // dependency of PIPE_MTE3 & PIPE_V caused by zLocal between 2 sequential loops AscendC::WaitFlag<AscendC::HardEvent::MTE3_V>(EVENT_ID0); } AscendC::Add(zLocal, xLocal, yLocal, TILE_LENGTH); if (i != (loopCount - 1)) { // dependency of PIPE_V & PIPE_MTE2 caused by xLocal/yLocal between 2 sequential loops AscendC::SetFlag<AscendC::HardEvent::V_MTE2>(EVENT_ID0); } // dependency of PIPE_V & PIPE_MTE3 caused by zLocal in one single loop AscendC::SetFlag<AscendC::HardEvent::V_MTE3>(EVENT_ID0); AscendC::WaitFlag<AscendC::HardEvent::V_MTE3>(EVENT_ID0); AscendC::DataCopy(zGm[i * TILE_LENGTH], zLocal, TILE_LENGTH); if (i != (loopCount - 1)) { // dependency of PIPE_MTE3 & PIPE_V caused by zLocal between 2 sequential loops AscendC::SetFlag<AscendC::HardEvent::MTE3_V>(EVENT_ID0); } 
```

# 流水优化

在基于TPipe的编程范式中，开发者只需要在InitBuffer时指定buffer数量为2，即可自 动开启Double Buffer。但是静态Tensor编程方式下，开发者需要手动开启Double Buffer，具体示例如下，完整样例请参考静态Tensor编程样例中的Double Buffer示 例。 

```txt
// ping   
AscendC::LocalTensor<float> xLocalPing(AscendC::TPosition::VECCALC, xAddrPing, TILE_LENGTH); AscendC::LocalTensor<float> yLocalPing(AscendC::TPosition::VECCALC, yAddrPing, TILE_LENGTH); AscendC::LocalTensor<float> zLocalPing(AscendC::TPosition::VECCALC, zAddrPing, TILE_LENGTH); // pong   
AscendC::LocalTensor<float> xLocalPong(AscendC::TPosition::VECCALC, xAddrPong, TILE_LENGTH); AscendC::LocalTensor<float> yLocalPong(AscendC::TPosition::VECCALC, yAddrPong, TILE_LENGTH); AscendC::LocalTensor<float> zLocalPong(AscendC::TPosition::VECCALC, zAddrPong, TILE_LENGTH);   
// double buffer   
AscendC::SetFlag<AscendC::HardEvent::MTE3_MTE2>(EVENT_ID0); AscendC::SetFlag<AscendC::HardEvent::MTE3_MTE2>(EVENT_ID1); for (int i = 0; i < loopCount; i++) { int32_t eventID = (i % 2 == 0 ? EVENT_ID0 : EVENT_ID1); AscendC::LocalTensor<float> &xLocal = (i % 2 == 0 ? xLocalPing : xLocalPong); AscendC::LocalTensor<float> &yLocal = (i % 2 == 0 ? yLocalPing : yLocalPong); AscendC::LocalTensor<float> &zLocal = (i % 2 == 0 ? zLocalPing : zLocalPong); // dependency of PIPE_MTE3 & PIPE_MTE2 caused by xLocal/yLocal between 2 sequential loops AscendC::WaitFlag<AscendC::HardEvent::MTE3_MTE2>(eventID); AscendC::DataCopy(xLocal, xGm[i * TILE_LENGTH], TILE_LENGTH); AscendC::DataCopy(yLocal, yGm[i * TILE_LENGTH], TILE_LENGTH); // dependency of PIPE_MTE2 & PIPE_V caused by xLocal/yLocal in one single loop AscendC::SetFlag<AscendC::HardEvent::MTE2_V>(eventID); AscendC::WaitFlag<AscendC::HardEvent::MTE2_V>(eventID); AscendC::Add(zLocal, xLocal, yLocal, TILE_LENGTH); // dependency of PIPE_V & PIPE_MTE3 caused by zLocal in one single loop AscendC::SetFlag<AscendC::HardEvent::V_MTE3>(eventID); AscendC::WaitFlag<AscendC::HardEvent::V_MTE3>(eventID); AscendC::DataCopy(zGm[i * TILE_LENGTH], zLocal, TILE_LENGTH); // dependency of PIPE_MTE3 & PIPE_MTE2 caused by zLocal between 2 sequential loops AscendC::SetFlag<AscendC::HardEvent::MTE3_MTE2>(eventID);   
} AscendC::WaitFlag<AscendC::HardEvent::MTE3_MTE2>(EVENT_ID0); AscendC::WaitFlag<AscendC::HardEvent::MTE3_MTE2>(EVENT_ID1); 
```

以下为不使能DoubleBuffer和使能DoubleBuffer的流水示意图。多数情况下，采用 DoubleBuffer能有效提升Vector的时间利用率，缩减算子执行时间，详细内容可参考 2.9.5.1 DoubleBuffer。 

![](images/cae9a5ab2e139a88e0f82ec4e725b7fac00af1a52f7ce6582a6d48a6dbae5ceb.jpg)


![](images/8b634eee3723a72c75757ce8395eeda5a1be81680dfd4995d8d2c2e40894e936.jpg)


# 使用约束和限制

静态Tensor编程方式需要遵循以下约束和限制： 

开发者不能使用TPipe/TQue/TQueBind/TBufPool等框架接口，和上述框架接口混 用可能会出现未定义行为。 

只能使用部分API。具体支持的API列表见支持的API范围。因为不在列表范围内的 API内部依赖TPipe分配事件ID，可能会和开发者定义的事件ID产生冲突。 

同步事件需要由开发者使用SetFlag/WaitFlag(ISASI)和PipeBarrier(ISASI)手动插 入，事件的类型和事件ID由开发者自行管理，但需要注意事件ID不能使用6和7 （可能与内部使用的事件ID出现冲突，进而出现未定义行为）。 

由于需要使用SetFlag/WaitFlag/PipeBarrier底层同步接口（属于ISASI硬件体系结 构相关的接口），无法保证算子跨硬件版本兼容。 

Kernel入口处需要开发者手动调用InitSocState接口用来初始化全局状态寄存器。 因为全局状态寄存器处于不确定状态，如果不调用该接口，可能导致算子执行过 程中出现未定义行为。在TPipe框架编程中，初始化过程由TPipe完成，无需开发 者关注。 

# 支持的 API 范围


表 2-3 针对 Atlas 推理系列产品 AI Core，支持的 API 范围


<table><tr><td>接口分类</td><td>接口名称</td></tr><tr><td>基础API &gt; 标量计算</td><td>ScalarGetCountOfValue、ScalarCountLeadingZero、ScalarCast、CountBitsCntSameAsSignBit、ScalarGetSFFValue</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 基础算术</td><td>Exp、Ln、Abs、Reciprocal、_sqrt、Rsqrt、Relu、 VectorPadding、Add、Sub、Mul、Div、Max、Min、 BilinearInterpolation、Adds、Muls、Maxs、Mins、 LeakyRelu</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 逻辑计算</td><td>Not、And、Or</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 复合计算</td><td>Axy、CastDeq、AddRelu、AddReluCast、 AddDeqRelu、SubRelu、SubReluCast、MulAddDst、 MulCast、FusedMulAdd、FusedMulAddRelu</td></tr><tr><td>基础API &gt; 矛量计算 &gt; 比较与选择</td><td>Compare、Compare(结果存入寄存器)、 CompareScalar、GetCmpMask、SetCmpMask、 Select、GatherMask</td></tr><tr><td>基础API &gt; 矛量计算 &gt; 类型转换</td><td>Cast</td></tr><tr><td>基础API &gt; 矛量计算 &gt; 归约计算</td><td>WholeReduceMax、WholeReduceMin、 WholeReduceSum、BlockReduceMax、 BlockReduceMin、BlockReduceSum、PairReduceSum、 RepeatReduceSum、GetReduceMaxMinCount</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 数据转换</td><td>Transpose、TransDataTo5HD</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 数据填充</td><td>Duplicate</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 排序组合</td><td>ProposalConcat、ProposalExtract、RpSort16、MrgSort4、GetMrgSortResult</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 离散与聚合</td><td>Gather、Scatter</td></tr><tr><td>基础API &gt; 矜量计算 &gt; 掩码操作</td><td>SetMaskCount、SetMaskNorm、SetVectorMask、ResetMask</td></tr><tr><td>基础API &gt; 矜量计算 &gt; 量化设置</td><td>SetDecqScale</td></tr><tr><td>基础API &gt; 数据搬运 &gt; DataCopy</td><td>基础数据搬运</td></tr><tr><td>基础API &gt; 同步控制 &gt; 核内同步</td><td>SetFlag/WaitFlag、PipeBarrier</td></tr><tr><td>基础API &gt; 缓存控制</td><td>DataCachePreload、DataCacheCleanAndInvalid、ICachePreLoad</td></tr><tr><td>基础API &gt; 系统变量访问</td><td>GetBlockNum、GetBlockIdx、GetDataBlockSizeInBytes、GetArchVersion、GetTaskRatio、InitSocState、GetProgramCounter、CheckLocalMemoryIA</td></tr><tr><td>基础API &gt; 原子操作</td><td>SetAtomicAdd、SetAtomicNone</td></tr><tr><td>基础API &gt; 矩阵计算</td><td>InitConstValue、LoadData、SetAippFunctions、LoadImageToLocal、LoadUnzipIndex、LoadDataUnzip、SetLoadDataBoundary、SetLoadDataPaddingValue、Mmad</td></tr></table>


表 2-4 针对 Atlas A2 训练系列产品/Atlas A2 推理系列产品，支持的 API 范围


<table><tr><td>接口分类</td><td>接口名称</td><td>备注</td></tr><tr><td>基础API &gt; 标量计算</td><td>ScalarGetCountOfValue、ScalarCountLeadingZero、ScalarCast、 CountBitsCntSameAsSignBit、 ScalarGetSFFValue、ToBfloat16、 ToFloat</td><td>-</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 基础算术</td><td>Exp、Ln、Abs、Reciprocal、Sqrt、Rsqrt、Relu、Add、Sub、Mul、Div、Max、Min、BilinearInterpolation、Adds、Muls、Mxs、Mins、LeakyRelu</td><td>-</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 逻辑计算</td><td>Not、And、Or、ShiftLeft、ShiftRight</td><td>-</td></tr><tr><td>基础API &gt; 矛量计算 &gt; 复合计算</td><td>Axpy、CastDeq、AddRelu、AddReluCast、AddDeqRelu、SubRelu、SubReluCast、MulAddDst、MulCast、FusedMulAdd、FusedMulAddRelu</td><td>-</td></tr><tr><td>基础API &gt; 矛量计算 &gt; 比较与选择</td><td>Compare、Compare(结果存入寄存器)、CompareScalar、GetCmpMask、SetCmpMask、Select、GatherMask</td><td>-</td></tr><tr><td>基础API &gt; 矛量计算 &gt; 类型转换</td><td>Cast</td><td>-</td></tr><tr><td>基础API &gt; 矛量计算 &gt; 归约计算</td><td>WholeReduceMax、WholeReduceMin、WholeReduceSum、BlockReduceMax、BlockReduceMin、BlockReduceSum、PairReduceSum、RepeatReduceSum、GetAccVal、GetReduceMaxMinCount</td><td>-</td></tr><tr><td>基础API &gt; 矛量计算 &gt; 数据转换</td><td>Transpose、TransDataTo5HD</td><td>-</td></tr><tr><td>基础API &gt; 矛量计算 &gt; 数据填充</td><td>Duplicate、Brcb</td><td>-</td></tr><tr><td>基础API &gt; 矛量计算 &gt; 排序组合</td><td>Sort32、MrgSort、GetMrgSortResult</td><td>-</td></tr><tr><td>基础API &gt; 矛量计算 &gt; 离散与聚合</td><td>Gather、Gatherb</td><td>-</td></tr><tr><td>基础API &gt; 矛量计算 &gt; 掩码操作</td><td>SetMaskCount、SetMaskNorm、SetVectorMask、ResetMask</td><td>-</td></tr><tr><td>基础API &gt; 矛量计算 &gt; 量化设置</td><td>SetDecqScale</td><td>-</td></tr><tr><td rowspan="6">基础API &gt; 数据搬运 &gt; DataCopy</td><td>基础数据搬运</td><td>不支持VECIN/VECCALC/VECOUT-&gt;TSCM通路的数据搬运。</td></tr><tr><td>增强数据搬运</td><td>不支持VECIN/VECCALC/VECOUT-&gt;TSCM通路的数据搬运。</td></tr><tr><td>切片数据搬运</td><td>-</td></tr><tr><td>随路转换ND2NZ搬运</td><td rowspan="3">不支持VECIN/VECCALC/VECOUT-&gt;TSCM通路的数据搬运。</td></tr><tr><td>随路转换NZ2ND搬运</td></tr><tr><td>随路量化激活搬运</td></tr><tr><td>基础API &gt; 数据搬运</td><td>Copy、DataCopyPad、SetPadValue</td><td>-</td></tr><tr><td>基础API &gt; 同步控制 &gt; 核内同步</td><td>SetFlag/WaitFlag、PipeBarrier、DataSyncBarrier</td><td>-</td></tr><tr><td>基础API &gt; 同步控制 &gt; 核间同步</td><td>CrossCoreSetFlag、CrossCoreWaitFlag</td><td>-</td></tr><tr><td>基础API &gt; 缓存控制</td><td>DataCachePreload、DataCacheCleanAndInvalid、ICachePreLoad、GetICachePreloadStatus</td><td>-</td></tr><tr><td>基础API &gt; 系统变量访问</td><td>GetBlockNum、GetBlockIdx、GetDataBlockSizeInBytes、GetArchVersion、GetTaskRatio、InitSocState、GetProgramCounter、GetSubBlockNum、GetSubBlockIdx、GetSystemCycle、CheckLocalMemoryIA</td><td>-</td></tr><tr><td>基础API &gt; 原子操作</td><td>SetAtomicAdd、SetAtomicType、SetAtomicNone、SetAtomicMax、SetAtomicMin、SetStoreAtomicConfig、GetStoreAtomicConfig</td><td>-</td></tr><tr><td>基础API &gt; 矩阵计算</td><td>Mmad、MmadWithSparse、SetHF32Mode、SetHF32TransMode、SetMMLayoutTransform、SetFixPipeConfig、SetFixpipeNz2ndFlag、SetFixpipePreQuantFlag、InitConstValue、LoadData、LoadDataWithTranspose、SetAippFunctions、LoadImageToLocal、LoadDataWithSparse、SetFmatrix、SetLoadDataBoundary、SetLoadDataRepeat、SetLoadDataPaddingValue、Fixpipe</td><td>-</td></tr><tr><td>Utilis API &gt; C++标准库&gt; 算法</td><td>max、min、index_sequence</td><td>-</td></tr><tr><td>Utilis API &gt; C++标准库&gt; 容器函数</td><td>tuple、get、make_tuple</td><td>-</td></tr><tr><td>Utilis API &gt; C++标准库&gt; 类型特性</td><td>is.convertible、is_base_of、is_same、enable_if、conditional</td><td>-</td></tr></table>


表 2-5 针对 Atlas A3 训练系列产品/Atlas A3 推理系列产品，支持的 API 范围


<table><tr><td>接口分类</td><td>接口名称</td><td>备注</td></tr><tr><td>基础API &gt; 标量计算</td><td>ScalarGetCountOfValue、ScalarCountLeadingZero、ScalarCast、 CountBitsCntSameAsSignBit、 ScalarGetSFFValue、ToBfloat16、 ToFloat</td><td>-</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 基础算术</td><td>Exp、Ln、Abs、Reciprocal、 Squrt、Rsqrt、Relu、Add、Sub、 Mul、Div、Max、Min、 BilinearInterpolation、Adds、 Muls、Mxs、Mins、LeakyRelu</td><td>-</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 逻辑计算</td><td>Not、And、Or、ShiftLeft、 ShiftRight</td><td>-</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 复合计算</td><td>Axpy、CastDecq、AddRelu、 AddReluCast、AddDeqRelu、 SubRelu、SubReluCast、 MulAddDst、MulCast、 FusedMulAdd、FusedMulAddRelu</td><td>-</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 比较与选择</td><td>Compare、Compare(结果存入寄存器)、CompareScalar、 GetCmpMask、SetCmpMask、 Select、GatherMask</td><td>-</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 类型转换</td><td>Cast</td><td>-</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 归约计算</td><td>WholeReduceMax、 WholeReduceMin、 WholeReduceSum、 BlockReduceMax、 BlockReduceMin、 BlockReduceSum、 PairReduceSum、 RepeatReduceSum、GetAccVal、 GetReduceMaxMinCount</td><td>-</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 数据转换</td><td>Transpose、TransDataTo5HD</td><td>-</td></tr><tr><td>基础API &gt; 矜量计算 &gt; 数据填充</td><td>Duplicate、Brcb</td><td>-</td></tr><tr><td>基础API &gt; 矜量计算 &gt; 排序组合</td><td>Sort32、MrgSort、 GetMrgSortResult</td><td>-</td></tr><tr><td>基础API &gt; 矜量计算 &gt; 离散与聚合</td><td>Gather、Gatherb</td><td>-</td></tr><tr><td>基础API &gt; 矜量计算 &gt; 掩码操作</td><td>SetMaskCount、SetMaskNorm、 SetVectorMask、ResetMask</td><td>-</td></tr><tr><td>基础API &gt; 矜量计算 &gt; 量化设置</td><td>SetDecqScale</td><td>-</td></tr><tr><td>基础API &gt; 数据搬运 &gt; DataCopy</td><td>基础数据搬运</td><td>不支持VECIN/ VECCALC/VECOUT -&gt; TSCM通路的数据搬运。</td></tr><tr><td rowspan="2">基础API &gt; 数据搬运</td><td>增强数据搬运</td><td>不支持VECIN/ VECCALC/VECOUT -&gt; TSCM通路的数据搬运。</td></tr><tr><td>切片数据搬运</td><td>-</td></tr><tr><td rowspan="4"></td><td>随路转换ND2NZ搬运</td><td rowspan="3">不支持VECIN/VECCALC/VECOUT-&gt;TSCM通路的数据搬运。</td></tr><tr><td>随路转换NZ2ND搬运</td></tr><tr><td>随路量化激活搬运</td></tr><tr><td>Copy、DataCopyPad、SetPadValue</td><td>-</td></tr><tr><td>基础API &gt;同步控制&gt;核内同步</td><td>SetFlag/WaitFlag、PipeBarrier、DataSyncBarrier</td><td>-</td></tr><tr><td>基础API &gt;同步控制&gt;核间同步</td><td>CrossCoreSetFlag、CrossCoreWaitFlag</td><td>-</td></tr><tr><td>基础API &gt;缓存控制</td><td>DataCachePreload、DataCacheCleanAndInvalid、ICachePreLoad、GetICachePreloadStatus</td><td>-</td></tr><tr><td>基础API &gt;系统变量访问</td><td>GetBlockNum、GetBlockIdx、GetDataBlockSizeInBytes、GetArchVersion、GetTaskRatio、InitSocState、GetProgramCounter、GetSubBlockNum、GetSubBlockIdx、GetSystemCycle、CheckLocalMemoryIA</td><td>-</td></tr><tr><td>基础API &gt;原子操作</td><td>SetAtomicAdd、SetAtomicType、SetAtomicNone、SetAtomicMax、SetAtomicMin、SetStoreAtomicConfig、GetStoreAtomicConfig</td><td>-</td></tr><tr><td>基础API &gt;矩阵计算</td><td>Mmad、MmadWithSparse、SetHF32Mode、SetHF32TransMode、SetMMLayoutTransform、SetFixPipeConfig、SetFixpipeNz2ndFlag、SetFixpipePreQuantFlag、InitConstValue、LoadData、LoadDataWithTranspose、SetAippFunctions、LoadImageToLocal、LoadDataWithSparse、SetFmatrix、SetLoadDataBoundary、SetLoadDataRepeat、SetLoadDataPaddingValue、Fixpipe</td><td>-</td></tr><tr><td>Utilis API &gt; C++标准库
&gt;算法</td><td>max、min、index_sequence</td><td>-</td></tr><tr><td>Utilis API &gt; C++标准库
&gt;容器函数</td><td>tuple、get、make_tuple</td><td>-</td></tr><tr><td>Utilis API &gt; C++标准库
&gt;类型特性</td><td>is.convertable、is_base_of、
is_same、enable_if、conditional</td><td>-</td></tr><tr><td>高阶API &gt; C++标准库
&gt;类型特性</td><td>is Converted、is_base_of、
is_same、enable_if、conditional</td><td>-</td></tr><tr><td>高阶API &gt;模板库函数
&gt;typetraits</td><td>is Converted、is_base_of、
is_same、enable_if、conditional</td><td>-</td></tr></table>


表 2-6 针对 Atlas 350 加速卡，支持的 API 范围


<table><tr><td>接口分类</td><td>接口名称</td><td>备注</td></tr><tr><td>基础API &gt; 标量计算</td><td>GetBitCount、CountLeadingZero、CountBitsCntSameAsSignBit、GetSFFValue、Cast (float转折 half、int32_t)、Cast (float转折bfloat16_t)、Cast (多类型转float)、Nop、GetUintDivMagicAndShift、WriteGmByPassDCache、ReadGmByPassDCache</td><td>-</td></tr><tr><td>基础API &gt; 矢量计算 &gt;基础算术</td><td>Exp、Ln、Abs、Reciprocal、sqrt、Rsqrt、Relu、Neg、Add、Sub、Mul、Div、Max、Min、BilinearInterpolation、Prelu、Mull、Adds、Adds (灵活标量位置)、Muls、Muls (灵活标量位置)、Mxs、Mxs (灵活标量位置)、Mins、Mins (灵活标量位置)、Subs、Divs、LeakyRelu</td><td>-</td></tr><tr><td>基础API &gt; 矛量计算 &gt;逻辑计算</td><td>Not、And、Or、ShiftLeft (左移位数为Tensor)、ShiftRight (右移位数为Tensor)、Ands、Ors、ShiftLeft、ShiftRight</td><td>-</td></tr><tr><td>基础API &gt; 矛量计算 &gt;复合计算</td><td>Axy、AddRelu、AddReluCast、AddDeqRelu、SubRelu、SubReluCast、MulAddDst、MulCast、FusedMulAdd、MulAddRelu、AbsSub、FusedExpSub、MulsCast</td><td>-</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 比较与选择</td><td>Compare、Compares、Compares(灵活标量位置)、GetCmpMask、SetCmpMask、GatherMask、Select(灵活标量位置)</td><td>-</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 类型转换</td><td>Truncate</td><td>-</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 归约计算</td><td>ReduceMax、ReduceMin、WholeReduceSum、BlockReduceMax、BlockReduceMin、BlockReduceSum、PairReduceSum、RepeatReduceSum、</td><td>-</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 数据转换</td><td>Transpose</td><td>-</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 数据填充</td><td>Duplicate、Brcb、CreateVeclIndex</td><td>-</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 排序组合</td><td>Sort32、MrgSort、GetMrgSortResult</td><td>-</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 离散与聚合</td><td>Gather、Gatherb、Scatter</td><td>-</td></tr><tr><td>基础API &gt; 矢量计算 &gt; 掩码操作</td><td>SetMaskCount、SetMaskNorm、SetVectorMask、ResetMask</td><td>-</td></tr><tr><td rowspan="6">基础API &gt; 数据搬运 &gt; DataCopy</td><td>基础数据搬运</td><td>不支持VECIN/VECCALC/VECOUT-&gt;TSCM通路的数据搬运。</td></tr><tr><td>增强数据搬运</td><td>不支持VECIN/VECCALC/VECOUT-&gt;TSCM通路的数据搬运。</td></tr><tr><td>切片数据搬运</td><td>-</td></tr><tr><td>随路转换ND2NZ搬运</td><td>不支持VECIN/VECCALC/VECOUT-&gt;TSCM通路的数据搬运。</td></tr><tr><td>随路转换NZ2ND搬运</td><td>-</td></tr><tr><td>随路量化激活搬运</td><td>-</td></tr><tr><td>基础API &gt; 数据搬运</td><td>Copy、DataCopyPad、SetPadValue</td><td>DataCopyPad 不支持VECIN/VECCALC/VECOUT -&gt; TSCM通路的数据搬运。</td></tr><tr><td>基础API &gt; 同步控制 &gt; 核内同步</td><td>SetFlag/WaitFlag、PipeBarrier、DataSyncBarrier</td><td>-</td></tr><tr><td>基础API &gt; 同步控制 &gt; 核间同步</td><td>CrossCoreSetFlag、CrossCoreWaitFlag、SyncAll</td><td>-</td></tr><tr><td>基础API &gt; 缓存控制</td><td>DataCachePreload、DataCacheCleanAndInvalid、ICachePreLoad、GetICachePreloadStatus</td><td>-</td></tr><tr><td>基础API &gt; 系统变量访问</td><td>GetBlockNum、GetBlockIdx、GetDataBlockSizeInBytes、GetArchVersion、InitSocState、GetSpr、ClearSpr、GetProgramCounter、GetSubBlockNum、GetSubBlockIdx、GetSystemCycle、SetCtrlSpr、GetCtrlSpr、ResetCtrlSpr</td><td>-</td></tr><tr><td>基础API &gt; 原子操作</td><td>SetAtomicAdd、SetAtomicType、DisableDmaAtomic、SetAtomicMax、SetAtomicMin、SetStoreAtomicConfig、GetStoreAtomicConfig、AtomicAdd、AtomicMin、AtomicMax、AtomicCas、AtomicExch</td><td>-</td></tr><tr><td>基础API &gt; 矩阵计算</td><td>Fill、LoadData、LoadDataWithTranspose、LoadDataWithSparse、SetFmatrix、SetLoadDataBoundary、SetLoadDataRepeat、SetLoadDataPaddingValue、Fixpipe、SetFixPipeConfig、SetFixpipeNz2ndFlag、SetFixpipePreQuantFlag、SetAippFunctions、LoadImageToLocal、Mmad、SetHF32Mode、SetHF32TransMode</td><td>-</td></tr><tr><td>Utilities API &gt; C++标准库 &gt; 算法</td><td>max、min、index_sequence</td><td>-</td></tr><tr><td>Utilis API &gt; C++标准库
&gt; 容器函数</td><td>tuple、get、make_tuple</td><td>-</td></tr><tr><td>Utilis API &gt; C++标准库
&gt; 类型特性</td><td>is.convertable、is_same、
enable_if、conditional</td><td>-</td></tr></table>

# 2.2.3.3.3 Reg 矢量计算编程

# 简介

Reg矢量计算API是面向RegBase架构开发的API，用户可以通过该API直接对芯片中涉 及Vector计算的寄存器进行操作，实现更大的灵活性和更好的性能。Reg矢量计算API 与基础API功能相似，但与基础API输入和输出数据必须为LocalTensor不同，Reg矢量 计算API的输入或输出数据均为Reg矢量计算寄存器。对于计算类API，其功能是从给定 的寄存器获取数据，进行计算，并将结果保存在给定的寄存器。对于搬运类API，其功 能是实现UB和寄存器的数据搬运。由此可见，Reg矢量计算API相较于基础API，将数 据搬运和Reg计算过程交给用户自主控制，从而实现更大的开发自由度。 

# Regbase 编程模型

基于寄存器（Regbase）的编程模型支持用户编写和调用Vector Funtion（向量函 数）。这些函数使用__simd_vf__标记，并被发送到硬件中的向量运算单元执行。在 simd vf函数内部，通过Reg矢量计算API实现计算操作，其内存层级与编程架构如图 2-9所示。 

在SIMD Vector的内存架构中，最靠近Vector计算单元的是VF Reg，它是SIMD的私有 内存，包含多种类型的Reg矢量计算寄存器，用于存放并行处理的多个数据元素。单核 内所有的VF Reg寄存器共享一个本地内存资源UB。SIMD架构不支持从全局内存 （Global Memory）加载数据到Reg矢量计算寄存器，先将数据从全局内存GM搬运至 Unified Buffer，再通过显式的Load/Store指令，由Unified Buffer加载到Reg矢量计算 寄存器中。 


图 2-9 SIMD Reg 矢量计算内存层级


![](images/60bf36ecf6db73785b1cb0e279170e94bad7ce09a40beb1bd05a523f241a0a35.jpg)


SIMD Reg矢量计算编程架构中，通过发出指令到Reg矢量计算执行单元，执行单元从 Registers读取数据，进行计算，计算结果写回Registers。DMA搬运单元负责在 Registers和Local Memory之间搬运数据。 


图 2-10 SIMD Reg 矢量计算编程架构


![](images/0d353ce26e432825c5b4b75659351ec947d8a8872edb3c6d2c361b6785668bf1.jpg)


# Regbase 和 Membase 编程调用层级

在Membase架构中，基础API调用框架API或直接调用编译器BuiltIn API实现功能，而 高阶API则通过调用基础API来实现功能。在Regbase架构中新增Reg矢量计算API，用 户在算子实现中可以直接调用该API，高阶API和基础API也可以调用该API来实现功 能，Reg矢量计算API则是直接调用编译器BuiltIn API实现功能。 

在Regbase架构中，中间结果可暂存在寄存器中，无需数据搬出到Local Memory的开 销；在Membase架构中，所有操作均基于内存进行，这意味着每次计算都需要从 Local Memory加载数据，计算完成后将结果搬回Local Memory，中间计算结果都需 要暂存在Local Memory上。 

在Regbase架构中，寄存器容纳的最大数据长度为VL（Vector Length），由于寄存器 容量的限制，每次只能处理VL长度的数据。因此，需要对数据进行切分，每次从Local Memory搬运VL长度的数据到寄存器中进行计算，计算完成后将结果搬回Local Memory。而在Membase架构中，则能够直接处理完整长度的LocalTensor，无需进行 数据切分，从而简化了数据处理流程。 

![](images/14210809c8d65a9ead57779dd8caa823b5a5ec898be54791d44bc85afbbef2d3.jpg)


![](images/5b085c9fe6bec71a071de7484067d0d7cdd0ad60dd41be717a501cad857cd85a.jpg)


# Reg 矢量计算调用层次

核函数，使用__global__ __aicore__标识的为核函数，是Device侧的入口函数， Host侧可以通过<<<...>>>语法进行调用。 

_aicore__函数，使用__aicore__标识该函数在Device侧执行。 核函数内可以调用 _aicore__函数。 

simd vf函数，使用__simd_vf__标记，能被核函数通过simd vf函数调用。simd vf 函数内只能调用__simd_callee__函数和constexpr aicore。 

_simd_callee__子函数，在simd vf函数内可以调用子函数，并且这些子函数有可 能需要返回值或者通过引用传参，这类子函数通过__simd_callee__标识。 __simd_callee__函数内只能调用__simd_callee__函数和constexpr aicore函数。 

具体的调用关系图如下： 

![](images/e6d358636408d0fd5c96a8e3ea432a410829a06862c61972cb1ec3cb413773a6.jpg)


以下为唯一合法函数调用链： 

![](images/126a823084a82345f23c60ce5da99dff3a711f06888d368424083192c20ac925.jpg)


Regbase编程模型中允许定义simd vf函数，并且通过__simd_vf__来进行标记，这种设 计方案有如下优点： 

_aicore__和__simd_vf__代码隔离清晰，编译器可以对编译器BuiltIn API的使用范 围是否合法做检测。 

对函数调用做完善的检查报错，比如在__simd_vf__内调用__aicore__函数或者 simt函数等错误用法。 

使用__simd_vf__函数编程，用户可以控制某些优化选项（如多个simd vf函数融 合）只针对特定函数生效，或针对特定函数关闭某些优化。 

本示例中，在__aicore__函数Compute中调用了VF函数AddVF进行向量加法操作。 

```txt
template <typename T>
    __aicore__ inline void Compute()
    {
        __aicore__ __inline void Compute()
    }
} 
```

```txt
//申请输出队列并读取输入结果  
...  
//调用simdvf函数  
asc_vf_call<AddVF<T>>(dstAddr, src0Addr, src1Addr, count, oneRepeatSize, repeatTimes);  
//写入结果到输出队列并释放输入队列的内存  
...  
} 
```

# Reg 矢量计算寄存器

Reg矢量计算API操作的基础数据类型介绍如下，具体API请参考Reg矢量计算。 

# ● RegTensor

矢量数据寄存器，Reg矢量计算基本存储单元，用于矢量计算。RegTensor的位宽 是VL（Vector Length），可存储VL/sizeof(T)的数据（T表示数据类型）。 

# MaskReg

掩码寄存器，用于矢量计算中选择参与计算的元素。MaskReg的位宽是VL/8。 

# ● UnalignRegForLoad & UnalignRegForStore

非对齐寄存器，作为缓冲区，用来优化UB和RegTensor之间的连续非对齐地址访 问的开销。在读非对齐地址前，UnalignReg应该通过LoadUnAlignPre初始化，然 后再使用LoadUnAlign。在写非对齐地址时，先使用StoreUnAlign，再使用 StoreUnAlignPost进行后处理。 

# AddrReg

地址寄存器，用于存储地址偏移量的寄存器。AddrReg通过CreateAddrReg初始 化，然后在循环之中使用AddrReg存储地址偏移量。AddrReg在每层循环中根据 所设置的stride进行自增。 

本示例中的AddVF函数通过Reg矢量计算API的add接口实现两组数据的相加操 作，实现高效、灵活的向量计算。通过设置MaskReg掩码寄存器，根据实际有效 数据长度count生成掩码mask，控制参与运算的数据元素的数量。通过 LoadAlign/StoreAlign接口，实现UB和Reg矢量计算寄存器之间的数据搬运。 

本示例为连续对齐搬入搬出场景，使用到的寄存器类型为RegTensor、MaskReg 和AddrReg。 

```cpp
template<typename T> __simd_vf__inline void AddVF(_ubuf_T* dstAddr, _ubuf_T* src0Addr, _ubuf_T* src1Addr, uint32_t count, uint32_t oneRepeatSize, uint16_t repeatTimes) {
    AscendC::Reg::RegTensor<T> srcReg0;
    AscendC::Reg::RegTensor<T> srcReg1;
    AscendC::Reg::RegTensor<T> dstReg;
    AscendC::Reg::MaskReg mask;
    AscendC::Reg::AddrReg aReg;
    for (uint16_t i = 0; i < repeatTimes; ++i) {
        aReg = AscendC::Reg::CreateAddrReg<T>(i, oneRepeatSize);
        mask = AscendC::Reg::UpdateMask<T>(count);
        AscendC::Reg::LoadAlign(srcReg0, src0Addr, aReg);
        AscendC::Reg::LoadAlign(srcReg1, src1Addr, aReg);
        AscendC::Reg::Add(dstReg, srcReg0, srcReg1, mask);
        AscendC::Reg::StoreAlign(dstAddr, dstReg, aReg, mask);
    }
} 
```

本示例为连续非对齐搬入搬出场景，使用到的寄存器类型为RegTensor、 MaskReg、AddrReg以及UnalignRegForLoad和UnalignRegForStore。 

```cpp
template<typename T> __simd_vf__inline void LoadUnAlignVF(_ubuf_T* dstAddr, _ubuf_T* srcAddr, uint32_t oneRepeatSize, uint16_t repeatTimes) {
    AscendC::Reg::RegTensor<T> srcReg; 
```

```cpp
AscendC::Reg::UnalignRegForLoad ureg0;   
AscendC::Reg::UnalignRegForStore ureg1;   
AscendC::Reg::AddrReg aReg;   
for (uint16_t i = 0; i < repeatTimes; ++i) { aReg = AscendC::Reg::CreateAddrReg<T>(i, oneRepeatSize); AscendC::Reg::LoadUnAlignPre(ureg0, srcAddr, aReg); AscendC::Reg::LoadUnAlign(srcReg, ureg0, srcAddr, aReg, 0); AscendC::Reg::StoreUnAlign.dstAddr, srcReg, ureg1, aReg); } AscendC::Reg::StoreUnAlignPost.dstAddr, ureg1, aReg); 
```

# 流水线同步控制

在SIMD的VF函数的编写中，有时候需要将不同的值根据循环写入到同一个地址中，或 者目标dst和源src是同一个地址，这就涉及到不同流水的同步指令。SIMD VF函数内不 同流水线之间的同步指令使用LocalMemBar来表示。该同步指令指定src源流水线和 dst目的流水线，如下图所示，目的流水线将等待源流水线上所有指令完成才进行执 行。写读场景下，当写指令使用的寄存器和读指令使用的寄存器相同时，可以触发寄 存器保序，指令将会按照代码顺序执行，不需要插入同步指令，而当写指令使用的寄 存器和读指令使用的的寄存器不同时，如果要确保两条指令顺序执行，则需要插入同 步指令，写写场景同理。 

![](images/39d793b3701f322b0e0b273b5cd801010413d55a3e1bd04cd167c772d0c05558.jpg)


![](images/b6b62b2c8ed32ae0d769be5af0f7ad4112b81555710254c61c98673b8e31dc14.jpg)


![](images/eb96d97b69f0fcfdb0e6ad9eeb44395c7d424f42971a7c0d07a3e51b09b84cf2.jpg)


函数原型： 

```txt
template <MemType src, MemType dst>
    __simd_callee__ inline void LocalMemBar() 
```

# 如何使用 Reg 矢量计算 API

基于寄存器的编程模型是指每次循环将一个VL长度的数据从从LocalTensor通过数据搬 运指令加载到寄存器中，进行复杂的数学计算Compute后搬出到LocalTensor中，所有 

的计算逻辑均在寄存器中完成，从而减少LocalTensor间的数据搬运，大大提升了整体 性能，具体流程如下所示： 

![](images/f5d5231286fdbf19e77825a512f12f68b59c31e86b4d8135303fd1962b308373.jpg)


以AddVF函数为例，首先定义三个矢量数据寄存器srcReg0、srcReg1和dstReg以及掩 码寄存器mask，每次将一个VL长度的数据使用数据搬运函数从src0、src1搬入到数据 寄存器srcReg0、srcReg1中，地址偏移是src0Addr+ i * oneRepeatSize、src1Addr + i * oneRepeatSize，然后调用Add函数，将结果存入到dstReg中（dstReg= srcReg0 + srcReg1)，mask表示参与Add计算的元素个数，最后调用数据搬运函数将结果从 dstReg中搬出到dst。 

Add的原型定义如下： 

```cpp
template<typename T = DefaultType, MaskMergeMode mode = MaskMergeMode::ZEROING, typename U> _simd_callee__ inline void Add(U& dstReg, U& srcReg0, U& srcReg1, MaskReg& mask) 
```

其中模板参数T表示操作数数据类型，MaskMergeMode表示mask未筛选的元素在dst 中置零或者保留原值，UpdateMask函数用于更新参与计算的mask元素，每次循环都 会消耗一个VL长度的元素。LoadAlign和StoreAlign函数用于数据的搬入搬出， LoadAlign(srcReg0, src0Addr + i * oneRepeatSize)表示数据从LocalTensor搬入到 srcReg0寄存器，起始地址是src0Addr + i * oneRepeatSize，StoreAlign(dstAddr+ i * oneRepeatSize, dstReg, mask)表示将dstReg搬出到LocalTensor，目标地址是dstAddr + i * oneRepatSize, mask表示有多少元素参与搬出。 

# Reg 矢量计算编程示例

以Add函数为例，宏函数AddVF使用__simd_vf__标记，这样的函数也被称为SIMD VF 函数。AddVF包含6个参数。dstAddr表示输出数据，src0Addr和src1Addr表示输入数 据。__ubuf__ 类型表示用于矢量计算的Local Memory（Unified Buffer），是 LocalTensor实际存储的物理位置。count表示输入数据参与计算的元素个数， repeatTimes表示循环次数，oneRepeatSize表示每次循环参与的数据量。Add函数首 先计算每次能搬入到寄存器中的数据量oneRepeatSize和循环次数repeatTimes，然后 使用GetPhyAddr获取输入数据和输出数据的UB地址，并通过asc_vf_call<AddVF<T>> 调用AddVF宏函数进行计算。 

```cpp
// SIMD函数  
template <typename T>  
_simd_vf__inline void AddVF(_ubuf_T\* dstAddr, _ubuf_T\* src0Addr, _ubuf_T\* src1Addr, uint32_t count, uint32_t oneRepeatSize, uint16_t repeatTimes)  
{  
    AscendC::Reg::RegTensor<T> srcReg0;  
    AscendC::Reg::RegTensor<T> srcReg0;  
    AscendC::Reg::RegTensor<T> dstReg;  
    AscendC::Reg::MaskReg mask;  
    for (uint16_t i = 0; i < repeatTimes; ++i) {  
        mask = AscendC::Reg::UpdateMask<T>(count);  
        AscendC::Reg::LoadAlign(srcReg0, src0Addr + i * oneRepeatSize);  
        AscendC::Reg::LoadAlign(srcReg1, src1Addr + i * oneRepeatSize);  
        AscendC::Reg::AdddstReg, srcReg0, srcReg1, mask);  
        AscendC::Reg::StoreAlign.dstAddr + i * oneRepeatSize, dstReg, mask);  
    }  
} 
```

```cpp
template<typename T> __aicore__inline void Compute()
{
    AscendC::LocalTensor<T> dst = outQueueZ AllocTensor<T>(); 
    AscendC::LocalTensor<T> src0 = inQueueX.DeQue<T>(); 
    AscendC::LocalTensor<T> src1 = inQueueY.DeQue<T>(); 
    constexpr uint32_t oneRepeatSize = AscendC::GetVecLen()/sizeof(T); 
    uint32_t count = 512; //向上取整，计算repeat 
    uint16_t repeatTimes = AscendC::CeilDivision(count, oneRepeatSize); 
    __ubuf_T* dstAddr = (_ubuf_T*)dst.GetPhyAddr(); 
    __ubuf_T* src0Addr = (_ubuf_T*)src0.GetPhyAddr(); 
    __ubuf_T* src1Addr = (_ubuf_T*)src1.GetPhyAddr(); 
    asc_vf_call<AddVF<T>>(dstAddr, src0Addr, src1Addr, count, oneRepeatSize, repeatTimes); 
    outQueueZ.EnQue.dst); 
    inQueueX.FreeTensor(src0); 
    inQueueY.FreeTensor(src1); 
```

# 2.2.3.3.4 基于语言扩展层 C API 编程

基于语言扩展层C API编程时，通过提供纯C风格的接口，符合C语言算子开发习惯，提 供与业界类似编程体验。本节主要介绍C API编程范式，通过内存管理、同步控制、计 算及搬运接口相关的介绍，使开发者更好地理解和使用C API进行编程。 

# 内存管理

C API通过C风格的地址限定符描述不同层级内存，并且可以通过指针直接操作内存地 址，从而精准控制数据存放位置。不同存储单元的地址限定符介绍如下： 


表 2-7 不同存储单元的地址限定符


<table><tr><td>存储单元</td><td>地址限定符</td><td>描述</td></tr><tr><td>Global Memory</td><td>__gm__</td><td>表示被修饰的变量位于Global Memory地址空间。</td></tr><tr><td>Unified Buffer</td><td>__ubuf__</td><td>表示被修饰的变量位于Unified Buffer地址空间。</td></tr><tr><td>L1 Buffer</td><td>__cbuf__</td><td>表示被修饰的变量位于L1 Buffer地址空间。</td></tr><tr><td>LOA Buffer</td><td>__ca__</td><td>表示被修饰的变量位于LOA Buffer地址空间。</td></tr><tr><td>LOB Buffer</td><td>__cb__</td><td>表示被修饰的变量位于LOB Buffer地址空间。</td></tr><tr><td>LOC Buffer</td><td>__cc__</td><td>表示被修饰的变量位于LOC Buffer地址空间。</td></tr></table>

地址空间限定符可以在数组或指针变量声明中使用，用于指定对象分配的区域。同一 个类型上不允许使用多个地址空间限定符。 

基于C API编程时，开发者需要自行通过显式的内存管理来控制内存，不同层级的内存 申请介绍如下： 

全局内存（Global Memory）：一般通过Device侧接口aclrtMalloc接口分配传 入，需要增加对应地址限定符使用。 

内部存储（包含Unified Buffer、L1 Buffer等）：由用户自行申请空间，通过地址 限定符关键字在Kernel内声明。无自动垃圾回收机制，需开发者严格控制生命周 期。以申请UB空间为例： 

```c
//在数组变量声明中使用地址空间限定符  
//total_length指参与计算的数据长度  
constexpr uint64_t total_length = 256;  
__ubuf__ float xLocal[ total_length ];  
__ubuf__ float yLocal[ total_length ];  
__ubuf__ float zLocal[ total_length ];  
//在指针变量声明中使用地址空间限定符  
uint64_t offset = 0; //首先为src0申请内存，从0开始。  
__ubuf__ half* src0 = (_ubuf__ half*)asc_get_phy_buf_addr(offset); //获取src0的地址，通过 ubuf_ 关键字指定该地址指向UB内存。 
```

# 同步控制

NPU内部有不同的计算单元，在计算前往往需要把计算数据搬运到计算单元上。不同 计算单元上的计算过程、数据搬运过程可划分为不同的流水线。如下表所示： 


表 2-8 指令流水类型和相关说明


<table><tr><td>流水类型</td><td>含义</td></tr><tr><td>PIPE_S</td><td>标量流水线</td></tr><tr><td>PIPE_V</td><td>矢量计算流水及部分硬件架构下的LOC Buffer-&gt;UB数据搬运流水</td></tr><tr><td>PIPE_M</td><td>矩阵计算流水</td></tr><tr><td>PIPE_MTE1</td><td>L1 Buffer -&gt;L0A Buffer、L1 Buffer-&gt;L0B Buffer数据搬运流水</td></tr><tr><td>PIPE_MTE2</td><td>GM-&gt;L1 Buffer、GM-&gt;UB等数据搬运流水</td></tr><tr><td>PIPE_MTE3</td><td>UB-&gt;GM等数据搬运流水</td></tr><tr><td>PIPE_fix</td><td>LOC Buffer-&gt;GM、LOC Buffer -&gt;L1等数据搬运流水</td></tr></table>

在调用C API提供的搬运或者计算类API编写算子时，需要根据流水线之间的数据依赖 关系插入对应的同步事件。C API提供了两种不同的同步控制接口，同步控制粒度由浅 到深，帮助开发者精准适配硬件架构，挖掘异构计算的性能极限。 

第一种：和静态Tensor编程方式一致的同步接口，主要通过asc_sync_notify/ asc_sync_wait接口来精细化管理，需要手动管理事件的类型和事件ID，还需要考虑正 向同步（循环内依赖）与反向同步（循环间依赖）。极致性能场景推荐使用此方式。 使用示例如下： 

```c
// 本片段仅用于说明数据搬运、矢量计算、同步操作间的关系。各接口的完整参数及上下文请参考下文中的编程示例。  
asc_copy_gm2ub(); // GM->UB的搬运流水  
asc-sync_notify(Pipe_MTE2, PIPE_V, EVENT_ID0);  
asc-sync_wait(Pipe_MTE2, PIPE_V, EVENT_ID0);  
asc_add(); // 矢量计算流水  
asc-sync_notify(Pipe_V, PIPE_MTE3, EVENT_ID0);  
asc-sync_wait(Pipe_V, PIPE_MTE3, EVENT_ID0);  
asc_copy ub2gm(); // UB->GM的搬运流水 
```

第二种：不感知流水类型的同步接口，将asc_sync接口添加在对应流水类型的指令后 面来实现。使用这类同步接口时，不需要考虑指令流水类型，接口内部会自动管理所 有指令流水的同步，简化同步指令。性能不敏感场景下，可以使用此方式。使用示例 如下： 

```txt
// 本片段仅用于说明数据搬运、矢量计算、同步操作间的关系。各接口的完整参数及上下文请参考下文中的编程示例。 
```

```c
asc_copy_gm2ub();//GM->UB的搬运流水  
ascSync(); //全同步无需考虑后面的指令流水  
asc_add(); //矢量计算流水  
ascSync(); //全同步无需考虑后面的指令流水  
asc_copy ub2gm(); //UB->GM的搬运流水 
```

另外，C API还提供了一组包含同步能力的搬运及计算接口，开发者无需显式手动管理 同步，同步操作隐藏在相应的接口中。性能不敏感场景下，推荐使用此方式。使用示 例如下： 

```txt
// 本片段仅用于说明数据搬运、矢量计算、同步操作间的关系。各接口的完整参数及上下文请参考下文中的编程示例。  
asc_copy_gm2ub_sync(); // GM->UB的搬运流水同时包含了和后面的任意指令流水的同步  
asc_add_sync(); // 矢量计算流水同时包含了和后面的任意指令流水的同步  
asc_copy ub2gm_SYNC(); // UB->GM的搬运流水同时包含了和后面的任意指令流水的同步 
```

# 编程示例


内存管理与精细化同步完整示例：


```c
include <cstdint>   
#include "c(API/asc_simd.h"   
constexpr uint32_t C_API_ONE_BLOCK_SIZE = 32;   
constexpr uint32_t C_API_ONE_REPEAT_BYTE_SIZE = 256;   
constexpr uint32_t C_API_TOTAL_LENGTH = 16384;   
constexpr uint32_t C_API_TILE_NUM = 8;   
constexpr uint32_t C_API_TILE_LENGTH = 256;   
vector __global __aicore __void addCustom(_gm __float* x, _gm __float* y, _gm __float* z) {   
asc_init();   
uint32_t blockLength = C_API_TOTAL_length / asc_get_block_num();   
uint32_t tileLength = blockLength / C_API_TILE_NUM;   
__gm __float* xGm = x + asc_get_block_idx() * blockLength;   
__gm __float* yGm = y + asc_get_block_idx() * blockLength;   
__gm __float* zGm = z + asc_get_block_idx() * blockLength;   
__ubuf __float xLocal[C_API_TILE_LENGTH];   
__ubuf __float yLocal[C_API_TILE_LENGTH];   
__ubuf __float zLocal[C_API_TILE_LENGTH];   
uint16_t burst_len = tileLength;   
for (uint32_t i = 0; i < C_API_TILE_NUM; i++) { if (i != 0) { asccSync_wait(PIPE_V, PIPE_MTE2, EVENT_ID0); }   
burst_len = tileLength * sizeof(float) / C_API_ONE_BLOCK_SIZE;   
asc_copy_gm2ub(xLocal, xGm + i * tileLength, 0, 1, burst_len, 0, 0);   
asc_copy_gm2ub(yLocal, yGm + i * tileLength, 0, 1, burst_len, 0, 0);   
asc-sync_notify(PIPE_MTE2, PIPE_V, EVENT_ID0);   
asc-sync_wait(PIPE_MTE2, PIPE_V, EVENT_ID0);   
if (i != 0) { asccSync_wait(PIPE_MTE3, PIPE_V, EVENT_ID0); }   
asc_add(zLocal, xLocal, yLocal, tileLength * sizeof(float) / C_API_ONE_REPEAT_BYTE_SIZE, 1, 1, 1, 8, 8, 8);   
if (i != (C_API_TILE_NUM-1)) { asccSyncNotify(PIPE_V, PIPE_MTE2, EVENT_ID0); } 
```

```c
asc_SYNC_notify(PIPE_V, PIPE_MTE3, EVENT_ID0);
asc_SYNC_wait(PIPE_V, PIPE_MTE3, EVENT_ID0);
asc_copy ub2gm(zGm + i * tileLength, zLocal, 0, 1, burst_len, 0, 0);
if (i != (C_API_TILE_NUM-1)) {
    esc_SYNC_notify(PIPE_MTE3, PIPE_V, EVENT_ID0);
} 
```


内存管理与不感知流水类型的同步管理完整示例如下：


include <cstdint>   
#include "c api/asc_simd.h"   
constexpr uint32_t TILE_LENGTH $= 2048$ constexpr uint32_t NUM_BLOCKS $= 8$ vector __global __aicore __void addCustom(_gm __float\* x, _gm __float\* y, _gm __float\* z)   
{ asc_init(); uint32_t blockLength $\equiv$ NUM_BLOCKS \* TILE_LENGTH / asc_get_block_num(); _gm __float\* xGm $\equiv$ x + asc_get_block_idx() \* blockLength; _gm __float\* yGm $\equiv$ y + asc_get_block_idx() \* blockLength; _gm __float\* zGm $\equiv$ z + asc_get_block_idx() \* blockLength; _ubuf __float xLocal[TILE_LENGTH]; _ubuf __float yLocal[TILE_LENGTH]; _ubuf __float zLocal[TILE_LENGTH];   
asc_copy_gm2ub(_ubuf __void\*)xLocal, (_gm __void\*)xGm, blockLength \* sizeof(float));   
asc_copy_gm2ub(_ubuf __void\*)yLocal, (_gm __void\*)yGm, blockLength \* sizeof(float));   
asc-sync();   
asc_add(zLocal, xLocal, yLocal, blockLength);   
asc-sync();   
asc_copy ub2gm(_gm __void\*)zGm, (_ubuf __void\*)zLocal, blockLength \* sizeof(float);   
asc-sync(); 


内存管理与使用带同步能力的接口完整示例如下：


```txt
include <cstdint> #include "c api/asc_simd.h" constexpr uint32_t TILE_LENGTH = 2048; constexpr uint32_t NUM_BLOCKS = 8; _vector __global __aicore __void addCustom(_gm __float* x, _gm __float* y, _gm __float* z) { _asc_init(); _ubuf __float xLocal[TILE_LENGTH]; _ubuf __float yLocal[TILE_LENGTH]; _ubuf __float zLocal[TILE_LENGTH]; uint32_t blockLength = TILE_LENGTH * NUM_BLOCKS / asc_get_block_num(); _asc_copy_gm2ubSync(_ubuf __void*)xLocal, (_gm __void*)(x + asc_get_blockidx() * blockLength), blockLength * sizeof(float)); _asc_copy_gm2ubSync(_ubuf __void*)yLocal, (_gm __void*)(y + asc_get_blockidx() * blockLength), blockLength * sizeof(float); _asc_add_sync(zLocal, xLocal, yLocal, blockLength); _asc_copy ub2gmSync(_gm __void*)(z + asc_get_blockidx() * blockLength), (_ubuf __void*)zLocal, 
```

```txt
blockLength \* sizeof(float));   
} 
```


内存管理、Reg矢量计算与精细化同步完整示例：


```c
include <cstdint>   
#include "c api/asc_simd.h"   
constexpr uint32_t TILE_LENGTH = 2048;   
constexpr uint32_t NUM_BLOCKS = 8;   
constexpr uint32_t BLK_NUM = 1;   
constexpr uint32_t MASK = 32;   
__simd_vf__inline void AddVF( uint16_t rep, uint16_t one_rep_size, uint32_t blockLength, __ubuf__float* xLocal, __ubuf__float* yLocal, __ubuf__float* zLocal)   
{ vector bool vmask; vector_float reg_src0; vector_float reg_src1; vector_float reg.dst; uint32_t remaining = blockLength; for (uint16_t i = 0; i < rep; ++i) { vmask = asc_update_mask_b32(remaining); asc_loadalign(reg_src0, xLocal + i * one_rep_size); asc_loadalign(reg_src1, yLocal + i * one_rep_size); asc_add(reg.dst, reg_src0, reg_src1, vmask); asc/storealign(zLocal + i * one_rep_size, reg.dst, vmask); }   
}   
vector __global __aicore__void addCustom(_gm__float* x, _gm__float* y, _gm__float* z)   
{ Asc_init(); uint32_t blockLength = TILE_LENGTH * NUM_BLOCKS / asc_get_block_num(); _gm__float* xGm = x + get.block_idx() * blockLength; _gm__float* yGm = y + get.block_idx() * blockLength; _gm__float* zGm = z + get.block_idx() * blockLength; _ubuf__float xLocal[TILE_LENGTH]; _ubuf__float yLocal[TILE_LENGTH]; _ubuf__float zLocal[TILE_LENGTH]; const uint8_t cacheMode0 = static_cast<uint8_t>(((uint64_t)xGm) >> 60); const uint8_t cacheMode1 = static_cast<uint8_t>(((uint64_t)yGm) >> 60); const uint8_t cacheMode2 = static_cast<uint8_t>(((uint64_t)zGm) >> 60); uint32_t burstLength = blockLength * 32; uint64_t srcStride = burstLength; uint32_t dstStride = (burstLength + 31) / 32 * 32;   
asc_copy_gm2ub_align(_ubuf__float*)xLocal, xGm, BLK_NUM, burstLength, 0, 0, true, cacheMode0, srcStride, dstStride); ascopy_gm2ub_align(_ubuf__float*)yLocal, yGm, BLK_NUM, burstLength, 0, 0, true, cacheMode1, srcStride, dstStride); as sync notify(Pipe_MTE2, PIPE_V, EVENT_ID0); as sync_wait(Pipe_MTE2, PIPE_V, EVENT_ID0); uint16_t mask_bit_size = 256; uint16_t one_rep_size = mask_bit_size / sizeof(float); uint16_t rep = (blockLength + one_rep_size - 1) / one_rep_size; asvf_callAddVF>(rep, one_rep_size, blockLength, (_ubuf__float*)xLocal, (_ubuf__float*)yLocal, (_ubuf__float*)zLocal); as sync notify(Pipe_V, PIPE_MTE3, EVENT_ID0); as sync_wait(Pipe_V, PIPE_MTE3, EVENT_ID0); as copy ub2gm align(zGm, (_ubuf__float*)zLocal, BLK_NUM, burstLength, cacheMode2, srcStride, dstStride); } 
```

# 2.2.3.4 SIMD 与 SIMT 混合编程

# 抽象硬件架构

AI Core上SIMD（Single Instruction Multiple Data，单指令多数据）与SIMT（Single Instruction Multiple Thread，单指令多线程）混合编程当前仅支持Atlas 350 加速 卡。该架构通过统一的计算资源和内存层级，实现向量级并行与线程级并行的高效协 同。 

整个执行过程以Vector Function（VF）为基本调度单位，VF为一个基本函数块。 SIMD与SIMT混合编程支持在同一算子中灵活切换SIMD与SIMT执行方式，两种不同类 型的VF可以快速切换，每个VF代表一个独立的计算任务片段，通常对应算子中的一段 可并行处理的逻辑，从而在性能、能效与开发效率之间取得更优平衡。在SIMD与SIMT 混合编程中： 

一个核函数中可包含多个VF。 

每个VF可以选择使用SIMD或SIMT方式进行编程。 

不同类型VF之间可以快速切换，切换粒度为单个VF。 

在同一时刻，一个AIV核只能执行SIMT或SIMD任务。 

在SIMD与SIMT混合编程中，SIMT能够简化复杂算子与不规则控制流的开发；而SIMD 基于向量寄存器与指令，实现高效的数据并行处理，即单指令处理多数据，提升每周 期的吞吐量。SIMD与SIMT混合编程支持开发者根据算子特征进行精细化映射：规则的 逐元素elementwise操作通过SIMD获得高带宽和高算力利用率，不规则或包含分支的 计算通过SIMT来缓解发散和控制复杂度。在系统层面，这有利于提高硬件利用率和能 效；同时，也更便于进行算子融合和数据复用等优化。同一个算子中既包含SIMD擅长 的连续规整计算，也包含SIMT擅长的离散访问等任务，从而在同一算子中同时利用 SIMD和SIMT的优势。 

如图2-11所示，SIMD和SIMT的内部执行流程为： 

Scalar计算单元将VF发射到Vector Function Queue中。 

SIMD与SIMT混合编程的工作模式以VF为粒度进行切换，执行上下文（UB Data Cache）在VF切换时会被保留。 

SIMD和SIMT之间的VF串序执行，同一时刻，一个AIV核仅能执行SIMD或SIMT任 务。 

● VF执行完成后，结果数据被写回Unified Buffer或Global Memory。 


图 2-11 SIMD 与 SIMT 混合编程硬件架构图


![](images/4b67f2004a4dca49e57625ea6b52d9efafd226de7403251a59e3162ccc6d89fe.jpg)


SIMD与SIMT编程存在以下差异： 


表 2-9 SIMD 与 SIMT 核心差异点


<table><tr><td>维度</td><td>SIMD</td><td>SIMT</td></tr><tr><td>编程模型</td><td>单指令多数据（SIMD），基于向量寄存器与向量指令。</td><td>单指令多线程（SIMT），以线程为单位并行执行。</td></tr><tr><td>数据搬运方式</td><td>通过显式Load/Store将数据从 Unified Buffer搬运到向量寄存器。
不支持直接从Global Memory搬运数据到SIMD的向量寄存器。</td><td>支持直接读写Global Memory或 Unified Buffer中的数据。</td></tr><tr><td>适用场景</td><td>规则、连续的逐元素操作（elementwise），如卷积、矩阵乘法、向量操作等。</td><td>不规则、含分支、动态访问等复杂逻辑，如注意力机制、稀疏操作等。</td></tr></table>

尽管SIMD与SIMT在编程模型和执行机制上有显著差异，但在硬件层面上共享以下关键 资源： 

● SIMT VF与SIMD VF共享ICache（Instruction Cache），提升指令预取效率。 

● SIMT与SIMD共享Vector ALU单元，基于该单元执行的功能和性能基本相同。 

Unified Buffer内存空间中一部分为SIMT与SIMD共享空间，另一部分作为SIMT的 Data Cache。 

# 内存层级

# SIMT内存层次结构包含：

每个线程独立的寄存器和栈，用于存储局部变量。可用寄存器数量与线程块中线 程数有关，具体支持情况请见表2-23。线程块内所有线程共享本地内存Unified Buffer。该内存区域由线程块内所有线程共同访问，且其生命周期和线程块一 致。 

所有线程均可通过Data Cache访问全局内存，即Global Memory。 

# SIMD内存层次结构包含：

SIMD的Register File（简称RF）中的多种Reg，Reg的类型请见Reg数据类型定 义。 

RF中所有Reg共享本地内存，即Unified Buffer。 

所有核共享全局内存，即Global Memory。 


图 2-12 SIMD 与 SIMT 混合编程内存模型示意图


![](images/5b0682d1cecd2deddaab8b4580e0b787e3026b25a528e9631fe1fb796d887511.jpg)


# UB 内存分配

UB（即Unified Buffer）内存空间总大小为256KB，参考图2-13，按功能划分为四个主 要区域，从低地址向高地址依次为静态内存、动态内存、 预留空间 、Data Cache， 具体结构如下： 

1. 静态内存：从内存的起始地址分配一段指定大小的内存空间，其大小在编译时确 定，不可动态修改。 

// 静态内存通过数组分配，例如： __ubuf__ char staticBuf[1024]; 

2. 动态内存（该方式将在后续版本中支持）：位于静态内存之后，通过<<<>>>中参 数dynUBufSize指定的动态内存大小空间，可通过以下方式申请使用： 

通过TPipe的相关接口申请。 

通过LocalMemAllocator的Alloc接口申请。 

使用动态数组分配。 

// 动态内存通过动态数组分配，例如： 

extern __ubuf__ char dynamicBuf[]; 

由于上述两种方法申请动态内存时均从静态内存结束位置之后开始分配，如果同 时使用可能会导致地址空间重叠，从而引发未定义行为，因此只能选择其中一种 方法进行申请。 

3. 预留空间：编译器和Ascend C预留空间，大小固定为8KB。 

4. Data Cache：SIMT专有的Data Cache空间，内存大小必须大于或等于32KB。 

# 说明

动态内存的动态数组分配方式目前开发中，将在后续版本中支持，请关注后续版本。 

● DataCache $=$ UB总大小（256KB） – 静态内存 – 动态内存 – 预留空间(8KB） 

● 若DataCache小于32KB，会出现校验报错。 

● 在SIMD与SIMT混合编程的场景下，算子内部不能使用全部的Unified Buffer空间，除了预留 8KB空间外，还需至少为SIMT预留32KB的Data Cache空间。 


图 2-13 UB 内存分配图


![](images/6f2d4188ec2d776d1b6f1dd17c7f7acd8248468513d01e5a5da6a24d00ba2e64.jpg)


# 核函数的定义

核函数定义方式 

SIMT VF函数定义： 

定义SIMT VF核函数时，__launch_bounds__(thread_num)是可选配置，用 于在编译期指定核函数启动的最大线程数，如果不配置thread_num， thread_num默认为1024。 

SIMD与SIMT混合编程中SIMT VF核函数定义的__simt_vf__、 _gm__修饰符 需要单独进行标识。关于SIMT VF函数编程的相关约束请参考附录。 

__simt__vf__ __launch_bounds__(thread_num) inline void simt_vector_function(__ubuf__ float* input, …) 

SIMD VF函数定义： 

SIMD VF核函数使用__simd_vf__修饰符进行标识。 

__simd_vf__ inline void my_kernel(__gm__ uint8_t* x, __gm__ uint8_t* y, __gm__ uint8_t* z); 

# 须知

SIMD_VF和SIMT_VF的入参只支持PoD（Plain Old Data）数据类型。 

● PoD数据类型：包括基础数据类型（int32_t、float等）以及这些基本数据 类型组成的数组和结构体；不包括构造函数、析构函数、复制构造函数、 复制赋值操作符、非静态成员函数或虚函数的类或结构体。 

SIMD与SIMT混合编程核函数的定义： 

i. 核函数使用__global__、__aicore__修饰符进行标识。 

ii. 核函数的入参和SIMD函数的用法一致。 

iii. 在SIMD与SIMT混合编程核函数中调用SIMT VF函数和SIMD VF函数。 

__global__ __aicore__ void my_kernel(__gm__ float*,…) 

SIMD与SIMT混合核函数调用方式： 

a. 核函数的调用请参见核函数。执行配置由3个参数决定： 

numBlocks：设置核函数启用的核数，通过<<<...>>>的方式传入。 

dynUBufSize：用于指定动态内存大小。动态内存的申请方式请参见UB 内存分配中的动态内存。 

stream：类型为aclrtStream，用于维护异步操作的执行顺序，确保在 device上按照程序中的代码调用顺序执行。 

b. 开发者需要保证核函数内使用的动态内存大小不超过dynUBufSize，超出会越 界访问预留空间或者Data Cache，引发未定义行为。 

c. 可配置的最大动态内存大小 $=$ 256KB - 保留空间（8KB）- 32KB（最小 DCache）- 静态内存。 

kernel_name<<<numBlocks, dynUBufSize, stream>>>(args...) 

# 调用层级

核函数：使用__global__ __aicore__标识，是Device侧的入口函数，在Host侧可以 通过<<<...>>>语法进行调用。 

_aicore__函数：使用__aicore__标识该函数在Device侧执行。核函数内可以调用 _aicore__函数。 

simd vf函数：使用__simd_vf__标记，能被核函数通过asc_vf_call接口调用。simd vf函数内只能调用__simd_callee__函数和constexpr函数。 

simt vf函数：使用__simt_vf__标记，能被核函数通过asc_vf_call接口调用。simt vf函数内只能调用__simt_callee__函数和constexpr函数。 

_simd_callee__子函数：被simd vf函数调用的子函数，子函数可能有返回值或者 通过引用传参，这类子函数通过__simd_callee__标识。__simd_callee__函数内只 能调用__simd_callee__函数和constexpr函数。 

_simt_callee__子函数：被simt vf函数调用的子函数，子函数可能有返回值或者 通过引用传参，这类子函数通过__simt_callee__标识。__simt_callee__函数内只能 调用__simt_callee__函数和constexpr函数。 

具体支持的调用关系图如下所示。 


图2-14 函数调用关系图


![](images/47cf56bcddc87165234570e9bce856bb5a0fa2db4a668e96e955ffa0d50faebc.jpg)


# 编程示例


样例中介绍的算子完整代码请参见SIMD与SIMT混合编程实现gather&adds算子样 例。


__simt_vf___launch_bounds_(THREAD_COUNT) inline void simt_gather( __gm__ float* input, __gm__ uint32_t* index, __ubuf__float* gather_output, uint32_t input_total_length, uint32_t index_total_length, uint32_t output_total_length)   
{ if (threadIdx.x >= output_total_length) { return; } // blockIdx will be supported later. int idx $=$ blockIdx.x \* blockDim.x + threadIdx.x; if (idx >= index_total_length) { return; } uint32_t gatheridx $=$ index[idx]; if (gatheridx >= input_total_length) { return; } gather_output[threadIdx.x] $=$ input[gather IDX]; 

```lisp
__simd_vf__inline void simd Adds(_ubuf_float* output, _ubuf_float* input, uint32_t count, uint32_t onerepeat_size, uint16_t repeat(times)   
{ AscendC::Reg::RegTensor<float> src_reg0; AscendC::Reg::RegTensor<float> dst_reg0; AscendC::Reg::MaskReg mask_reg; for (uint16_t i = 0; i < repeat(times; i++) { mask_reg = AscendC::Reg::UpdateMask<float>(count); AscendC::Reg::LoadAlign(src_reg0, input + i * oneRepeat_size); AscendC::Reg::Adds.dst_reg0, src_reg0, ADDS_ADDEND, mask_reg); AscendC::Reg::StoreAlign(output + i * oneRepeat_size, dst_reg0, mask_reg); }   
}   
__global __aicore__void gather_and Adds_kernel(_gm_float* input, _gm_uint32_t* index, _gm_ float* output, uint32_t input_total_length, uint32_t index_total_length)   
{ KERNEL_TASK_TYPE_DEFAULT(Kernel_TYPE_AIV_ONLY); AscendC::LocalMemAllocator<AscendC::Hardware::UB> ub_allocator; // 1. gather numbers from input. uint32_t index_total_length_per_block = index_total_length / AscendC::GetBlockNum(); AscendC::LocalTensor<float> gather_output = ub_allocator Alloc<float>(index_total_length_per_block); asc_vf_call<simt_gather>(dim3(THREAD_COUNT),input,index, (_ubuf floats)gather_output.GetPhyAddr(), input_total_length, index_total_length, index_total_length_per_block); // 2. use reg compute api to do addition. AscendC::LocalTensor<float> adds_output = ub_allocator Alloc<float>(index_total_length_per_block); constexpr uint32_t onerepeat_size = AscendC::GetVecLen() / sizeof(float); uint16_t repeat_times = (index_total_length_per_block + onerepeat_size - 1) / onerepeat_size; asc_vf_call<simdadds>((_ubuf floats)*adds_output.GetPhyAddr(), (_ubuf floats)gather_output.GetPhyAddr(), index_total_length_per_block, onerepeat_size, repeat-times); AscendC::SetFlag<AscendC::HardEvent::V_MTE3>(0); AscendC::WaitFlag<AscendC::HardEvent::V_MTE3>(0); // 3. copy data to global memory. AscendC::GlobalTensor<float> output_globaloxel; output_globaloxel.SetGlobalBuffer(output + index_total_length_per_block * AscendC::GetBlockIdx()); AscendC::DataCopy(output_globaloxel, adds_output, index_total_length_per_block);   
}   
int main(int argc, char *argv[])   
{ ... //numBlocks only supports one dimension currently. gather_and_adds_kernel<<numBlocks,dynUBufSize, stream>>*(input_device, index_device, output_device, input_total_length, index_total_length); ... 
```

# 2.2.4 AI Core SIMT 编程

# 2.2.4.1 抽象硬件架构

AI Core上的SIMT（Single Instruction Multiple Thread，单指令多线程）编程允许指 令对数据进行独立寻址，从而支持线程级并行计算。这种方式特别适用于离散访问和 复杂控制逻辑等场景，目前仅支持Atlas 350 加速卡。 

SIMT编程能够简化复杂算子和不规则控制流的开发，通过SIMT编程可以有效缓解包含 分支等的发散计算，同时控制程序复杂度。在系统层面，这有助于提高硬件利用率和 能效。如图2-15所示，AI处理器内部有多个Vector Core，每个Vector Core包含计算单 元、Share Memory即Unified Buffer、寄存器和堆栈空间，核外的Global Memory是 全局内存空间，被所有Vector Core共享。 


图 2-15 SIMT 抽象硬件架构图


![](images/dc91a3ad3b44f92c218206f549b29f6df6e90691921a2f84d89a223a42aa590d.jpg)


以下是SIMT多线程计算涉及到的硬件资源的说明。 

每个线程拥有独立的寄存器和栈空间，用于存储局部数据，寄存器的数量受线程 块内线程数量的影响。线程数量越多，每个线程拥有的寄存器数量就越少。 

Unified Buffer的一部分内存空间作为线程块内所有线程的共享内存（Share Memory），支持线程块内的线程进行数据交互，一部分作为读取Global Memory的Data Cache。 

SIMT模式中，读取Global Memory上的数据时，通过Data Cache单元完成数据中 转，数据流经由Global Memory到Data Cache，再从Data Cache到寄存器。Data Cache是Unified Buffer中预留的一部分空间，其最大容量为128KB，最小容量为 32KB，实际大小由用户自主分配。 

若您对上述内容中的线程、线程块等概念不熟悉，建议查阅2.2.4.2 线程架构了解更多 SIMT线程架构知识；同时，您也可以通过阅读2.2.4.3 内存层级，了解更多内存空间说 明及配置方式。 

# 2.2.4.2 线程架构

SIMT编程模型的线程层次结构分为两层： 

线程块网格（Grid）：由多个线程块（Thread Block）组成，使用内置变量 gridDim来表示启用的线程块的个数，同一时刻一个AIV核只执行一个线程块任 务。 

线程块（Thread Block）：由若干线程（thread）组成，使用内置变量blockDim 表示一个线程块启用的的线程个数，一个线程块最多可以启用2048个线程。 

基于SIMT编程模型的程序，在AIV核上执行多个结构相同的线程块，执行的总线程数 等于gridDim*blockDim。 


Thread Block


![](images/60e9b81c6aeb40d6c3e900598acab97d0b84c445867581ece1ccd2e825b06693.jpg)



Thread Block


![](images/f7873ae71803392c3db7728e79df337b32c1cec42dd69947a58c0417071f61f7.jpg)



Thread Block


![](images/876192718ccb6094520153b8a928cc3ea67dbaee3ac57f9d1519353eeac80a0d.jpg)



Thread Block


![](images/cd75e03432ef16ed7cd9a5ce28569848d6f332e8b76c7103066a424fb8f4e20a.jpg)



Thread Block


![](images/529e7b9aa90c5d6f35a2f10cada418016416220292cef950b24916cafe26533c.jpg)


gridDim由三维结构dim3来表示，{dimx，dimy，dimz}用于指定3个不同维度的线程 块的大小，三维乘积的总数不超过65535，各线程块可通过线程块索引blockIdx进行 标识。blockDim也由dim3三维结构表示，三维乘积的总数不超过2048，各线程可通 过线程块内线程索引threadIdx进行标识。线程索引的计算示例如下图所示： 


blockDim.x = 6


![](images/43e3800af85b770f46acd8471142a48823dce5494bb4b658899f52ece5a79497.jpg)



blockIdx.x = 0


![](images/35243c98ae8fdca9d5482f6d6f653cae9d92ed5d3825054c0a625b2f51e45add.jpg)



blockIdx.x = 1



threadIdx.x = 4



线程索引为：2*6+4=16


![](images/eebcb06a06c21a7d3a59c34e14f8c08ffadd600853bd92a349ffdb861437e27a.jpg)



blockIdx.x = 2


![](images/4ca64b10d18da44cccd9877483d3723865b2dc540d2d36dfe340b41ff7f5e806.jpg)



blockIdx.x = 3


![](images/036c3be6f8f44f5b4838b70ced4f45f4bdc7077da3479a0e6b5e6c73bbbc48ec.jpg)



blockIdxx =4


底层调度过程中，同一时刻一个AIV只能执行一个线程块任务，每个线程块会被切分成 多个Warp依次调度并完成执行。Warp是执行相同指令的线程的集合，每个Warp包含 32个线程。每个AIV核包含4个Warp调度器（Warp Scheduler），调度器编号 scheduler id为warp id % 4。 

# 2.2.4.3 内存层级

SIMT编程可使用的内存空间包含如下三种： 

每个线程独立的寄存器和栈，用于存储局部变量。可用寄存器数量与线程块中线 程数有关，具体支持情况请见下表。 


表 2-10 LAUNCH_BOUND 的 Thread 数量与每个 Thread 可用寄存器数


<table><tr><td>Thread的个数(个)</td><td>每个Thread可用寄存器个数(个)</td></tr><tr><td>1025~2048</td><td>16</td></tr><tr><td>513~1024</td><td>32</td></tr><tr><td>257~512</td><td>64</td></tr><tr><td>1~256</td><td>127</td></tr></table>

线程块内所有线程共享的本地内存，即Unified Buffer。该内存区域由线程块内所 有线程共同访问，且其生命周期和线程块一致。 

所有线程均可直接访问的全局内存，即Global Memory。 

![](images/391b3d42880461f4d9f985941461bba04dd02ef9d8f6cf602cf821a8e6272ba3.jpg)


Unified Buffer内存空间总大小为256KB，按功能划分为四个主要区域，从低地址向高 地址依次为静态内存、动态内存、 预留空间、Data Cache。 

![](images/411b15f75b4f5bf019c916611b37259322d7b2d69e75f4aaeeb7c2f9703243d8.jpg)


# 具体结构如下：

1. 静态内存：从内存的起始地址分配一段指定大小的内存空间，其大小在编译时确 定，不可动态修改，开发者通过数组分配申请使用。该方式将在后续版本中支 持。 

__ubuf__ half staticBuf[1024]; 

2. 动态内存：位于静态内存之后，通过<<<>>>中参数dynUBufSize指定的动态内存 大小空间，可通过使用动态数组分配。该方式将在后续版本中支持。 extern __ubuf__ char dynamicBuf[]; 

3. 预留空间：编译器和Ascend C预留空间，大小固定为8KB。 

4. Data Cache：SIMT专有的Data Cache空间，其内存大小受用户配置的静态和动 态内存大小影响。DataCache = UB总大小（256KB） - 静态内存 - 动态内存 - 预 留空间（8KB）。用户需要合理配置静态和动态内存大小，以确保DataCache大于 或等于32KB。 

# 说明

静态内存分配、动态内存的动态数组分配方式目前开发中，将在后续版本中支持，请关注后续版 本。 

● 若DataCache小于32KB，会出现校验报错。 

SIMT场景，算子开发不能使用全部的Unified Buffer空间，除了预留8KB空间外，还需至少 为SIMT预留32KB的Data Cache空间。 

# 2.2.4.4 核函数

# 核函数的定义

Ascend C支持开发者自定义核函数来扩展C++，核函数在AI处理器上执行时实际是若 干线程在并行执行，每个线程有独立的寄存器和栈，共同完成数据计算任务。 

核函数的定义示例如下： 

```lisp
__global__void kernel_nameargument list) 
```

定义核函数时需要遵循以下规则： 

使用函数类型限定符__global__， 标识它是一个核函数。 

核函数必须具有void返回类型。 

函数入参支持的类型如下： 

基础数据类型，如int32_t、float等。 

基础数据类型的指针类型，如int32_t*、float*等，实际上这些指针指向的是 GlobalMemory内存。 

# 核函数的调用

算子程序中的函数可以分为三类：host侧执行函数、核函数（device侧执行）、device 侧执行函数（除核函数之外）。下图以Kernel直调算子开发方式为例，描述三者的调 用关系： 

host侧执行函数可以调用其它host执行函数，也就是通用C/C++编程中的函数调 用；也可以通过 $< < < . . . > > >$ 调用核函数。 

核函数可以调用除核函数之外的其它device侧执行函数。 

device侧执行函数（除核函数之外）使用类型限定符__aicore__标识，可以调用同 类的其它device侧执行函数。 


图 2-16 算子程序中三种函数间的调用关系


![](images/9476fc104a5e1fe5e47eb2aec2601b5fe928e96119d52100c38212a50e3f3a4c.jpg)


Host侧通过内核调用符<<<...>>>的语法形式调用核函数，如下所示： 

```txt
kernel_name<<numBlocks, threadsPerBlock, dynUBufSize, stream>>>(args...) 
```

执行配置由4个参数决定： 

numBlocks：为核函数配置的线程块的个数，即启用的核数, 支持int32_t和dim3 类型； 

● threadsPerBlock：每个线程块内并发执行的线程数量，支持int32_t和dim3类型； 

● dynUBufSize：动态申请内存空间总大小，一般情况设置为0； 

stream：用于host侧和device侧的流同步。 

# 2.2.4.5 同步机制

SIMT是一种单指令多线程的编程模式，其异步编程模型旨在通过多线程并发执行达到 内存操作加速的目的。在这一编程模型中，线程作为执行计算或操作内存的最小抽象 单位，其操作是相互独立的。然而，在某些应用场景中，需要支持线程间的同步，或 防止不同线程对同一内存区域的读写操作引发的数据竞争。为此，Ascend C提供了相 应的同步接口，这些接口允许开发者根据需求选择合适的同步机制，以确保异步操作 的正确性和性能。 

<table><tr><td>接口名</td><td>功能说明</td></tr><tr><td>asc_synchreads</td><td>等待当前线程块内所有线程代码都执行到该函数位置。</td></tr><tr><td>asc_threadfencce</td><td>用于保证不同线程对同一份全局、共享内存的访问过程中，写入操作的时序性。它不会阻塞线程，仅保证内存操作的可见性顺序。</td></tr><tr><td>asc_threadfencce_block</td><td>用于协调同一线程块（Thread Block）内线程之间的内存操作顺序，确保某一线程在asc_threadfencce_block()之前的所有内存操作（读写），对同一线程块内的其他线程是可见的。</td></tr></table>

# 2.2.4.6 编程示例

# 说明

SIMT编程场景当前不支持使用SIMT API，敬请期待后续版本的正式发布。 

基于SIMT进行算子开发需要使用的内置关键字和API请参见2.4.2 SIMT BuiltIn关键 字、2.4.4 SIMT语言扩展层C API。当前SIMT编程暂不支持部分语法结构，相关限制 请参考2.10.1.2 C/C++语法限制。 

考虑如下计算场景：从形状为100000 * 128的二维向量中获取指定索引的12288行数 据。算子输出output第i行数据的计算公式为： 

```txt
output[i] = input[index[i]] 
```

在核函数中完成一行数据量的计算逻辑，通过配置多个线程完成不同行的数据计算操 作。核函数的实现逻辑具体为： 

通过每个线程独有的线程索引找到当前线程需要计算的数据偏移量。 

int32_t out_row $=$ blockIdx.x * blockDim.x + threadIdx.x; 

一个线程完成一次核函数的计算操作，核函数内通过计算blockIdx.x * blockDim.x + threadIdx.x得到索引偏移，其中blockIdx是当前线程块的索引，blockDim是用 户设置的线程块数，threadIdx是当前线程在线程块内的索引，更多详细介绍请参 考2.4.2 SIMT BuiltIn关键字。 

通过下标偏移将偏移位置的输入数据拷贝到输出中，从而完成获取指定数据的功 能。 

```txt
uint32_t in_row = index[out_row];  
for (int32_t col = 0; col < in_width; col++) { //每个线程完成一行数据的计算操作 int input_idx = in_row * in_width + col; int output_idx = out_row * in_width + col; gather_output[output_idx] = input[input_idx]; } 
```

核函数的实现参考如下代码。 

```txt
template<typename type_data, typename type_idx> __global__void gatherCustom(type_data* input, type_idx* index, type_data* gather_output, uint32_t in_width, uint32_t index_total_length) {
    // 计算计算索引偏移量
    int32_t out_row = blockIdx.x * blockDim.x + threadIdx.x;
    // 从index中取出需要处理的行索引
    uint32_t in_row = index[out_row];
    // 循环处理该行所有数据
    for (int32_t col = 0; col < in_width; col++) {
        int input_idx = in_row * in_width + col;
        int output_idx = out_row * in_width + col;
        gather_output[out_idx] = input[out_idx]; // 将输入数据拷贝到输出中
    }
} 
```

算子需要处理总共12288行数据，每行数据由核函数完成处理，因此需要12288个线程 来完成对所有数据的处理。在Host侧通过<<<...>>>调用核函数，同时设置启动48个线 程块、每个线程块包含256个线程，示例代码如下。 

```txt
int main(int argc, char* argv[])
{
    ...
    gather_custom<<48, 256, 0, stream>>(input_device, index_device, output_device, in_shape[1],
index_total_length);
    ...
} 
```

# 2.2.5 AI CPU 编程

AI CPU是位于Device侧ARM64架构的处理器，其具备与AI Core相同的内存访问能力， 可直接访问Device侧内存资源；也可以与Host侧的CPU一样，进行类似的数据计算， 通常作为AI Core的补充，主要承担非矩阵类、逻辑比较复杂的分支密集型计算。AI CPU的运行环境为基础的Linux环境，编程时可使用libc库，C++标准库，STL模板库 等。其硬件架构图如下所示： 


图 2-17 AI CPU 硬件架构图


![](images/a9c2d153cb29bae861c18318fbc4b2d09baf27579f1160fc5300e98a70cdacee.jpg)


本节介绍的AI CPU编程仅支持如下产品型号： 

Atlas 350 加速卡 

● Atlas A3 训练系列产品/Atlas A3 推理系列产品 

● Atlas A2 训练系列产品/Atlas A2 推理系列产品 

# AI CPU 核函数定义

在进行AI CPU编程时，与AI Core类似，同样需要定义设备侧函数入口（即核函数）， 该函数必须通过__aicpu__标识符进行声明，并且需与__global__标识符联合使用以表 明其只能被Host侧调用。AI CPU的Device侧实现文件需要以.aicpu为后缀（或者在编 译时增加-x aicpu选项）。该实现文件中包括上面介绍的核函数以及AI CPU普通函数定 义，AI CPU普通函数无需添加执行空间标识符。 

如下是一个AI CPU“Hello World”程序的示例，hello_world.aicpu文件内容如下： 

```cpp
//调用printf接口需要包含的头文件  
#include"aicpu_api.h"  
__global__aicpu_uint32_t hello_world(void\*args)  
{  
    AscendC::printf("Hello World!!!\n");  
    return 0;  
} 
```

# 说明

编程时需要遵循如下规范： 

● __aicpu__ __global__函数不能是void返回类型，并且入参只能是一个指针。 

● __aicpu__ __global__函数不能是类的成员函数，也不能存在于匿名空间下。 

● 尽管AI CPU的Kernel函数有返回值，但该返回值仅用于Runtime组件报告运行状态，开发者 无需编写返回逻辑，也无法使用该返回值。因此，对于用户而言，AI CPU Kernel函数等同于 void类型，不能作为右值使用。 

# AI CPU 核函数调用

AI CPU核函数的调用需要在.asc文件中进行，和AI Core的算子调用类似，同样使用 <<<>>>语法。 

hello_world<<<numBlocks, nullptr, stream>>>(&args, sizeof(KernelArgs)); 

numBlocks：AI CPU Device侧暂不支持分核逻辑，因此Host侧调用多核无实际意 义。建议设置为1。 

● l2ctrl：保留参数，当前固定为nullptr，开发者无需关注。 

stream：类型为aclrtStream，stream用于维护一些异步操作的执行顺序，确保按 照应用程序中的代码调用顺序在Device上执行。stream创建等管理接口请参考 “应用开发接口 $>$ AscendCL API（C&C++） > 运行时管理 > Stream管理”章 节。 

# 说明

在编写调用代码时需要遵循如下规范： 

● __aicpu__ __global__函数不能在.asc文件中进行定义，只能声明，且需要使用extern。 

Host侧调用__global__ __aicpu__函数时必须使用<<<>>>异构调用语法，输入的函数入参在 入参指针的基础上需要输入从指针中读取的数据大小。 

● 在Host侧使用内核调用符<<<...>>>调用AI Core与AI CPU算子时不能使用同一条stream。 

加载和运行算子时，需要使用Runtime API，完成运行时管理和配置，详细内容请参考 2.3.4 算子运行。AI CPU算子的编译请参考2.3.3 AI CPU算子编译。 

# AI CPU 模板核函数

若需要使用模板核函数，则需要在.aicpu文件中给出模板核函数的实例化声明，参考如 下： 

```cpp
template<typename T, int BUFF_SIZE> global __aicpu uint32_t hello_world(void *args) {
    AscendC::printf("Hello World!!!\n");
    AscendC::printf("buffer_size is %d\n", BUFF_SIZE);
    return 0;
} template __global __aicpu uint32_t hello_world<KernelArgs, 4096>(void *args); 
```

并在.asc文件中新增模板核函数实例化的extern声明： 

```c
template<typename T, int BUFF_SIZE> extern __global__aicpu_uint32_t hello_world(void *args); template extern __global__aicpu uint32_t hello_world <KernelArgs, 4096>(void *args); 
```

# 更多进阶用法

# 说明

更多AI CPU API的使用方法请参考AI CPU API。