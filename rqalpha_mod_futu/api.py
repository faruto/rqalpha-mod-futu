from decimal import Decimal

import six
import numpy as np

from rqalpha.api.api_base import instruments, cal_style
from rqalpha.const import SIDE, ORDER_TYPE
from rqalpha.environment import Environment
from rqalpha.model.instrument import Instrument
from rqalpha.model.order import Order, LimitOrder
# noinspection PyUnresolvedReferences
from rqalpha.utils.exception import patch_user_exc, RQInvalidArgument
from rqalpha.utils.i18n import gettext as _
from rqalpha.utils.logger import user_system_log
# noinspection PyUnresolvedReferences
from rqalpha.utils.scheduler import market_close, market_open
# noinspection PyUnresolvedReferences
from rqalpha.utils import scheduler


def order_shares(id_or_ins, amount, price=None, style=None):
    """
    落指定股数的买/卖单，最常见的落单方式之一。如有需要落单类型当做一个参量传入，如果忽略掉落单类型，那么默认是市价单（market order）。

    :param id_or_ins: 下单标的物
    :type id_or_ins: :class:`~Instrument` object | `str`

    :param int amount: 下单量, 正数代表买入，负数代表卖出。将会根据一手xx股来向下调整到一手的倍数，比如中国A股就是调整成100股的倍数。

    :param float price: 下单价格，默认为None，表示 :class:`~MarketOrder`, 此参数主要用于简化 `style` 参数。

    :param style: 下单类型, 默认是市价单。目前支持的订单类型有 :class:`~LimitOrder` 和 :class:`~MarketOrder`
    :type style: `OrderStyle` object

    :return: :class:`~Order` object

    :example:

    .. code-block:: python

        #购买Buy 2000 股的平安银行股票，并以市价单发送：
        order_shares('000001.XSHE', 2000)
        #卖出2000股的平安银行股票，并以市价单发送：
        order_shares('000001.XSHE', -2000)
        #购买1000股的平安银行股票，并以限价单发送，价格为￥10：
        order_shares('000001.XSHG', 1000, style=LimitOrder(10))
    """
    if amount == 0:
        # 如果下单量为0，则认为其并没有发单，则直接返回None
        return None
    style = cal_style(price, style)
    if isinstance(style, LimitOrder):
        if style.get_limit_price() <= 0:
            raise RQInvalidArgument(_(u"Limit order price should be positive"))
    order_book_id = assure_stock_order_book_id(id_or_ins)
    env = Environment.get_instance()

    price = env.get_last_price(order_book_id)
    if np.isnan(price):
        user_system_log.warn(
            _(u"Order Creation Failed: [{order_book_id}] No market data").format(order_book_id=order_book_id))
        return

    if amount > 0:
        side = SIDE.BUY
    else:
        amount = abs(amount)
        side = SIDE.SELL

    round_lot = int(env.get_instrument(order_book_id).round_lot)

    try:
        amount = int(Decimal(amount) / Decimal(round_lot)) * round_lot
    except ValueError:
        amount = 0

    r_order = Order.__from_create__(order_book_id, amount, side, style, None)

    if price == 0:
        user_system_log.warn(
            _(u"Order Creation Failed: [{order_book_id}] No market data").format(order_book_id=order_book_id))
        r_order.mark_rejected(
            _(u"Order Creation Failed: [{order_book_id}] No market data").format(order_book_id=order_book_id))
        return r_order

    if amount == 0:
        # 如果计算出来的下单量为0, 则不生成Order, 直接返回None
        # 因为很多策略会直接在handle_bar里面执行order_target_percent之类的函数，经常会出现下一个量为0的订单，如果这些订单都生成是没有意义的。
        r_order.mark_rejected(_(u"Order Creation Failed: 0 order quantity"))
        return r_order
    if r_order.type == ORDER_TYPE.MARKET:
        r_order.set_frozen_price(price)
    if env.can_submit_order(r_order):
        env.broker.submit_order(r_order)

    return r_order


def assure_stock_order_book_id(id_or_symbols):
    if isinstance(id_or_symbols, Instrument):
        return id_or_symbols.order_book_id
    elif isinstance(id_or_symbols, six.string_types):
        return assure_stock_order_book_id(instruments(id_or_symbols))
    else:
        raise RQInvalidArgument(_(u"unsupported order_book_id type"))
