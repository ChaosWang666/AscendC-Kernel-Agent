<!-- Source: 算子开发工具.md lines 6280-6911 | Section: 6.8 对外接口使用说明 -->

# 6.8 对外接口使用说明

# 6.8.1 接口列表

# 接口简介

msSanitizer工具包含sanitizer接口和mstx扩展接口两种类型。sanitizer接口用于 CANN软件栈的检测，与ACL系列接口一一对应。此类接口会在ACL对应接口的功能基 础上，额外向工具上报接口调用位置的代码文件和行号信息，使用时需导入sanitizer API头文件和链接动态库，具体请参见导入API头文件和链接动态库。mstx扩展接口用 于用户自定义上报内存池信息，以实现更准确的检测，具体请参见6.8.3 扩展接口 （mstx） 。 


表 6-8 msSanitizer 工具接口列表


<table><tr><td>接口类型</td><td>接口名称</td><td>功能简介</td></tr><tr><td rowspan="11">sanitizer接口</td><td>sanitizerRtMalloc</td><td rowspan="11">在ACL对应接口的功能基础上,向msSanitizer工具上报sanitizer接口调用位置的代码文件和行号信息。</td></tr><tr><td>sanitizerRtMallocCached</td></tr><tr><td>sanitizerRtFree</td></tr><tr><td>sanitizerRtMemset</td></tr><tr><td>sanitizerRtMemsetAsync</td></tr><tr><td>sanitizerRtMemcpy</td></tr><tr><td>sanitizerRtMemcpyAsync</td></tr><tr><td>sanitizerRtMemcpy2d</td></tr><tr><td>sanitizerRtMemcpy2dAsync</td></tr><tr><td>sanitizerReportMaIloc</td></tr><tr><td>sanitizerReportFree</td></tr><tr><td rowspan="5">扩展接口mstx(C/C++)</td><td>mstxDomainCreateA</td><td>创建域。</td></tr><tr><td>mstxMemHeapRegister</td><td>内存池注册接口。</td></tr><tr><td>mstxMemHeapUnregister</td><td>内存池注销接口。</td></tr><tr><td>mstxMemRegionsRegister</td><td>内存池二次分配注册接口。</td></tr><tr><td>mstxMemRegionsUnregister</td><td>内存池二次分配注销接口。</td></tr></table>

# 6.8.2 sanitizer 接口

# 6.8.2.1 sanitizerRtMalloc

# 功能说明

调用aclrtMalloc接口在Device上分配size大小的线性内存，并通过*devPtr返回已分配 内存的指针，并向检测工具上报内存分配信息。实际的内存分配行为和参数含义与 aclrtMalloc一致。 

# 说明

可参见《应用开发接口》手册中“acl API参考 > 运行时管理 $>$ 内存管理”章节查看aclrtMalloc 的详细说明。 

# 函数原型

aclError sanitizerRtMalloc(void **devPtr, size_t size, aclrtMemMallocPolicy policy, char const *filename, int lineno); 

# 参数说明


表6-9 参数说明


<table><tr><td>参数名</td><td>输入/输出</td><td>描述</td></tr><tr><td>devPtr</td><td>输出</td><td>指向“Device上已分配内存的指针”的指针。</td></tr><tr><td>size</td><td>输入</td><td>申请内存的大小，单位为Byte。
size不能为0。</td></tr><tr><td>policy</td><td>输入</td><td>内存分配规则。</td></tr><tr><td>filename</td><td>输入</td><td>内存分配被调用处的文件名。</td></tr><tr><td>lineno</td><td>输入</td><td>内存分配被调用处的行号。</td></tr></table>

# 返回值

返回0表示成功，返回其它值表示失败。 

# 调用示例

具体操作请参见使用示例的步骤4。 

# 6.8.2.2 sanitizerRtMallocCached

# 功能说明

