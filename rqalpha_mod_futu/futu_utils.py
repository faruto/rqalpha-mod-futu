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


from rqalpha.const import RUN_TYPE
from rqalpha.environment import Environment

import six


def IsFutuMarket_CNStock():
    """配置市场: 是否A股"""
    mkt = ["SH", "SZ"]
    cfg = Environment.get_instance().config.mod.futu.futu_market
    if isinstance(cfg, six.string_types):
        cfg = [cfg]
    for x in cfg:
        if str(x) in mkt:
            return True
    return False


def IsFutuMarket_HKStock():
    """配置市场: 是否港股股票"""
    mkt = ["HK"]
    cfg = Environment.get_instance().config.mod.futu.futu_market
    if isinstance(cfg, six.string_types):
        cfg = [cfg]
    for x in cfg:
        if str(x) in mkt:
            return True
    return False


def IsFutuMarket_USStock():
    """配置市场: 是否美股股票"""
    mkt = ["US"]
    cfg = Environment.get_instance().config.mod.futu.futu_market
    if isinstance(cfg, six.string_types):
        cfg = [cfg]
    for x in cfg:
        if str(x) in mkt:
            return True
    return False


def CheckFutuMarketConfig():
    """配置市场: 检查是否合法"""
    mkts = 0
    if IsFutuMarket_CNStock():
        mkts += 1
    if IsFutuMarket_HKStock():
        mkts += 1
    if IsFutuMarket_USStock():
        mkts += 1
    if mkts != 1:
        cfg = Environment.get_instance().config.mod.futu.futu_market
        raise RuntimeError("futu_market config err:{}".format(cfg))


def CheckRunTypeConfig():
    """配置runtype: 检查是否api能支持"""
    run_type = Environment.get_instance().config.base.run_type
    if run_type == RUN_TYPE.PAPER_TRADING:
        if IsFutuMarket_CNStock() or IsFutuMarket_USStock():
            raise RuntimeError("futu api的实时模拟交易仅支持港股!")
    if run_type == RUN_TYPE.LIVE_TRADING:
        if IsFutuMarket_CNStock():
            raise RuntimeError("futu api的实盘交易仅支持港股和美股!")


def IsRuntype_Backtest():
    """运行模式: 是否回测"""
    run_type = Environment.get_instance().config.base.run_type
    return run_type == RUN_TYPE.BACKTEST


def IsRuntype_RealtimeStrategy():
    """运行模式: 是否实时策略"""
    run_type = Environment.get_instance().config.base.run_type
    return run_type == RUN_TYPE.LIVE_TRADING or run_type == RUN_TYPE.PAPER_TRADING


def IsRuntype_RealTrade():
    """运行模式: 是否实盘交易"""
    run_type = Environment.get_instance().config.base.run_type
    return run_type == RUN_TYPE.LIVE_TRADING
