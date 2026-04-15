<!-- Source: 算子开发指南.md lines 3882-4593 | Section: 2.4 语言扩展层 -->

# 2.4 语言扩展层

# 2.4.1 SIMD BuiltIn 关键字

# 预定义宏

如其他语言一样，会提供一些内置的宏方便用户编写程序。预定义宏一节着重介绍一 些用户在做异构编程时会经常用到的宏，以及宏的解释。 

# _NPU_ARCH_

_NPU_ARCH__是Device侧AI Core代码中的预处理宏，用于标识AI处理器的架构 版本。该宏由四位数字组成，其中前三位数字用于标识AI Core的IP核(Intellectual Property Core)类型，第四位数字标识该AI Core同一个IP核的配置版本。通过该 宏，开发者可以针对不同AI处理器，差异化进行代码适配和优化。AI处理器型号 和__NPU_ARCH__对应关系如下表所示： 


表 2-17 AI 处理器型号和__NPU_ARCH__的对应关系


<table><tr><td>AI处理器型号</td><td>_NPU_ARCH_</td></tr><tr><td>Atlas 350 加速卡</td><td>3510</td></tr><tr><td>Atlas A3 训练系列产品/Atlas A3 推理系列产品</td><td>2201</td></tr><tr><td>Atlas A2 训练系列产品/Atlas A2 推理系列产品</td><td>2201</td></tr><tr><td>Atlas 200I/500 A2 推理产品</td><td>3002</td></tr><tr><td>Atlas 推理系列产品</td><td>2002</td></tr><tr><td>Atlas 训练系列产品</td><td>1001</td></tr></table>

以下为通过__NPU_ARCH__控制在不同AI处理器上算子输出值舍入模式的示例。 

__aicore__static inline void CopyOut uint64_t mulLen)   
{ #if_NPU_ARCH_ $= = 2002$ Cast.dstLocal,srcLocal,RoundMode::CAST_NONE,mulLen); //CAST_NONE表示舍入模式在转换有精 度损失时使用CAST_RINT模式，在不涉及精度损失时不进行舍入 #elif_NPU_ARCH_ $= = 2201$ Cast.dstLocal,srcLocal,RoundMode::CAST_RINT,mulLen); //CAST_RINT表示舍入模式为四舍六入五 成双舍入 #endif event_t eventVToMTE3 $\equiv$ static castGetTPipePtr()->FetchEventID(HardEvent::V_MTE3)); SetFlag<HardEvent::V_MTE3>(eventVToMTE3); WaitFlag<HardEvent::V_MTE3>(eventVToMTE3); CommonCopyOut<float>(dstLocal,mulLen); //拷贝LocalTensor至GlobalTensor   
} 

# ● ASCEND_IS_AIV、ASCEND_IS_AIC

ASCEND_IS_AIV和ASCEND_IS_AIC是通过C++宏实现的条件判断语句，用于在 _aicore__修饰的函数中实现代码的条件编译。基于分离模式（AIC核和AIV核分 离）开发融合算子时，算子逻辑中同时涉及AIV核和AIC核的处理逻辑，并需要进 行核间同步，此时需要通过ASCEND_IS_AIV/ ASCEND_IS_AIC进行AIV和AIC核代 码的隔离。 

# 说明

当使用高阶API Matmul时，其内部已通过REGIST_MATMUL_OBJ宏方式实现了AIV与AIC 核代码的隔离，用户无需再使用该宏进行处理。 

以MatmulNzCustom算子为例，该算子在分离模式下需要分别在AIV核和AIC核上 实现不同的逻辑。具体而言，AIV核负责将矩阵数据搬入Unified Buffer，完成数 据的重排（将矩阵数据转换为NZ格式），并将其写入Global Memory。而AIC核 则直接从Global Memory读取已经重排好的NZ格式数据，并执行矩阵乘法 （Matmul）计算。由于AIV核和AIC核的代码逻辑不同，需要通过 ASCEND_IS_AIV和ASCEND_IS_AIC宏进行代码隔离，确保在编译时分别生成适用 于AIV核和AIC核的代码。 

# 示例伪码如下：

```cpp
template<typename ATyp, typename BType, typename CType, typename BiasType> __aicore__ inline void MatmulKernel<ATyp, BType, CType, BiasType>::Process(AscendC::TPipe *pipe) {
    //利用AIV核的Vector计算单元实现ND2NZ格式转换。如下代码中MatrixBtoNZ为将B矩阵进行ND2NZ格式转换的函数。
    if ASCEND_IS_AIV {
        pipe->InitBuffer(ubBuf, TOTAL UB_SIZE);
        MatrixBtoNZ<typename B_TYPE::T>(tempGM, bGMNZ, tiling, isTransB, ubBuf, tiling.baseK, tiling.baseN); // Vector侧实现的ND2NZ函数
        SyncAll();
        // AIC核和AIV核同步
        AscendC::CrossCoreSetFlag<0x2, PIPE_MTE3>(0x4);
        return;
    }
    if ASCEND_IS_AIC {
        AscendC::CrossCoreWaitFlag(0x4); //等待AIV核完成ND2NZ格式转换
    }
    ...
    //设置左矩阵A、右矩阵B、Bias。
matmulObj.SetTail(tailM, tailN);
matmulObj.SetTensorA(aGlobal, false);
matmulObj.SetTensorB(bGlobal, false);
if (tiling.isBias) {
matmulObj.SetBias(biasGlobal);
}
//完成矩阵乘操作
matmulObj. IterateAll(cGlobal);
//结束矩阵乘操作
matmulObj.End();
} 
```

# ASCENDC_CUBE_ONLY

