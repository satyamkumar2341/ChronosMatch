import asyncio

import pytest

from src.matching_engine import MatchingEngine
from src.ring_buffer import RingBuffer
from src.trade_ledger import TradeLedger
from src.trading_pipeline import run_matching_firehose


def test_firehose_orders_reach_matching_engine_and_ledger(tmp_path):
    db_path = tmp_path / "pipeline.db"
    buffer_path = tmp_path / "pipeline.dat"

    ledger = TradeLedger(db_path)
    engine = MatchingEngine(trade_ledger=ledger)

    with RingBuffer(buffer_path, capacity=16) as buffer:
        result = asyncio.run(
            run_matching_firehose(
                buffer, 100, engine, order_prefix="TEST_"
            )
        )

    assert result["orders_processed"] == 100
    assert result["trades_executed"] > 0
    assert result["trades_executed"] == len(engine.trades)
    assert result["trades_executed"] == ledger.count_trades()

    stored_trades = ledger.get_trades(limit=1000)
    assert stored_trades
    assert all(
        trade["buy_order_id"].startswith("TEST_")
        and trade["sell_order_id"].startswith("TEST_")
        for trade in stored_trades
    )

    assert result["orders_per_second"] > 0
    assert result["average_latency_us"] > 0
    assert result["p99_latency_us"] > 0


def test_pipeline_handles_zero_orders(tmp_path):
    ledger = TradeLedger(tmp_path / "empty.db")
    engine = MatchingEngine(trade_ledger=ledger)

    with RingBuffer(tmp_path / "empty.dat", capacity=16) as buffer:
        result = asyncio.run(
            run_matching_firehose(buffer, 0, engine)
        )

    assert result["orders_processed"] == 0
    assert result["trades_executed"] == 0
    assert ledger.count_trades() == 0


def test_pipeline_rejects_negative_order_count(tmp_path):
    engine = MatchingEngine()

    with RingBuffer(tmp_path / "invalid.dat", capacity=16) as buffer:
        with pytest.raises(ValueError):
            asyncio.run(
                run_matching_firehose(buffer, -1, engine)
            )
