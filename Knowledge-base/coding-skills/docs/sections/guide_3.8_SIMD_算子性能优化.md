<!-- Source: 算子开发指南.md lines 19476-22294 | Section: 3.8 SIMD 算子性能优化 -->

# 3.8 SIMD 算子性能优化

# 3.8.1 优化建议总览表


表 3-17 性能优化建议总览表


<table><tr><td>分类</td><td>分类描述</td><td>优化建议</td></tr><tr><td>Tiling策略</td><td>提供Tiling相关的优化建议，便于开发者选择合适的Tiling切分策略。</td><td>核间负载均衡</td></tr><tr><td rowspan="5">头尾开销优化</td><td rowspan="5">提供降低算子头尾开销（算子执行计算前后产生的时延）的优化建议。</td><td>设置合适的核数和算子Kernel类型</td></tr><tr><td>限制TilingData结构大小</td></tr><tr><td>避免TPipe在对象内创建和初始化</td></tr><tr><td>核函数内删除Workspace相关冗余操作</td></tr><tr><td>设置DCI编译选项来减少算子尾开销</td></tr><tr><td rowspan="2">流水编排</td><td rowspan="2">通过任务并行化、异步调度等方法，提升硬件资源利用率，实现更高的吞吐率。</td><td>使能DoubleBuffer</td></tr><tr><td>使能Iterate或IterateAll异步接口避免AIC/AIV同步依赖</td></tr><tr><td rowspan="10">内存访问</td><td rowspan="10">通过控制搬运的数据块大小和GM地址等来实现搬运效率的最大化；通过Buffer的共享与复用、数据压缩精简、使用专用存储空间、访存调度优化等方法来减少内存占用，提升计算效率。</td><td>尽量一次搬运较大的数据块</td></tr><tr><td>GM地址尽量512B对齐</td></tr><tr><td>高效的使用搬运API</td></tr><tr><td>避免同地址访问</td></tr><tr><td>设置合理的L2 CacheMode</td></tr><tr><td>算子与高阶API共享临时Buffer</td></tr><tr><td>纯搬运类算子VECIN和VECOUT建议复用</td></tr><tr><td>通过缩减Tensor Shapelinfo维度，优化栈空间</td></tr><tr><td>避免Unified Buffer的bank冲突</td></tr><tr><td>L2 Cache切分</td></tr><tr><td rowspan="3">矢量计算</td><td rowspan="3">矢量计算相关优化建议。</td><td>通过Unified Buffer融合实现连续vector计算</td></tr><tr><td>Vector算子灵活运用Counter模式</td></tr><tr><td>选择低延迟指令，优化归约操作性能</td></tr><tr><td rowspan="5">矩阵计算</td><td rowspan="5">矩阵计算相关优化建议。</td><td>通过BT Buffer实现高效的bias计算</td></tr><tr><td>通过FP Buffer存放量化参数实现高效随路量化</td></tr><tr><td>通过LOC Buffer数据暂存实现高效的矩阵乘结果累加</td></tr><tr><td>较小矩阵长驻L1 Buffer，仅分次搬运较大矩阵</td></tr><tr><td>Matmul使能AtomicAdd选项</td></tr></table>

# 3.8.2 Tiling 策略

# 3.8.2.1 核间负载均衡

【优先级】：中 

【描述】AI处理器的物理核数是固定的，当L2 Cache切分之后，可能发生部分核有计 算拖尾的情况，即每次所有核计算量除以每个核处理的数据量不能被核数整除，导致 最后需要部分尾核来计算尾块数据。而在尾核计算时，部分核始终处于空闲状态，从 而使得算子的整体性能变差。如图1，假设总的数据量为TotalSize，L2 Cache切分之后 分为两份TotalSize / 2，每个核每次的计算量为TotalSize / 2 / 25，即需要25个核进行 

处理，由于AI处理器的核数为20，因此每次计算时，1到5核的每个核需要多算一份数 据，导致发生拖尾的情况。 

【反例】 


图 3-88 计算拖尾示意图


![](images/0f74ae6740784dcd69f58c14666a0f3159093a94ee17964d96a956d3112224d4.jpg)


【正例】 

针对上述切分策略，调整拖尾核的位置后可以达到全局负载最优，如图2所示。完成所 有计算时，1到10核多一次数据块的计算，可以实现全局负载最优。 


图 3-89 核间负载均衡示意图


![](images/2ec63b3d9a711e5ae5fa0195cf5ff3f419e182ea39d094c1894630f0ea63655f.jpg)


# 3.8.3 头尾开销优化

# 3.8.3.1 设置合适的核数和算子 Kernel 类型

在算子执行过程中，可能会因为以下几个原因产生额外的启动开销或者头开销： 

1. 核启动：每个核在启动时需要进行初始化操作，加载必要的配置和资源。 

2. 核取址TLB MISS：当核在访问内存时，如果Translation Lookaside Buffer （TLB）中没有对应的页表项，就需要从内存中加载页表项，这会导致额外的延 迟。 

3. 同地址访问冲突：由于硬件限制，多个核同时访问相同的内存地址时可能会发生 冲突，导致额外的时延。 

4. 变量资源初始化：在算子执行前，需要初始化一些变量和资源，这也可能带来额 外的性能开销。 

头开销会随着使用的核数增加而增加。下图展示了这部分头开销随启动核数的变化情 况。 


图 3-90 头开销随启动核数的变化


![](images/9858c8ca319ccc65f60a03a58eb6b5f7a9224aa4c6a71887037fffb658be99bb.jpg)


对于整体耗时在微秒级别且单核计算量耗时较少的算子，可以通过减少启动核数并增 加单核计算量的方式来获得性能提升。这种优化方式的本质是在头开销耗时和单核计 算量耗时之间进行权衡。为了达到最佳性能，开发者需要通过实践尝试，找到最合适 的核数设置。 

对于自定义算子工程，可以在TilingFunc（算子工程提供的在Host侧计算Tiling的 默认函数）中通过SetBlockDim接口来设置算子使用的核数，具体设置方法请参考 SetBlockDim；对于Kernel直调工程，可以在<<<>>>调用时指定算子使用的核 数。 

此外，算子的Kernel类型也会影响算子启动的核数。以纯Vector算子为例，如果 以混合启动的方式执行该算子，调度器会同时启动Vector核和Cube核。然而，此 时Cube核并没有实际的计算指令，但仍会产生核启动和核初始化的头开销。因 此，建议设置合适的Kernel类型以最小化头开销。 

通常，算子工程会通过算子使用的指令自动识别算子类型，但该功能无法区分AIC 和AIV的配比，默认按照AIV:AIC为1:2的配比下发任务。此外，自动识别功能可能 失效，因为其依赖于编译优化的结果。所以推荐用户手动设置算子的Kernel类 型。具体设置方法请参考设置Kernel类型。 

# 3.8.3.2 限制 TilingData 结构大小

【优先级】中 

【描述】TilingData结构是Tiling切分信息的载体，当Host侧按照Tiling切分策略计算 完Tiling后，算子会以入参的方式将Tiling切分信息从Host侧传递到Device侧，此时 Tiling信息存放在GM上。调用GET_TILING_DATA宏后，会将Tiling信息从GM拷贝到AI 处理器的栈空间上，期间会有拷贝开销，由于GM访问效率较低，同时考虑到栈空间限 制，需要限制TilingData结构大小。拷贝耗时为us级别，在小shape的场景下，进行此 类优化收益会更加明显。 

限制TilingData结构大小，可以从以下方面考虑： 

减少不必要的TilingData结构变量； 

根据Tiling的数据范围选择合适的变量类型； 

合理排布TilingData结构； 

TilingData整体结构要求8字节补齐。 

# 【反例】

如下的示例中存在TilingData结构变量冗余的情况：NumBlocks信息已经通过 SetBlockDim接口进行设置，可以在Kernel侧调用GetBlockNum接口获取，无需 通过TilingData结构传递。 

此外，变量的数据类型也不合理：formerNum和tailNum分别为计算整块数据的 核数和计算尾块数据的核数，不会超过NUM_BLOCKS的值，使用uint8_t类型即 可；formerLength等变量根据其计算逻辑，不会超出uint32_t的范围，使用 uint32_t类型即可。 

```c
// Tiling结构体定义  
BEGIN_TILING_DATADEF(TilingDataUnalign)  
TILING_DATA_FIELD_def(xint64_t, numBlocks);  
TILING_DATA_FIELD_def(xint64_t, formerNum);  
TILING_DATA_FIELD_def(xint64_t, tailNum);  
TILING_DATA_FIELD_def(xint64_t, formerLength);  
TILING_DATA_FIELD_def(xint64_t, tailLength);  
TILING_DATA_FIELD_def(xint64_t, alignNum);  
END_TILING_DATADEF;  
// Host侧Tiling函数计算Tiling结构信息  
constexpr uint32_t NUM_BLOCKS = 8;  
constexpr uint32_t SIZE_OF_HALF = 2;  
constexpr uint32_t BLOCK_SIZE = 32;  
constexpr uint32_t ALIGN_NUM = BLOCK_SIZE / SIZE_OF_HALF;  
static ge::graphStatus TilingFunc(gert::TilingContext *context)  
{  
    TilingDataUnalign tiling;  
    uint32_t totalLength = context->GetInputTensor(0) -> GetShapeSize();  
    // NumBlocks信息已经通过SetBlockDim接口进行设置  
    context->SetBlockDim(NUM_BLOCKS);  
    uint32_t totalLengthAligned = ((totalLength + ALIGN_NUM - 1) / ALIGN_NUM) * ALIGN_NUM;  
    // formerNum、tailNum保证不超过0-NUM_BLOCKS数据范围  
    uint32_t formerNum = (totalLengthAligned / ALIGN_NUM) % NUM_BLOCKS;  
    uint32_t tailNum = NUM_BLOCKS - formerNum;  
    // formerLength等变量根据其计算逻辑，不会超出uint32_t的范围  
    uint32_tformerLength = ((totalLengthAligned / NUM_BLOCKS + ALIGN_NUM - 1) / ALIGN_NUM) * ALIGN_NUM;  
    uint32_t tailLength = (totalLengthAligned / NUM_BLOCKS / ALIGN_NUM) * ALIGN_NUM;  
} 
```

# 【正例】

Tiling变量无冗余，变量数据类型最小化。 

```c
BEGIN_TILING_DATADEF(TilingDataUnalign)  
TILING_DATA_FIELDDEF uint8_t, formerNum);  
TILING_DATA_FIELDDEF uint8_t, tailNum);  
TILING_DATA_FIELDDEF uint32_t, formerLength); 
```

```c
TILING_DATA_FIELD_REF uint32_t, tailLength); TILING_DATA_FIELD_REF uint32_t, alignNum); END_TILING_DATA_REF; 
```

# 【反例】

如下的示例中TilingData结构不合理：由于AI处理器访存需要8字节对齐，在用户定义 TilingData结构后，Ascend C工程框架会按照8字节对齐的方式对字节进行补齐，并保 证整体TilingData结构满足8字节对齐要求。如下TilingData结构formerNum和 tailNum变量都会补充3个字节，整体TilingData结构会因为8字节对齐再补充4个字 节，该TilingData结构共计补充10个字节。 

```c
BEGIN_TILING_DATADEF(TilingDataUnalign)  
TILING_DATA_FIELDDEF uint8_t, formerNum); //需补充3个字节，使得formerLength变量访问无误  
TILING_DATA_FIELDDEF uint32_t, formerLength);  
TILING_DATA_FIELDDEF uint8_t, tailNum); //需补充3个字节，使得tailLength变量访问无误  
TILING_DATA_FIELDDEF uint32_t, tailLength);  
TILING_DATA_FIELDDEF uint32_t, alignNum); //需补充4个字节，使得下个TilingData结构访问无误  
END_TILING_DATADEF; 
```

# 【正例】

如下的示例中，对Tiling参数的排布进行了调整，字节排布合理，只需要补充2个字 节，达到了减小TilingData结构的目的。 

```c
BEGIN_TILING_DATADEF(TilingDataUnalign)  
TILING_DATA_FIELD_def uint8_t, formerNum);  
TILING_DATA_FIELD_def uint8_t, tailNum); //需补充2个字节，使得formerLength变量访问无误  
TILING_DATA_FIELD_def uint32_t, formerLength);  
TILING_DATA_FIELD_def uint32_t, tailLength);  
TILING_DATA_FIELD_def uint32_t, alignNum);  
END_TILING_DATADEF; 
```

# 3.8.3.3 避免 TPipe 在对象内创建和初始化

# 【优先级】中

【编译器背景知识】创建类对象时，会分配内存空间，用于存储类中的相关成员变量 或函数。当类中变量需要参与计算时，变量值从内存被加载到寄存器，计算完成后， 变量从寄存器存储回内存。Scalar常量折叠和常量传播是编译器编译时的优化方式，优 化前编译器会判断变量是否只初始化过一次或只赋值过一次，若满足此编译优化的前 提条件，变量值将会尽量驻留在寄存器中，从而在后续使用变量时，将减少读取内存 的操作，提升运行性能。 

【描述】TPipe是用来管理全局内存和同步的框架，用户可以调用TPipe的接口，为 TQue/TBuf进行内存分配。在编写Ascend C算子过程中，经常用一个类存放计算所需 的相关变量，这里称类名为KernelExample。当TPipe对象在KernelExample类的实现 中定义并初始化时，TPipe对象的内存空间在整个KernelExample对象的内存空间之 中；需要注意的是，创建TPipe对象时，对象初始化会设置全局变量的TPipe指针，这 导致KernelExample对象的内存有被外部污染的风险，此时编译器的编译优化将采取保 守策略，不会对KernelExample对象中的Scalar变量进行常量折叠和常量传播。因此， 在任何场景下，我们都建议将TPipe对象创建于KernelExample类外部，使得TPipe对象 的内存空间独立于KernelExample类对象的内存空间，触发编译器对KernelExample类 内Scalar的编译优化，减少算子Scalar指令耗时。 

# 【反例】

代码中TPipe对象由KernelExample类内部创建并初始化，影响编译器Scalar折叠优 化，在NPU侧导致Scalar不必要的增加。 

```txt
template<typename ComputeT> class KernelExample{ public: 
```

```lisp
__aicore__ inline KernelExample() {}  
__aicore__ inline void Init(..)  
{  
    ...  
    pipe.InitialBuffer(xxxBuf, BUFFER_NUM, xxxSize);  
}  
private:  
...  
TPipe pipe;  
};  
extern "C" __global__ __aicore__ void example_kernel(..) {  
    ...  
    KernelExample<float> op;  
    op.Initial();  
} 
```

# 【正例】

改为由Kernel入口函数创建TPipe对象，在KernelExample类中保存TPipe指针使用。 

```cpp
template <typename ComputeT> class KernelExample {
public:
    __aicore__ inline KernelExample() {}
    __aicore__ inline void Init(..., TPipe* pipeline)
    {
        ...
        pipe = pipeline;
        pipe->InitBuffer(xxxBuf, BUFFER_NUM, xxxSize);
        ...
    }
} private:
    ...
    TPipe* pipe;
} external "C" __global__ __aicore__ void example_kernel(...)
} 
```

# 【性能对比】


图 3-91 aiv_scalar_time 优化前后对比


![](images/0be52045de771613b6acfca41e87c75e8a4830f7d19b3bdbb2c0f1624436685c.jpg)



图 3-92 aiv_scalar_ratio 优化前后对比


![](images/ab67f98d2af8e7bcf3ea347bf0ea4cc69037a94ad5f1df14ac0f621be311e5aa.jpg)


通过性能数据对比可以看出，Scalar优化效果显著，平均时间从281us减少到236us， 下降17%；平均scalar_time时延占比从21%下降到17%。因此在Scalar bound（达到 上限）的场景下可以使用此优化措施。 

# 3.8.3.4 核函数内删除 Workspace 相关冗余操作

【优先级】中 

【描述】在Ascend C算子工程中，编写核函数时传入的参数workspace已经直接赋值 为用户Workspace，因此无需再通过SetSysWorkspace和GetUserWorkspace来设置和 获取Workspace。减少这些冗余判断后，编译器可以在不使用该参数的情况下进一步 优化未用到的workspace变量。 

【反例】 

fast_gelu函数的参数workspace等价于用户workspace，且不为空，仍然对workspace 进行判空，并且设置SetSysWorkspace和GetUserWorkspace来获取用户Workspace。 

```cpp
template <uint64_t schMode, uint64_t dType>
global __aicore__void fast_gelu(GM_ADDR x, GM_ADDR y, GM_ADDR workspace, GM_ADDR tiling)
{
    //反例，冗余判断
if (workspace == nullptr) {
    return;
}
SetSysWorkspace workspace);
GM_ADDR userWS = GetUserWorkspace workspace);
if (userWS == nullptr) {
    return;
}
REGISTER_TILING_DEFAULT(EleBaseTilingDataV2);
GET_TILING_DATA_WITHSTRUCT(EleBaseTilingDataV2, tilingData, tiling);
KERNEL_TASK_TYPE_DEFAULT(Kernel_TYPE_AIV_ONLY);
TPipe pipe;
if constexpr (dTType == static_cast<TPLFPS16>) {
ElementwiseSch<schMode, FastGeluDag::FastGeluNeedCast<half>::OpDag> sch(&tilingData, &pipe);
sch Init(x, y);
sch.Process();
} else if constexpr (dTType == static_cast<TPL_BF16>) {
ElementwiseSch<schMode, FastGeluDag::FastGeluNeedCast<flat float16_t>::OpDag> sch(&tilingData, &pipe);
sch Init(x, y);
sch.Process();
} else if constexpr (dTType == static_cast<TPLFPS32>) {
ElementwiseSch<schMode, FastGeluDag::FastGeluNoCast<float>::OpDag> sch(&tilingData, &pipe);
sch Init(x, y);
sch.Process();
} 
```

# 【正例】

fast_gelu函数中删除对workspace参数进行空指针判断，也无需设置SetSysWorkspace 和通过GetUserWorkspace来获取Workspace。 

```cpp
template <uint64_t schMode, uint64_t dType>
global __aicore__void fast_gelu(GM_ADDR x, GM_ADDR y, GM_ADDR workspace, GM_ADDR tiling)
{
    REGISTER_TILING_DEFAULT(EleBaseTilingDataV2);
    GET_TILING_DATA_WITHSTRUCT(EleBaseTilingDataV2, tilingData, tiling);
    KERNEL_TASK_TYPE_DEFAULT(Kernel_TYPE_AIV_ONLY);
    TPipe pipe;
    if constexpr (dType == static_cast<uint64_t>(TPL_FP16)) {
        ElementwiseSch<schMode, FastGeluDag::FastGeluNeedCast<half>::OpDag> sch(&tilingData, &pipe);
        schInit(x, y);
        sch.Process();
    } else if constexpr (dType == static_cast<uint64_t>(TPL_BF16)) {
        ElementwiseSch<schMode, FastGeluDag::FastGeluNeedCast<float16_t>::OpDag> sch(&tilingData, &pipe);
        schInit(x, y);
        sch.Process();
    } else if constexpr (dType == static_cast<uint64_t>(TPL_FP32)) {
        ElementwiseSch<schMode, FastGeluDag::FastGeluNoCast<float>::OpDag> sch(&tilingData, &pipe);
        schInit(x, y);
        sch.Process();
} 
```

# 3.8.3.5 设置 DCI 编译选项来减少算子尾开销

# 说明

该性能优化建议适用于如下型号： 

● Atlas 350 加速卡 

【优先级】高 

【描述】算子执行结束时，需要将DCache置为无效，防止后续算子继续使用DCache 中的数据而受到影响。可以通过在编译选项中添加--cce-no-dcache-flush=true，用于 在算子尾部增加DCI（DataCacheInvalid）指令来使DCache失效。如果不开启该选 项，则会默认增加DCCI（DataCacheCleanAndInvalid）指令来使DCache失效。 

插入DCI指令相比于插入DCCI指令，其减少了数据从DCache同步到GM（Clean）的过 程，性能上会有一定优势。插入DCCI是一种额外的容错保证，如果开发者使用了* gm__的方式改写GM内存，或者调用GlobalTensor.SetValue函数时，没有正确的调 用DataCacheCleanAndInvalid接口来保证Cache一致性，编译框架自动插入DCCI恰好 可以保证算子精度正常。 

所以在如下场景，可以通过开启该编译选项来降低算子尾部开销： 

算子使用* __gm__的方式改写GM内存，或者调用GlobalTensor.SetValue函数时， 正确的使用DataCacheCleanAndInvalid接口，手动将数据从DCache中回刷到GM 上，保证Cache的一致性。不依赖编译框架自动插入DCCI指令来保证一致性。 

算子不包含使用* __gm__的方式改写GM内存，或者调用GlobalTensor.SetValue函 数的代码。 

# 3.8.4 流水编排

# 3.8.4.1 使能 DoubleBuffer

【优先级】中 

【描述】执行于AI Core上的指令队列主要包括如下几类，Vector指令队列（V）、 Cube指令队列（M）、Scalar指令队列（S）和搬运指令队列（MTE1/MTE2/ MTE3）。不同指令队列间的相互独立性和可并行执行特性，是DoubleBuffer优化机制 的基石。 

以纯Vector计算为例，矢量计算前后的CopyIn、CopyOut过程使用搬运指令队列 （MTE2/MTE3），Compute过程使用Vector指令队列（V），不同指令队列可并行执 行，意味着CopyIn、CopyOut过程和Compute过程是可以并行的。如图3-93所示，考 虑一个完整的数据搬运和计算过程，CopyIn过程将数据从Global Memory搬运到Local Memory，Vector计算单元完成Compute计算后，经过CopyOut过程将计算结果搬回 Global Memory。 


图 3-93 数据搬运与 Vector 计算过程


![](images/e4024589c2c7267203fed71f139656203bc77ace38f707e4ed2f00ca9c4528dd.jpg)



图 3-94 未使能 DoubleBuffer 的流水图


![](images/311df278d41dce421715e956a531c22148426442b1f0d9595ab3faa87b80f83b.jpg)


在此过程中，数据搬运与Vector计算串行执行，Vector计算单元不可避免存在资源闲置 问题，假设CopyIn、Compute、CopyOut三阶段分别耗时相同均为t，则Vector的利用 率仅为1/3，等待时间过长，Vector利用率严重不足。 

为减少Vector等待时间，使能DoubleBuffer机制将待处理的数据一分为二，例如 Tensor1、Tensor2。如图3-95所示，当Vector单元对Tensor1中数据进行Compute计算 时，Tensor2数据流可以执行CopyIn的过程；而当Vector切换到计算Tensor2时， Tensor1数据流可以执行CopyOut的过程。由此，数据的进出搬运和Vector计算实现并 行执行，Vector闲置问题得以有效缓解。 

总体来说，DoubleBuffer是基于MTE指令队列与Vector指令队列的独立性和可并行 性，通过将数据搬运与Vector计算并行执行以隐藏大部分的数据搬运时间，并降低 Vector指令的等待时间，最终提高Vector单元的利用效率。通过为队列申请内存时设置 内存块的个数为2，使能DoubleBuffer，实现数据并行，简单代码示例如下： 

pipe.InitBuffer(inQueueX, 2, 256); 


图 3-95 DoubleBuffer 机制


![](images/c09e6c8336ffdef419f540264b2c9cf6cbb204060a6147b43cbe1e790e0b4cc9.jpg)



图 3-96 使能 DoubleBuffer 的流水图


![](images/a64c50538a0b6fd860ea0ac27c810be3b9c1c282f894ecc2f78740619a38386d.jpg)


# 需要注意：

多数情况下，采用DoubleBuffer能有效提升Vector的利用率，缩减算子执行时间。然 而，DoubleBuffer机制缓解Vector闲置问题，并不代表它总能带来明显的整体性能提 升。例如： 

当数据搬运时间较短，而Vector计算时间较长时，由于数据搬运在整个计算过程 中的时间占比较低，DoubleBuffer机制带来的性能收益会偏小。 

当原始数据较小且Vector可一次性完成所有数据量的计算时，强行使用 DoubleBuffer会降低Vector计算资源的利用率，最终效果可能适得其反。 

因此，DoubleBuffer的使用需综合考虑Vector算力、数据量大小、搬运与计算时间占 比等多种因素。 

# 【反例】

```c
aicore__inline void Init(_gm__uint8_t* src0Gm, _gm__uint8_t* src1Gm, _gm__uint8_t* dstGm)  
{src0Global.SetGlobalBuffer(_gm__half*)src0Gm);src1Global.SetGlobalBuffer(_gm__half*)src1Gm);dstGlobal.SetGlobalBuffer(_gm__half*)dstGm);//不使能DoubleBuffer，占用的物理空间是1\*sizeSrc0\*sizeof(half) //3个InitBuffer执行后总空间为1\* (sizeSrc0\*sizeof(half) + sizeSrc1\*sizeof(half) + sizeDst0\* sizeof(half))pipe.InitialBuffer(inQueueSrc0, 1, sizeSrc0\*sizeof(half));pipe.InitialBuffer(inQueueSrc1, 1, sizeSrc1\*sizeof(half));pipe.InitialBuffer(outQueueDst, 1, sizeDst0\*sizeof(half));}aicore__inline void Process()  
{//需要round\*2次循环才能处理完数据for (uint32_t index = 0; index < round \*2; ++index){Copyln(index);Compute();CopyOut(index);} 
```

# 【正例】

