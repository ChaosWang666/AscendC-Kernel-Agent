<!-- Source: 算子开发指南2.md lines 652-979 | Section: 3.10.1 FlashAttention 算子性能调优案例 -->

# 3.10.1 FlashAttention 算子性能调优案例

# 案例介绍

本案例中的算子FlashAttentionScoreGrad，用于训练场景下计算注意力的反向输出， 即FlashAttentionScore算子的反向计算。 

已知注意力的正向计算公式为： 

$$
Y = D r o p o u t (S o f t m a x (M a s k (\frac {Q K ^ {\tau} + p s e}{\sqrt {d}}), a t t e n _ {-} m a s k), k e e p _ {-} p r o b) V
$$

为方便表达，以变量S和P表示计算公式： 

$$
S = \operatorname {M a s k} (\frac {Q K ^ {\tau} + p s e}{\sqrt {d}}, \text {a t t e n} _ {-} \text {m a s k})
$$

$$
P = D r o p o u t (S o f t m a x (S), k e e p _ {p r o b})
$$

$$
Y = P V
$$

则注意力的反向计算公式为： 

$$
d V = P ^ {T} d Y
$$

$$
d Q = \frac {((d S) ^ {*} K)}{\sqrt {d}}
$$

$$
d K = \frac {\left(\left(d S\right) ^ {T *} Q\right)}{\sqrt {d}}
$$

$$
d (p s e) = d S ^ {*} \sqrt {d}
$$

计算流程图如下： 


图 3-144 算子计算流程


![](images/8990bb802d4790dcaa358b17a3c238fd1a007c026bc9a7c1d6460bbcdcbda65e.jpg)


按照FlashAttention反向计算流程的实现，简介整体计算流程如下。对本算子的算法感 兴趣的用户可简单了解，无需重点关注。 

1. 重计算p，本步骤重计算了FlashAttention流程中的softmax结果p，计算结果保存 在ub中。 

$$
p = \text {S i m p l e d S o f t m a x} (\text {M a s k} (\text {M a t m u l} (\text {q u e r y}, \text {k e y} ^ {\tau}) + p s e) ^ {*} \text {s c a l e})
$$

2. 计算dp，该计算包含matmul计算和dropout计算，matmul计算中，左矩阵为 dy，右矩阵为转置后的value。 

$$
d p = D r o p o u t (M a t m u l (d y, v a l u e ^ {T}))
$$

3. 计算ds，本计算中，FlashSoftmaxGrad计算的入参为dy、正向输出 attention_in，该结果与dp做减操作，最终的结果与p相乘得到结果ds。 

$$
d s = p ^ {*} \operatorname {S u b} (d p, F l a s h S o f t m a x G r a d (d y, a t t e n t i o _ {i n}))
$$

4. 计算dq，本计算将ds结果与key做matmul计算，并将结果与scale相乘得到结果 dq。 

$$
d q = M a t m u l (d s, k e y) ^ {*} s c a l e
$$

5. 计算dk，本计算将转置后的ds结果与query做matmul计算，并将结果与scale相乘 得到结果dk。 

$$
d k = M a t m u l (d s ^ {T}, q u e r y) ^ {*} s c a l e
$$

6. 计算dv，本计算将p的结果做drop计算，转置后与dy做matmul计算。 

$$
d v = M a t m u l (D r o p O u t (p) ^ {T}, d y)
$$

本案例的验证平台为Atlas A2 训练系列产品/Atlas A2 推理系列产品，以两个场景为 例，第一个场景的输入维度信息为：B=1，N1=12，N2=12，S1=6144，S2=6144， D=128，causal场景，即atten_mask的形状为下三角，如图3-145。第二个场景的输入 维度信息为：B=24，N1=5，N2=5，S1=9216，S2=9216，D=64，不带atten_mask和 drop_mask输入。主要涉及的优化手段包括tiling基本块大小调整，核间负载均衡，CV 流水并行，MTE2流水优化以及FixPipe流水优化等优化手段。 


图 3-145 causal 场景 atten_mask 形状