调用aclrtMallocCached接口在Device上申请size大小的线性内存，通过*devPtr返回已 分配内存的指针，并向检测工具上报内存分配信息。该接口在任何场景下，申请的内 存都支持cache缓存。实际的内存分配行为和参数含义与aclrtMallocCached一致。 

# 说明

可参见《应用开发接口》手册中“acl API参考 $>$ 运行时管理 $>$ 内存管理”章节查看 aclrtMallocCached的详细说明。 

# 函数原型

aclError sanitizerRtMallocCached(void **devPtr, size_t size, aclrtMemMallocPolicy policy, char const *filename, int lineno); 

# 参数说明


表6-10 参数说明


<table><tr><td>参数名</td><td>输入/输出</td><td>描述</td></tr><tr><td>devPtr</td><td>输出</td><td>指向“Device上已分配内存的指针”的指针。</td></tr><tr><td>size</td><td>输入</td><td>申请内存的大小，单位为Byte。
size不能为0。</td></tr><tr><td>policy</td><td>输入</td><td>内存分配规则。</td></tr><tr><td>filename</td><td>输入</td><td>内存分配被调用处的文件名。</td></tr><tr><td>lineno</td><td>输入</td><td>内存分配被调用处的行号。</td></tr></table>

# 返回值

返回0表示成功，返回其它值表示失败。 

# 调用示例

具体操作请参见使用示例的步骤4。 

# 6.8.2.3 sanitizerRtFree

# 功能说明

调用aclrtFree接口释放Device上的内存，并向检测工具上报内存释放信息。实际的内 存释放行为和参数含义与aclrtFree一致。 

# 说明

可参见《应用开发接口》手册中“acl API参考 $>$ 运行时管理 $>$ 内存管理”章节查看aclrtFree的 详细说明。 

# 函数原型

aclError sanitizerRtFree(void *devPtr, char const *filename, int lineno); 

# 参数说明


表 6-11 参数说明


<table><tr><td>参数名</td><td>输入/输出</td><td>描述</td></tr><tr><td>devPtr</td><td>输入</td><td>待释放内存的指针。</td></tr><tr><td>filename</td><td>输入</td><td>内存释放被调用处的文件名。</td></tr><tr><td>lineno</td><td>输入</td><td>内存释放被调用处的行号。</td></tr></table>

# 返回值

返回0表示成功，返回其它值表示失败。 

# 调用示例

具体操作请参见使用示例的步骤4。 

# 6.8.2.4 sanitizerRtMemset

# 功能说明

调用aclrtMemset接口初始化内存，将内存中的内容设置为指定值，并向检测工具上报 内存初始化信息。实际的内存初始化行为和参数含义与aclrtMemset一致。 

# 说明

可参见《应用开发接口》手册中“acl API参考 > 运行时管理 > 内存管理”章节查看 aclrtMemset的详细说明。 

# 函数原型

aclError sanitizerRtMemset(void *devPtr, size_t maxCount, int32_t value, size_t count, char const *filename, int lineno); 

# 参数说明


表 6-12 参数说明


<table><tr><td>参数名</td><td>输入/输出</td><td>描述</td></tr><tr><td>devPtr</td><td>输入</td><td>内存起始地址的指针。</td></tr><tr><td>maxCount</td><td>输入</td><td>内存的最大长度，单位为Byte。</td></tr><tr><td>value</td><td>输入</td><td>初始化内存的指定值。</td></tr><tr><td>count</td><td>输入</td><td>需要设置为指定值的内存长度，单位为Byte。</td></tr><tr><td>filename</td><td>输入</td><td>内存初始化被调用处的文件名。</td></tr><tr><td>lineno</td><td>输入</td><td>内存初始化被调用处的行号。</td></tr></table>

# 返回值

返回0表示成功，返回其它值表示失败。 

# 调用示例

具体操作请参见使用示例的步骤4。 

# 6.8.2.5 sanitizerRtMemsetAsync

# 功能说明