aicore__inline void Init(_gm__uint8_t* src0Gm, _gm__uint8_t* src1Gm, _gm__uint8_t* dstGm)  
{src0Global.SetGlobalBuffer(_gm__half*)src0Gm);src1Global.SetGlobalBuffer(_gm__half*)src1Gm);dstGlobal.SetGlobalBuffer(_gm__half*)dstGm);//InitBuffer中使用2表示使能DoubleBuffer，占用的物理空间是2\*sizeSrc0\*sizeof(half) //3个InitBuffer执行后总空间为2\* (sizeSrc0\*sizeof(half) + sizeSrc1\*sizeof(half) + sizeDst0\* sizeof(half))pipe.InitBuffer(inQueueSrc0, 2, sizeSrc0\*sizeof(half));pipe.InitBuffer(inQueueSrc1, 2, sizeSrc1\*sizeof(half));pipe.InitBuffer(outQueueDst, 2, sizeDst0\*sizeof(half));}aicore__inline void Process()  
{//开启DoubleBuffer的前提是循环次数 $\geqslant$ 2for (uint32_t index $= 0$ ;index $<$ round; ++index){Copyln(index);Compute();CopyOut(index);} 

# 3.8.4.2 使能 Iterate 或 IterateAll 异步接口避免 AIC/AIV 同步依赖

# 【优先级】高

【描述】在MIX场景，即AIC（AI Cube核）和AIV（AI Vector核）混合编程中，调用 Matmul Iterate或者IterateAll时，AIV发送消息到AIC启动Matmul计算。若通过 Iterate<true>同步方式，如图1 同步方式消息发送示意图，每次调用都会触发一次消 息发送，而通过Iterate<false>异步方式，如图2 异步方式消息发送示意图，仅第一次 需要发送消息，后续无需发送消息，从而减少Cube与Vector核间交互，减少核间通信 开销。因此，MIX场景推荐使用Iterate<false>或者IterateAll<false>异步接口（注意： 使用异步接口时需要设置Workspace）。 


图 3-97 同步方式消息发送示意图


![](images/f7e3365b435fa206ce5fbdaa5eeb7e132165362a2444815764b38dc2763e847b.jpg)



图 3-98 异步方式消息发送示意图


![](images/99b4b87b6a708a9fa5ddebfe263421172c813c80141bd2573dcfca58dff50f72.jpg)


# 【反例】

MIX场景使用Iterate接口的同步方式。 

```cpp
TQueBind<TPosition::CO2, TPosition::VECIN> qVcIn;  
TQueBind<TPosition::VECIN, TPosition::VECOUT> qVecOut;  
mm.SetTensorA(gmA); 
```

```txt
mm.SetTensorB(gmB);  
int16_t scalar = 2;  
while(mm.template Iterate()){  
    auto cInUB = qVecIn AllocTensor(float());  
    mm.GetTensorC(cInUB);  
    qVecIn.EnQue(cInUB);  
    cInUB = qVecIn.DeQue(float());  
    auto cOutUB = qVecOut AllocTensor(float());  
    Muls(cOutUB, cInUB, scalar, baseM*baseN);  
    qVecIn.FreeTensor(cInUB);  
} 
```

# 【正例】

MIX场景使用Iterate接口的异步方式。 

```cpp
TQueBind<TPosition::CO2, TPosition::VECIN> qVecIn;  
TQueBind<TPosition::VECIN, TPosition::VECOUT> qVecOut;  
mm.SetTensorA(gmA);  
mm.SetTensorB(gmB);  
mm.setWorkspace workspace,size);//其中，workspace为临时空间的物理地址，size为singleCoreM*singleCoreN大小的矩阵C占用的内存大小：singleCoreM*singleCoreN*sizeof(float)int16_t scalar = 2;  
while(mm.template Iteratefalse(){auto clnUB = qVecIn AllocTensor(float());mm.GetTensorC(clnUB);qVecIn.EnQue(clnUB);clnUB = qVecIn.DeQue(float());auto cOutUB = qVecOut AllocTensor(float());Muls(cOutUB,clnUB,scalar,baseM\*baseN);qVecIn.FreeTensor(clnUB);…} 
```

# 3.8.5 内存访问

# 3.8.5.1 尽量一次搬运较大的数据块

# 【优先级】高

【描述】搬运不同大小的数据块时，对带宽的利用率（有效带宽/理论带宽）不一样。 根据实测经验，单次搬运数据长度16KB以上时，通常能较好地发挥出带宽的最佳性 能。因此对于单次搬运，应考虑尽可能的搬运较大的数据块。下图展示了某款AI处理 器上实测的不同搬运数据量下带宽的变化图。 

# 说明

测试数据与处理器型号相关，且实际测试时可能会存在略微抖动，具体带宽数值并不一定和下文 的测试数据严格一致。 


图 3-99 UB->GM 方向不同单次搬运数据量下实际占用带宽的变化


![](images/0c8e18d3ed69f25a82d8fbacd8877b5602d8c5a695b3f3abd7c9f5e20e27572a.jpg)



图 3-100 GM->UB 方向不同单次搬运数据量下实际占用带宽的变化


![](images/f368a8fd487c1fae1cb701e5931349a37e257dc6a14fe22f0ec1670901e62008.jpg)


# 3.8.5.2 GM 地址尽量 512B 对齐

【优先级】高 

【描述】由于AI处理器内部设计约束，从GM向Local Memory搬运数据时，保证GM地 址512B对齐可以最有效的发挥出带宽的效率。如下图示例，展示了在512B对齐以及 32B对齐情况下单核的带宽效率：搬运同等数据量，带宽差距最大的情况，32B对齐场 景只能达到512B对齐场景的70%。 

# 说明

● 本性能优化手段仅针对Atlas A2 训练系列产品/Atlas A2 推理系列产品生效。 

● 测试数据与处理器型号相关，且实际测试时可能会存在略微抖动，具体带宽数值并不一定和 下文的测试数据严格一致。 


图 3-101 GM->UB 方向 512B 对齐和 32B 对齐实测带宽的差异对比


![](images/22a550bf6b9edcb4c8fe42288341b3d7944ca579df8d4bbf86f9e7b6706640cc.jpg)



图 3-102 UB->GM 方向 512B 对齐和 32B 对齐实测带宽的差异对比


![](images/281e8f3f9c874e83bcce7f774788192e338ef6bb75d7a176992c326179ef7230.jpg)


# 3.8.5.3 高效的使用搬运 API

# 【优先级】高

【描述】在使用搬运API时，应该尽可能地通过配置搬运控制参数实现连续搬运或者固 定间隔搬运，避免使用for循环，二者效率差距极大。如下图示例，图片的每一行为 16KB，需要从每一行中搬运前2KB，针对这种场景，使用for循环遍历每行，每次仅能 搬运2KB。若直接配置DataCopyParams参数（包含srcStride/dstStride/blockLen/ blockCount），则可以达到一次搬完的效果，每次搬运32KB；参考3.8.5.1 尽量一次 搬运较大的数据块章节介绍的搬运数据量和实际带宽的关系，建议一次搬完。 


图 3-103 待搬运数据排布


![](images/fd7f74fae6f57d8c05e87178e0a2d6f7be7e0d42e7ad8d6c2f6884b868cf11ab.jpg)


# 【反例】

```txt
//搬运数据存在间隔，从GM上每行16KB中搬运2KB数据，共16行 LocalTensor<float> tensorIn; GlobalTensor<float> tensorGM; constexpr int32_t copyingWidth = 2 * 1024 / sizeof(float); constexpr int32_t imgWidth = 16 * 1024 / sizeof(float); constexpr int32_t imgHeight = 16; //使用for循环，每次只能搬运2K，重复16次 for (int i = 0; i < imgHeight; i++) { DataCopy(tensorIn[i * copyingWidth], tensorGM[i * imgWidth], copyingWidth); } 
```

# 【正例】

```txt
LocalTensor<float> tensorIn;  
GlobalTensor<float> tensorGM;  
...  
constexpr int32_t copyWidth = 2 * 1024 / sizeof(float);  
constexpr int32_t imgWidth = 16 * 1024 / sizeof(float);  
constexpr int32_t imgHeight = 16;  
// 通过DataCopy包含DataCopyParams的接口一次搬完  
DataCopyParams copyParams;  
copyParams.blockCount = imgHeight;  
copyParams.blockLen = copyWidth / 8; // 搬运的单位为DataBlock(32Byte)，每个DataBlock内有8个float  
copyParams.srcStride = (imgWidth - copyWidth) / 8; // 表示两次搬运src之间的间隔，单位为DataBlock  
copyParams.dstStride = 0; // 连续写，两次搬运之间dst的间隔为0，单位为DataBlock  
DataCopy(tensorGM, tensorIn, copyParams); 
```

# 3.8.5.4 非对齐场景减少无效数据的搬运

【优先级】中 

# 说明

该性能优化建议适用于如下型号： 

● Atlas 350 加速卡 

【描述】在非对齐数据搬运场景中，Atlas 350 加速卡在基础API层面提供了 DataCopyPad接口，该接口支持Normal、Compact（紧凑）两种搬运模式。搬运多块 

非32B对齐数据块的场景下，使用Compact模式在可以减少搬运的无效数据量，节省带 宽。 

假设需要搬运三个数据块，每块数据块大小为48B，数据类型为float类型。除了这三 个48字节的数据块之外，其他所有数据均为无效数据。 


【反例】使用DataCopyPad接口进行Normal模式搬运数据


```cpp
aicore__inline void Copyln(){ AscendC::LocalTensor<T> xLocal = inQueueX AllocTensor<T>(); AscendC::Duplicate<T>(xLocal, 0, count); AscendC::DataCopyParams dataCopyParams; dataCopyParams.blockCount = 3; dataCopyParams.blockLen = 48; dataCopyParams.srcStride = 0; dataCopyParams.dstStride = 0; AscendC::DataCopyPadParams dataCopyPadParams; dataCopyPadParams.isPad = 1; dataCopyPadParams.leftPadding = 0; dataCopyPadParams.rightPadding = 4; dataCopyPadParams.paddingValue = 0; AscendC::DataCopyPad<T, AscendC::PaddingMode::Normal>(xLocal, xGm, dataCopyParams, dataCopyPadParams); inQueueX.EnQue<T>(xLocal); } 
```

# 搬运后UB内数据如下：

```txt
[1., 1., 1., 1., 1., 1., 1., 1., 1., 0., 0., 0., 0, 1., 1., 1., 1., 1., 1., 1., 1., 0., 0., 0., 0, 1., 1., 1., 1., 1., 1., 1., 1., 0., 0., 0, 0....] 
```


图 3-104 Normal 模式搬运


![](images/a0c2ab5c4d2b8c9464532ab46cf1edf6ca56faad661f3442f9d8634b41b60535.jpg)


如图所示，由于每块数据块为48B，非32B对齐，因此搬运每块数据块时需要插入16B 大小的padding数据使得数据32B对齐，最终搬运192B大小的数据到UB，其中包含48B 的无效数据。 


【正例】改用Compact模式搬运进行优化


```cpp
__aicore__ inline void Copyln(){ AscendC::LocalTensor<T> xLocal = inQueueX AllocTensor<T>(); AscendC::Duplicate<T>(xLocal, 0, count); AscendC::DataCopyParams dataCopyParams; dataCopyParams.blockCount = 3; dataCopyParams.blockLen = 48; dataCopyParams.srcStride = 0; dataCopyParams.dstStride = 0; AscendC::DataCopyPadParams dataCopyPadParams; dataCopyPadParams.isPad = 1; dataCopyPadParams.leftPadding = 0; dataCopyPadParams.rightPadding = 4; dataCopyPadParams(paddingValue = 0; 
```

```txt
AscendC::DataCopyPad<T, AscendC::PaddingMode::Compact>(xLocal, xGm, dataCopyParams, dataCopyPadParams); inQueueX.EnQue<T>(xLocal); } 
```

搬运后UB内数据如下： 

```json
[1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 1., 0, 0, 0,...] 
```


图 3-105 Compact 模式搬运


![](images/1fbc2e06c27ec754af26e0b022e055ca9e5cc5200368076152ed2a76b0fe815a.jpg)



160B total


根据Compact模式搬运的示意图，最终搬运了160B大小的数据，其中包含16B的无效 数据。 

【总结】通过比较可以发现，搬运多块非32B对齐数据块的场景下，使用Compact模式 在可以减少搬运的无效数据量，节省带宽。 

# 3.8.5.5 非连续搬运场景减少搬运次数

【优先级】中 

# 说明

该性能优化建议适用于如下产品型号： 

● Atlas 350 加速卡 

在非连续搬运场景可以使用DataCopyPad接口的Loop模式和DataCopy的多维数据搬 运接口来减少搬运次数，优化搬运性能。 

# 使用 Loop 模式减少非连续搬运的次数

【描述】DataCopyPad接口在Normal/Compact模式基础上，可以使用Loop模式搬运 二维数据，假设我们希望以下图的方式搬运8个48B大小的数据块： 

![](images/1bddf42b9e33414fd48d3ae52f1b0c4950af39ed19bf0aa7e92f89b656f2c988.jpg)


【反例】调用多次搬运接口进行搬运（以DataCopyPad为例） 

```cpp
aicore__inline void Copyln3(){ AscendC::LocalTensor<T> xLocal = inQueueX AllocTensor<T>(); AscendC::Duplicate<T>(xLocal, 0, count); AscendC::DataCopyParams dataCopyParams; dataCopyParams.blockCount = 2; 
```

```cpp
dataCopyParams.blockLen = 48;  
dataCopyParams.srcStride = 0;  
dataCopyParams.dstStride = 0;  
AscendC::DataCopyPadParams dataCopyPadParams;  
dataCopyPadParams.isPad = 0;  
dataCopyPadParams.leftPadding = 0;  
dataCopyPadParams.rightPadding = 0;  
dataCopyPadParams(paddingValue = 0;  
AscendC::DataCopyPad<T, AscendC::PaddingMode::Compact>(xLocal, xGm, dataCopyParams, dataCopyPadParams);  
AscendC::DataCopyPad<T, AscendC::PaddingMode::Compact>(xLocal[32], xGm[24], dataCopyParams, dataCopyPadParams);  
AscendC::DataCopyPad<T, AscendC::PaddingMode::Compact>(xLocal[72], xGm[48], dataCopyParams, dataCopyPadParams);  
AscendC::DataCopyPad<T, AscendC::PaddingMode::Compact>(xLocal[104], xGm[72], dataCopyParams, dataCopyPadParams);  
inQueueX.EnQue<T>(xLocal); 
```


图 3-106 使用多次 DataCopyPad 接口进行搬运


![](images/43356c9510e698fdd68f837f611152f3934fff31cd592a4d78c879f2bef69750.jpg)


# 【正例】使用Loop模式进行搬运

aicore__inline void CopyIn3(){ AscendC::LoopModeParams loopModeParams; loopModeParamsloop1Size $= 2$ . loopModeParams. loop2Size $= 2$ .. loopModeParams. loop1SrcStride $= 96$ .. loopModeParams. loop1DstStride $= 128$ .. loopModeParams. loop2SrcStride $= 192$ .. loopModeParams. loop2DstStride $= 288$ AscendC::LocalTensor<T> xLocal $=$ inQueueX AllocTensor(); AscendC::Duplicate<T>(xLocal,0,count); AscendC::DataCopyParams dataCopyParams; dataCopyParams.blockCount $= 2$ .. dataCopyParams.blockLen $= 48$ .. dataCopyParams.srcStride $= 0$ .. dataCopyParams.dstStride $= 0$ AscendC::DataCopyPadParams dataCopyPadParams; dataCopyPadParams.isPad $= 0$ .. dataCopyPadParams.leftPadding $= 0$ .. dataCopyPadParams.rightPadding $= 0$ .. dataCopyPadParams.paddingValue $= 0$ AscendC::SetLoopModePara(loopModeParams, AscendC::DataCopyMVTType::OUT_TO UB); AscendC::DataCopyPad<T, AscendC::PaddingMode::Compact>(xLocal,xGm,dataCopyParams, dataCopyPadParams); AscendC::ResetLoopModePara(AscendC::DataCopyMVTType::OUT_TO UB); inQueueX.EnQue<T>(xLocal);   
} 


图 3-107 使用 Loop 模式进行搬运


![](images/b38b267061a25b7dc1dd613bedcb265c32d06d286b2186a169d92a5c1f13f96d.jpg)


【总结】当数据块之间需要插入不同大小Padding时，使用Loop模式搬运代替多次的 DataCopyPad能够减少搬运指令的使用，提升性能。 

# 使用多维数据搬运减少非连续搬运次数

【描述】假设我们希望以下图的方式搬运2个8B大小的数据块： 


图 3-108 搬运前后数据


![](images/e796e4666b36b30f1041d063599997ce0fa7f50ff25896c941a33a7801e3bc45.jpg)


【反例】使用多次DataCopyPad进行搬运 


图 3-109 使用多次 DataCopyPad 进行搬运


![](images/051ae85a8c5055e6fa354269724b891431720d9f280d6a11a39e18f7d9ef9fb7.jpg)


```cpp
aicore__inline void CopyIn5(){ AscendC::LocalTensor<T> xLocal = inQueueX AllocTensor<T>(); AscendC::Duplicate<T>(xLocal, 0, count); AscendC::DataCopyParams dataCopyParams; dataCopyParams.blockCount = 1; dataCopyParams.blockLen = 8; dataCopyParams.srcStride = 0; dataCopyParams.dstStride = 0; AscendC::DataCopyPadParams dataCopyPadParams; dataCopyPadParams.isPad = 1; dataCopyPadParams.leftPadding = 5; dataCopyPadParams.rightPadding = 1; dataCopyPadParams(paddingValue = 0; 
```

```cpp
//第一次搬运 AscendC::DataCopyPad<T, AscendC::PaddingMode::Normal>(xLocal, xGm, dataCopyParams, dataCopyPadParams); dataCopyPadParams.isPad = 1; dataCopyPadParams.leftPadding = 1; dataCopyPadParams.rightPadding = 5; dataCopyPadParams(paddingValue = 0; //第二次搬运 AscendC::DataCopyPad<T, AscendC::PaddingMode::Normal>(xLocal[8], xGm[2], dataCopyParams, dataCopyPadParams); inQueueX.EnQue<T>(xLocal); } 
```

# 【正例】使用多维数据搬运

DataCopy接口在Atlas 350 加速卡上支持多维数据的搬运，具体可参考多维数据搬运 （ISASI）。以2D场景的搬运为例，代码如下： 

```cpp
__aicore__ inline void Copyln6(){ AscendC::LocalTensor<T> xLocal = inQueueX AllocTensor<T>(); AscendC::Duplicate<T>(xLocal, 0, count); AscendC::NdDmaLoopInfo<2> loopInfo{1, 2}, {1, 4}, {2, 2}, {1, 1}, {1, 1}; AscendC::NdDmaParams<T, 2> params = {loopInfo, 0}; AscendC::NdDmaDci(); static constexpr AscendC::NdDmaConfig config = {false}; AscendC::DataCopy<T, 2, config>(xLocal, xGm, params); inQueueX.EnQue<T>(xLocal); } 
```


图3-110 搬运前后数据


![](images/e7eae0d53f3804429907b00a3cd5fb47624be3ed135ae721ffbd633ef1ddb580.jpg)


【总结】使用多维数据搬运在部分场景下能够减少搬运指令的条数，从而提升性能。 

# 3.8.5.6 避免同地址访问

【优先级】高 

# 说明

该性能优化指导适用于如下产品型号： 

● Atlas A3 训练系列产品/Atlas A3 推理系列产品 

● Atlas A2 训练系列产品/Atlas A2 推理系列产品 

【描述】MTE2、MTE3、Scalar等单元访问Global Memory数据时，其地址请求会按 照512字节粒度对齐后进行处理。当同时访问Global Memory的数据，且地址处于连续 的512字节范围内时，由于数据一致性的原因，多个请求会被串行处理，进而影响数据 搬运效率。 

当前算子执行机制保证用户Kernel入参（包括Workspace/Tiling）的地址512字节对 齐，因此开发者只需要根据地址的偏移量即可判断两个地址是否会落入连续的512字节 范围内。 

如下图所示，AI Core内的各个核对Global Memory的数据同时发出读写请求，尽管 addr0~addr5是多个不同的地址，但因为落在连续的512字节范围内，被视为同一个地 址请求，此时这几个数据请求会被串行处理，数据访问效率会降低。同地址访问的影 响受同时访问的核数影响，同地址访问的核数越多时，串行导致的性能劣化越严重。 

![](images/9019815df58b6c291c8e4105f9ff41ff34c7b6f25481d8926b2b65a87ad8f203.jpg)


避免同地址访问的方法主要有以下两种：调整数据访问顺序和修改切分策略。下文介 绍配套的样例请参考避免同地址访问样例。 

# 调整数据访问顺序

以一个形状为 (8192, 128) 的float类型输入进行Adds计算为例。 

为了体现同地址冲突的影响，上述场景设计中每一行的数据大小为512字节（128个 float），每个核每一轮计算处理512 * 8字节的数据，并进行全核同步（实际场景中并 不需要），每一轮计算都需要等待所有核完成当前数据块的计算后，再进行下一轮。 

<table><tr><td>实现方案</td><td>原始实现</td><td>优化实现</td></tr><tr><td>实现方法</td><td>使用16个核参与计算，按列方向进行切分，每个核总计算数据量为8192*8；单核执行循环16次，每次计算的数据量为512*8；每个核的循环顺序如下图所示，列方向0~15表示每个核的数据块执行顺序。由于多个核同时访问同一行数据（512字节），导致同地址冲突的发生。</td><td>使用16个核参与计算，按列方向进行切分，每个核总计算数据量为8192*8；单核执行循环16次，每次计算的数据量为512*8；每个核的循环顺序如下图所示，列方向0~15表示每个核的数据块执行顺序。由于每个核每一轮处理的地址在不同行，不会同时访问连续的512字节，所以不会导致同地址访问冲突。</td></tr></table>

<table><tr><td>实现方案</td><td colspan="9">原始实现</td><td colspan="12">优化实现</td><td colspan="3"></td><td></td><td></td></tr><tr><td rowspan="18">示意图</td><td></td><td>0核</td><td>1核</td><td>2核</td><td>3核</td><td>4核</td><td>5核</td><td>6核</td><td>7核</td><td>8核</td><td>9核</td><td>10核</td><td>11核</td><td>0核</td><td>1核</td><td>2核</td><td>3核</td><td>4核</td><td>5核</td><td>6核</td><td>7核</td><td>8核</td><td>9核</td><td>10核</td><td>11核</td><td></td></tr><tr><td>0x00000-0x03FFF</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td colspan="3">0x0000-0x03FFF0</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>8</td><td>9</td><td>10</td><td>11</td><td>12</td></tr><tr><td>0x04000-0x07FFF</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td colspan="3">0x04000-0x07FFF1</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>8</td><td>9</td><td>10</td><td>11</td><td>12</td><td></td></tr><tr><td>0x08000-0x0BFFF</td><td>2</td><td>2</td><td>2</td><td>2</td><td>2</td><td>2</td><td>2</td><td>2</td><td>2</td><td colspan="3">0x08000-0x0BFFF2</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>8</td><td>9</td><td>10</td><td>11</td><td>12</td><td>13</td><td></td></tr><tr><td>0x0C000-0x0FFF</td><td>3</td><td>3</td><td>3</td><td>3</td><td>3</td><td>3</td><td>3</td><td>3</td><td>3</td><td colspan="3">0x0C000-0x0FFF3</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>8</td><td>9</td><td>10</td><td>11</td><td>12</td><td>13</td><td>14</td><td></td></tr><tr><td>0x10000-0x13FFF</td><td>4</td><td>4</td><td>4</td><td>4</td><td>4</td><td>4</td><td>4</td><td>4</td><td>4</td><td colspan="3">0x10000-0x13FFF4</td><td>4</td><td>5</td><td>6</td><td>7</td><td>8</td><td>9</td><td>10</td><td>11</td><td>12</td><td>13</td><td>14</td><td>15</td><td></td></tr><tr><td>0x14000-0x17FFF</td><td>5</td><td>5</td><td>5</td><td>5</td><td>5</td><td>5</td><td>5</td><td>5</td><td>5</td><td colspan="3">5x14000-0x17FFF5</td><td>5</td><td>6</td><td>7</td><td>8</td><td>9</td><td>10</td><td>11</td><td>12</td><td>13</td><td>14</td><td>15</td><td>0</td><td></td></tr><tr><td>0x18000-0x1BFFF</td><td>6</td><td>6</td><td>6</td><td>6</td><td>6</td><td>6</td><td>6</td><td>6</td><td>6</td><td colspan="3">6x18000-0x1BFFF6</td><td>6</td><td>7</td><td>8</td><td>9</td><td>10</td><td>11</td><td>12</td><td>13</td><td>14</td><td>15</td><td>0</td><td>1</td><td></td></tr><tr><td>0x1C000-0x1FFF</td><td>7</td><td>7</td><td>7</td><td>7</td><td>7</td><td>7</td><td>7</td><td>7</td><td>7</td><td colspan="3">7x1C000-0x1FFF7</td><td>7</td><td>8</td><td>9</td><td>10</td><td>11</td><td>12</td><td>13</td><td>14</td><td>15</td><td>0</td><td>1</td><td>2</td><td></td></tr><tr><td>0x20000-0x23FFF</td><td>8</td><td>8</td><td>8</td><td>8</td><td>8</td><td>8</td><td>8</td><td>8</td><td>8</td><td colspan="3">8x20000-0x23FFF8</td><td>8</td><td>9</td><td>10</td><td>11</td><td>12</td><td>13</td><td>14</td><td>15</td><td>0</td><td>1</td><td>2</td><td>3</td><td></td></tr><tr><td>0x24000-0x27FFF</td><td>9</td><td>9</td><td>9</td><td>9</td><td>9</td><td>9</td><td>9</td><td>9</td><td>9</td><td colspan="3">9x24000-0x27FFF9</td><td>9</td><td>10</td><td>11</td><td>12</td><td>13</td><td>14</td><td>15</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td></td></tr><tr><td>0x28000-0x2BFFF</td><td>10</td><td>10</td><td>10</td><td>10</td><td>10</td><td>10</td><td>10</td><td>10</td><td>10</td><td colspan="3">10x28000-0x2BFFF10</td><td>10</td><td>11</td><td>12</td><td>13</td><td>14</td><td>15</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td></td></tr><tr><td>0x2C000-0x2FFF</td><td>11</td><td>11</td><td>11</td><td>11</td><td>11</td><td>11</td><td>11</td><td>11</td><td>11</td><td colspan="3">11x2C000-0x2FFF11</td><td>11</td><td>12</td><td>13</td><td>14</td><td>15</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td></td></tr><tr><td>0x30000-0x33FFF</td><td>12</td><td>12</td><td>12</td><td>12</td><td>12</td><td>12</td><td>12</td><td>12</td><td>12</td><td colspan="3">12x30000-0x33FFF12</td><td>12</td><td>13</td><td>14</td><td>15</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td></td></tr><tr><td>0x34000-0x37FFF</td><td>13</td><td>13</td><td>13</td><td>13</td><td>13</td><td>13</td><td>13</td><td>13</td><td>13</td><td colspan="3">13x34000-0x37FFF13</td><td>13</td><td>14</td><td>15</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>8</td><td></td></tr><tr><td>0x38000-0x3BFFF</td><td>14</td><td>14</td><td>14</td><td>14</td><td>14</td><td>14</td><td>14</td><td>14</td><td>14</td><td colspan="3">14x38000-0x3BFFF4</td><td>14</td><td>15</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>8</td><td>9</td><td></td></tr><tr><td>0x3C000-0x3FFF</td><td>15</td><td>15</td><td>15</td><td>15</td><td>15</td><td>15</td><td>15</td><td>15</td><td>15</td><td colspan="3">15x3C000-0x3FFF15</td><td>15</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>8</td><td>9</td><td>10</td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td rowspan="13">示例代码</td><td rowspan="13" colspan="24">for (int32_t i = 0; i &lt; tiling-&gt;loopOneCore; i+)+ {AscendC::SyncAll();Copyln(i);Compute();AscendC::SyncAll();CopyOut(i);}</td><td></td><td></td></tr><tr><td></td><td></td></tr><tr><td></td><td></td></tr><tr><td></td><td></td></tr><tr><td></td><td></td></tr><tr><td></td><td></td></tr><tr><td></td><td></td></tr><tr><td></td><td></td></tr><tr><td></td><td></td></tr><tr><td></td><td></td></tr><tr><td></td><td></td></tr><tr><td></td><td></td></tr><tr><td></td><td></td></tr></table>

# 修改切分策略

仍以一个形状为 (8192, 128) 的float类型输入进行Adds计算为例。 

为了体现同地址冲突的影响，上述场景设计中每一行的数据大小为512字节（128个 float），每个核每一轮计算处理512 * 8字节的数据，并进行全核同步（实际场景中并 不需要），每一轮计算都需要等待所有核完成当前数据块的计算后，再进行下一轮。 

<table><tr><td>实现方案</td><td colspan="10">原始实现</td><td colspan="10">优化实现</td><td></td><td></td></tr><tr><td>实现方法</td><td colspan="10">使用16个核参与计算,按列方向进行切分,每个核总计算数据量为8192*8;单核执行循环16次,每次计算的数据量为512*8;每个核的循环顺序如下图所示,列方向0~15表示每个核的数据块执行顺序。由于多个核同时访问同一行数据(512字节),导致同地址冲突的发生。</td><td colspan="9">使用16个核参与计算,按行方向进行切分,每个核总计算数据量为512*128;单核执行循环16次,每次计算的数据量为512*8;每个核的循环顺序如下图所示(行方向),均为从块0~块15。由于每个核每一轮处理的地址在不同行,不会同时访问连续的512字节,所以不会导致同地址访问冲突。</td><td></td><td></td><td></td></tr><tr><td rowspan="18">示意图</td><td></td><td>0核</td><td>1核</td><td>2核</td><td>3核</td><td>4核</td><td>5核</td><td>6核</td><td>7核</td><td>8核</td><td>9核</td><td>10核</td><td>11核</td><td>0核</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td></tr><tr><td>0x0000-0x03FFF</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>1核</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td></tr><tr><td>0x0400-0x07FFF</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>2核</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td></tr><tr><td>0x0800-0x0BFFF</td><td>2</td><td>2</td><td>2</td><td>2</td><td>2</td><td>2</td><td>2</td><td>2</td><td>2</td><td>2</td><td>2</td><td>2</td><td>3核</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td></tr><tr><td>0x0C00-0x0FFF</td><td>3</td><td>3</td><td>3</td><td>3</td><td>3</td><td>3</td><td>3</td><td>3</td><td>3</td><td>3</td><td>3</td><td>3</td><td>4核</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td></tr><tr><td>0x1000-0x13FFF</td><td>4</td><td>4</td><td>4</td><td>4</td><td>4</td><td>4</td><td>4</td><td>4</td><td>4</td><td>4</td><td>4</td><td>4</td><td>5核</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td></tr><tr><td>0x1400-0x17FFF</td><td>5</td><td>5</td><td>5</td><td>5</td><td>5</td><td>5</td><td>5</td><td>5</td><td>5</td><td>5</td><td>5</td><td>5</td><td>6核</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td></tr><tr><td>0x1800-0x1BFFF</td><td>6</td><td>6</td><td>6</td><td>6</td><td>6</td><td>6</td><td>6</td><td>6</td><td>6</td><td>6</td><td>6</td><td>6</td><td>7核</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td></tr><tr><td>0x1C00-0x1FFF</td><td>7</td><td>7</td><td>7</td><td>7</td><td>7</td><td>7</td><td>7</td><td>7</td><td>7</td><td>7</td><td>7</td><td>7</td><td>8核</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td></tr><tr><td>0x2000-0x23FFF</td><td>8</td><td>8</td><td>8</td><td>8</td><td>8</td><td>8</td><td>8</td><td>8</td><td>8</td><td>8</td><td>8</td><td>8</td><td>9核</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td></tr><tr><td>0x2400-0x27FFF</td><td>9</td><td>9</td><td>9</td><td>9</td><td>9</td><td>9</td><td>9</td><td>9</td><td>9</td><td>9</td><td>9</td><td>9</td><td>10核</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td></tr><tr><td>0x2800-0x2BFFF</td><td>10</td><td>10</td><td>10</td><td>10</td><td>10</td><td>10</td><td>10</td><td>10</td><td>10</td><td>10</td><td>10</td><td>10</td><td>11核</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td></tr><tr><td>0x2C00-0x2FFF</td><td>11</td><td>11</td><td>11</td><td>11</td><td>11</td><td>11</td><td>11</td><td>11</td><td>11</td><td>11</td><td>11</td><td>11</td><td>12核</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td></tr><tr><td>0x3000-0x33FFF</td><td>12</td><td>12</td><td>12</td><td>12</td><td>12</td><td>12</td><td>12</td><td>12</td><td>12</td><td>12</td><td>12</td><td>12</td><td>13核</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td></tr><tr><td>0x3400-0x37FFF</td><td>13</td><td>13</td><td>13</td><td>13</td><td>13</td><td>13</td><td>13</td><td>13</td><td>13</td><td>13</td><td>13</td><td>13</td><td>14核</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td></tr><tr><td>0x3800-0x3BFFF</td><td>14</td><td>14</td><td>14</td><td>14</td><td>14</td><td>14</td><td>14</td><td>14</td><td>14</td><td>14</td><td>14</td><td>14</td><td>15核</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td></tr><tr><td>0x3C00-0x3FFF</td><td>15</td><td>15</td><td>15</td><td>15</td><td>15</td><td>15</td><td>15</td><td>15</td><td>15</td><td>15</td><td>15</td><td>15</td><td>16核</td><td>0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr></table>

<table><tr><td>实现方案</td><td>原始实现</td><td>优化实现</td></tr><tr><td>示例代码</td><td>_aicore__inline void Init(GM_ADDR x, GM_ADDR z, AddsCustomTilingData* tilingPtr) {tiling = tilingPtr; xGm.SetGlobalBuffer(_gm_float *)x + AscendC::GetBlockIdx() * tiling-&gt;tileN); zGm.SetGlobalBuffer(_gm_float *)z + AscendC::GetBlockIdx() * tiling-&gt;tileN); // we disable the L2 cache mode to highlight the influence of the gm address conflict xGm.SetL2CacheHint(AscendC::CacheMode::CA CHE_MODE_DISABLE); zGm.SetL2CacheHint(AscendC::CacheMode::CA CHE_MODE_DISABLE); pipeInitBuffer(inQueueX, BUFFER_NUM, tiling-&gt;tileM * tiling-&gt;tileN * sizeof(float)); pipeInitBuffer(outQueueZ, BUFFER_NUM, tiling-&gt;tileM * tiling-&gt;tileN * sizeof(float));}</td><td>_aicore__inline void Init(GM_ADDR x, GM_ADDR z, AscendC:GlobalBuffer(_gm_float *)x + AscendC::GetBlockIdx() * tiling-&gt;tileM * tiling-&gt;n); zGm.SetGlobalBuffer(_gm_float *)z + AscendC::GetBlockIdx() * tiling-&gt;tileM * tiling-&gt;n); // we disable the L2 cache mode to highlight the influence of the gm address conflict xGm.SetL2CacheHint(AscendC::CacheMode::CAC HE_MODE_DISABLE); zGm.SetL2CacheHint(AscendC::CacheMode::CAC HE_MODE_DISABLE); pipeInitBuffer(inQueueX, BUFFER_NUM, tiling-&gt;tileM * tiling-&gt;tileN * sizeof(float)); pipeInitBuffer(outQueueZ, BUFFER_NUM, tiling-&gt;tileM * tiling-&gt;tileN * sizeof(float));}</td></tr></table>

