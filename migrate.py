import argparse

import mysql.connector


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="DB migration script")
    parser.add_argument("--db-host", default="127.0.0.1")
    parser.add_argument("--db-port", type=int, default=3306)
    parser.add_argument("--db-user", required=True)
    parser.add_argument("--db-password", required=True)
    parser.add_argument("--db-name", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    conn = mysql.connector.connect(
        host=args.db_host,
        port=args.db_port,
        user=args.db_user,
        password=args.db_password,
        database=args.db_name,
    )
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id         INT AUTO_INCREMENT PRIMARY KEY,
            name       VARCHAR(255) NOT NULL,
            quantity   INT NOT NULL DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        SELECT COUNT(1) FROM information_schema.statistics
        WHERE table_schema = %s
          AND table_name = 'items'
          AND index_name = 'idx_items_name'
    """, (args.db_name,))

    (exists,) = cursor.fetchone()
    if not exists:
        cursor.execute(
            "CREATE INDEX idx_items_name ON items(name)"
        )

    conn.commit()
    cursor.close()
    conn.close()
    print("Migration completed successfully.")


if __name__ == "__main__":
    main()
