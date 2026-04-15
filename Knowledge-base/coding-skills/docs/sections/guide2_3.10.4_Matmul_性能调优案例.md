<!-- Source: 算子开发指南2.md lines 1327-2909 | Section: 3.10.4 Matmul 性能调优案例 -->

# 3.10.4 Matmul 性能调优案例

# 3.10.4.1 Matmul 性能优化策略总览

本节提供了一系列包含Matmul计算的算子性能调优案例，开发者可根据实际应用场 景，参考相关案例中的优化方法和思路，应用于具体实践中。案例分为如下五类，各 分类的简介请参见如下表格，详细内容请阅读后续章节。 

Tiling优化 


表 3-29 Tiling 优化策略总览


<table><tr><td>分类</td><td>适用场景</td><td>相关案例</td></tr><tr><td>Tiling优化：优化 Tiling分核及基本块切分策略。</td><td>数据量足够多的大Shape场 景。</td><td>Matmul算子优化 Tiling策略</td></tr></table>

并行度优化 


表3-30 并行度优化策略总览


<table><tr><td>分类</td><td>适用场景</td><td>相关案例</td></tr><tr><td>多核间任务并行：合理地将数据分配给不同的核来执行任务。</td><td>矩阵的K轴较大、M轴和N轴相比K轴较小的场景。</td><td>Matmul高阶API使能多核切K</td></tr><tr><td>多核间数据访问并行:优化多核数据并行访问机制,如多核场景同一内存数据的地址访问冲突优化,实现多核数据访问效率提升。</td><td>多核执行Matmul,输入矩阵的K轴较大且K轴非全载的场景。</td><td>Matmul高阶API使能多核K轴错峰访问内存</td></tr><tr><td>单核内流水并行:利用不同指令队列间的相互独立性和可并行执行特性,优化核内流水并行度。</td><td>1.算子的MMAD流水和FIXPIPE流水之间串行执行,同步等待的时间在算子整体执行耗时中占比较高。2.MTE2 Bound且MTE2流水和其他流水串行执行。</td><td>1. Matmul高阶API使能UnitFlag2. Matmul高阶API使能NBuffer33模板</td></tr></table>

# 内存优化


表 3-31 内存优化策略总览


<table><tr><td>分类</td><td>适用场景</td><td>相关案例</td></tr><tr><td>内存共享与复用：通过Buffer的共享与缓存复用，减少重复的数据搬运带来的开销。</td><td>MIX场景下，多个AIV的A矩阵或B矩阵GM地址相同，且多个AIV复用的A矩阵或B矩阵在L1Buffer上全载。</td><td>Matmul高阶API使能IBShare模板共享A和B矩阵数据Matmul高阶API使能IBShare模板共享B矩阵数据</td></tr><tr><td>内存对齐：确保处理的数据满足特定的对齐要求，针对非对齐数据使用不同的搬运策略，以提升数据搬运的效率。</td><td>输入矩阵内轴非256字节对齐，且数据量较大的场景。</td><td>AIV核上的ND2NZ格式转换</td></tr></table>

# Scalar优化


表 3-32 Scalar 优化策略总览


<table><tr><td>分类</td><td>适用场景</td><td>相关案例</td></tr><tr><td>Tiling常量化：在 Kernel编译期间完成 Matmul Tiling的计算，由变量转化为常量扩散到系统中，减少Scalar提升性能。</td><td>Matmul初始化时的Scalar计算较多，影响指令头开销。Matmul迭代之间的Scalar计算较多，阻塞MTE2流水。</td><td>Matmul高阶API使能Tiling全量常量化</td></tr><tr><td>纯Cube模式：减少消息处理机制带来额外的Scalar开销。</td><td>相较于MIX模式，没有矢量计算，只有矩阵计算的场景。</td><td>Matmul高阶API使能纯Cube模式</td></tr></table>

搬运优化 


表3-33 搬运优化策略总览


<table><tr><td>分类</td><td>适用场景</td><td>相关案例</td></tr><tr><td>搬运吞吐量优化：通过合理控制搬运数据块的大小，提升带宽利用效率，实现搬运效率的提升。</td><td>1.MTE2循环搬运次数多的大 shape场景。
2.输入和输出的数据量超过L2 Cache大小的场景。</td><td>1. Matmul 高阶API使能MDL模板
2. Matmul高阶API使能L2 Cache切分</td></tr><tr><td>预加载搬运：预加载需要搬运的数据块，减少流水之间的间隙。</td><td>MTE2流水间隙较大，且M或N数值较大的场景。</td><td>Matmul高阶API使能MTE2 Preload</td></tr></table>

# 3.10.4.2 Matmul 算子优化 Tiling 策略

# 案例介绍

本案例对Matmul算子进行性能分析和优化。Matmul算子实现的功能是矩阵乘法，其 中主要包含数据搬入和搬出流水，Cube计算流水。 

以矩阵维度M = 4096，N = 5120，K = 4096，输入数据类型half，输出数据类型 float，输出格式是ND为例，性能验证平台为Atlas A2 训练系列产品/Atlas A2 推理系 列产品，介绍针对Matmul算子的优化手段，包括优化分核逻辑、优化基本块、使能大 包搬运。 

分核逻辑：开启尽量多的Cube核使能并行计算。 

优化基本块，选择最优的baseM、baseN、baseK参数，其中baseM、baseN、 baseK为Matmul Tiling中的参数。 

使能大包搬运：从GM搬运数据到L1时，对于A矩阵，一次搬入depthA1个基本 块，基本块大小为baseM * baseK，对于B矩阵，一次搬入depthB1个基本块，基 本块大小为baseN * baseK。使能大包搬运后，一次搬入的数据量变大，从而提升 MTE2搬运效率。 

# 获取性能数据

使用msProf工具获取算子的Profiling数据，重点分析MTE2，Cube，Scalar pipeline的 流水情况。 

# 分析主要瓶颈点


图 3-164 优化前 Profiling 数据


![](images/79f01bfa952b1153ba633b1229c5602ad300ed6e0fa8e43e31ee709bb3724826.jpg)


由以上Profiling数据，可以看出MTE2耗时占比较大，当前性能瓶颈点在于MTE2流 水。 

Profiling数据的Block Dim可见分核未分满，考虑分核逻辑的优化。设 CurrentCore是未优化前分核的Cube核数，MaxCore为最大Cube核数，当开启全 部核并行做当前shape数据量的计算时，预估性能收益为MaxCore / CurrentCore 的倍数。 

优化基本块切分，将影响搬运数据的效率，算子搬运的总数据量为搬运的左矩阵 和右矩阵数据量之和。在Matmul计算K方向不能全载的场景下，根据矩阵乘法的 算法，搬运左矩阵的次数为N / baseN，搬运右矩阵的次数为M / baseM，即搬运 总数据量totalCnt = (N / baseN) * M * K + (M / baseM) * K * N。预估性能收益 为搬运数据量的比值，优化前搬运数据量totalCnt0/优化后搬运数据量 totalCnt1，化简后结果为(1 / baseM0 + 1 / baseN0) / (1 / baseM1 + 1 / baseN1)，其中，baseM0, baseN0为优化前基本块参数，baseM1, baseN1为优 化后基本块参数。 

使能大包搬运后，指令条数变化、地址对齐等因素会影响性能，按照经验预估， 对于MTE2为性能瓶颈的场景，会有20%以上的MTE2性能收益。 

# 设计优化方案

优化点一：优化分核逻辑 

由Profiling数据看出分核数为4，启动更多的核同时计算，可以提高计算并行度。 当前案例使用的AI处理器共20个核，每个核中包含1个Cube Core和2个Vector Core。NPU调用程序中设置numBlocks为实际使用的核数20。 

```cpp
//代码片段  
uint32_t numBlocks = 20; //优化前numBlocks为4  
CHECK_ACL(aclInit(nullptr));  
int32_t deviceId = 0;  
CHECK_ACL(aclrtSetDevice(deviceld));  
aclrtStream stream = nullptr;  
CHECK_ACL(aclrtCreateStream(&stream));  
uint8_t *aHost;  
uint8_t *aDevice;  
CHECK_ACL(aclrtMallocHost((void *))(&aHost), aFileSize));  
CHECK_ACL(aclrtMaloc((void *))&aDevice, aFileSize, ACL_MEM_MALLOC Huge_FIRST));  
ReadFile("\\input/x1_gm.bin", aFileSize, aHost, aFileSize);  
//PrintData(aHost, 16, printDataType::HALF);  
CHECK_ACL(aclrtMemcpy(aDevice, aFileSize, aHost, aFileSize, ACL_MEMCPY_HOST_TO_DEVICE));  
uint8_t *bHost;  
uint8_t *bDevice;  
CHECK_ACL(aclrtMallocHost((void *))(&bHost), bFileSize));  
CHECK_ACL(aclrtMalloc((void *))&bDevice, bFileSize, ACL_MEM_MALLOC Huge_FIRST));  
ReadFile("\\input/x2_gm.bin", bFileSize, bHost, bFileSize);  
//PrintData(bHost, 16, printDataType::HALF);  
CHECK_ACL(aclrtMempy(bDevice, bFileSize, bHost, bFileSize, ACL_MEMCPY_HOST_TO_DEVICE));  
uint8_t *workspaceHost; 
```

```cpp
uint8_t *workspaceDevice;  
CHECK_ACL(aclrtMallocHost((void **)(&workspaceHost), workspaceSize));  
CHECK_ACL(aclrtMalloc((void **)&workspaceDevice, workspaceSize, ACL_MEM_MALLOC Huge_FIRST));  
uint8_t *tilingHost;  
uint8_t *tilingDevice;  
CHECK_ACL(aclrtMallocHost((void **)(&tilingHost), tilingFileSize));  
CHECK_ACL(aclrtMalloc((void **)&tilingDevice, tilingFileSize, ACL_MEM_MALLOC Huge_FIRST));  
CHECK_ACL(aclrtMemcpy(tilingHost, tilingFileSize, GenerateTiling(), tilingFileSize, ACL_MEMPY_HOST_TO_HOST));  
// PrintData(tilingHost, 16, printDataType::UINT32_T);  
CHECK_ACL(aclrtMemcpy(tilingDevice, tilingFileSize, tilingHost, tilingFileSize, ACL_MEMPY_HOST_TO_DEVICE));  
uint8_t *cHost;  
uint8_t *cDevice;  
CHECK_ACL(aclrtMallocHost((void **)(&cHost), cFileSize));  
CHECK_ACL(aclrtMalloc((void **)&cDevice, cFileSize, ACL_MEM_MALLOC Huge_FIRST));  
// ACLRT-LaUNCH_KERNEL(matmulcustom)  
// (numBlocks, stream, aDevice, bDevice, cDevice, workspaceDevice, tilingDevice);  
matmul_custom_do(numBlocks, stream, aDevice, bDevice, cDevice, workspaceDevice, tilingDevice);  
由于Matmul API都是从Vector侧发起的，当前案例使用的AI处理器中Cube Core和Vector Core的配比为1：2，所以在Matmul tiling计算中需要按照2倍的numBlocks数切分，即Vector Core数。NPU调用程序中设置的实际运行核数是20核，所以Tiling代码中设置Tiling API按照40个核进行数据切分，如下代码所示。  
int usedCoreNum = 40; //优化前usedCoreNum是8  
int runMode = 1;  
int32_t baseM = 64; //64  
int32_t baseN = 64; //64  
optiling::TCubeTiling tilingData;  
MultiCoreMatmulTiling tilingApi;  
tilingApi.SetDim(usedCoreNum); 
```


图 3-165 优化分核逻辑后 Profiling 数据


```txt
aicore_tim aic_total_c aic_mac_tir aic.mac_raicscalar aicscalar aic_mte1_t aic_mte1_r aic_mte2_t aic_mte2_r aic_fixpipe aic_fixpipe 2532.53 93703665 706.283 0.279 1225.87 0.484 1201.55 0.474 2452.38 0.968 724.456 0.286 
```

修改代码后，算子执行时间从12045us下降到2532us，约等于(20核 / 4核) = 5倍 的性能提升。 

# 优化点二：优化基本块

当前Tiling中设置的base块为 [baseM, baseN, baseK] = [64, 64, 256]，这种基本 块Cube计算cycle少，计算访存比（即计算量与需要数据量的比值）低；搬出一次 Matmul结果到GM的base块是64 * 64，由于输出格式是ND，数据类型是float， 搬出下一次Matmul结果的起始地址需要偏移一个baseN的大小，即64 * 4 = 256 字节，导致fixpipe搬出时GM地址非512byte对齐，那么需要设置更优的基本块。 

针对当前shape较大的场景，基本块的选择原则为计算访存比最大，即在Cube计 算量最大的情况下，访存的数据量最小。在输入为fp16类型的情况下，Cube执行 单元1 cycle能算16 * 16 * 16个数。根据经验，[baseM, baseN, baseK] $=$ [128, 256, 64]和[128, 128, 128]两种切分方案均满足搬出时GM地址512Byte对齐（每 搬出一次Matmul结果时，地址分别偏移256 * 4byte和128 * 4byte），Cube计算 cycle数一致，为(128 * 64 * 256) / (16 * 16 * 16) = (128 * 128 * 128) / (16 * 16 * 16) = 512cycle。针对[baseM, baseN, baseK] $=$ [128, 256, 64]，计算访存比为 512cycle / (128 * 64 * 2 + 256 * 64 * 2) = 512cycle / 48KB；针对[baseM, baseN, baseK] = [128, 128, 128]，计算访存比为512cycle / (128 * 128 * 2 + 128 * 128 * 2) = 512cycle / 64KB；可见[128, 256, 64]基本块方案的计算访存比更 

高，计算密度更大，同样的计算量，需要的数据量最小，最大限度提高Cube单元 的计算量。 

修改Tiling代码，通过SetFixSplit()接口设置baseM和baseN，tiling函数会自动计 算出最优baseK，这里得到64。 

int32_t baseM $=$ 128; // 优化前baseM是64 

int32_t baseN $=$ 256; // 优化前baseN是64 

optiling::TCubeTiling tilingData; 

MultiCoreMatmulTiling tilingApi; 

tilingApi.SetDim(usedCoreNum); 

tilingApi.SetAType(leftPos, leftFormat, leftDtype, bool(transposeA)); 

tilingApi.SetBType(rightPos, rightFormat, rightDtype, bool(transposeB)); 

tilingApi.SetCType(resPos, resFormat, resDtype); 

tilingApi.SetBiasType(biasPos, biasFormat, biasDtype); 

tilingApi.SetOrgShape(M, N, K); 

tilingApi.SetShape(M, N, K); 

tilingApi.SetFixSplit(baseM, baseN, -1); 

使能这组基本块后，MTE2耗时（对应aic_mte2_time）从2452us降低到808us， MTE2性能提升3倍。 

图 3-166 优化基本块后 Profiling 数据 

aicoretimiaictotalcaicmatiaicmacraaic_scalaraicscalaraimtetaicmte1aicmte2taimteaicfxpipeaicfipipe 

835.6330918284615.797 0.737618.704 0.74415.068 0.497808.522 0.968 87.006 0.104 

# 优化点三：使能大包搬运

当前带宽利用率为：totalSize / mte2Time = totalCnt * dtype / mte2Time，代入 数据计算为2491GB/s。未使能大包搬运的情况下，矩阵从GM搬运到L1一次只搬 运1个基本块。通过模板参数使能大包搬运，一次搬运多个基本块，提高MTE2带 宽利用率。 

```cpp
//原始matmul对象定义：Matmul<AscendC::MatmulType<TPosition::GM, CubeFormat::ND, A_T>, AscendC::MatmulType<TPosition::GM, CubeFormat::ND, B_T>, AscendC::MatmulType<TPosition::GM, CubeFormat::ND, C_T>, AscendC::MatmulType<TPosition::GM, CubeFormat::ND, BiasT>>>mm; //通过在定义matmul对象的模板参数里加上CFG_MDL参数使能大包搬运功能：Matmul<AscendC::MatmulType<TPosition::GM, CubeFormat::ND, A_T>, AscendC::MatmulType<TPosition::GM, CubeFormat::ND, B_T>, AscendC::MatmulType<TPosition::GM, CubeFormat::ND, C_T>, AscendC::MatmulType<TPosition::GM, CubeFormat::ND, BiasT>, CFG_MDL>>mm; 
```

从下图可以看到，使能大包搬运后，MTE2耗时从808us下降到591us，带宽利用 率代入数据计算为3406GB/s，利用率提升36%+，Cube利用率达到80%+。 

图 3-167 使能大包搬运后 Profiling 数据 

aicoretimiaictotalcaicmactiaicmaraaic_scalaaic_salaaicmteltaicmteaicmte2_taicmteaicfipipeaicfpipe 

710.46 26286857581.815 0.819472.152 0.665481.4760.678591.0880.83226.882 0.038 

# 验证优化方案性能收益

优化分核逻辑，实际收益4.75倍，约等于(20核 / 4核) = 5倍收益，并且考虑到核 的启动开销，可以认为收益一致。 

优化基本块，实际收益约3倍，理论评估代入上述分析公式，收益为(1 / 64 + 1 / 64) / (1 / 128 + 1 / 256)，约等于2.7倍，考虑到cache缓存的影响，认为收益一 致。 

大包搬运，实际收益 $2 5 \% +$ ，与经验值一致。 

# 总结

优化点一和优化点二的适用场景，需要shape足够大，数据量足够多，才能分满核和使 能最优的基本块。大shape场景下，MTE2 Bound算子可参考此案例的优化手段。 

# 3.10.4.3 Matmul 高阶 API 使能纯 Cube 模式

# 案例介绍

本案例呈现了在矩阵乘算子场景中，使能Matmul高阶API的纯Cube模式对算子性能的 提升效果。如下图所示，Matmul API默认使用MIX模式，即用户从AIV侧发起消息，通 过消息通信框架中转消息后，在AIC侧执行Matmul计算。这套消息处理机制会带来额 外的Scalar性能开销。相较于MIX模式，纯Cube模式可以直接跳过消息通信框架，完 成Matmul计算，提升算子性能。 


图 3-168 默认 MIX 模式的 Matmul 流程示意图


![](images/4ba5c8b281d948116192fac695b932c82b006d69b4866c6c087c0de9908c4a84.jpg)


使能纯Cube模式的适用场景 

非融合算子，只有矩阵计算的场景。即相较于MIX模式（包含矩阵计算和矢量计 算），没有矢量计算的场景。本案例的算子规格如下： 


表3-34 算子用例规格


<table><tr><td>输入</td><td>Shape</td><td>Data type</td><td>Format</td></tr><tr><td>a</td><td>128, 64</td><td>float16</td><td>ND</td></tr><tr><td>b</td><td>64, 30720</td><td>float16</td><td>ND</td></tr></table>

当前案例使用的AI处理器共24个核，每个核中包含1个AIC核和2个AIV核。 

Tiling参数如下： 

原始shape： $\mathtt { M } = 1 2 8$ , N=30720, $\mathsf { K } \mathsf { = } 6 4$ 。 

单核shape： 

MIX场景：按48个AIV核进行切分，singleCoreM=128，singleCoreN $\mathtt { \Pi } = 6 4 0$ singleCoreK $\mathtt { - 6 4 }$ 。 

纯Cube场景：按24个AIC核进行切分，singleCoreM=128， singleCoreN=1280，singleCoreK $\mathtt { - 6 4 }$ 。 

基本块shape：baseM=128，baseN $\mathtt { 1 = 2 5 6 }$ ，baseK $\mathtt { \mathtt { = 6 4 } }$ 。 

L1相关Tiling参数：stepM=1，stepN=1，stepKa=4，stepKb $^ { - 4 }$ ，depthA1 $^ { = 8 }$ ， depthB1=8。 

# 获取性能数据

使用msProf工具获取算子仿真流水图和上板Profiling数据。因为纯Cube模式主要优化 Scalar流水性能，可以重点分析Scalar的流水情况。 

# 分析主要瓶颈点

优化前的Profiling数据如下，从C列的aic_time数据可以看出，多个核中最大算子 执行耗时为17.85us。从G列的aic_scalar_time数据可以看出，Scalar平均耗时为 15.02us，性能瓶颈在Scalar流水。 

