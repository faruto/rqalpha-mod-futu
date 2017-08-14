# rqalpha_mod_futu安装步骤
**1. 安装python3.5**

下载[Anaconda](https://mirrors.tuna.tsinghua.edu.cn/anaconda/archive/Anaconda3-4.2.0-Windows-x86_64.exe)，并安装。

**2. 安装rqalpha_develop**

在命令行中输入如下命令，这里需要安装的是rqalpha的master分支。

```
pip install https://github.com/ricequant/rqalpha/zipball/master
```

**3. 安装futu_api**

在命令行中输入如下命令。

```
git clone https://github.com/FutunnOpen/OpenQuant.git
cd OpenQuant
git checkout futu_rqalpha #切换到futu_rqalpha分支
```

根据[富途牛牛行情交易API入门指引](https://github.com/FutunnOpen/OpenQuant/blob/master/OpenInterface/Python/%E5%85%A5%E9%97%A8%E6%8C%87%E5%BC%95%E5%8F%8A%E6%8E%A5%E5%8F%A3%E6%96%87%E6%A1%A3/%E5%AF%8C%E9%80%94%E7%89%9B%E7%89%9B%E8%A1%8C%E6%83%85%E4%BA%A4%E6%98%93API%E5%85%A5%E9%97%A8%E6%8C%87%E5%BC%95.md)的指引，搭建富途API环境。

**4. 安装futu_mod**

在OpenQuant\OpenInterface\Python\rqalpha-mod-futu文件夹下打开命令行，输入以下命令。
```
rqalpha mod install -e . #此命令会扫描当前目录下的setup.py文件，执行安装
rqalpha mod list #查看当前有哪些mod,如果安装成功，应该会看到futu的mod
rqalpha mod enable futu #开户futu的mod
rqalpha mod disable sys_simulation # 关闭sys_simulation
```

**5. 开始编写策略**
```
cd OpenInterface\Python\rqalpha-mod-futu\rqalpha_mod_futu
```

在strategy文件夹中编写你自己的策略文件mystrategy.py。修改debug_run_file.py中的配置如下。


```
# -*- coding: utf-8 -*-

from rqalpha import run_file

config = {
  "base": {
  ... #这部分不用改，按照原来的配置即可
    "run_type": "b", #设为回测
  },
  ... #这部分不用改，按照原来的配置即可
}

strategy_file_path = "./strategy/mystrategy.py" # 设置策略文件

run_file(strategy_file_path, config)
```

然后运行debug_run_file.py文件即可。

关于如何编写你的mystrategy.py，请参考[文档](http://rqalpha.readthedocs.io/zh_CN/latest/intro/overview.html)。

**使用说明**

1. 如何设置运行类型

   在debug_run_file的config里，将运行类型run_type改为相应的标识，其中“b”代表历史数据回测，“p”代表实时数据模拟交易，“r”代表实时数据实盘交易

2. 如何新增策略文件

   在strategy文件夹中新建脚本，就可以开始写自己的策略了，记得在运行时把debug_run_file里的策略路径修改为对应的策略脚本路径

3. 如何修改股票代码、起始资金、起始日期等

   参数配置方式遵循rqalpha的参数配置优先级，策略代码中配置 > 命令行参 = run_file传参 > 用户配置文件 > 系统默认配置文件。这里以run_file运行策略为例，在策略代码中设置股票代码，在debug_run_file的config里benchmark可以设置股票池，accounts设置起始资金，start_date, end_date设置起始日期。
   
4. 如何设置ip
   在init.py中的config里可以配置ip，本地ip: 127.0.0.1，云端ip: 119.29.141.202

**注意**

* 目前暂时只支持日K级别的回测
* 港股下单不支持市价单，只支持限价单
* 历史数据需要用户本地下载，历史K线下载指引文档参见(https://github.com/FutunnOpen/OpenQuant/blob/master/OpenInterface/Python)
