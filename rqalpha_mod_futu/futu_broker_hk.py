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

from rqalpha.interface import AbstractBroker
from rqalpha.const import DEFAULT_ACCOUNT_TYPE
from rqalpha.events import EVENT, Event
from rqalpha.model.order import *
from rqalpha.model.base_position import Positions
from rqalpha.model.portfolio import Portfolio
from rqalpha.model.trade import *
from rqalpha.utils.i18n import gettext as _
from .futu_utils import *

from time import sleep
from threading import Thread
from futuquant import OpenHKTradeContext


class FUTUBrokerHK(AbstractBroker):
    """
    FUTUBrokerHK 对象用于对接futu港股的仿真和真实交易
    设计思路：
    1. 帐户的初始资金需要在rqalpha框架下的config中设置 config.base.stock_starting_cash
    不与futu的帐户信息同步, 一方面是不影响长期自动运行时计算的收益率等指标,另一方面也为了控制策略脚本对futu实际帐户资金的占用.
    2. 初始化时会同步一次futu帐户的持仓数据, 后续状态完全由rqalpha框架内部维护状态, 故策略中记录的持仓有可能与用户实际futu帐户不一致
    3. 下单 ，撤单调后，脚本中会定时检查该订单在futu环境中的状态, 产生对应的event事件，可能存在延时。
    """

    def __init__(self, env, mod_config):
        self._env = env
        self._mod_config = mod_config
        self._portfolio = None
        self._open_order = []

        self._env.event_bus.add_listener(EVENT.PRE_BEFORE_TRADING, self._pre_before_trading)
        self._env.event_bus.add_listener(EVENT.PRE_AFTER_TRADING, self._pre_after_trading)

        # futu api创建及参数
        self._trade_context = OpenHKTradeContext(self._mod_config.api_svr.ip, self._mod_config.api_svr.port)
        self._trade_envtype = 1  # futu交易 envtype : 0 = 实盘  1 = 仿真
        if IsRuntype_RealTrade():
            self._trade_envtype = 0

        thread_order_check = Thread(target=self._thread_order_check)
        thread_order_check.setDaemon(True)
        thread_order_check.start()

    def get_portfolio(self):
        """
        获取投资组合。系统初始化时，会调用此接口，获取包含账户信息、净值、份额等内容的投资组合
        :return: Portfolio
        """
        if self._portfolio is not None:
            return self._portfolio
        self._portfolio = self._init_portfolio()

        if not self._portfolio._accounts:
            raise RuntimeError("accout config error")

        return self._portfolio

    def submit_order(self, order):
        """
        提交订单。在当前版本，RQAlpha 会生成 :class:`~Order` 对象，再通过此接口提交到 Broker。
        TBD: 由 Broker 对象生成 Order 并返回？
        """

        print("FUTUBrokerHK.submit_order:{}".format(order))
        if order.type == ORDER_TYPE.MARKET:
            raise RuntimeError("submit_order not support ORDER_TYPE.MARKET")

        account = self._get_account(order.order_book_id)
        self._env.event_bus.publish_event(Event(EVENT.ORDER_PENDING_NEW, account=account, order=order))
        order.active()

        # 发起futu api接口请求
        futu_order_side = 0 if order.side == SIDE.BUY else 1
        futu_order_type = 0  # 港股增强限价单
        ret_code, ret_data = self._trade_context.place_order(order.price, order.quantity, order.order_book_id,
                                                             futu_order_side, futu_order_type, self._trade_envtype)

        # 事件通知
        if ret_code != 0:
            order.mark_rejected("futu api req err:{} ".format(ret_code))
            self._env.event_bus.publish_event(Event(EVENT.ORDER_CREATION_REJECT, account=account, order=order))
        else:
            futu_order_id = ret_data.loc[0, 'orderid']
            self._open_order.append((futu_order_id, order))
            self._env.event_bus.publish_event(Event(EVENT.ORDER_CREATION_PASS, account=account, order=order))
            sleep(0.1)
            self._check_open_orders(futu_order_id)

    def cancel_order(self, order):
        """
        撤单。
        :param order: 订单
        :type order: :class:`~Order`
        """
        account = self._get_account(order.order_book_id)
        futu_order_id = self._get_futu_order_id(order)

        if futu_order_id is None:
            return

        # 立即检查一次订单状态
        self._check_open_orders(futu_order_id)
        if order.is_final():
            return

        self._env.event_bus.publish_event(Event(EVENT.ORDER_PENDING_CANCEL, account=account, order=order))
        ret_code, ret_data = self._trade_context.set_order_status(0, futu_order_id, self._env)  # 0 = 撤单
        if ret_code != 0:
            self._env.event_bus.publish_event(Event(EVENT.ORDER_CANCELLATION_REJECT, account=account, order=order))
        else:
            sleep(0.1)
            self._check_open_orders(futu_order_id)  # 提交请求后，立即再检查一次状态

    def get_open_orders(self, order_book_id=None):
        """
        [Required]
        获得当前未完成的订单。
        :return: list[:class:`~Order`]
        """
        if order_book_id is None:
            return [order for __, order in self._open_orders]
        else:
            return [order for __, order in self._open_orders if order.order_book_id == order_book_id]

    def _pre_before_trading(self, event):
        print("broker before_trading")

    def _pre_after_trading(self, event):
        # 收盘时清掉未完成的订单

        for __, order in self._open_order:
            order.mark_rejected(_(u"Order Rejected: {order_book_id} can not match. Market close.").format(
                order_book_id=order.order_book_id
            ))
            account = self._env.get_account(order.order_book_id)
            self._env.event_bus.publish_event(Event(EVENT.ORDER_UNSOLICITED_UPDATE, account=account, order=order))
        self._open_orders = []
        print("broker after_trading")

    def _check_open_orders(self, futu_order_id=None):
        if len(self._open_order) == 0:
            return
        ret_code, pd_data = self._trade_context.order_list_query('', self._trade_envtype)
        if ret_code != 0:
            return
        ft_orders = []
        if futu_order_id is not None:
            ft_orders.append(futu_order_id)
        else:
            for (fid, __) in self._open_order:
                ft_orders.append(fid)

        for fid in ft_orders:
            pd_find = pd_data[pd_data.orderid == fid]
            if len(pd_find) != 1:
                continue
            order = self._get_order_by_futu_id(fid)
            account = self._get_account(order.order_book_id)
            if order is None:
                continue

            ct_amount = 0  # 期货用的，期货分平当天的仓位和以前的仓位
            price = order.avg_price  # 分多笔成交下的平均值
            trade = Trade.__from_create__(
                order_id=order.order_id,
                price=price,
                amount=0,
                side=order.side,
                position_effect=order.position_effect,
                order_book_id=order.order_book_id,
                frozen_price=order.frozen_price,
                close_today_amount=ct_amount,
                commission=0.,
                tax=0., trade_id=None
            )
            trade._commission = 0
            trade._tax = 0

            row = pd_find.iloc[0]
            ft_status = int(row['status'])
            if ft_status == 2 or ft_status == 3:  # 部分成交 | 全部成交
                qty_deal_last = order.quantity - order.unfilled_quantity
                qty_deal_new = int(row['dealt_qty'])
                if qty_deal_last == qty_deal_new:  # 记录的成交数量与上次相同
                    continue
                trade._amount = qty_deal_new - qty_deal_last
                order.fill(trade)
                self._env.event_bus.publish_event(Event(EVENT.TRADE, account=account, trade=trade, order=order))
                if ft_status == 3:
                    self._remove_open_order_by_futu_id(fid)

            elif ft_status == 5:  # 下单失败
                self._env.event_bus.publish_event(Event(EVENT.ORDER_CREATION_REJECT, account=account, order=order))
                self._remove_open_order_by_futu_id(fid)

            elif ft_status == 6:  # 6=已撤单
                order.mark_cancelled(_(u"{order_id} order has been cancelled by user.").format(order_id=order.order_id))
                self._env.event_bus.publish_event(Event(EVENT.ORDER_CANCELLATION_PASS, account=account, order=order))
                self._remove_open_order_by_futu_id(fid)

            elif ft_status == 4 or ft_status == 7:  # 4=已失效  	7=已删除
                reason = _(u"Order Cancelled:  code = {order_book_id} ft_status = {ft_status} ").format(
                    order_book_id=order.order_book_id, ft_status=ft_status)
                order.mark_rejected(reason)
                self._env.event_bus.publish_event(Event(EVENT.ORDER_CREATION_REJECT, account=account, order=order))
                self._remove_open_order_by_futu_id(fid)

            else:
                pass  # 8 = 等待开盘 21= 本地已发送 22=本地已发送，服务器返回下单失败、没产生订单 23=本地已发送，等待服务器返回超时

    def _get_futu_positions(self, env):
        StockPosition = env.get_position_model(DEFAULT_ACCOUNT_TYPE.STOCK.name)
        positions = Positions(StockPosition)
        ret, pd_data = self._trade_context.position_list_query(self._trade_envtype)
        if ret != 0:
            return None
        for i in range(len(pd_data)):
            row = pd_data.iloc[i]
            code_str = str(row['code'])
            pos_state = {}
            pos_state['order_book_id'] = code_str
            pos_state['quantity'] = int(row['qty'])
            pos_state['avg_price'] = float(row['cost_price'])
            pos_state['non_closable'] = 0
            pos_state['frozen'] = int(row['qty']) - int(row['can_sell_qty'])
            pos_state['transaction_cost'] = 0
            item = positions.get_or_create(code_str)
            item.set_state(pos_state)
        return positions

    def _init_portfolio(self):
        accounts = {}
        config = self._env.config
        start_date = config.base.start_date
        total_cash = 0
        for account_type, stock_starting_cash in six.iteritems(config.base.accounts):
            if account_type == DEFAULT_ACCOUNT_TYPE.STOCK.name:
                # stock_starting_cash = config.base.accounts
                if stock_starting_cash == 0:
                    raise RuntimeError(_(u"stock starting cash can not be 0, using `--stock-starting-cash 1000`"))
                all_positons = self._get_futu_positions(self._env)
                if all_positons is None:
                    raise RuntimeError("_init_portfolio fail")
                StockAccount = self._env.get_account_model(DEFAULT_ACCOUNT_TYPE.STOCK.name)
                accounts[DEFAULT_ACCOUNT_TYPE.STOCK.name] = StockAccount(stock_starting_cash, all_positons)
                total_cash += stock_starting_cash
            else:
                raise NotImplementedError

        return Portfolio(start_date, 1, total_cash, accounts)

    def _get_account(self, order_book_id):
        # account = self._env.get_account(order_book_id)
        # for debug
        account = self._env.portfolio.accounts[DEFAULT_ACCOUNT_TYPE.STOCK.name]
        return account

    def _get_futu_order_id(self, order):
        for fid, order_item in self._open_order:
            if order_item is order:
                return fid
        return None

    def _get_order_by_futu_id(self, futu_order_id):
        for fid, order_item in self._open_order:
            if futu_order_id == fid:
                return order_item
        return None

    def _remove_open_order_by_futu_id(self, futu_order_id):
        order = self._get_order_by_futu_id(futu_order_id)
        if order is not None:
            self._open_order.remove((futu_order_id, order))

    def _thread_order_check(self):
        while True:
            if len(self._open_order) == 0:
                print("broker:_thread_order_check None")
                sleep(5)
            else:
                self._check_open_orders()
                sleep(1)
