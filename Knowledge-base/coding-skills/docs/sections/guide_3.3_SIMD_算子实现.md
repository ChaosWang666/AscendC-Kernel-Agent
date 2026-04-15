<!-- Source: 算子开发指南.md lines 13647-18662 | Section: 3.3 SIMD 算子实现 -->

# 3.3 SIMD 算子实现

# 3.3.1 概述

Ascend C的算子实现主要包含两个部分： 

Host侧Tiling实现 

由于NPU中AI Core内部存储无法完全容纳算子输入输出的所有数据，需要每次搬 运一部分输入数据进行计算然后搬出，再搬运下一部分输入数据进行计算，这个 过程就称之为Tiling。切分数据的算法称为Tiling算法或者Tiling策略。根据算子的 shape等信息来确定数据切分算法相关参数（比如每次搬运的块大小，以及总共循 

环多少次）的计算程序，称之为Tiling实现，也叫Tiling函数（Tiling 

Function）。由于Tiling实现中完成的均为标量计算，AI Core并不擅长，所以我们 将其独立出来放在Host侧CPU上执行。 

Device侧Kernel实现 

Kernel实现即算子核函数实现，在Kernel函数内部通过解析Host侧传入的Tiling结 构体获取Tiling信息，根据Tiling信息控制数据搬入搬出Local Memory的流程；通 过调用计算、数据搬运、内存管理、任务同步API，实现算子逻辑。其核心逻辑基 本上都为计算密集型任务，需要在NPU上执行。 

本章介绍矢量编程、矩阵编程、融合算子编程三种典型场景下的算子Tiling、Kernel实 现，是对上文中典型编程范式的具体应用，同时也介绍了编程的更多细节、API的使用 方法等。 

# 3.3.2 矢量编程

# 3.3.2.1 概述

本节将以Add算子为例，带您快速构建Ascend C矢量算子程序，并学习矢量算子开发 的典型场景以及处理方式。涉及的场景包括： 

基础矢量算子：开发一个简单的Add矢量算子。 

TBuf的使用：在算子计算过程中使用临时空间存储运算的中间结果。 

多核Tiling：算子在AI处理器的多个核上运行，所有核的计算数据量相等且32字 节对齐。 

尾块Tiling：算子在AI处理器的多个核上运行，所有核的计算数据量相等，每个核 上除最后一个数据块（尾块）外，其余数据块的数据量相等，每个核都需要处理 尾块数据的计算。 

尾核Tiling：算子在AI处理器的多个核上运行，数据无法平均分配到每个核。将所 有核分为多个整核和多个尾核，整核的计算数据量相等，尾核的计算数据量相 等。 

尾核&尾块：算子在AI处理器的多个核上运行，数据无法平均分配到每个核，同时 每个核内的数据无法均分，除最后一个数据块（尾块）外，其余数据块的数据量 相等，每个核都需要单独处理尾块数据的计算。 

DoubleBuffer场景：使能double buffer，算子中的多条流水并行执行。 

Broadcast场景：算子中两个输入的shape（形状）不相等，需要将一个输入的 shape进行Broadcast（广播）后，再执行计算。 

非对齐场景：更多数据非32字节对齐场景的处理方案。 

# 须知

进行数据搬运和Vector计算时，对于搬运的数据长度和操作数的起始地址有如下的对 齐要求： 

● 使用DataCopy接口进行数据搬运，搬运的数据长度和操作数的起始地址（Unified Buffer上）必须保证32字节对齐。 

● 通常情况下，进行Vector计算时，操作数的起始地址必须保证32字节对齐，执行计 算的基本单位为32字节。 

# 3.3.2.2 基础矢量算子

基于Ascend C方式实现基础矢量算子核函数的流程如下图所示。 


图3-3 矢量算子核函数实现流程


![](images/4cd3edb1349e42e053cfd8dd3075b9d255dfc5f6210021096b105c3e45edeeb3.jpg)


算子分析：分析算子的数学表达式、输入、输出以及计算逻辑的实现，明确需要 调用的Ascend C接口。 

核函数定义：定义Ascend C算子入口函数。 

根据矢量编程范式实现算子类：完成核函数的内部实现，包括3个基本任务： CopyIn，Compute，CopyOut。 

下文以输入为half数据类型且shape的最后一维为32Bytes对齐、在单核上运行的、一 次完成计算的Add算子为例，对上述步骤进行详细介绍。本样例中介绍的算子完整代 码请参见基础Add算子样例。 

# 算子分析

算子分析具体步骤如下： 

步骤1 明确算子的数学表达式及计算逻辑。 

Add算子的数学表达式为： 

$$
z = x + y
$$

计算逻辑是：Ascend C提供的矢量计算接口的操作元素都为LocalTensor，输入数据需 要先从外部存储（Global Memory）搬运进片上存储（Unified Buffer），然后使用计 算接口完成两个输入参数相加，得到最终结果，再搬出到外部存储上。Ascend C Add 算子的计算逻辑如下图所示。 


图 3-4 算子计算逻辑


![](images/db9e5e30b478d794ad335aff3dcf35fcb051ff2e0dbe23ed3b2dd5d8a23a1993.jpg)


步骤2 明确输入和输出。 

● Add算子有两个输入：x与y；输出为z。 

本样例中算子的输入支持的数据类型为half（float16），算子输出的数据类型与 输入的数据类型相同。 

算子输入支持的shape为（1，2048），输出shape与输入shape相同。 

算子输入支持的format为：ND。 

步骤3 确定核函数名称和参数。 

您可以自定义核函数名称，本样例中核函数命名为vec_add_custom。 

根据对算子输入输出的分析，确定核函数有3个参数x，y，z；x，y为输入在 Global Memory上的内存地址，z为输出在Global Memory上的内存地址。 

步骤4 确定算子实现所需接口。 

实现涉及外部存储和内部存储间的数据搬运，查看Ascend C API参考中的数据搬 运接口，需要使用DataCopy来实现数据搬运。 

本样例只涉及矢量计算的加法操作，查看Ascend C API参考中的矢量计算接口， 初步分析可使用基础算术Add接口Add实现x+y。 

使用Queue队列管理计算中使用的Tensor数据结构，具体使用EnQue、DeQue等 接口。 

# ----结束

通过以上分析，得到Ascend C Add算子的设计规格如下： 

算子类型（OpType）：Add 

算子输入输出： 


表3-1 Add算子输入输出规格


<table><tr><td>name</td><td>shape</td><td>data type</td><td>format</td></tr><tr><td>x(输入)</td><td>(1, 2048)</td><td>half</td><td>ND</td></tr><tr><td>y(输入)</td><td>(1, 2048)</td><td>half</td><td>ND</td></tr><tr><td>z(输出)</td><td>(1, 2048)</td><td>half</td><td>ND</td></tr></table>

核函数名称：vec_add_custom 

使用的主要接口： 

DataCopy：数据搬移接口 

– Add：矢量基础算术接口 

EnQue、DeQue等接口：Queue队列管理接口 

算子实现文件名称：vector_add.asc 

# 核函数定义

根据核函数中介绍的规则进行核函数的定义。 

# 步骤1 函数原型定义

本样例中，函数名为vector_add_custom（核函数名称可自定义），根据算子分析中对 算子输入输出的分析，确定有3个参数x，y，z，其中x，y为输入内存，z为输出内存。 根据核函数的规则介绍，函数原型定义如下所示：使用__global__函数类型限定符标识 它是一个核函数，可以被<<<>>>调用；使用__vector__函数类型限定符标识该核函数 在设备端aicore的Vector Core上执行；为方便起见，统一使用GM_ADDR宏修饰入 参，GM_ADDR宏定义请参考核函数。 

```txt
global __vector__ void vector_add_custom(GM_ADDR x, GM_ADDR y, GM_ADDR z) { } 
```

# 步骤2 调用算子类的Init和Process函数。

算子类的Init函数，完成内存初始化相关工作，Process函数完成算子实现的核心逻 辑，具体介绍参见算子类实现。 

```txt
__global__ __vector__ void vector_add_custom(GM_ADDR x, GM_ADDR y, GM_ADDR z) {
    AscendC::TPipe pipe;
    KernelAdd op;
    op.Initial(x, y, z, &pipe);
    op.Process();
} 
```

步骤3 根据核函数定义和调用章节，调用核函数时，除了需要传入参数x，y，z，还需要传入 numBlocks（核函数执行的核数），nullptr（保留参数，设置为nullptr），stream （应用程序中维护异步操作执行顺序的stream）来规定核函数的执行配置。 

```txt
vector_add_custom<<numBlocks, nullptr, stream>>>(xDevice, yDevice, zDevice); 
```

----结束 

# 算子类实现

根据上一节介绍，核函数中会调用算子类的Init和Process函数，本节具体讲解如何基 于编程范式实现算子类。 

根据矢量编程范式对Add算子的实现流程进行设计的思路如下，矢量编程范式请参考 矢量编程范式，设计完成后得到的Add算子实现流程图参见图3 Add算子实现流程： 

Add算子的实现流程分为3个基本任务：CopyIn，Compute，CopyOut。CopyIn任 务负责将Global Memory上的输入Tensor xGm和yGm搬运至Local Memory，分 别存储在xLocal，yLocal，Compute任务负责对xLocal，yLocal执行加法操作，计 算结果存储在zLocal中，CopyOut任务负责将输出数据从zLocal搬运至Global Memory上的输出Tensor zGm中。 

CopyIn，Compute任务间通过VECIN队列inQueueX，inQueueY进行同步， Compute，CopyOut任务间通过VECOUT队列outQueueZ进行同步。 

任务间交互使用到的内存、临时变量的内存统一使用Pipe内存管理对象进行管 理。 


图 3-5 Add 算子实现流程


![](images/eae5052ba896e3439c10dcceb73fb4fea388962fe0557d4d5a3d47ce69252e87.jpg)


算子类中主要实现上述流程，包含对外开放的初始化Init函数和核心处理函数 Process，Process函数中会对上图中的三个基本任务进行调用；同时包括一些算子实现 中会用到的私有成员，比如上图中的GlobalTensor（xGm、yGm、zGm）和VECIN、 VECOUT队列等。KernelAdd算子类具体成员如下： 

```cpp
class KernelAdd {
public:
    __aicore__inline KernelAdd()
} //初始化函数，完成内存初始化相关操作
    __aicore__inline void Init(GM_ADDR x, GM_ADDR y, GM_ADDR z, AscendC::TPipe* pipeline)
//核心处理函数，实现算子逻辑，调用私有成员函数CopyIn、Compute、CopyOut完成矢量算子的三级流水操作
    __aicore__inline void Process()
}
private:
    //搬入函数，完成CopyIn阶段的处理，被核心Process函数调用
    __aicore__inline void CopyIn()
} //计算函数，完成Compute阶段的处理，被核心Process函数调用
    __aicore__inline void Compute()
} //搬出函数，完成CopyOut阶段的处理，被核心Process函数调用
    __aicore__inline void CopyOut()
}
private:
    AscendC::TPipe* pipe; // Pipe内存管理对象
    AscendC::TQue<TPosition::VECIN, 1> inQueueX; //输入数据Queue队列管理对象，TPosition为VECIN
    AscendC::TQue<TPosition::VECIN, 1> inQueueY; //输入数据Queue队列管理对象，TPosition为VECIN
    AscendC::TQue<TPosition::VECOUT, 1> outQueueZ; //输出数据Queue队列管理对象，TPosition为VECOUT
    AscendC::GlobalTensor<half> xGm; //管理输入输出Global Memory内存地址的对象，其中xGm, yGm为输入，zGm为输出
    AscendC::GlobalTensor<half> yGm; 
```

```txt
AscendC::GlobalTensor<half> zGm; }; 
```

初始化函数主要完成以下内容： 

设置输入输出Global Tensor的Global Memory内存地址。 本样例中的分配方案是：数据整体长度TOTAL_LENGTH为1 * 2048，使用 GlobalTensor类的SetGlobalBuffer接口设定该核上Global Memory的起始地址以 及长度。 

```javascript
xGm.SetGlobalBuffer((gm half*)x, TOTAL_LENGTH); 
```

通过Pipe内存管理对象为输入输出Queue分配内存。 比如，为输入x的Queue分配内存，可以通过如下代码段实现： 

```txt
pipe->InitBuffer(inQueueX, 1, TOTAL_LENGTH * sizeof(half)) 
```


具体的初始化函数代码如下：


```txt
constexpr int32_t TOTAL_LENGTH = 1 * 2048; // 数据总长  
__aicore__ inline void Init(GM_ADDR x, GM_ADDR y, GM_ADDR z, AscendC::TPipe* pipeline)  
{  
    pipe = pipeline;  
    // 设置Global Memory的起始地址以及长度  
xGm.SetGlobalBuffer((gm__half*)x, TOTAL_LENGTH);  
yGm.SetGlobalBuffer((gm__half*)y, TOTAL_LENGTH);  
zGm.SetGlobalBuffer((gm__half*)z, TOTAL_LENGTH);  
// 通过Pipe内存管理对象为输入输出Queue分配内存  
pipe->InitBuffer(inQueueX, 1, TOTAL_LENGTH * sizeof(half));  
pipe->InitBuffer(inQueueY, 1, TOTAL_LENGTH * sizeof(half));  
pipe->InitBuffer(outQueueZ, 1, TOTAL_LENGTH * sizeof(half));  
} 
```

基于矢量编程范式，将核函数的实现分为3个基本任务：CopyIn，Compute， CopyOut。Process函数中通过如下方式调用这三个函数。 

```txt
aicore__inline void Process()
{
    Copyln();
    Compute();
    CopyOut();
} 
```

根据编程范式上面的算法分析，将整个计算拆分成三个Stage，用户单独编写每个 Stage的代码，三阶段流程示意图参见图3-5，具体流程如下： 

步骤1 Stage1：CopyIn函数实现。 

1. 使用DataCopy接口将GlobalTensor数据拷贝到LocalTensor。 

2. 使用EnQue将LocalTensor放入VECIN的Queue中。 

```cpp
aicore__inline void Copyln()   
{ //从Que中为LocalTensor分配内存 AscendC::LocalTensor<half> xLocal = inQueueX AllocTensor<half>(); AscendC::LocalTensor<half> yLocal = inQueueY AllocTensor<half>(); //将GlobalTensor数据拷贝到LocalTensor AscendC::DataCopy(xLocal, xGm, TOTAL_LENGTH); AscendC::DataCopy(yLocal, yGm, TOTAL_LENGTH); //LocalTensor放入VECIN的Queue中 inQueueX.EnQue(xLocal); inQueueY.EnQue(yLocal);   
} 
```

步骤2 Stage2：Compute函数实现。 

1. 使用DeQue从VECIN中取出LocalTensor。 

2. 使用Ascend C接口Add完成矢量计算。 

3. 使用EnQue将计算结果LocalTensor放入到VECOUT的Queue中。 

4. 使用FreeTensor释放不再使用的LocalTensor。 

```txt
aicore__inline void Compute()   
{ //将Input从VECIN的Queue中取出 AscendC::LocalTensor<half> xLocal = inQueueX.DeQue<half>(); AscendC::LocalTensor<half> yLocal = inQueueY.DeQue<half>(); AscendC::LocalTensor<half> zLocal = outQueueZ AllocTensor<half>(); //调用Add算子进行计算 AscendC::Add(zLocal,xLocal,yLocal,TOTAL_LENGTH); //将计算结果LocalTensor放入到VECOUT的Queue中 outQueueZ.EnQue<half>(zLocal); //释放LocalTensor inQueueX.FreeTensor(xLocal); inQueueY.FreeTensor(yLocal);   
} 
```

步骤3 Stage3：CopyOut函数实现。 

1. 使用DeQue接口从VECOUT的Queue中取出LocalTensor。 

2. 使用DataCopy接口将LocalTensor拷贝到GlobalTensor上。 

3. 使用FreeTensor将不再使用的LocalTensor进行回收。 

__aicore__inline void CopyOut()   
{ //将计算结果从VECOUT的Queue中取出 AscendC::LocalTensor<half>zLocal $=$ outQueueZ.DeQue<half>(); //将计算结果从LocalTensor数据拷贝到GlobalTensor AscendC::DataCopy(zGm,zLocal,TOTAL_LENGTH); //释放LocalTensor outQueueZ.FreeTensor(zLocal);   
} 

----结束 

# 3.3.2.3 TBuf 的使用

在大多数算子开发时，核函数计算过程需要使用临时内存来存储运算的中间结果，这 些中间结果以临时变量表示，临时变量占用的内存可以使用TBuf数据结构来管理，具 体介绍请参考TBuf。下文将以输入的数据类型为bfloat16_t、在单核上运行的Add算子 为例，介绍TBuf的使用方式。本样例中介绍的算子完整代码请参见使用临时内存的 Add算子样例。 

在Atlas A2 训练系列产品/Atlas 800I A2 推理产品上，Add接口不支持对数据类型 bfloat16_t的源操作数进行求和计算。因此，需要先将算子输入的数据类型转换成Add 接口支持的数据类型，再进行计算。为保证计算精度，调用Cast接口将输入bfloat16_t 类型转换为float类型，再进行Add计算，并在计算结束后将float类型转换回bfloat16_t 类型。 

通过以上分析，得到Ascend C Add算子的设计规格如下： 

算子类型（OpType）：Add 

算子输入输出： 


表 3-2 Add 算子输入输出规格


<table><tr><td>name</td><td>shape</td><td>data type</td><td>format</td></tr><tr><td>x(输入)</td><td>(1, 2048)</td><td>float16_t</td><td>ND</td></tr><tr><td>y(输入)</td><td>(1, 2048)</td><td>float16_t</td><td>ND</td></tr><tr><td>z(输出)</td><td>(1, 2048)</td><td>float16_t</td><td>ND</td></tr></table>

核函数名称：tmp_buffer_custom 

使用的主要接口： 

DataCopy：数据搬移接口 

Cast：矢量精度转换接口 

– Add：矢量基础算术接口 

EnQue、DeQue等接口：Queue队列管理接口 

算子实现文件名称：tmp_buffer.asc 

# 算子类实现

该样例的CopyIn，CopyOut任务与基础矢量算子相同，Compute任务的具体流程如下 图所示。 


图 3-6 输入为 bfloat16_t 类型的 Add 计算流程


![](images/46ac47f6cc94cbd0a506e90edb814cd3e5944fe96925c4a722edd6ceae042a48.jpg)


在Compute任务中，表示Cast转换结果、Add计算结果的临时变量均需要使用临时内 存存储。与基础矢量算子实现的KernelAdd算子类相比，本样例新增两个TBuf类型的 成员变量tmpBuf0、tmpBuf1，用于管理计算过程中使用的临时内存，代码如下。 

```cpp
class KernelAdd {
public:
    __aicore__ inline KernelAdd() {}
    __aicore__ inline void Init(GM_ADDR x, GM_ADDR y, GM_ADDR z, AscendC::TPipe* pipeline) {}
    __aicore__ inline void Process()
}
private:
    __aicore__ inline void Copyln()
    __aicore__ inline void Compute()
    __aicore__ inline void CopyOut()
}
private:
    AscendC::TPipe* pipe;
    AscendC::TQue<TPosition::VECIN, 1> inQueueX;
    AscendC::TQue<TPosition::VECIN, 1> inQueueY;
    AscendC::TQue<TPosition::VECOUT, 1> outQueueZ;
    AscendC::TBuf<TPosition::VECCALC> tmpBuf0;
    AscendC::TBuf<TPosition::VECCALC> tmpBuf1;
    AscendC::GlobalTensor<flatfloat16_t> xGm; 
```

AscendC::GlobalTensor<bfloat16_t> yGm; AscendC::GlobalTensor<bfloat16_t> zGm;   
};   
初始化函数阶段除原有步骤外，需要调用InitBuffer接口为TBuf变量分配内存，具体的 初始化函数代码如下： _aicore__inline void Init(GM_ADDR x, GM_ADDR y, GM_ADDR z, AscendC::TPipe\*pipeline) { pipe $=$ pipeln; xGm.SetGlobalBuffer((gm_bfloat16_t) $x$ , TOTAL_LENGTH); yGm.SetGlobalBuffer((gm_bfloat16_t) $y$ , TOTAL_LENGTH); zGm.SetGlobalBuffer((gm_bfloat16_t) $z$ , TOTAL_LENGTH); pipe->InitBuffer(inQueueX, 1, TOTAL_LENGTH \* sizeof(bfloat16_t)); pipe->InitBuffer(inQueueY, 1, TOTAL_LENGTH \* sizeof(bfloat16_t)); pipe->InitBuffer(outQueueZ, 1, TOTAL_LENGTH \* sizeof(bfloat16_t)); pipe->InitBuffer(tmpBuf0, TOTAL_LENGTH \* sizeof(float)); pipe->InitBuffer(tmpBuf1, TOTAL_LENGTH \* sizeof(float));   
} 

基于矢量编程范式，核函数需要实现3个基本任务：CopyIn，Compute，CopyOut。 与基础矢量算子实现相同，Process函数按顺序调用CopyIn函数，Compute函数， CopyOut函数。其中，CopyIn函数，CopyOut函数与基础矢量算子的CopyIn函数、基 础矢量算子的CopyOut函数的实现没有差异，此处不过多赘述。Compute函数的实现 步骤如下： 

1. 使用DeQue从VECIN的Queue中取出LocalTensor。 

2. 使用TBuf.Get从TBuf上获取全部长度的Tensor作为临时内存。 

3. 使用Cast接口将LocalTensor转换为float类型，并存入临时内存。 

4. 使用Add接口完成矢量计算，将计算结果存入临时内存。 

5. 使用Cast接口将临时内存中的计算结果转换为bfloat16_t类型。 

6. 使用EnQue将bfloat16_t类型的结果LocalTensor放入VECOUT的Queue中。 

7. 使用FreeTensor释放不再使用的LocalTensor。 

aicore__inline void Compute()   
{ AscendC::LocalTensor<bfloat16_t> xLocal $=$ inQueueX.DeQue<bfloat16_t $\rangle$ ); AscendC::LocalTensor<bfloat16_t> yLocal $=$ inQueueY.DeQue<bfloat16_t $\rangle$ ); AscendC::LocalTensor<bfloat16_t> zLocal $=$ outQueueZ AllocTensor<bfloat16_t $\rangle$ ); AscendC::LocalTensor<float> tmpTensor0 $=$ tmpBuf0.Get<float>(); AscendC::LocalTensor<float> tmpTensor1 $=$ tmpBuf1.Get<float>(); AscendC::Cast(tmpTensor0,xLocal,AscendC::RoundMode::CAST_NONE,TOTAL_LENGTH); AscendC::Cast(tmpTensor1,yLocal,AscendC::RoundMode::CAST_NONE,TOTAL_LENGTH); AscendC::Add(tmpTensor0,tpTmpensor0,tpTmpensor1,TOTAL_LENGTH); AscendC::Cast(zLocal,tpTmpensor0,AscendC::RoundMode::CAST_RINT,TOTAL_LENGTH); outQueueZ.EnQue<bfloat16_t>(zLocal); inQueueX.FreeTensor(xLocal); inQueueY.FreeTensor(yLocal); 

# 3.3.2.4 多核&Tiling 切分

# 3.3.2.4.1 概述

Ascend C核函数是运行在一个核上的处理函数，上述介绍的基础矢量算子与TBuf的使 用样例均为在单核上运行的算子，不涉及Host侧Tiling实现。矢量算子实现的组成如下 图所示。 

为了提高算子的执行效率，通常在算子中实现多核并行计算，即对输入数据进行切 分，并将不同的数据块分配到不同的核上处理。此外，由于单个核上内部存储Local Memory大小有限，存在无法一次完整地容纳算子的输入和输出数据的场景，因此需 要每次搬运一部分输入进行计算然后搬出，再搬运下一部分输入进行计算，直到获得 最终的完整结果，这个数据切分、分块计算的过程称之为Tiling。切分数据的算法称为 Tiling算法或者Tiling策略。根据算子的shape等信息来确定数据切分算法相关参数（比 如每次搬运的块大小，以及总共循环多少次）的计算程序，称之为Tiling实现，也叫 Tiling函数（Tiling Function）。由于Tiling实现中完成的均为标量计算，AI Core并不 擅长，所以我们将其独立出来放在Host侧CPU上执行。核函数内部通过解析Host侧传 入的Tiling结构体获取Tiling信息，根据Tiling信息控制数据搬入、搬出Local Memory 的流程；通过调用计算、数据搬运、内存管理、任务同步API，实现算子逻辑。 

图 3-7 算子实现组成 

Kernel侧算子实现 

Host侧Tiling实现 （可选） 

由于硬件限制，在对输入数据进行数据切分时应遵循以下几个原则： 

1. 由于AI Core中Unified Buffer上的物理限制，要求Unified Buffer上的数据存储空 间必须保持32字节对齐。 

输入数据不满足32字节对齐时，需要取输入数据长度向上对齐到32字节的长 度作为输入数据总长度。 

进行Tiling有关计算时，以32字节为最小单位进行计算。 

2. 尽可能最大利用Unified Buffer空间。 

AI Core与外部存储交互时会产生性能开销，频繁的进行数据搬运会导致性能瓶 颈，因此应尽可能充分利用Unified Buffer空间，减少从Global Memory上搬运数 据的次数。 

3. AI处理器包含多个AI Core，应该充分均衡利用多核计算能力，将计算均衡分配到 多个AI Core上。 

本章将基于以上原则对几种典型场景进行说明，完整代码请参见多核Add算子样例。 


图 3-8 多核及 Tiling 示意图


![](images/c32930f4bb90e1f701fba884526e9658b9e34191e26c131ae6ba34e3e407cb29.jpg)


数据切分示意如上图所示，将长度为TOTAL_LENGTH的算子输入分配到多个核上进行 计算，每个核上计算的数据长度为BLOCK_LENGTH。对于每个核的计算数据，基于 Local Memory的大小进一步切分，切分数据块的个数为TILE_NUM，得到的每个数据 块的长度为TILE_LENGTH。 

根据每个核计算的数据量是否相同、核内每个数据块的数据量是否相同，切分策略可 能会存在以下几种场景： 

1. 核间均分，核内均分：每个核处理的数据量相同，核内每个数据块的数据量相 同。在此场景中，通过多核Tiling将数据均匀分配到各个核上执行，每个核上每次 计算的数据长度相同。 

2. 核间均分，核内不均分：每个核处理的数据量相同，核内各数据块的数据量不完 全相同。此场景基于多核Tiling，核内数据不能切分为多个数据量相同且32字节对 齐的数据块，需要通过尾块Tiling处理尾块数据的计算。 

3. 核间不均分，核内均分：每个核处理的数据量不同，核内每个数据块的数据量相 同。在此场景中，通过尾核Tiling的处理解决数据无法在各核间均匀分配的问题。 

4. 核间不均分，核内不均分：每个核处理的数据量不同，核内各数据块的数据量不 完全相同。该场景下需要同时考虑尾核&尾块，处理多核间及核内数据的合理切 分。 

# 3.3.2.4.2 多核 Tiling

基于Ascend C方式实现带有Tiling的算子的开发流程如下图所示。 


图 3-9 算子开发流程


![](images/80dbf53cb37f5db92144fb70ad45e8ceef4ae0595989eca14dc4757d0be8efd0.jpg)


# 算子分析

本样例为输入数据在核间均分、核内均分场景。本样例的Tiling策略为：数据整体长度 TOTAL_LENGTH为8 * 2048，数据平均分配到8个核上运行，每个核上计算的数据长度 BLOCK_LENGTH为2048，将单核上的数据切分成16块（此处切分成16块仅用来作为 Tiling的样例，并不代表性能最佳，仅供参考），每块数据的长度TILE_LENGTH为 128。数据切分示意如下图所示： 


图 3-10 数据切分示意图


![](images/ded595acddab9640edfeccd30bfea0631e55b0907ca3f0900c08174cf7c71f27.jpg)


通过以上分析，得到Ascend C Add算子的设计规格如下： 

算子类型（OpType）：Add 

算子输入输出： 


表 3-3 Add 算子输入输出规格


<table><tr><td>name</td><td>shape</td><td>data type</td><td>format</td></tr><tr><td>x(输入)</td><td>(8, 2048)</td><td>half</td><td>ND</td></tr><tr><td>y(输入)</td><td>(8, 2048)</td><td>half</td><td>ND</td></tr><tr><td>z(输出)</td><td>(8, 2048)</td><td>half</td><td>ND</td></tr></table>

核函数名称：tiling_strategy_custom 

使用的主要接口： 

DataCopy：数据搬移接口 

Add：矢量基础算术接口 

EnQue、DeQue等接口：Queue队列管理接口 

算子实现文件名称：tiling_strategy.asc 

# Tiling 实现

前述场景中算子的输入和输出均为固定shape，然而在实际的算子开发场景中，这些信 息是支持动态变化的，场景会更加灵活和复杂。动态shape场景下，输入的shape是未 知的。一些与输入shape相关的变量（比如每次搬运的块大小等），需要通过Tiling计 算出来，然后传递到kernel侧，kernel侧使用该参数进行后续的计算。 

具体实现方式为：分析设计Tiling参数、定义Tiling结构体，在Host侧通过上下文获取 输入输出的shape信息，根据shape信息，计算Tiling参数并设置到对应的Tiling结构体 中；通过核函数入口参数将Tiling信息传入核函数，在核函数内通过解析Tiling结构 体，获取并使用相关参数来实现核函数内部逻辑，详细介绍请参考Host侧tiling实现。 本节将以上述分析中的切分策略为例，说明如何实现Tiling。 

基于本节的切分策略，Tiling需要定义如下参数： 

blockLength：每个核的计算数据长度； 

tileNum：每个核需要计算的数据块个数； 

tileLength：每个核内每个数据块的长度。 

根据确定的Tiling参数，使用 ${ \mathsf { C } } { + } { + }$ 语法定义TilingData结构体，代码如下。 

```txt
struct AddCustomTilingData {
    uint32_t blockLength;
    uint32_t tileNum;
    uint32_t tileLength;
    ...
} 
```

接下来完成Tiling参数的计算。由于每个核内数据被切分为16块，根据使用的核数和核 内切分数，计算Tiling参数，并写入到Tiling结构体内。代码示例如下： 

```c
constexpr int32_t NUM_BLOCKS = 8; // 使用的核数
constexpr int32_t TILE_NUM = 16; // 核内切分数量
void GenerateTilingData( uint8_t* t* tilingBuf, uint32_t numBlocks) {
    uint32_t totalLength;
    // 此处省略如何获取数据总长TOTAL_LENGTH，可以根据具体情况实现。本章节仅介绍Tiling相关内容。
    AddCustomTilingData* tiling = reinterpret_cast<AddCustomTilingData *>(tilingBuf);
    uint32_t blockLength = TOTAL_LENGTH / numBlocks;
    uint32_t tileNum = TILE_NUM;
    uint32_t tileLength = blockLength / tileNum;
    tiling->blockLength = blockLength;
    tiling->tileNum = tileNum;
    tiling->tileLength = tileLength;
} 
```

最后，在Host侧调用程序中，调用上述Tiling参数计算函数，计算出相关参数，然后传 递到Kernel侧核函数。 

```c
constexpr int32_t NUM_BLOCKS = 8;
...
uint8_t *tiling = nullptr;
size_t tilingSize = sizeof(AddCustomTilingData);
GenerateTilingData(tiling, NUM_BLOCKS); // 调用tiling参数计算函数
...
tiling_strategy(custom<<NUM_BLOCKS, nullptr, stream>>>(xDevice, yDevice, zDevice, *reinterpret_cast<AddCustomTilingData>(tiling)); 
```

# 算子类实现

Kernel侧算子实现仍遵循矢量算子核函数实现流程，接下来重点介绍本场景中算子类 实现的不同点。 

设置输入输出Global Tensor的Global Memory内存地址。 

由于本样例中将数据分配到了多个核上进行处理，每个核处理不同的数据，因此 不同核要处理的数据在Global Memory上的地址不同，在初始化函数Init中，需要 获取单核所需处理的输入输出在Global Memory上的内存偏移地址，并将该偏移 地址设置到GlobalTensor中。 

以获取输入x在Global Memory上的内存偏移地址为例，数据整体长度 TOTAL_LENGTH为8 * 2048，平均分配到8个核上运行，每个核上处理的数据长度 blockLength为2048，调用GetBlockIdx接口获取当前核的index，x + blockLength * GetBlockIdx()即为单核处理程序中x在Global Memory上的内存偏 移地址，获取偏移地址后，使用GlobalTensor类的SetGlobalBuffer接口设定该核 

上Global Memory的起始地址以及长度，具体示意图请参考图3-11。代码如下所 示： 

```txt
xGm.SetGlobalBuffer(_gm__ half *)x + this->blockLength * AscendC::GetBlockIdx(), this->blockLength); 
```


图 3-11 多核并行处理示意图


![](images/cdfa35a7b9da7bfa526caa7f958ece1a627f82259b95ffba8dda01e661b5af4a.jpg)


通过Pipe内存管理对象为输入输出Queue分配内存。 

对于单核上的处理数据，可以进行数据切块（Tiling），在本示例中，仅作为参 考，将单核上的数据（2048个数）切分成16块（并不意味着16块就是性能最 优），每块tileLength（128）个数据。数据切分示意图如图3-12所示。 


图 3-12 单核数据切分示意图


![](images/d2910973a3f4af88458711a312d00add6e218adb9b15839f71fb68b7753895c7.jpg)


与基础矢量算子相比，在通过Pipe内存管理对象为输入输出Queue分配内存时， 需使用单核内每个数据块的长度tileLength作为分配内存的长度。比如，为输入x 的Queue分配内存，可以通过如下代码段实现，Pipe为inQueueX分配了一块大小 为tileLength * sizeof(half)个字节的内存块，每个内存块能容纳tileLength （128）个half类型数据。 

```txt
pipe->InitBuffer(inQueueX, 1, this->tileLength * sizeof(half)) 
```


具体的初始化函数代码如下：


__aicore__inline void Init(GM_ADDR x, GM_ADDR y, GM_ADDR z, AddCustomTilingData tiling, AscendC::TPipe* pipeln)   
{ pipe $=$ pipeln; this->blockLength $=$ tiling.blockLength; this->tileNum $=$ tilingtileNum; this->tileLength $=$ tilingtileLength; //计算每个核上的地址偏移 $\mathrm{xGm.SetGlobalBuffer((\_ gm\_ half*)x + \text{this->blockLength} *\text{AscendC::GetBlockIdx()}$ , this->blockLength); yGm.SetGlobalBuffer((\_ gm\_ half *)y $^+$ this->blockLength \* AscendC::GetBlockIdx(), this->blockLength); zGm.SetGlobalBuffer((\_ gm\_ half *)z $^+$ this->blockLength \* AscendC::GetBlockIdx(), this->blockLength); //pipeallocmemorytoqueue,theunitisBytes pipe->InitBuffer(inQueueX,1,this->tileLength\*sizeof(half)); pipe->InitBuffer(inQueueY,1,this->tileLength\*sizeof(half)); pipe->InitBuffer(outQueueZ,1,this->tileLength\*sizeof(half));   
} 

每个核需要对tileNum个数据块分别进行搬入、计算、搬出处理，因此Process函数内 将tileNum作为循环上限。 

