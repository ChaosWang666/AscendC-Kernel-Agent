<!-- Source: 算子开发工具.md lines 620-2882 | Section: 3.3 性能建模 -->

# 3.3 性能建模

# 3.3.1 原理概述

msKPP为了达到理论性能的目标，基于如下表3-1对实际处理器进行计算和搬运类指令 的性能建模。 


表 3-1 msKPP 建模假设性能


<table><tr><td>性能假设</td><td>说明</td></tr><tr><td>内部存储(LocalMemory)无限，但用户可以自己控制生命周期内的内存有限。</td><td>这个假设意味着在实际处理器的建模过程中，不考虑内存容量的限制。这允许用户或开发者可以自由地分配和使用内存资源，而不用担心内存不足的问题。在实际应用中，虽然物理内存是有限的，但这个假设可以简化模型，使得可以专注于其他性能相关的因素。</td></tr><tr><td>以统计评估的指令能力代表理论性能。</td><td>这个假设认为通过对处理器执行指令的统计分析可以得到其理论上的性能表现，处理器在执行指令时的平均性能可以反映出其最高性能潜力。这个假设有助于在设计和优化过程中，通过统计模型预测来提升处理器的性能。</td></tr><tr><td>下发无瓶颈。</td><td>这个假设意味着在数据或指令下发到处理器执行单元的过程中，不会遇到任何瓶颈或限制。也就是说，数据传输和指令调度可以无缝进行，不会因为任何硬件或软件的限制而降低性能。</td></tr></table>

# 3.3.2 算子特性建模

msKPP支持tensor拆分使用、debug模式和pipe信息的理论值与msprof实测值比对的 功能，也支持对算子特性进行建模（搬运通路建模、随路转换建模和cache命中率建 模），用户需根据实际需求进行选择，完成后可实现3.3.3 算子计算搬运规格分析、 3.3.4 极限性能分析以及3.3.5 算子tiling初步设计。 

# 说明

文档中的Ascendxxxyy需替换为实际使用的处理器类型。 

支持搬运通路建模（Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组件） 

在Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组件中，新 增了L1到fixpipe buffer(FP)的通路以及L1到Bias table(BT)的通路。前者用于 L0C_TO_OUT随路转换时存储量化转换的scale参数，后者用于存储一维的bias数 据。在本工具中对该搬运通路建模只需按照GM->L1->FP/BT的顺序即可。 

```python
in_x = Tensor("GM", "FP16", [64], format="ND")  
l1_x = Tensor("L1")  
fp_x = Tensor("FB")  
bt_x = Tensor("BT")  
l1_x.load(in_x)  
l1_x_to_fp = l1_x[0:32]  
l1_x_to_bt = l1_x[32:64]  
fp_x.load(l1_x_to_fp)  
bt_x.load(l1_x_to_bt) 
```

支持随路转换建模 

在昇腾AI处理器的CUBE单元中，进行计算的数据格式需要是特殊的私有NZ格式。 而通常在GM上的数据都是ND格式，因此在进行Cube运算时，需要将数据格式进 行转换。在Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组 件中，GM到CUBE相关的存储单元的搬运通路已具备ND转NZ的随路转换能力。 

在msKPP工具中，若GM-L1且用户定义GM的tensor是ND，L1的tensor是NZ，或 L0C-GM且用户定义L0C上的tensor是NZ，GM的tensor是ND，则开启随路转换， 调取相关实测数据。 

```python
in_x = Tensor("GM", "FP16", [128, 256], format="ND")  
l1_x1 = Tensor("L1", format="NZ")  
l1_x2 = Tensor("L1", format="NZ")  
l1_x1.load(in_x[128, 0:128])  
l1_x2.load(in_x[128, 128:]) 
```

支持Cache命中率建模 

L2Cache是指部分GM空间与vectorcore和cubecore存在高带宽的搬运通路，当 L2Cache命中率接近100%与L2Cache命中率接近0%时，带宽能有两倍以上的差 距。msKPP工具目前支持用户手动调整L2Cache命中率。 

```txt
with Chip("Ascendxxxxy") as chip: config = {"cache_hit_ratio": 0.6}  
chip.set_cache_hit_ratio(config) 
```

支持Tensor拆分使用 

msKPP工具中，Tensor拆分是指将一个大的Tensor用切片的手段生成新的小 Tensor，例如： 

```python
in_x = Tensor("GM", "FP16", [128, 256], format="ND")  
in_x_1 = in_x[128, 0:128] # 大小1*128  
in_x_2 = in_x[128, 64:] # 大小1*64 
```

支持debug模式 

该模式可使能用户初步定位DSL语言编码过程中哪个指令的出队入队存在问题，提 升与工具开发共同定位的效率，使能方式如下： 

with Chip("Ascendxxxyy", debug_mode=True) as chip: 

支持PIPE信息的理论值与msprof实测值比对 

以Ascend C算子为例，通过--application方式调用msprof，在 OPPROF_{timestamp}_XXX目录中输出PipeUtilization.csv文件，并在脚本中使 能： 

```txt
with Chip("Ascendxxxx") as chip:  
    chip.enable.metrics()  
    chip.set PROF.summary_path("/home/xx/OPPROF-{timestamp}|XXX/PipeUtilization.csv") 
```

生成的Pipe_statistic.csv文件包含“ProfDuration(us)_0”和“ProfRatio_0”两 列，其中ProfDuration(us)_0列的取值和PipeUtilization.csv文件中对应的值一 致，ProfRatio_0为实测值跟理论值的比值。 ProfRatio是实测值相对理论值的倍 数，倍数越大，优化空间越大。 


图 3-1 Pipe_statistic.csv 文件


![](images/779edfb381421b1a2b4edaeb412b3ef9a52e5ec974f954316af87c7c7a466693.jpg)


# 3.3.3 算子计算搬运规格分析

# 说明

文档中的Ascendxxxyy需替换为实际使用的处理器类型。 

以matmul算子为例，该用例表示准备处理[160, 240]和[240, 80]的矩阵乘，切割为5 个[32, 48]、[48, 16]和[32, 16]的小矩阵做矩阵乘。通过调用msKPP提供的接口实现 的main.py脚本样例如下： 

```python
from sklearn import mpad, Tensor, Chip
def my_mmad(gm_x, gm_y, gm_z):
    # 矩阵乘的基本数据通路:
    # 左矩阵x: GM-L1-L0A
    # 右矩阵y: GM-L1-L0B
    # 结果矩阵z: L0C(初始化)-GM
    # 样例数学表达式: z = x @ y + b
    # 定义和分配L1上的变量
    l1_x = Tensor("L1")
    l1_y = Tensor("L1")
    # 定义和分配L0A和L0B上的变量
    x = Tensor("L0A")
    y = Tensor("L0B")
    # 定义和分配在LOC上的偏置项, 理论上应该分配在累加器Buffer上, 分配在LOC不影响性能
    b = Tensor("L0C", "FP32", [32, 16], format="NC1HWC0")
    # 将GM上的数据移动到L1对应内存空间上
    l1_x.load(gm_x)
    l1_y.load(gm_y)
    # 将L1上的左右矩阵移动到L0A和L0B上
    x.load(l1_x)
    y.load(l1_y)
    # 当前数据已加载到L0A和L0B上, 调用指令进行计算, 结果保存在LOC上, out是mrad函数内部在LOC中分配的变量
    out = mrad(x, y, b, True())
    # 将LOC上的数据移动到GM变量gm_z的地址空间上
    gm_z.load(out[0])
    return gm_z
if __name__ == '__main__':
    with Chip("Ascendxxxxy") as chip:
        chip.enable_trace() # 使能算子模拟流水图的功能, 生成trace.json文件
        chip.enable.metrics() # 使能单指令及分PIPE的流水信息, 生成Instruction_statistics.csv和Pipe statistic.csv文件
        # 模拟一个大矩阵被切分成5个小矩阵进行计算
        for _ in range(5):
            # 应用算子进行AICORE计算
            in_x = Tensor("GM", "FP16", [32, 48], format="ND")
            in_y = Tensor("GM", "FP16", [48, 16], format="ND") 
```

```python
in_z = Tensor("GM", "FP32", [32, 16], format="NC1HWC0")  
my_mmad(in_x, in_y, in_z) 
```

使用Python执行以上main.py脚本后，会在当前路径/MSKPPTIMESTAMP目录下生成 搬运流水统计文件（Pipe_statistic.csv）和指令信息统计文件 （Instruction_statistic.csv），可查看msKPP建模结果。 

# 说明

TIMESTAMP为当前时间戳。 

# 搬运流水统计

搬运流水统计文件Pipe_statistic.csv，该文件统计了不同PIPE的总搬运数据量大小、 操作数个数以及耗时信息。 


图 3-2 Pipe_statistic.csv


<table><tr><td>Pipe</td><td>Duration(us)</td><td>Cycle</td><td>Size(B)</td><td>Ops</td></tr><tr><td>Total</td><td>5.2622</td><td>11095</td><td>56320</td><td>122880</td></tr><tr><td>PIPE-MTE2</td><td>5.0472</td><td>9085</td><td>23040</td><td>-</td></tr><tr><td>PIPE-MTE1</td><td>0.0667</td><td>120</td><td>23040</td><td>-</td></tr><tr><td>PIPE-V</td><td>0.025</td><td>45</td><td>-</td><td>122880</td></tr><tr><td>PIPE-FIX</td><td>1.025</td><td>1845</td><td>10240</td><td>-</td></tr></table>

关键字段说明如下。 


表 3-2 字段说明


<table><tr><td>字段名</td><td>字段解释</td></tr><tr><td>Pipe</td><td>表示昇腾处理器中不同PIPE单元的名称。</td></tr><tr><td>Duration(us)</td><td>PIPE耗时，单位us。</td></tr><tr><td>Cycle</td><td>各个指令每次执行时消耗的cycle数。</td></tr><tr><td>Size(B)</td><td>表示搬运类PIPE的搬运量大小，单位B。</td></tr><tr><td>Ops</td><td>表示计算类PIPE的计算元素大小。</td></tr></table>

对于流水线耗时最长，明显是搬运性能瓶颈的PIPE，通常有如下优化思路： 

若搬运数据量较大时，尽可能一次搬运较多的数据，充分利用搬运带宽。 

