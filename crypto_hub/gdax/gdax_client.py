import pandas as pd

from crypto_hub.constants import GDAX_PAIRS
from crypto_hub.gdax.auth_client import GDAXAuthClient
from crypto_hub.gdax.socket_client import GDAXSocketClient


class GDAXClient(object):
    """
    Single interface to the GDAX clients.
    """

    def __init__(self, auth_client=None, socket_client=None, mongo_collection=None):
        if auth_client is None:
            auth_client = GDAXAuthClient()
        if socket_client is None:
            socket_client = GDAXSocketClient(
                products=GDAX_PAIRS,
                mongo_collection=mongo_collection
            )
        self.auth_client = auth_client
        self.socket_client = socket_client
        self.public_client = socket_client.public_client

    def account_values_in_base_currency(self, accounts=None, quotes=None, base_currency='BTC'):
        if accounts is None:
            accounts = self.auth_client.get_accounts()
        if quotes is None:
            quotes = self.socket_client.get_bids()
        values = pd.Series(0.0, index=accounts.index)
        for currency, row in accounts.iterrows():
            amount = row.balance
            if currency == base_currency:
                values[base_currency] += amount
                continue
            product_id = '-'.join([currency, base_currency])
            if product_id not in quotes.index:
                continue
            exchange_rate = quotes.loc[product_id]
            values[currency] = amount * exchange_rate
        return pd.Series(values)