__aicore__ inline void Process()   
{ int32_t loopCount $=$ this->tileNum; // tiling strategy, pipeline parallel for (int32_t i $= 0$ ; $\mathrm{i} <   \mathrm{loop}\mathrm{Count};\mathrm{i} + + )$ { CopyIn(i, this->tileLength); Compute(i, this->tileLength); CopyOut(i, this->tileLength); }   
1 

对应的，每个核内搬入、搬出每个数据块时，需定位到每个数据块所在Global Memory上的内存偏移地址，因此在CopyIn和CopyOut函数内部使用DataCopy接口 时，需增加每个数据块的地址偏移。Compute函数没有变化，与基础矢量算子相同。 


CopyIn函数实现代码如下：


```cpp
aicore__inline void Copyln(int32_t progress, uint32_t tileLength)  
{  
    // copy progress_th tile from global tensor to local tensor  
    AscendC::DataCopy(xLocal, xGm[progress * this->tileLength], tileLength);  
    AscendC::DataCopy(yLocal, yGm[progress * this->tileLength], tileLength);  
    ...  
} 
```


CopyOut函数实现代码如下：


```cpp
aicore__inline void CopyOut(int32_t progress, uint32_t tileLength)   
{ //copy progress_th tile from local tensor to global tensor AscendC::DataCopy(zGm[progress \* this->tileLength],zLocal,tileLength); 1 
```

# 3.3.2.4.3 尾块 Tiling

如下图中的示例，算子的输入shape为（1，2048），支持的数据类型为half类型，输 入数据可以对齐到一个datablock的大小（32字节），输入数据为2048 * 2 / 32 = 128 个datablock，因此可以平均分配到每个核上（假设使用8个核），每个核上处理256个 数，16个datablock。此时不需要进行尾块处理。 


图 3-13 shape 对齐场景


![](images/6b3a92915b6e812d9f067697f06d5ee732d377719444afe653cda4dc7624e45e.jpg)


针对一些shape，比如算子的输入shape为（1，1904），支持的数据类型为half类 型，输入数据可以对齐到一个datablock的大小（32字节），可以平均分配到每个核上 （假设使用8个核），每个核上处理238个数，238个数无法均分到datablock上，分满 14个datablock后，剩余14个数（28字节），多核切分后需要进行尾块处理。 

对于不同shape的输入进行数据切分时，可能会发生Tiling后的数据平均分配到多核 上，但每个核内的数据无法均分的情况。针对此种场景，在Tiling参数中增加变量 lastTileLength，用来表示最后一个分块，即尾块的大小。因此，在定义算子的Tiling 结构体时包含以下四个成员： 

blockLength：每个核上计算的数据长度； 

tileNum：每个核上切分的主块数据块的个数； 

tileLength：每个核上主块数据块的长度； 

lastTileLength：每个核上尾块的长度。 


图 3-14 多核 Tiling 尾块示意图


![](images/f66439b20c83eb4c4a40731668c5203f6c19e44eb947e7fd8d73a11ce38de0d6.jpg)


# Tiling 实现

算子的Tiling结构体定义如下： 

```c
struct AddCustomTilingData {
    uint32_t blockLength;
    uint32_t tileNum;
    uint32_t tileLength; 
```

```txt
uint32_t lastTileLength;   
}； 
```

Host侧Tiling实现的主要内容为计算以上四个成员变量。步骤如下： 

步骤1 判断数据总长度totalLength是否满足32字节对齐，如不满足，则计算totalLength向上 32字节对齐后的长度totalLengthAligned。 

```c
constexpr uint32_t BLOCK_SIZE = 32;
//为方便计算，这里根据数据类型定义变量alignNum作为对齐数
uint32_t alignNum = BLOCK_SIZE / dataBlockSize;
//totalLength为数据总量
totalLengthAligned = (totalLength % alignNum == 0U) ?
    static_cast<uint32_t>(totalLength):
        ((static_cast<uint32_t>(totalLength) + alignNum - 1) / alignNum) * alignNum; 
```

步骤2 判断totalLengthAligned是否能被使用的核数NumBlocks均分，如果可以，则计算每 个核上计算数据长度blockLength。 

```c
constexpr uint32_t NUM_BLOCKS = 8;  
constexpr uint32_t UB_BLOCK_NUM = 100; //此处为方便验证，使用UB_BLOCK_NUM作为Unified Buffer可用的Block数量，因此可得出可用UB空间的大小为UB_BLOCK_NUM * BLOCK_SIZE  
uint32_t blockLength, tileNum;  
if ((totalLengthAligned / alignNum) % NUM_BLOCKS == 0U) {  
    blockLength = totalLengthAligned / NUM_BLOCKS;  
} 
```

步骤3 计算tileNum。为了减少数据搬运开销，应尽量使用核内的Unified Buffer空间。基于 每个核上的计算量以及可用Unified Buffer空间的大小，计算tileNum。 

```javascript
tileNum = blockLength / (alignNum * UB_BLOCK_NUM); 
```

步骤4 根据计算出的tileNum，计算tileLength和lastTileLength。 

如果每个核的计算量能够被当前可用Unified Buffer空间均分，则按照无尾块场景处 理。 

```c
if(static_cast<uint32_t>(blockLength / alignNum) % UB_BLOCK_NUM == 0U){ //单核的计算量能被当前可用UB空间均分，仅有主块，无尾块tileLength = UB_BLOCK_NUM * alignNum;lastTileLength = 0U; 
```

反之，按照尾块场景处理，尾块长度为单核计算数据长度 - tileNum * tileLength。 

```c
if (tileNum == 0U) { // 单核需要计算的长度小于UB可用空间，按照仅有尾块处理 tileLength = 0U; lastTileLength = static_cast<uint32_t>(((blockLength + alignNum - 1) / alignNum) * alignNum); } else { // 同时有主块和尾块 tileLength = UB_BLOCK_NUM * alignNum; lastTileLength = static_cast<uint32_t>(blockLength - tileNum * tileLength); } 
```

# ----结束

Host侧Tiling实现的代码如下： 

```txt
constexpr uint32_t BLOCK_SIZE = 32;  
constexpr uint32_t NUM_BLOCKS = 8;  
constexpr uint32_t UB_BLOCK_NUM = 100; //此处为方便验证，使用UB_BLOCK_NUM作为UB可用的Block数量，因此可得出可用UB空间的大小为UB_BLOCK_NUM * BLOCK_SIZE  
...  
uint32_t alignNum = BLOCK_SIZE / dataBlockSize; //为方便计算，这里根据数据类型定义变量alignNum作为对齐数，dataTypeSize为运算数据的数据类型对应的字节数  
//totalLength为数据总量  
totalLengthAligned = (totalLength % alignNum == 0U)? 
```

```txt
static cast<uint32_t>(totalLength) : ((static cast<uint32_t>(totalLength) + alignNum - 1) / alignNum) * alignNum; uint32_t blockLength, tileNum; if((totalLengthAligned / alignNum) % NUM_BLOCKS == 0U) { blockLength = totalLengthAligned / NUM_BLOCKS; tileNum = blockLength / alignNum / UB_BLOCK_NUM; if (tileNum == 0) { //单核需要计算的长度小于UB可用空间，按照仅有尾块处理 tileLength = 0; lastTileLength = ((blockLength + alignNum - 1) / alignNum) * alignNum; } else if ((blockLength / alignNum) % UB_BLOCK_NUM == 0) { //单核的计算量能被当前可用UB空间均分，仅有主块，无尾块 tileLength = UB_BLOCK_NUM * alignNum; lastTileLength = 0; } else { //同时有主块和尾块 tileLength = UB_BLOCK_NUM * alignNum; lastTileLength = blockLength - tileNum * tileLength; } ... } 
```

(1，1904)形状的输入数据计算后，tiling结构体内各个变量的值如下： 

```c
struct AddCustomTilingData {
    uint32_t blockLength = 238; // 每个核计算238个half，8个核共计算1904个half
    uint32_t tileNum = 0; // 可用的UB空间足够，为仅有尾块的场景
    uint32_t tileLength = 0; // 没有主块，主块长度为0
    uint32_t lastTileLength = 240; // 238个half未32B对齐，对齐到240个half搬运
}; 
```

# 算子类实现

与多核Tiling相比，在Init函数中通过Pipe内存管理对象为输入输出Queue分配内存 时，取tileLength与lastTileLength中的最大值作为分配内存的长度。例如，当单核需 要计算的长度小于UB可用空间时，按照仅有尾块处理，此时tileLength为0，而 lastTileLength为数据块长度。因此，需要取两者中的较大值来分配内存。 

```cpp
uint32_t initBufferLength = AscendC::Std::max(this->tileLength, this->lastTileLength);  
pipe->InitBuffer(inQueueX, 1, this->initBufferLength * sizeof(dataType)); 
```

由于尾块长度为lastTileLength，与主块数据块的长度不同，因此在CopyIn函数、 Compute函数、CopyOut函数中传入本次循环待处理的数据块长度参数tileLength，即 待处理的主块或尾块的数据长度。 

Process函数实现代码如下： 

```c
aicore__inline void Process()   
{ //计算主块数据，对应数据块长度为tileLength for (uint32_t i = 0; i < this->tileNum; i++) { Copyln(i, this->tileLength); Compute(i, this->tileLength); CopyOut(i, this->tileLength); } //计算尾块数据，对应数据块长度为lastTileLength if (this->lastTileLength > 0) { Copyln(this->tileNum, this->lastTileLength); Compute(this->tileNum, this->lastTileLength); CopyOut(this->tileNum, this->lastTileLength); } 
```

```txt
Copyln函数实现代码如下： aicore__inline void Copyln(int32_t progress, uint32_t tileLength) { 
```

```cpp
AscendC::LocalTensor<T> xLocal = inQueueX AllocTensor<T>(); AscendC::LocalTensor<T> yLocal = inQueueY AllocTensor<T>(); AscendC::DataCopy(xLocal, xGm[progress * this->tileLength], tileLength); AscendC::DataCopy(yLocal, yGm[progress * this->tileLength], tileLength); inQueueX.EnQue(xLocal); inQueueY.EnQue(yLocal); } 
```


Compute函数实现代码如下：


aicore__inline void Compute(int32_t progress, uint32_t tileLength)   
{ AscendC::LocalTensor<T> xLocal $=$ inQueueX.DeQue<T>(); AscendC::LocalTensor<T> yLocal $=$ inQueueY.DeQue<T>(); AscendC::LocalTensor<T> zLocal $=$ outQueueZ AllocTensor<T>(); AscendC::Add(zLocal,xLocal,yLocal,tileLength); outQueueZ.EnQue<T>(zLocal); inQueueX.FreeTensor(xLocal); inQueueY.FreeTensor(yLocal); 


CopyOut函数实现代码如下：


```cpp
aicore__inline void CopyOut(int32_t progress, uint32_t tileLength)  
{  
    AscendC::LocalTensor<T> zLocal = outQueueZ.DeQue<T>();  
    AscendC::DataCopy(zGm[progress * this->tileLength], zLocal, tileLength);  
    outQueueZ.FreeTensor(zLocal);  
} 
```

# 3.3.2.4.4 尾核 Tiling

对于不同shape的输入进行数据切分时，可能会发生数据无法平均分配到多个核的情 况。例如当算子的输入shape为[1, 1999]，使用核数为8，数据类型为half时，需要计 算的数据总量为1 * 1999 * sizeof(half) = 3998字节，3998字节既不满足32字节对 齐，也无法平均分配到8个核上。因此该场景下，对数据进行多核切分后，每个核的计 算数据量不同。此种情况下，应该尽可能均匀的分配数据，所有核上的计算数据量有 两种情况，将计算量较多的核称为整核，计算量较少的核称为尾核。 


图 3-15 数据对齐示意图


![](images/4e5ee586a180803eba7111f767fd813fe29052dd3d0c3926cec1a71a2dc37235.jpg)


# Tiling 实现

因为AI处理器在进行数据搬运和Vector计算时，对于搬运的数据长度和Unified Buffer首地址都有必须32字节对齐的要求，首先待处理数据需要先保证向上对齐 到32字节的大小。该场景下后续搬运和计算的处理细节请参考3.3.2.7 非对齐场 景。如下代码片段展示了将数据对齐到datablock大小的示例： 

```c
constexpr uint32_t SIZE_OF_HALF = 2;  
constexpr uint32_t BLOCK_SIZE = 32;  
constexpr uint32_t NUM_BLOCKS = 8;  
constexpr uint32_t ALIGN_NUM = BLOCK_SIZE / SIZE_OF_HALF;  
// shape需要对齐到的32字节，假设原totalLength为1999，向上满足32字节对齐后为2000  
uint32_t totalLengthAligned = (totalLength % ALIGN_NUM == 0U) ? 
```

```txt
static cast<uint32_t>(totalLength):
((static cast<uint32_t>(totalLength) + ALIGN_NUM - 1) / ALIGN_NUM) * ALIGN_NUM; 
```

满足32字节对齐后的数据，应尽可能的均分到每个核上。如果无法均分，那么先 将可以均分的部分平均分配，剩余的部分分配给部分核，会有部分核多算一个 datablock。为了保证切分后的数据仍是满足32字节对齐的，以ALIGN_NUM （ALIGN_NUM个数据为32字节）为粒度，将数据分配到所有核上。在本样例 中，数据类型为half，ALIGN_NUM = BLOCK_SIZE / sizeof(half) = 16。将对齐 后的数据总量按ALIGN_NUM为粒度分成x个数据块，x = 2000 / 16 = 125。 

AI处理器的核数NUM_BLOCKS为8，无法将125个数据块均分到8个核上。按照以 下步骤将数据块尽可能的均分到每个核上： 

a. 计算x / NUM_BLOCKS = 15； 

b. 计算x % NUM_BLOCKS = 5。 

根据上述步骤得出，如果每个核上分配15个数据块，那么将有5个数据块剩余。将 这5个剩余的数据块分配到5个核上，这样可以得到5个计算16个数据块的整核和3 个计算15个数据块的尾核。下图展示了数据无法均分时多核切分的示例。 


图 3-16 无法均分到每个核上的示例


![](images/faf899ec5f607c5d4ee0fc21f32cbc0c6e79bcd885c254ab4a40cad9baf1e17b.jpg)


基于上文，设计如下的算子Tiling结构体成员： 

formerNum：分配到数据量较多的核数，即整核的核数。 

tailNum：分配到数据量较少的核数，即尾核的核数。 

formerLength：整核计算的数据长度。 

tailLength：尾核计算的数据长度。 

Tiling参数的计算代码如下： 

```c
constexpr uint32_t NUM_BLOCKS = 8;  
constexpr uint32_t SIZE_OF_HALF = 2;  
constexpr uint32_t BLOCK_SIZE = 32;  
// shape需要对齐到的最小单位  
constexpr uint32_t ALIGN_NUM = BLOCK_SIZE / SIZE_OF_HALF;  
void GenerateTilingData uint8_t* tilingBuf, uint32_t numBlocks)  
{ // shape需要对齐到的datablock,假设原totalLength为1999，向上满足32字节对齐后为2000 uint32_t totalLengthAligned = (totalLength % ALIGN_NUM == 0U)? static_cast<uint32_t>(totalLength): 
```

((static_cast<uint32_t>(totalLength) + ALIGN_NUM - 1) / ALIGN_NUM) * ALIGN_NUM; //核心数为8，一个datablock包含16个数，那么：datablock的总数：2000 / 16 = 125 //有5个核会分到16个datablock： $125\%$ 8=5，可以称之为整核 //有3个核会分到15个datablock： $8 - 5 = 3$ ，可以称之为尾核 uint32_t formerNum = (totalLengthAligned / ALIGN_NUM) % numBlocks; uint32_t tailNum = numBlocks - formerNum; //整核计算的数据长度：totalLengthAligned / NUM_BLOCKS为每个核上计算的元素个数，formerLength为上述元素个数向上32字节对齐的结果 uint32_t formerLength = static_cast<uint32_t>(((totalLengthAligned + numBlocks - 1) / numBlocks + alignNum - 1) / alignNum) * alignNum; //尾核计算的数据长度：totalLengthAligned / NUM_BLOCKS为每个核上计算的元素个数，tailLength为上述元素个数向下32字节对齐的结果 uint32_t tailLength = (totalLengthAligned / numBlocks / ALIGN_NUM) * ALIGN_NUM; } 

# 算子类实现

在Kernel侧的Init函数中，计算输入在Global Memory上的内存偏移地址时，应对整核 和尾核加以区分。 

整核上，输入的内存偏移地址计算代码如下： 

```javascript
xGm.SetGlobalBuffer(_gm_T\*x +formerLength\*AscendC::GetBlockIdx(),formerLength); 
```

尾核上，计算输入的内存偏移地址时，需在全部整核的数据长度基础上加上尾核的偏 移量，代码如下： 

```rust
xGm.SetGlobalBuffer((gm_T*)x +formerLength *formerNum + tailLength * (AscendC::GetBlockIdx() -formerNum), tailLength); 
```

完整的Init函数实现代码如下： 

__aicore__inline void Init(GM_ADDR x, GM_ADDR y, GM_ADDR z, AddCustomTilingData tiling, AscendC::TPipe* pipeln)   
{ pipe $=$ pipeln; if (AscendC::GetBlockIdx() < tiling.formerNum) { this->tileLength $=$ tiling.formerLength; uint64_t offset $=$ tiling.formerLength \* AscendC::GetBlockIdx(); xGm.SetGlobalBuffer(_gm-half \*)x + offset, tiling.formerLength); yGm.SetGlobalBuffer(_gm-half \*)y + offset, tiling.formerLength); zGm.SetGlobalBuffer(_gm-half \*)z + offset, tiling.formerLength); } else { this->tileLength $=$ tiling.tailLength; uint64_t offset $=$ tiling.formerLength \* tiling.formerNum + tiling.tailLength \* (AscendC::GetBlockIdx( ) - tiling.formerNum); xGm.SetGlobalBuffer(_gm-half \*)x +offset, tiling.tailLength); yGm.SetGlobalBuffer(_gm-half \*)y + offset, tiling.tailLength); zGm.SetGlobalBuffer(_gm-half \*)z + offset, tiling.tailLength); } pipe->InitBuffer(inQueueX, 1, this->tileLength \* sizeofhalf)); pipe->InitBuffer(inQueueY, 1, this->tileLength \* sizeof(half)); pipe->InitBuffer(outQueueZ, 1, this->tileLength \* sizeof(half));   
} 

其余实现与多核Tiling中的实现一致，这里不重复进行说明。 

# 3.3.2.4.5 尾核&尾块

对于不同shape的输入进行数据切分时，可能会发生数据无法平均分配到多个核、同时 每个核内的数据无法均分的情况。参考核间均分场景下的尾块处理与核间不均分场景 下的尾核处理的处理方式，将两者结合起来考虑整核的尾块、尾核的尾块的处理方 式。 

# Tiling 实现

由于本场景中核间、核内的数据均无法均分，在核间不均分场景下的尾核处理定义的 Tiling结构体的基础上增加两个成员变量： 

● formerLastTileLength：数据量多的核最后一个分块大小，即整核的尾块大小。 计算时，先按3.3.2.4.4 尾核Tiling中提到的分核策略，切分数据量多的核。 

```cpp
// shape需要对齐到的datablock  
uint32_t totalLengthAligned = (totalLength % alignNum == 0U) ?  
static_cast<uint32_t>(totalLength):  
((static_cast<uint32_t>(totalLength) + alignNum - 1) / alignNum) * alignNum;  
// 计算整核数量  
uint32_t formerNum = (totalLengthAligned / alignNum) % numBlocks;  
// 计算整核的数据量  
uint32_t formerLength = static_cast<uint32_t>(((totalLengthAligned + numBlocks - 1) / numBlocks + alignNum - 1) / alignNum) * alignNum; 
```

再按3.3.2.4.3 尾块Tiling中的切分策略，计算尾块长度。 

