from six import iteritems
import numpy as np
import pandas as pd

from limitbook import LimitOrderBook


class OrderBook(LimitOrderBook):

    def get_size_frame(self):
        levels = {
            level: {
                side: sum(order['quantity'] for order in quotes[side])
                for side in quotes
            }
            for level, quotes in iteritems(self.book)
        }
        df = pd.DataFrame(levels).T
        df[df <= 0] = np.nan
        return df

    def get_cumulative_sizes(self, sizes=None):
        if sizes is None:
            sizes = self.get_size_frame()
        bids = sizes.bid.iloc[-1::-1].cumsum().iloc[-1::-1]
        asks = sizes.ask.cumsum()
        return pd.DataFrame({'bid': bids, 'ask': asks})