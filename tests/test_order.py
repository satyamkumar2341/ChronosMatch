
import unittest

from src.order import Order, Side


class TestOrder(unittest.TestCase):

    def test_valid_order(self):
        order = Order("ORD001", Side.BUY, 100, 5)

        self.assertEqual(order.order_id, "ORD001")
        self.assertEqual(order.side, Side.BUY)
        self.assertEqual(order.price, 100)
        self.assertEqual(order.quantity, 5)

    def test_invalid_price(self):
        with self.assertRaises(ValueError):
            Order("ORD002", Side.BUY, 0, 5)

    def test_invalid_quantity(self):
        with self.assertRaises(ValueError):
            Order("ORD003", Side.SELL, 100, 0)

    def test_empty_order_id(self):
        with self.assertRaises(ValueError):
            Order("", Side.BUY, 100, 5)

    
    def test_negative_price(self):
        with self.assertRaises(ValueError):
            Order("ORD004", Side.BUY, -100, 5)

    def test_negative_quantity(self):
        with self.assertRaises(ValueError):
            Order("ORD005", Side.SELL, 100, -5)



if __name__ == "__main__":
    unittest.main()
