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

from .futu_market_state import *

from rqalpha.interface import AbstractEventSource
from rqalpha.events import Event, EVENT
from rqalpha.const import DEFAULT_ACCOUNT_TYPE
from rqalpha.utils import get_account_type
from rqalpha.utils.datetime_func import convert_int_to_datetime
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.exception import CustomException, CustomError, patch_user_exc
from rqalpha.utils.logger import system_log

from datetime import timedelta, date, datetime


class FUTUEventForBacktest(AbstractEventSource):
    """ 回测用的event source """
    def __init__(self, env):
        self._env = env
        self._config = env.config
        self._universe_changed = False
        self._env.event_bus.add_listener(
            EVENT.POST_UNIVERSE_CHANGED, self._on_universe_changed)

    def _on_universe_changed(self, event):
        self._universe_changed = True

    def _get_universe(self):
        universe = self._env.get_universe()
        if len(universe) == 0 and DEFAULT_ACCOUNT_TYPE.STOCK.name not in self._config.base.accounts:
            error = CustomError()
            error.set_msg(
                "Current universe is empty. Please use subscribe function before trade")
            raise patch_user_exc(CustomException(error), force=True)
        return universe

    # [BEGIN] minute event helper
    @staticmethod
    def _get_stock_trading_minutes(trading_date):
        trading_minutes = set()
        # current_dt = datetime.combine(trading_date, time(9, 30))
        current_dt = trading_date.replace(hour=9, minute=30)
        am_end_dt = current_dt.replace(hour=12, minute=00)
        pm_start_dt = current_dt.replace(hour=13, minute=1)
        pm_end_dt = current_dt.replace(hour=16, minute=0)
        delta_minute = timedelta(minutes=1)
        while current_dt <= am_end_dt:
            trading_minutes.add(current_dt)
            current_dt += delta_minute

        current_dt = pm_start_dt
        while current_dt <= pm_end_dt:
            trading_minutes.add(current_dt)
            current_dt += delta_minute
        return trading_minutes

    def _get_future_trading_minutes(self, trading_date):
        trading_minutes = set()
        universe = self._get_universe()
        for order_book_id in universe:
            if get_account_type(order_book_id) == DEFAULT_ACCOUNT_TYPE.STOCK.name:
                continue
            trading_minutes.update(
                self._env.data_proxy.get_trading_minutes_for(order_book_id, trading_date))
        return set([convert_int_to_datetime(minute) for minute in trading_minutes])

    def _get_trading_minutes(self, trading_date):
        trading_minutes = set()
        for account_type in self._config.base.accounts:
            if account_type == DEFAULT_ACCOUNT_TYPE.STOCK.name:
                trading_minutes = trading_minutes.union(
                    self._get_stock_trading_minutes(trading_date))
            elif account_type == DEFAULT_ACCOUNT_TYPE.FUTURE.name:
                trading_minutes = trading_minutes.union(
                    self._get_future_trading_minutes(trading_date))
        return sorted(list(trading_minutes))
    # [END] minute event helper

    def events(self, start_date, end_date, frequency):
        if frequency == "1d":
            # 根据起始日期和结束日期，获取所有的交易日，然后再循环获取每一个交易日
            for day in self._env.data_proxy.get_trading_dates(start_date, end_date):
                _date = day.to_pydatetime()
                dt_before_trading = _date.replace(hour=0, minute=0)
                dt_bar = _date.replace(hour=15, minute=0)
                dt_after_trading = _date.replace(hour=16, minute=30)
                dt_settlement = _date.replace(hour=18, minute=0) + timedelta(days=2)
                yield Event(EVENT.BEFORE_TRADING, calendar_dt=dt_before_trading, trading_dt=dt_before_trading)
                yield Event(EVENT.BAR, calendar_dt=dt_bar, trading_dt=dt_bar)

                yield Event(EVENT.AFTER_TRADING, calendar_dt=dt_after_trading, trading_dt=dt_after_trading)
                yield Event(EVENT.SETTLEMENT, calendar_dt=dt_settlement, trading_dt=dt_settlement)
        elif frequency == '1m':
            for day in self._env.data_proxy.get_trading_dates(start_date, end_date):
                before_trading_flag = True
                _date = day.to_pydatetime()
                last_dt = None
                done = False

                dt_before_day_trading = _date.replace(hour=8, minute=30)

                while True:
                    if done:
                        break
                    exit_loop = True
                    trading_minutes = self._get_trading_minutes(_date)
                    for calendar_dt in trading_minutes:
                        if last_dt is not None and calendar_dt < last_dt:
                            continue

                        if calendar_dt < dt_before_day_trading:
                            trading_dt = calendar_dt.replace(year=_date.year,
                                                             month=_date.month,
                                                             day=_date.day)
                        else:
                            trading_dt = calendar_dt
                        if before_trading_flag:
                            before_trading_flag = False
                            yield Event(EVENT.BEFORE_TRADING,
                                        calendar_dt=calendar_dt - timedelta(minutes=30),
                                        trading_dt=trading_dt - timedelta(minutes=30))
                        if self._universe_changed:
                            self._universe_changed = False
                            last_dt = calendar_dt
                            exit_loop = False
                            break
                        # yield handle bar
                        yield Event(EVENT.BAR, calendar_dt=calendar_dt, trading_dt=trading_dt)
                    if exit_loop:
                        done = True

                dt = _date.replace(hour=15, minute=30)
                yield Event(EVENT.AFTER_TRADING, calendar_dt=dt, trading_dt=dt)

                dt = _date.replace(hour=17, minute=0)
                yield Event(EVENT.SETTLEMENT, calendar_dt=dt, trading_dt=dt)
        elif frequency == "tick":
            raise NotImplementedError()
            data_proxy = self._env.data_proxy
            for day in data_proxy.get_trading_dates(start_date, end_date):
                _date = day.to_pydatetime()
                last_tick = None
                last_dt = None
                dt_before_day_trading = _date.replace(hour=8, minute=30)
                while True:
                    for tick in data_proxy.get_merge_ticks(self._get_universe(), _date, last_dt):
                        # find before trading time
                        if last_tick is None:
                            last_tick = tick
                            dt = tick.datetime
                            before_trading_dt = dt - timedelta(minutes=30)
                            yield Event(EVENT.BEFORE_TRADING, calendar_dt=before_trading_dt,
                                        trading_dt=before_trading_dt)

                        dt = tick.datetime

                        if dt < dt_before_day_trading:
                            trading_dt = dt.replace(
                                year=_date.year, month=_date.month, day=_date.day)
                        else:
                            trading_dt = dt

                        yield Event(EVENT.TICK, calendar_dt=dt, trading_dt=trading_dt, tick=tick)

                        if self._universe_changed:
                            self._universe_changed = False
                            last_dt = dt
                            break
                    else:
                        break

                dt = _date.replace(hour=15, minute=30)
                yield Event(EVENT.AFTER_TRADING, calendar_dt=dt, trading_dt=dt)

                dt = _date.replace(hour=17, minute=0)
                yield Event(EVENT.SETTLEMENT, calendar_dt=dt, trading_dt=dt)
        else:
            raise NotImplementedError(
                _("Frequency {} is not support.").format(frequency))


