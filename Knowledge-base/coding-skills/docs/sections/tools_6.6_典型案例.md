<!-- Source: 算子开发工具.md lines 5812-6222 | Section: 6.6 典型案例 -->

# 6.6 典型案例

# 6.6.1 检测内核调用符方式的 Ascend C 算子

# 操作步骤

步骤1 请参考内核调用符场景准备，完成使用前准备。 

步骤2 参考6.2 使用前准备完成相关环境变量的配置。 

步骤3 构建单算子可执行文件。 

以Add算子为例，可执行文件的构建命令示例如下： 

```batch
bash run.sh -r npu -v <soc_version> 
```

一键式编译运行脚本完成后，在工程目录下生成NPU侧可执行文件 

```txt
<kernel_name>_npu。 
```

步骤4 使用msSanitizer检测工具拉起单算子可执行文件（以add npu为例）。 

内存检测执行以下命令，具体参数说明请参考表6-2和表6-3，内存检测请参考内 存检测示例说明。 mssanitizer --tool=memcheck ./add npu # 内存检测需指定 --tool=memcheck 

竞争检测执行以下命令，具体参数说明请参考表6-2，竞争检测请参考竞争检测示 例说明。 

mssanitizer --tool=racecheck ./add npu # 竞争检测需指定 --tool=racecheck 

单算子可执行文件所在路径可配置为绝对路径或相对路径，请根据实际环境配置。 

----结束 

# 内存检测示例说明

在步骤1之前，需要在Add算子中构造一个非法读写的场景，将DataCopy内存拷 贝长度从TILE_LENGTH改为2 * TILE_LENGTH，此时最后一次拷贝会发生内存读 写越界。 

aicore__inline void CopyOut(int32_t progress)   
{ //deque output tensor from VECOUT queue LocalTensor<half>zLocal $=$ outQueueZ.DeQue<half>(); //copy progress_th tile from local tensor to global tensor //构造非法读写场景 DataCopy(zGm[progress\* TILE_LENGTH],zLocal,2\* TILE_LENGTH); //free output tensor for reuse outQueueZ.FreeTensor(zLocal);   
} 

根据检测工具输出的报告，可以发现在add_custom.cpp的65行对GM存在224字 节的非法写操作，与我们构造的异常场景对应。 

```txt
$ mssanitizer --tool=memcheck ./add_npu
--------=ERROR:illegal write of size 224
--------=at 0x12c0c002ef00 on GM in add_custom_kernel
--------=in block aiv(7) on device 0
--------=code in pc current 0x1644 (serialNo:2342)
--------=#0 ${ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/impl/dav_c220/
kernel_operator_data_copy_impl.h:107:9
--------= #1 ${ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/inner/interface/
inner_kernel_operator_data_copy_intf.cppm:155:9
--------= #2 ${ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/inner/interface/
inner_kernel_operator_data_copy_intf.cppm:459:5
--------= #3 samples/operator/AddCustomSample/KernelLaunch/AddKernelInvocation/
addcustom.cpp:65:9
--------= #4 samples/operator/AddCustomSample/KernelLaunch/AddKernelInvocation/
addcustom.cpp:38:13
--------= #5 samples/operator/AddCustomSample/KernelLaunch/AddKernelInvocation/
addcustom.cpp:82:8 
```

# 竞争检测示例说明

在步骤1之前，需要在Add算子中构造一个核间竞争的场景，将DataCopy内存拷 贝长度从TILE_LENGTH改为2 * TILE_LENGTH，此时会在GM内存上存在核间竞 争。 

__aicore__inline void CopyOut(int32_t progress)   
{ //deque output tensor from VECOUT queue LocalTensor<half>zLocal $=$ outQueueZ.DeQue<half>(); //copy progress_th tile from local tensor to global tensor //构造核间竞争场景 DataCopy(zGm[progress\* TILE_LENGTH],zLocal,2\* TILE_LENGTH); //free output tensor for reuse outQueueZ.FreeTensor(zLocal);   
} 

根据检测工具输出的报告，可以发现在add_kernel.cpp的65行，AIV的0核和1核 存在核间竞争，符合我们构造的异常场景。 

