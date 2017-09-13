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


from .futu_utils import *

from rqalpha.interface import AbstractDataSource
from rqalpha.model.instrument import Instrument
from rqalpha.environment import Environment
from rqalpha.events import EVENT
from rqalpha.utils.i18n import gettext as _

from futuquant.open_context import CurKlineHandlerBase
from datetime import date, timedelta, datetime
import pandas as pd
import time
import six

RET_OK = 0
RET_ERROR = -1


class FUTUDataSource(AbstractDataSource):
    def __init__(self, env, quote_context, data_cache):
        self._env = env
        self._quote_context = quote_context
        # 订阅，得到cache的时候，订阅，拉历史，得到当前数据，push动态更新，去重
        self._quote_context.subscribe(stock_code=self._env.config.base.benchmark, data_type='K_DAY', push=False)
        self._quote_context.subscribe(stock_code=self._env.config.base.benchmark, data_type='K_1M', push=False)
        self._cache = data_cache._cache
        self._today = None
        self._data_cache = data_cache

    def get_all_instruments(self):
        """
        获取所有Instrument。---再封装一层，单独写个cache
        :return: list[:class:`~Instrument`]
        """
        if IsFutuMarket_HKStock() is True:
            if self._cache['basicinfo_hk'] is None:
                ret_code, ret_data = self._get_hk_cache()
            else:
                ret_code, ret_data = 0, self._cache['basicinfo_hk']

        elif IsFutuMarket_USStock() is True:
            if self._cache['basicinfo_us'] is None:
                ret_code, ret_data_cs = self._get_us_cache()
            else:
                ret_code, ret_data = 0, self._cache['basicinfo_us']
        else:
            raise ValueError

        if ret_code == RET_ERROR or ret_data is None:
            raise NotImplementedError

        all_instruments = [Instrument(i) for i in ret_data]
        return all_instruments

    def _get_hk_cache(self):
        for i in range(3):
            ret_code, ret_data_cs = self._quote_context.get_stock_basicinfo(market="HK", stock_type="STOCK")
            if ret_code != RET_ERROR and ret_data_cs is not None:
                break
            else:
                time.sleep(0.1)
        if ret_code == RET_ERROR or ret_data_cs is None:
            print("get instrument cache error")
        else:
            ret_data_cs.at[ret_data_cs.index, 'stock_type'] = 'CS'

        for i in range(3):
            ret_code, ret_data_idx = self._quote_context.get_stock_basicinfo("HK", "IDX")
            if ret_code != RET_ERROR and ret_data_idx is not None:
                break
            else:
                time.sleep(0.1)
        if ret_code == RET_ERROR or ret_data_idx is None:
            print("get instrument cache error")
        else:
            ret_data_idx.at[ret_data_idx.index, 'stock_type'] = 'INDX'

        for i in range(3):
            ret_code, ret_data_etf = self._quote_context.get_stock_basicinfo("HK", "ETF")
            if ret_code != RET_ERROR and ret_data_etf is not None:
                break
            else:
                time.sleep(0.1)
        if ret_code == RET_ERROR or ret_data_etf is None:
            print("get instrument cache error")

        for i in range(3):
            ret_code, ret_data_war = self._quote_context.get_stock_basicinfo("HK", "WARRANT")
            if ret_code != RET_ERROR and ret_data_war is not None:
                break
            else:
                time.sleep(0.1)
        if ret_code == RET_ERROR or ret_data_war is None:
            print("get instrument cache error")
        else:
            ret_data_war.at[ret_data_war.index, 'stock_type'] = 'CS'

        for i in range(3):
            ret_code, ret_data_bond = self._quote_context.get_stock_basicinfo("HK", "BOND")
            if ret_code != RET_ERROR and ret_data_bond is not None:
                break
            else:
                time.sleep(0.1)
        if ret_code == RET_ERROR or ret_data_bond is None:
            print("get instrument cache error")

        frames = [ret_data_cs, ret_data_idx, ret_data_etf, ret_data_war, ret_data_bond]
        ret_data = pd.concat(frames).reset_index(drop=True)

        del ret_data['stock_child_type'], ret_data['owner_stock_code']  # 删除多余的列
        ret_data.reset_index(drop=True)

        ret_data['de_listed_date'] = str("2999-12-31")  # 增加一列退市日期

        ret_data.rename(columns={'code': 'order_book_id', 'name': 'symbol', 'stock_type': 'type', 'listing_date':
            'listed_date', 'lot_size': 'round_lot'}, inplace=True)  # 修改列名
        ret_data = ret_data.to_dict(orient='records')  # 转置并转为字典格式
        self._cache['basicinfo_hk'] = ret_data

        return ret_code, ret_data

    def _get_us_cache(self):
        for i in range(3):
            ret_code, ret_data_cs = self._quote_context.get_stock_basicinfo(market="US", stock_type="STOCK")
            if ret_code != RET_ERROR and ret_data_cs is not None:
                break
            else:
                time.sleep(0.1)
        if ret_code == RET_ERROR or ret_data_cs is None:
            print("get instrument cache error")
        else:
            ret_data_cs.at[ret_data_cs.index, 'stock_type'] = 'CS'

        for i in range(3):
            ret_code, ret_data_idx = self._quote_context.get_stock_basicinfo("US", "IDX")
            if ret_code != RET_ERROR and ret_data_idx is not None:
                break
            else:
                time.sleep(0.1)
        if ret_code == RET_ERROR or ret_data_idx is None:
            print("get instrument cache error")
        else:
            ret_data_idx.at[ret_data_idx.index, 'stock_type'] = 'INDX'

        for i in range(3):
            ret_code, ret_data_etf = self._quote_context.get_stock_basicinfo("US", "ETF")
            if ret_code != RET_ERROR and ret_data_etf is not None:
                break
            else:
                time.sleep(0.1)
        if ret_code == RET_ERROR or ret_data_etf is None:
            print("get instrument cache error")

        frames = [ret_data_cs, ret_data_idx, ret_data_etf]
        ret_data = pd.concat(frames).reset_index(drop=True)

        del ret_data['stock_child_type'], ret_data['owner_stock_code']  # 删除多余的列
        ret_data.reset_index(drop=True)

        ret_data['de_listed_date'] = str("2999-12-31")  # 增加一列退市日期

        ret_data.rename(columns={'code': 'order_book_id', 'name': 'symbol', 'stock_type': 'type', 'listing_date':
            'listed_date', 'lot_size': 'round_lot'}, inplace=True)  # 修改列名
        ret_data = ret_data.to_dict(orient='records')  # 转置并转为字典格式
        self._cache['basicinfo_us'] = ret_data

        return ret_code, ret_data

    def get_bar(self, instrument, dt, frequency):
        """
        根据 dt 来获取对应的 Bar 数据 ---待实现 相当于获取K线 先从历史数据找（需要历史更新程序并且全量下载了），找到返回，
        没找到再从当前(获取指定时间的bar)---接口设计应该是先判断是否有cache，没有就chche，有的话就直接取.所有的先cache，取消当前K线cache

        :param instrument: 合约对象
        :type instrument: :class:`~Instrument`

        :param datetime.datetime dt: calendar_datetime

        :param str frequency: 周期频率，`1d` 表示日周期, `1m` 表示分钟周期

        :return: `numpy.ndarray` | `dict`
        """
        if frequency == '1d':
            return self.get_bar_day(instrument, dt)
        elif frequency == '1m':
            return self.get_bar_minute(instrument, dt)
        else:
            raise NotImplementedError

    def get_bar_minute(self, instrument, dt):
        if dt is None:
            dt = datetime.now()

        current_time = time.strftime("%Y%m%d%H%M", time.localtime())
        dt_time = dt.strftime("%Y%m%d%H%M")

        if dt_time == current_time:  # 判断时间是否是当天，每天都是要清空缓存，所以要先获取历史
            if self._cache['history_minute_kline'] is None or instrument.order_book_id not in self._cache[
                'history_minute_kline'].keys():
                ret_code, bar_data = self._get_cur_minute_cache(instrument)
            else:
                ret_code, bar_data = 0, self._cache['history_minute_kline'][instrument.order_book_id]
        elif dt_time != current_time:
            if self._cache['history_minute_kline'] is None or instrument.order_book_id not in self._cache[
                'history_minute_kline'].keys():
                ret_code, bar_data = self._get_history_minute_cache(instrument)
            else:
                ret_code, bar_data = 0, self._cache['history_minute_kline'][instrument.order_book_id]

        if ret_code == RET_ERROR or bar_data is None:
            raise Exception("can't get bar data")

        ret_dict = bar_data[bar_data.datetime <= int(dt_time + "00")].iloc[0].to_dict()

        return ret_dict

    def get_bar_day(self, instrument, dt):
        if dt is None:
            dt = datetime.now()

        current_time = time.strftime("%Y%m%d", time.localtime())
        dt_time = dt.strftime("%Y%m%d")

        if dt_time == current_time:  # 判断时间是否是当天，每天都是要清空缓存，所以要先获取历史
            if self._cache['history_kline'] is None or instrument.order_book_id not in self._cache[
                'history_kline'].keys():
                ret_code, bar_data = self._get_cur_cache(instrument)
            else:
                ret_code, bar_data = 0, self._cache['history_kline'][instrument.order_book_id]
        elif dt_time != current_time:
            if self._cache['history_kline'] is None or instrument.order_book_id not in self._cache[
                'history_kline'].keys():
                ret_code, bar_data = self._get_history_cache(instrument)
            else:
                ret_code, bar_data = 0, self._cache['history_kline'][instrument.order_book_id]

        if ret_code == RET_ERROR or bar_data is None:
            raise Exception("can't get bar data")

        ret_dict = bar_data[bar_data.datetime <= int(dt_time + "000000")].iloc[0].to_dict()

        return ret_dict

    def _fill_minute_cur_kline_cache_data(self, instrument):
        order_book_id = instrument.order_book_id
        for x in range(3):
            ret_code, ret_data = self._quote_context.get_cur_kline(order_book_id, 1, 'K_1M')
            if ret_code == 0 and len(ret_data) >= 1:
                bar_data = ret_data.iloc[-1:].copy()
                # 时间转换
                for i in range(len(bar_data['time_key'])):  # 时间转换
                    bar_data.loc[i, 'time_key'] = int(
                        bar_data['time_key'][i].replace('-', '').replace(' ', '').replace(':', ''))

                bar_data.rename(columns={'time_key': 'datetime', 'turnover': 'total_turnover'},
                                inplace=True)  # 将字段名称改为一致的
                bar_data['volume'] = bar_data['volume'].astype('float64')  # 把成交量的数据类型转为float
                self._cache['cur_minute_kline'][order_book_id] = bar_data
                break

    def _fill_cur_kline_cache_data(self, instrument):
        order_book_id = instrument.order_book_id
        for x in range(3):
            ret_code, ret_data = self._quote_context.get_cur_kline(order_book_id, 1, 'K_DAY')
            if ret_code == 0 and len(ret_data) >= 1:
                bar_data = ret_data.iloc[-1:].copy()
                # 时间转换
                for i in range(len(bar_data['time_key'])):  # 时间转换
                    bar_data.loc[i, 'time_key'] = int(
                        bar_data['time_key'][i].replace('-', '').replace(' ', '').replace(':', ''))

                bar_data.rename(columns={'time_key': 'datetime', 'turnover': 'total_turnover'},
                                inplace=True)  # 将字段名称改为一致的
                bar_data['volume'] = bar_data['volume'].astype('float64')  # 把成交量的数据类型转为float
                self._cache['cur_kline'][order_book_id] = bar_data
                break

    def _get_cur_minute_cache(self, instrument):
        ret_code = 0
        if self._cache['cur_minute_kline'] or instrument.order_book_id not in self._cache['cur_minute_kline'].keys():
            self._quote_context.subscribe(instrument.order_book_id, "K_1M", push=True)
            self._quote_context.set_handler(self._data_cache)
            self._quote_context.start()
            self._fill_cur_minute_kline_cache_data(instrument)
        else:
            return ret_code, self._cache['cur_minute_kline'][instrument.order_book_id]
        return ret_code, self._cache['cur_minute_kline'][instrument.order_book_id]

    def _get_cur_cache(self, instrument):
        ret_code = 0
        if self._cache['cur_kline'] or instrument.order_book_id not in self._cache['cur_kline'].keys():
            self._quote_context.subscribe(instrument.order_book_id, "K_DAY", push=True)
            self._quote_context.set_handler(self._data_cache)
            self._quote_context.start()
            self._fill_cur_kline_cache_data(instrument)
        else:
            return ret_code, self._cache['cur_kline'][instrument.order_book_id]
        return ret_code, self._cache['cur_kline'][instrument.order_book_id]

    def _get_history_minute_cache(self, instrument):
        one_day = timedelta(days=1)
        bar_data = pd.DataFrame()
        if self._cache['history_minute_kline'] is None:
            self._cache['history_minute_kline'] = {}
        self._cache['history_minute_kline'][instrument.order_book_id] = pd.DataFrame()
        trading_days = None
        if 'HK.' in instrument.order_book_id:
            ret, trading_days = self._quote_context.get_trading_days('HK')
            if ret != RET_OK:
                raise Exception("can't get hk trading days")
        elif 'US.' in instrument.order_book_id:
            ret, trading_days = self._quote_context.get_trading_days('US')
            if ret != RET_OK:
                raise Exception("can't get us trading days")
        else:
            raise NotImplementedError
        for trading_day in trading_days:
            if bar_data is None:
                break
            begin_date = datetime.strptime(trading_day, '%Y-%m-%d')
            end_date = begin_date + one_day
            for i in range(3):
                ret_code, bar_data = self._quote_context.get_history_kline(instrument.order_book_id,
                                                                           start=begin_date.strftime('%Y-%m-%d'),
                                                                           end=end_date.strftime('%Y-%m-%d'),
                                                                           ktype='K_1M')
                if ret_code != RET_ERROR:
                    break
                else:
                    time.sleep(0.1)
            if ret_code == RET_ERROR or isinstance(bar_data, str):
                print("get history minute kline error")

            if bar_data.empty:
                return ret_code, self._cache['history_minute_kline'][instrument.order_book_id]
            end_date = begin_date
            # 对数据做处理先做处理再存
            del bar_data['code']  # 去掉code
            for i in range(len(bar_data)):  # 时间转换
                bar_data.loc[i, 'time_key'] = int(
                    bar_data['time_key'][i].replace('-', '').replace(' ', '').replace(':', ''))
            bar_data['volume'] = bar_data['volume'].astype('float64')  # 把成交量的数据类型转为float
            bar_data.rename(columns={'time_key': 'datetime', 'turnover': 'total_turnover'}, inplace=True)  # 将字段名称改为一致的
            bar_data = bar_data[::-1]

            self._cache['history_minute_kline'][instrument.order_book_id] = self._cache['history_minute_kline'][
                instrument.order_book_id].append(bar_data)
        return ret_code, self._cache['history_minute_kline'][instrument.order_book_id]

    def _get_history_cache(self, instrument):
        end_date = date.today().replace(month=12, day=31)
        last_year = timedelta(days=365)
        bar_data = pd.DataFrame()
        if self._cache['history_kline'] is None:
            self._cache['history_kline'] = {}
        self._cache['history_kline'][instrument.order_book_id] = pd.DataFrame()
        while bar_data is not None:
            begin_date = end_date - last_year
            for i in range(3):
                ret_code, bar_data = self._quote_context.get_history_kline(instrument.order_book_id,
                                                                           start=begin_date.strftime('%Y-%m-%d'),
                                                                           end=end_date.strftime('%Y-%m-%d'),
                                                                           ktype='K_DAY')
                if ret_code != RET_ERROR:
                    break
                else:
                    time.sleep(0.1)
            if ret_code == RET_ERROR or isinstance(bar_data, str):
                print("get history kline error")

            if bar_data.empty:
                return ret_code, self._cache['history_kline'][instrument.order_book_id]
            end_date = begin_date

            # 对数据做处理先做处理再存
            del bar_data['code']  # 去掉code
            for i in range(len(bar_data)):  # 时间转换
                bar_data.loc[i, 'time_key'] = int(
                    bar_data['time_key'][i].replace('-', '').replace(' ', '').replace(':', ''))
            bar_data['volume'] = bar_data['volume'].astype('float64')  # 把成交量的数据类型转为float
            bar_data.rename(columns={'time_key': 'datetime', 'turnover': 'total_turnover'}, inplace=True)  # 将字段名称改为一致的
            bar_data = bar_data[::-1]

            self._cache['history_kline'][instrument.order_book_id] = self._cache['history_kline'][
                instrument.order_book_id].append(bar_data)
        return ret_code, self._cache['history_kline'][instrument.order_book_id]

    def history_bars(self, instrument, bar_count, frequency, fields, dt, skip_suspended=True,
                     include_now=False, adjust_type='pre', adjust_orig=None):
        """
        获取历史数据 这个先从cache中取得  获取指定时间段的bar数据

        :param instrument: 合约对象
        :type instrument: :class:`~Instrument`

        :param int bar_count: 获取的历史数据数量
        :param str frequency: 周期频率，`1d` 表示日周期, `1m` 表示分钟周期
        :param str fields: 返回数据字段

        =========================   ===================================================
        fields                      字段名
        =========================   ===================================================
        datetime                    时间戳
        open                        开盘价
        high                        最高价
        low                         最低价
        close                       收盘价
        volume                      成交量
        total_turnover              成交额
        datetime                    int类型时间戳
        open_interest               持仓量（期货专用）
        basis_spread                期现差（股指期货专用）
        settlement                  结算价（期货日线专用）
        prev_settlement             结算价（期货日线专用）
        =========================   ===================================================

        :param datetime.datetime dt: 时间
        :param bool skip_suspended: 是否跳过停牌日
        :param bool include_now: 是否包含当天最新数据
        :param str adjust_type: 复权类型，'pre', 'none', 'post'
        :param datetime.datetime adjust_orig: 复权起点；

        :return: `numpy.ndarray`

        """
        if not skip_suspended:
            raise NotImplementedError
        if frequency == '1d':
            return self.history_bars_days(instrument, bar_count, fields, dt, skip_suspended,
                                          include_now, adjust_type, adjust_orig)
        elif frequency == '1m':
            return self.history_bars_minutes(instrument, bar_count, fields, dt, skip_suspended,
                                             include_now, adjust_type, adjust_orig)

    def history_bars_minutes(self, instrument, bar_count, fields, dt, skip_suspended=True,
                             include_now=False, adjust_type='pre', adjust_orig=None):
        datetime_dt = int(dt.strftime("%Y%m%d%H%M%S"))

        if self._cache['history_minute_kline'] is None or instrument.order_book_id not in self._cache[
            'history_minute_kline'].keys():
            ret_code, bar_data = self._get_history_minute_cache(instrument)
            datetime_rows = self._cache['history_minute_kline'][instrument.order_book_id]
            if skip_suspended:
                bar_data = datetime_rows[datetime_rows['datetime'] <= datetime_dt].sort_values(['datetime'])[
                           -bar_count:]
        else:  # 不为空的时候，在历史缓存里寻找对应范围的数据就可以了
            datetime_rows = self._cache['history_minute_kline'][instrument.order_book_id]
            if skip_suspended:
                ret_code = 0
                bar_data = datetime_rows[datetime_rows['datetime'] <= datetime_dt].sort_values(['datetime'])[
                           -bar_count:]

        if ret_code == RET_ERROR or bar_data is None:
            raise NotImplementedError
        else:
            if isinstance(fields, str):
                return bar_data if fields is None else bar_data[fields].as_matrix()
            else:
                raise NotImplementedError

    def history_bars_days(self, instrument, bar_count, fields, dt, skip_suspended=True,
                          include_now=False, adjust_type='pre', adjust_orig=None):
        datetime_dt = int(dt.strftime("%Y%m%d%H%M%S"))

        if self._cache['history_kline'] is None or instrument.order_book_id not in self._cache['history_kline'].keys():
            ret_code, bar_data = self._get_history_cache(instrument)
            datetime_rows = self._cache['history_kline'][instrument.order_book_id]
            if skip_suspended:
                bar_data = datetime_rows[datetime_rows['datetime'] <= datetime_dt].sort_values(['datetime'])[
                           -bar_count:]
        else:  # 不为空的时候，在历史缓存里寻找对应范围的数据就可以了
            datetime_rows = self._cache['history_kline'][instrument.order_book_id]
            if skip_suspended:
                ret_code = 0
                bar_data = datetime_rows[datetime_rows['datetime'] <= datetime_dt].sort_values(['datetime'])[
                           -bar_count:]

        if ret_code == RET_ERROR or bar_data is None:
            raise NotImplementedError
        else:
            if isinstance(fields, str):
                return bar_data if fields is None else bar_data[fields].as_matrix()
            else:
                raise NotImplementedError

    def get_trading_calendar(self):
        """
        获取交易日历 ---看支持的交易日级别
        :return:
        """
        if self._cache["trading_days"] is None:
            ret_code, calendar_list = self._get_calendar_cache()
        else:
            ret_code, calendar_list = 0, self._cache["trading_days"]

        if ret_code == RET_ERROR or calendar_list is None:
            raise NotImplementedError
        return calendar_list

    def _get_calendar_cache(self):
        base = self._env.config.base
        for i in range(3):
            ret_code, calendar_list = self._quote_context.get_trading_days(market="HK",
                                                                           start_date=base.start_date.strftime(
                                                                               "%Y-%m-%d"),
                                                                           end_date=base.end_date.strftime(
                                                                               "%Y-%m-%d"))
            if ret_code != RET_ERROR and len(calendar_list) == 0:
                break
            else:
                time.sleep(0.1)

        if ret_code == RET_ERROR or len(calendar_list) == 0:
            print("get trading days error")

        calendar = pd.Index(pd.Timestamp(str(d)) for d in calendar_list)
        self._cache["trading_days"] = calendar[::-1]
        return ret_code, self._cache["trading_days"]

    def current_snapshot(self, instrument, frequency, dt):
        """
        获得当前市场快照数据。只能在日内交易阶段调用，获取当日调用时点的市场快照数据。  ---控制频率和数量 5s 200支(日K不用实现)
        市场快照数据记录了每日从开盘到当前的数据信息，可以理解为一个动态的day bar数据。
        在目前分钟回测中，快照数据为当日所有分钟线累积而成，一般情况下，最后一个分钟线获取到的快照数据应当与当日的日线行情保持一致。
        需要注意，在实盘模拟中，该函数返回的是调用当时的市场快照情况，所以在同一个handle_bar中不同时点调用可能返回的数据不同。
        如果当日截止到调用时候对应股票没有任何成交，那么snapshot中的close, high, low, last几个价格水平都将以0表示。

        :param instrument: 合约对象
        :type instrument: :class:`~Instrument`

        :param str frequency: 周期频率，`1d` 表示日周期, `1m` 表示分钟周期
        :param datetime.datetime dt: 时间

        :return: :class:`~Snapshot`
        """
        raise NotImplementedError

    def available_data_range(self, frequency):
        """
        此数据源能提供数据的时间范围 ---2000-2952  rqalpha是基于历史数据得到的，这个函数还用来在run里调整配置里的原始时间
        调整时间是用这里返回的end 和配置中做比较取得较小的---问题在于run是回测运行一次，实盘也有这个函数，返回max

       :param str frequency: 周期频率，`1d` 表示日周期, `1m` 表示分钟周期

        :return: (earliest, latest)
        """
        s = date(2000, 1, 1)
        # e = date.fromtimestamp(30999999999)
        e = date.today()
        return s, e

    def is_suspended(self, order_book_id, dates):
        #  用市场快照 判断一只股票是否停牌
        if IsRuntype_Backtest() is True:  # 回测
            return [(False) for d in dates]
        elif IsRuntype_RealTrade() is True or IsRuntype_RealtimeStrategy() is True:  # 实盘
            result = []
            for i in dates:
                if i.date() != date.today():
                    result.append(False)
                else:
                    if self._cache["market_snapshot"] is None or order_book_id not in self._cache[
                        "market_snapshot"].keys():
                        ret_code, ret_data = self._get_snapshot_cache(order_book_id)
                    else:
                        ret_code, ret_data = 0, self._cache["market_snapshot"][order_book_id]

                    if ret_data is not None:
                        if str(ret_data['suspension'])[5:10] == 'False':
                            result.append(False)
                        elif str(ret_data['suspension'])[5:10] == 'True':
                            result.append(True)
                    else:
                        result.append(True)
        return result

    def _get_snapshot_cache(self, order_book_id):
        self._cache["market_snapshot"] = {}

        for i in range(3):
            ret_code, ret_data = self._quote_context.get_market_snapshot([order_book_id])
            if ret_code != RET_ERROR and ret_data.empty:
                break
            else:
                time.sleep(5)
        if ret_code == RET_ERROR or ret_data.empty:
            print("get market snapshot error")

        self._cache["market_snapshot"][order_book_id] = ret_data

        self._cache["market_snapshot"][order_book_id] = self._cache["market_snapshot"][order_book_id].append(ret_data)
        return ret_code, self._cache["market_snapshot"][order_book_id]

    def _clear_cache(self, dt):
        if dt == date.today():
            self._cache.remove_all()

    def on_before_trading(self):
        self._today = Environment.get_instance().trading_dt.date()
        self._clear_cache(self._today)

    def _register_event(self):
        event_bus = Environment.get_instance().event_bus
        event_bus.add_listener(EVENT.PRE_BEFORE_TRADING, self.on_before_trading)

    def get_trading_minutes_for(self, order_book_id, trading_dt):
        """
        获取证券某天的交易时段，用于期货回测---不实现
        :param order_book_id:
        :param trading_dt:
        :return:
        """
        raise NotImplementedError

    def get_yield_curve(self, start_date, end_date, tenor=None):
        """
        获取国债利率---不实现

        :param pandas.Timestamp str start_date: 开始日期
        :param pandas.Timestamp end_date: 结束日期
        :param str tenor: 利率期限

        :return: pandas.DataFrame, [start_date, end_date]
        """
        return None

    def get_dividend(self, order_book_id):
        """
        获取股票/基金分红信息---不实现

        :param str order_book_id: 合约名
        :return:
        """
        return None

    def get_split(self, order_book_id):
        """
        获取拆股信息---不实现

        :param str order_book_id: 合约名

        :return: `pandas.DataFrame`
        """

        return None

    def get_settle_price(self, instrument, date):
        """
        获取期货品种在 date 的结算价---期货日线专用---不实现
        :param instrument: 合约对象
        :type instrument: :class:`~Instrument`

        :param datetime.date date: 结算日期

        :return: `str`
        """
        raise NotImplementedError

    def get_margin_info(self, instrument):
        """
        获取合约的保证金数据---margin_rate 是期货合约最低保证金率---不实现

        :param instrument: 合约对象
        :return: dict
        """
        raise NotImplementedError

    def get_commission_info(self, instrument):
        """
        获取合约的手续费信息---期货的类型---万分之五(针对期货的，故不实现)
        :param instrument:
        :return:
        """
        raise NotImplementedError

    def get_merge_ticks(self, order_book_id_list, trading_date, last_dt=None):
        """
        获取合并的 ticks---不支持逐笔---不实现

        :param list order_book_id_list: 合约名列表
        :param datetime.date trading_date: 交易日
        :param datetime.datetime last_dt: 仅返回 last_dt 之后的时间

        :return: Tick
        """
        raise NotImplementedError


