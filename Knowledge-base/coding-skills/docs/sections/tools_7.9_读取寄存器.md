<!-- Source: 算子开发工具.md lines 7625-7649 | Section: 7.9 读取寄存器 -->

# 7.9 读取寄存器

当用户使用msDebug调起算子后，可以通过命令行读取当前断点所在设备的寄存器 值。具体介绍如下： 

输入register read -a后，返回当前设备上所有可用的寄存器值。 

```txt
(msdbug) register read -a PC = 0x12C0C00F1F88 COND = 0x0 CTRL = 0x100000000003C GPR0 = 0x12C041200100 GPR1 = 0x146FD9 GPR2 = 0x146FC8 GPR3 = 0x8001000800 GPR4 = 0x80300000100 GPR5 = 0x8000000000 GPR6 = 0x0 GPR7 = 0x300000000 GPR8 = 0x3 GPR9 = 0x1000000 GPR10 = 0xFFFF GPR11 = 0xFC0 GPR12 = 0x0 GPR13 = 0x0 GPR14 = 0x0 GPR15 = 0x11 GPR16 = 0x7FFF GPR17 = 0x7A0 GPR18 = 0x0 GPR19 = 0x0 GPR20 = 0x0 GPR21 = 0x0 GPR22 = 0x0 GPR23 = 0x0 GPR24 = 0x0 GPR25 = 0x0 GPR26 = 0x0 GPR27 = 0x0 GPR28 = 0x0 GPR29 = 0x146EE8 GPR30 = 0x147640 GPR31 = 0x12C0C00F1ED4 LPCNT = 0xO 
```

STATUS $= 0\mathrm{x}0$ SYS_CNT $= 0x774E308602$ ICACHE_PRL_ST $= 0\mathrm{x}0$ SAFETY_CRC_EN $= 0\mathrm{x}0$ STAtomic_CFG $= 0\mathrm{x}5$ CALL_DEPTH_CNT $= 0\mathrm{x}5$ CONDITION_FLAG $= 0\mathrm{x}1$ FFTS_BASE_ADDR $= 0\mathrm{x}E7FFE044F000$ CUBE_EVENT_TABLE $= 0\mathrm{x}7000000000$ FIXP_EVENT_TABLE $= 0\mathrm{x}0$ MTE1_EVENT_TABLE $= 0\mathrm{x}70000000$ MTE2_EVENT_TABLE $= 0\mathrm{x}0$ SCALAR_EVENT_TABLE $= 0\mathrm{x}0$ 

输入register read $\$ 4$ {变量名}，返回当前设备上该寄存器值。一次性读取多个寄存 器时，需用空格隔开。 

当变量名在当前设备上可用时，返回该寄存器值。 

当变量名在当前设备上不可用时，返回Invalid register name '变量名'。 

```txt
(msdebug) register read $PC $test $GPR30
PC = 0x12C0C00F1F88
Invalid register name 'test'.
GPR30 = 0x147640 
```