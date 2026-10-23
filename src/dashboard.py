
import os
import time
from collections import deque

from src.order import Order, Side
from src.matching_engine import MatchingEngine


REFRESH_SECONDS = 1
DEMO_ORDERS = 1000


def format_price(order):
    return str(order.price) if order else "-"


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def run_dashboard():
    engine = MatchingEngine()
    recent_latencies = deque(maxlen=500)
    total_orders = 0
    total_trades = 0
    started_at = time.perf_counter()
    next_order_id = 1

    # Seed the book with resting orders on both sides.
    engine.submit_order(Order(f"O{next_order_id}", Side.BUY, 99, 100))
    next_order_id += 1
    engine.submit_order(Order(f"O{next_order_id}", Side.SELL, 101, 100))
    next_order_id += 1

    try:
        while True:
            cycle_start = time.perf_counter()

            # Generate demo orders around the spread.
            for i in range(DEMO_ORDERS):
                if i % 2 == 0:
                    side = Side.BUY
                    price = 101
                else:
                    side = Side.SELL
                    price = 99

                order = Order(
                    order_id=f"O{next_order_id}",
                    side=side,
                    price=price,
                    quantity=1,
                )
                next_order_id += 1

                order_start = time.perf_counter()
                trades = engine.submit_order(order)
                latency_us = (time.perf_counter() - order_start) * 1_000_000

                recent_latencies.append(latency_us)
                total_orders += 1
                total_trades += len(trades)

            elapsed = time.perf_counter() - started_at
            throughput = total_orders / elapsed if elapsed else 0
            sorted_latencies = sorted(recent_latencies)

            avg_latency = (
                sum(recent_latencies) / len(recent_latencies)
                if recent_latencies else 0
            )
            p99_index = int(0.99 * (len(sorted_latencies) - 1))
            p99_latency = (
                sorted_latencies[p99_index] if sorted_latencies else 0
            )

            best_bid = engine.order_book.best_bid()
            best_ask = engine.order_book.best_ask()
            spread = (
                best_ask.price - best_bid.price
                if best_bid and best_ask else None
            )

            clear_screen()
            print("=" * 60)
            print("          CHRONOSMATCH - TRADING DASHBOARD")
            print("=" * 60)
            print(f"Best Bid:              {format_price(best_bid)}")
            print(f"Best Ask:              {format_price(best_ask)}")
            print(f"Spread:                {spread if spread is not None else '-'}")
            print("-" * 60)
            print(f"Orders Processed:      {total_orders:,}")
            print(f"Trades Executed:       {total_trades:,}")
            print(f"Throughput:            {throughput:,.0f} orders/sec")
            print(f"Average Latency:       {avg_latency:.2f} microseconds")
            print(f"P99 Latency:           {p99_latency:.2f} microseconds")
            print(f"Recent Samples:        {len(recent_latencies)}")
            print("-" * 60)
            print("Demo mode: synthetic orders; not connected to a live exchange.")
            print("Press Ctrl+C to exit.")

            cycle_time = time.perf_counter() - cycle_start
            time.sleep(max(0, REFRESH_SECONDS - cycle_time))

    except KeyboardInterrupt:
        print("\nDashboard stopped.")


if __name__ == "__main__":
    run_dashboard()
