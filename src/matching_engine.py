
from dataclasses import dataclass

from src.order import Order, Side
from src.order_book import OrderBook


@dataclass
class Trade:
    buy_order_id: str
    sell_order_id: str
    price: int
    quantity: int


class MatchingEngine:
    def __init__(self, order_book=None, trade_ledger=None):
        self.order_book = order_book if order_book is not None else OrderBook()
        self.trade_ledger = trade_ledger
        self.trades = []

    def submit_order(self, order: Order) -> list[Trade]:
        if order.side not in (Side.BUY, Side.SELL):
            raise ValueError("Invalid order side")

        # Phase 1: Calculate executions without mutating the book.
        executed_trades = []
        planned_fills = []
        remaining_quantity = order.quantity

        if order.side == Side.BUY:
            book_side = self.order_book.asks
            prices = sorted(book_side)
        else:
            book_side = self.order_book.bids
            prices = sorted(book_side, reverse=True)

        for price in prices:
            if remaining_quantity <= 0:
                break

            if order.side == Side.BUY and price > order.price:
                break

            if order.side == Side.SELL and price < order.price:
                break

            for resting_order in book_side[price]:
                if remaining_quantity <= 0:
                    break

                traded_quantity = min(
                    remaining_quantity,
                    resting_order.quantity,
                )

                trade = Trade(
                    buy_order_id=(
                        order.order_id
                        if order.side == Side.BUY
                        else resting_order.order_id
                    ),
                    sell_order_id=(
                        order.order_id
                        if order.side == Side.SELL
                        else resting_order.order_id
                    ),
                    price=resting_order.price,
                    quantity=traded_quantity,
                )

                executed_trades.append(trade)
                planned_fills.append((resting_order, traded_quantity))
                remaining_quantity -= traded_quantity

        # Phase 2: Persist before changing in-memory matching state.
        if executed_trades and self.trade_ledger is not None:
            self.trade_ledger.record_trades(executed_trades)

        # Phase 3: Apply the planned executions.
        for resting_order, traded_quantity in planned_fills:
            order.quantity -= traded_quantity
            resting_order.quantity -= traded_quantity

            if resting_order.quantity == 0:
                self._remove_filled_order(resting_order)

        self.trades.extend(executed_trades)

        if order.quantity > 0:
            self.order_book.add_order(order)

        return executed_trades

    def _remove_filled_order(self, order: Order) -> None:
        self.order_book.remove_filled_order(order)