# 说明

你可以通过执行如下命令行，通过msprof工具获取上述示例的性能数据并进行对比。 

msprof op --launch-count=3 --output=./prof ./execute_adds_op 

重点关注PipeUtilization.csv中的aiv_mte2_time(us)和aiv_mte3_time(us)搬运指令耗时。 

# 3.8.5.7 设置合理的 L2 CacheMode

【优先级】高 

# 说明

该性能优化指导适用于如下产品型号： 

● Atlas A3 训练系列产品/Atlas A3 推理系列产品 

● Atlas A2 训练系列产品/Atlas A2 推理系列产品 

【描述】L2 Cache常用于缓存频繁访问的数据，其物理位置如下图所示： 

![](images/3865f78c12ea863ad4ebdbd527a2d861c5f888ee3eb8ce60221bfea354198d28.jpg)



L2 Cache的带宽相比GM的带宽有数倍的提升，因此当数据命中L2 Cache时，数据的 搬运耗时会优化数倍。通常情况下，L2 Cache命中率越高，算子的性能越好，在实际 访问中需要通过设置合理的L2 CacheMode来保证重复读取的数据尽量缓存在L2 Cache上。


# L2 Cache 访问的原理及 CacheMode 介绍

数据通过MTE2搬运单元搬入时，L2 Cache访问的典型流程如下： 

![](images/535a843a0a2591faed64eabc975c158a8e9a892fe0287bdf946a9b2c78e11f8f.jpg)



数据通过MTE3或者Fixpipe搬运单元搬出时，L2 Cache访问的典型流程如下：


![](images/4174dae55ff84c62d5312cabac926fe25b6d59bd3be63cfce4f6e3eb9b9bdea1.jpg)


从上面的流程可以看出，当数据访问总量超出L2 Cache容量时，AI Core会对L2 Cache 进行数据替换。由于Cache一致性的要求，替换过程中旧数据需要先写回GM（此过程 中会占用GM带宽），旧数据写回后，新的数据才能进入L2 Cache。 

开发者可以针对访问的数据设置其CacheMode，对于只访问一次的Global Memory数 据设置其访问状态为不进入L2 Cache，这样可以更加高效的利用L2 Cache缓存需要重 复读取的数据，避免一次性访问的数据替换有效数据。 

# 设置 L2 CacheMode 的方法

Ascend C基于GlobalTensor提供了SetL2CacheHint接口，用户可以根据需要指定 CacheMode。 

考虑如下场景，构造两个Tensor的计算，x的输入Shape为(5120, 5120)，y的输入 Shape为(5120, 15360)，z的输出Shape为(5120, 15360)，由于两个Tensor的Shape不 相等，x分别与y的3个数据块依次相加。该方案主要为了演示CacheMode的功能，示 例代码中故意使用重复搬运x的实现方式，真实设计中并不需要采用这个方案。下文完 整样例请参考设置合理L2 CacheMode样例。 

![](images/179bb45a497200a140b12fcef524947cafa2281909488e4b2bfe2fa7df7ad7ba.jpg)


<table><tr><td>实现方案</td><td>原始实现</td><td>优化实现</td></tr><tr><td>实现方法</td><td>总数据量700MB,其中:x:100MB;y:300MB;z:300MB。使用40个核参与计算,按列方向切分。x、y、z对应GlobalTensor的CacheMode均设置为CACHE_MODE_NORMAL,需要经过L2 Cache,需要进入L2 Cache的总数据量为700MB。</td><td>总数据量700MB,其中:x:100MB;y:300MB;z:300MB。使用40个核参与计算,按列方向切分。x对应的GlobalTensor的CacheMode设置为CACHE_MODE_NORMAL;y和z对应的GlobalTensor的CacheMode设置为CACHE_MODE_DISABLE。只有需要频繁访问的x,设置为需要经过L2 Cache。需要进入L2 Cache的总数据量为100MB。</td></tr><tr><td>示例代码</td><td>xGm.SetGlobalBuffer((gm_float*)x+AscendC::GetBlockIdx() * TILE_N);yGm.SetGlobalBuffer((gm_float*)y+AscendC::GetBlockIdx() * TILE_N);zGm.SetGlobalBuffer((gm_float*)z+AscendC::GetBlockIdx() * TILE_N);</td><td>xGm.SetGlobalBuffer((gm_float*)x+AscendC::GetBlockIdx() * TILE_N);yGm.SetGlobalBuffer((gm_float*)y+AscendC::GetBlockIdx() * TILE_N);zGm.SetGlobalBuffer((gm_float*)z+AscendC::GetBlockIdx() * TILE_N);// disable the L2 cache mode of y and zyGm.SetL2CacheHint(AscendC::CacheMode::CACHE_MODE_DISABLE);zGm.SetL2CacheHint(AscendC::CacheMode::CACHE_MODE_DISABLE);</td></tr></table>

# 说明

你可以通过执行如下命令行，通过msprof工具获取上述示例的性能数据并进行对比。 

```batch
msprof op --launch-count=2 --output=.prof ./execute_add_op 
```

重点关注Memory.csv中的aiv_gm_to_ub_bw(GB/s)和aiv_main_mem_write_bw(GB/s)写带宽的 速率。 

# 3.8.5.8 算子与高阶 API 共享临时 Buffer

# 【优先级】高

【描述】如果算子使用的高阶API需要传入临时Buffer，如SoftMax，该临时空间会挤 占算子其他计算的空间，从而导致单次计算搬运的数据量变少，搬运的次数变多。此 场景可通过共享临时Buffer空间，提升单次搬运的数据量，减少搬运的次数，提升内存 使用效率。 

# 【反例】

SoftMax高阶API计算需要临时Buffer空间，算子在进行其他计算时拥有独立临时 Buffer。UB空间是固定的，假设可以给SoftMax和Add能分配临时空间为64KB， SoftMax计算需要的临时Buffer空间tmpSoftmaxBuf占用32KB，则存储Add计算结果 的LocalTensor tmpSumBuf最多只能分配32KB。如果src0Tensor计算的数据量是 512KB，则需要搬运512 / 32 = 16次。 

```cpp
constEXPR int32_t blockLen = 32 * 1024;
TBuf<TPosition::VECCALC> tmpSoftmaxBuf;
pipe.InitialBuffer(tmpSoftmaxBuf, softmaxBufSize * sizeof uint8_t)); // 单独分配Softmax的临时Buf 32KB
TBuf<TPosition::VECCALC> tmpSumBuf; 
```

```txt
pipe InitBuffer(tmpSumBuf, sumBufSize * sizeof(T)); // 单独分配Add的临时Buf，且softmaxBufSize * sizeof uint8_t) + sumBufSize * sizeof(T) <= 64KB  
...  
for (int i = 0; i < 16; i++) {  
    LocalTensor调度任务  
    LocalTensor调度任务  
    LocalTensor调度任务  
    LocalTensor调度任务  
    LocalTensor调度任务  
    LocalTensor调度任务  
    LocalTensor调度任务  
    LocalTensor调度任务  
    LocalTensor调度任务  
    LocalTensor调度任务  
    LocalTensor调度任务  
    LocalTensor调度任务  
    LocalTensor调度任务  
    LocalTensor调度任务  
    LocalTensor调度任务  
    LocalTensor调度任务  
    LocalTensor调度任务  
    Local Tensor调度任务  
    Local Tensor调度任务  
    Local Tensor调度任务  
    Local Tensor调度任务  
    Local Tensor调度任务  
    Local Tensor调度任务  
    Local Tensor调度任务  
    Local Tensor调度任务  
    Local Tensor调度任务  
    Local Tensor调度任务  
    Local Tensor调度任务  
    Local Tensor调度任务  
    Local Tensor调度任务  
    Local Tensor调度任务  
    Local Tensor调度任务  
    Local Tensor调度任务  
    Local Tensor调度任务  
        Local Tensor调度任务  
        Local Tensor调度任务  
        Local Tensor调度任务  
        Local Tensor调度任务  
        Local Tensor调度任务  
        Local Tensor调度任务  
        Local Tensor调度任务  
        Local Tensor调度任务  
        Local Tensor调度任务  
        Local Tensor调度任务  
        Local Tensor调度任务  
        Local Tensor调度任务  
        Local Tensor调度任务  
        Local Tensor调度任务  
        Local Tensor调度任务  
        Local Tensor调度任务  
        Local Tensor调度业务  
        Local Tensor调度业务  
        Local Tensor调度业务  
        Local Tensor调度业务  
        Local Tensor调度业务  
        Local Tensor调度业务  
        Local Tensor调度业务  
        Local Tensor调度业务  
        Local Tensor调度业务  
        Local Tensor调度业务  
        Local Tensor调度业务  
        Local Tensor调度业务  
        Local Tensor调度业务  
        Local Tensor调度业务  
        Local Tensor调度业务  
        Local Tensor调度业务  
        Local Tensor调度业务  
        LocalTensor调度业务  
        LocalTensor调度业务  
        LocalTensor调度业务  
        LocalTensor调度业务  
        LocalTensor调度业务  
        LocalTensor调度业务  
        LocalTensor调度业务  
        LocalTensor调度业务  
        LocalTensor调度业务  
        LocalTensor调度业务  
        LocalTensor调度业务  
        LocalTensor调度业务  
        LocalTensor调度业务  
        LocalTensor调度业务  
        LocalTensor调度业务  
        LocalTensor调度业务  
        LocalTensor调度业务  
         local tensor sizeofT; // 该变量为大小的整型数据类型，即大小为64KB的数组元素。 
```

# 【正例】

SoftMax高阶API计算需要临时Buffer空间，算子在进行其他计算时可以共享此临时 Buffer，按照上述假设只需要搬运512 / 64 = 8次。 

constexpr int32_t blockLen $= 64$ *1024;   
TBuf<TPosition::VECCALC> tmpSharedBuf;   
pipe.InitialBuffer(tmpSharedBuf,bufferSize); //共享分配bufferSize $\equiv$ MAX(softmaxBufSize\*sizeof uint8_t), sumBufSize\* sizeof(T)) $\ll = 64\mathrm{KB}$ for (int i $= 0$ ;i $<  8$ . $\mathrm{i + + }$ { LocalTensor<uint8_t> tmpSharedTensor $=$ tmpSharedBuf.Get<uint8_t>(softmaxBufSize); SoftMax<T, true, true>(dstTensor, expSumTensor, dstMaxTensor, srcTensor, tmpSharedTensor, tiling); DataCopy(src0Tensor, src0Gm[i\*blockLen / sizeof(T)], Params); LocalTensor<T> tmpSumTensor $=$ tmpSharedBuf.Get<T>(sumBufSize); Add<T>(tmpSumTensor, src0Tensor, src1Tensor, count);   
} 

# 3.8.5.9 纯搬运类算子 VECIN 和 VECOUT 建议复用

# 【优先级】高

【描述】纯搬运类算子在执行时并不涉及实际vector计算，若存在冗余的vector指令， 会导致算子整体执行时间变长。这种场景可以使用Ascend C针对纯搬运类算子提供的 TQueBind接口，该接口可以将VECIN与VECOUT绑定，省略将数据从VECIN拷贝到 VECOUT的步骤，从而避免vector的无谓消耗。 

# 【反例】

此段代码为了保证数据搬入和数据搬出之间的流水同步，存在LocalTensor -> LocalTensor的DataCopy指令。 

```cpp
template <typename ComputeT> class KernelExample {
public:
    ...
    __aicore__ inline void Process(...)
    {
        for (int i = 0; i < iLen; ++i) {
            auto iLocal = Qual AllocTensor<ComputeT>(); 
            DataCopy(iLocal, inGm[i * 32], size); 
            Qual.EnQue(iLocal); 
            iLocal = Qual.DeQue<ComputeT>(); 
            for (int j = 0; j < jLen; ++j) {
                auto oLocal = QueO AllocTensor<ComputeT>(); 
```

DataCopy(oLocal, iLocal, size); // LocalTensor -> LocalTensor的数据Copy指令，以实现数据从VECIN到VECOUT的搬运QueO.EnQue(oLocal);auto oLocal $=$ QueO.DeQue<ComputeT>();DataCopyPad(outGm[j], oLocal, ...);QueO.FreeTensor(oLocal);}Quel.FreeTensor(iLocal);1}private:TQue<TPosition::VECIN,BUFFER_NUM> Quel;TQue<TPosition::VECOUT,BUFFER_NUM> QueO;};extern"C" _global_ _aicore_ void example_kernel(...){...op.Process(...);} 

# 【正例】

将LocalTensor $- >$ LocalTensor的DataCopy指令替换为TQueBind接口，减少将VECIN 拷贝到VECOUT的步骤，从而避免了冗余拷贝。 

```cpp
template <typename ComputeT> class KernelExample {
public:
    __aicore__ inline void Process(...)
    {
        for (int i = 0; i < iLen; ++i) {
            auto bindLocal = queBind AllocTensor<ComputeT>(); 
            DataCopy(bindLocal, inGm[i * 32], size); 
            queBind.EnQue(bindLocal); 
            bindLocal = queBind.DeQue<ComputeT>(); 
            for (int j = 0; j < jlen; ++j) {
                DataCopyPad(outGm[j], bindLocal, ...); 
            } 
            queBind.FreeTensor(bindLocal); 
        }
    }
private:
    __TQueBind<TPosition::VECIN, TPosition::VECOUT, BUFFER_NUM> queBind; // 使用TQueBind替换原来的 
    Quel, QueO
}; 
```

# 【性能对比】


图 3-111 aiv_vec_time 优化前后对比


![](images/31e6023e44ee068e00dc1b2c37ef0b9cc2fa5dc16b08e6d3fd2184335dba4987.jpg)


如上图所示，将反例中DataCopy指令替换为TQueBind之后有明显优化。由于省略了 数据从VECIN拷贝到VECOUT的步骤，aiv_vec_time几乎缩减为0。 

# 3.8.5.10 通过缩减 Tensor ShapeInfo 维度，优化栈空间

# 【优先级】中

【描述】GlobalTensor和LocalTensor中通过ShapeInfo类型的成员变量来保存shape信 息，SetShapeInfo/GetShapeInfo可以设置或者获取ShapeInfo，在算子实现内部用于 shape信息保存和传递。默认情况下支持的最大维度为8。在不使用上述ShapeInfo功能 的情况下，不需要这些信息，可以通过K_MAX_SHAPE_DIM宏将其设置为0。经实测减 小K_MAX_SHAPE_DIM值，可缩减栈空间，减少scalar指令和cache miss几率，提升算 子性能。 

```cpp
...
#	define K_MAX_SHAPE_DIM
#	define K_MAX_SHAPE_DIM 8
#endif
...
struct ShapeInfo {
public:
    ...
    uint32_t shape[K_MAX_SHAPE_DIM];
    uint32_t originalShape[K_MAX_SHAPE_DIM];
};
template<typename T> class GlobalTensor {
    ...
private:
    ShapeInfo shapeInfo_;
}
template<typename T> class LocalTensor {
    ...
private:
    ShapeInfo shapeInfo_;
} 
```

【反例】 

算子无需使用ShapeInfo，但未对ShapeInfo大小进行限制（使用默认值8），导致浪费 K_MAX_SHAPE_DIM * sizeof(uint32_t) * 2 * 4字节的栈空间。2表示有shape和 originalShape两个数组，4表示该样例中使用了GlobalTensor和LocalTensor共4个 Tensor。 

```c
include "kernel_operator.h" ...   
extern "C" __global __aicore__ void add_custom(GM_ADDR x, GM_ADDR x, GM_ADDR z, GM_ADDR   
workspace, GM_ADDR tiling)   
{ GlobalTensor<T> dataIn; GlobalTensor<T> dataOut; LocalTensor<T> vecIn; LocalTensor<T> vecOut; } 
```

【正例】 

算子无需使用ShapeInfo，设置#define K_MAX_SHAPE_DIM 0，有效缩减了 K_MAX_SHAPE_DIM * sizeof(uint32_t) * 2 * 4大小的栈空间。 

```c
define K_MAX_SHAPE_DIM 0   
...   
#include "kernel_operator.h" //需注意定义K_MAX_SHAPE_DIM宏的位置须在包含Ascend C相关头文件之前   
extern"C" _global _ aicore _ void addcustom(GM_ADDR x, GM_ADDR x, GM_ADDR z, GM_ADDR   
workspace, GM_ADDR tiling)   
{ GlobalTensor<T> dataIn; GlobalTensor<T> dataOut; LocalTensor<T> vecIn; LocalTensor<T> vecOut; } 
```

# 3.8.5.11 避免 Unified Buffer 的 bank 冲突

# 3.8.5.11.1 概述

【优先级】高 

【概述】 

为了提高数据访问的效率和吞吐量，Unified Buffer采用了大小相等的内存模块 （bank）结构设计。当多条读写指令同时访问Unified Buffer时，由于硬件资源的限 制，这些指令不能同时执行，从而引发bank冲突。在这种情况下，指令需要排队等待 资源，无法在一个指令周期内完成。 

针对NPU架构版本220x 

![](images/cb2542bf26f990201cdda47e288ac69b9a0adefd95bfcb28e28ec062fccfb46d.jpg)


