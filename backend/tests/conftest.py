import os
import sqlite3

import pytest

os.environ["DEMO_MODE"] = "1"  # тесты не ходят в API, даже если ключ есть в .env

from app import db  # noqa: E402 — после DEMO_MODE


@pytest.fixture
def conn():
    """Чистая БД в памяти со схемой и синтетическим сидом из seed/*.json."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(db.SCHEMA.read_text(encoding="utf-8"))
    db.seed(conn)
    yield conn
    conn.close()