```txt
$ mssanitizer --tool=racecheck ./add_npu
--------=ERROR: Potential WAW hazard detected at GM in add_custom_kernel:
--------=PIPE_MTE3 Write at WAW()+0x12c0c0025f00 in block 0 (aiv) on device 0 at pc current
0x1644 (serialNo:305)
--------= #0 ${ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/impl/dav_c220/
kernel_operator_data_copy_impl.h:107:9
--------= #1 ${ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/inner/interface/
inner_kernel_operator_data_copy_intf.cppm:155:9
--------= #2 ${ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/inner/interface/
inner_kernel_operator_data_copy_intf.cppm:459:5
--------= #3 samples/operator/AddCustomSample/KernelLaunch/AddKernelInvocation/
add_custom.cpp:65:9
--------= #4 samples/operator/AddCustomSample/KernelLaunch/AddKernelInvocation/
addcustom.cpp:38:13
--------= #5 samples/operator/AddCustomSample/KernelLaunch/AddKernelInvocation/
addcustom.cpp:82:8
--------= PIPE_MTE3 Write at WAW()+0x12c0c0026000 in block 1 (aiv) on device 0 at pc current
0x1644 (serialNo:329)
--------= #0 ${ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/impl/dav_c220/ 
```

kernel_operator_data_copyImpl.h:107:9 $= = = = = \# 1$ {\ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/inner/interface/  
inner_kernel_operator_data_copy_intc.cppm:155:9 $= = = = = \# 2$ {\ASCEND_HOME_PATH}/compiler/tikcpp/tikcfw/inner/interface/  
inner_kernel_operator_data_copy_intc.cppm:459:5 $= = = = = \# 3$ samples/operator/AddCustomSample/KernelLaunch/AddKernelInvocation/add_custom.cpp:65:9 $= = = = = \# 4$ samples/operator/AddCustomSample/KernelLaunch/AddKernelInvocation/add_custom.cpp:38:13 $= = = = = \# 5$ samples/operator/AddCustomSample/KernelLaunch/AddKernelInvocation/add_custom.cpp:82:8 

# 6.6.2 检测 API 调用的单算子

完成自定义算子的开发部署后，通过单算子API执行的方式调用，添加检测相关编译选 项重新编译算子并部署，使用msSanitizer工具运行可执行文件实现算子进行异常检 测。 

# 前提条件

单击Link获取样例工程，为进行算子检测做准备。 

# 说明

● 此样例工程不支持Atlas A3 训练系列产品。 

下载代码样例时，需执行以下命令指定分支版本。 git clone https://gitee.com/ascend/samples.git -b v1.5-8.2.RC1 

# 操作步骤

步骤1 执行以下命令，生成自定义算子工程，并进行Host侧和Kernel侧的算子实现。 bash install.sh -v Ascendxxxyy # xxxyy为用户实际使用的具体芯片类型 

步骤2 请参考4.5 算子编译部署，完成算子的编译部署。 

# 说明

```txt
在样例工程的${gitClone_path}/samples/operator/ascendc/0_introduction/  
1_add_frameworklaunch/CustomOp目录下，修改在op_kernel/CMakeLists.txt文件，在Kernel侧实现中增加检测选项-sanitizer，以支持检测功能  
add ops.compile-options(ALL OPTIONS -sanitizer) 
```

步骤3 单击前提条件，获取验证代码的样例工程目录。 

```txt
input //存放脚本生成的输入数据目录  
output //存放算子运行输出数据和真值数据的目录  
inc //头文件目录  
common.h //声明公共方法类，用于读取二进制文件  
operator_desc.h //算子描述声明文件，包含算子输入/输出，算子类型以及输入描述与输出描述  
op Runner.h //算子运行相关信息声明文件，包含算子输入/输出个数，输入/输出大小等  
src  
CMakeLists.txt //编译规则文件  
common.cpp //公共函数，读取二进制文件函数的实现文件  
main.cpp //单算子调用应用的入口  
operator_desc.cpp //构造算子的输入与输出描述  
op Runner.cpp //单算子调用主体流程实现文件  
scripts  
verify_result.py //真值对比文件  
gen_data.py //输入数据和真值数据生成脚本文件  
acl.json //acl配置文件 
```

步骤4 使用检测工具拉起算子API运行脚本。 

```txt
mssanitizer --tool=memcheck bash run.sh #内存检测需指定--tool=memcheck  
mssanitizer --tool=racecheck bash run.sh #竞争检测需指定--tool=racecheck 
```

步骤5 参考内存异常报告解析和竞争异常报告解析分析异常行为。 

----结束 

# 6.6.3 检测 PyTorch 接口调用的算子

# 前提条件

单击Link获取样例工程，为进行算子检测做准备。 

# 说明