<table><tr><td>0</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td>0</td><td>0</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td>0</td><td>0</td><td>0</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td>0</td><td>0</td><td>0</td><td>0</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>1</td><td>1</td><td>1</td></tr><tr><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>1</td><td>1</td></tr><tr><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>1</td></tr><tr><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr></table>

# 获取性能数据

流水优化分析工具包括CAModel和Profiling工具，分别从两个方面分析：第一个是从 Profiling工具生成的Profiling数据中分析各项流水的占比，第二个是从CAModel工具生 成的打点图分析各流水并行情况。 

# 分析主要瓶颈点

通过观察分析流水图和Profiling数据，结合优化经验来判断性能瓶颈点。在优化过程中 不同阶段可能会出现不同的瓶颈点，需要不断优化以达到最佳性能。 

根据优化经验，循环间会存在一些不必要的性能开销，循环越多性能可能越差； 满足UB最大空间限制的情况下，UB切分的基本块越大，循环越少。算子中通过 InitBuffer接口分配UB buffer大小。 

pipe->InitBuffer(ubBuffer, 120 * 1024); 

pipe->InitBuffer(tmpBuffer, 30 * 1024); 

pipe->InitBuffer(vecClc3, 8 * 1024); 

如上代码所示，InitBuffer接口的第二个参数表示buffer占用的大小，所有buffer 大小的和即为占用的总空间。这里120 * 1024 + 30 * 1024 + 8 * 1024 = 158KB < UB Size，没有充分利用UB空间。 

观察如下流水图，绿色为Vector侧的流水，橙色为Cube侧的流水，可以看出两侧 的流水都存在大段的空隙，CV之间流水很大程度上未并行，需要考虑CV流水优 化。 


图 3-146 优化前算子流水


![](images/74f7ed569802e690423803009ab2136eddb83da28f59fdb375dca7ce66a38c78.jpg)


对于上述场景一，causal场景下可能存在核间分布不均匀的情况，如下图经过 atten_mask掩码后，红色部分是算子需要计算的部分，绿色无需计算；如果不按 照基本块的个数来分核，按照第一根轴的大小8（行）来分核，假设平均分到9个 核上，每个核做ceil(8 / 9) = 1行，则第1个核只需做1个基本块，但是第8个核需 要做8个基本块的计算，出现明显的负载不均衡。因此需要考虑将红色块均匀分到 多个核上计算。 

图 3-147 causal 场景 atten_mask 形状 

![](images/db51792d8620c81c9f48df3ae01550eed8c0b4d0ce232f86e67ac171a66ece4e.jpg)


场景一的Profiling数据如下，aic_fixpipe_ratio占比极高，可能存在FixPipe bound。 


图 3-148 场景一 Profiling 数据



aic fxpipe aic_ fxpipe_ratio 0206737.67.44E+0926507.62 012822049101 0.9912238471 0.115357073.96 02761168511.6 pe_rati1 0.0025206734.51.49E+1055978.65 0.270824983.12 0.120838686.49 0.187126993.82 0.1306 0.001


场景二的Profiling数据如下，mte2_ratio占比高，可能存在MTE2 bound。 


图 3-149 场景二 Profiling 数据


![](images/7f7c083ae1bd8359ac0394b4960a7dcabed072b6dc799cf45b348c4671341c9b.jpg)


# 设计优化方案

# 优化点一：调整tiling基本块

在满足UB空间大小限制的前提下，tiling基本块的切分应尽可能大。如下图为优化 前按照(64, 128)切分计算，总共需要循环计算32次。 


图 3-150 优化前计算基本块及次数


![](images/2a71084a29adb070223c2878fc1778bcd1cd38ab8c41dc4060ebc1f9badc0f50.jpg)


考虑到UB空间没有用满，基本块调整到(128, 128)，如下图优化后只需循环计算 16次，切分后算子性能提升一倍。 


图 3-151 优化后计算基本块及次数


![](images/2fc23906b7106698d0658fb94271df5e0af855753608a2c87d82b5916e58ddd4.jpg)


# 优化点二：CV流水并行