尽可能保证性能瓶颈的PIPE在流水上一直在工作。 

# 指令信息统计

指令信息统计文件Instruction_statistic.csv，该文件统计了不同指令维度的总搬运数 据量大小、操作数个数以及耗时信息，能够发现指令层面上的瓶颈主要在MOV-GM_TO_L1（属于PIPE-MTE2），从指令层面找到了性能瓶颈处。 


图 3-3 Instruction_statistic.csv


<table><tr><td>Instruction</td><td>Duration(us)</td><td>Cycle</td><td>Size(B)</td><td>Ops</td></tr><tr><td>MOV-GM_TO_L1</td><td>5.0472</td><td>9085</td><td>23040</td><td>-</td></tr><tr><td>MOV-L1_TO_L0A</td><td>0.0417</td><td>75</td><td>15360</td><td>-</td></tr><tr><td>MOV-L1_TO_L0B</td><td>0.025</td><td>45</td><td>7680</td><td>-</td></tr><tr><td>MMAD</td><td>0.025</td><td>45</td><td>-</td><td>122880</td></tr><tr><td>MOV-L0C_TO_GM</td><td>1.025</td><td>1845</td><td>10240</td><td>-</td></tr></table>

关键字段说明如下。 


表 3-3 字段说明


<table><tr><td>字段名</td><td>字段解释</td></tr><tr><td>Instruction</td><td>指令名称。</td></tr><tr><td>Duration(us)</td><td>PIPE耗时，单位us。</td></tr><tr><td>Cycle</td><td>各个指令每次执行时消耗的cycle数。</td></tr><tr><td>Size(B)</td><td>表示搬运类PIPE的搬运量大小，单位B。</td></tr><tr><td>Ops</td><td>表示计算类PIPE的计算元素大小。</td></tr></table>

# 3.3.4 极限性能分析

# 说明

文档中的Ascendxxxyy需替换为实际使用的处理器类型。 

以matmul算子为例，该用例表示准备处理[160, 240]和[240, 80]的矩阵乘，切割为5 个[32, 48]、[48, 16]和[32, 16]的小矩阵做矩阵乘。通过调用msKPP提供的接口实现 的main.py脚本样例如下： 

```python
from sklearn import mammad, Tensor, Chip
def my_mammad(gm_x, gm_y, gm_z):
    # 矩阵乘的基本数据通路:
    # 左矩阵x: GM-L1-L0A
    # 右矩阵y: GM-L1-L0B
    # 结果矩阵z: LOC(初始化)-GM
    # 样例数学表达式: z = x @ y + b
    # 定义和分配L1上的变量
    l1_x = Tensor("L1")
    l1_y = Tensor("L1")
    # 定义和分配LOA和LOB上的变量
    x = Tensor("LOA")
    y = Tensor("LOB")
    # 定义和分配在LOC上的偏置项,理论上应该分配在累加器Buffer上,分配在LOC不影响性能
    b = Tensor("L0C", "FP32", [32, 16], format="NC1HWC0")
    # 将GM上的数据移动到L1对应内存空间上
    l1_x.load(gm_x)
    l1_y.load(gm_y)
    # 将L1上的左右矩阵移动到LOA和LOB上
    x.load(l1_x)
    y.load(l1_y)
    # 当前数据已加载到LOA和LOB上,调用指令进行计算,结果保存在LOC上,out是mammad函数内部在LOC中分配的变量
    out = mammad(x, y, b, True())
    # 将LOC上的数据移动到GM变量gm_z的地址空间上 
```

```python
gm_z.load(out[0])  
return gm_z  
if __name__ == __main__:  
    with Chip("Ascendxxxxy") as chip:  
        chip.enable_trace() # 使能算子模拟流水图的功能，生成trace.json文件  
        chip(enable.metrics() # 使能单指令及分PIPE的流水信息，生成Instruction_statistics.csv和Pipe_statistic.csv)  
文件  
# 模拟一个大矩阵被切分成5个小矩阵进行计算  
for _ in range(5):  
    # 应用算子进行AICORE计算  
    in_x = Tensor("GM", "FP16", [32, 48], format="ND")  
    in_y = Tensor("GM", "FP16", [48, 16], format="ND")  
    in_z = Tensor("GM", "FP32", [32, 16], format="NC1HWC0")  
    my_mmad(in_x, in_y, in_z) 
```

使用Python执行以上main.py脚本后，会在当前路径/MSKPPTIMESTAMP目录下生成 文件指令流水图（trace.json）和指令占比饼图 （instruction_cycle_consumption.html），可查看msKPP建模结果。 

# 说明

TIMESTAMP为当前时间戳。 

# 指令流水图

流水图文件trace.json，通过查看该文件可以发现在理想的流水中，性能瓶颈的PIPE-MTE2是需要能够一直进行运转的。 

# 说明

在Chrome浏览器中输入“chrome://tracing”地址，将.json文件拖到空白处并打开，通过键盘 上的快捷键（W：放大，S：缩小，A：左移，D：右移）进行查看。 


图 3-4 trace.json


![](images/f59577b1934c483f3cb5d5b505dc721b4b10e7aa819fbff9a986cd02c439a054.jpg)


单击流水图中的“MOV-GM_TO_L1”单指令，可查看该指令在当前搬运量及计算量下 的cycle数和带宽，如图3-5所示。 


图3-5 指令详细信息


![](images/2417b05d345558b2fa0a4a5b3b33a2fd62eb0ce3de6eaebd6214ff7cc0370510.jpg)


# 指令占比饼图

生成了指令占比饼图instruction_cycle_consumption.html，从中可以发现MOV-GM_TO_L1是算子里的最大瓶颈。 


图 3-6 指令耗时统计


![](images/73b3eb16c9e2bfecf783f76bf9e178b0625a3aa455f269755dbda63eaa9bb9a1.jpg)


![](images/355ab0906e8d8e0dfb4a009ea93d911d809ba5cc73099a77575b6f5bff1f65df.jpg)


# 3.3.5 算子 tiling 初步设计

tiling策略的模拟体现在算子功能函数的for循环中，进行切分时，需确保每次for循环 处理的数据量相同。 

# 说明

文档中的Ascendxxxyy需替换为实际使用的处理器类型。 

# 具体操作

以matmul算子为例，该用例表示模拟一个大矩阵被切分成小矩阵进行矩阵乘计算。需 根据用户算子逻辑方案实现算子功能函数。tiling策略的模拟体现在算子功能函数的for 循环中（以下代码中加粗部分），例如单核处理[160, 240]和[240, 80]的矩阵乘，切 割为25个[32, 48]和[48, 16]的小矩阵分批处理，就需要for循环25次并每次创建大小为 [32, 48]和[48, 16]的Tensor矩阵（在GM上）。 

```python
from mskpp import mmad, Tensor, def my_mmad(gm_x, gm_y, gm_z): # 矩阵乘的基本数据通路: # 左矩阵A: GM-L1-L0A # 右矩阵B: GM-L1-L0B # 结果矩阵C: LOC(初始化)-GM l1_x = Tensor("L1") l1_y = Tensor("L1") l1_x.load(gm_x) 
```

```python
l1_y.load(gm_y)  
x = Tensor("L0A")  
y = Tensor("L0B")  
x.load(l1_x)  
y.load(l1_y)  
z = Tensor("L0C", "FP32", [32, 16], format="NC1HWC0")  
out = mmad(x, y, z, True()) # 对于输出需要返回传出  
z = out[0]  
return z  
if __name__ == '__main__':  
    with Chip("Ascendxxxyy") as chip:  
    chip.enable_trace() # 使能算子模拟流水图的功能，生成trace.json文件  
    chip.enable.metrics() # 使能单指令及分Pipe的流水信息，生成Instruction_statistics.csv和  
Pipe_statistic.csv文件  
# 这里进入了对数据切分逻辑的处理，对一大块GM的数据，如何经过拆分成小数据分批次搬入，如何对  
# 内存进行分片多buffer搬运，都是属于Tiling策略的范畴，这里模拟了单buffer情况，  
# 将[160, 240]和[240, 80]的矩阵乘，切割为25个[32, 48]和[48, 16]的小矩阵分批次进行运算的一个  
Tiling策略  
for _in range(25):  
    in_x = Tensor("GM", "FP16", [32, 48], format="ND")  
    in_y = Tensor("GM", "FP16", [48, 16], format="ND")  
    in_z = Tensor("GM", "FP32", [32, 16], format="NC1HWC0")  
    out_z = my_mmad(in_x, in_y, in_z)  
    in_z.load(out_z) 
```

# 3.3.6 对外接口使用说明

# 3.3.6.1 接口列表

msKPP工具包括基础功能接口和指令接口两种接口类型。基础功能接口用于模拟算子 计算中芯片平台、基础数据等。指令接口用于模拟特定的算子指令操作，包括vector类 计算类指令和cube类计算指令。 


表 3-4 msKPP 工具接口列表