UB总大小为192KB，包含16个bank group，每个bank group包含3个bank。每个 bank大小为4KB，由128行组成，每行长度为32B。 

读写冲突：读操作和写操作同时尝试访问同一个bank。 

写写冲突：多个写操作同时尝试访问同一个bank group。 

读读冲突：多个读操作同时尝试访问同一个bank group。 

针对Atlas 350 加速卡 

![](images/98e34ec7421091076623e0795412052307d6ee2a7f6b9c161604098cd695f176.jpg)


UB总大小为256KB，包含8个bank group，每个bank group包含2个bank。每个 bank大小为16KB，由512行组成，每行长度为32B。 

读写冲突：读操作和写操作同时尝试访问同一个bank。 

写写冲突：多个写操作同时尝试访问同一个bank group。 

读读冲突：两个读操作同时尝试访问同一个bank，或者两个以上读操作同时 尝试访问同一个bank group。 

可以看出bank冲突的场景与Unified Buffer的规格密切相关，规格的变化通常会导致 bank冲突场景的变化。 

由于Atlas 350 加速卡的bank group上有两组读口和写口，因此两次读操作访问 同一个bank group的不同bank时，不会引起冲突。 

假设读指令操作的地址为0x0000（bank0），写指令操作的地址为0x10000 ，在 NPU架构版本220x中，地址0x10000（bank16）不会发生读写冲突，而在Atlas 350 加速卡中，这个地址0x10000（bank0）会引发读写冲突。 

下文介绍不同硬件架构下如何避免bank冲突。 

# 3.8.5.11.2 避免 bank 冲突（NPU 架构版本 220x）

【优先级】高 

# 说明

该性能优化建议适用于如下产品型号： 

● Atlas A3 训练系列产品/Atlas A3 推理系列产品 

● Atlas A2 训练系列产品/Atlas A2 推理系列产品 

【描述】为了提高数据访问的效率和吞吐量，Unified Buffer采用了bank（大小相等的 内存模块）结构设计。Unified Buffer总大小为192K，划分为48个bank。每个bank由 128行组成，每行长度为32B。这48个bank进一步组织为16个bank group，每个bank group包含3个bank，例如bank15、bank31和bank47组成一个bank group。 


图 3-112 bank 结构示意图（图中箭头方向表示内存排布的顺序）


![](images/c76c05b25d3c984e8638bde9a7c1355159c98436ba0c5c888b04408941de9474.jpg)


每个bank可以独立地进行数据的读写操作，允许多个数据请求同时进行。然而，当多 个读写操作试图同时访问同一个bank或bank group时，由于硬件资源的限制，这些操 作必须排队等待，会导致bank冲突，引起性能下降。 

具体来说，Vector计算单元每拍（一个指令周期）能够从每个bank group中读取或写 入一行数据。如果同一个API中的多个操作试图同时访问同一个bank或bank group， Vector计算单元无法在同一个周期内处理所有请求，导致这些请求排队等待。这种排 队增加了数据访问的延迟，降低了系统的整体性能。 

# bank 冲突的典型场景

bank冲突主要可以分为以下三种场景： 

读写冲突：读操作和写操作同时尝试访问同一个bank。 

写写冲突：多个写操作同时尝试访问同一个bank group。 

读读冲突：多个读操作同时尝试访问同一个bank group。 

下文给出了一些具体的示例，假设，0x10000地址在bank16上，0x10020在bank17 上，0x20020在bank33上，如下图所示： 


图 3-113 地址分配示意图


![](images/b93a45d2644881536257dcb74caca19b031e0421aa7a649ed495ab6760b97fa2.jpg)


读写冲突示例 

Vector指令的源操作数src和目的操作数dst同时读写到同一个bank时造成读写冲 突，具体分析如下： 


表 3-18 读写冲突示例


<table><tr><td>序号</td><td>src地址</td><td>dst地址</td><td>bank</td><td>bank group</td><td>结论</td></tr><tr><td>示例1</td><td>0x10 020</td><td>0x100 00</td><td>bank_id0 != bank_id1</td><td>bank_group_id0 != bank_group_id1</td><td>src地址和dst地址分别属于bank16和bank17,故无冲突。</td></tr><tr><td>示例2</td><td>0x10 020</td><td>0x10E 20</td><td>bank_id0 == bank_id1</td><td>bank_group_id0 == bank_group_id1</td><td>src地址和dst地址的地址都在bank17,故存在冲突。</td></tr></table>

# 写写冲突示例

Vector指令目的操作数dst对应的8个DataBlock（block0-block7）同时写到一个 bank group时造成写写冲突，具体分析如下： 


表 3-19 写写冲突示例


<table><tr><td>序号</td><td>dst地址</td><td>blk_stride</td><td>block0_addr</td><td>block1_addr</td><td>block2_addr</td><td>...</td><td>结论</td></tr><tr><td>示例1</td><td>0x1FE00</td><td>16</td><td>0x1FE00</td><td>0x20000</td><td>0x20200</td><td>...</td><td>8个DataBlock均在一个bank group下,故全部冲突,8拍完成一个Repeat的写入。</td></tr><tr><td>示例2</td><td>0x1FE00</td><td>8</td><td>0x1FE00</td><td>0x1FF00</td><td>0x20000</td><td>...</td><td>block0和block2在一个bank group,存在冲突,4拍完成一个Repeat的写入。</td></tr></table>

# 读读冲突

Vector指令多个源操作数同时读到同一个bank group时造成读读冲突，具体 分析如下： 


表 3-20 双 src 场景读读冲突示例


<table><tr><td>序号</td><td>src0地址</td><td>src1地址</td><td>bank</td><td>bank group</td><td>结论</td></tr><tr><td>示例1</td><td>0x10020</td><td>0x20020</td><td>bank_id0 != bank_id1</td><td>bank_group_id0 == bank_group_id1</td><td>存在冲突。</td></tr><tr><td>示例2</td><td>0x10020</td><td>0x10000</td><td>bank_id0 != bank_id1</td><td>bank_group_id0 != bank_group_id1</td><td>无冲突。</td></tr></table>

Vector指令某一个源操作数对应的8个DataBlock（block0-block7）读到同一 个bank group时造成读读冲突，具体分析如下： 


表 3-21 单 src 场景读读冲突示例


<table><tr><td>序号</td><td>src地址</td><td>blk_stride</td><td>block0_adr</td><td>block1_addr</td><td>block2_addr</td><td>...</td><td>结论</td></tr><tr><td>示例1</td><td>0x1FE00</td><td>16</td><td>0x1FE00</td><td>0x20000</td><td>0x20200</td><td>...</td><td>8个DataBlock均在一个 bank group下,故全部冲突,8拍完成一个Repeat的读操作。</td></tr><tr><td>示例2</td><td>0x1FE00</td><td>8</td><td>0x1FE00</td><td>0x1F000</td><td>0x20000</td><td>...</td><td>block0和block2在同一个bank group下,存在冲突,4拍完成一个Repeat。</td></tr></table>

# 说明

通过msProf工具可以进行资源冲突占比的相关性能数据采集。 

工具的具体使用方法请参考算子调优（msProf）。资源冲突占比文件性能数据文件说明请参考 ResourceConflictRatio（资源冲突占比）。 

# 如何避免 bank 冲突

避免bank冲突的方法有两种：优化计算逻辑和优化地址分配。 

# 优化计算逻辑

对一个shape为(8, 16, 16)的输入做(1, 0, 2)的transpose操作，输出shape为(16, 8, 16)。通过将计算逻辑由“跳读，连续写”修改为“连续读，跳写”可避免冲突 问题。实现方案对比如下： 

<table><tr><td>实现方案</td><td>原始实现</td><td>优化实现</td></tr><tr><td>实现方法</td><td>跳读，连续写
同一Repeat内输入的8个DataBlock都在同一个bankgroup而发生读读冲突。</td><td>连续读，跳写
同一个Repeat内输入的8个DataBlock不在同一个bank group内，避免了读读冲突。</td></tr></table>

<table><tr><td>实现方案</td><td colspan="101">原始实现</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td rowspan="9">示意图</td><td colspan="100">shape (8,16,16) 每一个小方格32B,包含16个数</td><td colspan="74">shape (8,16,16) 每一个小方格32B,包含16个数</td><td>shape (8,16,16) 每一个小方格32B,包含16个数</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>32B</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>32B</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>32B</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>32B</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>32B</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td rowspan="2">32B</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>32B</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32C</td><td rowspan="3">transpose</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32D</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32S</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="3">32B</td><td rowspan="2">32B</td><td rowspan="2">32B</td><td rowspan="2">32B</td><td>32B</td><td>32R</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32A</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32B</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32T</td><td>32B</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32T</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32T</td><td>32T</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32B</td><td>32T</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32B</td><td>32T</td><td>32B</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32T</td><td>32B</td><td>32B</td><td>32T</td><td>32T</td><td>32C</td><td>Transpose</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>30</td><td>Transpose</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td><td>32B</td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr></table>

# 优化地址分配

实现连续4096个float元素的加法z = x + y，通过在内存分配时适当扩大内存，保 证在一个Repeat内，x和y不会同时出现在同一个bank group内，x/y和z不会同时 出现同一个bank内。完整样例可参考避免bank冲突样例。 

实现方案对比如下： 

<table><tr><td>实现方案</td><td colspan="101">原始实现</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>实现方法</td><td colspan="100">不做地址优化,直接使用InitBuffer分配内存,各个Tensor的地址分别为:x:起始地址0x0,tensor长度为4096*size(float)字节y:起始地址0x4000,tensor长度为4096*size(float)字节z:起始地址0x8000,tensor长度为4096*size(float)字节在一个Repeat内,x和y同时读同一个bank group,x/y和z同时读写同一个bank。</td><td colspan="63">优化地址,使用InitBuffer分配内存时适当扩大内存申请,各个Tensor的地址分别为:x:起始地址0x0,tensor长度为(4096*size(float)+256)字节y:起始地址0x4100,tensor长度为(64*1024-(4096*size(float)+256))字节z:起始地址0x10000,tensor长度为4096*size(float)字节在一个Repeat内,x和y同时读同一个bank group,x/y和z同时读写同一个bank。</td><td colspan="100">优化地址,使用InitBuffer分配内存时适当扩大内存申请,各个Tensor的地址分别为:x:起始地址0x0,tensor长度为(4096*t size(float)+256)字节y:起始地址0x4100,tensor长度为(64*1024-(4096*t size(float)+256))字节z:起始地址0x10000,tensor长度为4096*t size(float)字节x多申请256字节,避免一个Repeat内x,y同时读同一个bank group;y多申请空间,确保z不会和x/y落入同一个bank</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>示意图</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>银行k04KB</td><td>bank14KB</td><td>bank24KB</td><td>bank34KB</td><td>bank44KB</td><td>bank54KB</td><td>bank64KB</td><td>bank74KB</td><td>bank84KB</td><td>bank94KB</td><td>bank104KB</td><td>bank114KB</td><td>bank124KB</td><td>bank134KB</td><td>bank144KB</td><td>bank154KB</td><td>bank164KB</td><td>bank174KB</td><td>bank184KB</td><td>bank194KB</td><td>bank204KB</td><td>bank214KB</td><td>bank224KB</td><td>bank234KB</td><td>bank244KB</td><td>bank254KB</td><td>bank264KB</td><td>bank274KB</td><td>bank284KB</td><td>bank294KB</td><td>bank304KB</td><td>bank314KB</td><td>bank324KB</td><td>bank334KB</td><td>bank344KB</td><td>bank354KB</td><td>bank364KB</td><td>bank374KB</td><td>bank384KB</td><td>bank394KB</td><td>bank404KB</td><td>bank414KB</td><td>bank424KB</td><td>bank434KB</td><td>bank444KB</td><td>bank454KB</td><td>bank464KB</td><td>bank474KB</td><td>bank484KB</td><td>bank494KB</td><td>bank504KB</td><td>bank514KB</td><td>bank524KB</td><td>bank534KB</td><td>bank544KB</td><td>bank554KB</td><td>bank564KB</td><td>bank574KB</td><td>bank584KB</td><td>bank594KB</td><td>bank604KB</td><td>bank614KB</td><td>bank624KB</td><td>bank634KB</td><td>bank644KB</td><td>bank654KB</td><td>bank664KB</td><td>bank674KB</td><td>bank684KB</td><td>bank694KB</td><td>bank704KB</td><td>bank714KB</td><td>bank724KB</td><td>bank734KB</td><td>bank744KB</td><td>bank754KB</td><td>bank764KB</td><td>bank774KB</td><td>bank784KB</td><td>bank794KB</td><td>bank804KB</td><td>bank814KB</td><td>bank824KB</td><td>bank834KB</td><td>bank844KB</td><td>bank854KB</td><td>bank864KB</td><td>bank874KB</td><td>bank884KB</td><td>bank894KB</td><td>bank904KB</td><td>bank914KB</td><td>bank924KB</td><td>bank934KB</td><td>bank944KB</td><td>bank954KB</td><td>bank964KB</td><td>bank974KB</td><td>bank984KB</td><td>bank994KB</td><td>bank104KB</td><td>bank1054KB</td><td>bank1064KB</td><td>bank1074KB</td><td>bank1084KB</td><td>bank1094KB</td><td>bank114KB</td><td>bank1154KB</td><td>bank1164KB</td><td>bank1174KB</td><td>bank1184KB</td><td>bank1194KB</td><td>bank1204KB</td><td>bank1214KB</td><td>bank1224KB</td><td>bank1234KB</td><td>bank1244KB</td><td>bank1254KB</td><td>bank1264KB</td><td>bank1274KB</td><td>bank1284KB</td><td>bank1294KB</td><td>bank1304KB</td><td>bank1314KB</td><td>bank1324KB</td><td>bank1334KB</td><td>bank1344KB</td><td>bank1354KB</td><td>bank1364KB</td><td>bank1374KB</td><td>bank1384KB</td><td>bank1394KB</td><td>bank1404KB</td><td>bank1414KB</td><td>bank1424KB</td><td>bank1434KB</td><td>bank1444KB</td><td>bank1454KB</td><td>bank1464KB</td><td>bank1474KB</td><td>bank1484KB</td><td>bank1494KB</td><td>bank1504KB</td><td>bank1514KB</td><td>bank1524KB</td><td>bank1534KB</td><td>bank1544KB</td><td>bank1554KB</td><td>bank1564KB</td><td>bank1574KB</td><td>bank1584KB</td><td>bank1594KB</td><td>bank1604KB</td><td>bank1614KB</td><td>bank1624KB</td><td>bank1634KB</td><td>bank1644KB</td><td>bank1654KB</td><td>bank1664KB</td><td>bank1674KB</td><td>bank1684KB</td><td>bank1694KB</td><td>bank1704KB</td><td>bank1714KB</td><td>bank1724KB</td><td>bank1734KB</td><td>bank1744KB</td><td>bank1754KB</td><td>bank1764KB</td><td>bank1774KB</td><td>bank1784KB</td><td>bank1794KB</td><td>bank1804KB</td><td>bank1814KB</td><td>bank1824KB</td><td>bank1834KB</td><td>bank1844KB</td><td>bank1854KB</td><td>bank1864KB</td><td>bank1874KB</td><td>bank1884KB</td><td>bank1894KB</td><td>bank1904KB</td><td>bank1914KB</td><td>bank1924KB</td><td>bank1934KB</td><td>bank1944KB</td><td>bank1954KB</td><td>bank1964KB</td><td>bank1974KB</td><td>bank1984KB</td><td>bank1994KB</td><td>bank2004KB</td><td>bank2014KB</td><td>bank2024KB</td><td>bank2034KB</td><td>bank2044KB</td><td>bank2054KB</td><td>bank2064KB</td><td>bank2074KB</td><td>bank2084KB</td><td>bank2094KB</td><td>bank2104KB</td><td>bank2114KB</td><td>bank2124KB</td><td>bank2134KB</td><td>bank2144KB</td><td>bank2154KB</td><td>bank2164KB</td><td>bank2174KB</td><td>bank2184KB</td><td>bank2194KB</td><td>bank2204KB</td><td>bank2214KB</td><td>bank2224KB</td><td>bank2234KB</td><td>bank2244KB</td><td>bank2254KB</td><td>bank2264KB</td><td>bank2274KB</td><td>bank2284KB</td><td>bank2294KB</td><td>bank2304KB</td><td>bank2314KB</td><td>bank2324KB</td><td>bank2334KB</td><td>bank2344KB</td><td>bank2354KB</td><td>bank2364KB</td><td>bank2374KB</td><td>bank2384KB</td><td>bank2394KB</td><td>bank2404KB</td><td>bank2414KB</td><td>bank2424KB</td><td>bank2434KB</td><td>bank2444KB</td><td>bank2454KB</td><td>bank2464KB</td><td>bank2474KB</td><td>bank2484KB</td><td>bank2494KB</td><td>bank2504KB</td><td>bank2514KB</td><td>bank2524KB</td><td>bank2534KB</td><td>bank2544KB</td><td>bank2554KB</td><td>bank2564KB</td><td>bank2574KB</td><td>bank2584KB</td><td>bank2594KB</td><td>bank2604KB</td><td>bank2614KB</td><td>bank2624KB</td><td>bank2634KB</td><td>bank2644KB</td><td>bank2654KB</td><td>bank2664KB</td><td>bank2674KB</td><td>bank2684KB</td><td>bank2694KB</td><td>bank2704KB</td><td>bank2714KB</td><td>bank2724KB</td><td>bank2734KB</td><td>bank2744KB</td><td>bank2754KB</td><td>bank2764KB</td><td>bank2774KB</td><td>bank2784KB</td><td>bank2794KB</td><td>bank2804KB</td><td>bank2814KB</td><td>bank2824KB</td><td>bank2834KB</td><td>bank2844KB</td><td>bank2854KB</td><td>bank2864KB</td><td>bank2874KB</td><td>bank2884KB</td><td>bank2894KB</td><td>bank2904KB</td><td>bank2914KB</td><td>bank2924KB</td><td>bank2934KB</td><td>bank2944KB</td><td>bank2954KB</td><td>bank2964KB</td><td>bank2974KB</td><td>bank2984KB</td><td>bank2994KB</td><td>bank3004KB</td><td>bank3014KB</td><td>bank3024KB</td><td>bank3034KB</td><td>bank3044KB</td><td>bank3054KB</td><td>bank3064KB</td><td>bank3074KB</td><td>bank3084KB</td><td>bank3094KB</td><td>bank3104KB</td><td>bank3114KB</td><td>bank3124KB</td><td>bank3134KB</td><td>bank3144KB</td><td>bank3154KB</td><td>bank3164KB</td><td>bank3174KB</td><td>bank3184KB</td><td>bank3194KB</td><td>bank3204KB</td><td>bank3214KB</td><td>bank3224KB</td><td>bank3234KB</td><td>bank3244KB</td><td>bank3254KB</td><td>bank3264KB</td><td>bank3274KB</td><td>bank3284KB</td><td>bank3294KB</td><td>bank3304KB</td><td>bank3314KB</td><td>bank3324KB</td><td>bank3334KB</td><td>bank3344KB</td><td>bank3354KB</td><td>bank3364KB</td><td>bank3374KB</td><td>bank3384KB</td><td>bank3394KB</td><td>bank3395KB</td><td>bank3404KB</td><td>bank3414KB</td><td>bank3424KB</td><td>bank3434KB</td><td>bank3444KB</td><td>bank3454KB</td><td>bank3464KB</td><td>bank3474KB</td><td>bank3484KB</td><td>bank3494KB</td><td>bank3504KB</td><td>bank3514KB</td><td>bank3524KB</td><td>bank3534KB</td><td>bank3544KB</td><td>bank3554KB</td><td>bank3564KB</td><td>bank3574KB</td><td>bank3584KB</td><td>bank3594KB</td><td>bank3604KB</td><td>bank3614KB</td><td>bank3624KB</td><td>bank3634KB</td><td>bank3644KB</td><td>bank3654KB</td><td>bank3664KB</td><td>bank3674KB</td><td>bank3684KB</td><td>bank3694KB</td><td>bank3704KB</td><td>bank3714KB</td><td>bank3724KB</td><td>bank3734KB</td><td>bank3744KB</td><td>bank3754KB</td><td>bank3764KB</td><td>bank3774KB</td><td>bank3784KB</td><td>bank3794KB</td><td>bank3804KB</td><td>bank3814KB</td><td>bank3824KB</td><td>bank3834KB</td><td>bank3844KB</td><td>bank3854KB</td><td>bank3864KB</td><td>bank3874KB</td><td>bank3884KB</td><td>bank3894KB</td><td>bank3904KB</td><td>bank3914KB</td><td>bank3924KB</td><td>bank3934KB</td><td>bank3944KB</td><td>bank3954KB</td><td>bank3964KB</td><td>bank3974KB</td><td>bank3984KB</td><td>bank3994KB</td><td>bank4004KB</td><td>bank4014KB</td><td>bank4024KB</td><td>bank4034KB</td><td>bank4044KB</td><td>bank4054KB</td><td>bank4064KB</td><td>bank4074KB</td><td>bank4084KB</td><td>bank4094KB</td><td>bank4104KB</td><td>bank4114KB</td><td>bank4124KB</td><td>bank4134KB</td><td>bank4144KB</td><td>bank4154KB</td><td>bank4164KB</td><td>bank4174KB</td><td>bank4184KB</td><td>bank4194KB</td><td>bank4204KB</td><td>bank4214KB</td><td>bank4224KB</td><td>bank4234KB</td><td>bank4244KB</td><td>bank4254KB</td><td>bank4264KB</td><td>bank4274KB</td><td>bank4284KB</td><td>bank4294KB</td><td>bank4304KB</td><td>bank4314KB</td><td>bank4324KB</td><td>bank4334KB</td><td>bank4344KB</td><td>bank4354KB</td><td>bank4364KB</td><td>bank4374KB</td><td>bank4384KB</td><td>bank4394KB</td><td>bank4395KB</td><td>bank4305KB</td><td>bank43154KB</td><td>bank43254KB</td><td>bank43354KB</td><td>bank43454KB</td><td>bank43554KB</td><td>bank43654KB</td><td>bank43754KB</td><td>bank43854KB</td><td>bank43954KB</td><td>bank44054KB</td><td>bank44154KB</td><td>bank44254KB</td><td>bank44354KB</td><td>bank44454KB</td><td>bank44554KB</td><td>bank44654KB</td><td>bank44754KB</td><td>bank448554KB</td><td>bank449554KB</td><td>bank450554KB</td><td>bank451554KB</td><td>bank452554KB</td><td>bank453554KB</td><td>bank454554KB</td><td>bank455554KB</td><td>bank4565554KB</td><td>bank4575554KB</td><td>bank4585554KB</td><td>bank4595554KB</td><td>bank46055554KB</td><td>bank46155554KB</td><td>bank46255554KB</td><td>bank46355554KB</td><td>bank464555554KB</td><td>bank465555554KB</td><td>bank4665555554KB</td><td>bank4675555554KB</td><td>bank46855555554KB</td><td>bank46955555554KB</td><td>bank470555555554KB</td><td>bank4715555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555555.</td></tr></table>

# 3.8.5.11.3 避免 bank 冲突（Atlas 350 加速卡）

为了提高数据访问的效率和吞吐量，Unified Buffer采用了bank（大小相等的内存模 块）结构设计。Unified Buffer总大小为256K，划分为16个bank。每个bank由512行 组成，每行长度为32B。这16个bank进一步组织为8个bank group，每个bank group 包含2个bank，例如bank7和bank15组成一个bank group。 


图 3-114 bank 结构示意图（图中箭头方向表示内存排布的顺序）


![](images/9202d45de7c5bf914c02359d5949fd4971fe47e43a6a70a7e927548015135887.jpg)


每个bank可以独立地进行数据的读写操作，允许多个数据请求同时进行。然而，当多 个读写操作试图同时访问同一个bank，由于硬件资源的限制，这些操作必须排队等 待，会导致bank冲突，引起性能下降。 

具体来说，Vector计算单元每拍（一个指令周期）能够从每个bank group中读取或写 入一行数据。当多个读写操作试图同时访问同一个bank，Vector计算单元无法在同一 个周期内处理所有请求，导致这些请求排队等待。这种排队增加了数据访问的延迟， 降低了系统的整体性能。 

# bank 冲突的典型场景

bank冲突主要可以分为以下三种场景： 

读写冲突：读操作和写操作同时尝试访问同一个bank。 

写写冲突：多个写操作同时尝试访问同一个bank group。 

读读冲突：两个读操作同时尝试访问同一个bank，或者两个以上读操作同时尝试 访问同一个bank group。 

下文给出了一些具体的示例，假设，0x10000地址在bank0上，0x10020在bank1上， 如下图所示： 


图 3-115 地址分配示意图


![](images/846f0bc1952f13c58a48762b31ec36284194d791f73be81bb2307ed33238e2ad.jpg)


# 读写冲突示例

Vector指令的源操作数src和目的操作数dst同时读写到同一个bank时造成读写冲 突，具体分析如下： 


表 3-22 读写冲突示例


<table><tr><td>序号</td><td>src地址</td><td>dst地址</td><td>bank</td><td>bank group</td><td>结论</td></tr><tr><td>示例1</td><td>0x10 020</td><td>0x100 00</td><td>bank_id0 != bank_id1</td><td>bank_group_id0 != bank_group_id1</td><td>src地址和dst地址分别属于bank0和bank1，故无冲突。</td></tr><tr><td>示例2</td><td>0x10 020</td><td>0x101 20</td><td>bank_id0 == bank_id1</td><td>bank_group_id0 == bank_group_id1</td><td>src地址和dst地址的地址都在bank0，故存在冲突。</td></tr></table>

# 写写冲突示例

Vector指令目的操作数dst对应的8个DataBlock（block0-block7）同时写到一个 bank group时造成写写冲突，具体分析如下： 


表 3-23 写写冲突示例


<table><tr><td>序号</td><td>dst地址</td><td>blk_stride</td><td>block0_addr</td><td>block1_addr</td><td>block2_addr</td><td>...</td><td>结论</td></tr><tr><td>示例1</td><td>0x10000</td><td>8</td><td>0x10000</td><td>0x10100</td><td>0x10200</td><td>...</td><td>8个DataBlock均在一个bank group下,故全部冲突,8拍完成一个Repeat的写入。</td></tr></table>

