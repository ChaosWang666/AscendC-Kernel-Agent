<!-- Source: 算子开发指南.md lines 5226-6308 | Section: 2.6 硬件实现 -->

# 2.6 硬件实现

# 2.6.1 基本架构

如下图所示，基于Ascend C开发的算子运行在AI Core上。Ascend C编程模型基于AI Core硬件架构的抽象进行介绍，了解硬件架构能够帮助开发者更好的理解编程模型； 对于需要完成高性能编程的深度开发者，更需要了解硬件架构相关知识，算子实践参 考中很多内容都以本章为基础进行介绍。 

![](images/e62fe51df5acca859fbb179e13a54ce1556f72a6cd8892d0c30f5f611dc79774.jpg)


AI Core负责执行矩阵、矢量计算密集的任务，其包括以下组成部分： 

计算单元：包括Cube（矩阵）计算单元、Vector（矢量）计算单元和Scalar（标 量）计算单元。 

存储单元：包括L1 Buffer、L0A Buffer、L0B Buffer、L0C Buffer、Unified Buffer、BiasTable Buffer、Fixpipe Buffer等专为高效计算设计的存储单元。 

搬运单元：包括MTE1、MTE2、MTE3和FixPipe，用于数据在不同存储单元之间 的高效传输。 

以Atlas A2 训练系列产品/Atlas A2 推理系列产品为例，硬件架构图如下： 

![](images/e79d22effa54421502dd9427cc0f3bc27c60d534d8c2cb16460b26c02fec3cc0.jpg)


本章节首先介绍硬件架构相关的关键概念和术语，以及AI Core的工作模式，为理解后 续内容奠定基础。随后以Atlas A2 训练系列产品/Atlas A2 推理系列产品为例，提供AI Core基本架构的介绍：首先介绍计算单元、存储单元和搬运单元的基本功能与结构， 然后通过典型的数据流和控制流示例，帮助开发者深入理解硬件架构的工作原理。针 对不同产品型号对应的具体架构规格和细节说明需要参考后续2.6.2 架构规格章节。 

# 关键概念和术语

Core 

拥有独立Scalar计算单元的计算核。Scalar计算单元是核内的调度单元，承担了核 内的指令发射等功能。 

AI Core 

AI处理器的计算核，负责执行矩阵、矢量计算密集的任务。 

Cube Core 

矩阵计算核，专注于矩阵计算。由Scalar调度单元、矩阵计算单元、搬运单元等组 成，不包括矢量计算单元。 

Vector Core 

矢量计算核，专注于矢量计算，由Scalar调度单元、矢量计算单元、搬运单元等组 成，不包括矩阵计算单元。 

AIC 

在AI Core分离模式下，一组Cube Core和Vector Core组合中的Cube Core。 

AIV 

在AI Core分离模式下，一组Cube Core和Vector Core组合中的Vector Core。 

# AI Core 的工作模式

分离模式 

AI Core的一种工作模式，矩阵计算单元、矢量计算单元各自对应独立的Scalar调 度单元，分离部署在Cube Core和Vector Core上。将Cube Core和Vector Core按 

照一定比例（1：N）进行组合，这样的组合视为一个AI Core，AI Core的核数以 Cube Core为准。 


图 2-27 分离模式示意图（N 的取值以硬件平台信息获取接口获取的数值为准）


![](images/6583fc6ea517841da3e7df5366551d69e27671299609305eb27873a86b7be0d6.jpg)


# 耦合模式

AI Core的一种工作模式，矩阵计算单元、矢量计算单元对应同一个Scalar调度单 元，部署在一个AI Core上。 


图 2-28 耦合模式示意图


![](images/109b7d202045b016b734a532a31e018a1e5441708a42d7d62e3b7ae5543382df.jpg)


# 说明

Ascend C编程中，不同产品的工作模式如下： 

Atlas 推理系列产品：耦合模式 

Atlas 训练系列产品：耦合模式 

Atlas A2 训练系列产品/Atlas A2 推理系列产品：分离模式 

Atlas A3 训练系列产品/Atlas A3 推理系列产品：分离模式 

Atlas 350 加速卡：分离模式 

Atlas 200I/500 A2 推理产品：耦合模式 

注意：针对Atlas 200I/500 A2 推理产品，硬件的工作模式既可以支持耦合模式，又可以支持分 离模式。耦合模式下，开发者仅需关注AI Core数量，无需关注Vector Core和Cube Core数量； 分离模式下，需要关注AI Core、Vector Core、Cube Core的数量。Ascend C编程场景下，仅支 持耦合模式。 

# 计算单元

计算单元是AI Core中提供强大算力的核心单元，包括三种基础计算单元：Cube（矩 阵）计算单元、Vector（矢量）计算单元和Scalar（标量）计算单元，完成AI Core中 不同类型的数据计算。 

# Cube

Cube计算单元负责执行矩阵运算，以float16数据类型为例，Cube每次执行可完 成两个float16类型的16x16矩阵的乘法操作。如下图所示，高亮部分为Cube计算 

单元及其访问的存储单元，其中L0A存储左矩阵，L0B存储右矩阵，L0C存储矩阵 乘的结果和中间结果。 


图 2-29 Cube 计算单元数据访问


![](images/b746b87732314ce85d7d3cc3be8535ad6ec3b1a8862ada82cc3799233b768208.jpg)


# Vector

Vector负责执行向量运算。向量计算单元执行向量指令，类似于传统的单指令多 数据（Single Instruction Multiple Data，SIMD）指令，每个向量指令可以完成 多个操作数的同一类型运算。向量计算单元可以快速完成两个float16类型的向量 相加或者相乘。向量指令支持多次迭代执行，也支持对带有间隔的向量直接进行 运算。 

如下图所示，Vector所有计算的源数据以及目标数据都要求存储在Unified Buffer 中，Vector指令的首地址和操作长度有对齐要求，通常要求32B对齐，具体对齐要 求参考API的约束描述。 


图 2-30 Vector 计算单元数据访问


![](images/1c65e5d069cfea8721a0a3d0c15834d463cf5aca44fa729d136c77a303da65ac.jpg)


# Scalar

Scalar负责各类型的标量数据运算和程序的流程控制。功能上可以看做一个小 CPU，完成整个程序的循环控制、分支判断、Cube/Vector等指令的地址和参数计 算以及基本的算术运算，并且可以通过在事件同步模块中插入同步符的方式来控 制AI Core中其他执行单元的流水。相对于Host CPU，AI Core中的Scalar计算能力 较弱，重点用于发射指令，所以在实际应用场景中应尽量减少Scalar计算，比如性 能调优时尽量减少if/else等分支判断及变量运算。 

如下图所示：Scalar执行标量运算指令时，执行标准的ALU(Arithmetic Logic Unit)语句，ALU需要的代码段和数据段（栈空间）都来自于GM， 

ICache(Instruction Cache)用于缓存代码段，缓存大小与硬件规格相关，比如为 16K或32K，以2K为单位加载；DCache(Data Cache)用于缓存数据段，大小也与 硬件规格相关，比如为16K，以Cache Line（64Byte）为单位加载。考虑到核内访 问效率最高，应尽量保证代码段和数据段被缓存在ICache和DCache，避免核外访 问； 同时根据数据加载单位不同，编程时可以考虑单次加载数据大小，来提升加 载效率。例如在DCache加载数据时，当数据内存首地址与Cache Line（64Byte） 对齐时，加载效率最高。 


图 2-31 Scalar 对指令和数据的访问


![](images/491a032aead74f2ce220698900c1e10ff7f34e0be2d647b7167e4fbe331b087e.jpg)


# 说明

硬件提供L2Cache用于缓存访问GM的数据（包括代码段、数据段），以此加快访问速度， 提高访问效率。核外L2Cache以Cache Line为单位加载数据，根据硬件规格不同，Cache Line大小不同（128/256/512Byte等）。 

# 存储单元和搬运单元

AI处理器中的计算资源要想发挥强劲算力，必要条件是保证输入数据能够及时准确地 出现在计算单元中，需要精心设计存储系统，保证计算单元所需的数据供应。 

如下图所示：AI Core中包含多级内部存储，AI Core需要把外部存储中的数据加载到内 部存储中，才能完成相应的计算。AI Core的主要内部存储包括：L1 Buffer（L1缓冲 区），L0 Buffer（L0缓冲区），Unified Buffer（统一缓冲区）等。为了配合AI Core 中的数据传输和搬运，AI Core中还包含MTE（Memory Transfer Engine，数据传递引 擎）搬运单元，在搬运过程中可执行随路数据格式/类型转换。 