ASCENDC_CUBE_ONLY是通过 $C ^ { + + }$ 宏实现的条件判断语句，用于在__aicore__修饰 的函数中实现代码的条件编译。 

基于分离模式开发非融合算子时，在只有矩阵计算的算子场景下，可以通过设置 ASCENDC_CUBE_ONLY，使能纯Cube模式完成Matmul计算，减少消息通信的性 能开销，提升算子性能。 

# 注意

ASCENDC_CUBE_ONLY宏必须在#include "lib/matmul_intf.h"之前设置。 

以matmul_custom算子为例，高阶API Matmul默认使用MIX模式，即用户从AIV 侧发起消息，通过消息通信框架中转消息后，在AIC侧执行Matmul计算。这套消 息处理机制会带来额外的Scalar性能开销。相较于MIX模式，纯Cube模式可以直 接跳过消息通信框架，完成Matmul计算，提升算子性能。 

# 示例伪码如下：

define ASCENDC_CUBE_ONLY #include "lib/matmul_intf.h" using A_TYPE $\equiv$ AscendC::MatmuleType<AscendC::TPosition::GM, CubeFormat::ND, AType>; using B_TYPE $=$ AscendC::MatmuleType<AscendC::TPosition::GM, CubeFormat::ND, BType>; using C_TYPE $=$ AscendC::MatmuleType<AscendC::TPosition::GM, CubeFormat::ND, CType>; using BIAS_TYPE $\equiv$ AscendC::MatmuleType<AscendC::TPosition::GM, CubeFormat::ND, BiasType>; AscendC::MatmulA_TYPE, B_TYPE, C_TYPE, BIAS_TYPE, CFG_NORM>matmulObj; 

# 函数执行空间限定符

函数执行空间限定符（Function Execution Space Qualifier）指示函数是在Host侧执 行还是在Device侧执行，以及它是否可从Host侧或Device侧调用。 

__global_ _global__执行空间限定符声明一个Kernel函数。Kernel函数有如下性质：在 Device上执行；只能被Host侧函数调用；__global__只是表示这是Device侧函数的 入口，并不表示具体的设备类型，具体的设备类型由__aicore__标记。具有如下使 用约束： 

– 一个__global__函数必须返回void类型，并且不能是class的成员函数。 

主机侧调用__global__函数必须使用<<<>>>异构调用语法。 

_global__的调用是异步的，意味着函数返回，并不表示kernel函数在device 侧已经执行完成，如果需要同步，需要使用Runtime同步接口显式同步，如 aclrtSynchronizeStream接口。 

__aicore__ __aicore__执行空间限定符声明一个函数，它具有如下属性： 

在Device侧执行 

只能被__global__函数，或者其他__aicore__函数调用 

```txt
// Only callable from device functions with same kind  
// of execution space  
__aicore__void bar() {}  
// Define a kernel function execute on Al Core device  
__global__aicore__void foo() {  
bar(); // OK.  
} 
```

__host__ __host__执行空间限定符声明一个函数，它具有如下属性： 

只能在Host侧执行 

只能被Host侧函数调用 

__global__ 和__host__不能一起使用 

__host__限定符是可选项，无函数执行空间限定符定义的函数，默认是host函数。 

__aicore__ int f() {} 

// defines a host side function int foo() {} 

// defines a host side function 

```txt
__host__int bar() {
    f(); // Error.
    foo(); // OK.
} // Error.
__global____host__void kfunc() {} 
```

AI CPU函数执行空间限定符__aicpu__用于指示函数是否为AI CPU Kernel函数， 它具有如下属性： 

在Device侧执行且只能被Host侧函数调用，因此必须与__global__同时声 明。 

一个__global__ __aicpu__函数不能是void返回类型，并且入参只能是一个指 针。 

一个__global__ __aicpu__函数不能在.asc文件中进行定义，只能声明，且需 要使用extern。 

Host侧调用__global__ __aicpu__函数时必须使用<<<>>>异构调用语法，输 入的函数入参在入参指针的基础上需要输入从指针中读取的数据大小。 

_global__的调用是异步的，意味着函数返回，并不表示kernel函数在Device 侧已经执行完成，如果需要同步，需要使用Runtime同步接口显式同步，如 aclrtSynchronizeStream接口 

```c
// Define a AI CPU kernel function in AI CPU device file  
aicpu__void foo() {} // Error, single __aicpu__identifier without __global__  
global__void foo() {} // Error, single __global__identifier without __aicpu__  
global__aicpu__void foo() {} // Error, return type is void  
global__aicpu__int foo(void *a) {} // OK  
global__aicpu__int foo(int a) {} // Error, input param is not pointer  
global__aicpu__int foo(void *a, void *b) {} // Error, input param num is not one  
// Declare a AI CPU kernel function in .asc file  
extern __global__aicpu uint32_t hello_world(void *args); // OK 
```

_inline_ 

__inline__限定符声明一个函数，它具有如下属性： 

标识Device侧函数强制内联，可以减少函数频繁调用产生的指令压栈、出栈 的开销，但可能会导致算子二进制增加。 

和 ${ \mathsf { C } } { + } { + }$ 函数修饰符inline的主要区别是Device侧__inline__是强制内联， ${ \mathsf { C } } { + } { + }$ 的 inline则是根据编译器优化选择性内联。 

AI Core对函数嵌套深度有限制，一般推荐嵌套深度不超过4层。使用强制内 联可以减少调用层次。 

__cube__ 

标识该核函数仅在Cube核执行。针对耦合模式的硬件架构，该修饰符不生效。 

```txt
extern "C" __global__ __cube__ void mmad_custom(GM_ADDR a, GM_ADDR b, GM_ADDR c)  
{  
    KernelMmad op;  
    opInit(a, b, c);  
    op.Process();  
} 
```