调用aclrtMemsetAsync接口初始化内存，将内存中的内容设置为指定的值，并向检测 工具上报内存初始化信息。此接口为异步接口。实际的内存初始化行为和参数含义与 aclrtMemsetAsync一致。 

# 说明

可参见《应用开发接口》手册中“acl API参考 > 运行时管理 > 内存管理”章节查看 aclrtMemsetAsync的详细说明。 

# 函数原型

aclError sanitizerRtMemsetAsync(void *devPtr, size_t maxCount, int32_t value, size_t count, aclrtStream stream, char const *filename, int lineno); 

# 参数说明


表 6-13 参数说明


<table><tr><td>参数名</td><td>输入/输出</td><td>描述</td></tr><tr><td>devPtr</td><td>输入</td><td>内存起始地址的指针。</td></tr><tr><td>maxCount</td><td>输入</td><td>内存的最大长度，单位为Byte。</td></tr><tr><td>value</td><td>输入</td><td>初始化内存的指定值。</td></tr><tr><td>count</td><td>输入</td><td>初始化内存的长度，单位为Byte。</td></tr><tr><td>stream</td><td>输入</td><td>指定的stream。</td></tr><tr><td>filename</td><td>输入</td><td>内存初始化被调用处的文件名。</td></tr><tr><td>lineno</td><td>输入</td><td>内存初始化被调用处的行号。</td></tr></table>

# 返回值

返回0表示成功，返回其它值表示失败。 

# 调用示例

具体操作请参见使用示例的步骤4。 

# 6.8.2.6 sanitizerRtMemcpy

# 功能说明

调用aclrtMemcpy接口完成内存复制，并向检测工具上报内存复制信息。实际的内存 复制行为和参数含义与aclrtMemcpy一致。 

# 说明

可参见《应用开发接口》手册中“acl API参考 > 运行时管理 $>$ 内存管理”章节查看 aclrtMemcpy的详细说明。 

# 函数原型

aclError sanitizerRtMemcpy(void *dst, size_t destMax, const void *src, size_t count, aclrtMemcpyKind kind, char const *filename, int lineno); 

# 参数说明


表 6-14 参数说明


<table><tr><td>参数名</td><td>输入/输出</td><td>描述</td></tr><tr><td>dst</td><td>输入</td><td>目的内存地址指针。</td></tr><tr><td>destMax</td><td>输入</td><td>目的内存地址的最大内存长度，单位为Byte。</td></tr><tr><td>src</td><td>输入</td><td>源内存地址指针。</td></tr><tr><td>count</td><td>输入</td><td>内存复制的长度，单位为Byte。</td></tr><tr><td>kind</td><td>输入</td><td>预留参数，系统内部会根据源内存地址指针、目的内存地址指针判断是否可以将源地址的数据复制到目的地址，如果不可以，则系统会返回报错。</td></tr><tr><td>filename</td><td>输入</td><td>内存复制被调用处的文件名。</td></tr><tr><td>lineno</td><td>输入</td><td>内存复制被调用处的行号。</td></tr></table>

# 返回值

返回0表示成功，返回其它值表示失败。 

# 调用示例

具体操作请参见使用示例的步骤4。 

# 6.8.2.7 sanitizerRtMemcpyAsync

# 功能说明

调用aclrtMemcpyAsync接口完成内存复制，并向检测工具上报内存复制信息。此接口 为异步接口。实际的内存复制行为和参数含义与aclrtMemcpyAsync一致。 

# 说明

可参见《应用开发接口》手册中“acl API参考 > 运行时管理 > 内存管理”章节查看 aclrtMemcpyAsync的详细说明。 

# 函数原型

aclError sanitizerRtMemcpyAsync(void *dst, size_t destMax, const void *src, size_t count, aclrtMemcpyKind kind, aclrtStream stream, char const *filename, int lineno); 

# 参数说明


表 6-15 参数说明


