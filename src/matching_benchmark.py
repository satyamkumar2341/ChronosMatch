"""Benchmark the Python matching engine."""

import argparse
import math
from time import perf_counter, perf_counter_ns

from src.matching_engine import MatchingEngine
from src.order import Order, Side


def run_benchmark(num_orders=10_000):
    if num_orders <= 0:
        raise ValueError("num_orders must be positive")

    engine = MatchingEngine()
    latencies = []
    start = perf_counter()

    for i in range(num_orders):
        engine.submit_order(Order(f"S{i}", Side.SELL, 100, 1))

        order_start = perf_counter_ns()
        trades = engine.submit_order(
            Order(f"B{i}", Side.BUY, 100, 1)
        )
        latencies.append(perf_counter_ns() - order_start)

        if len(trades) != 1 or trades[0].quantity != 1:
            raise RuntimeError(f"Order pair {i} did not match")

    elapsed = perf_counter() - start
    ordered = sorted(latencies)

    return {
        "orders_matched": num_orders,
        "trade_count": len(engine.trades),
        "elapsed_seconds": elapsed,
        "pairs_per_second": num_orders / elapsed,
        "average_latency_us": sum(latencies) / num_orders / 1000,
        "p99_latency_us": ordered[math.ceil(0.99 * num_orders) - 1] / 1000,
        "max_latency_us": max(latencies) / 1000,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--orders", type=int, default=10_000)
    args = parser.parse_args()

    try:
        result = run_benchmark(args.orders)
    except ValueError as error:
        parser.error(str(error))

    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
