import asyncio
import tempfile
import uuid
from pathlib import Path

from src.matching_engine import MatchingEngine
from src.ring_buffer import RingBuffer
from src.trade_ledger import TradeLedger
from src.trading_pipeline import run_matching_firehose


DEMO_ORDERS = 1000
DATABASE_PATH = "chronosmatch.db"


def display_dashboard(result, engine, ledger):
    best_bid = engine.order_book.best_bid()
    best_ask = engine.order_book.best_ask()

    spread = (
        best_ask.price - best_bid.price
        if best_bid and best_ask else None
    )

    recent_trades = ledger.get_trades(limit=10)

    print("\n" + "=" * 65)
    print("                 CHRONOSMATCH - TRADING DASHBOARD")
    print("=" * 65)

    print("\nMARKET OVERVIEW")
    print("-" * 65)
    print(f"Best Bid:                 {best_bid.price if best_bid else '-'}")
    print(f"Best Ask:                 {best_ask.price if best_ask else '-'}")
    print(f"Spread:                   {spread if spread is not None else '-'}")

    print("\nPIPELINE PERFORMANCE")
    print("-" * 65)
    print(f"Orders Processed:         {result['orders_processed']:,}")
    print(f"Trades Executed (batch):  {result['trades_executed']:,}")
    print(f"Total Stored Trades:      {ledger.count_trades():,}")
    print(f"Elapsed Time:             {result['elapsed_seconds']:.4f} sec")
    print(f"Throughput:               {result['orders_per_second']:,.0f} orders/sec")
    print(f"Average Matching Latency: {result['average_latency_us']:.2f} us")
    print(f"P99 Matching Latency:     {result['p99_latency_us']:.2f} us")

    print("\nRECENT EXECUTED TRADES")
    print("-" * 65)

    if not recent_trades:
        print("No trades recorded.")
    else:
        print(
            f"{'BUY ORDER':<15} {'SELL ORDER':<15} "
            f"{'PRICE':>10} {'QUANTITY':>10}"
        )
        for trade in recent_trades:
            print(
                f"{trade['buy_order_id']:<15} "
                f"{trade['sell_order_id']:<15} "
                f"{trade['price']:>10.2f} "
                f"{trade['quantity']:>10}"
            )

    print("\n" + "=" * 65)
    print("Simulation mode: synthetic market orders; no live exchange connection.")
    print(f"Trade database: {DATABASE_PATH}")
    print("=" * 65)


def run_dashboard():
    ledger = TradeLedger(DATABASE_PATH)
    engine = MatchingEngine(trade_ledger=ledger)

    print("Starting ChronosMatch pipeline...")
    order_prefix = f"R{uuid.uuid4().hex[:8].upper()}_"

    with tempfile.TemporaryDirectory() as temp_dir:
        buffer_path = Path(temp_dir) / "market.dat"

        with RingBuffer(buffer_path, capacity=1024) as buffer:
            result = asyncio.run(
                run_matching_firehose(
                    buffer, DEMO_ORDERS, engine,
                    order_prefix=order_prefix,
                )
            )

    display_dashboard(result, engine, ledger)


if __name__ == "__main__":
    run_dashboard()