内部存储单元和搬运单元的具体介绍请参考表2-27和表2-28。 


图 2-32 存储单元


![](images/1f62f576128673493d89c5c75577c78d3abaacf6016c7b532d8eb74313706d68.jpg)



表 2-27 存储单元介绍


<table><tr><td>存储单元</td><td>描述</td></tr><tr><td>L1 Buffer</td><td>L1缓冲区，通用内部存储，是AI Core内比较大的一块数据中转区，可暂存Cube计算单元需要反复使用的一些数据从而减少从总线读写的次数。</td></tr><tr><td>LOA Buffer / LOB Buffer</td><td>Cube指令的输入。</td></tr><tr><td>LOC Buffer</td><td>Cube指令的输出，但进行累加计算的时候，也是输入的一部分。</td></tr><tr><td>Unified Buffer</td><td>统一缓冲区，向量和标量计算的输入和输出。</td></tr><tr><td>BT Buffer</td><td>BiasTable Buffer, 存放矩阵计算中的Bias。</td></tr><tr><td>FP Buffer</td><td>Fixpipe Buffer, 存放量化参数、Relu参数等。</td></tr></table>


表2-28 搬运单元介绍


<table><tr><td>搬运单元</td><td>描述</td></tr><tr><td>MTE1</td><td>负责如下通路的数据搬运：
·L1-&gt;LOA/LOB
·L1-&gt;BT Buffer</td></tr><tr><td>MTE2</td><td>负责如下通路的数据搬运：
·GM-&gt;{L1, L0A/B}，在该通路下，基于分形大小搬运，搬运时满足Cache Line大小对齐，性能更优。
·GM-&gt;UB，基于Cache Line大小搬运性能更优。</td></tr><tr><td>MTE3</td><td>负责如下通路的数据搬运：
·UB -&gt; GM</td></tr><tr><td>FixPipe</td><td>负责如下通路的数据搬运，搬运过程中可以完成随路数据格式/类型转换：
·LOC-&gt;{GM/L1}
·L1-&gt;FP Buffer</td></tr></table>

# 说明

● 不同类型的AI处理器，存储单元大小不同，开发者可通过GetCoreMemSize接口获取。 

● 所有通过搬运单元读写GM的数据都缺省被缓存在L2Cache，以此加快访问速度，提高访问 效率。核外L2Cache以Cache Line为单位加载数据，根据硬件规格不同，Cache Line大小不 同（128/256/512Byte等）。 

# 典型的数据流

Vector计算典型的数据流如下： 

![](images/9987d5af6294f6b29c641caca83d93e4970d851bc30f0cb657bf3efdc7bcafad.jpg)


Cube计算典型的数据流如下： 

$\mathsf { G M } \to \mathsf { L 1 } \to \mathsf { L 0 A } / \mathsf { L 0 B } \to \mathsf { C u b e } \to \mathsf { L 0 C } \to \mathsf { F i x P i p e } \to \mathsf { G M }$ 

GM →L1→L0A/L0B →Cube →L0C→FixPipe→L1 

![](images/8d2b9a6c3e6f5eb3c2925b428a5a4d8908d39f8d6d5795eb49bbceb805d812ec.jpg)


# 典型的指令流

多条指令从系统内存通过总线接口进入到ICache(Instruction Cache)中，后续的指令执 行过程，根据指令的类型，有两种可能： 

如果指令是Scalar指令，指令会被Scalar单元直接执行。 

其他指令会被Scalar单元调度到独立的分类序列（Vector指令序列、Cube指令序 列、MTE1/MTE2/MTE3指令序列等），然后再被对应的执行单元执行。 


图 2-33 指令分类处理机制


![](images/45ee85c29241ddb7bc85165ebbad70acf882306fba9ba65e1a568261aa249ef0.jpg)


同一个指令序列中的指令是按照进入指令序列的顺序执行的，不同指令序列之间可以 并行执行，通过多个指令序列的并行执行可以提升整体执行效率。对于并行执行过程 中可能出现的数据依赖，通过事件同步模块插入同步指令来控制流水线的同步，提供 PipeBarrier、SetFlag/WaitFlag两种API，保证序列内部以及序列之间按照逻辑关系执 行。 

PipeBarrier本身是一条指令，用于在序列内部约束执行顺序（虽然指令是顺序执 行，但并不意味着后一条指令开始执行时前一条指令执行结束）。PipeBarrier指 令可以保证前序指令中所有数据读写全部完成，后序指令才开始执行。 

SetFlag/WaitFlag为两条指令，在SetFlag/WaitFlag的指令中，可以指定一对指令 序列的关系，表示两个序列之间完成一组“锁”机制，其作用方式为： 

SetFlag：当前序指令的所有读写操作都完成之后，当前指令开始执行，并将 硬件中的对应标志位设置为1。 

WaitFlag：当执行到该指令时，如果发现对应标志位为0，该序列的后续指令 将一直被阻塞；如果发现对应标志位为1，则将对应标志位设置为0，同时后 续指令开始执行。 

Ascend C提供同步控制API，开发者可以使用这类API来自行完成同步控制。需要注意 的是，通常情况下，开发者基于2.2 编程模型中介绍的编程模型和范式进行编程时不需 要关注同步，编程模型帮助开发者完成了同步控制；使用编程模型和范式是我们推荐 的编程方式，自行同步控制可能会带来一定的编程复杂度。 

但是我们仍然希望开发者可以理解同步的基本原理，便于后续更好的理解设计并行计 算程序；同时少数情况需要开发者手动插入同步，您可以通过什么时候需要开发者手 动插入同步来了解具体内容。 

# 2.6.2 架构规格

# 2.6.2.1 NPU 架构版本 200x

本节介绍__NPU_ARCH__版本号为200x的硬件架构和其功能说明，其中200代表IP核编 号，x表示同一个IP核的配置版本号。对应的产品型号为Atlas 推理系列产品。 

# 硬件架构图

![](images/3ff128264d5e0df54d752ef111f49bb28af835446051efbd7ac0b300cf4e16a7.jpg)


# 计算单元

# Cube计算单元和Vector计算单元同核部署

本架构中，Cube计算单元和Vector计算单元同核部署，共享同一个Scalar计算单元。 

# Vector计算单元

● Vector计算单元的数据来源来自于Unified Buffer，要求32字节对齐。 

● 数据从L0C Buffer传输至Unified Buffer需要以Vector计算单元作为中转。 

# Cube计算单元

Cube计算单元可以访问的存储单元有L0A Buffer、L0B Buffer、L0C Buffer，其中 L0A Buffer存储左矩阵，L0B Buffer存储右矩阵，L0C Buffer存储矩阵乘的结果和 中间结果。 

# 存储单元

# 获取存储单元的内存空间大小

开发者可以通过平台信息获取接口查询各存储单元的内存空间大小。 

# 各存储单元的最小访问粒度（对齐要求）

<table><tr><td>存储单元</td><td>对齐要求</td></tr><tr><td>Unified Buffer</td><td>32Byte对齐。</td></tr><tr><td>L1 Buffer</td><td>32Byte对齐。</td></tr><tr><td>LOA Buffer</td><td>512Byte对齐。</td></tr><tr><td>LOB Buffer</td><td>512Byte对齐。</td></tr><tr><td>LOC Buffer</td><td>64Byte对齐。</td></tr></table>

# 各存储单元推荐使用的数据排布格式

L0A Buffer、L0B Buffer和L0C Buffer推荐分别采用以下分形格式： 

– L0A Buffer：FRACTAL_ZZ 

L0B Buffer：FRACTAL_ZN 

– L0C Buffer：FRACTAL_NZ 

这些格式针对矩阵乘法等计算密集型任务进行优化，可显著提升计算效率。 

L1 Buffer缓存推荐使用FRACTAL_NZ格式。当L1采用NZ格式时，数据搬运到 L0A/L0B Buffer（需分别转换为ZZ和ZN格式）时，可降低格式转换开销。 

Unified Buffer对数据格式没有要求。 

# 解决存储单元的访问冲突，提升读写性能

当多个操作尝试同时访问Unified Buffer同一个bank或者bank group时，可能会发生 bank冲突，包括读写冲突、写写冲突、读读冲突，这种冲突会导致访问排队，降低性 能。可以通过优化bank分配的方式来提升读写性能，具体信息请参考3.8.5.11 避免 Unified Buffer的bank冲突章节。 