# 读读冲突

Vector指令两个源操作数同时读到同一个bank时造成读读冲突，具体分析如 下： 


表 3-24 双 src 场景读读冲突示例


<table><tr><td>序号</td><td>src0地址</td><td>src1地址</td><td>bank</td><td>bank group</td><td>结论</td></tr><tr><td>示例1</td><td>0x10000</td><td>0x10100</td><td>bank_id0==bank_id1</td><td>bank_group_id0 == bank_group_id1</td><td>存在冲突。</td></tr><tr><td>示例2</td><td>0x10000</td><td>0x10020</td><td>bank_id0 != bank_id1</td><td>bank_group_id0 != bank_group_id1</td><td>无冲突。</td></tr></table>

Vector指令某一个源操作数对应的8个DataBlock(block0-block7）读到同一 个bank时造成读读冲突，具体分析如下： 


表 3-25 单 src 场景读读冲突示例


<table><tr><td>序号</td><td>src地址</td><td>blk_stride</td><td>block0_adr</td><td>block1_addr</td><td>block2_addr</td><td>...</td><td>结论</td></tr><tr><td>示例1</td><td>0x10000</td><td>8</td><td>0x10000</td><td>0x10100</td><td>0x10200</td><td>...</td><td>8个DataBlock均在一个bank下,故全部冲突,8拍完成一个Repeat的读操作。</td></tr></table>

# 如何避免 bank 冲突

避免bank冲突的方法有两种：优化计算逻辑和优化地址分配。 

# 优化计算逻辑

对一个数据类型为float，shape为(16, 64)的输入每个元素加1。通过将计算逻辑 由逐列计算改为逐行计算可避免同一Repeat下的冲突问题，实现方案对比如下： 

<table><tr><td>实现方案</td><td>原始实现</td><td>优化实现</td></tr><tr><td>实现方法</td><td>逐列计算,同一Repeat内输入的8个DataBlock都在同一个bank而发生读读冲突。</td><td>逐行计算,同一个Repeat内输入的8个DataBlock不在同一个bank内,避免了同一Repeat内的读读冲突。</td></tr><tr><td rowspan="16">示意图</td><td>shape (8,64) 每一个小方格32B,包含8个数</td><td>shape (8,64) 每一个小方格32B,包含8个数</td></tr><tr><td>32B</td><td>32B 32B 32B 32B 32B 32B 32B</td></tr><tr><td>32B</td><td></td></tr><tr><td>32B</td><td></td></tr><tr><td>32B</td><td></td></tr><tr><td>32B</td><td></td></tr><tr><td>32B</td><td></td></tr><tr><td>32B</td><td></td></tr><tr><td>32B</td><td></td></tr><tr><td>32B</td><td></td></tr><tr><td>32B</td><td></td></tr><tr><td>32B</td><td></td></tr><tr><td>32B</td><td></td></tr><tr><td>32B</td><td></td></tr><tr><td>32B</td><td></td></tr><tr><td></td><td></td></tr><tr><td>示例代码</td><td>uint64_t mask = 64; 
AscendC::UnaryRepeatParams params; 
params.dstBlkStride = 8; 
params.srcBlkStride = 8; 
for( uint16_t i = 0; i &lt; 8; ++i) { 
    AscendC::Adds.dst[i * 8], src[i * 8], 1, mask, 1, params); 
}</td><td>uint64_t mask = 64; 
AscendC::UnaryRepeatParams params; 
params.dstBlkStride = 1; 
for( uint16_t i = 0; i &lt; 8; ++i) { 
    AscendC::Adds.dst[i * 64], src[i * 64], 1, mask, 1, params); 
}</td></tr></table>

# 优化地址分配

实现连续4096个float元素的加法z = x + y，通过在内存分配时适当扩大内存，保 证在一个Repeat内，x/y和z不会同时出现同一个bank内。 

实现方案对比如下： 

<table><tr><td>实现方案</td><td>原始实现</td><td>优化实现</td></tr><tr><td>实现方法</td><td>不做地址优化,直接使用InitBuffer分配内存,各个Tensor的地址分别为:x:起始地址0x00000,tensor长度为4096*size(float)字节y:起始地址0x04000,tensor长度为4096*size(float)字节z:起始地址0x08000,tensor长度为4096*size(float)字节在一个Repeat内,x和y同时读同一个bank group,x/y和z同时读写同一个bank。</td><td>优化地址,使用InitBuffer分配内存时适当扩大内存申请,各个Tensor的地址分别为:x:起始地址0x00000,tensor长度为4096*size(float)字节y:起始地址0x04000,tensor长度为(8*16*1024-(4096*size(float))字节z:起始地址0x20000,tensor长度为4096*size(float)字节y多申请空间,确保z不会和x/y落入同一个bank。</td></tr><tr><td>示意图</td><td>bank016KB bank116KB bank216KB bank316KB bank416KB bank516KB bank616KB bank716KB bank816KB bank916KB bank1016KB bank1116KB bank1216KB bank1316KB bank1416KB bank1516KB x y z</td><td>bank816KB bank916KB bank1016KB bank1116KB bank1216KB bank1316KB bank1416KB bank1516KB x y z</td></tr><tr><td>示例代码</td><td>pipe InitBuffer(inQueueX,1,4096*size(float));pipe InitBuffer(inQueueY,1,4096*size(float));pipe InitBuffer(outQueueZ,1,4096*size(float));</td><td>constexpr int32_t TOTAL_LENGTH = 1024 * 4;constexpr int32_t BUFFER_NUM = 1;constexpr int32_t_BANKGROUP_SIZE = 1024 * 128;...pipe InitBuffer(inQueueX,BUFFER_NUM,TOTAL_LENGTH * sizeof(float));pipe InitBuffer(inQueueY,BUFFER_NUM,BANKGROUP_SIZE - TOTAL_LENGTH * sizeof(float));pipe InitBuffer(outQueueZ,BUFFER_NUM,TOTAL_LENGTH * sizeof(float));</td></tr></table>

# 3.8.5.12 L2 Cache 切分

# 【优先级】：高

【描述】假设，AI处理器的L2 Cache大小为192MB，L2 Cache读写混合带宽约为 7TB/s，而GM的带宽约为1.6TB/s，两者之间存在较大差距。搬入或搬出相同数据量的 情况下，访问L2 Cache读写数据比GM更快。若数据无法命中L2 Cache，即需要访问 的数据不在L2 Cache内，导致需要去GM上读写，带宽利用效率较低，最终算子搬入或 搬出数据变为算子整个运行过程的性能瓶颈。切分策略建议：当输入和输出数据的数 据量超过L2 Cache大小时，Tiling中使能L2 Cache切分策略。 

【反例】 

假设输入数据大小为InputTotalSize，L2 Cache大小为L2CacheSize，InputTotalSize = L2CacheSize * 2，总核数为20个核，数据未切分，整体一次完成计算。假设20个核一 次可以处理共L2CacheSize的数据，则每个核至少两次读取输入数据。 


图 3-116 未使能 L2 Cache 切分


384MB 

<table><tr><td>0</td><td>0</td><td>1</td><td>1</td><td>2</td><td>2</td><td>3</td><td>3</td><td>4</td><td>4</td><td>5</td><td>5</td><td>6</td><td>6</td><td>7</td><td>7</td><td>8</td><td>8</td><td>9</td><td>9</td></tr><tr><td>10</td><td>10</td><td>11</td><td>11</td><td>12</td><td>12</td><td>13</td><td>13</td><td>14</td><td>14</td><td>15</td><td>15</td><td>16</td><td>16</td><td>17</td><td>17</td><td>18</td><td>18</td><td>19</td><td>19</td></tr></table>

![](images/1d57ce40b3aa03915c538b8c7a36de1322cd3a2274220595055d56a208c256cc.jpg)


中数字表示核ID 

```txt
constexpr int32_t TOTAL_LENGTH = InputTotalSize / sizeof(half);   
constexpr int32_t USE_CORE_NUM = 20;   
constexpr int32_t TILE_NUM = 2;   
constexpr int32_t BLOCK_LENGTH = TOTAL_LENGTH / USE_CORE_NUM;   
constexpr int32_t TILE_LENGTH = BLOCK_LENGTH / TILE_NUM;   
class KernelSample {   
public: _aicore__inline KernelSample() {} _aicore__inline void Init(GM_ADDR x) { xGm.SetGlobalBuffer((gm__half*)x + BLOCK_LENGTH * GetBlockIdx(), BLOCK_LENGTH); yGm.SetGlobalBuffer((gm__half*)y + BLOCK_LENGTH * GetBlockIdx(), BLOCK_LENGTH); pipeInitBuffer(inQueueX, 1, BLOCK_LENGTH * sizeof(half)); pipeInitBuffer(inQueueY, 1, BLOCK_LENGTH * sizeof(half)); } _aicore__inline void Process() { //示例演示对输入数据加2的运算 constexpr int32_t loopCount = 2; for (int32_t i = 0; i < loopCount; i++) { //外层的每次循环对输入数据进行加1的运算 for (int32_t j = 0; j < TILE_NUM; j++) { //内层循环分别处理每个核第0块和第1块数据 CopyIn(j); Compute(); CopyOut(j); } }   
private: _aicore__inline void CopyIn(int32_t process) { LocalTensor< half> xLocal = inQueueX AllocTensor< half>(); //对于每个核，除了首次读取外，读取第0块数据时，L2 Cache内缓存的是第1块数据； //对于每个核，读取第1块数据时，L2 Cache内缓存的是第0块数据； //每个核需要4次读取GM上的数据 DataCopy(xLocal, xGm[process * TILE_LENGTH], TILE_LENGTH); inQueueX.EnQue(xLocal); } _aicore__inline void Compute() { LocalTensor< half> yLocal = inQueueY AllocTensor< half>(); LocalTensor< half> xLocal = inQueueX.DeQue< half>(); Adds(yLocal, xLocal, 1, TILE_LENGTH); inQueueY.EnQue< half>(yLocal); inQueueX.FreeTensor(xLocal); } _aicore__inline void CopyOut(int32_t process) { LocalTensor< half> yLocal = inQueueY.DeQue< half>(); DataCopy(yGm[process * TILE_LENGTH], yLocal, TILE_LENGTH); inQueueY.FreeTensor(yLocal); } 
```

} 

# 【正例】

假设输入数据大小为InputTotalSize，L2 Cache大小为L2CacheSize，InputTotalSize = L2CacheSize * 2，能使用的总核数为20个核，输入数据均等切分成2份数据，则整体 分两次进行计算，每次的计算量为L2CacheSize，第一次20个核先计算前L2CacheSize 个数据，第二次20个核计算后L2CacheSize个数据。每次计算前读取的数据能够命中L2 Cache，提升算子性能。 


图 3-117 使能 L2 Cache 切分


![](images/ee16a44cba5db87aa1637e8862d32d08ef0f36ddab584dfe98c267ac5ed70a67.jpg)


![](images/41912cbeb72f30b4af4bca7fe5927cada240b79b0ef20ba1755958ee2f9822d8.jpg)


中数字表示核ID 

```txt
constexpr int32_t TOTAL_LENGTH = InputTotalSize / sizeof (half);   
constexpr int32_t TILE_NUM = 2;   
constexpr int32_t USE_CORE_NUM = 20;   
constexpr int32_t TILE_LENGTH = TOTAL_LENGTH / TILE_NUM;   
constexpr int32_t BLOCK_LENGTH = TILE_LENGTH / USE_CORE_NUM;   
class KernelSample {   
public: __aicore__ inline KernelSample() {} __aicore__ inline void Init(GM_ADDR x, GM_ADDR y, int32_t index) { xGm.SetGlobalBuffer((gm__half*)x + BLOCK_LENGTH * GetBlockIdx() + index * TILE_LENGTH, BLOCK_LENGTH); yGm.SetGlobalBuffer((gm__half*)y + BLOCK_LENGTH * GetBlockIdx() + index * TILE_LENGTH, BLOCK_LENGTH); pipeInitBuffer(inQueueX, 1, BLOCK_LENGTH * sizeof (half)); pipeInitBuffer(inQueueY, 1, BLOCK_LENGTH * sizeof (half)); } __aicore__ inline void Process() { //示例演示对输入数据加2的运算 constexpr int32_t loopCount = 2; for (int32_t i = 0; i < loopCount; i++) { //每次循环对输入数据进行加1的运算 CopyIn(); Compute(); CopyOut(); } }   
private: __aicore__ inline void CopyIn() { LocalTensor< half> xLocal = inQueueX AllocTensor< half>(); //对于每个核，除了首次读取外，第二次读取可以命中L2 Cache; //每个核2次读取GM上的数据，2次访问L2 Cache读数据 DataCopy(xLocal, xGm, BLOCK_LENGTH); inQueueX.EnQue(xLocal); } __aicore__ inline void Compute() { LocalTensor< half> yLocal = inQueueY AllocTensor< half>(); LocalTensor< half> xLocal = inQueueX.DeQue< half>(); Adds(yLocal, xLocal, 1, BLOCK_LENGTH); inQueueY.EnQue< half>(yLocal); inQueueX.FreeTensor(xLocal); } 
```

```cpp
__aicore__ inline void CopyOut()
{
    LocalTensor<half> yLocal = inQueueY.DeQue<half>();
    DataCopy(yGm, yLocal, BLOCK_LENGTH);
    inQueueY.FreeTensor(yLocal);
}
}
extern "C" __global__ __aicore__ void simple_kernel(_gm uint8_t* srcGm, _gm uint8_t* dstGm)
{
    AscendC::KernelSample op;
    // 输入数据均等切分成2份数据进行计算
    for (int32_t i = 0; i < TILE_NUM; i++) {
        opInit(srcGm, dstGm, i);
        op.Process();
    }
} 
```

更多完整样例请参考L2 Cache切分的算子样例。 

# 3.8.6 矢量计算

# 3.8.6.1 通过 Unified Buffer 融合实现连续 vector 计算

【优先级】高 

【描述】算子实现中涉及多次vector计算，且前一次计算输出是后一次计算输入的情况 下，可将前一次计算输出暂存在UB（Unified Buffer）上直接作为下一次计算的输入， 不需要将前一次的计算输出从UB搬运到GM后再从GM搬运到UB。这种UB Buffer融合 的方式可以减少搬入搬出次数，实现连续vector计算，提升内存使用效率。数据流图对 比如下： 


图 3-118 数据流图对比


![](images/0d29c8dd44499a721c95c6413a6d4d54a066b1f7dfac5e6cc89f828a181d6f57.jpg)


![](images/9d985b1ddbf2e12b781fcfd2a2d1ed173626fa4f8dc9ecbf60641fb11294d84a.jpg)


【反例】 

该算子的计算逻辑为进行Exp计算后再进行Abs计算。计算过程中先把源操作数从GM 搬运到UB进行Exp计算，Exp计算完成后将Exp的结果从UB搬运到GM；再从GM中把 Exp的结果搬运到UB上作为Abs计算的输入，Abs计算完成后将目的操作数结果从UB搬 运到GM。整个过程从GM搬进搬出共4次。当需要进行的vector计算为n次时，从GM 搬进搬出共需要2n次。 

```cpp
class KernelSample{   
public: __aicore__ inline KernelSample() {} __aicore__ inline void Init(_gm__ uint8_t\* src0Gm, _gm__ uint8_t\* dstGm) 
```

```txt
{ src0Global.SetGlobalBuffer(_gm_float\*src0Gm); dstGlobal.SetGlobalBuffer(_gm_float\*dstGm); pipe.InitialBuffer(inQueueSrc0,1,1024\*sizeof(float)); pipe.InitialBuffer(outQueueDst,1,1024\*sizeof(float)); } acore__inline void Process() { Copyln(); Compute(); CopyOut(); Copyln1(); Compute1(); CopyOut1(); } private: acore__inline void Copyln() { LocalTensor<float> src0Local = inQueueSrc0 AllocTensor<float>(); DataCopy(src0Local,src0Global,1024); inQueueSrc0.EnQue(src0Local); } acore__inline void Compute() { LocalTensor<float> src0Local = inQueueSrc0.DeQue<float>(); LocalTensor<float> dstLocal = outQueueDstAllocTensor<float>(); Exp.dstLocal,src0Local,1024); outQueueDst.EnQue<float>(dstLocal); inQueueSrc0.FreeTensor(src0Local); } acore__inline void CopyOut() { LocalTensor<float> dstLocal = outQueueDst.DeQue<float>(); DataCopy.dstGlobal,dstLocal,1024); outQueueDst.FreeTensor.dstLocal; } acore__inline void Copyln1() { LocalTensor<float> src0Local = inQueueSrc0 AllocTensor<float>(); DataCopy(src0Local,dstGlobal,1024); inQueueSrc0.EnQue(src0Local); } acore__inline void Compute1() { LocalTensor<float> src0Local = inQueueSrc0.DeQue<float>(); LocalTensor<float> dstLocal = outQueueDstAllocTensor<float>(); Abs.dstLocal,src0Local,1024); outQueueDst.EnQue<float>(dstLocal); inQueueSrc0.FreeTensor(src0Local); } acore__inline void CopyOut1() { LocalTensor<float> dstLocal = outQueueDst.DeQue<float>(); DataCopy.dstGlobal,dstLocal,1024); outQueueDst.FreeTensor.dstLocal; } private: TPipe pipe; TQue<TPosition::VECIN,1>inQueueSrc0; TQue<TPosition::VECOUT,1>outQueueDst; GlobalTensor<float> src0Global, dstGlobal; }; 
```

# 【正例】

使用UB Buffer融合方式后，在UB上进行连续vector计算时，前一次的结果可直接作为 后一次计算的输入，继续在UB上进行计算，不需要中间的搬进搬出，只需在开始计算 

时将源操作数搬运到UB，以及全部计算结束后将最终结果从UB搬运到GM，共2次搬 进搬出。 

class KernelSample {   
public: __aicore__inline KernelSample(){ __aicore__inline void Init(_gm__uint8_t\* src0Gm,_gm__uint8_t\* dstGm) { src0Global.SetGlobalBuffer(_gm__float\*)src0Gm); dstGlobal.SetGlobalBuffer(_gm__float\*)dstGm); pipe.InitialBuffer(inQueueSrc0,1,1024\*sizeof(float)); pipe.InitialBuffer(outQueueDst,1,1024\*sizeof(float)); } __aicore__inline void Process() { Copyln(); Compute(); CopyOut();   
}   
private: __aicore__inline void Copyln() { LocalTensor<float> src0Local $\equiv$ inQueueSrc0 AllocTensor<float>(); DataCopy(src0Local,src0Global,1024); inQueueSrc0.EnQue(src0Local); } __aicore__inline void Compute() { LocalTensor<float> src0Local $\equiv$ inQueueSrc0.DeQue<float>(); LocalTensor<float>dstLocal $\equiv$ outQueueDst AllocTensor<float>(); Exp(dstLocal,src0Local,1024); Abs(dstLocal,dstLocal,1024); outQueueDst.EnQue<float>(dstLocal); inQueueSrc0.FreeTensor(src0Local); } __aicore__inline void CopyOut() { LocalTensor<float>dstLocal $\equiv$ outQueueDst.DeQue<float>(); DataCopy(dstGlobal,dstLocal,1024); outQueueDst.FreeTensor(dstLocal);   
}   
private: TPipe pipe; TQue<TPosition::VECIN,1>inQueueSrc0; TQue<TPosition::VECOUT,1>outQueueDst; GlobalTensor<float> src0Global,dstGlobal;   
}; 

# 3.8.6.2 Vector 算子灵活运用 Counter 模式

# 【优先级】高

【描述】Normal模式下，通过迭代次数repeatTimes和掩码mask，控制Vector算子中 矢量计算API的计算数据量；当用户想要指定API计算的总元素个数时，首先需要自行 判断是否存在不同的主块和尾块，主块需要将mask设置为全部元素参与计算，并且计 算主块所需迭代次数，然后根据尾块中剩余元素个数重置mask，再进行尾块的运算， 在此过程中涉及大量Scalar计算。 

Counter模式下，用户不需要计算迭代次数以及判断是否存在尾块，将mask模式设置 为Counter模式后，只需要设置mask为{0, 总元素个数}，然后调用相应的API，处理逻 辑更简便，减少了指令数量和Scalar计算量，同时更加高效地利用了指令单次执行的并 发能力，进而提升性能。 

提示：Normal模式和Counter模式、掩码的介绍可参考2.5.2.3.1 如何使用掩码操作 API。 

以下反例和正例中的代码均以AddCustom算子为例，修改其中Add接口的调用代码， 以说明Counter模式的优势。 

```txt
AscendC::Add(zLocal, xLocal, yLocal, this->tileLength); 
```

# 【反例】

输入数据类型为half的xLocal, yLocal，数据量均为15000。Normal模式下，每个迭代 内参与计算的元素个数最多为256B/sizeof(half)=128个，所以15000次Add计算会被分 为：主块计算15000/128=117次迭代，每次迭代128个元素参与计算；尾块计算1次迭 代，该迭代15000-117*128=24个元素参与计算。从代码角度，需要计算主块的 repeatTimes、尾块元素个数；主块计算时，设置mask值为128，尾块计算时，需要设 置mask值为尾块元素个数24；这些过程均涉及Scalar计算。 

```cpp
uint32_t ELE_SIZE = 15000;  
AscendC::BinaryRepeatParams binaryParams;  
uint32_t numPerRepeat = 256 / sizeof(DTYPE_X); // DTYPE_X为half数据类型  
uint32_t mainRepeatTimes = ELE_SIZE / numPerRepeat;  
uint32_t tailEleNum = ELE_SIZE % numPerRepeat;  
AscendC::MaskNorm();  
AscendC::SetVectorMask<DTYPE_X, AscendC::MaskMode::NORMAL>(numPerRepeat); // 设置normal模式  
mask, 使每个迭代计算128个数  
AscendC::Add<DTYPE_X, false>(zLocal, xLocal, yLocal, AscendC::MASK-placeHOLDER, mainRepeatTimes, binaryParams); // MASK_placeHOLDER值为0，此处为mask占位，实际mask值以SetVectorMask设置的为准  
if (tailEleNum > 0) {  
    AscendC::SetVectorMask<DTYPE_X, AscendC::MaskMode::NORMAL>(tailEleNum); // 设置normal模式  
mask, 使每个迭代计算24个数  
// 偏移tensor的起始地址，在xLocal和yLocal的14976个元素处，进行尾块计算  
AscendC::Add<DTYPE_X, false>(zLocal[mainRepeatTimes * numPerRepeat], xLocal[mainRepeatTimes * numPerRepeat], yLocal[mainRepeatTimes * numPerRepeat], AscendC::MASK_placeHOLDER, 1, binaryParams);  
}  
AscendC::ResetMask(); // 还原mask值 
```

# 【正例】

输入数据类型为half的xLocal, yLocal，数据量均为15000。Counter模式下，只需要设 置mask为所有参与计算的元素个数15000，然后直接调用Add指令，即可完成所有计 算，不需要繁琐的主尾块计算，代码较为简练。 

当要处理多达15000个元素的矢量计算时，Counter模式的优势更明显，不需要反复修 改主块和尾块不同的mask值，减少了指令条数以及Scalar计算量，并充分利用了指令 单次执行的并发能力。 

```cpp
uint32_t ELE_SIZE = 15000;  
AscendC::BinaryRepeatParams binaryParams;  
AscendC::SetMaskCount();  
AscendC::SetVectorMask<DTYPE_X, AscendC::MaskMode::COUNTER>(ELE_SIZE); //设置counter模式mask，  
总共计算15000个数  
AscendC::Add<DTYPE_X, false>(zLocal, xLocal, yLocal, AscendC::MASK_placeHOLDER, 1,  
binaryParams); //MASK_placeHOLDER值为0，此处为mask占位，实际mask值以SetVectorMask设  
置的为准  
AscendC::ResetMask(); //还原mask值 
```

# 【性能对比】


图 3-119 Normal 模式和 Counter 模式下的 Scalar 执行时间对比


![](images/c279604382a990b756d4c09f57a710ef6a34afca620e22440bba3fc11f239646.jpg)



图 3-120 Normal 模式和 Counter 模式下的 Vector 执行时间对比


![](images/25c28f03a448f42a3af478aea8f39d5e5b7c1ba2d0d2706c555a97024c1e52f1.jpg)


以上性能数据是分别循环运行1000次反例和正例代码得到的Scalar和Vector执行时 间。从上述两幅性能对比图和示例代码可以看到，使用Counter模式能够大幅度简化代 码，易于维护，同时能够降低Scalar和Vector计算耗时，获得性能提升。 

# 3.8.6.3 选择低延迟指令，优化归约操作性能

# 【优先级】高

# 【描述】

指令执行延迟（Instruction Execution Latency） 指的是一条指令从开始执行到完全完 成（即所有操作结束，结果可用）所消耗的时间，它直接影响程序的响应速度和实时 性。在延迟敏感的场景中，降低指令执行延迟是提升性能的关键。下文以归约操作为 例，介绍了几种归约方案的性能对比，便于开发者在使用归约指令时，能够根据具体 的数据规模和场景，选择性能更高的方案。 

# 二分累加方案和归约类指令方案的对比

根据单指令性能测试数据（开发者可以自行测试）分析，WholeReduceSum等归约指 令的延迟时间约为Add指令的2-5倍。因此，对于连续数据的归约操作，可以采用Add 指令和WholeReduceSum指令的组合，以优化整体性能。该方案简称为二分累加方 案，具体方案说明如下： 

二分累加：将数据一分为二，使用Add指令将两部分数据相加；将相加后的结果 再次一分为二，继续使用Add指令进行累加，重复此过程。 

当二分累加后的数据量小于等于256Byte（一条指令一个Repeat的数据操作 量），使用WholeReduceSum指令，一次执行得到归约结果。 

假设输入数据的数据类型为float，shape为(5, 256)，下图展示了一行数据的执行过 程： 


图 3-121 二分累加方案示意图


