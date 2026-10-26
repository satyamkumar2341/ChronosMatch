
import random

from src.order import Order, Side
from src.matching_engine import MatchingEngine
from src.fast_engine import CythonMatchingEngine


def trade_signature(trades):
    return [
        (
            trade.buy_order_id,
            trade.sell_order_id,
            trade.price,
            trade.quantity,
        )
        for trade in trades
    ]


def best_order_signature(order):
    if order is None:
        return None

    return (
        order.order_id,
        order.side,
        order.price,
        order.quantity,
    )


def book_snapshot(engine):
    return (
        best_order_signature(engine.order_book.best_bid()),
        best_order_signature(engine.order_book.best_ask()),
    )


def test_randomized_python_cython_matching_parity():
    rng = random.Random(20261026)

    python_engine = MatchingEngine()
    cython_engine = CythonMatchingEngine()

    for index in range(500):
        order_id = f"R{index:04d}"
        side = rng.choice([Side.BUY, Side.SELL])
        price = rng.randint(90, 110)
        quantity = rng.randint(1, 20)

        python_order = Order(
            order_id, side, price, quantity
        )
        cython_order = Order(
            order_id, side, price, quantity
        )

        python_trades = python_engine.submit_order(
            python_order
        )
        cython_trades = cython_engine.submit_order(
            cython_order
        )

        assert trade_signature(python_trades) == (
            trade_signature(cython_trades)
        ), f"Trade mismatch after order {order_id}"

        assert book_snapshot(python_engine) == (
            book_snapshot(cython_engine)
        ), f"Best order mismatch after order {order_id}"

        assert trade_signature(python_engine.trades) == (
            trade_signature(cython_engine.trades)
        ), f"Trade history mismatch after order {order_id}"
