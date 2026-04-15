<!-- Source: 算子开发指南2.md lines 3000-3475 | Section: 4.2.2 220x 迁移 351x 指导 -->

# 4.2.2 220x 迁移 351x 指导

# 4.2.2.1 基础 API 迁移指导

本节针对351x架构芯片变更对基础API兼容性产生的影响进行说明，并提供基础API的 兼容性适配方案。 

# 矢量计算

351x架构默认不支持Subnormal功能。 

说明：SubNormal浮点数指的是指数位全为0、尾数不为0的浮点数，用于表示比 最小正常数更小的值，避免“下溢为0”。351x版本默认不支持Subnormal， Subnormal浮点数在计算中被视为0。 

兼容方案：通过设置config模板参数来配置Subnormal计算模式。软件模拟对 Subnormal数据的处理，通过精度扩展等处理方式来避免Subnormal浮点数下溢 为0。 


表 4-7 涉及 Subnormal 的 API 和 config 参数说明


<table><tr><td>Ascend C 基础API</td><td>兼容说明</td></tr><tr><td>Exp、Ln、 Reciprocal、Sqrt、 Rsqrt、Div</td><td>以Ln接口为例来进行说明。 通过LnConfig结构体的参数algo来配置Subnormal计算模 式。algo取值如下: · LnAlgo::INTRINSIC、 LnAlgo::PRECISION_1ULP_FTZ_true,使用单指令计 算得出结果,所有Subnormal被近似为0。 · LnAlgo::PRECISION_1ULP_FTZFalse,支持 Subnormal数据计算。 该参数默认值DEFAULT_LN_CONFIG的取值如下: constexpr LnConfig DEFAULT_LN_CONFIG = { LnAlgo::INTRINSIC };</td></tr></table>


可以参考以下代码片段：


```cpp
//定义模板参数
constexpr AscendC::LnConfig CONFIG = {
    AscendC::LnAlgo::PRECISION_1ULP_FTZFalse
};
template<typename T> __acore__ inline void Compute(GM_ADDR dst, GM_ADDR src, uint32_t count) {
    AscendC::TPipe pipe;
    AscendC::GlobalTensor<T> srcGlobal;
    AscendC::GlobalTensor<T> dstGlobal;
    srcGlobal.SetGlobalBuffer((gm_T*)src);
    dstGlobal.SetGlobalBuffer((gm_T*)dst);
    AscendC::TQue<AscendC::TPosition::VECIN, 1> inQueue;
    AscendC::TQue<AscendC::TPosition::VECOUT, 1> outQueue;
    pipeInitBuffer(inQueue, 1, count * sizeof(T));
    pipeInitBuffer(outQueue, 1, count * sizeof(T));
    AscendC::LocalTensor<T> dstLocal = outQueue AllocTensor<T>();
    AscendC::LocalTensor<T> srcLocal = inQueue AllocTensor<T>();
    AscendC::DataCopy(srcLocal, srcGlobal, count);
    AscendC::SetFlag<AscendC::HardEvent::MTE2_V>(EVENT_ID0);
    AscendC::WaitFlag<AscendC::HardEvent::MTE2_V>(EVENT_ID0);
    //调用基础API Ln，传入模板参数
    AscendC::Ln<T, CONFIG>(dstLocal, srcLocal, count);
    AscendC::SetFlag<AscendC::HardEvent::V_MTE3>(EVENT_ID1);
    AscendC::WaitFlag<AscendC::HardEvent::V_MTE3>(EVENT_ID1);
    AscendC::DataCopy.dstGlobal, dstLocal, count);
    inQueue.FreeTensor(srcLocal);
} 
```

# 数据搬运

● DataCopy接口不支持L1 Buffer -> GM通路。 

说明：硬件删除L1 Buffer到GM的通路，无法将数据从L1 Buffer直接搬运到GM 中。现有接口不支持L1 Buffer到GM的直接搬运。 

兼容方案：对于纯Cube计算场景：在GM多分配一个单位矩阵，通过Mmad矩阵 乘法计算输出到L0C Buffer，再从L0C Buffer通过Fixpipe搬运到GM。对于Vector 和Cube计算融合场景，可以通过L1 Buffer搬运到UB，再搬运到GM。以下以纯 Cube计算场景为例进行说明，介绍算子核心流程。 

a. 将矩阵A从GM搬运到L1 Buffer。 