<table><tr><td>参数名</td><td>输入/输出</td><td>描述</td></tr><tr><td>dst</td><td>输入</td><td>目的内存地址指针。</td></tr><tr><td>destMax</td><td>输入</td><td>目的内存地址的最大内存长度，单位为Byte。</td></tr><tr><td>src</td><td>输入</td><td>源内存地址指针。</td></tr><tr><td>count</td><td>输入</td><td>内存复制的长度，单位为Byte。</td></tr><tr><td>kind</td><td>输入</td><td>预留参数，系统内部会根据源内存地址指针、目的内存地址指针判断是否可以将源地址的数据复制到目的地址，如果不可以，则系统会返回报错。</td></tr><tr><td>stream</td><td>输入</td><td>当前内存复制行为指定的stream。</td></tr><tr><td>filename</td><td>输入</td><td>内存复制被调用处的文件名。</td></tr><tr><td>lineno</td><td>输入</td><td>内存复制被调用处的行号。</td></tr></table>

# 返回值

返回0表示成功，返回其它值表示失败。 

# 调用示例

具体操作请参见使用示例的步骤4。 

# 6.8.2.8 sanitizerRtMemcpy2d

# 功能说明

调用aclrtMemcpy2d接口完成矩阵数据内存复制，并向检测工具上报内存复制信息。 实际的矩阵数据内存复制行为和参数含义与aclrtMemcpy2d一致。 

# 说明

可参见《应用开发接口》手册中“acl API参考 > 运行时管理 $>$ 内存管理”章节查看 aclrtMemcpy2d的详细说明。 

# 函数原型

aclError sanitizerRtMemcpy2d(void *dst, size_t dpitch, const void *src, size_t spitch, size_t width, size_t height, aclrtMemcpyKind kind, char const *filename, int lineno); 

# 参数说明


表 6-16 参数说明


<table><tr><td>参数名</td><td>输入/输出</td><td>描述</td></tr><tr><td>dst</td><td>输入</td><td>目的内存地址指针。</td></tr><tr><td>dpitch</td><td>输入</td><td>目的内存中相邻两列向量的地址距离。</td></tr><tr><td>src</td><td>输入</td><td>源内存地址指针。</td></tr><tr><td>spitch</td><td>输入</td><td>源内存中相邻两列向量的地址距离。</td></tr><tr><td>width</td><td>输入</td><td>待复制的矩阵宽度。</td></tr><tr><td>height</td><td>输入</td><td>待复制的矩阵高度。
height最大设置为5*1024*1024=5242880，否则接口返回失败。</td></tr><tr><td>kind</td><td>输入</td><td>内存复制的类型。</td></tr><tr><td>filename</td><td>输入</td><td>矩阵数据内存复制被调用处的文件名。</td></tr><tr><td>lineno</td><td>输入</td><td>矩阵数据内存复制被调用处的行号。</td></tr></table>

# 返回值

返回0表示成功，返回其它值表示失败。 

# 调用示例

具体操作请参见使用示例的步骤4。 

# 6.8.2.9 sanitizerRtMemcpy2dAsync

# 功能说明

调用aclrtMemcpy2dAsync接口完成矩阵数据内存复制，并向检测工具上报内存复制信 息。此接口为异步接口。实际的矩阵数据内存复制行为和参数含义与 aclrtMemcpy2dAsync一致。 

# 说明

可参见《应用开发接口》手册中“acl API参考 > 运行时管理 $>$ 内存管理”章节查看 aclrtMemcpy2dAsync的详细说明。 

# 函数原型

aclError sanitizerRtMemcpy2dAsync(void *dst, size_t dpitch, const void *src, size_t spitch, size_t width, size_t height, aclrtMemcpyKind kind, aclrtStream stream, char const *filename, int lineno); 

# 参数说明


表 6-17 参数说明


