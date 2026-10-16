
from collections import deque

from src.order import Order, Side


class OrderBook:
    def __init__(self):
        # Price -> FIFO queue of orders
        self.bids = {}
        self.asks = {}

    def add_order(self, order: Order):
        if order.side == Side.BUY:
            book_side = self.bids
        elif order.side == Side.SELL:
            book_side = self.asks
        else:
            raise ValueError("Invalid order side")

        if order.price not in book_side:
            book_side[order.price] = deque()

        book_side[order.price].append(order)

    def best_bid(self):
        if not self.bids:
            return None

        best_price = max(self.bids)
        return self.bids[best_price][0]

    def best_ask(self):
        if not self.asks:
            return None

        best_price = min(self.asks)
        return self.asks[best_price][0]
