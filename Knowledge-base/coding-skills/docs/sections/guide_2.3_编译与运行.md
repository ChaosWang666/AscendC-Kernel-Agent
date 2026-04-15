<!-- Source: 算子开发指南.md lines 3104-3881 | Section: 2.3 编译与运行 -->

# 2.3 编译与运行

# 2.3.1 AI Core SIMD 编译

# 2.3.1.1 算子编译简介

本章节介绍的算子编译方法支持开发者通过bisheng命令行和CMake进行手动配置编译 选项，或编写CMake脚本来实现编译。开发者可以将Host侧main.cpp和Device侧 Kernel核函数置于同一实现文件中，以实现异构编译。 

目前，该编译方法仅支持如下型号： 

Atlas 350 加速卡 

Atlas A3 训练系列产品/Atlas A3 推理系列产品 

– Atlas A2 训练系列产品/Atlas A2 推理系列产品 

Atlas 推理系列产品 

异构编译场景中的编程相关约束请参考2.3.1.6 约束说明。 

# 2.3.1.2 通过 bisheng 命令行编译

毕昇编译器是一款专为AI处理器设计的编译器，支持异构编程扩展，可以将用户编写 的昇腾算子代码编译成二进制可执行文件和动态库等形式。毕昇编译器的可执行程序 命名为bisheng，支持x86、aarch64等主机系统，并且原生支持设备侧AI Core架构指 令集编译。通过使用毕昇编译器，用户可以更加高效地进行针对昇腾AI处理器的编程 和开发工作。 

# 入门示例

以下是一个使用毕昇编译器编译静态Shape的add_custom算子入门示例。该示例展示 了如何编写源文件add_custom.asc以及具体的编译命令。通过这个示例，您可以了解 如何使用毕昇编译器进行算子编译。完整样例请参考LINK。 

步骤1 包含头文件。 

在编写算子源文件时，需要包含必要的头文件。 

```c
//头文件
#include "acl/acl.h"
#include "kernel_operator.h" 
```

步骤2 核函数实现。 

核函数支持模板。 

核函数入参支持传入用户自定义的结构体，比如示例中用户自定义的 AddCustomTilingData结构体。 

```javascript
//用户自定义的TilingData结构体struct AddCustomTilingData{uint32_t totalLength; 
```

```cpp
uint32_t tileNum;   
}；   
// Kernel核心实现逻辑，包括搬运，计算等 class KernelAdd { public: aicore__inline KernelAdd() {} //...   
}；   
.global__vector__void add_custom(GM_ADDR x, GM_ADDR y, GM_ADDR z, AddCustomTilingData tiling) //该算子执行时仅启动AI Core上的Vector核 { KernelAdd op; opInit(x,y,z,tiling.totalLength,tilingtileNum); op.Process();   
} 
```

步骤3 Host侧调用函数逻辑，包括内存申请和释放，初始化和去初始化，内核调用符调用核 函数等。 

```txt
// Host侧应用程序需要包含的头文件
#include "acl/acl.h"
// Kernel侧需要包含的头文件
#include "kernel_operator.h"
// 核函数开发部分
...
global __vector__void addcustom(GM_ADDR x, GM_ADDR y, GM_ADDR z, AddCustomTilingData tiling)
{
    KernelAdd op;
    op.Insert(x, y, z, tiling.totalLength, tilingtileNum);
    op.Process();
}
// 通过<<...>>内核调用符调用算子
std::vector<float> kernel_add(std::vector<float>&x, std::vector<float>&y)
{
    ...
} // 计算结果比对
uint32_t VerifyResult(std::vector<float>&output, std::vector<float>&golden)
{
    ...
} // 算子验证主程序
int32_t main(int32_t argc, char *argv[])
{
    constexpr uint32_t totalLength = 8 * 2048;
    constexpr float valueX = 1.2f;
    constexpr float valueY = 2.3f;
    std::vector<float>x(totalLength, valueX);
    std::vector<float>y(totalLength, valueY);
    std::vector<float> output = kernel_add(x, y);
    std::vector<float> golden(totalLength, valueX + valueY);
    return VerifyResult(output, golden);
} 
```

步骤4 采用如下的编译命令进行编译。 

-o demo：指定输出文件名为demo。 

--npu-arch=dav-2201：指定NPU的架构版本为dav-2201。dav-后为NPU架构版 本号，各产品型号对应的架构版本号请通过对应关系表进行查询。 

bisheng add_custom.asc -o demo --npu-arch=dav-2201 

步骤5 执行可执行文件。 

./demo 

----结束 

# 程序的编译与执行

通过毕昇编译器可以将算子源文件（以.asc为后缀）编译为当前平台的可执行文件或算 子动态库，静态库。此外，也支持编译以.cpp/.c等为后缀的C++/C源文件，但需要增 加-x asc编译选项。 

编译生成可执行文件 

#1.编译hello_world.cpp为当前平台可执行文件 

#bisheng[算子源文件]-o[输出产物名称]--npu-arch=[NPU架构版本号]，常见参数顺序与g $\nleftarrow$ 保持一 致。 

bisheng -x asc add_custom.cpp -o add_custom --npu-arch=dav-xxxx 

生成的可执行文件可通过如下方式执行： 

./add_custom 

编译生成算子动态库 

#2.编译add_custom_base.cpp生成算子动态库 

#bisheng-shared[算子源文件]-o[输出产物名称]--npu-arch=[NPU架构版本号] 

#动态库 

bisheng -shared -x asc add_custom_base.cpp -o libadd.so --npu-arch=dav-xxxx 

编译生成算子静态库 

#3.编译addcustom_base.cpp生成算子静态库 

bisheng-lib[算子源文件]-o[输出产物名称]--npu-arch=[NPU架构版本号] 

# 静态库 

bisheng -lib -x asc add_custom_base.cpp -o libadd.a --npu-arch=dav-xxxx 

在命令行编译场景下，可以按需链接需要的库文件，常见的库文件请参考常用的链接 库。编译时会默认链接表2-12中列出的库文件。注意如下例外场景：在使用g++链接 asc代码编译生成的静态库时，需要手动链接默认链接库。 

# 2.3.1.3 常用的编译选项

# 常用的编译选项

常用的编译选项说明如下，全量的编译选项请参考毕昇编译器编译选项。 

