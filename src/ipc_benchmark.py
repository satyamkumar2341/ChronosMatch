
import multiprocessing as mp
import os
import time

from src.ring_buffer import RingBuffer

TOTAL_ORDERS = 1_000_000
CAPACITY = 4096
BUFFER_PATH = "ipc_shared_buffer.dat"



def producer(path, capacity, lock, total_orders, start_event, done_event):
    with RingBuffer(path, capacity, create=False, lock=lock) as buffer:
        start_event.wait()
        batch_size = 256

        for start in range(0, total_orders, batch_size):
            batch = []

            for i in range(start, min(start + batch_size, total_orders)):
                batch.append((
                    f"ORD{i:08d}",
                    "BUY" if i % 2 == 0 else "SELL",
                    100.0 + (i % 100) * 0.5,
                    (i % 10) + 1,
                ))

            offset = 0
            while offset < len(batch):
                written = buffer.write_many(batch[offset:])
                offset += written

                if written == 0:
                    time.sleep(0)

    done_event.set()




def consumer(path, capacity, lock, total_orders, start_event, result_queue):
    received = 0

    with RingBuffer(path, capacity, create=False, lock=lock) as buffer:
        start_event.wait()

        while received < total_orders:
            orders = buffer.read_many(256)

            if not orders:
                time.sleep(0)
                continue

            received += len(orders)

    result_queue.put(received)


def main():
    if os.path.exists(BUFFER_PATH):
        os.remove(BUFFER_PATH)

    lock = mp.Lock()
    start_event = mp.Event()
    done_event = mp.Event()
    result_queue = mp.Queue()

    with RingBuffer(BUFFER_PATH, CAPACITY, create=True, lock=lock):
        producer_process = mp.Process(
            target=producer,
            args=(BUFFER_PATH, CAPACITY, lock, TOTAL_ORDERS,
                  start_event, done_event),
        )
        consumer_process = mp.Process(
            target=consumer,
            args=(BUFFER_PATH, CAPACITY, lock, TOTAL_ORDERS,
                  start_event, result_queue),
        )

        producer_process.start()
        consumer_process.start()

        start = time.perf_counter()
        start_event.set()

        producer_process.join()
        consumer_process.join()
        elapsed = time.perf_counter() - start

        if producer_process.exitcode != 0 or consumer_process.exitcode != 0:
            raise RuntimeError("Producer or consumer process failed")

        received = result_queue.get(timeout=5)

    os.remove(BUFFER_PATH)

    print(f"Orders sent:      {TOTAL_ORDERS}")
    print(f"Orders received:  {received}")
    print(f"Elapsed:          {elapsed:.3f} seconds")
    print(f"Throughput:       {received / elapsed:,.0f} orders/sec")
    print(f"Target achieved:  {received / elapsed >= 100_000}")


if __name__ == "__main__":
    mp.freeze_support()
    main()
