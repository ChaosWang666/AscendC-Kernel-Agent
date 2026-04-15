<!-- Source: 算子开发指南.md lines 4594-5225 | Section: 2.5 C++类库 API -->

# 2.5 C++类库 API

# 2.5.1 编程接口概述

# 说明

本章提供编程API的概述。具体API参考见Ascend C API。 

Ascend C提供一组类库API，开发者使用标准C++语法和类库API进行编程。Ascend C 编程类库API示意图如下所示，分为： 

语言扩展层 C API：开放芯片完备编程能力，支持数组分配内存，一般基于指针 编程，提供与业界一致的C语言编程体验。 

基础API：实现对硬件能力的抽象，开放芯片的能力，保证完备性和兼容性。标注 为ISASI（Instruction Set Architecture Special Interface，硬件体系结构相关的接 口）类别的API，不能保证跨硬件版本兼容。 

高阶API：实现一些常用的计算算法，用于提高编程开发效率，通常会调用多种基 础API实现。高阶API包括数学库、Matmul、Softmax等API。高阶API可以保证兼 容性。 

Utils API（公共辅助函数）：丰富的通用工具类，涵盖标准库、平台信息获取、 运行时编译及日志输出等功能，支持开发者高效实现算子开发与性能优化。 

![](images/031f723433b61a911dadcfd9d1449d5863c9e7e8d07df24833a0eb50d384539d.jpg)


# 说明

Ascend C API所在头文件目录为： 

● 基础API：${INSTALL_DIR}/include/ascendc/basic_api/interface 

● 高阶API：（注意，如下目录头文件中包含的接口如果未在资料中声明，属于间接调用接 口，开发者无需关注） 

${INSTALL_DIR}/include/ascendc/highlevel_api/lib 

${INSTALL_DIR}/include/tiling 