● 此样例工程仅支持Python3.9，若要在其他Python版本上运行，需要修改$ {git_clone_path}/samples/operator/ascendc/0_introduction/ 1_add_frameworklaunch/PytorchInvocation目录下run_op_plugin.sh文件中的Python 版本。 

● 此样例工程不支持Atlas A3 训练系列产品。 

下载代码样例时，需执行以下命令指定分支版本。 git clone https://gitee.com/ascend/samples.git -b v1.5-8.2.RC1 

已参考《Ascend Extension for PyTorch 软件安装指南》，完成PyTorch框架和 torch_npu插件的安装。 

# 操作步骤

步骤1 执行以下命令，生成自定义算子工程，并进行Host侧和Kernel侧的算子实现。 

bash install.sh -v Ascendxxxyy # xxxyy为用户实际使用的具体芯片类型 

步骤2 参考4.5 算子编译部署，完成算子的编译部署。 

# 说明

```txt
编辑样例工程目录\$\{gitclone_path\}/samples/operator/ascendc/0_introduction/1_add_frameworklaunch/CustomOp/op_kernel下的CMakeLists.txt文件，增加编译选项-sanitizer。  
add ops.compile-options(ALL OPTIONS -sanitizer) 
```

步骤3 进入PyTorch接入工程，使用PyTorch调用方式调用AddCustom算子工程，并按照指导 完成编译。 

```txt
PytorchEnvocation  
opPluginpatch  
run_opPlugin.sh //5.执行样例时，需要使用  
test ops(custom.py //步骤6启动工具时，需要使用 
```

步骤4 执行样例，样例执行过程中会自动生成测试数据，然后运行PyTorch样例，最后检验运 行结果。 

```txt
bash run_opPlugin.sh
-- CMAKE_CCE_COMPILER: ${INSTALL_DIR}/toolkit/tools/ccec_computer/bin/ccec
-- CMAKE_CURRENT_LIST_DIR: ${INSTALL_DIR}/AddKernellInvocation/cmake/Modules
-- ASCEND_PRODUCT_TYPE:
    Ascend.xxxxv
-- ASCEND_CORE_TYPE:
    VectorCore
-- ASCEND_install_PATH:
    /usr/local/Ascend/ascend-toolkit/latest
-- The CXX compiler identification is GNU 10.3.1
-- Detecting CXX compiler ABI info
-- Detecting CXX compiler ABI info - done
-- Check for working CXX compiler: /usr/bin/c++ - skipped
-- Detecting CXX compile features
-- Detecting CXX compile features - done 
```

```sql
-- Configuring done
-- Generating done
-- Build files have been written to: ${INSTALL_DIR}/AddKernellInvocation/build
Scanning dependencies of target add_npu
[33%] Building CCE object cmake/npu/CMakeFiles/add_npu.dir/..//add_custom.cpp.o
[66%] Building CCE object cmake/npu/CMakeFiles/add_npu.dir/..//main.cpp.o
[100%] Linking CCE executable ..//../add_npu
[100%] Built target add_npu
${INSTALL_DIR}/AddKernellInvocation
INFO: compile op on ONBOARD succeed!
INFO: execute op on ONBOARD succeed!
test pass 
```

步骤5 启动msSanitizer工具拉起Python程序，进行异常检测。 

步骤6 参考内存异常报告解析、竞争异常报告解析及未初始化异常报告解析分析异常行为。 

----结束 

# 6.6.4 检测 CANN 软件栈的内存

针对用户程序调用CANN软件栈接口可能出现的内存异常操作场景，msSanitizer检测 工具提供了Device相关接口和AscendCL相关接口的内存检测能力，方便用户对程序内 存异常操作位置的排查和定位。 

# 内存泄漏检测使用原理

当npu-smi info命令查询到的设备内存不断增大时，可使用本工具进行内存泄漏定位 定界，若AscendCL系列接口泄漏可支持定位到代码行。 

如图6-1所示，CANN软件栈内存操作接口包含两个层级，向下使用驱动侧提供的 Device侧接口，向上提供了AscendCL系列接口供用户代码调用。 


图6-1 内存检测


![](images/ddb9f8628c381ff60fab24840aa41280f7a87279b52f4353bca2d999e85d5f35.jpg)


内存泄漏定位可分为以下步骤： 

1. 使能Device系列接口进行泄漏检测，判断内存泄漏是否发生在Host侧。若没有， 则定界到Device侧的应用出现泄漏；若有，则通过下一个步骤判断AscendCL接口 调用是否发生泄漏； 

