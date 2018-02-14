import numpy as np
import pandas as pd
from gdax import PublicClient
from crypto_hub.constants import SATOSHI


class PublicGDAXClient(PublicClient):
    """
    Public client for requesting history
    """

    def get_product_historic_rates(self, product_id,
                                   granularity=86400,
                                   start=None, end=None):
        """
        Returns a pd.DataFrame of historical rates.

        :param product_id: ticker
        :param granularity: bar size in seconds
            valid sizes [60, 300, 900, 3600, 21600, 86400]
        :param start: start date
        :param end: end date
        :return:
        """
        response = super(PublicGDAXClient, self).get_product_historic_rates(
            product_id,
            start=start,
            end=end,
            granularity=granularity
        )
        return parse_gdax_history_to_frame(response)

    def get_quote(self, product_id):
        quote = self.public_client.get_product_ticker(product_id)
        return pd.Series(convert_quote(quote))


def parse_gdax_history_to_frame(raw_response):
    df = pd.DataFrame(columns=['low', 'high', 'open', 'close', 'volume'])
    for row in raw_response:
        dt = pd.Timestamp.fromtimestamp(row[0]).tz_localize('UTC')
        df.loc[dt] = row[1:]
    df[df < SATOSHI] = np.nan
    return df.sort_index()
