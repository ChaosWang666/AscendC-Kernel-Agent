<!-- Source: 算子开发指南.md lines 6723-7434 | Section: 2.9 概念原理和术语 -->

# 2.9 概念原理和术语

# 2.9.1 术语表


表 2-33 术语表


<table><tr><td>术语/缩略语</td><td>含义</td></tr><tr><td>A1</td><td>AscendC::TPosition::A1代表设备上用于矩阵计算的逻辑内存，用于存放左矩阵，物理存储对应Al Core的L1 Buffer。</td></tr><tr><td>A2</td><td>AscendC::TPosition::A2代表设备上用于矩阵计算的逻辑内存，用于存放小块左矩阵（如经过分割、适配LOA Buffer容量的分块），物理存储对应Al Core的L0A Buffer。</td></tr><tr><td>AddrReg</td><td>Address Register(地址寄存器),是用于存储地址偏移量的寄存器。</td></tr><tr><td>AI Core</td><td>AI处理器的计算核,负责执行矩阵、矢量计算密集的任务。</td></tr><tr><td>AIC</td><td>在AI Core分离模式下,一组Cube Core和Vector Core组合中的Cube Core。</td></tr><tr><td>AIV</td><td>在AI Core分离模式下,一组Cube Core和Vector Core组合中的Vector Core。</td></tr><tr><td>Ascend IR</td><td>Ascend Intermediate Representation, AI处理器专用的、用于表达计算流程的抽象数据结构。在本文档中,若无特殊说明,IR默认指代Ascend IR。</td></tr><tr><td>B1</td><td>AscendC::TPosition::B1代表设备上用于矩阵计算的逻辑内存,用于存放右矩阵,物理存储对应AI Core的L1 Buffer。</td></tr><tr><td>B2</td><td>AscendC::TPosition::B2代表设备上用于矩阵计算的逻辑内存,用于存放小块右矩阵(如经过分割、适配L0B Buffer容量的分块),物理存储对应AI Core的L0B Buffer。</td></tr><tr><td>Block</td><td>Block在不同场景下具有多种含义,通常情况下指AI Core的逻辑核。典型场景有:· AI Core逻辑核:一个Block表示一个AI Core的逻辑核,其BlockID是以0为起始的逻辑编号。· DataBlock:一个DataBlock表示一条NPU矢量计算指令处理的数据单元,大小通常为32字节,一条指令可同时处理多个DataBlock。· 基本块:表示一次计算需要的典型数据块大小。</td></tr><tr><td>BlockID</td><td>以0为起始的AI Core逻辑编号,可以比实际硬件核数大。</td></tr><tr><td>numBlocks</td><td>参与计算的逻辑AI Core核数,在调用核函数时由开发者指定,其值一般等于或大于实际物理核数。</td></tr><tr><td>BiasTable Buffer</td><td>偏置存储,AI Core内部物理存储单元,通常用于存储矩阵计算所需的Bias(偏置)数据,与逻辑内存AscendC::TPosition::C2相对应。</td></tr><tr><td>Broadcast</td><td>广播,一种张量操作机制。通过广播,较小的张量可以自动扩展以匹配较大的张量的形状。</td></tr><tr><td>C1</td><td>AscendC::TPosition::C1代表设备上用于矩阵计算的逻辑内存,用于存放Bias(偏置)数据,物理存储对应AI Core的L1 Buffer或Unified Buffer。</td></tr><tr><td>C2</td><td>AscendC::TPosition::C2代表设备上用于矩阵计算的逻辑内存,用于存放小块Bias(偏置)数据(如经过分割、适配BT Buffer容量的分块),物理存储对应AI Core的BT Buffer或LOC Buffer。</td></tr><tr><td>C2PIPE2GM</td><td>AscendC::TPosition::C2PIPE2GM代表设备上用于矩阵计算的逻辑内存,用于存放量化参数,物理存储对应AI Core的FixpipeBuffer。</td></tr><tr><td>Cache Line</td><td>缓存（DCache、ICache、L2 Cache）中的最小数据单位。</td></tr><tr><td>Core</td><td>拥有独立Scalar计算单元的计算核，Scalar计算单元承担了核内的指令发射等功能，也称之为核内的调度单元。</td></tr><tr><td>CO1</td><td>AscendC::TPosition::CO1代表设备上用于矩阵计算的逻辑内存，用于存放小块矩阵计算结果（如经过分割的矩阵计算结果分块），物理存储对应AI Core的LOC Buffer。</td></tr><tr><td>CO2</td><td>AscendC::TPosition::CO2代表设备上用于矩阵计算的逻辑内存，用于存放矩阵计算结果（如原始矩阵的最终计算结果），物理存储对应Global Memory或AI Core的Unified Buffer。</td></tr><tr><td>Compute</td><td>Ascend C算子编程范式中典型的三个阶段之一，负责完成计算任务。</td></tr><tr><td>Copyln</td><td>Ascend C算子编程范式中典型的三个阶段之一，负责将待计算数据从Global Memory搬运到Local Memory。</td></tr><tr><td>CopyOut</td><td>Ascend C算子编程范式中典型的三个阶段之一，负责将计算结果从Local Memory搬运到Global Memory。</td></tr><tr><td>Core ID</td><td>AI Core核的物理编号，与实际硬件核数一一对应。</td></tr><tr><td>Cube</td><td>AI Core上的Cube计算单元，负责执行矩阵运算。以float16数据类型为例，Cube每次执行可完成两个float16类型的16x16矩阵的乘法操作。</td></tr><tr><td>Cube Core</td><td>矩阵计算核，专注于矩阵计算。由Scalar调度单元、矩阵计算单元、搬运单元等组成，不包括矢量计算单元。</td></tr><tr><td>DataBlock</td><td>矢量计算指令处理的数据单元，大小通常为32字节，矢量计算指令执行一次，可同时处理多个DataBlock。</td></tr><tr><td>DataBlock Stride</td><td>矢量计算指令单次Repeat内DataBlock的间隔大小，即下次处理的起始数据地址与本次处理的起始数据地址之间的DataBlock个数。</td></tr><tr><td>DCache</td><td>Data Cache，数据缓存。用于缓存Scalar计算单元近期可能被重复访问的数据段，以提升访问效率。</td></tr><tr><td>Device</td><td>Device指安装了昇腾AI处理器的硬件设备，利用PCIe接口与主机Host侧连接，为Host提供神经网络计算能力。若存在多个Device，多个Device之间的内存资源不能共享。</td></tr><tr><td>Dim3</td><td>Dim3是用于定义单个线程块中三维线程结构的数据类型。使用AscendC::Simt::Dim3在启动SIMT VF时指定3个维度的取值，3个维度的乘积必须小于等于2048。</td></tr><tr><td>DMA</td><td>Direct Memory Access，直接内存访问单元。负责数据搬运，包括Global Memory和Local Memory之间的数据搬运以及不同层级Local Memory之间的数据搬运，包含搬运单元MTE2、MTE3等。</td></tr><tr><td>DoubleBuffer/D B</td><td>双缓冲,并行领域常用的优化方式,通过创建多个持有数据的缓冲区(Buffer)提高数据处理的并行性。</td></tr><tr><td>Elementwise</td><td>元素级操作是对张量的每个元素独立进行的操作。每个元素的结果仅依赖于对应的输入元素。</td></tr><tr><td>Fixpipe</td><td>AI Core中负责将矩阵计算结果从LOC Buffer搬运到Global Memory或L1 Buffer的单元,搬运过程中随路完成量化、激活等操作。</td></tr><tr><td>Fixpipe Buffer</td><td>AI Core内部物理存储单元,通常用于存储Fixpipe搬运过程中所需的量化参数等数据,与逻辑内存 AscendC::TPosition::C2PIPE2GM相对应。</td></tr><tr><td>Global Memory/GM</td><td>设备端的主内存,AI Core的外部存储,用于存储大规模数据,但需要优化访问模式以提升性能。</td></tr><tr><td>GlobalTensor</td><td>存放Global Memory全局数据的Tensor。</td></tr><tr><td>Host</td><td>指与设备端Device相连接的X86服务器、ARM服务器,会利用 Device提供的NN(Neural-Network)计算能力,完成业务。</td></tr><tr><td>ICache</td><td>Instruction Cache,指令缓存。用于缓存最近或频繁使用的指令。极致性能优化时,需要关注如何降低ICache Miss(指令缓存未命中)。</td></tr><tr><td>InferShape</td><td>算子shape推导,仅在GE图模式时才使用。实际的网络模型生成过程中,会先进行Tensor shape以及datatype的推导。这样可以在图执行之前,就知道各Tensor的数据类型和形状,提前校验其正确性;同时提前推理出算子的输出张量描述,包括张量的形状、数据类型及数据排布格式等信息,算子构图准备阶段就可以为所有的张量静态分配内存,避免动态内存分配带来的开销。</td></tr><tr><td>Kernel</td><td>核函数,是Device设备上执行的并行函数。核函数通过 __global__修饰,多个核并行执行相同的核函数,其主要区别是不同核函数运行时具有不同的BlockID。</td></tr><tr><td>Kernel Launch</td><td>将kernel程序提交至硬件进行启动执行的过程。</td></tr><tr><td>LOA Buffer</td><td>AI Core内部物理存储单元,通常用于存储矩阵计算的左矩阵,与逻辑内存AscendC::TPosition::A2相对应。</td></tr><tr><td>LOB Buffer</td><td>AI Core内部物理存储单元,通常用于存储矩阵计算的右矩阵,与逻辑内存AscendC::TPosition::B2相对应。</td></tr><tr><td>LOC Buffer</td><td>AI Core内部物理存储单元,通常用于存储矩阵计算的结果,与逻辑内存AscendC::TPosition::CO1相对应。</td></tr><tr><td>L1 Buffer</td><td>AI Core内部物理存储单元,空间相对较大,通常用于缓存矩阵计算的输入数据。矩阵计算的输入一般需要从GM搬运到L1 Buffer,然后分别搬运到LOA Buffer和LOB Buffer。L1 Buffer与逻辑内存AscendC::TPosition::A1、AscendC::TPosition::B1相对应。</td></tr><tr><td>L2 Cache</td><td>二级缓存，专门用于存储频繁访问的数据，以便减少对Global Memory的读写。</td></tr><tr><td>Lane</td><td>Warp中的每个线程称为Lane。</td></tr><tr><td>LCM</td><td>Local Cache Memory, AscendC::TPosition::LCM代表临时共享的Unified Buffer空间，与VECCALC实现同样的功能。</td></tr><tr><td>Local Memory</td><td>AI Core的内部存储，包括L1 Buffer、LOA Buffer、LOB Buffer、LOC Buffer、Unified Buffer等存储单元。</td></tr><tr><td>LocalTensor</td><td>存放AI Core中Local Memory本地数据的Tensor。</td></tr><tr><td>Mask</td><td>用于控制矢量计算指令每次Repeat内参与计算的元素，可通过连续模式和逐比特模式两种方式进行设置。</td></tr><tr><td>MaskReg</td><td>掩码寄存器，是一个256位的寄存器，用于指示在计算过程中RegTensor的哪些元素参与计算。</td></tr><tr><td>Membase</td><td>Membase是指基于内存的架构。Membase架构中所有操作均基于内存进行，这意味着每次计算都需要从Local Memory加载数据，计算完成后将结果搬回Local Memory，中间计算结果都需要暂存在Local Memory上。</td></tr><tr><td>MTE1</td><td>Memory Transfer Engine 1, AI Core的数据传递引擎，负责将数据从L1 Buffer搬运到LOA Buffer或LOB Buffer等。注意：不同硬件能力可能有差异。</td></tr><tr><td>MTE2</td><td>Memory Transfer Engine 2, AI Core的数据传递引擎，负责将数据从GM搬运到L1 Buffer、LOA Buffer、LOB Buffer、Unified Buffer等。注意：不同硬件能力可能有差异。</td></tr><tr><td>MTE3</td><td>Memory Transfer Engine 3, AI Core的数据传递引擎，负责将数据从Unified Buffer搬运到Global Memory、L1 Buffer等。注意：不同硬件能力可能有差异。</td></tr><tr><td>NC1HWC0</td><td>一种五维数据格式，其中C0与硬件架构强相关，采用该格式可提升矩阵乘法的计算效率。</td></tr><tr><td>NCHW</td><td>按照[Batch, Channels, Height, Width]的排列顺序存储特征图数据。</td></tr><tr><td>ND</td><td>普通格式，N维张量。</td></tr><tr><td>NHWC</td><td>按照[Batch, Height, Width, Channels]的排列顺序存储特征图数据。</td></tr><tr><td>NPU</td><td>Neural-Network Processing Unit，神经网络处理器单元。采用“数据驱动并行计算”的架构，专门用于处理人工智能应用中的大量计算任务。</td></tr><tr><td>OP</td><td>算子（Operator，简称OP），是深度学习算法中执行特定数学运算或操作的基础单元，例如激活函数（如ReLU）、卷积（Conv）、池化（Pooling）以及归一化（如Softmax）。通过组合这些算子，可以构建神经网络模型。</td></tr><tr><td>OpType</td><td>算子类型,一类算子的统称。例如,在网络中可能会出现多个Add算子,名称分别为Add1、Add2,但这类算子的OpType均为Add。</td></tr><tr><td>Pipe</td><td>Ascend C编程范式核心概念之一,用于统一管理Device端内存等资源,一个Kernel函数必须且只能初始化一个Pipe对象。</td></tr><tr><td>Preload</td><td>在计算任务开始前,预先将必要的指令或数据加载到缓存中,用于减少指令或数据访问的延迟,提高计算效率。</td></tr><tr><td>Reduce</td><td>减维操作,用于减少多维张量的维度。常见的减维操作包括求和、求平均、求最大值、求最小值等。</td></tr><tr><td>RegTensor</td><td>矢量数据寄存器,Reg矢量计算基本单元。</td></tr><tr><td>Regbase</td><td>Regbase是指基于寄存器的架构。Regbase架构下,中间结果可暂存在寄存器中,无需数据搬出到Local Memory的开销。</td></tr><tr><td>Repeat</td><td>矢量计算指令执行一次,读取8个DataBlock数据进行计算,称之为一个迭代(Repeat)。通常情况下,需要循环执行多次才能完成所有数据的读取与计算。</td></tr><tr><td>Repeat Stride</td><td>矢量计算指令循环执行时,下一次Repeat起始数据地址与当前Repeat起始数据地址之间的DataBlock个数。</td></tr><tr><td>Repeat Times</td><td>矢量计算指令循环执行的次数。</td></tr><tr><td>Scalar</td><td>AI Core上的标量计算单元,主要负责标量数据运算和对其他单元(如MTE数据搬运单元、Vector矢量计算单元、Cube矩阵计算单元)的指令发射。</td></tr><tr><td>SIMD</td><td>SIMD: Single Instruction, Multiple Data,一条指令同时对多个数据进行相同的操作。</td></tr><tr><td>SIMT</td><td>SIMT: Single Instruction, Multiple Threads,一条指令被多个线程并行执行,每个线程处理不同的数据。</td></tr><tr><td>SPMD</td><td>Single-Program Multiple-Data,一种并行程序设计模型,其主要思想是使用同一个程序在多个核上并行执行,但每个核处理不同数据。</td></tr><tr><td>SSBuffer</td><td>AI Core内部物理存储单元,分离模式下,Cube Core和Vector Core 1:2通信可选择使用SSBuffer在Cube Core和Vector Core的Scalar单元之间通信。</td></tr><tr><td>SuperKernel</td><td>SuperKernel是一种算子的二进制融合技术,与源码融合不同,它聚焦于内核函数(Kernel)的二进制的调度方案,展开深度优化,于已编译的二进制代码基础上融合创建一个超级Kernel函数(SuperKernel),以调用子函数的方式调用多个其他内核函数,也就是子Kernel。相对于单算子下发,SuperKernel技术可以减少任务调度等待时间和调度开销,同时利用Task间隙资源进一步优化算子头开销。</td></tr><tr><td>Tensor</td><td>Tensor张量是算子计算数据的容器,是N维数据结构,最常见的是标量、矢量或矩阵。张量的元素可以包含整数值、浮点值或字符串值。</td></tr><tr><td>Thread Block</td><td>线程块,一个线程块最大支持2048个线程( Thread )。SIMT VF一次在AI Core上运行一个线程块( Block )。</td></tr><tr><td>Tiling</td><td>Tiling指数据的切分和分块。计算数据量较大时,需要将数据进行多核切分、每个核也需要分块多次计算。</td></tr><tr><td>TilingData</td><td>TilingData指数据切分和分块的相关参数(如每次搬运的块大小、循环次数)。鉴于设备端Scalar计算能力限制,一般Tiling参数在Host侧计算完成,然后传输到设备侧供Kernel函数使用。</td></tr><tr><td>TilingFunc</td><td>算子工程提供的在Host侧计算Tiling的默认函数。</td></tr><tr><td>TilingKey</td><td>用来区分Kernel函数不同版本的特例实现,不同的TilingKey会编译生成不同二进制。</td></tr><tr><td>TPosition</td><td>Ascend C管理不同层级的物理内存时,用一种抽象的逻辑位置(T Position)来表达各级别的存储,代替了片上物理存储的概念,达到隐藏硬件架构的目的。TPosition类型包括: VECIN、VECOUT、VECCALC、A1、A2、B1、B2、CO1、CO2等,其中VECIN、VECCALC、VECOUT主要用于矢量编程,A1、A2、B1、B2、CO1、CO2用于矩阵编程。</td></tr><tr><td>TSCM</td><td>AscendC::TPosition::TSCM表示L1 Buffer空间对应的逻辑内存,需开发者自行管理以高效利用硬件资源,主要用于Matmul计算。比如,开发者可缓存一份TSCM数据,在不同使用场景中灵活配置为Matmul操作的A矩阵、B矩阵或Bias偏置矩阵,实现内存复用与计算效率优化。</td></tr><tr><td>UnalignRegForLoad</td><td>非对齐寄存器,用作缓冲区来优化UB和RegTensor之间连续不对齐地址访问的开销,适用于连续非对齐搬入场景。</td></tr><tr><td>UnalignRegForStore</td><td>非对齐寄存器,用作缓冲区来优化UB和RegTensor之间连续不对齐地址访问的开销,适用于连续非对齐搬出场景。</td></tr><tr><td>UnifiedBuffer/UB</td><td>AI Core内部存储单元,主要用于矢量计算,与逻辑内存AscendC::TPosition::VECIN、AscendC::TPosition::VECOUT、AscendC::TPosition::VECCALC相对应。</td></tr><tr><td>VECCALC</td><td>Vector Calculation,AscendC::TPosition::VECCALC代表设备上用于矢量计算的逻辑内存,用于存放临时变量,物理存储对应AI Core的Unified Buffer。</td></tr><tr><td>VECIN</td><td>Vector Input,AscendC::TPosition::VECIN代表设备上用于矢量计算的逻辑内存,用于存放矢量计算的输入数据,物理存储对应AI Core的Unified Buffer。</td></tr><tr><td>VECOUT</td><td>Vector Output,AscendC::TPosition::VECOUT代表设备上用于矢量计算的逻辑内存,用于存放矢量计算的输出数据,物理存储对应AI Core的Unified Buffer。</td></tr><tr><td>Vector</td><td>AI Core上的Vector计算单元,负责执行矢量运算。其算力低于Cube,但灵活度高于Cube(如支持数学中的求倒数,求平方根等)。</td></tr><tr><td>Vector Core</td><td>矢量计算核,专注于矢量计算,由Scalar调度单元、矢量计算单元、搬运单元等组成,不包括矩阵计算单元。</td></tr><tr><td>VF</td><td>Vector Funtion(向量函数)是由标量计算单元调用的一组连续的向量指令,用_simt_vf_或_simd_vf_标记。</td></tr><tr><td>VL</td><td>Vector Length,RegTensor的位宽,通常取值为256Byte。</td></tr><tr><td>Warp</td><td>每个线程块被切分成多个Warp,Warp是执行相同指令的线程集合,每个Warp包含32个线程 thread),一个Block的多个Warp被依次调度到Al Core中的同一个AlV核执行。</td></tr><tr><td>Workspace</td><td>通常情况下指一个预分配的、临时使用的Global Memory内存,用于存储中间结果或临时数据。</td></tr><tr><td>CPU域调试</td><td>Ascend C提供的一种孪生调试方法,在CPU上模拟设备侧Kernel函数的执行和调试,仅调试算子功能和精度。</td></tr><tr><td>基本块</td><td>一次计算需要的典型数据块大小。</td></tr><tr><td>静态Tensor编程</td><td>静态Tensor编程方式,相比基于Pipe的编程方式,这种方式避免了TPipe内存管理初始化过程(约数百纳秒),从而减少了运行时开销,更有助于开发者实现极致性能。通过直接构造指定地址和存储位置的LocalTensor,并将其传递给计算、搬运等API进行编程,提供了更高的灵活性。</td></tr><tr><td>Kernel直调</td><td>一种简单直接的Kernel调用方式。完成Kernel侧算子实现和Host侧Tiling实现后,即可通过运行时接口,完成算子Kernel直调。该方式下Tiling开发不受CANN框架的限制,简单直接,多用于算子功能的快速验证。</td></tr><tr><td>NPU域调试</td><td>Ascend C提供的一种孪生调试方法,指基于NPU仿真软件或NPU硬件调试。</td></tr><tr><td>Tiling下沉</td><td>Tiling下沉是指将Tiling计算下沉至Device侧的AI CPU上执行,从而实现计算全程在Device侧高效完成。</td></tr><tr><td>分离模式</td><td>AI Core的一种工作模式,其矩阵计算单元和矢量计算单元分别由独立的Scalar调度单元进行调度,并分离部署在Cube Core和Vector Core上。将Cube Core和Vector Core按照一定比例(1:N)进行组合,这样的组合视为一个AI Core,AI Core的核数以Cube Core为准。</td></tr><tr><td>孪生调试</td><td>Ascend C提供的算子调试方法,支持在CPU域调试精度和NPU域调试精度/性能。</td></tr><tr><td>流水任务</td><td>Ascend C编程范式是一种流水线式的编程范式,把算子核内的处理程序,分成多个流水任务。流水任务是指单核处理程序中主程序调度的并行任务。在核函数内部,可以通过流水任务实现数据的并行处理,进一步提升性能。</td></tr><tr><td>连续模式</td><td>使用Mask控制矢量计算每次Repeat内参与计算的元素时，可选择的模式之一，表示前面连续的多少个元素参与计算。</td></tr><tr><td>耦合模式</td><td>AI Core的一种工作模式，采用同一个Scalar调度单元同时调度矩阵计算单元、矢量计算单元，所有的单元部署在一个AI Core上。</td></tr><tr><td>融合算子</td><td>融合算子由多个独立的小算子融合而成，其功能与多个小算子的功能等价，性能方面通常优于独立的小算子。用户可以根据实际业务场景诉求，按照具体算法自由融合矢量（Vector）、矩阵（Cube）算子以达到性能上的收益。</td></tr><tr><td>算子入图</td><td>算子入图指通过GE图模式运行算子，在图模式下首先将所有算子构造成一张图，然后通过GE将图下发到AI处理器执行。</td></tr><tr><td>算子原型</td><td>算子原型是算子的抽象描述，定义了算子的输入、输出、属性等信息。</td></tr><tr><td>通算融合算子</td><td>通算融合算子是融合集合通信任务和计算任务的算子，在算子执行过程中，计算和通信任务可以实现部分流水并行，从而提升性能。</td></tr><tr><td>Reg矢量计算</td><td>Reg矢量计算API是面向RegBase架构开发的API，用户可以通过该类API直接对芯片中涉及Vector计算的寄存器进行操作，实现更大的灵活性和更好的性能。</td></tr><tr><td>逐比特模式</td><td>使用Mask控制矢量计算每次Repeat内参与计算的元素时，可选择的模式之一，可以按位控制哪些元素参与计算，bit位的值为1表示参与计算，0表示不参与。</td></tr><tr><td>自定义算子工程</td><td>Ascend C提供的基于msOpGen工具生成的算子工程。</td></tr></table>