class TimePeriod(Enum):
    BEFORE_TRADING = 'before_trading'
    AFTER_TRADING = 'after_trading'
    REST = "rest"
    TRADING = 'trading'
    CLOSING = 'closing'


class FUTUEventForRealtime(AbstractEventSource):
    """ 实时策略的event """
    def __init__(self, env, mod_config, market_state_source):
        self._env = env
        self._mod_config = mod_config
        fps = int(float(self._mod_config.futu_bar_fps) * 1000)  # 转成毫秒
        self._fps_delta_dt = timedelta(
            days=0, seconds=fps//1000, microseconds=fps % 1000)

        self._before_trading_processed = False
        self._after_trading_processed = False
        self._time_period = None
        self._market_state_source = market_state_source
        self._last_onbar_dt = None

    def mark_time_period(self, start_date, end_date):
        trading_days = self._env.data_proxy.get_trading_dates(
            start_date, end_date)

        def in_before_trading_time(time):
            return self._market_state_source.get_futu_market_state() == Futu_Market_State.MARKET_PRE_OPEN

        def in_after_trading(time):
            return self._market_state_source.get_futu_market_state() == Futu_Market_State.MARKET_CLOSE

        def in_rest_trading(time):
            return self._market_state_source.get_futu_market_state() == Futu_Market_State.MARKET_REST

        def in_trading_time(time):
            return self._market_state_source.get_futu_market_state() == Futu_Market_State.MARKET_OPEN

        def in_trading_day(time):
            if time.date() in trading_days:
                return True
            return False

        while True:
            now = datetime.now()
            if in_trading_time(now):
                self._time_period = TimePeriod.TRADING
                continue
            if in_rest_trading(now):
                self._time_period = TimePeriod.REST
                continue
            if not in_trading_day(now):
                self._time_period = TimePeriod.CLOSING
                continue
            if in_before_trading_time(now):
                self._time_period = TimePeriod.BEFORE_TRADING
                continue
            if in_after_trading(now):
                self._time_period = TimePeriod.AFTER_TRADING
                continue
            else:
                self._time_period = TimePeriod.CLOSING
                continue

    def events(self, start_date, end_date, frequency):

        while datetime.now().date() < start_date - timedelta(days=1):
            continue

        mark_time_thread = Thread(target=self.mark_time_period, args=(
            start_date, date.fromtimestamp(2147483647)))
        mark_time_thread.setDaemon(True)
        mark_time_thread.start()
        while True:
            if self._time_period == TimePeriod.BEFORE_TRADING:
                if self._after_trading_processed:
                    self._after_trading_processed = False
                if not self._before_trading_processed:
                    system_log.debug(
                        "FUTUEventForRealtime: before trading event")
                    yield Event(EVENT.BEFORE_TRADING, calendar_dt=datetime.now(), trading_dt=datetime.now())
                    self._before_trading_processed = True
                    continue
                else:
                    sleep(0.01)
                    continue
            elif self._time_period == TimePeriod.TRADING:
                now_dt = datetime.now()
                if not self._before_trading_processed:
                    yield Event(EVENT.BEFORE_TRADING, calendar_dt=now_dt, trading_dt=now_dt)
                    self._before_trading_processed = True
                    continue
                else:
                    fire_bar = False
                    if not self._last_onbar_dt or (now_dt > (self._last_onbar_dt + self._fps_delta_dt)):
                        self._last_onbar_dt = now_dt
                        fire_bar = True
                    if fire_bar:
                        system_log.debug("FUTUEventForRealtime: BAR event")
                        yield Event(EVENT.BAR, calendar_dt=now_dt, trading_dt=now_dt)
                    else:
                        sleep(0.01)
                    continue
            elif self._time_period == TimePeriod.AFTER_TRADING:
                if self._before_trading_processed:
                    self._before_trading_processed = False
                if not self._after_trading_processed:
                    system_log.debug(
                        "FUTUEventForRealtime: after trading event")
                    yield Event(EVENT.AFTER_TRADING, calendar_dt=datetime.now(), trading_dt=datetime.now())
                    self._after_trading_processed = True
                else:
                    sleep(0.01)
                    continue
