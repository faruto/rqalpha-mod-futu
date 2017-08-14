1. 如何设置运行类型<br/>
在debug_run_file的config里，将运行类型run_type改为相应的标识，其中“b”代表历史数据回测，“p”代表实时数据模拟交易，“r”代表实时数据实盘交易

2. 如何新增策略文件<br/>
在strategy文件夹中新建脚本，就可以开始写自己的策略了，记得在运行时把debug_run_file里的策略路径修改为对应的策略脚本路径

3. 如何修改股票代码、起始资金、起始日期等<br/>
参数配置方式遵循rqalpha的参数配置优先级，策略代码中配置 > 命令行参 = run_file传参 > 用户配置文件 > 系统默认配置文件。这里以run_file运行策略为例，在策略代码中设置股票代码，在debug_run_file的config里benchmark可以设置股票池，accounts设置起始资金，start_date, end_date设置起始日期。

4. 如何设置ip<br/>
在init.py中的config里可以配置ip，本地ip: 127.0.0.1，云端ip: 119.29.141.202