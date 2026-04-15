<!-- Source: 算子开发指南.md lines 749-1449 | Section: 1.3 快速入门 -->

# 1.3 快速入门

# 1.3.1 简介

AI Core是AI处理器的计算核心，一块AI处理器通常集成多个AI Core以实现并行计算。 相比传统CPU，AI处理器更适用于模型训练与推理，这得益于其内部集成的大量计算 单元以及丰富的向量计算指令——单个硬件指令即可完成对多组数据的并行操作。 

AI处理器上主要支持以下两种编程模型： 

SIMT（Single Instruction Multiple Thread，单指令多线程）：以单条指令驱动 多个线程的形式实现并行计算。 

SIMD（Single Instruction Multiple Data，单指令多数据）：以单条指令操作多 个数据的形式实现并行计算。 

其中，SIMT编程适用于离散访存、复杂分支控制等场景下的矢量算子开发，也便于熟 悉业界SIMT算子开发的开发者快速上手Ascend C算子开发。 

SIMD编程则适用于纯矩阵计算、连续访存的矢量算子或融合算子场景。 

此外，我们还提供SIMD与SIMT混合编程方式，融合两种模型的优势，在性能与易用性 之间取得更好的平衡。 

# 1.3.2 基于 SIMD 编程

# 1.3.2.1 HelloWorld

本示例展示了如何使用Ascend C编写一个简单的"Hello World"程序，包括核函数（设 备侧实现的入口函数）的实现、调用流程以及编译运行的完整步骤。通过本示例，您 可以快速了解Ascend C的基本开发流程。完整样例请参考LINK。 

代码文件hello_world.asc包括核函数实现和主函数实现。 

核函数实现：该核函数的核心逻辑是输出"Hello World!!!"字符串。 

主函数实现：在主函数中，进行初始化环境、申请资源、通过<<<>>>调用核函数 以及释放资源等操作。完整的代码流程和逻辑可以通过代码注释查看。 

```cpp
// Host侧应用程序需要包含的头文件
#include "acl/acl.h"
// Kernel侧需要包含的头文件
#include "kernel_operator.h"
global __vector __void hello_world()
{
    AscendC::printf("Block (%lu/%lu): Hello World!!!\n", AscendC::GetBlockIdx(), AscendC::GetBlockNum());
}
int32_t main(int argc, char const *argv[])
{
    // 初始化
    acInit(nullptr);
    // 运行管理资源申请
    int32_t deviceld = 0;
    acrtSetDevice(deviceld);
    acrtStream stream = nullptr;
    acrtCreateStream(&stream);
    // 设置参与计算的核数为8（核数可根据实际需求设置）
    constexpr uint32_t numBlocks = 8;
    // 用内核调用符<<>>调用核函数
    hello_world<<numBlocks, nullptr, stream>>(); 
```

```txt
aclrtDestroyStream(stream);  
aclrtResetDevice(deviceld);  
aclFinalize();  
return 0; 
```

完成代码实现后，可以通过两种方式，对上述代码进行编译： 

# 说明

● 该样例仅支持如下型号： 

Atlas 350 加速卡 

Atlas A3 训练系列产品/Atlas A3 推理系列产品 

Atlas A2 训练系列产品/Atlas A2 推理系列产品 

● 编译命令中的--npu-arch用于指定NPU的架构版本，dav-后为架构版本号，请替换为您实际 使用的架构版本号。各AI处理器型号对应的架构版本号请通过AI处理器型号和 _NPU_ARCH__的对应关系进行查询。 

使用bisheng命令行进行编译 

```batch
bisheng hello_world.asc --npu-arch=dav-2201 -o demo ./demo 
```

使用CMake进行编译 

CMake编译配置如下： 

```cmake
cmake_minimum_required(VERSION 3.16)
# findpackage(ASC)是CMake中用于查找和配置Ascend C编译工具链的命令
findpackage(ASC REQUIRED)
#指定项目支持的语言包括ASC和CXX, ASC表示支持使用毕昇编译器对Ascend C编程语言进行编译
project(kernel_samples LANGUAGES ASC CXX)
add_executabledemo
hello_world.asc
)#通过编译选项设置NPU架构
target.compile-options(demo PRIVATE
${<$<COMPILE_LANGUAGE:ASC>:-npu-arch=dav-2201> 
```

编译和运行步骤如下： 

```txt
mkdir -p build && cd build;  
cmake ../make -j;  
./demo 
```

运行结果如下，本样例共调度8个核，打印了核号和"Hello World!!!"等信息。 

```txt
[Block (0/8)]:HelloWorld![]  
[Block (1/8)]:HelloWorld![]  
[Block (2/8)]:HelloWorld![]  
[Block (3/8)]:HelloWorld![]  
[Block (4/8)]:HelloWorld![]  
[Block (5/8)]:HelloWorld![]  
[Block (6/8)]:HelloWorld![]  
[Block (7/8)]:HelloWorld![] 
```

