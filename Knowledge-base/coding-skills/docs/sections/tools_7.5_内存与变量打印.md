<!-- Source: 算子开发工具.md lines 7241-7355 | Section: 7.5 内存与变量打印 -->

# 7.5 内存与变量打印

根据变量类型和用法，变量可以存储在寄存器中或存储在Local Memory、Global Memory内存中，用户可以打印变量的地址以找出它的存储位置并进一步打印关联的 内存。 

# 打印变量

命中断点后，使用 p variable_name 的命令形式可打印指定的变量的值，比如： 

```lisp
(msdebug) p alpha  
(float) $0 = 0.00100000005  
(msdebug) p tiling  
(const TCubeTiling) $1 = {  
    usedCoreNum = 2  
    M = 1024  
    N = 640  
    Ka = 256  
    ...  
} 
```

# 打印 GlobalTensor

GlobalTensor一般用来存放Global Memory（外部存储）的全局数据。 

输入以下命令，进行GlobalTensor变量打印。以cGlobal为例，zGm所在内存地址请参 考address_字段，此处为“0x000012c045400000” 

```txt
(msdebug) p cGlobal
(AscendC::GlobalTensor)<float> $0 = {
AscendC::BaseGlobalTensor<float> = {
address_ = 0x000012c045400000
oriAddress_ = 0x000012c045400000
}
bufferSize_ = 655360
shapelInfo_ = {
shapeDim = '\0'
originalShapeDim = '\0'
shape = ([0] = 0, [1] = 0, [2] = 0, [3] = 0, [4] = 0, [5] = 0, [6] = 0, [7] = 0)
originalShape = ([0] = 0, [1] = 0, [2] = 0, [3] = 0, [4] = 0, [5] = 0, [6] = 0, [7] = 0)
dataFormat = ND
}
cacheMode_ = Cache_MODE_NORMAL 
```

因GlobalTensor类型变量实际的值保存在GM内存中，输入以下命令，打印GM内存中 位于地址“0x000012c045400000”上的值，打印格式设置为：打印1行，每行256字 节，按照float32格式打印。 

```txt
(msdebug) x -m GM -f float32[] 0x000012c045400000 -s 256 -c 1  
0x12c045400000: {4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096  
4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096  
4096 4096 4096 4096 4096 4096.4096.4096.4096.4096.4096.4096.4096.4096  
4096 4096 4096 4096 4096 4096.4096.4096.4096.4096 
```

# 说明

● 若需要打印其他自定义地址，用户需自行保证该自定义地址的合法性，否则可能会导致算子 运行出错。 

● 若需要以自定义地址为起始进行内存打印，可基于address_字段作为起始地址增加偏移，偏 移量单位为字节数，得到偏移后的GM内存地址后，传入内存打印命令即可。 

# 打印 LocalTensor

LocalTensor一般用于存放AI Core中Local Memory（内部存储）的数据。 

输入以下命令，进行LocalTensor变量打印，以reluOutLocal为例，reluOutLocal所在 内存地址请参考address_字段中的bufferAddr参数，此处位于0上，长度为131072。 

```autohotkey
(msdebug) p reluOutLocal
(AscendC::LocalTensor<float>) $2 = { 
```

```txt
AscendC::BaseLocalTensor<float> = {
    address_ = (dataLen = 131072, bufferAddr = 0, bufferHandle = "", logicPos = '\n')
}
shapelinfo_ = {
    shapeDim = '\0'
    originalShapeDim = '\0'
    shape = ([0] = 0, [1] = 1092616192, [2] = 4800, [3] = 1473680, [4] = 0, [5] = 1473888, [6] = 0, [7] = 1471968)
    originalShape = ([0] = 0, [1] = 3222199212, [2] = 4800, [3] = 1, [4] = 0, [5] = 1473376, [6] = 0, [7] = 1473376)
    dataFormat = ND
} 
```

该Tensor变量的实际内容保存在UB内存中，输入以下命令，打印UB内存中位于地址0 上的值，打印格式设置为：打印1行，每行256字节，按照float32格式打印。 

# 说明

● 本用例中，Tensor变量的实际内容保存在UB上，但LocalTensor不一定都保存在UB中，也可 能在L1/L0A/L0B上，需要用户根据代码自行判断，然后在打印命令的-m选项中选择正确的 内存类型。 

● 若需要以自定义地址为起始进行内存打印，可基于address_字段作为起始地址增加偏移，偏 移量单位为字节数，得到偏移后的GM内存地址后，传入内存打印命令即可。 

```txt
(msdebug) x -m UB -f float32[] 0 -s 256 -c 1  
0x00000000: {4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096  
4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096 4096  
4096 4096 4096 4096 4096 4096.  
4096 4096 4096 4096 4096 4096. 
```

# 打印所有局部变量

输入以下命令，打印当前作用域所有局部变量。 

```txt
(msdebug) var  
(MatmulLeakyKernel<__fp16, __fp16, float, float> *__stack__) this = 0x0000000000167b60  
 uint32_t) count = 0  
(const uint32_t) roundM = 2  
(const uint32_t) roundN = 5  
 uint32_t) startOffset = 0  
(AscendC::DataCopyParams) copyParam = (blockCount = 256, blockLen = 16, srcStride = 0, dstStride = 64) 
```