![](images/30f643247f6b9b627e11577ea10482e8eaeef8622bedc517ee26343d624ad7a5.jpg)


将以上过程，针对每一行，各自执行，得到最终归约结果，即shape为(m, k)的数据， 归约完成后，shape为(m, 1)。 

由于ReduceSum接口是由多种指令组合实现，通常来说，数据量较大，循环次数较多 的场景，二分累加方案性能 > WholeReduceSum单指令操作性能 > ReduceSum接口 性能。而小数据量或者特殊shape下的场景，需要拆分开来，依据指令执行时间和指令 执行数目等条件，具体问题具体分析。 

下文给出了二分累加方案和归约类指令方案的核心代码片段和性能数据对比。完整样 例请参考ReduceCustom。 

# 【性能数据】

输入shape为30000，数据类型为float时，如下示例的性能数据对比如下，数据单位为 cycle，使用GetSystemCycle接口获取。 

<table><tr><td>二分累加方案</td><td>WholeReduceSum单指令操作</td></tr><tr><td>172</td><td>242</td></tr></table>

# 【二分累加方案】

```cpp
__aicore__inline void BinaryReduceSumImpl(const AscendC::LocalTensor& dst, const AscendC::LocalTensor<float>& src, const uint32_t bsLength, const uint32_t hLength)  
{ //src为二维数据，shape为(bsLength, hLength)，dst的shape为(bsLength,1) AscendC::BinaryRepeatParams binaryParams; AscendC::UnaryRepeatParams unaryParams; AscendC::SetMaskCount(); for (uint32_t i = 0; i < bsLength; i++) { AscendC::LocalTensor<float> srcTmp = src[i * hLength]; AscendC::LocalTensor<float> dstTmp = dst[i * hLength]; uint32_t totalNum = hLength / 16 * 16; uint32_t remaining = hLength - totalNum; AscendC::LocalTensor<float> remainingTensor = srcTmp[totalNum]; while (totalNum > ONE_REPEAT_FLOAT_SIZE) { uint32_t halfNum = AscendC::DivCeil(totalNum, 16) * DEFAULT REPstride; AscendC::SetVectorMask<uint8_t, AscendC::MaskMode::COUNTER>(0, totalNum - halfNum); AscendC::Add<float, false>(dstTmp, srcTmp, srcTmp[halfNum], AscendC::MASK_placeHOLDER, 1, binaryParams); totalNum = halfNum; srcTmp = dstTmp; } if (remaining != 0 && hLength > ONE_REPEAT_FLOAT_SIZE) { AscendC::SetVectorMask<uint8_t, AscendC::MaskMode::COUNTER>(0, remaining); AscendC::Add<float, false>(dstTmp, dstTmp, remainingTensor, AscendC::MASK_placeHOLDER, 1, binaryParams); AscendC::SetVectorMask<uint8_t, AscendC::MaskMode::COUNTER>(0, totalNum); AscendC::WholeReduceSum<float, false>(dstTmp, srcTmp, AscendC::MASK_placeHOLDER, 1, DEFAULT_BLKstride, DEFAULT_BLKstride, DEFAULT REPstride); AscendC::ResetMask(); AscendC::SetMaskNorm(); } 
```

# 【WholeReduceSum单指令操作】

```cpp
__aicore__ inline void WholeReduceSumImpl(const AscendC::LocalTensor& dst, const AscendC::LocalTensor& src, const uint32_t bsLength, const uint32_t hLength) { //src为二维数据，shape为(bsLength, hLength)，dst的shape为(bsLength,1) AscendC::SetMaskCount(); for (uint32_t i = 0; i < bsLength; i++) { uint32_t totalNum = hLength; 
```

```cpp
AscendC::LocalTensor<float> srcTmp = src[i * hLength]; AscendC::LocalTensor<float> dstTmp = dst[i * hLength]; while (totalNum > 1) { AscendC::SetVectorMask<int8_t, AscendC::MaskMode::COUNTER>(0, totalNum); AscendC::WholeReduceSum<float, false>(dstTmp, srcTmp, AscendC::MASK_placeHOLDER, 1, DEFAULT_BLK_STRIDE, DEFAULT_BLK_STRIDE, DEFAULTRep_STRIDE); totalNum = AscendC::DivCeil(totalNum, ONE_REPEAT_FLOAT_SIZE); srcTmp = dstTmp; } AscendC::ResetMask(); AscendC::SetMaskNorm(); 
```

# BlockReduceSum 和 WholeReduceSum 归约方案对比

进一步测试分析可知，单指令BlockReduceSum的执行效率优于WholeReduceSum， 因此，根据不同的shape，通过不同的指令组合，可以达到更佳的执行性能。 

例如数据类型为float，shape大小为256的数据，可以通过如下三种方式得到归约结 果： 

使用两次WholeReduceSum； 

使用三次BlockReduceSum； 

一次BlockReduceSum操作加一次WholeReduceSum操作。 

通过分析单指令性能数据（开发者可以自行测试）可知：一次BlockReduceSum操作加 一次WholeReduceSum操作性能优于两次WholeReduceSum，同时也优于三次 BlockReduceSum的方案。 

下文给出了上面三种方式的核心代码片段和性能数据对比。完整样例请参考 ReduceCustom。 

【性能数据】 

输入shape为256，数据类型为float。如下示例的性能数据如下： 


表 3-26 两次 WholeReduceSum、三次 BlockReduceSum、一次 BlockReduceSum 加 一次 WholeReduceSum，三种归约操作的性能数据（循环 100 次的时间总和）


<table><tr><td>两次WholeReduceSum</td><td>三次BlockReduceSum</td><td>一次BlockReduceSum加一次WholeReduceSum</td></tr><tr><td>13us</td><td>13.94us</td><td>8.44us</td></tr></table>

# 【两次WholeReduceSum操作】

```cpp
pipe.InitialBuffer(calcBuf, totalLength * sizeof(DTYPE));  
AscendC::LocalTensor<DTYPE> tempTensor1 = calcBuf.Get<DTYPE>();  
const uint32_t repeatNum = (totalLength * sizeof(DTYPE) + REP_LEN - 1) / REP_LEN;  
AscendC::SetMaskCount();  
AscendC::SetVectorMask<DTYPE>(0, totalLength);  
AscendC::WholeReduceSum<DTYPE, false>(tempTensor1, xLocal, 1, AscendC::MASKPLACEHOLDER, DEFAULT_BLK_STRIDE, DEFAULT_BLK_STRIDE, DEFAULTRep_STRIDE);  
AscendC::PipeBarrier<DPE_V>();  
AscendC::SetVectorMask<DTYPE>(0, repeatNum);  
AscendC::WholeReduceSum<DTYPE, false>(zLocal, tempTensor1, 1, AscendC::MASKPLACEHOLDER, 
```

```cpp
DEFAULT_BLK_STRIDE, DEFAULT_BLK_STRIDE, DEFAULTRep_STRIDE); AscendC::PipeBarrier<PIPE_V>(); AscendC::SetMaskNorm(); ... 
```

# 【三次BlockReduceSum操作】

```cpp
static constexpr uint32_t BLK_LEN = 32;  
TBuf<TPosition::VECCALC> calcBuf;  
constexpr uint32_t c0Count = BLK_LEN / sizeof(DTYPE_X);  
const uint32_t blockNum0 = (totalLength + c0Count - 1) / c0Count;  
const uint32_t blockNum1 = (blockNum0 + c0Count - 1) / c0Count;  
AscendC::SetMaskCount();  
AscendC::SetVectorMask<DTYPE_X>(0, totalLength);  
AscendC::BlockReduceSum<DTYPE_X, false>(tempTensor1, xLocal, AscendC::MASK-placeHOLDER, 1, DEFAULT_BLK_STRIDE, DEFAULT_BLK_STRIDE, DEFAULTRep_STRIDE);  
AscendC::PipeBarrier<PIPE_V>();  
AscendC::SetVectorMask<DTYPE_X>(0, blockNum0);  
AscendC::BlockReduceSum<DTYPE_X, false>(tempTensor1, tempTensor1, AscendC::MASK_placeHOLDER, 1, DEFAULT_BLK_STRIDE, DEFAULT_BLK_STRIDE, DEFAULTRep_STRIDE);  
AscendC::PipeBarrier<PIPE_V>();  
AscendC::SetVectorMask<DTYPE_X>(0, blockNum1);  
AscendC::BlockReduceSum<DTYPE_X, false>(zLocal, tempTensor1, AscendC::MASK_placeHOLDER, 1, DEFAULT_BLK_STRIDE, DEFAULT_BLK_STRIDE, DEFAULTRep_STRIDE);  
AscendC::PipeBarrier<PIPE_V>();  
AscendC::SetMaskNorm(); 
```

# 【BlockReduceSum $^ +$ WholeReduceSum操作】

```cpp
pipe InitBuffer(calcBuf, totalLength * sizeof(DTYPE));  
AscendC::LocalTensor<DTYPE> tempTensor1 = calcBuf.Get<DTYPE>();  
const expr uint32_t c0Count = BLK_LEN / sizeof(DTYPE);  
const uint32_t blockNum0 = (totalLength + c0Count - 1) / c0Count;  
AscendC::SetMaskCount();  
AscendC::SetVectorMask<DTYPE>(0, totalLength);  
AscendC::BlockReduceSum<DTYPE, false>(tempTensor1, xLocal, 1, AscendC::MASKPLACEHOLDER, DEFAULT_BLKstride, DEFAULT_BLKstride, DEFAULT_REPstride);  
AscendC::PipeBarrier<PIPE_V>();  
AscendC::SetVectorMask<DTYPE>(0, blockNum0);  
AscendC::WholeReduceSum<DTYPE, false>(zLocal, tempTensor1, 1, AscendC::MASKPLACEHOLDER, DEFAULT_BLKstride, DEFAULT_BLKstride, DEFAULT_REPstride);  
AscendC::PipeBarrier<PIPE_V>();  
AscendC::SetMaskNorm(); 
```

# 3.8.6.4 VF 性能优化

# 3.8.6.4.1 VF 循环优化

Atlas 350 加速卡对应的架构中，Vector Function（VF）是实现高性能向量计算的核 心载体。VF函数中可以包含最多四层嵌套循环，每层循环中还可以包含多个串行循 环，同时支持非循环的向量操作和标量操作。VF循环对控制结构的支持有限，仅支持 for循环和条件判断，不支持switch、do-while和 while-do等其他控制结构。VF循环通 过尽可能优化为硬件级向量循环（Hardware Loop），从而实现性能优化。 

当VF函数中的循环满足Hardware Loop编码规范时，会被编译器优化为Hardware Loop，提升整体的编码性能，否则它的循环逻辑会由迭代变量和条件判断语句构成 Software Loop，无法使能VF循环优化。 

在遵循Hardware Loop编码规范，确保循环可被优化为Hardware Loop基础上，可以 通过成员变量访问、指令分布优化和地址管理优化等方面进一步提升性能。 

# Hardware Loop 编码规范

为了能让编译器识别并生成Hardware Loop，对应的Loop代码必须符合硬件设计的要 求。具体规范如下： 

迭代变量类型 

VF内所有Loop的迭代变量必须是uint16_t 类型。 

起始值与步长 

循环起始值从0开始。 

每次迭代的步长必须是递增1。 

循环內不允许跳转指令，比如条件判断跳转, 如if/else，三元运算符?。 

VF内if/else在Loop内会阻碍Hardware Loop的生成，编译器虽然会尽可能的做if/ else消除优化，但是不做完全性保证。 

if控制流可使用if constexpr或者for(1)替换。if constexpr在编译时已经完成，无 运行时开销，但是需要传入的参数是编译时常量，不能依赖运行时变量；for(1)可 以触发编译器的循环优化，在当前硬件条件下，Vector侧执行Loop的性能是远远 优于条件分支跳转的。 

本示例展示了尾块处理场景，当尾块大小不为0时，hasTail为1，通过for(1)来代 替if(hasTail)的判断，提高了Loop的性能。 

```txt
//【反例】使用if语句  
uint16_t tailK = srcK % floatRepSize;  
uint16_t hasTail = 0;  
//通过!!tailK，对是否产生尾块进行判断，如果srcK % floatRepSize余数为0，则hasTail对应bool值为0（false），否则为1（true）  
hasTail = !!tailK;  
if(tailK > 0) {  
//尾块处理内容  
}  
//【正例】使用for(1)来替代if判断语句  
uint16_t tailK = srcK % floatRepSize;  
uint16_t hasTail = 0;  
hasTail = !!tailK;  
for uint16_t i = 0; i < hasTail; i++) {  
//尾块处理内容  
} 
```

一旦执行，循环计数/边界不允许被更改。 

若要利用外层循环的计数作为循环边界，将外层循环计数器移动到另一个寄存器 中，然后将其设置为循环边界。 

下文示例展示了编译器识别并处理为Hardware Loop和Software Loop的两种场景： 

```c
//【正例】被编译器优化为Hardware Loop  
//嵌套循环  
for (uint16_t i = 0; i < LoopBound; i++) {  
    for (uint16_t j = 0; j < LoopBound; j++) {  
        for (uint16_t k = 0; k < LoopBound; k++) {  
            for (uint16_t m = 0; m < LoopBound; m++) {  
                // ...  
            }  
        }  
    }  
}  
//【反例】无法被编译器优化，构成Software Loop  
for (uint16_t i = 0; i < LoopBound; i++) { // Software Loop，循环内包含了if判断  
        if(){  
            }  
}  
for (uint16_t i = 2; i < LoopBound*3; i+=2) { // Software Loop，循环起始值不为0，循环步长不为1 
```

...} 

# 循环内成员变量访问优化

在一个VF内，不推荐直接访问类的成员变量。直接访问类的成员变量相当于从栈上把 内容搬运到Tensor寄存器中，之后通过地址访问Tensor上的内容，该操作将导致VF融 合失效，建议通过局部变量临时传参解决，示例如下： 

```cpp
//【反例】直接读取成员变量
__aicore__inline void SoftMaxGenericNDlmpVF(_ubuf__float* dstAddr, _ubuf__float* sumAddr, _ubuf__float* maxAddr,
__ubuf__float* srcAddr, _ubuf__float* workAddr, const LastAxisShapeND originalSrcShape, const SoftMaxTiling tiling)
{
    for (uint16_t i = 0; i < (uint16_t) tiling.srcM; i++) {
        AscendC::ReduceMax(maxAddr + i * FLOAT_NUM_PER_BLK, srcAddr + i * tiling.srcK, workAddr,
            (uint16_t)originalSrcShape.k);
    }
}
//【正例】通过局部变量传递VF内访问的成员变量
__aicore__inline void SoftMaxGenericNDlmpVF(_ubuf__float* dstAddr, _ubuf__float* sumAddr, _ubuf__float* maxAddr,
__ubuf__float* srcAddr, _ubuf__float* workAddr, const LastAxisShapeND originalSrcShape, const SoftMaxTiling tiling)
{
    uint16_t srcK = tiling.srcK;
    uint16_t srcM = tiling.srcM;
    uint16_t reduceK = FLOAT_NUM_PER_BLK;
    uint16_t originK = (uint16_t)originalSrcShape.k;
    for (uint16_t i = 0; i < (uint16_t) srcM; i++) {
        AscendC::ReduceMax(maxAddr + i * reduceK, srcAddr + i * srcK, workAddr, originK);
    }
} 
```

# 循环内指令分布优化

减少Loop循环内非索引相关语句。for循环中存在与索引无关的语句可以提出for循环外 来减少指令数。 

```cpp
//【反例】Duplicate语句放在for循环中，每次循环都会执行一次  
template<typename T>  
__simd_vf__inline void DuplicateVF(_ubuf_T* dstAddr, T scalarValue, uint32_t oneRepeatSize, uint16_t repeatTimes)  
{  
    AscendC::Reg::RegTensor<T> dstReg;  
    AscendC::Reg::MaskReg mask = AscendC::Reg::CreateMask<T>();  
    for (uint16_t i = 0; i < repeatTimes; i++) {  
        AscendC::Reg::DuplicatedstReg, scalarValue);  
        AscendC::Reg::StoreAligndstAddr + i * oneRepeatSize, dstReg, mask);  
    }  
}  
//【正例】Duplicate放在for循环外，仅执行一次，有效减少指令数  
template<typename T>  
__simd_vf__inline void DuplicateVF(_ubuf_T* dstAddr, T scalarValue, uint32_t oneRepeatSize, uint16_t repeatTimes)  
{  
    AscendC::Reg::RegTensor<T> dstReg;  
    AscendC::Reg::MaskReg mask = AscendC::Reg::CreateMask<T>();  
    AscendC::Reg::DuplicatedstReg, scalarValue);  
    for (uint16_t i = 0; i < repeatTimes; i++) {  
        AscendC::Reg::StoreAligndstAddr + i * oneRepeatSize, dstReg, mask);  
    }  
} 
```

# 循环内地址管理优化

在VF循环中，当使用搬运指令时，需要计算搬入和搬出的地址偏移量，由此会引入较 多的标量计算开销。在Atlas 350 加速卡中，通过引入地址寄存器，可有效优化地址偏 移量的计算。当满足如下的地址寄存器生成模式时，编译器有机会生成地址寄存器， 从而消除相关的Scalar计算消耗，提升整体性能。 

其中，地址寄存器最多支持4层循环寻址，如下图所示。 

![](images/36e481797309764d0f63e38679d378c2229983a5be3d389c7a15caacc9fcf339.jpg)


如下是一个满足地址寄存器生成模式的代码示例，源操作数地址按照上图的方式进行 最多四维的寻址： 

```cpp
for uint16_t i = 0; i < extent1; i++) {
    for uint16_t j = 0; j < extent2; j++) {
        for uint16_t k = 0; k < extent3; k++) {
            for uint16_t m = 0; m < extent4; m++) {
                AscendC::Reg::LoadAlign(srcReg, srcAddr + i * const1 + j * const2 + k * const3 + m * const4);
            }
        }
} 
```

编译器会将以上模式优化为使用AddrReg进行地址管理，优化为以下模式： 

```cpp
AscendC::Reg::AddrReg aReg;  
for uint16_t i = 0; i < extent1; i++) {  
    for (uint16_t j = 0; j < extent2; j++) {  
        for (uint16_t k = 0; k < extent3; k++) {  
            for (uint16_t m = 0; m < extent4; m++) {  
                aReg = AscendC::Reg::CreateAddrReg(i, const1, j, const2, k, const3, m, const4);  
                AscendC::Reg::LoadAlign(srcReg, srcAddr, aReg);  
            }  
        }  
} 
```

编译器通过识别LoadAlign、StoreAlign等指令进行模式匹配，当代码结构满足特定优 化模式时，编译器将有机会进行高效优化，从而获得最佳的性能收益。相反，若直接 使用AddrReg存储偏移量或其它底层接口，可能会限制编译器的全局优化能力。 

特别地，当四层循环构成连续访问场景时，地址管理可被简化为一维模式，从而实现 更高效的搬运优化，进一步提升数据访问的局部性和执行效率。 

```txt
//使能向量地址生成指令优化_simd_vf__inline void ComputeModeVF(_ubuf_T\* dstAddr,_ubuf_T\* srcAddr, uint32_t oneRepeatSize, uint16_t repeatTimes)   
{ AscendC::Reg::RegTensor<T> dstReg; 
```

AscendC::Reg::MaskReg mask $=$ AscendC::Reg::CreateMask<T>(); for (uint16_t i = 0; i <repeatTimes; ++i){ AscendC::Reg::LoadAlign.dstReg,srcAddr+i\*oneRepeatSize); AscendC::Reg::StoreAlign.dstAddr,dstReg,i\*oneRepeatSize,mask); }   
} 

# 3.8.6.4.2 指令双发优化

指令双发指的是处理器在同一个时钟周期内，能够同时发射两条指令到执行单元进行 处理。这种能力需要满足以下两个条件： 

两条指令之间没有数据上的依赖关系（依赖关系指后一条指令需要使用前一条指 令产生的结果） 

硬件中拥有足够的执行资源 

这种机制可以在不改变程序逻辑的前提下，提升处理器在单位时间内的指令处理效 率，是实现指令级并行的重要基础之一。 

如下示例中，VLoop-1循环16次，由于每个循环内的4条指令有数据依赖，所以执行队 列的深度是64。64条指令并发执行顺序如下图所示，LoadAlign_0和LoadAlign_1没有 依赖关系，可以并发执行。黑框选中的位置仅代表该4条指令有同时执行的资格，真正 执行时是乱序选取其中的2条执行。 

```cpp
for (uint16_t i = 0; i < 16; ++i) { // VLoop-1
// 循环16次，每次4条指令
// 数据依赖性：Adds依赖LoadAlign, Mul依赖Adds ...
mask = AscendC::Reg::UpdateMask<T>(count);
int16_t scalar = 2;
AscendC::Reg::LoadAlign(srcReg, src0Addr + i * oneRepeatSize);
AscendC::Reg::Adds.dstReg1, srcReg, scalar, mask);
AscendC::Reg::Mul.dstReg2, dstReg1, srcReg, mask);
AscendC::Reg::StoreAlign.dstAddr + i * oneRepeatSize, dstReg2, mask);
} 
```


图3-122 执行队列和指令的执行顺序


![](images/c05745aa711950c7ab1dba5cf01995971f5643a05cdb7cf41c4656911481f7be.jpg)


在编写算子时，开发者通常习惯于按“加载数据 → 处理计算 → 存储结果”的顺序来 组织代码流程。这种写法在寄存器资源充足时运行良好，但一旦资源紧张，问题就会 被放大。当多个计算指令之间会产生依赖关系，这些等待会堆积在执行队列中，导致 后续指令无法及时发射。 

开发者在编程时应尽可能保证队列里存在数目充足且无依赖的并发指令，从而高效的 利用硬件双发特性。可以通过合理拆分VF循环以及手动控制循环展开等方案来提高性 能。 

# 合理拆分 VF 循环

VF并不是写的越长，把所有运算都放在一个for循环内就好，需要适当的搬出中间结果 到UB，减少数据依赖。 

# 优化前：

```cpp
for (uint16_t i = 0; i < 32; ++i) { // VLoop-1
// 数据依赖性：每一条Adds的输入都依赖上一条Adds的结果
mask = AscendC::Reg::UpdateMask<T>(count);
AscendC::Reg::LoadAlign(srcReg0, src0Addr + i * oneRepeatSize);
AscendC::Reg::LoadAlign(srcReg1, src1Addr + i * oneRepeatSize);
AscendC::Reg::Add.dstReg, srcReg0, srcReg1, mask);
AscendC::Reg::Adds.dstReg, dstReg, 10, mask);
AscendC::Reg::Adds.dstReg, dstReg, 10, mask);
AscendC::Reg::AddsDstReg, dstReg, 10, mask);
AscendC::Reg::AddsDstReg, dstReg, 10, mask);
AscendC::Reg::StoreAlignDstAddr + i * oneRepeatSize, dstReg, mask);
} 
```

# 优化后：

```cpp
for (uint16_t i = 0; i < 32; ++i) { // VLoop-1  
    mask = AscendC::Reg::UpdateMask<T>(count);  
    AscendC::Reg::LoadAlign(srcReg0, src0Addr + i * oneRepeatSize);  
    AscendC::Reg::LoadAlign(srcReg1, src1Addr + i * oneRepeatSize);  
    AscendC::Reg::Add.dstReg, srcReg0, srcReg1, mask);  
    AscendC::Reg::Adds.dstReg, dstReg1, 10, mask);  
    AscendC::Reg::Adds.dstReg, dstReg1, 10, mask);  
    AscendC::Reg::Adds.dstReg, dstReg1, 10, mask);  
    AscendC::Reg::StoreAlign.dstAddr + i * oneRepeatSize, dstReg, mask);  
}  
for (uint16_t i = 0; i < 32; ++i) { // VLoop-2  
    mask = AscendC::Reg::UpdateMask<T>(count);  
    AscendC::Reg::LoadAlign.dstReg, dstAddr + i * oneRepeatSize);  
    AscendC::Reg::Adds.dstReg, dstReg, 10, mask);  
    AscendC::Reg::Adds.dstReg, dstReg, 10, mask);  
    AscendC::Reg::AddsDstReg, dstReg, 10, mask);  
    AscendC::Reg::StoreAlign.dstAddr + i * oneRepeatSize, dstReg, mask);  
} 
```

# 手动控制循环拆分

如果循环内存在依赖关系过多的指令，队列没有办法同时加载进for(i = n)和for(i = n +1)的所有指令，那么即使循环之间没有依赖关系，也无法使能双发特性，指令无法并 发执行。可以通过手动展开循环，这样做有两个好处：贴近硬件乱序执行的特性，为 下发的指令创造更多执行的机会；减少指令因为寄存器资源未到位而产生的等待。 

```txt
for (uint16_t i = 0; i < 32; ++i) { // for循环间没有依赖关系：i=0,i=1可以并行执行，但是由于循环内数据依赖指令过多导致i=1的指令无法加载进行队列中 AscendC::Reg::LoadAlign(srcReg, srcAddr, offset); AscendC::Reg::Adds.dstReg0, srcReg, 10, mask); AscendC::Reg::Muls.dstReg1 dstReg0, 20, mask); ... // 超过64条有数据依赖的指令 AscendC::Reg::StoreAlign.dstAddr, dstReg1, offset, mask); } 
```

# 展开后

```cpp
for (uint16_t i = 0; i < 8; ++i) { // 32做4展开
    AscendC::Reg::LoadAlign(srcReg0, srcAddr, offset);
    AscendC::Reg::LoadAlign(srcReg1, srcAddr, offset);
    AscendC::Reg::LoadAlign(srcReg2, srcAddr, offset);
    AscendC::Reg::LoadAlign(srcReg3, srcAddr, offset);
    AscendC::Reg::Adds(...); 
```

```autohotkey
AscendC::Reg::Adds(...)
AscendC::Reg::Adds(...)
AscendC::Reg::Adds(...)
AscendC::Reg::Muls(...)
AscendC::Reg::Muls(...)
AscendC::Reg::Muls(...)
AscendC::Reg::Muls(...)
...
AscendC::Reg::StoreAlign(...)
AscendC::Reg::StoreAlign(...)
AscendC::Reg::StoreAlign(...)
AscendC::Reg::StoreAlign(...)
} 
```