# 搬运单元

# 搬运时的对齐要求

由于搬运后的数据用于参与数据计算，因此对搬运数据大小有要求，搬运到Unified Buffer的数据大小需要按照DataBlock对齐，其余存储单元的数据搬运必须按分形要求 进行搬运。例如，数据从L1 Buffer搬运到L0A Buffer时，数据格式需要从NZ转换为ZZ 

格式，搬运数据的大小要按分形大小对齐，如果L1 Buffer的剩余大小不足1个分形，则 硬件执行中会出现异常。 

# 同步控制

# 核内同步

由于AI Core内部的执行单元（如MTE2搬运单元、Vector计算单元等）以异步并行的 方式运行，在读写Local Memory（如Unified Buffer）时可能存在数据依赖关系。为 确保数据一致性及计算正确性，需通过同步控制协调操作时序。 

以MTE2从GM搬运数据至UB，进行Vector计算单元的Abs计算，再搬运回GM的流程为 例，需满足以下同步条件： 

# 1. 数据搬运与计算顺序

GM→UB搬运完成后再启动Vector单元的Abs计算（避免计算时未完成搬运导 致的数据缺失）； 

– Vector计算完成后再执行UB→GM的数据搬运（确保结果数据已就绪）。 

# 2. 循环搬运计算场景的同步规则

前序计算完成后再启动新搬运：上一次计算未完成时，不得触发新数据搬运 （防止UB中旧数据被覆盖）； 

前序数据搬出完成后再启动新计算：上一次数据未完全从UB搬出时，不得触 发新计算任务（避免目标内存区域的覆盖冲突）。 


同步控制流程如下图所示：


![](images/14a2e26db818066b5a841af0bae583e3a8ca9696359b075bb01c05dc4a246a86.jpg)



上图中，ID1、ID2、ID3、ID4、ID5、ID6表示事件ID（EventID），每个EventID对应 一块存储数据的搬运状态，确保数据操作的正确性和一致性。


# 需要注意以下几点：

建议通过AllocEventID或者FetchEventID接口获取EventID，以确保其合法性和有 效性。 

EventID的数量有限，使用后应立即调用ReleaseEventID释放资源，避免EventID 耗尽，影响系统正常运行。 

SetFlag和WaitFlag必须成对使用，且SetFlag和WaitFlag的参数必须完全一致 （包括模板参数和事件ID）。如果不匹配，可能导致当前核的计算异常，或影响 下一个核的算子执行，引发timeout问题。 

例如，SetFlag<HardEvent::S_MTE3>(1)和SetFlag<HardEvent::MTE3_MTE1>(1) 设置的不是同一个EventID，因为其模板参数不同。只有当模板参数和事件ID完全 一致时，才表示同一个EventID。 

● 不允许连续设置同一个EventID，因为这可能导致事件状态混乱或未被正确处理。 

# 核间同步

该硬件架构不支持核间同步。 

# 2.6.2.2 NPU 架构版本 220x

本节介绍__NPU_ARCH__版本号为220x的硬件架构和其功能说明，其中220代表IP核编 号，x表示同一个IP核的配置版本号。对应的产品型号为： 

● Atlas A3 训练系列产品/Atlas A3 推理系列产品 

● Atlas A2 训练系列产品/Atlas A2 推理系列产品 

# 硬件架构图

如下图所示，本架构中AI Core分为AIC和AIV两个独立的核，分别用于矩阵计算和向量 计算。每个核都有自己的Scalar单元，能独立加载自己的代码段。AIV与AIC之间通过 Global Memory进行数据传递。 

![](images/b75eedb05aeb28e3bbfb4cf9fceeef13cc369400b975f213344bded78c1fe26a.jpg)


# 计算单元

# Cube计算单元和Vector计算单元分离部署

本架构中，Cube计算单元和Vector计算单元分别部署在AIC核和AIV核上，每个核都有 自己的Scalar单元，能独立加载自己的代码段。 

# Vector计算单元

● Vector计算单元的数据来自于Unified Buffer，要求32字节对齐。 

# Cube计算单元

Cube计算单元可以访问的存储单元有L0A Buffer、L0B Buffer、L0C Buffer，其中 L0A Buffer存储左矩阵，L0B Buffer存储右矩阵，L0C Buffer存储矩阵乘的结果和 中间结果。 

# 存储单元

# 获取存储单元的内存空间大小

开发者可以通过平台信息获取接口查询各存储单元的内存空间大小。 

# 各存储单元的最小访问粒度（对齐要求）

<table><tr><td>核</td><td>存储单元</td><td>对齐要求</td></tr><tr><td>AIV</td><td>Unified Buffer</td><td>32Byte对齐。</td></tr><tr><td rowspan="6">AIC</td><td>L1 Buffer</td><td>32Byte对齐。</td></tr><tr><td>LOA Buffer</td><td>512Byte对齐。</td></tr><tr><td>LOB Buffer</td><td>512Byte对齐。</td></tr><tr><td>LOC Buffer</td><td>64Byte对齐。</td></tr><tr><td>BiasTable Buffer</td><td>64Byte对齐。</td></tr><tr><td>Fixpipe Buffer</td><td>64Byte对齐。</td></tr></table>

# 各存储单元推荐使用的数据排布格式

● L0A Buffer、L0B Buffer和L0C Buffer推荐分别采用以下分形格式： 

– L0A Buffer：FRACTAL_ZZ 

L0B Buffer：FRACTAL_ZN 

– L0C Buffer：FRACTAL_NZ 

这些格式针对矩阵乘法等计算密集型任务进行优化，可显著提升计算效率。 

L1 Buffer缓存推荐使用FRACTAL_NZ格式。当L1 Buffer采用NZ格式时，数据搬运 到L0A/L0B Buffer（需分别转换为ZZ和ZN格式）时，可降低格式转换开销。 

Unified Buffer对数据格式没有要求。 

# 解决存储单元的访问冲突，提升读写性能

当多个操作尝试同时访问Unified Buffer同一个bank或者bank group时，可能会发生 bank冲突，包括读写冲突、写写冲突、读读冲突，这种冲突会导致访问排队，降低性 能。可以通过优化bank分配的方式来提升读写性能，具体信息请参考3.8.5.11 避免 Unified Buffer的bank冲突章节。 

# 搬运单元

# 搬运时的对齐要求

由于搬运后的数据用于参与数据计算，因此对搬运数据大小有要求，搬运到Unified Buffer的数据大小需要按照DataBlock对齐，其余存储单元的数据搬运必须按分形要求 进行搬运。例如，数据从L1 Buffer搬运到L0A Buffer时，数据格式需要从NZ转换为ZZ 

格式，搬运数据的大小要按分形大小对齐，如果L1 Buffer的剩余大小不足1个分形，则 硬件执行中会出现异常。 

# 支持跨卡数据搬运（Hccs物理链路）

在跨卡通信算子开发场景，DataCopy类接口支持跨卡数据搬运，在Atlas A2 训练系列 产品/Atlas A2 推理系列产品设备上，仅支持Hccs物理链路，不支持其他通路；开发者 开发过程中，请关注涉及卡间通信的物理通路； 通过npu-smi info -t topo指令查询 Hccs 物理通路。 

# 支持Fixpipe硬件化加速

Fixpipe是NPU将典型操作进行硬化的加速模块，位于AIC内部，配合Cube计算单元完 成随路计算，主要功能如下： 

量化反量化：包括S322FP16、S322S32、S322S4、S322S8、S322S16、 FP322FP16、FP322BF16、FP322S8、FP322S4、FP322FP32。 

Relu功能，包括ReLu、PReLu和Leaky ReLu等典型的激活函数。 

数据格式转换，包括： 

通过Channel merge、Channel split可以实现分形大小的转换，保证输出到 L1 Buffer/GM的分形满足诉求。 

NZ2ND数据格式转换。 

![](images/9f49f17b40c98352b1bd81c71afc16c73396dc0e14a841fb40e60d1d7b5e1932.jpg)


上图中，Channel merge支持S8、U8、S4和U4数据类型，而Channel split支持FP32 数据类型。 

Channel merge（S8和U8数据类型） 

对于转换为S8或U8的目标数据类型，分形矩阵通过硬件从16x16转换为16x32， 如果输出通道数N是16的偶数倍，则N方向上每2个相邻的16x16分形矩阵将合并 为1个16x32分形矩阵。如果N是16的奇数倍，则将通道1到通道（N–16）合并， 最后16个通道保持未合并。 