<table><tr><td>1</td><td>block</td><td>id</td><td>sub block</td><td>ref</td><td>C</td><td>D</td><td>E</td><td>F</td><td>G</td><td>H</td><td>I</td><td>J</td><td>K</td><td>L</td><td>M</td><td>N</td><td>O</td><td>P</td><td>Q</td><td>R</td><td>S</td><td>T</td></tr><tr><td>1</td><td>sub block</td><td>id</td><td>sub block</td><td>ref</td><td>acc. totali</td><td>acc. sub block</td><td>acc. rateri</td><td>acc. rateri</td><td>acc. rateri</td><td>acc. rateri</td><td>acc. rateri</td><td>acc. rateri</td><td>acc. rateri</td><td>acc. active bi</td><td>acc. rateri</td><td>acc. rateri</td><td>acc. rateri</td><td>acc. rateri</td><td>acc. rateri</td><td>acc. rateri</td><td>acc. rateri</td><td>acc. rateri</td></tr><tr><td>1</td><td>sub block</td><td>id</td><td>sub block</td><td>ref</td><td>23045</td><td>1,807,697</td><td>1,807,697</td><td>1,807,697</td><td>1,807,697</td><td>1,807,697</td><td>1,807,697</td><td>1,807,697</td><td>1,807,697</td><td>1,807,697</td><td>1,807,697</td><td>1,807,696</td><td>1,807,697</td><td>1,807,697</td><td>1,807,697</td><td>1,807,697</td><td>1,807,697</td><td>1,807,697</td></tr><tr><td>2</td><td>sub block</td><td>id</td><td>sub block</td><td>ref</td><td>23045</td><td>2,393,978</td><td>2,117,919</td><td>16,897,687</td><td>16,897,687</td><td>1,849,378</td><td>1,855,514</td><td>1,855,514</td><td>1,857,629</td><td>1,874,329</td><td>1,874,329</td><td>1,874,329</td><td>1,874,329</td><td>1,874,329</td><td>1,874,329</td><td>1,874,329</td><td>1,874,329</td><td>1,874,329</td></tr><tr><td>3</td><td>sub block</td><td>id</td><td>sub block</td><td>ref</td><td>23045</td><td>2,118,189</td><td>1,037,703</td><td>11,856,522</td><td>11,856,522</td><td>1,580,903</td><td>1,535,454</td><td>1,535,454</td><td>1,579,629</td><td>1,476,447</td><td>1,476,447</td><td>1,476,447</td><td>1,476,447</td><td>1,476,447</td><td>1,476,447</td><td>1,476,447</td><td>1,476,447</td><td>1,476,447</td></tr><tr><td>4</td><td>sub block</td><td>id</td><td>sub block</td><td>ref</td><td>23045</td><td>2,442,322</td><td>1,448,322</td><td>12,114,124</td><td>12,114,124</td><td>1,648,070</td><td>1,648,070</td><td>1,648,070</td><td>1,648,070</td><td>1,648,070</td><td>1,648,070</td><td>1,648,070</td><td>1,648,070</td><td>1,648,070</td><td>1,648,070</td><td>1,648,071</td><td>1,648,071</td><td>1,648,071</td></tr><tr><td>5</td><td>sub block</td><td>id</td><td>sub block</td><td>ref</td><td>23045</td><td>1,715,879</td><td>1,618,577</td><td>16,874,454</td><td>16,874,454</td><td>1,618,577</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,515</td><td>1,653,515</td></tr><tr><td>6</td><td>sub block</td><td>id</td><td>sub block</td><td>ref</td><td>23045</td><td>1,692,973</td><td>1,692,973</td><td>16,876,587</td><td>16,876,587</td><td>1,692,973</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,516</td><td>1,653,515</td><td>1,653,515</td></tr><tr><td>7</td><td>sub block</td><td>id</td><td>sub block</td><td>ref</td><td>23045</td><td>1,658,619</td><td>1,658,619</td><td>1,612,155</td><td>1,612,155</td><td>1,630,757</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,525</td><td>1,653,515</td><td>1,653,515</td></tr><tr><td>8</td><td>sub block</td><td>id</td><td>sub block</td><td>ref</td><td>23045</td><td>13,601,62</td><td>2,518,3</td><td>1,548,405</td><td>1,548,405</td><td>1,648,138</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,5275</td><td>1,653,515</td><td>1,653,515</td></tr><tr><td>9</td><td>sub block</td><td>id</td><td>sub block</td><td>ref</td><td>23045</td><td>18,002,22</td><td>2,192,182</td><td>1,681,002</td><td>1,681,002</td><td>1,681,002</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,526</td><td>1,653,515</td><td>1,653,515</td></tr><tr><td>10</td><td>sub block</td><td>id</td><td>sub block</td><td>ref</td><td>23045</td><td>31,605</td><td>1,627,968</td><td>1,683,009</td><td>1,683,009</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,512</td><td>1,653,515</td><td>1,653,515</td><td>1,653,515</td></tr><tr><td>11</td><td>sub block</td><td>id</td><td>sub block</td><td>ref</td><td>23045</td><td>10,077,568</td><td>32,389</td><td>1,186</td><td>1,093</td><td>1,578,218</td><td>1,768,881</td><td>1,688,881</td><td>1,688,881</td><td>1,687,307</td><td>1,687,307</td><td>1,687,307</td><td>1,687,307</td><td>1,687,307</td><td>1,687,307</td><td>1,687,305</td><td>1,687,306</td><td>1,687,306</td></tr><tr><td>12</td><td>sub block</td><td>id</td><td>sub block</td><td>ref</td><td>23045</td><td>20,002,22</td><td>1,689,002</td><td>1,689,002</td><td>1,689,002</td><td>1,689,002</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,65,525</td><td>1,653,515</td><td>1,653,515</td></tr><tr><td>13</td><td>sub block</td><td>id</td><td>sub block</td><td>ref</td><td>23045</td><td>12,776,585</td><td>1,625,04</td><td>1,614,094</td><td>1,614,094</td><td>1,768,727</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,5025</td><td>1,653,515</td><td>1,653,515</td></tr><tr><td>14</td><td>sub block</td><td>id</td><td>sub block</td><td>ref</td><td>23045</td><td>13,374</td><td>1,48</td><td>0,074</td><td>15,047,984</td><td>15,047,984</td><td>1,752,189</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,5225</td><td>1,653,5025</td><td>1,653,515</td><td>1,653,515</td></tr><tr><td>15</td><td>sub block</td><td>id</td><td>sub block</td><td>ref</td><td>23045</td><td>20,002,22</td><td>1,681,002</td><td>1,681,002</td><td>1,681,002</td><td>1,681,002</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,514</td><td>1,653,5225</td><td>1,653,5025</td><td>1,653,5025</td><td>1,653,5025</td><td>1,653,515</td><td>1,653,515</td></tr><tr><td>16</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>17</td><td>sub block</td><td>id</td><td>sub block</td><td>ref</td><td>23045</td><td>17,202,373</td><td>1,509,2</td><td>1,520,819</td><td>17,536,822</td><td>17,536,822</td><td>1,708,001</td><td>1,653,514</td><td>1,653,514</td><td>1,660,101</td><td>1,653,504</td><td>1,653,504</td><td>1,653,5025</td><td>1,653,5025</td><td>17,274,773</td><td>3,988,649</td><td>1,983,422</td><td>133,730,934</td></tr><tr><td>18</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>19</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>20</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>21</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>22</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>23</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>24</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>25</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>26</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>27</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>28</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>29</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>30</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>31</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>32</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr></table>

优化前的流水图如下，由于默认为MIX模式，每次Matmul计算均涉及消息通信框 架对消息进行处理，Scalar流水重，性能开销较大，如下图红框所示。 

<table><tr><td>Record</td><td>Save</td><td>Load</td><td colspan="14">trace.json</td></tr><tr><td></td><td></td><td></td><td></td><td>μs</td><td></td><td></td><td>μs</td><td></td><td></td><td>μs</td><td></td><td></td><td>μs</td><td></td><td></td><td>μs</td></tr><tr><td colspan="17">·SCALAR (pid 10)</td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td colspan="17">·SCALARLDST (pid 20)</td></tr><tr><td>SCALARLDST_1</td><td></td><td></td><td></td><td></td><td></td><td>LOL</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>SCALARLDST_2</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>SCALARLDST_3</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>SCALARLDST_4</td><td></td><td></td><td></td><td></td><td>ST-</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>SCALARLDST_5</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>SCALARLDST_6</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>SCALARLDST_7</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>SCALARLDST_8</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>SCALARLDST_9</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>SCALARLDST_10</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>SCALARLDST_11</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>SCALARLDST_12</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>SCALARLDST_13</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>SCALARLDST_14</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td colspan="17">·CUBE (pid 40)</td></tr><tr><td>CUBE_1</td><td></td><td></td><td></td><td></td><td></td><td>W-</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>CUBE_2</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>CUBE_3</td><td></td><td></td><td></td><td></td><td></td><td>Wt-</td><td>Wt-</td><td></td><td></td><td></td><td></td><td></td><td>Wt-</td><td></td><td></td><td></td></tr><tr><td>CUBE_4</td><td></td><td></td><td></td><td></td><td></td><td>WAIT_FLAG</td><td>WAIT_FLAG</td><td>WAIT_FLAG</td><td>WAIT_FLAG</td><td>WAIT_FLAG</td><td>WAIT_FLAG</td><td>Wt-</td><td></td><td></td><td></td><td></td></tr><tr><td colspan="17">·MTE1 (pid 50)</td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td colspan="17">·MTE2 (pid 60)</td></tr><tr><td>MTE2_1</td><td></td><td></td><td></td><td></td><td></td><td rowspan="3">NO</td><td rowspan="3">MOV</td><td rowspan="3">MOV</td><td></td><td rowspan="3">MOV_OUT</td><td rowspan="3">MOV</td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>MTE2_2</td><td></td><td></td><td></td><td></td><td></td><td></td><td rowspan="2">MOV</td><td rowspan="3"></td><td rowspan="3"></td><td rowspan="3"></td><td></td></tr><tr><td>MTE2_3</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>MTE2_4</td><td></td><td></td><td></td><td></td><td></td><td>MOV</td><td></td><td></td><td>MOV_OUT</td><td>MOV</td><td></td><td></td><td></td></tr><tr><td colspan="17">·MTE3 (pid 70)</td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td colspan="17">·FIXP (pid 80)</td></tr><tr><td>FIXP_1</td><td></td><td></td><td></td><td></td><td></td><td rowspan="3">VAL-</td><td rowspan="3"></td><td rowspan="2">FIX_LOC-</td><td rowspan="2">FIX_LOC-</td><td rowspan="2">FIX_LOC_TO_DST</td><td rowspan="2">W-</td><td rowspan="2">FIX_LOC_TO_DST</td><td rowspan="3">FIX_LOC-</td><td rowspan="3">FL-</td><td rowspan="3"></td><td></td></tr><tr><td>FIXP_2</td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>FIXP_3</td><td></td><td></td><td></td><td></td><td></td><td>WAI-</td><td></td><td></td><td>WAI-</td><td></td><td></td></tr></table>

# 设计优化方案

默认MIX模式下，用户在AIV侧发起消息，通过消息通信框架中转消息后，在AIC侧执 行Matmul计算。基于这样的流程，用户使用Matmul高阶API编写算子代码时，可以使 用REGIST_MATMUL_OBJ宏，无需区分AIV和AIC，但也因这套消息处理机制导致产生 了额外的性能开销，如图1 默认MIX模式的Matmul流程示意图所示。 

实现默认MIX模式的具体步骤如下： 

步骤1 Kernel侧，定义Matmul对象。 

#include "lib/matmul_intf.h" 

```julia
using A_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, AType>;  
using B_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, BType>;  
using C_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, CType>;  
using BIAS_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, BiasType>;  
AscendC::Matmul<A_TYPE, B_TYPE, C_TYPE, BIAS_TYPE, CFG_NORM> matmulObj; 
```

步骤2 Host侧，Matmul多核Tiling对象调用SetDim接口设置参与运算的核数。 

```cpp
auto ascendcPlatform = platform_ascending::PlatformAscendCManager::GetInstance();  
matmul_tiling::MultiCoreMatmulTiling cubeTiling(* ascendcPlatform);  
int32_t numBlocks = ascendcPlatform->GetCoreNumAiv(); // MIX模式使用GetCoreNumAiv获取AI处理器可用的核数。  
cubeTiling.SetDim(numBlocks); 
```

步骤3 调用核函数，参考核函数定义和调用，设置核函数的numBlocks参数配置。 

```txt
matmul_custom_do(ascendcPlatform->GetCoreNumAic(), stream, x1, x2, bias, y, workspaceDevice, tilingDevice); // MIX模式下，启动时，按照AIV和AIC组合启动，numBlocks用于设置启动多少个AI Core。 
```

----结束 

在没有矢量计算的算子场景下，可以跳过消息通信框架的机制，使能纯Cube模式完成 Matmul计算，减少消息通信的性能开销，提升算子性能。 


图 3-169 纯 Cube 模式的 Matmul 流程示意图


![](images/f663a91692e6ba17bb790882c62447b70544f75153991fe8ad074aca57740b8b.jpg)


Matmul API使能纯Cube模式的完整样例请参考Matmul API性能优化样例。使能纯 Cube模式的主要步骤如下： 

步骤1 Kernel侧，在定义Matmul对象的代码中，包含matmul_intf.h头文件前设置 ASCENDC_CUBE_ONLY宏。 

```cpp
define ASCENDC_CUBE_ONLY // 在#include "lib/matmul_intf.h"前，设置ASCENDC_CUBE_ONLY宏 #include "lib/matmul_intf.h" using A_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, AType>; using B_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, BType>; using C_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, CType>; using BIAS_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, BiasType>; AscendC::Matmul<A_TYPE, B_TYPE, C_TYPE, BIAS_TYPE, CFG_NORM> matmulObj; 
```

步骤2 Host侧，Matmul多核Tiling对象调用SetDim接口设置参与运算的核数。 

```cpp
auto ascendcPlatform = platform_ascending::PlatformAscendCManager::GetInstance();  
matmul_tiling::MultiCoreMatmulTiling cubeTiling(*ascendingPlatform);  
int32_t numBlocks = ascendcPlatform->GetCoreNumAic(); //纯Cube模式使用GetCoreNumAic接口获取AI处理器可用的核数。  
cubeTiling.SetDim(numBlocks); 
```

步骤3 调用核函数，参考核函数定义和调用，设置核函数的numBlocks参数配置。 

```txt
matmulcustom_do(ascendcPlatform->GetCoreNumAic(), stream, x1, x2, bias, y, workspaceDevice, tilingDevice); // 仅包含Cube计算的算子，numBlocks用于设置启动多少个AIC。 
```

步骤4 Kernel侧，核函数实现中增加AIV侧返回分支。 

```cpp
extern "C" __global __aicore__ void matmul/custom(GM_ADDR a, GM_ADDR b, GM_ADDR bias, GM_ADDR c, GM_ADDR workspace, GM_ADDR tilingGm)  
{ if (g_coreType == AscendC::AIV) { // 纯Cube模式，AIV侧直接return return; } // 其他代码  
} 
```

----结束 

# 验证优化方案性能收益

优化后的Profiling数据如下，从C列的aic_time数据来看，多个核中最大算子执行 耗时为11.21us，较优化前的17.85us有较大提升。从G列的aic_scalar_time数据来 看，Scalar平均耗时从优化前的15.02us降低至5.17us。 

<table><tr><td colspan="2">A</td><td colspan="2">B</td><td colspan="2">C</td><td colspan="2">D</td><td colspan="2">E</td><td colspan="2">F</td><td colspan="2">G</td><td colspan="2">H</td><td colspan="2">I</td><td colspan="2">J</td><td colspan="2">K</td><td colspan="2">L</td><td colspan="2">M</td><td colspan="2">N</td><td colspan="2">O</td><td colspan="2">P</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>8</td><td>9</td><td>10</td><td>11</td><td>12</td><td>13</td><td>14</td><td>15</td><td>16</td><td>17</td><td>18</td><td>19</td><td>20</td><td>21</td><td>22</td><td>23</td><td>24</td><td>25</td><td>26</td><td>27</td><td>28</td><td>29</td><td>30</td><td>31</td><td>32</td><td>33</td><td>34</td><td>35</td><td></td><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>00.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>-0.000000</td><td></td><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td colspan="8"></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td colspan="9"></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td colspan="9"></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td colspan="9"></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td colspan="9"></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td colspan="10"></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td colspan="10"></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td colspan="10"></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.00000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td>0.000000</td><td></td><td></td><td></td><td></td></tr></table>

优化后的流水图如下。对比优化前的流水图，红框所示位置的Scalar流水明显变稀 疏。纯Cube模式相较于MIX模式，减少了对消息通信的处理，优化了整体Scalar 性能开销。 

![](images/bb7efe4977aab146f9a2e9cb1ada121f8ece14fdf30ca863190ea25c34e65577.jpg)


# 总结

在只有矩阵计算，没有矢量计算的场景下，可以考虑使能纯Cube模式，优化Matmul 计算中的消息通信性能开销，提升算子性能。 

# 3.10.4.4 Matmul 高阶 API 使能 MDL 模板

# 案例介绍

本案例呈现了在矩阵乘算子场景中，使用Matmul高阶API进行矩阵乘法计算，使能 MDL模板对算子性能的提升效果。在MDL模板中，MTE2流水从Global Memory到 A1/B1的数据搬运为一次性大包搬运，即一次MTE2能搬入多个Matmul计算的基本 

块，提升带宽利用率，使后续的MTE1流水尽可能复用A1/B1内基本块的缓存数据，减 少MTE2的搬运次数。MDL模板的详细介绍请参考MatmulConfig。 

MDL模板的适用场景 

一般适用于MTE2循环搬运次数多的大shape场景，MDL模板在A1/B1中缓存多次 计算需要的数据，避免MTE2频繁搬运。 

MDL模板的约束条件 

MDL模板的TCubeTiling结构体需要满足TCubeTiling约束条件和MDL模板补充约 束条件，具体请参考TCubeTiling结构体。 

本案例的算子规格如下： 


表 3-35 算子规格


<table><tr><td>输入</td><td>Shape</td><td>Data type</td><td>Format</td></tr><tr><td>a</td><td>128, 1024</td><td>float16</td><td>ND</td></tr><tr><td>b</td><td>1024, 30720</td><td>float16</td><td>ND</td></tr></table>

当前案例使用的AI处理器共24个核，每个核中包含1个AIC核和2个AIV核。 

Tiling参数如下： 

原始shape：M=128, N=30720, K=1024。 

单核shape：按24个AIC核进行切分，singleCoreM=128，singleCoreN=1280， singleCoreK=1024。 

对于B矩阵，沿着N轴进行切分，切分成24份的singleCoreN，单核上处理K * SingleCoreN大小的数据。对于A矩阵，M轴不进行切分即singleCoreM=M，单核 上处理singleCoreM * K大小的数据。总共24个核参与计算。 

基本块shape：baseM=128，baseN=256，baseK=64。 

L1相关Tiling参数：stepM=1，stepN=1，stepKa=4，stepKb=4，depthA1=8， depthB1=8。 

# 获取性能数据

使用msProf工具获取算子仿真流水图和上板Profiling数据，因为MDL模板主要优化 MTE2搬运效率，重点分析MTE2的流水情况。 

# 分析主要瓶颈点

优化前的Profiling数据如下，Matmul默认为Norm模板。从C列的aic_time数据可 以看出，多个核中最大算子执行耗时为83.68us。从C列的aic_time、L列的 aic_mte2_time和M列的aic_mte2_ratio几组数据来看，MTE2平均耗时75.64us， 耗时占比达到92%以上，因此需要优化MTE2流水的耗时。 

<table><tr><td></td><td>A</td><td>B</td><td>C</td><td>D</td><td>E</td><td>F</td><td>G</td><td>H</td><td>I</td><td>J</td><td>K</td><td>L</td><td>M</td><td>N</td><td>O</td><td>P</td><td>Q</td><td>R</td><td>S</td><td>T</td><td>V</td><td></td></tr><tr><td>1</td><td>block id</td><td>sub block id</td><td>arc (microns)</td><td>arc total cycles arc (circles)</td><td>arc ratio ratio arc (circles)</td><td>arc ratio ratio arc (circles)</td><td>arc ratio ratio arc (circles)</td><td>arc ratio ratio arc (circles)</td><td>arc ratio ratio arc (circles)</td><td>arc ratio ratio arc (circles)</td><td>arc ratio ratio arc (circles)</td><td>arc ratio ratio arc (circles)</td><td>arc ratio ratio arc (circles)</td><td>arc ratio ratio arc (circles)</td><td>arc ratio ratio arc (circles)</td><td>arc ratio ratioarc (circles)</td><td>arc ratio ratioarc (circles)</td><td>arc ratio ratioarc (circles)</td><td>arc ratio ratioarc (circles)</td><td>arc ratio ratioarc (circles)</td><td>arc ratio ratioarc (circles)</td><td>arc ratio ratioarc (circles)</td></tr><tr><td>2</td><td>0</td><td>sub0.6454</td><td>15493</td><td>24.42-18.62</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>4.4124</td><td>4.4124</td><td></td></tr><tr><td>3</td><td>1</td><td>sub0.6454</td><td>15493</td><td>24.42-18.62</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.8000</td><td>0.8000</td><td>0.8000</td><td>0.8000</td><td>0.8000</td><td>4.4124</td><td>4.4124</td><td></td></tr><tr><td>4</td><td>2</td><td>sub0.6454</td><td>15493</td><td>24.42-18.62</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.9000</td><td>0.9000</td><td>0.9000</td><td>0.9000</td><td>0.9000</td><td>4.4124</td><td>4.4124</td><td></td></tr><tr><td>5</td><td>3</td><td>sub0.6454</td><td>15493</td><td>24.42-18.62</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.1000</td><td>0.1000</td><td>0.1000</td><td>0.1000</td><td>0.1000</td><td>4.4124</td><td>4.4124</td><td></td></tr><tr><td>6</td><td>4</td><td>sub0.6454</td><td>15493</td><td>24.42-18.62</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.2000</td><td>0.2000</td><td>0.2000</td><td>0.2000</td><td>0.2000</td><td>4.4124</td><td>4.4124</td><td></td></tr><tr><td>7</td><td>5</td><td>sub0.6454</td><td>15493</td><td>24.42-18.62</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.4200</td><td>0.4200</td><td>0.4200</td><td>0.4200</td><td>0.4200</td><td>4.4124</td><td>4.4124</td><td></td></tr><tr><td>8</td><td>6</td><td>sub0.6454</td><td>15493</td><td>24.42-18.62</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.5200</td><td>0.5200</td><td>0.5200</td><td>0.5200</td><td>0.5200</td><td>4.4124</td><td>4.4124</td><td></td></tr><tr><td>9</td><td>7</td><td>sub0.6454</td><td>15493</td><td>24.42-18.62</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.6200</td><td>0.6200</td><td>0.6200</td><td>0.6200</td><td>0.6200</td><td>4.4124</td><td>4.4124</td><td></td></tr><tr><td>10</td><td>8</td><td>sub0.6454</td><td>15493</td><td>24.42-18.62</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.3200</td><td>0.3200</td><td>0.3200</td><td>0.3200</td><td>0.3200</td><td>4.4124</td><td>4.4124</td><td></td></tr><tr><td>11</td><td>9</td><td>sub0.6454</td><td>15493</td><td>24.42-18.62</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.0000</td><td>0.0000</td><td>0.0000</td><td>0.0000</td><td>0.0000</td><td>4.4124</td><td>4.4124</td><td></td></tr><tr><td>12</td><td>10</td><td>sub0.6454</td><td>15493</td><td>24.42-18.62</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0,0000</td><td>0.0000</td><td>0.0000</td><td>0.0000</td><td>0.0000</td><td>4.4124</td><td>4.4124</td><td></td></tr><tr><td>13</td><td>11</td><td>sub0.6454</td><td>15493</td><td>24.42-18.62</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0,9100</td><td>0.9100</td><td>0.9100</td><td>0.9100</td><td>0.9100</td><td>4.4124</td><td>4.4124</td><td></td></tr><tr><td>14</td><td>12</td><td>sub0.6454</td><td>15493</td><td>24.42-18.62</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0,1000</td><td>0.1000</td><td>0.1000</td><td>0.1000</td><td>0.1000</td><td>4.4124</td><td>4.4124</td><td></td></tr><tr><td>15</td><td>13</td><td>sub0.6454</td><td>15493</td><td>24.42-18.62</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0,2000</td><td>0.2000</td><td>0.2000</td><td>0.2000</td><td>0.2000</td><td>4.4124</td><td>4.4124</td><td></td></tr><tr><td>16</td><td>14</td><td>sub0.6454</td><td>15493</td><td>24.42-18.62</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0,3200</td><td>0.3200</td><td>0.3200</td><td>0.3200</td><td>0.3200</td><td>4.4124</td><td>4.4124</td><td></td></tr><tr><td>17</td><td>15</td><td>sub0.6454</td><td>15493</td><td>24.42-18.62</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0,5200</td><td>0.5200</td><td>0.5200</td><td>0.5200</td><td>0.5200</td><td>4.4124</td><td>4.4124</td><td></td></tr><tr><td>18</td><td>16</td><td>sub0.6454</td><td>15493</td><td>24.42-18.62</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0,6200</td><td>0,6200</td><td>0,6200</td><td>0,6200</td><td>0,6200</td><td>4.4124</td><td>4.4124</td><td></td></tr><tr><td>19</td><td>17</td><td>sub0.6454</td><td>15493</td><td>24.42-18.62</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0,7250</td><td>0,7250</td><td>0,7250</td><td>0,7250</td><td>0,7250</td><td>4.4124</td><td>4.4124</td><td></td></tr><tr><td>20</td><td>18</td><td>sub0.6454</td><td>15493</td><td>24.42-18.62</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0,9100</td><td>0,9100</td><td>0,9100</td><td>0,9100</td><td>0,9100</td><td>0,9100</td><td>4.4124</td><td>4.4124</td><td></td></tr><tr><td>21</td><td>20</td><td>sub0.6454</td><td>15493</td><td>24.42-18.62</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0,9100</td><td>0,1000</td><td>0,1000</td><td>0,1000</td><td>0,1000</td><td>0,1000</td><td>4.4124</td><td>4.4124</td><td></td></tr><tr><td>22</td><td>21</td><td>sub0.6454</td><td>15493</td><td>24.42-18.62</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0,9100</td><td>0,5200</td><td>0,5200</td><td>0,5200</td><td>0,5200</td><td>0,5200</td><td>4.4124</td><td>4.4124</td><td></td></tr><tr><td>23</td><td>22</td><td>sub0.6454</td><td>15493</td><td>24.42-18.62</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0.7868</td><td>0,9100</td><td>0,3200</td><td>0,3200</td><td>0,3200</td><td>0,3200</td><td>0,3200</td><td>4.4124</td><td>4.4124</td><td></td></tr></table>