__vector__ 

标识该核函数仅在Vector核执行。针对耦合模式的硬件架构，该修饰符不生效。 

```txt
_vector__global__aicore__void add(custom(){} 
```

__mix__(cube, vec) 

标识该核函数同时在Cube核和Vector核上执行。(cube, vec)分别表示核函数启动 的Cube核和Vector核的配比，支持的配比为(1, 0)，(0, 1)，(1, 1)， (1, 2)。针对 耦合模式的硬件架构，该修饰符不生效。 

# __schedmode__(mode)

标识该核函数的执行调度模式。如下图所示： 

mode = 0 : normal mode，尽可能选择空闲物理核下发执行核函数，若空闲 物理核数无法满足当前核函数的需要，没有下发的部分等待核心空闲后执 行。此时OP1和OP2算子会存在交叠执行（overlap）的情况。 

mode = 1 : batch mode，在下发核函数时先进行判断，若空闲物理核数无法 满足当前核函数的需要，则等待至空闲物理核数满足该核函数所需要的所有 物理核时，同时下发执行，OP1和OP2的执行被切分（split）开，不会出现交 叠执行的情况。 


任务序列


![](images/8b63d19528afda5c3395a1ed53e859219894d88c8daf3562baa119782e0cbf16.jpg)



NORMALMODE


![](images/48c4459e177187040d26f0514b2a4d4872da9215923e4825513822fe43783cc6.jpg)



时间轴



BATCH MODE


![](images/c813848289236a3175718ea779882156eda3a6bcd45712a4529ed5e0ed57476d.jpg)


在多流并发场景，多算子并行执行时，若执行总核数超过最大物理核数，且多个 算子逻辑使用SyncALL等核间同步接口时，建议设置mode为1，防止多个算子之 间互相等待空闲核调度，导致死锁。默认值mode为0。 

```cpp
_schedmode_(1)_global___mix_(1,2)void OP1()//OP1使用了SyncAll接口，且存在多流并发的可能，需要设置batch mode（mode1）{AscendC::SyncAll(); 
```

```cpp
_schedmode_(1)_global___mix_(1,2)void OP2()//OP2使用了SyncAll接口，且存在多流并发的可能，需要设置batch mode（mode1）{AscendC::SyncAll();}_schedmode_(0)_global__vector(void OP3(){..} //OP3没有使用SyncAll接口，可以设置为normal mode(mode0)，按照正常规则执行算子。or_global__vector(void OP3){...} //不设置_schedmode，默认为normal mode。 
```

# 函数标记宏

__simd_vf__ 

函数标记宏，用于标记SIMD VF入口函数，函数无返回值。使用asc_vf_call调用 SIMD VF入口函数，启动VF子任务。 

```txt
_simd_vf__inline void KernelAdd(_ubuf__float\*x,_ubuf__float\*y,_ubuf__float\*z) 
```

__simd_vf__标记的SIMD VF有以下入参约束： 

支持指针传参（Pass-by-Pointer），指针变量必须用__ubuf__地址空间限定 符修饰。 

不支持引用传参（Pass-by-Reference）。 

不支持函数指针传参，函数对象。 

```cpp
__simd_vf__使用的示例如下：  
__simd_vf__inline void simd Adds(_ubuf_float *output, _ubuf_float *input, uint32_t count, uint16_t onerepeat_size, uint16_t repeat(times)  
{  
    AscendC::Reg::RegTensor<float> src_reg0;  
    AscendC::Reg::RegTensor<float> dst_reg0;  
    //asc_update_mask() will be supported later.  
    //initMaskRegwith the count of all numbers.  
    AscendC::Reg::MaskReg mask_reg = AscendC::Reg::UpdateTime<float>(count);  
    for (uint16_t i = 0; i < repeat(times; i++) {  
        //asc_load, asc Adds and asc/store will be supported later.  
        //load data from UB to RegTensor.  
        AscendC::Reg::LoadAlign(src_reg0, input + i * onerepeat_size);  
        AscendC::Reg::Adds.dst_reg0, src_reg0, 1.0f, mask_reg);  
        //store data from RegTensor to UB.  
        AscendC::Reg::StoreAlign(output + i * onerepeat_size, dst_reg0, mask_reg);  
    }  
} 
```

__simd_callee__ 

函数标记宏，函数可以有返回值，允许被SIMD VF入口函数或其他非入口函数调 用。 

```python
__simd_callee__ inline float add(float x, float y) 
```

# 地址空间限定符

AI Core具备多级独立片上存储，各个地址空间独立编址，具备各自的访存指令，根据 架构差异，有些存储空间具备统一地址空间（Generic Address Space），有些则没 有。设备侧编程基于语法扩展允许地址空间作为合法的类型限定符，以提供针对不同 地址空间的访问能力和地址空间合法性检查。 


表 2-18 地址空间映射关系


<table><tr><td>地址空间限定符</td><td>AI Core物理存储空间</td></tr><tr><td>__gm__</td><td>设备侧内存GM</td></tr><tr><td>__ubuf__</td><td>Vector Unified Buffer</td></tr><tr><td>__ca__</td><td>Cube L0A Buffer</td></tr><tr><td>__cb__</td><td>Cube L0B Buffer</td></tr><tr><td>__cc__</td><td>Cube L0C Buffer</td></tr><tr><td>__cbuf__</td><td>Cube L1 Buffer</td></tr><tr><td>__fbuf__</td><td>Fixpipe Buffer</td></tr><tr><td>__ssbuf__</td><td>SSBuffer</td></tr></table>

