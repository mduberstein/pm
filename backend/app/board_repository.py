import json
from pathlib import Path

from backend.app.board_defaults import DEFAULT_BOARD_STATE
from backend.app.db import connect, ensure_database


class BoardRepository:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path

    def _target_path(self) -> Path:
        return ensure_database(self.db_path)

    def _ensure_user_id(self, conn, username: str) -> int:
        row = conn.execute(
            "SELECT id FROM users WHERE username = ?", (username,)
        ).fetchone()
        if row is not None:
            return int(row["id"])
        cursor = conn.execute(
            "INSERT INTO users (username) VALUES (?)", (username,)
        )
        return int(cursor.lastrowid)

    def _ensure_active_board_id(self, conn, user_id: int) -> int:
        row = conn.execute(
            "SELECT id FROM boards WHERE user_id = ? AND is_active = 1 LIMIT 1",
            (user_id,),
        ).fetchone()
        if row is not None:
            return int(row["id"])
        cursor = conn.execute(
            """
            INSERT INTO boards (user_id, name, is_active, board_state_json, schema_version)
            VALUES (?, 'Main Board', 1, ?, 1)
            """,
            (user_id, json.dumps(DEFAULT_BOARD_STATE)),
        )
        return int(cursor.lastrowid)

    def get_active_board(self, username: str) -> dict:
        return self.get_active_board_with_snapshot(username)[0]

    def get_active_board_with_snapshot(self, username: str) -> tuple[dict, str]:
        """Returns (board_dict, raw_json_snapshot) for optimistic locking."""
        target_path = self._target_path()
        with connect(target_path) as conn:
            user_id = self._ensure_user_id(conn, username)
            board_id = self._ensure_active_board_id(conn, user_id)
            row = conn.execute(
                "SELECT board_state_json FROM boards WHERE id = ?", (board_id,)
            ).fetchone()
        if row is None:
            raw = json.dumps(DEFAULT_BOARD_STATE)
            return json.loads(raw), raw
        return json.loads(row["board_state_json"]), row["board_state_json"]

    def update_active_board(self, username: str, board_state: dict) -> dict:
        target_path = self._target_path()
        with connect(target_path) as conn:
            user_id = self._ensure_user_id(conn, username)
            board_id = self._ensure_active_board_id(conn, user_id)
            conn.execute(
                """
                UPDATE boards
                SET board_state_json = ?,
                    schema_version = 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (json.dumps(board_state), board_id),
            )
        return board_state

    def update_active_board_if_unchanged(
        self, username: str, board_state: dict, snapshot_json: str
    ) -> dict | None:
        """Returns the saved board dict, or None if a concurrent update was detected."""
        new_json = json.dumps(board_state)
        target_path = self._target_path()
        rows_affected = 0
        with connect(target_path) as conn:
            user_id = self._ensure_user_id(conn, username)
            board_id = self._ensure_active_board_id(conn, user_id)
            cursor = conn.execute(
                """
                UPDATE boards
                SET board_state_json = ?,
                    schema_version = 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND board_state_json = ?
                """,
                (new_json, board_id, snapshot_json),
            )
            rows_affected = cursor.rowcount
        if rows_affected == 0:
            return None
        return board_state