优化前的流水图如下，MTE2分多次从Global Memory搬运基本块到A1/B1。由于 输入的矩阵Shape较大，MTE2循环搬运的次数多，但每次只搬运1个基本块，导 致带宽利用率低，整体的MTE2搬运耗时长。进而影响后续的MTE1和MMAD流 水，导致流水之间同步等待时间偏长。如红框所示，第一个基本块 （baseM*baseN）的计算需要调用16次MMAD指令（singleCoreK/baseK=16）， 从左侧的第1个MMAD指令调用开始，到右侧的第16个MMAD指令调用结束，期 间耗时10.899us，其中大部分是流水同步等待耗时。 

![](images/8df61db1d0be72df7ddf40e2337b1d59da0f087adc8a9a55a03f352fb8d55638.jpg)


# 设计优化方案

下图是默认的Norm模板的Matmul计算流水示意图，MTE2分多次从Global Memory 搬运基本块到A1或B1，每次只搬运一个基本块。Norm模板的优势为启动开销小，可 以提前启动MTE1流水；Norm模板的劣势为在大Shape场景，MTE2搬运次数多，搬运 带宽利用率低，整体性能开销大。 


图 3-170 默认 Norm 模板流水示意图


![](images/2895e51d27b5f02d83506d67eeedf3c261ed88424d11ee8eed0006589f93a415.jpg)


实现Norm模板的具体步骤如下： 

步骤1 创建Matmul对象，使用默认的Norm模板参数CFG_NORM。 

```cpp
define ASCENDC_CUBE_ONLY
#include "lib/matmul_intf.h"
using A_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, AType>;
using B_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, BType>;
using C_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, CType>;
using BIAS_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, BiasType>;
AscendC::Matmul<A_TYPE, B_TYPE, C_TYPE, BIAS_TYPE, CFG_NORM> matmulObj; // 使用CFG_NORM定义Matmul对象 
```

----结束 

下图是MDL模板的Matmul计算流水示意图，MTE2一次性从Global Memory搬运多个 基本块到A1或B1，每次搬运stepM * stepKa个基本块到A1或搬运stepN * stepKb个基 本块到B1。MDL模板的优势为MTE2一次性搬运多个基本块，带宽利用率高，后续的 MTE1流水能尽可能复用A1或B1的缓存数据，MTE2重复搬运次数少。MDL模板的劣势 为MTE2头开销时间较长，MTE1流水需要等待MTE2流水完成后才启动，MTE1启动时 间晚。 


图 3-171 MDL 模板流水示意图


![](images/0dbac23e86ebe0501971505adfccf9df07d7b1273a47040e1f871a68c1ecab08.jpg)


Matmul API使能MDL模板的完整样例请参考Matmul API性能优化样例。使能MDL模 板的主要步骤如下： 

步骤1 创建Matmul对象，使用默认的MDL模板参数CFG_MDL。 

```cpp
define ASCENDC_CUBE_ONLY
#include "lib/matmul_intf.h"
using A_TYPE = AscendC::MatmuleType<AscendC::TPosition::GM, CubeFormat::ND, AType>;
using B_TYPE = AscendC::MatmuleType<AscendC::TPosition::GM, CubeFormat::ND, BType>;
using C_TYPE = AscendC::MatmuleType<AscendC::TPosition::GM, CubeFormat::ND, CType>;
using BIAS_TYPE = AscendC::MatmuleType<AscendC::TPosition::GM, CubeFormat::ND, BiasType>;
AscendC::Matmul<A_TYPE, B_TYPE, C_TYPE, BIAS_TYPE, CFG_MDL> matmulObj; // 使用CFG_MDL定义Matmul对象 
```

# ----结束

# 验证优化方案性能收益

优化后的Profiling数据如下，从C列的aic_time数据可以看出，多个核中最大算子 执行耗时为53.4us，相较于优化前的83.68us有较大提升。从L列的aic_mte2_time 数据可以看出，MTE2平均耗时下降较多，从优化前的75.64us降低至46.24us。 

<table><tr><td></td><td>A</td><td>B</td><td>C</td><td>D</td><td>E</td><td>F</td><td>G</td><td>H</td><td>I</td><td>J</td><td>K</td><td>L</td><td>M</td><td>N</td><td>O</td><td>P</td><td>Q</td><td>R</td><td>S</td><td>T</td></tr><tr><td>1</td><td>block_id</td><td>sub_block_id</td><td>abcumu(ratio)</td><td>abctotal_ratio</td><td>abcubumu(ratio)</td><td>abcratio ratio</td><td>abcateratio</td><td>abcrate ratio</td><td>abcratio ratio</td><td>abcrate ratio</td><td>abcrate ratio</td><td>abcrate ratio</td><td>abcrate ratio</td><td>abcrate ratio</td><td>abcrate ratio</td><td>abcrate ratio</td><td>abcrate ratio</td><td>abcrate ratio</td><td>abcrate ratio</td><td>abcrate ratio</td></tr><tr><td>1</td><td>1</td><td>0.000</td><td>54286</td><td>0.4238</td><td>0.2975</td><td>0.2837</td><td>0.2837</td><td>0.2837</td><td>0.2837</td><td>0.2837</td><td>0.2837</td><td>0.2837</td><td>0.2837</td><td>0.2837</td><td>0.2837</td><td>0.2837</td><td>0.2837</td><td>0.2837</td><td>0.2837</td><td>0.2837</td></tr><tr><td>2</td><td>1</td><td>0.000</td><td>52.85274</td><td>0.7779</td><td>0.298243</td><td>0.434474</td><td>0.1323973</td><td>0.338783</td><td>0.337165</td><td>0.338783</td><td>0.2886222</td><td>0.4673938</td><td>0.893955</td><td>0.741414</td><td>0.0001001</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td></tr><tr><td>4</td><td>2</td><td>0.000</td><td>51.45862</td><td>0.95199</td><td>0.2185948</td><td>0.4237954</td><td>0.1244424</td><td>0.121547</td><td>0.1875135</td><td>0.327934</td><td>0.2303042</td><td>0.4497833</td><td>0.870009</td><td>0.8179812</td><td>0.0001001</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td></tr><tr><td>6</td><td>3</td><td>0.000</td><td>51.45862</td><td>0.95199</td><td>0.2185948</td><td>0.4237954</td><td>0.1244424</td><td>0.121547</td><td>0.1875135</td><td>0.327934</td><td>0.2303042</td><td>0.4497868</td><td>0.8700149</td><td>0.8179233</td><td>0.0001001</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td></tr><tr><td>8</td><td>4</td><td>0.000</td><td>52.20423</td><td>0.95199</td><td>0.2185948</td><td>0.4237954</td><td>0.1244424</td><td>0.121547</td><td>0.1875135</td><td>0.327934</td><td>0.2303042</td><td>0.4497868</td><td>0.8700149</td><td>0.7743937</td><td>0.0001001</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td></tr><tr><td>7</td><td>5</td><td>0.000</td><td>53.342183</td><td>0.98883</td><td>0.2254686</td><td>0.4236986</td><td>0.1452913</td><td>0.1862434</td><td>0.1862434</td><td>0.317955</td><td>0.2303066</td><td>0.4667858</td><td>0.8759419</td><td>0.7823203</td><td>0.0001001</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td></tr><tr><td>10</td><td>6</td><td>0.000</td><td>54.16167</td><td>0.98883</td><td>0.2254686</td><td>0.4236986</td><td>0.1452913</td><td>0.1862434</td><td>0.1862434</td><td>0.317955</td><td>0.2303066</td><td>0.4667858</td><td>0.8759419</td><td>0 7383203</td><td>0.0001001</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td></tr><tr><td>7</td><td>8</td><td>0.000</td><td>53.456163</td><td>0.97693</td><td>0.2477394</td><td>0.4250291</td><td>0.1577398</td><td>0.1873966</td><td>0.1869666</td><td>0.316561</td><td>0.2317698</td><td>0.4673866</td><td>0.8759418</td><td>0.7383299</td><td>0.0001001</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td></tr><tr><td>10</td><td>8</td><td>0.000</td><td>52.758567</td><td>0.97693</td><td>0.2477394</td><td>0.4250291</td><td>0.1577398</td><td>0.1873966</td><td>0.1869666</td><td>0.316561</td><td>0.2317698</td><td>0.4673866</td><td>0.8759418</td><td>0 7383299</td><td>0.0001001</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td></tr><tr><td>12</td><td>11</td><td>0.000</td><td>51.339458</td><td>0.9479</td><td>0.169564</td><td>0.4214887</td><td>0.14740541</td><td>0.1873966</td><td>0.1869666</td><td>0.32777</td><td>0.2317695</td><td>0.4673936</td><td>0.870333</td><td>0.8169625</td><td>0.0001001</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td></tr><tr><td>13</td><td>11</td><td>0.000</td><td>52.655515</td><td>0.97409</td><td>0.2369379</td><td>0.423933</td><td>0.15854616</td><td>0.1873966</td><td>0.1869666</td><td>0.327772</td><td>0.1869666</td><td>0.4673936</td><td>0.8658575</td><td>0.803446</td><td>0.0001001</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td></tr><tr><td>14</td><td>11</td><td>0.000</td><td>52.655515</td><td>0.97409</td><td>0.2369379</td><td>0.423933</td><td>0.15854616</td><td>0.1873966</td><td>0.1869666</td><td>0.327772</td><td>0.1869666</td><td>0.327772</td><td>0.7843967</td><td>0.7743936</td><td>0.0001001</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td></tr><tr><td>15</td><td>11</td><td>0.000</td><td>51.991383</td><td>0.98939</td><td>0.1823244</td><td>0.4189391</td><td>0.14816926</td><td>0.1873966</td><td>0.1869666</td><td>0.3191555</td><td>0.17951497</td><td>0.4682432</td><td>0.893948</td><td>0.778721</td><td>0.0001001</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td></tr><tr><td>16</td><td>14</td><td>0.000</td><td>51.72216</td><td>0.98886</td><td>0.2433838</td><td>0.4370511</td><td>0.14730511</td><td>0.1869666</td><td>0.1869666</td><td>0.329397</td><td>0.1869666</td><td>0.4673936</td><td>0.893948</td><td>0.798721</td><td>0.0001001</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td></tr><tr><td>17</td><td>16</td><td>0.000</td><td>52.441928</td><td>0.97693</td><td>0.2331694</td><td>0.4233838</td><td>0.14730511</td><td>0.1869666</td><td>0.1869666</td><td>0.329397</td><td>0.1869666</td><td>0.4673936</td><td>0.893948</td><td>0.798721</td><td>0.0001001</td><td>0.000002</td><td>0 0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td></tr><tr><td>18</td><td>17</td><td>0.000</td><td>52.441928</td><td>0.97693</td><td>0.2331694</td><td>0.4233838</td><td>0.14730511</td><td>0.1869666</td><td>0.1869666</td><td>0.329397</td><td>0.1869666</td><td>0.4682433</td><td>0.893948</td><td>0.798721</td><td>0.0001001</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td></tr><tr><td>21</td><td>18</td><td>0.000</td><td>53.474957</td><td>0.96837</td><td>0.2432342</td><td>0.423933</td><td>0.14741982</td><td>0.1873966</td><td>0.1869666</td><td>0.3283123</td><td>0.1869666</td><td>0.4673936</td><td>0.8759418</td><td>0.7383299</td><td>0.0001001</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td><td>0.000002</td></tr><tr><td>22</td><td>19</td><td>0.000</td><td>53.474957</td><td>0.96837</td><td>0.2432342</td><td>0.423933</td><td>0.14741982</td><td>0.1873966</td><td>0.1869666</td><td>0.3283123</td><td>0.1869666</td><td>0.4682433</td><td>0.8759418</td><td>0.7383299</td><td>0.0001001</td><td>0.000002</td><td>0.000002</td><td>0.4473741</td><td>0.415394</td><td>0.444346</td></tr><tr><td>23</td><td>20</td><td>0.000</td><td>53.019151</td><td>0.98129</td><td>0.2342365</td><td>0.4256255</td><td>0.1436767</td><td>0.1869666</td><td>0.1869666</td><td>0.338228</td><td>0.17437474</td><td>0.46461621</td><td>0.882383</td><td>78.189572</td><td>0.0001001</td><td>0.000002</td><td>0.000002</td><td>0.4873467</td><td>0.415494</td><td>0.443446</td></tr><tr><td>24</td><td>21</td><td>0.000</td><td>53.474957</td><td>0.98129</td><td>0.2342365</td><td>0.4256255</td><td>0.1436767</td><td>0.1869666</td><td>0.1869666</td><td>0.338228</td><td>0.17437474</td><td>0.46461621</td><td>0.882383</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td></tr><tr><td>25</td><td>22</td><td>0.000</td><td>52.848948</td><td>0.77771</td><td>0.2358216</td><td>0.4262576</td><td>0.14372739</td><td>0.1873966</td><td>0.1869666</td><td>0.329397</td><td>0.17437474</td><td>0.46461621</td><td>0.882383</td><td>78.189572</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td></tr><tr><td>26</td><td>23</td><td>0.000</td><td>52.448948</td><td>0.77771</td><td>0.2358216</td><td>0.4262576</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td></td></tr><tr><td>27</td><td>24</td><td>0.000</td><td>51.458756</td><td>0.95199</td><td>0.2198726</td><td>0.4747457</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td></td></tr></table>

优化后的流水图如下，MDL模板相较于默认的Norm模板，MTE2可以一次性搬运 多个基本块，整体的MTE2搬运次数减少了。同时因为MTE2一次搬运多个基本块 到A1/B1，后续的MTE1流水能尽量复用A1/B1的缓存数据，减少了流水同步等 待，提升了算子整体性能。如红框所示，第一个基本块（baseM*baseN）的计算 需要调用16次MMAD指令（singleCoreK/baseK=16），从左侧的第1个MMAD指 令调用开始，到右侧的第16个MMAD指令调用结束耗时约5.198us，较优化前的 10.899us提升较大，其中流水同步等待时间大幅减少。 

![](images/30a26c2170ac36708aa4edc4d1e5d5ae9243eea0cd0327b809e6656624b1aad9.jpg)


# 总结

大Shape输入、MTE2搬运次数多，且MTE1流水等MTE2流水的同步等待耗时较长的场 景下，可以使能MDL模板。通过实现MTE2从Global Memory一次性搬入多个基本块 到A1或B1，使后续的MTE1流水能尽量复用A1/B1的缓存数据，减少MTE2的搬运次 数，从而提升算子性能。 

# 3.10.4.5 Matmul 高阶 API 使能 UnitFlag

# 案例介绍

本案例呈现了在矩阵乘算子场景中，使用Matmul高阶API进行矩阵乘法计算，使能 UnitFlag功能对算子性能的提升效果。UnitFlag功能为AIC核中MMAD计算指令和 FIXPIPE数据搬运指令提供了基于内存访问的细粒度同步，使计算与搬运流水并行。使 能UnitFlag功能的方式为将MatmulConfig中的enUnitFlag参数设置为true。 enUnitFlag参数的详细介绍请参考MatmulConfig。 

使能UnitFlag的适用场景 

算子的MMAD流水和FIXPIPE流水之间串行执行，FIXPIPE等待MMAD计算完成才 搬出结果，这个指令同步等待的时间在算子整体执行耗时中占比较高。这种场景 可以使能UnitFlag功能，以获得MMAD和FIXPIPE流水并行的性能收益。如果算子 原本的MMAD、FIXPIPE流水可以被其他流水掩盖（比如MTE2 Bound），这时使 能UnitFlag功能总体收益很小。 

使能UnitFlag的约束条件 

UnitFlag功能仅支持Norm、IBShare、MDL三个模板。 

使能UnitFlag功能时，不支持算子内同时存在CO1(L0C)搬出到Global Memory和A1(L1)搬出到Global Memory的两种流水。 

使能UnitFlag功能时，若同时使能L0C累加功能，不支持多次Iterate计算、一 次GetTensorC输出。 

本案例的算子规格如下： 


表3-36 算子规格


<table><tr><td>输入</td><td>Shape</td><td>Data type</td><td>Format</td></tr><tr><td>a</td><td>128, 64</td><td>float16</td><td>ND</td></tr><tr><td>b</td><td>64, 30720</td><td>float16</td><td>ND</td></tr></table>

当前案例使用的AI处理器共20个核，每个核包含1个AIC核和2个AIV核。 

算子的Tiling参数如下： 

原始shape： $\mathtt { M } = 1 2 8$ , N=30720, K=64。 

单核shape：按20个AIC核进行切分，singleCoreM=128，singleCoreN=1536， singleCoreK $\mathtt { \mathtt { = 6 4 } }$ 。 

对于B矩阵，沿着N轴进行切分，切分成20份singleCoreN，单核上处理K * SingleCoreN大小的数据。对于A矩阵，M轴不进行切分即singleCoreM=M，单核 上处理singleCoreM * K大小的数据。总共20个核参与计算。 

基本块shape：baseM=128，baseN=256，baseK=64。 

L1相关Tiling参数：stepM=1，stepN=1，stepKa=4，stepKb=4，depthA1=8， depthB1=8。 

# 获取性能数据

使用msProf工具获取算子仿真流水图和上板Profiling数据。因为UnitFlag功能主要优 化MMAD和FIXPIPE流水串行问题，所以获取性能数据后重点分析Cube、FIXPIPE的流 水情况。 

# 分析主要瓶颈点

优化前的流水图如下。如下图中红框所示，每一轮MMAD计算流水和FIXPIPE数据 搬出流水之间都是串行执行的，完成MMAD计算后才开始FIXPIPE数据搬出，考虑 实现MMAD与FIXPIPE之间流水并行来优化算子性能。 

![](images/319a6c2d95984acdb30769ee67955e648e835af090851264e860131e187c17bc.jpg)


优化前的Profiling数据如下，从C列的aic_time数据可以看出，多个核中最大算子 执行耗时为37.39us。 

![](images/760a3c1f4e30e4cc1919c007e0242ab5bdca060dcd38f5dd4cf1484a3316f5a2.jpg)


# 设计优化方案

如下图所示，未开启UnitFlag功能时，MMAD和FIXPIPE是指令级别的同步，FIXPIPE 指令需要等MMAD指令执行完成才进行结果搬出，MMAD和FIXPIPE之间流水串行。 


图 3-172 未开启 UnitFlag 功能


![](images/870021dc16ead1ec521baaf28bb6fbcb301bb505000fa67f38a97487fd653dcd.jpg)


如下图所示，开启UnitFlag功能时，MMAD和FIXPIPE指令是512B大小的细粒度同步。 在一条MMAD指令执行过程中，每当完成一个512B数据结果的计算，FIXPIPE立即开 始搬出该512B的数据，从而实现MMAD和FIXPIPE之间的流水并行，提升算子性能。 


图 3-173 开启 UnitFlag 功能


![](images/78f00ed42777720b1a15ba1d945a6d048ad2cb90a0ae9595ebfe704def402b62.jpg)


Matmul API使能UnitFlag功能的完整样例请参考Matmul API性能优化样例。使能 UnitFlag功能的主要步骤如下： 

步骤1 自定义MatmulConfig模板参数，将其中的enUnitFlag参数设置为true，使能UnitFlag 功能。 

aicore__inline constexpr MatmulConfig GetCustomMDLCFG()   
{ auto mmCfg $=$ CFG_MDL; mmCfg.enUnitFlag $\equiv$ true; return mmCfg;   
}   
constexpr static MatmulConfig CUSTOM_CFG_MDL $=$ GetCustomMDLCFG(); 

步骤2 基于自定义的MatmulConfig模板参数，创建Matmul对象。 

```julia
using A_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, AType>;  
using B_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, BType>;  
using C_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, CType>;  
using BIAS_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, BiasType>;  
AscendC::Matmul<A_TYPE, B_TYPE, C_TYPE, BIAS_TYPE, CUSTOM_CFG_MDL > matmulObj; 
```

----结束 

# 验证优化方案性能收益

优化后的流水图如下，MMAD计算流水和FIXPIPE数据搬出流水之间实现了流水并 行。 

![](images/a7fc0e3560d0daf78563d73ac9ae1bbdc00730184d62e34a463cc6c4a75aa9b2.jpg)


优化后的Profiling数据如下，从C列的aic_time数据可以看出，多个核中最大算子 执行耗时为34.66us，较优化前的37.39us有约7.3%的性能提升。 

![](images/f84b3a520ba32003622b9ba85e9efabaddc87b59c0d1ed3e6963454a5b5af41b.jpg)


# 总结

在算子的MMAD计算流水和FIXPIPE数据搬出流水串行且未被其他流水掩盖（比如 MTE2 Bound）时，考虑使能UnitFlag功能，实现MMAD计算流水和FIXPIPE数据搬出 流水的流水并行，提升算子性能。 

# 3.10.4.6 Matmul 高阶 API 使能 Tiling 全量常量化

# 案例介绍

本案例呈现了在使用Matmul高阶API进行矩阵乘法计算时，使能Matmul Tiling全量常 量化对算子性能的提升效果。Matmul API在初始化和迭代过程中有大量Scalar计算， Matmul初始化时的Scalar计算影响指令头开销，Matmul迭代间的Scalar计算可能阻塞 MTE2流水。在调用Matmul API实现矩阵乘法时，使用MatmulApiStaticTiling参数替 代TCubeTiling变量参数，将Scalar计算提前到编译期进行，以减少运行时的Scalar计 算开销，实现算子性能的提升。 

Matmul Tiling常量化的适用场景： 

Matmul初始化时的Scalar计算较多，影响指令头开销。 

Matmul迭代之间的Scalar计算较多，阻塞MTE2流水。 

Matmul Tiling常量化需要在编译期确定部分Tiling参数，根据确定参数的不同， 分为全量常量化和部分常量化两种场景，使用Matmul Tiling常量化需要满足两种 场景中任一场景的条件： 

全量常量化：能够确定常量singleCore Shape（singleCoreM/singleCoreN/ singleCoreK）和常量base Shape（basicM/basicN/basicK，也称baseM/ baseN/baseK）。 

部分常量化：能够确定常量base Shape（basicM/basicN/basicK，也称 baseM/baseN/baseK）。 

其中，全量常量化场景比部分常量化场景可以减少更多的Scalar计算开销。 

本案例的算子规格如下： 


