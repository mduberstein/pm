import sqlite3

from backend.app.db import ensure_database


def test_ensure_database_creates_db_and_tables(tmp_path) -> None:
    db_path = tmp_path / "pm-test.db"

    ensure_database(db_path)

    assert db_path.exists()

    connection = sqlite3.connect(db_path)
    try:
        table_rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"
        ).fetchall()
        table_names = {row[0] for row in table_rows}

        assert "users" in table_names
        assert "boards" in table_names
    finally:
        connection.close()
