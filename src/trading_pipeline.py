import asyncio
import math
from time import perf_counter, perf_counter_ns

from src.market_firehose import produce_orders
from src.matching_engine import MatchingEngine
from src.order import Order, Side


async def consume_and_match_orders(buffer, total_orders, engine):
    processed = 0
    latencies = []
    trades_before = len(engine.trades)

    while processed < total_orders:
        batch = buffer.read_many(max_items=256)

        if not batch:
            await asyncio.sleep(0)
            continue

        for record in batch:
            order = Order(
                order_id=record["order_id"],
                side=Side(record["side"]),
                price=record["price"],
                quantity=record["quantity"],
            )

            started = perf_counter_ns()
            engine.submit_order(order)
            latencies.append(perf_counter_ns() - started)

            processed += 1

    return {
        "orders_processed": processed,
        "latencies_ns": latencies,
        "trades": engine.trades[trades_before:],
    }


async def run_matching_firehose(buffer, total_orders, engine, order_prefix='ORD'):
    if isinstance(total_orders, bool) or not isinstance(total_orders, int):
        raise ValueError("total_orders must be a non-negative integer")

    if total_orders < 0:
        raise ValueError("total_orders must be non-negative")

    started = perf_counter()

    producer = asyncio.create_task(
        produce_orders(buffer, total_orders, order_prefix=order_prefix)
    )

    consumer = asyncio.create_task(
        consume_and_match_orders(buffer, total_orders, engine)
    )

    try:
        _, result = await asyncio.gather(producer, consumer)
    finally:
        for task in (producer, consumer):
            if not task.done():
                task.cancel()

        await asyncio.gather(
            producer, consumer, return_exceptions=True
        )

    elapsed = perf_counter() - started
    latencies = sorted(result["latencies_ns"])

    count = len(latencies)

    average_latency = (
        sum(latencies) / count / 1000 if count else 0
    )

    p99_latency = (
        latencies[math.ceil(0.99 * count) - 1] / 1000
        if count else 0
    )

    return {
        "orders_processed": result["orders_processed"],
        "trades_executed": len(result["trades"]),
        "trades": result["trades"],
        "elapsed_seconds": elapsed,
        "orders_per_second": (
            result["orders_processed"] / elapsed if elapsed else 0
        ),
        "average_latency_us": average_latency,
        "p99_latency_us": p99_latency,
    }