# 2.9.2 神经网络和算子

# 2.9.2.1 算子基本概念

算子（Operator，简称OP），是深度学习算法中执行特定数学运算或操作的基础单 元，例如激活函数（如ReLU）、卷积（Conv）、池化（Pooling）以及归一化（如 Softmax）。通过组合这些算子，可以构建神经网络模型。 

本章节介绍算子中常用的基本概念。 

# 算子名称（Op Name）

算子的名称，用于标识网络中的某个算子，同一网络中算子的名称需要保持唯一。如 下图所示Conv1、Pool1、Conv2都是此网络中的算子名称，其中Conv1与Conv2算子 的类型为Convolution，表示分别做一次卷积运算。 


图 2-38 网络拓扑示例


![](images/019a078f52dff7979a2a85b707b3dec8759abfc2d47047663ec63aea28446894.jpg)


# 算子类型（Op Type）

网络中每一个算子根据算子类型进行算子实现的匹配，相同类型算子的实现逻辑相 同。在一个网络中同一类型的算子可能存在多个，例如上图中的Conv1算子与Conv2算 子的类型都为Convolution。 

# 张量（Tensor）

Tensor是算子计算数据的容器，包含如下属性信息。 


表 2-34 Tensor 属性信息


<table><tr><td>属性</td><td>定义</td></tr><tr><td>形状</td><td>Tensor的形状，比如(10, )或者(1024, 1024)或者(2, 3, 4)等。如形状(3, 4)表示第一维有3个元素，第二维有4个元素，(3, 4)表示一个3行4列的矩阵数组。
形式：(i1, i2, ..., in)，其中i1到in均为正整数。</td></tr><tr><td>数据类型</td><td>指定Tensor对象的数据类型。
取值范围：float16, float32, int8, int16, int32, uint8, uint16, bfloat16, bool等。</td></tr><tr><td>数据排布格式</td><td>数据的物理排布格式，详细请参见2.9.2.2 数据排布格式。</td></tr></table>