表 3-37 算子规格


<table><tr><td>输入</td><td>Shape</td><td>Data type</td><td>Format</td></tr><tr><td>a</td><td>128, 64</td><td>float16</td><td>ND</td></tr><tr><td>b</td><td>64, 30720</td><td>float16</td><td>ND</td></tr></table>

当前案例使用的AI处理器共24个核，每个核中包含1个AIC核和2个AIV核。 

Tiling参数如下： 

原始shape：M=128, N=30720, K=64。 

单核shape：按24个AIC核进行切分，singleCoreM=128，singleCoreN=1280， singleCoreK=64。 

对于B矩阵，沿着N轴进行切分，切分成24份的singleCoreN，单核上处理K * singleCoreN大小的数据。对于A矩阵，M轴不进行切分即singleCoreM=M，单核 上处理singleCoreM * K大小的数据。总共24个核参与计算。 

基本块shape：baseM=128，baseN=256，baseK=64。 

L1相关Tiling参数：stepM=1，stepN=1，stepKa=4，stepKb=4，depthA1=8， depthB1=8。 

# 获取性能数据

使用msProf工具获取算子仿真流水图和上板Profiling数据。相较于基础场景，Tiling常 量化在编译期期间将部分或全部Tiling参数由变量转化为常数值，在算子执行时直接使 用常量化的Tiling参数，可以减少Scalar性能开销，所以重点分析Scalar流水。 

# 分析主要瓶颈点

优化前的流水图如下，默认不使能Tiling常量化，Tiling参数需要从Host侧拷贝到 Kernel侧，导致Matmul初始化时的Scalar计算较多，第一个MTE2指令开始于 3.536us左右，MTE2前的指令头开销在算子整个流水中占比较大，因此需要优化 Scalar计算。 

![](images/09d776e400309d530d860b5fbc9211adcde8e34451af9f8e75baa27aa93b2d8a.jpg)


优化前的Profiling数据如下，从C列的aic_time数据来看，多个核中最大算子执行 耗时为10.62us，从G列的aic_scalar_time数据来看，Scalar平均耗时6.32us。 

![](images/3b995c3c4caa42004ca95a0beb3d538a2688dd530b99f2356a2e9d2db40d6a81.jpg)


# 设计优化方案

如下图所示，默认不使能Tiling常量化功能时，开发者在host侧创建Tiling对象，通过 调用API自动获取Tiling参数。然后将Tiling参数从Host侧传递到Kernel侧，在Kernel侧 初始化操作时传入。在算子执行时，使用Tiling变量参数完成矩阵乘操作。 


图 3-174 默认不使能 Tiling 常量化的 Matmul 计算流程示意图


![](images/e99c8c05767b98a442194b2e0938c76c1894bc2d69393c262b23a14988cafe36.jpg)


如下图所示，使能Tiling常量化功能时，开发者只需要在Kernel侧创建Matmul对象 时，调用GetMatmulApiTiling接口在编译期获取常量化Tiling信息，即可完成Tiling常 量化。在算子执行时，使用常量化的Tiling参数完成矩阵乘操作，减少Scalar计算开 销。 


图 3-175 使能 Tiling 常量化的 Matmul 计算流程示意图


![](images/140ef5016b78d35a24707484d16f392fe89b04492a39318b6a5983d89d410ee7.jpg)


Matmul API使能Tiling全量常量化的完整样例请参考Matmul Tiling常量化的算子样 例。使能Tiling全量常量化功能的步骤如下： 

步骤1 调用获取MatmulConfig模板的接口GetMMConfig时，使用常数值设置 MatmulShapeParams，得到带有常量化参数的自定义MatmulConfig模板 CUSTOM_CFG。 

```cpp
constexpr int32_t MAX_M = 10000; // custom matmul kernel support max value of M Dim shape  
constexpr int32_t MAX_N = 10000; // custom matmul kernel support max value of N Dim shape  
constexpr int32_t MAX_K = 10000; // custom matmul kernel support max value of K Dim shape  
constexpr int32_t BASE_M = 128; // BASE_M * BASE_K * sizeof(typeA) <=L0A size  
constexpr int32_t BASE_N = 256; // BASE_N * BASE_K * sizeof(typeB) <=L0B size  
constexpr int32_t BASE_K = 64; // BASE_M * BASE_N * sizeof(typeC) <=L0C size  
constexpr MatmulShapeParams shapeParams = { MAX_M, MAX_N, MAX_K, BASE_M, BASE_N, BASE_K };  
constexpr MatmulConfig CUSTOM_CFG =  
GetMMConfig<MatmulConfigMode::CONFIG_MDL>(shapeParams); 
```

步骤2 创建Matmul对象。首先调用GetMatmulApiTiling接口，将Tiling信息常量化，得到常 量化模板参数CONSTANT_CFG，包括常量化的Matmul Tiling信息和MatmulConfig模 板。创建Matmul对象时，使用常量化模板参数CONSTANT_CFG。 

```julia
using A_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, aType>;  
using B_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, bType>;  
using C_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, cType>;  
using BIAS_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, biasType>;  
constexpr static auto CONSTANT_CFG = AscendC::GetMatmulApiTiling<A_TYPE, B_TYPE, C_TYPE, BIAS_TYPE>(CUSTOM_CFG);  
AscendC::Matmul<A_TYPE, B_TYPE, C_TYPE, BIAS_TYPE, CONSTANT_CFG> matmulObj; 
```

步骤3 初始化操作。全量常量化时，可以在REGIST_MATMUL_OBJ接口的入参传递Tiling参数 的位置，使用空指针替代。部分常量化时，在Kernel侧使用REGIST_MATMUL_OBJ接 口初始化Matmul对象时，仍需要使用Tiling。 

```txt
// 全量常量化场景，初始化操作示例  
REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), matmulObj, (TCubeTiling*)nullptr);  
// 部分常量化场景，初始化操作示例  
REGIST_MATMUL_OBJ(&pipe, GetSysWorkSpacePtr(), matmulObj, &tiling); 
```

----结束 

# 验证优化方案性能收益

优化后的流水图如下，通过使能Tiling全量常量化，无需将Tiling参数从Host侧拷 贝到Kernel侧，在编译期完成Tiling常量化，减少了Matmul初始化时的Scalar计 算。从0us起到第一个MTE2指令发起，这之间的时间为Matmul初始化时间， Matmul初始化时间从优化前的3.536us减少到2.185us，性能有所提升。 

![](images/ba3d5e7d3c0e8a5af803d22c862a4ca719b07f6d85c487a1af187b10bfb8b3ab.jpg)


优化后的Profiling数据如下，从C列的aic_time数据来看，多个核中最大算子执行 耗时为7.87us，相较于优化前的10.62us提升了25.9%。从G列的aic_scalar_time 数据来看，Scalar平均耗时3.38us，相较于优化前的6.32us提升了46.5%。 

![](images/cd4d30e23e239d2c3b209fe6d4c7b4f8b79f67d7582ec96bb556b3f42760afe1.jpg)


# 总结

算子在调用Matmul API完成矩阵乘计算时，若Matmul初始化时的Scalar计算较多，影 响了指令头开销，或Matmul迭代间的Scalar计算较多，阻塞了MTE2流水。在这两类 场景下，满足上文提及的Tiling常量化使能条件（全量常量化或部分常量化），可以考 虑使能Tiling常量化，减少Scalar计算开销，提升算子性能。 

# 3.10.4.7 Matmul 高阶 API 使能 L2 Cache 切分

# 案例介绍

本案例呈现了在Matmul计算过程中，输入和输出的数据总量超过L2 Cache大小时，通 过L2 Cache数据切分对算子性能的提升效果。使能L2 Cache切分的完整样例请参考L2 Cache切分的算子样例。 

本案例使用的AI处理器的L2 Cache大小为192MB，L2 Cache纯读带宽约为GM的3到4 倍，两者之间存在较大差距。在搬入或搬出相同数据量的情况下，访问L2 Cache内的 数据比访问GM更快。若数据无法命中L2 Cache，即需要访问的数据不在L2 Cache 内，导致需要访问GM进行读写，带宽利用效率较低，最终算子搬入或搬出数据成为算 子整个运行过程的性能瓶颈。 

使能L2 Cache切分的适用场景 

输入和输出的数据量超过L2 Cache的大小。 

本案例的算子规格如下： 


表3-38 算子规格


<table><tr><td>输入</td><td>Shape</td><td>Data type</td><td>Format</td></tr><tr><td>a</td><td>30720, 1024</td><td>float16</td><td>ND</td></tr><tr><td>b</td><td>4096, 1024</td><td>float16</td><td>ND</td></tr></table>

# 获取性能数据

使用msProf工具获取算子仿真流水图和上板Profiling数据。因为L2 Cache切分功能主 要利用带宽更大的L2 Cache，减少MTE2数据搬运开销，所以重点分析MTE2的流水。 

# 分析主要瓶颈点

当前案例基于Tiling全量常量化进一步优化，Tiling全量常量化请参考3.10.4.6 Matmul高阶API使能Tiling全量常量化案例。优化前的Profiling数据如下，C列的 aic_time是867us，K列的aic_mte2_time是861.9us，MTE2占比为99%，MTE2数据搬 运是当前算子性能的瓶颈。 

<table><tr><td></td><td>A</td><td>B</td><td>C</td><td>D</td><td>E</td><td>F</td><td>G</td><td>H</td><td>I</td><td>J</td><td>K</td><td>L</td><td>M</td><td>N</td><td>O</td><td>P</td></tr><tr><td>1</td><td>block_id</td><td>sub_block</td><td>aic_time(US)</td><td>aic_total</td><td>aic Cube_tai</td><td>aic Cube_tai</td><td>aic scalar_tai</td><td>aic scalar_tai</td><td>aic_mte1</td><td>aic_mte1</td><td>aic_mte2</td><td>aic_mte2</td><td>aic_mte3</td><td>aic_mte3</td><td>aic fixpipe</td><td>aic fixpipe</td></tr><tr><td>2</td><td>0</td><td>cube_0</td><td>867.0195</td><td>1560635</td><td>743.8261</td><td>0.857912</td><td>275.6295</td><td>0.317905</td><td>553.735</td><td>0.638665</td><td>861.9689</td><td>0.994175</td><td>0.001111</td><td>0.000001</td><td>134.3511</td><td>0.154957</td></tr><tr><td>3</td><td>1</td><td>cube_0</td><td>866.4894</td><td>1559681</td><td>744.5584</td><td>0.859281</td><td>276.6311</td><td>0.319255</td><td>555.375</td><td>0.640948</td><td>859.5522</td><td>0.991994</td><td>0.001111</td><td>0.000001</td><td>134.8006</td><td>0.155571</td></tr><tr><td>4</td><td>2</td><td>cube_0</td><td>866.7955</td><td>1560232</td><td>743.9828</td><td>0.858314</td><td>276.9461</td><td>0.319506</td><td>553.6789</td><td>0.638765</td><td>861.8239</td><td>0.994264</td><td>0.001111</td><td>0.000001</td><td>134.7617</td><td>0.155471</td></tr><tr><td>5</td><td>3</td><td>cube_0</td><td>869.3867</td><td>1564896</td><td>743.9955</td><td>0.857571</td><td>276.0161</td><td>0.317484</td><td>557.9583</td><td>0.641784</td><td>861.2433</td><td>0.990633</td><td>0.001111</td><td>0.000001</td><td>136.5989</td><td>0.157121</td></tr><tr><td>6</td><td>4</td><td>cube_0</td><td>866.4155</td><td>1559548</td><td>742.9822</td><td>0.857536</td><td>276.0467</td><td>0.318608</td><td>558.6055</td><td>0.644732</td><td>857.1456</td><td>0.989301</td><td>0.001111</td><td>0.000001</td><td>133.7272</td><td>0.154345</td></tr><tr><td>7</td><td>5</td><td>cube_0</td><td>867.6189</td><td>1561714</td><td>744.0605</td><td>0.857589</td><td>276.8322</td><td>0.319071</td><td>557.2839</td><td>0.642314</td><td>858.1094</td><td>0.98904</td><td>0.001111</td><td>0.000001</td><td>135.7422</td><td>0.156454</td></tr><tr><td>8</td><td>6</td><td>cube_0</td><td>867.2844</td><td>1561112</td><td>742.9639</td><td>0.856655</td><td>276.4828</td><td>0.317638</td><td>560.2095</td><td>0.645935</td><td>856.4794</td><td>0.987542</td><td>0.001111</td><td>0.000001</td><td>133.0506</td><td>0.153411</td></tr><tr><td>9</td><td>7</td><td>cube_0</td><td>866.1272</td><td>1559029</td><td>743.3489</td><td>0.858244</td><td>275.8489</td><td>0.318485</td><td>557.39</td><td>0.643543</td><td>853.5717</td><td>0.985504</td><td>0.001111</td><td>0.000001</td><td>133.0356</td><td>0.153598</td></tr><tr><td>10</td><td>8</td><td>cube_0</td><td>867.3917</td><td>1561305</td><td>742.9006</td><td>0.856476</td><td>275.4478</td><td>0.317559</td><td>558.1</td><td>0.643423</td><td>856.1794</td><td>0.987074</td><td>0.001111</td><td>0.000001</td><td>135.6339</td><td>0.15637</td></tr><tr><td>11</td><td>9</td><td>cube_0</td><td>868.9461</td><td>1564103</td><td>744.1939</td><td>0.856433</td><td>278.135</td><td>0.320083</td><td>551.4667</td><td>0.634638</td><td>864.5028</td><td>0.994887</td><td>0.001111</td><td>0.000001</td><td>134.5694</td><td>0.154865</td></tr><tr><td>12</td><td>10</td><td>cube_0</td><td>866.6683</td><td>1560003</td><td>743.4911</td><td>0.857873</td><td>276.8239</td><td>0.319412</td><td>553.7267</td><td>0.638914</td><td>861.4861</td><td>0.994021</td><td>0.001111</td><td>0.000001</td><td>134.4906</td><td>0.155181</td></tr><tr><td>13</td><td>11</td><td>cube_0</td><td>867.2733</td><td>1561092</td><td>743.6395</td><td>0.857445</td><td>277.1039</td><td>0.319512</td><td>553.0695</td><td>0.637711</td><td>862.9461</td><td>0.995011</td><td>0.001111</td><td>0.000001</td><td>135.2517</td><td>0.15595</td></tr><tr><td>14</td><td>12</td><td>cube_0</td><td>867.4889</td><td>1561480</td><td>743.6367</td><td>0.857229</td><td>276.1606</td><td>0.318345</td><td>554.3283</td><td>0.639003</td><td>861.1934</td><td>0.992743</td><td>0.001111</td><td>0.000001</td><td>135.9372</td><td>0.156702</td></tr><tr><td>15</td><td>13</td><td>cube_0</td><td>866.1033</td><td>1558986</td><td>743.5217</td><td>0.858468</td><td>276.5183</td><td>0.319267</td><td>553.9489</td><td>0.639588</td><td>861.5122</td><td>0.994699</td><td>0.001111</td><td>0.000001</td><td>135.82</td><td>0.156817</td></tr><tr><td>16</td><td>14</td><td>cube_0</td><td>866.7022</td><td>1560064</td><td>744.0677</td><td>0.858505</td><td>276.3206</td><td>0.318818</td><td>555.5745</td><td>0.641021</td><td>859.2367</td><td>0.991386</td><td>0.001111</td><td>0.000001</td><td>133.2717</td><td>0.153769</td></tr><tr><td>17</td><td>15</td><td>cube_0</td><td>869.4316</td><td>1564977</td><td>742.7806</td><td>0.854329</td><td>275.4756</td><td>0.316846</td><td>557.4161</td><td>0.641127</td><td>860.0016</td><td>0.989154</td><td>0.001111</td><td>0.000001</td><td>134.0194</td><td>0.154146</td></tr><tr><td>18</td><td>16</td><td>cube_0</td><td>865.9283</td><td>1558671</td><td>743.1533</td><td>0.858216</td><td>274.7839</td><td>0.317329</td><td>557.99</td><td>0.644384</td><td>854.0439</td><td>0.986275</td><td>0.001111</td><td>0.000001</td><td>134.7578</td><td>0.155622</td></tr><tr><td>19</td><td>17</td><td>cube_0</td><td>867.5294</td><td>1561553</td><td>743.7022</td><td>0.857265</td><td>276.2833</td><td>0.318471</td><td>555.9783</td><td>0.640875</td><td>858.4106</td><td>0.989489</td><td>0.001111</td><td>0.000001</td><td>135.6844</td><td>0.156403</td></tr><tr><td>20</td><td>18</td><td>cube_0</td><td>867.3689</td><td>1561264</td><td>743.2472</td><td>0.856899</td><td>276.0567</td><td>0.318269</td><td>555.0605</td><td>0.639936</td><td>861.1278</td><td>0.992805</td><td>0.001111</td><td>0.000001</td><td>135.155</td><td>0.155822</td></tr><tr><td>21</td><td>19</td><td>cube_0</td><td>866.1895</td><td>1559141</td><td>744.1061</td><td>0.859057</td><td>277.1489</td><td>0.319963</td><td>553.74</td><td>0.639283</td><td>861.4194</td><td>0.994493</td><td>0.001111</td><td>0.000001</td><td>135.1089</td><td>0.155981</td></tr><tr><td>22</td><td>20</td><td>cube_0</td><td>867.2083</td><td>1560975</td><td>743.8272</td><td>0.857726</td><td>276.3544</td><td>0.318671</td><td>553.2839</td><td>0.638006</td><td>861.2522</td><td>0.993132</td><td>0.001111</td><td>0.000001</td><td>134.2833</td><td>0.154846</td></tr><tr><td>23</td><td>21</td><td>cube_0</td><td>868.8367</td><td>1563906</td><td>744.0677</td><td>0.856395</td><td>276.9517</td><td>0.318761</td><td>554.5561</td><td>0.638274</td><td>862.7622</td><td>0.993009</td><td>0.001111</td><td>0.000001</td><td>134.3883</td><td>0.154676</td></tr><tr><td>24</td><td>22</td><td>cube_0</td><td>866.3228</td><td>1559381</td><td>743.9667</td><td>0.858764</td><td>277.1939</td><td>0.319966</td><td>552.5367</td><td>0.637795</td><td>861.8406</td><td>0.994826</td><td>0.001111</td><td>0.000001</td><td>134.2789</td><td>0.154999</td></tr><tr><td>25</td><td>23</td><td>cube_0</td><td>867.2939</td><td>1561129</td><td>744.1261</td><td>0.857986</td><td>276.6233</td><td>0.31895</td><td>554.9172</td><td>0.639826</td><td>861.7117</td><td>0.993564</td><td>0.001111</td><td>0.000001</td><td>134.7367</td><td>0.155353</td></tr></table>

# 设计优化方案

# 优化点一：调整切块大小和计算次数

优化前，输入数据不进行切分，所有核一次计算全部数据。如下图所示，图 中数字表示核id，24个核一次计算A和B矩阵的所有数据。 

优化后，输入数据被切分多次，所有核分多次计算，每个核单次计算只依赖 切分后的数据量。L2 Cache切分方案确保单次计算的数据都在L2 Cache缓存 中，搬运输入数据的效率更高。 


图 3-176 优化点一示意图


![](images/f0d16bc112b75ebfc7b8ad4ed472aece23f6bf69962f2183feaf5c1c20070fba.jpg)



优化点二：选择拖尾较小的L2 Cache切分方案 结合3.8.2.1 核间负载均衡的原理，AI处理器的物理核数固定，当数据进行L2 Cache切分之后，可能出现部分核有计算拖尾的情况，即每次所有核总计算量除以


每个核单次处理的数据量不能被核数整除，导致每次计算的最后需要部分尾核计 算剩余数据。而在尾核计算时，部分核始终处于空闲状态，导致算子的整体性能 变差。下图中标黄的数据块就是尾块数据，左边方案由于拖尾，每次计算中0、 1、2、3核多执行一次处理剩余数据。为达到全局负载最优，调整拖尾核的位置， 如右边方案所示，完成所有计算时，0到7核均多一次数据块的计算。 

在实际场景中，满足切分后的数据量小于L2 Cache大小的前提下，拖尾越小越 好。基于这个原则可以确定L2 Cache切分块数。 


图 3-177 优化点二示意图


![](images/38d0595f82555cdefc8e789991d35969cd78c335dbc3cf88c53d8a0289c0e04f.jpg)


优化点三：错位分核，减少左右矩阵同地址冲突问题 

同地址冲突：多核并发执行Matmul计算时，如果多核同时访问输入矩阵的相同地 址，会导致地址冲突，影响性能。 

在M和N方向，将矩阵数据L2 Cache切分为大数据块， 然后在数据块间错位分 核，即将每个数据块依次沿对角线分配给不同的核处理，从而有效减少同地址冲 突的问题。比如，在处理同一行的尾块数据0，1，2，3时，如果顺序分配执行的 核，多核会同时读同一行左矩阵数据，导致读读冲突。若按照对角线方式分配执 行的核，在对角线上的尾块数据被分配给核0，1，2，3计算，多核访问不同行的 左矩阵数据，将减少同地址冲突的次数。 


图 3-178 优化点三示意图


![](images/f5ee621447e9e44c15f6f8de348b8d80c72b3f152793d8f96bb3cd8953bae1b0.jpg)


Matmul API使能L2 Cache切分的完整样例请参考L2 Cache切分的算子样例。实现L2 Cache切分的关键步骤如下： 

步骤1 判断是否需要进行L2 Cache切分。如果数据总量超过设定的L2 Cache大小，则计算L2 Cache切分数目。 

```txt
bool smallDim = mTileNum_< L1_MIN_UT_ST_DIM && nTileNum_< L1_MIN_UT_ST_DIM;  
if (smallDim || (!EnableL2Tile())) { // 判断计算数据总量是否小于L2Cache阈值  
    mL2TileNum_ = mTileNum_;  
    nL2TileNum_ = nTileNum_;  
    mL2BlockNum_ = 1;  
    nL2BlockNum_ = 1;  
    return; // 不需要切分，提前返回 
```

```javascript
} InitL2TileTail(); //计算L2切分 
```

步骤2 基于负载均衡原则，计算L2 Cache切分的份数，m方向L2 Cache切分数： mL2TileNum_，n方向L2 Cache切分数：nL2TileNum_。 

```c
int64_t mConflict = INT64_MAX;  
int64_t nConflict = INT64_MAX;  
constexpr bool isNMajor = l1N > l1M; // 根据shape大小，判断主维度  
for (int64_t i = maxMajor; i >= L1_MIN_UT_DIM; i--) {  
    for (int64_t j = maxMinor; j >= minMinor; j--) {  
        if (GetTotalSize(j * l1M, i * l1N, k_) <= L2_TILE_THRESHOLD) { // 确保分块小于L2Cache阈值  
            uint64_t mConflictTmp = AscendC::Ceil(blockNum_, mL2TileNumTailTmp); // 计算负载冲突值  
            uint64_t nConflictTmp = AscendC::Ceil(blockNum_, nL2TileNumTailTmp);  
        }  
    if (mConflict >= mConflictTmp && nConflict >= nConflictTmp) { // 若冲突值更小，更新分块数量  
            mConflict = mConflictTmp;  
            nConflict = nConflictTmp;  
            mL2TileNum_ = curMajorDim;  
            mL2TileNum_ = curMinorDim;  
        }  
    } 
```

