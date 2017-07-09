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

__config__ = {
    "api_svr": {
        "ip": "127.0.0.1",
        "port": 11111,
    },
    "futu_account": {
        "unlock_password": "",
    },

    # 策略对应的股票市场, 不同的大市场目前不能同时存在, 如 "HK" 与"US"
    "futu_market": ("HK"),  # ("SH", "SZ")| ("HK") | ("US")

    # 实时策略在盘中handle_bar间隔多少秒触发一次
    "futu_bar_fps": 1.0,

    "rqalpha_broker_config":
    {
        # 是否开启信号模式
        "signal": False,
        # 启用的回测引擎，目前支持 `current_bar` (当前Bar收盘价撮合) 和 `next_bar` (下一个Bar开盘价撮合)
        "matching_type": "current_bar",
        # 设置滑点
        "slippage": 0,
        # 设置手续费乘数，默认为1
        "commission_multiplier": 1,
        # price_limit: 在处于涨跌停时，无法买进/卖出，默认开启【在 Signal 模式下，不再禁止买进/卖出，如果开启，则给出警告提示。】
        "price_limit": True,
        # liquidity_limit: 当对手盘没有流动性的时候，无法买进/卖出，默认关闭
        "liquidity_limit": False,
        # 是否有成交量限制
        "volume_limit": True,
        # 按照当前成交量的百分比进行撮合
        "volume_percent": 0.25,
    }
}


def load_mod():
    from .mod import FUTUMod
    return FUTUMod()
