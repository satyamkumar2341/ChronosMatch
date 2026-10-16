
import unittest

from src.order import Order, Side
from src.order_book import OrderBook


class TestOrderBook(unittest.TestCase):

    def setUp(self):
        self.book = OrderBook()

    def test_empty_order_book(self):
        self.assertIsNone(self.book.best_bid())
        self.assertIsNone(self.book.best_ask())

    def test_add_buy_order(self):
        order = Order("B1", Side.BUY, 100, 5)

        self.book.add_order(order)

        self.assertIs(self.book.best_bid(), order)

    def test_add_sell_order(self):
        order = Order("S1", Side.SELL, 110, 5)

        self.book.add_order(order)

        self.assertIs(self.book.best_ask(), order)

    def test_highest_buy_price_has_priority(self):
        self.book.add_order(Order("B1", Side.BUY, 100, 5))
        self.book.add_order(Order("B2", Side.BUY, 105, 3))
        self.book.add_order(Order("B3", Side.BUY, 102, 4))

        self.assertEqual(self.book.best_bid().price, 105)

    def test_lowest_sell_price_has_priority(self):
        self.book.add_order(Order("S1", Side.SELL, 110, 5))
        self.book.add_order(Order("S2", Side.SELL, 103, 3))
        self.book.add_order(Order("S3", Side.SELL, 108, 4))

        self.assertEqual(self.book.best_ask().price, 103)

    def test_fifo_for_same_buy_price(self):
        first = Order("B1", Side.BUY, 100, 5)
        second = Order("B2", Side.BUY, 100, 3)

        self.book.add_order(first)
        self.book.add_order(second)

        self.assertIs(self.book.best_bid(), first)


if __name__ == "__main__":
    unittest.main()
