from pathlib import Path
import os
import sqlite3

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "data" / "pm.db"

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS boards (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  name TEXT NOT NULL DEFAULT 'Main Board',
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
  board_state_json TEXT NOT NULL CHECK (json_valid(board_state_json)),
  schema_version INTEGER NOT NULL DEFAULT 1,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_boards_user_id ON boards(user_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_boards_user_active
  ON boards(user_id)
  WHERE is_active = 1;
"""


def get_db_path() -> Path:
    configured = os.getenv("DB_PATH")
    if configured:
        return Path(configured)
    return DEFAULT_DB_PATH


def connect(db_path: Path | None = None) -> sqlite3.Connection:
    target_path = db_path or get_db_path()
    connection = sqlite3.connect(target_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def ensure_database(db_path: Path | None = None) -> Path:
    target_path = db_path or get_db_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with connect(target_path) as connection:
        connection.executescript(SCHEMA_SQL)
    return target_path