步骤3 错位分核。输入当前数据块的下标，获取按对角线分配的核的下标。 

```lisp
__aicore__inline BlockCoord GetBlockCoord(int64_t tileIdx) {GetCommonTileIndex(tileIdx);int64_t mTileIdx = newBlockIdx_% mL2TileNumTmp_;mTileIdx = mTileIdx + mL2Idx_* mL2TileNum_;int64_t nTileIdx = 0;if (mL2TileNumTmp_ != 0 && nL2TileNumTmp_ != 0) {int64_t tmp = newBlockIdx_/CalcLcm(mL2TileNumTmp_, mL2TileNumTmp_);nTileIdx = (newBlockIdx_ + tmp) % mL2TileNumTmp_;}nTileIdx = nTileIdx + mL2Idx_* mL2TileNum_;return{mTileIdx * l1M, nTileIdx * l1N, 0};} 
```

步骤4 设置左右矩阵，根据前序步骤计算的L2 Cache切分数和执行核的下标，循环多次计算 Matmul。 

```txt
L2CacheOpt l2Opt(shape, blockNum);  
matmulObj.SetOrgShape(shape.m, shapes.n, shapes.k);  
for (int64_t tileIdx = curBlockIdx; tileIdx < l2Opt.GetTileNum(); tileIdx += blockNum) {  
    auto blockShape = l2Opt.GetBlockShape(tileIdx); // 获取单次计算L2切分块大小  
    if (Get<0>(blockShape) <= 0 || Get<1>(blockShape) <= 0) {  
        return;  
    }  
    auto blockCoord = l2Opt.GetBlockCoord(tileIdx);  
    // 获取当前执行计算的核的下标blockCoord  
    matmulObj.setTail(Get<0>(blockShape), Get<1>(blockShape), Get<2>(blockShape));  
    const auto& offsetCoord = CalcOffset(shape, blockCoord); // 基于下标计算矩阵偏移  
    int64_t offsetA = Get<0>(offsetCoord);  
    int64_t offsetB = Get<1>(offsetCoord);  
    int64_t offsetC = Get<2>(offsetCoord);  
    matmulObj.setTensorA(aGlobal[offsetA], false);  
    matmulObj.setTensorB(bGlobal[offsetB], false);  
    if (shapes.isBias) {  
        matmulObj.setBias(biasGlobal);  
    }  
    matmulObj.IterateAll(cGlobal[offsetC]); // 计算L2切分块  
}  
matmulObj.End(); 
```

----结束 

# 验证优化方案性能收益

优化后的Profiling数据如下，C列的aic_time为805.6us，相比于优化前，总执行时间降 低了约7.1%，MTE2搬运时间降低了约10.7%。 

<table><tr><td></td><td>A</td><td>B</td><td>C</td><td>D</td><td>E</td><td>F</td><td>G</td><td>H</td><td>I</td><td>J</td><td>K</td><td>L</td><td>M</td><td>N</td><td>O</td><td>P</td><td></td></tr><tr><td>1</td><td>block_id</td><td>sub_block</td><td>aic_time(ω)</td><td>aic_total</td><td>aic Cube_tie</td><td>aic Cube_tie</td><td>aic Cube_tie</td><td>aic scalar</td><td>aic scalar</td><td>aic_mte1</td><td>aic_mte1</td><td>aic_mte2</td><td>aic_mte2</td><td>aic_mte3</td><td>aic_mte3</td><td>aic_fixpe</td><td>aic_fixpe</td></tr><tr><td>2</td><td>0</td><td>cube0</td><td>805.7633</td><td>1450374</td><td>739.6234</td><td>0.917916</td><td>284.7161</td><td>0.35335</td><td>571.9861</td><td>0.709869</td><td>760.5233</td><td>0.943855</td><td>0.001111</td><td>0.000001</td><td>126.0561</td><td>0.156443</td><td></td></tr><tr><td>3</td><td>1</td><td>cube0</td><td>802.1606</td><td>1443889</td><td>739.5</td><td>0.921885</td><td>284.6589</td><td>0.354865</td><td>572.6211</td><td>0.713849</td><td>757.5767</td><td>0.94442</td><td>0.001111</td><td>0.000001</td><td>125.6339</td><td>0.156619</td><td></td></tr><tr><td>4</td><td>2</td><td>cube0</td><td>799.1456</td><td>1438462</td><td>739.3761</td><td>0.925208</td><td>284.6972</td><td>0.356252</td><td>571.7355</td><td>0.715434</td><td>754.8494</td><td>0.944571</td><td>0.001111</td><td>0.000001</td><td>127.3744</td><td>0.159388</td><td></td></tr><tr><td>5</td><td>3</td><td>cube0</td><td>816.015</td><td>1468827</td><td>740.37</td><td>0.9073</td><td>284.8033</td><td>0.349017</td><td>567.6578</td><td>0.695646</td><td>795.1061</td><td>0.974377</td><td>0.001111</td><td>0.000001</td><td>125.8111</td><td>0.154177</td><td></td></tr><tr><td>6</td><td>4</td><td>cube0</td><td>807.84</td><td>1454112</td><td>740.4239</td><td>0.916548</td><td>284.7967</td><td>0.352541</td><td>568.8739</td><td>0.704191</td><td>783.5178</td><td>0.969892</td><td>0.001111</td><td>0.000001</td><td>126.3439</td><td>0.156397</td><td></td></tr><tr><td>7</td><td>5</td><td>cube0</td><td>804.7416</td><td>1448535</td><td>739.8639</td><td>0.919381</td><td>284.8022</td><td>0.353905</td><td>569.0039</td><td>0.707064</td><td>777.0356</td><td>0.965571</td><td>0.001111</td><td>0.000001</td><td>126.69</td><td>0.157429</td><td></td></tr><tr><td>8</td><td>6</td><td>cube0</td><td>818.2178</td><td>1472792</td><td>741.01</td><td>0.905639</td><td>285.4111</td><td>0.34882</td><td>568.1128</td><td>0.69433</td><td>796.1216</td><td>0.972995</td><td>0.001111</td><td>0.000001</td><td>126.7339</td><td>0.15489</td><td></td></tr><tr><td>9</td><td>7</td><td>cube0</td><td>814.1428</td><td>1465457</td><td>740.8483</td><td>0.909974</td><td>285.1306</td><td>0.350222</td><td>569.9772</td><td>0.700095</td><td>790.7106</td><td>0.971219</td><td>0.001111</td><td>0.000001</td><td>125.4344</td><td>0.154069</td><td></td></tr><tr><td>10</td><td>8</td><td>cube0</td><td>807.8306</td><td>1454095</td><td>740.3572</td><td>0.916476</td><td>285.1772</td><td>0.353016</td><td>568.4178</td><td>0.703635</td><td>782.9439</td><td>0.969193</td><td>0.001111</td><td>0.000001</td><td>126.5244</td><td>0.156622</td><td></td></tr><tr><td>11</td><td>9</td><td>cube0</td><td>803.1967</td><td>1445754</td><td>739.1906</td><td>0.920311</td><td>285.0422</td><td>0.354885</td><td>571.3561</td><td>0.711353</td><td>769.2961</td><td>0.957793</td><td>0.001111</td><td>0.000001</td><td>126.6961</td><td>0.15774</td><td></td></tr><tr><td>12</td><td>10</td><td>cube0</td><td>803.5383</td><td>1446369</td><td>738.8417</td><td>0.919485</td><td>284.7495</td><td>0.354369</td><td>571.6644</td><td>0.711434</td><td>760.8555</td><td>0.946881</td><td>0.001111</td><td>0.000001</td><td>126.62</td><td>0.157578</td><td></td></tr><tr><td>13</td><td>11</td><td>cube0</td><td>808.0139</td><td>1454425</td><td>739.0767</td><td>0.914683</td><td>285.2744</td><td>0.353056</td><td>571.0839</td><td>0.706775</td><td>766.0711</td><td>0.948092</td><td>0.001111</td><td>0.000001</td><td>124.3628</td><td>0.153912</td><td></td></tr><tr><td>14</td><td>12</td><td>cube0</td><td>805.0511</td><td>1449092</td><td>739.3517</td><td>0.918391</td><td>284.6683</td><td>0.353603</td><td>571.41</td><td>0.709781</td><td>764.96</td><td>0.950201</td><td>0.001111</td><td>0.000001</td><td>126.4333</td><td>0.15705</td><td></td></tr><tr><td>15</td><td>13</td><td>cube0</td><td>803.7078</td><td>1446674</td><td>739.2683</td><td>0.919822</td><td>284.4889</td><td>0.353971</td><td>570.6089</td><td>0.709971</td><td>767.9094</td><td>0.955459</td><td>0.001111</td><td>0.000001</td><td>126.0356</td><td>0.156818</td><td></td></tr><tr><td>16</td><td>14</td><td>cube0</td><td>803.0511</td><td>1445492</td><td>739.6194</td><td>0.921012</td><td>284.5255</td><td>0.354305</td><td>571.5584</td><td>0.711733</td><td>774.99</td><td>0.965057</td><td>0.001111</td><td>0.000001</td><td>125.2233</td><td>0.155934</td><td></td></tr><tr><td>17</td><td>15</td><td>cube0</td><td>817.5378</td><td>1471568</td><td>741.0917</td><td>0.906492</td><td>285.6128</td><td>0.349357</td><td>566.67</td><td>0.693142</td><td>797.8073</td><td>0.975866</td><td>0.001111</td><td>0.000001</td><td>127.4817</td><td>0.155934</td><td></td></tr><tr><td>18</td><td>16</td><td>cube0</td><td>806.5061</td><td>1451711</td><td>739.1672</td><td>0.916505</td><td>285.1239</td><td>0.35353</td><td>571.2061</td><td>0.708248</td><td>769.6733</td><td>0.95433</td><td>0.001111</td><td>0.000001</td><td>126.5522</td><td>0.156914</td><td></td></tr><tr><td>19</td><td>17</td><td>cube0</td><td>800.7289</td><td>1441312</td><td>738.7955</td><td>0.922654</td><td>284.2606</td><td>0.355002</td><td>572.0061</td><td>0.714357</td><td>756.9067</td><td>0.945272</td><td>0.001111</td><td>0.000001</td><td>123.9328</td><td>0.154775</td><td></td></tr><tr><td>20</td><td>18</td><td>cube0</td><td>788.9984</td><td>1420197</td><td>738.9898</td><td>0.936629</td><td>284.01</td><td>0.359963</td><td>573.4628</td><td>0.726824</td><td>737.2867</td><td>0.934459</td><td>0.001111</td><td>0.000001</td><td>123.3733</td><td>0.156367</td><td></td></tr><tr><td>21</td><td>19</td><td>cube0</td><td>806.2889</td><td>1451320</td><td>739.1967</td><td>0.916789</td><td>284.4944</td><td>0.352844</td><td>571.7455</td><td>0.709108</td><td>768.0311</td><td>0.952551</td><td>0.001111</td><td>0.000001</td><td>125.0094</td><td>0.155043</td><td></td></tr><tr><td>22</td><td>20</td><td>cube0</td><td>805.7067</td><td>1450272</td><td>738.7505</td><td>0.916898</td><td>284.7761</td><td>0.353449</td><td>572.4617</td><td>0.710509</td><td>768.0133</td><td>0.953217</td><td>0.001111</td><td>0.000001</td><td>125.3339</td><td>0.155558</td><td></td></tr><tr><td>23</td><td>21</td><td>cube0</td><td>804.2167</td><td>1447590</td><td>739.4839</td><td>0.919508</td><td>284.6667</td><td>0.353968</td><td>571.2539</td><td>0.710323</td><td>773.0367</td><td>0.961229</td><td>0.001111</td><td>0.000001</td><td>125.2983</td><td>0.155802</td><td></td></tr><tr><td>24</td><td>22</td><td>cube0</td><td>797.9305</td><td>1436275</td><td>739.5328</td><td>0.926813</td><td>284.2545</td><td>0.35624</td><td>572.7439</td><td>0.717787</td><td>745.6906</td><td>0.934531</td><td>0.001111</td><td>0.000001</td><td>125.525</td><td>0.157313</td><td></td></tr><tr><td>25</td><td>23</td><td>cube0</td><td>805.1544</td><td>1449278</td><td>739.39</td><td>0.918321</td><td>284.7444</td><td>0.353652</td><td>572.1</td><td>0.710547</td><td>764.0517</td><td>0.94895</td><td>0.001111</td><td>0.000001</td><td>125.0522</td><td>0.155315</td><td></td></tr></table>

# 总结

在Matmul计算数据量超过L2 Cache大小的场景下，可以考虑使能L2 Cache切分，提 高L2 Cache命中率，利用L2 Cache高带宽特性提升算子性能。 

# 3.10.4.8 Matmul 高阶 API 使能多核切 K

# 案例介绍

本案例呈现了在矩阵乘算子场景中，使用Matmul高阶API进行矩阵乘法计算，使能多 核切K功能对算子性能的提升效果。为了实现算子在多核上并行执行，提升计算效率， 需要将矩阵数据进行切分，切分后的数据块被分配到不同的核上处理。通常情况下， 切分矩阵数据时仅切分M、N轴，不切分K轴。若M和N较小，切分M和N轴较困难，此 时需要考虑K轴切分；使能多核切K功能后，该场景下可以对矩阵的K轴进行切分，从 而使算子在多核上并行执行。由于K轴较大，在该场景下不切分K轴通常会导致单核的 输入数据量过大，使能K轴切分后，切分策略能够更有效地平衡输出带宽和输入带宽。 

使能多核切K的适用场景 

矩阵的K轴较大，M轴和N轴相比K轴较小，可以在K轴进行切分，使算子并行 执行的核数更多。 

矩阵的M轴、N轴和K轴均较大时，可以在K轴进行切分，使切分策略更好地 平衡输入和输出带宽。 

使能多核切K的约束条件 

使能多核切K的场景，获取C矩阵结果时仅支持输出到Global Memory。 

使能多核切K的场景，需在Kernel侧代码中首次将C矩阵分片的结果写入 Global Memory之前，先对Global Memory进行清零，在获取C矩阵分片的 结果时，开启AtomicAdd累加。如果不预先清零Global Memory，可能会因 为累加Global Memory中的原始无效数据而产生精度问题。 

使能多核切K的场景，不支持Bias参与矩阵乘计算。 

本案例的算子规格如下： 


表 3-39 算子规格


<table><tr><td>输入</td><td>Shape</td><td>Data type</td><td>Format</td></tr><tr><td>a</td><td>16, 1024</td><td>float16</td><td>ND</td></tr><tr><td>b</td><td>1024, 16</td><td>float16</td><td>ND</td></tr></table>

当前案例使用的AI处理器共24个核，算子中使能高阶API Matmul的纯Cube模式。 Tiling参数如下： 

原始shape： $\mathsf { M } = \mathsf { 1 6 }$ , N= 16, K=1024。 

单核shape：未开启多核切K时，singleCoreM=16，singleCoreN $\mathtt { \Omega } = 1 6$ ， singleCoreK=1024；开启多核切K后，singleCoreM $= 1 6$ ，singleCoreN $\mathtt { 1 } = 1 6$ ， singleCoreK $\mathtt { \Omega } = 5 1 2$ 。 

# 获取性能数据

使用msProf工具获取算子仿真流水图和上板Profiling数据。 

# 分析主要瓶颈点

优化前的流水图如下，由于未使能多核切K，且M和N非常小，原始矩阵数据未进 行切分，所有数据在单核上进行计算。 

![](images/ed227f07d2cc1683c43a3e0cb38a381438fef560e982b1526da33ecaa282f003.jpg)


优化前的Profiling数据如下，可以看到算子只在单核上执行，aic_time耗时约 19.60us，其中aic_mte2_time的平均耗时约为13.72us，aic_mte2_ratio占比较 高。 

![](images/03bea13fbd2fd2d6a5051eebec50042f491accb81481ee359ab089c31af4abba.jpg)


# 设计优化方案

使能多核切K后，矩阵的K方向数据可以进行切分。如下图所示，C矩阵中的R矩阵块， 是通过A1*B1+A2*B2+A3*B3累加得到的，其中，A1*B1、A2*B2、A3*B3可在多个核上 并行计算。 


图 3-179 开启多核切 K


![](images/3487b0611731703449e2958e3ec1d2770a7b9be373b4e64480a2de54c83cc9b4.jpg)


使能多核切K功能的方式为：在GetTiling接口前调用EnableMultiCoreSplitK接口，使 能多核切K，并在Kernel实现中，对C矩阵的Global Memory地址清零后开启 AtomicAdd。使能多核切K的完整样例请参考多核切K场景的算子样例。具体步骤如 下： 

Tiling实现 

通过GetTiling接口获取TCubeTiling结构体前，调用EnableMultiCoreSplitK接口且 入参为true，使能多核切K。 

```cpp
cubeTiling.SetOrgShape(M, N, K);  
cubeTiling.SetShape(M, N, K);  
cubeTiling EnableBias(isBias);  
cubeTiling.setBufferSpace(-1, -1, -1); // tiling enable split K  
cubeTiling EnableMultiCoreSplitK(true);  
if (cubeTiling.GetTiling(tilingData) == -1) { std::cout << "gen tiling failed." << std::endl; return {}; } 
```

Kernel实现 

调用Fill接口，对C矩阵的Global Memory地址清零。 

cGlobal.SetGlobalBuffer(reinterpret_cast<__gm__ cType $\rightharpoondown$ (c), tiling.M \* tiling.N); // clear gm Fill(cGlobal, tiling.M \* tiling.N, (cType)0); 

调用IterateAll接口，开启AtomicAdd累加，完成矩阵乘操作。 

```c
// setAtomicAdd  
uint8_t enAtomic = 1;  
matmulObj.IterateAll(cGlobal, enAtomic); 
```

# 验证优化方案性能收益

优化后的流水图如下，开启多核切K后，切分原始矩阵的K方向，单核处理K方向 的数据量由原来的1024变为512，单核处理的数据量减半，MTE2流水变短。 

![](images/daa09036c22e1413fff0619c6f4338a434f6e21e9c81e896e2567eee44ebff98.jpg)


优化后的Profiling数据如下，可以看到算子在两个核上执行，aic_time平均耗时约 为13.70us，较优化前的19.60us有较大提升。 

<table><tr><td>1</td><td>A</td><td>B</td><td>C</td><td>D</td><td>E</td><td>F</td><td>G</td><td>H</td><td>I</td><td>J</td><td>K</td><td>L</td><td>M</td><td>N</td><td>O</td><td>P</td></tr><tr><td>1</td><td>block_id</td><td>sub_c0d</td><td>iccam_time(s)</td><td>ic_sub_total_cycles</td><td>ic_cub_time(s)</td><td>ic_cuallate_time(s)</td><td>ic_cscalar_time(s)</td><td>ic_cmtkt_time(s)</td><td>ic_mctkt_ratio</td><td>ic_mctktvalue(s)</td><td>ic_mctkt ratio</td><td>ic_mctktvalue(s)</td><td>ic_mctktvalue(s)</td><td>ic_mctktvalue(s)</td><td>ic_mctktvalue(s)</td><td>ic_mctktvalue(s)</td></tr><tr><td>2</td><td>0</td><td>c0b0cd</td><td>13 405487</td><td>24802</td><td>0.056576</td><td>0.041533</td><td>0.408469</td><td>0.309192</td><td>0.191351</td><td>0.009798</td><td>7.411495</td><td>0.55306</td><td>0.001031</td><td>0.000001</td><td>0.699459</td><td>0.520295</td></tr><tr><td>3</td><td>1</td><td>c0b0e</td><td>13 99081</td><td>25883</td><td>0.057297</td><td>0.004095</td><td>3.942703</td><td>0.281807</td><td>0.131351</td><td>0.009388</td><td>7.90973</td><td>0.565352</td><td>0.001081</td><td>0.000077</td><td>0.7394595</td><td>0.528532</td></tr><tr><td>4</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>5</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr></table>

# 总结

当算子使用Matmul API完成矩阵计算时，原始矩阵的M和N方向无法进行有效切分， 且结果输出到Global Memory时，可以考虑使能多核切K功能，实现多核并行，提升计 算效率。 

# 3.10.4.9 Matmul 高阶 API 使能多核 K 轴错峰访问内存

# 案例介绍

本案例呈现在矩阵乘算子场景中，使用Matmul高阶API进行矩阵乘法计算，使能多核K 轴错峰访问Device内存对算子性能的提升效果。在多核并行执行Matmul计算时，如果 输入矩阵A或B的内存位置位于GM，并且参与多核计算的矩阵相同，那么将出现多核 同时访问相同GM地址的情况，导致地址访问冲突，从而影响算子性能。若使能多核K 轴错峰访问Device内存，切分的矩阵K轴方向对应的不同核将尽量从不同的GM起始地 址开始访问和搬运数据，缓解地址访问冲突，提升算子性能。 


图 3-180 访问地址冲突示意图


![](images/a231b84019748a1111cf33e79be9a53263af4e83d2a5494a7d534ba9ba66eeb8.jpg)



图 3-181 缓解地址冲突示意图


![](images/3d1a533a61e01fdf2752ea2c33c49ef4c4579920d55b5e192197702aad20b59d.jpg)


使能多核K轴错峰访问内存的适用场景： 多核执行Matmul，且输入矩阵的K轴较大。 

. 使能多核K轴错峰访问内存的约束条件： 输入矩阵的K轴非全载，K轴非全载即矩阵的K方向数据不能同时搬入及保持 在L1 Buffer中。 仅支持MDL模板。 在多核上执行Matmul计算。 A矩阵或B矩阵的内存位置位于GM。 

本案例的算子规格如下： 


表 3-40 算子用例规格


<table><tr><td>输入</td><td>Shape</td><td>Data type</td><td>Format</td></tr><tr><td>a</td><td>768, 6144</td><td>float16</td><td>ND</td></tr><tr><td>b</td><td>6144, 2048</td><td>float16</td><td>ND</td></tr></table>

# 获取性能数据

使用msProf工具获取算子仿真流水图和上板Profiling数据，重点分析MTE2的流水。 

# 分析主要瓶颈点

优化前的Profiling数据（PipeUtilization.csv）如下所示，aic_mte2_ratio平均达到 0.93，MTE2在算子整体执行时长中占比较高，算子当前为MTE2 Bound。本案例中， 矩阵按M和N方向切分，单核shape[singleCoreM，singleCoreN，singleCoreK]为 [128, 512, 6144]，基本块shape[baseM，baseN，baseK]为[128, 256, 64]，每次加 载A矩阵的数据时，多核有概率同时访问同一GM地址，引发地址冲突，导致MTE2搬 运效率降低，MTE2执行耗时增加。 