# 形状（Shape）

张量的形状，以(D0, D1, … ,Dn-1)的形式表示，D0到Dn是任意的正整数。 

如形状(3,4)表示第一维有3个元素，第二维有4个元素，(3,4)表示一个3行4列的矩阵数 组。 

形状的第一个元素对应张量最外层中括号中的元素个数，形状的第二个元素对应张量 中从左边开始数第二个中括号中的元素个数，依此类推。例如： 


表2-35 张量的形状举例


<table><tr><td>张量</td><td>形状</td><td>描述</td></tr><tr><td>1</td><td>(0,)</td><td>0维张量，也是一个标量</td></tr><tr><td>[1,2,3]</td><td>(3,)</td><td>1维张量</td></tr><tr><td>[[1,2],[3,4]]</td><td>(2,2)</td><td>2维张量</td></tr><tr><td>[[[1,2],[3,4]], [[5,6],[7,8]]]]</td><td>(2,2,2)</td><td>3维张量</td></tr></table>

物理含义我们应该怎么理解呢？假设我们有这样一个shape=(4, 20, 20, 3)。 

假设有一些照片，每个像素点都由红/绿/蓝3色组成，即shape里面3的含义，照片的宽 和高都是20，也就是20*20=400个像素，总共有4张的照片，这就是shape=(4, 20, 20, 3)的物理含义。 