# 1.3.2.2 Add 自定义算子开发

本入门教程，将会引导你完成以下任务，体验Ascend C SIMD算子开发基本流程。 

1. 算子分析，明确数学表达式和计算逻辑等内容； 

2. Add算子核函数开发； 

3. 算子核函数运行验证。 

在正式的开发之前，还需要先完成环境准备工作，开发Ascend C算子的基本流程如下 图所示： 


图 1-1 开发 Ascend C 算子的基本流程


![](images/0a7ac242364307450ef5ca0ce2958b65483032bfa574572fd4b2f6ec41d23f4e.jpg)


# 说明

● 请点击LINK获取样例代码。 

● 使用本教程只需要您具有一定的C/C++基础，在此基础上，如果您已经对Ascend C编程模型 有一定的了解，您可以在实际操作的过程中加深对理论的理解；如果您还没有开始了解 Ascend C编程模型，也无需担心，您可以先尝试跑通教程中的样例，参考教程最后的指引进 行进一步的学习。 

# 环境准备

CANN软件安装 

开发算子前，需要先准备好开发环境和运行环境，开发环境和运行环境的介绍和 具体的安装步骤可参见《CANN 软件安装指南》。 

环境变量配置 

安装CANN软件后，使用CANN运行用户进行编译、运行时，需要以CANN运行用 户登录环境，执行source ${INSTALL DIR}/set_env.sh命令设置环境变量。$ {INSTALL_DIR}请替换为CANN软件安装后文件存储路径。以root用户安装为例， 安装后文件默认存储路径为：/usr/local/Ascend/cann。 

# 算子分析

主要分析算子的数学表达式、输入输出的数量、Shape范围以及计算逻辑的实现，明确 需要调用的Ascend C接口。下文以Add算子为例，介绍具体的分析过程。 

步骤1 明确算子的数学表达式及计算逻辑。 

Add算子的数学表达式为： 

$$
\vec {z} = \vec {x} + \vec {y}
$$

计算逻辑是：从外部存储Global Memory搬运数据至内部存储Local Memory，然后使 用Ascend C计算接口完成两个输入参数相加，得到最终结果，再搬运到Global Memory上。 

# 步骤2 明确输入和输出。

Add算子有两个输入：x与y，输出为z。 

本样例中算子输入支持的数据类型为float，算子输出的数据类型与输入数据类型 相同。 

算子输入支持的shape为（8，2048），输出shape与输入shape相同。 

算子输入支持的format为：ND。 

# 步骤3 确定核函数名称和参数。

本样例中核函数命名为add_custom。 

根据对算子输入输出的分析，确定核函数有3个参数x，y，z；x，y为输入参数，z 为输出参数。 

# 步骤4 确定算子实现所需接口。

实现涉及外部存储和内部存储间的数据搬运，查看Ascend C API参考中的数据搬 运接口，需要使用DataCopy来实现数据搬移。 

本样例只涉及矢量计算的加法操作，查看Ascend C API参考中的矢量计算接口 Memory矢量计算，初步分析可使用Add接口Add实现x+y。 

计算中使用到的Tensor数据结构，使用AllocTensor、FreeTensor进行申请和释 放。 

● 并行流水任务之间使用Queue队列完成同步，会使用到EnQue、DeQue等接口。 

# ----结束

通过以上分析，得到Ascend C Add算子的设计规格如下： 


表 1-1 Ascend C Add 算子设计规格


<table><tr><td>算子类型
(Opacity)</td><td colspan="4">AddCustom</td></tr><tr><td rowspan="3">算子输入</td><td>name</td><td>shape</td><td>data type</td><td>format</td></tr><tr><td>x</td><td>(8, 2048)</td><td>float</td><td>ND</td></tr><tr><td>y</td><td>(8, 2048)</td><td>float</td><td>ND</td></tr><tr><td>算子输出</td><td>z</td><td>(8, 2048)</td><td>float</td><td>ND</td></tr><tr><td>核函数名称</td><td colspan="4">add_custom</td></tr><tr><td rowspan="4">使用的主要接口</td><td colspan="4">DataCopy: 数据搬运接口</td></tr><tr><td colspan="4">Add: 矢量基础算术接口</td></tr><tr><td colspan="4">AllocTensor、FreeTensor: 内存管理接口</td></tr><tr><td colspan="4">EnQue、DeQue接口: Queue队列管理接口</td></tr><tr><td>算子实现文件名称</td><td colspan="4">addcustom.asc</td></tr></table>

# 核函数开发