由于FAG算子中Cube计算比Vector计算快且存在依赖性，同时为了减少CV之间的 通信次数，通过缓存机制使matmul提前计算多块，这里的缓存机制指的是将mm 一次性计算多个基本块缓存到GM上。如下代码中，SetTail设置的singleCoreM和 singleCoreN大小分别为BaseM，BaseN的倍数，即matmul一次发起多个基本块 的计算，实现matmul结果的缓存，Vector侧分多次取matmul的结果。 

```txt
mm3.setTail(s2CvExtend, -1, preS1Extend);  
mm3.setTensorA(mulWorkSpaceGm[pingponIdx * coreNum * cubeBaseMN + cBlockIdx * cubeBaseMN], true);  
mm3.setTensorB(queryGm[mm2aTensorOffsetCv]);  
mm3.template IterateAll(false> (dkWorkSpaceGm[bTensorOffsetCv], true); 
```


图 3-152 完成 mm1/mm2/mm3 缓存的流水


![](images/402b0a641d3187f01e076cf1bf00f119e60ba7583c7559a622cbc38538247955.jpg)


如上图是实现mm1、mm2和mm3缓存的流水图，并行度提高，CV的间隔减小， 提升了算子性能。 


图 3-153 Vector 等 Cube 流水的间隔插入 Vector 计算


![](images/53f3a2d297c4934874c6d1dad13b79f4f8a15b10c9e801d0d1e64335bc9c3b3b.jpg)


基于缓存mm1/mm2/mm3的优化后，在本轮Vector计算等Cube流水的间隔，插 入下一轮循环的Vector计算，如上图所示，这样使Vector流水与Cube流水之间的 并行度更高，反映到流水图中为Vector计算更密集。原计算过程伪代码与在CV间 隔中插入下一轮Vector计算的伪代码，分别如以下两段所示。 

```txt
//原计算过程伪代码  
//mm1计算;  
dropout();  
Sub();  
//mm2计算;  
Softmax();  
AttenMask();  
...  
//在Vector等Cube流水的间隔中，插入下一轮循环的Vector计算伪代码  
//mm1计算;  
dropout();  
Sub();  
dropout(); //下一轮循环的Vector计算  
Sub(); //下一轮循环的Vector计算  
//mm2计算;  
Softmax();  
AttenMask();  
... 
```

# 优化点三：每个核负载均衡


图 3-154 causal 场景优化前每个核计算量


![](images/fc059648efe14dcb5daf6add74acb2a06586e49be7cb4a96851fcf84fb95a6fa.jpg)



图 3-155 causal 场景优化后每个核计算量


![](images/b6e954438a6b360a36a6597d7297d7f05889ecbf2ecefcbe22b9caebd67266b2.jpg)


尽量实现每个核的计算量均匀，负载均衡。优化前的分核及每个核的计算量如图 11 causal场景优化前每个核计算量所示，按照第一根轴的大小8（行）来分核， 平均分到9个核上，每个核计算ceil(8/9)=1行，第1个核只计算1个基本块，但是第 8个核计算8个基本块。优化后如图12 causal场景优化后每个核计算量所示，红色 块总共36个基本块，均分到每个核上，每个核的计算量为4个基本块，性能提升一 倍。 

优化点四： FIXPIPE优化 

从采集的Profiling数据来看，Cube FixPipe占比高达81%，出现了很严重的bound （达到上限）。CAModel工具打印发现存在很多异常的128B搬运，排查代码，发 现workspace地址未512B对齐。 


图 3-156 场景一优化前 Profiling 数据


![](images/af82d0c81fbbc611744a67afad2ac96c967320e5937156903a33cbed70e44f2d.jpg)


代码实现中使用SetGlobalBuffer接口设置workspace的起始地址，如果起始地址 不是按照512B对齐，搬运效率会很低，可以强制GM地址512Byte对齐来避免这 个情况。下面代码中ADDR_ALIGN_SIZE即为512。 