<table><tr><td>接口类型</td><td>接口名称</td><td>接口简介</td></tr><tr><td rowspan="4">基础功能接口</td><td>Chip</td><td>创建性能建模的芯片平台,初始化芯片各项性能数据。</td></tr><tr><td>Core</td><td>模拟芯片内部的AI Core。</td></tr><tr><td>Tensor</td><td>算子执行基础数据类型。</td></tr><tr><td>Tensor.load</td><td>数据搬运接口,对数据在不同单元搬运进行建模。</td></tr><tr><td rowspan="2">同步类指令接口</td><td>set_flag</td><td>核内PIPE间同步的指令接口,与wait_flag配套使用。</td></tr><tr><td>wait_flag</td><td>核内PIPE间同步的指令接口,与set_flag配套使用。</td></tr><tr><td rowspan="5">指令接口</td><td>mmad</td><td>对cube类指令的mmad性能建模接口。</td></tr><tr><td>vadd</td><td>对vector类指令的vadd性能建模接口。</td></tr><tr><td>vbrcb</td><td>对vector类指令的vbrcb性能建模接口。</td></tr><tr><td>vconv</td><td>对vector类指令的vconv性能建模接口。</td></tr><tr><td>vconv_deq</td><td>对vector类指令的vconv_deq性能建模接口。</td></tr><tr><td rowspan="30"></td><td>vconv_vdeq</td><td>对vector类指令的vconv_vdeq性能建模接口。</td></tr><tr><td>vector_dup</td><td>对vector类指令的vector_dup性能建模接口。</td></tr><tr><td>vexp</td><td>对vector类指令的vexp性能建模接口。</td></tr><tr><td>vln</td><td>对vector类指令的vln性能建模接口。</td></tr><tr><td>vmax</td><td>对vector类指令的 vmax性能建模接口。</td></tr><tr><td>vmul</td><td>对vector类指令的vmul性能建模接口。</td></tr><tr><td>vmuls</td><td>对vector类指令的vmuls性能建模接口。</td></tr><tr><td>vsub</td><td>对vector类指令的vsub性能建模接口。</td></tr><tr><td>vdiv</td><td>对vector类指令的vdiv性能建模接口。</td></tr><tr><td>vcadd</td><td>对vector类指令的vcadd性能建模接口。</td></tr><tr><td>vabs</td><td>对vector类指令的vabs性能建模接口。</td></tr><tr><td>vaddrelu</td><td>对vector类指令的vaddrelu性能建模接口。</td></tr><tr><td>vaddreluconv</td><td>对vector类指令的vaddreluconv性能建模接口。</td></tr><tr><td>vadds</td><td>对vector类指令的vadds性能建模接口。</td></tr><tr><td>vand</td><td>对vector类指令的vand性能建模接口。</td></tr><tr><td>vaxpy</td><td>对vector类指令的vaxpy性能建模接口。</td></tr><tr><td>vbitsort</td><td>对vector类指令的vbitsort性能建模接口。</td></tr><tr><td>vcgadd</td><td>对vector类指令的vcgadd性能建模接口。</td></tr><tr><td>vcgmax</td><td>对vector类指令的vcgmax性能建模接口。</td></tr><tr><td>vcgmin</td><td>对vector类指令的vcgmin性能建模接口。</td></tr><tr><td>vcmax</td><td>对vector类指令的vcmax性能建模接口。</td></tr><tr><td>vcmin</td><td>对vector类指令的vcmin性能建模接口。</td></tr><tr><td>vcmp_xxx</td><td>对vector类指令的vcmp_xxx性能建模接口。</td></tr><tr><td>vcmpv_xxx</td><td>对vector类指令的vcmpv_xxx性能建模接口。</td></tr><tr><td>vcmpvs_xxx</td><td>对vector类指令的vcmpvs_xxx性能建模接口。</td></tr><tr><td>vcopy</td><td>对vector类指令的vcopy性能建模接口。</td></tr><tr><td>vcpadd</td><td>对vector类指令的vcpadd性能建模接口。</td></tr><tr><td>vgather</td><td>对vector类指令的vgather性能建模接口。</td></tr><tr><td>vgatherb</td><td>对vector类指令的vgatherb性能建模接口。</td></tr><tr><td>vlrelu</td><td>对vector类指令的vlrelu性能建模接口。</td></tr><tr><td rowspan="22"></td><td>vmadd</td><td>对vector类指令的vmadd性能建模接口。</td></tr><tr><td>vmaddrelu</td><td>对vector类指令的vmaddrelu性能建模接口。</td></tr><tr><td>vmaxs</td><td>对vector类指令的vmaxs性能建模接口。</td></tr><tr><td>vmin</td><td>对vector类指令的vmin性能建模接口。</td></tr><tr><td>vmins</td><td>对vector类指令的vmins性能建模接口。</td></tr><tr><td>vmla</td><td>对vector类指令的vmla性能建模接口。</td></tr><tr><td>vmrgsort</td><td>对vector类指令的vmrgsort性能建模接口。</td></tr><tr><td>vmulconv</td><td>对vector类指令的vmulconv性能建模接口。</td></tr><tr><td>vnot</td><td>对vector类指令的vnot性能建模接口。</td></tr><tr><td>vor</td><td>对vector类指令的vor性能建模接口。</td></tr><tr><td>vrec</td><td>对vector类指令的vrec性能建模接口。</td></tr><tr><td>vreduce</td><td>对vector类指令的vreduce性能建模接口。</td></tr><tr><td>vreducev2</td><td>对vector类指令的vreducev2性能建模接口。</td></tr><tr><td>vrelu</td><td>对vector类指令的vrelu性能建模接口。</td></tr><tr><td>vrsqrt</td><td>对vector类指令的vrsqrt性能建模接口。</td></tr><tr><td>vsel</td><td>对vector类指令的vsel性能建模接口。</td></tr><tr><td>vshl</td><td>对vector类指令的vshl性能建模接口。</td></tr><tr><td>vshr</td><td>对vector类指令的vshr性能建模接口。</td></tr><tr><td>vsqrt</td><td>对vector类指令的vsqrt性能建模接口。</td></tr><tr><td>vsubrelu</td><td>对vector类指令的vsubrelu性能建模接口。</td></tr><tr><td>vsubreluconv</td><td>对vector类指令的vsubreluconv性能建模接口。</td></tr><tr><td>vtranspose</td><td>对vector类指令的vtranspose性能建模接口。</td></tr></table>

# 3.3.6.2 基础功能接口

# 3.3.6.2.1 Chip

# 功能说明

处理器抽象，在with语句中实例化并用来明确针对某一昇腾AI处理器类型进行建模。 

# 接口原型

class Chip(name, debug_mode=False) 

# 参数说明

<table><tr><td>参数名</td><td>输入类型</td><td>说明</td></tr><tr><td>name</td><td>string</td><td>处理器名称。
目前大部分数据基于Atlas A2 训练系列产品/Atlas 800I A2 推理产品/A200I A2 Box 异构组件采集，使用npu-smi info可以查看当前设备昇腾AI处理器类型。</td></tr><tr><td>debug_mode</td><td>bool</td><td>是否启用调试模式，默认为False。
• True: 启用
• False: 不启用
说明
开启debug模式后可查看未正确运行的指令，但不会生成任何输出件。</td></tr></table>

# 成员

<table><tr><td>成员名称</td><td>描述</td></tr><tr><td>chip enabling_trace()</td><td>使能算子模拟流水图的功能，生成流水图文件trace.json。</td></tr><tr><td>chip enabling_metric(   )</td><td>使能单指令及分PIPE的流水信息，生成指令统计 (InstructionStatistic.csv)、搬运流水统计 (Pipe statistic.csv) 文件和指令占比饼图 (instruction_cycleconsumption.html)。</td></tr><tr><td>chip.set_cache_hi_ratio(config)</td><td>用于使能手动调整L2Cache命中率，其中config = {&quot;cache_hit_ratio&quot;: 0.6}, 具体介绍请参见支持cache命中率建模。</td></tr><tr><td>chip.setprof_summary_path(&quot;xx/ PipeUtilization.csv&quot;)</td><td>其中PipeUtilization.csv为msprof的结果示例，用于使能PIPE信息的理论值与msprof实测值比对。具体介绍请参见支持PIPE信息的理论值与msprof实测值比对。</td></tr><tr><td>chip.disable_inst_r_log(   )</td><td>使能后，抑制指令任务添加和调度结束后的日志打印。</td></tr></table>

# 约束说明

需在with语句下将该类初始化。 

# 使用示例

from mskpp import Chip # 如何查看当前设备昇腾处理器类型请参见以下说明 with Chip("Ascendxxxyy") as chip: # Ascendxxxyy需替换为实际使用的处理器类型 chip.enable_trace() # 调用该函数即可使能算子模拟流水图的功能，生成流水图文件 

chip.enable_metrics() # 调用该函数即可使能单指令及分PIPE的流水信息，生成搬运流水统计、指令信息统计 和指令占比饼图 

# 说明

非Atlas A3 训练系列产品/Atlas A3 推理系列产品：在安装昇腾AI处理器的服务器执行npu-smi info命令进行查询，获取Chip Name信息。实际配置值为AscendChip Name，例如Chip Name 取值为xxxyy，实际配置值为Ascendxxxyy。当Ascendxxxyy为代码样例的路径时，需要配置为 ascendxxxyy。 

# 3.3.6.2.2 Core

# 功能说明

AI Core抽象，在with语句中实例化并用来明确针对某一AI Core类型进行建模。 

# 接口原型

class Core(core_type_name) 

# 参数说明

<table><tr><td>参数名</td><td>输入类型</td><td>说明</td></tr><tr><td>core_type_name</td><td>string</td><td>昇腾计算单元类型字符串，通常可以表示为“AICx”或“AIVx”，其中x为数字，即使用的AI Cube Core/ AI Vector Core的序号。仅支持A-Za-z0-9中的一个或多个字符。</td></tr></table>

# 约束说明

需在with语句下将该类初始化。 

# 使用示例

from mskpp import Core with Core("AIC0") as aic: # AI Cube Core 0上的算子计算逻辑相关代码 .. 

# 3.3.6.2.3 Tensor

# 功能说明

片上Tensor的抽象，可指定Tensor的内存位置、数据类型、大小及排布格式作为指令 的数据依赖标识。 

# 接口原型

class Tensor(mem_type, dtype=None, size=None, format=None, is_inited=False) 

# 参数说明

<table><tr><td>参数名</td><td>输入类型</td><td>说明</td></tr><tr><td>mem_type</td><td>字符串</td><td>抽象Tensor所处的内存空间的位置，如“GM”、“UB”、“L1”、“LOA”、“LOB”、“LOC”、“FB”、“BT”等。</td></tr><tr><td>dtype</td><td>字符串</td><td>数据类型，如BOOL、UINT1、UINT2、UINT8、UINT16、UINT32、BF16、UINT64、INT4、INT8、INT16、INT32、INT64、FP16、FP32。</td></tr><tr><td>size</td><td>list</td><td>Tensor的shape。</td></tr><tr><td>format</td><td>字符串</td><td>数据排布格式，详细可参见《Ascend C算子开发指南》的“附录 &gt; Tensor基础知识参考 &gt; 数据排布格式”章节。</td></tr><tr><td>is_initd</td><td>bool</td><td>控制Tensor类是否已就绪的开关，开启后，以该Tensor为输入的指令即可启动。</td></tr></table>

# 成员