图 2-39 示意图


![](images/c8f4bb1b09616ff2bd043613cb7111ba6df3b5600807a558202ca8c0afd4614a.jpg)


如果体现在编程上，可以简单把shape理解为操作Tensor的各层循环，比如我们要对 shape=(4, 20, 20, 3)的A tensor进行操作，循环语句如下： 

```txt
produce A {
    for (i, 0, 4) {
        for (j, 0, 20) {
            for (p, 0, 20) {
                for (q, 0, 3) {
                    A[(((((i*20) + j)*20) + p)*3) + q)] = a_tensor[(((((i*20) + j)*20) + p)*3) + q)]
            }
        }
    }
} 
```

# 轴（axis）

轴是相对shape来说的，轴代表张量的shape的下标，比如张量a是一个5行6列的二维 数组，即shape是(5,6)，则axis=0表示是张量中的第一维，即行。axis=1表示是张量中 的第二维，即列。 

例如张量数据[[[1,2],[3,4]], [[5,6],[7,8]]]，Shape为(2,2,2)，则轴0代表第一个维度的 数据即[[1,2],[3,4]]与[[5,6],[7,8]]这两个矩阵，轴1代表第二个维度的数据即[1,2]、 [3,4]、[5,6]、[7,8]这四个数组，轴2代表第三个维度的数据即1，2，3，4，5，6， 7，8这八个数。 

轴axis可以为负数，此时表示是倒数第axis个维度。 

N维Tensor的轴有：0 , 1, 2,……，N-1。 


图 2-40 轴示意图


![](images/a26c28fac415b0ce2d9214cdb1ce4f4d0bf34d94b1db23537d10a93fcc6b13d4.jpg)


# 2.9.2.2 数据排布格式

数据排布格式（Data Layout Format）是深度学习中对多维Tensor在内存中存储方式 的描述。 

常见的数据格式包括ND、NHWC和NCHW等，为Tensor的每个轴赋予了特定的业务语 义。 

除了上述NHWC和NCHW格式外，还存在一些特殊的私有数据格式，如FRACTAL_NZ （也简称NZ）、NC1HWC0、FRACTAL_Z、NDC1HWC0、FRACTAL_Z_3D等。这些格 式的引入是为了满足AI Core中Cube计算单元的高性能计算需求，通过优化内存布局， 这些格式能够提升计算效率。在使用矩阵乘、卷积API开发相关算子的过程中，您可以 看到这些格式的具体应用。 

# 普通格式

# ● ND、NHWC和NCHW

数据排布格式最初用于表示图像在内存中的存储方式，其中常见的包括ND、 NHWC和NCHW。在一般情况下，所有的Tensor都是N维的（ND），而NHWC和 NCHW则是为四维Tensor中的每个轴赋予了特定的业务语义，例如高度 （Height）、宽度（Width）和通道数（Channels）。 

NHWC和NCHW的主要区别在于通道（Channel）维度的位置： 

NHWC格式中，通道维度位于最后一个位置。 

NCHW格式中，通道维度位于高度和宽度之前。 

具体解释每个轴的含义： 

N：Batch数量，表示图像的数目。 

H：Height，图像的高度，即垂直方向的像素个数。 

W：Width，图像的宽度，即水平方向的像素个数。 

– C：Channels，图像的通道数，例如彩色RGB图像的Channels为3。 

如图2-41所示，以一张格式为RGB的图片为例，NCHW中，C排列在外层，实际存 储的是“RRRRRRGGGGGGBBBBBB”，即同一通道的所有像素值顺序存储在一 起；而NHWC中C排列在最内层，实际存储的则是 

“RGBRGBRGBRGBRGBRGB”，即多个通道的同一位置的像素值顺序存储在一 起。 


图 2-41 NCHW 和 NHWC 存储示例


![](images/20d01d804f32fe351d6f838ad35d73a70998d4a31ac2218c083df94997ac71da.jpg)


尽管存储的数据相同，但不同的存储顺序会导致数据的访问特性不一致，因此即 便进行同样的运算，相应的计算性能也会不同。 

# NDHWC和NCDHW

NDHWC和NCDHW是五维Tensor，较NHWC和NCHW多了一个D的维度，D代表 特征深度（Depth），表示数据在深度方向上的扩展，如视频的时间步或医学图 像的深度层，因此该类格式便于在时间维度上进行卷积操作。以NDHWC为例， 其数据格式如下图所示： 

![](images/35fb3354bb888a9ee8d97caf254577d8b90c77da8844eb37a025263c1741fc46.jpg)


# 矩阵乘相关特殊格式

使用Mmad基础API进行矩阵乘计算时，对矩阵输入输出的数据排布格式有一定的要 求，如下图所示，要求A矩阵（位于L0A Buffer）为FRACTAL_ZZ，B矩阵（位于L0B Buffer）为FRACTAL_ZN，C矩阵（位于L0C Buffer）为FRACTAL_NZ。这些格式将矩 阵划分成了一些分形（Fractal Matrix），适配Cube计算单元每次读取(16, 16)× (16, 16) 的数据进行计算的硬件特点（以half数据类型为例），从而提高矩阵计算的效率。 分形的大小和数据类型有关，也和所在的存储位置有关，具体可参见下文的详细介 绍。 

![](images/a53613c35fd0b34dd0b305274a2621034a796b982b7afe57110daec7ed40840d.jpg)



MatrixA


![](images/d1c983a92844fbfcc63b832d55aa48c2a9de0ca595874b4decc0da61737ee15a.jpg)



MatrixB


![](images/89e7778b0fb5e623b61700f4a94c6879655b8d3dc1127bbe340e2dc53dee669e.jpg)


![](images/b2e9a583a3c0e1040786990a325f07b6869fa05e1967de1a4a6dcb63cdad058e.jpg)



MatrixC


# FRACTAL_NZ/NZ

FRACTAL_NZ格式，简称NZ格式，是对一个Tensor最低两维（一个Tensor的所有 维度，右侧为低维，左侧为高维）进行填充（pad）、拆分（reshape）和转置 （transpose）操作后得到的格式。具体的转换过程如下： 

(M，N)大小的矩阵被分为M1 * N1个分形，按照column major（列优先）排布， 形状如N字形；每个分形内部有M0 * N0个元素，按照row major（行优先）排 布，形状如Z字形，所以这种数据格式称为NZ格式。其中，(M0, N0)表示一个分 形的大小。 

# 通过公式表达为：

(…, B, M, N)->pad->(…, B, M1 * M0, N1 * N0)->reshape->(…, B, M1, M0, N1, N0)->transpose->(…, B, N1, M1, M0, N0) 

# 说明

通常情况下，NZ格式在L0C Buffer和L1 Buffer中分别用于不同的场景： 

● 在L0C Buffer中，NZ格式用于存储矩阵乘法的结果。其分形形状为16x16，包含256个 元素，这种结构非常适合Cube计算单元进行高效的矩阵乘法运算。 

● 在L1 Buffer中，NZ格式被采用以便于将数据搬运到L0A Buffer和L0B Buffer时，能够 方便地转换为对应的ZZ和ZN格式。此时，分形形状为16 x (32B / sizeof(Datatype))， 大小为512字节。 

因此，当数据从L0C Buffer搬运到L1 Buffer时，其分形大小可能会发生变化。 

下面通过一个具体的例子来了解ND格式转换为NZ格式的过程。 

原始Tensor的Shape为(20, 28)： 

```python
data = [x for x in range(20 * 28)]  
data_a = data * np.ones((20 * 28), dtype="float16")  
tensor_a = data_a.reshape((20, 28))  
print(tensor_a) 
```

# 原始Tensor数据打印如下：

```json
[0.1.2.3.4.5.6.7.8.9.10.11.12.13. 14.15.16.17.18.19.20.21.22.23.24.25.26.27.] [28.29.30.31.32.33.34.35.36.37.38.39.40.41. 42.43.44.45.46.47.48.49.50.51.52.53.54.55.] [56.57.58.59.60.61.62.63.64.65.66.67.68.69. 70.71.72.73.74.75.76.77.78.79.80.81.82.83.] [84.85.86.87.88.89.90.91.92.93.94.95.96.97. 98.99.100.101.102.103.104.105.106.107.108.109.110.111.] [112.113.114.115.116.117.118.119.120.121.122.123.124.125. 126.127.128.129.130.131.132.133.134.135.136.137.138.139.] [140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167.] [168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181.] 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195.] [196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223.] [224, 225, 226, 227, 228, 229, 230, 231, 232, 233, 234, 235, 236, 237.] 
```

