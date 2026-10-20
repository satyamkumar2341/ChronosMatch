
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
    def __init__(self, order_book=None):
        self.order_book = order_book or OrderBook()
        self.trades = []

    def submit_order(self, order: Order) -> list[Trade]:
        if order.side not in (Side.BUY, Side.SELL):
            raise ValueError("Invalid order side")

        executed_trades = []

        while order.quantity > 0:
            if order.side == Side.BUY:
                resting_order = self.order_book.best_ask()

                if resting_order is None:
                    break

                if order.price < resting_order.price:
                    break

            else:
                resting_order = self.order_book.best_bid()

                if resting_order is None:
                    break

                if order.price > resting_order.price:
                    break

            traded_quantity = min(
                order.quantity,
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

            order.quantity -= traded_quantity
            resting_order.quantity -= traded_quantity

            executed_trades.append(trade)
            self.trades.append(trade)

            if resting_order.quantity == 0:
                self._remove_filled_order(resting_order)

        if order.quantity > 0:
            self.order_book.add_order(order)

        return executed_trades

    def _remove_filled_order(self, order: Order) -> None:
        self.order_book.remove_filled_order(order)