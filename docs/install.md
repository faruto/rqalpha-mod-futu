**1. 安装python的Anaconda环境**

下载[Anaconda 4.4.0](https://mirrors.tuna.tsinghua.edu.cn/anaconda/archive/Anaconda3-4.4.0-Windows-x86_64.exe)，并安装。

**2. 安装rqalpha**

在命令行中输入如下命令

```
pip install -U rqalpha
```

**3. 安装futuquant**

安装可在命令行中输入如下命令：

```
pip install futuquant
```

- futuquant提供基于富途牛牛客户端的程序化交易接口以及行情和历史数据。
- 根据[富途牛牛行情交易API入门指引](https://futunnopen.github.io/futuquant/document/Futunn_API_Intro/)的指引，搭建富途API环境。

**4. 安装rqalpha-mod-rqalpha**

```
rqalpha mod install futu				# 安装futu mod
rqalpha mod list						# 查看当前有哪些mod, 如果安装成功，应该会看到futu的mod
rqalpha mod enable futu  				# 开启futu的mod
rqalpha mod disable sys_simulation		# 关闭sys_simulation
```

**5. 开始编写策略**

在examples文件夹中编写你自己的策略文件mystrategy.py。修改debug_run_file.py中的配置如下。

```
# -*- coding: utf-8 -*-

from rqalpha import run_file

config = {
  "base": {
  ... # 这部分不用改，按照原来的配置即可
    "run_type": "b", # 设为回测
  },
  ... # 这部分不用改，按照原来的配置即可
}

strategy_file_path = "./strategy/mystrategy.py" # 设置策略文件

run_file(strategy_file_path, config)
```

然后运行debug_run_file.py文件即可。

关于如何编写你的mystrategy.py，请参考[文档](http://rqalpha.readthedocs.io/zh_CN/latest/intro/overview.html)。