<table><tr><td>238. 239. 240. 241. 242. 243. 244. 245. 246. 247. 248. 249. 250. 251.]</td></tr><tr><td>[252. 253. 254. 255. 256. 257. 258. 259. 260. 261. 262. 263. 264. 265.</td></tr><tr><td>266. 267. 268. 269. 270. 271. 272. 273. 274. 275. 276. 277. 278. 279.]</td></tr><tr><td>[280. 281. 282. 283. 284. 285. 286. 287. 288. 289. 290. 291. 292. 293.</td></tr><tr><td>294. 295. 296. 297. 298. 299. 300. 301. 302. 303. 304. 305. 306. 307.]</td></tr><tr><td>[308. 309. 310. 311. 312. 313. 314. 315. 316. 317. 318. 319. 320. 321.</td></tr><tr><td>322. 323. 324. 325. 326. 327. 328. 329. 330. 331. 332. 333. 334. 335.]</td></tr><tr><td>[336. 337. 338. 339. 340. 341. 342. 343. 344. 345. 346. 347. 348. 349.</td></tr><tr><td>350. 351. 352. 353. 354. 355. 356. 357. 358. 359. 360. 361. 362. 363.]</td></tr><tr><td>[364. 365. 366. 367. 368. 369. 370. 371. 372. 373. 374. 375. 376. 377.</td></tr><tr><td>378. 379. 380. 381. 382. 383. 384. 385. 386. 387. 388. 389. 390. 391.]</td></tr><tr><td>[392. 393. 394. 395. 396. 397. 398. 400. 401. 402. 403. 404. 405.</td></tr><tr><td>406. 407. 408. 409. 410. 411. 412. 413. 414. 415. 416. 417. 418. 419.]</td></tr><tr><td>[420. 421. 422. 423. 424. 425. 426. 427. 428. 429. 430. 431. 432. 433.</td></tr><tr><td>434. 435. 436. 437. 438. 439. 440. 441. 442. 443. 444. 445. 446. 447.]</td></tr><tr><td>[448. 449. 450. 451. 452. 453. 454. 455. 456. 457. 458. 459. 460. 461.</td></tr><tr><td>462. 463. 464. 465. 466. 467. 468. 469. 470. 471. 472. 473. 474. 475.]</td></tr><tr><td>[476. 477. 478. 479. 480. 481. 482. 483. 484. 485. 486. 487. 488. 489.</td></tr><tr><td>490. 491. 492. 493. 494. 495. 496. 497. 498. 499. 500. 501. 502. 503.]</td></tr><tr><td>[504. 505. 506. 507. 508. 509. 510. 511. 512. 513. 514. 515. 516. 517.</td></tr><tr><td>518. 519. 520. 521. 522. 523. 524. 525. 526. 527. 528. 529. 530. 531.]</td></tr><tr><td>[532. 533. 534. 535. 536. 537. 538. 539. 540. 541. 542. 543. 544. 545.</td></tr><tr><td>546. 547. 548. 549. 550. 551. 552. 553. 554. 555. 556. 557. 558. 559.]</td></tr></table>


转换过程通过伪代码表达如下：


```python
N0 = 16  
N1 = (28 + N0 - 1) // N0  
pad_n = N1 * N0 - 28  
M0 = 16  
M1 = (20 + M0 - 1) // M0  
pad_m = M1 * M0 - 20  
tensor_b = np_pad(tensor_a, [[0, pad_m], [0, pad_n]])  
tensor_b = tensor_b.reshape((M1, M0, N1, N0))  
tensor_b = tensor_b.transpose((2, 0, 1, 3))  
print(tensor_b) 
```

转换过程示意图如下： 

<table><tr><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>...</td><td>11</td><td>12</td><td>13</td><td>14</td><td>15</td><td>16</td><td>17</td><td>18</td><td>19</td><td>20</td><td>...</td><td>27</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>28</td><td>29</td><td>30</td><td>31</td><td>32</td><td>...</td><td>39</td><td>40</td><td>41</td><td>42</td><td>43</td><td>44</td><td>45</td><td>46</td><td>47</td><td>48</td><td>...</td><td>55</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>56</td><td>57</td><td>58</td><td>59</td><td>60</td><td>...</td><td>67</td><td>68</td><td>69</td><td>70</td><td>71</td><td>72</td><td>73</td><td>74</td><td>75</td><td>76</td><td>...</td><td>83</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>84</td><td>85</td><td>86</td><td>87</td><td>88</td><td>...</td><td>95</td><td>96</td><td>97</td><td>98</td><td>99</td><td>100</td><td>101</td><td>102</td><td>103</td><td>104</td><td>...</td><td>111</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>112</td><td>113</td><td>114</td><td>115</td><td>116</td><td>...</td><td>123</td><td>124</td><td>125</td><td>126</td><td>127</td><td>128</td><td>129</td><td>130</td><td>131</td><td>132</td><td>...</td><td>139</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td></td></tr><tr><td>308</td><td>309</td><td>310</td><td>311</td><td>312</td><td>...</td><td>319</td><td>320</td><td>321</td><td>322</td><td>323</td><td>324</td><td>325</td><td>326</td><td>327</td><td>328</td><td>...</td><td>335</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>336</td><td>337</td><td>338</td><td>339</td><td>340</td><td>...</td><td>347</td><td>348</td><td>349</td><td>350</td><td>351</td><td>352</td><td>353</td><td>354</td><td>355</td><td>356</td><td>...</td><td>363</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>364</td><td>365</td><td>366</td><td>367</td><td>368</td><td>...</td><td>375</td><td>376</td><td>377</td><td>378</td><td>379</td><td>380</td><td>381</td><td>382</td><td>383</td><td>384</td><td>...</td><td>391</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>392</td><td>393</td><td>394</td><td>395</td><td>396</td><td>...</td><td>403</td><td>404</td><td>405</td><td>406</td><td>407</td><td>408</td><td>409</td><td>410</td><td>411</td><td>412</td><td>...</td><td>419</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>420</td><td>421</td><td>422</td><td>423</td><td>424</td><td>...</td><td>431</td><td>432</td><td>433</td><td>434</td><td>435</td><td>436</td><td>437</td><td>438</td><td>439</td><td>440</td><td>...</td><td>447</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>448</td><td>449</td><td>450</td><td>451</td><td>452</td><td>...</td><td>459</td><td>460</td><td>461</td><td>462</td><td>463</td><td>464</td><td>465</td><td>466</td><td>467</td><td>468</td><td>...</td><td>475</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>476</td><td>477</td><td>478</td><td>479</td><td>480</td><td>...</td><td>487</td><td>488</td><td>489</td><td>490</td><td>491</td><td>492</td><td>493</td><td>494</td><td>495</td><td>496</td><td>...</td><td>503</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>504</td><td>505</td><td>506</td><td>507</td><td>508</td><td>...</td><td>515</td><td>516</td><td>517</td><td>518</td><td>519</td><td>520</td><td>521</td><td>522</td><td>523</td><td>524</td><td>...</td><td>531</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>532</td><td>533</td><td>534</td><td>535</td><td>536</td><td>...</td><td>543</td><td>544</td><td>545</td><td>546</td><td>547</td><td>548</td><td>549</td><td>550</td><td>551</td><td>552</td><td>...</td><td>559</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>...</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>...</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td></td></tr><tr><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>...</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>...</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>...</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>...</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>...</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>...</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0</td><td>0</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td></td></tr><tr><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>...</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>...</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr><tr><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>...</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr></table>

# 转换后Tensor打印如下：

[[[[ 0. 1. 2. ... 13. 14. 15.] 

[ 28. 29. 30. ... 41. 42. 43.] 

[ 56. 57. 58. ... 69. 70. 71.] 

[364. 365. 366. ... 377. 378. 379.] 

[392. 393. 394. ... 405. 406. 407.] 

[420. 421. 422. ... 433. 434. 435.]] 

[[448. 449. 450. ... 461. 462. 463.] 

[476. 477. 478. ... 489. 490. 491.] 

[504. 505. 506. ... 517. 518. 519.] 

[ 0. 0. 0. ... 0. 0. 0.] 

[ 0. 0. 0. ... 0. 0. 0.] 

[ 0. 0. 0. ... 0. 0. 0.]]] 

[[[ 16. 17. 18. ... 0. 0. 0.] 

[ 44. 45. 46. ... 0. 0. 0.] 

[ 72. 73. 74. ... 0. 0. 0.] 

[380.381.382. 0. 0.0.] 

[408. 409. 410. ... 0. 0. 0.] 

[436. 437. 438. ... 0. 0. 0.]] 

[[464. 465. 466. ... 0. 0. 0.] 

[492. 493. 494. ... 0. 0. 0.] 

[520. 521. 522. ... 0. 0. 0.] 

[ 0. 0. 0. ... 0. 0. 0.] 

[ 0. 0. 0. ... 0. 0. 0.] 

[ 0. 0. 0. ... 0. 0. 0.]]]] 

# FRACTAL_ZZ/ZZ

FRACTAL_ZZ格式，简称ZZ格式，是对一个Tensor最低两维（一个Tensor的所有维 度，右侧为低维，左侧为高维）进行填充（pad）、拆分（reshape）和转置 （transpose）操作后得到的格式。具体转换过程如下： 

(M, K)大小的矩阵被分为M1 * K1个分形，按照row major排布，形状如Z字形； 每个分形内部有M0 * K0个元素，按照row major排布，形状如Z字形，所以这种 数据格式称为ZZ格式。其中，(M0, K0)表示一个分形的大小，分形Shape为16 x (32B / sizeof(Datatype))，大小为512字节。 

![](images/6494e739bf52006d49373a4e6383038d47a287bdef920a09d7972e5ff1500625.jpg)


