

from collections import deque

from src.order import Order, Side


cdef class CythonOrderBook:
    cdef public dict bids
    cdef public dict asks
    cdef object _best_bid_price
    cdef object _best_ask_price

    def __cinit__(self):
        self.bids = {}
        self.asks = {}
        self._best_bid_price = None
        self._best_ask_price = None

    def add_order(self, order):
        cdef dict book_side

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

    def remove_filled_order(self, order):
        cdef dict book_side
        cdef object queue

        if order.side == Side.BUY:
            book_side = self.bids
        elif order.side == Side.SELL:
            book_side = self.asks
        else:
            raise ValueError("Invalid order side")

        queue = book_side.get(order.price)

        if not queue or queue[0] is not order:
            raise ValueError(
                "Order is not at the front of its price queue"
            )

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


cdef class CythonTrade:
    cdef public object buy_order_id
    cdef public object sell_order_id
    cdef public int price
    cdef public int quantity

    def __init__(
        self, buy_order_id, sell_order_id, price, quantity
    ):
        self.buy_order_id = buy_order_id
        self.sell_order_id = sell_order_id
        self.price = price
        self.quantity = quantity

    def __repr__(self):
        return (
            f"CythonTrade(buy_order_id={self.buy_order_id!r}, "
            f"sell_order_id={self.sell_order_id!r}, "
            f"price={self.price}, quantity={self.quantity})"
        )


cdef class CythonMatchingEngine:
    cdef public object order_book
    cdef public list trades

    def __init__(self, order_book=None):
        self.order_book = (
            order_book if order_book is not None
            else CythonOrderBook()
        )
        self.trades = []

    def submit_order(self, order):
        cdef list executed_trades = []
        cdef object resting_order
        cdef int traded_quantity

        if order.side not in (Side.BUY, Side.SELL):
            raise ValueError("Invalid order side")

        while order.quantity > 0:
            if order.side == Side.BUY:
                resting_order = self.order_book.best_ask()

                if (
                    resting_order is None
                    or order.price < resting_order.price
                ):
                    break
            else:
                resting_order = self.order_book.best_bid()

                if (
                    resting_order is None
                    or order.price > resting_order.price
                ):
                    break

            traded_quantity = min(
                order.quantity, resting_order.quantity
            )

            if order.side == Side.BUY:
                trade = CythonTrade(
                    order.order_id,
                    resting_order.order_id,
                    resting_order.price,
                    traded_quantity,
                )
            else:
                trade = CythonTrade(
                    resting_order.order_id,
                    order.order_id,
                    resting_order.price,
                    traded_quantity,
                )

            order.quantity -= traded_quantity
            resting_order.quantity -= traded_quantity

            executed_trades.append(trade)
            self.trades.append(trade)

            if resting_order.quantity == 0:
                self.order_book.remove_filled_order(resting_order)

        if order.quantity > 0:
            self.order_book.add_order(order)

        return executed_trades
