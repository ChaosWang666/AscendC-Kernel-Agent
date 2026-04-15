<!-- Source: 算子开发工具.md lines 3696-3738 | Section: 3.6 FAQ -->

# 3.6 FAQ

# 3.6.1 运行 Kernel 时提示权限错误

# 现象描述

运行Kernel时出现以下报错： 

```txt
raise PermissionError(f'Path {path} cannot have write permission of group.')  
PermissionError: Path /any_path/_gen_module.so cannot have write permission of group. 
```

# 错误原因

当前用户创建的文件的默认权限过大（具有group写权限）。 

# 解决措施

先通过umask -S命令查询权限配置，再使用umask 0022命令调整权限配置。 

```txt
$ umask -S
$ umask 0022
u=rwx,g=rx,o=rx 
```

# 4 算子工程创建（msOpGen）

工具概述 

使用前准备 

创建算子工程 

算子开发 

算子编译部署 

查看算子仿真流水图 

典型案例