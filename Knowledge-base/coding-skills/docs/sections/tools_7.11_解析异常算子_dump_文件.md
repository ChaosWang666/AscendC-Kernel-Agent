<!-- Source: 算子开发工具.md lines 7760-7818 | Section: 7.11 解析异常算子 dump 文件 -->

# 7.11 解析异常算子 dump 文件

客户现场发生硬件异常时，需要反复压测复现问题，定位效率低。为了解决该问题， 系统检测到潜在的硬件异常时，会自动触发一个dump操作，捕获当前的状态信息。 msDebug工具通过对异常算子dump文件的解析，即使在没有主动压测的情况下也能 收集到足够的数据用于问题分析。通过上述功能，不仅提高了硬件异常问题的定位效 率，还减少因反复压测给用户带来的不便。 

# 操作步骤

步骤1 准备acl.json配置文件。 

工程化算子开发：单算子API调用场景：参考《AscendCL应用开发指南 (C&C+ +)》的“初始化与去初始化”节点，自行创建acl.json文件，然后通过aclinit接口 进行加载。 

AI框架算子适配：PyTorch框架场景：在用户torch_npu的安装目录中搜索acl.json 文件。 

# 说明

配置acl.json文件后将不能使用msDebug的其他功能。 

步骤2 参见《AscendCL应用开发指南 (C&C++)》的“acl API参考 > 系统配置 > aclInit”章 节的配置文件示例（异常算子Dump配置），开启生成异常算子dump文件的功能。 

1. 在acl.json配置文件中，将dump_scene参数设置为aic_err_detail_dump。 

2. 在acl.json配置文件中，配置dump_path参数设置导出异常算子dump文件的路 径。 

步骤3 程序崩溃时（如内存溢出、段错误等），触发生成异常算子dump文件。 

# 说明

默认情况下，该文件名为core或core.pid（其中PID为进程ID）。 

步骤4 使用msDebug工具执行以下命令，加载异常算子dump文件。 

```txt
(py38) root@ubuntu:~/CLionProjects/untitled/build$ msdebug --core corefile //corefile 为用户异常算子dump文件的路径
msdebug(MindStudio Debugger) is part of MindStudio Operator-dev Tools.
The tool provides developers with a mechanism for debugging Ascend kernels running on actual hardware.
This enables developers to debug Ascend kernels without being affected by potential changes brought by simulation and emulation environments.
(msdebug) target create --core "/home/xx/coredump_file/
GatherV3_9e31943a1a48bf81ddbf1fc6379e0be3_high_performance_10330.2.1.20250217233735574.core"
Core file "/home/xx/coredump_file/
GatherV3_9e31943a1a48bf81ddbf1fc6379e0be3_high_performance_10330.2.1.20250217233735574.core"
(hiipu64) was loaded.
[Switching to focus on Coreld 30, Type av] 
```

步骤5 查看异常算子dump文件信息。 

(msdebug) ascend info summary Coreld CoreType Deviceld ChipType 25 AIV 0 A2/A3 26 AIV 0 A2/A3 27 AIV 0 A2/A3 28 AIV 0 A2/A3 29 AIV 0 A2/A3 30 AIV 0 A2/A3 31 AIV 0 A2/A3 32 AIV 0 A2/A3 33 AIV 0 A2/A3 34 AIV 0 A2/A3 35 AIV 0 A2/A3 36 AIV 0 A2/A3 51 AIV 0 A2/A3 52 AIV 0 A2/A3 57 AIV 0 A2/A3 58 AIV 0 A2/A3 59 AIV 0 A2/A3 60 AIV 0 A2/A3 61 AIV 0 A2/A3 62 AIV 0 A2/A3 63 AIV 0 A2/A3 64 AIV 0 A2/A3 65 AIV 0 A2/A3 66 AIV 0 A2/A3 67 AIV 0 A2/A3 68 AIV 0 A2/A3 69 AIV 0 A2/A3 70 AIV 0 A2/A3 71 AIV 0 A2/A3 72 AIV 0 A2/A3 Id DataType MemType Addr Size Coreld dim O DEVICE_KERNEL_OBJECT GM $0\mathrm{x}12\mathrm{c}0\mathrm{c}0052000$ 280344 