如下所示，目标数据类型为S8，M为32，N为48，首先将前2列16x16分形矩阵合 并为一个16x32矩阵，然后将剩余的16x16分形矩阵直接移入L1 Buffer。 

![](images/5f54a517c0e7794f5c21c33ff18030b06ab798cee47bb831c94baf983e076f23.jpg)


Channel merge（S4和U4数据类型） 

对于转换为S4或U4的目标数据类型，分形矩阵通过硬件从16x16转换为16x64， 如果输出通道数N是64的倍数，则N方向上每4个相邻的16x16分形矩阵将合并为1 个16x64分形矩阵。 

例如，这里目标数据类型为S4，M为32，N为64，首先将第1行16x16分形矩阵合 并为一个16x64矩阵，然后将第2行16x16分形矩阵也合并。 

在这种情况下，N的配置必须是64的倍数。 

![](images/8452cc840951faf9b8f1ca17dff281c2878820174a80978093e36835d48cb9b9.jpg)


FP32 Channel split： 

对于目标类型为FP32，分形矩阵可以通过硬件从16x16转换为16x8，如果使能 Channel split，则每个16x16分形矩阵将被分裂为2个16x8分形矩阵。 

如下图所示，这里的目标数据类型是FP32，M是64，N是32，它将被拆分为16个 16x8的分形。 

![](images/f407f714890f0c159f2afcad15e077d0b2ed57c21f3e2fa303bda4bbe3934ccb.jpg)


# 同步控制

核内同步 

由于AI Core内部的执行单元（如MTE2搬运单元、Vector计算单元等）以异步并 行的方式运行，在读写Local Memory（如Unified Buffer）时可能存在数据依赖 关系。为确保数据一致性及计算正确性，需通过同步控制协调操作时序。 

以MTE2从GM搬运数据至UB，进行Vector计算单元的Abs计算，再搬运回GM的流 程为例，需满足以下同步条件： 

# a. 数据搬运与计算顺序

GM→UB搬运完成后再启动Vector单元的Abs计算（避免计算时未完成搬 运导致的数据缺失）； 

Vector计算完成后再执行UB→GM的数据搬运（确保结果数据已就 绪）。 

# b. 循环搬运计算场景的同步规则

前序计算完成后再启动新搬运：上一次计算未完成时，不得触发新数据 搬运（防止UB中旧数据被覆盖）； 

前序数据搬出完成后再启动新计算：上一次数据未完全从UB搬出时，不 得触发新计算任务（避免目标内存区域的覆盖冲突）。 

# 同步控制流程如下图所示：

![](images/820bd13abff359a41828d0522ef4188be8257b5adb72e4cf417a99c0909c82b8.jpg)



上图中，ID1、ID2、ID3、ID4、ID5、ID6表示事件ID（EventID），每个EventID 对应一块存储数据的搬运状态，确保数据操作的正确性和一致性。


# 需要注意以下几点：

建议通过AllocEventID或者FetchEventID接口获取EventID，以确保其合法性 和有效性。 

EventID的数量有限，使用后应立即调用ReleaseEventID释放资源，避免 EventID耗尽，影响系统正常运行。 

SetFlag和WaitFlag必须成对使用，且SetFlag和WaitFlag的参数必须完全一 致（包括模板参数和事件ID）。如果不匹配，可能导致当前核的计算异常， 或影响下一个核的算子执行，引发timeout问题。 

例如，SetFlag<HardEvent::S_MTE3>(1)和 

SetFlag<HardEvent::MTE3_MTE1>(1)设置的不是同一个EventID，因为其模 板参数不同。只有当模板参数和事件ID完全一致时，才表示同一个EventID。 

不允许连续设置同一个EventID，因为这可能导致事件状态混乱或未被正确处 理。 

不建议手动插入 TEventID，不能手动插入6和7的TEventID，因为它们可能被 系统预留或用于特殊用途。 

# 核间同步

当不同核之间操作同一块全局内存时，可能存在读后写、写后读以及写后写等数 据依赖问题，需要进行核间同步控制。 

核间同步控制分为以下几种模式，如下图所示： 

模式0：AI Core核间的同步控制。对于AIC场景，同步所有的AIC核，直到所 有的AIC核都执行到CrossCoreSetFlag时，CrossCoreWaitFlag后续的指令才 会执行；对于AIV场景，同步所有的AIV核，直到所有的AIV核都执行到 CrossCoreSetFlag时，CrossCoreWaitFlag后续的指令才会执行。 

模式1：AI Core内部，AIV核之间的同步控制。如果两个AIV核都运行了 CrossCoreSetFlag，CrossCoreWaitFlag后续的指令才会执行。 

模式2：AI Core内部，AIC与AIV之间的同步控制。在AIC核执行 CrossCoreSetFlag之后， 两个AIV上CrossCoreWaitFlag后续的指令才会继续 执行；两个AIV都执行CrossCoreSetFlag后，AIC上CrossCoreWaitFlag后续的 指令才能执行。 

![](images/9f27a3ae01859ac237db0f59dd23e7178b8a1dfed4dc059f647d3801d1b952a6.jpg)


例如，在AIC中将L0C的计算结果搬运到GM后，AIV需要将GM的数据搬运到UB。 此时，可以使用CrossCoreSetFlag和CrossCoreWaitFlag命令，确保数据从L0C成 功搬运到GM后，再从GM搬运到UB，流程如下图所示。 

![](images/48987924e74087d324046446d464e95e39e62a4b85f52113d27b67ac6a29038f.jpg)


CrossCoreSetFlag和CrossCoreWaitFlag接口配合使用。使用时需传入核间同步的 标记ID(flagId)，即上图中的ID1，每个ID对应一个初始值为0的计数器。执行 CrossCoreSetFlag后ID对应的计数器增加1；执行CrossCoreWaitFlag时如果对应 的计数器数值为0则阻塞不执行；如果对应的计数器大于0，则计数器减一，同时 后续指令开始执行。flagId取值范围是0-10。 

需要注意以下几点： 

# 成对使用

CrossCoreSetFlag和CrossCoreWaitFlag必须成对使用，否则可能导致算子超 时问题。 

# 一致性要求

CrossCoreSetFlag 的模板参数和flagId必须与CrossCoreWaitFlag完全一致， 否则视为不同的flagId。例如，CrossCoreSetFlag<0x0, PIPE_MTE3>(0x8) 和 CrossCoreSetFlag<0x2, PIPE_FIX>(0x8) 设置的不是同一个flagId。 

# 避免连续设置

不允许连续设置同一个flagId，以防止计数器状态混乱。 

# 与高阶 API 的使用冲突

Matmul高阶API内部实现中使用了本接口进行核间同步控制，所以不建议开 发者同时使用该接口和Matmul高阶API，否则会有flagId冲突的风险。 

# 计数器限制

同一flagId的计数器最多可以设置15次。 

# 默认流水类型

CrossCoreWaitFlag不需要显式设置指令所在的流水类型，默认使用PIPE_S。 

# 2.6.2.3 NPU 架构版本 300x

本节介绍__NPU_ARCH__版本号为300x的硬件架构和其功能说明，其中300代表IP核编 号，x表示同一个IP核的配置版本号。对应的产品型号为： 

Atlas 200I/500 A2 推理产品 

# 硬件架构图

![](images/9c8cce9d1033e5e9596bac303c07fb0a7940fd5b4afb1ff4a17e8430abc103d6.jpg)


# 计算单元

# Cube计算单元和Vector计算单元同核部署

本架构中，Cube计算单元和Vector计算单元同核部署，共享同一个Scalar计算单元。 

# Vector计算单元

● Vector计算单元的数据来源来自于Unified Buffer，要求32字节对齐。 

# Cube计算单元

Cube计算单元可以访问的存储单元有L0A Buffer、L0B Buffer、L0C Buffer，其中 L0A Buffer存储左矩阵，L0B Buffer存储右矩阵，L0C Buffer存储矩阵乘的结果和 中间结果。 

# 存储单元

# 获取存储单元的内存空间大小

开发者可以通过平台信息获取接口查询各存储单元的内存空间大小。 

# 各存储单元的最小访问粒度（对齐要求）

