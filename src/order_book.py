
from collections import deque

from src.order import Order, Side


class OrderBook:
    def __init__(self):
        # Price -> FIFO queue of orders
        self.bids = {}
        self.asks = {}

        # Cache the best available price on each side.
        self._best_bid_price = None
        self._best_ask_price = None

    def add_order(self, order: Order):
        if order.side == Side.BUY:
            book_side = self.bids

            if order.price not in book_side:
                book_side[order.price] = deque()

            book_side[order.price].append(order)

            if (
                self._best_bid_price is None
                or order.price > self._best_bid_price
            ):
                self._best_bid_price = order.price

        elif order.side == Side.SELL:
            book_side = self.asks

            if order.price not in book_side:
                book_side[order.price] = deque()

            book_side[order.price].append(order)

            if (
                self._best_ask_price is None
                or order.price < self._best_ask_price
            ):
                self._best_ask_price = order.price

        else:
            raise ValueError("Invalid order side")

    def best_bid(self):
        if self._best_bid_price is None:
            return None

        return self.bids[self._best_bid_price][0]

    def best_ask(self):
        if self._best_ask_price is None:
            return None

        return self.asks[self._best_ask_price][0]

    def remove_filled_order(self, order: Order):
        if order.side == Side.BUY:
            book_side = self.bids
        elif order.side == Side.SELL:
            book_side = self.asks
        else:
            raise ValueError("Invalid order side")

        queue = book_side.get(order.price)

        if not queue or queue[0] is not order:
            raise ValueError("Order is not at the front of its price queue")

        queue.popleft()

        if queue:
            return

        del book_side[order.price]

        if order.side == Side.BUY:
            if self._best_bid_price == order.price:
                self._best_bid_price = (
                    max(self.bids) if self.bids else None
                )
        else:
            if self._best_ask_price == order.price:
                self._best_ask_price = (
                    min(self.asks) if self.asks else None
                )