完成环境准备和初步的算子分析后，即可开始Ascend C核函数的开发。开发之前请先 从LINK获取样例代码，以下样例代码在add_custom.asc中实现。 

本样例中使用多核并行计算，即把数据进行分片，分配到多个核上进行处理。Ascend C核函数是在一个核上的处理函数，所以只处理部分数据。分配方案是：假设共启用8 个核，数据整体长度为8 * 2048个元素，平均分配到8个核上运行，每个核上处理的数 据大小为2048个元素。对于单核上的处理数据，也可以进行数据切块，实现对数据的 流水并行处理。 

步骤1 根据分配方案设计一个结构体AddCustomTilingData，用于保存并行数据切分相关的 参数。AddCustomTilingData定义了两个参数：totalLength、tileNum。totalLength 指待处理的数据总大小为（8 * 2048）个元素，tileNum指每个核需要计算的数据块个 数。 

```c
struct AddCustomTilingData {
    uint32_t totalLength;
    uint32_t tileNum;
}; 
```

步骤2 根据核函数定义和调用中介绍的规则进行核函数的定义，并在核函数中调用算子类的 Init和Process函数，算子类实现在后续步骤中介绍。 

```txt
global __aicore__ void add_custom(GM_ADDR x, GM_ADDR y, GM_ADDR z, AddCustomTilingData tiling)  
{  
    KERNEL_TASK_TYPE_DEFAULT(Kernel_TYPE_AIV_ONLY); //设置Kernel类型为Vector核（用于矢量计算）  
    KernelAdd op;  
    op.Add(x, y, z, tiling.totalLength, tiling>tileNum);  
    op.Process();  
} 
```

使用__global__函数类型限定符来标识它是一个核函数，可以被<<<>>>调用；使 用__aicore__函数类型限定符来标识该核函数在设备端AI Core上执行。指针入参 变量需要增加变量类型限定符__gm__，表明该指针变量指向Global Memory上某 处内存地址。为了统一表达，使用GM_ADDR宏来修饰入参，GM_ADDR宏定义如 下： #define GM_ADDR __gm__ uint8_t* 

算子类的Init函数，完成内存初始化相关工作，Process函数完成算子实现的核心 逻辑。 

步骤3 根据矢量编程范式实现算子类，本样例中定义KernelAdd算子类，其具体成员如下： 

```cpp
class KernelAdd{   
public: __aicore__inline KernelAdd(){ //初始化函数，完成内存初始化相关操作 __aicore__inline void Init(GM_ADDR x, GM_ADDR y, GM_ADDR z, uint32_t totalLength, uint32_t tileNum)   
} //核心处理函数，实现算子逻辑，调用私有成员函数CopyIn、Compute、CopyOut完成矢量算子的三级流水操作 __aicore__inline void Process(){   
private: //搬入函数，从GlobalMemory搬运数据至LocalMemory，被核心Process函数调用 __aicore__inline void CopyIn(int32_t progress){ //计算函数，完成两个输入参数相加，得到最终结果，被核心Process函数调用 __aicore__inline void Compute(int32_t progress){ //搬出函数，将最终结果从LocalMemory搬运到GlobalMemory上，被核心Process函数调用 __aicore__inline void CopyOut(int32_t progress){   
private: AscendC::TPipe pipe; //TPipe内存管理对象 AscendC::TQue<TPosition::VECIN,BUFFER_NUM>inQueueX,inQueueY; //输入数据Queue队列管理对象，TPosition为VECIN 
```

```cpp
AscendC::TQue<AscendC::TPosition::VECOUT, BUFFER_NUM>outQueueZ; //输出数据Queue队列管理对象，TPosition为VECOUT AscendC::GlobalTensor<float>xGm; //管理输入输出GlobalMemory内存地址的对象，其中xGm,yGm为输入，zGm为输出 AscendC::GlobalTensor<float>yGm; AscendC::GlobalTensor<float>zGm; uint32_t blockLength; //每个核的计算数据长度 uint32_t tileNum; //每个核需要计算的数据块个数 uint32_t tileLength; //每个核内每个数据块的长度 }; 
```

内部函数的调用关系示意图如下： 


图 1-2 核函数调用关系图


![](images/a936ce894e42c816610c0904a983dcc1deb2446d1f15dca9ea4e5c9be4ed8083.jpg)


由此可见除了Init函数完成初始化外，Process中完成了对流水任务“搬入、计算、搬 出”的调用，开发者可以重点关注三个流水任务的实现。 

步骤4 初始化函数Init主要完成以下内容：设置输入输出Global Tensor的Global Memory内 存地址，通过TPipe内存管理对象为输入输出Queue分配内存。 

上文我们介绍到，本样例将数据切分成8块，平均分配到8个核上运行，每个核上处理 的数据大小为2048个元素。那么我们是如何实现这种切分的呢？ 