<table><tr><td>选项</td><td>是否必需</td><td>说明</td></tr><tr><td>-help</td><td>否</td><td>查看帮助。</td></tr><tr><td>--npu-arch</td><td>是</td><td>编译时指定的AI处理器架构，取值为dav&lt;arch-version&gt;，其中&lt;arch-version&gt;为NPU架构版本号，各产品型号对应的架构版本号请通过对应关系表进行查询。</td></tr><tr><td>--npu-soc</td><td>否</td><td>编译时指定的AI处理器型号,npu-soc和npu-arch同时配置时,优先使能npu-arch。AI处理器的型号请通过如下方式获取:·针对如下产品:在安装AI处理器的服务器执行npu-sminfo命令进行查询,获取Name信息。实际配置值为AscendName,例如Name取值为xxxx,实际配置值为Ascendxxxx。Atlas A2训练系列产品/Atlas A2推理系列产品Atlas 200I/500 A2推理产品Atlas 推理系列产品Atlas 训练系列产品·针对如下产品,在安装AI处理器的服务器执行npu-sminfo -t board -i id -c chip_id命令进行查询,获取Chip Name和NPU Name信息,实际配置值为Chip Name_NPU Name。例如Chip Name取值为Ascendxxx,NPU Name取值为1234,实际配置值为Ascendxxx_1234。其中:-id:设备id,通过npu-sminfo -l命令查出的NPU ID即为设备id。-chip_id:芯片id,通过npu-sminfo -m命令查出的Chip ID即为芯片id。Atlas 350加速卡Atlas A3训练系列产品/Atlas A3推理系列产品</td></tr><tr><td>-x</td><td>否</td><td>指定编译语言。指定为asc时表示Ascend C编程语言。</td></tr><tr><td>-o &lt;file&gt;</td><td>否</td><td>指定输出文件的名称和位置。</td></tr><tr><td>-c</td><td>否</td><td>编译生成目标文件。</td></tr><tr><td>-shared, --shared</td><td>否</td><td>编译生成动态链接库。</td></tr><tr><td>-lib, --ccse-build-static-lib</td><td>否</td><td>编译生成静态链接库。编译器会将Device侧的代码进行编译链接,生成Device侧二进制文件,随后将该文件作为Host侧编译的输入进行编译,最后链接生成静态链接库。</td></tr><tr><td>-g</td><td>否</td><td>编译时增加调试信息。</td></tr><tr><td>--sanitizer</td><td>否</td><td>编译时增加代码正确性校验信息。使用sanitizer选项时，需要同步添加-g选项，且不能在-O0场景下使用。
注意，启用该选项后GlobalTensor默认使能L2Cache，无法通过AscendC::SetL2CacheHint接口设置不使能L2 Cache的模式。</td></tr><tr><td>-fPIC</td><td>否</td><td>告知编译器产生位置无关代码。</td></tr><tr><td>-O</td><td>否</td><td>用于指定编译器的优化级别，当前支持-O3，-O2，-O0。</td></tr><tr><td>--run-mode=sim</td><td>否</td><td>sim模式：链接时用户添加仿真模式对应的实现库，实现代码在仿真模式下运行，可以查看仿真相关日志，方便用户性能调试。</td></tr></table>

# 内置编译宏开关

内置编译宏开关列表如下： 

ASCENDC_DUMP用于控制Dump开关，默认开关打开，开发者调用printf/ DumpTensor/assert后会有信息打印（需要注意直调工程的kernel文件内存在host 函数，如果在host函数内调用了printf接口，也会触发kernel内的printf相关初始化 动作，进而影响kernel的执行性能)；设置为0后，表示开关关闭。示例如下： // 关闭所有算子的printf打印功能 ascendc_compile_definitions(ascendc_kernels_${RUN_MODE} PRIVATE ASCENDC_DUMP=0 