<table><tr><td>成员名称</td><td>描述</td></tr><tr><td>tensor.set_valid()</td><td>使能当前tensor就绪，开启后，以该tensor为输入的指令即可立即启动。</td></tr><tr><td>tensor.setinelid()</td><td>使当前tensor处于非就绪状态，关闭后，以该tensor为输入的指令不可立即启动。</td></tr><tr><td>tensor.is_valid()</td><td>用于获取当前的tensor就绪状态。</td></tr></table>

# 约束说明

需通过创建一个shape为[1]且is_inited=True的Tensor进行标量创建。 

# 使用示例

```python
from sklearn import Tensor, Core  
gm_tmp = Tensor("GM", "FP16", [48, 16], format="ND")  
with Core("AIV0") as aiv: # AIV0上的相关计算逻辑  
...  
gm_tmp.load(result, set_value=0)  
with Core("AIC0") as aic:  
in_x = Tensor("GM", "FP16", [48, 16], format="ND")  
in_x.load(gm_tmp, expect_value=0) # AIC0上的相关计算逻辑 
```

# 3.3.6.2.4 Tensor.load

# 功能说明

所有的数据搬运指令在msKPP工具下都抽象为load方法，用户只需关心昇腾AI处理器 中合理的搬运通路，无需考虑搬运指令中复杂的stride概念。 

# 接口原型

Tensor.load(tensor, repeat=1, set_value=-1, expect_value=-1) 

# 参数说明

<table><tr><td>参数名</td><td>输入类型</td><td>说明</td></tr><tr><td>tensor</td><td>变量</td><td>输入的其他tensor，其功能与接口中Tensor的定义一致。</td></tr><tr><td>repeat</td><td>int</td><td>该参数是对搬运指令repeat的模拟，通过输入该值可获取不同repeat值下搬运通路的带宽值，该带宽值用于计算搬运指令的耗时。
非必选参数，默认值为1，建议值为[1,255]之间的整数。
当输入的repeat值不满足要求时，系统将会抛出异常：&quot;input repeat = xx invalid.&quot;,其中xx为输入的异常repeat值。</td></tr><tr><td>set_value</td><td>int</td><td>设置此tensor数据被依赖的标识号，可以自己定义，需与expect_value配对使用。
非必选参数，不输入则不会使能依赖关系。</td></tr><tr><td>expect_value</td><td>int</td><td>设置此tensor数据加载依赖数据的标识号，可以自己定义，需与set_value配对使用。
非必选参数，不输入则不会使能依赖关系。</td></tr></table>

# 约束说明

set_value和expect_value需配对使用，否则可能会造成流水阻塞。 

repeat参数仅支持以下4条搬运通路：L1_TO_L0A、L1_TO_L0B、GM_TO_L0A和 GM_TO_L0B。 

# 3.3.6.3 同步类指令接口

# 3.3.6.3.1 set_flag

# 功能说明

用于确保核内各PIPE间不同指令的同步，pipe_src先完成调度后，pipe_dst将解除阻塞 状态。设置set_flag和3.3.6.3.2 wait_flag之后，指令流水图将会更贴合用户的调用预 期。 

# 接口原型

set_flag(pipe_src, pipe_dst, event_id) 

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>说明</td></tr><tr><td>pipe_src</td><td>输入</td><td>源PIPE，在pipe_src调度后设置event_id。取值范围为&quot;PIPE-MTE1&quot;、&quot;PIPE-MTE2&quot;、&quot;PIPE-MTE3&quot;、&quot;PIPE-FIX&quot;、&quot;PIPE-M&quot;、&quot;PIPE-V&quot;、&quot;PIPE-S&quot;。数据类型：string。必选参数。</td></tr><tr><td>pipe.dst</td><td>输入</td><td>目的PIPE，在pipe_src调度之后，pipe.dst将会解除阻塞状态。取值范围为&quot;PIPE-MTE1&quot;、&quot;PIPE-MTE2&quot;、&quot;PIPE-MTE3&quot;、&quot;PIPE-FIX&quot;、&quot;PIPE-M&quot;、&quot;PIPE-V&quot;、&quot;PIPE-S&quot;。数据类型：string。必选参数。</td></tr><tr><td>event_id</td><td>输入</td><td>同步指令之间依赖的唯一值。取值范围[0, 65535]。数据类型：int。必选参数。</td></tr></table>

# 约束说明

在同一核内set_flag与wait_flag个数需匹配。 

同核内不应出现重复的set_flag指令。 

同一核内，当set_flag和wait_flag内的pipe_src和pipe_dst相同时，event_id也应 保持唯一。 

# 使用示例

```python
from sklearn import Tensor, Chip, set_flag, wait_flag  
with Chip("Ascendxxy") as chip:  
gm_weight = Tensor("GM", "FP16", [128, 256], format="ND")  
l1_weight = Tensor("L1", "FP16", [128, 256], format="ND")  
for convidx in range(4): # L0A数据加载前，GM分批加载到L1上  
gm_weight_part = gm_weight[:, 64]  
l1_weight_part = l1_weight[:, 64]  
l1_weight_part.load(gm_weight_part)  
if convidx == 3:  
    set_flag("PIPE-MTE2", "PIPE-MTE1", 1) # 当完成MTE2，才可以执行MTE1  
x = Tensor("LOA") # L0A  
# 正在执行MTE2操作，MTE1操作需要等待MTE2完成才能执行。  
l1_weight.set_valid() # 手动使能L1  
wait_flag("PIPE-MTE2", "PIPE-MTE1", 1)  
x.load(l1_weight) 
```

# 3.3.6.3.2 wait_flag

# 功能说明

用于确保核内各PIPE间不同指令的同步，pipe_dst等待pipe_src完成调度之后解除阻塞 状态。 

# 接口原型

wait_flag(pipe_src, pipe_dst, event_id) 

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>说明</td></tr><tr><td>pipe_src</td><td>输入</td><td>源PIPE，在pipe_src调度后设置event_id。取值范围为&quot;PIPE-MTE1&quot;、&quot;PIPE-MTE2&quot;、&quot;PIPE-MTE3&quot;、&quot;PIPE-FIX&quot;、&quot;PIPE-M&quot;、&quot;PIPE-V&quot;、&quot;PIPE-S&quot;。数据类型：string。必选参数。</td></tr><tr><td>pipe.dst</td><td>输入</td><td>目的PIPE，在pipe_src调度之后，pipe.dst将会解除阻塞状态。取值范围为&quot;PIPE-MTE1&quot;、&quot;PIPE-MTE2&quot;、&quot;PIPE-MTE3&quot;、&quot;PIPE-FIX&quot;、&quot;PIPE-M&quot;、&quot;PIPE-V&quot;、&quot;PIPE-S&quot;。数据类型：string。必选参数。</td></tr><tr><td>event_id</td><td>输入</td><td>同步指令之间依赖的唯一值。取值范围[0, 65535]。数据类型：int。必选参数。</td></tr></table>

# 约束说明

在同一核内set_flag与wait_flag个数需匹配。 

同核内不应出现重复的set_flag指令。 

同一核内，当set_flag和wait_flag内的pipe_src和pipe_dst相同时，event_id也应 保持唯一。 

# 使用示例

```python
from mskpp import Tensor, Chip, set_flag, wait_flag  
with Chip("Ascendxxyy") as chip:  
gm_weight = Tensor("GM", "FP16", [128, 256], format="ND")  
l1_weight = Tensor("L1", "FP16", [128, 256], format="ND")  
for convidx in range(4): # L0A数据加载前，GM分批加载到L1上  
gm_weight_part = gm_weight[;, 64]  
l1_weight_part = l1_weight[;, 64] 
```

```python
l1_weight_part.load(gm_weight_part) if conv_idx == 3: set_flag("PIPE-MTE2","PIPE-MTE1",1)#当完成MTE2，才可以执行MTE1 x = Tensor("LOA") #LOA #正在执行MTE2操作，MTE1操作需要等待MTE2完成才能执行。   
l1_weight.set_valid() #手动使能L1 wait_flag("PIPE-MTE2","PIPE-MTE1",1)   
x.load(l1_weight) 
```

# 3.3.6.4 指令接口

# 3.3.6.4.1 mmad

# 功能说明

完成矩阵乘加操作。 

# 接口原型

```txt
class mmad(x, y, b, is_init=False) 
```

# 参数说明

<table><tr><td>参数名</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>Tensor变量</td><td>左矩阵，在“LOA”空间。支持FP16。</td></tr><tr><td>y</td><td>Tensor变量</td><td>右矩阵，在“LOB”空间。支持FP16。</td></tr><tr><td>b</td><td>Tensor变量</td><td>偏置项，可以在“LOC”空间或Bias Table空间。支持 FP32。</td></tr><tr><td>is_init</td><td>bool</td><td>当输入是在“LOC”空间时，需要加is_init=True，因为不存在通路将数据从GM直接搬运到LOC。</td></tr></table>

# 约束说明

偏置项在Bias Table空间时，其Tensor的数据格式需为ND，shape是[n, ]。 

# 使用示例

```python
from mskpp import mmad, Tensor  
in_x = Tensor("GM", "FP16", [32, 48], format="ND")  
in_y = Tensor("GM", "FP16", [48, 16], format="ND")  
in_z = Tensor("GM", "FP32", [32, 16], format="NC1HWC0")  
out_z = mmad(in_x, in_y, in_z)() 
```

# 3.3.6.4.2 vadd

# 功能说明

vadd指令抽象。 

$z = x + y$ ，x、y按元素相加。 

# 接口原型

class vadd(x, y, z) 

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor，支持FP16、FP32、INT16、INT32。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入y向量Tensor，支持FP16、FP32、INT16、INT32。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。</td></tr></table>

# 约束说明

vector指令所有输入输出数据的Tensor均在“UB”空间中，shape需保持一致。 

# 使用示例

```python
from mskpp import vadd, Tensor  
ub_x, ub_y, ub_z = Tensor("UB"), Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vadd(ub_x, ub_y, ub_z()) 
```

# 3.3.6.4.3 vbrcb

# 功能说明

vbrcb指令抽象。 

根据指令的stride将Tensor进行扩维，由于目前msKPP工具的指令体系里并没有stride 的概念，需要用户填写如何扩维倍数，并保持输入输出Tensor的shape维度一致。 

# 接口原型

