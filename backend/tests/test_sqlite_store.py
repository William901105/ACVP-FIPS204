from __future__ import annotations

import sqlite3

from app.storage.sqlite_store import get_db_path, init_db, reset_db_for_tests


def test_sqlite_db_init_creates_required_tables() -> None:
    reset_db_for_tests()
    init_db()

    conn = sqlite3.connect(str(get_db_path()))
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
    finally:
        conn.close()

    table_names = {row[0] for row in rows}
    assert {
        "imports",
        "demo_sessions",
        "acvp_sessions",
        "acvp_vector_sets",
        "state_events",
    }.issubset(table_names)