<table><tr><td>核</td><td>存储单元</td><td>对齐要求</td></tr><tr><td>AIV</td><td>Unified Buffer</td><td>32Byte对齐。</td></tr><tr><td rowspan="6">AIC</td><td>L1 Buffer</td><td>32Byte对齐。</td></tr><tr><td>LOA Buffer</td><td>512Byte对齐。</td></tr><tr><td>LOB Buffer</td><td>512Byte对齐。</td></tr><tr><td>LOC Buffer</td><td>64Byte对齐。</td></tr><tr><td>BiasTable Buffer</td><td>64Byte对齐。</td></tr><tr><td>Fixpipe Buffer</td><td>64Byte对齐。</td></tr></table>

# 各存储单元推荐使用的数据排布格式

● L0A Buffer、L0B Buffer和L0C Buffer推荐分别采用以下分形格式： 

– L0A Buffer：FRACTAL_ZZ 

L0B Buffer：FRACTAL_ZN 

– L0C Buffer：FRACTAL_NZ 

这些格式针对矩阵乘法等计算密集型任务进行优化，可显著提升计算效率。 

L1 Buffer缓存推荐使用FRACTAL_NZ格式。当L1 Buffer采用NZ格式时，数据搬运 到L0A/L0B Buffer（需分别转换为ZZ和ZN格式）时，可降低格式转换开销。 

Unified Buffer对数据格式没有要求。 

# 解决存储单元的访问冲突，提升读写性能

当多个操作尝试同时访问Unified Buffer同一个bank或者bank group时，可能会发生 bank冲突，包括读写冲突、写写冲突、读读冲突，这种冲突会导致访问排队，降低性 能。可以通过优化bank分配的方式来提升读写性能，具体信息请参考3.8.5.11 避免 Unified Buffer的bank冲突章节。 

# 搬运单元

# 搬运时的对齐要求

由于搬运后的数据用于参与数据计算，因此对搬运数据大小有要求，搬运到Unified Buffer的数据大小需要按照DataBlock对齐，其余存储单元的数据搬运必须按分形要求 进行搬运。例如，数据从L1 Buffer搬运到L0A Buffer时，数据格式需要从NZ转换为ZZ 

格式，搬运数据的大小要按分形大小对齐，如果L1 Buffer的剩余大小不足1个分形，则 硬件执行中会出现异常。 

# 支持Fixpipe硬件化加速

Fixpipe是NPU将典型操作进行硬化的加速模块，位于AIC内部，配合Cube计算单元完 成随路计算，主要功能如下： 

量化反量化：包括S322FP16、S322S32、S322S4、S322S8、S322S16、 FP322FP16、FP322BF16、FP322S8、FP322S4、FP322FP32。 

Relu功能，包括ReLu、PReLu和Leaky ReLu等典型的激活函数。 

数据格式转换，包括： 

通过Channel merge、Channel split可以实现分形大小的转换，保证输出到 L1 Buffer/GM的分形满足诉求。 

NZ2ND数据格式转换。 

![](images/3dfee507c7920242978ba0b352e58e26492c7b74aec0d882665490abf3586766.jpg)


上图中，Channel merge支持S8、U8、S4和U4数据类型，而Channel split支持FP32 数据类型。 

Channel merge（S8和U8数据类型） 

对于转换为S8或U8的目标数据类型，分形矩阵通过硬件从16x16转换为16x32， 如果输出通道数N是16的偶数倍，则N方向上每2个相邻的16x16分形矩阵将合并 为1个16x32分形矩阵。如果N是16的奇数倍，则将通道1到通道（N–16）合并， 最后16个通道保持未合并。 

如下所示，目标数据类型为S8，M为32，N为48，首先将前2列16x16分形矩阵合 并为一个16x32矩阵，然后将剩余的16x16分形矩阵直接移入L1 Buffer。 

![](images/28c85fbaf3cf7c7a75125d3a0ab2304b36d503e44fcf4aee3bf731bf7fa5791e.jpg)


Channel merge（S4和U4数据类型） 

对于转换为S4或U4的目标数据类型，分形矩阵通过硬件从16x16转换为16x64， 如果输出通道数N是64的倍数，则N方向上每4个相邻的16x16分形矩阵将合并为1 个16x64分形矩阵。 

例如，这里目标数据类型为S4，M为32，N为64，首先将第1行16x16分形矩阵合 并为一个16x64矩阵，然后将第2行16x16分形矩阵也合并。 

在这种情况下，N的配置必须是64的倍数。 

![](images/a001ac09b9c5d8a3d57349ddef23dd663b1e5d23aeb67112e97a81d9aab9aa4e.jpg)


FP32 Channel split： 

对于目标类型为FP32，分形矩阵可以通过硬件从16x16转换为16x8，如果使能 Channel split，则每个16x16分形矩阵将被分裂为2个16x8分形矩阵。 

如下图所示，这里的目标数据类型是FP32，M是64，N是32，它将被拆分为16个 16x8的分形。 

![](images/b5e0bf7e7bece7948f707446a2253647668e611bea0733ad8360640fd735bc12.jpg)


# 同步控制

核内同步 

由于AI Core内部的执行单元（如MTE2搬运单元、Vector计算单元等）以异步并 行的方式运行，在读写Local Memory（如Unified Buffer）时可能存在数据依赖 关系。为确保数据一致性及计算正确性，需通过同步控制协调操作时序。 

以MTE2从GM搬运数据至UB，进行Vector计算单元的Abs计算，再搬运回GM的流 程为例，需满足以下同步条件： 

a. 数据搬运与计算顺序 

GM→UB搬运完成后再启动Vector单元的Abs计算（避免计算时未完成搬 运导致的数据缺失）； 

Vector计算完成后再执行UB→GM的数据搬运（确保结果数据已就 绪）。 

b. 循环搬运计算场景的同步规则 

前序计算完成后再启动新搬运：上一次计算未完成时，不得触发新数据 搬运（防止UB中旧数据被覆盖）； 

前序数据搬出完成后再启动新计算：上一次数据未完全从UB搬出时，不 得触发新计算任务（避免目标内存区域的覆盖冲突）。 


同步控制流程如下图所示：


![](images/5bebde1296f09c228e06459fdbe6b1c8a1b983d67f6dfc62c0c6938b8e0798ec.jpg)



上图中，ID1、ID2、ID3、ID4、ID5、ID6表示事件ID（EventID），每个EventID 对应一块存储数据的搬运状态，确保数据操作的正确性和一致性。


需要注意以下几点： 

建议通过AllocEventID或者FetchEventID接口获取EventID，以确保其合法性 和有效性。 

EventID的数量有限，使用后应立即调用ReleaseEventID释放资源，避免 EventID耗尽，影响系统正常运行。 

SetFlag和WaitFlag必须成对使用，且SetFlag和WaitFlag的参数必须完全一 致（包括模板参数和事件ID）。如果不匹配，可能导致当前核的计算异常， 或影响下一个核的算子执行，引发timeout问题。 

例如，SetFlag<HardEvent::S_MTE3>(1)和 

SetFlag<HardEvent::MTE3_MTE1>(1)设置的不是同一个EventID，因为其模 板参数不同。只有当模板参数和事件ID完全一致时，才表示同一个EventID。 

不允许连续设置同一个EventID，因为这可能导致事件状态混乱或未被正确处 理。 

不建议手动插入 TEventID，不能手动插入6和7的TEventID，因为它们可能被 系统预留或用于特殊用途。 

核间同步 

该硬件架构不支持核间同步。 

# 2.6.2.4 NPU 架构版本 351x

本节介绍__NPU_ARCH__版本号为351x的硬件架构和其功能说明。 

# 硬件架构图

如下图所示，本架构中AI Core分为AIC和AIV两个独立的核，分别用于矩阵计算和向量 计算。AIC核与AIV核配比为1：2。每个核都有自己的Scalar单元，能独立加载自己的 代码段。 

![](images/57a5f0932ec629e8b7ba121a73a85d46ba348ddb7d37186cbc5df0db1761d804.jpg)


# 该架构的关键特点有：

● 增加L0C Buffer $- >$ Unified Buffer、Unified Buffer $< - > \lfloor 1 \AA$ Buffer的数据通路。 

删除Global Memory -> L0A Buffer、Global Memory -> L0B Buffer的数据通 路。 

删除L1 Buffer-> Global Memory的数据通路。 

SSBuffer，用于AIC和AIV的核间通信。 

增加SIMD Register File存储层次，在SIMD程序中，数据从Unified Buffer搬运到 Register进行计算，产生的中间结果可以不用传回Unified Buffer，直接在寄存器 计算。 

新增SIMT相关硬件单元。SIMT相关硬件单元介绍如下： 