每个核上处理的数据地址需要在起始地址上增加GetBlockIdx() * blockLength（每个 block处理的数据长度）的偏移来获取。这样也就实现了多核并行计算的数据切分。 

以输入x为例，x + blockLength * GetBlockIdx()即为单核处理程序中x在Global Memory上的内存偏移地址，获取偏移地址后，使用GlobalTensor类的 SetGlobalBuffer接口设定该核上Global Memory的起始地址以及长度。具体示意图如 下。 


图1-3 多核并行处理示意图


![](images/05634194a9a82165934372bb5dc610cbc5df9a615d7b1c47dd1f1fa9a58b8281.jpg)


上面已经实现了多核数据的切分，那么单核上的处理数据如何进行切分？ 

对于单核上的处理数据，可以进行数据切块（Tiling），在本示例中，仅作为参考，将 数据切分成8块（并不意味着8块就是性能最优）。切分后的每个数据块再次切分成2 块，即可开启double buffer，实现流水线之间的并行。 

这样单核上的数据（2048个数）被切分成16块，每块tileLength（128）个数据。 TPipe为inQueueX分配了两块大小为tileLength * sizeof(float)个字节的内存块，每个 内存块能容纳tileLength（128）个float类型数据。数据切分示意图如下。 


图 1-4 单核数据切分示意图


![](images/a3869920896590ab4c2a9c9c98cbe397e2b3c887ce57bc10e400380bd419531d.jpg)



具体的初始化函数代码如下：


```cpp
// Kernel侧所需头文件
#include "kernel_operator.h"
constexpr int32_t BUFFER_NUM = 2; // tensor num for each queue
acore__inline void Init(GM_ADDR x, GM_ADDR y, GM_ADDR z, uint32_t totalLength, uint32_t tileNum)
{
    this->blockLength = totalLength / AscendC::GetBlockNum(); // length computed of each core
    this->tileNum = tileNum; // split data into 8 tiles for each core
    this->tileLength = this->blockLength / tileNum / BUFFER_NUM; // separate to 2 parts, due to double buffer
    // get start index for current core, core parallel
    xGm.SetGlobalBuffer((gm_float *)x + this->blockLength * AscendC::GetBlockIdx(), this->blockLength);
    yGm.SetGlobalBuffer((gm_float *)y + this->blockLength * AscendC::GetBlockIdx(), this->blockLength);
    zGm.SetGlobalBuffer((gm_float *)z + this->blockLength * AscendC::GetBlockIdx(), this->blockLength);
    // pipe alloc memory to queue, the unit is Bytes
    pipe.InitialBuffer(inQueueX, BUFFER_NUM, this->tileLength * sizeof(float));
    pipe.InitialBuffer(inQueueY, BUFFER_NUM, this->tileLength * sizeof(float));
    pipe.InitialBuffer(outQueueZ, BUFFER_NUM, this->tileLength * sizeof(float));
} 
```

步骤5 基于矢量编程范式，将核函数的实现分为3个基本任务：CopyIn，Compute， CopyOut。Process函数中通过如下方式调用这三个函数。 

aicore__inline void Process()   
{ // loop count need to be doubled, due to double buffer int32_t loopCount $=$ this->tileNum \* BUFFER_NUM; // tiling strategy, pipeline parallel for (int32_t i $= 0$ ; i $<$ loopCount; i++) { Copyln(i); Compute(i); CopyOut(i); }   
} 

1. CopyIn函数实现。 

a. 使用DataCopy接口将GlobalTensor数据拷贝到LocalTensor。 

b. 使用EnQue将LocalTensor放入VecIn的Queue中。 

```txt
aicore__inline void Copyln(int32_t progress) { //alloc tensor from queue memory 
```

```cpp
AscendC::LocalTensor<xLocal = inQueueX AllocTensor<float>(); AscendC::LocalTensor<yLocal = inQueueY AllocTensor<float>(); // copy progress_th tile from global tensor to local tensor AscendC::DataCopy(xLocal, xGm[progress * this->tileLength], this->tileLength); AscendC::DataCopy(yLocal, yGm[progress * this->tileLength], this->tileLength); // enqueue input tensors to VECIN queue inQueueX.EnQue(xLocal); inQueueY.EnQue(yLocal); } 
```

2. Compute函数实现。 

a. 使用DeQue从VecIn中取出LocalTensor。 

b. 使用Ascend C接口Add完成矢量计算。 

c. 使用EnQue将计算结果LocalTensor放入到VecOut的Queue中。 

d. 使用FreeTensor将释放不再使用的LocalTensor。 