```cpp
aicore__inline void CopyGmToA1() { 
```

```autohotkey
AscendC::LocalTensor<T> leftMatrix = inQueueA1 AllocTensor<T>(); AscendC::Nd2NzParams intriParams1{1, 64, 128, 0, 128, 64, 1, 0}; AscendC::DataCopy(leftMatrix, aGlobal, intriParams1); inQueueA1.EnQue(leftMatrix); } 
```

b. 将矩阵B（矩阵B为单位矩阵）从GM搬运到L1 Buffer。 

__aicore__ inline void CopyGmToB1()   
{ AscendC::LocalTensor<U> rightMatrix $=$ inQueueB1 AllocTensor<U>(); AscendC::Nd2NzParams intriParams2{1, 128, 128, 0, 128, 128, 1, 0}; AscendC::DataCopy(rightMatrix, bGlobal, intriParams2); inQueueB1.EnQue(rightMatrix);   
} 

c. 将矩阵A从L1 Buffer搬运到L0A Buffer。 

```cpp
__aicore__ inline void Load2DA1ToL0A()
{
    AscendC::LocalTensor<T> a1 = inQueueA1.DeQue<T>();  
    AscendC::LocalTensor<T> a2 = inQueueA2 AllocTensor<T>();  
    AscendC::LoadData2DParamsV2 loadDataParams;  
    ...  
    AscendC::LoadData(a2, a1, loadDataParams);  
} 
```

d. 将矩阵B从L1 Buffer搬运到L0B Buffer。 

```cpp
__aicore__ inline void Load2DA1ToL0B()   
{ AscendC::LocalTensor<U> b1 = inQueueB1.DeQue<U>(); AscendC::LocalTensor<U> b2 = inQueueB2 AllocTensor<U>(); AscendC::LoadData2DParamsV2 loadDataParams; AscendC::LoadData(b2, b1, loadDataParams); } 
```

e. 进行Mmad矩阵计算，结果输出到L0C Buffer。 

aicore__inline void Compute()   
{ AscendC::MmadParams mmadParams; AscendC::LocalTensorS> co1Local $=$ inQueueCO1 AllocTensorS>(); AscendC::LocalTensor<T>a2 $=$ inQueueA2.DeQue<T>(); AscendC::LocalTensorU b2 $=$ inQueueB2.DeQueU(); AscendC::Mmad(co1Local,a2,b2, mmadParams);   
} 

f. 通过FixPipe将矩阵C从L0C Buffer拷贝到GM。 

aicore__inline void CopyL0CToGm()   
{ AscendC::LocalTensor $<  S>$ co1Local $\equiv$ inQueueCO1.DeQue $<  S>$ (); AscendC::FixpipeParamsV220 fixpipeParams; AscendC::Fixpipe $<  S$ ,S,AscendC::CFG_ROWMajor>(cGlobal,co1Local,fixpipeParams); } 

不支持SetLoadDataBoundary接口。 

说明：351x架构硬件删除了L1 Buffer的边界值设定相关寄存器，不再支持 SetLoadDataBoundary接口。该接口用于设置Load3D时L1 Buffer的边界值。如 果指令在处理源操作数时，源操作数在L1 Buffer上的地址超出设置的边界，则会 从L1 Buffer的起始地址开始读取数据。设置为0表示无边界，可以使用整个L1 Buffer。 

兼容方案： 

– 220x架构版本的接口参数boundaryValue设置为0时与351x架构版本等价。 

如果需要在L1 Buffer上循环读取操作数，需要将对应的Load3D接口手动拆分 成多条指令，手动绕回。 

![](images/1e4320877c68ee69ed4a37f9b1da7576458c8e943d0db905f026d0ad2a535f4b.jpg)


如上图所示，以L1 Buffer到L0A Buffer的搬运为例。矩阵A为half数据类型，大小 为32 * 32的矩阵，假设边界为512B，可以重复搬运数据到L0A Buffer，在每次搬 运时设置目的操作数的地址偏移量。 

a. 将矩阵A从GM搬运到L1 Buffer。 

__aicore__ inline void CopyGmToA1Nd2Nz()   
{ AscendC::LocalTensor<T> leftMatrix $=$ qidA1_.template AllocTensor<T>(); AscendC::Nd2NzParams nd2nzParams; AscendC::DataCopy(leftMatrix, aGlobal_, nd2nzParams); } 