class vbrcb(x, y, broadcast_num) 

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持UINT16、UINT32。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出y向量Tensor。支持UINT16、UINT32。</td></tr><tr><td>broadca st_num</td><td>输入</td><td>int</td><td>指定最后一维扩维到多少倍，实测性能数据不同扩维倍数对性能影响不大，因此直接以常用的扩维16倍数据为准（对应指令的dstBlockStride=1，dstRepeatStride=8）。</td></tr></table>

# 使用示例

```python
from mskpp import vbrcb, Tensor  
ub_x, ub_y = Tensor("UB"), Tensor("UB")  
gm_x = Tensor("GM")  
broadcast_num = 16  
ub_x.load(gm_x)  
out = vbrcb(ub_x, ub_y, broadcast_num()) 
```

# 3.3.6.4.4 vconv

# 功能说明

vconv指令抽象。 

y = vconv(x, dtype)，vconv表示对输入数据进行类型转换的向量计算。 

目前支持转换类型包括：BF16->FP32、FP16->FP32、FP16->INT16、FP16->INT32、 FP16->INT4、FP16->INT8、FP16- $\cdot >$ UINT8、FP32- $\cdot >$ BF16、FP32->FP16、FP32- >INT32、FP32->INT64、INT4->FP16、INT64->FP32、INT8->FP16、UINT8- >FP16。 

# 接口原型

```txt
class vconv(x, y, dtype) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出y向量Tensor。</td></tr><tr><td>dtype</td><td>输入</td><td>字符串</td><td>表示目标Tensor的数据类型。</td></tr></table>

# 使用示例

```python
from mskpp import vconv, Tensor  
ub_x, ub_y = Tensor("UB", "FP16"), Tensor("UB")  
gm_x = Tensor("GM")  
ub_x.load(gm_x)  
out = vconv(ub_x, ub_y, "FP32")() 
```

# 3.3.6.4.5 vconv_deq

# 功能说明

vconv_deq指令抽象。 y = vconv_deq(x, dtype)，vconv_deq表示对输入数据进行量化操作的向量计算。 目前支持转换类型包括：FP16->INT8、INT32>FP16。 

# 接口原型

```txt
class vconv_deq(x, y, dtype) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出y向量Tensor。</td></tr><tr><td>dtype</td><td>输入</td><td>字符串</td><td>表示目标Tensor的数据类型。</td></tr></table>

# 使用示例

```python
from sklearn import vconv_deq, Tensor  
ub_x, ub_y = Tensor("UB", "FP16"), Tensor("UB")  
gm_x = Tensor("GM")  
ub_x.load(gm_x)  
out = vconv_deq(ub_x, ub_y, "FP32")(   ) 
```

# 3.3.6.4.6 vconv_vdeq

# 功能说明

vconv_vdeq指令抽象。 

y = vconv_vdeq(x, dtype)，vconv_vdeq表示对输入数据进行量化操作的向量计算。 

目前支持转换类型包括：INT16->INT8。 

# 接口原型

```txt
class vconv_vdeg(x,y, dtype) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出y向量Tensor。</td></tr><tr><td>dtype</td><td>输入</td><td>字符串</td><td>表示目标Tensor的数据类型。</td></tr></table>

# 使用示例

```python
from mskpp import vconv_vdeq, Tensor  
ub_x, ub_y = Tensor("UB", "FP16"), Tensor("UB")  
gm_x = Tensor("GM")  
ub_x.load(gm_x)  
out = vconv_vdeq(ub_x, ub_y, "FP32")() 
```

# 3.3.6.4.7 vector_dup

# 功能说明

vector_dup指令抽象。 

y = vector_dup(x)， x、 y按元素填充元素。 

# 接口原型

class vector_dup(x, y, fill_shape) 

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持FP16、FP32、INT16、INT32、UINT16、UINT32。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出y向量Tensor。支持FP16、FP32、INT16、INT32、UINT16、UINT32。</td></tr><tr><td>fill_shape</td><td>输入</td><td>list</td><td>表示目标Tensor的要被扩充的shape值。</td></tr></table>

# 约束说明

由于该指令输入仅一个标量，因此需要创建一个shape为[1]且is_inited=True的Tensor 作为模拟标量输入，不增加性能开销。 

# 使用示例

```python
from sklearn import vector_dup, Tensor  
ub_x = Tensor("UB", "FP16", [1], format="ND", is_init=True)  
ub_y = Tensor("UB")  
out = vector_dup(ub_x, ub_y, [8, 2048])() 
```

# 3.3.6.4.8 vexp

# 功能说明

vexp指令抽象。 

$\mathsf { y } = \mathsf { v e x p } ( \mathsf { x } )$ ， x、y按元素取指数。 

# 接口原型

class vexp(x, y) 

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持FP16、FP32。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出y向量Tensor。支持FP16、FP32。</td></tr></table>

# 使用示例

from mskpp import vexp, Tensor ub_x $=$ Tensor("UB") 

```txt
ub_x.load(gm_x)  
ub_y = Tensor("UB")  
out = vexp(ub_x, ub_y()) 
```

# 3.3.6.4.9 vln

# 功能说明

vln指令抽象。 

$y = \mathsf { v l n } ( \mathsf { x } )$ ，x、y按元素取对数。 

# 接口原型

```txt
class vln(x, y) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持FP16、FP32。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出y向量Tensor。支持FP16、FP32。</td></tr></table>

# 使用示例

```python
from mskpp import vln, Tensor  
ub_x = Tensor("UB")  
gm_x = Tensor("GM")  
ub_x.load(gm_x)  
ub_y = Tensor("UB")  
out = vln(ub_x, ub_y)() 
```

# 3.3.6.4.10 vmax

# 功能说明

vmax指令抽象。 

z = vmax(x, y)，x、y按元素取最大。 

# 接口原型

```txt
class vmax(x, y, z) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持FP16、FP32、INT16、INT32。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入y向量Tensor。支持FP16、FP32、INT16、INT32。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持FP16、FP32、INT16、INT32。</td></tr></table>

# 使用示例

```python
from mskpp import vmax, Tensor  
ub_x, ub_y, ub_z = Tensor("UB"), Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vmax(ub_x, ub_y, ub_z()) 
```

# 3.3.6.4.11 vmul

# 功能说明

vmul指令抽象。 

$z = x ^ { \star } y$ ，x、y按元素相乘。 

# 接口原型

```txt
class vmul(x, y, z) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持FP16、FP32、INT16、INT32。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入y向量Tensor。支持FP16、FP32、INT16、INT32。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持FP16、FP32、INT16、INT32。</td></tr></table>

# 使用示例

```python
from mskpp import vmul, Tensor  
ub_x, ub_y, ub_z = Tensor("UB"), Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vmul(ub_x, ub_y, ub_z()) 
```

# 3.3.6.4.12 vmuls

# 功能说明

vmuls指令抽象。 

z = vmuls(x, y)，vmuls求值向量x与标量y的乘积。 

# 接口原型

class vmuls(x, y, z) 

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入向量Tensor。支持FP16、FP32、INT16、INT32。</td></tr><tr><td>y</td><td>输入</td><td>Python标量</td><td>输入标量，程序不对该参数做任何处理。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持FP16、FP32、INT16、INT32。</td></tr></table>

# 使用示例

```txt
from mskpp import vmuls, Tensor  
ub_x, ub_z = Tensor("UB"), Tensor("UB")  
gm_x = Tensor("GM")  
ub_x.load(gm_x)  
out = vmuls(ub_x, 5, ub_z()) //5为y标量的值 
```

# 3.3.6.4.13 vsub

# 功能说明

vsub指令抽象。 

$z = x - y$ ，x、y按元素相减。 

# 接口原型

```txt
class vsub(x,y,z) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持FP16、FP32、INT16、INT32。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入y向量Tensor。支持FP16、FP32、INT16、INT32。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持FP16、FP32、INT16、INT32。</td></tr></table>

# 使用示例

```python
from mskpp import vsub, Tensor  
ub_x, ub_y, ub_z = Tensor("UB"), Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x) 
```

```python
ub_y.load(gm_y)  
out = vsub(ub_x, ub_y, ub_z()) 
```

# 3.3.6.4.14 vdiv

# 功能说明

vdiv指令抽象。 

$z = \textsf { x } / \textsf { y }$ ，x、y按元素相除。 

# 接口原型

```txt
class vdiv(x,y,z) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持FP16、FP32。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入y向量Tensor。支持FP16、FP32。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持FP16、FP32。</td></tr></table>

# 使用示例

```python
from mskpp import vdiv, Tensor  
ub_x, ub_y, ub_z = Tensor("UB"), Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vdiv(ub_x, ub_y, ub_z()) 
```

# 3.3.6.4.15 vcadd

# 功能说明

vcadd指令抽象。 

根据指令的入参将Tensor进行reduce维度，在msKPP指令体系里由reduce_num控制 shape缩减倍数，并保持输入输出Tensor的shape维度一致。当shape最后一维reduce 到1，则将该维度消除。需保证shape中最后一维能够被reduce_num整除且不为0。 

# 接口原型

```javascript
class vcppadd(x, y, reduce_num) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持FP16、FP32。</td></tr><tr><td>reduce_num</td><td>输入</td><td>int</td><td>指定最后一维reduce到多少倍，此参数的取值对该指令的性能无影响。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出y向量Tensor。支持FP16、FP32。</td></tr></table>

# 使用示例

```python
from mskpp import vcpp, Tensor  
ub_x, ub_y = Tensor("UB"), Tensor("UB")  
gm_x = Tensor("GM")  
reduce_num = 16  
ub_x.load(gm_x)  
out = vcpp(ub_x, ub_y, reduce_num()) 
```

# 约束说明

reduce_num不能为0。 

# 3.3.6.4.16 vabs

# 功能说明

vabs指令抽象。 $y = \mathrm{vabs}(x)$ ， $x$ 、y按元素取绝对值。 

# 接口原型

```txt
class vabs(x,y) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持FP16、FP32。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出y向量Tensor。支持FP16、FP32。</td></tr></table>

# 使用示例

```python
from mskpp import vabs, Tensor  
ub_x, ub_y = Tensor("UB"), Tensor("UB")  
gm_x = Tensor("GM")  
ub_x.load(gm_x)  
out = vabs(ub_x, ub_y()) 
```

# 3.3.6.4.17 vaddrelu

# 功能说明

vaddrelu指令抽象。 

$z =$ vaddrelu(x, y)，x、y按元素相加后再计算relu值。 

