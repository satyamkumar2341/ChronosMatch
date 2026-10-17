
import os
import tempfile
import unittest

from src.ring_buffer import RingBuffer


class TestRingBuffer(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp()
        os.close(fd)

        self.buffer = RingBuffer(self.path, capacity=2)

    def tearDown(self):
        self.buffer.close()
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_write_and_read(self):
        self.assertTrue(
            self.buffer.write("ORD001", "BUY", 100.5, 10)
        )

        order = self.buffer.read()

        self.assertEqual(order["order_id"], "ORD001")
        self.assertEqual(order["side"], "BUY")
        self.assertEqual(order["price"], 100.5)
        self.assertEqual(order["quantity"], 10)

    def test_empty_buffer(self):
        self.assertIsNone(self.buffer.read())

    def test_full_buffer(self):
        self.buffer.write("ORD001", "BUY", 100, 5)
        self.buffer.write("ORD002", "SELL", 101, 3)

        self.assertFalse(
            self.buffer.write("ORD003", "BUY", 99, 2)
        )

    def test_wrap_around(self):
        self.buffer.write("ORD001", "BUY", 100, 5)
        self.buffer.write("ORD002", "SELL", 101, 3)

        self.buffer.read()
        self.buffer.write("ORD003", "BUY", 102, 7)

        self.assertEqual(self.buffer.read()["order_id"], "ORD002")
        self.assertEqual(self.buffer.read()["order_id"], "ORD003")

    def test_invalid_side(self):
        with self.assertRaises(ValueError):
            self.buffer.write("ORD001", "HOLD", 100, 5)

    def test_invalid_quantity(self):
        with self.assertRaises(ValueError):
            self.buffer.write("ORD001", "BUY", 100, 0)


if __name__ == "__main__":
    unittest.main()
