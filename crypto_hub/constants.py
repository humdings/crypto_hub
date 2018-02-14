
# Constants to keep the order book protocol consistent.

SATOSHI = 0.00000001
ORDER_ID = 'order_id'

BID = 'bid'
ASK = 'ask'
SIZE = 'size'
SIDE = 'side'
PRICE = 'price'

ORDER_SIDES = {
    BID: BID,
    ASK: ASK,
    'buy': BID,
    'sell': ASK
}