# 接口原型

class vaddrelu(x, y, z) 

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持FP16、FP32、INT16。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入y向量Tensor。支持FP16、FP32、INT16。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持FP16、FP32、INT16。</td></tr></table>

# 使用示例

```python
from mskpp import vaddrelu, Tensor  
ub_x, ub_y, ub_z = Tensor("UB"), Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vaddrelu(ub_x, ub_y, ub_z()) 
```

# 3.3.6.4.18 vaddreluconv

# 功能说明

vaddreluconv指令抽象。 

$z =$ vaddreluconv(x, y)，x、y按元素相加，计算relu值，并对输出做量化操作。 

支持的类型转换有FP16->INT8、FP32->FP16、INT16->INT8。 

# 接口原型

class vaddreluconv(x, y, z) 

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持FP16、FP32、INT16。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入y向量Tensor。支持FP16、FP32、INT16。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持FP16、INT8。</td></tr></table>

# 使用示例

```python
from mskpp import vaddreluconv, Tensor  
ub_x, ub_y, ub_z = Tensor("UB"), Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vaddreluconv(ub_x, ub_y, ub_z()) 
```

# 3.3.6.4.19 vadds

# 功能说明

vadds指令抽象。 

z = vadds(x, y)，vadds求值向量x与标量y的和。 

# 接口原型

```txt
class vadds(x, y, z) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入向量Tensor。支持FP16、FP32、INT16、INT32。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入标量。程序不对该参数做任何处理。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持FP16、FP32、INT16、INT32。</td></tr></table>

# 使用示例

```python
from mskpp import vadds, Tensor  
ub_x, ub_z = Tensor("UB"), Tensor("UB")  
gm_x = Tensor("GM")  
ub_x.load(gm_x)  
out = vadds(ub_x, 5, ub_z()) //5为y标量的值 
```

# 3.3.6.4.20 vand

# 功能说明

vand指令抽象。 vand(x, y, z)，x、y按元素取与，得到z值。 

# 接口原型

class vand(x, y, z) 

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持INT16、UINT16。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入y向量Tensor。支持INT16、UINT16。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持INT16、UINT16。</td></tr></table>

# 使用示例

```python
from mskpp import vand, Tensor  
ub_x, ub_y, ub_z = Tensor("UB"), Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vand(ub_x, ub_y, ub_z()) 
```

# 3.3.6.4.21 vaxpy

# 功能说明

vaxpy指令抽象。 

z = x * y + z，vaxpy求值向量x与标量y的乘积后加上目标地址z上的和，可以通过 if_mix将输出的数据类型格式指定为FP32。 

# 接口原型

```txt
vaxpy(x, y, z, if_mix=False) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入向量Tensor。支持FP16、FP32、INT16、INT32。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入标量，程序不对该参数做任何处理。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持FP16、FP32、INT16、INT32。</td></tr><tr><td>if_mix</td><td>输入</td><td>Tensor变量</td><td>● 默认为False。
● 若设置为True，指定输出数据类型为FP32。</td></tr></table>

# 使用示例

```python
from mskpp import vaxpy, Tensor  
ub_x, ub_z = Tensor("UB"), Tensor("UB")  
gm_x = Tensor("GM")  
ub_x.load(gm_x)  
out = vaxpy(ub_x, ub_y, ub_z()) 
```

# 3.3.6.4.22 vbitsort

# 功能说明

vbitsort指令抽象。 

根据x输入进行排序，并在排序后给出元素原始的index数据，因此输出向量Tensor的 shape会是x数据的两倍。 

# 接口原型

```txt
class vbitsort(x, y, z) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入向量Tensor。支持FP16、FP32。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入向量Tensor。支持UINT32。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持FP16、FP32。</td></tr></table>

# 使用示例

```python
from mskpp import vbitsort, Tensor  
ub_x, ub_y, ub_z = Tensor("UB"), Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vbitsort(ub_x, ub_y, ub_z()) 
```

# 3.3.6.4.23 vcgadd

# 功能说明

vcgadd指令抽象 

计算每个block元素的和，共计8个block，不支持混合地址。 

# 接口原型

```javascript
class vcgadd(x, y, reduce_num) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor，支持FP16、FP32。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出y向量Tensor，支持FP16、FP32。</td></tr><tr><td>reduce_num</td><td>输入</td><td>int</td><td>shape指定的缩减倍数。</td></tr></table>

# 约束说明

reduce_num不能为0。 

# 使用示例

```python
from mskpp import vcgadd, Tensor  
ub_x, ub_y = Tensor("UB"), Tensor("UB")  
gm_x = Tensor("GM")  
reduce_num = 16  
ub_x.load(gm_x)  
out = vcgadd(ub_x, ub_y, reduce_num()) 
```

# 3.3.6.4.24 vcgmax

# 功能说明

vcgmax指令抽象 

计算每个block的最大元素，共计8个block，不支持混合地址。 

# 接口原型

```javascript
class vcgmax(x, y, reduce_num) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor，支持FP16、FP32。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出y向量Tensor，支持FP16、FP32。</td></tr><tr><td>reduce_num</td><td>输入</td><td>int</td><td>指定最后一维reduce到多少倍，此参数的取值对该指令的性能无影响。</td></tr></table>

# 约束说明

reduce_num不能为0。 

# 使用示例

```python
from sklearn import vcgmax, Tensor
ub_x, ub_y = Tensor("UB"), Tensor("UB") 
```

```julia
gm_x = Tensor("GM")  
reduce_num = 16  
ub_x.load(gm_x)  
out = vcfgmax(ub_x, ub_y, reduce_num()) 
```

# 3.3.6.4.25 vcgmin

# 功能说明

vcgmin指令抽象 

计算每个block的最小元素，共计8个block，不支持混合地址。 

# 接口原型

```javascript
class vcgmin(x, y, reduce_num) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor，支持FP16。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出y向量Tensor，支持FP16。</td></tr><tr><td>reduce_num</td><td>输入</td><td>int</td><td>指定最后一维reduce到多少倍，实测性能数据reduce对性能无影响。</td></tr></table>

# 约束说明

reduce_num不能为0。 

# 使用示例

```python
from mskpp import vcgmin, Tensor  
ub_x, ub_y = Tensor("UB"), Tensor("UB")  
gm_x = Tensor("GM")  
reduce_num = 16  
ub_x.load(gm_x)  
out = vcgmin(ub_x, ub_y, reduce_num()) 
```

# 3.3.6.4.26 vcmax

# 功能说明

vcmax指令抽象。 

计算输入的vector中的元素最大值。 

# 接口原型

```txt
class vcmax(x, y, reduce_num) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor，支持FP16、FP32。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出y向量Tensor，支持FP16、FP32。</td></tr><tr><td>reduce_num</td><td>输入</td><td>int</td><td>指定最后一维reduce到多少倍，实测性能数据reduce对性能无影响。</td></tr></table>

# 约束说明

reduce_num不能为0。 

# 使用示例

```python
from mskpp import vmax, Tensor  
ub_x, ub_y = Tensor("UB"), Tensor("UB")  
gm_x = Tensor("GM")  
reduce_num = 16  
ub_x.load(gm_x)  
out = vmax(ub_x, ub_y, reduce_num()) 
```

# 3.3.6.4.27 vcmin

# 功能说明

vcmin指令抽象。 

计算输入的vector中的元素最小值。 

# 接口原型

```txt
class vcmin(x, y, reduce_num) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor，支持FP16、FP32。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出y向量Tensor，支持FP16、FP32。</td></tr><tr><td>reduce_num</td><td>输入</td><td>int</td><td>指定最后一维reduce到多少倍，实测性能数据reduce对性能无影响。</td></tr></table>

# 约束说明

reduce_num不能为0。 

# 使用示例

```python
from sklearn import vcmin, Tensor
ub_x, ub_y = Tensor("UB"), Tensor("UB") 
```

```julia
gm_x = Tensor("GM")  
reduce_num = 16  
ub_x.load(gm_x)  
out = vmaxmin(ub_x, ub_y, reduce_num()) 
```

# 3.3.6.4.28 vcmp_xxx

# 功能说明

vcmp_[eq|ge|gt|le|lt|ne]指令抽象，该六条指令性能一致。 

vcmp_eq: $z = ( \times = = y )$ ， $\mathsf { x }$ 、y按元素比较相等得到z。 

vcmp_ge: $z = ( \mathsf { x } > = \mathsf { y } )$ ， $\mathsf { x }$ 、y按元素比较大于或等于得到z。 

vcmp_gt: ${ \boldsymbol z } = ( { \mathsf x } > { \mathsf y } )$ ， x、y按元素比较大于得到z。 

vcmp_le: $z = ( \mathsf { x } < = \mathsf { y } )$ ， $\mathsf { x }$ 、y按元素比较小于或等于得到z。 

vcmp_lt: $z = ( \mathsf { x } < \mathsf { y } )$ ， x、y按元素比较小于得到z。 

vcmp_ne: $z = ( \times ! = y )$ ， x、y按元素比较不等得到z。 

# 接口原型

```txt
class vcmp(x, y) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor，支持FP16、FP32。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出y向量Tensor，支持FP16、FP32。</td></tr></table>

# 约束说明

vector指令所有输入输出数据的Tensor均在“UB”空间中，shape需保持一致。 

# 使用示例

```python
from mskpp import vcmp, Tensor  
ub_x, ub_y = Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vcmp(ub_x, ub_y()) 
```

# 3.3.6.4.29 vcmpv_xxx

# 功能说明

vcmpv_[eq|ge|gt|le|lt|ne]指令抽象，该六条指令性能一致。 

vcmpv_eq: $\boldsymbol z = ( \boldsymbol x = = \boldsymbol y )$ ， x、y按元素比较相等得到z。 

vcmpv_ge: $z = ( \mathsf { x } > = \mathsf { y } )$ ， x、y按元素比较大于或等于得到z。 

vcmpv_gt: $z = ( { \mathsf { x } } > { \mathsf { y } } )$ ， x、y按元素比较大于得到z。 

vcmpv_le: $z = ( \mathsf { x } < = \mathsf { y } )$ ， x、y按元素比较小于或等于得到z。 

vcmpv_lt: $z = ( \mathsf { x } < \mathsf { y } )$ ， x、y按元素比较小于得到z。 

vcmpv_ne: $z = ( \times ! = y )$ ， x、y按元素比较不等得到z。 

# 接口原型

```txt
class vcmpv(x, y, z) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor，支持FP16、FP32。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入y向量Tensor，支持FP16、FP32。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。</td></tr></table>

