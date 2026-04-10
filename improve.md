## AscendC Kernel Agent 修改计划

### 设计成Agent Team的形式

整个Agent Team的结构设计：
主Agent负责任务理解，架构设计，任务分发给代码编写Agent和测试Agent等，架构设计Agent的可以参考https://gitcode.com/cann/skills.git这个仓库
代码编写Agent的可以参考https://gitcode.com/cann/skills.git这个仓库，可以设计成多个Agent如开发和review，
测试Agent的设计可以参考/data/w00936672/MultiKernelBench下面的流程，然后https://gitcode.com/cann/skills.git这个仓库里面的测试的一些skill也可以参考
还有一个Supervisor Agent，参考./AVO-paper里面的表述，不干预主Agent的执行，只会在特定时刻参与

### 把整个工程实现从Kernel直调改成自定义算子工程，不要用那种简单的算子实现来糊弄我，我要的是完整的算子工程，测试Agent通过其他框架调用这个算子，具体实现可以参考/data/w00936672/MultiKernelBench里面的流程