<table><tr><td>1</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c140864000</td><td>16384</td><td>25</td></tr><tr><td>2</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c140868000</td><td>16384</td><td>26</td></tr><tr><td>3</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c14086c000</td><td>16384</td><td>27</td></tr><tr><td>4</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c140870000</td><td>16384</td><td>28</td></tr><tr><td>5</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c140874000</td><td>16384</td><td>29</td></tr><tr><td>6</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c140878000</td><td>16384</td><td>30</td></tr><tr><td>7</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c14087c000</td><td>16384</td><td>31</td></tr><tr><td>8</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c140880000</td><td>16384</td><td>32</td></tr><tr><td>9</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c140884000</td><td>16384</td><td>33</td></tr><tr><td>10</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c140888000</td><td>16384</td><td>34</td></tr><tr><td>11</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c14088c000</td><td>16384</td><td>35</td></tr><tr><td>12</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c140890000</td><td>16384</td><td>36</td></tr><tr><td>13</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c1408cc000</td><td>16384</td><td>51</td></tr><tr><td>14</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c1408d0000</td><td>16384</td><td>52</td></tr><tr><td>15</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c1408e4000</td><td>16384</td><td>57</td></tr><tr><td>16</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c1408e8000</td><td>16384</td><td>58</td></tr><tr><td>17</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c1408ec000</td><td>16384</td><td>59</td></tr><tr><td>18</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c1408f0000</td><td>16384</td><td>60</td></tr><tr><td>19</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c1408f4000</td><td>16384</td><td>61</td></tr><tr><td>20</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c1408f8000</td><td>16384</td><td>62</td></tr><tr><td>21</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c1408fc000</td><td>16384</td><td>63</td></tr><tr><td>22</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c140900000</td><td>16384</td><td>64</td></tr><tr><td>23</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c140904000</td><td>16384</td><td>65</td></tr><tr><td>24</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c140908000</td><td>16384</td><td>66</td></tr><tr><td>25</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c14090c000</td><td>16384</td><td>67</td></tr><tr><td>26</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c140910000</td><td>16384</td><td>68</td></tr><tr><td>27</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c140914000</td><td>16384</td><td>69</td></tr><tr><td>28</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c140918000</td><td>16384</td><td>70</td></tr><tr><td>29</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c14091c000</td><td>16384</td><td>71</td></tr><tr><td>30</td><td>STACK</td><td>GM/DCACHE</td><td>0x12c140920000</td><td>16384</td><td>72</td></tr><tr><td>31</td><td>INPUT_TENSOR</td><td>GM</td><td>0x12c0413e0000</td><td>131072</td><td>[]</td></tr><tr><td>32</td><td>INPUT_TENSOR</td><td>GM</td><td>0x12c080ae1000(invalid)</td><td>120000</td><td>[]</td></tr><tr><td>33</td><td>INPUT_TENSOR</td><td>GM</td><td>0x12c0413c0000</td><td>131072</td><td>[]</td></tr><tr><td>34</td><td>ARGS</td><td>GM/DCACHE</td><td>0x12c100091000</td><td>56</td><td></td></tr><tr><td colspan="6">(msdebug) x -m GM -f uint8_t 0x12c0c0052000 -s 8 -c 2</td></tr><tr><td colspan="6">0x12c0c0052000: {0xa0 0x3f 0x3a 0x07 0x10 0x00 0x7b 0x07}</td></tr><tr><td colspan="6">0x12c0c0052008: {0x80 0x38 0x9e 0x02 0x81 0xd7 0x3b 0x00}</td></tr><tr><td colspan="6">(msdebug) x -m DCache -f uint8_t 0x12c140864000 -s 8 -c 2</td></tr><tr><td colspan="6">0x12c140864000: {0x00 0x00 0x00 0x00 0x00 0x00 0x00}</td></tr><tr><td colspan="6">0x12c140864008: {0x00 0x00 0x00 0x00 0x00 0x00 0x00}</td></tr></table>

步骤6 请参考7.8 核切换、7.9 读取寄存器以及7.5 内存与变量打印章节的内存打印相关操作 定位硬件异常。 

步骤7 调试完以后，执行q命令并输入Y或y结束调试。 

```txt
(msdebug) q Quitting LLDB will kill one or more processes. Do you really want to proceed: [Y/n] y 
```

----结束