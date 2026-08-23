import sqlite3


DB_NAME = "data/orders.db"


def init_db():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            product TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'new'
        )
    """)

    cursor.execute("PRAGMA table_info(orders)")
    columns = [column[1] for column in cursor.fetchall()]

    if "price" not in columns:
        cursor.execute(
            "ALTER TABLE orders ADD COLUMN price REAL NOT NULL DEFAULT 0"
        )

    if "total" not in columns:
        cursor.execute(
            "ALTER TABLE orders ADD COLUMN total REAL NOT NULL DEFAULT 0"
        )

    if "created_at" not in columns:
        cursor.execute(
            "ALTER TABLE orders ADD COLUMN created_at TIMESTAMP"
        )

    connection.commit()
    connection.close()
def create_order(
    user_id: int,
    product: str,
    price: float,
    quantity: int,
):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    total = price * quantity

    cursor.execute(
        """
        INSERT INTO orders (
            user_id,
            product,
            price,
            quantity,
            total,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'))
        """,
        (
            user_id,
            product,
            price,
            quantity,
            total,
        ),
    )

    order_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return order_id
    connection.commit()
    connection.close()
def get_user_orders(user_id: int):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, product, price, quantity, total, status, created_at
        FROM orders
        WHERE user_id = ?
        ORDER BY id DESC
        """,
        (user_id,),
    )

    orders = cursor.fetchall()

    connection.close()

    return orders
def get_all_orders():
    connection = sqlite3.connect(DB_NAME)

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, user_id, product, quantity, status
        FROM orders
        ORDER BY id DESC
        """
    )

    orders = cursor.fetchall()

    connection.close()

    return orders


def update_order_status(order_id: int, status: str):
    connection = sqlite3.connect(DB_NAME)

    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE orders
        SET status = ?
        WHERE id = ?
        """,
        (status, order_id),
    )

    connection.commit()
    connection.close()

def get_order(order_id: int):
    connection = sqlite3.connect(DB_NAME)

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT id, user_id, product, quantity, status
        FROM orders
        WHERE id = ?
        """,
        (order_id,),
    )

    order = cursor.fetchone()

    connection.close()

    return order
    
def cancel_order(order_id: int, user_id: int):
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        UPDATE orders
        SET status = 'cancelled'
        WHERE id = ?
          AND user_id = ?
          AND status = 'new'
        """,
        (order_id, user_id),
    )

    changed = cursor.rowcount

    connection.commit()
    connection.close()

    return changed > 0
def get_statistics():
    connection = sqlite3.connect(DB_NAME)
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT
            COUNT(*),
            SUM(CASE WHEN status = 'new' THEN 1 ELSE 0 END),
            SUM(CASE WHEN status = 'processing' THEN 1 ELSE 0 END),
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END),
            SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END),
            COALESCE(SUM(
                CASE
                    WHEN status = 'completed' THEN total
                    ELSE 0
                END
            ), 0)
        FROM orders
        """
    )

    result = cursor.fetchone()

    connection.close()

    return result