${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。以root用户安装为例，安装后文件默 认存储路径为：/usr/local/Ascend/cann。 

使用Ascend C API依赖的库文件说明如下： 

● 基础API：不涉及 

● 高阶API：因高阶API配套Host Tiling接口，需要链接libtiling_api.a。 

# 2.5.2 基础 API

# 2.5.2.1 概述

基础API实现对硬件能力的抽象，开放芯片的能力，保证完备性和兼容性。标注为 ISASI（Instruction Set Architecture Special Interface，硬件体系结构相关的接口）类 别的API，不能保证跨硬件版本兼容。 

# 根据功能的不同，主要分为以下几类：

标量计算API，实现调用Scalar计算单元执行计算的功能。 

Memory矢量计算API，实现调用Vector计算单元执行计算的功能。 

矩阵计算API，实现调用Cube计算单元执行计算的功能。 

数据搬运API，计算API基于Local Memory数据进行计算，所以数据需要先从 Global Memory搬运至Local Memory，再使用计算API完成计算，最后从Local Memory搬出至Global Memory。执行搬运过程的接口称之为数据搬运API，比如 DataCopy接口。 

资源管理API，用于分配管理内存，比如AllocTensor、FreeTensor接口; 

同步控制API，完成任务间的通信和同步，比如EnQue、DeQue接口。不同的API 指令间有可能存在依赖关系，从2.2.3.1 抽象硬件架构可知，不同的指令异步并行 

执行，为了保证不同指令队列间的指令按照正确的逻辑关系执行，需要向不同的 组件发送同步指令。同步控制API内部即完成这个发送同步指令的过程，开发者无 需关注内部实现逻辑，使用简单的API接口即可完成。 

# 根据对数据操作方法的不同，分为以下几类：

连续计算API：支持Tensor前n个数据计算。针对源操作数的连续n个数据进行计算 并连续写入目的操作数，解决一维tensor的连续计算问题。 Add(dst, src1, src2, n); 

高维切分API：支持Repeat和Stride。功能灵活的计算API，提供与BuilitIn API完 全对等编程能力，充分发挥硬件优势，支持对每个操作数的DataBlock Stride， Repeat Stride，Mask等参数的操作。 

下图以矢量加法为例，展示了连续计算API和高维切分API的特点。 


图 2-18 计算 API 几种计算方式的特点


![](images/25d4a2e6a257444dd45cfbca1882c9db1ceefab4e6df8a632f16d93ff60474d5.jpg)


![](images/31e3496e354367870973d0cf5d1a2fe16d2bc9adda2b34a71a93863515b8ce86.jpg)


# 2.5.2.2 接口分类说明

# 2.5.2.2.1 连续计算 API

连续计算API，支持Tensor前n个数据计算。针对源操作数的连续n个数据进行计算并连 续写入目的操作数，解决一维tensor的连续计算问题。 

Add(dst, src1, src2, n); 

下图以矢量加法为例，展示了连续计算API的特点。 


图 2-19 连续计算 API


![](images/5f065e64554b99d885ed30188b6412af1b5cec91f1ef79eeffb2a626813f8b74.jpg)


# 2.5.2.2.2 高维切分 API

# 说明

● 本章节对矢量计算基础API中的tensor高维切分计算接口做解释说明。如果您不需要使用此 类接口，可略过该章节。 

● 下文中的repeatTime、dataBlockStride、repeatStride、mask为通用描述，其命名不一定与 具体指令中的参数命名完全对应。 

比如，单次迭代内不同datablock间地址步长dataBlockStride参数，在单目API中，对应为 dstBlkStride、srcBlkStride参数；在双目API中，对应为dstBlkStride、src0BlkStride、 src1BlkStride参数。 

您可以在具体接口的参数说明中，找到参数含义的描述。 

使用tensor高维切分计算API可充分发挥硬件优势，支持开发者控制指令的迭代执行和 操作数的地址间隔，功能更加灵活。 

矢量计算通过Vector计算单元完成，矢量计算的源操作数和目的操作数均通过Unified Buffer（UB）来进行存储。Vector计算单元每个迭代会从UB中取出8个datablock（每 个datablock数据块内部地址连续，长度32Byte），进行计算，并写入对应的8个 datablock中。下图为单次迭代内的8个datablock进行Exp计算的示意图。 


图 2-20 单次迭代内的 8 个 datablock 进行 Exp 计算示意图


![](images/85d0260933da42294c93a0f22e8f1064c1a27a667fa46a14e5dd9702be52d389.jpg)


矢量计算API支持开发者通过repeatTime来配置迭代次数，从而控制指令的多次 迭代执行。假设repeatTime设置为2，矢量计算单元会进行2个迭代的计算，可计 算出2 * 8（每个迭代8个datablock） * 32Byte（每个datablock32Byte） = 512Byte的结果。如果数据类型为half，则计算了256个元素。下图展示了2次迭代 Exp计算的示意图。由于硬件限制，repeatTime不能超过255。 


图 2-21 2 次迭代 Exp 计算


![](images/1e4cd200a0fafef66bd20be06ee304c6d2d574d32141779e3ca8235c8228f359.jpg)


针对同一个迭代中的数据，可以通过mask参数进行掩码操作来控制实际参与计算 的个数。下图为进行Abs计算时通过mask逐比特模式按位控制哪些元素参与计算 的示意图，1表示参与计算，0表示不参与计算。 


图 2-22 通过 mask 参数进行掩码操作示意图（以 float 数据类型为例）


![](images/70554aa0abf2ce9121dc15c5b579d682d6ead1f537ef2440733ed3299f5d0b0f.jpg)



注：un表示undefined


矢量计算单元还支持带间隔的向量计算，通过dataBlockStride（单次迭代内不同 datablock间地址步长）和repeatStride（相邻迭代间相同datablock的地址步 长）来进行配置。 

# dataBlockStride

如果需要控制单次迭代内，数据处理的步长，可以通过设置同一迭代内不同 datablock的地址步长dataBlockStride来实现。下图给出了单次迭代内非连续 场景的示意图，示例中源操作数的dataBlockStride配置为2，表示单次迭代内 不同datablock间地址步长（起始地址之间的间隔）为2个datablock。 


图 2-23 单次迭代内非连续场景的示意图


![](images/d01f26bc1e699afc0d95db2cf4864e95f21dbb62b7bb74a74d6fc0587aefacce.jpg)


# repeatStride

当repeatTime大于1，需要多次迭代完成矢量计算时，您可以根据不同的使用 场景合理设置相邻迭代间相同datablock的地址步长repeatStride的值。 

下图给出了多次迭代间非连续场景的示意图，示例中源操作数和目的操作数 的repeatStride均配置为9，表示相邻迭代间相同datablock起始地址之间的 间隔为9个datablock。相同datablock是指datablock在迭代内的位置相同， 比如下图中的src1和src9处于相邻迭代，在迭代内都是第一个datablock的位 置，其间隔即为repeatStride的数值。 


图 2-24 多次迭代间非连续场景的示意图


![](images/62d485a75a7d6690e0ce59a838e73914bc2f6edcceb9028f1d92fe237ec66894.jpg)


下文中给出了dataBlockStride、repeatStride、mask的详细配置说明和示例。 

# dataBlockStride

dataBlockStride是指同一迭代内不同datablock的地址步长。 

连续计算，dataBlockStride设置为1，对同一迭代内的8个datablock数据连续进行 处理。 

非连续计算，dataBlockStride值大于1（如取2），同一迭代内不同datablock之间 在读取数据时出现一个datablock的间隔，如下图所示。 


图 2-25 dataBlockStride 不同取值举例


![](images/3a2663e75dc3c7021c6f01ccfd22a5b6ae3640cf447a85d4c3f40c6bfe8deb82.jpg)


repeatTime >1 repeatStride $= 8$ dataBlockStride = 1 

![](images/e6ad403060cc890c8573547be75c59418039f016286f5f29199cfdce8f6f6cb7.jpg)


![](images/2281b4f7fbad77bf198261291b85c627a30628b5397b2b861364da20b7160045.jpg)


repeatTime >1 repeatStride $\equiv$ 16 dataBlockStride $^ { \circ 2 }$ 

![](images/0176cb4305d2d50c7dd40c50cf57dcd5eef61642527432f18678d1c445e8e3b9.jpg)


# repeatStride

repeatStride是指相邻迭代间相同datablock的地址步长。 

连续计算场景：假设定义一个Tensor供目的操作数和源操作数同时使用（即地址 重叠），repeatStride取值为8。此时，矢量计算单元第一次迭代读取连续8个 datablock，第二轮迭代读取下一个连续的8个datablock，通过多次迭代即可完成 所有输入数据的计算。 

repeatTime >1 repeatStride = 8 

![](images/448892ee0efbb56ded422b409cf2321c4b29af197f208a93957c64c36de53821.jpg)


非连续计算场景：repeatStride取值大于8（如取10）时，则相邻迭代间矢量计算 单元读取的数据在地址上不连续，出现2个datablock的间隔。 

repeatTime >1 repeatStride = 10 

![](images/8fe85bc19857a77bba07c028cd18407d23ee09217f5364b0f179723274856daf.jpg)


反复计算场景：repeatStride取值为0时，矢量计算单元会对首个连续的8个 datablock进行反复读取和计算。 

repeatTime>1 repeatStride ${ \mathfrak { \mathbf { \alpha } } } = { \mathfrak { 0 } }$ 

![](images/de1cb6617ef0f1de7fba1c157934b31b00849a2d65f3c4f288f20d03be299806.jpg)


部分重复计算：repeatStride取值大于0且小于8时，相邻迭代间部分数据会被矢量 计算单元重复读取和计算，此种情形一般场景不涉及。 

![](images/6313073d58ca4c2ddae6a62acd1c87ee00ecee1d356b526fcb6afacc7be0cc8a.jpg)


# mask 参数

mask用于控制每次迭代内参与计算的元素。可通过连续模式和逐bit模式两种方式进行 设置。 

连续模式：表示前面连续的多少个元素参与计算。数据类型为uint64_t。取值范围 和源操作数的数据类型有关，数据类型不同，每次迭代内能够处理的元素个数最 大值不同（当前数据类型单次迭代时能处理的元素个数最大值为：256 / sizeof(数 据类型)）。当操作数的数据类型占bit位16位时（如half/uint16_t），mask∈[1, 128]；当操作数为32位时（如float/int32_t），mask∈[1, 64]。 

# 具体样例如下：

```cpp
// int16_t数据类型单次迭代能处理的元素个数最大值为256/sizeof(int16_t) = 128, mask = 64, mask ∈ [1, 128], 所以是合法输入
// repeatTime = 1, 共128个元素，单次迭代能处理128个元素，故repeatTime = 1
// dstBlkStride, src0BlkStride, src1BlkStride = 1, 单次迭代内连续读取和写入数据
// dstRepStride, src0RepStride, src1RepStride = 8, 迭代间的数据连续读取和写入
uint64_t mask = 64;
AscendC::Add.dstLocal, src0Local, src1Local, mask, 1, {1, 1, 1, 8, 8, 8}; 
```

# 结果示例如下：

```txt
输入数据(src0Local): [1 2 3 ... 64 ... 128]  
输入数据(src1Local): [1 2 3 ... 64 ... 128]  
输出数据.dstLocal): [2 4 6 ... 128 undefined...undefined] 
```

```cpp
// int32_t数据类型单次迭代能处理的元素个数最大值为256 sizeof(int32_t) = 64, mask = 64, mask ∈ [1, 64], 所以是合法输入
// repeatTime = 1, 共64个元素，单次迭代能处理64个元素，故repeatTime = 1
// dstBlkStride, src0BlkStride, src1BlkStride = 1, 单次迭代内连续读取和写入数据
// dstRepStride, src0RepStride, src1RepStride = 8, 迭代间的数据连续读取和写入
uint64_t mask = 64;
AscendC::Add.dstLocal, src0Local, src1Local, mask, 1, {1, 1, 1, 8, 8, 8}; 
```

# 结果示例如下：

```txt
输入数据(src0Local): [1 2 3 ... 64]  
输入数据(src1Local): [1 2 3 ... 64]  
输出数据.dstLocal): [2 4 6 ... 128] 
```

逐bit模式：可以按位控制哪些元素参与计算，bit位的值为1表示参与计算，0表示 不参与。 

mask为数组形式，数组长度和数组元素的取值范围和操作数的数据类型有关。当 操作数为16位时，数组长度为2，mask[0]、mask[1] $\in$ [0, 264-1]并且不同时为 0；当操作数为32位时，数组长度为1，mask[0] $\in$ (0, 264-1]；当操作数为64位 时，数组长度为1， $\mathsf { m a s k } [ 0 ] \in ( 0 , 2 ^ { 3 2 } - 1 ]$ $\in$ 。 

# 具体样例如下:

```c
//数据类型为int16_t  
uint64_t mask[2] = {6148914691236517205, 6148914691236517205};  
//repeatTime = 1,共128个元素，单次迭代能处理128个元素，故repeatTime = 1。  
//dstBlkStride, src0BlkStride, src1BlkStride = 1, 单次迭代内连续读取和写入数据。  
//dstRepStride, src0RepStride, src1RepStride = 8, 迭代间的数据连续读取和写入。  
AscendC::AdddstLocal, src0Local, src1Local, mask, 1, {1, 1, 1, 8, 8, 8}； 
```

# 结果示例如下：

```txt
输入数据(src0Local): [1 2 3 ... 64 ... 127 128]  
输入数据(src1Local): [1 2 3 ... 64 ... 127 128]  
输出数据.dstLocal): [2 undefined 6 ... undefined ...254 undefined] 
```

# mask过程如下：

mask={6148914691236517205, 6148914691236517205}（注： 6148914691236517205表示64位二进制数0b010101....01，mask按照低位到高位 的顺序排布） 

<table><tr><td>src0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>8</td><td>9</td><td>10</td><td>11</td><td>12</td><td>13</td><td>14</td><td>15</td><td>16</td><td>17</td><td>18</td><td>19</td><td>20</td><td>...</td><td>64</td><td>...</td><td>127</td><td>128</td></tr><tr><td>src1</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>8</td><td>9</td><td>10</td><td>11</td><td>12</td><td>13</td><td>14</td><td>15</td><td>16</td><td>17</td><td>18</td><td>19</td><td>20</td><td>...</td><td>64</td><td>...</td><td>127</td><td>128</td></tr><tr><td>mask</td><td>1</td><td>0</td><td>1</td><td>0</td><td>1</td><td>0</td><td>1</td><td>0</td><td>1</td><td>0</td><td>1</td><td>0</td><td>1</td><td>0</td><td>1</td><td>0</td><td>1</td><td>0</td><td>1</td><td>0</td><td>...</td><td>0</td><td>...</td><td>1</td><td>0</td></tr><tr><td>dst</td><td>2</td><td>un</td><td>6</td><td>un</td><td>10</td><td>un</td><td>14</td><td>un</td><td>18</td><td>un</td><td>22</td><td>un</td><td>26</td><td>un</td><td>30</td><td>un</td><td>34</td><td>un</td><td>38</td><td>un</td><td>...</td><td>un</td><td>...</td><td>254</td><td>un</td></tr></table>


注：un表示undefined 


```c
//数据类型为int32_t  
uint64_t mask[1] = {6148914691236517205};  
//repeatTime = 1,共64个元素，单次迭代能处理64个元素，故repeatTime = 1。  
//dstBlkStride, src0BlkStride, src1BlkStride = 1,单次迭代内连续读取和写入数据。  
//dstRepStride, src0RepStride, src1RepStride = 8,迭代间的数据连续读取和写入。  
AscendC::AdddstLocal, src0Local, src1Local, mask, 1,{1,1,1,8,8,8}）; 
```

# 结果示例如下：

```txt
输入数据(src0Local): [1 2 3 ... 63 64]  
输入数据(src1Local): [1 2 3 ... 63 64]  
输出数据.dstLocal): [2 undefined 6 ... 126 undefined] 
```

# mask过程如下：

mask={6148914691236517205, 0}（注：6148914691236517205表示64位二进 制数0b010101....01） 

<table><tr><td>src0</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>8</td><td>9</td><td>10</td><td>11</td><td>12</td><td>13</td><td>14</td><td>15</td><td>16</td><td>17</td><td>18</td><td>19</td><td>20</td><td>...</td><td>63</td><td>64</td></tr><tr><td>src1</td><td>1</td><td>2</td><td>3</td><td>4</td><td>5</td><td>6</td><td>7</td><td>8</td><td>9</td><td>10</td><td>11</td><td>12</td><td>13</td><td>14</td><td>15</td><td>16</td><td>17</td><td>18</td><td>19</td><td>20</td><td>...</td><td>63</td><td>64</td></tr><tr><td>mask</td><td>1</td><td>0</td><td>1</td><td>0</td><td>1</td><td>0</td><td>1</td><td>0</td><td>1</td><td>0</td><td>1</td><td>0</td><td>1</td><td>0</td><td>1</td><td>0</td><td>1</td><td>0</td><td>1</td><td>0</td><td>...</td><td>1</td><td>0</td></tr><tr><td>dst</td><td>2</td><td>un</td><td>6</td><td>un</td><td>10</td><td>un</td><td>14</td><td>un</td><td>18</td><td>un</td><td>22</td><td>un</td><td>26</td><td>un</td><td>30</td><td>un</td><td>34</td><td>un</td><td>38</td><td>un</td><td>...</td><td>126</td><td>un</td></tr></table>


注：un表示undefined 


# 2.5.2.3 常用操作速查指导

# 2.5.2.3.1 如何使用掩码操作 API

Mask用于控制矢量计算中参与计算的元素个数，支持以下工作模式及配置方式： 


表 2-24 Mask 工作模式


<table><tr><td>工作模式</td><td>说明</td></tr><tr><td>Normal模式</td><td>默认模式，支持单次迭代内的Mask能力，需要开发者配置迭代次数，额外进行尾块的计算。
Normal模式下，Mask用来控制单次迭代内参与计算的元素个数。通过调用SetMaskNorm设置Normal模式。</td></tr><tr><td>Counter模式</td><td>简化模式，直接传入计算数据量，自动推断迭代次数，不需要开发者去感知迭代次数、处理非对齐尾块的操作；但是不具备单次迭代内的Mask能力。
Counter模式下，Mask表示整个矢量计算参与计算的元素个数。通过调用SetMaskCount设置Counter模式。</td></tr></table>


表 2-25 Mask 配置方式


<table><tr><td>配置方式</td><td>说明</td></tr><tr><td>接口传参(默认)</td><td>通过矢量计算API的入参直接传递Mask值。矢量计算API的模板参数 isSetMask(仅部分API支持)用于控制接口传参还是外部API配置,默认值为true,表示接口传参。Mask对应于高维切分计算API中的mask-mask[]参数或者tensor前n个数据计算API中的calCount参数。</td></tr><tr><td>外部API配置</td><td>调用SetVectorMask接口设置Mask值,矢量计算API的模板参数 isSetMask设置为false,接口入参中的Mask参数(对应于高维切分计算API中的mask/mask[]参数或者tensor前n个数据计算API中的calCount参数)不生效。适用于Mask参数相同,多次重复使用的场景,无需在矢量计算API内部反复设置,会有一定的性能优势。</td></tr></table>

Mask操作的使用方式如下： 


表 2-26 Mask 操作的使用方式


<table><tr><td>配置方式</td><td>工作模式</td><td>前n个数据计算API</td><td>高维切分计算API</td></tr><tr><td rowspan="2">接口传参</td><td>Normal模式</td><td>不涉及。</td><td>isSetMask模板参数设置为true，通过接口入参传入Mask，根据使用场景配置dataBlockStride、repeatStride、repeatTime参数。</td></tr><tr><td>Counter模式</td><td>isSetMask模板参数设置为true，通过接口入参传入Mask。</td><td>● isSetMask模板参数设置为true，通过接口入参传入Mask。
● 根据使用场景配置dataBlockStride、repeatStride参数。repeatTime传入固定值即可，建议统一设置为1，该值不生效。</td></tr><tr><td rowspan="2">外部API配置</td><td>Nomencl模式</td><td>不涉及。</td><td>调用SetVectorMask设置Mask,之后调用高维切分计算API。· SetMask模板参数设置为false,接口入参中的mask值设置为占位符MASK_placeHOLDER,用于占位,无实际含义。· 根据使用场景配置repeatTime、dataBlockStride、repeatStride参数。</td></tr><tr><td>Counter模式</td><td>调用SetVectorMask设置Mask,之后调用前n个数据计算API,isSetMask模板参数设置为false;接口入参中的calCount建议设置成1。</td><td>调用SetVectorMask设置Mask,之后调用高维切分计算API。· SetMask模板参数设置为false;接口入参中的mask值设置为MASK_placeHOLDER,用于占位,无实际含义。· 根据使用场景配置dataBlockStride、repeatStride参数。repeatTime传入固定值即可,建议统一设置为1,该值不生效。</td></tr></table>

# 典型场景的使用示例如下：

场景1：Normal模式 $^ +$ 外部API配置 $^ +$ 高维切分计算API 

```cpp
AscendC::LocalTensor<half> dstLocal;  
AscendC::LocalTensor<half> src0Local;  
AscendC::LocalTensor<half> src1Local;  
// 1、设置Normal模式  
AscendC::SetMaskNorm();  
// 2、设置Mask  
AscendC::SetVectorMask<half, AscendC::MaskMode::NORMAL>(0xFFFFFFAAAAAAAA, 0xFFFFFFAAAAAAAA); //逐bit模式  
// SetVectorMask<half, MaskMode::NORMAL>(128); //连续模式  
// 3、多次调用矢量计算API, isSetMask模板参数设置为false，接口入参中的mask值设置为占位符MASK_placeHOLDER，用于占位，无实际含义  
//根据使用场景配置repeatTime、dataBlockStride、repeatStride参数  
// dstBlkStride, src0BlkStride, src1BlkStride = 1, 单次迭代内数据连续读取和写入  
// dstRepStride, src0RepStride, src1RepStride = 8, 相邻迭代间数据连续读取和写入  
AscendC::Add<half, false>(dstLocal, src0Local, src1Local, AscendC::MASK_placeHOLDER, 1, {2,2,2,8,8});  
AscendC::Sub<half, false>(src0Local, dstLocal, src1Local, AscendC::MASK_placeHOLDER, 1, {2,2,2,8,8,8});  
AscendC::Mul<half, false>(src1Local, dstLocal, src0Local, AscendC::MASK_placeHOLDER, 1, {2,2,2,8,8,8});  
//4、恢复Mask值为默认值  
AscendC::ResetMask(); 
```

场景2：Counter模式 $^ +$ 外部API配置 $^ +$ 高维切分计算API 

```txt
AscendC::LocalTensor<half> dstLocal;  
AscendC::LocalTensor<half> src0Local;  
AscendC::LocalTensor<half> src1Local;  
int32_t len = 128; //参与计算的元素个数//1、设置Counter模式 
```

```rust
AscendC::SetMaskCount();  
//2、设置Mask  
AscendC::SetVectorMask<half, AscendC::MaskMode::COUNTER>(len);  
//3、多次调用矢量计算API,isSetMask模板参数设置为false；接口入参中的mask值设置为MASK_placeHOLDER，用于占位，无实际含义  
//根据使用场景正确配置dataBlockStride、repeatStride参数。repeatTime传入固定值即可，建议统一设置为1，该值不生效  
AscendC::Add<half,false>(dstLocal,src0Local,src1Local,AscendC::MASK_placeHOLDER,1,{1,1,1,8,8,8});  
AscendC::Sub<half,false>(src0Local,dstLocal,src1Local,AscendC::MASK_placeHOLDER,1,{1,1,1,8,8,8});  
AscendC::Mul<half,false>(src1Local,dstLocal,src0Local,AscendC::MASK_placeHOLDER,1,{1,1,1,8,8,8});  
//4、恢复工作模式  
AscendC::SetMaskNorm();  
//5、恢复Mask值为默认值  
AscendC::ResetMask(); 
```

场景3：Counter模式 $^ +$ 外部API配置 $^ +$ 前n个数据计算接口配合使用 

```txt
AscendC::LocalTensor<half> dstLocal;  
AscendC::LocalTensor<half> src0Local;  
half num = 2;  
//1、设置Mask  
AscendC::SetVectorMask<half, AscendC::MaskMode::COUNTER>(128); //参与计算的元素个数为128  
//2、调用前n个数据计算API，isSetMask模板参数设置为false；接口入参中的calCount建议设置成1。  
AscendC::Adds<half, false>(dstLocal, src0Local, num, 1);  
AscendC::Muls<half, false>(dstLocal, src0Local, num, 1);  
//3、恢复工作模式  
AscendC::SetMaskNorm();  
//4、恢复Mask值为默认值  
AscendC::ResetMask(); 
```

# 说明

● 前n个数据计算API接口内部会设置工作模式为Counter模式，所以如果前n个数据计算API配 合Counter模式使用时，无需手动调用SetMaskCount设置Counter模式。 

● 所有手动使用Counter模式的场景，使用完毕后，需要调用SetMaskNorm恢复工作模式。 

● 调用SetVectorMask设置Mask，使用完毕后，需要调用ResetMask恢复Mask值为默认值。 

● 使用高维切分计算API配套Counter模式使用时，比前n个数据计算API增加了可间隔的计算， 支持dataBlockStride、repeatStride参数。 

# 2.5.2.3.2 如何使用归约计算 API

归约指令将数据集合简化为单一值或者更小的集合。按照归约操作的数据范围的不 同，归约指令分为以下几种，可参考归约指令示意图： 

ReduceMax/ReduceMin/ReduceSum：对所有的输入数据做归约操作，得到最大 值和最大值索引/最小值和最小值索引/数据总和。 

WholeReduceMax/WholeReduceMin/WholeReduceSum：对每个repeat内的输 入数据做归约操作，得到每个repeat内的最大值和最大值索引/最小值和最小值索 引/数据总和。返回索引时返回的是repeat内部索引。 

BlockReduceMax/BlockReduceMin/BlockReduceSum：对每个datablock内的输 入数据做归约操作，得到每个datablock内的最大值/最小值/数据总和。 

PairReduce：相邻两个（奇偶）元素求和，例如（a1, a2, a3, a4, a5, a6...），归 约后结果为（a1+a2, a3+a4, a5+a6, ......）。 


图 2-26 归约指令示意图


![](images/da488858e34f59298d14174b59cf12a9ac8ac8a537b1f9922f1eebe3942dd7c0.jpg)


![](images/2503169544eb6a4ddeae5439c27cead3aa47ef8dc0c194f2d132c616d1a988a2.jpg)


![](images/84ae23d4ced629d203f3f7da7a5a1cee2f74380635775e0d2d9695a1f519daff.jpg)


![](images/d5205f930520a09250ad67ced18a9cdff90e77f4ae44b0399bf698ad73444013.jpg)


针对归约指令，和其他的基础API一样也提供了tensor高维切分计算接口，可充分发挥 硬件优势，支持开发者控制指令的迭代执行和操作数的地址间隔，功能更加灵活。但 具体参数的单位和约束与基础API略有不同，下文将对这些差异点进行介绍。 

repeatTime：迭代次数，开发者通过repeatTime来配置迭代次数，从而控制指令 的多次迭代执行。 

ReduceMax/ReduceMin/ReduceSum对于repeatTime超过255的情况，在API 内部进行了处理，所以repeatTime支持更大的取值范围，保证不超过int32_t 最大值的范围即可。 

WholeReduceMax/WholeReduceMin/WholeReduceSum/BlockReduceMax/ BlockReduceMin/BlockReduceSum/PairReduce和其他基础API一样， repeatTime要求不超过255。 

mask：用于控制每次迭代内参与计算的元素，mask参数的使用方法和基础API通 用的使用方法一致。 

repeatStride：表示相邻迭代间的地址步长。 

ReduceMax/ReduceMin/ReduceSum指令的目的操作数会归约成一个最大 值/最小值/总和，所以其目的操作数不支持配置repeatStride。仅源操作数支 持repeatStride，其含义、单位（datablock）和基础API通用说明一致。 

WholeReduceMax/WholeReduceMin/WholeReduceSum/BlockReduceMax/ BlockReduceMin/BlockReduceSum/PairReduce源操作数和目的操作数都支 持配置repeatStride，源操作数repeatStride的含义、单位（datablock）和基 础API通用说明一致。目的操作数repeatStride的含义、单位和基础API通用说 明有差异，因为归约后，目的操作数的长度会变短，比如WholeReduceSum 归约后每个repeat会合并为一个值，所以迭代之间的间隔不能再使用一个 datablock为单位，而以一个repeat归约后的长度为单位。 

dataBlockStride：表示单次迭代内datablock的地址步长。 

ReduceMax/ReduceMin/ReduceSum指令的目的操作数会归约成一个最大 值/最小值/总和，所以其目的操作数不支持配置dataBlockStride。源操作数 也不支持dataBlockStride。 

WholeReduceMax/WholeReduceMin/WholeReduceSum/BlockReduceMax/ BlockReduceMin/BlockReduceSum/PairReduce源操作数支持配置 dataBlockStride，源操作数dataBlockStride的含义、单位（datablock）和基 础API通用说明一致。目的操作数不支持dataBlockStride，因为归约后，目的 操作数的长度会变短，比如WholeReduceSum归约后每个repeat会合并为一 个值，不再有迭代内datablock和地址间隔的概念。 

# 2.5.3 高阶 API

# 2.5.3.1 概述

高阶API基于单核对常见算法进行抽象和封装，实现了一些常用的计算算法，旨在提高 编程开发效率。高阶API一般通过调用多种基础API实现。高阶API包括数学计算、矩阵 计算、激活函数等API。 

如下图所示，实现一个矩阵乘操作，使用基础API需要的步骤较多，需要关注格式转 换、数据切分等逻辑；使用高阶API则无需关注这些逻辑，可以快速实现功能。 

![](images/914c2b84e69f8c1d8a816fe22a392d02f8825516bee01aa73cf38c998591d1d6.jpg)


# 2.5.3.2 常用操作速查指导

# 2.5.3.2.1 如何使用 Tiling 依赖的头文件

由于AI处理器的Scalar计算单元执行能力有限，为减少算子Kernel侧的Scalar计算，将 部分计算在Host端执行，这需要编写Host端Tiling代码。注意，在程序中调用高阶API 的Tiling接口或者使用高阶API的Tiling结构体参数时，需要引入依赖的头文件。在不同 的Tiling实现方式下，具体为： 

# 使用标准C++语法定义Tiling结构体

这种方式需要引入依赖的头文件如下。所有高阶API的Tiling结构体定义在 AscendC::tiling命名空间下，因此需要通过AscendC::tiling访问具体API的Tiling结 构体。 

```txt
include "kernel_tiling/kernel_tiling.h" // ... AscendC::tiling::TCubeTiling cubeTilingData; 
```

# 使用TILING_DATA_DEF宏定义Tiling结构体

这种方式需要引入依赖的头文件如下。所有高阶API的Tiling结构体和Tiling函数定 义在optiling命名空间下。 

```txt
include "tiling/tiling_api.h"   
namespace optiling{ //...   
} 
```

# 2.5.3.2.2 如何使用 Kernel 侧临时空间

Kernel侧接口的内部实现一般涉及复杂的数学计算，需要额外的临时空间来存储计算 过程中的中间变量。除矩阵计算、HCCL通信类、卷积计算等，对于多数高阶API中临 

时空间的处理，开发者可以通过Kernel侧接口的入参sharedTmpBuffer传入提前申请的 临时空间、通过接口框架申请临时空间两种方式。 

通过sharedTmpBuffer入参传入，Kernel侧接口使用该传入的Tensor作为临时空 间。该方式下，开发者可以自行管理sharedTmpBuffer内存空间，并在接口调用完 成后，复用该部分内存，内存不会反复申请释放，灵活性较高，内存利用率也较 高。 

接口框架申请临时空间，开发者无需在Kernel侧申请临时空间，但是需要预留临 时空间的大小，即在分配内存空间时，应在可用空间大小中减去需预留的临时空 间大小。 

无论开发者采用上述哪种方式，在申请Tensor空间或预留临时空间时，都需要提前获 取Kernel侧接口所需的临时空间大小BufferSize，为此相应类别API中提供了 GetxxxMaxMinTmpSize接口，用于获取所需预留空间的大小范围，其中xxx为对应的 Kernel侧接口。开发者在Host侧调用GetxxxMaxMinTmpSize接口，获取预留/申请的 最大和最小临时空间大小，基于此范围选择合适的空间大小作为Tiling参数传递到 Kernel侧使用。 

● 为保证功能正确，预留/申请的临时空间大小不能小于最小临时空间大小； 

在最小临时空间-最大临时空间范围内，随着临时空间增大，Kernel侧接口计算性 能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存 使用情况进行空间预留/申请。 

# 以Asin接口为例：

```cpp
// 算子输入的数据类型T为half，isReuseSource传入默认值false  
auto shape_input = context->GetInputTensor(0)->GetOriginShape();  
std::vector<int64_t> srcDims = {shape_input.GetDim(0), shape_input.GetDim(1)};  
uint32_t srcSize = 1;  
for (auto dim : srcDims) {  
    srcSize * = dim;  
}  
uint32_t(typeSize = 2);  
ge::Shape shape(srcDims);  
uint32_t minValue = 0;  
uint32_t maxValue = 0;  
AscendC::GetAsinMaxMinTmpSize(shape, typeSize, false, maxValue, minValue);  
auto platformInfo = context->GetPlatformInfo();  
auto ascendcPlatform = platform_ascendingc::PlatformAscendC platformInfo);  
uint64_t tailSize = 0; // UB剩余空间大小  
ascendcPlatform.GetCoreMemSize platform_ascendingc::CoreMemType::UB, tailSize); // 本样例中使用完整的ub空间，实际情况下tailSize需要减掉用户已使用的UB空间  
auto tmpSize = tailSize >= maxValue ? maxValue : tailSize;  
AsinCustomTilingData tiling;  
tiling.set_tmpBufferSize(tmpSize); // 将临时空间大小设置为Tiling参数 
```

另外，多数高阶API中提供了GetxxxTmpBufferFactorSize接口，该接口用于获取 maxLiveNodeCnt和extraBuf，maxLiveNodeCnt表示临时空间是单次计算数据量所占 空间的多少倍；extraBuf表示Kernel侧接口所需的临时空间大小。在固定空间大小的情 况下，通过maxLiveNodeCnt和extraBuf可以推算算子单次最大计算元素数量。 

# 推算示例如下：

算子实现需要调用Mean接口，开发者为其预留currBuff大小的空间（即总可用空 间），利用GetMeanTmpBufferFactorSize接口得到maxLiveNodeCnt、extraBuf 输出值，可推导算子单次最大计算元素数量为： 

```javascript
currentShapeSize = (currBuff - extraBuf) / maxLiveNodeCnt / typeSize 
```

算子实现需要调用两个Kernel侧API KernelIntf1、KernelIntf2，利用两个 GetXxxTmpBufferFactorSize（其中Xxx为需要调用的两个高阶API）接口的两组输 出值(maxLiveNodeCnt、extraBuf)以及当前现有的临时空间currBuff，推导单次 最大计算元素数量currentShapeSize为： currentShapeSize1 $=$ (currBuff - extraBuf1) / maxLiveNodeCnt1 / typeSize currentShapeSize2 $=$ (currBuff - extraBuf2) / maxLiveNodeCnt2 / typeSize currentShapeSize $=$ min(currentShapeSize1 , currentShapeSize2) 

注意上文中的currBuff表示接口计算可用的空间，需要去除用户输入输出等空间。 

以算子中需要同时调用Asin、Acos接口为例： 

```cpp
// 算子输入的数据类型T为half  
auto shape_input = context->GetInputTensor(0) ->GetOriginShape();  
std::vector<int64_t> srcDims = { shape_input.GetDim(0), shape_input.GetDim(1) };  
uint32_t srcSize = 1;  
uint32_t srcCurSize = 1;  
for (auto dim : srcDims) {  
    srcSize *= dim;  
}  
uint32_t typeSize = 2;  
auto platformInfo = context->GetPlatformInfo();  
auto ascendcPlatform = platform ascendc::PlatformAscendC platformInfo);  
uint64_t tailSize = 0; // UB剩余空间大小  
ascendingPlatform.GetCoreMemSize platform_ascending::CoreMemType::UB, tailSize);  
uint32_t asinMaxLiveNodeCount = 0;  
uint32_t asinExtraBuf = 0;  
uint32_t acosMaxLiveNodeCount = 0;  
uint32_t acosExtraBuf = 0;  
AscendC::GetAsinTmpBufferFactorSize(typeSize, asinMaxLiveNodeCount, asinExtraBuf);  
AscendC::GetAcosTmpBufferFactorSize(typeSize, acosMaxLiveNodeCount, acosExtraBuf);  
// tmp的大小需要减去UB上调用api接口输入和输出占用的大小  
//该示例中包括Asin接口的输入输出，以及Acos的输入输出，其中Asin接口的输出作为Acos的输入，因此一共需要3份src的空间大小  
auto tmpSize = tailSize - srcSize * typeSize * 3;  
assert(tmpSize >= asinExtraBuf);  
assert(tmpSize >= acosExtraBuf);  
//计算Asin算子单次最大计算元素数量  
if (asinMaxLiveNodeCount != 0) {  
    srcAsinCurSize = (tmpSize - asinExtraBuf) / asinMaxLiveNodeCount / typeSize;  
} else {  
    srcAsinCurSize = srcSize;  
}  
//计算Acos算子单次最大计算元素数量  
if (acosMaxLiveNodeCount != 0) {  
    srcAscosCurSize = (tmpSize - acosExtraBuf) / acosMaxLiveNodeCount / typeSize;  
} else {  
    srcAcosCurSize = srcSize;  
}  
srcCurSize = std::min(srcAsinCurSize, srcAcosCurSize);  
AsinCustomTilingData tiling;  
tiling.set_srcCurSize(srcCurSize); //将单次最大计算元素数量设置为Tiling参数 
```

# 2.5.4 Utils API

Ascend C开发提供了丰富的通用工具类，涵盖标准库、平台信息获取、上下文构建、 运行时编译及日志输出等功能，支持开发者高效实现算子开发与性能优化。 

$\mathsf { C } { + + }$ 标准库API：提供算法、数学函数、容器函数等 $\cdot ( + +$ 标准库函数。 

● 平台信息获取API：提供获取平台信息的功能，比如获取硬件平台的核数等信息。 

RTC API：Ascend C运行时编译库，通过aclrtc接口，在程序运行时，将中间代码 动态编译成目标机器码，提升程序运行性能。 

log API：提供Host侧打印Log的功能。开发者可以在算子的TilingFunc代码中使用 ASC_CPU_LOG_XXX接口来输出相关内容。 

调测接口：SIMT VF调试场景下使用的相关接口。