b. 将矩阵B从GM搬运到L1 Buffer。 

__aicore__ inline void CopyGmToB1Nd2Nz()   
{ AscendC::LocalTensor<U> rightMatrix $=$ qidB1_template AllocTensor<U>(); AscendC::Nd2NzParams nd2nzParams; AscendC::DataCopy(rightMatrix,bGlobal_,nd2nzParams); } 

c. 将矩阵A从L1 Buffer搬运到L0A Buffer。 

__aicore__ inline void Load3DA1ToL0A()   
{ auto leftMatrix $=$ qidA1_.template DeQue<T>(); AscendC::LocalTensor<T> a2 $=$ qidA2_.AllocTensor<T>(); AscendC::LoadData3DParamsV2Pro loadData3dParamsPro; //多次调用LoadData进行手动绕回 AscendC::LoadData(a2,leftMatrix,loadData3dParamsPro); AscendC::LocalTensor<T>a3=a2[256]; AscendC::LoadData(a3,leftMatrix,loadData3dParamsPro); AscendC::LocalTensor<T>a4=a2[512]; AscendC::LoadData(a4,leftMatrix,loadData3dParamsPro); AscendC::LocalTensor<T>a5=a2[768]; AscendC::LoadData(a5,leftMatrix,loadData3dParamsPro); } 

d. 将矩阵B从L1 Buffer搬运到L0B Buffer。 

```cpp
__aicore__ inline void Load3DB1ToLOB() { AscendC::SetLoadDataRepeat({0, 1, 0, dstStride}); 
```

```txt
} 
```

e. 矩阵计算。 

aicore__inline void Compute()   
{ AscendC::MmadParams mmadParams; auto co1Local $=$ qidCO1_.AllocTensor<V>(); auto a2 $=$ qidA2_.DeQue<T>(); auto b2 $=$ qidB2_.DeQue<U>(); AscendC::Mmad(co1Local, a2, b2, mmadParams); } 

f. 将矩阵C从L0C Buffer搬运到GM。 

__aicore__inline void CopyL0CToGm(const AscendC::GlobalTensor<S>& gm)   
{ auto co1Local $=$ qidCO1_.DeQue<V>(); AscendC::FixpipeParamsV220 fixpipeParams(nLength, static cast<mLength), AscendC::DivCeil(mLength, AscendC::BLOCK_CUBE)\* AscendC::BLOCK_CUBE, static cast<nLength), 0); AscendC::Fixpipe<S,V, AscendC::CFG_ROWMajor>(gm,co1Local,fixpipeParams); qidCO1_.FreeTensor(co1Local);   
} 

# 矩阵计算

Cube计算单元删除int4b_t数据类型。 

说明：相较于220x架构版本，351x架构版本的Cube计算单元不支持int4b_t。相 关的基础API有LoadData、Mmad和LoadDataWithTranspose，这些接口不再支 持int4b_t。 

兼容方案：算子侧通过编写CV融合算子在Vector Core进行int4b_t到int8_t的Cast 转换，再通过UB搬运到L1后进行Mmad计算。图层面可以在该算子前增加Cast节 点进行int4b_t到int8_t的转换。 

a. 在Vector Core进行int4b_t到int8_t的Cast转换，转换后的数据保存到新的GM 空间中。 

```cpp
__aicore__inline void Unzip(AscendC::GlobalTensor<int8_t>& dstGlobalTensor, AscendC::GlobalTensor<int8_t>& srcGlobalTensor, uint32_t count, AscendC::TQue<AscendC::TPosition::VECIN, 1>& q1, AscendC::TQue<AscendC::TPosition::VECOUT, 1>& q2, AscendC::TQue<AscendC::TPosition::VECOUT, 1>& q3)   
{ AscendC::LocalTensor<int8_t> srcLocalTensor = q1 AllocTensor<int8_t>(); AscendC::LocalTensor<half> tmpTensor = q2 AllocTensor<half>(); AscendC::LocalTensor<int8_t> dstLocalTensor = q3 AllocTensor<int8_t>(); AscendC::DataCopy(srcLocalTensor, srcGlobalTensor, count); AscendC::LocalTensor<AscendC::int4b_t> int4SrcLocalTensor = srcLocalTensor.ReinterpretCast<AscendC::int4b_t>(); uint32_t mask = count / sizeof(half); AscendC::SetFlag<AscendC::HardEvent::MTE2_V>(EVENT_ID0); AscendC::WaitFlag<AscendC::HardEvent::MTE2_V>(EVENT_ID0); AscendC::Cast<half, AscendC::int4b_t>(tmpTensor, int4SrcLocalTensor, AscendC::RoundMode::CAST_NON, count * 2); AscendC::Cast<int8_t, half>(dstLocalTensor, tmpTensor, AscendC::RoundMode::CAST_CEIL, count * 2); AscendC::SetFlag<AscendC::HardEvent::V_MTE3>(EVENT_ID1); AscendC::WaitFlag<AscendC::HardEvent::V_MTE3>(EVENT_ID1); AscendC::DataCopy.dstGlobalTensor, dstLocalTensor, count * 2); q1.FreeTensor(srcLocalTensor); q2.FreeTensor(tmpTensor); q3.FreeTensor.dstLocalTensor);   
} 
```

