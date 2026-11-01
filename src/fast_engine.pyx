from time import perf_counter_ns
from collections import deque

from src.order import Side


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
    cdef public bint track_latency
    cdef public list latency_records
    cdef public list trade_latency_records

    def __init__(self, order_book=None, track_latency=False):
        self.order_book = (
            order_book if order_book is not None
            else CythonOrderBook()
        )
        self.trades = []
        self.track_latency = track_latency
        self.latency_records = []
        self.trade_latency_records = []


    def submit_order(self, order):
        if not self.track_latency:
            return self._submit_order_impl(order)

        entry_ns = perf_counter_ns()

        try:
            return self._submit_order_impl(order)
        finally:
            exit_ns = perf_counter_ns()
            self.latency_records.append({
                "order_id": order.order_id,
                "entry_ns": entry_ns,
                "exit_ns": exit_ns,
                "duration_ns": exit_ns - entry_ns,
            })

    def _submit_order_impl(self, order):
        cdef list executed_trades = []
        cdef object order_book = self.order_book
        cdef object order_side = order.side
        cdef object order_price = order.price
        cdef object order_id = order.order_id
        cdef object order_quantity = order.quantity

        cdef object resting_order
        cdef object resting_price
        cdef object resting_quantity
        cdef object traded_quantity
        cdef object trade

        cdef object trade_entry_ns
        cdef object trade_exit_ns

        cdef object best_bid = order_book.best_bid
        cdef object best_ask = order_book.best_ask
        cdef object remove_filled = order_book.remove_filled_order
        cdef object add_order = order_book.add_order

        if order_side != Side.BUY and order_side != Side.SELL:
            raise ValueError("Invalid order side")

        while order_quantity > 0:
            if order_side == Side.BUY:
                resting_order = best_ask()

                if resting_order is None:
                    break

                resting_price = resting_order.price
                if order_price < resting_price:
                    break
            else:
                resting_order = best_bid()

                if resting_order is None:
                    break

                resting_price = resting_order.price
                if order_price > resting_price:
                    break

            if self.track_latency:
                trade_entry_ns = perf_counter_ns()

            resting_quantity = resting_order.quantity

            if order_quantity < resting_quantity:
                traded_quantity = order_quantity
            else:
                traded_quantity = resting_quantity

            if order_side == Side.BUY:
                trade = CythonTrade(
                    order_id,
                    resting_order.order_id,
                    resting_price,
                    traded_quantity,
                )
            else:
                trade = CythonTrade(
                    resting_order.order_id,
                    order_id,
                    resting_price,
                    traded_quantity,
                )

            order_quantity -= traded_quantity
            resting_quantity -= traded_quantity

            order.quantity = order_quantity
            resting_order.quantity = resting_quantity

            executed_trades.append(trade)
            self.trades.append(trade)

            if resting_quantity == 0:
                remove_filled(resting_order)

            if self.track_latency:
                trade_exit_ns = perf_counter_ns()
                self.trade_latency_records.append({
                    "buy_order_id": trade.buy_order_id,
                    "sell_order_id": trade.sell_order_id,
                    "entry_ns": trade_entry_ns,
                    "exit_ns": trade_exit_ns,
                    "duration_ns": trade_exit_ns - trade_entry_ns,
                })

        if order_quantity > 0:
            add_order(order)

        return executed_trades
    
        # Cache bound methods to avoid repeated attribute lookups.
        cdef object best_bid = order_book.best_bid
        cdef object best_ask = order_book.best_ask
        cdef object remove_filled = order_book.remove_filled_order
        cdef object add_order = order_book.add_order

        if order_side != Side.BUY and order_side != Side.SELL:
            raise ValueError("Invalid order side")

        while order_quantity > 0:
            if order_side == Side.BUY:
                resting_order = best_ask()

                if resting_order is None:
                    break

                resting_price = resting_order.price
                if order_price < resting_price:
                    break

            else:
                resting_order = best_bid()

                if resting_order is None:
                    break

                resting_price = resting_order.price
                if order_price > resting_price:
                    break

            resting_quantity = resting_order.quantity

            # Avoid calling Python's min() in the matching loop.
            if order_quantity < resting_quantity:
                traded_quantity = order_quantity
            else:
                traded_quantity = resting_quantity

            if order_side == Side.BUY:
                trade = CythonTrade(
                    order_id,
                    resting_order.order_id,
                    resting_price,
                    traded_quantity,
                )
            else:
                trade = CythonTrade(
                    resting_order.order_id,
                    order_id,
                    resting_price,
                    traded_quantity,
                )

            order_quantity -= traded_quantity
            resting_quantity -= traded_quantity

            # Preserve the original order mutation behaviour.
            order.quantity = order_quantity
            resting_order.quantity = resting_quantity

            executed_trades.append(trade)
            self.trades.append(trade)

            if resting_quantity == 0:
                remove_filled(resting_order)

        if order_quantity > 0:
            add_order(order)

        return executed_trades

