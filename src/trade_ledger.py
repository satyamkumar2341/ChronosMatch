
import math
import sqlite3


class TradeLedger:
    """Persistent SQLite ledger for executed trades."""

    def __init__(self, db_path="chronosmatch.db"):
        self.db_path = str(db_path)
        self._initialize()

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _initialize(self):
        with self._connect() as connection:
            connection.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    buy_order_id TEXT NOT NULL,
                    sell_order_id TEXT NOT NULL,
                    price REAL NOT NULL CHECK(price > 0),
                    quantity INTEGER NOT NULL CHECK(quantity > 0),
                    created_at TEXT NOT NULL DEFAULT
                        (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                )
            """)

    @staticmethod
    def _validate_trade(trade):
        buy_id = trade.buy_order_id
        sell_id = trade.sell_order_id
        price = trade.price
        quantity = trade.quantity

        if not isinstance(buy_id, str) or not buy_id.strip():
            raise ValueError("Invalid buy order ID")

        if not isinstance(sell_id, str) or not sell_id.strip():
            raise ValueError("Invalid sell order ID")

        if isinstance(price, bool) or not isinstance(price, (int, float)):
            raise ValueError("Price must be numeric")

        if not math.isfinite(price) or price <= 0:
            raise ValueError("Price must be finite and positive")

        if isinstance(quantity, bool) or not isinstance(quantity, int):
            raise ValueError("Quantity must be an integer")

        if quantity <= 0:
            raise ValueError("Quantity must be positive")

    def record_trade(self, trade):
        self.record_trades([trade])

    def record_trades(self, trades):
        rows = []

        # Validate the entire batch before database insertion.
        for trade in trades:
            self._validate_trade(trade)

            rows.append((
                trade.buy_order_id,
                trade.sell_order_id,
                trade.price,
                trade.quantity
            ))

        if not rows:
            return 0

        with self._connect() as connection:
            connection.executemany("""
                INSERT INTO trades (
                    buy_order_id,
                    sell_order_id,
                    price,
                    quantity
                )
                VALUES (?, ?, ?, ?)
            """, rows)

        return len(rows)

    def get_trades(
        self,
        limit=100,
        buy_order_id=None,
        sell_order_id=None
    ):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError("Limit must be a positive integer")

        if buy_order_id is not None:
            if not isinstance(buy_order_id, str) or not buy_order_id.strip():
                raise ValueError("Invalid buy order ID")

        if sell_order_id is not None:
            if not isinstance(sell_order_id, str) or not sell_order_id.strip():
                raise ValueError("Invalid sell order ID")

        query = """
            SELECT id, buy_order_id, sell_order_id,
                   price, quantity, created_at
            FROM trades
        """

        conditions = []
        parameters = []

        if buy_order_id is not None:
            conditions.append("buy_order_id = ?")
            parameters.append(buy_order_id)

        if sell_order_id is not None:
            conditions.append("sell_order_id = ?")
            parameters.append(sell_order_id)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY id DESC LIMIT ?"
        parameters.append(limit)

        with self._connect() as connection:
            cursor = connection.execute(query, parameters)

            columns = [column[0] for column in cursor.description]

            return [
                dict(zip(columns, row))
                for row in cursor.fetchall()
            ]

    def count_trades(self):
        with self._connect() as connection:
            return connection.execute(
                "SELECT COUNT(*) FROM trades"
            ).fetchone()[0]