地址空间限定符可以在变量声明中使用，用于指定对象分配的区域。如果对象的类型 被地址空间名称限定，那么该对象将被分配在指定的地址空间中。同样地，对于指 针，指向的类型可以通过地址空间进行限定，以指示所指向的对象所在的地址空间。 

```lisp
// declares a pointer p in the __gm__ address space that  
// points to an object (has int type) in the __gm__ address space  
__gm__ int *p;  
global __aicore__ void foo(...)  
{  
// declares an array of 4 floats in the private address space. float x[4];  
} 
```

地址空间限定符不能用于非指针返回类型，非指针函数参数，函数类型，同一个类型 上不允许使用多个地址空间限定符。 

```txt
// OK. __aicore__ int f() {...}  
// Error. Address space qualifier cannot be used with a non-pointer return type. __ubuf__ int f() {...}  
// OK. Address space qualifier can be used with a pointer return type. __ubuf__ int *f() {...}  
// Error. Multiple address spaces specified for a type. __ubuf__ __gm__ int i;  
// OK. The first address space qualifies the object pointed to and the second  
// qualifies the pointer. __ubuf__ int * __gm__ ptr; 
```

# 说明

重要：不同地址空间指针的大小可能不同。例如，不能认为 sizeof(__gm__ int *)总是等于 sizeof(__ubuf__ int *)，譬如编译器或许可能在某些系统上以32bit存储__ubuf__指针。 

# private地址空间

private地址空间是大多数变量的默认地址空间，特别是局部变量。 

```txt
// m is in a specific kernel parameter address space, // it's physical location is implementation determined. 
```

```txt
global __aicore__void foo(int m) {
// OK. i is an int variable allocated in private address space
int i;
}
acore__void bar(int k) { //OK. k is in private address space
// OK. i is an int variable allocated in private address space
int i;
} 
```

# __gm__地址空间

_gm__地址空间限定符用来表示分配于设备侧全局内存的对象，全局内存对象可 以声明为标量、用户自定义结构体的指针。 

```c
-gm_int\*var; // var point to an array of int elements typedef struct { float a[3]; int b[2]; } foo_t; _gm foo_t \*info; // info point to an array of foo_t elements 
```

# __ubuf__地址空间

__ubuf__地址空间用来描述存储于AI Core核内UB存储空间的变量。 

```cpp
global __aicore__void foo()
{
    // ptr is in private address space, point to __ubuf__
    __ubuf__int *ptr;
} 
```

# __ca__, __cb__, __cc__, __cbuf__地址空间

上述几个地址空间主要用于特定的DMA指令访问，不具备标量直接访问能力。 

```txt
class ObjTy{ ObjTy({...} void print({...})   
private: int a; int b; }; __global __aicore_ void foo(_ca_int \*ptr) { // Error. Cannot have ca_ // qualifier in kernel arguments // OK _ca_int \*ptr; } 
```

# 内置常量

<table><tr><td>常量名</td><td>取值</td><td>功能</td></tr><tr><td>constexpr int32_t g_coreType</td><td>· AscendC::AIC
· AscendC::AIV</td><td>常量值由框架自动设置，AIC核下，配置为 AscendC::AIC，AIV核下，配置为 AscendC::AIV。
可以通过对该常量值的判断，来实现了AIV与 AIC核代码的区分和隔离。功能等同于直接使用 ASCEND_IS_AIV、ASCEND_IS_AIC。</td></tr></table>

# 内置变量

<table><tr><td>变量名</td><td>对应API</td><td>功能</td></tr><tr><td>block_num</td><td>GetBlockNum</td><td>当前任务配置的核数，用于代码内部的多核逻辑控制等。</td></tr><tr><td>blockidx</td><td>GetBlockIdx</td><td>当前核的索引，用于代码内部的多核逻辑控制及多核偏移量计算等。</td></tr></table>

通常，建议用户使用内置变量对应的API获取所需值，不建议用户直接使用内置变量。 因为内置变量反映的是单个硬件资源的配置信息，对于软件栈整合硬件资源、扩展硬 件的功能，内置变量的值与实际语义可能不符。 

例如，在Atlas 推理系列产品中，当启用KERNEL_TYPE_MIX_VECTOR_CORE时，算子 会同时运行在AI Core和Vector Core上。此时，block_idx在这两种核心上都是从0开始 计数，用户无法直接通过block_idx来切分数据和控制多核逻辑。而GetBlockIdx在 Vector Core上对block_idx增加偏移量（AI Core的block_num），从而保证返回的值能 够正确反映多核环境下的实际逻辑。 

# SIMD 与 SIMT 混合编程场景

SIMD与SIMT混合编程场景中，SIMT VF的入口函数使用__simt_vf__进行标识，通过在 SIMD的__aicore__函数中使用asc_vf_call调用SIMT入口函数。被SIMT VF入口函数调 用的函数使用__simt_callee__进行标识。 

__simt_vf__ 

函数标记宏，用于标记SIMT VF入口函数，函数无返回值。使用asc_vf_call接口调 用SIMT VF入口函数，启动VF子任务。 

```python
__simt_vf__ inline void KernelAdd(_gm__ float* x, _gm__ float* y, _gm__ float* z) 
```

__simt_vf__标记的SIMT VF函数参数类型支持： 

指针类型：__ubuf__ *、__gm__ *； 

标量类型：bool、int8_t、uint8_t、int16_t、uint16_t、half、bfloat16、 int32_t、uint32_t、float、int64_t、uint64_t。 

_simt_vf__的使用示例如下： 

```txt
_simt_vf___launch_bounds_(THREAD_COUNT) inline void simt_gather( 
```

_gm__ float* input, 

__gm__ uint32_t* index, 

