import numpy as np
import pandas as pd
from gdax import WebsocketClient

from crypto_hub.constants import GDAX_PAIRS
from crypto_hub.gdax.gdax_book import GDAXOrderBook
from crypto_hub.gdax.public_client import PublicGDAXClient
import logbook

log = logbook.Logger(__name__)


class GDAXSocketClient(WebsocketClient):
    """
    Websocket Client that maintains and order book
    for each pair subscribed to.
    """

    def __init__(self, products=GDAX_PAIRS, mongo_collection=None, should_print=False, **kwargs):
        super(GDAXSocketClient, self).__init__(
            products=products,
            mongo_collection=mongo_collection,
            should_print=should_print,
            **kwargs
        )
        self._public_client = PublicGDAXClient()
        self.books = {
            product: GDAXOrderBook(
                product_id=product,
                public_client=self._public_client
            )
            for product in self.products
        }

    @property
    def public_client(self):
        return self._public_client

    def on_message(self, msg):
        try:
            self.books[msg['product_id']].on_message(msg)
        except KeyError:
            log.error("KeyError in msg: {}".format(msg))

        super(GDAXSocketClient, self).on_message(msg)

    def get_bid(self, product):
        try:
            return float(self.books[product].get_bid())
        except:
            return np.nan

    def get_ask(self, product):
        try:
            return float(self.books[product].get_ask())
        except:
            return np.nan

    def get_bids(self):
        return pd.Series({product: self.get_bid(product)
                          for product in self.products})

    def get_asks(self):
        return pd.Series({product: self.get_ask(product)
                          for product in self.products})

    def bid_ask_frame(self):
        return pd.DataFrame({'bid': self.get_bids(),
                             'ask': self.get_asks()})