
import pytest

from src.trade_ledger import TradeLedger
from src.matching_engine import Trade


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
