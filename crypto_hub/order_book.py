from six import iteritems
from collections import deque

import numpy as np
import pandas as pd

from crypto_hub.constants import SATOSHI, BID, ASK, SIZE, PRICE, ORDER_ID, SIDE


class LimitOrderBook(object):
    """
    Limit order book implementation for a single asset.

    Orders are stored in a dictionary with integer keys.
    The keys are the prices converted to an integer multiple of the minimum tick

    The matching algorithm runs in linear time

    Orders are mutable mappings with the following minimum structure.
        {
            'order_id': hashable identifier,
            'price': float, limit price (defaults to min/max prices),
            'size': float/int,
            'side': str, bid/ask flag,

            actual keys are defined in crypto_hub.constants
        }

    Warning:
        Order quantities are modified in place so pass copies if they're needed elsewhere.
    """

    def __init__(self, tick_size=SATOSHI, max_price=1e9):
        self.tick_size = tick_size
        self._book = {}
        self._orders_by_id = {}
        self._trade_nonce = 0
        self.max_level = self.price_to_level(max_price)
        self._ask_min = self.price_to_level(max_price)
        self._bid_max = self.price_to_level(tick_size)
        self.fills = []

    @property
    def book(self):
        frame = pd.DataFrame({
            level: {
                side: sum(order[SIZE] for order in quotes[side])
                for side in quotes
            }
            for level, quotes in iteritems(self._book)
        }).T
        frame[frame <= 0] = np.nan
        return frame

    @property
    def cumulative_book(self):
        sizes = self.book
        bids = sizes.bid.iloc[-1::-1].cumsum().iloc[-1::-1]
        asks = sizes.ask.cumsum()
        return pd.DataFrame({BID: bids, ASK: asks})

    def price_to_level(self, price):
        """
        :param price: float
            order limit price
        :return: int
            index for orders at that price
        """
        return int(price / self.tick_size)

    def level_to_price(self, level):
        """
        :param level: number
            order index (or approximation)
        :return: float
            market price for the level
        """
        return level * self.tick_size

    def best_bid(self):
        """
        :returns dict
            copy of the best bid in the book.
            None if no bid exists.
        """
        bids = self.side_at_level(self._bid_max, BID)
        if not bids:
            if self._bid_max < self.tick_size:
                return None
            self._bid_max -= 1
            return self.best_bid()
        return bids[0].copy()

    def best_ask(self):
        """
        :returns dict
            copy of the best ask in the book.
            None if no ask exists.
        """
        asks = self.side_at_level(self._ask_min, ASK)
        if not asks:
            if self._ask_min > self.max_level:
                return None
            self._ask_min += 1
            return self.best_ask()
        return asks[0].copy()

    def get_level(self, level):
        if level not in self._book:
            self._book[level] = {BID: deque(), ASK: deque()}
        return self._book[level]

    def side_at_level(self, level, side):
        books = self.get_level(level)
        return books[side]

    def relay_fill(self, size, remaining):
        """
        Override this to send fill updates out.

        :param size: fill size
        :param remaining: remaining order
        :return: None
        """
        self.fills.append((size, remaining.copy()))

    def cancel_order(self, order_id):
        order = self._orders_by_id.pop(order_id, None)
        if order is None:
            return
        level = self.price_to_level(order[PRICE])
        side = order[SIDE]
        order_list = self.side_at_level(level, side)
        order[SIZE] = 0
        try:
            order_list.remove(order)
        except ValueError:
            pass
        return order

    def process_order(self, order):
        """
        Forwards buy sell order to process buy/sell functions.
        See self.process_buy()

        This injects a bogus limit for orders with no price (market orders)

        :param order: dict
            order mapping
        :return: int
            trade nonce, incremented if a fill occured.
        """
        side = order[SIDE]
        if PRICE not in order:
            if side == BID:
                order[PRICE] = self.level_to_price(self.max_level)
            else:
                order[PRICE] = self.tick_size
        if side == BID:
            return self.process_buy(order)
        elif side == ASK:
            return self.process_sell(order)
        else:
            raise ValueError("Invalid trade side")

    def process_buy(self, order):
        """
        Order filling logic. (Buys)

        When a Buy order arrives outstanding sell orders
        that cross with the incoming order are searched for
        starting at self.ask_min and proceed upwards until:
            a) The incoming buy order is filled.
            b) A price point is reached that no longer crosses with the incoming
               order
        In case b), the remainder of the incoming order is added appended the book.

        Sell orders are handled analogously (self.bid_max and down).

        :param order: dict
            order mapping
        :return: int
            trade nonce, incremented if a fill occurred.
        """
        assert order[SIDE] == BID
        price = order[PRICE]
        level = self.price_to_level(price)

        if level >= self._ask_min:
            # Fill orders
            while level > self._ask_min:
                ask_min = self._ask_min
                if ask_min not in self._book:
                    # Skip this process if the level hasn't been visited.
                    # This speeds up search and avoids memory overhead.
                    self._ask_min += 1
                    continue
                quantity = order[SIZE]
                orders_to_fill = self.side_at_level(ask_min, ASK)
                if orders_to_fill:
                    book_entry = orders_to_fill[0]
                    if book_entry[SIZE] <= quantity:
                        # Clear a resting order
                        amount = book_entry[SIZE]
                        order[SIZE] -= amount
                        book_entry[SIZE] = 0
                        fill = orders_to_fill.popleft()
                        self.relay_fill(amount, fill)
                        self.relay_fill(amount, order)
                        continue
                    # Partially fill a resting order
                    order[SIZE] -= quantity
                    book_entry[SIZE] -= quantity
                    self.relay_fill(quantity, book_entry)
                    self.relay_fill(quantity, order)
                    self._trade_nonce += 1
                    return self._trade_nonce
                self._ask_min += 1
        # Insert unfilled order into book
        buy_orders = self.side_at_level(level, BID)
        buy_orders.append(order)
        order_id = order.get(ORDER_ID)
        if order_id is not None:
            self._orders_by_id[order_id] = order
        if self._bid_max < level:
            self._bid_max = level
        return self._trade_nonce

    def process_sell(self, order):
        assert order[SIDE] == ASK
        price = order[PRICE]
        level = self.price_to_level(price)
        if level <= self._bid_max:
            # Fill orders
            while level <= self._bid_max:
                bid_max = self._bid_max
                if bid_max not in self._book:
                    # Skip this process if the level hasn't been visited.
                    # This speeds up search and avoids memory overhead.
                    self._bid_max -= 1
                    continue
                quantity = order[SIZE]
                orders_to_fill = self.side_at_level(bid_max, BID)
                if orders_to_fill:
                    book_entry = orders_to_fill[0]
                    if book_entry[SIZE] <= quantity:
                        # Order clears the resting order
                        amount = book_entry[SIZE]
                        book_entry[SIZE] = 0
                        order[SIZE] -= amount
                        fill = orders_to_fill.popleft()
                        self.relay_fill(amount, fill)
                        self.relay_fill(amount, order)
                        continue
                    # Partially fill a resting order
                    order[SIZE] -= quantity
                    book_entry[SIZE] -= quantity
                    self.relay_fill(quantity, book_entry)
                    self.relay_fill(quantity, order)
                    self._trade_nonce += 1
                    return self._trade_nonce
                self._bid_max -= 1
        sell_orders = self.side_at_level(level, ASK)
        sell_orders.append(order)
        order_id = order.get(ORDER_ID)
        if order_id is not None:
            self._orders_by_id[order_id] = order
        if self._ask_min > level:
            self._ask_min = level
        return self._trade_nonce