# 约束说明

vector指令所有输入输出数据的Tensor均在“UB”空间中，shape需保持一致。 

# 使用示例

```python
from mskpp import vcmpv, Tensor  
ub_x, ub_y, ub_z = Tensor("UB"), Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vcmpv(ub_x, ub_y, ub_z()) 
```

# 3.3.6.4.30 vcmpvs_xxx

# 功能说明

vcmpvs_[eq|ge|gt|le|lt|ne]指令抽象，该六条指令性能一致。 

vcmpvs_eq: $z = ( \times = = y )$ ， x逐元素与y中存储的标量比较相等得到z。 

vcmpvs_ge: $z = ( \mathsf { x } > = \mathsf { y } )$ ， x逐元素与y中存储的标量比较大于或等于得到z。 

vcmpvs_gt: ${ \boldsymbol z } = ( { \mathsf x } > { \mathsf y } )$ ，x逐元素与y中存储的标量比较大于得到z。 

vcmpvs_le: $z = ( \mathsf { x } < = \mathsf { y } )$ ， x逐元素与y中存储的标量比较小于或等于得到z。 

vcmpvs_lt: $z = ( \mathsf { x } < \mathsf { y } )$ ， x逐元素与y中存储的标量比较小于得到z。 

vcmpvs_ne: $z = ( \times ! = y )$ ， x逐元素与y中存储的标量比较不等得到z。 

# 接口原型

```txt
class vcmpvs(x, y, z) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor，支持FP16、FP32。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入y向量Tensor，支持FP16、FP32。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。</td></tr></table>

# 约束说明

vector指令所有输入输出数据的Tensor均在“UB”空间中，shape需保持一致。 

# 使用示例

```python
from mskpp import vcmpvs, Tensor  
ub_x, ub_y, ub_z = Tensor("UB"), Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vcmpvs(ub_x, ub_y, ub_z()) 
```

# 3.3.6.4.31 vcopy

# 功能说明

vcopy指令抽象 

将源地址的Tensor拷贝到目标地址。 

# 接口原型

```txt
class vcopy(x, y) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入向量Tensor。支持int16、int32、uint16、uint32。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持int16、int32、uint16、uint32。</td></tr></table>

# 使用示例

```python
from mskpp import vcopy, Tensor  
ub_x, ub_y = Tensor("UB"), Tensor("UB")  
gm_x = Tensor("GM")  
ub_x.load(gm_x)  
out = vcopy(ub_x, ub_y()) 
```

# 3.3.6.4.32 vcpadd

# 功能说明

vcpadd指令抽象。 

计算输入的x向量的n和n+1的和，n为偶数下标，将结果写回y。reduce_num控制了输 出的type。 

# 接口原型

class vcpadd(x, y, reduce_num) 

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持fp16、fp32。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出y向量Tensor。支持fp16、fp32。</td></tr><tr><td>reduce_n um</td><td>输入</td><td>int</td><td>shape指定的缩减倍数。</td></tr></table>

# 使用示例

```python
from mskpp import vcpadd, Tensor  
ub_x, ub_y = Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vcpadd(ub_x, ub_y, reduce_num()) 
```

# 3.3.6.4.33 vgather

# 功能说明

给定输入的张量和一个地址偏移张量，vgather指令根据偏移地址将输入张量按元素收 集到结果张量中。 

# 接口原型

class vgather(x, y) 

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持UINT16、UINT32。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出y向量Tensor。支持UINT16、UINT32。</td></tr></table>

# 使用示例

```python
from mskpp import vgather, Tensor  
ub_x, ub_y = Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vgather(ub_x, ub_y()) 
```

# 3.3.6.4.34 vgatherb

# 功能说明

给定一个输入的张量和一个地址偏移张量，vgatherb指令根据偏移地址将输入张量收 集到结果张量中。 

# 接口原型

```txt
class vgather(x, y) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持UINT16、UINT32。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出y向量Tensor。支持UINT16、UINT32。</td></tr></table>

# 使用示例

```python
from mskpp import vgatherb, Tensor  
ub_x, ub_y = Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vgatherb(ub_x, ub_y()) 
```

# 3.3.6.4.35 vlrelu

# 功能说明

vlrelu指令抽象。 

若x大于等于0，则 ${ \sf z } = { \sf x }$ ；若x小于0，则 $1 z = x ^ { \star } y$ ，x按元素与标量y相乘。 

# 接口原型

```txt
class vrelu(x, y, z) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持float16、float32。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入y标量。支持float16、float32。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持float16、float32。</td></tr></table>

# 使用示例

```python
from mskpp import vlrelu, Tensor  
ub_x, ub_z = Tensor("UB"), Tensor("UB")  
gm_x = Tensor("GM")  
scalar_y = 5 //5为y标量的值  
ub_x.load(gm_x)  
out = vlrelu(ub_x, scalar_y, ub_z()) 
```

# 3.3.6.4.36 vmadd

# 功能说明

vmadd指令抽象。 

$z = x ^ { \star } z + y$ 。对两个向量中的每个元素执行乘法和加法。 

# 接口原型

```txt
class vmadd(x, y, z) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持float16、float32。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入y向量Tensor。支持float16、float32。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持float16、float32。</td></tr></table>

# 使用示例

```python
from mskpp import vmadd, Tensor  
ub_x, ub_y, ub_z = Tensor("UB"), Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vmadd(ub_x, ub_y, ub_z()) 
```

# 3.3.6.4.37 vmaddrelu

# 功能说明

vmaddrelu指令抽象。 

z = RELU(x * z + y)。对两个向量中的每个元素进行乘法和加法，然后对该结果中的每 个元素进行MADDRELU操作。 

# 接口原型

class vmaddrelu(x, y, z) 

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持float16、float32。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入y向量Tensor。支持float16、float32。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持float16、float32。</td></tr></table>

# 使用示例

```python
from mskpp import vmaddrelu, Tensor  
ub_x, ub_y, ub_z = Tensor("UB"), Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vmaddrelu(ub_x, ub_y, ub_z()) 
```

# 3.3.6.4.38 vmaxs

# 功能说明

vmaxs指令抽象。 

对向量中的每个元素和标量进行比较，返回较大者。 

# 接口原型

```txt
class vmaxs(x, y, z) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持float16、float32、int16、int32。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入标量。程序不对该参数做任何处理。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持float16、float32、int16、int32。</td></tr></table>

# 使用示例

```python
from mskpp import vmaxs, Tensor  
ub_x, ub_z = Tensor("UB"), Tensor("UB")  
gm_x = Tensor("GM")  
ub_x.load(gm_x)  
out = vmaxs(ub_x, 5, ub_z()) 
```

# 3.3.6.4.39 vmin

# 功能说明

vmin指令抽象。 

对两个向量中的每个元素和标量进行比较，返回较小者。 

# 接口原型

class vmin(x, y, z) 

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持float16、float32、int16、int32。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入y向量Tensor。支持float16、float32、int16、int32。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持float16、float32、int16、int32。</td></tr></table>

# 使用示例

```python
from mskpp import vmin, Tensor  
ub_x, ub_y, ub_z = Tensor("UB"), Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vmin(ub_x, ub_y, ub_z()) 
```

# 3.3.6.4.40 vmins

# 功能说明

vmins指令抽象。 

对向量中的每个元素和标量进行比较，返回较小者。 

# 接口原型

class vmins(x, y, z) 

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持float16、float32、int16、int32。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入标量。程序不对该参数做任何处理。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持float16、float32、int16、int32。</td></tr></table>

# 使用示例

```python
from mskpp import vmaxs, Tensor  
ub_x, ub_z = Tensor("UB"), Tensor("UB")  
gm_x = Tensor("GM")  
ub_x.load(gm_x)  
out = vmaxs(ub_x, 5, ub_z()) //5为y的标量值 
```

# 3.3.6.4.41 vmla

# 功能说明

vmla指令抽象。 

z = x * y + z， x、y按元素相乘，相乘的结果与z按元素相加，可以通过if_mix将输出的 数据类型格式指定为FP32。 

目前支持： 

$$
\text {t y p e} = \mathrm {f} 1 6, \mathrm {f} 1 6 = \mathrm {f} 1 6 ^ {*} \mathrm {f} 1 6 + \mathrm {f} 1 6 。
$$

$$
\text {t y p e} = \mathrm {f} 3 2, \mathrm {f} 3 2 = \mathrm {f} 3 2 * \mathrm {f} 3 2 + \mathrm {f} 3 2 。
$$

if_mix = True时，f32 = f16 * f16 + f32。其中x、y向量使用64个元素的f16数据用于计 算，源向量仅使用低4个block，4个高block被忽略。z是64个元素的包含8个block的 f32数据，同时作为目标向量和第三个源向量。 

# 接口原型

```javascript
class vmla(x, y, z, if_mix=False) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor，支持FP16、FP32。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入y向量Tensor，支持FP16、FP32。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor，支持FP16、FP32。</td></tr><tr><td>if_mix</td><td>输入</td><td>Tensor变量</td><td>• 默认为False。
• 若设置为True，指定输出数据类型为FP32。</td></tr></table>

# 约束说明

vector指令输入输出数据的Tensor均在“UB”空间中。 

# 使用示例

```python
from mskpp import vmla, Tensor  
ub_x, ub_y, ub_z = Tensor("UB"), Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vmla(ub_x, ub_y, ub_z()) 
```

# 3.3.6.4.42 vmrgsort

# 功能说明

将已经排好序的最多4条region proposals队列，排列并合并成1条队列，结果按照 score域由大到小排序。 

# 接口原型

```txt
class vmrgsort(x, y, z) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor，支持FP16、FP32。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入y向量Tensor，支持UINT64。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor，支持FP16、FP32。</td></tr></table>

# 使用示例

```python
from mskpp import vmrgsort, Tensor  
ub_x, ub_y, ub_z = Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vmrgsort(ub_x, ub_y, ub_z()) 
```

# 3.3.6.4.43 vmulconv

# 功能说明

vmulconv指令抽象。 

$z =$ vmulconv(x, y)，x、y按元素相乘，并对输出做量化操作。 

