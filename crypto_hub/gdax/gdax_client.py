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


