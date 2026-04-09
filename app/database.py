from __future__ import annotations

import mysql.connector
from mysql.connector import pooling

_pool: pooling.MySQLConnectionPool | None = None


def init_db(
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
) -> None:
    global _pool
    _pool = pooling.MySQLConnectionPool(
        pool_name="mywebapp",
        pool_size=5,
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
    )


def get_connection() -> pooling.PooledMySQLConnection:
    if _pool is None:
        raise RuntimeError("Database pool is not initialized")
    return _pool.get_connection()


def is_ready() -> bool:
    try:
        conn = get_connection()
        conn.close()
        return True
    except Exception:
        return False
