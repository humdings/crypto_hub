import pandas as pd
import numpy as np
from crypto_hub.order_book import LimitOrderBook
from crypto_hub.constants import (
    PRICE, SIDE, SIZE, TIMESTAMP,
    ORDER_ID, ORDER_SIDES
)


class CoinExchange(object):
    """
    Implements coinexchange.io API
    """

    _markets_url = 'https://www.coinexchange.io/api/v1/getmarkets'
    _summary_url = 'https://www.coinexchange.io/api/v1/getmarketsummaries'
    _book_url = 'https://www.coinexchange.io/api/v1/getorderbook?market_id={}'

    def __init__(self, refresh_minutes=10):
        self._last_refresh = pd.Timestamp('1970-01-01', tz='utc')
        self._refresh_delta = pd.Timedelta(minutes=refresh_minutes)
        self._data = None

    @property
    def markets(self):
        """
        Joins the summary and markets api calls into a DataFrame
        :return: DataFrame indexed by market id.
        """
        now = pd.Timestamp.utcnow()
        needs_refresh = (now - self._last_refresh) >= self._refresh_delta
        if needs_refresh or self._data is None:
            markets = self.fetch_markets()
            quotes = self.fetch_summaries()
            self._data = markets.join(quotes, how='outer')
            self._last_refresh = now
        return self._data

    def get_order_book(self, quote_currency='HODL', base_currency='BTC', market_id=None):
        if market_id is None:
            if quote_currency is None:
                raise ValueError('Must pass market_id or the quote/base currencies')
            market_id = self.lookup_market_id(quote_currency, base_currency)
        orders = self._fetch_book_orders(market_id)
        book = LimitOrderBook()
        for order in orders:
            book.process_order(order)
        return book

    def fetch_markets(self):
        result = pd.read_json(self._markets_url)
        markets = pd.DataFrame([i for i in result.result.values])
        int_cols = ['MarketID', 'BaseCurrencyID', 'MarketAssetID']
        markets.loc[:, int_cols] = markets.loc[:, int_cols].astype(np.int)
        markets.index = markets.pop('MarketID')
        return markets

    def fetch_summaries(self):
        result = pd.read_json(self._summary_url)
        frame = pd.DataFrame([i for i in result.result.values])
        frame.index = frame.pop('MarketID').astype(np.int)
        return frame.astype(np.float)

    def _fetch_book_orders(self, market_id):
        url = self._book_url.format(market_id)
        result = pd.read_json(url).result
        orders = result.loc['BuyOrders']
        orders.extend(result.loc['SellOrders'])
        for i, order in enumerate(orders):
            order[ORDER_ID] = i
            # Not actually sure if these are utc but meh for now
            order[TIMESTAMP] = pd.Timestamp(order.pop('OrderTime'), tz='utc')
            order[PRICE] = float(order.pop('Price'))
            order[SIZE] = float(order.pop('Quantity'))
            order[SIDE] = ORDER_SIDES[order.pop('Type')]
        return sorted(orders, key=lambda order: order[TIMESTAMP])

    def lookup_market_id(self, quote_currency, base_currency='BTC'):
        mask = self.markets['MarketAssetCode'] == quote_currency.upper()
        mask &= self.markets['BaseCurrencyCode'] == base_currency.upper()
        result = mask.index[mask]
        hits = len(result)
        if hits > 1:
            raise ValueError('Multiple pairs for {}/{}'.format(quote_currency, base_currency))
        elif hits < 1:
            return None
        return result[0]


