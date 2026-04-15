<!-- Source: 算子开发指南2.md lines 415-539 | Section: 3.9.1 内存访问 -->

# 3.9.1 内存访问

# 3.9.1.1 使用 Unified Buffer 提升内存访问效率

# 说明

该性能优化建议适用于如下型号： 

● Atlas 350 加速卡 

# 【优先级】高

【描述】SIMT访问Global Memory的粒度为128B，在随机访问Global Memory中的数 据时，访存效率较低。当所需访问的数据量远小于最大可用Unified Buffer空间 （256KB - 系统预留8KB - 最小Dcache 32KB）时，可以使用SIMD搬运接口将数据从 Global Memory搬运到Unified Buffer，使SIMT编程能够直接从Unified Buffer读取数 据，从而提高内存访问效率，提升算子的整体性能。 

【样例介绍】以SIMD与SIMT混合编程方式实现的gather算子为例，该算子从长度为 8192的一维向量中获取指定索引的65536个数据。通过将输入数据预先搬运到Unified Buffer中，提高离散内存访问的效率，从而提升算子的整体性能。 


表 3-27 算子规格


<table><tr><td>名称</td><td>name</td><td>shape</td><td>data type</td><td>format</td></tr><tr><td rowspan="2">算子输入</td><td>input</td><td>8192</td><td>float</td><td>ND</td></tr><tr><td>index</td><td>65536</td><td>uint32_t</td><td>ND</td></tr><tr><td>算子输出</td><td>output</td><td>65536</td><td>float</td><td>ND</td></tr></table>

SIMT线程层次结构为： 

线程块数：64 

单个线程块中线程数：1024 

完整样例请参考SIMD与SIMT混合编程使用UB提高内存访问效率。 

【反例】 

SIMT随机访问Global Memory上的input数据，触发数据加载到Dcache，随机访存效 率低，代码如下。 

namespace{ constexpr uint32_t THREAD_COUNT $= 1024$ constexpr uint32_t INPUT_SIZE $= 8192$ constexpr uint32_t INDEX_SIZE $= 65536$ } _simt_vf __launch_bounds_(THREAD_COUNT) inline void simt_gather( _gm_float\* input, _gm_uint32_t\* index, _gm_float\* output) { int32_t idx $\equiv$ blockIdx.x \* blockDim.x + threadIdx.x; if(idx $\Rightarrow$ INDEX_SIZE){ return; } uint32_t gatheridx $\equiv$ index[idx]; if(gatheridx $\rightharpoondown$ INPUT_SIZE){ return; } output[idx] $\equiv$ input[gatheridx]; } global _vector_void gather_kernel(_gm_float\* input,_gm_uint32_t\* index,_gm_float\* output) { asc_vf_call<simt_gather>(dim3(THREAD_COUNT),input,index,output); 

【正例】 

使用SIMD接口将数据从Global Memory搬运到Unified Buffer，基于SIMT编程方式直 接从Unified Buffer读取数据，访存效率远高于读取Global Memory上的数据，代码如 下。 

namespace{ constexpr uint32_t THREAD_COUNT $= 1024$ constexpr uint32_t INPUT_SIZE $= 8192$ constexpr uint32_t INDEX_SIZE $= 65536$ } 

```c
simt_vf __launch_bounds__(THREAD_COUNT) inline void simt_gather(
    __ubuf__ float* input,
    __gm__ uint32_t* index,
    __gm__ float* output)
{
    int32_t idx = blockIdx.x * blockDim.x + threadIdx.x;
    if (idx >= INDEX_SIZE) {
        return;
    }
    uint32_t gatheridx = index[idx];
    if (gatheridx >= INPUT_SIZE) {
        return;
    }
    output[idx] = input[gatheridx];
}
global __vector__ void gather_kernel(_gm__float* input, _gm__uint32_t* index, _gm__float* output)
{
    __ubuf__ float input_buf(INPUT_SIZE);
    uint32_t blk_length = INPUT_SIZE * sizeof blk);
    __asc_copy_gm2ub_align(input_buf, input, 1, blk_length, 0,0,false,0,0,0);
    if ASC_IS_AIV {
        __asc-sync_notify(Pipe_MTE2, PIPE_V, EVENT_ID0);
        __asc-sync_wait(Pipe_MTE2, PIPE_V, EVENT_ID0);
    }
    __asc_vf_call<simt_gather>(dim3(THREAD_COUNT), input_buf, index, output);
} 
```

# 【性能对比】

下图为反例的流水图，线程中有两条SIMT_LDG指令，对应表示从Global Memory上 加载数据，其中第二条指令占用区间分布不均，指令启动时间差异明显，同一个线程 块中随机访问输入数据input，单次访存加载128B数据，而针对单精度浮点数，实际有 效数据仅为4B，导致访存效率低。 


图 3-136 反例指令流水图（仿真数据）


![](images/66f8c5341bc302facec877ee2715dc43a1cdac735292027505929c8fd34e2016.jpg)


下图为反例的内存负载分析图，L2 Cache到Dcache数据传输带宽为10.04GB/s。 


图 3-137 反例内存负载分析（上板数据）


![](images/bc8d50b74181af207f5a2f0190c6355fccc08bb0db6b5948036578ed4181f6a0.jpg)


下图为正例的流水图，只有一条占用大区间的SIMT_LDG指令，MTE2流水新增搬运指 令MOV_SRC_TO_DST_ALIGNv2。 


图 3-138 正例指令流水图（仿真数据）


![](images/8159f3e568698164817244fc773074ccf3c137424648ad5b3fe8f637a525ca50.jpg)


下图为正例的内存负载分析图，L2 Cache到Dcache数据传输带宽降低为1.61GB/s，L2 Cache到Unified Buffer数据传输带宽提升至12.93GB/s。 


图 3-139 正例内存负载分析（上板数据）


![](images/41c691ee057f647448097a5ea947dcccde0d233675981fd5c4b28e7467fc2a4e.jpg)


对比算子运行时间，反例约为4.56us，正例约为3.57us，整体性能提升约21.71%。 


图 3-140 反例算子运行时间（上板数据）


![](images/d78cd19a27e120778d3c13242bc4494c553e65f8609567da8986ef45fd39a6c7.jpg)



图 3-141 正例算子运行时间（上板数据）


![](images/54bff79e206d9ba8ae83268475f5aeb5b57d6bc4c5fb52c4a1d4e9cda49f1829.jpg)