<table><tr><td>参数名</td><td>输入/输出</td><td>描述</td></tr><tr><td>dst</td><td>输入</td><td>目的内存地址指针。</td></tr><tr><td>dpitch</td><td>输入</td><td>目的内存中相邻两列向量的地址距离。</td></tr><tr><td>src</td><td>输入</td><td>源内存地址指针。</td></tr><tr><td>spitch</td><td>输入</td><td>源内存中相邻两列向量的地址距离。</td></tr><tr><td>width</td><td>输入</td><td>待复制的矩阵宽度。</td></tr><tr><td>height</td><td>输入</td><td>待复制的矩阵高度。
height最大设置为5*1024*1024=5242880，否则接口返回失败。</td></tr><tr><td>kind</td><td>输入</td><td>内存复制的类型。</td></tr><tr><td>stream</td><td>输入</td><td>当前矩阵数据内存复制行为指定的stream。</td></tr><tr><td>filename</td><td>输入</td><td>矩阵数据内存复制被调用处的文件名。</td></tr><tr><td>lineno</td><td>输入</td><td>矩阵数据内存复制被调用处的行号。</td></tr></table>

# 返回值

返回0表示成功，返回其它值表示失败。 

# 调用示例

具体操作请参见使用示例的步骤4。 

# 6.8.2.10 sanitizerReportMalloc

# 功能说明

手动上报GM内存分配信息。 

# 函数原型

void sanitizerReportMalloc(void *ptr, uint64_t size); 

# 说明

此接口是__sanitizer_report_malloc接口的封装， __sanitizer_report_malloc接口为弱函数，只 有当用户程序被检测工具拉起时才会生效。 

# 参数说明


表 6-18 参数说明


<table><tr><td>参数名</td><td>输入/输出</td><td>描述</td></tr><tr><td>ptr</td><td>输入</td><td>分配的内存地址。</td></tr><tr><td>size</td><td>输入</td><td>分配的内存长度。</td></tr></table>

# 返回值

无 

# 调用示例

无 

# 6.8.2.11 sanitizerReportFree

# 功能说明

手动上报GM内存释放信息。 

# 函数原型

void sanitizerReportFree(void *ptr); 

# 说明

此接口是__sanitizer_report_free接口的封装，__sanitizer_report_free接口为弱函数，只有当用 户程序被检测工具拉起时才会生效。 

# 参数说明


表 6-19 参数说明


<table><tr><td>参数名</td><td>输入/输出</td><td>描述</td></tr><tr><td>ptr</td><td>输入</td><td>释放的内存地址。</td></tr></table>

# 返回值

无 

# 调用示例

无 

# 6.8.3 扩展接口（mstx）

# 6.8.3.1 mstx 接口简介

mstx接口是MindStudio提供的一个性能分析接口，它允许用户在应用程序中插入特定 的标记，以便在工具进行内存检测时能够更精确地定位特定算子的内存问题。例如， 针对二级指针类算子，在不使能mstx接口的情况下，得到的地址空间可能不准确。通 过mstx的6.8.3.4 mstxMemRegionsRegister和6.8.3.5 

mstxMemRegionsUnregister接口，可以将准确的地址空间传递给异常检测工具，实 现更精准的内存检测。 

# 说明

Kernel直调中的内核调用符场景暂不支持使用mstx接口。 

# mstx 接口的使用

msSanitizer工具默认使能mstx接口，允许用户使用mstx接口自定义算子使用的内 存空间地址和大小，可识别并快速界定算子的内存问题。 

mstx当前提供了两种API的使用方式：库文件和头文件，以Link为例： 

# 说明

● 此样例工程不支持Atlas A3 训练系列产品。 

```txt
- 在$\{git_clone_path\}/samples/operator/ascending/0_introduction/1_add_frameworklaunch/AclNNInvocation/src/CMakeLists.txt路径下新增库文件libms.tools_ext.so,地址为:${\INSTALL_DIR}/lib64/libms.tools_ext.so。
#Header path
includeDirectories(...
${CUSTPKG_PATH}/include)
...
target_linklibraries( 
```

```txt
） dl 
```

