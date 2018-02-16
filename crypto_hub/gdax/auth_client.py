
import os

from gdax.authenticated_client import AuthenticatedClient


class GDAXAuthClient(AuthenticatedClient):
    """
    Auth client that looks up the API credentials in the
    environment variables if they are not passed at initialization.
    """

    def __init__(self, key=None, b64secret=None, passphrase=None,
                 api_url="https://api.gdax.com", timeout=30):
        key = key or os.environ.get('GDAX_API_KEY')
        b64secret = b64secret or os.environ.get('GDAX_API_SECRET')
        passphrase = passphrase or os.environ.get('GDAX_PASSPHRASE')
        super(AuthenticatedClient, self).__init__(
            key=key,
            b64secret=b64secret,
            passphrase=passphrase,
            api_url=api_url,
            timeout=timeout
        )