aicore__inline void Compute(int32_t progress)   
{ // deque input tensors from VECIN queue AscendC::LocalTensor<float> xLocal $=$ inQueueX.DeQue<float>(); AscendC::LocalTensor<float> yLocal $=$ inQueueY.DeQue<float>(); AscendC::LocalTensor<float> zLocal $=$ outQueueZ AllocTensor<float>(); // call Add instr for computation AscendC::Add(zLocal, xLocal, yLocal, this->tileLength); // enque the output tensor to VECOUT queue outQueueZ.EnQue<float>(zLocal); // free input tensors for reuse inQueueX.FreeTensor(xLocal); inQueueY.FreeTensor(yLocal);   
} 

3. CopyOut函数实现。 

a. 使用DeQue接口从VecOut的Queue中取出LocalTensor。 

b. 使用DataCopy接口将LocalTensor拷贝到GlobalTensor上。 

c. 使用FreeTensor将不再使用的LocalTensor进行回收。 

__aicore__ inline void CopyOut(int32_t progress)   
{ // deque output tensor from VECOUT queue AscendC::LocalTensor<float> zLocal $=$ outQueueZ.DeQue<float>(); //copy progress_th tile from local tensor to global tensor AscendC::DataCopy(zGm[progress \* this->tileLength],zLocal,this->tileLength); //free output tensor for reuse outQueueZ.FreeTensor(zLocal);   
} 

# ----结束

# 核函数运行验证

完成Kernel侧核函数开发后，即可编写Host侧的核函数调用程序。实现从Host侧的 APP程序调用算子，执行计算过程。 

步骤1 Host侧应用程序框架的编写。 

```txt
// Host侧应用程序需要包含的头文件
#include "acl/acl.h"
// Kernel侧需要包含的头文件
#include "kernel_operator.h"
// 核函数开发部分
...
global __aicore__ void addCustom(GM_ADDR x, GM_ADDR y, GM_ADDR z, AddCustomTilingData tiling) 
```

```cpp
KERNEL_TASK_TYPE_DEFAULT(Kernel_TYPE_AIV_ONLY); KernelAdd op; op Init(x, y, z, tiling.totalLength, tilingtileNum); op.Process();   
}   
//通过<<...>>内核调用符调用算子 std::vector<float> kernel_add(std::vector<float> &x, std::vector<float> &y)   
{   
}   
//计算结果比对 uint32_t VerifyResult(std::vector<float> &output, std::vector<float> &golden)   
{ auto printTensor = []std::vector<float> &tensor, const char *name) { constexpr size_t maxPrintSize = 20; std::cout << name << ";"; std::copy(tensor.begin(), tensor.begin() + std::min(tensor.size(), maxPrintSize), std::ostream_iterator<float>(std::cout, "")); if (tensor.size() > maxPrintSize) { std::cout << "..."; } std::cout << std::endl; }; printTensor(output, "Output"); printTensor(golden, "Golden"); if (std::equal(golden.begin(), golden.end(), output.begin())) { std::cout << "[Success] Case accuracy is verification passed." << std::endl; return 0; } else { std::cout << "[Failed] Case accuracy is verification failed!" << std::endl; return 1; } return 0;   
}   
//算子验证主程序 int32_t main(int32_t argc, char *argv[])   
{ constexpr uint32_t totalLength = 8 * 2048; constexpr float valueX = 1.2f; constexpr float valueY = 2.3f; std::vector<float> x(totalLength, valueX); std::vector<float> y(totalLength, valueY); std::vector<float> output = kernel_add(x, y); std::vector<float> golden(totalLength, valueX + valueY); return VerifyResult(output, golden);   
} 
```

步骤2 编写通过<<<...>>>内核调用符调用算子的代码。 


图 1-5 调用步骤


![](images/82e0e341d24a598001b682f47dada8438aeb101c35a0e9b808ab649c6c971c96.jpg)


如下示例中的acl API使用方法请参考“acl API（ $\mathsf { C } \& \mathsf { C } + +$ ）”章节。 