TilingParamsCalc(formerLength, alignNum, formerTileNum, formerTileLength,formerLastTileLength);   
void TilingParamsCalc( uint32_t length, uint32_t alignNum, uint32_t& tileNum, uint32_t& tileLength, uint32_t& lastTileLength)   
{ tileNum $=$ length / (alignNum \* UB_BLOCK_NUM); if (tileNum $= = 0U$ { tileLength $= 0U$ . lastTileLength $=$ static cast<uint32_t>(((length $^+$ alignNum-1)/ alignNum)\* alignNum); } else if (static cast<uint32_t>(length/ alignNum) % UB_BLOCK_NUM $= = 0U$ { tileLength $=$ UB_BLOCK_NUM\* alignNum; lastTileLength $= 0U$ . } else { tileLength $=$ UB_BLOCK_NUM\* alignNum; lastTileLength $=$ static cast<uint32_t>(length - tileNum\* tileLength); }   
} 

tailLastTileLength：数据量少的核最后一个分块大小，即尾核的尾块大小。 计算时，先按3.3.2.4.4 尾核Tiling中提到的分核策略，切分数据量少的核。 

```c
//计算尾核数量  
uint32_t tailNum = numBlocks - formerNum;  
//计算尾核的数据量  
uint32_t tailLength = (totalLengthAligned / numBlocks / alignNum) * alignNum; 
```

再按3.3.2.4.3 尾块Tiling中的切分策略，计算尾块长度。 

```c
TilingParamsCalc(tailLength, alignNum, tailTileNum, tailTileLength, tailLastTileLength);   
void TilingParamsCalc( uint32_t length, uint32_t alignNum, uint32_t& tileNum, uint32_t& tileLength, uint32_t& lastTileLength)   
{ tileNum = length / (alignNum * UB_BLOCK_NUM); if (tileNum == 0U) { tileLength = 0U; lastTileLength = static_cast<uint32_t>(((length + alignNum - 1) / alignNum) * alignNum); } else if (static_cast<uint32_t>(length / alignNum) % UB_BLOCK_NUM == 0U) { tileLength = UB_BLOCK_NUM * alignNum; lastTileLength = 0U; } else { tileLength = UB_BLOCK_NUM * alignNum; lastTileLength = static_cast<uint32_t>(length - tileNum * tileLength); }   
} 
```

# 算子类实现

Kernel侧Init函数和Process函数的实现需将核间均分场景下的尾块处理与核间不均分场 景下的尾核处理的实现结合起来。 

Init函数中由于整核和尾核对应的tileLength和lastTileLength不同。因此需按照核间不 均分场景下的尾核处理中提到的分别处理整核和尾核。后续对主块和尾块的CopyIn、 Compute、CopyOut函数的处理方式与核间均分场景下的处理方式相同。 

Init函数实现代码如下： 

__aicore__inline void Init(GM_ADDR x, GM_ADDR y, GM_ADDR z, AddCustomTilingData tiling, AscendC::TPipe* pipeIn)   
{ pipe $=$ pipeln; if (AscendC::GetBlockIdx() < tiling.formerNum) { this->tileNum $=$ tiling.formerTileNum; this->tileLength $=$ tiling.formerTileLength; this->lastTileLength $=$ tiling.formerLastTileLength; uint64_t offset $=$ tiling.formerLength \* AscendC::GetBlockIdx(); xGm.SetGlobalBuffer((gm half \*)x + offset, tiling.formerLength); yGm.SetGlobalBuffer((gm half \*)y + offset, tiling.formerLength); zGm.SetGlobalBuffer((gm half \*)z + offset, tiling.formerLength); } else { this->tileNum $=$ tiling.tailTileNum; this->tileLength $=$ tiling.tailTileLength; this->lastTileLength $=$ tiling.tailLastTileLength; uint64_t offset $=$ tiling.formerLength \* tiling.formerNum +tiling.tailLength \* (AscendC::GetBlockIdx(）- tiling.formerNum); xGm.SetGlobalBuffer((gm half \*)x + offset, tiling.tailLength); yGm.SetGlobalBuffer((gm half \*)y + offset, tiling.tailLength); zGm.SetGlobalBuffer((gm half \*)z + offset, tiling.tailLength); } // 只有尾块的场景下，tileLength为0，因此取tileLength和lastTileLength的最大值来初始化 uint32_t initBufferLength $=$ AscendC::Std::max(this->tileLength, this->lastTileLength); pipe->InitBuffer(inQueueX, 1, this->initBufferLength \* sizeof(half)); pipe->InitBuffer(inQueueY, 1, this->initBufferLength \* sizeof(half)); pipe->InitBuffer(outQueueZ, 1, this->initBufferLength \* sizeof(half));   
} 

# 3.3.2.5 DoubleBuffer 场景

因存在算子中多次搬入搬出数据的场景，为充分利用硬件资源，实现多流水并行，引 入DoubleBuffer机制。DoubleBuffer是通过将输入数据分成大小相等的两块，充分 利用AI Core的硬件资源，实现数据搬入、计算、数据搬出的并行执行方式。下面以 “核间不均分，核内不均分”的样例为例，介绍算子中DoubleBuffer的实现，完整样 例代码请参见使用DoubleBuffer的Add算子样例。 


图 3-17 DoubleBuffer 数据切分示意图


![](images/436f1d30ab8fc66abca65faac3c8e6444e54f03a5be5fbac03ed0ce566813fd9.jpg)


# Tiling 实现

使能DoubleBuffer后，每一个数据块会分成大小相等的两块，因此，若要使能 DoubleBuffer，要求数据总量应该能够均分。为了简化处理，将可用的Unified Buffer 空间以32字节为粒度，分成n块dataBlock，如果n不是偶数，则减1，这样就可以保证 一套代码兼容开启或不开启DoubleBuffer功能。对应步骤如下： 

步骤1 判断数据总长度totalLength是否满足32字节对齐，如不满足，则计算totalLength向上 32字节对齐后的长度totalLengthAligned。 

```txt
constexpr uint32_t BLOCK_SIZE = 32;
//为方便计算，这里根据数据类型定义变量alignNum作为对齐数
uint32_t alignNum = BLOCK_SIZE / dataBlockSize;
//totalLength为数据总量
uint32_t totalLengthAligned = (totalLength % alignNum == 0)? totalLength : ((totalLength + alignNum - 1) / alignNum) * alignNum; 
```

步骤2 根据totalLengthAligned，计算每个核的计算数据长度blockLength，分核策略可参照 3.3.2.4.4 尾核Tiling。 

步骤3 计算其余Tiling参数。 

对当前Unified Buffer可用空间以32字节为粒度，进行切分，计算出数据块个数 UB_BLOCK_NUM。根据是否开启DoubleBuffer计算出当前可用的最大数据块个数， 记作MAX_AVAILABLE_UB_BLOCK_NUM。最后，以 MAX_AVAILABLE_UB_BLOCK_NUM为粒度，对blockLength进行切分。为方便演示， 如下代码直接给出UB_BLOCK_NUM，作为当前Unified Buffer可用空间包含的block （32字节）数。 

```c
constexpr uint32_t BUFFER_NUM = 2;  
constexpr uint32_t UB_BLOCK_NUM = 21; // UB最大可以使用的block数量  
constexpr uint32_t MAXAVAILABLE_UB_BLOCK_NUM = UB_BLOCK_NUM / BUFFER_NUM * BUFFER_NUM; 
```

tileNum $=$ blockLength/(alignNum \* MAXAVAILABLE UB_BLOCK_NUM); if (tileNum $= = 0$ { //单核需要计算的长度小于UB可用空间，按照仅有尾块处理 tileLength $= 0$ . lastTileLength $=$ (blockLength $^+$ alignNum-1)/alignNum \* alignNum; }elseif((blockLength/alignNum)%MAXAVAILABLE UB_BLOCK_NUM $= = 0$ ）{ //单核的计算量能被当前可用UB空间均分，仅有主块，无尾块 tileLength $=$ MAXAVAILABLE UB_BLOCK_NUM \* alignNum; lastTileLength $= 0$ .   
}else{ //同时有主块和尾块 tileLength $=$ MAXAVAILABLE UB_BLOCK_NUM \* alignNum; lastTileLength $=$ blockLength-tileNum \*tileLength; 

----结束 

# 算子类实现

不开启DoubleBuffer时，只需要对每个核上最后一个分块的起始地址做处理；开启 DoubleBuffer后，需要处理的数据块长度变成原来的一半，所以需要对最后两个数据 块的起始地址做处理。 

开启DoubleBuffer，参考InitBuffer接口函数原型，将num参数配置成2，即 BUFFER_NUM。 

```cpp
this->initBufferLength = AscendC::Std::max(this->tileLength, this->lastTileLength);  
pipe InitBuffer(inQueueX, BUFFER_NUM, this->initBufferLength * sizeof(dataType));  
pipe InitBuffer(inQueueY, BUFFER_NUM, this->initBufferLength * sizeof(dataType));  
pipe InitBuffer(outQueueZ, BUFFER_NUM, this->initBufferLength * sizeof(dataType)); 
```

同时在计算核内每个数据块的长度时，考虑DoubleBuffer场景，需要将Buffer数量， 即BUFFER_NUM=2带入计算。 

```txt
this->tileLength = tilingtileLength / BUFFER_NUM; 
```

由于无法保证尾块满足DoubleBuffer的条件，因此不对尾块进行切分。 

```javascript
this->lastTileLength = tiling.lastTileLength; 
```


Init函数实现代码如下：


```cpp
aicore__inline void Init(GM_ADDR x, GM_ADDR y, GM_ADDR z, AddCustomTilingData tiling) { if (tiling.isEvenCore) { this->blockLength = tiling.blockLength; this->tileNum = tilingtileNum; this->tileLength = tilingtileLength / BUFFER_NUM; this->lastTileLength = tiling.lastTileLength; xGm.SetGlobalBuffer((gm_dataType *)x + this->blockLength * AscendC::GetBlockIdx(), this-blockLength); yGm.SetGlobalBuffer((gm_dataType *)y + this->blockLength * AscendC::GetBlockIdx(), this-blockLength); zGm.SetGlobalBuffer((gm_dataType *)z + this->blockLength * AscendC::GetBlockIdx(), this-blockLength); } else { if (AscendC::GetBlockIdx() < tiling.formerNum) { this->tileNum = tiling.formerTileNum; this->tileLength = tiling.formerTileLength / BUFFER_NUM; this->lastTileLength = tiling.formerLastTileLength; xGm.SetGlobalBuffer((gm_dataType *)x + tiling.formerLength * AscendC::GetBlockIdx(), tiling.formerLength); yGm.SetGlobalBuffer((gm_dataType *)y + tiling.formerLength * AscendC::GetBlockIdx(), tiling.formerLength); zGm.SetGlobalBuffer((gm_dataType *)z + tiling.formerLength * AscendC::GetBlockIdx(), tiling.formerLength); } else { this->tileNum = tiling.tailTileNum; this->tileLength = tiling.tailTileLength / BUFFER_NUM; this->lastTileLength = tiling.tailLastTileLength; xGm.SetGlobalBuffer((gm_dataType *)x + tiling.formerLength * tiling.formerNum + tiling.tailLength * (AscendC::GetBlockIdx() - tiling.formerNum), tiling.tailLength); yGm.SetGlobalBuffer((gm_dataType *)y + tiling.formerLength * tiling.formerNum + tiling.tailLength * (AscendC::GetBlockIdx() - tiling.formerNum), tiling.tailLength); zGm.SetGlobalBuffer((gm_dataType *)z + tiling.formerLength * tiling.formerNum + tiling.tailLength * (AscendC::GetBlockIdx() - tiling.formerNum), tiling.tailLength); } } uint32_t initBufferLength = AscendC::Std::max(this->tileLength, this->lastTileLength); pipeInitBuffer(inQueueX, BUFFER_NUM, initBufferLength * sizeof(dataType)); pipeInitBuffer(inQueueY, BUFFER_NUM, initBufferLength * sizeof(dataType)); pipeInitBuffer(outQueueZ, BUFFER_NUM, initBufferLength * sizeof(dataType)); } 
```

由于开启DoubleBuffer后，切分后的主块数据块个数翻倍，在Process函数中，需要将 BUFFER_NUM带入计算循环次数；尾块独立计算，不开启DoubleBuffer。后续主尾块 在CopyIn、Compute、CopyOut函数中的处理，与尾块tiling处理相同。 

aicore__inline void Process()  
{ //主块进行DoubleBuffer计算，所以loopCount得乘以2  
uint32_t loopCount $=$ this->tileNum\*BUFFER_NUM;  
for (uint32_t i $= 0$ ;i $<$ loopCount;i++) {  
Copyln(i,this->tileLength);  
Compute(i,this->tileLength);  
CopyOut(i,this->tileLength); 

} //尾块进行计算，不做DoubleBuffer操作 if(this->lastTileLength $>0U$ ）{ CopyIn（loopCount,this->lastTileLength); Compute（loopCount,this->lastTileLength); CopyOut（loopCount,this->lastTileLength); }   
1 

# 3.3.2.6 Broadcast 场景

在某些场景下，可能会存在两个输入shape不相同的情况。由于Add接口只支持对 shape相同的输入进行计算，因此需要先对输入进行shape变换，再进行Add计算。本 节将对满足Broadcast条件的输入在算子实现中的Broadcast处理进行介绍，其他场景 可以参考本章节中提供的思路。 

# 须知

Broadcast机制通过扩展较小维度的数据，使得不同shape的输入能够进行运算，从而 避免了显式的复制操作，提高了计算效率。数据进行Broadcast需满足：两个输入的维 度个数相同，并且仅在某一个维度上的长度不同，某一个输入在此维度的长度为1。比 如：shape为(32, 8) 和 (32, 1) 的两个输入可以进行Broadcast，因为它们都是二维， 且第一个维度大小相等，而不相等的维度中第二个输入的维度为1，满足条件。 

本节中将使用Broadcast接口，因此输入需满足该API相关约束。同时，由于硬件限 制，该API的输入地址需满足32字节对齐。本节以输入维度为2、第二个轴（axis = 1） 需要Broadcast为例进行说明。完整的样例代码请参见输入Broadcast的Add算子样 例。 

# Tiling 实现

与输入shape相同的场景相比，在Tiling结构体中增加相应的成员变量，表示是否需要 对输入进行Broadcast、需要对哪个维度进行Broadcast、Broadcast的轴需要扩充的倍 数。因此新增四个Tiling结构体成员： 

xLen和yLen：表示两个输入的数据长度。 

axis：表示对输入的哪个维度进行Broadcast。 

coef：表示Broadcast的输入需要扩维的倍数。例如，x shape为(m, 1)，y shape 为(m, n)，则coef = n。如下图所示，图中相同颜色部分为单次计算的数据块。 


图 3-18 axis=1 时 coef 示意图


![](images/da862112e435e1102a2729d41c1f4f3dbbdf1dc49090a46b322fb9b9478c00b3.jpg)



Tiling结构体定义代码如下所示：


```c
struct AddCustomTilingData {
    uint32_t xLen;
    uint32_t yLen;
    uint32_t coef;
    uint32_t axis;
}; 
```

设需要进行Broadcast的输入长度为shorterAxisLen；不需要进行Broadcast的输入长度 为totalLength。 

```c
constexpr uint32_t BLOCK_SIZE = 32;
... // 读入数据
uint32_t totalLength = (xLen > yLen)? xLen : yLen;
uint32_t shorterAxisLen = (xLen < yLen)? xLen : yLen; 
```

使用shorterAxisLen进行分核计算，并使用分核后的长度与coef相乘作为totalLength 的分核长度。 

```txt
constexpr uint32_t BLOCK_SIZE = 32;  
uint32_t alignCoef = (tiling->axis == 0U) ? shorterAxisLen : totalLength / shorterAxisLen;  
uint32_t divDimCoef = (tiling->axis == 0U) ? totalLength / shorterAxisLen : shorterAxisLen;  
if (divDimCoef % blockDim == 0U) {  
    uint32_t blockLength = divDimCoef / blockDim * alignCoef;  
} else {  
    uint32_t formerNum = (divDimCoef / BUFFER_NUM) % blockDim;  
    uint32_t tailNum = blockDim - formerNum;  
    uint32_t formerLength = ((divDimCoef / BUFFER_NUM) / blockDim + 1U) * BUFFER_NUM * alignCoef;  
    uint32_t tailLength = ((divDimCoef / BUFFER_NUM) / blockDim) * BUFFER_NUM * alignCoef;  
} 
```

进行核内数据切分时，需要计算Unified Buffer数据块的数量向coef和BUFFER_NUM对 齐之后的数量ubBlockAligned。 

```c
uint32_t ubBlockAligned = (MAX-available_UB_BLOCK_NUM * alignNum / (alignCoef * BUFFER_NUM) * (alignCoef * BUFFER_NUM) == 0U)? MAXAVAILABLE_UB_BLOCK_NUM : MAXAVAILABLE_UB_BLOCK_NUM * alignNum / (alignCoef * BUFFER_NUM) * (alignCoef * BUFFER_NUM);   
...   
tileNum = length / ubBlockAligned; 
```

```javascript
if(length % ubBlockAligned == 0U || tileNum == 0U) { if (tileNum == 0U) { tileNum = 1U; } if(length < ubBlockAligned) { tileLength = length; lastTileLength = tileLength; } else { tileLength = ubBlockAligned; lastTileLength = tileLength; } } else { tileNum++; tileLength = ubBlockNum; lastTileLength = (uint32_t)(length - (tileNum - 1) * tileLength); } 
```

# 算子类实现

在核函数初始化阶段，根据Tiling结构体传入的参数确定对哪个输入进行Broadcast。 由于针对输入的第二个轴（axis = 1）进行Broadcast，可以计算出，对于需要进行 Broadcast的输入，每个核搬入数据长度为blockLength / coef。 

# 初始化函数代码如下：

aicore__inline void Init(GM_ADDR x, GM_ADDR y, GM_ADDR z, AddCustomTilingData tiling, AscendC::TPipe* pipeln)   
{ pipe $=$ pipeln; GM_ADDR longerInputPtr; GM_ADDR shorterInputPtr; if (tiling.xLen $>$ tiling.yLen){ longerInputPtr $= x$ shortlputPtr $= y$ 1 } else { longerInputPtr $= y$ shortlputPtr $= x$ 1 } this->coef $=$ tiling.coef; if (tiling.isEvenCore){ this->tileNum $=$ tilingtileNum; this->tileLength $=$ tilingtileLength / BUFFER_NUM; this->lastTileLength $=$ tiling.lastTileLength; xGm.SetGlobalBuffer((gm_T\*)longlputPtr + tiling.blockLength \* AscendC::GetBlockIdx(), tiling.blockLength); yGm.SetGlobalBuffer((gm_T\*)shorterlputPtr + tiling.blockLength \* AscendC::GetBlockIdx() / this- >coef, tiling.blockLength / this->coef); zGm.SetGlobalBuffer((gm_T\*)z + tiling.blockLength \* AscendC::GetBlockIdx(), tiling.blockLength); }else{ if (AscendC::GetBlockIdx() < tiling.formerNum){ this->tileNum $=$ tiling.formerTileNum; this->tileLength $=$ tiling.formerTileLength / BUFFER_NUM; this->lastTileLength $=$ tiling.formerLastTileLength; xGm.SetGlobalBuffer((gm_T\*)longlputPtr + tiling.formerLength \* AscendC::GetBlockIdx(), tiling.formerLength); yGm.SetGlobalBuffer((gm_T\*)shorterlputPtr + tiling.formerLength \* AscendC::GetBlockIdx() / this->coef, tiling.formerLength / this->coef); zGm.SetGlobalBuffer((gm_T\*)z + tiling.formerLength \* AscendC::GetBlockIdx(), tiling.formerLength); }else{ this->tileNum $=$ tiling.tailTileNum; this->tileLength $=$ tiling.tailTileLength / BUFFER_NUM; this->lastTileLength $=$ tiling.tailLastTileLength; xGm.SetGlobalBuffer((gm_T\*)longlputPtr + tiling.formerLength \* tiling.formerNum + tiling.tailLength \* (AscendC::GetBlockIdx() - tiling.formerNum), tiling.tailLength); yGm.SetGlobalBuffer((gm_T\*)shorterlputPtr + tiling.formerLength \* tiling.formerNum / this- >coef + tiling.tailLength \* (AscendC::GetBlockIdx() - tiling.formerNum) / this->coef, tiling.tailLength / this-

```cpp
>coef); zGm.SetGlobalBuffer(_gm_T\*z + tiling.formerLength * tiling.formerNum + tiling.tailLength * (AscendC::GetBlockIdx() - tiling.formerNum), tiling.tailLength); } } pipe->InitBuffer(inQueueX, BUFFER_NUM, this->tileLength * sizeof(T)); pipe->InitBuffer(inQueueY, BUFFER_NUM, this->coef * sizeof(T)); pipe->InitBuffer(outQueueZ, BUFFER_NUM, this->tileLength * sizeof(T)); pipe->InitBuffer(tmpBuf2, this->tileLength * sizeof(dataType)); } 
```

由于数据是向coef对齐的，在数据拷贝的过程中可能会出现地址不满足32字节对齐的 场景，因此CopyIn函数、CopyOut函数中使用DataCopyPad进行数据拷贝。 


CopyIn函数实现代码如下：


```cpp
aicore__inline void Copyln(int32_t progress)   
{ AscendC::LocalTensor<T> xLocal = inQueueX AllocTensor<T>(); AscendC::LocalTensor<T> yLocal = inQueueY AllocTensor<T>(); AscendC::DataCopyExtParams copyXParams = {1, (uint32_t)(this->tileLength * sizeof(T)), 0, 0, 0}; AscendC::DataCopyExtParams copyYParams = {1, (uint32_t)(this->tileLength * sizeof(T) / this->coef), 0, 0, 0}; AscendC::DataCopyPadExtParams<T> padParams = {false, 0, 0, 0}; if (progress == (this->tileNum * BUFFER_NUM - 1)) { AscendC::DataCopyPad<T>(xLocal, xGm[(progress - LAST TWO_TILE) * this->tileLength + this- lastTileLength], copyXParams, padParams); AscendC::DataCopyPad<T>(yLocal, yGm[((progress - LAST TWO_TILE) * this->tileLength + this- lastTileLength) / this->coef], copyYParams, padParams); } else { AscendC::DataCopyPad<T>(xLocal, xGm[progress * this->tileLength], copyXParams, padParams); AscendC::DataCopyPad<T>(yLocal, yGm[progress * this->tileLength / this->coef], copyYParams, padParams); } inQueueX.EnQue(xLocal); inQueueY.EnQue(yLocal); } 
```


CopyOut函数实现代码如下：


aicore__inline void CopyOut(int32_t progress)   
{ AscendC::LocalTensor<T> zLocal $=$ outQueueZ.DeQue<T>(); AscendC::DataCopyExtParams copyParams $=$ {1,(uint32_t)(this->tileLength \* sizeof(T)),0,0,0}; if (progress $= =$ (this->tileNum \* BUFFER_NUM-1)) { AscendC::DataCopyPad<T>(zGm[(progress- LAST TWO TILE)\* this->tileLength + this- lastTileLength],zLocal,copyParams); } else { AscendC::DataCopyPad<T>(zGm[progress\* this->tileLength],zLocal,copyParams); } outQueueZ.FreeTensor(zLocal); 

在Compute函数中，调用Add接口前需要先对输入进行Broadcast。这里需要计算 Broadcast前后的shape。基于前文提到的数据关系，可以计算得出Broadcast前后的 shape分别为{tileLength / broadcastCoef, 1}和{tileLength / broadcastCoef, broadcastCoef}。在此基础上对输入进行Broadcast，并将计算结果存入临时空间中， 然后进行Add计算。实现代码示例如下所示： 

aicore__inline void Compute(int32_t progress)   
{ AscendC::LocalTensor<T> xLocal $=$ inQueueX.DeQue<T>(); AscendC::LocalTensor<T> yLocal $=$ inQueueY.DeQue<T>(); AscendC::LocalTensor<T> zLocal $=$ outQueueZ AllocTensor<T>(); AscendC::LocalTensor<T> broadcastTmpTensor $=$ tmpBuf2.Get<T>(); uint32_t dstShape[] $=$ {this->tileLength / this->coef, this->coef}; 

```cpp
uint32_t srcShape[] = {this->tileLength / this->coef, 1};  
AscendC::Broadcast<T, 2, 1>(broadcastTmpTensor, yLocal, dstShape, srcShape);  
} 
```

# 3.3.2.7 非对齐场景

本节介绍非32字节对齐数据的更多处理方式，包括数据搬入、计算和搬出的处理。用 户在实际算子开发中，可以参考如下方案介绍和算子样例灵活地处理非对齐场景。 

# 数据搬运和 Vector 计算的对齐要求

# 须知

进行数据搬运和Vector计算时，对于搬运的数据长度和操作数的起始地址有如下的对 齐要求： 

● 使用DataCopy接口进行数据搬运，搬运的数据长度和操作数的起始地址（UB上） 必须保证32字节对齐。 

● 通常情况下，进行Vector计算时，操作数的起始地址必须保证32字节对齐。具体对 齐要求需要查阅对应的API参考进行确认。 

下文描述中的Global指Global Memory上的tensor，Local指Local Memory上的 tensor。 

下面是一些非对齐搬运和计算的例子。 

# 非对齐搬入

当需要从Global拷贝11个half数值到Local时，为保证搬运的数据长度32字节对 齐，使用DataCopy拷贝16个half（32B）数据到Local上，Local[11]~Local[15]被 写成无效数据-1。 


图 3-19 非对齐搬入


![](images/efcb1d33a3a3184305b77f15d83407d8138f0b5f1b17f78d2d61b7129f3002ff.jpg)


![](images/6e73a76ef503af5e315652bc9628b8853e7c7ba0e9cb997a759eb2b14b578b2b.jpg)


DataCopy(Local, Global, 16); 

![](images/ab952db4531490a471b52b1406aed2fb2d574930ccb3a67f5800dc7c56188127.jpg)


# 非对齐搬出

当需要从Local拷贝11个half数值到Global时，为保证搬运的数据长度32字节对 齐，使用DataCopy拷贝16个half（32B）数据到Global上， Global[11]~Global[15]被写成无效数据-1。 


图3-20 非对齐搬出


![](images/eaa20c6937b5c3ce79d7e06144e8ca8a504ec028ea7907f0f84ba6eb4b51545c.jpg)


![](images/88891f19b912919433d8c668264d6bf86c21a60dc15915f67a736544f7d71b5c.jpg)


DataCopy(Global, Lobal, 6); 

![](images/aaf2d5bc1636b366220f02592b01364dd0306c705bcf76474a944293ba7fed01.jpg)


# 矢量计算起始地址非32字节对齐的错误示例

矢量计算时需要保证起始地址32字节对齐，如下的示例中，从Local1[7]，即 LocalTensor的第8个数开始计算，起始地址不满足32字节对齐，是错误示例。 


图 3-21 矢量计算起始地址非 32 字节对齐的错误示例


![](images/481bb59c4bb720a139a140e0211142e36e023658cc131ad03911a5f1e164f6bf.jpg)


# 非对齐处理方案

DataCopyPad接口提供非对齐搬运的功能，如果基于该接口支持的产品开发算子（参 见产品支持情况），则可以直接使用该接口解决非对齐场景下的搬运问题。使用 DataCopyPad的完整示例请参考DataCopyPad样例。 

部分型号不支持DataCopyPad接口，需要参考如下的方案处理。 


图 3-22 非对齐处理方案示意图


![](images/e387a202b04ab46cd3c6b5009c901fe20427d3d07f33173be01dbbeb125c095b.jpg)


由于搬入时搬运的数据长度必须保证32字节对齐。数据长度非对齐的情况下，从 Global逐行搬运Tensor数据到Local中，Local中每行都存在冗余数据。 

搬入后，进行矢量计算时对冗余数据的处理方式有以下几种： 

● 冗余数据参与计算。一般用于elewise计算场景。 

通过mask参数掩掉冗余数据。一般用于轴归约计算等场景。 

通过Duplicate逐行清零。计算前，针对每一行数据，调用基础API Duplicate对冗 余数据位置填充0值。 

通过Pad一次性清零。计算前，针对多行数据，可以采用高阶API Pad接口对冗余 数据一次性清零。 

由于搬出时搬运的数据长度和操作数的起始地址（UB上）必须保证32字节对齐，搬出 时可以选择去除冗余数据或者带着冗余数据搬出的方式。 

使用UnPad接口去除冗余数据后搬出。待搬出的有效数据总长度满足32字节对齐 时，可使用高阶API UnPad接口去除冗余数据并完整搬出。 

使用GatherMask收集有效数据后搬出。待搬出的有效数据总长度大于等于32字 节时，可使用GatherMask重新收集有效数据，保证搬出的有效数据起始地址和数 据长度32字节对齐。 

带冗余数据搬出。注意多核处理时开启原子加（使用SetAtomicAdd接口），防止 数据踩踏。 

下面分别对上述几种处理方案做详细说明。 

冗余数据参与计算 

如下图所示，对前11个half数据进行Abs计算，冗余数据可以参与计算，不影响最 终结果。步骤为： 

a. 使用DataCopy从Global搬运16个half数据到Local1中，包含冗余数 据-11~-15； 

b. 直接使用Abs做整块计算，不用计算尾块大小，冗余数据参与计算。 


图 3-23 冗余数据参与计算


![](images/1f24814bac9695fc186cfa6a4087e820050faeff1f86d63ad819a6182406b261.jpg)


使用mask掩掉冗余数据 

如下图所示，假设输入数据的shape为16 * 4，将输入数据搬入到UB后每行数据前 4个half数据为有效数据，其余为冗余数据。为只对前4个half数据进行ReduceMin 计算，可以通过设置mask参数的方法掩掉冗余数据。针对每行数据的处理步骤 为： 

a. 使用DataCopy从Global搬运16个half数据到Local1中； 

b. 对归约计算的目的操作数Local2清零，如使用Duplicate等； 

c. 进行归约操作，将ReduceMin的mask模式设置为前4个数据有效，从而掩掉 冗余数据。 


图 3-24 使用 mask 掩掉脏数据


![](images/413cab60cbd024119a3e963fc7f8efdd94b1e6f91ab574fe6481bec8543e5b40.jpg)


通过Duplicate逐行清零。 

如下图所示，对于搬入后的非对齐数据，逐行进行Duplicate清零处理，步骤为： 

a. 使用DataCopy从Global搬运16个half数据到Local中； 

b. 使用基础API Duplicate，按照如下方式设置mask值，控制仅后5个元素位置 有效，将冗余数据填充为0。 

uint64_t mask0 $=$ ((uint64_t)1 << 16) - ((uint64_t)1 << 11); 

uint64_t mask[2] $=$ {mask0, 0}; 


图 3-25 通过 Duplicate 逐行清零


![](images/c493adb773bbb31939a0cb673532728b38cd8a682fff479ad5063650aeb89fdd.jpg)


通过Pad一次性清零。 

如下图所示，假设输入数据的shape为16 * 6，搬入Local后大小为16 * 16，每行 都包含冗余数据，逐行清零性能较差，可以使用Pad一次性清零，步骤为： 

a. 将 $1 6 ^ { \star } 6$ 的数据从GM上逐行搬入UB后，每行有6个有效数据； 

b. 使用Pad接口将冗余数据位置填充为0。（对应Pad接口使用场景为：tensor 的width已32B对齐，但是有部分冗余数据）。 


图 3-26 通过 Pad 一次性清零


![](images/36ba985698bb93d509fdd86ad77e68612f066c655bc490a03608880c44369c8e.jpg)


使用UnPad接口去除冗余数据后搬出。 

如下图所示，Local内存大小为 $1 6 ^ { \star } 1 6$ ，每行中只有前6个数为有效数据， 要搬出 的有效数据16 * 6满足32B对齐，可以使用UnPad接口去除冗余数据并完整搬出。 步骤如下： 

a. 使用UnPad高阶API去除冗余值； 

b. 使用DataCopy搬运出连续的16 * 6个half数据到Global中。 


图 3-27 使用 UnPad 接口去除冗余数据后搬出


![](images/094f040b8fbe95f8cb07b7b74552c71a8bf75e63d6a4e382c180c7290a889be2.jpg)


使用GatherMask收集有效数据后搬出。 

如下图所示，为搬出19个half数据到Global中，有16-18这3个数据的搬运无法满 足对齐要求，使用GatherMask对有效数据进行重新收集，收集3-18这16个数据并 搬出。步骤如下： 

a. 完整拷贝前16个half（32B）数据到Global中； 

b. 使用GatherMask接口，将Local1[3]~[18]的数Gather到Local2中，Local2从 对齐地址开始； 

c. 从Local2中搬运Gather的数据（32B整数倍）到Global中。 


图 3-28 使用 GatherMask 收集有效数据后搬出。


![](images/035643b2560d9823ef52ff25ddc6363332e21010c38f9cbb75e99b50e2e6f2ae.jpg)


# 带冗余数据搬出

如下图所示，有4个核参与计算，每个核拷贝出4个数，每个核上拷贝的数据长度 不满足32字节对齐，采用将冗余数据一起搬出的方式，步骤如下： 

a. 将目标Global完整清零，可以通过在host清零或者在kernel侧用UB覆盖的方 式处理； 

b. 将本核内的Local数据，除了要搬出的4个有效数据，其余冗余部分清零（使 用Duplicate接口）； 

c. 使用原子累加的方式拷贝到Global，原子累加结合冗余数据清零，确保不会 出现数据踩踏。 


图 3-29 带冗余数据搬出


![](images/15db36fda352ac28751ee6baadc7c1821ea4aa1663538b6d5a561a8a7e0d465c.jpg)


# 样例介绍

样例一：冗余数据参与计算+使用GatherMask收集有效数据后搬出。 

本样例中展示了shape为128 * 18的tensor进行Abs计算的算子实现。针对每行数 据的处理方案如下： 

搬入后，每行数据的后14个数为冗余数据。Abs接口入参BLOCKLEN_CEIL为32个 数，是18个数进行32字节对齐后的结果，有14个冗余数据参与计算。 

AscendC::Abs(outputLocal, inputLocal, BLOCKLEN_CEIL); // main calculation 

计算完成后，通过GatherMask的bufPattern入参控制收集18个数中的后16个数。 

```cpp
uint16_t tmpValue = 0;  
AscendC::Duplicate<uint16_t>(bufPattern, tmpValue, 16);  
bufPatternSetValue(0, 0b1111111111111100); // select the last 14 elements of the first 16  
bufPatternSetValue(1, 0b000000000000011); // select the first 2 elements of the next 16  
uint32_t mask = 32;  
uint64_t rsvdCnt = 0;  
AscendC::LocalTensor<half> tailLocal = outQueueTail AllocTensor<half>();  
AscendC::GatherMask(tailLocal, outputLocal, bufPattern, true, mask, {1, 1, 8, 8}, rsvdCnt); 
```

首先使用DataCopy搬运前16个数，然后搬运后16个数，中间的14个数存在重复 搬运。注意：因为DataCopy的目的地址存在重叠所以需要通过PipeBarrier添加流 水同步。 

```txt
uint32_t copyLenMain = TILE_LENGTH * sizeof(half) / 32 * 32 / sizeof(half);  
uint32_t offsetMain = progress * TILE_LENGTH;  
AscendC::DataCopy.dstGlobal[offsetMain], outputLocal, copyLenMain);  
AscendC::PipeBarrier<PIPE_MTE3>();  
uint32_t tailLen = 32 / sizeof(half);  
uint32_t offsetTail = offsetMain + ( TILE_LENGTH - tailLen);  
AscendC::DataCopy.dstGlobal[offsetTail], tailLocal, tailLen); 
```

搬入时要保证32字节对齐，所以要将输入的最后一行补齐到32字节对齐，防止访 问非法数据，main.cpp中对GM上输入的长度的定义如下： 

```c
size_t inputByteSize = 2318 * sizeof(int16_t); // 2318 = 2304 + 32 - 18  
size_t outputByteSize = 2304 * sizeof(int16_t); 
```

样例二：通过Duplicate逐行清零 $^ +$ 带冗余数据搬出。 

本样例中展示了shape为 $6 4 ^ { \star } 1 1$ 的tensor进行Abs计算的算子实现。 共使用4个 核，每个核处理 $1 6 ^ { \star } 1 1$ 个数据。 

搬入后，每行数据的后5个数为冗余数据。通过Duplicate接口对每行数据中的后5 个数据进行清零。 

```cpp
// mask mode controls only the last 5 elements doing Duplicate  
uint64_t mask0 = (1ul << 16) - (1ul << BLOCK_element_NUM);  
uint64_t mask[2] = {mask0, 0};  
for (int32_t i = 0; i < BLOCK_GROUP_NUM; i++) {  
    AscendC::Duplicate<half>(inputLocal[i * BLOCKLEN Ceiling], 0, mask, 1, 1, 1); // clear dummy data on inputLocal  
}  
AscendC::Abs(outputLocal, inputLocal, BLOCKLEN Ceiling * BLOCK_GROUP_NUM); 
```

搬出时，带冗余数据搬出并开启原子累加，BLOCKLEN_CEIL中包含冗余数据。 

```rust
AscendC::SetAtomicAdd<half>();   
for (int32_t i = 0; i < BLOCK_GROUP_NUM; i++) { AscendC::DataCopy<half>(dstGlobal[i * BLOCK_element_NUM], outputLocal[i * BLOCKLEN Ceiling], BLOCKLEN_CEIL);   
} AscendC::DisableDmaAtomic(); 
```

所以在初始化时，需要对GM数据进行清零，清零代码如下，示例中多个核都调用 Fill接口进行清零，需要调用SyncAll进行核间同步。 

```cpp
AscendC::Fill<half>(dstGlobal, blockLength, 0);  
pipe.InitialBuffer(inQueue, BUFFER_NUM, BLOCK_GROUP_NUM * BLOCKLEN Ceiling * sizeof(half));  
pipe.InitialBuffer(outQueue, BUFFER_NUM, BLOCK_GROUP_NUM * BLOCKLEN Ceiling * sizeof(half));  
pipe.InitialBuffer(syncLocalTbuf, USE_CORE_NUM * DEFAULT_SYNCCALL NEED_SIZE * sizeof(int32_t));  
AscendC::LocalTensor<int32_t> SyncLocal = syncLocalTbuf.Get<int32_t>();  
AscendC::SyncAll(syncGlobal, SyncLocal, USE_CORE_NUM); 
```

搬入时要保证32字节对齐，需要将输入的最后一行补齐到32字节对齐，防止访问 非法数据；搬出时带冗余数据搬出，输出的最后一行也需要补齐到32字节对齐。 main.cpp中对GM上输入输出的长度的定义如下： 

```txt
uint32_t elemLength = 709; // TOTAL_LENGTH + (BLOCKLEN Ceiling - BLOCK_element_NUM) // copy in borrow the next (BLOCKLEN Ceiling - BLOCK_element_NUM) elements of srcGM size_t inputByteSize = elemLength * sizeof(int16_t); // copy out atomic add extra (BLOCKLEN Ceiling - BLOCK_element_NUM) zeros to dstGM size_t outputByteSize = elemLength * sizeof(int16_t); 
```

样例三：冗余数据参与计算 $\cdot$ 使用UnPad接口去除冗余数据后搬出。 

本样例中展示了shape为2048 * 14的tensor进行Abs计算的算子实现。 共使用8个 核，每个核处理256 * 14个数据。 

搬入后，每行数据的后2个数为冗余数据。Abs接口入参BLOCK_GROUP_NUM * BLOCKLEN_CEIL为连续的16行数据，每行16个数，每行的冗余数据参与计算。 

AscendC::Abs(inputLocal, inputLocal, BLOCK_GROUP_NUM * BLOCKLEN_CEIL); // main calculation 计算后，使用UnPad接口去除冗余数据后再搬出，通过unPadParams.rightPad参 数控制去除每行最后的2个冗余数据。 

unPadParams.rightPad $=$ BLOCKLEN_CEIL - BLOCK_ELEMENT_NUM; // delete 2 dummy half each row AscendC::UnPad<half>(outputLocal, inputLocal, unPadParams, this->tiling); 

注意：UnPad接口需要传入tiling参数。abs_unpad_tiling.cpp中关键计算过程如 下： 

AscendC::GetUnPadMaxMinTmpSize(*ascendcPlatform, srcShape, sizeof(int16_t), tmpMaxSize, tmpMinSize); optiling::UnPadTiling tilingData; AscendC::UnPadTilingFunc(srcShape, tmpMaxSize, sizeof(int16_t), tilingData); 

tiling参数需要通过核函数的入参传入到kernel侧，供UnPad高阶API使用。 

abs_unpad_custom<<<numBlocks, nullptr, stream>>>(xDevice, zDevice, tilingDevice); 

搬入时要保证32字节对齐，所以要将输入的最后一行补齐到32字节对齐，防止访 问非法数据，main.cpp中对GM上输入的长度的定义如下。 

```c
// 28674 is TOTAL_LENGTH + (BLOCKLEN_CEIL - BLOCK_element_NUM)  
// 28672 is TOTAL_LENGTH  
// copy in borrow the next (BLOCKLEN_CEIL - BLOCK_element_NUM) elements of srcGM  
uint32_t oriLength = 28672;  
uint32_t colNum = 14;  
uint32_t maxColNum = 32 / sizeof( uint16_t);  
uint32_t padLength = oriLength + maxColNum - colNum;  
size_t inputByteSize = padLength * sizeof(int16_t);  
size_t outputByteSize = oriLength * sizeof(int16_t); 
```

示例四：通过Pad一次性清零 $^ +$ 带冗余数据搬出。 

本样例中展示了shape为 $2 0 4 8 ^ { \star } 7$ 的tensor进行Abs计算的算子实现。 共使用8个 核，每个核处理 $2 5 6 ^ { \star } 7$ 个数据。 

搬入后，每行数据的后9个数为冗余数据。每个核上通过Pad接口将256 * 9的冗余 数据块整体清零后参与Abs计算。 

AscendC::PadParams padParams $=$ {0, BLOCKLEN_CEIL - BLOCK_ELEMENT_NUM, 0}; AscendC::Pad(outputLocal, inputLocal, padParams, this->tiling); AscendC::Abs(outputLocal, outputLocal, BLOCK_GROUP_NUM * BLOCKLEN_CEIL); // main calculation 

计算后带冗余数据搬出的代码解释和样例二一致。 

注意：Pad接口需要传入tiling参数。abs_pad_tiling.cpp中关键计算过程如下： 

AscendC::GetPadMaxMinTmpSize(srcShape, sizeof(int16_t), tmpMaxSize, tmpMinSize); optiling::PadTiling tilingData; AscendC::PadTilingFunc(srcShape, oriSrcShape, tmpMaxSize, sizeof(int16_t), tilingData); 

tiling参数需要通过核函数的入参传入到kernel侧，供Pad高阶API使用。 

abs_pad_custom<<<numBlocks, nullptr, stream>>>(xDevice, zDevice, tilingDevice); 

搬入时要保证32字节对齐，需要将输入的最后一行补齐到32字节对齐，防止访问 非法数据；搬出时带冗余数据搬出，输出的最后一行也需要补齐到32字节对齐。 main.cpp中对GM上输入输出的长度的定义如下： 

```c
// 14336 is the length of input data  
uint32_t oriLength = 14336;  
// we must allocate more space to prevent invalid address access  
uint32_t padLength = oriLength + shapePad[1] - shapeUsed[1];  
size_t inputByteSize = padLength * sizeof(int16_t);  
size_t outputByteSize = padLength * sizeof(int16_t);  
// however, original length must be used when output to file size_t outputFileSize = oriLength * sizeof(int16_t); 
```

样例五：使用mask掩掉冗余数据 $^ { \cdot + }$ 带冗余数据搬出。 

本样例中展示了shape为16 * 4的tensor每行数据进行ReduceMin计算的算子实 现。 共使用4个核，每个核处理4 * 4个数据。 

搬入后，每行数据的后12个数为冗余数据。通过ReduceMin的入参Mask控制只有 前4个数参与计算。 

```cpp
uint64_t Mask0 = ((uint64_t)1 << BLOCK_element_NUM) - 1; // mask mode controls only the first 4 elements do ReduceMin calculation  
uint64_t Mask[2] = {Mask0, 0};  
// main calculation  
for (int i = 0; i < BLOCK_GROUP_NUM; i++) {  
    AscendC::ReduceMin<half>(outputLocal[i * BLOCKLEN Ceiling], inputLocal[i * BLOCKLEN Ceiling], workLocal, Mask, 1, 8, false);  
}  
outQueue.EnQue<half>(outputLocal);  
inQueue.FreeTensor(inputLocal); 
```

计算后带冗余数据搬出的代码解释和样例二一致。 

搬入时要保证32字节对齐，需要将输入的最后一行补齐到32字节对齐，防止访问 非法数据；搬出时带冗余数据搬出，输出的最后一行也需要补齐到32字节对齐。 main.cpp中对GM上输入输出的长度的定义如下： 

```c
// copy in borrow the next (BLOCKLEN Ceiling - BLOCK_element_NUM) elements of srcGM size_t inputByteSize = 76 * sizeof(int16_t); // copy out atomic add extra (BLOCKLEN Ceiling - BLOCK_element_NUM) zeros to dstGM size_t outputByteSize = 76 * sizeof(int16_t); 
```

# 3.3.3 矩阵编程（高阶 API）

# 3.3.3.1 基础知识

# 说明

本节内容为使用高阶API进行矩阵乘法的编程指导。使用高阶API进行实际的矩阵编程时，需要通 过API参考确认接口支持的产品型号。 

# 矩阵乘法概述

Matmul的计算公式为： ${ \mathsf { C } } = { \mathsf { A } } ^ { \star } { \mathsf { B } } ^ { } +$ bias，其示意图如下。 

● A、B为源操作数，A为左矩阵，形状为[M, K]；B为右矩阵，形状为[K, N]。 

C为目的操作数，存放矩阵乘结果的矩阵，形状为[M, N]。 

bias为矩阵乘偏置，形状为[1, N]。对 $\mathsf { A } ^ { \star } \mathsf { B }$ 结果矩阵的每一行都采用该bias进行偏 置。 


图 3-30 Matmul 矩阵乘示意图


![](images/bdbdee7190baf6eadd70bf799e43d5e6c464b127462bec86cc5be6653b9d2aa6.jpg)


# 矩阵乘法数据流

在了解矩阵乘法数据流之前，需要先回顾一下几个重要的存储逻辑位置的概念： 

搬入数据的存放位置：A1，用于存放整块A矩阵，可类比CPU多级缓存中的二级 缓存； 

搬入数据的存放位置：B1，用于存放整块B矩阵，可类比CPU多级缓存中的二级缓 存； 

搬入数据的存放位置：C1，用于存放整块的矩阵乘偏置Bias矩阵，可类比CPU多 级缓存中的二级缓存； 

搬入数据的存放位置：A2，用于存放切分后的小块A矩阵，可类比CPU多级缓存 中的一级缓存； 

搬入数据的存放位置：B2，用于存放切分后的小块B矩阵，可类比CPU多级缓存中 的一级缓存； 

搬入数据的存放位置：C2，用于存放切分后的小块矩阵乘偏置Bias矩阵，可类比 CPU多级缓存中的一级缓存； 

结果数据的存放位置：CO1，用于存放小块结果C矩阵，可理解为Cube Out； 

结果数据的存放位置：CO2，用于存放整块结果C矩阵，可理解为Cube Out； 

搬入数据的存放位置：VECCALC，一般在计算需要临时变量时使用此位置。 

矩阵乘法数据流指矩阵乘的输入输出在各存储位置间的流向。逻辑位置的数据流向如 下图所示（为了简化描述，没有列出bias）： 

A矩阵从输入位置到A2的数据流如下（输入位置可以是GM或者VECOUT）：GM->A2，GM->A1->A2；VECOUT->A1->A2。 

由于A1比A2的空间更大，数据从GM或VECOUT可以先搬入A1进行缓存，待该数 据执行Cube计算前，数据直接从A1搬入A2，这样在搬运大量数据时可以减少计算 前的等待时间，提升性能，只有在搬入数据较少的场景才可能使用GM->A2的数 据流。 

B矩阵从输入位置到B2的数据流如下（输入位置可以是GM或者VECOUT）：GM->B2，GM->B1->B2；VECOUT->B1->B2。 

由于B1比B2的空间更大，数据从GM或VECOUT可以先搬入B1进行缓存，待该数 据执行Cube计算前，数据直接从B1搬入B2，这样在搬运大量数据时可以减少计算 前的等待时间，提升性能，只有在搬入数据较少的场景才可能使用GM->B2的数据 流。 

完成A2*B2=CO1计算。 

CO1数据汇聚到CO2：CO1->CO2。 

从CO2到输出位置（输出位置可以是GM或者VECIN）：CO2->GM/CO2- >VECIN。 

![](images/b53a88f9737b1eaa69f39c1275084f3fa292b1f809598a52817da4e49df4612e.jpg)


# 数据格式

在完成Matmul矩阵乘法时，主要涉及到两种分形格式ND和NZ。其它的数据格式请参 考数据排布格式。 

ND：普通格式，N维张量。 

● NZ：为满足AI Core中Cube计算单元高性能计算的需要，引入该特殊格式。 

ND $- >$ NZ的变换过程为： 

(..., N, H, W )->pad->(..., N, H1*H0, W1*W0)->reshape->(..., N, H1, H0, W1, W0)->transpose->(..., N, W1, H1, H0, W0) 

如下图所示 （W，H）大小的矩阵被分为（H1*W1）个分形，按照列优先排布， 形状如N字形；每个分形内部有（H0*W0）个元素，按照行优先排布，形状如z字 形。所以这种数据格式称为NZ（大N小Z）格式。 

![](images/af645060fb657e450e0a3e9ce55bdb1ffa9f6f4ab9b69dee7b28e7a2bcbcda43.jpg)


下面我们再通过一个具体的例子来深入理解ND和NZ格式的数据排布区别。假设 分形格式为2*2，如下图所示4*4的矩阵，ND（1，4，4）和NZ（1，2，2，2， 2）格式存储的情况下，数据在内存中的排布格式分别为： 

ND: 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15 

NZ: 0, 1, 4, 5, 8, 9, 12, 13, 2, 3, 6, 7, 10, 11, 14, 15 

![](images/f3e8b75befd65cc60615b505dcee5997264411af45342a1e7730a1a6566b677a.jpg)


关于矩阵ND到NZ格式转换的样例请参考Matmul输入矩阵ND到NZ格式转换的算 子样例。 

# 数据分块（Tiling）

# 多核切分

为了实现多核并行，需要将矩阵数据进行切分，分配到不同的核上进行处理。切 分策略如下图所示： 

对于A矩阵，沿着M轴进行切分，切分成多份的singleCoreM，单核上处理 SingleCoreM * K大小的数据。 

对于B矩阵，沿着N轴进行切分，切分成多份的singleCoreN，单核上处理K * SingleCoreN大小的数据。 

对于C矩阵，SingleCoreM * K大小的A矩阵和K * SingleCoreN大小的B矩阵相 乘得到SingleCoreM * SingleCoreN大小的C矩阵，即为单核上输出的C矩阵大 小。 

比如，下图中共有8个核参与计算，将A矩阵沿着M轴划分为4块，将B矩阵沿着N 轴切分为两块，单核上仅处理某一分块（比如图中绿色部分为core3上参与计算的 数据）：SingleCoreM * K大小的A矩阵分块和SingleCoreN* K大小的B矩阵分块相 乘得到SingleCoreM * SingleCoreN大小的C矩阵分块。 

![](images/edf87b2197f550d27b57af41ff307cf160c67a0bc46707de5415b0dc15415385.jpg)


另外，单核上处理的K轴长度为SingleCoreK，对于K轴较大的场景，可以沿着K轴 进行切分，切分成多份的singleCoreK，详细案例介绍请参考Matmul高阶API使能 多核切K。 

# 核内切分

大多数情况下，Local Memory的存储，无法完整的容纳算子的输入与输出，需要 每次搬运一部分输入进行计算然后搬出，再搬运下一部分输入进行计算，直到得 到完整的最终结果，也就是需要做核内的输入切分。切分的策略如下所示： 

对于A矩阵，沿M轴进行切分，将singleCoreM切分成多份的baseM，切分成 的份数对应图示的mIter；沿K轴进行切分，切分成多份的baseK。 

对于B矩阵，沿N轴进行切分，将singleCoreN切分成多份的baseN，切分成的 份数对应图示的nIter；沿K轴进行切分，切分成多份的baseK。 

对于C矩阵，A矩阵中baseM*baseK大小的分块和B矩阵中baseK*baseN大小 的分块相乘并累加，得到C矩阵中对应位置baseM*baseN大小的分块。比 如，图中结果矩阵中的绿色矩阵块5是通过如下的累加过程得到的：a*a+b*b +c*c+d*d+e*e+f*f。 

![](images/1529da7c3c002ebdcc676b36241d98648a503f0dd3555ca9d4e11d7f04103716.jpg)


除了基本块形状baseM, baseN, baseK外，还有一些常用的tiling参数，其含义如 下： 

iterateOrder：一次Iterate迭代计算出[baseM, baseN]大小的C矩阵分片。 Iterate完成后，Matmul会自动偏移下一次Iterate输出的C矩阵位置， iterateOrder表示自动偏移的顺序。 

0代表先往M轴方向偏移再往N轴方向偏移； 

1代表先往N轴方向偏移再往M轴方向偏移。 

在上图的示例中，iterateOrder取值为0。 

depthA1，depthB1：A1、B1上存储的矩阵片全载A2、B2的份数，A2、B2存 储大小分别是baseM * baseK、baseN * baseK，即depthA1是A1矩阵切片含 有baseM * baseK块的个数，depthB1是B1矩阵切片含有baseN * baseK块的 个数。 

stepM，stepN：stepM为左矩阵在A1中缓存的buffer M方向上baseM的倍 数，stepN为右矩阵在B1中缓存的buffer N方向上baseN的倍数。 

stepKa，stepKb：stepKa为左矩阵在A1中缓存的buffer K方向上baseK的倍 数，stepKb为右矩阵在B1中缓存的buffer K方向上baseK的倍数。 

# 3.3.3.2 算子实现

# 实现流程

上文介绍了Matmul矩阵乘的数据切分方案和数据流。Ascend C提供一组Matmul高阶 API，封装了这些常用的切分和数据搬运、计算的算法逻辑，方便用户快速实现 Matmul矩阵乘法的运算操作。开发者在host侧通过调用API自动获取Tiling参数，该参 数传递到kernel侧后，在初始化操作时传入，通过几个简单的API即可完成矩阵乘操 作。完整样例请参考LINK。 


图 3-31 矩阵编程流程示意图


![](images/36a89d49b7372d04035f2fa87bf689db50291c33321c499188228619fa60ea64.jpg)


host侧自动获取Tiling参数的关键步骤介绍如下： 

# 步骤1 创建Tiling对象。

```cpp
auto ascendcPlatform = platform_ascending::PlatformAscendCManager::GetInstance();  
matmul_tiling::MultiCoreMatmulTiling tilingApi(*ascendingPlatform); 
```

传入硬件平台信息创建PlatformAscendC对象，然后创建Tiling对象，硬件平台信息可 以通过GetPlatformInfo获取。 

# 步骤2 设置参与Matmul运算的核数，A、B、Bias的内存逻辑位置、格式和数据类型。

```cpp
tilingApi.SetDim(ascendcPlatform->GetCoreNumAic());  
tilingApi.SetATOpe(AscendC::TPosition::GM, CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT16);  
tilingApi.SetBType(AscendC::TPosition::GM, CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT16);  
tilingApi.SetCType(AscendC::TPosition::GM, CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT);  
tilingApi.SetBiasType(AscendC::TPosition::GM, CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT); 
```

# 步骤3 设置矩阵shape信息。

```txt
tilingApi.SetShape(M, N, K);
tilingApi.SetOrgShape(M, N, K); // 设置原始完整的形状M、N、K 
```

# 步骤4 设置可用空间大小信息。

设置Matmul计算时可用的L1 Buffer/L0C Buffer/Unified Buffer空间大小，-1表示AI处 理器对应Buffer的大小。 

```javascript
tilingApi.SetBufferSpace(-1, -1, -1); 
```

# 步骤5 按需设置其他参数，比如设置bias参与计算。

```javascript
tilingApi.EnabledBias(true); 
```

# 步骤6 获取Tiling参数。

int64_t res $=$ tilingApi.GetTiling(tilingData); if(res $\equiv = -1$ ）{ std::cout<<"gen tiling failed"<<std::endl; } 

步骤7 Tiling参数的序列化保存等其他操作。 

```txt
uint32_t tcubeTilingSize = tilingData的数据Size();  
tilingData.SaveToBuffer(tilingBuf, tcubeTilingSize); 
```

# ----结束

kernel侧使用Matmul API矩阵乘运算的具体步骤如下： 

# 步骤1 创建Matmul对象

创建Matmul对象的示例如下： 

纯Cube模式（只有矩阵计算）场景下，建议在代码中定义ASCENDC_CUBE_ONLY 宏，避免额外的性能开销。本节内容以纯Cube模式举例。 

默认为MIX模式（包含矩阵计算和矢量计算），该场景下通常不定义 ASCENDC_CUBE_ONLY宏，如果在程序中使用了ASCENDC_CUBE_ONLY宏，则 必须使用ASCEND_IS_AIC宏和ASCEND_IS_AIV宏将Cube计算和Vector计算隔离 开，更多内容请参考3.3.5 融合算子编程。 

```cpp
// 纯Cube模式（只有矩阵计算）场景下，需要设置该代码宏，并且必须在#include"lib/matmul_intf.h"之前设置  
#define ASCENDC_CUBE_ONLY  
#include "lib/matmul_intf.h"  
typedef AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, half> aType;  
typedef AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, half> bType;  
typedef AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, float> cType;  
typedef AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, float> biasType;  
AscendC::Matmul<aType, bType, cType, biasType> mm; 
```

创建对象时需要传入A、B、C、Bias的参数类型信息， 类型信息通过MatmulType来定 义，包括：内存逻辑位置、数据格式、数据类型。 

# 步骤2 初始化操作。

```cpp
REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm, &tiling); // 初始化 
```

# 说明

Matmul高阶API内部实现时需要使用系统workspace（即对应本步骤中的GetSysWorkSpacePtr 接口），开发者需要自行申请系统workspace的空间： 

```txt
- 在host侧Tiling实现时，设置总的workspace的数值大小（包含用户workspace和系统 workspace），workspace空间由框架来申请并管理。系统workspace的空间大小通过GetLibApiWorkSpaceSize获取。
size_t userWorkspaceSize = 0;
size_t systemWorkspaceSize = static_cast < size_t > (ascendcPlatform.GetLibApiWorkSpaceSize());
size_t *currentWorkspace = context->GetWorkspaceSizes(1);
currentWorkspace[0] = userWorkspaceSize + systemWorkspaceSize; 
```

```c
- 若算子工程不是自定义算子工程，也不是带有HAVE_WORKSPACE编译宏的Kernel直调算子工程，框架不会自动设置workspace，需要在kernel侧的Matmul初始化前，通过SetSysWorkSpace设置系统workspace。
// 使用Matmul时必须设置workspace空间
SetSysWorkspace workspace);
if (GetSysWorkSpacePtr() == nullptr) {
return;
} 
```

# 步骤3 设置左矩阵A、右矩阵B、Bias。

```txt
mm.SetTensorA(gm_a); //设置左矩阵A  
mm.SetTensorB(gm_b); //设置右矩阵B  
mm.SetBias(gm.bias); //设置Bias 
```

# 步骤4 完成矩阵乘操作。

调用Iterate完成单次迭代计算，叠加while循环完成单核全量数据的计算。Iterate 方式，可以自行控制迭代次数，完成所需数据量的计算，方式比较灵活。 

```javascript
while (mm.Iterate()) { mm.GetTensorC(gm_c); } 
```

调用IterateAll完成单核上所有数据的计算。IterateAll方式，无需循环迭代，使用 比较简单。 mm.IterateAll(gm_c); 

# 步骤5 结束矩阵乘操作。

```javascript
mm.End(); 
```

# ----结束

# 设置 Shape 信息

在实现Host Tiling时可以设置Shape信息，用于Tiling计算；kernel侧运行时也可以修 改部分Shape信息，用于尾块设置、Matmul复用（多个Matmul计算复用一个Matmul 对象）等场景。本节对涉及到的Shape概念进行介绍，并给出host侧和kernel侧设置 Tiling信息的指导。 

orgShape：M、N、K 

singleCoreShape：singleCoreM、singleCoreN、singleCoreK 

singleShape：singleM、singleN、singleK 

baseShape：baseM、baseN、baseK 

通过数据分块（Tiling）的介绍我们已经了解了orgShape(M、N、K)， singleCoreShape(singleCoreM、singleCoreN、singleCoreK)，baseShape(baseM、 baseN、baseK)的概念，如下图所示： 

![](images/a800df5368d85111e388eee8a57eb91cd793738e2839828f6bfd6020800663a2.jpg)


![](images/ea3913712b9df3efeb7ae5267a95ae29143cd15106dd6b1df411faffd2816775.jpg)


![](images/b6f67c7da376c9b7e9faaa11622d333f3d8028dc97cb13b811ecff0b354f9830.jpg)


除此之外，单核的Matmul Tiling时，实际参与Matmul计算的shape可以是原始shape 中的一部分，singleM, singleN, singleK用于表达实际参与Matmul计算的shape，如下 图所示。在单核的情况下，singleM, singleN, singleK会透传给singleCoreM, singleCoreN, singleCoreK。 

![](images/2e143d9296c69ae64eb0f4f5fd6717abb5e9f26bf7f7b5d277ec8cf8a3040c4f.jpg)


Kernel运行时设置 

SetTail、SetSingleShape都是运行时修改singleCoreM、singleCoreN、 singleCoreK，处理尾块时使用SetTail，Matmul复用（多个Matmul计算复用 一个Matmul对象）的场景可以使用SetSingleShape重新设置。 

SetOrgShape是运行时修改M、N、K，Matmul复用的场景可以使用 SetOrgShape重新设置。 

单核Tiling时设置 

– SetOrgShape（必选）：设置M、N、K 

SetShape（非必选）： 设置singleM、singleN、singleK，等同于设置 singleCoreM、singleCoreN、singleCoreK 

SetFixSplit（非必选）：设置baseM、baseN、baseK 

多核Tiling时设置 

– SetOrgShape（必选）：设置M、N、K 

SetShape（非必选）： 设置singleM、singleN、singleK 

– SetFixSplit（非必选）：设置baseM、baseN、baseK 

– SetSingleShape(非必选)： 设置singleCoreM、singleCoreN、singleCoreK 

SetSingleRange(非必选) ：设置singleCoreM、singleCoreN、singleCoreK的 范围 

# 设置 format 格式

创建Matmul对象时需要传入A、B、C、Bias的参数类型信息， 类型信息通过 MatmulType来定义，包括：内存逻辑位置、数据格式、数据类型。示例如下： 

typedef AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, half> aType; typedef AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, half> bType; 

typedef AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, float> cType; typedef AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, float> biasType; AscendC::Matmul<aType, bType, cType, biasType> mm; 

针对数据格式，包括CubeFormat::ND, CubeFormat::NZ, CubeFormat::ND_ALIGN三 种，ND和NZ格式在数据格式章节已经介绍，ND_ALIGN格式的介绍请参考数据排布格 式。 

# 3.3.3.3 特性场景

# 3.3.3.3.1 Matmul 特性介绍

除了前述基础知识和算子实现中介绍的基本计算能力外，Matmul矩阵编程还提供了适 用于不同场景的处理能力及多种功能，具体场景和功能列于下表中，详细内容请见后 续章节。 


表 3-4 Matmul 功能特性表


<table><tr><td>特性描述</td><td>功能简介</td></tr><tr><td>多核对齐切分</td><td>在多核场景中，支持将矩阵数据沿M、N、K轴切分，满足M能被singleCoreM整除、N能被singleCoreN整除、K能被singleCoreK整除的对齐场景时的处理方式，从而实现多核并行计算矩阵乘。</td></tr><tr><td>多核非对齐切分</td><td>在多核场景中，支持将矩阵数据沿M、N、K轴切分。当出现M不能被singleCoreM整除、或N不能被singleCoreN整除、或K不能被singleCoreK整除的非对齐场景（即尾块场景）时的处理方式。</td></tr><tr><td>异步场景处理</td><td>MIX场景（包含矩阵计算和矢量计算）下不需要等待矩阵乘计算完成，先执行其它计算。</td></tr><tr><td>矩阵乘输出的量化/反量化</td><td>将矩阵乘的计算结果从CO1搬出到Global Memory时，对矩阵元素执行数据量化或反量化操作。</td></tr><tr><td>自定义数据搬入搬出</td><td>自定义矩阵乘计算前后的数据搬运函数。本功能支持用户实现左矩阵A、右矩阵B从Global Memory分别自定义搬入到A1、B1的过程，输出C矩阵从CO1自定义搬出到Global Memory的过程。</td></tr><tr><td>矩阵乘输出的Channel拆分</td><td>矩阵乘输出的Channel拆分，又称ChannelSplit。指float数据类型、NZ数据格式的输出C矩阵按照16*8的分形大小存储。</td></tr><tr><td>矩阵向量乘</td><td>矩阵向量乘即GEMV，指矩阵乘计算中M=1，K&gt;1的场景，即对形状为(1，K)的左矩阵A实现矩阵乘计算。</td></tr><tr><td>4:2稀疏矩阵乘</td><td>4:2稀疏矩阵乘，又称Sparse Matmul。指对稀疏左矩阵A和4:2稠密化的右矩阵B实现矩阵乘计算。</td></tr><tr><td>上/下三角矩阵乘</td><td>忽略位于矩阵中下三角或上三角位置的元素的计算，实现矩阵中上三角或下三角位置的元素的矩阵乘计算。</td></tr><tr><td>TSCM输入的矩阵乘</td><td>对内存逻辑位置为TSCM的左矩阵A或右矩阵B实现矩阵乘计算。</td></tr><tr><td>矩阵乘输出的N方向对齐</td><td>矩阵乘输出的N方向对齐，又称NDALIGN格式输出。指对数据格式为NDALIGN的输出C矩阵实现N方向32字节对齐的自动补齐及输出。</td></tr><tr><td>单次矩阵乘局部输出</td><td>单次矩阵乘局部输出，又称Partial Output，指矩阵乘计算时不
对单核K方向的计算结果做累加，直接输出计算结果。</td></tr><tr><td>AIC和AIV独立运行机制</td><td>AIC和AIV独立运行机制，又称双主模式。MIX场景（包含矩阵计算和矢量计算）下AIC核和AIV核独立运行代码，不依赖消息驱动。</td></tr><tr><td>MxMatmul场景</td><td>带有量化系数的矩阵乘法，即左矩阵和右矩阵均有对应的量化系数矩阵，对左矩阵和右矩阵分别量化后再做矩阵乘计算。</td></tr></table>


表 3-5 BatchMatmu 功能 l 特性表


<table><tr><td>特性描述</td><td>功能简介</td></tr><tr><td>Batch Matmul基础功能</td><td>Batch Matmul基础功能，支持批量处理Matmul，调用一次 IterateBatch接口，计算出多个singleCoreM * singleCoreN大小的C矩阵。</td></tr><tr><td>Batch Matmul复用Bias矩阵</td><td>每个Batch的Matmul计算复用同一个不带Batch轴的Bias矩阵。</td></tr></table>

# 3.3.3.3.2 多核对齐切分

# 功能介绍

为了实现多核并行，提升计算效率，需要将矩阵数据进行切分，分配到不同的核上进 行处理。主要的切分策略有切分K轴和不切分K轴两种。 

不切分K轴、仅切分M、N轴的策略如下： 

对于A矩阵，沿着M轴进行切分，切分成多份的singleCoreM，单核上处理 SingleCoreM * K大小的数据。 

对于B矩阵，沿着N轴进行切分，切分成多份的singleCoreN，单核上处理K * SingleCoreN大小的数据。 

对于C矩阵，SingleCoreM * K大小的A矩阵和K * SingleCoreN大小的B矩阵相乘得 到SingleCoreM * SingleCoreN大小的C矩阵，即为单核上输出的C矩阵大小。 

比如，下图中共有8个核参与计算，将A矩阵沿着M轴划分为4块，将B矩阵沿着N轴切 分为两块，单核上仅处理某一分块（比如图中绿色部分为core5上参与计算的数据）： SingleCoreM * K大小的A矩阵分块和SingleCoreN * K大小的B矩阵分块相乘得到 SingleCoreM * SingleCoreN大小的C矩阵分块。 

![](images/6cb191a780a17de15930b71656794a56f9917c2d0cb08d55373188641f77905f.jpg)



矩阵A


![](images/0f7290c7858fbaa5e78e4da91fee07b0b713a76c32ca2d1b035e791d0ee54a25.jpg)


![](images/d13ca1c8d027544744f635e4d2940ebc92159c43db4f6d3bd3cd8ca73652a741.jpg)



矩阵B


![](images/bdc085321875d156e406fe6f7518627b26f319b9902b5ecea800722986ffd097.jpg)


![](images/251feca3ca07efb0e6557c9f88b940ae9576c9d4897d520929ddc9776b673826.jpg)



矩阵c


切分M、N、K轴的策略如下图所示： 

对于A矩阵，沿着M轴进行切分，切分成多份的singleCoreM，沿着K轴切分，切 分成多份的singleCoreK，单核上处理singleCoreM * singleCoreK大小的数据。 

对于B矩阵，沿着K轴进行切分，切分成多份的singleCoreK，沿着N轴进行切分， 切分成多份的singleCoreN，单核上处理singleCoreK * singleCoreN大小的数据。 

对于C矩阵，singleCoreM * singleCoreK大小的A矩阵与singleCoreK * singleCoreN大小的B矩阵相乘并累加得到singleCoreM * singleCoreN大小的C矩阵 分块。 

比如下图中，C矩阵中的R矩阵块，是通过A1*B1+A2*B2+A3*B3累加得到的，其中， A1*B1、A2*B2、A3*B3可在多个核上并行计算。 

![](images/6736d29d6bec249ff70049fe6f9270bbc176b38f420b1305118f4c7fa95d93ef.jpg)



矩阵A


![](images/780a2b731f484ca5332b24f41cf0824b839e8f219fae37c20a093fec7e4e5601.jpg)


![](images/ddee2ce7ceda2c7b5115662c04da1680f27bbd1d071cce40f9d22e27c361cb3c.jpg)


![](images/55a77244ef685b86be9cd23384454e6557df40ef18b56eab39a27f772fa39d85.jpg)



矩阵B



矩阵c


上述的切分策略会在Tiling参数中体现，比如SingleCoreM、SingleCoreN、 SingleCoreK，开发者在host侧通过调用API自动获取Tiling参数，与单核场景的不同的 是，多核Tiling需要使用MultiCoreMatmulTiling构造多核Tiling对象，并通过SetDim 接口设置Matmul计算所用的核数。注意：这里设置的核数为Matmul计算可用的核 数，仅在多核场景下设置，用于计算tiling参数；SetBlockDim为整个算子计算所用核 数，是实际会加载的核数，是必须设置的。SetBlockDim的设置规则请参考 numBlocks的说明。SetDim的设置规则如下： 

纯Cube模式（只有矩阵计算）场景，本节内容以纯Cube模式举例。 

SetDim设置当前AI处理器可用的核数，通过Tiling计算得到执行Matmul计算实际 使用的核数，实际使用的核数小于等于AI处理器可用的核数。SetBlockDim按照实 际使用的核数由用户进行配置。 

MIX模式（包含矩阵计算和矢量计算）的设置规则请参考MIX场景核数设置规则。 

# 使用场景

多核处理Matmul矩阵计算场景。 

# 约束说明

无 

# 调用示例

该场景的关键代码示例如下。Matmul多核对齐场景的完整样例请参考：多核切M、N 的样例：Matmul多核Kernel直调样例；多核切K的样例：多核切K场景的算子样例。 

```rust
//构造多核Tiling对象  
auto ascendcPlatform = platform ascendc::PlatformAscendCManager::GetInstance(socVersion);matmul_tiling::MultiCoreMatmulTiling cubeTiling(* ascendcPlatform);  
//仅包含Cube计算的算子，设置可参与矩阵乘运算的核数为当前AI处理器上的Cube核数  
cubeTiling.SetDim(ascendingPlatform.GetCoreNumAic());  
cubeTiling.setType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND,matmul_tiling::DataType::DT_FLOAT16);  
cubeTiling.setType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND,matmul_tiling::DataType::DT_FLOAT16);  
cubeTiling.setType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND,matmul_tiling::DataType::DT_FLOAT16);  
cubeTiling.setBiasType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND,matmul_tiling::DataType::DT_FLOAT16);  
cubeTiling.setOrgShape(M, N, K);  
cubeTiling.setShape(M, N, K);  
cubeTiling EnableBias(isBias);  
optiling::TCubeTiling tilingData;  
//获取Tiling参数  
int ret = cubeTiling.GetTiling(tilingData); //if ret = -1, gen tiling failed 
```

# 3.3.3.3.3 多核非对齐切分

# 功能介绍

多核场景，对矩阵进行切分时，若M、N、K无法整除singleCoreM 、singleCoreN、 singleCoreK时，就会出现尾块，即多核非对齐场景。如下图矩阵A、B的最后一行和最 后一列的矩阵块： 

![](images/e0fa9964581d7d866e02a53e97027ad09d13d51b5edb740edc3a01fafc4febeb.jpg)



矩阵A


![](images/adeb5b1f6da25c34c889abbd1aa2cae162ed89dceaacfa4ebccdc142ee62a0e5.jpg)



矩阵B



矩阵c


此时，C矩阵中的R矩阵块，依然是通过A1*B1+A2*B2+A3*B3+A4*B4累加得到的，处 理A1*B1、A2*B2、A3*B3、A4*B4等尾块时，需在kernel侧设置尾块大小，在不改变原 有tiling的情况下，调用SetTail接口重新设置本次计算的singleCoreM/singleCoreN/ singleCoreK，在处理尾块的时候按照设置的值也就是tailM/tailN/tailK进行搬运和计 算。 

# 使用场景

多核处理Matmul矩阵计算，存在尾块的场景。 

# 约束说明

处理尾块调用的SetTail接口，需要在Iterate/IterateAll之前调用。 

# 调用示例

Matmul多核非对齐场景的完整样例请参考Matmul多核非对齐切分算子样例。该场景 的关键代码示例如下。 

```javascript
// 处理尾块  
int tailM = tiling.M - mCoreIndex * tiling.singleCoreM;  
tailM = tailM < tiling(singleCoreM ? tailM : tiling.singleCoreM;  
int tailN = tiling.N - nCoreIndex * tiling.singleCoreN;  
tailN = tailN < tiling.singleCoreN ? tailN : tiling.singleCoreN;  
// 当tailM < singleCoreM 或 tailN < singleCoreN时被认为需要处理尾块，此时可以调用SetTail接口进行设置  
if (tailM < tilingsingleCoreM || tailN < tiling.singleCoreN) {matmulObj.SetTail(tailM, tailN);} 
```

# 3.3.3.3.4 异步场景处理

# 功能介绍

Matmul的Iterate和IterateAll接口在MIX场景（包含矩阵计算和矢量计算）下提供了同 步和异步两种模式，纯Cube场景（只有矩阵计算）下，只支持同步模式。 

同步模式指的是程序执行时，需要等待某个操作完成后才能继续执行下一步操作。 异 步模式指的是程序执行时，不需要等待某个操作完成就可以继续执行下一步操作。 

Iterate&GetTensorC的同步和异步 

同步：执行完一次Iterate迭代计算后，执行GetTensorC搬运矩阵C分片，搬 运完成后，才能进行下一次计算。如下图所示，C矩阵中，矩阵块1搬走后， 才能计算矩阵块2，矩阵块2搬运完成后，才能计算矩阵块3。 

![](images/035eb4229134b314080eca5cba8886db44da70ca41ebf4d104b433f431898eff.jpg)


![](images/1a4f6a4babde144a78d6b66c58a234967c3e2eb8b1440a1783e5128a5e50c1e1.jpg)



=


![](images/fdcb92e1ba1610941343c20a80407a923c2e436ad31e115dbb930b300db9570e.jpg)


Iterate&GetTensorC同步模式的关键代码示例如下： 

```javascript
while (mm.Iterate()) { mm.GetTensorC(gm_c); } 
```

异步：通过设置Iterate接口的模板参数开启异步模式。调用Iterate后，无需 立即调用GetTensorC同步等待矩阵C分块搬运完成，可以先执行其它操作， 待需要获取结果时再调用GetTensorC。异步模式可以减少同步等待，提高并 行度，开发者对计算性能要求较高时，可以选用该方式。异步场景时，需要 使用一块临时空间来缓存Iterate计算结果，否则会覆盖计算结果，调用 GetTensorC时会在该临时空间中获取C的矩阵分片。临时空间通过 SetWorkspace接口进行设置。SetWorkspace接口需要在Iterate接口之前调 用。 

Iterate&GetTensorC异步模式的关键代码示例如下：  
mm.SetWorkspace workspace,size); //其中，workspace为临时空间的物理地址，size为singleCoreM \* singleCoreN的矩阵C大小//异步模式  
mm.template Iteratefalse>();  
……//执行其他操作  
auto mIter $=$ Ceil(singleCoreM,baseM);  
auto nIter $=$ Ceil(singleCoreN,baseN);  
for (int i = 0; i < mIter \* nIter ; ++i) {mm.GetTensorCfalse>(gm_c);} 

IterateAll的同步和异步 

同步：后续操作需要同步等待IterateAll执行结束。 

IterateAll同步模式的关键代码示例如下： 

```txt
mm.SetTensorA(gm_a); //设置左矩阵A  
mm.SetTensorB(gm_b); //设置右矩阵B  
mm.SetBias(gm.bias); //设置Bias  
mm.IterateAll(gm_c); //后续操作 
```

异步：后续操作不需要同步等待IterateAll执行结束，需要IterateAll的结果 时，调用WaitIterateAll等待IterateAll异步接口返回。 

IterateAll异步模式的关键代码示例如下： 

```cpp
AscendC::Matmul<aType, bType, cType, biasType> mm;  
mm.SetTensorA(queryGm[tensorACoreOffset]);  
mm.SetTensorB(keyGm[tensorBCoreOffset + slnnerStart * singleProcessSLinnerSize * tilingData->attentionScoreOffsetStrideParams.matmulHead], true);  
mm.setTail(singleProcessSOuterSize, mmNNum);  
mm.template IterateAll(false>(workspaceGm[tmp_block_idx * mmResUbSize * slnnerLoopTimes], 0, false, true);  
//执行其他操作  
mm.WaitIterateAll(); //等待IterateAll完成  
DataCopy.dstUB, GM); //进行GM到UB的拷贝 
```

# 使用场景

Iterate&GetTensorC的同步：MIX场景（包含矩阵计算和矢量计算）、纯Cube场 景（只有矩阵计算）。 

Iterate&GetTensorC的异步：仅MIX场景（包含矩阵计算和矢量计算）。 

IterateAll的同步：MIX场景（包含矩阵计算和矢量计算）、纯Cube场景（只有矩 阵计算）。 

IterateAll的异步：仅MIX场景（包含矩阵计算和矢量计算）。 

# 约束说明

Iterate&GetTensorC的异步场景： 

传入的C矩阵地址空间大小需要保证不小于baseM * baseN。 

SetWorkspace接口需要在Iterate接口之前调用。 

支持只输出到VECIN、只输出到Global Memory，同时输出到Global Memory和VECIN三种输出方式。 

取出C矩阵到VECIN时，数据格式仅支持NZ；取出C矩阵到GM时，数据格式 支持ND或NZ。 

IterateAll的异步场景： 

– 传入的C矩阵地址空间大小需要保证不小于singleCoreM * singleCoreN。 

仅支持连续输出至Global Memory。 

# 调用示例

Iterate&GetTensorC的异步场景的完整样例请参考异步场景样例、Iterate异步场 景样例。 

IterateAll的异步场景的完整样例请参考IterateAll异步场景样例。 

# 3.3.3.3.5 矩阵乘输出的量化/反量化

# 功能介绍

对于特定输入输出数据类型，Matmul支持将计算结果从CO1搬出到Global Memory 时，对输出C矩阵元素执行数据量化或反量化操作。 

Matmul量化场景：Matmul计算时左矩阵A、右矩阵B为half或bfloat16_t数据类 型，输出C矩阵为int8_t数据类型。该场景下，C矩阵的数据从CO1搬出到Global Memory时，会执行量化操作，将最终结果量化为int8_t类型，如下图所示。 


图 3-32 Matmul 量化场景示意图


![](images/6aa873194ee1cd4c1ab73a3e5fd99400bc2df7e68ae920c5a6d60353c2038943.jpg)


Matmul反量化场景：Matmul计算时左矩阵A、右矩阵B为int8_t或int4b_t数据类 型，输出C矩阵为half数据类型，或者左矩阵A、右矩阵B为int8_t数据类型，输出 C矩阵为int8_t数据类型。该场景下，C矩阵的数据从CO1搬出到Global Memory 时，会执行反量化操作，将最终结果反量化为对应的half类型或int8_t类型，如下 图所示。 


图 3-33 Matmul 反量化场景示意图


![](images/ea5725c6cd2d11a884c97ef1b7d3eb9217a314cf1156477c8daf352dc89f834a.jpg)


Matmul量化/反量化包含两种模式：同一系数的量化/反量化模式、向量的量化/反量化 模式，开发者在算子Tiling侧调用SetDequantType接口设置量化或反量化模式，这两 种模式的具体区别为： 

同一系数的量化/反量化模式（PER_TENSOR模式）：整个C矩阵对应一个量化参 数，量化参数的shape为[1]。开发者在算子Kernel侧调用接口SetQuantScalar设 置量化参数。 

向量的量化/反量化模式（PER_CHANNEL模式）：C矩阵的shape为[m, n]，每个 channel维度即C矩阵的每一列，对应一个量化参数，量化参数的shape为[n]。开 发者在算子Kernel侧调用接口SetQuantVector设置量化参数。 


表 3-6 量化/反量化模式对应的接口配置


<table><tr><td>模式</td><td>Tiling侧接口</td><td>Kernel侧接口</td></tr><tr><td>同一系数的量化/反量化</td><td>SetDequantType(DequantType::SCALAR)</td><td>SetQuantScalar(gmScalar)</td></tr><tr><td>向量的量化/反量化</td><td>SetDequantType(DequantType::TENSOR)</td><td>SetQuantVector(gmTensor)</td></tr></table>

# 使用场景

需要对矩阵计算结果进行量化/反量化操作的场景，当前该场景下，Matmul输入输出 矩阵支持的数据类型如下表所示。 


表 3-7 Matmul 量化/反量化支持的数据类型


<table><tr><td>A矩阵</td><td>B矩阵</td><td>C矩阵</td><td>支持平台</td></tr><tr><td>half</td><td>half</td><td>int8_t</td><td>Atlas 350 加速卡
Atlas A3 训练系列产品/Atlas A3
推理系列产品
Atlas A2 训练系列产品/Atlas A2
推理系列产品</td></tr><tr><td>bfloat16_t</td><td>bfloat16_t</td><td>int8_t</td><td>Atlas 350 加速卡
Atlas A3 训练系列产品/Atlas A3
推理系列产品
Atlas A2 训练系列产品/Atlas A2
推理系列产品</td></tr><tr><td>int8_t</td><td>int8_t</td><td>half</td><td>Atlas 350 加速卡
Atlas A3 训练系列产品/Atlas A3
推理系列产品
Atlas A2 训练系列产品/Atlas A2
推理系列产品</td></tr><tr><td>int4b_t</td><td>int4b_t</td><td>half</td><td>Atlas A3 训练系列产品/Atlas A3
推理系列产品
Atlas A2 训练系列产品/Atlas A2
推理系列产品</td></tr><tr><td>int8_t</td><td>int8_t</td><td>int8_t</td><td>Atlas 350 加速卡
Atlas A3 训练系列产品/Atlas A3
推理系列产品
Atlas A2 训练系列产品/Atlas A2
推理系列产品</td></tr><tr><td>int8_t</td><td>int8_t</td><td>bfloat16_t</td><td>Atlas 350 加速卡</td></tr><tr><td>fp8_e4m3fn_t/ fp8_e5m2_t</td><td>fp8_e4m3fn_ t/fp8_e5m2_t</td><td>fp8_e4m3f n_t/half/ bfloat16_t/ float</td><td>Atlas 350 加速卡</td></tr><tr><td>hifloat8_t</td><td>hifloat8_t</td><td>hifloat8_t/ half/ bfloat16_t/ float</td><td>Atlas 350 加速卡注意:输出为hifloat8_t时,采用Half to Away Round方式量化。量化场景的输出为float类型时,该量化模式精度无法达到双万分之一,可以达到双千分之一。如果有双万分之一的精度要求,建议使用 AscendDeQuant高阶API。</td></tr></table>

# 约束说明

● SetQuantScalar和SetQuantVector接口必须在Iterate或者IterateAll接口前调用。 

在Kernel侧与Tiling侧设置的量化/反量化模式需要保持一致： 

Kernel侧调用SetQuantScalar接口设置同一系数的量化/反量化模式，对应 Tiling侧调用SetDequantType接口配置模式为DequantType::SCALAR。 

Kernel侧调用SetQuantVector接口设置向量的量化/反量化模式，对应Tiling 侧调用SetDequantType接口配置模式为DequantType::TENSOR。 

当A、B矩阵为int8_t或int4b_t类型，C矩阵为half时，本节特性的输出结果不支持 INF_NAN模式。若结果需要以INF_NAN输出，建议在调用Matmul API时将结果 输出到TPosition::VECIN，同时将输出的数据类型设置为int32_t，再基于AIV核使 用高阶API AscendDequant将该结果反量化为half类型。 

# 调用示例

完整的算子样例请参考matmul_quant样例。 

Tiling实现 

调用SetDequantType接口设置量化或反量化模式，其他实现内容与基础场景相 同。 

auto ascendcPlatform $=$ platform_ascendc::PlatformAscendC(context->GetPlatformInfo()); 

matmul_tiling::MatmulApiTiling tiling(ascendcPlatform); 

tiling.SetAType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND, matmul_tiling::DataType::DT_INT8); 

tiling.SetBType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND, matmul_tiling::DataType::DT_INT8); 

tiling.SetCType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT16); 

tiling.SetBiasType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND, matmul_tiling::DataType::DT_INT32); 

tiling.SetShape(M, N, K); 

tiling.SetOrgShape(M, N, K); 

tiling.EnableBias(true); 

tiling.SetDequantType(DequantType::SCALAR); // 设置同一系数的量化/反量化模式 

// tiling.SetDequantType(DequantType::TENSOR); // 设置向量的量化/反量化模式 

... // 执行其他配置 

# Kernel实现

根据具体量化模式场景，调用SetQuantScalar或SetQuantVector接口设置量化参 数。其他实现内容与基础场景相同。 

# 同一系数的量化/反量化模式

```cpp
REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm, &tiling);  
float tmp = 0.1; // 输出gm时会乘以0.1  
uint64_t ans = static_cast<uint64_t>(*reinterpret_cast<int32_t*)(&tmp)); // 浮点值量化系数转换为  
uint64_t类型进行设置  
mm.SetQuantScalar(ans);  
mm.SetTensorA(gm_a);  
mm.SetTensorB(gm_b);  
mm.SetBias(gm.bias);  
mm.IterateAll(gm_c); 
```

# 向量的量化/反量化模式

```txt
GlobalTensor gmQuant;   
...   
REGIST_MATMUL_OBJ(&pipe,GetSysWorkSpacePtr(),mm,&tiling);   
mm.SetQuantVector(gmQuant);   
mm.SetTensorA(gm_a);   
mm.SetTensorB(gm_b);   
mm.SetBias(gm.bias);   
mm.IterateAll(gm_c); 
```

# 3.3.3.3.6 矩阵乘输出的 Channel 拆分

# 功能介绍

矩阵乘输出的Channel拆分，又称ChannelSplit。指当Matmul计算结果C矩阵的格式为 NZ时，C矩阵采用分形存储，关于NZ格式的详细内容请参考数据格式。当C矩阵的物 理排布格式为NZ、数据类型为float时，默认情况下，每个分形内部包含16*16个元 素，即分形的大小为16*16。ChannelSplit的功能为将此场景下C矩阵的每个16*16的分 形切分为16*8的分形，使得C矩阵按照16*8的分形进行存储。 

由于1个float类型数据的大小为4字节，16*8的分形在内轴满足32字节对齐，内轴上的 数据量与一条NPU矢量计算指令处理的数据单元一致，这便于后续的其它计算。 ChannelSplit功能默认不启用，用户需通过设置MatmulConfig中的 isEnableChannelSplit参数为true来开启此功能。 


图 3-34 ChannelSplit 功能示意图


![](images/4f454959db4ec10a05995b162db2a10a164695b69191cf566652e2cb05838206.jpg)


![](images/c1913c8bc780dedaf14a18ed817c40686b26abb0fd6677385a19fd50cb5f3a3d.jpg)


# 使用场景

对于NZ格式、float类型的C矩阵，需要按 $1 6 ^ { \star } 8$ 的分形存储时，使用该功能。 

# 约束说明

开启ChannelSplit功能需满足： 

C矩阵的数据排布格式为CubeFormat::NZ。 

C矩阵的数据类型为float。 

C矩阵的内存逻辑位置为Global Memory。 

矩阵乘结果CO1数据类型为float。 

# 调用示例

完整的算子样例请参考matmul_channelsplit算子样例。 

```cpp
//指定获取和修改的MatmulConfig模板  
constexpr static MatmulConfigMode configMode = MatmulConfigMode::CONFIG_NORM;  
//修改模板参数EnableChannelSplit=true，开启该MatmulConfig模板的ChannelSplit功能  
constexpr static MatmulFuncParams funcParamsChannelSplit{  
    false, false, false, false, 0, IterateOrder::ORDER_M, ScheduleType::INNER_PRODUCT, true, false, false, false, true/*isEnableChannelSplit*/  
};  
constexpr static MatmulConfig MM_CFG = GetMMConfig<configMode>(funcParamsChannelSplit);  
Matmul<A_TYPE, B_TYPE, C_TYPE, BIAS_TYPE, MM_CFG> mm;  
//常规Matmul计算，最后输出分形为16*8  
REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm);  
mm.SetTensorA(gm_a);  
mm.SetTensorB(gm_b);  
mm.SetBias(gm.bias);  
mm.IterateAll(gm_c); 
```

# 3.3.3.3.7 矩阵向量乘

# 功能介绍

矩阵向量乘（General Matrix-Vector multiplication），即GEMV，是指Matmul计算 中M=1，形状为(1, K)的左矩阵A与形状为(K, N)的右矩阵B进行矩阵乘运算的场景。 Matmul支持在Tiling侧与Kernel侧通过配置A矩阵的数据格式为VECTOR来开启GEMV 模式，从而高效处理M=1的计算场景。若在M=1时未开启GEMV模式，Matmul计算则 将M方向作为非对齐场景进行处理。GEMV模式相较于非对齐处理方式，搬运数据量更 少，性能更好。 

以M=1，K=256，N=32，左右矩阵数据类型为half的Matmul为具体示例，说明GEMV 模式的Matmul API内部处理过程。 

GEMV模式 

将A矩阵从A1搬运到A2时，1*256的向量被当作16*16的矩阵进行处理，调用 LoadData接口一次完成16*16分形大小的矩阵搬运。B矩阵的搬运以及矩阵乘计算 跟基础场景相同，如下图所示。 


图 3-35 GEMV 模式 $\mathsf { M } = \mathsf { 1 }$ 的矩阵乘计算示意图


![](images/3b23ee57065a627110e375f3a895deec33fd71826fb5068dfb1ac9447a8a2bce.jpg)


非GEMV模式 

将A矩阵从A1搬运到A2时，1*256的向量被当作非对齐矩阵数据进行处理，将M方 向对齐到32字节后进行搬运。调用LoadData接口每次搬运16*16分形大小的矩 阵，一共搬运K/16=16次，导致搬运数据量增加，性能相较于GEMV模式差，如下 图所示。 


图 3-36 非 GEMV 模式 M=1 的矩阵乘计算示意图


![](images/ed8257aafe68ade42c4127624dd2210c1fd2ad6c6400a47ae8a3fafe33f06eb0.jpg)


# 使用场景

形状为(1, K)的A矩阵（ $\mathsf { M } = \mathsf { 1 }$ ，K>1）做矩阵乘计算，即输入A矩阵的数据是向量数据。 

# 约束说明

在Matmul计算中，若要开启GEMV模式，A矩阵的原始输入形状M必须等于1。 

GEMV场景下，左矩阵A不支持转置。 

GEMV场景下，Global Memory上的左矩阵数据需要保证16字节对齐。 

MxMatmul场景计算矩阵向量乘时，左矩阵A和左量化系数矩阵scaleA仅支持内 存逻辑位置为TPosition::GM。 

# 调用示例

完整的算子样例请参考matmul_gemv算子样例。 

# Tiling实现

调用SetAType接口，设置A矩阵的数据格式为CubeFormat::VECTOR，其它Tiling 实现与基础场景相同。 

```txt
auto ascendcPlatform = platform_ascending::PlatformAscendC(context->GetPlatformInfo());  
matmul_tiling::MatmulApiTiling(ascendingPlatform);  
// 调用设置A矩阵的格式为CubeFormat::VECTOR  
tiling.SetATOType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::VECTOR,  
matmul_tiling::DataType::DT_FLOAT16);  
tiling.SetBType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND,  
matmul_tiling::DataType::DT_FLOAT16);  
tiling.SetCType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND,  
matmul_tiling::DataType::DT_FLOAT);  
tiling.SetBiasType(AscendC::TPosition::GM, matmul_tiling::CubeFormat::ND,  
matmul_tiling::DataType::DT_FLOAT);  
... // 其他实现内容  
optiling::TCubeTiling tilingData;  
int ret = tiling.GetTiling(tilingData); 
```

# Kernel实现

相较于基础场景，GEMV场景在创建Matmul对象时，设置模板参数A_TYPE的数 据格式为CubeFormat::VECTOR。 

include"lib/matmul_intf.h"   
usingA_TYPE $\equiv$ AscendC::MatmulType<AscendC::TPosition::GM,CubeFormat::VECTOR, half>;   
usingB_TYPE $=$ AscendC::MatmulType<AscendC::TPosition::GM,CubeFormat::ND, half>;   
usingC_TYPE $=$ AscendC::MatmulType<AscendC::TPosition::GM,CubeFormat::ND, float>;   
usingBIAS_TYPE $\equiv$ AscendC::MatmulType<AscendC::TPosition::GM,CubeFormat::ND, float>;   
AscendC::Matmul<A_TYPE,B_TYPE,C_TYPE,BIAS_TYPE>mm; 

# 3.3.3.3.8 4:2 稀疏矩阵乘

# 功能介绍

4:2稀疏矩阵乘，又称Sparse Matmul。该场景下输入的原始左矩阵A、右矩阵B为稀疏 矩阵，稀疏矩阵B中每4个元素中至少有2个为零元素；在进行Matmul计算前，用户需 要自行对B矩阵进行4：2稠密化，即基于原始稀疏矩阵B在每4个元素中过滤掉2个零元 素，使B矩阵稠密化为稠密矩阵；Sparse Matmul场景调用Matmul API完成A矩阵与 4:2稠密化后的B矩阵的矩阵乘计算。Sparse Matmul可以跳过稀疏矩阵B中的零元素， 仅对非零元素进行数据搬运存储和计算，从而减少矩阵乘计算时的内存占用和计算 量，提升性能。 

# 实现流程

# 步骤1 数据预处理

在计算前的数据准备阶段，用户自行对原始为稀疏矩阵的B矩阵完成稠密化，稠密过程 请参考稠密算法说明。稠密化过程结束后，得到4:2稠密化后的右矩阵B和索引矩阵 index，稠密化后的右矩阵B和索引矩阵index将作为Sparse Matmul场景的计算输入。 


图 3-37 对原始稀疏矩阵 B 进行 4:2 稠密化过程示意图


![](images/77045ee0d662ca5d3ab7da82ea7f79ee30ea9b3e49dd8290f9b7a87d64abdba8.jpg)


稠密化过程对于稀疏矩阵B的每4个元素，在索引矩阵index中生成2个2位索引，每个索 引分别指向对应非零元素的相对位置，具体规则可参考稠密算法说明。稠密化过程生 成的索引矩阵的数据类型为int2，索引矩阵在加载入Matmul前，需要拼成int8的数据 类型。索引矩阵在一个int8的地址中的排布是逆序排布的，例如：索引矩阵1 2 0 1 0 2 1 0，在地址中的排布为1 0 2 1 0 1 2 0，其中1 0 2 1（对应索引矩阵前四位1 2 0 1） 为一个int8，0 1 2 0（对应索引矩阵后四位0 2 1 0）为一个int8。 

# 步骤2 使能Sparse Matmul场景

在Host侧，获取Tiling前需要通过SetSparse接口设置使能Sparse Matmul场景。 

```txt
auto ascendcPlatform = platform ascendc::PlatformAscendC(context->GetPlatformInfo());  
matmul_tiling::MatmulApiTiling tiling(ascendcPlatform);  
tiling.SetATOType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND,  
matmul_tiling::DataType::DT_INT8);  
tiling.SetBType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND,  
matmul_tiling::DataType::DT_INT8);  
tiling.SetCTType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND,  
matmul_tiling::DataType::DT_INT32);  
tiling.SetBiasType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND,  
matmul_tiling::DataType::DT_INT32);  
//设置使能Sparse Matmul场景  
tiling.SetSparse(true);  
//其他实现内容  
optiling::TCubeTiling tilingData;  
int ret = tiling.GetTiling(tilingData); 
```

# 步骤3 创建Matmul对象

在Kernel侧创建Matmul对象时，通过MatmulType定义A、C、Bias的参数类型信息， 包括：内存逻辑位置、数据格式、数据类型。通过SparseMatmulType类型定义B矩 阵的参数类型，包括：B矩阵的内存逻辑位置、索引矩阵的内存逻辑位置、数据格式、 数据类型等。 

include"lib/matmul_intf.h"   
usingA_TYPE $\equiv$ AscendC::MatmulType<AscendC::TPosition::GM,CubeFormat::ND,ATYPE,false>; //使用SparseMatmulType定义B矩阵的参数类型信息   
usingB_TYPE $\equiv$ AscendC::SparseMatmulType<AscendC::TPosition::GM,AscendC::TPosition::GM, CubeFormat::ND,BType, true>;   
usingC_TYPE $\equiv$ AscendC::MatmulType<AscendC::TPosition::GM,CubeFormat::ND,CType>;   
usingBIAS_TYPE $\equiv$ AscendC::MatmulType<AscendC::TPosition::GM,CubeFormat::ND,BiasType>; AscendC::Matmul<A_TYPE,B_TYPE,C_TYPE,BIAS_TYPE,CFG_MDL $>$ mm; 

# 步骤4 设置索引矩阵

通过SetSparseIndex接口传入稠密化过程中生成的索引矩阵。 

```javascript
mm.SetTensorA(gm_a); //设置左矩阵A  
mm.SetTensorB(gm_b); //设置右矩阵B  
mm.setSparseIndex(gm_index); //传入稠密化过程中生成的索引矩阵  
mm.setBias(gm.bias); //设置Bias 
```

# 步骤5 完成矩阵乘操作

在Kernel侧，基于步骤4加载的索引矩阵，完成矩阵乘操作。Matmul API内部完成对A 矩阵的稠密化，即根据索引矩阵从A矩阵的每4个元素中，选择2个对应位置元素参与计 算。 

```javascript
//调用Iterate和GetTensorC或IterateAll接口完成矩阵乘计算  
while (mm.Iterate()) {  
    mm.GetTensorC(gm_c);  
}  
//mm.IterateAll(gm_c);  
mm.End(); 
```

----结束 

# 参数说明


表 3-8 SparseMatmulType 类型参数说明


<table><tr><td>参数</td><td>说明</td></tr><tr><td>POSITION</td><td>内存逻辑位置。
B矩阵仅支持设置为TPosition::GM。</td></tr><tr><td>INDEX_POSI
ON</td><td>索引矩阵内存逻辑位置。
仅支持设置为TPosition::GM。</td></tr><tr><td>CubeFormat</td><td>数据的物理排布格式，详细介绍请参考数据格式。
B矩阵支持设置为CubeFormat::ND，CubeFormat::NZ。</td></tr><tr><td>TYPE</td><td>B矩阵仅支持设置为int8_t数据类型。</td></tr><tr><td>ISTRANS</td><td>是否开启使能矩阵转置的功能。
当前只支持取值为true，表示开启使能矩阵转置的功能。</td></tr><tr><td>LAYOUT</td><td>表征数据的排布。Sparse Matmul场景仅支持取值为
LAYOUT::NONE。
NONE: 默认值，表示不使用BatchMatmul。</td></tr><tr><td>IBSHARE</td><td>是否使能IBShare（IntraBlock Share）。IBShare的功能是能够复用L1 Buffer上相同的A矩阵或B矩阵数据。当A矩阵和B矩阵同时使能IBShare时，表示L1 Buffer上的A矩阵和B矩阵同时复用。
Sparse Matmul场景当前仅支持该参数取值为false，表示不使能IBShare。</td></tr></table>

# 使用场景

左矩阵A为稀疏矩阵、右矩阵B为4:2稠密化后的矩阵的Matmul计算场景。 

# 约束说明

该场景仅支持MDL模板下的纯Cube模式（只有矩阵计算）。 

通过SetSparseIndex接口传入的索引矩阵只支持int8数据类型和NZ数据排布格 式。 

原始稀疏矩阵B中每4个元素中应保证最多2个非零元素（即最少2个零元素），如 果存在3个或更多非零元素，则仅使用前2个非零元素。 

M、K、N中的任意一个值不能为0。 

# 调用示例

Sparse Matmul场景的完整样例请参考Sparse Matmul场景的算子样例。 

# 3.3.3.3.9 TSCM 输入的矩阵乘

# 功能介绍

TSCM表示L1 Buffer空间对应的逻辑内存，L1 Buffer相关内容见存储单元，开发者可 以自行管理TSCM以高效利用硬件资源。比如，开发者可缓存一份TSCM数据，在不同 使用场景中灵活配置为Matmul操作的A矩阵、B矩阵或Bias偏置矩阵，实现内存复用与 计算效率优化。在TSCM输入场景，用户管理整块TSCM内存空间，Matmul直接使用 传入的TSCM内存地址，不进行Global Memory到TSCM的数据搬入。 

# 使用场景

用户需要自定义数据搬入到TSCM及自定义管理的场景，即需要自定义实现数据搬入功 能，如非连续搬入或对搬入数据进行预处理等。用户通过自定义管理TSCM可灵活配置 MTE2流水，实现跨Matmul对象的全局DoubleBuffer，MTE2相关内容见搬运单元。 

# 约束说明

设置为TSCM输入的矩阵必须在TSCM中全载，全载即全部的矩阵数据同时搬入及保持 在TSCM中。 

# 调用示例

完整的算子样例请参考自定义数据来源为GM的TSCM输入的Matmul算子样例、 BatchMatmul自定义TSCM输入的算子样例。 

```cpp
TQue<TPosition::A1, 1> scm; // 队列逻辑位置A1，队列深度为1  
pipe->InitBuffer(scm, 1, tiling.M * tiling.Ka * sizeof(A_T));  
// A_TYPE的TPosition为TSCM，B_TYPE的TPosition为GM  
Matmul<A_TYPE, B_TYPE, C_TYPE, BIAS_TYPE> mm1;  
REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm1);  
mm1 Init(&tiling);  
// 自定义A矩阵GM到TSCM的搬运  
auto scmTensor = scm AllocTensor<A_T>();  
DataCopy(scmTensor, gm_a, tiling.M * tiling.Ka);  
scm.EnQue(scmTensor);  
LocalTensor<A_T> scmLocal = scm.DeQue<A_T>();  
// A矩阵设置为TSCM输入，B矩阵为GM输入  
mm1.SetTensorA(scmLocal);  
mm1.SetTensorB(gm_b);  
mm1.SetBias(gm.bias);  
mm1.IterateAll(gm_c);  
scm.FreeTensor(scmLocal); 
```

# 3.3.3.3.10 矩阵乘输出的 N 方向对齐

# 功能介绍

矩阵乘输出的N方向对齐，即矩阵乘结果C矩阵按ND_ALIGN格式输出。在Matmul矩 阵乘法中，常用的矩阵数据格式有ND、NZ，相关介绍可参考数据格式章节。 ND_ALIGN是矩阵的另一种数据格式，该格式一般用于N方向非32字节对齐的矩阵乘计 算中，配置结果C矩阵为ND_ALIGN格式后，将按照N方向32字节对齐的补齐规则输出 C矩阵，详细内容请见ND_ALIGN。 

以M=16，K=16，N=14，A、B矩阵数据类型为half的Matmul为具体示例，说明 ND_ALIGN输出功能。当配置C矩阵为ND格式并输出到Global Memory时，按照原始 N方向大小非32字节对齐输出如图3-38所示。当配置C矩阵为ND格式时，按照N方向 32字节对齐输出如图3-39所示，C矩阵的N方向最后两列由下一行的实际数据进行填充 补齐，以实现N方向对齐到32字节并输出。当配置C矩阵为ND_ALIGN格式时， Matmul API会在C矩阵的N方向上通过添加无效数据来填充最后两列，以确保N方向对 齐至32字节并输出，如图3-40所示。 


图 3-38 ND 格式 C 矩阵 N 方向非 32 字节对齐示意图


![](images/28df380faa78f329b3292493ab53727a32044571b2fb63af8009da028ac0889c.jpg)


![](images/6f70ab7937f30cf72b4b1b961bc00e22a4ba873c41b17632698d209a9d32ec2c.jpg)


![](images/429ab7ae8175d1146f4dd27ae9753cef245e79325564954c918be26ecf1a1a08.jpg)


![](images/c42a3caa31207a35c6efc738ca13b94c04c007b1e2014823501b8c217821a7fa.jpg)


![](images/55d72fdadc26a95722b11d25ba4229033f76a48c9840256a72df8fe9fda2f910.jpg)



图 3-39 ND 格式 C 矩阵 N 方向 32 字节对齐示意图


![](images/ec15538a658d8a730bebd861e6042490492106b74b8f936403d58d16d7868517.jpg)



图 3-40 ND_ALIGN 格式 C 矩阵 N 方向 32 字节对齐示意图


![](images/93a895fb31a98616fb1521f324e257ba4a8d41b212f70125e88ea11b35fc4461.jpg)



矩阵c


# 使用场景

Matmul计算中N方向非32字节对齐，输出C矩阵的N方向要求32字节对齐的场景。 

# 约束说明

若配置C矩阵为ND_ALIGN格式输出，则为C矩阵申请的Buffer空间为N向上32字节对齐 后的空间大小。 

# 调用示例

完整的算子样例请参考matmul_nd_align算子样例。 

Tiling实现 

调用SetCType接口，设置C矩阵的数据格式为CubeFormat::ND_ALIGN，其它 Tiling实现与基础场景相同。 

```txt
auto ascendcPlatform = platform_ascending::PlatformAscendC(context->GetPlatformInfo());  
matmul_tiling::MatmulApiTiling(tiling(ascendingPlatform));  
tiling.SetATOType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND,  
matmul_tiling::DataType::DT_FLOAT16);  
tiling.SetBType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND,  
matmul_tiling::DataType::DT_FLOAT16);  
//设置C矩阵，buffer位置为GM，数据格式为NDALIGN  
tiling.SetCType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::NDALIGN,  
matmul_tiling::DataType::DT_FLOAT);  
tiling.SetBiasType(AscendC::TPosition::GM, matmul_tiling::CubeFormat::ND,  
matmul_tiling::DataType::DT_FLOAT);  
//其他实现内容  
optiling::TCubeTiling tilingData;  
int ret = tiling.GetTiling(tilingData); 
```

Kernel实现 

相较于基础场景，ND_ALIGN输出功能要求在创建Matmul对象时，设置模板参数 cType的数据格式为CubeFormat::ND_ALIGN。 

```cpp
include"lib/matmul_intf.h" typedef AscendC::MatmulType<AscendC::TPosition::GM,CubeFormat::ND, half> aType; typedef AscendC::MatmulType<AscendC::TPosition::GM,CubeFormat::ND, half> bType; //设置模板参数cType的数据格式为ND ALIGN 
```

typedef AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND_ALIGN, float> cType; typedef AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, float> biasType; AscendC::Matmul<aType, bType, cType, biasType> mm; 

# 3.3.3.3.11 单次矩阵乘局部输出

# 功能介绍

单次矩阵乘局部输出，又称Partial Output。如基础知识中所述，一次Iterate计算过程 中，会按K方向进行一次或多次基本块计算，其中的一次基本块计算为baseM*baseK和 baseK*baseN大小的输入数据进行计算得到baseM*baseN大小的结果；每次基本块计 算的结果进行累加后，便得到baseM*singleCoreK和singleCoreK*baseN大小的输入数 据计算得到的结果baseM*baseN，并将其作为一次Iterate的最终结果输出。 

开启Partial Output功能后，调用Iterate接口不会进行K轴累加，只进行单次基本块计 算。用户可以通过GetTensorC接口获取对应的单片数据，最后自行进行K轴上的累 加。 


图 3-41 未开启 Partial Output 功能计算示意图


![](images/60f79a1fe0009b7210f9dedd32c2fcf1dc90805b6f0f36a01740cf303cfee51b.jpg)



图 3-42 开启 Partial Output 功能计算示意图


![](images/94ebd0a0e5c6ef8aa13178fba4f2e30a2dbcaa1a518f089ea084c0ccc6debce7.jpg)


# 使用场景

矩阵乘计算结果不需要累加，只需要输出baseM*baseK和baseK*baseN的计算结果 baseM*baseN。例如需要先获取单次基本块计算的数据进行反量化，再累加得到最终 结果。 

# 约束说明

该功能仅支持MDL模板。 

获取矩阵乘计算结果时，仅支持调用Iterate和GetTensorC接口的连续写模式，不 支持非连续写模式以及IterateAll接口获取计算结果，连续写模式的介绍请参考 GetTensorC。 

该功能不支持带有Bias矩阵的Matmul计算，即不支持输入Bias矩阵。 

# 调用示例

完整的算子样例请参考开启Partial Output功能的算子样例。 

//配置MDL模板，使能Partial Output  
constexpr static MatmulConfigMode configMode $=$ MatmulConfigMode::CONFIG_MD;  
constexpr static MatmulFuncParams funcParams $=$ {false,false,false,false,0,IterateOrder::UNDEF,ScheduleType::INNER_PRODUCT, true, true, true/\*isPartialOutput\*/}；  
constexpr static MatmulConfig CFG_PARTIAL $=$ GetMMConfig<configMode>(funcParams);Matmul<A_TYPE,B_TYPE,C_TYPE,BIAS_TYPE,CFG_PARTIAL>mm;REGIST_MATMUL_OBJ(&pipe,GetSysWorkSpacePtr(),mm);  
mm Init(&tiling);  
mm.SetTensorA(gmA,isTransposeA);  
mm.SetTensorB(gmB,isTransposeB);  
while(mm.Iterate()){mm.GetTensorC(tmpGmC[dstOffset],false,True);dstOffset $+ =$ baseM \*baseN;//其他操作} 

# 3.3.3.3.12 AIC 和 AIV 独立运行机制

# 功能介绍

AIC和AIV独立运行机制，又称双主模式。在分离模式下，区别于MIX模式（包含矩阵 计算和矢量计算）通过消息机制驱动AIC运行，双主模式为AIC和AIV独立运行代码，不 依赖消息驱动，使能双主模式能够提高Matmul计算性能。默认情况下，双主模式不使 能，需要通过MatmulConfig中的enableMixDualMaster参数开启。 

# 使用场景

算子中的矩阵计算和矢量计算相关代码独立运行，不依赖消息驱动时，可以开启双主 模式，以提高Matmul计算性能。 

# 约束说明

该功能仅支持Norm模板和MDL模板。 

算子核函数的类型为MIX，同时AIC核数 : AIV核数为1:1。 

算子核函数的类型为MIX，同时AIC核数 : AIV核数为1:2，且A矩阵和B矩阵同时使 能IBSHARE参数。 

● 同一算子中所有Matmul对象的该参数取值必须保持一致。 

● A、B、Bias矩阵只支持从Global Memory输入。 

获取矩阵计算结果只支持调用IterateAll接口输出到GlobalTensor，即计算结果放 置于Global Memory的地址，不能调用GetTensorC等接口获取结果。 

# 调用示例

完整的算子样例请参考使能双主模式的算子样例。 

```cpp
// 修改模板参数enableMixDualMaster=true，Norm模板开启双主模式，MDL模板使用GetMDLConfig接口获取模板参数。  
constexpr static MatmulConfig MM_CFG = GetNormalConfig(false, false, false, BatchMode::BATCH_LESS_THAN_L1, true, IterateOrder::ORDER_M, ScheduleType::OUTPUT_PRODUCT, false, true/*enableMixDualMaster*/);  
Matmul<A_TYPE, B_TYPE, C_TYPE, BIAS_TYPE, MM_CFG> mm; 
```

```txt
//常规Matmul计算  
REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm);  
mm.SetTensorA(gm_a);  
mm.SetTensorB(gm_b);  
mm.SetBias(gm.bias);  
mm.IterateAll(gm_c); 
```

# 3.3.3.3.13 MxMatmul 场景

# 背景介绍

浮点数在科学计算、图像处理、神经网络等领域应用广泛。以AI训练为例，现有的浮 点数格式或数值范围不足，或精度不高，这影响了模型的收敛速度和性能。如果要同 时满足数值范围和精度的要求，将会导致内存占用过大，从而增加数据存储和传输的 成本。基于此种情况，业内提出了一种新的浮点数格式——微缩放（Microscaling， MX）格式。MX格式的浮点数可以支持更低比特位宽的AI训练和推理，并且占用的内 存更少。符合MX标准的数据格式在使用8位或更低比特位的情况下，能够实现稳健的 AI训练和推理模型精度。 

MX格式是一种块数据格式，若干个数据可以组成一个块（或者一个组），数据以块为 单位。MX格式的数据由三部分构成： 

共享缩放因子X，位宽为w bits； 

私有元素Pi，位宽为d bits； 

块大小k，表示多少个低比特数据形成一个块； 

所有k个元素P有相同的位宽和数据类型，并且共享一个缩放因子X，每个包含k个元素 的块可以使用（ ${ \mathsf { w } } { + } { \mathsf { k } } ^ { \star } { \mathsf { d } }$ ）位进行编码。元素的数据类型和缩放因子可以独立选择。 

下图为MX格式的浮点数的数据结构，S、E和M分别用于表示浮点数的符号、指数和尾 数字段的值。其中，共享缩放因子X是一个用于整个数据块的缩放比例因子，它决定了 数据块中所有元素的动态范围。通过引入共享缩放因子，MX格式的数据能够在保持低 位宽的同时，灵活地表示不同范围的数据。块大小k指的是组成一个数据块（或组）的 低比特数据的数量。私有元素P是指数据块中的每个低比特数据元素。这些元素经过缩 放因子X的调整后，共同表示了一个高精度的浮点数或整数。 


图 3-43 MX 格式组成示意图


![](images/fcdfa4072077f8fb7819b9359f020b5c9475df888b6fa48c676252a9cb1ae116.jpg)


MX格式的数据类型包含多种，例如MXFP8、MXFP4、MXFP16、MXINT4等。下表列 举了MxMatmul场景（全称Microscaling Matmul）支持的数据类型。 


表 3-9 MxMatmul 支持 MX 格式的数据类型


<table><tr><td>数据类型</td><td>私有元素数据类型</td><td>私有元素位宽(d)</td><td>块大小(k)</td><td>共享缩放因子数据类型</td><td>共享缩放因子位宽(w)</td></tr><tr><td>MXFP8</td><td>fp8_e5m2_t</td><td>8</td><td>32</td><td>fp8_e8m0_t</td><td>8</td></tr><tr><td>MXFP8</td><td>fp8_e4m3f_n_t</td><td>8</td><td>32</td><td>fp8_e8m0_t</td><td>8</td></tr><tr><td>MXFP4</td><td>fp4x2_e1m2_t</td><td>4</td><td>32</td><td>fp8_e8m0_t</td><td>8</td></tr><tr><td>MXFP4</td><td>fp4x2_e2m1_t</td><td>4</td><td>32</td><td>fp8_e8m0_t</td><td>8</td></tr></table>

# 功能介绍

MxMatmul（全称Microscaling Matmul）为带有量化系数的矩阵乘法，即左矩阵和右 矩阵均有对应的量化系数矩阵，左量化系数矩阵scaleA和右量化系数矩阵scaleB。 MxMatmul场景中，左量化系数矩阵与左矩阵乘积，右量化系数矩阵与右矩阵乘积， 对两个乘积的结果做矩阵乘法。 

MxMatmul的计算公式为：C = (scaleA ⊗ A) * (scaleB ⊗ B) + Bias，“⊗”表示广播 乘法，左/右矩阵与左/右量化系数矩阵做乘积时，K方向上每32个元素共享一个量化因 子，如图3-44所示。 

A、scaleA、B、scaleB为源操作数。A为左矩阵，形状为[M, K]；scaleA为左量化 系数矩阵，形状为[M, K/32]；B为右矩阵，形状为[K, N]；scaleB为右量化系数矩 阵，形状为[K/32, N]。 

C为目的操作数，存放矩阵乘结果的矩阵，形状为[M, N]。 

Bias为矩阵乘偏置，形状为[1, N]。对(scaleA $\otimes$ A) * (scaleB ⊗ B)结果矩阵的每 一行都采用该Bias进行偏置。 


图 3-44 MxMatmul 矩阵乘示意图


![](images/0c66ed79c4aaa7cddfd8a9d11445b51bcabc0e4f5e6deab3b2901ae95d2f7b5c.jpg)


矩阵A、scaleA、B、scaleB在不同位置中的排布格式分别如下图所示。 


图 3-45 A 矩阵在不同位置的排布格式


![](images/8a444350e84a41d6a726cd1f53258ecb3ee54e3564c43304e8d023e85bec692b.jpg)



图 3-46 B 矩阵在不同位置的排布格式


![](images/c2014081ce889ea02ce866957358e00bad324b4e095be09259b68cc13df4976e.jpg)


![](images/f41d323f983767119385bc3f2a55e15b3836c3867eca75150c6b9b8d4a65e6db.jpg)



图 3-47 scaleA 矩阵在不同位置的排布格式


![](images/f239faeb604ef251518f727838ffd1eef7df1d7e41d882603d13f04709168e0e.jpg)


![](images/4260fac98bd45a46c695f2d8b2f907889c5bc91b0efb00683324918cdc7aee5c.jpg)



图 3-48 scaleB 矩阵在不同位置的排布格式


![](images/a16b0aa6a0a19d9095f04b05ecf2cdefa86764fb17f9d8fdc27088ce04499322.jpg)


# 使用场景

矩阵计算之前，需要对A、B矩阵进行量化操作的场景。当前该场景下，Matmul输入 输出矩阵支持的数据类型如下表所示。 


表 3-10 MxMatmul 支持的量化场景


<table><tr><td>A矩阵</td><td>B矩阵</td><td>ScaleA矩阵/ScaleB矩阵</td><td>Bias矩阵</td><td>C矩阵</td><td>支持平台</td></tr><tr><td>fp4x2_e1m2_t</td><td>fp4x2_e1m2_t/fp4x2_e2m1_t</td><td>fp8_e8m0_t</td><td>float/half/bfloat16_t</td><td>float/half/bfloat16_t</td><td>Atlas 350加速卡</td></tr><tr><td>fp4x2_e2m1_t</td><td>fp4x2_e2m1_t/fp4x2_e1m2_t</td><td>fp8_e8m0_t</td><td>float/half/bfloat16_t</td><td>float/half/bfloat16_t</td><td>Atlas 350加速卡</td></tr><tr><td>fp8_e4m3f n_t</td><td>fp8_e4m3fn_t/fp8_e5m2_t</td><td>fp8_e8m0_t</td><td>float/half/bfloat16_t</td><td>float/half/bfloat16_t</td><td>Atlas 350加速卡</td></tr><tr><td>fp8_e5m2_t</td><td>fp8_e4m3fn_t/fp8_e5m2_t</td><td>fp8_e8m0_t</td><td>float/half/bfloat16_t</td><td>float/half/bfloat16_t</td><td>Atlas 350加速卡</td></tr></table>

# 实现流程

Host侧自动获取Tiling参数的关键步骤介绍如下： 

# 步骤1 创建Tiling对象。

auto ascendcPlatform $=$ platform_ascendc::PlatformAscendC(context->GetPlatformInfo()); 

matmul_tiling::MatmulApiTiling cubeTiling(ascendcPlatform); 

传入硬件平台信息创建PlatformAscendC对象，然后创建Tiling对象，硬件平台信息可 以通过GetPlatformInfo获取。 

步骤2 设置A、B、C、Bias的内存逻辑位置、格式、数据类型以及是否转置的信息，设置 scaleA、scaleB的内存逻辑位置、格式以及是否转置的信息。 

调用SetScaleAType、SetScaleBType接口，设置scaleA、scaleB的内存逻辑位置、格式 以及是否转置。 

cubeTiling.SetAType(AscendC::TPosition::GM, CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT8_E5M2, false); 

cubeTiling.SetBType(AscendC::TPosition::GM, CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT8_E5M2, true); 

cubeTiling.SetScaleAType(AscendC::TPosition::GM, CubeFormat::ND, false); 

cubeTiling.SetScaleBType(AscendC::TPosition::GM, CubeFormat::ND, true); 

cubeTiling.SetCType(AscendC::TPosition::GM, CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT); 

cubeTiling.SetBiasType(AscendC::TPosition::GM, CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT); 

步骤3 使能MxMatmul场景。 

调用SetMadType接口，设置Tiling计算逻辑为MxMatmul场景。 

cubetiling.SetMadType(MatrixMadType::MXMODE); 

步骤4 设置矩阵shape信息。 

cubeTiling.SetShape(M, N, K); 

cubeTiling.SetOrgShape(M, N, K); // 设置原始完整的形状M、N、K 

步骤5 设置可用空间大小信息。 

设置Matmul计算时可用的L1 Buffer/L0C Buffer/Unified Buffer空间大小，-1表示AI处 理器对应Buffer的大小。 

cubeTiling.SetBufferSpace(-1, -1, -1); 

步骤6 按需设置其他参数，比如设置bias参与计算。 

cubeTiling.EnableBias(true); 

步骤7 获取Tiling参数。 

```txt
MatmulCustomTilingData tiling;  
if (cubeTiling.GetTiling(tiling.cubeTilingData) == -1){  
return ge::GRAPH_FAILED;  
} 
```

步骤8 Tiling参数的序列化保存等其他操作。 

----结束 

Kernel侧的关键步骤介绍如下： 

步骤1 创建Matmul对象。 

// MxMatmul场景通过MatmulTypeWithScale定义A、scaleA、B、scaleB的参数类型信息 

typedef AscendC::MatmulTypeWithScale<AscendC::TPosition::GM, AscendC::TPosition::GM, CubeFormat::ND, fp8_e5m2_t, isTransposeA> aType; 

typedef AscendC::MatmulTypeWithScale<AscendC::TPosition::GM, AscendC::TPosition::GM, CubeFormat::ND, fp8_e5m2_t, isTransposeB> bType; 

typedef AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, float> cType; 

typedef AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, float> biasType; 

// 定义matmul对象时，传入MatmulWithScalePolicy表明使能MxMatmul模板策略 

AscendC::Matmul<aType, bType, cType, biasType, CFG_MDL, MatmulCallBackFunc<nullptr, nullptr, nullptr>, 

AscendC::Impl::Detail::MatmulWithScalePolicy> mm; 

创建对象时需要传入A、scaleA、B、scaleB、C、Bias的参数类型信息， A、scaleA、 B、scaleB类型信息通过MatmulTypeWithScale来定义，C、Bias类型信息通过 

MatmulType来定义，包括：内存逻辑位置、数据格式、数据类型、转置信息。同时， 通过模板参数MatmulPolicy传入MatmulWithScalePolicy表明使能MxMatmul场景。 

```c
template <TPosition POSITION, TPosition SCALE_POSITION, CubeFormat FORMAT, typename TYPE, bool ISTRANS = false, TPosition SRCPOS = TPosition::GM, CubeFormat SCALE_FORMAT = FORMAT, bool SCALE_ISTRANS = ISTRANS, TPosition SCALE_SRCPOS = SRCPOS> 
struct MatmulTypeWithScale: public MatmulType<POSITION, FORMAT, TYPE, ISTRANS> {
    constexpr static TPosition scalePosition = SCALE_POSITION;
    constexpr static CubeFormat scaleFormat = SCALE_FORMAT;
    constexpr static bool isScaleTrans = SCALE_ISTRANS;
    constexpr static TPosition srcScalePos = SCALE_SRCPOS;
}; 
```

步骤2 初始化操作。 

```cpp
REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm, &tiling); // 初始化 
```

步骤3 设置左矩阵A、右矩阵B、左量化系数矩阵scaleA、右量化系数矩阵scaleB、Bias。 

通过SetTensorScaleA、SetTensorScaleB设置左量化系数矩阵scaleA、右量化系数矩阵 scaleB。 

```txt
mm.SetTensorA(gm_a, isTransposeA); //设置左矩阵A  
mm.SetTensorB(gm_b, isTransposeB); //设置右矩阵B  
mm.SetTensorScaleA(gm_scaleA, isTransposeScaleA); //设置左量化系数矩阵scaleA  
mm.SetTensorScaleB(gm_scaleB, isTransposeScaleB); //设置右量化系数矩阵scaleB  
mm.SetBias(gm.bias); //设置Bias 
```

步骤4 完成矩阵乘操作。 

调用Iterate完成单次迭代计算，叠加while循环完成单核全量数据的计算。Iterate 方式，可以自行控制迭代次数，完成所需数据量的计算，方式比较灵活。 while (mm.Iterate()) { mm.GetTensorC(gm_c); } 

调用IterateAll完成单核上所有数据的计算。IterateAll方式，无需循环迭代，使用 比较简单。 mm.IterateAll(gm_c); 

步骤5 结束矩阵乘操作。 

```javascript
mm.End(); 
```

----结束 

更多完整的算子样例请参考Scale的K方向为偶数的MxMatmul样例、Scale的K方向为 奇数的MxMatmul样例、mx_ub_tscm_nz样例、matmul_mx_typepara样例。 

# 参数说明


表 3-11 MatmulTypeWithScale 参数说明


<table><tr><td>参数</td><td>说明</td></tr><tr><td>POSITION</td><td>左右矩阵的内存逻辑位置。针对Atlas 350 加速卡:A矩阵可设置为TPosition::GM, TPosition::VECOUT,TPosition::TSCMB矩阵可设置为TPosition::GM, TPosition::VECOUT,TPosition::TSCM注意:A、B矩阵设置为TPosition::TSCM时,对应的Format仅支持CubeFormat::NZ。</td></tr><tr><td>SCALE_POSI-TION</td><td>量化系数矩阵的内存逻辑位置。针对Atlas 350 加速卡:scaleA矩阵可设置为TPosition::GM, TPosition::VECOUT,TPosition::TSCMscaleB矩阵可设置为TPosition::GM, TPosition::VECOUT,TPosition::TSCM注意: scaleA、scaleB矩阵设置为TPosition::TSCM时,对应的SCALE_FORMAT仅支持CubeFormat::NZ。</td></tr><tr><td>FORMAT</td><td>数据的物理排布格式,详细介绍请参考数据格式。针对Atlas 350 加速卡:A矩阵可设置为CubeFormat::ND, CubeFormat::NZ,CubeFormat::VECTORB矩阵可设置为CubeFormat::ND, CubeFormat::NZ注意: NZ排布格式,A/B的排布格式请参考数据格式。</td></tr><tr><td>TYPE</td><td>数据类型。针对Atlas 350 加速卡:A矩阵可设置为fp4x2_e1m2_t、fp4x2_e2m1_t、fp8_e4m3fn_t、fp8_e5m2_tB矩阵可设置为fp4x2_e1m2_t、fp4x2_e2m1_t、fp8_e4m3fn_t、fp8_e5m2_t注意:具体数据类型组合关系请参考MxMatmul支持数据类型。</td></tr><tr><td>ISTRANS</td><td>是否开启使能A、B矩阵转置的功能。默认值为false。参数支持的取值如下:true:开启使能矩阵转置的功能,开启后,分别通过SetTensorA和SetTensorB中的isTransposeA、isTransposeB参数设置A、B矩阵是否转置。若设置A、B矩阵转置,Matmul会认为A矩阵形状为[K,M],B矩阵形状为[N,K]。false:不开启使能矩阵转置的功能,通过SetTensorA和SetTensorB不能设置A、B矩阵的转置情况。Matmul会认为A矩阵形状为[M,K],B矩阵形状为[K,N]。</td></tr><tr><td>SRCPOS</td><td>A/B矩阵的POSITION参数配置为TPosition::TSCM时,要设置TSCM中矩阵数据的来源的内存逻辑位置,默认为TPosition::GM。针对Atlas 350 加速卡:A矩阵可设置为TPosition::GM, TPosition::VECOUTB矩阵可设置为TPosition::GM, TPosition::VECOUT</td></tr><tr><td>SCALE_FORMAT</td><td>量化系数矩阵的物理排布格式,详细介绍请参考数据格式。默认值为FORMAT。针对Atlas 350 加速卡:scaleA矩阵可设置为CubeFormat::ND,CubeFormat::NZ,CubeFormat::VECTORscaleB矩阵可设置为CubeFormat::ND,CubeFormat::NZ注意:NZ排布格式请参考NZ。MxMatmul场景,scaleA、scaleB的数据类型为fp8_e8m0_t,分形大小H0=16,W0=2。在Scale矩阵为ND格式的场景中,当通过SetTensorScaleA接口设置scaleA矩阵转置时,scaleA内存排布格式必须按照(K/64,M,2)排布,通过SetTensorScaleB接口设置scaleB矩阵不转置时,scaleB内存排布格式必须按照(K/64,N,2)排布,详细介绍请参考数据格式。</td></tr><tr><td>SCALE_ISTRANS</td><td>是否开启使能scaleA、scaleB矩阵转置的功能。默认值为ISTRANS。参数支持的取值如下:true:开启使能矩阵转置的功能。开启后,分别通过SetTensorScaleA和SetTensorScaleB中的isTransposeScaleA、isTransposeScaleB参数设置scaleA、scaleB矩阵是否转置。在Scale矩阵为ND格式的场景中,若设置scaleA、scaleB矩阵转置,Matmul会认为scaleA矩阵形状为[Ceil(K/64),M,2],scaleB矩阵形状为[N,Ceil(K/64),2]。false:不开启使能矩阵转置的功能。通过SetTensorScaleA和SetTensorScaleB不能设置scaleA、scaleB矩阵的转置情况。Matmul会认为scaleA矩阵形状为[M,Ceil(K/64),2],scaleB矩阵形状为[Ceil(K/64),N,2]。使用该参数的完整样例请参考scaleA转置scaleB不转置的的MxMatmul样例、scaleA不转置scaleB转置的的MxMatmul样例。</td></tr><tr><td>SCALE_SRCPOS</td><td>scaleA、scaleB矩阵的SCALE_position参数设置为TPosition::TSCM时,需要通过本参数设置TSCM中矩阵数据来源的内存逻辑位置,默认值为SRCPOS。针对Atlas 350 加速卡:scaleA矩阵可设置为TPosition::GM,TPosition::VECOUTscaleB矩阵可设置为TPosition::GM,TPosition::VECOUT</td></tr></table>

# 约束说明

MxMatmul场景仅支持Norm模板和MDL模板。 

在MxMatmul场景中，如果A与B矩阵的位置同时为GM，对singleKIn没有特殊限 制，在这种情况下，若scaleA和scaleB的K方向大小（即Ceil(singleKIn, 32)）为奇 数，用户需自行在scaleA和scaleB的K方向补0至偶数。例如，当singleKIn为30 时，Ceil(singleKIn, 32)为1，用户需要自行在scaleA和scaleB的K方向补0，使K方 向为偶数。对于其它A、B矩阵逻辑位置的组合情况，即A与B矩阵的位置不同时为 GM，singleKIn以32个元素向上对齐后的数值必须是32的偶数倍。 

在MxMatmul场景中，当输入数据类型为fp4x2_e2m1_t/fp4x2_e1m2_t时，内轴 必须为偶数。 

在MxMatmul场景中，通过将A矩阵和scaleA矩阵的数据格式设置为VECTOR，来 开启GEMV模式。在此模式下，A和scaleA矩阵仅支持内存逻辑位置为GM，并且 均不支持转置。 

A矩阵、B矩阵为UB输入时，矩阵的内轴需要向上32字节对齐，例如，A矩阵的形 状为(M, K)时，将K对齐到32字节；A矩阵的形状为(K, M)时，将M对齐到32字 节。 

scaleA矩阵、scaleB矩阵为UB输入时，矩阵的内轴需要向上32字节对齐，例如， scaleA矩阵的形状为(M, K/32)时，将K/32对齐到32字节；scaleA矩阵的形状为 (K/32, M)时，将M对齐到32字节。 

当scaleA和scaleB矩阵以ND格式输入时，高阶API在内部实现格式转换时，需要占 用UB临时空间。开发者需使用SetLocalWorkspace接口配置临时空间，临时空间 大小（单位字节）的计算公式如下。 

```cpp
int32_t scaleATmpBuf = 0;  
int32_t scaleBTmpBuf = 0;  
if constexpr (A_TYPE::scalePosition == TPosition::VECOUT) {  
    if (A_TYPE::isScaleTrans) {  
        scaleATmpBuf = CeilAlign(SingleCoreM, 32) * scaleK;  
    } else {  
        scaleATmpBuf = CeilAlign(scaleK, 32) * SingleCoreM;  
    }  
}  
if constexpr (B_TYPE::scalePosition == TPosition::VECOUT) {  
    if (B_TYPE::isScaleTrans) {  
        scaleBTmpBuf = SingleCoreN * CeilAlign(scaleK, 32);  
    } else {  
        scaleBTmpBuf = scaleK * CeilAlign(SingleCoreN, 32);  
    }  
}  
int32_t totalTmpBuf = scaleATmpBuf + scaleBTmpBuf; 
```

# 3.3.3.3.14 Batch Matmul 基础功能

# 功能介绍

Batch Matmul是指批量处理Matmul计算的场景。该场景对外提供了IterateBatch的调 用接口，调用一次IterateBatch，可以计算出多个singleCoreM * singleCoreN大小的C 矩阵。 

Matmul单次计算的过程需要搬入和搬出数据，当进行多次Matmul计算且单次 Matmul计算的输入shape较小时，搬运开销在整体耗时中占比较大。通过IterateBatch 接口批量处理Matmul，可以有效提升带宽利用率。 

Batch Matmul当前支持4种Layout类型：BSNGD、SBNGD、BNGS1S2、NORMAL （BMNK的数据排布格式），相关数据排布格式请参考IterateBatch。 

下图为NORMAL数据排布格式的Batch Matmul计算。整个Matmul计算一共包含4个 矩阵乘操作：mat_a1*mat_b1、mat_a2*mat_b2、mat_a3*mat_b3、 mat_a4*mat_b4，需要单核上计算四个singleCoreM *singleCoreN。在该场景下，如 果shape较小，可以将其视为Batch Matmul场景进行批量处理，以提升性能。一次 IterateBatch可同时计算出mat_c1 = mat_a1 * mat_b1、mat_c2 = mat_a2 * mat_b2、mat_c3 = mat_a3 * mat_b3、mat_c4 = mat_a4 * mat_b4。 


图 3-49 NORMAL 数据排布格式的 Batch Matmul 示意图


![](images/a58a7da08e23fa15dec4ba964ed43ded4a81d83af5ebb3fc7523a46adfc5fdc5.jpg)


# 使用场景

Matmul计算需要计算出多个singleCoreM * singleCoreN大小的C矩阵，且单次 Matmul计算处理的shape较小。 

# 约束说明

只支持Norm模板。 

对于BSNGD、SBNGD、BNGS1S2 Layout格式，输入A、B矩阵按分形对齐后的多 Batch数据总和应小于L1 Buffer的大小；对于NORMAL Layout格式没有这种限 制，但需通过MatmulConfig配置batchMode参数，即输入A、B矩阵多Batch数据 大小与L1 Buffer的大小关系； 

对于BSNGD、SBNGD、BNGS1S2 Layout格式，称左矩阵、右矩阵的G轴分别为 ALayoutInfoG、BLayoutInfoG，则ALayoutInfoG / batchA = BLayoutInfoG / batchB；对于NORMAL Layout格式，batchA 、batchB必须满足倍数关系。Bias 的shape(batch, n)中的batch必须与C矩阵的batch相等。 

如果接口输出到Unified Buffer上，输出C矩阵大小BaseM*BaseN应小于分配的 Unified Buffer内存大小。 

对于BSNGD、SBNGD Layout格式，输入输出只支持ND格式数据。对于 BNGS1S2、NORMAL Layout格式， 输入支持ND/NZ格式数据。 

Batch Matmul不支持量化/反量化模式，即不支持SetQuantScalar、 SetQuantVector接口。 

BSNGD场景，不支持一次计算多行SD，需要算子程序中循环计算。 

异步模式不支持IterateBatch搬运到Unified Buffer上。 

模板参数enableMixDualMaster（默认取值为false）设置为true，即使能 MixDualMaster（双主模式）场景时，不支持Batch Matmul。 

在batch场景，A矩阵、B矩阵支持half/float/bfloat16_t/int8_t数据类型，不支持 int4b_t数据类型。 

# 调用示例

以下是NORMAL数据排布格式的Batch Matmul调用示例。BSNDG数据排布格式的 Batch Matmul完整示例请参考BatchMatmul样例。 

Tiling实现 使用SetBatchInfoForNormal设置A/B/C的M/N/K轴信息和A/B矩阵的 BatchNum。 

```cpp
auto ascendcPlatform = platform ascendc::PlatformAscendC(context->GetPlatformInfo());  
matmul_tiling::MultiCoreMatmulTiling tiling(ascendcPlatform);  
int32_t M = 32;  
int32_t N = 256;  
int32_t K = 64;  
tiling->SetDim(1);  
tiling->SetATOType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT16);  
tiling->SetBType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT16);  
tiling->SetCTType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT);  
tiling->SetBiasType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT);  
tiling->SetShape(M, N, K);  
tiling->SetOrgShape(M, N, K);  
tiling->EnableBias(true);  
tiling->SetBufferSpace(-1, -1, -1); 
```

```c
constexpr int32_t BATCH_NUM = 3;  
tiling->SetBatchInfoForNormal(BATCH_NUM, BATCH_NUM, M, N, K); //设置矩阵排布  
tiling->SetBufferSpace(-1, -1, -1); 
```

```txt
optiling::TCubeTiling tilingData;  
int ret = tiling.GetTiling(tilingData); 
```

Kernel实现 

创建Matmul对象。 

通过MatmulType设置输入输出的Layout格式为NORMAL。 

```cpp
include"lib/matmul_intf.h" typedef AscendC::MatmulType <AscendC::TPosition::GM, CubeFormat::ND, half, false, LayoutMode::NORMAL> aType; typedef AscendC::MatmulType <AscendC::TPosition::GM, CubeFormat::ND, half, true, LayoutMode::NORMAL> bType; typedef AscendC::MatmulType <AscendC::TPosition::GM, CubeFormat::ND, float, false, LayoutMode::NORMAL> cType; typedef AscendC::MatmulType <AscendC::TPosition::GM, CubeFormat::ND, float> biasType; constexpr MatmulConfig MM_CFG = GetNormalConfig(false, false, false, BatchMode::BATCH_LESS_THAN_L1); AscendC::Matmul<aType, bType, cType, biasType, MM_CFG> mm; 
```

初始化操作。 REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm, &tiling); // 初始化matmul对象 

设置左矩阵A、右矩阵B、Bias。 mm.SetTensorA(gm_a); // 设置左矩阵A mm.SetTensorB(gm_b); // 设置右矩阵B mm.SetBias(gm_bias); // 设置Bias 

完成矩阵乘操作。左矩阵每次计算batchA个MK数据，右矩阵每次计算 batchB个KN数据。 mm.IterateBatch(gm_c, batchA, batchB, false); 

结束矩阵乘操作。 mm.End(); 

# 3.3.3.3.15 Batch Matmul 复用 Bias 矩阵

# 功能介绍

在Batch Matmul场景中，Matmul API可以一次性计算出多个大小为singleCoreM * singleCoreN的C矩阵。当Batch Matmul场景有Bias输入时，默认的Bias输入矩阵包含 Batch轴，即Bias的大小为Batch * N。通过开启Bias复用功能，当每个Batch计算使用 的Bias数据相同时，只需输入一个不带Batch轴的Bias矩阵。Batch Matmul的Bias矩阵 复用功能默认不启用，用户需要设置MatmulConfig中的isBiasBatch参数为false来开启 此功能。 


图 3-50 带有 Batch 轴的 Bias 计算示意图


![](images/e56fb3746f421e9e9fdc368de7b974355ca7b43dd1b92756e4e79891cce3d2b8.jpg)


如上图所示，Batch Matmul中未复用Bias矩阵的场景，每计算出一个singleCoreM * singleCoreN大小的C矩阵，都会与1 * singleCoreN大小的Bias矩阵相加。若不同Batch 

的计算使用的Bias数据相同，则多Batch计算可以复用同一个Bias矩阵，如下图所示， 此场景中调用SetBias接口时，只需设置一个1 * singleCoreN大小的Bias矩阵。 


图 3-51 复用 Bias 计算示意图


![](images/0a5cd8bc4a13a36c3a6a171ac05be7b2411a7897ca5cec21bcbd209a88e0ae67.jpg)


# 使用场景

Batch Matmul中每个Batch的Matmul计算可以使用相同的Bias矩阵。 

# 约束说明

A、B、C矩阵的Layout类型都为NORMAL时，不支持batchMode参数设为 SINGLE_LARGE_THAN_L1，即Bias复用场景下，单Batch的A、B矩阵数据总和不得超 过L1 Buffer的大小。 

# 调用示例

完整的算子样例请参考BatchMatmul复用Bias算子样例。 

```cpp
//自定义MatmulConfig参数，将其中的isBiasBatch参数设置为false，使能BatchMatmul的Bias复用功能。  
constexpr MatmulConfigMode configMode = MatmulConfigMode::CONFIG_NORM;  
constexpr MatmulBatchParams batchParams = {  
    false, BatchMode::BATCH_LESS_THAN_L1, false /* isBiasBatch */  
};  
constexpr MatmulConfig CFG_MM = GetMMConfig<configMode>(batchParams);  
AscendC::Matmul<A_TYPE, B_TYPE, C_TYPE, BIAS_TYPE, CFG_MM> mm;  
REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), mm, &tiling); //初始化matmul对象 
```

```javascript
mm.SetTensorA(gm_a); //设置左矩阵A  
mm.SetTensorB(gm_b); //设置右矩阵B  
mm.SetBias(gm.bias); //设置Bias，矩阵大小为1*singleCoreN  
mm.IterateBatch(gm_c, batchA, batchB, false);  
mm.End(); 
```

# 3.3.4 矩阵编程（基础 API）

# 3.3.4.1 耦合模式

# 说明

本节内容为针对耦合模式，使用基础API进行矩阵乘法的编程指导。 如下章节内容暂不支持Atlas 350 加速卡。 

# 编程范式

Cube编程范式把算子的实现流程分为5个基本任务：CopyIn，Split，Compute， Aggregate，CopyOut。CopyIn负责搬入操作，Split负责数据切分操作，Compute负 责矩阵指令计算操作，Aggregate负责数据汇聚操作，CopyOut负责搬出操作。 


图 3-52 矩阵编程基本任务设计


![](images/dd7982c36a9d29cba849e5ac40b01d0a40b2dd3400deab2f0180f59bb5a5e91f.jpg)


具体任务之间的交互流程和流程图如下。 

步骤1 Stage1：CopyIn任务。 

1. 使用DataCopy接口将GlobalTensor数据拷贝到LocalTensor。 

2. 使用EnQue将LocalTensor放入A1/B1的Queue中。 

步骤2 Stage2：Split任务。 

1. 使用DeQue从A1/B1中取出LocalTensor。 

2. 使用LoadData接口将LocalTensor从A1/B1中搬运到A2/B2。 

3. 使用EnQue将计算结果LocalTensor放入到A2/B2的Queue中。 

步骤3 Stage3：Compute任务。 

1. 使用DeQue从A2/B2中取出LocalTensor。 

2. 使用Mmad接口完成矩阵计算。 

3. 使用EnQue将计算结果LocalTensor放入到CO1的Queue中。 

步骤4 Stage4：Aggregate任务。 

1. 使用DeQue从CO1中取出LocalTensor。 

2. 使用Ascend C接口拷贝结果矩阵到CO2。 

3. 使用EnQue将计算结果LocalTensor放入到CO2的Queue中。 

步骤5 Stage5：CopyOut任务。 

1. 使用DeQue接口从CO2的Queue中取出LocalTensor。 

2. 使用DataCopy接口将LocalTensor拷贝到GlobalTensor上。 

----结束 


图 3-53 矩阵编程 Queue 队列


![](images/be1f5b8b6b08024353e81266178fd2984e3189c4a6f7a923e8fa3cc7671d1d16.jpg)


# 开发流程

基于Ascend C方式实现矩阵算子的流程如下图所示。 


图 3-54 矩阵算子实现流程


![](images/3559e1c8755616cd51a9011b7091ee7d380efcb917fbffb8a8cbe0eff8c8228e.jpg)


算子分析：分析算子的数学表达式、输入、输出以及计算逻辑的实现，明确需要 调用的Ascend C接口。 

核函数定义：定义Ascend C算子入口函数。 

根据矩阵编程范式实现算子类：完成核函数的内部实现，调用私有成员函数 CopyIn、SplitA、SplitB、Compute、Aggregate、CopyOut完成矩阵算子的五级 流水操作。 

下文将以Matmul算子为例对上述步骤进行详细介绍，Matmul算子的代码框架如下， 完整代码请参见Mmad样例。 

```cpp
include"kernel_operator.h"   
//根据编程范式实现算子类   
class KernelMatmul{   
public: aicore__inline void Init(GM_ADDR a, GM_ADDR b, GM_ADDR c) { //... } aicore__inline void Process() { Copyln(); SplitA(); AscendC::LocalTensor<half> b1Local = inQueueB1.DeQue<half>(); AscendC::LocalTensor<half> a2Local = inQueueA2.DeQue<half>(); AscendC::LocalTensor<float> c2Local = outQueueCO2 AllocTensor<float>(); // split matrix b into 2 parts, [32, 16] and [32, 16] for (int i = 0; i < 2; ++i) { SplitB(b1Local, i); Compute(a2Local); Aggregate(c2Local, i); } inQueueB1.FreeTensor(b1Local); inQueueA2.FreeTensor(a2Local); outQueueCO2.EnQue<c2Local>; CopyOut();   
}   
private: aicore__inline void Copyln() { //... 
```

```txt
} aicore__inline void SplitA() { //... } aicore__inline void SplitB(const LocalTensor<half>& b1Local, const int bSplitIdx) { //... } aicore__inline void Compute(const LocalTensor<half>& a2Local) { //... } aicore__inline void Aggregate(const LocalTensor<float>& c2Local, const int bSplitIdx) { //... } aicore__inline void CopyOut() { //... } private: //... }; //核函数定义 extern "C" global __aicore__void matmul_custom(GM_ADDR a, GM_ADDR b, GM_ADDR c) { KernelMatmul op; opInit(a, b, c); op.Process(); } 
```

# 算子分析

在开发算子代码之前需要分析算子的数学表达式、输入、输出以及计算逻辑的实现， 明确需要调用的Ascend C接口。 

步骤1 明确算子的数学表达式及计算逻辑。 

Matmul算子完成矩阵乘操作，其数学表达式如下，形状为[m, k]的矩阵a和形状为[k, n]的矩阵b相乘，得到形状为[m, n]的矩阵c。为了方便，令m=k=n=32。 c = a * b 

注意需要处理的数据过大时，需要对数据进行切分并分块搬运到A2、B2，分别计算后 再进行汇聚。下文的计算逻辑为了展示Split和Aggregate阶段的样例，请您根据实际需 要处理的数据大小决定是否需要切分和汇聚。 

# 计算逻辑如下：

1. 分别搬运输入数据矩阵a、b至Local Memory A1、B1。 

2. 将a矩阵从A1搬运至A2。为实现部分并行，将b矩阵切分为part1和part2，形状均 为[k, n / 2]，切分后再分块搬运至B2。 

3. a矩阵和b矩阵part1、part2分别做矩阵乘运算，获得矩阵c的part1和part2，形状 均为[m, n / 2]。计算结果在CO1存储。 

4. 将矩阵c的part1和part2分别拷贝到CO2进行合并。 

5. 将合并后的输出数据从CO2搬出。 

步骤2 明确输入和输出。 

Matmul算子有两个输入：a与b，输出为c。 

本样例中算子输入支持的数据类型为half（float16），算子输出的数据类型为 float32。 

矩阵a、b、c的形状均为[32, 32]。 

算子输入输出支持的数据格式为：ND。 

# 步骤3 确定核函数名称和参数。

您可以自定义核函数名称，本样例中核函数命名为matmul_custom。 

根据对算子输入输出的分析，确定核函数有3个参数a，b，c；a，b为输入在 Global Memory上的内存地址，c为输出在Global Memory上的内存地址。 

# 步骤4 约束分析。

由于硬件架构对矩阵乘计算的输入输出有格式约束，需要在算子实现中增加格式转换 的流程。 

搬运矩阵a、b至A1、B1时，将ND格式的矩阵a、b转换为NZ格式。 

从A1搬运矩阵a至A2时，将NZ格式的a矩阵转换为ZZ格式；从B1搬运矩阵b到B2 时将NZ格式的b矩阵转换为ZN格式。 

将计算结果从CO2搬出时，将NZ格式的c矩阵转换为ND格式。 

数据排布格式的相关介绍详见数据排布格式。 

# 步骤5 确定算子实现所需接口。

实现外部存储和内部存储间的数据搬运，查看Ascend C API参考中的数据搬移接 口，具体参考DataCopy。 

实现矩阵数据格式转换，查看Ascend C API参考中的数据转换接口，具体参考 LoadData。 

矩阵计算过程涉及矩阵乘法，查看Ascend C API参考中的矩阵计算接口，具体参 考Mmad。 

计算中使用到的Tensor数据结构，使用Queue队列进行管理，会使用到EnQue、 DeQue等接口。 

# ----结束

通过以上分析，得到Ascend C Matmul算子的计算流程图和设计规格如下： 


图 3-55 Matmul 算子的计算流程图


![](images/0cd4479495ec8388729445016502027c63d39489c1218156f175bd0ddee63006.jpg)



表 3-12 Ascend C Matmul 算子设计规格


<table><tr><td>算子类型
(Opacity)</td><td colspan="4">Matmul</td></tr><tr><td rowspan="3">算子输入</td><td>name</td><td>shape</td><td>data type</td><td>format</td></tr><tr><td>a</td><td>(m, k) = (32, 32)</td><td>half</td><td>ND</td></tr><tr><td>b</td><td>(k, n) = (32, 32)</td><td>half</td><td>ND</td></tr><tr><td>算子输出</td><td>c</td><td>(m, n) = (32, 32)</td><td>float32</td><td>ND</td></tr><tr><td>核函数名称</td><td colspan="4">matmul_custom</td></tr><tr><td rowspan="4">使用的主要接口</td><td colspan="4">DataCopy: 数据搬移接口</td></tr><tr><td colspan="4">LoadData: 矩阵数据格式转换接口</td></tr><tr><td colspan="4">Mmad: 矩阵乘计算接口</td></tr><tr><td colspan="4">EnQue、DeQue等接口: Queue队列管理接口</td></tr><tr><td>算子实现文件名称</td><td colspan="4">matmul_custom.cpp</td></tr></table>

# 核函数定义

根据2.2.3.2 核函数中介绍的规则进行核函数的定义。 

# 步骤1 函数原型定义。

本样例中，函数名为matmul_custom（核函数名称可自定义）；根据算子分析中对算 子输入输出的分析，确定有3个参数a，b，c，其中a，b都为输入内存，c为输出内存。 根据2.2.3.2 核函数中核函数的规则介绍，函数原型定义如下所示：使用__global__函 数类型限定符来标识它是一个核函数，可以被<<<>>>调用；使用__aicore__函数类型 限定符来标识该核函数在设备端aicore上执行；为方便起见，统一使用GM_ADDR宏修 饰入参，GM_ADDR宏定义请参考2.2.3.2 核函数。 

```txt
extern "C" __global__ __aicore__ void matmul_custom(GM_ADDR a, GM_ADDR b, GM_ADDR c) { } 
```

# 步骤2 调用算子类的Init和Process函数。

算子类的Init函数，完成内存初始化相关工作，Process函数完成算子实现的核心逻 辑，具体介绍参见算子类实现。 

```txt
extern "C" __global__ __aicore__ void matmul_custom(GM_ADDR a, GM_ADDR b, GM_ADDR c)  
{  
    KernelMatmul op;  
    opInit(a, b, c);  
    op.Process();  
} 
```

步骤3 对核函数进行封装，得到matmul_custom_do函数，便于主程序调用。#ifndef ASCENDC_CPU_DEBUG表示该封装函数仅在编译运行NPU侧的算子时会用到，编译运 行CPU侧的算子时，可以直接调用matmul_custom函数。根据核函数定义和调用章 节，调用核函数时，除了需要传入参数a，b，c，还需要传入numBlocks（核函数执行 的核数），l2ctrl（保留参数，设置为nullptr），stream（应用程序中维护异步操作执 行顺序的stream）来规定核函数的执行配置。 

```txt
#ifndef ASCENDC_CPU_DEBUG
// call of kernel function
void matmul_custom_do uint32_t numBlocks, void* l2ctrl, void* stream, uint8_t* a, uint8_t* b, uint8_t* c)
{
    matmul_custom<<numBlocks, l2ctrl, stream>>>(a, b, c);
} 
```

# ----结束

# 算子类实现

根据上一章节介绍，核函数中会调用算子类的Init和Process函数，本章具体讲解基于 编程范式实现算子类。矩阵编程范式请参考编程范式。 

算子类中主要包含对外开放的初始化Init函数和核心处理函数Process以及一些实现中 会用到的私有成员。KernelMatmul算子类的定义如下： 

```cpp
class KernelMatmul{   
public: __aicore__inline KernelMatmul(){ //初始化函数，完成内存初始化相关操作 __aicore__inline void Init(GM_ADDR a, GM_ADDR b, GM_ADDR c){ //核心处理函数，实现算子逻辑 //调用私有成员函数CopyIn、SplitA、SplitB、Compute、Aggregate、CopyOut完成矩阵算子的五级流水操作 __aicore__inline void Process(){   
private: __aicore__inline void CopyND2NZ(const LocalTensor<half>& dst, const GlobalTensor<half>& src, const uint16_t height, const uint16_t width){ //搬进函数，完成编程范式中的Copyln阶段的处理，由Process函数调用 __aicore__inline void CopyIn(){ //搬进函数，完成编程范式中的Split阶段的处理，由Process函数调用 __aicore__inline void SplitA(){ 
```

```cpp
// 搬进函数，完成编程范式中的Split阶段的处理，由Process函数循环调用两次，分别搬运b矩阵的两个part __aicore__inline void SplitB(const LocalTensor<half>& b1Local, const int bSplitIdx){ // 计算函数，完成编程范式中的Compute阶段的处理，由Process函数循环调用两次，分别计算出矩阵c的两个  
part __aicore__inline void Compute(const LocalTensor<half>& a2Local){ // 搬出函数，完成编程范式中的Aggregate阶段的处理，由Process函数循环调用两次，分别搬出矩阵c的两个  
part __aicore__inline void Aggregate(const LocalTensor<float>& c2Local, const int bSplitIdx){ // 搬出函数，完成编程范式中的CopyOut阶段的处理，由Process函数调用 __aicore__inline void CopyOut(){ }  
private: AscendC::TPipe pipe; // Pipe内存管理对象，管理Queue队列的内存 AscendC::TQue<TPosition::A1, 1> inQueueA1; // 输入数据的队列，TPosition为A1 AscendC::TQue<TPosition::A2, 1> inQueueA2; // 输入数据的队列，TPosition为A2 AscendC::TQue<TPosition::B1, 1> inQueueB1; // 输入数据的队列，TPosition为B1 AscendC::TQue<TPosition::B2, 2> inQueueB2; // 输入数据的队列，TPosition为B2 AscendC::TQue<TPosition::CO1, 2> outQueueCO1; // 输出数据的队列，TPosition为CO1 AscendC::TQue<TPosition::CO2, 1> outQueueCO2; // 输出数据的队列，TPosition为CO2 // 管理输入输出Global Memory内存地址的对象，其中aGM, bGM为输入，cGM为输出 AscendC::GlobalTensor<half> aGM, bGM; AscendC::GlobalTensor<float> cGM; uint16_t m = 32; uint16_t n = 32; uint16_t k = 32; uint16_t aSize, bSize, cSize, mBlocks, nBlocks, kBlocks; }; 
```

# KernelMatmul构造函数实现

构造函数中对私有成员变量进行初始化，具体代码如下： 

aicore__inline KernelMatmul()   
{ aSize $=$ m\*k; bSize $\equiv$ k\*n; cSize $=$ m\*n; mBlocks $= \mathrm{m}$ /16; nBlocks $=$ n/16; kBlocks $=$ k/16;   
} 

矩阵a的形状为[m, k]，矩阵b的形状为[k, n]，矩阵c的形状为[m,n]，此样例中m、 n、k均设置为32。 

aSize、bSize、cSize分别为矩阵a、b、c的数值个数。 

mBlocks、 nBlocks、 kBlocks为m、n、k所占分形数量，half类型一个分形Shape为 16 * 16，blocks计算公式为： 

mBlocks = m / 16 

nBlocks = n / 16 

kBlocks = k / 16 

分形具体介绍可参考2.9.2.2 数据排布格式。 

# Init函数实现

Init函数主要完成以下内容： 

设置输入输出Global Tensor的Global Memory内存地址。 

以设置输入a在Global Memory上的内存偏移地址为例： 

aGM.SetGlobalBuffer((__gm__ half*)a); 

注意，因为本样例中Init函数的入参统一设置为uint8_t*，这里需要强转成具体的 数据类型(__gm__ half*)，再进行偏移。 

通过Pipe内存管理对象为输入输出Queue分配内存。 

比如，为输入数据队列inQueueB2分配内存，可以通过如下代码段实现： 

```txt
pipe.InitialBuffer(inQueueB2, 2, bSize * sizeof(half) / 2); 
```

此样例中将b矩阵切分为两个part，为inQueueB2分配内存时需要申请两块内存空 间，每一块的大小为b矩阵大小的一半，outQueueCO1的内存初始化同理。 


具体的初始化函数代码如下：


```txt
aicore__inline void Init(GM_ADDR a, GM_ADDR b, GM_ADDR c)  
{  
    aGM.SetGlobalBuffer(_gm__half*)a);  
    bGM.SetGlobalBuffer(_gm__half*)b);  
    cGM.SetGlobalBuffer(_gm__float*)c);  
    pipeInitBuffer(inQueueA1, 1, aSize * sizeof(half));  
    pipeInitBuffer(inQueueA2, 1, aSize * sizeof(half));  
    pipeInitBuffer(inQueueB1, 1, bSize * sizeof(half));  
    pipeInitBuffer(inQueueB2, 2, bSize * sizeof(half) / 2);  
    pipeInitBuffer(outQueueCO1, 2, cSize * sizeof(float) / 2);  
    pipeInitBuffer(outQueueCO2, 1, cSize * sizeof(float));  
} 
```

# Process函数实现

基于矩阵编程范式，将核函数的实现分为5个基本阶段：CopyIn，Split，Compute， Aggregate，CopyOut。Split，Compute，Aggregate阶段需要区分a、b矩阵。 Process函数中通过如下方式调用这几个函数。 

```cpp
aicore__inline void Process()   
{ CopyIn(); SplitA(); AscendC::LocalTensor<half> b1Local = inQueueB1.DeQue<half>(); AscendC::LocalTensor<half> a2Local = inQueueA2.DeQue<half>(); AscendC::LocalTensor<float> c2Local = outQueueCO2 AllocTensor<float>(); // split matrix b into 2 parts, [32, 16] and [32, 16] for (int i = 0; i < 2; ++i) { SplitB(b1Local, i); Compute(a2Local); Aggregate(c2Local, i); } inQueueB1.FreeTensor(b1Local); inQueueA2.FreeTensor(a2Local); outQueueCO2.EnQue<c2Local>; CopyOut(); 
```

两次循环内，SplitB需要从inQueueB1中分别搬运两个part的b矩阵，Compute需要分 别计算a矩阵和两个part b矩阵的乘法，Aggregate要分别搬运两个part的c矩阵，具体 五个阶段数据流通示意图如下： 


图 3-56 数据流通示意图


![](images/9e67d06bc009bd7e805e275f00583d123863d7676adddb3bcea122401105ba3f.jpg)


切分b矩阵，可以实现一部分的并行，本样例的流水并行示意图如下： 


图 3-57 并行示意图


![](images/e1056fc040b324c40c68fa11d8d1a7d2ef4ec8325f0fef2e36d9173944b3c58c.jpg)


步骤1 Stage1：CopyIn函数实现。 

1. 使用AllocTensor从A1，B1的Queue中申请a1Local和b1Local。 

2. 使用DataCopy接口将矩阵a、b搬运到Local Memory，同时将其数据格式从ND转 换为NZ。 

一次DataCopy指令搬运height*16个数，循环执行width/16次。DataCopy的参数 设置如下： 

blockCount设置为height，共搬运height次。 

blockLen设置为1，一次搬运16个类型为half的数。 

srcStride设置为width/16 - 1，源矩阵每搬运一个block需要跳跃一行。 

dstStride设置为0，目的矩阵每个block在内存中连续存储。 

每次循环迭代，源矩阵首地址移动16个数，目的矩阵首地址移动16*height个 数。 

格式转换示意图如下，第一次循环搬运蓝色部分，第二次循环搬运绿色部分；图 中width为32，占两个分形，height为32，占两个分形，一共搬运4个 $1 6 ^ { \star } 1 6$ 分 形。 


图 3-58 ND to NZ 转换示意图


![](images/7e26ce6fbb5149492ceaa83e63a4f88ac24f3025ff92678d7827f0b3223ff311.jpg)


注意：上述ND到NZ的格式转换仅作为举例说明，开发者可根据实际情况选择合 适的转换方式。 

3. 使用EnQue将a1Local、b1Local分别放入A1、B1的Queue中。 

# 具体代码如下：

```cpp
__aicore__ inline void CopyND2NZ(const LocalTensor<half>& dst, const GlobalTensor<half>& src, const uint16_t height, const uint16_t width)  
{  
    for (int i = 0; i < width / 16; ++i) {  
        int srcOffset = i * 16;  
        int dstOffset = i * 16 * height;  
        AscendC::DataCopy.dst[dstOffset], src[srcOffset], { height, 1, uint16_t(width / 16 - 1), 0 });  
    }  
}  
__aicore__ inline void Copyln()  
{  
    AscendC::LocalTensor<half> a1Local = inQueueA1 AllocTensor<half>();  
    AscendC::LocalTensor<half> b1Local = inQueueB1 AllocTensor<half>();  
    CopyND2NZ(a1Local, aGM, m, k);  
    CopyND2NZ(b1Local, bGM, k, n);  
    inQueueA1.EnQue(a1Local);  
    inQueueB1.EnQue(b1Local);  
} 
```

步骤2 Stage2：SplitA函数实现。 

1. 使用DeQue从A1的Queue中取出a1Local。 

2. 使用AllocTensor从A2的Queue中申请a2Local。 

3. 使用LoadData将矩阵a搬运到A2，同时将a矩阵从NZ格式转换为ZZ格式。 

搬运及格式转换示意图如下：图中k为32，占kBlocks（ $k / 1 6 = 2$ ）个分形，m为 32，占mBlocks（ $m / 1 6 = 2$ ）个分形，一共搬运4个 $1 6 ^ { \star } 1 6$ 分形。本示例中，调用一 次LoadData接口完成两个 $1 6 ^ { \star } 1 6$ 分形的搬运，循环调用两次LoadData。第一次循 环搬运蓝色部分两个分形，第二次循环搬运绿色部分两个分形。 

单次循环中LoadData（本样例中要完成2个分形的搬运，蓝色部分或者绿色部 分）的参数设置如下： 

repeatTimes表示数据处理的迭代次数，因为LoadData每个迭代处理一个分 形，所以也可以理解为待搬运分形的个数。本样例中即为k轴方向的分形个 数，设置为kBlocks，表示搬运kBlocks个分形。 

srcStride表示，相邻迭代间源操作数分形首地址之间的间隔，以搬运蓝色部 分分形为例：下图中左侧源操作数矩阵，第一个蓝色分形和第二个蓝色分形 起始地址之间的间隔为mBlocks个分形，此处设置为mBlocks。 

dstGap使用默认值，目的矩阵两个分形连续存储。 

– ifTranspose设置为false，每块分形搬运前搬运后都为Z格式，不使能转置。 

每次循环迭代源矩阵首地址偏移 $1 6 ^ { \star } 1 6$ ，目的矩阵首地址偏移 $1 6 ^ { \star } \mathsf { k }$ 。 


图 3-59 NZ to ZZ 格式转换示意图


![](images/4d70dba5ceffa67cb6425e38b171ba4c69ae6b2e0ef36c82b4efe0941503c3d3.jpg)


# 4. 使用EnQue将计算结果a2Local放入到A2的Queue中。

# 具体代码如下：

aicore__inline void SplitA()   
{ int srcOffset $= 0$ int dstOffset $= 0$ AscendC::LocalTensor<half> a1Local $=$ inQueueA1.DeQue<half>(); AscendC::LocalTensor<half> a2Local $=$ inQueueA2 AllocTensor<half>(); // transform nz to zz for (int i $= 0$ ; i $<$ mBlocks; ++i) { AscendC::LoadData2DParams loadDataParams; loadDataParamsrepeatTimes $=$ kBlocks; loadDataParams.srcStride $=$ mBlocks; loadDataParams.ifTranspose $=$ false; AscendC::LoadData(a2Local[dstOffset], a1Local[srcOffset], loadDataParams); srcOffset $+ = 16^{*}16$ dstOffset $+ = k^{*}16$ 1   
inQueueA2.EnQue<(a2Local); inQueueA1.FreeTensor(a1Local); 

# 步骤3 Stage2：SplitB函数实现。

1. SplitB需要传入两个参数：使用DeQue从B1的Queue中取出的b1Local和循环迭代 变量index。 

2. 使用AllocTensor从B2的Queue中申请b2Local。 

3. 使用LoadData将b矩阵搬运到B2，同时从NZ格式转换为ZN格式。 

搬运及格式转换示意图如下：图中k为32，占kBlocks（k/16=2）个分形，n为 32，占nBlocks（n/16=2）个分形，一共搬运4个16*16分形。本示例中，调用一 次LoadData接口完成两个16*16分形的搬运，循环调用两次LoadData。第一次循 环搬运蓝色部分两个分形，第二次循环搬运绿色部分两个分形。 

单次循环中LoadData（本样例中要完成2个分形的搬运，蓝色部分或者绿色部 分）的参数设置如下： 

repeatTimes表示数据处理的迭代次数，因为LoadData每个迭代处理一个分 形，所以也可以理解为待搬运分形的个数。本样例中即为k轴方向的分形个 数，设置为kBlocks，表示搬运kBlocks个分形。 

srcStride相邻迭代间源操作数分形首地址之间的间隔，以搬运蓝色部分分形 为例：下图中左侧源操作数矩阵，第一个蓝色分形和第二个蓝色分形起始地 址之间的间隔为1个分形，此处设置为1，源矩阵两个分形连续存储。 

dstGap使用默认值0，目的矩阵两个分形连续存储。 

ifTranspose设置为true，每块分形搬运前为Z格式，搬运后需要为N格式，需 要使能转置。 

每次循环迭代，源矩阵首地址需要偏移k*n/2。 


图 3-60 NZ to ZN 格式转换示意图


![](images/c70b0575c200b8fe9e63ed59bf7e2e19632ffc88bd327aeda7b949841427262b.jpg)


# 4. 使用EnQue将计算结果b2Local放入到B2的Queue中。

# 具体代码如下：

```cpp
aicore__inline void SplitB(const AscendC::LocalTensor<half>& b1Local, const int bSplitIdx)  
{ AscendC::LocalTensor<half> b2Local = inQueueB2 AllocTensor<half>(); // transform nz to zn AscendC::LoadData2DParams loadDataParams; loadDataParamsrepeatTimes = kBlocks; loadDataParams.srcStride = 1; loadDataParams.ifTranspose = true; AscendC::LoadData(b2Local, b1Local[bSplitIdx * bSize / 2], loadDataParams); inQueueB2.EnQue<half>(b2Local); } 
```

步骤4 Stage3：Compute函数实现，完成核心的矩阵计算功能。 

1. Compute函数需要传入参数a2Local，a2Local从A2的Queue中使用DeQue取出。 

2. 使用AllocTensor从CO1的Queue中申请c1Local。 

3. 使用DeQue从B2中取出b2Local。 

4. 使用Mmad完成矩阵乘计算。 

5. 使用EnQue将计算结果c1Local放入到CO1的Queue中。 

# 具体代码如下：

```cpp
aicore__inline void Compute(const AscendC::LocalTensor<half>& a2Local)  
{ AscendC::LocalTensor<half> b2Local = inQueueB2.DeQue<half>(); AscendC::LocalTensor<float> c1Local = outQueueCO1 AllocTensor<float>(); AscendC::MmadParams mmadParams; mmadParams.m = m; mmadParams.n = n / 2; mmadParams.k = k; AscendC::Mmad(c1Local, a2Local, b2Local, mmadParams); outQueueCO1.EnQue<float>(c1Local); inQueueB2.FreeTensor(b2Local); } 
```

步骤5 Stage4：Aggregate函数实现，完成数据汇聚操作。 

1. Aggregate需要传入两个参数：使用AllocTensor从CO2的Queue中申请的c2Local 和循环迭代变量index。 

2. 使用DeQue从CO1中取出c1Local。 

3. 使用DataCopy将结果矩阵从CO1搬运到CO2。 

DataCopy参数设置如下： 

blockCount设置为1，blockLen设置为2，连续搬运两个分形，无需格式转 换。 

blockMode设置为BlockMode::BLOCK_MODE_MATRIX，表示需要按分形搬 运。 

c2Local首地址偏移量设置为index * cSize / 2。 

# 具体代码如下：

```cpp
aicore__inline void Aggregate(const AscendC::LocalTensor& c2Local, const int bSplitIdx)  
{  
    AscendC::LocalTensor<float> c1Local = outQueueCO1.DeQue<float>();  
    AscendC::DataCopyParams dataCopyParams;  
    dataCopyParams.blockCount = 1;  
    dataCopyParams.blockLen = 2;  
    AscendC::DataCopyEnhancedParams enhancedParams;  
    enhancedParams.blockMode = AscendC::BlockMode::BLOCK_MODEMATRIX;  
    AscendC::DataCopy(c2Local[bSplitIdx * cSize / 2], c1Local, dataCopyParams, enhancedParams);  
    outQueueCO1.FreeTensor(c1Local);  
} 
```

步骤6 Stage5：CopyOut函数实现。 

1. 使用DeQue从CO2中取出c2Local。 

2. 使用DataCopy将结果矩阵从CO2搬运到Global Memory，同时需要将格式从NZ 转换为ND。 

每次循环移动一个分形，搬运 $\mathsf { m } ^ { \star } \mathsf { 1 6 }$ 个数。DataCopy参数说明如下： 

blockCount设置为m，共搬运m次。 

– blockLen设置为2，DataCopy指令一次搬运2个block，每个block16个数。 

srcStride设置为0，每两次搬运间没有间隙。 

dstStride设置为(nBlocks - 1) * 2，每两次搬运间隔2个block。 

每次循环迭代，目的矩阵偏移16，源矩阵偏移 $\mathsf { m } ^ { \star } 1 6$ 。 

格式转换示意图如下，第一次循环搬运蓝色部分数据，第二次循环搬运绿色部分 数据。 


图 3-61 NZ to ND 格式转换示意图


![](images/3c7d7d72584df747b5cd7f1be1fbb6a1d84682d2cf12a852e01a55ae5f9ad21a.jpg)


![](images/f5b00801ea6fd839031599018e061e1b0b99625bc20fefcc2717d918ebaacdb9.jpg)



具体代码如下：


aicore__inline void CopyOut()   
{ AscendC::LocalTensor<float> c2Local $=$ outQueueCO2.DeQue<float>(); // transform nz to nd for (int $\mathrm{i} = 0$ .i $<$ nBlocks; $+ + \mathrm{i}$ { AscendC::DataCopy(cGM[i\*16],c2Local[i\*m\*16],{m,2,0,uint16_t((nBlocks-1)\*2)}); } outQueueCO2.FreeTensor(c2Local); 

----结束 

# 3.3.4.2 分离模式

# 说明

本节内容为针对分离模式，使用基础API进行矩阵乘法的编程指导。 

如下章节内容暂不支持Atlas 350 加速卡。 

针对分离模式，使用基础API进行矩阵乘法算子实现的编程范式和3.3.4.1 耦合模式 致，由于硬件架构不同，具体实现有一些差异，本节仅提供差异点说明。完整代码请 参见Mmad样例。 

# CopyIn阶段差异

# 耦合模式

在CopyIn阶段，即从GM->A1/B1（L1 Buffer）的阶段，耦合模式下可以使用 DataCopy接口直接将数据从GM搬入L1 Buffer，也可以将数据从GM搬入 UB，再搬入L1 Buffer。若需要ND2NZ的格式转换，需要开发者自行完成； 或使用DataCopy接口提供的随路格式转换功能，但该功能会使用UB临时空 间。 

如下示例，直接使用了GM->A1/B1的数据搬运指令，自行完成ND2NZ的格 式转换。 

```cpp
__aicore__ inline void CopyND2NZ(const AscendC::LocalTensor<half>& dst, const AscendC::GlobalTensor<half>& src, const uint16_t height, const uint16_t width) { for (int i = 0; i < width / 16; ++i) { int srcOffset = i * 16; int dstOffset = i * 16 * height; AscendC::DataCopy.dst[dstOffset], src[srcOffset], { height, 1, uint16_t(width / 16 - 1), } } __aicore__ inline void Copyln() { AscendC::LocalTensor<half> a1Local = inQueueA1 AllocTensor<half>(); AscendC::LocalTensor<half> b1Local = inQueueB1 AllocTensor<half>(); CopyND2NZ(a1Local, aGM, m, k); CopyND2NZ(b1Local, bGM, k, n); inQueueA1.EnQue(a1Local); inQueueB1.EnQue(b1Local); } 
```

# 分离模式

分离模式下数据无法经过VECIN/VECCALC/VECOUT (UB) 直接搬运到A1/B1 (L1 Buffer) ，但是使用DataCopy接口提供的随路格式转换功能一条指令即 可完成格式转换，无需UB作为临时空间。 

示例如下： 

```cpp
aicore__inline void Copyln()   
{ AscendC::LocalTensor<half> a1Local = inQueueA1 AllocTensor<half>(); AscendC::LocalTensor<half> b1Local = inQueueB1 AllocTensor<half>(); AscendC::Nd2NzParams nd2nzA1Params; nd2nzA1Params.ndNum = 1; nd2nzA1Params.nValue = m; nd2nzA1Params.dValue = k; nd2nzA1Params.srcNdMatrixStride = 0; nd2nzA1Params.srcDValue = k; nd2nzA1Params.dstNzC0Stride = CeilCubeBlock(m) * CUBE_BLOCK; nd2nzA1Params.dstNzNStride = 1; nd2nzA1Params.dstNzMatrixStride = 0; AscendC::DataCopy(a1Local, aGM, nd2nzA1Params); AscendC::Nd2NzParams nd2nzB1Params; nd2nzB1Params.ndNum = 1; nd2nzB1Params.nValue = k; nd2nzB1Params.dValue = n; nd2nzB1Params.srcNdMatrixStride = 0; nd2nzB1Params.srcDValue = n; nd2nzB1Params.dstNzC0Stride = CeilCubeBlock(k) * CUBE_BLOCK; nd2nzB1Params.dstNzNStride = 1; nd2nzB1Params.dstNzMatrixStride = 0; AscendC::DataCopy(b1Local, bGM, nd2nzB1Params); inQueueA1.EnQue(a1Local); inQueueB1.EnQue(b1Local); } 
```

# Aggregate及CopyOut阶段差异

# 耦合模式

耦合模式中，完成矩阵乘计算后数据存放于CO1（L0C Buffer），最终搬入 GM需要通过CO2（UB），且NZ2ND的格式转换需要在CO1->CO2->GM阶 段中手动完成。如下样例，在Aggregate阶段将NZ格式数据从CO1搬入CO2 中，在CO2->GM的阶段使用for循环调用DataCopy完成了格式转换。 

```cpp
__aicore__inline void Aggregate(const AscendC::LocalTensor&c2Local, const int bSplitIdx) { AscendC::LocalTensor<float> c1Local = outQueueCO1.DeQue<float>(); AscendC::DataCopyParams dataCopyParams; dataCopyParams.blockCount = 1; dataCopyParams.blockLen = 2; AscendC::DataCopyEnhancedParams enhancedParams; enhancedParams.blockMode = AscendC::BlockMode::BLOCK_MODEMATRIX; AscendC::DataCopy(c2Local[bSplitIdx * cSize / 2], c1Local, dataCopyParams, enhancedParams); outQueueCO1.FreeTensor(c1Local); } __aicore__inline void CopyOut() { AscendC::LocalTensor<float> c2Local = outQueueCO2.DeQue<float>(); // transform nz to nd for (int i = 0; i < nBlocks; ++i) { AscendC::DataCopy(cGM[i * 16], c2Local[i * m * 16], {m, 2, 0, uint16_t((nBlocks - 1) * 2)}); } outQueueCO2.FreeTensor(c2Local); } 
```

# 分离模式

分离模式下，矩阵乘的计算结果从CO1（L0C Buffer）可以通过Fixpipe通路 直接写入GM，而且Fixpipe提供了随路NZ2ND的功能，方便用户做格式转 换。样例如下，样例中省去了Aggregate阶段，直接CopyOut。 

__aicore__ inline void CopyOut()   
{ AscendC::LocalTensor<float> c1Local $=$ outQueueCO1.DeQue<float>(); AscendC::FixpipeParamsV220 fixpipeParams; fixpipeParams.nSize $\equiv$ n; fixpipeParams.mSize $\equiv$ m; fixpipeParams.srcStride $\equiv$ m; fixpipeParams.dstStride $\equiv$ n; fixpipeParams.ndNum $\equiv$ 1; fixpipeParams.srcNdStride $\equiv$ 0; fixpipeParams.dstNdStride $\equiv$ 0; AscendC::Fixpipe(cGM,c1Local,fixpipeParams); outQueueCO1.FreeTensor(c1Local);   
} 

# 3.3.5 融合算子编程

# 3.3.5.1 CV 融合

# 3.3.5.1.1 基础知识

说明 

学习融合算子编程之前，请确保已经掌握矩阵编程相关知识。 

# CV 融合算子

融合算子由多个独立的小算子融合而成，其功能与多个小算子的功能等价，性能方面 通常优于独立的小算子。用户可以根据实际业务场景诉求，按照具体算法自由融合向 

量（Vector）、矩阵（Cube）算子以达到性能上的收益。融合了Cube计算、Vector计 算的算子统称为CV融合算子。 

比如对于LLM大模型中最核心的一个融合算子Flash Attention， 其核心实现如下图。 图中的Matmul算子（Cube）、Scale算子（Vector）、Mask算子（Vector）、 SoftMax算子（Vector）融合为一个大的算子Flash Attention。 


图 3-62 Flash Attention 核心实现


![](images/f06f1cb1b008f4e45cba223a579a567b5242e35a53a6b6b7c2965acd18ce2bf3.jpg)


# 使用场景和优势

针对有数据依赖的矢量算子和矩阵算子，可以通过融合算子编程的方式，将矢量算子 和矩阵算子进行融合，通过一个算子Kernel函数来承载，由此来获得性能上的收益。 下图展示了独立矢量算子和矩阵算子、Mix融合算子的执行耗时对比，由此可以看出为 什么开发Mix融合算子会带来性能上的收益。 


图 3-63 独立矢量算子和矩阵算子、Mix 融合算子的执行耗时对比


![](images/63b2db0e8cfad0ac363db2117cf479a256d1a1063151573cc24080bd6e2838cf.jpg)


独立的矢量算子和矩阵算子实现：矩阵计算后的结果需要搬运到Global Memory 上，然后由Global Memory搬运到Local Memory，再进行矢量算子的计算，计算 和搬运都是串行执行，另外多个算子的调度执行，会增加算子的调度耗时。 

融合算子的实现方法：可以对数据进行切片，再通过流水的设计，使得矢量计算 单元和矩阵计算单元实现并行计算；另外相比于不融合的单算子，减少了算子的 调度耗时。 

除了有效提升算子性能，充分发挥AI处理器的算力，融合算子还有如下优势： 

减少计算量：融合算子可以将多个算子合并为一个，简化计算过程，减少计算 量，提高计算效率。 

减少内存占用：融合算子可以将多个算子的中间结果合并为一个，从而减少内存 占用，提高内存利用率。 

优化数据流：融合算子可以优化数据流，减少数据在不同算子之间的传输，从而 提高数据处理效率。 

简化代码实现：融合算子可以简化代码实现，减少代码量，提高代码可读性和可 维护性。 

总之，融合算子是一种优化计算的有效手段，可以提高计算效率和内存利用率，优化 数据流，简化代码实现。 

# 编程范式

Ascend C提供融合算子的编程范式，方便开发者基于该范式表达融合算子的数据流， 快速实现自定义的融合算子。 

融合算子数据流指融合算子的输入输出在各存储位置间的流向。以一个典型的Cube和 Vector融合算子为例，逻辑位置间的数据流向如下图所示： 

Cube的输出可以作为Vector的输入：CO2->VECIN 

● Vector的输出可以作为Cube的输入：VECOUT->A1->A2、VECOUT->B1->B2 

![](images/94a7f5b8004a4f8024d8693089de9f93531aef0e50965abe34babafbe7a3b25b.jpg)


基于Matmul高阶API的融合算子编程范式，对上述数据流简化表达如下： 


图 3-64 融合算子编程范式


![](images/97f7b531662e07fcea266fddb3e51f37c1404c00c6cac6b99fdfc509ca87faa7.jpg)


1. 初始化一个Matmul对象。 

2. 进行Matmul内部的计算。 

3. 将Matmul的计算结果搬运到Vector核上。 

4. 进行Vector矢量计算。 

5. 将输出结果搬运到Global Memory上。 

整个过程的示例代码如下（伪代码）。完整样例请参考MatmulLeakyRelu。 

```cpp
template<typename aType, typename bType, typename cType, typename biasType> __aicore__ inline void MatmulLeakyKernel<aType, bType, cType, biasType>::Process()
{
    uint32_t computeRound = 0;
    matmulObj.SetTensorA(aGlobal);
    matmulObj.SetTensorB(bGlobal);
    matmulObj.SetBias(biasGlobal);
    while (matmulObj.template Iterate(true)) { // 步骤2：进行Matmul内部的计算。
        // 步骤3：将Matmul的计算结果搬运到Vector核上。
        reluLocal = reluQueue_AllocTensor<cType>();
        matmulObj.template GetTensorC(true)(reluOutLocal, false, true);
        // 步骤4：进行Vector矢量计算。 
```

```txt
AscendC::LeakyRelu(reluOutLocal, reluOutLocal, (cType)alpha, tiling.baseM * tiling.baseN);  
reluOutQueue_.EnQue(reluOutLocal);  
//步骤5：将输出结果搬运到Global Memory上  
reluOutQueue_.DeQue<cType>();  
...  
AscendC::DataCopy(cGlobal[ startOffset], reluOutLocal, copyParam);  
reluOutQueue_.FreeTensor(reluOutLocal);  
computeRound++;  
}  
matmulObj.End();  
}  
// kernel入口函数，_mix_(1,2)表示：mix场景，AIC:AIV=1:2。  
_global _ mix_(1,2) void matmul_leakyrelucustom(GM_ADDR a, GM_ADDR b, GM_ADDR bias, GM_ADDR c, _kfc Workspace__GM_ADDR workspace, AscendC::tiling::TCubeTiling  
tiling)  
{  
    AscendC::TPipe pipe;  
    MatmulLeakyKernel< half, half, float, float> matmulLeakyKernel;  
    matmulLeakyKernelInit(a, b, bias, c, workspace, tiling, &pipe);  
    //步骤1：初始化Matmul对象。  
REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), matmulLeakyKernel.matmulObj, &matmulLeakyKernel.tiling);  
matmulLeakyKernel.Process(&pipe);  
} 
```

# 3.3.5.1.2 算子实现

下文将以Matmul+LeakyRelu融合算子的实现为例，介绍Mix融合算子的设计和实现流 程。该样例仅支持在Atlas A2 训练系列产品/Atlas A2 推理系列产品上运行。 

算子的设计过程分为算子分析、数据流分析、Tiling策略设计三部分。 

# 算子分析

算子分析是指明确算子的数学表达式、输入、输出，核函数的名称等信息。 

步骤1 明确算子的数学表达式及计算逻辑。该算子的计算逻辑为，先进行一个矩阵乘操作， 然后将矩阵乘的结果与一个alpha参数进行LeakyRelu操作。数学表达式如下： 

```javascript
c = LeakyRelu(a * b + bias, alpha); 
```

步骤2 明确输入和输出。 

Matmul+LeakyRelu算子输入为a、b、bias，输出为c。alpha作为激活函数 LeakyRelu的系数，为固定值，可以在算子实现中直接使用常数值参与计算。 

本样例中算子输入a、b支持的数据类型为half（float16），算子输入bias支持的 数据类型为float32，算子输出c的数据类型为float32。 

输入矩阵a的形状为[M，K]，输入矩阵b的形状为[K, N]，输出矩阵c的形状为 [M，N]，输入bias的形状为[1, N]。 

算子输入输出支持的数据格式为：ND。 

步骤3 确定核函数名称和参数。 

您可以自定义核函数名称，本样例中核函数命名为matmul_leakyrelu_custom。 

根据对算子输入输出的分析，确定核函数的参数a，b，bias，c；a，b, bias为输 入在Global Memory上的内存地址，c为输出在Global Memory上的内存地址。 

----结束 

通过以上分析，得到Ascend C Matmul+LeakyRelu算子的设计规格如下： 

算子类型（OpType）：MATMUL_LEAKYRELU 

算子输入输出： 


表 3-13 MATMUL_LEAKYRELU 算子输入输出规格


<table><tr><td>name</td><td>shape</td><td>data type</td><td>format</td></tr><tr><td>a(输入)</td><td>[M, K]</td><td>half</td><td>ND</td></tr><tr><td>b(输入)</td><td>[K, N]</td><td>half</td><td>ND</td></tr><tr><td>bias(输入)</td><td>[1, N]</td><td>float32</td><td>ND</td></tr><tr><td>z(输出)</td><td>[M, N]</td><td>float32</td><td>ND</td></tr></table>

核函数名称：matmul_leakyrelu_custom 

# 数据流分析

进行算子的数据流分析：数据流向为在Cube核上完成Matmul计算后将数据搬运至 Vector核进行LeakyRelu计算。根据上述数据流并结合融合算子的编程范式，规划并行 的流水任务。如下图所示： 

![](images/dd6fe4a5875c5756b1d4f0eb0363c927a2a362df6cdb4aece24b360cd3a303f5.jpg)


步骤1 将输入数据从Global Memory搬运到Cube核。 

步骤2 进行Matmul内部的计算，计算公式和计算示意图如下： 

注：bias的shape为[1, N]，对A*B结果矩阵的每一行都采用该bias进行偏置。 


图 3-65 Matmul 矩阵乘示意图


![](images/9cae60604d89011198529103afed9b6ee31f251b56a10d9f39f2f313bc5beb4f.jpg)


步骤3 将Matmul的计算结果搬运到Vector核。 

步骤4 进行Vector矢量计算，该样例中进行LeakyReLU计算。 

Leaky ReLU（带泄露线性整流函数）激活函数，是人工神经网络中一种常用的激活函 数，其数学表达式和函数图像如下所示： 

$$
f (x _ {i}) = \left\{ \begin{array}{l l} x _ {i} & \text {i f} x _ {i} \geq 0 \\ a x _ {i} & \text {i f} x _ {i} <   0 \end{array} \right.
$$

![](images/049e48c2a2394465a4aff8eaea940de616b016c0f6ab1b52c0ed099aaa78f44a.jpg)


步骤5 将输出结果搬运到Global Memory。 

----结束 

前三步的内容都封装在Matmul高阶API内，本样例中可以简化为3个stage。如下图所 示： 

![](images/09b1f5b511c29bafc9c3a0c372aa7303c19f86dea185c0ea5ba7d744d3362681.jpg)


根据上述分析，明确实现过程中会使用到Matmul高阶API接口，LeakyRelu Vector计 算接口、DataCopy、EnQue、DeQue接口。 

# Tiling 策略设计

Tiling策略的设计主要包括多核切分和核内切分策略。 

多核切分: 根据当前核数，对输入shape的M, K, N进行多核切分，得到单核内 shape大小singleCoreM, singleCoreK, singleCoreN。 

核内切分: 根据Local Memory的大小约束，对单核内的shape大小进一步切分，得 到A、B、C矩阵参与一次矩阵乘指令的shape大小baseM, baseN, baseK。切分时 需要注意：GetTensorC的结果如果放在LocalMemory（UB）上，需要注意， baseM * baseN的大小不能超出UB的限制。 

切分策略示意图如下，更多切分策略相关原理请参考数据分块（Tiling）。 

![](images/66649ecf8c193970f45ef90ab7953a855fed7acd5bd6650e5a0b05eff98e151e.jpg)


# 算子实现

在矩阵编程章节，我们得知Ascend C提供一组Matmul高阶API，封装了常用的切分和 数据搬运、计算的算法逻辑，方便用户快速实现Matmul矩阵乘法的运算操作。融合算 子中矩阵编程部分的实现与之类似，开发者在host侧通过调用API自动获取Tiling参 数，该参数传递到kernel侧后，在初始化操作时传入，通过几个简单的API即可完成矩 阵乘操作。再结合上文的融合算子的编程范式，融合算子实现的步骤如下。完整样例 请参考MatmulLeakyRelu。 

![](images/54883085b575f3363301c090138c941831f498b137e9f58cef0f2d44e33301fb.jpg)


kernel侧实现的代码框架如下，在完成Matmul对象的初始化、左矩阵A、右矩阵B、 Bias的设置后，通过单次Iterate叠加while循环的方式完成后续的Matmul计算、 LeakyRelu计算、CopyOut流程。 

```txt
template<typename aType, typename bType, typename cType, typename biasType> __aicore__ inline void MatmulLeakyKernel<aType, bType, cType, biasType>::Process(){
    uint32_t computeRound = 0;
    //设置Matmul的输入（包括左矩阵、右矩阵、bias）
    matmulObj.SetTensorA(aGlobal);
    matmulObj.SetTensorB(bGlobal);
    matmulObj.SetBias(biasGlobal);
    //调用matmul iterate获取一块.baseM, baseN]的计算结果
    while (matmulObj.template Iterate(true>) {
        MatmulCompute();
        LeakyReluCompute();
        CopyOut(computeRound);
        computeRound++;
    }
    matmulObj.End();
}
// kernel入口函数，mix场景，AIC:AIV=1:2
_global__ mix__(1, 2) void matmul_leakyrelucustom(GM_ADDR a, GM_ADDR b, GM_ADDR bias,
GM_ADDR c,
        __kfc Workspace__ GM_ADDR workspace, AscendC::tiling::TCubeTiling
tiling)
{
    AscendC::TPipe pipe;
    MatmulLeakyKernel<half, half, float, float> matmulLeakyKernel;
    matmulLeakyKernelInit(a, b, bias, c, workspace, tiling, &pipe);
    //Matmul对象初始化
    REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), matmulLeakyKernel.matmulObj,
&matmulLeakyKernel.tiling);
    matmulLeakyKernel.Process(&pipe);
} 
```

Matmul计算、LeakyRelu计算、CopyOut的具体实现代码如下： 

# 步骤1 Matmul计算：

1. 在Cube核上，进行Matmul内部的计算。 

2. 将Matmul的计算结果搬运到Vector核。 

```cpp
template<typename aType, typename bType, typename cType, typename biasType> __aicore__ inline void MatmulLeakyKernel<aType, bType, cType, biasType>::Process(){
    uint32_t computeRound = 0;
    // ...
    // 调用matmul iterate获取一块[baseM, baseN]的计算结果
    while (matmulObj.template Iterate(true));
    {
        MatmulCompute();
        // ...
        computeRound++;
    }
    matmulObj.End();
} 
```

步骤2 LeakyRelu计算。 

```txt
//调用LeakyRule接口进行计算 template<typename aType, typename bType, typename cType, typename biasType> 
```

```cpp
aicore inline void MatmulLeakyKernel<aType, bType, cType, biasType>::LeakyReluCompute(){
    AscendC::LeakyRelu(reluOutLocal, reluLocal, (cType)alpha, tiling.baseM * tiling.baseN);
    reluOutQueue_.EnQue(reluOutLocal);
} 
```

步骤3 CopyOut，将输出结果搬运到Global Memory。 

//将结果搬出到GM   
template<typename aType, typename bType, typename cType, typename biasType> _aicore__inline void MatmulLeakyKernel<aType,bType,cType,biasType>::CopyOut uint32_t count){ reluQueue_.DeQue<cType>(); const uint32_t roundM $=$ tiling.singleCoreM / tiling.baseM; const uint32_t roundN $=$ tiling(singleCoreN / tiling.baseN; uint32_t startOffset $=$ (count $\%$ roundM \* tiling.baseM \* tiling.N $^+$ count / roundM \* tiling.baseN); AscendC::DataCopyParams copyParam $=$ { (uint16_t)tiling.baseM, (uint16_t)(tiling.baseN \* sizeof(cType) / DEFAULT_C0_SIZE),0, (uint16_t)((tiling.N - tiling.baseN) \* sizeof(cType) / DEFAULT_C0_SIZE)}; AscendC::DataCopy(cGlobal[startOffset],reluOutLocal,copyParam); reluQueue_.FreeTensor(reluOutLocal);   
} 

----结束 

host侧实现GenerateTiling函数，在该函数中自动获取Tiling参数，关键步骤介绍如 下： 

步骤1 创建Tiling对象。 

```cpp
auto ascendcPlatform = platform_ascending::PlatformAscendC(context->GetPlatformInfo()); matmul_tiling::MultiCoreMatmulTiling cubeTiling(ascendingPlatform); 
```

创建对象时需要传入硬件平台信息，硬件平台信息可以通过GetPlatformInfo获取。 

步骤2 设置A、B、Bias的数据类型和格式。 

设置示例如下，其中TPosition::LCM是Unified Buffer上的逻辑位置，等同于 TPosition::VECCALC，关于TPosition的详细内容请参考TPosition。 

```rust
cubeTiling.SetAType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT16);  
cubeTiling.SetBType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT16);  
cubeTiling.setCType(matmul_tiling::TPosition::LCM, matmul_tiling::CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT);  
cubeTiling.setBiasType(matmul_tiling::TPosition::GM, matmul_tiling::CubeFormat::ND, matmul_tiling::DataType::DT_FLOAT); 
```

步骤3 设置矩阵shape信息。 

```javascript
cubeTiling.SetShape(M, N, K); cubeTiling.SetOrgShape(M, N, K); 
```

步骤4 设置可用空间大小信息。 

设置Matmul计算时可用的L1 Buffer/L0C Buffer/Unified Buffer空间大小，-1表示 AI处理器对应Buffer的大小。 

```javascript
cubeTiling.SetBufferSpace(-1, -1, -1); 
```

步骤5 按需设置其他参数，比如设置bias参与计算。 

```javascript
cubeTiling.SetBias(true); 
```

步骤6 获取Tiling参数。 

```txt
MatmulLeakyreluCustomTilingData tiling;  
if (cubeTiling.GetTiling(tiling.cubeTilingData) == -1){  
return ge::GRAPH_FAILED;  
} 
```

步骤7 Tiling参数的序列化保存等其他操作。 

----结束 

# 说明

● 特别的对于多核场景，需要通过SetDim接口设置Matmul计算所用的核数，MIX模式（包含 矩阵计算和矢量计算）的设置规则如下： 

分离模式：Matmul API都是从AIV侧发起的，调用Iterate计算时在AIV侧只会起到通知 的作用，通知AIC去做矩阵计算，计算完成后AIC告知AIV计算完成。这个架构下， SetBlockDim设置为实际计算会用到的AI Core（AIC、AIV组合）的数量，SetDim设置 为实际计算会用到的AIV的数量。例如，SetBlockDim时可以设置为20，启动20个AI Core（AIC AIV的组合），SetDim设置为40，表示按照40个AIV进行切分。 

耦合模式：SetBlockDim加载的核数就是Matmul API实际计算会用到的核数，SetDim 和SetBlockDim设置的值是一样的。 

● Matmul高阶API内部实现时需要使用系统workspace，开发者需要： 

在host侧Tiling实现时，设置总的workspace的数值大小（包含用户workspace和系统 workspace），workspace空间由框架来申请并管理。系统workspace的空间大小通过 GetLibApiWorkSpaceSize获取。 size_t userWorkspaceSize $= 0 ;$ size_t systemWorkspaceSize $=$ ascendcPlatform.GetLibApiWorkSpaceSize(); size_t *currentWorkspace $=$ context->GetWorkspaceSizes(1); currentWorkspace[0] $=$ userWorkspaceSize $^ +$ systemWorkspaceSize; 

若算子工程不是自定义算子工程，也不是带有HAVE_WORKSPACE编译宏的Kernel直 调算子工程，kernel侧需要在Matmul初始化前，通过SetSysWorkSpace设置系统 workspace。 // 使用Matmul时必须设置workspace空间 SetSysWorkspace(workspace); if (GetSysWorkSpacePtr() $= =$ nullptr) { return; } 

● 上文介绍的实现方法，AIC侧和AIV侧的代码隔离和核间同步由框架来完成，开发者无需关 心。除该方法外，开发者也可以选择底层编码的方式在分离模式下实现融合算子，这种方式 将更加灵活。采用底层编码方式时，需要注意以下几点： 

通过ASCEND_IS_AIV和ASCEND_IS_AIC实现AIV和AIC代码之间的隔离。 

自行实现AIC和AIV核之间的同步：比如Matmul $^ +$ LeakyRelu算子样例中，需要确保在 AIC完成矩阵计算后，AIV再进行LeakyRelu的计算。 

使用高阶API Matmul时需要设置ASCENDC_CUBE_ONLY，表示仅在AIC侧调用Matmul API。 

使用设置Kernel类型接口设置Kernel类型为KERNEL_TYPE_MIX_xxx，同时启用AIV核和 AIC核。 

```cpp
define ASCENDC_CUBE_ONLY // 指定Matmul运行在AIC上  
KERNEL_TASK_TYPE_DEFAULT(Kernel_TYPE_MIX_AIC_1_2); // 设置Kernel类型为  
KERNEL_TYPE_MIX_xxx  
if ASCEND_IS_AIC{  
    // AIC核进行Matmul计算  
    // AIC核完成计算后，通过AscendC::CrossCoreSetFlag<modeld, pipe>(flagld)发送同步flag  
}  
if ASCEND_IS_AIV{  
    // AIV核通过AscendC::CrossCoreWaitFlagflagld)接收同步flag  
    // AIV核进行LeakyRelu计算  
} 
```

完整样例请参考BareMix样例。 

# 3.3.5.2 通算融合

# 3.3.5.2.1 基础知识

# 说明

本节内容为通算融合算子的理论背景和开发指导，学习本节内容之前，请确保已经掌握矩阵编程 和《HCCL集合通信库用户指南》中的相关知识。 

通算融合算子一般支持如下产品型号： 

Atlas 350 加速卡 

Atlas A3 训练系列产品/Atlas A3 推理系列产品 

Atlas A2 训练系列产品/Atlas A2 推理系列产品 

# 通算融合算子

相比于一般的计算或搬运类算子，通算融合算子将原本串行的通信和计算操作融合在 一起，通过在算子内部进行数据切分，实现了计算和通信任务在算子内的并行执行， 从而提升算子性能。通算融合算子统称为MC²算子，即Matrix Computation & Communication。 

如下图所示，串行的通信算子和计算算子的理想执行耗时为两个算子执行时间的加 和，而在融合通信和计算任务得到的通算融合算子内，将需要通信和计算的数据进行 切分，一次通信和计算的数据量减少，整个通信和计算任务分多次进行，使得计算与 通信流水并行，理论执行耗时大大缩短，从而带来性能收益。 


图 3-66 通信计算融合前后的理论执行耗时对比示意图


![](images/96a06eec273cc75c3945298c64d45d7043e560cf13604d432cd4e4027799a00e.jpg)


# 使用场景和优势

随着模型规模的增长，单设备上的训练和推理在计算能力、内存容量和能效等方面面 临瓶颈，因此分布式并行计算成为必选技术路径。对于大模型分布式训练和推理过程 中的通信和计算任务，可根据通信和计算的依赖关系分为两类： 

# 弱依赖计算通信任务

通信或计算的结果不会立即被对方使用，两者虽有依赖，但在两者中间可以调度 执行其他无依赖的计算或通信任务。如图2所示，通信1与计算1-2、计算4有依赖 关系，通信1与计算1-1、计算2-1、计算2-2、计算3无依赖关系；通信2与计算 2-2、计算4有依赖关系，通信2与计算2-1、计算3无依赖关系。因此，通信1和通 信2都有较大的流水空间，可以被与它们无依赖的计算任务所掩盖。如图3所示， 通信1和通信2均可以被无依赖的计算任务掩盖。在模型中，此类无依赖的通信和 计算可以实现任务级并行，无需做算子融合。因此，弱依赖计算通信任务不适用 通算融合场景。 


图 3-67 弱依赖计算通信任务示意图


![](images/8db82abd53f6c01bd936e32a057757504d0154675694c19abc9b012cc2185743.jpg)



图 3-68 弱依赖计算通信任务的调度模拟示意图


![](images/56451e469044be87998c242a6bec98947745239dce351d09b4222000bb07c5cc.jpg)


# 强依赖计算通信任务

通信或计算的结果立即被对方使用，两者间存在紧密依赖关系。如下图所示，计 算通信任务必须串行执行，在通信1和通信2执行过程中，硬件计算资源闲置，此 类通信计算模式若在模型中大量出现，将导致算力利用率低，通信成为主要性能 瓶颈。强依赖计算通信任务适合融合为通算融合算子，利用通算融合技术提升性 能。 


图3-69 强依赖计算通信任务示意图


![](images/19551a84fea0f0970c6f6ea3e9db663f1c604513eabc40e1b708378419a63b1f.jpg)



图 3-70 强依赖计算通信任务的调度模拟示意图


![](images/aede6d234adeb36b6e71b676538770cf1de5a3e14a52a85da6b7324467abae57.jpg)


通算融合技术与网络模型结构密切相关，一般而言，符合上述强依赖计算通信任务都 有可能通过通算融合算子实现性能提升。 

# 3.3.5.2.2 算子实现

在通算融合类算子的实现中，通信操作使用Hccl高阶API，矩阵乘计算操作使用 Matmul高阶API。关于更多集合通信的内容和相关概念请参考《HCCL集合通信库用户 指南》。通算融合算子的开发过程与一般算子相同，但请注意，当前通算融合算子暂 不支持Kernel直调和入图（GE图）开发，仅支持单算子API调用。 

下文将以AllGatherMatmulCustom算子（简称AllGatherMatmul）的实现为例，从算 子分析、数据流分析、创建算子工程、原型定义、Tiling实现、Kernel实现、编译与运 行等方面介绍通算融合算子的设计和实现流程。本样例中算子的完整代码请参见 AllGatherMatmul样例。该样例仅支持在Atlas A2 训练系列产品/Atlas A2 推理系列 产品上运行。 

# 算子分析

算子分析是指明确算子的数学表达式、输入、输出，核函数的名称等信息。 

步骤1 明确算子的数学表达式及通信计算逻辑。 

AllGatherMatmul算子实现了AllGather通信和Matmul矩阵乘法的融合。算子逻辑 为：对输入的通信矩阵a做AllGather通信得到Matmul计算的左矩阵，即通信结果 gather_out，将gather_out和右矩阵b做Matmul运算得到输出c。对应的数学表达式 为： 

```python
gather_out = AllGather(a)  
c = gather_out * b 
```

步骤2 明确输入、输出和属性。 

a、b为源操作数，a为通信的输入矩阵，形状为[M, K]；b为Matmul的右矩阵，形 状为[K, N]。在样例中，M、K、N分别固定为512、5120、640。 

gather_out为目的操作数，存放AllGather通信结果，形状为[M * rankDim, K]， 其中，rankDim为通信域内的卡数，在样例中固定为8。 

c为目的操作数，存放Matmul运算结果，形状为[M * rankDim, N]。 

算子输入输出的数据类型为float16，format为：ND。 

group为算子属性，表示通信域名称，明确算子运行时所在的通信域。 

步骤3 确定核函数名称和参数。 

本样例中核函数命名为all_gather_matmul_custom。 

根据对算子输入输出的分析，确定核函数的参数aGM，bGM，cGM， gatherOutGM；aGM，bGM为输入在Global Memory上的内存地址，cGM， gatherOutGM为输出在Global Memory上的内存地址。注意，核函数的参数和单 算子API调用的输入输出在命名上存在区别，原因是核函数的参数是输入输出在 Global Memory上的内存地址，而单算子API调用时输入输出的类型是 aclTensor，两者并不完全一致。 

步骤4 确定算子实现所需接口。 

算子涉及AllGather通信，查看Ascend C API参考中的通信相关接口，需要使用 Hccl高阶API来实现AllGather通信。 

算子涉及Matmul左右矩阵在外部存储和内部存储间的数据搬运，查看Ascend C API参考中的数据搬运接口，需要使用DataCopy来实现数据搬运。 

计算过程涉及矩阵计算操作，查看Ascend C API参考中的矩阵计算相关接口，需 要使用Matmul高阶API实现矩阵乘计算。 

----结束 


表 3-14 AllGatherMatmulCustom 算子规格


<table><tr><td>算子类型
(Opacity)</td><td colspan="4">AllGatherMatmulCustom</td></tr><tr><td rowspan="5">算子输入输出</td><td>name</td><td>shape</td><td>data type</td><td>format</td></tr><tr><td>a</td><td>[512, 5120]</td><td>float16</td><td>ND</td></tr><tr><td>b</td><td>[5120, 640]</td><td>float16</td><td>ND</td></tr><tr><td>c</td><td>[4096, 640]</td><td>float16</td><td>ND</td></tr><tr><td>gather_out</td><td>[4096, 5120]</td><td>float16</td><td>ND</td></tr><tr><td>算子属性</td><td colspan="4">group(char*), Host侧标识通信域的字符串, 表示通信域名称。</td></tr><tr><td>核函数名称</td><td colspan="4">all_gather_matmul_custom</td></tr></table>

# 数据流分析

AllGatherMatmul算子的数据在卡间进行AllGather通信，在卡内进行Matmul计算， 通信和计算按照数据切分后的主块、尾块分多次进行，流水互相掩盖。分析过程中， 假定通信矩阵的切分策略为按M轴进行切分，切分后主块数（tileCnt）为2，尾块数 （tailCnt）为1，则可得到通信计算掩盖示意图如下。 


图 3-71 AllGatherMatmul 通信计算掩盖示意图


![](images/d0a099e3ff1ca4256fa1aa2ca988e8c3fb027836b55307832e1b6dce2270e475.jpg)


AllGather的功能为将通信域内所有卡的输入按照卡id重新排序，然后拼接起来，再将 结果发送到所有卡。因此，AllGather的结果中包含本卡数据，即本卡输入的通信矩阵 a，算子无需等待这部分数据的通信完成，也无需对数据进行切分，可直接基于完整的 通信矩阵a进行Matmul计算。AllGatherMatmul算子首先做本卡数据的Matmul计算， 这样做的好处在于主块1的通信能与Matmul计算互相掩盖，同时，主块1、主块2、尾 块1的计算无需再包括对本卡数据的Matmul计算，可以减少后续主尾块的计算量，增 加通信计算的掩盖率，从而提高性能。注意，不是所有的通算融合算子都适合首先进 行本卡数据的Matmul计算。因为AllGatherMatmul算子的通信在计算之前，所以先进 行本卡数据的Matmul计算，可以实现本卡数据计算和第一次通信之间的互相掩盖。如 果是计算在通信前的算子，如MatmulAllReduce，建议将本卡数据的计算放在最后， 与最后一次通信互相掩盖，如下图所示。 


图 3-72 MatmulAllReduce 通信计算掩盖示意图


![](images/8a4e530c6bee45eefbc6099cb82c1398c86a3d907efccce0f4c39a7680e39bbe.jpg)


AllGatherMatmul算子逻辑分析： 

步骤1 AI Core将要执行的通信信息写入Global Memory中的消息区，实现任务下发。消息区 是特定地址的Global Memory，AI Core和AI CPU通过向其写入和轮询读取来实现消息 在两者间的传递，这些操作统一封装于Hccl高阶API中。 


图 3-73 通算融合算子通信流程示意图


![](images/d1e3f659c355a0413d4a2b5278fbbd0c2ebbf73a7da4caa3130258be00a54063.jpg)


步骤2 AI CPU从消息区读取到所有通信任务信息，开始基于HCCS（华为缓存一致性系统，用 于CPU/NPU之间的高速互联）或RoCE（承载在融合以太网上的RDMA技术，即跨越以 太网的RDMA通信方式）等链路执行第一轮AllGather集合通信任务。与此同时，AI Core开始对本卡数据进行Matmul计算。 

下图是通信卡数为4时，第一轮通信与本卡计算的示意图。tile 1表示图示为第一轮通 信和与其相互掩盖的矩阵乘计算的处理流程。图中切分后的小矩阵中形如X-Y的数字表 示它所在的数据块对应于第X张卡第Y块数据。 


图 3-74 AllGatherMatmul 第一轮通信与 rank0 上的本卡数据矩阵乘示意图


![](images/1b34dca57fd77e240d6b37f98f9048c1f5084bc74b1223de97b72cb1f2447c82.jpg)


步骤3 AI CPU完成第一轮通信任务后，向消息区写入第一轮通信任务已完成的消息，并开始 执行第二轮通信任务。同时，AI Core在完成本卡数据的Matmul计算后，通过轮询消 息区等到第一轮通信任务已完成的消息，开始进行第一轮通信结果即主块1的Matmul 计算。 

下图是通信卡数为4时，第二轮通信与rank0计算的示意图。tile 2表示图示为第二轮通 信和与其相互掩盖的矩阵乘计算的处理流程。 


图 3-75 AllGatherMatmul 第二轮通信与 rank0 上主块 1 的矩阵乘示意图


![](images/017b35fd010724bf049145e5054a617aa5155df899895c20931f4bfb628fd2bb.jpg)


步骤4 类似步骤3，逐步完成剩余所有数据块的通信和计算。 

----结束 

# 创建算子工程

创建通算融合算子的算子工程与一般算子相同，具体请参考2.10.2.2 创建算子工程章 节。本样例基于如下原型定义json文件，使用自定义算子工程生成工具msOpGen，为 AllGatherMatmul算子创建算子工程。 

```json
{
    "op": "AllGatherMatmulCustom",
    "input_desc": [
        "name": "a",
        "param_type": "required",
        "format": [
            "ND"
        ],
        "type": [
            "float16"
        ]
   ],
    {
        "name": "b",
        "param_type": "required",
        "format": [
            "ND"
        ],
        "type": [
            "float16"
        ]
    }
},
"output_desc": [
    "name": "c",
    "param_type": "required",
    "format": [
            "ND"
        ],
    "type": [
            "float16"
        ]
] 
```

```snap
}，{"name": "gather_out","param_type": "required","format": [ND"],"type":[float16"]}，]，"attr":[{"name":"group","type":"string","default_value":"","param_type":"required"}]  
} 
```

# 算子原型定义

相比于一般算子，通算融合算子在实现算子原型定义时，有如下约束： 

必须定义一个表示算子通信域名称的属性。通信域是集合通信执行的上下文，管 理对应的通信实体（例如一个NPU就是一个通信实体）和通信所需的资源。 

必须通过原型注册中的MC2接口注册该算子为通算融合算子，并通过HcclGroup 接口配置该算子的通信域名称。 

AllGatherMatmul算子使用"group"属性表示该算子的通信域名称，其在算子原型中定 义如下： 

```txt
this->Attr("group").AttrType(REQUIRED).String(); // "group"为通算融合算子的属性，表示通信域名称，原型定义中的String类型对应单算子API中的char*类型  
...  
this->MC2().HcclGroup("group"); // 将"group"属性配置为该算子的通信域名称 
```

AllGatherMatmul算子的完整原型定义如下： 

```cpp
namespace ops {
class AllGatherMatmulCustom : public OpDef {
public:
explicit AllGatherMatmulCustom(const char *name) : OpDef(name)
{
    this->Input("a");
    .ParamType(REQUIRED)
    .DataType({ge::DT_FLOAT16})
    .Format({ge::FORMAT_ND})
    .UnknownShapeFormat({ge::FORMAT_ND});
    this->Input("b");
    .ParamType(REQUIRED)
    .DataType({ge::DT_FLOAT16})
    .Format({ge::FORMAT_ND})
    .UnknownShapeFormat({ge::FORMAT_ND})
    .IgnoreContiguous();
    this->Output("c");
    .ParamType(REQUIRED)
    .DataType({ge::DT_FLOAT16})
    .Format({ge::FORMAT_ND})
    .UnknownShapeFormat({ge::FORMAT_ND});
    this->Output("gather_out")
    .ParamType(REQUIRED)
    .DataType({ge::DT_FLOAT16})
    .Format({ge::FORMAT_ND}) 
```

```cpp
.UnknownShapeFormat({ge::FORMAT_ND}); this->Attr("group").AttrType(REQUIRED).String(); this->AlCore().SetTiling(AllGatherMatmulCustomTilingFunc); //注册 AllGatherMatmulCustomTilingFunc为Tiling入口函数 this->AlCore().AddConfig("ascendxxx"); //ascendxxx请修改为对应的AI处理器型号。 this->MC2().HcclGroup("group"); } }; OP_ADD(AllGatherMatmulCustom); } 
```

# Tiling 实现

通算融合算子Tiling策略的设计主要包括通信切分策略、Matmul多核切分和核内切分 策略。 

通信切分策略：每轮通信数据块的大小，对通算融合算子的性能有较大影响。样 例中按照主块M轴长度448对通信矩阵A的M轴进行切分。具体场景中如何确定切 分策略请参考MC²算子性能调优案例。 

Matmul多核切分和核内切分: 

多核切分: 根据当前核数，对输入shape的M、K、N进行多核切分，得到单核 内shape大小singleCoreM、singleCoreK、singleCoreN。 

核内切分: 根据Local Memory的大小约束，对单核内的shape大小进一步切 分，得到A、B、C矩阵参与一次矩阵乘指令的shape大小baseM、baseN、 baseK。 

如上所述，通信矩阵被切分为主块、尾块，主块、尾块的通信结果以及本卡数据 需要分别进行Matmul计算。如下图，主块、尾块和本卡数据在M轴的长度分别为 tileM、tailM和rankM，即Matmul计算时的左矩阵存在三种不同的形状，因此需 要分别以通信矩阵主块、尾块和本卡数据块的大小为矩阵乘原始的输入形状，调 用Matmul高阶API提供的Tiling接口，得到对应这三种形状的多核切分和核内切分 策略。这里，singleCoreM、baseM等概念和相关原理的介绍请参考3.3.3.1 基础 知识。 


图 3-76 AllGatherMatmul 算子在 rank0 的矩阵乘示意图


![](images/c699ecbbb3ca9d6d3ee53612ec6764199d5091c66470f583ca08252754e78982.jpg)


下面给出Tiling实现的关键步骤： 

步骤1 定义AllGatherMatmul算子的Tiling结构体。 

通信和Matmul融合得到的通算融合算子的Tiling结构体一般包括如下三个部分： 

Hccl高阶API的Tiling结构体。定义Mc2InitTiling和Mc2CcTiling参数。 Mc2InitTiling参数用于初始化通信任务配置，必须定义为算子Tiling结构体的第一 个参数。Mc2CcTiling为具体每个通信任务的参数配置，由于AllGatherMatmul算 子中只有AllGather一个通信任务，因此仅需定义一个Mc2CcTiling参数。 

Matmul高阶API的Tiling结构体TCubeTiling。一般而言，主块、尾块和本卡数据 的shape是不同的，由于TCubeTiling只能存储对一个输入形状进行Tiling计算得到 的结果，因此需要分别定义主块、尾块和本卡数据块的Tiling结构体，来存放它们 的多核切分和核内切分策略。 

● AllGatherMatmul算子额外需要的自定义结构体AllGatherMatmulTiling。 


AllGatherMatmul算子的完整Tiling结构体定义如下：


```c
struct AllGatherMatmulTiling {
    uint32_t rankM; // A矩阵M轴的长度
    uint32_t rankN; // B矩阵N轴的长度
    uint32_t rankK; // A、B矩阵K轴的长度
    uint32_t tileNum; // 主块个数
    uint32_t tailM; // 尾块的M轴长度
    uint32_t tailNum; // 尾块个数（0或1）
}; 
```

步骤2 获取AllGatherMatmul算子的Tiling结构体对象指针。 

AllGatherMatmulCustomTilingData *tiling $=$ context->GetTilingData<AllGatherMatmulCustomTilingData>(); 

context为TilingContext的对象指针，该指针由框架自动从注册的Tiling入口函数 AllGatherMatmulCustomTilingFunc传入，用于保存算子Tiling计算的上下文。在 AllGatherMatmul算子的Tiling实现中，通过该上下文context获取计算Tiling所需要的 输入输出shape、输入属性等参数，然后将Tiling结果（例如TilingKey、TilingData） 保存至上下文中，供后续算子执行时使用。 

步骤3 设置算子自定义的Tiling结构体参数。 

```c
tiling->cfgtileNum = rankM / TILE_M; // TILE_M在样例中为常量448，表示通信数据块切分后的主块在M轴的长度
tiling->cfg.tailM = rankM % TILE_M;
tiling->cfg.tailNum = (rankM % TILE_M == 0) ? 0 : 1;
tiling->cfg rankings = rankM;
tiling->cfg rankings = rankN;
tiling->cfg rankings = rankK; 
```

步骤4 设置Matmul高阶API Tiling结构体。 

通过matmul_tiling::MultiCoreMatmulTiling获取TCubeTiling结构体，首先创建多核 Tiling对象mmTiling，然后设置A、B、C的参数类型信息，M、N、K形状信息等，最 后调用GetTiling接口，获取Tiling信息，具体方法可详见Matmul Tiling类。 

AllGatherMatmul算子中将上述逻辑封装为matmulTilingFunc函数，再分别根据主 块、尾块和本卡数据的形状大小，调用matmulTilingFunc函数，得到对应的 TCubeTiling参数。 

//封装设置TCubeTiling结构体的函数为matmulTilingFunc   
auto matmulTilingFunc $= [\& ]$ (int64_t m,int64_t n,int64_t k,TCubeTiling &cubeTiling) -> bool{ matmul_tiling::MultiCoreMatmulTiling mmTiling;   
mmTiling.SetATOType(matmul_tiling::TPosition:GM，matmul_tiling::CubeFormat::ND,   
matmul_tiling::DataType::DT_FLOAT16);   
mmTiling.SetBType(matmul_tiling::TPosition:GM，matmul_tiling::CubeFormat::ND,   
matmul_tiling::DataType::DT_FLOAT16);   
mmTiling.SetCType(matmul_tiling::TPosition:GM，matmul_tiling::CubeFormat::ND,   
matmul_tiling::DataType::DT_FLOAT16);   
mmTiling.SetBias(false);   
mmTiling.SetDim(aicCoreNum);   
mmTiling.SetShape(m,n,k);   
mmTiling.SetOrgShape(m,n,k);   
mmTiling.SetBufferSpace(L1_buffer_SIZE); if(mmTiling.GetTiling(cubeTiling) $! = 0$ ）{ return false; } return true;   
}；   
//设置本卡数据的Matmul TCubeTiling结构体   
if(!matmulTilingFunc(rankM,rankN,rankK,tiling->localTiling)){ ERROR_LOG("Get local matmul tiling failed"); return ge::GRAPH_FAILED;   
}   
//设置主块的Matmul TCubeTiling结构体   
if(!matmulTilingFunc(TILE_M,rankN,rankK,tiling->tileTiling)){ ERROR_LOG("Get tile matmul tiling failed"); return ge::GRAPH_FAILED;   
}   
//设置尾块的Matmul TCubeTiling结构体   
if(!matmulTilingFunc(rankM % TILE_M,rankN,rankK,tiling->tailTiling)){ ERROR_LOG("Get tail matmul tiling failed"); return ge::GRAPH_FAILED; 

步骤5 设置Hccl高阶API Tiling结构体。 

根据通信任务类型、算法配置等，创建一个Mc2CcTilingConfig类对象，通过向 GetTiling方法传入算子Tiling结构体中mc2InitTiling和mc2CcTiling成员的引用，完成 

需要传递给Kernel侧的Mc2InitTiling参数和Mc2CcTiling参数的获取。Hccl高阶API Tiling结构体的具体使用方法详见Hccl Tiling使用说明。 

```cpp
uint32_t opType = HCCL_CMD_ALLGATHER; //设置通信任务类型  
std::string algConfig = "AllGather=level0:doublering"; //设置通信算法，该参数为预留字段，配置后不生效  
uint32_t reduceType = HCCL Reduce SUM; //设置Reduce操作类型，仅对有归约操作的通信任务有效，作为AllGather通信，可以直接配置默认值HCCL Reduce SUM  
AscendC::Mc2CcTilingConfig mc2CcTilingConfig(group, opType, algConfig, reduceType);  
mc2CcTilingConfig.GetTiling(tiling->mc2InitTiling);  
mc2CcTilingConfig.SetSkipLocalRankCopy(0); //输出gatherOut需带有本卡的A矩阵，因此设置为0  
mc2CcTilingConfig.GetTiling(tiling->mc2CcTiling); 
```

----结束 

# Kernel 实现

在AllGatherMatmul算子的Kernel实现中，需要对本卡数据、通信主块、通信尾块共 三种形状的左矩阵进行Matmul运算，为避免重复代码，有必要抽象出一个通用的适用 于不同输入形状的Matmul计算函数。设计该Matmul计算函数前，需要考虑Matmul 计算需要的基本信息，罗列如下： 

输入A、B矩阵和输出C矩阵的地址。 

TCubeTiling结构体：包含矩阵A、B、C的形状、数据类型等信息，以及A、B矩阵 进行Matmul运算时在核间和核内的切分策略。 

除了上述Matmul运算所需的信息外，为了快速实现Matmul矩阵乘法，可以使用 Matmul高阶API中的Matmul对象来执行计算。如果Matmul对象在Matmul计算函数 中定义，每次调用该函数时都会实例化Matmul对象并释放资源，这将导致较大的运行 时开销。因此，将该对象也作为Matmul计算函数的参数，以实现对象的复用。 

综上所述，在Kernel实现中定义的适用于不同输入形状的Matmul计算函数如下。其中 Matmul计算函数函数名定义为MatmulKernel，入参aGM、bGM、cGM表示需要运算 的原始输入输出矩阵的地址，入参tiling表示TCubeTiling结构体，入参mm对应 Matmul高阶API的实现类。MATMUL_TYPE是特化了MatmulType模板的类型别名。 

```txt
using MATMUL_TYPE = MatmulType<AscendC::TPosition::GM, CubeFormat::ND, half>;  
__aicore__ inline void MatmulKernel(GM_ADDR aGM, GM_ADDR bGM, GM_ADDR cGM, TCubeTiling &tiling, Matmul<MATMUL_TYPE, MATMUL_TYPE, MATMUL_TYPE> &mm) 
```

MatmulKernel函数的实现步骤如下。 

步骤1 TCubeTiling结构体存储了Matmul计算所需的核数，在无需计算的核上直接返回，结 束计算。 

```txt
if (GetBlockIdx() >= tiling_usedCoreNum) { return; } 
```

步骤2 Matmul高阶API要求使用GlobalTensor作为输入输出矩阵，因此，根据函数输入的A、 B、C矩阵在Global Memory的地址，分别定义aGlobal、bGlobal、cGlobal三个 GlobalTensor。 

GlobalTensor<half> aGlobal, bGlobal, cGlobal;  
aGlobal.SetGlobalBuffer(reinterpret_cast<__gm__ half $\ast >$ (aGM), tiling.M * tiling.Ka);  
bGlobal.SetGlobalBuffer(reinterpret_cast<__gm__ half $\ast >$ (bGM), tiling.Ka * tiling.N);  
cGlobal.SetGlobalBuffer(reinterpret_cast<__gm__ half $\ast >$ (cGM), tiling.M * tiling.N); 

步骤3 为了实现多核并行，提升计算效率，将矩阵数据进行切分，切分后的数据分配到不同 的核上进行处理。这里采用了不切分K轴、仅切分M、N轴的切分策略，示意图如下。 在这种场景下，每个核需要计算待处理的矩阵数据相对于原始矩阵的偏移量，并将偏 移后的矩阵作为传入A、B、C矩阵时的入参。同时，为支持分核后的尾块数据的处 

理，每个核需要计算实际处理的singleCoreM、singleCoreN大小，并在下一步中通过 调用Matmul高阶API进行设置。 


图 3-77 Matmul 计算分核示意图


![](images/eb7fa052baa16ca8fcd134ea263e36c2bd3aefa52f3815c8afe304d21aee701a.jpg)


![](images/aae3b55c6fe06a84119dbeb49ccd1760e18f08117e0456bb8c9d74594a5197a8.jpg)



矩阵b



=


![](images/45daf335d7b7fac9586c0ff515ceddd790368d0e1ca1a7e20aaad03e8f5088be.jpg)



矩阵c


```rust
int mSingleBlocks = (tiling.M + tiling.singleCoreM - 1) / tiling.singleCoreM;  
int mCoreIndex = GetBlockIdx() % mSingleBlocks;  
int nCoreIndex = GetBlockIdx() / mSingleBlocks;  
// 计算当前核需要处理的矩阵数据相对于原始矩阵的偏移  
int offsetA = mCoreIndex * tiling.Ka * tiling.singleCoreM;  
int offsetB = nCoreIndex * tiling(singleCoreN;  
int offsetC = mCoreIndex * tiling.N * tiling.singleCoreM + nCoreIndex * tiling.singleCoreN;  
// 计算当前核的singleCoreM/singleCoreN，作为后续SetTail接口的入参  
int tailM = Std::min(tiling.M - mCoreIndex * tiling.singleCoreM, tiling.singleCoreM);  
int tailN = Std::min(tiling.N - nCoreIndex * tiling.singleCoreN, tiling.singleCoreN); 
```

步骤4 调用Matmul高阶API设置Matmul计算的原始完整的形状、当前核处理的输入输出矩阵 的地址和计算的实际singleCoreM、singleCoreN的大小，并完成矩阵乘运算。 

```txt
mm.SetOrgShape(tiling.M, tiling.N, tiling.Ka, tiling.Kb);  
mm.setTensorA(aGlobal[offsetA]);  
mm.setTensorB(bGlobal[offsetB]);  
mm.setTail(tailM, tailN);  
mm.IterateAll(cGlobal[offsetC]); 
```

# ----结束

AllGatherMatmul算子的核函数定义如下，aGM、bGM、cGM、gatherOutGM参数含 义如算子分析中所述，workspaceGM和tilingGM分别表示wrokspace空间和tiling数据 在Global Memory的地址。 

```txt
extern "C" __global__ __aicore__ void all_gather_matmul/custom(GM_ADDR aGM, GM_ADDR bGM, GM_ADDR cGM, GM_ADDR gatherOutGM, GM_ADDR workspaceGM, GM_ADDR tilingGM) 
```

下面介绍AllGatherMatmul算子主流程实现的具体步骤。 

步骤1 Matmul计算依赖AIC核，因此控制算子逻辑仅运行于AIC中。通过ASCEND_IS_AIV 宏，判断如果当前核为AIV核，直接返回，结束当前核的运行。 

```txt
if ASCEND_IS_AIV{ return; } 
```

步骤2 注册算子Tiling结构体、获取Tiling，并初始化TPipe。 

```c
REGISTER_TILING_DEFAULT(AllGatherMatmulCustomTilingData);  
GET_TILING_DATA(tilingData, tilingGM);  
TPipe pipe; 
```

步骤3 定义并赋值后续计算所需变量。 

```javascript
auto &&localTiling = tilingData.localTiling;  
auto &&tileTiling = tilingDatatileTiling;  
auto &&tailTiling = tilingData.tailTiling;  
const auto tileNum = tilingData.cfgtileNum; //主块数量  
const auto tailNum = tilingData.cfg.tailNum; //尾块数量  
const auto aTileEleCnt = tileTiling.M * tileTiling.Ka; //通信矩阵主块元素数  
const auto aTileSize = tileTiling.M * tileTiling.Ka * sizeof(half); //通信矩阵主块字节数  
const auto cTileSize = tileTiling.M * tileTiling.N * sizeof(half); //通信矩阵主块对应在输出矩阵的字节数  
const auto aTailEleCnt = tailTiling.M * tailTiling.Ka; //通信矩阵尾块元素数  
const auto aRankEleCnt = localTiling.M * localTiling.Ka; //通信矩阵元素数  
const auto aRankSize = localTiling.M * localTiling.Ka * sizeof(half); //通信矩阵字节数  
const auto cRankSize = localTiling.M * localTiling.N * sizeof(half); //通信矩阵对应在输出矩阵的字节数 
```

步骤4 初始化hccl对象并下发AllGather通信任务。 

```cpp
Hclhcl;   
GM_ADDR contextGM = GetHcclContext<HCCL_GROUP_ID_0>();   
hcclInitV2(contextGM, &tilingData);   
hccl.SetCcTilingV2(offsetOf(AllGatherMatmulCustomTilingData, mc2CcTiling));   
auto handleId = hccl.AllGathertrue>(aGM, gatherOutGM, aTileEleCnt,   
HcclDataType::HCCL_DATA_TYPE_FP16, aRankEleCnt, tileNum);   
auto tailHandleId = hccl.AllGathertrue>(aGM + tileNum * aTileSize, gatherOutGM + tileNum * aTileSize, aTailEleCnt, HcclDataType::HCCL_DATA_TYPE_FP16, aRankEleCnt, tailNum); 
```

步骤5 初始化Matmul对象，对本卡数据进行Matmul计算。 

```c
Matmul<MATMUL_TYPE, MATMUL_TYPE, MATMUL_TYPE> mm;  
REGIST_MATMUL_OBJ(GetTPipePtr(), GetSysWorkSpacePtr(), mm);  
mm Init(&localTiling);  
MatmulKernel(aGM, bGM, cGM + hccl.GetRankld() * cRankSize, localTiling, mm); 
```

步骤6 逐轮等待主块的通信完成，并对其进行Matmul计算。 

auto aAddr = gatherOutGM;   
auto cAddr $=$ cGM;   
mmInit(&tileTiling);   
for (uint32_t i = 0; i < tileNum; i++) { hccl.Wait(handleld); for (uint32_t rankld = 0; rankld < hccl.GetRankDim(); rankld++) { if (rankld == hccl.GetRankld()) continue; MatmulKernel(aAddr + rankld * aRankSize, bGM, cAddr + rankld * cRankSize, tileTiling, mm); } aAddr $+ =$ aTileSize; cAddr $+ =$ cTileSize; 

步骤7 等待尾块的通信完成，并对其进行Matmul计算。 

```txt
aAddr = gatherOutGM + tileNum * aTileSize;  
cAddr = cGM + tileNum * cTileSize;  
if (tailNum > 0) {  
    mmInit(&tailTiling);  
    hccl.Wait(tailHandleId);  
    for (uint32_t rankld = 0; rankld < hccl.GetRankDim(); rankld++) {  
        if (rankld == hccl.GetRankld())  
            continue;  
        MatmulKernel(aAddr + rankld * aRankSize, bGM, cAddr + rankld * cRankSize, tailTiling, mm);  
    }  
} 
```

步骤8 释放资源。 

```javascript
mm.End();  
hccl_FINALize(); 
```

# ----结束


整合前述代码 ，完整Kernel代码如下。


```cpp
define ASCENDC_CUBE_ONLY
#include "kernel_operator.h"
#include "lib/matmul_intf.h"
#include "all_gather_matmul_custom_tiling.h"
using namespace AscendC;
using MATMUL_TYPE = MatmulType<AscendC::TPosition::GM, CubeFormat::ND, half>;
__aicore__inline void MatmulKernel(GM_ADDR aGM, GM_ADDR bGM, GM_ADDR cGM, TCubeTiling &tiling,
Matmul<MATMUL_TYPE, MATMUL_TYPE, MATMUL_TYPE> &mm)
{
if (GetBlockIdx() >= tiling_usedCoreNum) {
return;
}
GlobalTensor<half> aGlobal, bGlobal, cGlobal;
aGlobal.SetGlobalBuffer(reinterpret_cast<gm__half>(aGM), tiling.M * tiling.Ka);
bGlobal.SetGlobalBuffer(reinterpret_cast<gm__half>(bGM), tiling.Ka * tiling.N);
cGlobal.SetGlobalBuffer(reinterpret_cast<gm__half>(cGM), tiling.M * tiling.N);
int mSingleBlocks = (tiling.M + tiling.singleCoreM - 1) / tiling.singleCoreM;
int mCoreIndex = GetBlockIdx() % mSingleBlocks;
int nCoreIndex = GetBlockIdx() / mSingleBlocks;
int offsetA = mCoreIndex * tiling.Ka * tiling(singleCoreM;
int offsetB = nCoreIndex * tiling.singleCoreN;
int offsetC = mCoreIndex * tiling.N * tiling-singleCoreM + nCoreIndex * tiling.singleCoreN;
int tailM = Std::min(tiling.M - mCoreIndex * tiling-singleCoreM, tiling-singleCoreM);
int tailN = Std::min(tiling.N - nCoreIndex * tiling.singleCoreN, tiling-singleCoreN);
mm.SetOrgShape(tiling.M, tiling.N, tiling.Ka, tiling.Kb);
mm.SetTensorA(aGlobal[offsetA]);
mm.SetTensorB(bGlobal[offsetB]);
mm.SetTail(tailM, tailN);
mm.IterateAll(cGlobal[offsetC]);
}
extern "C" __global__ __aicore__void all_gather_matmul/custom(GM_ADDR aGM, GM_ADDR bGM,
GM_ADDR cGM, GM_ADDR gatherOutGM, GM_ADDR workspaceGM,
GM_ADDR tilingGM)
{
if ASCEND_IS_AIV {
return;
}
REGISTER_TILING_DEFAULT(AllGatherMatmulCustomTilingData);
GET_TILING_DATA(tilingData, tilingGM);
TPipe pipe;
auto &&localTiling = tilingData.localTiling;
auto &&tileTiling = tilingDatatileTiling;
auto &&tailTiling = tilingData.tailTiling;
const auto tileNum = tilingData.cfgtileNum; //主块数量
const auto tailNum = tilingData.cfg.tailNum; //尾块数量
const auto aTileEleCnt = tileTiling.M * tileTiling.Ka; //通信矩阵主块元素数
const auto aTileSize = tileTiling.M * tileTiling.Ka * sizeof(half); //通信矩阵主块字节数
const auto cTileSize = tileTiling.M * tileTiling.N * sizeof(half); //输出矩阵主块字节数
const auto aTailEleCnt = tailTiling.M * tailTiling.Ka; //通信矩阵尾块元素数
const auto aRankEleCnt = localTiling.M * localTiling.Ka; //单卡通信矩阵元素数
const auto aRankSize = localTiling.M * localTiling.Ka * sizeof(half); //单卡通信矩阵字节数
const auto cRankSize = localTiling.M * localTiling.N * sizeof(half); //单卡输出矩阵字节数
Hccl hccl;
GM_ADDR contextGM = GetHcclContext<HCCL_GROUP_ID_0>(); 
```

auto handled = hccl.AllGathertrue>(aGM, gatherOutGM, aTileEleCnt,   
HcclDataType::HCCL_DATA_TYPE_FP16, aRankEleCnt, tileNum);   
auto tailHandleld $=$ hccl.AllGathertrue>(aGM $^+$ tileNum \* aTileSize, gatherOutGM $^+$ tileNum \* aTileSize,   
aTailEleCnt, HcclDataType::HCCL_DATA_TYPE_FP16, aRankEleCnt, tailNum); MatmulM MATMUL_TYPE, MATMUL_TYPE, MATMUL_TYPE> mm; REGIST_MATMUL_OBJ(GetTPipePtr(), GetSysWorkSpacePtr(), mm); mm Init(&localTiling); MatmulKernel(aGM, bGM, cGM + hccl.GetRankld() \* cRankSize, localTiling, mm); auto aAddr $=$ gatherOutGM; auto cAddr $=$ cGM; mmInit(&tileTiling); for (uint32_t i = 0; i < tileNum; i++) { hcl.Wait(handleld); for (uint32_t rankld = 0; rankld < hccl.GetRankDim(); rankld++) { if (rankld == hccl.GetRankld()) continue; MatmulKernel(aAddr + rankld \* aRankSize, bGM, cAddr + rankld \* cRankSize, tileTiling, mm); } aAddr $+ =$ aTileSize; cAddr $+ =$ cTileSize; } aAddr $=$ gatherOutGM $^+$ tileNum \* aTileSize; cAddr $=$ cGM $^+$ tileNum \* cTileSize; if (tailNum > 0) { mm Init(&tailTiling); hccl.Wait(tailHandleld); for (uint32_t rankld = 0; rankld < hccl.GetRankDim(); rankld++) { if (rankld == hccl.GetRankld()) continue; MatmulKernel(aAddr + rankld \* aRankSize, bGM, cAddr + rankld \* cRankSize, tailTiling, mm); } } mm.End(); hccl.Finallyize(); 

# 编译和运行

下面从编译、安装、运行三个步骤对AllGatherMatmul样例作简要介绍。 

# 步骤1 编译

参考AllGatherMatmul样例中生成自定义算子工程、编译算子的命令，运行install.sh 脚本完成编译。 

样例目录结构如下，AllGatherMatmulCustom目录为必要的算子实现，install.sh脚本 使用msOpGen在21_all_gather_matmul_custom目录下创建一个CustomOp目录，并 将算子实现文件复制到对应目录下，再调用msOpGen生成的编译入口脚本build.sh编 译算子。 

```javascript
21_all_gather_matmul_custom  
—AcNInvocation //通过aclnn调用的方式调用AllGatherMatmulCustom算子  
—AllGatherMatmulCustom // AllGatherMatmulCustom算子工程  
—all_gather_matmul_custom.json // AllGatherMatmulCustom算子的原型定义json文件  
—all_gather_matmul_demo_def.h // AllGatherMatmulCustom算子参数配置  
—install.sh //脚本，调用msOpGen生成自定义算子工程，并编译 
```

msOpGen生成的CustomOp目录结构如下。 

```txt
CustomOp // msOpGen生成的AllGatherMatmul自定义算子工程  
—cmake // host侧实现文件 
```

```txt
op_kernel // kernel侧实现文件  
scripts //自定义算子工程打包相关脚本所在目录  
build.sh //编译入口脚本  
CMakeLists.txt //算子工程的CMakeLists.txt  
CMakePresets.json //编译配置项 
```

# 步骤2 安装

部署自定义算子包前，请确保环境中存在自定义算子包默认部署路径的环境变量 ASCEND_OPP_PATH。 

```txt
查看环境变量输出echo $ASCEND_OPP_PATH 
```

```txt
若无输出，则需设置环境变量，ASCENDINSTALL_PATH为CANN软件包安装路径 source [ASCENDInstall_PATH]/set_env.bash #例如source/usr/local/Ascend/cann/set_env.sh 
```

然后执行如下命令，切换目录为编译出的自定义算子安装包所在目录，并安装自定义 算子包。 

```txt
cd CustomOp/build_out
./custom_opp_<target os>_<target architecture>.run 
```

命令执行成功后，自定义算子包中的相关文件将部署至环境变量ASCEND_OPP_PATH 指向的的vendors/customize目录中。 

# 步骤3 运行

```txt
切换目录为AclNNInvocation目录，执行run.sh脚本运行单算子样例。  
cd ..//AclNNInvocation  
bash run.sh 
```

样例中的AclNNInvocation目录提供了完整的单算子API调用的示例代码。完成前两个 步骤自定义算子的编译部署后，会自动生成单算子API，该API可以直接在应用程序中 调用。算子API的形式一般为“两段式接口”，形如： 

```txt
// 获取算子使用的workspace空间大小  
aclnnStatus aclnnAllGatherMatmulCustomGetWorkspaceSize(const aclTensor *a, const aclTensor *b, char *group, const aclTensor *cOut, const aclTensor *gatherOutOut, uint64_t *workspaceSize, aclOpExecutor **executor);  
// 执行算子  
aclnnStatus aclnnAllGatherMatmulCustom(void *workspace, uint64_t workspaceSize, aclOpExecutor *executor, const aclrtStream stream); 
```

其中aclnnAllGatherMatmulCustomGetWorkspaceSize为第一段接口，主要用于计算 本次API调用计算过程中需要的workspace内存大小。按照该workspaceSize大小申请 Device侧内存，然后调用第二段接口aclnnAllGatherMatmulCustom执行计算。详细 内容请参考单算子API调用章节。 

在通算融合场景，单算子API调用的程序中需要调用HCCL接口参考中的接口创建通信 域，并在多线程上执行AllGatherMatmul算子。以下给出main函数和线程调用函数中 关键步骤的代码示例，仅供参考。 

```cpp
int main(int argc, char **argv)  
{ // 1 AscendCL初始化 if (acclInit(NULL) != ACL_SUCCESS) { ERROR_LOG("acclInit failed"); 
```

returnFAILED;   
}   
//2.通信域创建   
HcclComm comms[RANK_DIM]；//RANK_DIM为卡数，示例中为8   
int32_t devices[RANK_DIM];   
for(int32_t i = 0;i < RANK_DIM;i++) { devices[i] = i;   
}   
if(HcclCommInitAll(RANK_DIM,devices,comms) != HCCL_SUCCESS){ ERROR_LOG("Hccl comm init failed."; (void)aclFinalize(); returnFAILED;   
}   
//3.创建多线程以在通信域的所有卡上都调用AllGatherMatmul算子 std::vector<std::unique_ptr<std::thread>> threads(RANK_DIM); for (uint32_t rankld $= 0$ ;rankld $<$ RANK_DIM; rankld $^{+ + }$ ）{ threads[rankld].reset(new(std::throw) std::thread(&RunOp, rankld, std::ref(comms[rankld])));   
}   
for (uint32_t rankld $= 0$ ;rankld $<$ RANK_DIM; rankld $^{+ + }$ ) { threads[rankld] $\rightharpoonup$ join();   
}   
//4.AscendCL去初始化 (void)aclFinalize(); return SUCCESS; 

在main函数中，通过HcclCommInitAll接口在当前进程统一创建了RANK_DIM张卡的 通信域，一张卡对应后续创建的一个线程。每个线程都调用RunOp函数，该函数负责 卡上运行时资源申请和单算子API的二阶段接口调用。RunOp函数的代码示例如下。 

bool RunOp(uint32_t rankId, HcclComm &comm) 

```c
//1.申请当前线程的context、stream等资源  
aclrtContext context;  
aclrtCreateContext(&context, rankId);  
aclrtStream stream;  
aclrtCreateStream(&stream);  
aclrtSetCurrentContext(context);  
//2.获取当前线程对应卡的通信域名称  
char group[128] = {0};  
HcclGetCommName comm, group);  
//3.申请device侧内存存放算子的输入输出  
//......  
//4.计算workspace大小并申请内存  
size_t workspaceSize = 0;  
aclOpExecutor *handle = nullptr;  
auto ret = aclnAllGatherMatmulCustomGetWorkspaceSize(a, b, group, c, gatherOut, &workspaceSize, &handle);  
void *workspace = nullptr;  
if (workspaceSize != 0) {  
    acltMalloc(&workspace, workspaceSize);  
}  
//5.执行算子  
ret = aclnAllGatherMatmulCustom workspace, workspaceSize, handle, stream);  
//6.同步等待  
ret = acltSynchronizeStreamWithTimeout(stream, 10000); //10000ms流同步超时  
//7.释放算子输入、输出和workspace等device侧内存  
//......  
//8.释放通信域、context、stream等资源  
(void)HcclCommDestroy(comm);  
(void)aclrtDestroyStream(stream);  
(void)aclrtDestroyContext(context);  
(void)aclrtResetDevice(rankId); 
```

```lua
return true; } 
```

----结束 

# 3.3.5.2.3 特性场景

# 重执行

为避免执行通信任务的环境中硬件闪断导致发生通信中断，通算融合算子可通过配置 编译宏与环境变量，开启重执行能力。通算融合算子开启重执行后，AI CPU在检测到 环境异常时，通过下图示意的机制，通知AI Core重新下发通信任务，避免由于硬件闪 断造成的通信中断，提升通信稳定性。 

当前，该能力的支持情况如下： 

Atlas 350 加速卡不支持通算融合算子的重执行。 

Atlas A2 训练系列产品/Atlas A2 推理系列产品不支持通算融合算子的重执行。 

Atlas A3 训练系列产品/Atlas A3 推理系列产品支持通算融合算子的重执行。 


图 3-78 通信任务重执行机制


![](images/61c7d0c7f18cd2f46008c5a7075d1fcee6d361986eb9ebbc4f13a84c89d99132.jpg)


# 开启重执行的条件如下：

通算融合算子的输出内存地址和输入内存地址不相同。 

通算融合算子仅存在Server间通信（Server为计算节点，通常是8卡或16卡的昇腾 NPU设备组成的服务器形态的统称）。 

算子编译时，配置编译宏AICORE_EXCEPTION_RESTART，如下所示。具体的编译 宏配置阶段和方式请参考支持自定义编译选项。 add_ops_compile_options(ALL OPTIONS -DAICORE_EXCEPTION_RESTART) 

配置HCCL重执行环境变量HCCL_OP_RETRY_ENABLE，开启重执行的检测和上报 能力，该环境变量的说明请参考《环境变量参考》“集合通信 > 可靠性相关 > HCCL_OP_RETRY_ENABLE”。请在算子执行前设置该环境变量，具体配置如下： # server间L1需配置为1, 不支持跨超节点，L2配置为0。 export HCCL_OP_RETRY_ENABLE="L1:1, L2:0" 

注意，开启重执行后，若AI Core第一次下发通信任务后通信中断，默认只重执行 一次。若需修改重执行次数或重传间隔时间，请参考《环境变量参考》“集合通 信 > 可靠性相关 > HCCL_OP_RETRY_PARAMS” 。