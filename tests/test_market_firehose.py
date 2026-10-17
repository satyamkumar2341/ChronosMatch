
import asyncio
import os
import tempfile
import unittest

from src.ring_buffer import RingBuffer
from src.market_firehose import run_firehose


class TestMarketFirehose(unittest.TestCase):
    def test_orders_are_generated_and_consumed(self):
        fd, path = tempfile.mkstemp()
        os.close(fd)

        try:
            with RingBuffer(path, capacity=16) as buffer:
                results = asyncio.run(run_firehose(buffer, 100))

            self.assertEqual(results["orders_processed"], 100)
            self.assertEqual(len(results["orders"]), 100)
            self.assertGreater(results["orders_per_second"], 0)

            first = results["orders"][0]
            self.assertEqual(first["order_id"], "ORD00000000")
            self.assertEqual(first["side"], "BUY")

            second = results["orders"][1]
            self.assertEqual(second["order_id"], "ORD00000001")
            self.assertEqual(second["side"], "SELL")
        finally:
            if os.path.exists(path):
                os.remove(path)


if __name__ == "__main__":
    unittest.main()