std::vector<float> kernel_add(std::vector<float> &x, std::vector<float> &y)   
{ constexpr uint32_t numBlocks $= 8$ uint32_t totalLength $\equiv$ x.size(); size_t totalByteSize $\equiv$ totalLength \* sizeof(float); int32_t deviceld $= 0$ aclrtStream stream $=$ nullptr; AddCustomTilingData tiling $=$ {/*totalLength:/totalLength, /*tileNum:/8}; uint8_t \*xHost $\equiv$ reinterpret_cast<uint8_t $\succ$ (x.data()); uint8_t \*yHost $\equiv$ reinterpret_cast<uint8_t $\succ$ (y.data()); uint8_t \*zHost $\equiv$ nullptr; uint8_t \*xDevice $\equiv$ nullptr; uint8_t \*yDevice $\equiv$ nullptr; uint8_t \*zDevice $\equiv$ nullptr; //初始化 acllInit(nullptr); //运行管理资源申请 aclrtSetDevice(deviceld); aclrtCreateStream(&stream); //分配Host内存 aclrtMallocHost((void \*\*)(&zHost), totalByteSize); //分配Device内存 aclrtMalloc((void \*\*)&xDevice,totalByteSize,ACL_MEM_MALLOC Huge_FIRST); aclrtMalloc((void \*\*)&yDevice,totalByteSize,ACL_MEM_MALLOC Huge_FIRST); aclrtMalloc((void \*\*)&zDevice,totalByteSize,ACL_MEM_MALLOC Huge_FIRST); 

```cpp
//将Host上的输入数据拷贝到Device侧  
aclrtMemcpy(xDevice,totalByteSize,xHost,totalByteSize,ACL_MEMCPY_HOST_TO_DEVICE);  
aclrtMemcpy(yDevice,totalByteSize,yHost,totalByteSize,ACL_MEMCPY_HOST_TO_DEVICE);  
//用内核调用符<<...>>调用核函数完成指定的运算  
addcustom<<numBlocks,nullptr,stream>>>(xDevice,yDevice,zDevice,tiling);  
aclrtSynchronizeStream streamline);  
//将Device上的运算结果拷贝回Host  
aclrtMemcpy(zHost,totalByteSize,zDevice,totalByteSize,ACL_MEMCPY_DEVICE_TO_HOST);  
std::vector<float>z((float*)zHost,(float*)(zHost + totalByteSize));  
//释放申请的资源  
aclrtFree(xDevice);  
aclrtFree(yDevice);  
aclrtFree(zDevice);  
aclrtFreeHost(zHost);  
//去初始化  
aclrtDestroyStream(stream);  
aclrtResetDevice(deviceld);  
aclFinalize();  
return z; 
```


步骤3 CMake编译配置如下：


```cmake
cmake_minimum_required(VERSION 3.16)
# findpackage(ASC)是CMake中用于查找和配置Ascend C编译工具链的命令
findpackage(ASC REQUIRED)
#指定项目支持的语言包括ASC和CXX, ASC表示支持使用毕昇编译器对Ascend C编程语言进行编译
project(kernel_samples LANGUAGES ASC CXX)
add_executable demo
    add_custom.asc
)
#通过编译选项设置NPU架构
target.compile-optionsdemo PRIVATE
$<$<COMPILE_LANGUAGE:ASC>:-npu-arch=dav-2201> 
```


步骤4 编译和运行步骤如下


```txt
mkdir -p build && cd build;  
cmake ../make -j;  
./demo 
```

# 说明

● 该样例仅支持如下型号： 

Atlas 350 加速卡 

Atlas A3 训练系列产品/Atlas A3 推理系列产品 

Atlas A2 训练系列产品/Atlas A2 推理系列产品 

--npu-arch用于指定NPU的架构版本，dav-后为架构版本号，请替换为您实际使用的架构版 本号。各AI处理器型号对应的架构版本号请通过AI处理器型号和__NPU_ARCH__的对应关系 进行查询。 

# ----结束

# 接下来的引导

如果您对教程中的多核并行、流水编程等概念不了解，导致阅读过程有些吃力，可以 参考2.2 编程模型学习基本概念，再来回顾本教程；如果您已经了解相关概念，并跑通 了该样例，您可以参考3.3.2 矢量编程了解Ascend C矢量编程中的更多细节。 

# 1.3.3 基于 SIMT 编程

# 1.3.3.1 Add 自定义算子开发

本入门教程，将会引导你完成以下任务，体验Ascend C SIMT算子开发基本流程。 

1. 算子分析，明确数学表达式和计算逻辑等内容； 

2. Add算子核函数开发； 

3. 算子核函数运行验证。 

在正式的开发之前，需要先完成环境准备工作，开发Ascend C算子的基本流程如下图 所示： 


图 1-6 开发 Ascend C 算子的基本流程


![](images/4d80076f6c1e76f719ada8ffb347d938d736d54a1e86ca0ee4c88b386dbc1b72.jpg)


# 说明

使用本教程只需要您具有一定的C/C++基础，在此基础上，如果您已经对Ascend C SIMT编程模 型有一定的了解，您可以在实际操作的过程中加深对理论的理解；如果您还没有开始了解 Ascend C SIMT编程模型，也无需担心，您可以先尝试跑通教程中的样例，参考教程最后的指引 进行进一步的学习。 

# 环境准备

CANN软件安装 

开发算子前，需要先准备好开发环境和运行环境，开发环境和运行环境的介绍和 具体的安装步骤可参见《CANN 软件安装指南》。 

环境变量配置 

安装CANN软件后，使用CANN运行用户进行编译、运行时，需要以CANN运行用 户登录环境，执行source ${INSTALL DIR}/set_env.sh命令设置环境变量。$ {INSTALL_DIR}请替换为CANN软件安装后文件存储路径。以root用户安装为例， 安装后文件默认存储路径为：/usr/local/Ascend/cann。 

# 算子分析

主要分析算子的数学表达式、输入输出的数量、Shape范围以及计算逻辑的实现，明确 需要调用的Ascend C SIMT接口或操作符。下文以Add算子为例，介绍具体的分析过 程。 

步骤1 明确算子的数学表达式及计算逻辑。 

Add算子的数学表达式为： 

$$
z [ i ] = x [ i ] + y [ i ]
$$

计算逻辑是：逐元素将外部存储Global Memory对应位置上的输入x与y相加，结果存 储在Global Memory输出z上。 

步骤2 明确输入和输出。 

● Add算子有两个输入：x与y，输出为z。 

本样例中算子输入支持的数据类型为float，算子输出的数据类型与输入数据类型 相同。 

算子的输入、输出shape为（48，256）。 

步骤3 确定核函数名称和参数。 

本样例中核函数命名为add_custom。 

根据对算子输入输出的分析，确定核函数有3个输入输出参数x，y，z， 数据类型 均为float。 

增加一个核函数入参total_length，用于记录算子实际的输入、输出数据长度，数 据类型为uint64_t。 

步骤4 确定算子实现逻辑。 

将数据均分到48个Thread Block上，每个Thread Block起256个线程处理256个元 素，每个线程处理一个元素。 

通过每个线程独有的线程索引，计算当前线程需要处理的数据的偏移量。 

# ----结束

通过以上分析，得到Ascend C SIMT实现的Add算子的设计规格如下： 


表1-2 Add 算子输入输出规格


<table><tr><td>name</td><td>shape</td><td>data type</td><td>format</td></tr><tr><td>x(输入)</td><td>48 * 256</td><td>float*</td><td>ND</td></tr><tr><td>y(输入)</td><td>48 * 256</td><td>float*</td><td>ND</td></tr><tr><td>z(输出)</td><td>48 * 256</td><td>float*</td><td>ND</td></tr><tr><td>total_length</td><td>-</td><td>uint64_t</td><td>-</td></tr></table>

核函数名称：add_custom 

算子实现文件名称：add.asc 

# 核函数开发

通过当前线程块索引blockIdx、单个线程块包含的线程数blockDim、当前线程索引 threadIdx计算获得当前线程的索引，以当前线程索引作为当前计算数据行的偏移量。 int32_t idx $=$ blockIdx.x * blockDim.x $^ +$ threadIdx.x; 

通过下标偏移和加法运算符，计算该偏移位置的数据相加的结果，并将结果写入到输 出中。 z[idx] = x[idx] + y[idx]; 

完整的核函数代码实现如下所示： 

global__void addCustom(float\*x, float\*y, float\*z, uint64_t total_length)   
{ // Calculate global thread ID int32_t idx = blockIdx.x \* blockDim.x + threadIdx.x; // Maps to the row index of output tensor if(idx >= total_length){ return; } $z[\mathrm{idx}] = x[\mathrm{idx}] + y[\mathrm{idx}]$ 1 

# 核函数运行验证

完成Kernel侧核函数开发后，即可编写Host侧的核函数调用程序。实现从Host侧的 APP程序调用算子，执行计算过程。 

步骤1 Host侧应用程序框架的编写。 

```cpp
//Host调用需要的头文件
#include <vector>
#include "acl/acl.h"
//核函数开发部分
global _void addcustom(float* x, float* y, float* z, uint64_t total_length)
{
...
}
//通过<<...>>内核调用符调用算子
std::vector<float> add(std::vector<float>& x, std::vector<float>& y)
{
...
// Calc spline params
uint32_t block_num = 48;
uint32_t thread_num_per_block = 256;
uint32_t dyn_ubuf_size = 0; // No need to alloc dynamic memory.
// Call kernel funtion with <<...>>>
add_custom<<block_num, thread_num_per_block, dyn_ubuf_size, stream>>(x_device, y_device,
z_device, x.size());
...
return output;
}
//计算结果比对
uint32_t verify_result(std::vector<float>& output, std::vector<float>& golden)
{
if (std::equal(output.begin(), output.end(), golden.begin())) {
std::cout << "[Success] Case accuracy is verification passed." << std::endl;
return 0;
} else {
std::cout << "[Failed] Case accuracy is verification failed!" << std::endl;
return 1;
} 
```

} return 0;   
1   
//验证算子主程序 int32_t main(int32_t argc, char\* argv[]) { constexpr uint32_t in_shape $= 48^{*}256$ std::vector<x(in_shape); std::vector y(in_shape); std::vector golden(in_shape); std::vector output $=$ add(x,y); return verify_result(output,golden); 

步骤2 编写通过<<<...>>>内核调用符调用算子的代码。 


图 1-7 调用步骤


![](images/5dbe3bda2742f2421bed7707dc449d5c57c0eacb10bd167f9d2ab8faf536b57c.jpg)


如下示例中的acl API使用方法请参考“acl API（ $\mathsf { C } \& \mathsf { C } + +$ ）”章节。 

```cpp
std::vector<float>add(std::vector<float>& x, std::vector<float>& y)  
{  
    size_t total_byte_size = x.size() * sizeof(float);  
    int32_t device_id = 0;  
    aclrtStream stream = nullptr;  
    uint8_t* x_host = reinterpret_cast<int8_t *>(x.data());  
    uint8_t* y_host = reinterpret_cast<int8_t *>(y.data()); 
```

```cpp
uint8_t\* z_host = nullptr; float\* x_device = nullptr; float\* y_device = nullptr; float\* z_device = nullptr; // Init aclInit(nullptr); aclrtSetDevice(device_id); aclrtCreateStream(&stream); // Malloc memory in host and device aclrtMallocHost((void \*\*)(&z_host), total_byte_size); aclrtMalloc((void \*\*)&x_device, total_byte_size, ACL_MEM_MALLOC Huge_FIRST); aclrtMalloc((void \*\*)&y_device, total_byte_size, ACL_MEM_MALLOC Huge_FIRST); aclrtMalloc((void \*\*)&z_device, total_byte_size, ACL_MEM_MALLOC Huge_FIRST); aclrtMemcpy(x_device, total_byte_size, x_host, total_byte_size, ACL_MEMPY_HOST_TO_DEVICE); aclrtMemcpy(y_device, total_byte_size, y_host, total_byte_size, ACL_MEMPY_HOST_TO_DEVICE); // Calc spline params uint32_t block_num = 48; uint32_t thread_num_per_block = 256; uint32_t dyn ubuf_size = 0; // No need to alloc dynamic memory. // Call kernel funtion with <<...>> addcustom<<block_num, thread_num_per_block, dyn ubuf_size, stream>>>(x_device, y_device, z_device, x.size()); aclrtSynchronizeStream streamline); // Copy result from device to host aclrtMemcpy(z_host, total_byte_size, z_device, total_byte_size, ACL_MEMPY_DEVICE_TO_HOST); std::vector<float> output((float \*)z_host, (float \*)(z_host + total_byte_size)); // Free memory aclrtFree(x_device); aclrtFree(y_device); aclrtFree(z_device); aclrtFreeHost(z_host); // Delint aclrtDestroyStream streamline); aclrtResetDevice(device_id); aclFinalize(); return output; 
```

步骤3 CMake编译配置如下。注意：当前版本暂不支持CMake编译，请关注后续正式发布版 本。 

```cmake
cmake_minimum_required(VERSION 3.16)
# findpackage(ASC)是CMake中用于查找和配置Ascend C编译工具链的命令
findpackage(ASC REQUIRED)
#指定项目支持的语言包括ASC和CXX, ASC表示支持使用毕昇编译器对Ascend C编程语言进行编译
project(kernel_samples LANGUAGE ASC CXX)
add_executable demo
add.asc)
#通过编译选项设置NPU架构
target.compile-optionsdemo PRIVATE
$-$<COMPILE_LANGUAGE:ASC>:-npu-arch=dav-3510 --enable-simt>
) 
```

步骤4 编译和运行命令如下 

```shell
mkdir -p build && cd build; # 创建并进入build目录  
cmake.; make -j; # 编译工程  
./demo 
```

# 说明

● 该样例仅支持如下型号： 

Atlas 350 加速卡 

● --enable-simt用于指定SIMT编程场景。 

--npu-arch用于指定NPU的架构版本，dav-后为架构版本号，各AI处理器型号对应的架构版 本号请通过AI处理器型号和__NPU_ARCH__的对应关系进行查询。 

# ----结束

# 接下来的引导

如果您想了解更多SIMT编程相关概念，可以参考2.2.4 AI Core SIMT编程学习基本概 念，再来回顾本教程；如果您已经了解相关概念，并跑通了该样例，您可以参考3.4 SIMT算子实现了解Ascend C SIMT编程中的更多细节。 

# 2 编程指南

2.1 本文档组织结构 

2.2 编程模型 

2.3 编译与运行 

2.4 语言扩展层 

2.5 ${ \mathsf { C } } { + } { + }$ 类库API 

2.6 硬件实现 

2.7 调试调优 

2.8 兼容性指南 

2.9 概念原理和术语 

2.10 附录