
import mmap
import os
import struct


# Header: read position, write position, number of stored orders
HEADER = struct.Struct("<III")

# Record: Order ID, side, price, quantity
RECORD = struct.Struct("<32s4s d I")


class RingBuffer:
    def __init__(self, path, capacity=1024):
        if capacity <= 0:
            raise ValueError("Capacity must be positive")

        self.path = path
        self.capacity = capacity
        self.record_size = RECORD.size
        self.header_size = HEADER.size
        self.size = self.header_size + capacity * self.record_size

        self.file = open(path, "w+b")
        self.file.truncate(self.size)

        self.memory = mmap.mmap(self.file.fileno(), self.size)
        self.memory[:self.header_size] = HEADER.pack(0, 0, 0)

    def write(self, order_id, side, price, quantity):
        read_pos, write_pos, count = HEADER.unpack(
            self.memory[:self.header_size]
        )

        if count == self.capacity:
            return False

        if side not in ("BUY", "SELL"):
            raise ValueError("Side must be BUY or SELL")

        if not order_id or len(order_id.encode("utf-8")) > 32:
            raise ValueError("Order ID must be 1-32 UTF-8 bytes")

        if price <= 0 or quantity <= 0:
            raise ValueError("Price and quantity must be positive")

        record = RECORD.pack(
            order_id.encode("utf-8"),
            side.encode("ascii"),
            float(price),
            int(quantity),
        )

        offset = self.header_size + write_pos * self.record_size
        self.memory[offset:offset + self.record_size] = record

        write_pos = (write_pos + 1) % self.capacity
        count += 1

        self.memory[:self.header_size] = HEADER.pack(
            read_pos, write_pos, count
        )
        return True

    def read(self):
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
        if os.path.exists(self.path):
            os.remove(self.path)
