
import mmap
import multiprocessing
import os
import struct


HEADER = struct.Struct("<III")
RECORD = struct.Struct("<32s4sdI")


class RingBuffer:
    def __init__(self, path, capacity=1024, create=True, lock=None):
        if capacity <= 0:
            raise ValueError("Capacity must be positive")

        self.path = path
        self.capacity = capacity
        self.lock = lock if lock is not None else multiprocessing.Lock()
        self.record_size = RECORD.size
        self.header_size = HEADER.size
        self.size = self.header_size + capacity * self.record_size

        if create:
            self.file = open(path, "w+b")
            self.file.truncate(self.size)
        else:
            self.file = open(path, "r+b")
            if os.path.getsize(path) != self.size:
                self.file.close()
                raise ValueError("Existing buffer size does not match capacity")

        self.memory = mmap.mmap(self.file.fileno(), self.size)

        if create:
            self.memory[:self.header_size] = HEADER.pack(0, 0, 0)
            self.memory.flush()

    def write(self, order_id, side, price, quantity):
        if side not in ("BUY", "SELL"):
            raise ValueError("Side must be BUY or SELL")

        encoded_id = order_id.encode("utf-8")
        if not encoded_id or len(encoded_id) > 32:
            raise ValueError("Order ID must be 1-32 UTF-8 bytes")

        if price <= 0 or quantity <= 0:
            raise ValueError("Price and quantity must be positive")

        record = RECORD.pack(
            encoded_id, side.encode("ascii"), float(price), int(quantity)
        )

        with self.lock:
            read_pos, write_pos, count = HEADER.unpack(
                self.memory[:self.header_size]
            )

            if count == self.capacity:
                return False

            offset = self.header_size + write_pos * self.record_size
            self.memory[offset:offset + self.record_size] = record

            write_pos = (write_pos + 1) % self.capacity
            count += 1

            self.memory[:self.header_size] = HEADER.pack(
                read_pos, write_pos, count
            )
            return True
    
    def write_many(self, orders):
        records = []

        for order_id, side, price, quantity in orders:
            if side not in ("BUY", "SELL"):
                raise ValueError("Side must be BUY or SELL")

            encoded_id = order_id.encode("utf-8")
            if not encoded_id or len(encoded_id) > 32:
                raise ValueError("Order ID must be 1-32 UTF-8 bytes")

            if price <= 0 or quantity <= 0:
                raise ValueError("Price and quantity must be positive")

            records.append(
                RECORD.pack(
                    encoded_id,
                    side.encode("ascii"),
                    float(price),
                    int(quantity),
                )
            )

        written = 0

        with self.lock:
            read_pos, write_pos, count = HEADER.unpack(
                self.memory[:self.header_size]
            )

            available = self.capacity - count
            written = min(len(records), available)

            for record in records[:written]:
                offset = self.header_size + write_pos * self.record_size
                self.memory[offset:offset + self.record_size] = record
                write_pos = (write_pos + 1) % self.capacity

            count += written
            self.memory[:self.header_size] = HEADER.pack(
                read_pos, write_pos, count
            )

        return written

    def read_many(self, max_items=256):
        if max_items <= 0:
            raise ValueError("max_items must be positive")

        orders = []

        with self.lock:
            read_pos, write_pos, count = HEADER.unpack(
                self.memory[:self.header_size]
            )

            amount = min(max_items, count)

            for _ in range(amount):
                offset = self.header_size + read_pos * self.record_size
                record = self.memory[offset:offset + self.record_size]

                order_id, side, price, quantity = RECORD.unpack(record)

                orders.append({
                    "order_id": order_id.rstrip(b"\x00").decode("utf-8"),
                    "side": side.rstrip(b"\x00").decode("ascii"),
                    "price": price,
                    "quantity": quantity,
                })

                read_pos = (read_pos + 1) % self.capacity

            count -= amount
            self.memory[:self.header_size] = HEADER.pack(
                read_pos, write_pos, count
            )

        return orders


    def read(self):
        with self.lock:
            read_pos, write_pos, count = HEADER.unpack(
                self.memory[:self.header_size]
            )

            if count == 0:
                return None

            offset = self.header_size + read_pos * self.record_size
            record = self.memory[offset:offset + self.record_size]

            order_id, side, price, quantity = RECORD.unpack(record)

            read_pos = (read_pos + 1) % self.capacity
            count -= 1

            self.memory[:self.header_size] = HEADER.pack(
                read_pos, write_pos, count
            )

            return {
                "order_id": order_id.rstrip(b"\x00").decode("utf-8"),
                "side": side.rstrip(b"\x00").decode("ascii"),
                "price": price,
                "quantity": quantity,
            }

    def close(self):
        self.memory.close()
        self.file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