class DataCache(CurKlineHandlerBase):
    def __init__(self):
        super(CurKlineHandlerBase, self).__init__()
        self._cache = {}
        self._cache["basicinfo_hk"] = None
        self._cache["basicinfo_us"] = None
        self._cache["history_kline"] = None
        self._cache["trading_days"] = None
        self._cache["market_snapshot"] = None
        self._cache['cur_kline'] = {}
        self._cache['history_minute_kline'] = None
        self._cache['cur_minute_kline'] = {}

    def remove_all(self):
        """删除全部"""
        for key in self._cache:
            self._cache[key] = None

    def on_recv_rsp(self, rsp_str):
        ret_code, ret_data = super(DataCache, self).on_recv_rsp(rsp_str)
        if ret_code == RET_ERROR or isinstance(ret_data, str):
            six.print_(_(u"push kline data error:{bar_data}").format(ret_data=ret_data))
        else:
            if ret_data.empty:
                self._cache['cur_kline'] = {}
                self._cache['cur_minute_kline'] = {}
            else:
                bar_data = ret_data.iloc[-1:].copy()
                del bar_data['code'], bar_data['k_type']  # 删除推送数据多出来的字段
                for i in range(len(bar_data['time_key'])):  # 时间转换
                    bar_data.loc[i, 'time_key'] = int(
                        bar_data['time_key'][i].replace('-', '').replace(' ', '').replace(':', ''))

                bar_data.rename(columns={'time_key': 'datetime', 'turnover': 'total_turnover'},
                                inplace=True)  # 将字段名称改为一致的
                bar_data['volume'] = bar_data['volume'].astype('float64')  # 把成交量的数据类型转为float

                if ret_data['k_type'][0] == 'K_DAY':
                    self._cache['cur_kline'][ret_data['code'][0]] = bar_data
                    return ret_code, self._cache['cur_kline'][ret_data['code'][0]]
                elif ret_data['k_type'][0] == 'K_1M':
                    self._cache['cur_minute_kline'][ret_data['code'][0]] = bar_data
                    return ret_code, self._cache['cur_minute_kline'][ret_data['code'][0]]
                else:
                    print('unimplemented k_type')
                    raise NotImplementedError
