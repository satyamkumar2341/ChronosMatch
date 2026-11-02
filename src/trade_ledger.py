
import sqlite3
from pathlib import Path


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
            connection.commit()

    def record_trade(self, trade):
        self.record_trades([trade])

    def record_trades(self, trades):
        rows = []

        for trade in trades:
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

    def get_trades(self, limit=100):
        if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
            raise ValueError("Limit must be a positive integer")

        with self._connect() as connection:
            cursor = connection.execute("""
                SELECT id, buy_order_id, sell_order_id,
                       price, quantity, created_at
                FROM trades
                ORDER BY id DESC
                LIMIT ?
            """, (limit,))

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