_gm__ float* gather_output, 

uint32_t input_total_length, 

uint32_t index_total_length, 

uint32_t output_total_length) 

{ 

if (threadIdx.x $> =$ output_total_length) { 

return; 

} 

int idx $=$ blockIdx * blockDim.x $^ +$ threadIdx.x; 

if (idx $> =$ index_total_length) { 

return; 

} 

// calculate index of the number we need in input. 

uint32_t gather_idx $=$ index[idx]; 

if (gather_idx $> =$ input_total_length) { 

return; 

} 

```txt
gather_output[threadIdx.x] = input[gatheridx]; 
```

__simt_callee__ 

函数标记宏，用于标记SIMT VF非入口函数，函数可以有返回值，允许被SIMT VF 入口函数或其他非入口函数调用。 

```python
__simt_callee__ inline float add(float x, float y) 
```

Ascend C为SIMT编程、SIMD与SIMT混合编程提供了布尔、整形、浮点型的标量数据 类型和短向量数据类型，提供了用于表达线程块、线程网格三维信息的内置变量。 关 于内置数据格式的详细说明请参见内置数据类型，内置变量请参见内置变量。 

# 2.4.2 SIMT BuiltIn 关键字

# 函数执行空间限定符

函数执行空间限定符（Function Execution Space Qualifier）指示函数是在Host侧执 行还是在Device侧执行，以及能被调用的空间范围。 


表 2-19 函数执行空间限定符概览


<table><tr><td rowspan="2">函数执行空间限定符</td><td colspan="2">执行空间</td><td colspan="2">调用函数空间</td></tr><tr><td>Host</td><td>Device</td><td>Host</td><td>Device</td></tr><tr><td>_host_, 无限定符</td><td>✓</td><td>x</td><td>✓</td><td>x</td></tr><tr><td>_aicore_</td><td>x</td><td>✓</td><td>x</td><td>✓</td></tr><tr><td>_global_</td><td>x</td><td>✓</td><td>✓</td><td>x</td></tr></table>

__global__修饰的函数是核函数入口，有以下使用约束： 

函数返回类型必须为void，不能是class、struct或者union的成员函数。 

不支持递归调用。 

对__global__函数的调用是异步的，调用后即返回Host侧的主机线程。 

只能被Host侧函数调用，在Device上执行。 

_aicore__修饰的函数只能在Device侧执行，只能被__global__函数，或者其他 __aicore__函数调用。 

__host__修饰的函数只能在Host侧被调用和执行。 

# 内存空间限定符

使用内存空间限定符__ubuf__来表示动、静态内存，静态内存的大小在编译期是确定 的，动态内存的大小在核函数执行时确定。 

![](images/a258a59b24a9ee6bae64bb2ebf56dc054248ba3fac0f7eee3b5d89c0f38f41fd.jpg)


当前版本暂未支持动、静态内存，请关注后续版本。 

静态内存通过数组分配： __ubuf__ half staticBuf[1024]; 

动态内存通过以下方式申请使用： 

动态内存的实际内存大小需要在核函数启动时配置，详见核函数配置。 

# 内置变量

dim3 

用于指定和获取线程网格（grid）、线程块（block）在x、y、z维度上的内置结构 体。 

dim3由3个无符号整数组成，结构体定义为{dimx，dimy，dimz}，用于指定3个 不同维度的大小，三维总数为dimx * dimy * dimz。开发者可以通过如下方式创建 dim3结构。 

dim3(x); // 创建一维结构，dimy和dimz为默认值1 

dim3(x, y); // 创建二维结构，dimz为默认值1 

dim3(x, y, z); // 创建三维结构 

当前提供了以下仅在Device上可用的dim3结构的内置变量： 

blockDim 

内置全局变量，在核函数中可以直接使用，用于获取线程块中配置的线程的三维 层次结构，即启动VF时配置的dim3结构体实例值。blockDim.x，blockDim.y， blockDim.z分别表示线程块中三个维度的线程数。 

gridDim 

内置全局变量，只能在核函数中使用，表示整个计算任务在各个维度上分别由多 少个线程块构成。 

gridDim.x是x维度上的线程块数量。 

gridDim.y是y维度上的线程块数量，目前只能返回1。 

gridDim.z是z维度上的线程块数量，目前只能返回1。 

blockIdx 

内置全局变量，只能在核函数中使用，用于获取块索引。表示当前线程所在的线 程块在整个网格中的位置坐标。 

blockIdx.x的范围是0到gridDim.x - 1。 

blockIdx.y的范围是0到gridDim.y - 1，目前只能返回0。 

blockIdx.z的范围是0到gridDim.z - 1，目前只能返回0。 

threadIdx 

内置全局变量，在核函数中可以直接使用，用于获取当前线程在线程块内部的索 引。threadIdx.x，threadIdx.y，threadIdx.z分别表示当前线程在3个维度的索引， threadIdx.x的范围为[0, blockDim.x)，threadIdx.y的范围为[0, blockDim.y)， threadIdx.z的范围为[0, blockDim.z)。线程块内线程的索引与线程ID对应关系如 下： 

对于一维线程块，其线程ID为threadIdx.x。 

– 对于二维线程块，其线程ID为（threadIdx.x $^ +$ threadIdx.y * blockDim.x）。 

对于三维线程块，其线程ID为（threadIdx.x $^ +$ threadIdx.y * blockDim.x + threadIdx.z * blockDim.x * blockDim.y）。 

当前提供了以下仅在Device上可用的int类型的内置变量： 

warpSize 

运行时变量，表示一个线程束（warp）中的线程数量，当前为固定值32。 

# 内置数据类型

目前提供了一系列适用于Device侧的数据类型，包括标量和短向量。短向量是由多个 元素组成的简单向量。 


表 2-20 标量数据类型


<table><tr><td>类型</td><td>数据类型</td><td>描述</td><td>Size(bit)</td><td>取值范围</td></tr><tr><td>布尔型</td><td>bool</td><td>类型,占8比特,全0时代表false,否则代表true。</td><td>8</td><td>true, flase</td></tr><tr><td rowspan="8">整形</td><td>uint8</td><td>unsigned char</td><td>8</td><td>[0, 255]</td></tr><tr><td>int8</td><td>signed char</td><td>8</td><td>[-128, 127]</td></tr><tr><td>uint16</td><td>unsigned short</td><td>16</td><td>[0, 65535]</td></tr><tr><td>int16</td><td>signed short</td><td>16</td><td>[-32768, 32767]</td></tr><tr><td>uint32</td><td>unsigned int</td><td>32</td><td>[0, 4294967295]</td></tr><tr><td>int32</td><td>signed int</td><td>32</td><td>[-2147483648, 2147483647]</td></tr><tr><td>uint64</td><td>unsigned long</td><td>64</td><td>[0,1844674407370 9551615]</td></tr><tr><td>int64</td><td>signed long</td><td>64</td><td>[-92233720368547 75808, 922337203685477 5807]</td></tr><tr><td rowspan="6">浮点型</td><td>float8_e4m3</td><td>符号位宽1,指数位宽4,尾数位宽3</td><td>8</td><td>[2^6 - 2^9, 2^9 - 2^6]</td></tr><tr><td>float8_e5m2</td><td>符号位宽1,指数位宽5,尾数位宽2</td><td>8</td><td>[2^{13} - 2^{16}, 2^{16} - 2^{13}]</td></tr><tr><td>hifloat8</td><td>符号位宽1,点域位宽2,指数与尾数位宽由点域编码决定</td><td>8</td><td>点域编码决定数据精度与取值范围</td></tr><tr><td>half</td><td>符号位宽1,指数位宽5,尾数位宽10</td><td>16</td><td>[2^5 - 2^{16}, 2^{16} - 2^5]</td></tr><tr><td>bfloat16</td><td>符号位宽1,指数位宽8,尾数位宽7</td><td>16</td><td>[2^{120} - 2^{128}, 2^{128} - 2^{120}]</td></tr><tr><td>float</td><td>符号位宽1,指数位宽8,尾数位宽23</td><td>32</td><td>[2^{104} - 2^{128}, 2^{128} - 2^{104}]</td></tr></table>

短向量数据类型分为Vector X2、Vector X3、Vector X4，表示一个短向量变量有2、 3、4个元素，当前支持的类型分布如下： 

<table><tr><td>元素数据类型</td><td>Vector X2</td><td>Vector X3</td><td>Vector X4</td></tr><tr><td>unsigned char</td><td>ucharx2</td><td>ucharx3</td><td>ucharx4</td></tr><tr><td>signed char</td><td>charx2</td><td>charx3</td><td>charx4</td></tr><tr><td>unsigned short (16bit)</td><td>ushortx2</td><td>ushortx3</td><td>ushortx4</td></tr><tr><td>signed short (16bit)</td><td>shortx2</td><td>shortx3</td><td>shortx4</td></tr><tr><td>unsigned int</td><td>uintx2</td><td>uintx3</td><td>uintx4</td></tr><tr><td>signed int</td><td>intx2</td><td>intx3</td><td>intx4</td></tr><tr><td>无符号的长整型 (64bit)</td><td>ulonglongx2</td><td>ulonglongx3</td><td>ulonglongx4</td></tr><tr><td>有符号的长整型 (64bit)</td><td>longlongx2</td><td>longlongx3</td><td>longlongx4</td></tr><tr><td>无符号的长整型 (32bit)</td><td>ulongx2</td><td>ulongx3</td><td>ulongx4</td></tr><tr><td>有符号的长整型 (32bit)</td><td>longx2</td><td>longx3</td><td>longx4</td></tr><tr><td>浮点型, 1符号位, 2指数位, 1尾数位</td><td>float4_e2m1x2</td><td>-</td><td>-</td></tr><tr><td>浮点型, 1符号位, 1指数位, 2尾数位</td><td>float4_e1m2x2</td><td>-</td><td>-</td></tr><tr><td>浮点型, 1符号位, 4指数位, 3尾数位</td><td>float8_e4m3x2</td><td>-</td><td>-</td></tr><tr><td>浮点型, 1符号位, 5指数位, 2尾数位</td><td>float8_e5m2x2</td><td>-</td><td>-</td></tr><tr><td>浮点型 hif8</td><td>hifloat8x2</td><td>-</td><td>-</td></tr><tr><td>浮点型, 1符号位, 5指数位, 10尾数位</td><td>halfx2</td><td>-</td><td>-</td></tr><tr><td>浮点型, 1符号位, 8指数位, 7尾数位</td><td>bfloat16x2</td><td>-</td><td>-</td></tr><tr><td>浮点型, 1符号位, 8指数位, 23尾数位</td><td>floatx2</td><td>floatx3</td><td>floatx4</td></tr></table>


表2-21 短向量数据类型


<table><tr><td>数据类型</td><td>内存大小（字节）</td><td>地址对齐（字节）</td></tr><tr><td>charx2, ucharx2</td><td>2</td><td>2</td></tr><tr><td>charx3, ucharx3, charx4, ucharx4</td><td>4</td><td>4</td></tr><tr><td>shortx2, shortx2</td><td>4</td><td>4</td></tr><tr><td>shortx3, ushortx3, shortx4, shortx4</td><td>8</td><td>8</td></tr><tr><td>intx2, uintx2</td><td>8</td><td>8</td></tr><tr><td>intx3, uintx3, intx4, uintx4</td><td>16</td><td>16</td></tr><tr><td>longx2, ulongx2</td><td>8</td><td>8</td></tr><tr><td>longx3, ulongx3, longx4, ulongx4</td><td>16</td><td>16</td></tr><tr><td>longlongx2, ulonglongx2</td><td>16</td><td>16</td></tr><tr><td>longlongx3, ulonglongx3, longlongx4, ulonglongx4</td><td>32</td><td>32</td></tr><tr><td>floatx2</td><td>8</td><td>8</td></tr><tr><td>floatx3, floatx4</td><td>16</td><td>16</td></tr><tr><td>float4_e2m1x2, float4_e1m2x2</td><td>1</td><td>1</td></tr><tr><td>float8_e4m3x2, float8_e5m2x2、hifloat8x2</td><td>2</td><td>2</td></tr><tr><td>halfx2, bfloat16x2</td><td>4</td><td>4</td></tr></table>

# 运算符

SIMT编程提供了一系列运算符，用于执行数学运算。以下是支持的运算符列表。 


表2-22 SIMT 编程支持的运算符列表


<table><tr><td>类别</td><td>运算符</td><td>bool</td><td>int8_t/uint8_t/ int16_t/uint16_t/ int32_t/uint32_t/ int64_t/uint64_t</td><td>half/ bfloat16 _t/float</td><td>half2/ bfloat16x 2_t</td><td>hiflo at8_t</td></tr><tr><td rowspan="7">算术运算符</td><td>+</td><td>X</td><td>✓</td><td>✓</td><td>✓</td><td>X</td></tr><tr><td>-</td><td>X</td><td>✓</td><td>✓</td><td>✓</td><td>X</td></tr><tr><td>*</td><td>X</td><td>✓</td><td>✓</td><td>✓</td><td>X</td></tr><tr><td>/</td><td>X</td><td>✓</td><td>✓</td><td>✓</td><td>X</td></tr><tr><td>%</td><td>X</td><td>✓</td><td>X</td><td>X</td><td>X</td></tr><tr><td>++</td><td>X</td><td>✓</td><td>✓</td><td>✓</td><td>X</td></tr><tr><td>--</td><td>X</td><td>✓</td><td>✓</td><td>✓</td><td>X</td></tr><tr><td rowspan="2"></td><td>+(取正)</td><td>x</td><td>✓</td><td>✓</td><td>✓</td><td>x</td></tr><tr><td>-(取反)</td><td>x</td><td>✓</td><td>✓</td><td>✓</td><td>x</td></tr><tr><td rowspan="6">比较运算符</td><td>&lt;</td><td>x</td><td>✓</td><td>✓</td><td>x</td><td>x</td></tr><tr><td>&lt;=</td><td>x</td><td>✓</td><td>✓</td><td>x</td><td>x</td></tr><tr><td>&gt;</td><td>x</td><td>✓</td><td>✓</td><td>x</td><td>x</td></tr><tr><td>&gt;=</td><td>x</td><td>✓</td><td>✓</td><td>x</td><td>x</td></tr><tr><td>==</td><td>x</td><td>✓</td><td>✓</td><td>x</td><td>x</td></tr><tr><td>!=</td><td>x</td><td>✓</td><td>✓</td><td>x</td><td>x</td></tr><tr><td rowspan="6">位运算符</td><td>&amp;</td><td>x</td><td>✓</td><td>x</td><td>x</td><td>x</td></tr><tr><td>|</td><td>x</td><td>✓</td><td>x</td><td>x</td><td>x</td></tr><tr><td>^</td><td>x</td><td>✓</td><td>x</td><td>x</td><td>x</td></tr><tr><td>~</td><td>x</td><td>✓</td><td>x</td><td>x</td><td>x</td></tr><tr><td>&lt;&lt;</td><td>x</td><td>✓</td><td>x</td><td>x</td><td>x</td></tr><tr><td>&gt;&gt;</td><td>x</td><td>✓</td><td>x</td><td>x</td><td>x</td></tr><tr><td rowspan="3">逻辑运算符</td><td>&amp;&amp;</td><td>✓</td><td>✓</td><td>✓</td><td>x</td><td>x</td></tr><tr><td>||</td><td>✓</td><td>✓</td><td>✓</td><td>x</td><td>x</td></tr><tr><td>!</td><td>✓</td><td>✓</td><td>✓</td><td>x</td><td>x</td></tr><tr><td>条件运算符</td><td>a?b:c</td><td>✓</td><td>✓</td><td>✓</td><td>✓</td><td>x</td></tr></table>

运算符使用示例如下所示： 

```txt
//加法运算  
res[idx] = x[idx] + y[idx];  
//取反运算  
x[idx] = (-x[idx]);  
//比较运算  
if (x[idx] > y[idx]) {  
    res[idx] = x[idx];  
} else {  
    res[idx] = y[idx];  
} 
```

```javascript
// 按位与运算  
res[idx] = x[idx] & y[idx];  
// 逻辑或运算  
if (x[idx] || y[idx]) {  
    res[idx] = 1;  
}  
// 条件运算  
res[idx] = x[idx] > y[idx] ? x[idx] : y[idx]; 
```

# 核函数配置

在调用__global__限定符修饰的函数时必须指定执行配置。执行配置通过在函数名后带 括号的参数列表之间插入，形如： 

```txt
<<grid_dim, block_dim, dynamic_mem_size, stream>> 
```

# 其中：

grid_dim：int或dim3类型，用于指定网格（grid）的维度与规模，grid_dim.x * grid_dim.y * grid_dim.z等于启动的线程块总数。 

block_dim：int或dim3类型，用于指定每个线程块（block）的维度与规模， block_dim.x * block_dim.y * block_dim.z等于每个线程块包含的线程数。 

dynamic_mem_size：size_t类型，该参数指定除静态分配的内存外，本次调用为 每个线程块动态分配的共享内存字节数。 

stream：aclrtStream类型指针，指定关联的流，用于维护异步操作的执行顺序。 

以下示例展示了内核函数的声明与调用方式。 

```txt
// 声明
_global__void add_custom(float* x, float* y, float* z, uint64_t total_length);
// 调用
addcustom<<<block_num, thread_num_per_block, dyn ubuf_size, stream>>>(x, y, z, 1024); 
```

在执行函数之前，会先对上述配置参数进行校验。如果grid_dim或block_dim超出设备 的最大允许规模，或dynamic_smem_bytes超过分配静态内存后剩余的可用共享内 存，该函数将会执行失败。 

在多线程并发执行时，每个线程使用较少的寄存器可以让更多的线程和线程块驻留在 AI处理器上，从而提升性能。因此，编译器会采用启发式算法，将寄存器溢出 （register spilling）和指令数量控制在最低水平，同时尽量减少寄存器的使用量。应 用程序可以通过在__global__函数定义中使用__launch_bounds__()限定符来限制启动 边界（launch bounds），提供附加信息辅助编译器优化这一过程，这属于可选配置。 

_launch_bounds__(N)是函数标记宏，在SIMT VF入口函数上可选配置，用于在 编译期指定SIMT VF启动的最大线程数。若未配置__launch_bounds__，最大线程 数默认为1024。参数N需要满足： 

– N >= dimx * dimy * dimz；dimx，dimy，dimz为表示线程的dim3结构体。 

N的取值范围为1到2048。 

最大线程数决定了每个线程可分配的寄存器数量，具体对应关系请见下表， 寄存器用于存储线程中的局部变量，若局部变量的个数超出寄存器个数，容 易出现栈溢出等问题。建议最大线程数与启动VF任务的dim3线程数保持一 致。 


表 2-23 __launch_bounds__的 Thread 数量与每个 Thread 可用寄存器数


<table><tr><td>Thread的个数(个)</td><td>每个Thread可用寄存器个数(个)</td></tr><tr><td>1025~2048</td><td>16</td></tr><tr><td>513~1024</td><td>32</td></tr><tr><td>257~512</td><td>64</td></tr><tr><td>1~256</td><td>127</td></tr></table>

配置SIMT函数最大线程数为512，示例如下： 

```c
__simt_vf___launch_bounds_(512) inline void add(_gm__uint8_t* x, _gm__uint8_t* y, __gm__uint8_t* z) 
```

# 2.4.3 SIMD 语言扩展层 C API

C API开放芯片完备编程能力，支持以数组形式分配内存，一般基于指针编程。提供与 业界一致的C语言编程体验。 

包含asc_simd.h文件来调用C API相应接口。如无特殊说明，包含该头文件即可满足接 口调用需求。 若API文档中有特殊说明，则应遵循API的具体说明。 

```txt
include "c_api/asc_simd.h" 
```

对于C API，主要分为以下几类： 

矢量计算，实现调用Vector计算单元执行计算的功能。 

数据搬运，计算API基于Local Memory数据进行计算，所以数据需要先从Global Memory搬运至Local Memory，再使用计算API完成计算，最后从Local Memory 搬出至Global Memory。执行搬运过程的接口称之为数据搬运API。 

同步控制，完成任务间的通信和同步，比如asc_sync_notify/asc_sync_wait接口。 不同的API指令间有可能存在依赖关系，从2.2.3.1 抽象硬件架构可知，不同的指 令异步并行执行，为了保证不同指令队列间的指令按照正确的逻辑关系执行，需 要向不同的组件发送同步指令。同步控制API内部即完成这个发送同步指令的过 程。 

系统变量，访问、获取系统内置变量，辅助计算API。 

对于计算类API可以分为以下几类： 

前n个数据计算：该类型API在计算时采用“紧密排布”的数据读取方式，即从起 始位置开始，按顺序连续获取所需数据。例如，若需处理N个数据，则从源操作数 的第0个位置开始，依次取至第N-1个位置。 

高维切分计算：该类型API按照设定的规则“跳过部分数据”。适合处理需要间隔 采样的场景，灵活度高，但需要额外配置相关参数。 

同步计算：该类型API内部自动插入同步操作，易用性更强。 

# 2.4.4 SIMT 语言扩展层 C API

SIMT编程基于AI Core的硬件能力实现，可以使用asc_vf_call接口启动SIMT VF （Vector Function）子任务。当前，SIMT语言扩展层支持的C API类别如下： 

同步函数：提供内存管理与同步接口，解决不同核内的线程间可能存在的数据竞 争以及线程的同步问题。 

数学函数：提供处理数学运算的函数接口集合。 

精度转换：提供不同精度类型间的转换功能的一系列API接口。 

比较函数：用于判断数据是否为有限数、无穷或nan。 

Atomic函数：提供对Unified Buffer或Global Memory上的数据与指定数据执行原 子操作的一系列API接口。 

Warp函数：提供对单个Warp内32个线程的数据进行处理的相关操作的一系列API 接口。 

类型转换：根据源操作数和目的操作数的数据类型进行精度转换。 

向量类型构造函数：向量类型构造相关接口。 

使能Cache Hints的Load/Store函数：数据加载和数据缓存相关接口。 

调测接口：SIMT VF调试场景下使用的相关接口。