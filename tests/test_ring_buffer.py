

import os
import tempfile
import unittest
import math

from src.ring_buffer import RingBuffer, MAX_QUANTITY


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

    def test_nan_price_rejected(self):
        with self.assertRaises(ValueError):
            self.buffer.write("ORD001", "BUY", math.nan, 5)

    def test_infinite_price_rejected(self):
        with self.assertRaises(ValueError):
            self.buffer.write("ORD001", "BUY", math.inf, 5)

    def test_negative_infinite_price_rejected(self):
        with self.assertRaises(ValueError):
            self.buffer.write("ORD001", "BUY", -math.inf, 5)

    def test_fractional_quantity_rejected(self):
        with self.assertRaises(ValueError):
            self.buffer.write("ORD001", "BUY", 100, 2.5)

    def test_boolean_quantity_rejected(self):
        with self.assertRaises(ValueError):
            self.buffer.write("ORD001", "BUY", 100, True)

    def test_quantity_over_uint32_rejected(self):
        with self.assertRaises(ValueError):
            self.buffer.write(
                "ORD001", "BUY", 100, MAX_QUANTITY + 1
            )

    def test_max_uint32_quantity_accepted(self):
        self.buffer.write("ORD001", "BUY", 100, MAX_QUANTITY)
        order = self.buffer.read()
        self.assertEqual(order["quantity"], MAX_QUANTITY)

    def test_order_id_must_be_string(self):
        with self.assertRaises(ValueError):
            self.buffer.write(123, "BUY", 100, 5)

    def test_order_id_utf8_limit(self):
        with self.assertRaises(ValueError):
            self.buffer.write("अ" * 11, "BUY", 100, 5)

    def test_invalid_batch_is_atomic(self):
        orders = [
            ("ORD001", "BUY", 100, 5),
            ("ORD002", "SELL", 101, 3),
            ("ORD003", "BUY", 102, 2.5),
        ]

        with self.assertRaises(ValueError):
            self.buffer.write_many(orders)

        self.assertEqual(self.buffer.read(), None)

    def test_write_many_respects_capacity(self):
        orders = [
            ("ORD001", "BUY", 100, 5),
            ("ORD002", "SELL", 101, 3),
            ("ORD003", "BUY", 102, 2),
        ]

        self.assertEqual(self.buffer.write_many(orders), 2)

        result = self.buffer.read_many()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["order_id"], "ORD001")
        self.assertEqual(result[1]["order_id"], "ORD002")


if __name__ == "__main__":
    unittest.main()