<table><tr><td>SIMT硬件单元名称</td><td>说明</td></tr><tr><td>SIMT
DCache</td><td>SIMT访问GM需要经过SIMT DCache中转，SIMT支持最大128KB Data Cache, Data Cache直接复用UB作为cacheline, SIMT所有对外访存都是以128B为粒度。</td></tr><tr><td>Warp Scheduler</td><td>实现硬件的多线程调度。
SIMT每个AIV有4个Warp Scheduler。</td></tr><tr><td>SIMT
Register File</td><td>为SIMT应用程序提供的总容量为128KB的超大容量寄存器。每个Thread可用的寄存器数和Thread数量有关，对应关系为：
·1025~2048条Thread: 16个Register。
·513~1024条Thread: 32个Register。
·257~512条Thread: 64个Register。
·1~256条Thread: 127个Register。</td></tr></table>

# 计算单元

# Cube计算单元和Vector计算单元分离部署

本架构中，Cube计算单元和Vector计算单元分别部署在AIC核和AIV核上，每个核都有 自己的Scalar单元，能独立加载自己的代码段。 

# Vector计算单元

Vector计算单元支持U8、U16、U32、S8、S16、S32、BF16、FP16、FP32数据 类型。 

Vector计算单元每拍可处理256字节的数据。 

● Vector计算单元处理的数据来源来自于Register。 

在本架构版本中，高维切分接口中的传入的掩码值会被转化为MaskReg传入 Vector计算单元，而在NPU架构版本220x中，掩码值从特殊的掩码寄存器中读 取。 


图 2-34 NPU 架构版本 220 高维切分


![](images/1f0a1743d974eeac48d5cf344ee4b5fb8dc6183e3ea9f061fa11397a93f2034f.jpg)



图 2-35 本架构版本高维切分


![](images/b3751309c930e137da554a6c06b690c12562d3195a391ce50cdb92c27cf15e59.jpg)


# Cube计算单元

Cube计算单元支持FP32/FP16/BF16/HiF8/FP8_E4M3/U8/S8。 一拍完成一个 float16数据类型的16x16与16x16大小的矩阵乘；如果是int8_t数据类型，则一拍 完成 $1 6 ^ { \star } 3 2$ 与 $3 2 ^ { \star } 1 6$ 大小的矩阵乘。 

Cube计算单元可以访问的存储单元有L0A Buffer、L0B Buffer、L0C Buffer，其中 L0A Buffer存储左矩阵，L0B Buffer存储右矩阵，L0C Buffer存储矩阵乘的结果和 中间结果。 

# Scalar单元

Scalar单元支持U16/S16/U32/S32/U64/S64/FP64数据类型。 

在Reagbase架构中，Aux Scalar计算单元单独处理SIMD_VF函数内的Scalar计 算，Scalar计算单元处理SIMD_VF函数外的Scalar计算。 

# 存储单元

# 获取存储单元的内存空间大小

开发者可以通过平台信息获取接口查询各存储单元的内存空间大小。 


各存储单元的最小访问粒度（对齐要求）


<table><tr><td>核</td><td>存储单元</td><td>对齐要求</td></tr><tr><td>AIV</td><td>Unified Buffer</td><td>32Byte对齐。</td></tr><tr><td rowspan="6">AIC</td><td>L1 Buffer</td><td>32Byte对齐。</td></tr><tr><td>LOA Buffer</td><td>512Byte对齐。</td></tr><tr><td>LOB Buffer</td><td>512Byte对齐。</td></tr><tr><td>LOC Buffer</td><td>64Byte对齐。</td></tr><tr><td>BiasTable Buffer</td><td>64Byte对齐。</td></tr><tr><td>Fixpipe Buffer</td><td>64Byte对齐。</td></tr></table>

# 各存储单元推荐使用的数据排布格式

● L0A Buffer、L0B Buffer和L0C Buffer推荐分别采用以下分形格式： 

L0A Buffer：FRACTAL_NZ（由于硬件结构变更，本架构下L0A Buffer的分形 改为NZ） 

– L0B Buffer：FRACTAL_ZN 

L0C Buffer：FRACTAL_NZ 

这些格式针对矩阵乘法等计算密集型任务进行优化，可显著提升计算效率。 

L1 Buffer缓存推荐使用FRACTAL_NZ格式。当L1 Buffer采用NZ格式时，数据搬运 到L0A/L0B Buffer（需分别转换为ZN格式）时，可降低格式转换开销。 

Unified Buffer对数据格式没有要求。 

# 存储单元的访问冲突

本NPU架构版本UB结构如下图所示，当多个操作尝试同时访问Unified Buffer同一个 bank或者bank group时，可能会发生bank冲突，包括读写冲突、写写冲突、读读冲 突，这种冲突会导致访问排队，降低性能。在NPU架构版本220x中，同一个bank group只有一组读口和写口，最多一拍完成一读或者一写，在本NPU架构版本中每个 bank group有两组读口和写口，最多同时允许2读0写或者1读1写。相关读写约束如 下： 

读写冲突：读操作和写操作同时尝试访问同一个bank。 

写写冲突：多个写操作同时尝试访问同一个bank group。 

读读冲突：两个读操作同时尝试访问同一个bank，或者两个以上读操作同时尝试 访问同一个bank group。 


图 2-36 本架构版本 UB bank 示意图


![](images/7d93569c48cb26254265fd9a7ebdbd4b15281f740642f055d4ae3239a4a9a6d9.jpg)


# Register寄存器

● RegTensor RegTensor用于存放Reg矢量计算数据， RegTensor位宽为VL（256B）。 

MaskReg MaskReg用于指示在计算过程中哪些元素参与计算，宽度为RegTensor的八分之 一（VL/8）。 

UnalignRegForLoad & UnalignRegForStore UnalignRegForLoad、UnalignRegForStore用作缓冲区来优化UB和RegTensor之 间连续不对齐地址访问的开销。在读不对齐地址前，UnalignRegForLoad、 UnalignRegForStore应该通过LoadUnAlignPre API初始化，然后使用 LoadUnAlign API。在写不对齐地址时，先使用StoreUnAlign API，再使用 StoreUnAlignPost API后处理。 

AddrReg AddrReg即为Address Register（地址寄存器），是用于存储地址偏移量的寄存 器。AddrReg应该通过CreateAddrReg初始化，然后在循环之中使用AddrReg存储 地址偏移量。AddrReg每层循环中根据所设置的stride进行自增。 

# 搬运单元

# 搬运时的对齐要求

由于搬运后的数据用于参与数据计算，因此对搬运数据大小有要求，搬运到Unified Buffer的数据大小需要按照DataBlock对齐，其余存储单元的数据搬运必须按分形要求 进行搬运。例如，数据从L1 Buffer搬运到L0A Buffer时，数据格式需要从NZ转换为ZN 格式，搬运数据的大小要按分形大小对齐，如果L1 Buffer的剩余大小不足1个分形，则 硬件执行中会出现异常。 

# MTE硬通道

AIV新增Unified Buffer和L1 Buffer之间的硬通道。 

新增支持GM到Unified Buffer搬运和Unified Buffer到GM搬运的Loop模式。在 Loop模式下，每次循环可以是Normal模式或Compact模式，Normal模式和 Compact模式可参考DataCopyPad(ISASI)。 

单次Loop以Normal模式搬运 

若单个数据块长度为32B对齐，则无需插入Padding，可通过多次Repeat搬运 多组数据块。 

![](images/c3cc88d0db1f75f7d23fa2481a31ede0c4829af01018a11e4b124b2bb807253b.jpg)


若单个数据块长度不为32B对齐，则需在每个数据块后插入Padding，使其 32B对齐后再进行搬运。 

![](images/946f0054f4bc7635567ad975181fcf7ed867ca2ca62e476ca8d66088c1725279.jpg)


# 单次Loop以Compact模式搬运

Compact可以一次搬运一组数据块，当这些数据块的总长度为32B对齐的时 候，则无需在最后插入Padding。 

![](images/bcdea017a951647a3c6c6486a593fa8478546d961e935be44f99e9b0baef6bf0.jpg)


当一组数据块的长度不是32B对齐，需要在这组数据块后插入padding，使总 长度32B对齐。 

![](images/56ff4a72fc35fca41cd86698dcc0ffad85fae90fe6ac6c93c44c3ab975422ed7.jpg)


# 支持Fixpipe硬件化加速

Fixpipe是NPU将典型操作进行硬化的加速模块，位于AIC内部，配合Cube计算单元完 成随路计算，主要功能如下： 