在${git_clone_path}/samples/operator/ascendc/0_introduction/ 1_add_frameworklaunch/AclNNInvocation/src/main.cpp路径下，将用户程 序编译链接dl库，对应的头文件ms_tools_ext.h地址：${INSTALL_DIR}/ include/mstx。 

```txt
include"mstx/ms.tools_ext.h" 
```

![](images/ea033f3890bb6369b985bfba25fa77cf5fd23a49951fc3dffc90fa1c4d88ed9e.jpg)


# 说明

${INSTALL_DIR}请替换为CANN软件安装后文件存储路径。若安装的Ascend-canntoolkit软件包，以root安装举例，则安装后文件存储路径为：/usr/local/Ascend/ ascend-toolkit/latest。 

# 整体调用示例

mstxMemVirtualRangeDesc_t rangeDesc = {};  
rangeDesc.deviceld = deviceId; //设备编号  
rangeDesc.ptr = gm; //注册的内存池CM首地址  
rangeDesc.size = 1024; //内存池大小  
heapDesc.typeSpecificDesc = &rangeDesc;  
mstxMemHeapDesc_t heapDesc{};  
mstxMemHeapHandle_t memPool = mstxMemHeapRegister(globalDomain, &heapDesc); //注册内存池  
mstxMemVirtualRangeDesc_t rangesDesc[1] = {}; //二次分配包含的region数量  
mstxMemRegionHandle_t regionHandles[1] = {};  
rangesDesc[0].deviceId = deviceId; //设备编号  
rangesDesc[0].ptr = gm; //二次分配GM地址  
rangesDesc[0].size = 256; //二次分配大小  
mstxMemRegionsRegisterBatch_t regionsDesc{};  
regionsDesc.heap = memPool;  
regionsDesc(regionType = MSTX_MEM_TYPE_VIRTUAL_ADDRESS;  
regionsDesc(regionCount = 1;  
regionsDesc(regionDescArray = rangesDesc;  
regionsDesc(regionHandleArrayOut = regionHandles;  
mstxMemRegionsRegister(globalDomain, $\text{®}$ ionsDesc); //二次分配注册  
Do(blockDim, nullptr, stream, gm); //算子Kernel函数  
mstxMemRegionRef_t regionRef[1] = {};  
regionRef[0].refType = MSTX_MEMREGION_REF_TYPE_handle;  
regionRef[0].handle = regionHandles[0];  
mstxMemRegionsUnregisterBatch_t refsDesc = {};  
refsDesc.refCount = 1;  
refsDesc.refArray = regionRef;  
mstxMemRegionsUnregister(globalDomain, &refsDesc); //注销二次分配  
mstxMemHeapUnregister(globalDomain, memPool); //注销内存池 

# 6.8.3.2 mstxDomainCreateA

# 函数原型

mstxDomainHandle_t mstxDomainCreateA(const char *name) 

# 功能说明

创建一个新的mstx域。 

# 参数说明


表 6-20 参数说明


<table><tr><td>参数</td><td>输入/输出</td><td>说明</td></tr><tr><td>name</td><td>输入</td><td>要创建的域的名称。
最大长度为1023，仅支持数字、大小写字母和_符号。
数据类型：const char *。
默认域名为globalDomain。</td></tr><tr><td>返回值</td><td>输出</td><td>创建的域句柄，域句柄的定义如下：
struct mstxDomainRegistration_st;
typedef struct mstxDomainRegistration_st
mstxDomainRegistration_t;
typedef mstxDomainRegistration_t*
mstxDomainHandle_t;</td></tr></table>

# 返回值

返回域对应的句柄。 

说明 

若传入相同的域名，接口将会返回相同的句柄。 

# 调用示例

```vba
mstxDomainHandle_t domain = mstxDomainCreateA("sample") 
```

# 6.8.3.3 mstxMemHeapRegister

# 函数原型

mstxMemHeapHandle_t mstxMemHeapRegister(mstxDomainHandle_t domain, mstxMemHeapDesc_t const *desc) 

# 功能说明

注册内存池。用户在调用该接口注册内存池时，需确保该内存已提前申请。 

# 参数说明


表 6-21 参数说明


<table><tr><td>参数</td><td>输入/输出</td><td>说明</td></tr><tr><td>domain</td><td>输入</td><td>为globalDomain或6.8.3.2 mstxDomainCreateA返回的句柄。数据类型: const char *。</td></tr><tr><td>desc</td><td>输入</td><td>typedef enum mstxMemHeapUsageType{/* @brief 此堆内存作为内存池使用* 使用此使用方式注册的堆内存,需要使用二次分配注册后才可以访问*/MSTX_MEM_heap_USAGE_TYPE_SUBAllocator = 0,} mstxMemHeapUsageType;/** @brief 堆内存的类型*此处的“类型”是指通过何种方式来描述堆内存指针。当前仅支持线性排布的*内存,但此处保留日后支持更多内存类型的扩展能力。比如某些API返回多个*句柄来描述内存范围,或者一些高维内存需要使用 stride、tiling 或* interlace 来描述*/typedef enum mstxMemType{/** @brief 标准线性排布的虚拟内存*此时mstxMemHeapRegister 接收mstxMemVirtualRangeDesc_t 类型的描述*/MSTX_MEM_TYPE_VIRTUAL_ADDRESS = 0,} mstxMemType;typedef struct mstxMemVirtualRangeDesc_t{uint32_t deviceld; //内存区域对应的设备IDvoid const *ptr; //内存区域的起始地址uint64_t size; //内存区域的长度} mstxMemVirtualRangeDesc_t;typedef struct mstxMemHeapDesc_t{mstxMemHeapUsageType usage; //堆内存的使用方式mstxMemType type; //堆内存的类型void const *typeSpecificDesc; //堆内存在指定内存类型下的描述信息} mstxMemHeapDesc_t;</td></tr></table>

# 返回值

内存池对应的句柄。 

# 调用示例

```javascript
mstxMemVirtualRangeDesc_t rangeDesc = {};  
rangeDesc.deviceld = deviceId; // 设备编号  
rangeDesc.ptr = gm; // 注册的内存池gm首地址  
rangeDesc.size = 1024; // 内存池大小  
heapDesc.typeSpecificDesc = &rangeDesc;  
mstxMemHeapDesc_t heapDesc{};  
mstxMemHeapHandle_t memPool = mstxMemHeapRegister(globalDomain, &heapDesc); // 注册内存池 
```

# 6.8.3.4 mstxMemRegionsRegister

# 函数原型

void mstxMemRegionsRegister(mstxDomainHandle_t domain, mstxMemRegionsRegisterBatch_t const *desc) 

# 功能说明

注册内存池二次分配。用户需保证RegionsRegister的内存位于6.8.3.3 mstxMemHeapRegister注册的范围内，否则工具会提示越界读写。 

# 参数说明


表6-22 参数说明


<table><tr><td>参数</td><td>输入/输出</td><td>说明</td></tr><tr><td>domain</td><td>输入</td><td>为globalDomain或6.8.3.2mstxDomainCreateA返回的句柄。数据类型: const char *。</td></tr><tr><td>desc</td><td>输入</td><td>内存池待二次分配的内存区域描述信息,不能为空。struct mstxMemRegion_st; typedef struct mstxMemRegion_stmstxMemRegion_t; typedef mstxMemRegion_t* mstxMemRegionHandle_t; typedef struct mstxMemRegionsRegisterBatch_t{mstxMemHeapHandle_t heap; //要进行二次分配的内存池句柄mstxMemType regionType; //内存区域的内存类型size_t regionCount; //内存区域的个数void const *regionDescArray; //内存区域描述数据mstxMemRegionHandle_t*regionHandleArrayOut; //返回的注册二次分配得到的句柄数组}mstxMemRegionsRegisterBatch_t;</td></tr></table>

# 返回值

无 

# 调用示例

```txt
mstxMemRegionsRegisterBatch_t regionsDesc{};  
regionsDesc.heap = memPool;  
regionsDesc(regionType = MSTX_MEM_TYPE_VIRTUAL_ADDRESS;  
regionsDesc(regionCount = 1;  
regionsDesc(regionDescArray = rangesDesc; 
```

```txt
regionsDesc(regionHandleArrayOut = regionHandles;  
mstxMemRegionsRegister(globalDomain, ®ionsDesc); //二次分配注册 
```

# 6.8.3.5 mstxMemRegionsUnregister

# 函数原型

void mstxMemRegionsUnregister(mstxDomainHandle_t domain, mstxMemRegionsUnregisterBatch_t const *desc) 

# 功能说明

注销内存池二次分配。 

# 参数说明


表 6-23 参数说明


<table><tr><td>参数</td><td>输入/输出</td><td>说明</td></tr><tr><td>domain</td><td>输入</td><td>为globalDomain或6.8.3.2mstxDomainCreateA返回的句柄。数据类型: const char *。</td></tr><tr><td>desc</td><td>输入</td><td>输入的描述信息必须是某一次6.8.3.3mstxMemHeapRegister的输入描述信息,否则工具将打屏提示错误。typedef enum mstxMemRegionRefType{ //通过指针描述内存引用MSTX_MEMREGION_REF_TYPE_POINTER = 0, //通过句柄描述内存引用MSTX_MEMREGION_REF_TYPE_handle} mstxMemRegionRefType;typedef struct mstxMemRegionRef_t{ mstxMemRegionRefType refType; //描述内存引用的方式union {void const* pointer; //当前内存引用通过指针描述时,此处保存内存区域指针mstxMemRegionHandle_t handle; //当内存引用通过句柄描述时,此处保存内存区域的句柄};} mstxMemRegionRef_t;typedef struct mstxMemRegionsUnregisterBatch_t{ size_t refCount; //内存引用的个数mstxMemRegionRef_t const *refArray; //要注销的内存区域引用} mstxMemRegionsUnregisterBatch_t;</td></tr></table>

# 返回值

无 

# 调用示例

```javascript
mstxMemRegionsUnregisterBatch_t refsDesc = {}
refsDesc.refCount = 1;
refsDesc.refArray = regionRef;
mstxMemRegionsUnregister(globalDomain, &refsDesc); //注销二次分配 
```

# 6.8.3.6 mstxMemHeapUnregister

# 函数原型

```txt
void mstxMemHeapUnregister(mstxDomainHandle_t domain, mstxMemHeapHandle_t heap) 
```

# 功能说明

注销内存池时，与之关联的Regions将一并被注销。 

# 参数说明


表 6-24 参数说明


<table><tr><td>参数</td><td>输入/输出</td><td>说明</td></tr><tr><td>domain</td><td>输入</td><td>domain为内存池所属的域，为 globalDomain或6.8.3.2 pstxDomainCreateA返回的句柄。数据类型：const char *。</td></tr><tr><td>heap</td><td>输入</td><td>heap为需要注销内存池的句柄，为6.8.3.3 pstxMemHeapRegister的返回值。struct pstxMemHeap_st; typedef struct pstxMemHeap_st pstxMemHeap_t; typedef pstxMemHeap_t* pstxMemHeapHandle_t;</td></tr></table>

# 返回值

无 

# 调用示例

```txt
mstxMemHeapDesc_t heapDesc{};  
mstxMemHeapHandle_t memPool = mstxMemHeapRegister(globalDomain, &heapDesc); // 注册内存池  
...  
mstxMemHeapUnregister(globalDomain, memPool); // 注销内存池 
```

# 7 算子调试（msDebug）

工具概述 

使用前准备 

指定Device ID（通算融合算子场景） 

断点设置 

内存与变量打印 

单步调试 

中断运行 

核切换 

读取寄存器 

调试信息展示 

解析异常算子dump文件 

典型案例 

FAQ