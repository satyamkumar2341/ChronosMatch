
import asyncio
import time

from src.ring_buffer import RingBuffer


async def produce_orders(buffer, total_orders, batch_size=1000):
    """Generate mock orders and publish them to the ring buffer."""
    for i in range(total_orders):
        order_id = f"ORD{i:08d}"
        side = "BUY" if i % 2 == 0 else "SELL"
        price = 100.0 + (i % 100) * 0.5
        quantity = (i % 10) + 1

        while not buffer.write(order_id, side, price, quantity):
            await asyncio.sleep(0)

        if (i + 1) % batch_size == 0:
            await asyncio.sleep(0)


async def consume_orders(buffer, total_orders):
    """Read orders from the ring buffer."""
    orders = []

    while len(orders) < total_orders:
        order = buffer.read()

        if order is None:
            await asyncio.sleep(0)
            continue

        orders.append(order)

    return orders


async def run_firehose(buffer, total_orders):
    """Run producer and consumer concurrently."""
    start = time.perf_counter()

    producer = asyncio.create_task(
        produce_orders(buffer, total_orders)
    )
    consumer = asyncio.create_task(
        consume_orders(buffer, total_orders)
    )

    await producer
    orders = await consumer

    elapsed = time.perf_counter() - start
    rate = len(orders) / elapsed if elapsed > 0 else 0

    return {
        "orders_processed": len(orders),
        "elapsed_seconds": elapsed,
        "orders_per_second": rate,
        "orders": orders,
    }


async def main():
    total_orders = 100_000

    with RingBuffer("market_firehose.dat", capacity=1024) as buffer:
        results = await run_firehose(buffer, total_orders)

    print(f"Orders processed: {results['orders_processed']}")
    print(f"Time: {results['elapsed_seconds']:.3f} seconds")
    print(f"Throughput: {results['orders_per_second']:.0f} orders/sec")


if __name__ == "__main__":
    asyncio.run(main())