量化反量化：包括S4/S8/S32/FP16/FP32/FP8_E4M3/HiF8/BF16。 

Relu功能，包括ReLu、PReLu和Leaky ReLu等典型的激活函数。 

数据格式转换，包括： 

通过Channel merge、Channel split可以实现分形大小的转换，保证输出到 L1 Buffer/GM的分形满足诉求。 

支持L0C Source的NZ2ND、NZ2DN随路转换。 

Channel merge支持S8、U8、S4和U4数据类型，而Channel split支持FP32数据类 型。 

Channel merge（S8和U8数据类型） 

对于转换为S8或U8的目标数据类型，分形矩阵通过硬件从16x16转换为16x32， 如果输出通道数N是16的偶数倍，则N方向上每2个相邻的16x16分形矩阵将合并 为1个16x32分形矩阵。如果N是16的奇数倍，则将通道1到通道（N–16）合并， 最后16个通道保持未合并。 

如下所示，目标数据类型为S8，M为32，N为48，首先将前2列16x16分形矩阵合 并为一个16x32矩阵，然后将剩余的16x16分形矩阵直接移入L1 Buffer。 

![](images/8d7e10b732ee801d4ef790cef70c34248ea05df20863ebfa49a71984beee7e23.jpg)


Channel merge（S4和U4数据类型）： 

对于转换为S4或U4的目标数据类型，分形矩阵通过硬件从16x16转换为16x64， 如果输出通道数N是64的倍数，则N方向上每4个相邻的16x16分形矩阵将合并为1 个单个的16x64分形矩阵。 

例如，这里目标数据类型为S4，M为32，N为64，首先将第1行16x16分形矩阵合 并为一个16x64矩阵，然后将第2行16x16分形矩阵也合并。 

在这种情况下，N的配置必须是64的倍数。 

![](images/11efdaf549be0e3e481e7185f2a7e1f87d355e63fd8bfae9e98c55e2955588ad.jpg)


FP32 Channel split： 

对于目标类型为FP32，分形矩阵可以通过硬件从16x16转换为16x8，如果使能 Channel split，则每个16x16分形矩阵将被分裂为2个16x8分形矩阵。 

如下图所示，这里的目标数据类型是FP32，M是64，N是32，它将被拆分为16个 16x8的分形。 

![](images/5bd3278b6f9130bbbba98f0b630b8022f8b73a5094bc2944ff8e853634911a82.jpg)


# AIC AIV 核间通信

该架构支持AIC: AIV为1:1和1:2的核间通信，核间通信通过SSBuf进行，这一点和 NPU220架构有所不同，NPU220架构中核间通信通过GM来完成。 

![](images/09178d405f667f0c33084bb8453a867138541c378a7884ba253aa767822fd555.jpg)


![](images/8efcd653a9b3384e1cbe9fb2eee7ced0faa596e341ced747d6a56d9bd1e060ac.jpg)


# 同步控制

# 核内同步

由于AI Core内部的执行单元（如MTE2搬运单元、Vector计算单元等）以异步并 行的方式运行，在读写Local Memory（如Unified Buffer）时可能存在数据依赖 关系。为确保数据一致性及计算正确性，需通过同步控制协调操作时序。 

以MTE2从GM搬运数据至UB，进行Vector计算单元的Abs计算，再搬运回GM的流 程为例，需满足以下同步条件： 

# a. 数据搬运与计算顺序

GM→UB搬运完成后再启动Vector单元的Abs计算（避免计算时未完成搬 运导致的数据缺失）； 

Vector计算完成后再执行UB→GM的数据搬运（确保结果数据已就 绪）。 

# b. 循环搬运计算场景的同步规则

前序计算完成后再启动新搬运：上一次计算未完成时，不得触发新数据 搬运（防止UB中旧数据被覆盖）； 

前序数据搬出完成后再启动新计算：上一次数据未完全从UB搬出时，不 得触发新计算任务（避免目标内存区域的覆盖冲突）。 

# 同步控制流程如下图所示：

![](images/a35ec1221618c09f25a76355856cddd6bea0acdbb4c3c195be934e326113273c.jpg)


上图中，ID1、ID2、ID3、ID4、ID5、ID6表示事件ID（EventID），每个EventID 对应一块存储数据的搬运状态，确保数据操作的正确性和一致性。 

需要注意以下几点： 

建议通过AllocEventID或者FetchEventID接口获取EventID，以确保其合法性 和有效性。 

EventID的数量有限，使用后应立即调用ReleaseEventID释放资源，避免 EventID耗尽，影响系统正常运行。 

SetFlag和WaitFlag必须成对使用，且SetFlag和WaitFlag的参数必须完全一 致（包括模板参数和事件ID）。如果不匹配，可能导致当前核的计算异常， 或影响下一个核的算子执行，引发timeout问题。 

例如，SetFlag<HardEvent::S_MTE3>(1)和 

SetFlag<HardEvent::MTE3_MTE1>(1)设置的不是同一个EventID，因为其模 板参数不同。只有当模板参数和事件ID完全一致时，才表示同一个EventID。 

不允许连续设置同一个EventID，因为这可能导致事件状态混乱或未被正确处 理。 

不建议手动插入TEventID，不能手动插入6和7的TEventID，因为它们可能被 系统预留或用于特殊用途。 

# 核间同步

当不同核之间操作同一块全局内存时，可能存在读后写、写后读以及写后写等数 据依赖问题，需要进行核间同步控制。 

核间同步控制分为以下几种模式，如下图所示： 

模式0：AI Core核间的同步控制。对于AIC场景，同步所有的AIC核，直到所 有的AIC核都执行到CrossCoreSetFlag时，CrossCoreWaitFlag后续的指令才 会执行；对于AIV场景，同步所有的AIV核，直到所有的AIV核都执行到 CrossCoreSetFlag时，CrossCoreWaitFlag后续的指令才会执行。 

模式1：AI Core内部，AIV核之间的同步控制。如果两个AIV核都运行了 CrossCoreSetFlag，CrossCoreWaitFlag后续的指令才会执行。 

模式2：AI Core内部，AIC与AIV之间的同步控制（1:2）。在AIC核执行 CrossCoreSetFlag之后， 两个AIV上CrossCoreWaitFlag后续的指令才会继续 执行；两个AIV都执行CrossCoreSetFlag后，AIC上CrossCoreWaitFlag后续的 指令才能执行。 

模式4：AI Core内部，AIC与AIV之间的同步控制（1:1）。AIV0与AIV1可单独 触发AIC等待。比如，在AIC核执行CrossCoreSetFlag之后， AIV0上 CrossCoreWaitFlag后续的指令才会继续执行；AIV0执行CrossCoreSetFlag 后，AIC上CrossCoreWaitFlag后续的指令才能执行。 

![](images/d1e90991ef8d79d7677d9875ec686d2289ef77de77e593fd7642ffb45b70addf.jpg)


例如，在AIC中将L0C的计算结果搬运到GM后，AIV需要将GM的数据搬运到UB。 此时，可以使用CrossCoreSetFlag和CrossCoreWaitFlag命令，确保数据从L0C成 功搬运到GM后，再从GM搬运到UB，流程如下图所示。 

![](images/b4c79a71512d5f321f82d1f29de73217a59b5b6febfad4346ed4250d95e90cc4.jpg)


CrossCoreSetFlag和CrossCoreWaitFlag接口配合使用。使用时需传入核间同步的 标记ID(flagId)，即上图中的ID1，每个ID对应一个初始值为0的计数器。执行 CrossCoreSetFlag后ID对应的计数器增加1；执行CrossCoreWaitFlag时如果对应 的计数器数值为0则阻塞不执行；如果对应的计数器大于0，则计数器减一，同时 后续指令开始执行。flagId取值范围是0-10。 

需要注意以下几点： 

# 成对使用

CrossCoreSetFlag和CrossCoreWaitFlag必须成对使用，否则可能导致算子超 时问题。 

# 一致性要求

CrossCoreSetFlag 的模板参数和flagId必须与CrossCoreWaitFlag完全一致， 否则视为不同的flagId。例如，CrossCoreSetFlag<0x0, PIPE_MTE3>(0x8) 和 CrossCoreSetFlag<0x2, PIPE_FIX>(0x8) 设置的不是同一个flagId。 

# 避免连续设置

不允许连续设置同一个flagId，以防止计数器状态混乱。 

# 与高阶 API 的使用冲突

