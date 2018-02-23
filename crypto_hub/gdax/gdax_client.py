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

    def account_values_in_base_currency(self, base_currency='BTC'):
        """
        Returns a series of account values in the base currency.

        :param base_currency:
        :return: pd.Series
        """
        quotes = self.socket_client.get_bids()

        if base_currency not in ('BTC', 'USD'):
            usd_values = self.account_values_in_base_currency(base_currency='USD')
            usd_cross = '-'.join([base_currency, 'USD'])
            cross_rate = quotes.loc[usd_cross]
            return usd_values / cross_rate

        accounts = self.auth_client.get_accounts()
        values = pd.Series(0.0, index=accounts.index)
        for currency, row in accounts.iterrows():
            amount = row.balance
            if currency == base_currency:
                values[base_currency] += amount
                continue
            product_id = '-'.join([currency, base_currency])
            other_id = '-'.join([base_currency, currency])
            if product_id in quotes.index:
                exchange_rate = quotes.loc[product_id]
                values[currency] += amount * exchange_rate
            if other_id in quotes.index:
                # Only BTC should trigger this.
                exchange_rate = quotes.loc[other_id]
                values[currency] += amount / exchange_rate
        return pd.Series(values)
