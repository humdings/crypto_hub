
import os
import numpy as np
import pandas as pd

from gdax.authenticated_client import AuthenticatedClient


class GDAXAuthClient(AuthenticatedClient):
    """
    Auth client that looks up the API credentials in the
    environment variables if they are not passed at initialization.
    """

    def __init__(self, key=None, b64secret=None, passphrase=None, api_url="https://api.gdax.com"):
        key = key or os.environ.get('GDAX_API_KEY')
        b64secret = b64secret or os.environ.get('GDAX_API_SECRET')
        passphrase = passphrase or os.environ.get('GDAX_PASSPHRASE')
        super(GDAXAuthClient, self).__init__(
            key, b64secret, passphrase,
            api_url=api_url,
        )

    def get_accounts(self):
        """
        Returns a DataFrame indexed by currency.
        """
        json_result = super(GDAXAuthClient, self).get_accounts()
        df = pd.DataFrame(json_result)
        df.index = df.pop('currency')
        float_cols = ['available', 'balance', 'hold']
        df[float_cols] = df[float_cols].astype(np.float)

        return df