通过公式表达转换过程如下： 

$(\cdots, B, M, K) \rightarrow$ pad-> $(\cdots, B, M1 * M0, K1 * K0) \rightarrow$ reshape-> $(\cdots, B, M1, M0, K1, K0) \rightarrow$ transpose-> $(\cdots, B, M1, K1, M0, K0)$ 

对于不同的数据类型，M0和K0的大小不同： 

位宽为4的数据类型： $\mathsf { M O } = 1 6$ ， $K 0 { = } 6 4$ 。 

位宽为8的数据类型： $\mathsf { M O } = 1 6$ ， $K 0 = 3 2$ 。 

位宽为16的数据类型： $\mathsf { M O } = 1 6$ ， ${ \sf K O = } 1 6$ 

位宽为32的数据类型， $\mathsf { M O } = 1 6$ ， $\ K 0 { = } 8$ 。 

# FRACTAL_ZN/ZN

FRACTAL_ZN格式，简称ZN格式，是对一个Tensor最低两维（一个Tensor的所有 维度，右侧为低维，左侧为高维）进行填充（pad）、拆分（reshape）和转置 （transpose）操作后得到的格式。具体转换过程如下： 

(K, N)大小的矩阵被分为K1 * N1个分形，按照row major排布，形状如Z字形；每 个分形内部有K0 * N0个元素，按照column major排布，形状如N字形，所以这种 数据格式称为ZN格式。其中，(K0, N0)表示一个分形的大小，分形shape为 (32B / sizeof(Datatype)) x 16，大小为512字节。 

![](images/7c60f95b6acd834eb1b39992bc0b927ba6129c2fc5fa148de4ff84bd2fced774.jpg)


通过公式表达转换过程如下： 

(…, B, K, N)->pad->(…, B, K1 * K0, N1 * N0)->reshape->(…, B, K1, K0, N1, N0)->transpose->(…, B, K1, N1, N0, K0) 

对于不同的数据类型，K0和N0的大小不同： 

位宽为4的数据类型： $K 0 { = } 6 4$ ， $N 0 { = } 1 6$ ； 

位宽为8的数据类型： $K 0 = 3 2$ ， $N 0 { = } 1 6$ ； 

位宽为16的数据类型： ${ \sf K O = } 1 6$ ， $N 0 { = } 1 6$ ； 

位宽为32的数据类型： $\ K 0 { = } 8$ ， $N 0 { = } 1 6$ 。 

# 卷积相关特殊格式

# NC1HWC0

AI处理器中，为了提高通用矩阵乘法（GEMM）运算数据块的访问效率，所有张 量数据统一采用NC1HWC0的五维数据格式。其中C0与微架构强相关，等于AI Core中矩阵计算单元的大小。 

C1=(C+C0-1)/C0。如果结果不整除，向下取整。 

NHWC/NCHW -> NC1HWC0的转换过程为：将数据在C维度进行分割，变成C1 份NHWC0/NC0HW，再将C1份NHWC0/NC0HW在内存中连续排列成 NC1HWC0，其格式转换示意图如下图所示。 

![](images/d5eb2edc90ad1945a1b10025f4ab778606065bf7be4cd45f5aa205f03bf3910b.jpg)


NHWC $- >$ NC1HWC0的转换公式如下： 

Tensor.reshape( [N, H, W, C1, C0]).transpose( [0, 3, 1, 2, 4] ) 

NCHW -> NC1HWC0的转换公式如下： 

Tensor.reshape( [N, C1, C0, H, W]).transpose( [0, 1, 3, 4, 2] ) 

# FRACTAL_Z

FRACTAL_Z是用于定义卷积权重的数据格式，由FT Matrix（FT：Filter，卷积 核）变换得到。FRACTAL_Z是送往Cube的最终数据格式，采用 “C1HW,N1,N0,C0”的4维数据排布。 

数据有两层Tiling，如下图所示： 

![](images/8a5c1016c66737dbacdb32a92129f92b466fa57bd50394c84ed474394ba1eca8.jpg)


第一层与Cube的Size相关，数据按照列的方向连续（小n）；第二层与矩阵的Size 相关，数据按照行的方向连续（大Z）。 

例如： ${ \mathsf { H W C N } } = ( 2 , 2 , 3 2 , 3 2 )$ $=$ ，将其变成FRACTAL_Z(C1HW, N1, N0, C0) = (8, 2, 16, 16)。 

HWCN变换FRACTAL_Z的过程为： 

Tensor.padding([ [0,0], [0,0], [0,(C0-C%C0)%C0], [0,(N0-N%N0)%N0] ]).reshape( [H, W, C1, C0, N1, N0]).transpose( [2, 0, 1, 4, 5, 3] ).reshape( [C1*H*W, N1, N0, C0]) 

NCHW变换FRACTAL_Z的过程为： 

Tensor.padding([ [0,(N0-N%N0)%N0], [0,(C0-C%C0)%C0], [0,0], [0,0] ]).reshape( [N1, N0, C1, C0, H, W,]).transpose( [2, 4, 5, 0, 1, 3] ).reshape( [C1*H*W, N1, N0, C0]) 

# ● NDC1HWC0

为了提高矩阵乘法运算数据块的访问效率，将NDHWC转换为NDC1HWC0格式。 其中C0与微架构强相关，等于AI Core中矩阵计算单元的大小，对于float16_t类型 为16，对于int8_t类型则为32，这部分数据需要连续存储。 

C1=(C+C0-1)/C0。如果结果不整除，向下取整。 

NDHWC -> NDC1HWC0的转换过程为：将数据在C维度进行分割，变成C1份 NDHWC0，再将C1份NDHWC0在内存中连续排列成NDC1HWC0，其格式转换示 意图如下图所示。 

![](images/6bc463c55f2d461d90f9fa359b9dd2871e6be59b483ec09e1945934a23390796.jpg)


# FRACTAL_Z_3D

FRACTAL_Z_3D是3D卷积权重格式，例如Conv3D算子都会涉及到用这种格式来表 达3D卷积的权重。 

NDHWC $- >$ FRACTAL_Z_3D的变换过程通过公式表达如下： 

(…, N, D, H, W, C)->pad- $\cdot >$ (…, N1 * N0, D, H, W, C1 * C0)->reshape->(…, N1, N0, D, H, W, C1, C0)- >transpose->(D, C1, H, W, N1, N0, C0)->reshape->(…, D * C1 * H * W, N1, N0, C0) 

对于不同的数据类型，C0和N0的大小不同： 

位宽为4的数据类型： $\complement 0 { = } 6 4$ ， $N 0 { = } 1 6$ ； 

位宽为8的数据类型： $C 0 = 3 2$ ， $N 0 { = } 1 6$ ； 

位宽为16的数据类型： ${ \mathsf { C } } 0 { = } 1 6$ ， $N 0 { = } 1 6$ ； 

位宽为32的数据类型： $\complement 0 { = } 8$ ， $N 0 { = } 1 6$ 。 

输入一个NDHWC格式的Tensor，Shape大小为(48, 2, 2, 2, 32)： 

![](images/b01fd54da520300e80f496e7b2dc4f3832967d3a0eda71282dcf6b34b577c2d2.jpg)



转换后，得到FRACTAL_Z_3D格式如下所示：


![](images/5e5e71463021ca981b7ab0821f9adea300014fbb33d3a44e4e6fa3408a575933.jpg)


# Matmul 高阶 API 相关格式

BSH/SBH：B：Batch，批处理的大小； S：sequence length，序列长度；H = N * D，其中，N为head的数量，D为head的大小，此格式通常用于Matmul矩阵 乘。数据排布格式如下图所示： 

$$
\mathrm {B S H} (\mathrm {B} = 2, \mathrm {S} = 2, \mathrm {H} = 1 2)
$$

<table><tr><td colspan="2"></td><td colspan="12">H</td></tr><tr><td rowspan="4">B</td><td rowspan="2">S</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>8</td><td>9</td><td>10</td><td>11</td><td>12</td></tr><tr><td>13</td><td>14</td><td>15</td><td>16</td><td>17</td><td>18</td><td>19</td><td>20</td><td>21</td><td>22</td><td>23</td><td>24</td></tr><tr><td rowspan="2">S</td><td>25</td><td>26</td><td>27</td><td>28</td><td>29</td><td>30</td><td>31</td><td>32</td><td>33</td><td>34</td><td>35</td><td>36</td></tr><tr><td>37</td><td>38</td><td>39</td><td>40</td><td>41</td><td>42</td><td>43</td><td>44</td><td>45</td><td>46</td><td>47</td><td>48</td></tr></table>

$$
\mathrm {S B H} (S = 2, B = 2, H = 1 2)
$$

<table><tr><td></td><td colspan="21">B</td><td></td><td></td><td></td></tr><tr><td></td><td colspan="12">H</td><td colspan="9">H</td><td></td><td></td><td></td></tr><tr><td rowspan="2">S</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>8</td><td>9</td><td>10</td><td>11</td><td>12</td><td>13</td><td>14</td><td>15</td><td>16</td><td>17</td><td>18</td><td>19</td><td>20</td><td>21</td><td>22</td><td>23</td><td>24</td></tr><tr><td>25</td><td>26</td><td>27</td><td>28</td><td>29</td><td>30</td><td>31</td><td>32</td><td>33</td><td>34</td><td>35</td><td>36</td><td>37</td><td>38</td><td>39</td><td>40</td><td>41</td><td>42</td><td>43</td><td>44</td><td>45</td><td>46</td><td>47</td><td>48</td></tr></table>