```txt
// init workspace address
syncGlobal.SetGlobalBuffer((__gm__int32_t*)workspace);
uint64_t workspaceOffsets = SYNCGLOBAL_WORKSPACE_SIZE;
dqWorkSpaceGm.SetGlobalBuffer((__gm__float*)workspace + workspaceOffsets / sizeof(T2));
workspaceOffsets = (workspaceOffsets + qPostBlockTotal * sizeof(float) + ADDRALIGN_SIZE) /
ADDRALIGN_SIZE * ADDR ALIGN_SIZE; dkWorkSpaceGm.SetGlobalBuffer((__gm__float*)workspace
+ workspaceOffsets / sizeof(T2));
workspaceOffsets = (workspaceOffsets + kvPostBlockTotal * sizeof(float) + ADDR ALIGN SIZE) /
ADDR ALIGN SIZE * ADDR ALIGN SIZE; dvWorkSpaceGm.SetGlobalBuffer((__gm__float*)workspace
+ workspaceOffsets / sizeof(T2));
workspaceOffsets = (workspaceOffsets + kvPostBlockTotal * sizeof(float) + ADDR ALIGN SIZE) /
ADDR ALIGN SIZE * ADDR ALIGN SIZE;
// matmul1 and matmul2 workspace size
matmulWorkspaceSize = cubeBaseMN * sizeof(float);
mm1WorkspaceGm.SetGlobalBuffer((__gm__T2*)(workspace + workspaceOffsets + cBlockIdx *
matmulWorkspaceSize)); mm2WorkspaceGm.SetGlobalBuffer((__gm__T2*)(workspace +
workspaceOffsets + coreNum * matmulWorkspaceSize + cBlockIdx * matmulWorkspaceSize)); // drop 
```

```txt
workspace offset
workspaceOffsets = (workspaceOffsets + coreNum * cubeBaseMN * sizeof(float) * INPUT_NUMS + ADDRALIGN_SIZE) / ADDRALIGN_SIZE * ADDRALIGN_SIZE;
dropWorkSpaceGm.SetGlobalBuffer(_gm_T1*) workspace + workspaceOffsets / sizeof(T1)); // mul workspace offset
workspaceOffsets = (workspaceOffsets + coreNum * cubeBaseMN * sizeof(half) * 2 + ADDRALIGN_SIZE) / ADDRALIGN_SIZE * ADDRALIGN_SIZE;
mulWorkSpaceGm.SetGlobalBuffer(_gm_T1*) workspace + workspaceOffsets / sizeof(T1)); 
```

修改代码，workspace地址经过512B对齐后，FixPipe时间减半。 


图 3-157 场景一优化后 Profiling 数据


![](images/b243b55736c8dddc33166030aaacec8f58ec0f2e88be8fe2e3bb72ccff89b404.jpg)


优化点五：MTE2优化 

结合如下的Profiling数据和流水图，可以看出MTE2 bound，且部分MTE2搬运时 间异常。 


图 3-158 场景二 Profiling 数据


![](images/990d740dd4c91ef4b2503d729c7bb00886753d537109ee78d93e2eb31c701444.jpg)



图 3-159 场景二流水图


![](images/0db97b46a3e60d91cc0e900e5456193babe2375e654a65ddb2f98574a3879272.jpg)


将输入数据排布格式从BSH更改为BNSD后，数据搬运连续，不需要跳地址读取数 据，搬运效率提升一倍，部分异常搬运时长降低了一半。 

# 验证优化方案性能收益

调整tiling基本块：理论评估Vector切块越大，计算和搬运循环次数越少，同时能 够充分利用搬运带宽和Vector算力。基本块大小从(64, 128)增大到(128, 128) 后，性能提升一倍，实测与理论分析一致。 

CV流水并行：CV流水掩盖的时间即为提升的性能，符合预期的收益。 

核间负载均衡：优化前负载最多的核计算量减少的倍数，即为预期提升的性能； 案例中优化前负载最多的核的计算量大小为8块，优化后为4块，实际性能提升一 倍，符合预期的收益。 

FixPipe优化：从Profiling数据看出FixPipe占比0.8，优化后占比0.55，实测算子性 能提升45%，与理论分析一致。 

MTE2优化：从Profiling数据看出MTE2占比0.52，优化后占比减少一半，实测算 子性能提升30%，与理论分析一致。 

# 总结

融合算子场景，可参考此优化。