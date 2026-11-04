
import pytest

from src.matching_engine import MatchingEngine, Trade
from src.order import Order, Side
from src.trade_ledger import TradeLedger


def test_database_initialization(tmp_path):
    ledger = TradeLedger(tmp_path / "test.db")
    assert ledger.count_trades() == 0


def test_record_single_trade(tmp_path):
    ledger = TradeLedger(tmp_path / "test.db")

    trade = Trade("BUY1", "SELL1", 100, 10)
    ledger.record_trade(trade)

    assert ledger.count_trades() == 1

    saved = ledger.get_trades()[0]

    assert saved["buy_order_id"] == "BUY1"
    assert saved["sell_order_id"] == "SELL1"
    assert saved["price"] == 100
    assert saved["quantity"] == 10


def test_record_multiple_trades(tmp_path):
    ledger = TradeLedger(tmp_path / "test.db")

    trades = [
        Trade("B1", "S1", 100, 5),
        Trade("B2", "S2", 101, 10),
        Trade("B3", "S3", 102, 15),
    ]

    assert ledger.record_trades(trades) == 3
    assert ledger.count_trades() == 3


def test_empty_batch(tmp_path):
    ledger = TradeLedger(tmp_path / "test.db")

    assert ledger.record_trades([]) == 0
    assert ledger.count_trades() == 0


def test_invalid_limit(tmp_path):
    ledger = TradeLedger(tmp_path / "test.db")

    with pytest.raises(ValueError):
        ledger.get_trades(0)


def test_database_persistence(tmp_path):
    db_path = tmp_path / "persistent.db"

    ledger = TradeLedger(db_path)
    ledger.record_trade(Trade("B1", "S1", 100, 5))

    reopened = TradeLedger(db_path)

    assert reopened.count_trades() == 1

from src.order import Order, Side


def test_matching_engine_persists_executed_trade(tmp_path):
    ledger = TradeLedger(tmp_path / "integration.db")
    engine = MatchingEngine(trade_ledger=ledger)

    engine.submit_order(
        Order("SELL1", Side.SELL, 100, 10)
    )

    executed = engine.submit_order(
        Order("BUY1", Side.BUY, 100, 5)
    )

    assert len(executed) == 1
    assert ledger.count_trades() == 1

    saved = ledger.get_trades()[0]

    assert saved["buy_order_id"] == "BUY1"
    assert saved["sell_order_id"] == "SELL1"
    assert saved["price"] == 100
    assert saved["quantity"] == 5


def test_matching_engine_persists_multiple_executions(tmp_path):
    ledger = TradeLedger(tmp_path / "batch.db")
    engine = MatchingEngine(trade_ledger=ledger)

    engine.submit_order(Order("S1", Side.SELL, 100, 3))
    engine.submit_order(Order("S2", Side.SELL, 100, 4))

    executed = engine.submit_order(
        Order("B1", Side.BUY, 100, 7)
    )

    assert len(executed) == 2
    assert ledger.count_trades() == 2


def test_matching_engine_without_ledger_still_works():
    engine = MatchingEngine()

    engine.submit_order(Order("S1", Side.SELL, 100, 5))

    executed = engine.submit_order(
        Order("B1", Side.BUY, 100, 5)
    )

    assert len(executed) == 1
    assert len(engine.trades) == 1

def test_database_failure_preserves_order_book_state(tmp_path):
    ledger = TradeLedger(tmp_path / "failure.db")
    engine = MatchingEngine(trade_ledger=ledger)

    resting_sell = Order("SELL1", Side.SELL, 100, 10)
    engine.submit_order(resting_sell)

    incoming_buy = Order("BUY1", Side.BUY, 100, 5)

    def fail_persistence(trades):
        raise RuntimeError("Simulated database failure")

    ledger.record_trades = fail_persistence

    with pytest.raises(RuntimeError, match="Simulated database failure"):
        engine.submit_order(incoming_buy)

    # Incoming order must remain unchanged.
    assert incoming_buy.quantity == 5

    # Resting order must remain unchanged.
    assert resting_sell.quantity == 10

    # Order book must remain unchanged.
    assert engine.order_book.best_ask() is resting_sell

    # No trade should be added to memory or database.
    assert engine.trades == []
    assert ledger.count_trades() == 0

def test_rejects_invalid_price(tmp_path):
    ledger = TradeLedger(tmp_path / "invalid.db")

    for price in [0, -100, float("nan"), float("inf"), -float("inf")]:
        with pytest.raises(ValueError):
            ledger.record_trade(Trade("B1", "S1", price, 5))

    assert ledger.count_trades() == 0


def test_rejects_invalid_quantity(tmp_path):
    ledger = TradeLedger(tmp_path / "invalid_quantity.db")

    for quantity in [0, -1, 1.5, True]:
        with pytest.raises(ValueError):
            ledger.record_trade(Trade("B1", "S1", 100, quantity))

    assert ledger.count_trades() == 0


def test_rejects_empty_order_ids(tmp_path):
    ledger = TradeLedger(tmp_path / "invalid_ids.db")

    invalid_trades = [
        Trade("", "S1", 100, 5),
        Trade("B1", "", 100, 5),
        Trade("   ", "S1", 100, 5),
    ]

    for trade in invalid_trades:
        with pytest.raises(ValueError):
            ledger.record_trade(trade)

    assert ledger.count_trades() == 0


def test_invalid_batch_is_atomic(tmp_path):
    ledger = TradeLedger(tmp_path / "atomic.db")

    trades = [
        Trade("B1", "S1", 100, 5),
        Trade("B2", "S2", -10, 5),
        Trade("B3", "S3", 102, 5),
    ]

    with pytest.raises(ValueError):
        ledger.record_trades(trades)

    assert ledger.count_trades() == 0


def test_valid_batch_is_persisted(tmp_path):
    ledger = TradeLedger(tmp_path / "valid.db")

    trades = [
        Trade("B1", "S1", 100, 5),
        Trade("B2", "S2", 105, 10),
    ]

    assert ledger.record_trades(trades) == 2
    assert ledger.count_trades() == 2
