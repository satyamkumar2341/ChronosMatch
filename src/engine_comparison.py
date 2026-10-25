
"""Compare Python and Cython matching engines."""
import argparse
import gc
import math
import statistics
from time import perf_counter, perf_counter_ns

from src.fast_engine import CythonMatchingEngine
from src.matching_engine import MatchingEngine
from src.order import Order, Side


def run_benchmark(engine_class, num_pairs=10_000, repeats=3):
    if num_pairs <= 0 or repeats <= 0:
        raise ValueError("num_pairs and repeats must be positive")

    timings = []
    latencies = []
    final_trade_count = 0

    for _ in range(repeats):
        engine = engine_class()
        batch_latencies = []

        gc.collect()
        start = perf_counter()
        for i in range(num_pairs):
            engine.submit_order(Order(f"S{i}", Side.SELL, 100, 1))

            order_start = perf_counter_ns()
            trades = engine.submit_order(
                Order(f"B{i}", Side.BUY, 100, 1)
            )
            batch_latencies.append(perf_counter_ns() - order_start)

            if len(trades) != 1 or trades[0].quantity != 1:
                raise RuntimeError(f"Pair {i} failed to match")

        timings.append(perf_counter() - start)
        latencies = batch_latencies
        final_trade_count = len(engine.trades)

    elapsed = statistics.median(timings)
    ordered = sorted(latencies)

    return {
        "pairs": num_pairs,
        "repeats": repeats,
        "median_elapsed_seconds": elapsed,
        "pairs_per_second": num_pairs / elapsed,
        "average_latency_us": statistics.mean(latencies) / 1000,
        "p99_latency_us": ordered[math.ceil(0.99 * num_pairs) - 1] / 1000,
        "trade_count": final_trade_count,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--orders", type=int, default=10_000,
                        help="Number of matched buy/sell pairs per run")
    parser.add_argument("--repeats", type=int, default=3)
    args = parser.parse_args()

    try:
        python_result = run_benchmark(
            MatchingEngine, args.orders, args.repeats
        )
        cython_result = run_benchmark(
            CythonMatchingEngine, args.orders, args.repeats
        )
    except ValueError as error:
        parser.error(str(error))

    print("Python MatchingEngine:")
    for key, value in python_result.items():
        print(f"  {key}: {value}")

    print("\nCythonMatchingEngine:")
    for key, value in cython_result.items():
        print(f"  {key}: {value}")

    ratio = (
        cython_result["pairs_per_second"]
        / python_result["pairs_per_second"]
    )
    print(f"\nCython/Python throughput ratio: {ratio:.3f}x")
    if ratio > 1:
        print(f"Cython throughput improvement: {(ratio - 1) * 100:.1f}%")
    elif ratio < 1:
        print(f"Cython throughput difference: {(1 - ratio) * 100:.1f}% lower")
    else:
        print("Throughput is equal.")


if __name__ == "__main__":
    main()
