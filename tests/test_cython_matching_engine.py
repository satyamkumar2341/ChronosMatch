
import pytest

from src.order import Order, Side
from src.fast_engine import CythonMatchingEngine


def test_buy_matches_sell_with_partial_fill():
    engine = CythonMatchingEngine()
    engine.submit_order(Order("S1", Side.SELL, 100, 10))

    trades = engine.submit_order(Order("B1", Side.BUY, 100, 4))

    assert len(trades) == 1
    assert trades[0].buy_order_id == "B1"
    assert trades[0].sell_order_id == "S1"
    assert trades[0].price == 100
    assert trades[0].quantity == 4
    assert engine.order_book.best_ask().quantity == 6


def test_non_crossing_orders_do_not_match():
    engine = CythonMatchingEngine()
    engine.submit_order(Order("S1", Side.SELL, 110, 5))

    trades = engine.submit_order(Order("B1", Side.BUY, 100, 5))

    assert trades == []
    assert engine.order_book.best_bid().price == 100
    assert engine.order_book.best_ask().price == 110


def test_price_priority():
    engine = CythonMatchingEngine()
    engine.submit_order(Order("S1", Side.SELL, 105, 5))
    engine.submit_order(Order("S2", Side.SELL, 100, 5))

    trades = engine.submit_order(Order("B1", Side.BUY, 110, 5))

    assert trades[0].sell_order_id == "S2"
    assert trades[0].price == 100


def test_fifo_at_same_price():
    engine = CythonMatchingEngine()
    engine.submit_order(Order("S1", Side.SELL, 100, 3))
    engine.submit_order(Order("S2", Side.SELL, 100, 3))

    trades = engine.submit_order(Order("B1", Side.BUY, 100, 4))

    assert len(trades) == 2
    assert trades[0].sell_order_id == "S1"
    assert trades[0].quantity == 3
    assert trades[1].sell_order_id == "S2"
    assert trades[1].quantity == 1


def test_fully_filled_order_is_removed():
    engine = CythonMatchingEngine()
    engine.submit_order(Order("S1", Side.SELL, 100, 5))

    engine.submit_order(Order("B1", Side.BUY, 100, 5))

    assert engine.order_book.best_ask() is None
    assert len(engine.trades) == 1
    assert engine.trades[0].quantity == 5


def test_remaining_buy_quantity_rests_in_book():
    engine = CythonMatchingEngine()
    engine.submit_order(Order("S1", Side.SELL, 100, 3))

    trades = engine.submit_order(Order("B1", Side.BUY, 100, 7))

    assert len(trades) == 1
    assert trades[0].quantity == 3
    assert engine.order_book.best_bid().quantity == 4
    assert engine.order_book.best_ask() is None


def test_buy_matches_multiple_price_levels():
    engine = CythonMatchingEngine()
    engine.submit_order(Order("S1", Side.SELL, 100, 2))
    engine.submit_order(Order("S2", Side.SELL, 105, 3))

    trades = engine.submit_order(Order("B1", Side.BUY, 110, 5))

    assert len(trades) == 2
    assert trades[0].sell_order_id == "S1"
    assert trades[0].price == 100
    assert trades[0].quantity == 2
    assert trades[1].sell_order_id == "S2"
    assert trades[1].price == 105
    assert trades[1].quantity == 3
    assert engine.order_book.best_ask() is None


def test_invalid_order_side_raises():
    engine = CythonMatchingEngine()
    order = Order("X1", Side.BUY, 100, 1)
    order.side = "INVALID"

    with pytest.raises(ValueError, match="Invalid order side"):
        engine.submit_order(order)
