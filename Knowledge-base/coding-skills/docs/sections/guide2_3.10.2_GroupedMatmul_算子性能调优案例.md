<!-- Source: 算子开发指南2.md lines 980-1131 | Section: 3.10.2 GroupedMatmul 算子性能调优案例 -->

# 3.10.2 GroupedMatmul 算子性能调优案例

# 案例介绍

本案例对分组Matmul即GroupedMatmul算子的per-token量化场景进行性能分析和优 化，GroupedMatmul算子计算过程（通过python代码表达）为： 

offset $= 0$ for i in range(g): mmOut $\equiv$ x[offset:offset $^+$ groupList[i] \* weight[i] $^+$ bias[i] y[offset:offset $^+$ groupList[i]] $=$ Gelu(mmOut \* scale[i] \*pertokenScale[offset:offset + groupList[i]]) offset $+ =$ groupList[i] 

验证平台为Atlas A2 训练系列产品/Atlas A2 推理系列产品。 

优化分析以如下算子规格为例： 


表3-28 算子规格


<table><tr><td>input</td><td>shape</td><td>data type</td><td>format</td></tr><tr><td>x</td><td>(1024,1024)</td><td>int8</td><td>ND</td></tr><tr><td>weight</td><td>(8,1024,8192)</td><td>int8</td><td>NZ</td></tr><tr><td>bias</td><td>(8,8192)</td><td>int32</td><td>ND</td></tr><tr><td>groupList</td><td>8</td><td>int64</td><td>ND</td></tr><tr><td>scale</td><td>(8,8192)</td><td>float</td><td>ND</td></tr><tr><td>pertokenScale</td><td>1024</td><td>float</td><td>ND</td></tr><tr><td>y</td><td>(1024,8192)</td><td>float16</td><td>ND</td></tr></table>

主要介绍以下优化方法： 

对于Vector计算占比较高（Vector Bound）的场景，将AI Core中的AIC核和AIV核 启动比例设置为1:2； 

优化CV并行流水，减少Cube和Vector计算间的空闲等待时间； 

优化Vector计算流水，提高Vector并行计算速度。 

# 获取性能数据

固定8核测试，即当前性能和后续优化tiling中numBlocks固定设置为8。 

通过msProf算子调优工具获取算子性能数据： 

获取真实环境执行的性能数据（指令的cycle占比数据 ArithmeticUtilization.csv），包含各个流水的占比情况； 

获取仿真性能数据（指令流水图），包含各个流水的占用区间，可观察流水间依 赖情况，从而优化并行效率。 

# 分析主要瓶颈点

固定8核进行测试的情况下，通过msprof op命令获取指令的cycle占比数据如下： 


图 3-160 指令的 cycle 占比数据 ArithmeticUtilization.csv（性能总耗时为 218.1us）


<table><tr><td>Op Name</td><td>OP Type</td><td>Task Dura</td><td>aicore(TIM</td><td>aic_mte2</td><td>aic_mte2</td><td>aiv_time(u</td><td>aiv_vec_tir</td><td>aiv_vec_ra</td><td>aiv_mte2</td><td>aiv_mte2_ratio</td></tr><tr><td>quant_grc</td><td>quant_grc</td><td>218.064</td><td>215.38</td><td>95.262</td><td>0.442</td><td>212.04</td><td>91.333</td><td>0.431</td><td>27.016</td><td>0.127</td></tr></table>

通过msprof op simulator获取到的指令流水图如下图所示： 


图 3-161 指令流水图


![](images/0a45e266bf3d9df5a3db27728b5b96d44eab646d7a4471174d2624cb42e16405.jpg)


结合上述两种数据（真实数据和仿真数据）进行性能分析： 

● Vector计算bound，当前为减少核启动开销设置为1:1； 

实际优化过程中，对上述问题进行优化、Vector计算占比下降后，Cube和Vector 计算各自都有间隙，相互之间都有等待耗时； 

![](images/fcacb5c31de3b197a5c71a0156c02c163d3939f4a5b6db2f701544f5c6b11e8d.jpg)


● Vector计算没有开启double buffer，计算和数据搬运部分没有并行。 

![](images/e3c38b1f47a2be8636092742d2f3d5765b1df2540f91b81b82967a69aa60cd6d.jpg)


# 设计优化方案

将AI Core中的AIC核和AIV核启动比例设置为1:2。每次AIC输出的数据，由两个 AIV并行计算对应的反量化和激活函数；在Vector侧代码的循环里，AIV0和AIV1交 替进行计算（前提条件，循环次数不为1）。代码示例如下： 

```txt
uint32_t vecCount = 0;  
uint32_t taskRation = GetTaskRatio();  
for (uint32_t offsetN = 0; offsetN < curCubeSingleN; offsetN += mnConfig.baseN) {  
    if (unlikely(offsetN + mnConfig.baseN >= curCubeSingleN)) {  
        curVecBaseN = curCubeSingleN - offsetN;  
    }  
    uint32_t alignBaseN = Ceil(curVecBaseN, uint32_t(8)) * 8;  
    DataCopyScale(curVecBaseN, alignBaseN, scaleOffset + offsetN);  
    uint32_t curVecBaseM = vecBaseM;  
    uint64_t mmOutOffset = mnConfig.workSpaceOffset + offsetN * mnConfig.baseM;  
    CrossCoreWaitFlag(SYNC_AIC_TO_AIV);  
    for (uint32_t offsetM = 0; offsetM < curCubeSingleM; offsetM += vecBaseM) {  
        vecCount++;  
        if (vecCount % taskRation != subBlockIdx) {  
            continue; // AIV0和AIV1交替进行计算  
        }  
        if (unlikely(offsetM + vecBaseM >= curCubeSingleM)) {  
            curVecBaseM = curCubeSingleM - offsetM;  
        }  
        // 使用AscendDequant接口做perchannel反量化  
        LocalTensor<cT::T> mmOutLocal = vecInQueue AllocTensor<cT::T>();  
        DataCopyPad2D(mmOutLocal, mmOutGm[mmOutOffset + offsetM * curVecBaseN], curVecBaseM, curVecBaseN, curVecBaseN);  
        vecInQueue.EnQue(mmOutLocal);  
        ComputeDequantAndActivate(mnConfig, curVecBaseM, alignBaseN, curVecBaseN, offsetM);  
        LocalTensor<DTYPE_Y> yLocal = vecOutQueue.DeQue<DTYPE_Y>();  
        DataCopyPad2D(yGm[outOffset + offsetM * tiling->n + offsetN], yLocal, curVecBaseM, curVecBaseN, alignBaseN, tiling->n);  
        vecOutQueue.FreeTensor(yLocal);  
    }  
} 
```

AIC和AIV启动比例设置为1:2后，出现Cube和Vector计算各自都有间隙、相互之间 都有等待耗时的情况。分析原因是因为Vector和Cube计算存在使用一份 workspace进行数据传递的场景，通过4份workspace的方案进行优化：host按4倍 baseM * baseN申请workspace，Cube侧代码在计算前可以跳过前4轮的等待。 

if ASCEND_IS_AIC{ if (cubeCount $> =$ tiling->parallelNum){ //tiling->parallelNum设置为4 CrossCoreWaitFlag(SYNC_AIV_TO_AIC); } mm.SetOrgShape(mnConfig.m, tiling->n, tiling->k); mm.setSingleShape(curSingleM, curSingleN, tiling->k); mm.SetTensorA(xGm[xOffset]); auto weightSlice $=$ weightGm[weightOffset]; if (mnConfig.numBlocksM $= = 1$ { weightSlice.SetL2CacheHint(CacheMode::CACHE_MODE_DISABLE); } mm.SetTensorB(weightSlice); uint64_t workspaceOffset $=$ mnConfig.workSpaceOffset; 

while (mm Iterate()) { mm.GetTensorC(mmOutGm[workspaceOffset], 0, true); CrossCoreSetFlag $<  2$ ,PIPEFix $\rightharpoondown$ (SYNC_AIC_TO_AIV); workspaceOffset $+ =$ (mnConfig.baseM\*mnConfig.baseN); } cubeCount++; 

Vector计算开启double buffer，InitBuffer指定分配内存块个数为2。 pipe->InitBuffer(scaleInQueue, 2, tiling->mmTilingData.baseN * sizeof(DTYPE_SCALE)); pipe->InitBuffer(perTokenScaleInQueue, 2, tiling->mmTilingData.baseM * sizeof(float)); pipe->InitBuffer(vecInQueue, 2, tiling->ubCalSize * sizeof(cT::T)); pipe->InitBuffer(vecOutQueue, 2, tiling->ubCalSize * sizeof(DTYPE_Y)); 

# 验证优化方案性能收益

将AI Core中的AIC和AIV启动比例设置为1:2后，执行总耗时从218.1us下降为 154.2us。指令流水图显示Cube计算间等待变小。 

![](images/2bde882399d311bbfc6699238ebdf9ac662ac0c79479eb3d52695ed434c5c878.jpg)


如上图所示，Vector计算已经不处于bound状态，但Cube和Vector计算都有间 隙，未被充分利用（上述两个箭头的位置）。分析原因如下： 

Vector计算在等Cube计算输出的数据，Cube侧需要等Vector计算完释放 workspace以存放下一轮的计算结果，当前为了让Cube、Vector计算流水并行， workspace使用了两份空间： 

![](images/62568e665b607cb79e7c68bd9b1802a17eec1f79f653b0f025c62017a42810c7.jpg)


因为Vector和Cube计算存在使用一份workspace进行数据传递的场景，存在数据 依赖，所以会有等待的间隔。 

可以采用4份workspace进行优化： 

![](images/54b37c77cacf4b6dc4cccb21e5234c1f0ef22b52ef506e19257e754758c8e6a6.jpg)


优化后，总耗时由154.2us下降为131.8us。指令流水图显示Vector、Cube计算各 自间隙明显减小。 

![](images/b4ed7f143e0b270dc560440a39eaa654ef84347984f8f3956a19896b71ef8c66.jpg)


● Vector计算开启double buffer，优化后执行总耗时从131.8us下降为128.1us。 

![](images/d92582c66d6807fbb3225ad244276b9d2c5fdc0225d935e439948a5ff106d184.jpg)


# 总结

● 在Vector计算为主要瓶颈点时，将AI Core中的AIC核和AIV核启动比例设置为1:2； 

Cube、Vector计算时间接近，且两者都有因相互等待导致的间隙时，采用4份 workspace优化； 

观察数据搬运是否与计算相互掩盖，多轮计算没有数据依赖，且buffer够大时，开 启double buffer，增加并行效率。