ASCENDC_DEBUG用于控制Ascend C API的调测开关，默认开关关闭；增加该编 译宏后，表示开关打开，此时接口内部的assert校验生效，校验不通过会有assert 日志打屏。开启该功能会对算子实际运行的性能带来一定影响，通常在调测阶段 使用。示例如下： ascendc_compile_definitions(ascendc_kernels_${RUN_MODE} PRIVATE ASCENDC_DEBUG 

当前ASCENDC_DEBUG功能支持的产品型号为： 

Atlas 推理系列产品 

Atlas A2 训练系列产品/Atlas A2 推理系列产品 

ENABLE_CV_COMM_VIA_SSBUF用于控制是否使用SSBuffer以及UB到L1 Buffer 的硬通道，在涉及CV通信（AIC和AIV）或使用数据搬运API时需关注此选项。开 启该选项可以提高相关API的性能或拓展使用更多功能。默认开关关闭；设置为 true后，表示开关打开。示例如下： 

ascendc_compile_definitions(ascendc_kernels_${RUN_MODE} PRIVATE ENABLE_CV_COMM_VIA_SSBUF=true 

仅在Atlas 350 加速卡支持该选项。 

从其它硬件平台移植到此平台的算子，开关默认关闭以保持兼容性。 

在该平台新开发的算子，以下场景需要打开：使用矩阵计算Matmul高阶 API，且使用SetTensorScaleA等接口，这些接口属于Atlas 350 加速卡新增的 

功能，其内部实现使用了SSBuffer；使用DataCopy接口从UB拷贝数据到L1 Buffer。 

● NO_OVERLAP_IN_MULTI_REPEAT 

该编译选项用于在没有地址重叠的情况下移除不必要的内存同步指令，以提升性 能。针对Atlas 350 加速卡，使用基础API的高维切分计算API时，默认会插入内存 同步指令以确保在地址重叠等复杂场景下的数据正确性，但这些同步指令会带来 性能开销。在追求极致性能的场景下，如果您可以确定代码在任何情况下都不会 发生内存重叠，可以使用此选项。 

# 2.3.1.4 通过 CMake 编译

项目中可以使用CMake来更简便地使用毕昇编译器编译Ascend C算子，生成可执行文 件、动态库、静态库或二进制文件。 

以下是CMake脚本的示例及其核心步骤说明： 

```txt
# 1、findpackage(ASC)是CMake中用于查找和配置Ascend C编译工具链的命令
findpackage(ASC)
# 2、指定项目支持的语言包括ASC和CXX, ASC表示支持使用毕昇编译器对Ascend C编程语言进行编译
project(kernel_samples LANGUAGES ASC CXX)
# 3、使用CMake接口编译可执行文件、动态库、静态库、二进制文件
add_executable demo
add_custom.asc
)#......
target.compile-optionsdemo PRIVATE
# --npu-arch用于指定NPU的架构版本,dav-后为架构版本号,各产品型号对应的架构版本号请通过对应关系表进行查询。
# <COMPILE_LANGUAGE:ASC>:表明该编译选项仅对语言ASC生效
$<$<COMPILE_LANGUAGE:ASC>: --npu-arch=dav-2201> 
```

以下是动态库、静态库编译示例，同时展示如何将源文件切换为用语言ASC编译： 

编译.cpp文件生成动态库 

#将.cpp文件置为ASC属性，启用Ascend C语言进行编译  
set_source_files.properties( add_custom_base.cpp sub_custom_base.cpp PROPERTIES LANGUAGE ASC )  
add_library(kernel_lib SHARED add_custom_base.cpp sub Himself  
target_generate_options(kernel_lib PRIVATE \ $<\$ <COMPILE_LANGUAGE:ASC>:--npu-arch=dav-2201>   
)  
add_executabledemo main.cpp   
）  
target_linklibrariesdemo PRIVATE kernel_lib 

编译.asc文件生成静态库 

```txt
#.asc文件会默认启用Ascend C语言进行编译，不需要通过set_source_files_propertyson进行设置  
add_library(kernel_libSTATIC  
    addcustom_base.asc  
    subcustom_base.asc 
```

```makefile
target.compile-options(kernel_lib PRIVATE
$$<$$<COMPILE(Language:ASC>: --npu-arch=dav-2201>
)
add_executable demo
main.cpp
)
target_linklibrariesdemo PRIVATE
kernel_lib 
```

下文列出了使用CMake编译时常用的链接库、以及默认链接库。 


表 2-11 常用的链接库（在使用高阶 API 时，必须链接以下库，因为这些库是高阶 API 功能所依赖的。在其他场景下，可以根据具体需求选择是否链接这些库。）


<table><tr><td>使用场景</td><td>名称</td></tr><tr><td rowspan="3">使用高阶API相关的Tiling接口时需要同时链接。</td><td>libtiling_api.a</td></tr><tr><td>libregister.so</td></tr><tr><td>libgraph_base.so</td></tr><tr><td>使用PlatformAscendC相关硬件平台信息接口时需要链接。</td><td>libplatform.so</td></tr></table>


表2-12 默认链接库


<table><tr><td>名称</td><td>作用描述</td></tr><tr><td>libascendc_runti me.a</td><td>Ascend C算子参数等组装库。</td></tr><tr><td>libruntime.so</td><td>Runtime运行库。</td></tr><tr><td>libprofapi.so</td><td>Ascend C算子运行性能数据采集库。</td></tr><tr><td>libunified_dlog.so</td><td>CANN日志收集库。</td></tr><tr><td>libmmpa.so</td><td>CANN系统接口库。</td></tr><tr><td>libascend_dump.s o</td><td>CANN维测信息库。</td></tr><tr><td>libc(sec.so</td><td>CANN安全函数库。</td></tr><tr><td>liberrormanager. so</td><td>CANN错误信息管理库。</td></tr><tr><td>libascendcl.so</td><td>acl相关接口库。</td></tr></table>

# 2.3.1.5 RTC

RTC是Ascend C运行时编译库，通过aclrtc接口，在程序运行时，将中间代码动态编译 成目标机器码，提升程序运行性能。 

运行时编译库提供以下核心接口： 

aclrtcCreateProg：根据输入参数（字符串形式表达的Ascend C源代码等）创建 aclrtcProg程序实例。 

aclrtcCompileProg：编译给定的程序，支持用户自定义编译选项，比如指定NPU 架构版本号：--npu-arch=dav-2201。支持的编译选项可以参考毕昇编译器编译选 项。 

aclrtcGetBinDataSize：获取编译后的Device侧二进制数据的大小。 

aclrtcGetBinData：获取编译后的Device侧二进制数据。 

aclrtcDestroyProg：在编译和执行过程结束后，销毁给定的程序。 

编译完成后需要调用如下接口完成（仅列出核心接口）Kernel加载与执行。完整流程 和详细接口说明请参考“Kernel加载与执行”章节。 

1. 通过aclrtBinaryLoadFromData接口解析由aclrtcGetBinData接口获取的算子二进 制数据。 

2. 获取核函数句柄并根据核函数句柄操作其参数列表，相关接口包括 aclrtBinaryGetFunction（获取核函数句柄）、aclrtKernelArgsInit（初始化参数 列表）、aclrtKernelArgsAppend（追加拷贝用户设置的参数值如xDevice, yDevice, zDevice）等。 

3. 调用aclrtLaunchKernelWithConfig接口，启动对应算子的计算任务。 

如下是一个使用aclrtc接口编译并运行Add自定义算子的完整样例： 

include<iostream>   
#include <fstream>   
#include <vector>   
#include"acl/acl.h"   
//使用aclrtc接口需要包含的头文件   
#include"acl/acl_rt.compile.h"   
#define CHECK_ACL(x) do{ aclError_ret=x; if(_ret!=ACL_ERROR_NONE){ std::cerr<<FILE<<:":"<<LINE<<"aclError:"<<_ret<<std:end; } }while(0);   
int main(int argc,char\*argv[]) { //aclrtc part const char \*src $=$ R""("   
#include "kernel_operator.h" constexpr int32_t TOTAL_LENGTH $= 8$ *1024; //total length of data constexpr int32_t USE_CORE_NUM $= 8$ ; //num of core used constexpr int32_t BLOCK_LENGTH $=$ TOTAL_LENGTH /USE_CORE_NUM; //length computed of each core constexpr int32_t TILE_NUM $= 8$ ; // split data into 8 tiles for each core constexpr int32_t BUFFER_NUM $= 2$ ; //tensor num for each queue constexpr int32_t TILE_LENGTH $=$ BLOCK_LENGTH / TILE_NUM / BUFFER_NUM; //separate to 2 parts, due to double buffer   
class KernelAdd{ public: __aicore__inline KernelAdd() { __aicore__inline void Init(GM_ADDRx,GM_ADDRy,GM_ADDRz) { xGm.SetGlobalBuffer((gm_float\*)x+BLOCK_LENGTH\*AscendC::GetBlockIdx(),BLOCK_LENGTH); yGm.SetGlobalBuffer((gm_float\*)y+BLOCK_LENGTH\*AscendC::GetBlockIdx(),BLOCK_LENGTH); zGm.SetGlobalBuffer((gm_float\*)z+BLOCK_LENGTH\*AscendC::GetBlockIdx(),BLOCK_LENGTH); pipeInitBuffer(inQueueX,BUFFER_NUM,TILE_LENGTH\*sizeof(float)); pipeInitBuffer(inQueueY,BUFFER_NUM,TILE_LENGTH\*sizeof(float)); 

```cpp
pipe InitBuffer(outQueueZ, BUFFER_NUM, TILE_LENGTH * sizeof(float));  
}  
__aicore__inline void Process()  
{int32_t loopCount = TILE_NUM * BUFFER_NUM;for (int32_t i = 0; i < loopCount; i++) {Copyln(i);Compute(i);CopyOut(i);}  
}  
}  
private:  
__aicore__inline void Copyln(int32_t progress)  
{AscendC::LocalTensor<float> xLocal = inQueueX AllocTensor<float>();AscendC::LocalTensor<float> yLocal = inQueueY AllocTensor<float>();AscendC::DataCopy(xLocal, xGm[progress * TILE_LENGTH], TILE_LENGTH);AscendC::DataCopy(yLocal, yGm[progress * TILE_LENGTH], TILE_LENGTH);inQueueX.EnQue(xLocal);inQueueY.EnQue(yLocal);}  
}  
__aicore__inline void Compute(int32_t progress)  
{AscendC::LocalTensor<float> xLocal = inQueueX.DeQue<float>();AscendC::LocalTensor<float> yLocal = inQueueY.DeQue<float>();AscendC::LocalTensor<float> zLocal = outQueueZ AllocTensor<float>();AscendC::Add(zLocal, xLocal, yLocal, TILE_LENGTH);outQueueZ.EnQue<float>(zLocal);inQueueX.FreeTensor(xLocal);inQueueY.FreeTensor(yLocal);}  
}  
__aicore__inline void CopyOut(int32_t progress)  
{AscendC::LocalTensor<float> zLocal = outQueueZ.DeQue<float>();AscendC::DataCopy(zGm[progress * TILE_LENGTH], zLocal, TILE_LENGTH);outQueueZ.FreeTensor(zLocal);}  
}  
private:  
AscendC::TPipe pipe;AscendC::TQue<TPosition::VECIN, BUFFER_NUM> inQueueX, inQueueY;AscendC::TQue<TPosition::VECOUT, BUFFER_NUM> outQueueZ;AscendC::GlobalTensor<float>xGm;AscendC::GlobalTensor<float>yGm;AscendC::GlobalTensor<float> zGm;  
};extern "C" __global __aicore__void addcustom(GM_ADDR x, GM_ADDR y, GM_ADDR z)  
{KERNEL_TASK_TYPE_DEFAULT(Kernel_TYPE_AIV_ONLY);KernelAdd op;op.Linit(x, y, z);op.Process();}  
}""";//aclrtc流程，src为用户Device侧源码，通过aclrtcCreateProg来创建编译程序aclrtcProg prog;CHECK_ACL(aclrtcCreateProg(&prog, src, "add_custom", 0, nullptr, nullptr));//aclrtc流程，传入毕昇编译器的编译选项，调用aclrtcCompileProg进行编译const char *options[] = {--npu-arch=dav-2201",};int numOptions = sizeof(options) / sizeof(options[0]);CHECK_ACL(aclrtcCompileProg(prog, numOptions, options));//aclrtc流程，获取Device侧二进制内容和大小size_t binDataSizeRet; 
```

```cpp
CHECK_ACL(aclrtcGetBinDataSize(prog, &binDataSizeRet)); std::vector<char> deviceELF.binDataSizeRet); CHECK_ACL(aclrtcGetBinData(prog, deviceELF.data())); const char *funcName = "add_custom"; // -- aclrt part uint32_t numBlocks = 8; size_t inputByteSize = 8 * 1024 * sizeof uint32_t); size_t outputByteSize = 8 * 1024 * sizeof uint32_t); CHECK_ACL(aclInit(nullptr)); int32_t deviceld = 0; CHECK_ACL(aclrtSetDevice(deviceld)); aclrtStream stream = nullptr; CHECK_ACL(aclrtCreateStream(&stream)); uint8_t *xHost, *yHost, *zHost; uint8_t *xDevice, *yDevice, *zDevice; CHECK_ACL(aclrtMallocHost((void **)(&xHost), inputByteSize)); CHECK_ACL(aclrtMallocHost((void **)(&yHost), inputByteSize)); CHECK_ACL(aclrtMallocHost((void **)(&zHost), outputByteSize)); CHECK_ACL(aclrtMalloc((void **)&yDevice, inputByteSize, ACL_MEM_MALLOC Huge_FIRST)); CHECK_ACL(aclrtMalloc((void **)&zDevice, outputByteSize, ACL_MEM_MALLOC Huge_FIRST)); CHECK_ACL(aclrtMemcpy(xDevice, inputByteSize, xHost, inputByteSize, ACL_MEMPY_HOST_TO_DEVICE)); CHECK_ACL(aclrtMemcpy(yDevice, inputByteSize, yHost, inputByteSize, ACL_MEMPY_HOST_TO_DEVICE)); aclrtBinHandle binHandle = nullptr; aclrtBinaryLoadOptions loadOption; loadOption.numOpt = 1; aclrtBinaryLoadOption option; option.type = ACL_RT_BINARY_LOAD_OPT_LAZY Madness; option.value magic = ACL_RT_BINARY Madness ELF_VECTOR_CORE; //设置magic值，表示算子在Vector Core上执行 loadOption(options = &option; CHECK_ACL(aclrtBinaryLoadFromData(deviceELF.data(), binDataSizeRet, &loadOption, &binHandle)); aclrtFuncHandle funcHandle = nullptr; CHECK_ACL(aclrtBinaryGetFunction(binHandle, funcName, &funcHandle)); aclrtArgsHandle argsHandle = nullptr; aclrtParamHandle paramHandle = nullptr; CHECK_ACL(aclrtKernelArgslInit FUNCHandle, &argsHandle); CHECK_ACL(aclrtKernelArgsAppend(argsHandle, (void **)&xDevice, sizeof(void_t), &paramHandle); CHECK_ACL(aclrtKernelArgsAppend(argsHandle, (void **)&yDevice, sizeof(void_t), &paramHandle); CHECK_ACL(aclrtKernelArgsAppend(argsHandle, (void **)&zDevice, sizeof(void_t), &paramHandle); CHECK_ACL(aclrtKernelArgsFinalize(argsHandle)); //核函数入口 CHECK_ACL(aclrtLaunchKernelWithConfig FUNCHandle, numBlocks, stream, nullptr, argsHandle, nullptr); CHECK_ACL(aclrtSynchronizeStream(stream); CHECK_ACL(aclrtMemcpy(zHost, outputByteSize, zDevice, outputByteSize, ACL_MEMCPY_DEVICE_TO_HOST)); //获取日志大小并得到日志字符串 size_t logSize; CHECK_ACL(aclrtcGetCompileLogSize(prog, &logSize)); char* log = (char*)malloc(logSize); CHECK_ACL(aclrtcGetCompileLog(prog, log)); //将日志字符串存到文件中 /* std::ofstream logFile("compile.log"); if (logFile.is_open()) { logFile << log << std::endl; logFile.close(); std::cout << "already write to compile.log!" << std::endl; } 
```

```txt
free(log);  
CHECK_ACL(aclrBinaryUnLoad.binHandle));  
CHECK_ACL(aclrFree(xDevice));  
CHECK_ACL(aclrFree(yDevice));  
CHECK_ACL(aclrFree(zDevice));  
CHECK_ACL(aclrFreeHost(xHost));  
CHECK_ACL(aclrFreeHost(yHost));  
CHECK_ACL(aclrFreeHost(zHost));  
CHECK_ACL(aclrDestroyStream(stream));  
CHECK_ACL(aclrResetDevice(deviceld));  
CHECK_ACL(aclFinalize());  
//编译和运行均已结束，销毁程序  
CHECK_ACL(acltrcDestroyProg(&prog));  
return 0; 
```

编译命令如下，编译时需要设置-I路径为${INSTALL_DIR}/include，用于找到aclrtc相 关头文件，并需要链接alc_rtc动态库。 

```shell
g++ add_custom.cpp -l${INSTALL_DIR}/include -L${INSTALL_DIR}/lib64 -lascendcl -lacl_rtc -o main 
```

${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。以root用户安装为例，安 装后文件默认存储路径为：/usr/local/Ascend/cann。 

# 2.3.1.6 约束说明

在同一个编译单元，若存在多个核函数，暂不支持自动推导Kernel类型，需要开 发者手动设置Kernel类型。 

特别地，针对如下型号，无论是否是同一个编译单元多个核函数的场景，均 不支持在开发者未设置Kernel类型时进行自动推导。建议开发者手动设置 Kernel类型。 

Atlas 350 加速卡 

Atlas 推理系列产品 

针对Atlas 推理系列产品 ，暂不支持设置Kernel类型为 KERNEL_TYPE_MIX_VECTOR_CORE。 

KERNEL_TASK_TYPE_DEFAULT接口需在核函数中进行调用。 

纯Scalar算子无法实现自动推导 需手动标记Kernel函数类型，推荐设置为纯Vector类型，添加__vector__ attribute 进行标记： 

```cpp
global __vector __aicore __void func0(_gm__ uint8* Addr) {
    Addr[1] = Addr[0];
    AscendC::printf("Hello world");
} 
```

Kernel函数不支持特化 使用特化核函数调用，目前依然会使用主模板核函数。 

include"kernel_operator.h" #include"acl/acl.h" //测试_mix $(x,y)$ 中x，y由模板参数控制是否可行 template<int32_t cube,int32_t vec> _mix $\mathbf{\Pi}^{\mathrm{~\text{一}}}$ cube,vec）_global_void hello_world() { ifASCEND_IS_AIC{ AscendC::printf("Hello World AIC with cube,vec !!!\n"); }else{ 

```c
AscendC::printf("Hello World AIV with cube, vec !!!\n");   
}   
}   
// 特化写法，不支持 template<> _mix_(1,0) _global_ void hello_world<1,0>(） { if ASCEND_IS_AIC{ AscendC::printf("1:0 Hello World AIC with vec !!!\n"); } else{ AscendC::printf("1:0 Hello World AIV with vec !!!\n"); }   
}   
int32_t main(int argc, char const \*argv[]) { uint8_t *aHost; uint8_t \*aDevice; aclInit(nullptr); int32_t deviceld = 0; aclrtSetDevice(deviceld); aclrtStream stream \(=\) nullptr; aclrtCreateStream(&stream); aclrtMallocHost((void **)(&aHost), sizeof(aui32_t)); aclrtMalloc((void **)&aDevice, sizeof(aui32_t), ACL_MEM_MALLOC Huge_FIRST); \*aHost = 12; aclrtMemcpy(aDevice, sizeof(aui32_t), aHost, sizeof(aui32_t), ACL_MEMPY_HOST_TO_DEVICE); constexpr uint32_t numBlocks \(= 8\) ： hello_world<1, \(2 > <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   < 10; hello_world<1, \(0 > <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   <   < 10; aclrtSynchronizeStream streamline>>(); aclrtSynchronizeStream streamline>>(); aclrtFree(aDevice); aclrtFreeHost(aHost); aclrtDestroyStream streamline); aclrtResetDevice(deviceld); aclFinalize(); return 0; 
```

bfloat16_t等数据类型在Host侧不支持，使用这些数据类型时，Host和Device不 能写在同一个实现文件里。Host侧不支持的数据类型如下： 

Atlas 350 加速卡：bfloat16_t、hifloat8_t、fp8_e5m2_t、fp8_e4m3fn_t、 fp8_e8m0_t、fp4x2_e2m1_t、fp4x2_e1m2_t、int4x2_t。 

Atlas A2 训练系列产品/Atlas A2 推理系列产品：bfloat16_t。 

Atlas A3 训练系列产品/Atlas A3 推理系列产品：bfloat16_t。 

不支持可变参数模板和可变参数函数 

```txt
// 不支持以下写法  
template<typename...Args> //Args是一个“类型参数包”  
void func(Args...args); //args是一个“函数参数包” 
```

不支持#line 预处理 

```txt
// 不支持以下写法  
#line number // 更改行号  
#line number "filename" // 更改文件名 
```

# 2.3.2 AI Core SIMT 编译

# 2.3.2.1 算子编译简介

# 说明

当前暂不支持本章节介绍的编译方式，该方式将在下个版本支持，请关注后续发布版本。 

本章节介绍的SIMT编程场景算子编译方法，支持开发者通过bisheng命令行或编写 CMake脚本来实现编译。开发者可以将Host侧调用代码和Device侧Kernel核函数置于 同一实现文件中，以实现异构编译。 

目前，该编译方法仅支持如下型号： 

Atlas 350 加速卡 

异构编译场景中的编程相关约束请参考2.3.2.5 约束说明。 

# 2.3.2.2 通过 bisheng 命令行编译

毕昇编译器是一款专为AI处理器设计的编译器，支持异构编程扩展，可以将用户编写 的昇腾算子代码编译成二进制可执行文件和动态库等形式。毕昇编译器的可执行程序 命名为bisheng，支持x86、aarch64等主机系统，并且原生支持设备侧AI Core架构指 令集编译。通过使用毕昇编译器，用户可以更加高效地进行针对昇腾AI处理器的编程 和开发工作。 

# 入门示例

以下是一个使用毕昇编译器编译的SIMT编程实现的Add算子入门示例。该示例展示了 如何编写源文件add.asc以及具体的编译命令。通过这个示例，您可以了解如何使用毕 昇编译器进行SIMT算子编译。 

步骤1 包含头文件。 

在编写算子源文件时，需要包含必要的头文件。 

```cpp
//头文件  
#include"acl/acl.h”//调用核函数相关接口头文件  
#include"asc_simt.h”//核函数内调用SIMTAPI接口的头文件 
```

步骤2 核函数实现。 

核函数入参当前仅支持基础数据类型及其指针类型，核函数具体语法及约束说明参见 2.2.4.4 核函数。 

global__void addCustom(float\*x, float\*y, float\*z, uint64_t total_length)   
{ // Calculate global thread ID int32_t idx $=$ blockIdx.x\*blockDim.x $^+$ threadIdx.x; // Maps to the row index of output tensor if(idx $\Rightarrow$ total_length){ return; } z[idx] $=$ x[idx] $^+$ y[idx]; 

步骤3 Host侧调用函数逻辑，包括内存申请和释放，初始化和去初始化，内核调用符调用核 函数等。 

```txt
// Host侧应用程序需要包含的头文件
#include "acl/acl.h"
// 核函数实现
global _ void addcustom(float* x, float* y, float* z, uint64_t total_length)
{
    ...
} 
```

```cpp
//通过<<...>>内核调用符调用算子  
std::vector<float>add(std::vector<float>& x, std::vector<float>& y)  
{  
    // Call kernel funtion with <<...>>  
    add_custom<<...>>((...));  
}  
//计算结果比对  
uint32_t verify_result(std::vector<float>& output, std::vector<float>& golden)  
{  
    ...  
}  
//算子验证主程序  
int32_t main(int32_t argc, char *argv[])  
{  
    constexpr uint32_t in_shape = 48 * 256;  
    std::vector<float> x(in_shape);  
    for (uint32_t i = 0; i < in_shape; i++) {  
        x[i] = i * 1.1f;  
    }  
    std::vector<float> y(in_shape);  
    for (uint32_t i = 0; i < in_shape; i++) {  
        y[i] = i + 3.4f;  
    }  
    std::vector<float> golden(in_shape);  
    for (uint32_t i = 0; i < in_shape; i++) {  
        golden[i] = x[i] + y[i];  
    }  
    std::vector<float> output = add(x, y);  
    return verify_result(output, golden); 
```

步骤4 采用如下的编译命令进行编译。 

```batch
bisheng -x asc add.asc -o demo --npu-arch=dav-3510 --enable-simt 
```

-x asc：-x指定编译语言，asc表示编程语言为Ascend C。 

-o demo：指定输出文件名为demo。 

--npu-arch=dav-3510：指定NPU的架构版本为dav-3510。dav-后为NPU架构版 本号，各产品型号对应的架构版本号请通过对应关系表进行查询。 

--enable-simt： SIMT编译的固定选项。 

步骤5 执行可执行文件。 

```txt
./demo 
```

----结束 

# 程序的编译与执行

通过毕昇编译器可以将算子源文件（以.asc为后缀）编译为当前平台的可执行文件。此 外，也支持使用-x asc编译选项编译以.cpp/.c等为后缀的C++/C源文件。 

#bisheng-xasc[算子源文件]-o[输出产物名称]--npu-arch=[NPU架构版本号]--enable-simt，常见参数顺序 与g++保持一致。 

# ${ \mathsf { C } } { + } { + }$ 源文件 

bisheng -x asc add_custom.cpp -o add_custom --npu-arch=dav-xxxx --enable-simt # 后缀为.asc的算子源文件 

bisheng -x asc add_custom.asc -o add_custom --npu-arch=dav-xxxx --enable-simt 

生成的可执行文件可通过如下方式执行： 

```txt
./add(custom 
```

在命令行编译场景下，可以按需链接需要的库文件，编译时会默认链接表2-13中列出 的库文件。 

# 2.3.2.3 常用的编译选项

常用的编译选项说明如下，全量的编译选项请参考毕昇编译器编译选项。 

<table><tr><td>选项</td><td>是否必需</td><td>说明</td></tr><tr><td>-help</td><td>否</td><td>查看帮助。</td></tr><tr><td>--npu-arch</td><td>是</td><td>编译时指定的AI处理器架构，取值为dav&lt;arch-version&gt;，其中&lt;arch-version&gt;为NPU架构版本号，各产品型号对应的架构版本号请通过对应关系表进行查询。</td></tr><tr><td>-x</td><td>否</td><td>指定编译语言。
指定为asc时表示Ascend C编程语言。</td></tr><tr><td>-o &lt;file&gt;</td><td>否</td><td>指定输出文件的名称和位置。</td></tr><tr><td>-c</td><td>否</td><td>编译生成目标文件。</td></tr><tr><td>--enable-simt</td><td>是</td><td>指定SIMT编程场景。</td></tr></table>

# 2.3.2.4 通过 CMake 编译

项目中可以使用CMake来更简便地使用毕昇编译器编译Ascend C SIMT算子，生成可 执行文件。 

以下是CMake脚本的示例及其核心步骤说明： 

```txt
# 1、findpackage(ASC)是CMake中用于查找和配置Ascend C编译工具链的命令  
findpackage(ASC)  
# 2、指定项目支持的语言包括ASC和CXX，ASC表示支持使用毕昇编译器对Ascend C编程语言进行编译  
project(kernel_samples LANGUAGES ASC CXX)  
# 3、使用CMake接口编译可执行文件  
add_executable demo  
add_custom.asc  
）  
#....  
target.compile-optionsdemo PRIVATE  
# --npu-arch用于指定NPU的架构版本，dav-后为架构版本号  
# <COMPILE_LANGUAGE:ASC>:表明该编译选项仅对语言ASC生效  
$<<COMPILE_LANGUAGE:ASC>: --npu-arch=dav-3510>  
# 开启SIMT编程模型的编译功能  
--enable-simt  
） 
```

下文列出了使用CMake编译时默认链接库。 


表 2-13 默认链接库


<table><tr><td>名称</td><td>作用描述</td></tr><tr><td>libascendc_runti me.a</td><td>Ascend C算子参数等组装库。</td></tr><tr><td>libruntime.so</td><td>Runtime运行库。</td></tr><tr><td>libprofapi.so</td><td>Ascend C算子运行性能数据采集库。</td></tr><tr><td>libunified_dlog.so</td><td>CANN日志收集库。</td></tr><tr><td>libmmpa.so</td><td>CANN系统接口库。</td></tr><tr><td>libascend_dump.s o</td><td>CANN维测信息库。</td></tr><tr><td>libc(sec.so</td><td>CANN安全函数库。</td></tr><tr><td>liberrormanager. so</td><td>CANN错误信息管理库。</td></tr><tr><td>libascendcl.so</td><td>acl相关接口库。</td></tr></table>

# 2.3.2.5 约束说明

bfloat16_t等数据类型在Host侧不支持，使用这些数据类型时，Host和Device不 能写在同一个实现文件里。Host侧不支持的数据类型如下： 

Atlas 350 加速卡：bfloat16_t、hifloat8_t、fp8_e5m2_t、fp8_e4m3fn_t、 fp8_e8m0_t、fp4x2_e2m1_t、fp4x2_e1m2_t、int4x2_t。 

不支持可变参数模板和可变参数函数 

// 不支持以下写法 template <typename... Args> // Args 是一个“类型参数包” void func(Args... args); // args 是一个“函数参数包” 

不支持#line 预处理 

// 不支持以下写法 #line number // 更改行号 #line number "filename" // 更改文件名 

# 2.3.3 AI CPU 算子编译

# 通过 bisheng 命令行编译

下文基于一个Hello World打印样例来讲解如何通过bisheng命令行编译AI CPU算子。 

hello_world.aicpu文件内容如下： 

```cpp
include"aicpu_api.h" global_aicpu_uint32_t hello_world(void\*args) { AscendC::printf("Hello World!!\n"); return 0; } 
```

Host侧使用内核调用符 $< < < \ldots > > >$ 进行AI CPU算子的调用， main.asc示例代码如下： 

include"acl/acl.h"   
struct KernelArgs{ int mode;   
};   
extern global aicpu uint32_t hello_world(void\*args);   
int32_t main(int argc, char const \*argv[])   
{ aclInit(nullptr); int32_t deviceld $= 0$ . aclrtSetDevice(deviceld); aclrtStream stream $=$ nullptr; aclrtCreateStream(&stream); struct KernelArgs args $= \{0\}$ constexpr uint32_t numBlocks $= 1$ . hello_world<<numBlocks, nullptr, stream>>&args,sizeof(KernelArgs)); aclrtSynchronizeStream(stream); aclrtDestroyStream(stream); aclrtResetDevice(deviceld); aclFinalize(); return 0; 

开发者可以使用bisheng命令行将hello_world.aicpu与main.asc分别编译成.o，再链接 成为可执行文件，编译命令如下： 

编译hello_world.aicpu时，通过-I指定依赖头文件所在路径；通过--cce-aicpulaicpu_api为Device链接依赖的库libaicpu_api.a，通过--cce-aicpu-L指定 libaicpu_api.a的库路径。 

编译main.asc时，通过--npu-arch编译选项指定对应的架构版本号。 

${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。以root用户安装为例，安 装后文件默认存储路径为：/usr/local/Ascend/cann。 

```powershell
$bisheng -O2 hello_world.aicpu --cce-aicpu-L$\{INSTALL_DIR\}/lib64/device/lib64 --cce-aicpu-laicpu_api -l${INSTALL_DIR}/include/ascendc/aicpu_api-c-o hello_world.aicpu.o
# --npu-arch用于指定NPU的架构版本,dav-后为架构版本号,各产品型号对应的架构版本号请通过对应关系表进行查询。
$bisheng --npu-arch=dav-2201 main.asc-c-o main.asc.o
$bisheng hello_world.aicpu.o main.asc.o -o demo 
```

上文我们通过一个入门示例介绍了使用bisheng命令行编译生成可执行文件的示例。除 此之外，使用bisheng命令行也支持编译生成AI CPU算子的动态库与静态库，用户可在 asc代码中通过内核调用符<<<...>>>调用AI CPU算子的核函数，并在编译asc代码源文 件生成可执行文件的时候，链接AI CPU动态库或者静态库，注意：若单独编译AI CPU 算子代码生成动态库、静态库时，需要手动链接表2-12。 

编译生成算子动态库 

```shell
编译test_aicpu.cpp生成算子动态库  
# -lxxx表示默认链接库  
# bisheng -shared -x aicpu test_aicpu.cpp -o libtest_aicpu.so -lxxx ... 
```

编译生成算子静态库 

```shell
编译test_aicpu.cpp生成算子静态库  
# -lxxx表示默认链接库  
# bisheng -lib -x aicpu test_aicpu.cpp -o libtest_aicpu.a -lxxx ... 
```

# AI CPU 算子常用编译选项

AI CPU算子常用的编译选项说明如下： 

<table><tr><td>选项</td><td>是否必需</td><td>说明</td></tr><tr><td>-help</td><td>否</td><td>查看帮助。</td></tr><tr><td>-x</td><td>否</td><td>指定编译语言。
指定为aicpu时表示AI CPU算子编程语言。</td></tr><tr><td>-o &lt;file&gt;</td><td>否</td><td>指定输出文件的名称和位置。</td></tr><tr><td>-c</td><td>否</td><td>编译生成目标文件。</td></tr><tr><td>-shared, --shared</td><td>否</td><td>编译生成动态链接库。</td></tr><tr><td>-lib</td><td>否</td><td>编译生成静态链接库。</td></tr><tr><td>-g</td><td>否</td><td>编译时增加调试信息。</td></tr><tr><td>-fPIC</td><td>否</td><td>告知编译器产生位置无关代码。</td></tr><tr><td>-O</td><td>否</td><td>用于指定编译器的优化级别，当前支持-O3，-O2，-O0。</td></tr><tr><td>--cee-aicpu-L</td><td>否</td><td>指定AI CPU Device依赖的库路径。</td></tr><tr><td>--cee-aicpu-l</td><td>否</td><td>指定AI CPU Device依赖的库。</td></tr></table>

# 通过 CMake 编译

项目中可以使用CMake来更简便地使用毕昇编译器编译AI CPU算子，生成可执行文 件、动态库、静态库或二进制文件。 

仍以通过bisheng命令行编译中介绍的Hello World打印样例为例，除了代码实现文 件，还需要在工程目录下准备一个CMakeLists.txt。 

```batch
hello_world.aicpu // AI CPU算子核函数定义  
main.asc // AI CPU算子核函数调用  
CMakeLists.txt 
```

CMakeLists.txt内容如下： 

```cmake
cmake_minimum_required(VERSION 3.16)  
#1、findpackage()是CMake中用于查找和配置Ascend C编译工具链的命令  
findpackage(ASC REQUIRED)  
findpackage(AICPU REQUIRED)  
#2、指定项目支持的语言包括ASC、AICPU和CXX，ASC表示支持使用毕昇编译器对Ascend C编程语言进行编译，AI CPU表示支持使用毕昇编译器对AI CPU算子进行编译  
project(kernel_samples LANGUAGES ASC AICPU CXX)  
#3、使用CMake接口编译可执行文件  
add_executable demo hello_world.aicpu main.asc)  
#4、由于存在ASC与AI CPU语言，需要指定链接器  
set_target_propertyssdemo PROPERTIES LINKER LANGUAGE ASC) #指定链接使用语言  
target.compile-optionsdemo PRIVATE #--npu-arch用于指定NPU的架构版本，dav-后为架构版本号，各产品型号对应的架构版本号请通过对应关系 
```

表进行查询。 

# <COMPILE_LANGUAGE:ASC>:表明该编译选项仅对语言ASC生效 

$<$<COMPILE_LANGUAGE:ASC>:--npu-arch=dav-2201> 

如果需要CMake编译编译生成动态库、静态库，下面提供了更详细具体的编译示例： 

# 编译.cpp文件生成动态库

```txt
#将.cpp文件置为ASC属性，启用Ascend C语言进行编译  
set_source_files_propertyss( add_custom_base.cpp sub_custom_base.cpp PROPERTIES LANGUAGE ASC)   
#将.cpp文件置为AICPU属性，支持AI CPU算子编译  
set_source_files_propertyss( aicpu_kernel.cpp PROPERTIES LANGUAGE AICPU )  
add_library(kernel_lib SHARED add_custom_base.cpp sub_custom_base.cpp aicpu_kernel.cpp # 支持AI CPU算子与AI Core算子一起打包为动态库  
target.compile_options(kernel_lib PRIVATE \\(<\\<COMPILE_LANGUAGE:ASC>:\\--npu-arch=dav-2201>   
# AI CPU算子编译时，需要手动链接以下依赖库（若指定链接语言为ASC时，不需要手动链接以下库） target_linklibraries(kernel_lib PRIVATE ascendc这段时间 profapi unified_dlog ascendcl runtime c_sec mmpa errormanager ascend_dump   
)   
add_executabledemo main.asc   
target_linklibraries demo PRIVATE kernel_lib 
```

# 编译.asc文件与.aicpu文件生成静态库

#.asc文件会默认启用Ascend C语言进行编译，.aicpu文件会默认启用AICPU语言进行编译，不需要通过  
set_source_files_propertyson进行设置  
add_library(kernel_libSTATIC  
addcustom_base.asc  
subcustom_base.asc  
aicpu_kernel.aicpu #可支持AI CPU算子与AI Core算子一起打包为静态库  
）  
target.compile-options(kernel_libPRIVATE $< <   <   \mathrm{COMPILE\_L A N G U A G E: A S C} > : - - n p u - a r c h = d a v - 2 2 0 1>$ ）  
add_executabledemo  
main.asc  
）  
target_linklibrariesdemo PRIVATE  
kernel_lib  
） 

下文列出了使用CMake编译时常用的变量配置说明、常用的链接库。 


表 2-14 常用的变量配置说明


<table><tr><td>变量</td><td>配置说明</td></tr><tr><td>CMAKE-built_TYPE</td><td>编译模式选项,可配置为:·“Release”,Release版本,不包含调试信息,编译最终发布的版本。·“Debug”,Debug版本,包含调试信息,便于开发者开发和调试。</td></tr><tr><td>CMAKEInstall_PREFIX</td><td>用于指定CMake执行install时,安装的路径前缀,执行install后编译产物(ascending bookstore中指定的target以及对应的头文件)会安装在该路径下。默认路径为当前目录的out目录下。</td></tr><tr><td>CMAKE_CXX_COMPILER-LaUNCHER</td><td>用于配置C++语言编译器(如g++)、毕昇编译器的启动器程序为ccache,配置后即可开启cache缓存编译,加速重复编译并提高构建效率。使用该功能前需要安装ccache。配置方法如下,在对应的CMakeLists.txt进行设置:set(CMAKE_CXX_COMPILER-LaUNCHER &lt;launchersprogram&gt;)其中&lt;launchersprogram&gt;是ccache的安装路径,比如ccache的安装路径为/usr/bin/ccache,示例如下:set(CMAKE_CXX_COMPILER-LaUNCHER /usr/bin/ccache)</td></tr></table>


表2-15 常用的链接库（在使用高阶API时，必须链接以下库，因为这些库是高阶 API 功能所依赖的。在其他场景下，可以根据具体需求选择是否链接这些库。）


<table><tr><td>名称</td><td>作用描述</td><td>使用场景</td></tr><tr><td>libtiling_api.a</td><td>Tiling函数相关库。</td><td>使用高阶API相关的Tiling接口时需要链接。</td></tr><tr><td>libregister.so</td><td>Tiling注册相关库。</td><td>使用高阶API相关的Tiling接口时需要链接。</td></tr><tr><td>libgraph_base.so</td><td>基础数据结构和接口库。</td><td>调用ge::Shape, ge::DataType等基础结构体时需要链接。</td></tr><tr><td>libplatform.so</td><td>硬件平台信息库。</td><td>使用PlatformAscendC相关硬件平台信息接口时需要链接。</td></tr></table>


表2-16 编译 AI CPU 算子需要手动链接的库


<table><tr><td>名称</td><td>作用描述</td></tr><tr><td>libascendc_runti me.a</td><td>Ascend C算子参数等组装库。</td></tr><tr><td>libruntime.so</td><td>Runtime运行库。</td></tr><tr><td>libprofapi.so</td><td>Ascend C算子运行性能数据采集库。</td></tr><tr><td>libunified_dlog.so</td><td>CANN日志收集库。</td></tr><tr><td>libmmpa.so</td><td>CANN系统接口库。</td></tr><tr><td>libascend Dump.s0</td><td>CANN维测信息库。</td></tr><tr><td>libc(sec.so</td><td>CANN安全函数库。</td></tr><tr><td>liberrormanager.so</td><td>CANN错误信息管理库。</td></tr><tr><td>libascendcl.so</td><td>acl相关接口库。</td></tr></table>

# 2.3.4 算子运行

算子的计算算法实现通过Ascend C SIMT API来完成，而算子的加载调用则使用 Runtime API来完成。本章节将结合核函数调用介绍CANN软件栈中Ascend C算子运行 时常用的Runtime接口。Runtime接口更多信息与细节可以参考“acl API（C&C+ +）”章节。 

# 加载和运行代码

加载和运行算子时，需要使用Runtime API，完成运行时管理和配置。主要流程和使用 到的API如下： 

1. 初始化：aclInit。 

2. 运行时资源申请：通过aclrtSetDevice和aclrtCreateStream分别申请Device、 Stream运行管理资源。 

3. 使用aclrtMallocHost分配Host内存，并进行数据初始化。 

4. 使用aclrtMalloc分配Device内存，并通过aclrtMemcpy将数据从Host上拷贝到 Device上，参与核函数计算。 

5. 使用<<<>>>调用算子核函数。 

6. 执行核函数后，将Device上的运算结果拷贝回Host。 

7. 异步等待核函数执行完成：aclrtSynchronizeStream。 

8. 资源释放：通过aclrtDestroyStream和aclrtResetDevice分别释放Stream、Device 运行管理资源。 

9. 去初始化：aclFinalize。 

![](images/0236137bb421bccb2ed35e4d54c0805d0fde6e0d8e116b864d603df58e6cc25d.jpg)


# Kernel 加载与执行的更多方式

Kernel的加载与执行也可以通过二进制加载方式实现，这是最底层的接口实现方式。 内核调用符<<<...>>>为对底层接口的封装实现。使用时需要bisheng命令行编译将算子 源文件编译为二进制.o文件，再通过aclrtLaunchKernelWithConfig等Kernel加载与执 行接口完成算子调用。 

Kernel加载与执行接口的具体说明请参考“Kernel加载与执行”章节。 

关于更多bisheng命令行编译选项的使用介绍，SIMD编程、SIMD与SIMT混合编 程场景请参考常用的编译选项， SIMT编程场景请参考SIMT编程常用的编译选 项。 

SIMD编程、SIMD与SIMT混合编程场景完整样例请参考Kernel加载与执行（加载 二进制）样例，SIMT编程场景的样例请参考LINK。 

# 说明

核函数的调用是异步的，核函数的调用结束后，控制权立刻返回给主机端，可以调用以下 aclrtSynchronizeStream函数来强制主机端程序等待所有核函数执行完毕。 

aclError aclrtSynchronizeStream(aclrtStream stream);