b. 进行int8_t数据类型的矩阵计算。 

```cpp
template<class A_TYPE, class B_TYPE, class C_TYPE, class BIAS_TYPE>
    __aicore__ inline void MatMulKernel(AscendC::GlobalTensor<int8_t>& aGlobal,
AscendC::GlobalTensor<int8_t>& bGlobal,
AscendC::GlobalTensor<int32_t>& cGlobal, GM_ADDR tilingGM,
GM_ADDR workspaceGM,
int32_t isTransposeAln, int32_t isTransposeBln, AscendC::TPipe& que)
{
    using A_T = typename A_TYPE::T;
    using B_T = typename B_TYPE::T;
    using C_T = typename C_TYPE::T;
    using BiasT = typename BIAS_TYPE::T;
    ...
    int offsetA = 0;
    int offsetB = 0;
    int offsetC = 0;
    int offsetBias = 0;
    ...
    auto gma = aGlobal[offsetA];
    auto gmb = bGlobal[offsetB];
    auto gmc = cGlobal[offsetC];
AscendC::Matmullpl<A_TYPE, B_TYPE, C_TYPE, BIAS_TYPE, CFG_MDL> mm;
mm.SetSubBlockIdx(0);
mmInit(&tiling, &que);
mm.SetTensorA(gma, isTransposeA);
mm.SetTensorB(gmb, isTransposeB);
mm IterateAll(gmc);
} 
```

# ● L0A Buffer分形改变，从ZZ转换为ZN格式。

说明：涉及的API有LoadData、Mmad和LoadDataWithTranspose。 

220x架构版本，参与矩阵乘计算（ $\mathsf { A } ^ { \star } \mathsf { B } = \mathsf { C } $ ）时， ABC矩阵的数据排布格式 分别为ZZ，ZN，NZ。A、B、C矩阵分别位于L0A Buffer、L0B Buffer、L0C Buffer。 

矩阵A：每个分形矩阵内部是行主序，分形矩阵之间是行主序。分形Shape为 16 x (32B/sizeof(AType))，大小为512Byte。 

矩阵B：每个分形矩阵内部是列主序，分形矩阵之间是行主序。分形Shape为 (32B/sizeof(BType)) x 16，大小为512Byte。 

矩阵C：每个分形矩阵内部是行主序，分形矩阵之间是列主序。分形Shape为 16 x 16，大小为256个元素。 

![](images/d33ea0825f23a2e6038fddb2ada62c933e71900bfb3aee676641982f74472f46.jpg)


351x架构版本，参与矩阵乘计算（ $A ^ { \star } B = C$ ）时， ABC矩阵的数据排布格式 分别为NZ，ZN，NZ。 

矩阵A：每个分形矩阵内部是行主序，分形矩阵之间是列主序。其Shape为16 x (32B/sizeof(AType))，大小为512Byte。 

矩阵B：每个分形矩阵内部是列主序，分形矩阵之间是行主序。其Shape为 (32B/sizeof(BType)) x 16，大小为512Byte。 

矩阵C：每个分形矩阵内部是行主序，分形矩阵之间是列主序。其Shape为16 x 16，大小为256个元素。 

![](images/72ac1eb461d15132f80621b1065d45aa688c98ec63fa27a2c7cf350bd9d9a3da.jpg)


兼容方案：非L0A Buffer切分的场景兼容220x版本，L0A Buffer切分的场景需要 根据新的分形重新适配。 

