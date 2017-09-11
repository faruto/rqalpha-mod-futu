#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2017 Futu Securities
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


from .rqalpha_simulate_broker import RQSimulateBroker
from .futu_event_source import *
from .futu_broker_hk import FUTUBrokerHK
from .futu_market_state import FUTUMarketStateSource
from .futu_data_source import FUTUDataSource, DataCache
from .futu_position import FutuStockPosition
from .futu_utils import *

from rqalpha.interface import AbstractMod
from .const import FUTU_ACCOUNT_TYPE
from .futu_account import FutuStockAccount
from futuquant import OpenQuoteContext


class FUTUMod(AbstractMod):
    _futu_mod = None
    _data_cache = ''

    def __init__(self):
        FUTUMod._futu_mod = self
        self._env = None
        self._mod_config = None
        self._quote_context = None

    @classmethod
    def get_instance(cls):
        return FUTUMod._futu_mod

    def start_up(self, env, mod_config):
        self._env = env
        self._mod_config = mod_config
        self._data_cache = DataCache()

        # 需要在用户的策略脚本中配置不加载mod_sys_simulation
        if self._env.config.mod.sys_simulation.enabled or self._env.broker or self._env.event_source:
            raise RuntimeError("请在策略脚本中增加config, {'mod':'sys_simulation':{'enabled': False,} } ")

        # 检查市场配置参数: 一个策略脚本只针对一个市场
        CheckFutuMarketConfig()

        # runtype有三种 ： 回测、实盘交易、仿真交易
        # futu api对接，只能支持港美股的实盘和港股的仿真
        CheckRunTypeConfig()

        # 初始化api行情对象
        self._quote_context = self._init_quote_context()

        # 替换关键组件
        self._set_broker()
        self._set_data_source()
        self._set_event_source()
        self._env.set_position_model(FUTU_ACCOUNT_TYPE.FUTU_STOCK.name, FutuStockPosition)
        self._env.set_account_model(FUTU_ACCOUNT_TYPE.FUTU_STOCK.name, FutuStockAccount)
        print(">>> FUTUMod.start_up")

    def tear_down(self, success, exception=None):
        print(">>> FUTUMod.tear_down")
        pass

    def _set_broker(self):
        if IsRuntype_Backtest():
            config_broker = self._mod_config.rqalpha_broker_config
            self._env.set_broker(RQSimulateBroker(self._env, config_broker))
        elif IsRuntype_RealtimeStrategy():
            if IsFutuMarket_HKStock():  # 港股实时策略
                broker = FUTUBrokerHK(self._env, self._mod_config)
                self._env.set_broker(broker)
            elif IsFutuMarket_USStock():  # 美股实时策略
                raise RuntimeError("_set_broker no impl")
        else:
            raise RuntimeError("_set_broker err param")

    def _set_event_source(self):
        if IsRuntype_Backtest():
            # event_source = FUTUEventForBacktest(self._env, self._env.config.base.accounts)
            event_source = FUTUEventForBacktest(self._env)
            self._env.set_event_source(event_source)
        elif IsRuntype_RealtimeStrategy():
            market_state_source = FUTUMarketStateSource(self._env, self._quote_context)
            event_source = FUTUEventForRealtime(self._env, self._mod_config, market_state_source)
            self._env.set_event_source(event_source)
        else:
            raise RuntimeError("_set_event_source err param")

    def _set_data_source(self):
        data_source = FUTUDataSource(self._env, self._quote_context, self._data_cache)  # 支持回测和实时
        if data_source is None:
            raise RuntimeError("_set_data_source err param")
        self._env.set_data_source(data_source)

    def _init_quote_context(self):
        self._quote_context = OpenQuoteContext(str(self._mod_config.api_svr.ip), int(self._mod_config.api_svr.port))
        return self._quote_context
