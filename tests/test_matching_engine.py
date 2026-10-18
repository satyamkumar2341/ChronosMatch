
from src.order import Order, Side
from src.matching_engine import MatchingEngine


def test_matching_buy_and_sell():
    engine = MatchingEngine()

    engine.submit_order(
        Order("S1", Side.SELL, 100, 10)
    )
    trades = engine.submit_order(
        Order("B1", Side.BUY, 100, 4)
    )

    assert len(trades) == 1
    assert trades[0].price == 100
    assert trades[0].quantity == 4
    assert engine.order_book.best_ask().quantity == 6


def test_non_crossing_orders_do_not_match():
    engine = MatchingEngine()

    engine.submit_order(
        Order("S1", Side.SELL, 110, 5)
    )
    trades = engine.submit_order(
        Order("B1", Side.BUY, 100, 5)
    )

    assert trades == []
    assert engine.order_book.best_bid().price == 100
    assert engine.order_book.best_ask().price == 110


def test_price_priority():
    engine = MatchingEngine()

    engine.submit_order(
        Order("S1", Side.SELL, 105, 5)
    )
    engine.submit_order(
        Order("S2", Side.SELL, 100, 5)
    )

    trades = engine.submit_order(
        Order("B1", Side.BUY, 110, 5)
    )

    assert trades[0].sell_order_id == "S2"
    assert trades[0].price == 100


def test_fifo_at_same_price():
    engine = MatchingEngine()

    engine.submit_order(
        Order("S1", Side.SELL, 100, 3)
    )
    engine.submit_order(
        Order("S2", Side.SELL, 100, 3)
    )

    trades = engine.submit_order(
        Order("B1", Side.BUY, 100, 4)
    )

    assert trades[0].sell_order_id == "S1"
    assert trades[0].quantity == 3
    assert trades[1].sell_order_id == "S2"
    assert trades[1].quantity == 1


def test_order_fully_filled():
    engine = MatchingEngine()

    engine.submit_order(
        Order("S1", Side.SELL, 100, 5)
    )
    engine.submit_order(
        Order("B1", Side.BUY, 100, 5)
    )

    assert engine.order_book.best_ask() is None
    assert len(engine.trades) == 1
    assert engine.trades[0].quantity == 5