2. 使能AscendCL系列接口进行泄漏检测，判断用户代码调用AscendCL接口是否存在 泄漏。若没有，则定界为非AscendCL接口调用问题；如果出现泄漏，则通过下一 步定位到具体代码行； 

3. 使用msSanitizer检测工具中提供的新接口，对头文件重新编译，再用检测工具拉 起检测程序，可定位到未释放内存的分配函数所对应的文件名与代码行号。新接 口的详细说明请参见6.8 对外接口使用说明。 

# 排查步骤

步骤1 参考6.2 使用前准备完成相关环境变量配置。 

步骤2 定界是否为Host侧泄漏。 

1. 使用msSanitizer检测工具拉起待检测程序，命令示例如下： 

$$
m s s a n i t i z e r - c h e c k - d e v i c e - h e a p = y e s - l e a k - c h e c k = y e s. / a d d _ {n p u}
$$

待检测程序（以add custom npu为例）所在路径可配置为绝对路径或相对路径， 请根据实际环境配置。 

2. 若无异常输出则说明检测程序运行成功，且Host侧不存在内存泄漏情况；若输出 如下错误说明Host侧的应用出现了内存泄漏。 

以下输出结果表明Host侧共有一处分配了内存但未释放，导致内存泄漏32800字 节。 

$$
\begin{array}{l} = = = = = = E R R O R: \text {L e a k C h e c k : d e t e c t e d m e r r o r y l e a k s} \\ = = = = = \quad \text {D i r e c t} \\ = = = = = = \quad a t 0 x 1 2 4 0 8 0 0 2 4 0 0 0 o n G M a l l o c a t e d i n <   u n k n o w >: 0 (s e r i a l N o: 0) \\ = = = = = = S U M M A R Y: 3 2 8 0 0 \text {b y t e} (s) \text {l e a k e d i n} 1 \text {a l l o c a t i o n} (s) \\ \end{array}
$$

步骤3 定界是否为AscendCL接口调用导致泄漏。 

1. 使用msSanitizer检测工具拉起待检测程序，命令示例如下： 

$$
m s s a n i t i z e r - - c h e c - c a n n - h e a p = y e - - l e a k - c h e c = y e \quad / + d d _ {n p u}
$$

2. 若无异常输出则说明检测程序运行成功，且AscendCL接口调用不存在内存泄漏情 况；若输出如下错误说明AscendCL接口调用出现了内存泄漏。 

以下输出结果表明调用AscendCL接口时共有一处分配了内存但未释放，导致内存 泄漏32768字节。 

$$
\begin{array}{l} = = = = = E R R O R: \text {L e a k C h e c k : d e t e c t e d m e r r o y l e a k s} \\ = = = = = \quad \text {D i r e c t} \\ = = = = = = \quad a t 0 x 1 2 4 0 8 0 0 2 4 0 0 0 o n G M a l l o c a t e d i n <   u n k n o w >: 0 (s e r i a l N o: 0) \\ = = = = = = S U M M A R Y: 3 2 7 6 8 \text {b y t e} (s) \text {l e a k e d i n 1 a l l o c a t i o n} (s) \\ \end{array}
$$

步骤4 若存在泄漏，可通过msSanitizer工具中提供的msSanitizer API头文件“acl.h”和对应 的动态库文件定位发生泄漏的代码文件和代码行。 

定位发生泄漏的代码文件和代码行时，需要将用户代码中原有的“acl/acl.h”头文件替 换为工具中提供的msSanitizer API头文件“acl.h”，并将动态库 

libascend_acl_hook.so文件链接至用户的应用工程中，并重新编译应用工程，具体操 作步骤请参见导入API头文件和链接动态库。 

步骤5 使用msSanitizer工具重新拉起程序，命令示例如下： 

$$
m s s a n i t i z e r - - c h e c - c a n n - h e a p = y e \text {- - l e a k - c h e c} = y e / a d d _ {n p u}
$$

以下输出结果表明在调用应用程序main.cpp的第55行存在一次内存分配但未释放，至 此可定位到内存泄漏的原因。 

$$
\begin{array}{l} = = = = = = E R R O R: \text {L e a k C h e c k : d e t e c t e d m e r r o l y l e a k s} \\ = = = = = \quad \text {D i r e c t} \\ = = = = = = \quad a t 0 x 1 2 4 0 8 0 0 2 4 0 0 0 o n G M a l l o c a t e d i n m a i n. c p p: 5 5 (s e r i a l N o: 0) \\ \end{array}
$$