# 避免寄存器数量超限，导致执行队列中依赖指令的数量增加

在同一个VF中，硬件可以同时处理的最大RegTensor寄存器个数为32，如果超出，编 译器会进行数据的换入换出并加入同步指令，严重拖慢算子的执行效率。同理，在同 一个VF中，MaskReg不超过8个，读/写UnalignRegForLoad和UnalignRegForStore各 不超过4个，否则会发生寄存器溢出，导致性能劣化。 

优化方案： 

使用布尔代数运算。比如!(a && b) 可简化为 !a || !b，!(a || b) 可以化简为 !a && !b。 

适当等价调整指令顺序，节省寄存器。 

本示例用于判断两个double类型数据是否相等，需要处理两个特殊场景，是否为NAN 或者+0和-0的场景。 

```cpp
template<typename T = Reg::DefaultType, CMPMODE mode = CMPMODE::EQ, typename RegT> _simd_caller__inline void CompareDoubleImpl(Reg::MaskReg &dstMask, RegT &srcReg0, RegT &srcReg1, Reg::MaskReg &mask) {
    using ActualT = typename RegT::ActualT;
    static_assert(SupportType<ActualT, double, uint64_t>) ("CompareDoubleImpl only support double and uint64_t type");
    Reg::RegTensor<uint64_t, Reg::RegTraitNumTwo> tmpSrcReg0 = (Reg::RegTensor<uint64_t, Reg::RegTraitNumTwo>&)srcReg0;
    Reg::RegTensor<uint64_t, Reg::RegTraitNumTwo> tmpSrcReg1 = (Reg::RegTensor<uint64_t, Reg::RegTraitNumTwo>&)srcReg1;
    Reg::RegTensor<uint64_t, Reg::RegTraitNumTwo> exponent0;
    Reg::RegTensor<uint64_t, Reg::RegTraitNumTwo> exponent1;
    Reg::ShiftRights(exponent0, tmpSrcReg0, static_cast<int16_t>(52), mask);
    Reg::ShiftRights(exponent1, tmpSrcReg1, static_cast<int16_t>(52), mask);
    Reg::RegTensor<uint64_t, Reg::RegTraitNumTwo> scalarExponent;
    Reg::Duplicate(SCalarExponent, static_cast<uint64_t>(0x7ff), mask);
    Reg::And(exponent0, exponent0, scalarExponent, mask);
    Reg::And(exponent1, exponent1, scalarExponent, mask);
    Reg::RegTensor<uint64_t, Reg::RegTraitNumTwo> mantissa0, mantissa1;
    Reg::RegTensor<uint64_t, Reg::RegTraitNumTwo> scalarMantissa;
    Reg::Duplicate(SCalarMantissa, static_cast<uint64_t>(0xFFFFFF), mask);
    Reg::And(mantissa0, tmpSrcReg0, scalarMantissa, mask);
    Reg::And(mantissa1, tmpSrcReg1, scalarMantissa, mask);
    Reg::MaskReg tmpMask0, tmpMask1;
    Reg::Compares(tmpMask0, exponent0, 0x7ff, mask);
    Reg::Compares.dstMask, exponent1, 0x7ff, mask);
    Reg::MaskAnd.dstMask, tmpMask0, dstMask, mask);
    // dstMask表示两个double数的尾数不同时为0，需要先判断两个数的尾数部分是否不为0，全为0时为0，再进行或运算，tmpMask为1表示两个数不同时为0 
```

```cpp
Reg::MaskReg tmpMask1; Reg::Compares<uint64_t,CMPMODE::NE>(tmpMask1,mantissa0,0,mask); Reg::Compares<uint64_t,CMPMODE::NE>(tmpMask0,mantissa1,0,mask); Reg::MaskOr(tmpMask0, tmpMask1, tmpMask0, mask); //【反例】判断指数全为1，尾数不同时为0（结果为NAN）的特殊情况，用到的公式为!(a&&b)，需要多申请一个MaskReg即noNaNMask来记录a&&b中间结果 Reg::MaskReg noNaNMask; Reg::MaskAnd(noNaNMask, dstMask, tmpMask0, mask); Reg::MaskNot(noNaNMask, noNaNMask, mask); //判断+0和-0的特殊情况 Reg::RegTensor<uint64_t, Reg::RegTraitNumTwo> unsignedPart0, unsignedPart1; Reg::RegTensor<uint64_t, Reg::RegTraitNumTwo> scalarUnsignedPart; Reg::Duplicate(scalarUnsignedPart, static_cast<uint64_t>(0x7FFFFFF), mask); Reg::And(unsignedPart0, tmpSrcReg0, scalarUnsignedPart, mask); Reg::And(unsignedPart1, tmpSrcReg1, scalarUnsignedPart, mask); //【反例】先分别判断两个无符号数是否为0，接着对结果进行与运算，可以通过将判断unsignedPart1是否为0的mask换成tmpMask，可以节省一条MaskAnd指令 Reg::Compares<uint64_t,CMPMODE::EQ>(tmpMask0, unsignedPart0, 0,mask); Reg::Compares<uint64_t,CMPMODE::EQ>(dstMask, unsignedPart1, 0,mask); Reg::MaskAnd(tmpMask0, tmpMask0, dstMask, mask); Reg::Compare.dstMask, tmpSrcReg0, tmpSrcReg1, mask); Reg::MaskAnd.dstMask, dstMask, noNaNMask, mask); Reg::MaskOr.dstMask, dstMask, tmpMask0, mask); } 
```


优化后：


```cpp
template<typename T = Reg::DefaultType, CMPMODE mode = CMPMODE::EQ, typename RegT> _simd_caller inline void CompareDoubleImpl(Reg::MaskReg &dstMask, Reg &srcReg0, Reg &srcReg1, Reg::MaskReg &mask) {
    using ActualT = typename RegT::ActualT;
    static_assert(SupportType<ActualT, double, uint64_t>) ("CompareDoubleImpl only support double and uint64_t type");
    Reg::RegTensor<uint64_t, Reg::RegTraitNumTwo> tmpSrcReg0 = (Reg::RegTensor<uint64_t, Reg::RegTraitNumTwo>&) srcReg0;
    Reg::RegTensor<uint64_t, Reg::RegTraitNumTwo> tmpSrcReg1 = (Reg::RegTensor<uint64_t, Reg::RegTraitNumTwo>&) srcReg1;
    Reg::RegTensor<uint64_t, Reg::RegTraitNumTwo> exponent0;
    Reg::RegTensor<uint64_t, Reg::RegTraitNumTwo> exponent1;
    Reg::ShiftRights(exponent0, tmpSrcReg0, static_cast<int16_t>(52), mask);
    Reg::ShiftRights(exponent1, tmpSrcReg1, static_cast<int16_t>(52), mask);
    Reg::RegTensor<uint64_t, Reg::RegTraitNumTwo> scalarExponent;
    Reg::Duplicate(SCalarExponent, static_cast<uint64_t>(0x7ff), mask);
    Reg::And(exponent0, exponent0, scalarExponent, mask);
    Reg::And(exponent1, exponent1, scalarExponent, mask);
    Reg::RegTensor<uint64_t, Reg::RegTraitNumTwo> mantissa0, mantissa1;
    Reg::RegTensor<uint64_t, Reg::RegTraitNumTwo> scalarMantissa;
    Reg::Duplicate(SCalarMantissa, static_cast<uint64_t>(0xFFFFFFaaaa), mask);
    Reg::And(mantissa0, tmpSrcReg0, scalarMantissa, mask);
    Reg::And(mantissa1, tmpSrcReg1, scalarMantissa, mask);
    Reg::MaskReg tmpMask0, tmpMask1;
    Reg::Compares(tmpMask0, exponent0, 0x7ff, mask);
    Reg::Compares.dstMask, exponent1, 0x7ff, tmpMask0);
    Reg::MaskNot.dstMask, dstMask, mask);
    Reg::Compares<uint64_t, CMPMODE::EQ>(tmpMask1, mantissa0, 0, mask);
    Reg::Compares<uint64_t, CMPMODE::EQ>(tmpMask0, mantissa1, 0, tmpMask1);
    //【正例】!(a&&b)化简为 !a||!b，表示指数不全为1或者tmpMask0均为0时候，可以正常进行判断，不需要申请寄存器
    Reg::MaskOr(tmpMask0, tmpMask0, dstMask, mask);
    Reg::Compare(tmpMask, tmpSrcReg0, tmpSrcReg1, mask);
    Reg::MaskAnd(tmpMask, dstMask, tmpMask0, mask);
    //+0-0
    Reg::RegTensor<uint64_t, Reg::RegTraitNumTwo> unsignedPart0, unsignedPart1;
    Reg::RegTensor<uint64_t, Reg::RegTraitNumTwo> scalarUnsignedPart; 
```

```cpp
Reg::Duplicate(SCalarUnsignedPart, static cast<uint64_t>(0x7FFFFFF), mask); Reg::And(unsignedPart0, tmpSrcReg0, scalarUnsignedPart, mask); Reg::And(unsignedPart1, tmpSrcReg1, scalarUnsignedPart, mask); //【正例】这里将unsignedPart1判断后的mask替换为tmpMask0，相当于unsignedPart0，unsignedPart1分别判断完后再进行与运算，相较于反例省略了一条MaskAnd指令。 Reg::Compares<uint64_t,CMPMODE::EQ>(tmpMask0, unsignedPart0, 0, mask); Reg::Compares<uint64_t,CMPMODE::EQ>(tmpMask1, unsignedPart1, 0, tmpMask0); Reg::MaskOr.dstMask, dstMask, tmpMask0, mask); } 
```

# 3.8.6.4.3 连续非对齐场景优化

# 连续非对齐搬运优化建议

优先采用连续对齐搬运以避免额外开销，提升整体性能。 

由于硬件支持限制，连续非对齐搬运时不建议使用AddrReg存储偏移量，推荐使 用uint32_t类型存储偏移量，使用post update模式搬运，该场景下每次调用接口 自动更新源操作数在UB上的地址。后续的优化建议均基于此场景展开。 

连续非对齐搬入时，每次将UB数据搬运至RegTensor后，非对齐寄存器会缓存后 续非对齐数据，下一次搬运时非对齐寄存器中的数据会写入RegTensor，因此连续 非对齐搬入初始化仅需执行一次，应移至for循环外部。 

连续非对齐搬出时，每次将RegTensor数据搬运至UB后，非对齐寄存器会缓存后 续非对齐数据，下一次搬运时非对齐寄存器中缓存的数据将写入UB，因此连续非 对齐搬出后处理只需执行一次，应移至for循环外部。 

# 【正例】

```cpp
//非对齐搬入初始化，使用uint32_t管理偏移量，移至for循环外部。  
AscendC::Reg::LoadUnAlignPre(ureg0, srcAddr);  
for (uint16_t i = 0; i < repeatTimes; ++i) {  
    AscendC::Reg::LoadUnAlign(srcReg, ureg0, srcAddr + i * postUpdateStride);  
    AscendC::Reg::StoreUnAlign.dstAddr, srcReg, ureg1, postUpdateStride);  
}  
//非对齐搬出后处理，移至for循环外部。  
AscendC::Reg::StoreUnAlignPost.dstAddr, ureg1, 0); 
```

# 【反例】

```cpp
for (uint16_t i = 0; i < repeatTimes; ++i) { AscendC::Reg::LoadUnAlignPre(ureg0, srcAddr + i * postUpdateStride); AscendC::Reg::LoadUnAlign(srcReg, ureg0, srcAddr + i * postUpdateStride); AscendC::Reg::StoreUnAlign.dstAddr, srcReg, ureg1, postUpdateStride); AscendC::Reg::StoreUnAlignPost.dstAddr, ureg1, 0); } 
```

# 连续非对齐搬运接口介绍

为提升对不规则内存地址的处理能力，Reg矢量计算支持在数据搬运过程中对非32字 节对齐的地址进行访问，适用于从UB向RegTensor非对齐搬运，或从RegTensor向UB 非对齐搬运的场景。为降低非对齐访问带来的性能开销，RegBase引入非对齐寄存器 缓存机制，该机制利用非对齐寄存器UnalignRegForLoad和UnalignRegForStore作为 临时缓存区，用于暂存跨对齐边界的数据，从而实现高效的连续非对齐数据传输。 

在读非对齐地址前，应该先通过LoadUnAlignPre进行初始化，然后再使用 LoadUnAlign。在写非对齐地址时，先使用StoreUnAlign，再使用StoreUnAlignPost 进行后处理。使用uint32_t管理偏移量的搬入搬出接口和maskReg搬出接口如下： 

连续非对齐搬入，使用uint32_t存储搬运量 _simd_callee__ inline void LoadUnAlignPre(UnalignRegForLoad& ureg, __ubuf__ T* srcAddr); _simd_callee__ inline void LoadUnAlign(U& dstReg, UnalignRegForLoad& ureg, __ubuf__ T*& srcAddr, uint32_t postUpdateStride); 

连续非对齐搬出，使用uint32_t存储偏移量 

__simd_callee__ inline void StoreUnAlign(__ubuf__ ${ \sf T } ^ { \star } { \& }$ dstAddr, U& srcReg, UnalignRegForStore& ureg, uint32_t postUpdateStride); __simd_callee__ inline void StoreUnAlignPost(__ubuf__ ${ \sf T } ^ { \star } { \& }$ dstAddr, UnalignRegForStore& ureg, int32_t postUpdateStride); 

连续非对齐搬出，将maskReg搬出至UB 

__simd_callee__ inline void StoreUnAlign(__ubuf__ T*& dstAddr, MaskReg& mask, UnalignRegForStore& ureg); __simd_callee__ inline void StoreUnAlignPost(__ubuf__ ${ \sf T } ^ { \star } { \& }$ dstAddr, UnalignRegForStore& ureg, int32_t postUpdateStride); 

# 非对齐寄存器原理

本节主要介绍在非对齐搬运过程中，非对齐寄存器如何发挥其作用，并详细解释内部 原理，帮助开发者理解为什么上文的性能优化建议能够带来性能收益。首先介绍连续 非对齐数据搬入、连续非对齐数据搬出以及MaskReg连续非对齐数据搬出的实现原 理，然后通过一个具体的搬入搬出例子将这些关键流程串接起来。 

# 非对齐数据搬入

如下图所示，从UB地址srcAddr ~ 304读取数据，并将其搬运至目标寄存器dstReg （256B）。处理流程如下： 

调用LoadUnAlignPre进行非对齐搬入初始化。非对齐寄存器ureg缓存UB地 址32 ~ 64的有效数据，作为后续非对齐访问的前置数据缓存。 

调用LoadUnAlign，硬件指令将UB地址64 ~ 320的数据搬入临时寄存器 tmpReg，并将ureg中srcAddr ~ 64对应的数据与tmpReg中地址64 ~ 304对 应的数据拼接在一起，将结果写入dstReg。本次搬运后，UB地址288 ~ 320 的数据会被写入ureg。连续非对齐搬入时，由于LoadUnAlign会将后续未对 齐的数据缓存至ureg，所以下一次搬入不需要再次调用LoadUnAlignPre，只 需在第一次搬入前调用一次LoadUnAlignPre，从而实现非对齐搬入的性能优 化。 


图 3-123 非对齐数据搬入


![](images/6999cb663a4567aa4cfe895f7b19cdb39bc4cf5ef4807794bc6ab0150ae7fd24.jpg)


# 非对齐数据搬出

将源寄存器srcReg中的非对齐数据写入UB地址dstAddr，根据ureg当前状态，分 为两种场景： 

# 场景一：ureg为空

调用StoreUnAlign，此时ureg内无有效数据，表示连续非对齐搬出的起始状 态，将srcReg中对应UB地址48 ~ 288的数据写入dstAddr，同步将srcReg中 对应UB地址288 ~ 320的数据缓存至ureg。 

调用StoreUnAlignPost进行非对齐搬出后处理。将ureg中缓存的UB地址288 ~ 320对应的有效数据写入UB。 


图 3-124 非对齐数据搬出（ureg 为空）


![](images/d0fb0de41207b6f677a30277fd1459e76ab274addea838b7dfd27392c9f37a69.jpg)


# 场景二：ureg不为空

调用StoreUnAlign，此时ureg内有有效数据，系统将ureg中UB地址32 ~ dstAddr对应的数据与srcReg中UB地址dstAddr ~ 288对应的数据进行拼接， 结果写入UB地址dstAddr。同步将srcReg中对应UB地址288 ~ 320的数据缓存 至ureg。连续非对齐搬出时，由于当ureg不为空时，下一次StoreUnAlign会 读本次StoreAUnlign缓存至ureg中数据，所以本次搬出不需调用 StoreUnAlignPost，只需在搬出后调用一次StoreUnAlignPost，从而实现非 对齐搬出的性能优化。 

调用StoreUnAlignPost进行非对齐搬出后处理。将ureg中缓存的UB地址288 ~ 320对应的有效数据写入UB。 


图 3-125 非对齐数据搬出（ureg 不为空）


![](images/581a14cb339ba20b01b8d1f476a759684960b04f6e742b18b8552903c186ce1c.jpg)


# MaskReg连续非对齐数据搬出

将源寄存器MaskReg（32B）搬出至UB。 

UB地址上数据类型为b16时，硬件指令从每个2位数据中提取最低有效位 （LSB），将MaskReg中32B数据打包成16B，写入UB。搬运完成后UB地址 按16B偏移量更新。 

UB地址上数据类型为b32时，硬件指令从每个4位数据中提取最低有效位 （LSB），将MaskReg中32B数据打包成8B，写入UB。搬运完成后UB地址按 8B偏移量更新。 

以UB地址上数据类型为b16为例，将两个MaskReg数据写入dstAddr ~ 72，按以 下步骤进行非对齐搬出： 

将maskReg1压缩后的16B数据（UB地址dstAddr ~ 56）缓存至ureg。 

将ureg中的数据与maskReg2压缩后的16B数据的部分数据（UB地址56 ~ 64）进行拼接，结果写入UB地址dstAddr ~ 64。 

– 将maskReg2压缩后的16B数据的部分数据（UB地址64 ~ 72）缓存至ureg。 

非对齐搬出后处理。将ureg中缓存的数据写入UB地址64 ~ 72。MaskReg连 续非对齐搬出与RegTensor连续非对齐搬出类似，只需在搬出后调用一次 StoreUnAlignPost，实现MaskReg连续非对齐搬出的性能优化。 


图 3-126 MaskReg 连续非对齐数据搬出


![](images/e2de6a38baee8911cbf8f4f334c6fac780bb33a43c9d0f735b9a6b1d0bd984bd.jpg)


# 连续非对齐搬入搬出示例

如下图，将UB地址48 ~ 560的uint32_t数据[1, 2, 3, ... , 128]搬入至dstReg，再搬 回UB，需要两次搬入搬出操作，即for循环执行两次，初始化和后处理移至for循 环外。 

a. 非对齐搬入初始化：更新ureg1 $=$ [1, 2, 3, 4]； 

b. 非对齐搬入：tmpReg $=$ [5, 6, 7, ... , 68]，tmpReg部分数据和ureg1数据写入 dstReg $=$ [1, 2, 3, ... , 64]，更新ureg1 $=$ [61, 62, 63, ... , 68]; 

c. 非对齐搬出：dstReg部分数据[1, 2, 3, ... , 60]写入UB地址48 ~ 288，更新 ureg2 $=$ [61, 62, 63, 64]； 

d. 非对齐搬入：tmpReg $=$ [69, 70, 71, ... ,128]，tmpReg数据和ureg1部分数据 写入dstReg $= [ 6 5 ,$ $=$ 66 67, ... , 128]； 

e. 非对齐搬出：ureg2数据[61, 62, 63, 64]和dstReg部分数据[65, 66, 67, ... ,124]写入UB地址 $2 8 8 \sim 5 4 4$ ，更新ureg2 $=$ [125, 126, 127, 128]； 

f. 非对齐搬出后处理：将ureg2中缓存的数据[125, 126, 127, 128]写入UB地址 $5 4 4 \sim 5 6 0$ 。 


图 3-127 连续非对齐搬入搬出


![](images/f06ae8915bea6c70ba27f474b5469c279b5e6b6b6cd5028bd3cb253d31aa7626.jpg)


# 3.8.6.4.4 VF 融合优化

# 【优先级】高

【描述】VF融合是将代码中多个VF函数融合成一个VF函数，有效提升性能。VF融合特 性是优化特性，VF自动融合会借助Loop Fuse算法，将VF转换成Loop形态，然后将控 制流等价（Control-Flow-Equivalent）的VF进行融合，最后将VF进行还原。编译器首 先会做融合前的合法性检查，判断两个VF是否等价，Main侧中间代码是否能在VF内执 行以及融合后是否可产生正收益（不会引起传参寄存器溢出、VF代码不会过大）等， 如果满足VF融合条件，编译器会自动执行VF融合优化，为保证融合后的VF执行逻辑与 语义与融合前一致，会在原来两个VF之间保守地插入同步指令，编译器还会尝试外 提、合并融合后的VF中的指令，对VF代码进行优化。融合策略是能融尽融，用户按照 符合融合的合法性检查的模式进行编码，可以增加VF融合的机会。 

# VF 融合原理介绍

VF融合优化可分为三个阶段：VF浅度融合、VF深度融合和VF内自动同步： 

VF浅度融合：编译器首先会分析两个VF的控制流是否等价，构建Cost Model分析是否 有正向收益，如果满足VF融合条件，将VF外部的控制流融入到VF内，将VF外的 Software Loop硬化成VF内的Hardware Loop，然后使能VF自动融合的基础能力，将 两个VF融合成一个VF，为后续的VF深度融合提供基础。 

![](images/3ffdb246e993d2705b5d71ec99d4557f2a4bba39397fbd88c11c46fc34ef5f60.jpg)


VF深度融合：VF深度融合会继续对VF内的Hardware Loop进行融合，从而减少 Hardware Loop的启动开销，并且极大地减少冗余的Load/Store操作，充分复用寄存 器。 

![](images/a126febc7180ff7859397bfdd56a840b2d7b304237f8fd9de6ba90489c0399af.jpg)


VF内自动同步：编译器会精准地插入必要的同步指令，删除冗余的同步指令，极大地 释放了硬件OOO（Out of Order）能力。用户无需手动插入同步指令，极大地降低了 用户的编码难度。 

# VF 融合编写指导

1. 多个VF函数自动融合：如果多个VF函数的控制流等价，且满足均为Hardware Loop循环，编译器会执行VF融合优化特性。 

【正例】VF函数DivVF和AddVF会被编译器融合成一个VF函数，并且能优化多余 的Load/Store指令。 

```cpp
template<typename T> _simd_vf__inline void DivVF(_ubuf_T* dstAddr, _ubuf_T* srcAddr, uint32_t count, uint32_t repeatTime, uint32_t oneRepNum) {
    AscendC::Reg::MaskReg mask;
    AscendC::Reg::RegTensor<T> reg0, reg1, reg2;
    constexpr float num = 1.0f;
    for (uint16_t j = 0; j < repeatTime; ++j) {
        mask = AscendC::Reg::UpdateMask<T>(count);
        AscendC::Reg::LoadAlign(reg0, srcAddr + j * oneRepNum);
        AscendC::Reg::Duplicate(reg1, num, mask);
        AscendC::Reg::Div(reg2, reg1, reg0, mask);
        AscendC::Reg::StoreAlign.dstAddr + j * oneRepNum, reg2, mask);
    }
} template<typename T> _simd_vf__inline void AddVF(_ubuf_T* dstAddr, _ubuf_T* srcAddr, uint32_t count, uint32_t repeatTime, uint32_t oneRepNum) {
        AscendC::Reg::MaskReg mask;
        AscendC::Reg::RegTensor<T> srcReg;
        AscendC::Reg::RegTensor<T> dstReg;
        constexpr float num = 1.0f;
        for (uint16_t j = 0; j < repeatTime; ++j) {
            mask = AscendC::Reg::UpdateMask<T>(count);
            AscendC::Reg::LoadAlign(srcReg, srcAddr + j * oneRepNum);
            AscendC::Reg::Adds.dstReg, srcReg, num, mask);
            AscendC::Reg::StoreAlign.dstAddr + j * oneRepNum, dstReg, mask);
        }
} template<typename T> class Kernel {
public:
    __aicore__inline Kernel() = default;
    __aicore__inline void Init(GM_ADDR x, GM_ADDR y, uint32_t count, AscendC::TPipe* pipeline) {
        // ...
    }
    __aicore__inline void Copyln(){
        // ...
    }
} __aicore__inline void Compute(){
    AscendC::LocalTensor<T> xLocal = inQueueX.DeQue<T>();
    AscendC::LocalTensor<T> yLocal = outQueueY AllocTensor<T>();
    AscendC::DataCopy(yLocal, xLocal, count);
    __ubuf_T* srcAddr = reinterpret_cast<_ubuf_T*>(xLocal.GetPhyAddr());
} 
```

```cpp
\ubuf_T* dstAddr = reinterpret_cast<T>(yLocal.GetPhyAddr());
constexpr uint32_t oneRepNum = 256 / sizeof(T);
uint32_t repeatTime = count / oneRepNum;
DivVF.dstAddr, srcAddr, count, repeatTime, oneRepNum);
AddVF.dstAddr, dstAddr, count, repeatTime, oneRepNum);
outQueueY.EnQue<T>(yLocal);
}
aicoreINLINE void CopyOut(){
// ...
} aicoreINLINE void Process(){
Copyln();
Compute();
CopyOut();
}
private:
AscendC::TPipe* pipe = nullptr;
uint32_t count;
AscendC::GlobalTensor<T> xGm;
AscendC::GlobalTensor<T> yGm;
AscendC::TQue<AscendC::TPosition::VECIN, 1> inQueueX;
AscendC::TQue<AscendC::TPosition::VECOUT, 1> outQueueY;
}; 
```

2. 使用基础API连续计算模式：基础API实现对硬件能力的抽象，开放芯片的能力， 保证完备性和兼容性。基础API根据对数据操作方法的不同，可以分为两大类： 