# 接口原型

```txt
class vmulconv(x, y, z, dtype) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持FP16。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入y向量Tensor。支持FP16。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。</td></tr><tr><td>dtype</td><td>输入</td><td>Tensor变量</td><td>•指定输入数据类型，包含UINT8、INT8。
•z的输出数据类型由dtype决定。</td></tr></table>

# 使用示例

```python
from mskpp import vmulconv, Tensor  
ub_x, ub_y, ub_z = Tensor("UB"), Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vmulconv(ub_x, ub_y, ub_z, 'UINT8')( 
```

# 3.3.6.4.44 vnot

# 功能说明

vnot指令抽象。 

vnot指令对输入向量按位取反，每个向量为8*256bits。 

# 接口原型

```txt
class vnot(x, y) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor，支持INT16、UINT16。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出y向量Tensor，支持INT16、UINT16。</td></tr></table>

# 使用示例

```python
from mskpp import vnot, Tensor  
ub_x, ub_y = Tensor("UB"), Tensor("UB")  
gm_x = Tensor("GM")  
ub_x.load(gm_x)  
out = vnot(ub_x, ub_y()) 
```

# 约束说明

该指令仅支持普通掩码模式和计数器模式。 

# 3.3.6.4.45 vor

# 功能说明

vor指令抽象。 

vor指令对输入向量按位取或，每个向量为 ${ ^ { 8 } } ^ { \star } 2 5$ 6bits。 

# 接口原型

```javascript
class vor(x, y, z) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor，支持INT16、UINT16。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入y向量Tensor，支持INT16、UINT16。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出z向量Tensor，支持INT16、UINT16。</td></tr></table>

# 使用示例

```python
from mskpp import vor, Tensor  
ub_x, ub_y, ub_z = Tensor("UB"), Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vor(ub_x, ub_y, ub_z()) 
```

# 约束说明

该指令仅支持普通掩码模式和计数器模式。 

# 3.3.6.4.46 vrec

# 功能说明

vrec指令抽象。 

vrec指令进行浮点倒数估计，找到每个向量的近似倒数估计。 

# 接口原型

```txt
class vrec(x, y) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor，支持FP16、FP32。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出y向量Tensor，支持FP16、FP32。</td></tr></table>

# 使用示例

```python
from mskpp import vrec, Tensor  
ub_x, ub_y = Tensor("UB"), Tensor("UB")  
gm_x = Tensor("GM")  
ub_x.load(gm_x)  
out=vrec(ub_x, ub_y()) 
```

# 3.3.6.4.47 vreduce

# 功能说明

vreduce指令抽象。 

vreduce指令根据输入y向量的mask数据，决定取x向量中的某些元素存至z向量，由于 msKPP中的Tensor并无实际元素，因此增加了reserve_num的参数，z输出的shape由 该参数决定。 

# 接口原型

```txt
class vreduce(x, y, z, reserve_num) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持UINT16、UINT32。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入y向量Tensor。支持UINT16、UINT32。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出z向量Tensor。支持UINT16、UINT32。</td></tr><tr><td>reserve_num</td><td>输入</td><td>int</td><td>指定输出元素的个数。</td></tr></table>

# 使用示例

```python
from mskpp import vreduce, Tensor  
ub_x, ub_y, ub_z = Tensor("UB"), Tensor("UB"), Tensor("UB")  
gm_x, gm_y, gm_z = Tensor("GM"), Tensor("GM"), Tensor("GM")  
reserve_num = 16  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vreduce(ub_x, ub_y, ub_z, reserve_num())  
gm_z.load(out[0]) 
```

# 3.3.6.4.48 vreducev2

# 功能说明

vreducev2指令抽象。 

vreducev2指令根据输入y向量的mask数据，决定取x向量中的某些block级的元素存至 z向量，由于msKPP中的Tensor并无相关概念，因此增加了reserve_num的参数，z输出 的shape由该参数决定。 

# 接口原型

```javascript
class vreducev2(x, y, z, reserve_num) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持UINT16、UINT32。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入y向量Tensor。支持UINT16、UINT32。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出z向量Tensor。支持UINT16、UINT32。</td></tr><tr><td>reserve_n um</td><td>输入</td><td>int</td><td>指定输出元素的个数。</td></tr></table>

# 使用示例

```python
from mskpp import vreducev2, Tensor  
ub_x, ub_y, ub_z = Tensor("UB"), Tensor("UB"), Tensor("UB")  
gm_x, gm_y, gm_z = Tensor("GM"), Tensor("GM"), Tensor("GM")  
reserve_num = 16  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vreducev2(ub_x, ub_y, ub_z, reserve_num())  
gm_z.load(out[0]) 
```

# 3.3.6.4.49 vrelu

# 功能说明

vrelu指令抽象。 

每个元素的relu操作，按照元素小于0的取0，大于等于0的取本身。 

# 接口原型

```txt
class vrelu(x, y) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持float16、float32、int32。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持float16、float32、int32。</td></tr></table>

# 使用示例

```python
from mskpp import vrelu, Tensor  
ub_x, ub_y = Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vrelu(ub_x, ub_y()) 
```

# 3.3.6.4.50 vrsqrt

# 功能说明

vrsqrt指令抽象。 

浮点数的倒数平方根。 

# 接口原型

```txt
class vrsqrt(x, y) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持float16、float32。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持float16、float32。</td></tr></table>

# 使用示例

```python
from mskpp import vsqrt, Tensor  
ub_x, ub_y = Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vsqrt(ub_x, ub_y()) 
```

# 3.3.6.4.51 vsel

# 功能说明

vsel指令抽象。 

通常与vcmp合用，根据获得的cmp_mask来选取x，y中对应位置的某个元素。 

# 接口原型

class vsel(x, y, z) 

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持FP16、FP32、INT16、INT32。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入y向量Tensor。支持FP16、FP32、INT16、INT32。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持FP16、FP32、INT16、INT32。</td></tr></table>

# 使用示例

```python
from mskpp import vsel, Tensor  
ub_x, ub_y, ub_z = Tensor("UB"), Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vsel(ub_x, ub_y, ub_z()) 
```

# 3.3.6.4.52 vshl

# 功能说明

vshl指令抽象。 

根据输入类型进行逻辑左移或算术左移。 

# 接口原型

class vshl(x, y) 

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持UINT16、UINT32、INT16、INT32。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出y向量Tensor。支持UINT16、UINT32、INT16、INT32。</td></tr></table>

# 使用示例

```python
from mskpp import vshl, Tensor  
ub_x, ub_z = Tensor("UB"), Tensor("UB")  
gm_x = Tensor("GM")  
ub_x.load(gm_x)  
out = vshl(ub_x, ub_z()) 
```

# 3.3.6.4.53 vshr

# 功能说明

vshr指令抽象。 

根据输入类型进行逻辑左移或算术左移。 

# 接口原型

class vshr(x, y) 

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持UINT16、UINT32、INT16、INT32。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出y向量Tensor。支持UINT16、UINT32、INT16、INT32。</td></tr></table>

# 使用示例

```python
from mskpp import vshr, Tensor  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vshr(ub_x, ub_y()) 
```

# 3.3.6.4.54 vsqrt

# 功能说明

vsqrt指令抽象。 

$\mathsf { y } = \mathsf { \sqrt { x } }$ ， x按元素开平方根。 

# 接口原型

class vsqrt(x, y) 

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持float16、float32。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持float16、float32。</td></tr></table>

# 使用示例

from mskpp import vsqrt, Tensor ub_x, ub_z $=$ Tensor("UB"), Tensor("UB") 

```julia
gm_x = Tensor("GM")  
ub_x.load(gm_x)  
out = vsqrt(ub_x, ub_y()) 
```

# 约束说明

输入的值应为正数，否则结果未知并产生异常。 

# 3.3.6.4.55 vsubrelu

# 功能说明

vsubrelu指令抽象。 

$z =$ vsubrelu(x, y)，x、y按元素相减后再计算relu值。 

# 接口原型

class vsubrelu $(x,y,z)$ 

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持float16、float32。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入y向量Tensor。支持float16、float32。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持float16、float32。</td></tr></table>

# 使用示例

```python
from mskpp import vsubrelu, Tensor  
ub_x, ub_y, ub_z = Tensor("UB"), Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vsubrelu(ub_x, ub_y, ub_z()) 
```

# 3.3.6.4.56 vsubreluconv

# 功能说明

vsubreluconv指令抽象。 

$z =$ vsubreluconv(x, y)，x、y按元素相减，计算relu值，并对输出做量化操作。 

支持的类型转换有FP16->INT8、FP32->FP16、INT16->INT8。 

# 接口原型

```txt
class vsubreluconv(x, y, z) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持FP16、FP32、INT16。</td></tr><tr><td>y</td><td>输入</td><td>Tensor变量</td><td>输入y向量Tensor。支持FP16、FP32、INT16。</td></tr><tr><td>z</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持FP16、INT8。</td></tr></table>

# 使用示例

```python
from mskpp import vsubreluconv, Tensor  
ub_x, ub_y, ub_z = Tensor("UB"), Tensor("UB"), Tensor("UB")  
gm_x, gm_y = Tensor("GM"), Tensor("GM")  
ub_x.load(gm_x)  
ub_y.load(gm_y)  
out = vsubreluconv(ub_x, ub_y, ub_z()) 
```

# 3.3.6.4.57 vtranspose

# 功能说明

vtranspose指令抽象。 

从输入地址x（32字节对齐）开始转置一个16x16矩阵，每个元素为16位，结果输出到 y中，输入输出都是连续的512B存储空间。 

# 接口原型

```python
class vtranspose (x, y) 
```

# 参数说明

<table><tr><td>参数名</td><td>输入/输出</td><td>数据类型</td><td>说明</td></tr><tr><td>x</td><td>输入</td><td>Tensor变量</td><td>输入x向量Tensor。支持INT16。</td></tr><tr><td>y</td><td>输出</td><td>Tensor变量</td><td>输出向量Tensor。支持INT16。</td></tr></table>

# 使用示例

```python
from mskpp import vtranspose, Tensor  
ub_x, ub_y = Tensor("UB"), Tensor("UB")  
gm_x = Tensor("GM")  
ub_x.load(gm_x)  
out = vtranspose(ub_x, ub_y()) 
```