
# Constants used in the order book protocol.

SATOSHI = 0.00000001
ORDER_ID = 'order_id'

BID = 'bid'
ASK = 'ask'
SIZE = 'size'
SIDE = 'side'
PRICE = 'price'
TIMESTAMP = 'dt'

ORDER_SIDES = {
    BID: BID,
    ASK: ASK,
    'buy': BID,
    'sell': ASK
}

GDAX_PAIRS = [
    'BTC-USD',
    'ETH-USD',
    'LTC-USD',
    'BCH-USD',
    'BCH-BTC',
    'LTC-BTC',
    'ETH-BTC',
]
