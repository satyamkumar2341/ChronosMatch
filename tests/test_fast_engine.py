import pytest

from src.order import Order, Side
from src.order_book import OrderBook

try:
    from src.fast_engine import CythonOrderBook
except ImportError as exc:
    pytest.skip(
        f"Cython extension cannot be loaded: {exc}",
        allow_module_level=True,
    )


@pytest.mark.parametrize("book_class", [OrderBook, CythonOrderBook])
def test_empty_book(book_class):
    book = book_class()
    assert book.best_bid() is None
    assert book.best_ask() is None


@pytest.mark.parametrize("book_class", [OrderBook, CythonOrderBook])
def test_best_prices_and_fifo(book_class):
    book = book_class()

    buy1 = Order("B1", Side.BUY, 100, 5)
    buy2 = Order("B2", Side.BUY, 100, 3)
    buy3 = Order("B3", Side.BUY, 105, 2)
    sell1 = Order("S1", Side.SELL, 110, 4)
    sell2 = Order("S2", Side.SELL, 108, 1)

    for order in (buy1, buy2, buy3, sell1, sell2):
        book.add_order(order)

    assert book.best_bid() is buy3
    assert book.best_ask() is sell2

    book.remove_filled_order(buy3)
    assert book.best_bid() is buy1

    book.remove_filled_order(buy1)
    assert book.best_bid() is buy2

    book.remove_filled_order(sell2)
    assert book.best_ask() is sell1


@pytest.mark.parametrize("book_class", [OrderBook, CythonOrderBook])
def test_remove_non_front_order_raises(book_class):
    book = book_class()
    first = Order("B1", Side.BUY, 100, 5)
    second = Order("B2", Side.BUY, 100, 3)

    book.add_order(first)
    book.add_order(second)

    with pytest.raises(ValueError):
        book.remove_filled_order(second)


@pytest.mark.parametrize("book_class", [OrderBook, CythonOrderBook])
def test_remove_missing_order_raises(book_class):
    book = book_class()
    missing = Order("B1", Side.BUY, 100, 5)

    with pytest.raises(ValueError):
        book.remove_filled_order(missing)