在220x架构中，矩阵计算要求左矩阵为ZZ分形（350x中为NZ），右矩阵为ZN分 形，由于L1 Buffer的数据分形为NZ，所以220x架构下将左矩阵从L1 Buffer搬运 到L0A Buffer需要额外做NZ分形到ZZ分形的转换，351x架构下则不用转换分形。 

![](images/8adfea04f464878677d2e6f97b790d2a4809515507037e2f7a72015de3d5939a.jpg)


![](images/1d7d18a8d50a148f66dcc629cb78f71e01c7c26b84e89f09c96c3df0777fc1ea.jpg)


分形变化带来的变动主要体现在L1 Buffer到L0A Buffer的搬运过程，以下代码片 段进行展示： 

```cpp
aicore__inline void SplitA()  
{int srcOffset = 0;int dstOffset = 0;AscendC::LocalTensor<half> a1Local = inQueueA1.DeQue<half>();AscendC::LocalTensor<half> a2Local = inQueueA2 AllocTensor<half>();//220x架构下LoadData时做Nz2Zz的分形转换//for (int i = 0; i < mBlocks; ++i) {AscendC::LoadData2DParams loadDataParams;loadDataParamsrepeatTimes = kBlocks; //kBlocks表示列方向上有几个宽为16的half类型矩阵loadDataParams.srcStride = mBlocks; //mBlocks表示行方向上有几个高为16的half类型矩阵loadDataParams.ifTranspose = false;AscendC::LoadData(a2Local[dstOffset], a1Local[srcOffset], loadDataParams);srcOffset += 16*16;dstOffset += k*16;  
} 
```

```txt
// 350x架构下LoadData时不需要做Nz2Zz的分形转换，对应搬运参数需要修改 AscendC::LoadData2DParams loadDataParams; loadDataParamsrepeatTimes = m * k / 512; // 小z矩阵的个数 loadDataParams.srcStride = 1; // 小z矩阵之间的间隔 loadDataParams.dstGap = 0; loadDataParams.ifTranspose = false; AscendC::LoadData(a2Local, a1Local, loadDataParams); inQueueA2.EnQue<half>(a2Local); inQueueA1.FreeTensor(a1Local); } 
```

351x架构版本硬件架构删除4：2结构化稀疏功能。 

说明：LoadDataWithSparse用于将存储在L1 Buffer中的512B稠密权重矩阵搬运 到L0B buffer，并同时读取128B的索引矩阵以实现稠密矩阵的稀疏化。由于351x 架构版本不支持结构化稀疏功能，因此LoadDataWithSparse在此版本中并不适 用。另一方面，MmadWithSparse负责执行矩阵乘加操作，其中右矩阵B为稠密矩 阵，需要通过调用LoadDataWithSparse进行载入。由于351x架构不支持 LoadDataWithSparse，因此MmadWithSparse也无法在351x架构版本中使用。 

兼容方案：在算子侧可以不调用LoadDatawithSparse进行矩阵稠密转稀疏操作， 然后使用Mmad进行正常的稠密矩阵计算。稀疏矩阵相关算法可参考 MmadWithSparse中的介绍。 

351x架构版本删除GM- $\cdot >$ L0A Buffer/L0B Buffer 通路 

说明：硬件删除GM- $\cdot >$ L0A Buffer/L0B Buffer通路，调用LoadData时，不再支持 这些通路。 

兼容方案：实现GM- $\cdot >$ L0A Buffer/L0B Buffer搬运需拆分成两步进行，先从GM搬 运到L1 Buffer，再从L1 Buffer搬运到L0A Buffer、L0B Buffer。 

以GM -> L1 Buffer -> L0A Buffer通路为例可以参考以下步骤： 

a. 将矩阵A从GM搬运到L1 Buffer。 

aicore__inline void CopyGmToA1()   
{ AscendC::LocalTensor<T> leftMatrix $=$ inQueueA1 AllocTensor<T>(); AscendC::Nd2NzParams intriParams1{1,64,128,0,128,64,1,0}; AscendC::DataCopy(leftMatrix,aGlobal,intriParams1); inQueueA1.EnQue(leftMatrix);   
} 

b. 将矩阵A从L1 Buffer搬运到L0A Buffer。 