<table><tr><td>block_id</td><td>sub_block_id</td><td>aic_time(us)</td><td>aic_total_cycle</td><td>aic Cube_time(us)</td><td>aic Cube_ratio</td><td>aic scalar_time(us)</td><td>aic scalar_ratio</td><td>aic mte1_time(us)</td><td>aic mte1_ratio</td><td>aic_mte2_time(us)</td><td>aic_mte2_ratio</td></tr><tr><td>0</td><td>cube0</td><td>97.181084</td><td>179785</td><td>55.972973</td><td>0.575966</td><td>55.87027</td><td>0.574909</td><td>40.527027</td><td>0.417026</td><td>91.097298</td><td>0.937397</td></tr><tr><td>1</td><td>cube0</td><td>97.074051</td><td>179587</td><td>56.074596</td><td>0.577648</td><td>56.449188</td><td>0.581506</td><td>40.240002</td><td>0.414529</td><td>90.012436</td><td>0.927255</td></tr><tr><td>2</td><td>cube0</td><td>97.836754</td><td>180998</td><td>56.035675</td><td>0.572747</td><td>57.169189</td><td>0.584332</td><td>40.281082</td><td>0.411717</td><td>90.380539</td><td>0.923789</td></tr><tr><td>3</td><td>cube0</td><td>97.211891</td><td>179842</td><td>55.773514</td><td>0.573731</td><td>58.014053</td><td>0.596779</td><td>40.107025</td><td>0.412573</td><td>90.107025</td><td>0.926914</td></tr><tr><td>4</td><td>cube0</td><td>97.215675</td><td>179849</td><td>55.769188</td><td>0.573665</td><td>58.704323</td><td>0.603857</td><td>40.13081</td><td>0.412802</td><td>91.602699</td><td>0.942263</td></tr><tr><td>5</td><td>cube0</td><td>97.799461</td><td>180929</td><td>55.758919</td><td>0.570135</td><td>57.950272</td><td>0.592542</td><td>40.439999</td><td>0.413499</td><td>90.181625</td><td>0.922108</td></tr><tr><td>6</td><td>cube0</td><td>96.235672</td><td>178036</td><td>55.756218</td><td>0.579372</td><td>57.925404</td><td>0.601912</td><td>40.931892</td><td>0.42533</td><td>87.956215</td><td>0.913967</td></tr><tr><td>7</td><td>cube0</td><td>95.905945</td><td>177426</td><td>56.257298</td><td>0.586588</td><td>57.697838</td><td>0.601609</td><td>40.234596</td><td>0.419521</td><td>89.915138</td><td>0.937535</td></tr><tr><td>8</td><td>cube0</td><td>95.640541</td><td>176935</td><td>55.976215</td><td>0.585277</td><td>58.24054</td><td>0.608952</td><td>40.447567</td><td>0.422912</td><td>89.642159</td><td>0.937282</td></tr><tr><td>9</td><td>cube0</td><td>96.136757</td><td>177853</td><td>55.721622</td><td>0.579608</td><td>57.837296</td><td>0.601615</td><td>40.551891</td><td>0.421815</td><td>88.26973</td><td>0.918168</td></tr><tr><td>10</td><td>cube0</td><td>96.471352</td><td>178472</td><td>55.834595</td><td>0.578769</td><td>56.701622</td><td>0.587756</td><td>40.582703</td><td>0.420671</td><td>88.286484</td><td>0.915158</td></tr><tr><td>11</td><td>cube0</td><td>95.916214</td><td>177445</td><td>55.696217</td><td>0.580676</td><td>56.547028</td><td>0.589546</td><td>40.754593</td><td>0.424898</td><td>88.122704</td><td>0.918747</td></tr><tr><td>12</td><td>cube0</td><td>97.657837</td><td>180667</td><td>55.989189</td><td>0.57332</td><td>56.523243</td><td>0.578789</td><td>40.53838</td><td>0.415106</td><td>91.364326</td><td>0.935555</td></tr><tr><td>13</td><td>cube0</td><td>97.375679</td><td>180145</td><td>56.216217</td><td>0.577313</td><td>56.554596</td><td>0.580788</td><td>40.586487</td><td>0.416803</td><td>91.158379</td><td>0.936151</td></tr><tr><td>14</td><td>cube0</td><td>96.977295</td><td>179408</td><td>56.20108</td><td>0.579528</td><td>57.469189</td><td>0.592605</td><td>40.312431</td><td>0.415689</td><td>91.942703</td><td>0.948085</td></tr><tr><td>15</td><td>cube0</td><td>97.511353</td><td>180396</td><td>55.836758</td><td>0.572618</td><td>57.203243</td><td>0.586632</td><td>40.582703</td><td>0.416184</td><td>90.81189</td><td>0.931296</td></tr><tr><td>16</td><td>cube0</td><td>97.162704</td><td>179751</td><td>55.779461</td><td>0.574083</td><td>57.581081</td><td>0.592625</td><td>40.311893</td><td>0.414891</td><td>90.610268</td><td>0.932562</td></tr><tr><td>17</td><td>cube0</td><td>97.564323</td><td>180494</td><td>56.042702</td><td>0.574418</td><td>57.611351</td><td>0.590496</td><td>40.426487</td><td>0.414357</td><td>91.854057</td><td>0.941472</td></tr><tr><td>18</td><td>cube0</td><td>96.501625</td><td>178528</td><td>55.714054</td><td>0.577338</td><td>57.474052</td><td>0.595576</td><td>40.663784</td><td>0.421379</td><td>89.143784</td><td>0.923754</td></tr><tr><td>19</td><td>cube0</td><td>96.171349</td><td>177917</td><td>55.944324</td><td>0.581715</td><td>57.375675</td><td>0.596598</td><td>40.725407</td><td>0.423467</td><td>89.225403</td><td>0.927775</td></tr><tr><td>20</td><td>cube0</td><td>96.37027</td><td>178285</td><td>55.652973</td><td>0.577491</td><td>57.369728</td><td>0.595305</td><td>40.465946</td><td>0.419901</td><td>89.97081</td><td>0.933595</td></tr><tr><td>21</td><td>cube0</td><td>96.087029</td><td>177761</td><td>55.860542</td><td>0.581354</td><td>57.825405</td><td>0.601802</td><td>40.457836</td><td>0.421054</td><td>89.34919</td><td>0.929878</td></tr><tr><td>22</td><td>cube0</td><td>96.438377</td><td>178411</td><td>55.589188</td><td>0.576422</td><td>57.696758</td><td>0.598276</td><td>40.523243</td><td>0.420198</td><td>89.07267</td><td>0.923598</td></tr><tr><td>23</td><td>cube0</td><td>95.808647</td><td>177246</td><td>55.984863</td><td>0.58434</td><td>57.725945</td><td>0.602513</td><td>40.36108</td><td>0.421268</td><td>89.839996</td><td>0.937702</td></tr></table>

MTE2的搬运效率还可以通过查看其带宽利用率进行验证，如下图所示，通过分析 Memory.csv，发现MTE2平均带宽利用率只有34.4%。 

<table><tr><td>read_main_memory datas(KB)</td><td>write_main_memory datas(KB)</td><td>GM_to_L1 datas(KB)</td><td>GM_to_L1_bwusage_rate(%)</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>34.257599</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>34.295368</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>34.028015</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>34.246742</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>34.245407</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>34.040989</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>34.594139</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>34.713074</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>34.809402</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>34.629734</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>34.509628</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>34.709358</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>34.090355</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>34.189137</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>34.329586</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>34.141567</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>34.264076</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>34.123032</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>34.498802</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>34.617279</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>34.545826</td></tr><tr><td>9216.75</td><td>256.125</td><td>9216</td><td>34.647655</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>34.521423</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>34.748329</td></tr></table>

查看OpBasicInfo.csv文件，优化前算子整体耗时为98.72us。 

# 设计优化方案

使能K轴错峰访问内存：在创建Matmul对象时，将MatmulConfig中的 enableKdimReorderLoad参数设置为true。enableKdimReorderLoad参数的详细介绍 请参考MatmulConfig。 

使能K轴错峰访问内存的完整样例请参考K轴错峰加载数据的算子样例。使能该功能的 主要步骤如下： 

步骤1 配置MDL模板参数，将其中的enableKdimReorderLoad参数设置为true，使能多核K轴 错峰访问Device内存。 

constexpr MatmulConfig GetMDLKDImReorderConfig()   
{ auto CFG $=$ CFG_MDL; CFG enableKdimReorderLoad $=$ true; return CFG;   
}   
constexpr static MatmulConfig MM_CFG $=$ GetMDLKDImReorderConfig(); 

步骤2 基于自定义的MatmulConfig模板参数，创建Matmul对象。 

```cpp
AscendC::Matmul<AscendC::MatmulType<TPosition::GM, CubeFormat::ND, aType>, AscendC::MatmulType<TPosition::GM, CubeFormat::ND, bType>, AscendC::MatmulType<TPosition::GM, CubeFormat::ND, cType>, AscendC::MatmulType<TPosition::GM, CubeFormat::ND, biasType>, MM_CFG> matmulObj; 
```

----结束 

# 验证优化方案性能收益

算子Tiling参数不变，优化后的Profiling数据（PipeUtilization.csv）如下所示。可以看 到，MTE2耗时显著降低，MTE2的平均耗时从90us降低到69.87us，最大耗时从 91.94us降低到75.82us。 

<table><tr><td>block_id</td><td>sub_block_id</td><td>aic_time(us)</td><td>aic_total_cycles</td><td>aic_cube_time(us)</td><td>aic_cube_ratio</td><td>aicScalar_time(us)</td><td>aicScalar_ratio</td><td>aic_mte1_time(us)</td><td>aic_mte1_ratio</td><td>aic_mte2_time(us)</td><td>aic_mte2_ratio</td></tr><tr><td>0</td><td>cube0</td><td>78.071892</td><td>144433</td><td>53.95892</td><td>0.691144</td><td>58.42865</td><td>0.748395</td><td>43.446487</td><td>0.556493</td><td>69.223785</td><td>0.886667</td></tr><tr><td>1</td><td>cube0</td><td>77.507568</td><td>143389</td><td>54.162704</td><td>0.698805</td><td>57.375134</td><td>0.740252</td><td>43.763783</td><td>0.564639</td><td>68.304863</td><td>0.881267</td></tr><tr><td>2</td><td>cube0</td><td>78.468651</td><td>145167</td><td>53.987568</td><td>0.688015</td><td>56.552975</td><td>0.720708</td><td>43.652973</td><td>0.556311</td><td>68.991348</td><td>0.879222</td></tr><tr><td>3</td><td>cube0</td><td>79.827568</td><td>147681</td><td>53.952972</td><td>0.675869</td><td>57.167568</td><td>0.716138</td><td>43.250271</td><td>0.541796</td><td>69.38324</td><td>0.869164</td></tr><tr><td>4</td><td>cube0</td><td>80.668648</td><td>149237</td><td>53.994595</td><td>0.669338</td><td>58.288109</td><td>0.722562</td><td>43.816216</td><td>0.543163</td><td>69.952972</td><td>0.867164</td></tr><tr><td>5</td><td>cube0</td><td>84.896217</td><td>157058</td><td>54.560001</td><td>0.642667</td><td>58.983784</td><td>0.694775</td><td>42.615135</td><td>0.501967</td><td>75.561081</td><td>0.890041</td></tr><tr><td>6</td><td>cube0</td><td>78.974052</td><td>146102</td><td>53.936214</td><td>0.682961</td><td>58.467567</td><td>0.740339</td><td>43.268108</td><td>0.547877</td><td>68.018379</td><td>0.861275</td></tr><tr><td>7</td><td>cube0</td><td>78.737297</td><td>145664</td><td>54.020542</td><td>0.686086</td><td>58.810268</td><td>0.746918</td><td>43.918919</td><td>0.557791</td><td>67.791893</td><td>0.860988</td></tr><tr><td>8</td><td>cube0</td><td>78.758919</td><td>145704</td><td>53.978378</td><td>0.685362</td><td>58.65892</td><td>0.74791</td><td>43.52919</td><td>0.552689</td><td>68.038918</td><td>0.863888</td></tr><tr><td>9</td><td>cube0</td><td>79.076218</td><td>146291</td><td>53.92054</td><td>0.681881</td><td>58.251892</td><td>0.736655</td><td>43.400002</td><td>0.548838</td><td>67.408112</td><td>0.852445</td></tr><tr><td>10</td><td>cube0</td><td>79.098381</td><td>146332</td><td>54.211349</td><td>0.685366</td><td>58.585407</td><td>0.740665</td><td>43.184864</td><td>0.545964</td><td>69.188652</td><td>0.874716</td></tr><tr><td>11</td><td>cube0</td><td>82.610809</td><td>152830</td><td>54.591892</td><td>0.660832</td><td>59.13892</td><td>0.715874</td><td>42.374054</td><td>0.512936</td><td>74.741081</td><td>0.904737</td></tr><tr><td>12</td><td>cube0</td><td>78.178917</td><td>144631</td><td>53.951351</td><td>0.690101</td><td>56.943783</td><td>0.728378</td><td>43.131893</td><td>0.551707</td><td>69.227028</td><td>0.885495</td></tr><tr><td>13</td><td>cube0</td><td>77.57301</td><td>143518</td><td>53.989189</td><td>0.695941</td><td>56.585945</td><td>0.729414</td><td>43.57135</td><td>0.561651</td><td>68.375137</td><td>0.881381</td></tr><tr><td>14</td><td>cube0</td><td>79.400002</td><td>146890</td><td>54.136215</td><td>0.681816</td><td>57.812431</td><td>0.728116</td><td>44.243782</td><td>0.557226</td><td>68.981079</td><td>0.868779</td></tr><tr><td>15</td><td>cube0</td><td>79.317841</td><td>146738</td><td>54.033512</td><td>0.681228</td><td>57.177296</td><td>0.720863</td><td>43.816757</td><td>0.55242</td><td>68.676216</td><td>0.865836</td></tr><tr><td>16</td><td>cube0</td><td>80.390808</td><td>148723</td><td>54.009731</td><td>0.67184</td><td>57.611893</td><td>0.716648</td><td>43.364864</td><td>0.539426</td><td>70.575676</td><td>0.877907</td></tr><tr><td>17</td><td>cube0</td><td>84.824326</td><td>156925</td><td>54.648109</td><td>0.64425</td><td>58.284866</td><td>0.687124</td><td>42.815136</td><td>0.504751</td><td>76.032433</td><td>0.896352</td></tr><tr><td>18</td><td>cube0</td><td>78.860001</td><td>145891</td><td>54.025948</td><td>0.685087</td><td>57.82</td><td>0.733198</td><td>43.699459</td><td>0.55414</td><td>68.462166</td><td>0.868148</td></tr><tr><td>19</td><td>cube0</td><td>79.150269</td><td>146428</td><td>54.017296</td><td>0.682465</td><td>58.177296</td><td>0.735023</td><td>43.815674</td><td>0.553576</td><td>68.165947</td><td>0.861222</td></tr><tr><td>20</td><td>cube0</td><td>79.089188</td><td>146315</td><td>53.98811</td><td>0.682623</td><td>57.604324</td><td>0.728346</td><td>43.797298</td><td>0.553771</td><td>68.152435</td><td>0.861716</td></tr><tr><td>21</td><td>cube0</td><td>78.625946</td><td>145458</td><td>53.952972</td><td>0.686198</td><td>57.782703</td><td>0.734906</td><td>44.067028</td><td>0.560464</td><td>67.874054</td><td>0.863253</td></tr><tr><td>22</td><td>cube0</td><td>80.194595</td><td>148360</td><td>53.974052</td><td>0.673039</td><td>57.956577</td><td>0.722688</td><td>43.76865</td><td>0.545781</td><td>70.025406</td><td>0.873194</td></tr><tr><td>23</td><td>cube0</td><td>84.536758</td><td>156393</td><td>54.593513</td><td>0.645796</td><td>58.799461</td><td>0.695549</td><td>43.023785</td><td>0.508936</td><td>75.827026</td><td>0.896971</td></tr></table>

MTE2的带宽利用率（Memory.csv）如下所示，平均带宽利用率提升到 $4 1 . 7 \%$ 。 

<table><tr><td>read_main_memory datas(KB)</td><td>write_main_memory datas(KB)</td><td>GM_to_L1 datas(KB)</td><td>GM_to_L1_bw_use_rate(%)</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>42.642628</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>42.953102</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>42.42701</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>41.704773</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>41.269943</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>39.214825</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>42.155495</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>42.282257</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>42.270645</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>42.101028</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>42.089233</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>40.299694</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>42.584248</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>42.91449</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>41.929348</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>41.972782</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>41.412575</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>39.248062</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>42.216465</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>42.061646</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>42.094128</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>42.342133</td></tr><tr><td>9216.875</td><td>256.25</td><td>9216</td><td>41.513901</td></tr><tr><td>9216.75</td><td>256.125</td><td>9216</td><td>39.381569</td></tr></table>

查看OpBasicInfo.csv文件，优化后算子整体耗时为85.68us，耗时从98.72us降低到 85.68us，性能提升13.2%。 

# 总结

在多核执行Matmul的场景，当输入矩阵K轴较大（一般大于4096）时，可以尝试使用 MDL模板并开启K轴错峰访问内存的功能，缓解地址访问冲突，提升MTE2搬运效率， 进而优化算子性能。 

# 3.10.4.10 Matmul 高阶 API 使能 NBuffer33 模板

# 案例介绍

本案例呈现了在矩阵乘算子场景中，使用Matmul高阶API进行矩阵乘法计算，使能 NBuffer33模板对算子性能的提升效果。NBuffer33模板的实现为单核计算的A矩阵切 分为3x3个基本块，该3x3个A矩阵的基本块全载和保持在L1 Buffer中，每次与3x1个B 矩阵的基本块计算矩阵乘，同时DoubleBuffer并行搬入下次计算所需的3x1个B矩阵基 本块，直到singleCoreN方向的矩阵乘计算完成。针对MTE2 Bound场景，通过 NBuffer33算法的切分数据方式，错开搬运流水，减少单次搬运的数据量，平衡MTE2 和FixPipe的数据流量，让两者带宽均匀分布。NBuffer33模板的详细介绍请参考 MatmulPolicy。 

使能NBuffer33模板的适用场景 

MTE2 Bound的场景，Tiling参数满足约束条件时，可以使能NBuffer33模板。 

使能NBuffer33模板的约束条件 

仅支持MatmulConfig为MDL模板。 

A矩阵、B矩阵的内存逻辑位置只支持TPosition::GM。 

仅支持纯Cube模式（只有矩阵计算），暂不支持MIX模式（包含矩阵计算和 矢量计算）。 

仅支持通过IterateAll接口获取Matmul的计算结果C矩阵。 

stepM、stepKa、stepKb小于等于3，且满足： 

stepKa $=$ stepKb $| =$ Ceil(singleCoreK/baseK)。 

A矩阵全载的基本块大小与B矩阵载入的基本块大小之和不超过L1 Buffer的大 小。 

本案例的算子规格如下： 


表 3-41 算子规格


<table><tr><td>输入</td><td>Shape</td><td>Data type</td><td>Format</td></tr><tr><td>a</td><td>256, 192</td><td>float16</td><td>ND</td></tr><tr><td>b</td><td>192, 512</td><td>float16</td><td>ND</td></tr></table>

当前案例使用的AI处理器共24个核，算子中使能高阶API Matmul的纯Cube模式，使用 MDL模板，Tiling参数如下： 

原始shape： $\mathtt { M } = 2 5 6$ , N=512, $\mathsf { K } = \mathsf { 1 9 2 }$ 。 

● 单核shape：singleCoreM $= 2 5 6$ ，singleCoreN $\mathtt { I } = 2 5 6$ ，singleCoreK=192。 

基本块shape：baseM=128，baseN=256，baseK $\mathtt { - 6 4 }$ 。 

L1缓存相关Tiling参数：stepM=2，stepN=1，stepKa $^ { = 3 }$ ，stepKb=3。 

# 获取性能数据

使用msProf工具获取算子仿真流水图和上板Profiling数据，重点分析Cube、Fixpipe的 流水情况。 

# 分析主要瓶颈点

优化前的流水图如下，MatmulPolicy的默认模板下A、B矩阵全载，A、B矩阵都只 搬运一次。此时MTE2执行时间较长，且流水整体呈串行。 

![](images/9cd125e97ad7610e047bd05b34b72fac24490ce534a93caf17e4c80493babfa1.jpg)


优化前的Profiling数据如下，aic_time平均耗时34.01us。 

<table><tr><td>A</td><td>B</td><td>C</td><td>D</td><td>E</td><td>F</td><td>G</td><td>H</td><td>I</td><td>J</td><td>K</td><td>L</td><td>M</td><td>N</td><td>O</td><td>P</td></tr><tr><td>1</td><td>block_id</td><td>sub_block_id</td><td>ac_time(s)</td><td>ac_total_cycle</td><td>ac Cube_time(s)</td><td>ac Cube_ratio</td><td>acScalar_time(s)</td><td>acScalar_ratio</td><td>ac_mtei_time(s)</td><td>ac_mtei_ratio</td><td>ac_mte3_time(s)</td><td>ac_mte3_ratio</td><td>ac_fixupce_time(s)</td><td>ac_fixupce_ratio</td><td>ac_fixupce ratio</td></tr><tr><td>2</td><td>cube0</td><td>03430459</td><td>62964</td><td>1707027</td><td>0.050156</td><td>5.18972</td><td>0.152508</td><td>1.160541</td><td>0.034135</td><td>10.97837</td><td>0.297009</td><td>0.001081</td><td>0.000032</td><td>15.78495</td><td>0.464593</td></tr><tr><td>3</td><td>1 cube0</td><td></td><td></td><td></td><td></td><td>5121081</td><td>0.150467</td><td>1.160541</td><td>0.034099</td><td>9.201622</td><td>0.270361</td><td>0.001081</td><td>0.000032</td><td></td><td>0.485706</td></tr></table>

# 设计优化方案

使能NBuffer33模板：在GetTiling接口前，调用SetMatmulConfigParams接口开启 NBuffer33模式，使获取的Tiling满足要求；Kernel侧在创建Matmul对象时使能 NBuffer33模板。使能NBuffer33模板的完整样例请参考使能NBuffer33模板策略的样 例。具体步骤如下： 

# Tiling实现

调用GetTiling接口获取TCubeTiling结构体前，开启NBuffer33模式。 

```cpp
matmul_tiling::MatmulConfigParams matmulConfigParams(1, false, matmul_tiling::ScheduleType::N_buffer_33, /* NBuffer33模式 */ matmul_tiling::MatrixTraverse::NOSET, false);  
cubeTiling.SetMatmulConfigParams(matmulConfigParams);  
if (cubeTiling.GetTiling(tilingData) == -1) { std::cout << "Generate tiling failed." << std::endl; return {}; } 
```

# Kernel实现

设置模板参数MatmulPolicy为NBuffer33模板策略，创建Matmul对象。 

```rust
AscendC::MatmullImpl< AscendC::MatmuleType<AscendC::TPosition::GM, CubeFormat::ND, aType>, AscendC::MatmuleType<AscendC::TPosition::GM, CubeFormat::ND, bType>, AscendC::MatmuleType<AscendC::TPosition::GM, CubeFormat::ND, cType>, AscendC::MatmuleType<AscendC::TPosition::GM, CubeFormat::ND, biasType>, CFG_MDL, AscendC::MatmulBackFunc<nullptr, nullptr, nullptr>, AscendC::Impl::Detail::NBuffer33MatmulPolicy> matmulObj; 
```