```txt
SUMMARY: 32768 byte(s) leaked in 1 allocation(s) 
```

# ----结束

# 导入 API 头文件和链接动态库

本示例以Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组件的内 核调用符场景为例，说明导入msSanitizer API头文件“acl.h”和链接相对应的动态库 文件的具体操作步骤，其他类型的自定义工程需根据用户实际构建的脚本进行调整。 

步骤1 单击Link，获取验证代码的样例工程。 

# 说明

下载代码样例时，需执行以下命令指定分支版本。 

git clone https://gitee.com/ascend/samples.git -b v1.5-8.2.RC1 

步骤2 在${git_clone_path}/samples/operator/ascendc/0_introduction/ 3_add_kernellaunch/AddKernelInvocationNeo目录中，将main.cpp文件引入的“acl/ acl.h”头文件替换为msSanitizer工具提供头文件“acl.h” 。 

# 说明

在模板库场景下，需将Ascend C模板库/examples/common/helper.hpp路径下的#include <acl/acl.h>替换为#include "acl.h"，具体操作步骤如下。 

1. 执行以下命令，下载Link中的Ascend C模板库。 

git clone https://gitee.com/ascend/catlass.git -b catlass-v1-stable 

2. 进入/examples/common/helper.hpp代码目录。 

cd catlass/examples/common/helper.hpp 

3. 将#include <acl/acl.h>替换为#include "acl.h"。 

```cpp
include "data_utils.h" #ifndef ASCENDC_CPU_DEBUG // #include "acl/ac1.h" //acl/ac1.h替换为acl.h #include "acl.h" extern void addcustom_do( uint32_t blockDim, void *stream, uint8_t \*x, uint8_t \*y, uint8_t \*z); #else 
```

步骤3 在${git_clone_path}/samples/operator/ascendc/0_introduction/ 3_add_kernellaunch/AddKernelInvocationNeo目录下编辑CMakeLists.txt文件，导入 API头文件路径 ${INSTALL_DIR}/tools/mssanitizer/include/acl和动态库路径 

```txt
${INSTALL_DIR}/tools/mssanitizer/lib64/libascend_acl-hook.so。 
```

# 说明

● 模板库场景仅适用于Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组 件。 

● 模板库场景时，可通过以下方式增加检测编译选项。 

```cmake
-1$ENV{ASCEND_HOME_PATH}/tools/mssanitizer/include/acl
-1$ENV{ASCEND_HOME_PATH}/tools/mssanitizer/lib64
-ascend_acl-hook
add_executable(ascendc_kernels_bbit ${CMAKE_CURRENT_SOURCE_DIR}/main.cpp)
target.compile-options(ascendc_kernels_bbit PRIVATE
$<BUILD_INTERFACE:$<STREQUAL:${RUN_MODE},cpu>:-g>
-O2 -std=c++17 -D_GLIBCXX_USE_CXX11_ABI=0 -Wall -Werror)
# 算子可执行文件编译时,引入API头文件路径
target includeldirections(ascendc_kernels_bbit PUBLIC
$ENV{ASCEND_HOME_PATH}/tools/mssanitizer/include/acl) 
```

```cmake
# 算子可执行文件链接时,引入libascend_acl-hook.so动态库路径
target_linkDirectories(ascendc_kernels_bbit PRIVATE
$ENV{ASCEND_HOME_PATH}/tools/mssanitizer/lib64)
target_link_libraries(ascendc_kernels_bbit PRIVATE
$(<BUILD_INTERFACE:$<OR:$<STREQUAL:${RUN_MODE},npu>,$(STREQUAL:$
{RUN_MODE},sim>::host_intf_pub))
$(<BUILD_INTERFACE:$<STREQUAL:${RUN_MODE},cpu>:ascendcl>
ascendc_kernels $(RUN_MODE)
# 将算子可执行文件链接至libascend_acl-hook.so动态库
ascend_acl-hook 
```

步骤4 导入环境变量，并重新编译算子。 

# 说明

在安装昇腾AI处理器的服务器执行npu-smi info命令进行查询，获取Chip Name信息。实际配 置值为AscendChip Name，例如Chip Name取值为xxxyy，实际配置值为Ascendxxxyy。 

export LD.Library_PATH= ${ASCEND_HOME_PATH}\}/tools/mssanitizer/lib64:$ LD.Library_PATH
mssanitizer --check-cann-heap=yes --leak-check=yes -- bash run.sh -r npu -v Ascendcxxyy 

----结束