```cpp
__aicore__inline void Load2DA1ToL0A()   
{ AscendC::LocalTensor<T> a1 = inQueueA1.DeQue<T>(); AscendC::LocalTensor<T> a2 = inQueueA2 AllocTensor<T>(); AscendC::LoadData2DParamsV2 loadDataParams; AscendC::LoadData(a2, a1, loadDataParams); } 
```

351x架构版本删除L0A Buffer/L0B Buffer初始化的相关硬件指令。 

说明：InitConstValue将特定存储位置的LocalTensor初始化为某一具体数值，不 支持直接初始化L0A Buffer、L0B Buffer。 

兼容方案：先初始化L1 Buffer，再通过LoadData接口将L1 Buffer上的数据搬运到 L0A Buffer、L0B Buffer。 

以 $\mathsf { G M } \to \mathsf { L } 1$ Buffer -> L0A Buffer的数据通路为例： 

a. 初始化L1 Buffer。 

__aicore__ inline void InitConstA1()   
{ AscendC::LocalTensor<T> leftMatrix $=$ inQueueA1 AllocTensor<T>(); AscendC::InitConstValue(leftMatrix, {1, static cast<int16_t>(m\*k\*sizeof(T)/32),0,1)}; 

```cpp
inQueueA1.EnQue(leftMatrix);   
}   
调用LoadData接口将L1Buffer上的数据搬运到LOABuffer。 aicore__inline void Load2DA1ToL0A() { AscendC::LocalTensor<T>a1 = inQueueA1.DeQue<T>(); AscendC::LocalTensor<T>a2 = inQueueA2 AllocTensor<T>(); AscendC::LoadData2DParamsV2 loadDataParams; AscendC::LoadData(a2,a1,loadDataParams); inQueueA2.EnQue(a2); inQueueA1.FreeTensor(a1); 
```

# 系统变量访问

不支持CheckLocalMemoryIA，351x架构版本相关寄存器删除。 

说明：CheckLocalMemoryIA监视设定范围内的UB读写行为，如果监视到有设定 范围的读写行为则会出现EXCEPTION报错，未监视到设定范围的读写行为则不会 报错。 

兼容方案：该接口为调测接口，对功能无影响。 

# 调测 API

● L1 Buffer上不支持Tensor信息的打印。 

说明：因芯片删除L1 Buffer -> GM通路，不支持L1 Buffer $- >$ GM的功能。 

兼容方案：该接口为调测接口，对功能无影响。 

# 4.2.2.2 高阶 API 迁移指导

Ascend C高阶API基本兼容351x架构与220x架构，部分API进行了扩展。当前351x架构 不支持卷积计算类高阶API。 

# Matmul 类高阶 API

支持的数据类型有变化。 


表4-8 数据类型兼容性情况


<table><tr><td>A矩阵</td><td>B矩阵</td><td>Bias矩阵</td><td>C矩阵</td><td>说明</td></tr><tr><td>int4b_t</td><td>int4b_t</td><td>int32_t</td><td>int32_t、half</td><td>351x架构不支持。</td></tr><tr><td>fp8_e4m3fn_t、fp8_e5m2_t</td><td>fp8_e4m3fn_t、fp8_e5m2_t</td><td>float、half、bfloat16_t</td><td>fp8_e4m3fn_t、half、bfloat16_t、float</td><td>351x架构新增。</td></tr><tr><td>hifloat8_t</td><td>hifloat8_t</td><td>float、half、bfloat16_t</td><td>hifloat8_t、half、bfloat16_t、float</td><td>351x架构新增。</td></tr><tr><td>float</td><td>float</td><td>bfloat16_t</td><td>float、half、bfloat16_t</td><td>351x架构新增。</td></tr><tr><td>bfloat16_t</td><td>bfloat16_t</td><td>bfloat16_t</td><td>float、half、bfloat16_t</td><td>351x架构新增。</td></tr><tr><td>half</td><td>half</td><td>bfloat16_t</td><td>float、half、bfloat16_t</td><td>351x架构新增。</td></tr><tr><td>int8_t</td><td>int8_t</td><td>int32_t</td><td>bfloat16_t</td><td>351x架构新增。</td></tr></table>

不支持4:2稀疏特性。具体兼容方案请参考4：2结构化稀疏功能。 

# 其它高阶 API


表4-9 数学计算


<table><tr><td>AscendC 高阶API</td><td>兼容说明</td></tr><tr><td>Tanh、Asin、Sin、Acos、Cos、Log、Atan、Fmod</td><td>兼容220x架构。
扩展支持算法配置，通过模板参数配置API使用的算法，从而提供高精度、高性能的算法选择。</td></tr><tr><td>Sinh、Cosh、Tan、Trunc、Frac、Erf、Erfc、Atanh、Asinh、Acosh、Floor、Ceil、Round、Axpy、Exp、Lgamma、Digamma、Xor、Cumsum</td><td>兼容220x架构。</td></tr><tr><td>Power</td><td>兼容220x架构。
扩展支持uint8_t、int8_t、uint16_t、int16_t、uint32_t、float16_t数据类型。</td></tr><tr><td>Sign</td><td>兼容220x架构。
扩展支持int64_t数据类型。</td></tr></table>


表4-10 激活函数


<table><tr><td>AscendC 高阶API</td><td>兼容说明</td></tr><tr><td>SoftMax、SimpleSoftMax、SoftmaxFlash、SoftmaxGrad、SoftmaxFlashV2、SoftmaxFlashV3、SoftmaxGradFront、AdjustSoftMaxRes、LogSoftMax、FasterGelu、FasterGeluV2、Gelu、SwiGLU、Silu、Swish、GeGLU、ReFlu、Sigmoid</td><td>兼容220x架构。</td></tr></table>


表 4-11 数据归一化


<table><tr><td>AscendC 高阶API</td><td>兼容说明</td></tr><tr><td>LayerNormGrad、LayerNormGradBeta、RmsNorm、BatchNorm、DeepNorm、GroupNorm</td><td>兼容220x架构。</td></tr><tr><td>Normalize、WelfordUpdate</td><td>兼容220x架构。
扩展支持bfloat16_t数据类型。</td></tr><tr><td>LayerNorm</td><td>兼容220x架构。
扩展支持求方差。</td></tr><tr><td>WelfordFinalize</td><td>兼容220x架构。
扩展支持算法配置，通过模板参数指定在计算方差时是否使用修正系数。</td></tr></table>


表 4-12 量化操作


<table><tr><td>AscendC 高阶API</td><td>兼容说明</td></tr><tr><td>AscendQuant</td><td>兼容220x架构。
扩展支持PRE_TOKEN量化、PRE_GROUP量化。
扩展支持从half、bfloat16_t、float类型到fp8_e5m2_t、fp8_e4m3fn_t、hifloat8_t、int8_t类型的量化。
扩展支持从half、bfloat16_t类型到fp4x2_e1m2_t、fp4x2_e2m1_t类型的量化。</td></tr><tr><td>AscendDequant</td><td>兼容220x架构。
扩展支持PRE_TOKEN量化、PRE_GROUP量化。
扩展支持从int32_t类型到half、bfloat16_t、float类型反量化。
扩展支持从float类型到half、bfloat16_t、float类型的反量化。</td></tr><tr><td>AscendAntiQuant</td><td>兼容220x架构。
扩展支持PRE_TOKEN量化、PRE_GROUP量化。
扩展支持从int8_t、hifloat8_t、fp8_e5m2_t、fp8_e4m3fn_t类型到half、bfloat16_t、float、half类型的伪量化。
扩展支持从fp4x2_e1m2_t、fp4x2_e2m1_t类型到half、bfloat16_t类型的伪量化。</td></tr></table>


表 4-13 归约操作


<table><tr><td>AscendC 高阶API</td><td>兼容说明</td></tr><tr><td>Sum、Mean、ReduceXorSum、ReduceMean、ReduceAny、ReduceAll、ReduceProd</td><td>兼容220x架构。</td></tr><tr><td>ReduceSum</td><td>兼容220x架构。
扩展支持int32_t、uint32_t、int64_t、uint64_t数据类型。</td></tr><tr><td>ReduceMax、ReduceMin</td><td>兼容220x架构。
扩展支持int8_t、uint8_t、int16_t、uint16_t、float16_t、int32_t、uint32_t、int64_t、uint64_t数据类型。</td></tr></table>


表4-14 排序操作


<table><tr><td>AscendC 高阶API</td><td>兼容说明</td></tr><tr><td>Concat、Extract、GetSortOffset、GetSortLen、MrgSort</td><td>兼容220x架构。</td></tr><tr><td>TopK</td><td>兼容220x架构。
使用RADIX_SELECT算法时，扩展支持 uint8_t、int8_t、uint16_t、int16_t、uint32_t、int32_t、float16_t、uint64_t、int64_t数据类型。</td></tr><tr><td>Sort</td><td>兼容220x架构。
扩展支持算法配置，通过模板参数指定排序算法以及降序升序排序。</td></tr></table>


表 4-15 索引计算


<table><tr><td>AscendC 高阶API</td><td>兼容说明</td></tr><tr><td>Arange</td><td>兼容220x架构。
扩展支持int64_t数据类型。</td></tr></table>


表4-16 数据过滤


<table><tr><td>AscendC 高阶API</td><td>兼容说明</td></tr><tr><td>Select</td><td>兼容220x架构。</td></tr><tr><td>DropOut</td><td>兼容220x架构。
扩展支持bfloat16_t数据类型。</td></tr></table>


表 4-17 张量变换


<table><tr><td>AscendC 高阶API</td><td>兼容说明</td></tr><tr><td>Transpose</td><td>兼容220x架构。
新增支持数据排布转换场景：
· 二维转置或者三维的后两位转置。
· 三维中的第一维和第二维互换。
· 三维中的第一维和第三维互换。
· 使用交织指令对二维ND2NZ转置。</td></tr><tr><td>TransData、Pad、UnPad</td><td>兼容220x架构。</td></tr><tr><td>Broadcast</td><td>兼容220x架构。
扩展支持动态Shape。
扩展支持int16_t、uint16_t、float16_t、int32_t、uint32_t数据类型。</td></tr><tr><td>Fill</td><td>兼容220x架构。
扩展支持uint8_t、int8_t、float16_t、uint64_t、int64_t数据类型。</td></tr></table>


表 4-18 Hccl


<table><tr><td>AscendC 高阶API</td><td>兼容说明</td></tr><tr><td>Hccl模板参数</td><td>支持HCCL_SERVER_TYPE_CCU服务端类型。</td></tr><tr><td>InitV2、SetCcTilingV2、
AllReduce、AllGather、
ReduceScatter、AlltoAll、
AlltoAllV、Commit、Wait、
Finalize</td><td>兼容220x架构。</td></tr><tr><td>BatchWrite、iterate、Query、
InterHcclGroupSync、
GetWindowsInAddr、
GetWindowsOutAddr、
GetRankId、GetRankDim、
QueueBarrier、GetQueueNum</td><td>351x架构暂不支持。</td></tr><tr><td>SetReduceType、AlltoAllvWrite</td><td>351x架构新增。</td></tr></table>

# 4.2.2.3 算子编译迁移指导

进行算子编译时，开发者需要感知不同架构、不同的AI处理器型号。 

异构编译场景，开发者使用命令行或者编写Cmake文件进行编译的情况，需要手 动修改NPU架构版本号或者AI 处理器型号。以修改NPU架构版本号为例，更改编 译命令行或编译工程CMakeLists.txt文件中的--npu-arch配置，示例如下： 

```txt
...
target.compile-optionsdemo PRIVATE //将dav-xxxx更换为对应NPU架构版本号
$<$$<COMPILE_LANGUAGE:ASC>:--npu-arch=dav-xxxx> 
```

对于使用msOpGen工具生成的标准自定义算子工程的情况，会自动在算子工程目 录下生成编译配置项文件CMakePresets.json中，并自动填充 

ASCEND_COMPUTE_UNIT字段。开发者需要在进行算子原型定义时，通过 AddConfig接口注册算子支持的AI处理器型号以及相关的配置信息。AddConfig接 口原型如下：soc参数表示AI处理器型号，aicore_config表示其他配置信息。 

```txt
void AddConfig(const char *soc);  
void AddConfig(const char *soc, OpAlCoreConfig &aicore_config); 
```

通过该接口注册AI处理器型号的样例如下，ascendxxx填写规则请参考算子工程目 录下编译配置项文件CMakePresets.json中的ASCEND_COMPUTE_UNIT字段，该 字段取值在使用msOpGen创建工程时自动生成。 

```cpp
...
namespace ops {
class AddCustom : public OpDef {
public:
    AddCustom(const char* name) : OpDef(name)
    ...
    // 将ascendXXX更换为对应芯片版本
    this->AlCore().AddConfig("ascendxxx");
}
};
OP_ADD(AddCustom);
} // namespace ops 
```

# 5 可视化专区

Cube 算子执行过程可视化 

Vector 算子执行过程可视化