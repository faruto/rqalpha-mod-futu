#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017 Futu, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from rqalpha import run_file


config = {
    "base": {
        "start_date": "2016-01-01",
        "end_date": "2016-12-01",
        "accounts": {
            "stock": 100000
        },
        "benchmark": "HK.00001",
        "frequency": "1d",
        # 运行类型，`b` 为历史数据回测，`p` 为实时数据模拟交易, `r` 为实时数据实盘交易。
        "run_type":  "b",
    },
    "extra": {
        "log_level": "verbose",
    },
    "mod": {
        "sys_analyser": {
            "enabled": True,
            "plot": True
        },
        "sys_simulation": {
            'enabled': False,
        },
        "sys_stock_realtime": {
            "enabled": False,
        },
    }
}

strategy_file_path = "./debug_strategy.py"

run_file(strategy_file_path, config)
