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

from rqalpha.api import *


# 在这个方法中编写任何的初始化逻辑。context对象将会在你的算法策略的任何方法之间做传递。
def log_cash(context, bar_dict):
    logger.info("Remaning cash: %r" % context.portfolio.cash)


def init(context):
    logger.info("init")
    context.s1 = "HK.00001"

    update_universe(context.s1)
    # 是否已发送了order
    context.fired = False
    context.days = 0


def before_trading(context):
    print("before trading ... ")
    pass


def after_trading(context):
    print("after_trading ... ")
    pass


# 你选择的证券的数据更新将会触发此段逻辑，例如日或分钟历史数据切片或者是实时数据切片更新
def handle_bar(context, bar_dict):
    # 开始编写你的主要的算法逻辑

    # bar_dict[order_book_id] 可以拿到某个证券的bar信息
    # context.portfolio 可以拿到现在的投资组合状态信息

    # 使用order_shares(id_or_ins, amount)方法进行落单
    context.days += 1
    # TODO: 开始编写你的算法吧！
    if not context.fired:
        # order_percent并且传入1代表买入该股票并且使其占有投资组合的100%
        # order_percent(context.s1, 1)
        order_price =bar_dict[context.s1].low
        ret_order = order_percent(context.s1, 0.1, style=LimitOrder(order_price))
        print("order_percent finish:{}!".format(ret_order))
        context.fired = True