BMNK：通用数据格式；B：Batch，批处理的大小；M、N、K为矩阵乘[M, K]*[K, N]的矩阵维度；其数据排布格式如下： 

$$
B M N K (B = 2, M = 3, N = 4, K = 4)
$$

![](images/68af38d2fca4dd7ebc0af80145331be43410cb5d5782c7abdc565a475604e197.jpg)



矩阵A


![](images/b071e0d44fc4f09f9c2821c0b7539ce5a287928f111911fb11dd4904d6cdfe70.jpg)



矩阵B


BSNGD：为原始BSH shape做reshape后的shape，S和D为单Batch的矩阵乘的M 轴（或N轴）和K轴，一个SD为一个batch的计算数据，此格式通常用于Matmul 矩阵乘，数据排布格式如下图所示： 


$\mathsf { S } = 3$ $N = 3$


<table><tr><td></td><td></td><td colspan="11">N</td></tr><tr><td></td><td></td><td colspan="3">G</td><td colspan="4">G</td><td colspan="4">G</td></tr><tr><td></td><td></td><td>D</td><td colspan="2">D</td><td>D</td><td colspan="2">D</td><td colspan="2">D</td><td colspan="3">D</td></tr><tr><td rowspan="6">B</td><td rowspan="3">S</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>8</td><td>9</td><td>10</td><td>11</td></tr><tr><td>13</td><td>14</td><td>15</td><td>16</td><td>17</td><td>18</td><td>19</td><td>20</td><td>21</td><td>22</td><td>23</td></tr><tr><td>25</td><td>26</td><td>27</td><td>28</td><td>29</td><td>30</td><td>31</td><td>32</td><td>33</td><td>34</td><td>35</td></tr><tr><td rowspan="3">S</td><td>37</td><td>38</td><td>39</td><td>40</td><td>41</td><td>42</td><td>43</td><td>44</td><td>45</td><td>46</td><td>47</td></tr><tr><td>49</td><td>50</td><td>51</td><td>52</td><td>53</td><td>54</td><td>55</td><td>56</td><td>57</td><td>58</td><td>59</td></tr><tr><td>61</td><td>62</td><td>63</td><td>64</td><td>65</td><td>66</td><td>67</td><td>68</td><td>69</td><td>70</td><td>71</td></tr></table>

SBNGD：为原始SBH shape做reshape后的shape，S和D为单Batch的矩阵乘的M 轴（或N轴）和K轴，一个SD为一个Batch的计算数据，此格式通常用于Matmul 矩阵乘，数据排布格式如下图所示： 


$5 8 N G 0 \ ( \textsf { S } = 3 \ , \textsf { B } = 2 \ , \textsf { N } = 3 \ , \textsf { G } = 2 \ , \textsf { D } = 2 \ )$


<table><tr><td></td><td colspan="21">B</td><td></td><td></td><td></td></tr><tr><td></td><td colspan="11">N</td><td colspan="10">N</td><td></td><td></td><td></td></tr><tr><td></td><td colspan="3">G</td><td colspan="4">G</td><td colspan="4">G</td><td colspan="4">G</td><td colspan="4">G</td><td colspan="2">G</td><td></td><td></td><td></td></tr><tr><td></td><td>D</td><td colspan="2">D</td><td colspan="2">D</td><td colspan="2">D</td><td colspan="2">D</td><td colspan="2">D</td><td colspan="2">D</td><td colspan="2">D</td><td colspan="2">D</td><td colspan="2">D</td><td colspan="2">D</td><td></td><td></td><td></td></tr><tr><td rowspan="3">S</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>8</td><td>9</td><td>10</td><td>11</td><td>12</td><td>13</td><td>14</td><td>15</td><td>16</td><td>17</td><td>18</td><td>19</td><td>20</td><td>21</td><td>22</td><td>23</td><td>24</td></tr><tr><td>25</td><td>26</td><td>27</td><td>28</td><td>29</td><td>30</td><td>31</td><td>32</td><td>33</td><td>34</td><td>35</td><td>36</td><td>37</td><td>38</td><td>39</td><td>40</td><td>41</td><td>42</td><td>43</td><td>44</td><td>45</td><td>46</td><td>47</td><td>48</td></tr><tr><td>49</td><td>50</td><td>51</td><td>52</td><td>53</td><td>54</td><td>55</td><td>56</td><td>57</td><td>58</td><td>59</td><td>60</td><td>61</td><td>62</td><td>63</td><td>64</td><td>65</td><td>66</td><td>67</td><td>68</td><td>69</td><td>70</td><td>71</td><td>72</td></tr></table>

BNGS1S2：一般为前两种数据排布进行矩阵乘的输出，S1S2数据连续存放，一个 S1S2为一个Batch的计算数据，此格式通常用于Matmul矩阵乘，数据排布格式如 下图所示： 

<table><tr><td></td><td colspan="16">B</td><td></td></tr><tr><td></td><td colspan="8">N</td><td colspan="8">N</td><td></td></tr><tr><td></td><td colspan="2">G</td><td colspan="3">G</td><td colspan="3">G</td><td colspan="3">G</td><td colspan="3">G</td><td colspan="2">G</td><td></td></tr><tr><td></td><td>S2</td><td>S2</td><td>S2</td><td>S2</td><td>S2</td><td>S2</td><td>S2</td><td>S2</td><td>S2</td><td>S2</td><td>S2</td><td>S2</td><td>S2</td><td>S2</td><td>S2</td><td>S2</td><td></td></tr><tr><td>S1</td><td>1 2 3 4 5 6</td><td>7 8 9 10 11 12</td><td>13 14 15 16 17 18</td><td>19 20 21 22 23 24</td><td>25 26 27 28 29 30</td><td>31 32 33 34 35 36</td><td>37 38 39 40 41 42</td><td>43 44 45 46 47 48</td><td>49 50 51 52 53 54</td><td>55 56 57 58 59 60</td><td colspan="7">61 62 63 64 69 70 71 72</td></tr></table>

ND_ALIGN：ND_ALIGN是ND数据格式的一种变换数据格式。输出矩阵乘的结果 矩阵C时，用于配置C矩阵按照N方向32字节对齐的规则进行输出。 

ND->ND_ALIGN变换过程如下图所示，假设矩阵乘结果矩阵C的数据类型是 int32_t，输出到VECOUT，原矩阵N方向没有32字节对齐，设置ND_ALIGN后则在 其后补0，将其对齐到32字节。 

![](images/049bc7be5899636466b965971c24a0cddf276ef7604873ab3d264f62305f165b.jpg)


VECTOR：VECTOR是GEMV（矩阵向量乘，General Matrix-Vector Multiply）场 景使用的一种数据格式，配置矩阵为VECTOR数据排布格式即代表输入数据是一个 向量。 


图 2-42 GEMV 场景输入 Vector 格式的 A 矩阵示意图


![](images/982374f4123b9fb013f807357b455b1acb1111fcc2c304d5483d3f423996fb15.jpg)



A矩阵


# COLUMN_MAJOR

ND数据排布格式也称为ROW_MAJOR（行优先），相应的有COLUMN_MAJOR（列优 先）。这两种数据排布格式的区别是数组或矩阵中哪个方向上的连续元素在内存连 续。 

ROW_MAJOR：行方向的连续元素在内存上连续。 

COLUMN_MAJOR：列方向的连续元素在内存上连续。 

两种数据排布格式的示意图如下所示。 


ND (ROW_MAJOR)


![](images/b7f763729bb64e8c849cbdda4e54d6a5d54b49f672ed76ec8274cb9f095f20d2.jpg)



COLUMN_MAJOR


![](images/2a63b9cb4028eee3fbe6d1c8917657f37c87519fc49f3776760102bbff917825.jpg)


# 2.9.3 编程模型设计原理

Ascend C编程模型中，并行编程范式核心要素是：一组并行计算任务、通过队列实现 任务之间的同步、开发者自主表达对并行计算任务和资源的调度。本节介绍编程模型 的设计原理，作为扩展阅读，便于开发者更好的理解编程模型的设计思路和优势，对 于后续的深度开发也会有所帮助。 

每个并行任务Stage的编程范式如下： 

1. 获取Local Memory的内存：调用AllocTensor申请内存，或者从上游队列DeQue 一块内存数据。 

2. 完成计算或者数据搬运。 

3. 把上一步处理好的数据调用EnQue入队。 

4. 调用FreeTensor释放不再需要的内存。 

以最简单的矢量编程范式为例，在调用上述接口时，实际上会给各执行单元下发一些 指令，如下图所示： 


图 2-43 Vector 编程范式指令队列示例


![](images/560500ef1cdcf887e229ed9f8a5377dac121c5344e2712316504f0ba78fd55b2.jpg)


● EnQue/DeQue的具体处理流程： 

a. 标量执行单元读取算子指令序列 

b. 把这些指令发射到对应的执行单元的指令队列 

c. 各个执行单元并行执行这些指令序列 