连续计算API：支持Tensor前n个数据计算。针对源操作数的连续n个数据进行 计算并连续写入目的操作数，解决一维tensor的连续计算问题。 

高维切分API：支持Repeat和Stride。功能灵活的计算API，提供与Builtin API 完全对等的编程能力，充分发挥硬件优势，支持对每个操作数的DataBlock Stride，Repeat Stride，Mask等参数的操作。 

在VF融合优化中，推荐使用基础API的连续计算模式编写算子，可以充分发挥出 VF融合优化的能力，与高维切分API相比，连续计算API使得编译器能更好地分析 VF融合优化，更加容易满足VF融合优化的条件，使用基础API的连续计算模式能 写出性能更优的算子。 

【反例】使用基础API的高维切分模式编写算子，编译器在分析VF融合时受复杂的 计算逻辑影响，无法对Add和Mul接口进行VF融合优化。 

```cpp
template<typename T>   
class Kernel {   
public: // ...  
    __aicore__inline void Compute() { AscendC::LocalTensor<T> xLocal = inQueueX.DeQue<T>(); AscendC::LocalTensor<T> yLocal = outQueueY AllocTensor<T>(); AscendC::DataCopy(yLocal, xLocal, inner * outter); uint64_t mask = 128; AscendC::Add(yLocal, xLocal, xLocal, mask, 4, {1, 1, 1, 8, 8, 8}); AscendC::Mul(yLocal, yLocal, xLocal, mask, 4, {1, 1, 1, 8, 8, 8}); outQueueY.EnQue<T>(yLocal); } // ...   
}; 
```

【正例】使用基础API的连续计算模式，编译器分析Add和Mul函数后符合VF融合 要求，将Add和Mul融合成一个VF函数。 

```cpp
template<typename T>   
class Kernel {   
public: // ...  
    __acore__ inline void Compute() { AscendC::LocalTensor<T> xLocal = inQueueX.DeQue<T>(); AscendC::LocalTensor<T> yLocal = outQueueY AllocTensor<T>(); AscendC::DataCopy(yLocal, xLocal, inner * outter); AscendC::Add(yLocal, xLocal, xLocal, count); 
```

```cpp
AscendC::Mul(yLocal,yLocal,xLocal,count); outQueueY.EnQue<T>(yLocal); } //...   
}； 
```

# 3.8.7 矩阵计算

# 3.8.7.1 通过 BT Buffer 实现高效的 bias 计算

【优先级】高 

【描述】算子中进行带bias的矩阵乘计算时，可将bias数据搬运至C2(Bias Table Buffer)上，调用一次Mmad接口实现矩阵乘加bias的计算，或者直接调用Matmul高阶 API完成功能。相比于先将矩阵乘的结果从CO1(L0C)搬运到GM上，再搬运到UB上进 行加bias的过程，减少了数据搬运的次数，可提升内存使用效率。数据流图对比如 下： 


图 3-128 反例数据流图


![](images/aedbf67d0636927c39321b799590bd1f527c3a4632c9b2da1333263c2786e2c0.jpg)



图3-129 正例数据流图


![](images/3b0dd3b58a73e6e8e8c9325e53d9240c8db63310dd6f37f46fff07ab2c5d56f3.jpg)


【反例】 

该算子进行带bias的矩阵乘计算时，过程如下： 

将矩阵乘的计算结果从CO1(L0C)搬运到workspace(GM)上； 

从workspace搬运到UB上； 

在UB上进行加bias的运算； 

最后将结果搬运到GM。 

当循环n次该计算过程，则分别增加了n次CO1->workspace、workspace->UB的搬 运。 

```txt
// 该样例仅做示例说明，非完整代码，省略了部分同步控制代码  
public:  
acore__inline KernelSample()  
{  
aSize = m * k;  
bSize = k * n;  
cSize = m * n;  
}  
acore__inline void Init(_gm_uint8_t *a, _gm_uint8_t *b, _gm_uint8_t *bias, _gm_uint8_t *c)  
{  
aGM.SetGlobalBuffer(_gm-half*)a);  
bGM.SetGlobalBuffer(_gm-half*)b);  
cGM.SetGlobalBuffer(_gm_float*)c);  
biasGM.SetGlobalBuffer(_gm_float*)bias);  
pipeInitBuffer(inQueueA1, 1, aSize * sizeof(full));  
pipeInitBuffer(inQueueA2, 1, aSize * sizeof(full));  
pipeInitBuffer(inQueueB1, 1, bSize * sizeof(float));  
pipeInitBuffer(inQueueB2, 2, bSize * sizeof(float));  
pipeInitBuffer(outQueueCO1, 1, cSize * sizeof(float));  
pipeInitBuffer(inQueueBias, 1, n * sizeof(float));  
pipeInitBuffer(inQueueSrc0, 1, cSize * sizeof(float));  
pipeInitBuffer(outQueueDst, 1, cSize * sizeof(float));  
}  
acore__inline void Process()  
{  
Copyln();  
SplitA();  
SplitB();  
Compute();  
CopyOut();  
Copyln1();  
Compute1();  
CopyOut1();  
}  
private:  
acore__inline void CopyIn()  
{  
LocalTensor<half> a1Local = inQueueA1 AllocTensor<half>();  
LocalTensor<half> b1Local = inQueueB1 AllocTensor<half>();  
LocalTensor<float> biasLocal = inQueueBias AllocTensor<float>();  
Nd2NzParams dataCopyA1Params;  
dataCopyA1Params.ndNum = 1;  
dataCopyA1Params.nValue = m;  
dataCopyA1Params.dValue = k;  
dataCopyA1Params.srcNdMatrixStride = 0;  
dataCopyA1Params.srcDValue = k;  
dataCopyA1Params.dstNzC0Stride = m;  
dataCopyA1Params.dstNzNStride = 1;  
dataCopyA1Params.dstNzMatrixStride = 0;  
DataCopy(a1Local, aGM, dataCopyA1Params);  
Nd2NzParams dataCopyB1Params;  
dataCopyB1Params.ndNum = 1;  
dataCopyB1Params.nValue = k;  
dataCopyB1Params.dValue = n;  
dataCopyB1Params.srcNdMatrixStride = 0;  
dataCopyB1Params.srcDValue = n;  
dataCopyB1Params.dstNzC0Stride = k;  
dataCopyB1Params.dstNzNStride = 1;  
dataCopyB1Params.dstNzMatrixStride = 0;  
DataCopy(b1Local, bGM, dataCopyB1Params);  
// 将bias搬运到UB  
DataCopy(biasLocal, biasGM, n);  
inQueueA1.EnQue(a1Local);  
inQueueB1.EnQue(b1Local);  
inQueueBias.EnQue(biasLocal); 
```

```cpp
}  
acore__inline void SplitA()  
{  
...  
}  
acore__inline void SplitB()  
{  
...  
}  
acore__inline void Compute()  
{  
LocalTensor<half> a2Local = inQueueA2.DeQue<half>();  
LocalTensor<half> b2Local = inQueueB2.DeQue<half>();  
LocalTensor<float> c1Local = outQueueCO1 AllocTensor<float>();  
MmadParams mmadParams;  
mmadParams.m = m;  
mmadParams.n = n;  
mmadParams.k = k;  
// 矩阵乘  
Mmad(c1Local, a2Local, b2Local, mmadParams); // m*n  
outQueueCO1.EnQue<c1Local>;  
inQueueA2.FreeTensor(a2Local);  
inQueueB2.FreeTensor(b2Local);  
}  
acore__inline void CopyOut()  
{  
LocalTensor<float> c1Local = outQueueCO1.DeQue<float>();  
GM_ADDR usrWorkspace = AscendC::GetUserWorkspace workspace);  
xGm.SetGlobalBuffer((gm_float*) (usrWorkspace));  
FixpipeParamsV220 fixpipeParams;  
fixpipeParams.nSize = n;  
fixpipeParams.mSize = m;  
fixpipeParams.srcStride = m;  
fixpipeParams.dstStride = n;  
fixpipeParams.ndNum = 1;  
fixpipeParams.srcNdStride = 0;  
fixpipeParams.dstNdStride = 0;  
// 将矩阵乘的计算结果从CO1搬运到workspace  
Fixpipe(xGm, c1Local, fixpipeParams);  
outQueueCO1.FreeTensor(c1Local);  
}  
acore__inline void CopyIn1()  
{  
PipeBarrier<PIPE_ALL>();  
// 将矩阵乘的计算结果从workspace搬运到UB  
LocalTensor<float> src0Local = inQueueSrc0 AllocTensor<float>();  
DataCopy(src0Local, xGm, cSize);  
inQueueSrc0.EnQue(src0Local);  
}  
acore__inline void Compute1()  
{  
LocalTensor<float> src0Local = inQueueSrc0.DeQue<float>();  
LocalTensor<float> biasLocal = inQueueBias.DeQue<float>();  
LocalTensor<float> dstLocal = outQueueDstAllocTensor<float>();  
BinaryRepeatParams addRepeatParams;  
addRepeatParams.dstRepStride = 8;  
addRepeatParams.src0RepStride = 8;  
addRepeatParams.src1RepStride = 0;  
// 加bias的运算  
AdddstLocal, src0Local, biasLocal, 32, m, addRepeatParams);  
outQueueDst.EnQue.dstLocal);  
inQueueSrc0.FreeTensor(src0Local);  
inQueueBias.FreeTensor(biasLocal);  
}  
acore__inline void CopyOut1()  
{ 
```

```cpp
TPipe pipe;  
TQue<TPosition::A1, 1> inQueueA1;  
TQue<TPosition::A2, 1> inQueueA2;  
TQue<TPosition::B1, 1> inQueueB1;  
TQue<TPosition::B2, 1> inQueueB2;  
TQue<TPosition::VECIN, 1> inQueueBias;  
TQue<TPosition::VECIN, 1> inQueueSrc0;  
TQue<TPosition::VECOUT, 1> outQueueDst;  
GlobalTensor<half> aGM;  
GlobalTensor<half> bGM;  
GlobalTensor<float> cGM;  
GlobalTensor<float> biasGM;  
uint16_t m = 32, k = 32, n = 32;  
uint16_t aSize, bSize, cSize; 
```

【正例】 

该算子进行带bias的矩阵乘计算时，先将bias搬运到BT上，调用一次Mmad接口实现矩 阵乘加bias的计算。 

```cpp
// 该样例仅做示例说明，非完整代码，省略了部分同步控制代码  
public:  
    __aicore__inline KernelSample()  
{  
        aSize = m * k;  
        bSize = k * n;  
        cSize = m * n;  
}  
    __aicore__inline void Init(gmuint8_t *a, gmmuint8_t *b, gmmuint8_t *bias, gmmuint8_t *c)  
{  
            aGM.SetGlobalBuffer((gm-half*)a);  
            bGM.SetGlobalBuffer((gm-half*)b);  
            cGM.SetGlobalBuffer((gm_float*)c);  
            biasGM.SetGlobalBuffer((gm_float*)bias);  
            pipeInitBuffer(inQueueA1, 1, aSize * sizeof(full));  
            pipeInitBuffer(inQueueA2, 1, aSize * sizeof(full));  
            pipeInitBuffer(inQueueB1, 1, bSize * sizeof(full));  
            pipeInitBuffer(inQueueB2, 2, bSize * sizeof(full));  
            pipeInitBuffer(outQueueCO1, 1, cSize * sizeof(float));  
            pipeInitBuffer(inQueueC1, 1, n * sizeof(float));  
            pipeInitBuffer(outQueueC2, 1, n * sizeof(float));  
}  
    __aicore__inline void Process()  
{  
        Copyln();  
        SplitA();  
        SplitB();  
        SplitBias();  
        Compute();  
        CopyOut();  
}  
private:  
    __aicore__inline void CopyIn()  
{  
        LocalTensor<half> a1Local = inQueueA1 AllocTensor<half>();  
        LocalTensor<half> b1Local = inQueueB1 AllocTensor<half>();  
        LocalTensor<float> bias1Local = inQueueC1 AllocTensor<float>();  
        Nd2NzParams dataCopyA1Params;  
        dataCopyA1Params.ndNum = 1;  
        dataCopyA1Params.nValue = m;  
        dataCopyA1Params.dValue = k;  
        dataCopyA1Params.srcNdMatrixStride = 0;  
        dataCopyA1Params.srcDValue = k;  
        dataCopyA1Params.dstNzC0Stride = m;  
        dataCopyA1Params.dstNzNStride = 1;  
        dataCopyA1Params.dstNzMatrixStride = 0; 
```

```txt
DataCopy(a1Local, aGM, dataCopyA1Params);  
Nd2NzParams dataCopyB1Params;  
dataCopyB1Params.ndNum = 1;  
dataCopyB1Params.nValue = k;  
dataCopyB1Params.dValue = n;  
dataCopyB1Params.srcNdMatrixStride = 0;  
dataCopyB1Params.srcDValue = n;  
dataCopyB1Params.dstNzC0Stride = k;  
dataCopyB1Params.dstNzNStride = 1;  
dataCopyB1Params.dstNzMatrixStride = 0;  
DataCopy(b1Local, bGM, dataCopyB1Params);  
//将bias从GM搬运到L1  
DataCopy(bias1Local, biasGM, n);  
inQueueA1.EnQue(a1Local);  
inQueueB1.EnQue(b1Local);  
inQueueC1.EnQue(bias1Local);  
}  
__acore__inline void SplitA()  
{  
...  
}  
__acore__inline void SplitB()  
{  
...  
}  
__acore__inline void SplitBias()  
{  
LocalTensor<float> bias1Local = inQueueC1.DeQue<float>();  
LocalTensor<float> bias2Local = outQueueC2 AllocTensor<float>();  
//将bias从L1搬运到BT  
DataCopy(bias2Local, bias1Local, {1, (uint16_t)(n * sizeof(float) / 64), 0, 0});  
outQueueC2.EnQue<float>(bias2Local);  
inQueueC1.FreeTensor(bias1Local);  
}  
__acore__inline void Compute()  
{  
LocalTensor<half> a2Local = inQueueA2.DeQue<half>();  
LocalTensor<half> b2Local = inQueueB2.DeQue<half>();  
LocalTensor<float> bias2Local = outQueueC2.DeQue<float>();  
LocalTensor<float> c1Local = outQueueCO1 AllocTensor<float>();  
MmadParams mmadParams;  
mmadParams.m = m;  
mmadParams.n = n;  
mmadParams.k = k;  
mmadParams.cmatrixInitVal = false;  
//矩阵乘  
Mmad(c1Local, a2Local, b2Local, bias2Local, mmadParams);  
outQueueCO1.EnQue<float>(c1Local);  
inQueueA2.FreeTensor(a2Local);  
inQueueB2.FreeTensor(b2Local);  
outQueueC2.FreeTensor(bias2Local);  
}  
__acore__inline void CopyOut()  
{  
LocalTensor<float> c1Local = outQueueCO1.DeQue<float>();  
FixpipeParamsV220 fixpipeParams;  
fixpipeParams.nSize = n;  
fixpipeParams.mSize = m;  
fixpipeParams.srcStride = m;  
fixpipeParams.dstStride = n;  
fixpipeParams.ndNum = 1;  
fixpipeParams.srcNdStride = 0;  
fixpipeParams.dstNdStride = 0;  
Fixpipe(cGM, c1Local, fixpipeParams);  
outQueueCO1.FreeTensor(c1Local); 
```

```cpp
private:  
TPipe pipe;  
TQue<TPosition::A1, 1> inQueueA1;  
TQue<TPosition::A2, 1> inQueueA2;  
TQue<TPosition::B1, 1> inQueueB1;  
TQue<TPosition::B2, 1> inQueueB2;  
TQue<TPosition::CO1, 1> outQueueCO1;  
TQue<TPosition::C1, 1> inQueueC1;  
TQue<TPosition::C2, 1> outQueueC2;  
GlobalTensor<half> aGM;  
GlobalTensor<half> bGM;  
GlobalTensor<float> cGM;  
GlobalTensor<float> biasGM;  
uint16_t m = 32, k = 32, n = 32;  
uint16_t aSize, bSize, cSize; 
```

# 3.8.7.2 通过 FP Buffer 存放量化参数实现高效随路量化

【优先级】高 

【描述】算子实现中对矩阵乘结果进行量化计算时，可将量化参数搬运到C2PIPE2GM （Fixpipe Buffer）上，调用一次Fixpipe接口实现矩阵乘结果的量化计算。相比于将矩 阵乘的结果从CO1（L0C）搬运到GM，再从GM搬运到UB，在UB进行量化计算的过 程，数据搬运的次数更少，内存使用效率更高。 

# 说明

本性能优化手段仅针对Atlas A2 训练系列产品/Atlas A2 推理系列产品生效。 


图 3-130 反例数据流图


![](images/893da16e9be8f579830e3d52d6feef933cc0f4000b54f55f1e50e85f4f906da5.jpg)



图3-131 正例数据流图


![](images/374005ce750a9e056b2dbf172bebc302e8eee4f9c77d27d7ffd307f536d5bf39.jpg)


【反例】 

对矩阵乘结果进行量化计算的过程如下： 

将矩阵乘的结果从CO1搬运到workspace上； 

再从workspace搬运到UB上； 

将量化参数搬运到UB上，和矩阵乘的结果一起在UB上进行一系列量化计算； 

将最终量化结果从UB搬运到GM上。 

相比于正确示例多增加了CO1->workspace、workspace->UB的搬运过程和量化的 vector计算。 

```txt
// 该样例仅做示例说明，非完整代码，省略了部分同步控制代码  
public:  
    __aicore__inline KernelSample()  
{  
        aSize = m * k;  
        bSize = k * n;  
        cSize = m * n;  
    }  
    __aicore__inline void Init(gm uint8_t *a, gm uint8_t *b, gm uint8_t *c, gm uint8_t *deqTensor)  
{  
        aGM.SetGlobalBuffer((gm half *)a);  
        bGM.SetGlobalBuffer((gm half *)b);  
        cGM.SetGlobalBuffer((gm float *)c);  
        deqGM.SetGlobalBuffer((gm half *)deqTensor);  
        pipeInitBuffer(inQueueA1, 1, aSize * sizeof(full));  
        pipeInitBuffer(inQueueA2, 1, aSize * sizeof(full));  
        pipeInitBuffer(inQueueB1, 1, bSize * sizeof(full));  
        pipeInitBuffer(inQueueB2, 2, bSize * sizeof(full));  
        pipeInitBuffer(outQueueCO1, 1, cSize * sizeof(float));  
        pipeInitBuffer(inQueueSrc0, 1, cSize * sizeof(float));  
        pipeInitBuffer(inQueueTmp, 1, cSize * sizeof(full));  
        pipeInitBuffer(inQueueDec, 1, cSize * sizeof(full));  
        pipeInitBuffer(outQueueDst, 1, cSize * sizeof(int8_t));  
}  
    __aicore__inline void Process()  
{  
        CopyIn();  
        SplitA();  
        SplitB();  
        Compute();  
        CopyOut();  
        Copyln1();  
        Compute1();  
        CopyOut1();  
}  
private:  
    __aicore__inline void CopyIn()  
{  
        LocalTensor<half> a1Local = inQueueA1 AllocTensor<half>();  
        LocalTensor<half> b1Local = inQueueB1 AllocTensor<half>();  
        LocalTensor<half> dqLocal = inQueueDecAllocTensor<half>();  
        Nd2NzParams dataCopyA1Params;  
        dataCopyA1Params.ndNum = 1;  
        dataCopyA1Params.nValue = m;  
        dataCopyA1Params.dValue = k;  
        dataCopyA1Params.srcNdMatrixStride = 0;  
        dataCopyA1Params.srcDValue = k;  
        dataCopyA1Params.dstNzC0Stride = m;  
        dataCopyA1Params.dstNzNStride = 1;  
        dataCopyA1Params.dstNzMatrixStride = 0;  
        DataCopy(a1Local, aGM, dataCopyA1Params);  
    Nd2NzParams dataCopyB1Params;  
    dataCopyB1Params.ndNum = 1;  
    dataCopyB1Params.nValue = k;  
    dataCopyB1Params.dValue = n;  
    dataCopyB1Params.srcNdMatrixStride = 0; 
```

```txt
dataCopyB1Params.srcDValue = n;  
dataCopyB1Params.dstNzC0Stride = k;  
dataCopyB1Params.dstNzNStride = 1;  
dataCopyB1Params.dstNzMatrixStride = 0;  
DataCopy(b1Local, bGM, dataCopyB1Params);  
// 将量化参数搬运到UB  
DataCopy(deqLocal, deqGM, cSize);  
inQueueA1.EnQue(a1Local);  
inQueueB1.EnQue(b1Local);  
inQueueDeq.EnQue(deqLocal);  
}  
acore__inline void SplitA()  
{  
    acore__inline void SplitB()  
{  
        acore__inline void Compute()  
{  
            LocalTensor<half> a2Local = inQueueA2.DeQue<half>();  
            LocalTensor<half> b2Local = inQueueB2.DeQue<half>();  
            LocalTensor<float> c1Local = outQueueCO1 AllocTensor<float>();  
            MpadParams mmadParams;  
            mmadParams.m = m;  
            mmadParams.n = n;  
            mmadParams.k = k;  
            // 矩阵乘  
            Mpad(c1Local, a2Local, b2Local, mmadParams); // m*noutQueueCO1.EnQue<c1Local>;  
            inQueueA2.FreeTensor(a2Local);  
            inQueueB2.FreeTensor(b2Local);  
}  
acore__inline void CopyOut()  
{  
            LocalTensor<float> c1Local = outQueueCO1.DeQue<float>();  
            GM_ADDR usrWorkspace = AscendC::GetUserWorkspace workspace);  
            xGm.SetGlobalBuffer(_gm_float*) (usrWorkspace));  
            FixpipeParamsV220 fixpipeParams;  
            fixpipeParams.nSize = n;  
            fixpipeParams.mSize = m;  
            fixpipeParams.srcStride = m;  
            fixpipeParams.dstStride = n;  
            fixpipeParams.ndNum = 1;  
            fixpipeParams.srcNdStride = 0;  
            fixpipeParams.dstNdStride = 0;  
            // 将矩阵乘的计算结果从CO1搬运到workspace  
            Fixpipe(xGm, c1Local, fixpipeParams);  
            outQueueCO1.FreeTensor(c1Local);  
}  
acore__inline void CopyIn1()  
{  
    // 将矩阵乘的计算结果从workspace搬运到UB  
    LocalTensor<float> src0Local = inQueueSrc0 AllocTensor<float>();  
    DataCopy(src0Local, xGm, cSize);  
    inQueueSrc0.EnQue(src0Local);  
}  
acore__inline void Compute1()  
{  
    LocalTensor<float> src0Local = inQueueSrc0.DeQue<float>();  
    LocalTensor<half> tmpLocal = inQueueTmpAllocTensor<half>();  
    LocalTensor<half> dqLocal = inQueueDeq.DeQue<half>();  
    LocalTensor<int8_t> dstLocal = outQueueDstAllocTensor<int8_t>();  
// 量化计算  
Cast(tmpLocal, src0Local, RoundMode::CASTNONE, cSize);  
LocalTensor<half> tmpHalfBuffer = src0Local.ReinterpretCast<half>();  
Mul(tmpHalfBuffer, tmpLocal, deqLocal, cSize); 
```

```txt
Cast.dstLocal, tmpHalfBuffer, RoundMode::CAST_NON, cSize); outQueueDst.EnQue<int8_t>(dstLocal); inQueueSrc0.FreeTensor(src0Local); inQueueTmp.FreeTensor(tmpLocal); inQueueDeq.FreeTensor(deqLocal); } __aicore__ inline void CopyOut1() { ... } private: TPipe pipe; TQue<TPosition::A1, 1> inQueueA1; TQue<TPosition::A2, 1> inQueueA2; TQue<TPosition::B1, 1> inQueueB1; TQue<TPosition::B2, 1> inQueueB2; TQue<TPosition::CO1, 1> outQueueCO1; TQue<TPosition::VECIN, 1> inQueueDecq; TQue<TPosition::VECIN, 1> inQueueSrc0; TQue<TPosition::VECCALC, 1> inQueueTmp; TQue<TPosition::VECOUT, 1> outQueueDst; GlobalTensor<half> aGM; GlobalTensor<half> bGM; GlobalTensor<float> cGM; GlobalTensor<float> biasGM; uint16_t m = 32, k = 32, n = 32; uint16_t aSize, bSize, cSize; 
```

# 【正例】

该算子对矩阵乘的结果进行量化计算时，可将量化参数搬运到FB(Fixpipe Buffer)上， 调用一次Fixpipe接口实现矩阵乘结果的量化计算。 

public: aicore__inline KernelSample() { aSize $=$ m\*k; bSize $= \mathrm{k}^{*}\mathrm{n};$ cSize $= \mathrm{m}^{*}\mathrm{n};$ QuantSize $= \mathfrak{n};$ 1 aicore__inline void Init( $\mathtt{gm\_uint8\_t}^*\mathtt{a},$ _gm_ uint8_t \*b,_gm_ uint8_t \*c,_gm_ uint8_t \*deqTensor) { aGM.SetGlobalBuffer((gm-half\*)a); bGM.SetGlobalBuffer((gm-half\*)b); cGM.SetGlobalBuffer((gm_float\*)c); deqGM.SetGlobalBuffer((gm_uint64_t\*)deqTensor); pipe.InitialBuffer(inQueueA1,1,aSize\*sizeofhalf)); pipe.InitialBuffer(inQueueA2,1,aSize\*sizeof(float)); pipe.InitialBuffer(inQueueB1,1,bSize\*sizeof(float)); pipe.InitialBuffer(inQueueB2,2,bSize\*sizeof(float)); pipe.InitialBuffer(outQueueCO1,1,cSize\*sizeof(float)); pipe.InitialBuffer(inQueueDeq1,1,Quantity\*sizeof uint64_t); pipe.InitialBuffer(inQueueDec,1,Quantity\*sizeof uint64_t); } aicore__inline void Process() { CopyIn(); SplitA(); SplitB(); SplitDeq(); Compute(); CopyOut(); } private: aicore__inline void Copyln()