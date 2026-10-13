
from dataclasses import dataclass
from enum import Enum


class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Order:
    order_id: str
    side: Side
    price: int
    quantity: int

    def __post_init__(self):
        if not self.order_id:
            raise ValueError("Order ID cannot be empty")

        if self.price <= 0:
            raise ValueError("Price must be positive")

        if self.quantity <= 0:
            raise ValueError("Quantity must be positive")