# 验证优化方案性能收益

优化后的流水图如下，Tiling参数不变，但由于stepM为2，NBuffer33模式会将左 矩阵数据的搬运拆分为两次。可以看到，第一次MTE2结束后的计算过程（包括 MTE1、MMAD和FIXPIPE）可以和第二次MTE2并行。分块搬运数据可以减少一 次搬运数据导致的部分头开销，优化加载数据的性能。 

![](images/258184e2afc9b8c16e9d687b9fc36595db480c933fe808e9dca6487f69edb6e5.jpg)


优化后的Profiling数据如下，aic_time平均耗时32.66us，较优化前的34.01us有所 提升。 

![](images/430fbb3d47242a5b1e06085c6d448f356d5507e24f4d7312901ab755cc92e026.jpg)


# 总结

MTE2 Bound的场景，Tiling参数满足stepM、stepKa、stepKb小于等于3的条件时， 可以考虑使能NBuffer33模板，切分矩阵将搬运流水错开， 减少单次搬运的数据量， 平衡MTE2和FixPipe的数据流量。 

# 3.10.4.11 Matmul 高阶 API 使能 IBShare 模板共享 B 矩阵数据

# 案例介绍

本案例呈现了在矩阵乘算子场景中，使用Matmul高阶API进行矩阵乘法计算，B矩阵使 能IBShare对算子性能的提升效果。IBShare功能通过共享L1 Buffer上相同的A矩阵或B 矩阵数据，减少重复的MTE2数据搬运开销，提升算子性能。该功能支持A矩阵和B矩 阵其中一个矩阵使能IBShare，也支持A矩阵和B矩阵同时使能IBShare。 

使能IBShare的适用场景 

MIX场景（包含矩阵计算和矢量计算）下，多个AIV的A矩阵或B矩阵GM地址相 同，且多个AIV复用的A矩阵或B矩阵在L1 Buffer上全载。 

使能IBShare的约束条件 

A矩阵和B矩阵同时使能IBShare的场景，同一算子中其它Matmul对象的A矩 阵和B矩阵也必须同时使能IBShare。 

A矩阵和B矩阵同时使能IBShare的场景，获取矩阵计算结果时，只支持调用 IterateAll接口，且只支持输出到Global Memory。 

本案例的算子规格如下： 


表 3-42 算子规格


<table><tr><td>输入</td><td>Shape</td><td>Data type</td><td>Format</td></tr><tr><td>a</td><td>64, 384</td><td>float16</td><td>ND</td></tr><tr><td>b</td><td>384, 256</td><td>float16</td><td>ND</td></tr></table>

当前案例使用的AI处理器共20个核，每个核中包含1个AIC核和2个AIV核。因为输入 shape较小，本案例以单核为示例，参考SetDim接口在MIX模式下的使用，在Tiling程 序中设置参与运算的核数为2。Tiling参数如下： 

原始shape：M=64, N= 256, K=384。 

单核shape：singleCoreM=32，singleCoreN=256，singleCoreK=384。A矩阵拆 成两半，一半在AIV0上处理，一半在AIV1上处理；AIV0和AIV1使用的B矩阵数据 相同。 

基本块shape：baseM=32，baseN=256，baseK=64。 

L1缓存相关Tiling参数：stepM=1，stepN=1，stepKa=6，stepKb=6。 

# 获取性能数据

使用msProf工具获取算子仿真流水图和上板Profiling数据，因为IBShare功能主要是通 过共享L1 Buffer上相同的A矩阵或B矩阵数据，减少重复的MTE2数据搬运开销，所以 重点分析MTE2的流水情况。 

# 分析主要瓶颈点

优化前的流水图如下，不使能IBShare模板，默认使用的Norm模板。黑框标识 AIV0发起的MTE2搬运流水：MTE2总共搬运了12次，其中A矩阵搬运了6次 （stepM*stepKa=6），B矩阵搬运了6次（stepN*stepKb=6）。红框标识的AIV1 发起的MTE2搬运流水，跟AIV0基本一致。在该案例中，因为AIV1使用的B矩阵跟 AIV0使用的B矩阵数据相同，且singleCoreN=baseN*stepN， singleCoreK=baseK*stepKb，即B矩阵可以在L1全载。考虑在AIV0搬入B矩阵到L1 Buffer后，将B矩阵数据缓存在L1 Buffer上等待AIV1进行复用，进而节省B矩阵的 MTE2重复搬运开销。 

![](images/8c6812570bc3e1282089df35c1bae04aa5a49fe7039971c72c256fa6164061cd.jpg)


优化前的Profiling数据如下，C列的aic_time是10.29us，K列的aic_mte2_time是 5.56us。 

![](images/f0bfdf03f691ec2eb0ef8bd77388066df7d3b94346f958422e9e5af45f9be09a.jpg)


# 设计优化方案

下图是不使能IBShare模板（默认使用Norm模板）的Matmul计算流水示意图。MTE2 分多次从Global Memory搬运基本块到A1或B1，即使前后两次搬运的B矩阵基本块数 据是相同的数据，也会重复搬运。 


图 3-182 不使能 IBShare 模板的 Matmul 流水示意图


![](images/6184fda3301b149bae84579c5b7867574d06e440d25540b4ac8acd228abc316a.jpg)


下图是使能IBShare模板的Matmul计算流水示意图。MTE2分多次从Global Memory搬 运基本块到A1或B1，若前后两次搬运的B矩阵基本块数据相同，不会重复搬运，第一 次搬运到B1内的数据会被复用。 


图 3-183 使能 IBShare 模板的 Matmul 流水示意图


![](images/690554b91a531761953e5248048b7dfac7cabfc63f1c9830f4288eb2bf9bbd70.jpg)


Matmul API使能IBShare模板共享B矩阵的完整样例请参考仅B矩阵使能IBShare样例。 使能IBShare功能的主要步骤如下： 

步骤1 创建Matmul对象。 

```cpp
define ASCENDC_CUBE_ONLY
#include "lib/matmul_intf.h"
using A_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, AType>;
using B_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, BType, false,
商业模式::NONE, true>; // 设置B矩阵的IBSHARE参数为true
using C_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, CType>;
using BIAS_TYPE = AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, BiasType>;
AscendC::Matmul<A_TYPE, B_TYPE, C_TYPE, BIAS_TYPE, CFG(IBSHARE_NORM> matmulObj; // 使用默认的
IBShare模板参数CFG(IBSHARE_NORM定义Matmul对象 
```

# ----结束

# 验证优化方案性能收益

优化后的流水图如下，黑框标识的AIV0发起的MTE2搬运流水，与优化前一致。红 框标识的AIV1发起的MTE2搬运流水，相较于优化前的A矩阵和B矩阵一共12次 MTE2数据搬运，减少到了仅6次A矩阵的MTE2数据搬运，省去了B矩阵的6次 MTE2数据搬运开销。 

![](images/af50d0904c34e0c26ca9554f0c945b7e74178f00f21373eabd3331ede6e5c6de.jpg)


优化后的Profiling数据如下，C列的aic_time是9.93us，较优化前的10.29us提升了 3.55%。K列的aic_mte2_time是4.71us，较优化前的5.56us提升了15.46%。 

<table><tr><td>A</td><td>B</td><td>C</td><td>D</td><td>E</td><td>F</td><td>G</td><td>H</td><td>I</td><td>J</td><td>K</td><td>L</td><td>M</td><td>N</td><td>O</td><td>P</td></tr><tr><td>1</td><td>block_id</td><td>sub_block_id</td><td>alc_time(g)</td><td>alc_total_cycles</td><td>alc_blockTime</td><td>alc_block_ratio</td><td>alc_block_ratio</td><td>alc_block_ratio</td><td>alc_block_ratio</td><td>alc_block_ratio</td><td>alc_block_ratio</td><td>alc_block_ratio</td><td>alc_block_ratio</td><td>alc_block_ratio</td><td>alc_block_ratio</td></tr><tr><td>2</td><td>0</td><td>0</td><td>9.47545</td><td>NA</td><td>NA</td><td>0.0249</td><td>9.47545</td><td>0.02794</td><td>2.264845</td><td>0.47273</td><td>1.07171</td><td>0.6306</td><td>0.00992</td><td>0.10755</td><td>NA</td></tr><tr><td>3</td><td>0</td><td>vector</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td></tr><tr><td>4</td><td>0</td><td>vector</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td><td>NA</td></tr></table>

# 总结

MIX场景（包含矩阵计算和矢量计算）下，若多个AIV的A矩阵或B矩阵GM地址相同， 且多个AIV复用的A矩阵/B矩阵在L1 Buffer上全载。可以考虑使能IBShare模板，通过 共享L1 Buffer上相同的A矩阵或B矩阵数据，减少重复的MTE2数据搬运开销，提升算 子性能。 

# 3.10.4.12 Matmul 高阶 API 使能 IBShare 模板共享 A 和 B 矩阵数据

# 案例介绍

本案例呈现了在融合算子场景中，使用Matmul高阶API进行矩阵乘法计算时，A矩阵和 B矩阵同时启用IBShare对性能的提升效果。 

该案例的关键优化措施包括： 

分核逻辑：以Cube核视角分核，Matmul计算结果输出到GM，提供给Vector核进 行后续计算。 

开启IBShare：A矩阵和B矩阵同时开启IBShare。 

本案例的算子规格如下： 


表3-43 算子规格


<table><tr><td>输入</td><td>Shape</td><td>Data type</td><td>Format</td></tr><tr><td>x</td><td>128,384</td><td>float16</td><td>ND</td></tr><tr><td>y</td><td>384,256</td><td>float16</td><td>ND</td></tr></table>

开启IBShare和未开启IBShare的完整样例请参考A、B矩阵均使能IBShare样例和 MatmulNoABshare样例。 

# 获取性能数据

使用msProf工具获取算子的Profiling的数据，重点分析MTE2，Cube，Scalar的流水情 况。 

# 分析主要瓶颈点


图 3-184 优化前 Profiling 数据


<table><tr><td>Op Name</td><td>Task Type</td><td>Task Duration</td><td>Task V</td><td>ai core</td><td>aic</td><td>tota</td><td>ai mac</td><td>mac</td><td>mca</td><td>icac</td><td>scalar</td><td>time</td><td>aic</td><td>sca</td><td>ic</td><td>mte</td><td>ic</td><td>mtte</td><td>ic</td><td>mte2</td><td>ai</td><td>mtte</td><td>ic</td><td>fixip</td><td>ic</td><td>fixip</td><td>ic</td><td>mach</td><td>iv</td><td>time</td><td>auiv</td><td>total</td><td>cai</td><td>vec</td><td>tic</td><td>inv</td><td>vec</td><td>rat</td><td>ai</td><td>scalar</td><td>ia</td><td>scalar</td></tr><tr><td>matmul.noAibsharecustom</td><td>MIX_AIC</td><td></td><td>27</td><td>26.651</td><td>27</td><td>26.3</td><td>48589</td><td>275</td><td>0.105</td><td>25.753</td><td>0.981</td><td>4953</td><td>0.189</td><td>9854</td><td>0.375</td><td>0.158</td><td>0.017</td><td>0.572</td><td>0.005</td><td>20.74</td><td>76729</td><td>0.042</td><td>0.002</td><td>4.941</td><td>0.238</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>matmul.noAibshare custom</td><td>MIX_AIC</td><td></td><td>27.341</td><td>2.98</td><td>26.9</td><td>49618</td><td>275</td><td>0.102</td><td>26.393</td><td>0.996</td><td>4954</td><td>0.184</td><td>10.048</td><td>0.373</td><td>0.156</td><td>0.026</td><td>0.565</td><td>0.007</td><td>21.09</td><td>78033</td><td>0.042</td><td>0.002</td><td>4.934</td><td>0.234</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>matmul.noAibshare custom</td><td>MIX_AIC</td><td></td><td>27.441</td><td>2.96</td><td>27.1</td><td>50123</td><td>275</td><td>0.102</td><td>26.615</td><td>0.982</td><td>4953</td><td>0.183</td><td>10.152</td><td>0.375</td><td>0.1533</td><td>0.566</td><td>0.005</td><td>21.05</td><td>77890</td><td>0.042</td><td>0.002</td><td>4.71</td><td>0.224</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>matmul.noAibshare custom</td><td>MIX_AIC</td><td></td><td>27.48</td><td>2.86</td><td>27.1</td><td>50142</td><td>275</td><td>0.101</td><td>26.777</td><td>0.988</td><td>4953</td><td>0.183</td><td>10.117</td><td>0.375</td><td>0.1537</td><td>0.567</td><td>0.005</td><td>21.29</td><td>78788</td><td>0.042</td><td>0.002</td><td>4.884</td><td>0.229</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>matmul.noAibshare custom</td><td>MIX_AIC</td><td></td><td>26.8</td><td>2.82</td><td>26.4</td><td>48870</td><td>2751</td><td>0.104</td><td>26.122</td><td>0.989</td><td>4955</td><td>0.188</td><td>9.935</td><td>0.376</td><td>0.1509</td><td>0.57</td><td>0.006</td><td>20.91</td><td>77352</td><td>0.042</td><td>0.002</td><td>5.004</td><td>0.239</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>matmul.noAibshare custom</td><td>MIX_AIC</td><td></td><td>26.701</td><td>2.9</td><td>26.3</td><td>48653</td><td>275</td><td>0.105</td><td>25.772</td><td>0.98</td><td>4954</td><td>0.188</td><td>9.923</td><td>0.377</td><td>0.1572</td><td>0.573</td><td>0.006</td><td>20.9</td><td>77324</td><td>0.042</td><td>0.002</td><td>4.85</td><td>0.232</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>matmul.noAibshare custom</td><td>MIX_AIC</td><td></td><td>26.881</td><td>2.92</td><td>26.5</td><td>48939</td><td>275</td><td>0.104</td><td>25.956</td><td>0.981</td><td>4953</td><td>0.187</td><td>10.169</td><td>0.384</td><td>0.1536</td><td>0.58</td><td>0.005</td><td>20.85</td><td>77148</td><td>0.042</td><td>0.002</td><td>4.74</td><td>0.227</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>matmul.noAibshare custom</td><td>MIX_AIC</td><td></td><td>27.041</td><td>2.78</td><td>26.6</td><td>49225</td><td>275</td><td>0.103</td><td>26.081</td><td>0.98</td><td>4954</td><td>0.186</td><td>10.25</td><td>0.385</td><td>0.1538</td><td>0.579</td><td>0.006</td><td>21.07</td><td>77959</td><td>0.042</td><td>0.002</td><td>4.748</td><td>0.225</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>matmul.noAibshare custom</td><td>MIX_AIC</td><td></td><td>27.28</td><td>2.68</td><td>27</td><td>49893</td><td>275</td><td>0.102</td><td>26.488</td><td>0.962</td><td>4954</td><td>0.184</td><td>10.119</td><td>0.375</td><td>0.1529</td><td>0.567</td><td>0.005</td><td>21.15</td><td>78248</td><td>0.042</td><td>0.002</td><td>4.745</td><td>0.224</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>matmul.noAibshare custom</td><td>MIX_AIC</td><td></td><td>27.52</td><td>3.02</td><td>27.2</td><td>50314</td><td>2751</td><td>0.101</td><td>26.672</td><td>0.981</td><td>4954</td><td>0.182</td><td>10.349</td><td>0.38</td><td>0.1529</td><td>0.571</td><td>0.005</td><td>21.42</td><td>79243</td><td>0.042</td><td>0.002</td><td>4.774</td><td>0.223</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr></table>

通过分析以上Profiling数据可以看出，算子执行多次的平均耗时为27.11us， aic_scalar_time的平均耗时为26.27us，当前性能瓶颈点为Cube的Scalar流水。 

# 设计优化方案

A矩阵和B矩阵均未开启IBShare时，数据需要根据K轴、M轴或N轴进行切分计算。这 里以K轴切分为例，未开启IBShare之前，算子以AIV Block为视角进行tiling切分， AIV0发起A0*B0的计算，AIV1发起A1*B1的计算。 


图 3-185 未开启 IBShare


![](images/58b378c8d82a533ff12e866c306c0c092cb442ffe658580cbdb9137d9b9cc336.jpg)


当A矩阵和B矩阵都启用IBShare时，可以一次性加载到L1 Buffer上，省去了切分，分 开搬运的过程，同时Cube计算单元完全由AIV0单核驱动，发起一次计算，计算的结果 由AIV0和AIV1共享，从而减少Cube响应的次数，减少Scalar计算。 


图 3-186 开启 IBShare


![](images/d35869921015c791592e930592adb9b13ae3c4fa6cc38cb496e0b2ebd3499932.jpg)


开启IBShare和不开启IBShare的数据交互对比示意图如下： 

![](images/9b2207702feac52722bc910d670896d2298dd7c15ac2c039bada676dc44cad71.jpg)


![](images/19e162c298850a1f4c1ae2f32948a6acbc4c6530e08d4873405e85cf0bed1ad6.jpg)


通过设置A和B矩阵MatmulType的IBShare均为true，开启该优化，具体代码如下： 

```cpp
constexpr bool isABshare = true;   
template <typename aType, typename bType, typename cType> class MatmulABshareKernel {   
public: __aicore__ inline MatmulABshareKernel();   
__aicore__ inline void Init(GM_ADDR a, GM_ADDR b, GM_ADDR c, GM_ADDR workspace, const TCubeTiling &tiling, AscendC::TPipe *pipe);   
__aicore__ inline void Process(AscendC::TPipe *pipe);   
__aicore__ inline void CalcOffset(int32_t blockIdx, const TCubeTiling &tiling, int32_t &offsetA, int32_t &offsetB, int32_t &offsetC);   
AscendC::Matmul<AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, aType, false, LayoutMode::NONE, isABshare>, AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, bType, false, LayoutMode::NONE, isABshare>, AscendC::MatmulType<AscendC::TPosition::VECIN, CubeFormat::ND, cType>> matmulObj; 
```

