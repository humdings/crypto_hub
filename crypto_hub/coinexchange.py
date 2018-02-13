import pandas as pd
import numpy as np
from crypto_hub.order_book import LimitOrderBook
from crypto_hub.constants import BID, ASK


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
        Joins the summary and markets api calls into a DatFrame
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

    def fetch_markets(self):
        result = pd.read_json(self._markets_url)
        markets = pd.DataFrame([i for i in result.result.values])
        int_cols = ['MarketID', 'BaseCurrencyID', 'MarketAssetID']
        markets.loc[:, int_cols] = markets.loc[:, int_cols].astype(np.int)
        markets.index = markets.pop('MarketID')
        return markets

    def fetch_summaries(self):
        result = pd.read_json(self._summary_url)
        frame = pd.DataFrame([i for i in result.result.values])  # .astype(np.float)
        frame.index = frame.pop('MarketID').astype(np.int)
        return frame.astype(np.float)

    def get_order_book(self, market_id=316):
        url = self._book_url.format(market_id)
        result = pd.read_json(url).result
        buys = pd.DataFrame([i for i in result['BuyOrders']])
        sells = pd.DataFrame([i for i in result['SellOrders']])
        quotes = buys.append(sells)
        order_times = quotes.OrderTime.apply(lambda dt: pd.Timestamp(dt, tz='utc'))
        quotes['OrderTime'] = order_times
        quotes.sort_values(by='OrderTime', inplace=True)
        quotes.index = range(quotes.shape[0])
        float_cols = ['Price', 'Quantity']
        quotes[float_cols] = quotes[float_cols].astype(np.float)

        return quotes

    def convert_book_frame_to_order_book(self, book_frame):
        side_map = {
            'buy': BID,
            'sell': ASK
        }
        book = LimitOrderBook()
        for idx, row in book_frame.iterrows():
            order = {
                'type': 'limit',
                'order_id': idx,
                'price': row.Price,
                'quantity': row.Quantity,
                'timestamp': row.OrderTime,
                'side': side_map[row.Type]
            }
            book.process_order(order)
        return book