d. EnQue/DeQue解决对内存的写后读问题 

EnQue调用会发射同步指令set，发送信号激活wait 

DeQue调用会发射同步指令wait，等待数据写入完成 

wait需要等到set指令执行完成后才能执行否则阻塞 

![](images/6c283ca780633727406f42e2c4122e9d0af8674c749943f93f23ec404c6aa7f4.jpg)


由此可以看出，EnQue/DeQue主要解决了存在数据依赖时，并行执行单元的写后 读同步控制问题。 

![](images/d75df96496849ef032d857ad73faa76208c4a8595960321aee54ffc5bc5f4884.jpg)


AllocTensor/FreeTensor的具体处理流程 

a. 标量执行单元读取算子指令序列 

b. 把这些指令发射到对应的执行单元的指令队列 

c. 各个执行单元并行执行这些指令序列 

d. AllocTensor/FreeTensor，解决对内存的读后写问题 

AllocTensor调用会发射同步指令wait等待内存被读完成 

FreeTensor调用会发射同步指令set，通知内存释放，可以重复写 

wait需要等到set指令执行完成后才能执行否则阻塞 

![](images/780119b34ac69607c5c6775103171a81e36fd1360e024e65922e3c8d733c62ea.jpg)


由此可以看出，AllocTensor/FreeTensor主要解决了存在数据依赖时，并行执行单 元的读后写同步控制问题。 

![](images/89fb117b359cfe195f561373e9e10f90318f8b08d40a40b12051ba6ba6f72500.jpg)


通过上文的详细说明，可以看出异步并行程序需要考虑复杂的同步控制，而Ascend C 编程模型将这些流程进行了封装，通过EnQue/DeQue/AllocTensor/FreeTensor这种开 发者熟悉的资源控制方式来体现，达到简化编程和易于理解的目的。 

# 2.9.4 内存访问原理

# 2.9.4.1 Scalar 读写数据

AI Core中Scalar计算单元负责各类型的标量数据运算和程序的流程控制。根据硬件架 构设计，Scalar仅支持对Global Memory和Unified Buffer的读写操作，而不支持对L1 Buffer、L0A Buffer、L0B Buffer和L0C Buffer等其他类型存储的访问。下文分别介绍 了Scalar读写Global Memory和Unified Buffer的方式和Scalar读写数据时的同步机 制。 

# Scalar 读写 Global Memory

![](images/1491f0e7c0924594e13ee6f55240a680844d8a7ec42ea3ede5060cd479435a32.jpg)


如上图所示，Scalar读写GM数据时会经过DataCache，DataCache主要用于提高标量 访存指令的执行效率，每一个AIC/AIV核内均有一个独立的DataCache。下面通过一个 具体示例来讲解DataCache的具体工作机制。 

globalTensor1是位于GM上的Tensor： 

执行完GetValue(0)后，globalTensor1的前8个元素会进入DataCache，后续 GetValue(1)~GetValue(7)不需要再访问GM，而可以直接从DataCache的Cache Line中读取数据，提高了标量连续访问的效率。 

执行完SetValue(8, val)后，globalTensor1的index为8~15的元素会进入 DataCache，SetValue只会修改DataCache中的Cache Line数据，同时将Cache Line的状态设置为Dirty，表明Cache Line中的数据与GM中的数据不一致。 

```txt
AscendC::GlobalTensor<int64_t> globalTensor1;  
globalTensor1.SetGlobalBuffer(_gm_int64_t*)input);  
//从0~7共计8个uint64_t类型，DataCache的CacheLine长度为64字节  
//执行完GetValue(0)后，GetValue(1)~GetValue(7)可以直接从CacheLine中读取，不需要再访问GM  
globalTensor1.GetValue(0);  
globalTensor1.GetValue(1);  
globalTensor1.GetValue(2);  
globalTensor1.GetValue(3);  
globalTensor1.GetValue(4);  
globalTensor1.GetValue(5);  
globalTensor1.GetValue(6);  
globalTensor1.GetValue(7);  
//执行完SetValue(8)后，不会修改GM上的数据，只会修改DataCache中CacheLine数据  
//同时CacheLine的状态置为dirty，dirty表示DataCache中CacheLine数据与GM中的数据不一致  
int64_t val = 32;  
globalTensor1SetValue(8, val);  
globalTensor1SetValue(8); 
```

根据上文的工作机制（如下图所示），多核间访问globalTensor1会出现数据不一致的 情况，如果其余核需要获取GM数据的变化，则需要开发者手动调用 DataCacheCleanAndInvalid来保证数据的一致性。 

![](images/0ec8226c1ffb6773d45e87ec13b14fe1bba6800ecad5efa74b7026a916093852.jpg)


# Scalar 读写 Unified Buffer

Scalar读写Unified Buffer时，可以使用LocalTensor的SetValue和GetValue接口。示例 如下： 

```txt
for (int32_t i = 0; i < 16; ++i) {
    inputLocalSetValue(i, i); // 对inputLocal中第i个位置进行赋值为i
}  
for (int32_t i = 0; i < srcLen; ++i) {
    auto element = inputLocal.Values(i); // 获取inputLocal中第i个位置的数值
} 
```

# Scalar读写数据时的同步

Scalar读写Global MemoryUnified Buffer时属于PIPE_S（Scalar流水）操作，当用户 使用SetValue或者GetValue接口，且算子工程使能自动同步时，不需要手动插入同步 事件。 

如果用户关闭算子工程的自动同步功能时，则需要手动插入同步事件： 

```cpp
// GetValue为Scalar操作，与后续的Duplicate存在数据依赖  
// 因此Vector流水需要等待Scalar操作结束  
float inputVal = srcLocal.GetValue(0);  
SetFlag<HardEvent::S_V>(eventID1);  
WaitFlag<HardEvent::S_V>(eventID1);  
AscendC::Duplicate.dstLocal, inputVal, srcDataSize);  
// SetValue为Scalar操作，与后续的数据搬运操作存在数据依赖  
// 因此MTE3流水需要等待Scalar操作结束  
srcLocalSetValue(0, value);  
SetFlag<HardEvent::S_MTE3>(eventID2);  
WaitFlag<HardEvent::S_MTE3>(eventID2);  
AscendC::DataCopy.dstGlobal, srcLocal, srcDataSize); 
```

# 2.9.5 性能优化技术原理

# 2.9.5.1 DoubleBuffer

执行于AI Core上的指令队列主要包括如下几类，即Vector指令队列、Cube指令队列和 MTE指令队列。不同指令队列间的相互独立性和可并行执行性，是DoubleBuffer优化 机制的基石。 

矢量计算CopyIn、CopyOut过程使用MTE指令队列（MTE2、MTE3），Compute过程 使用Vector指令队列（V），意味着CopyIn、CopyOut过程和Compute过程是可以并行 的。 

如图2-44所示，考虑一个完整的数据搬运和计算过程，CopyIn过程将数据从Global Memory搬运到Local Memory，Vector计算单元完成计算后，经过CopyOut过程将计 算结果搬回Global Memory。 


图 2-44 数据搬运与 Vector 计算过程


![](images/e0c00909b250705859a1d052aaabff8528fab71e1f8d6bd03bc4f159a8e90836.jpg)


在此过程中，数据搬运与Vector计算串行执行，Vector计算单元无可避免存在资源闲置 问题。举例而言，若CopyIn、Compute、CopyOut三阶段分别耗时t，则Vector的时间 利用率仅为1/3，等待时间过长，Vector利用率严重不足。 

为减少Vector等待时间，DoubleBuffer机制将待处理的数据一分为二，比如Tensor1、 Tensor2。如图2-45所示，当Vector对Tensor1中数据进行Compute时，Tensor2可以执 行CopyIn的过程；而当Vector切换到计算Tensor2时，Tensor1可以执行CopyOut的过 程。由此，数据的进出搬运和Vector计算实现并行执行，Vector闲置问题得以有效缓 解。 

总体来说，DoubleBuffer是基于MTE指令队列与Vector指令队列的独立性和可并行 性，通过将数据搬运与Vector计算并行执行以隐藏数据搬运时间并降低Vector指令的等 待时间，最终提高Vector单元的利用效率，您可以通过为队列申请内存时设置内存块 的个数来实现数据并行，简单代码示例如下： 

pipe.InitBuffer(inQueueX, 2, 256); 


图 2-45 DoubleBuffer 机制


![](images/20ade90a133bd5e5a076b08c305cb3b16fc02d34b4a07fcfd5a1050408f8316c.jpg)


# 需要注意：

多数情况下，采用DoubleBuffer能有效提升Vector的时间利用率，缩减算子执行时 间。然而，DoubleBuffer机制缓解Vector闲置问题并不代表它总能带来整体的性能提 升。例如： 

当数据搬运时间较短，而Vector计算时间显著较长时，由于数据搬运在整个计算 过程中的时间占比较低，DoubleBuffer机制带来的性能收益会偏小。 

又如，当原始数据较小且Vector可一次性完成所有计算时，强行使用 DoubleBuffer会降低Vector计算资源的利用率，最终效果可能适得其反。 

因此，DoubleBuffer的性能收益需综合考虑Vector算力、数据量大小、搬运与计算时 间占比等多种因素。