AscendC::GlobalTensor<aType>aGlobal; AscendC::GlobalTensor<bType>bGlobal; AscendC::GlobalTensor<cType>cGlobal; TCubeTiling tiling;   
}; template <typename aType, typename bType, typename cType> __aicore__inline void MatmulABshareKernel<aType,bType,cType>::Init(GM_ADDR a,GM_ADDR b, GM_ADDR c, GM_ADDR workspace,const TCubeTiling &tiling, AscendC::TPipe *pipe) { this->tiling = tiling; aGlobal.SetGlobalBuffer(reinterpret_cast<_gm__aType $\succ$ aType $\succ$ aType $\succ$ aType $\succ$ aType $\succ$ aType $\succ$ aType $\succ$ aType $\succ$ aType $\succ$ aType $\succ$ aType $\succ$ aType $\succ$ aType $\succ$ aType $\succ$ aType $\succ$ aType $\succ$ aType $\succ$ aType $\rightarrow$ aType $\rightarrow$ aType $\rightarrow$ aType $\rightarrow$ aType $\rightarrow$ aType $\rightarrow$ aType $\rightarrow$ aType $\rightarrow$ aType $\rightarrow$ aType $\rightarrow$ aType $\rightarrow$ aType $\rightarrow$ aType $\rightarrow$ aType $\rightarrow$ aType $\rightarrow$ aType $\rightarrow$ aType $\rightarrow$ aType 

# 验证优化方案性能收益

优化后执行多次的平均耗时：22.44us，较优化前有较大提升。 


图 3-187 优化后 Profiling 数据


<table><tr><td>Op Name</td><td>Task Type</td><td>Task Duration</td><td>Task Duration</td><td>Task Vacere</td><td>tioa</td><td>tioa</td><td>macac</td><td>mia</td><td>tcal</td><td>time</td><td>ic</td><td>sca</td><td>mte</td><td>ate</td><td>mte2</td><td>ate</td><td>mtie</td><td>fixip</td><td>fixip</td><td>fixip</td><td>ichae</td><td>time</td><td>ivac</td><td>total</td><td>calv</td><td>vec</td><td>tin</td><td>av</td><td>vec</td><td>rata</td><td>scalar</td><td>ivac</td><td>scalar</td></tr><tr><td>matmul_Ashare/custom</td><td>MIX_AIC</td><td>24.46</td><td>2596</td><td>241</td><td>4457</td><td>2486</td><td>0.103</td><td>19.46</td><td>0.808</td><td>4851</td><td>0.201</td><td>7.862</td><td>0.326</td><td>9.533</td><td>0.396</td><td>0.029</td><td>21.81</td><td>80694</td><td>0.022</td><td>0.001</td><td>3.831</td><td>0.176</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>matmul_Ashare/custom</td><td>MIX_AIC</td><td>22.1</td><td>28</td><td>217</td><td>40167</td><td>2486</td><td>0.115</td><td>19.718</td><td>0.908</td><td>4856</td><td>0.224</td><td>8.074</td><td>0.372</td><td>9.759</td><td>0.45</td><td>0.026</td><td>19.5</td><td>72157</td><td>0.022</td><td>0.001</td><td>3.761</td><td>0.193</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>matmul_Ashare/custom</td><td>MIX_AIC</td><td>22.6</td><td>276</td><td>223</td><td>42113</td><td>2487</td><td>0.112</td><td>19.883</td><td>0.892</td><td>4856</td><td>0.218</td><td>8.002</td><td>0.359</td><td>9.719</td><td>0.436</td><td>0.028</td><td>20.08</td><td>74306</td><td>0.022</td><td>0.001</td><td>3.912</td><td>0.195</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>matmul_Ashare/custom</td><td>MIX_AIC</td><td>22.2</td><td>286</td><td>217</td><td>40052</td><td>2487</td><td>0.115</td><td>19.363</td><td>0.894</td><td>4847</td><td>0.224</td><td>7.766</td><td>0.359</td><td>9.394</td><td>0.434</td><td>0.027</td><td>19.6</td><td>72531</td><td>0.022</td><td>0.001</td><td>4.002</td><td>0.204</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>matmul_Ashare/custom</td><td>MIX_AIC</td><td>21.68</td><td>1058</td><td>213</td><td>39367</td><td>2487</td><td>0.117</td><td>19.229</td><td>0.904</td><td>4857</td><td>0.228</td><td>7.713</td><td>0.362</td><td>9.426</td><td>0.443</td><td>0.027</td><td>19.3</td><td>71392</td><td>0.022</td><td>0.001</td><td>3.937</td><td>0.204</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>matmul_Ashare/custom</td><td>MIX_AIC</td><td>21.5</td><td>1388</td><td>211</td><td>39076</td><td>2486</td><td>0.118</td><td>19.179</td><td>0.908</td><td>4867</td><td>0.223</td><td>7.907</td><td>0.365</td><td>9.459</td><td>0.459</td><td>0.026</td><td>19.21</td><td>71082</td><td>0.022</td><td>0.001</td><td>3.944</td><td>0.205</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>matmul_Ashare/custom</td><td>MIX_AIC</td><td>21.5</td><td>1388</td><td>211</td><td>39076</td><td>2486</td><td>0.115</td><td>19.179</td><td>0.908</td><td>4867</td><td>0.223</td><td>7.899</td><td>0.365</td><td>9.459</td><td>0.459</td><td>0.026</td><td>19.21</td><td>71082</td><td>0.022</td><td>0.001</td><td>3.944</td><td>0.205</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>matmul_Ashare/custom</td><td>MIX_AIC</td><td>22.28</td><td>1294</td><td>219</td><td>40443</td><td>2486</td><td>0.114</td><td>19.522</td><td>0.893</td><td>4843</td><td>0.222</td><td>8.095</td><td>0.37</td><td>9.774</td><td>0.447</td><td>0.027</td><td>19.69</td><td>72852</td><td>0.022</td><td>0.001</td><td>3.796</td><td>0.193</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>matmul_Ashare/custom</td><td>MIX_AIC</td><td>23.101</td><td>127</td><td>228</td><td>42096</td><td>2486</td><td>0.109</td><td>20.162</td><td>0.886</td><td>4852</td><td>0.213</td><td>8.286</td><td>0.364</td><td>9.943</td><td>0.437</td><td>0.027</td><td>20.38</td><td>75399</td><td>0.022</td><td>0.001</td><td>3.704</td><td>0.182</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr><tr><td>matmul_Ashare/custom</td><td>MIX_AIC</td><td>22.78</td><td>226</td><td>224</td><td>41463</td><td>2486</td><td>0.111</td><td>20.383</td><td>0.91</td><td>4835</td><td>0.216</td><td>8.186</td><td>0.365</td><td>9.862</td><td>0.44</td><td>0.026</td><td>19.97</td><td>73878</td><td>0.022</td><td>0.001</td><td>3.929</td><td>0.197</td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr></table>

# 总结

融合算子场景下，Matmul A矩阵和B矩阵同时开启IBShare，以Cube核视角分核，可 以有效减少Cube侧的Scalar开销，提升性能。 

# 3.10.4.13 AIV 核上的 ND2NZ 格式转换

# 案例介绍

本案例展示了在矩阵乘算子场景中，使用Matmul高阶API进行计算，对内轴（内轴即 矩阵的行方向）非256字节对齐的输入矩阵，在AIV核上进行ND2NZ格式转换对算子性 能提升的效果。为提升Cube单元的计算效率，ND格式的输入矩阵在执行Cube计算前 会先转换为NZ格式，ND格式和NZ格式的具体内容可参考数据格式。Matmul API内部 使用随路ND2NZ指令同时进行格式转换以及数据搬运。但在数据非256字节对齐时， 随路ND2NZ指令存在带宽利用率低的问题。因此输入矩阵的内轴非256字节对齐时， 在进行Matmul计算前，利用AIV核上Vector计算单元完成ND格式到NZ格式的转换， 可以避免随路非对齐数据搬运存在的效率低的问题，从而提升算子性能。 

AIV核上的ND2NZ格式转换的适用场景 

输入矩阵内轴非256字节对齐，且数据量较大影响随路格式转换的效率。 

本案例的算子规格如下： 


表 3-44 算子规格


<table><tr><td>输入</td><td>Shape</td><td>Data type</td><td>Format</td></tr><tr><td>a</td><td>1024, 1024</td><td>float16</td><td>ND</td></tr><tr><td>b</td><td>1024, 4095</td><td>float16</td><td>ND</td></tr></table>

当前案例使用的AI处理器共24个核，算子中使能高阶API Matmul的纯Cube模式。使用 MDL模板，Tiling参数如下： 

原始shape： $\mathsf { M } = 1 0 2 4$ , N= 4095, $K = 1 0 2 4$ 。 

● 单核shape：singleCoreM $_ { 1 } = 1 2 8$ ，singleCoreN=1408，singleCoreK=1024。 

基本块shape：baseM $\yen 123$ ，baseN $\mathtt { \Lambda } = 2 5 6$ ，baseK $\mathtt { - 6 4 }$ 。 

L1缓存相关Tiling参数：stepM=1，stepN=1，stepKa $^ { = 4 }$ ，stepKb=4。 

# 获取性能数据

使用msProf工具获取算子仿真流水图和上板Profiling数据，重点分析MTE2的流水。 

# 分析主要瓶颈点

优化前的Cube流水图如下，由于使用了随路ND2NZ指令，在MTE2数据搬运过程 中进行数据格式的转换，导致MTE2整体占比较高。 

![](images/ca629335059455a8e746d82bb26820fb6b407873e08dd40422f7107935b93f9b.jpg)


优化前的Profiling数据如下，可以看到只使用Cube单元执行计算，aic_time最大 耗时149.04us，其中aic_mte2_ratio占比很高。 

<table><tr><td>1</td><td>A</td><td>B</td><td>C</td><td>D</td><td>E</td><td>F</td><td>G</td><td>H</td><td>I</td><td>J</td><td>K</td><td>L</td><td>M</td><td>N</td><td>O</td><td>P</td></tr><tr><td>1</td><td>block_id</td><td>sub_block</td><td>ac_time(s)</td><td>ac_total_cycles</td><td>ac Cube_time(s)</td><td>ac Cube_ratio</td><td>acScalar_time(s)</td><td>acScalar_ratio</td><td>ac_mte_ttime(s)</td><td>ac_mte_rtime(s)</td><td>ac_mte_rtime(s)</td><td>ac_mte_rtime(s)</td><td>ac_mte_rtime</td><td>ac_mte_rtime</td><td>ac_mte_rtime</td><td>ac_mte_rtime</td></tr><tr><td>2</td><td>0 cube</td><td>146.70813</td><td>271526</td><td>25.303244</td><td>0.1724</td><td>15.216757</td><td>0.1036977</td><td>19.120001</td><td>0.130271</td><td>17.265441</td><td>0.935236</td><td>0.001081</td><td>0.000007</td><td>44.967026</td><td>0.006576</td><td></td></tr><tr><td>2</td><td>1 cube</td><td>146.70828</td><td>272027</td><td>25.303244</td><td>0.1724</td><td>15.216757</td><td>0.1036977</td><td>19.120001</td><td>0.130271</td><td>17.265441</td><td>0.935236</td><td>0.001081</td><td>0.000007</td><td>44.966109</td><td>0.006576</td><td></td></tr><tr><td>4</td><td>2 cube</td><td>146.636749</td><td>271278</td><td>25.200001</td><td>0.171853</td><td>16.196756</td><td>0.110455</td><td>19.065405</td><td>0.130018</td><td>134.101074</td><td>0.914512</td><td>0.001081</td><td>0.000007</td><td>45.814053</td><td>0.012432</td><td></td></tr><tr><td>5</td><td>3 cube</td><td>146.13298</td><td>270346</td><td>25.118919</td><td>0.171891</td><td>18.375298</td><td>0.118777</td><td>18.92054</td><td>0.129475</td><td>133.7146</td><td>0.91502</td><td>0.001081</td><td>0.000007</td><td>45.768108</td><td>0.009773</td><td></td></tr><tr><td>6</td><td>4 cube</td><td>146.454015</td><td>270953</td><td>25.228107</td><td>0.172251</td><td>17.389169</td><td>0.118779</td><td>18.989169</td><td>0.129663</td><td>135.298388</td><td>0.923784</td><td>0.001081</td><td>0.000007</td><td>46.238733</td><td>0.136104</td><td></td></tr><tr><td>7</td><td>5 cube</td><td>146.505254</td><td>272173</td><td>25.403787</td><td>0.172673</td><td>17.611235</td><td>0.119707</td><td>18.984534</td><td>0.129099</td><td>133.535808</td><td>0.944444</td><td>0.001081</td><td>0.000007</td><td>45.754958</td><td>0.136104</td><td></td></tr><tr><td>8</td><td>6 cube</td><td>146.695494</td><td>271320</td><td>25.297838</td><td>0.172494</td><td>17.235676</td><td>0.117522</td><td>18.981081</td><td>0.129423</td><td>134.307074</td><td>0.915745</td><td>0.001007</td><td>0.000007</td><td>44.086847</td><td>0.002119</td><td></td></tr><tr><td>9</td><td>7 cube</td><td>146.376055</td><td>272617</td><td>25.280001</td><td>0.171552</td><td>17.397839</td><td>0.118063</td><td>18.912973</td><td>0.128345</td><td>135.111893</td><td>0.91688</td><td>0.001007</td><td>0.000007</td><td>45.315494</td><td>0.007508</td><td></td></tr><tr><td>10</td><td>8 cube</td><td>146.891995</td><td>275482</td><td>25.312433</td><td>0.176701</td><td>18.130812</td><td>0.121757</td><td>19.118378</td><td>0.12839</td><td>136.95459</td><td>0.919719</td><td>0.001007</td><td>0.000007</td><td>44.56216</td><td>0.299257</td><td></td></tr><tr><td>11</td><td>9 cube</td><td>146.892443</td><td>275995</td><td>25.32998</td><td>0.176811</td><td>18.17984</td><td>0.129554</td><td>19.120001</td><td>0.128394</td><td>135.111893</td><td>0.919719</td><td>0.001007</td><td>0.000007</td><td>45.692331</td><td>0.388777</td><td></td></tr><tr><td>12</td><td>10 cube</td><td>146.67244</td><td>275044</td><td>26.18973</td><td>0.176157</td><td>16.801081</td><td>0.113007</td><td>19.012974</td><td>0.127885</td><td>136.249725</td><td>0.916442</td><td>0.001007</td><td>0.000007</td><td>45.120541</td><td>0.30349</td><td></td></tr><tr><td>13</td><td>11 cube</td><td>146.55513</td><td>272977</td><td>25.828108</td><td>0.17504</td><td>16.572972</td><td>0.110962</td><td>19.07946</td><td>0.129394</td><td>134.450006</td><td>0.911119</td><td>0.001007</td><td>0.000007</td><td>44.468109</td><td>0.031966</td><td></td></tr><tr><td>14</td><td>12 cube</td><td>146.55527</td><td>272777</td><td>25.828108</td><td>0.176236</td><td>16.636926</td><td>0.11195</td><td>19.10188</td><td>0.129394</td><td>134.450006</td><td>0.911119</td><td>0.001007</td><td>0.000007</td><td>44.468109</td><td>0.031966</td><td></td></tr><tr><td>15</td><td>13 cube</td><td>146.95784</td><td>271872</td><td>25.837837</td><td>0.175818</td><td>16.602702</td><td>0.109301</td><td>19.121627</td><td>0.130116</td><td>136.176224</td><td>0.928635</td><td>0.001007</td><td>0.000007</td><td>44.967298</td><td>0.30592</td><td></td></tr><tr><td>16</td><td>14 cube</td><td>146.041077</td><td>275726</td><td>26.243784</td><td>0.176084</td><td>17.125946</td><td>0.114908</td><td>19.285406</td><td>0.129397</td><td>137.628113</td><td>0.923424</td><td>0.001007</td><td>0.000007</td><td>45.275768</td><td>0.304128</td><td></td></tr><tr><td>17</td><td>15 cube</td><td>146.550278</td><td>272968</td><td>26.005405</td><td>0.176248</td><td>16.989729</td><td>0.115145</td><td>19.306486</td><td>0.130847</td><td>135.220535</td><td>0.916437</td><td>0.001007</td><td>0.000007</td><td>45.396755</td><td>0.30767</td><td></td></tr><tr><td>18</td><td>16 cube</td><td>146.32546</td><td>248246</td><td>26.243784</td><td>0.176237</td><td>16.989729</td><td>0.115349</td><td>19.363463</td><td>0.12966</td><td>136.176224</td><td>0.916437</td><td>0.001007</td><td>0.000007</td><td>41.74222</td><td>0.3082</td><td></td></tr><tr><td>19</td><td>17 cube</td><td>146.325216</td><td>248866</td><td>26.011892</td><td>0.176383</td><td>14.182703</td><td>0.10543</td><td>18.607566</td><td>0.12943</td><td>131.02943</td><td>0.900167</td><td>0.001007</td><td>0.000008</td><td>40.794594</td><td>0.303256</td><td></td></tr><tr><td>20</td><td>18 cube</td><td>146.323242</td><td>248498</td><td>26.918664</td><td>0.1637</td><td>13.918379</td><td>0.103619</td><td>18.669188</td><td>0.125587</td><td>120.627571</td><td>0.898039</td><td>0.001007</td><td>0.000008</td><td>40.942162</td><td>0.304803</td><td></td></tr><tr><td>21</td><td>19 cube</td><td>146.356168</td><td>250419</td><td>22.224865</td><td>0.164189</td><td>14.327027</td><td>0.105843</td><td>16.722244</td><td>0.123545</td><td>121.604688</td><td>0.897632</td><td>0.001007</td><td>0.000008</td><td>40.697839</td><td>0.302136</td><td></td></tr><tr><td>22</td><td>20 cube</td><td>146.356166</td><td>250419</td><td>22.224865</td><td>0.164189</td><td>14.424968</td><td>0.105845</td><td>16.722244</td><td>0.123545</td><td>121.604688</td><td>0.897632</td><td>0.001007</td><td>0.000008</td><td>41.59288</td><td>0.304803</td><td></td></tr><tr><td>23</td><td>21 cube</td><td>146.3541895</td><td>247996</td><td>22.169189</td><td>0.165378</td><td>14.104721</td><td>0.106421</td><td>16.827026</td><td>0.125556</td><td>11.897716</td><td>0.001007</td><td>0.000008</td><td>0.000008</td><td>42.005405</td><td>0.313352</td><td></td></tr><tr><td>24</td><td>22 cube</td><td>146.734188</td><td>251134</td><td>22.26504</td><td>0.163984</td><td>14.553514</td><td>0.10721</td><td>16.764864</td><td>0.1235</td><td>121.797295</td><td>0.89723</td><td>0.001007</td><td>0.000008</td><td>42.97567</td><td>0.316584</td><td></td></tr><tr><td>25</td><td>23 cube</td><td>146.127583</td><td>249986</td><td>22.227028</td><td>0.164489</td><td>14.616756</td><td>0.10817</td><td>16.635136</td><td>0.123317</td><td>121.336754</td><td>0.897942</td><td>0.001007</td><td>0.000008</td><td>41.444325</td><td>0.306883</td><td></td></tr></table>

# 设计优化方案

对于ND格式的输入矩阵，不再使用随路ND2NZ指令进行格式转换，而是利用Vector计 算单元的能力完成数据格式转换。首先使用DataCopyPad接口，将非对齐的矩阵数据 搬入Unified Buffer，使用Duplicate接口填充需要补为对齐位置的数据，再逐行调用 Copy接口实现数据从ND到NZ格式的重排，将重排后的NZ数据写入workspace内存， 最后直接读取workspace上的NZ数据，进行Matmul计算。 

AIV核上的ND2NZ格式转换的完整样例请参考Matmul输入矩阵ND到NZ格式转换的算 子样例。实现AIV核上的ND2NZ格式转换的主要步骤如下： 

步骤1 创建Matmul对象时，定义内轴非256字节对齐的B矩阵的Format为NZ格式。 

using A_TYPE $\equiv$ AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, ATYPE, true>; //使用CubeFormat::NZ定义矩阵B的类型信息   
using B_TYPE $\equiv$ AscendC::MatmulType<AscendC::TPosition::GM, AscendC::TPosition::GM, CubeFormat::NZ, BType, true>;   
using C_TYPE $\equiv$ AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, CType>;   
using BIAS_TYPE $\equiv$ AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, BiasType>; AscendC::Matmul<A_TYPE,B_TYPE,C_TYPE,BIAS_TYPE, CFG_MDL>matmulObj; 

步骤2 利用Vector计算单元实现ND2NZ格式转换。如下代码中MatrixBtoNZ为将B矩阵的ND 格式转换为NZ格式的函数，该函数的具体实现请参考完整样例代码。 

```cpp
// Vector ND2NZ  
if ASCEND_IS_AIV{  
    pipe->InitBuffer(ubBuf, TOTAL UB_SIZE);  
    MatrixBtoNZ<typename B_TYPE::T>(tempGM, bGMNZ, tiling, isTransB, ubBuf, tiling.baseK, tiling.baseN); // ND2NZ格式转换函数  
    SyncAll();  
    // CV SYNC  
    NotifyEvent<PIPE_MTE3>(4);  
    return;  
}  
if ASCEND_IS_AIC{  
    WaitEvent(4); // 等待Vector完成ND2NZ格式转换  
} 
```

步骤3 设置左矩阵A、右矩阵B、Bias，完成矩阵乘操作。 

```javascript
matmulObj.SetTail(tailM, tailN, shapes.k);  
matmulObj.setTensorA(aGlobal, false);  
matmulObj.setTensorB(bGlobal, false);  
if (shapes.isBias) {  
    matmulObj.setBias(biasGlobal);  
}  
matmulObj.IterateAll(cGlobal); 
```

----结束 

# 验证优化方案性能收益

优化后的Vector流水图如下所示，利用Vector计算单元的能力，完成B矩阵的数据 格式转换。 

![](images/1f72bb0debe6d18cc739e3f551fa90c9f345e648fd2d63ccb3a359de2bce585a.jpg)


优化后的Cube流水图如下所示，不使用随路ND2NZ指令对B矩阵进行格式转换 后，MTE2的占比明显下降。 

![](images/9e6f27f9cecd02207c1cddafcf00b4f3af6f4b93c9b1acae1d10a38fe8a2cbdc.jpg)


优化后的Profiling数据如下，可以看到同时使用Cube单元和Vector单元，aic_time 最大耗时90.95us，其中aic_mte2_ratio占比明显降低。 

![](images/abc494abce373fec8430e25d52d3638cb9e7443d1f1f3633816fbd87403c2984.jpg)



表 3-45 端到端性能对比


<table><tr><td>优化方法</td><td>总耗时(us)</td><td>AIC_MTE2平均耗时(us)</td><td>AIV_MTE2平均耗时(us)</td></tr><tr><td>随路ND2NZ</td><td>149.82</td><td>130.77</td><td>0</td></tr><tr><td>Vector侧ND2NZ</td><td>93.76</td><td>22.85</td><td>10.31</td></tr></table>

从上表中执行时间的对比，可以看出：不使用随路ND2NZ指令后，总耗时大幅下降， 端到端性能提升明显。 

# 总结

对于矩阵乘计算中矩阵内轴非256字节对齐的场景，随路ND2NZ指令的带宽利用率 低，影响算子性能，通过在AIV核上进行ND2NZ的数据重排，提升算子整体性能。值 得注意的是，带宽利用率与数据量有关，如果矩阵数据总量太小，即使是在AIV核上进 行的ND2NZ转换也无法明显提升有效带宽，反而会因为引入了多核同步，导致算子端 到端的性能劣化。 

# 3.10.4.14 Matmul 高阶 API 使能 MTE2 Preload

# 案例介绍

本案例呈现了在矩阵乘算子场景中，使用Matmul高阶API进行矩阵乘法计算，使能 MTE2 Preload对算子性能的提升效果。通过MatmulConfig中的doMTE2Preload参数 开启矩阵M或N方向的预加载功能，预加载即在MTE2间隙提前加载A矩阵/B矩阵数 据，开启预加载功能后，可以减少MTE2间隙，提升算子性能。doMTE2Preload参数的 详细介绍请参考MatmulConfig。 

使能MTE2 Preload的适用场景 

MTE2流水间隙较大，且M或N数值较大时。 

使能MTE2 Preload的约束条件 

仅在使用MDL模板和SpecialMDL模板时，MTE2 Preload有效。 

开启M或N方向预加载功能时，需保证K方向数据全载，且M或N方向开启 DoubleBuffer。 

K方向数据全载的条件是singleK $< =$ baseK * stepK。 

M方向开启DoubleBuffer的条件是depthA1 $=$ stepM * stepK $^ { \star } 2$ 。 

– N方向开启DoubleBuffer的条件是depthB1 $=$ stepN * stepK $^ { \star } 2$ 

本案例的算子规格如下： 


表3-46 算子规格


<table><tr><td>输入</td><td>Shape</td><td>Data type</td><td>Format</td></tr><tr><td>a</td><td>128, 512</td><td>float16</td><td>ND</td></tr><tr><td>b</td><td>512, 24576</td><td>float16</td><td>ND</td></tr></table>

当前案例使用的AI处理器共24个核，算子中使能高阶API Matmul的纯Cube模式。使用 MDL模板，Tiling参数如下： 

原始shape： $\mathtt { M } = 1 2 8$ , N= 24576, $\mathtt { K } = 5 1 2$ 。 

单核shape：singleCoreM $_ { 1 } = 1 2 8$ ，singleCoreN $\scriptstyle 1 = 1 0 2 4$ ，singleCoreK=512。 

基本块shape：baseM $\yen 128$ ，baseN $\yen 128$ ，baseK $\mathtt { \mathtt { = 6 4 } }$ 。 

L1缓存相关Tiling参数：stepM=1，stepN=1，stepKa $^ { = 8 }$ ，stepKb=8， depthA1 $^ { = 8 }$ ，depthB1 $= 1 6$ 。 

# 获取性能数据

使用msProf工具获取算子仿真流水图和上板Profiling数据，重点分析Cube，Fixpipe的 流水情况。 

# 分析主要瓶颈点

优化前的流水图如下，M和K方向全载，因此A矩阵只搬运一次。由于N较大，B矩 阵会搬运多次，可以看到单次MTE2间存在间隙。 

![](images/3323b47e8aa0d12f05484b2a9eec69b5af63f10227067d9f835721642acca69e.jpg)


优化前的Profiling数据如下，aic_time平均耗时30.88us。 

![](images/830d3dd411dddb17d1751fdf0fb5d8bf276b66769ee1afa62cea9aa5ea59f374.jpg)


# 设计优化方案

使能MTE2 Preload功能：在创建Matmul对象时，开启doMTE2Preload开关。使能 MTE2 Preload的完整样例请参考M方向预加载Matmul算子样例。具体步骤如下： 

步骤1 配置MDL模板参数，将其中的doMTE2Preload参数设置为2，使能N方向Preload功 能。 

```txt
// preloadMode = 2  
static constexpr MatmulConfig MM_CFG = GetMDLConfig(false, false, preloadMode); 
```

步骤2 基于自定义MatmulConfig模板参数，创建Matmul对象。 

```txt
AscendC::Matmul<AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, aType>, AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, bType>, 
```

AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, cType>, AscendC::MatmulType<AscendC::TPosition::GM, CubeFormat::ND, biasType>, MM_CFG> matmulObj; 

----结束 

# 验证优化方案性能收益

优化后的流水图如下，Tiling参数不变，可以看到，下一次计算使用的B矩阵数据 提前加载，MTE2间的间隙缩短。 

![](images/4c75987c1e51027682ce641759ed99d4e88c2b8de753495b684e49077099d9ad.jpg)


优化后的Profiling数据如下，aic_time平均耗时28.50us，较优化前的30.88us有所 下降。 

![](images/f754d7bd2de437bc45a052bf48a5a7adf30ebd2c4fba2d10fb46e9fb06dcc48c.jpg)


# 总结

当MTE2流水间隙较大，且M或N数值较大时，可以考虑使能MTE2 Preload功能，提前 加载A矩阵或B矩阵数据。 

# 4 兼容性迁移指南