Matmul高阶API内部实现中使用了本接口进行核间同步控制，所以不建议开 发者同时使用该接口和Matmul高阶API，否则会有flagId冲突的风险。 

# 计数器限制

同一flagId的计数器最多可以设置15次。 

# 默认流水类型

CrossCoreWaitFlag不需要显式设置指令所在的流水类型，默认使用PIPE_S。 

# 2.6.3 硬件约束

# 2.6.3.1 NPU 架构版本 200x

本节介绍硬件约束以及解决方案建议。对应的产品型号为：Atlas 推理系列产品。 

# 全局变量使用约束

NPU架构版本200x不支持Generic Addressing通用寻址（针对UB、stack、GM等 地址空间），因此语言层面地址空间必须匹配。不同的地址空间信息不允许转 换，不符合语法。全局变量位于GM上，传参位于stack上，函数内传参使用全局 变量时会报错。目前编译器仅在优化级别为O0的场景下，对constexpr做了适配处 

理：将全局变量先从DDR上放到stack上。所以全局变量仅支持在O0下使用 constexpr进行定义和使用，在其他场景均不支持。 

# 支持场景

在O0下支持constexpr全局变量小规模类型（整型、浮点型）数据的引用，支 持数组取元素。 

```c
constexpr int a=1;  
int *pa=&a;  
//数组  
constexpr uint8_t padList[4] = {0, 1, 3, 5};  
__acore__ uint64_t Compute uint32_t padNumber){  
uint64_t regFMatrix = 3;  
for (uint32_t i = 0; i < padNumber; i++) {  
    regFMatrix |= uint64_t PadList[i]);  
}  
return regFMatrix; 
```

# 不支持场景

对于使用constexpr之外的全局参数将报错。 

```cpp
const float aa = 3.141592653589; // 不支持const 应修改为constexpr template<typename T> __global__ __aicore__ void hello_world3() { AscendC::printf("global var is %f\n", aa); }; 
```

# 2.6.3.2 NPU 架构版本 220x

本节介绍硬件约束以及解决方案建议。对应的产品型号为： 

● Atlas A3 训练系列产品/Atlas A3 推理系列产品 

● Atlas A2 训练系列产品/Atlas A2 推理系列产品 


表 2-29 硬件约束以及解决方案建议


<table><tr><td>分类</td><td>硬件约束描述</td><td>解决方案建议</td></tr><tr><td>内存访问 (L0 Buffer/L 1 Buffer/UB等)</td><td>各存储单元的最小访问粒度/地址对齐要求: Unified Buffer: 32Byte对齐。 L1 Buffer: 32Byte对齐。 LOA Buffer/LOB Buffer: 512Byte对齐。 LOC Buffer: 64Byte对齐。 BiasTable Buffer: 64Byte对齐。 Fixpipe Buffer: 128Byte对齐。</td><td>·进行数据搬运时,需要感知对齐约束。 ·针对UB,遇到一些非对齐的场景,可以使用非对齐搬运的接口或者通过一些技巧(比如搬入时包含冗余数据,搬出时去除冗余数据)来解决。详情见3.3.2.7 非对齐场景。</td></tr><tr><td>内存访问(UB)</td><td>UB bank访问冲突(Vector计算访问/搬运访问)。</td><td>需要按照芯片要求,在软件实现时错开处理的地址,从而解决bank冲突。具体解决方案可参考3.8.5.11避免Unified Buffer的bank冲突章节。</td></tr><tr><td>内存访问(GM)</td><td>多核并行同地址访问GM,会被硬件串行化。</td><td>对相同地址的访问,会被硬件串行化,性能为排队时间,大约下降10%-20%;多核访问通过错峰访问(调整数据访问顺序和修改切分策略等),使得第一次加载数据到L2 Cache,后续访问性能反而提升。具体解决方案可参考3.8.5.6避免同地址访问章节。</td></tr><tr><td>内存访问(GM)</td><td>单次搬运数据长度16KBI以上时,可发挥带宽的最佳性能。</td><td>根据实测经验,单次搬运数据长度16KBI以上时,通常能较好地发挥出带宽的最佳性能。因此对于单次搬运,应考虑尽可能的搬运较大的数据块(不同芯片不一样)。具体解决方案可参考3.8.5.1尽量一次搬运较大的数据块章节。</td></tr><tr><td>内存访问(GM--&gt;L1)</td><td>DataCopy中源操作数相邻连续数据块的间隔(前面一个数据块的尾与后面数据块的头的间隔)不要超出65535,单位为DataBlock(32字节)。</td><td>前面一个数据块的尾与后面数据块的头的间隔超出65535时,需要拆分成多条指令来实现。</td></tr><tr><td>内存访问(GM)</td><td>数据搬运会被拆成128B/256B/512B不同长度进行搬运,非对齐会向上取整。</td><td>Tiling尽量让搬运的内轴128B、256B、512B对齐。具体解决方案可参考3.8.5.2 GM地址尽量512B对齐章节。</td></tr><tr><td>Cube</td><td>MTE1和MMAD指令队列的深度为32。</td><td>对应指令队列容易满,会阻塞其他指令下发,引起流水断流。Load2D从L1 Buffer搬运到L0 Buffer,需要发射32条指令,Load3D只需要一条指令,建议使用Load3D来实现。</td></tr><tr><td>ICache</td><td>ICache硬件规格限制32KB。</td><td>拆分Tiling_key或使用模板函数来减少代码段。详情见2.10.2.5.5 Tiling模板编程。</td></tr><tr><td>ICache</td><td>多核并行同地址访问ICache,会被硬件串行化。</td><td>小Shape场景尽量减少启动核数,减少多核同地址访问问题。</td></tr><tr><td>DCache</td><td>DCache硬件规格限制32KB</td><td>无</td></tr><tr><td>Scalar</td><td>标量写GM时,数据会被缓存在Dcache。硬件不保证DCache和GM一致性,需要用户保证。</td><td>使用DataCacheCleanAndInvalid来保证一致性。</td></tr><tr><td>Cube</td><td>LOC Buffer容量128KB。</td><td>无</td></tr><tr><td>Cube</td><td>BiasTable Buffer为1KB。</td><td>无</td></tr><tr><td>Cube</td><td>Cube计算场景float算力为half算力的1/4。</td><td>无</td></tr><tr><td>Cube</td><td>Cube输出随路量化场景,不支持int32_t到bfloat16_t类型量化。</td><td>·AIV上存在int32_t-&gt;float、float&gt;bfloat16_t的转换。
·AIC支持float-&gt;bfloat16_t的随路量化。</td></tr><tr><td>Vector</td><td>Reduce接口half比float性能差。</td><td>half写回UB时存在非32Byte对齐,导致性能劣化,建议把half转float计算,此场景建议使用float数据类型。</td></tr><tr><td>Vector</td><td>Exp/Ln接口处理同样数量的half/full的耗时是一样的</td><td>内部对float做了优化,故两者性能相当,开发者可以根据实际情况选择合适的精度类型。</td></tr><tr><td>流水同步(核内)</td><td>set/wait同步不匹配,状态会残留,影响后续算子。</td><td>通过孪生调试/mssanitizer工具,提前识别此类问题。</td></tr><tr><td>流水同步(核间)</td><td>CrossCoreSetFlag计数器存在限制,超出15次需要做一次反向同步,否则会出现卡死。</td><td>通过孪生调试/mssanitizer工具,超出场景提前报错。</td></tr><tr><td>API通用约束</td><td>使用Ascend C API时,源操作数和目的操作数的地址重叠通用约束</td><td>使用基础API的Tensor高维切分计算接口时,为了节省地址空间,开发者可以定义一个Tensor,供源操作数与目的操作数同时使用(即地址重叠)。使用时需要注意以下约束:
·单次迭代内:源操作数与目的操作数必须100%完全重叠,不支持部分重叠。
·多次迭代间:不支持前序迭代的目的操作数与后序迭代的源操作数重叠。例如,第N次迭代的目的操作数是第N+1次的源操作数。在这种情况下,第N次迭代可能会改写覆盖源操作数的数值,导致无法得到预期结果。特别地,对于部分双目计算类的API(Add、Sub、Mul、Max、Min、AddRelu、SubRelu),当数据类型为half、int32_t、float时,支持前序迭代的目的操作数与后序迭代的源操作数重叠:仅针对目的操作数和第二个源操作数重叠的情况,且src1RepStride或者dstRepStride必须为0。</td></tr></table>