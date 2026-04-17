import copy
import json
from pathlib import Path

from backend.app.board_defaults import DEFAULT_BOARD_STATE
from backend.app.db import connect, ensure_database


class BoardRepository:
    def __init__(self, db_path: Path | None = None):
        self.db_path = db_path

    def _target_path(self) -> Path:
        return ensure_database(self.db_path)

    def _get_or_create_user_id(self, username: str) -> int:
        target_path = self._target_path()
        with connect(target_path) as connection:
            row = connection.execute(
                "SELECT id FROM users WHERE username = ?",
                (username,),
            ).fetchone()
            if row is not None:
                return int(row["id"])

            cursor = connection.execute(
                "INSERT INTO users (username) VALUES (?)",
                (username,),
            )
            return int(cursor.lastrowid)

    def _get_or_create_active_board_id(self, user_id: int) -> int:
        target_path = self._target_path()
        with connect(target_path) as connection:
            row = connection.execute(
                "SELECT id FROM boards WHERE user_id = ? AND is_active = 1 LIMIT 1",
                (user_id,),
            ).fetchone()
            if row is not None:
                return int(row["id"])

            cursor = connection.execute(
                """
                INSERT INTO boards (user_id, name, is_active, board_state_json, schema_version)
                VALUES (?, 'Main Board', 1, ?, 1)
                """,
                (user_id, json.dumps(DEFAULT_BOARD_STATE)),
            )
            return int(cursor.lastrowid)

    def get_active_board(self, username: str) -> dict:
        user_id = self._get_or_create_user_id(username)
        board_id = self._get_or_create_active_board_id(user_id)

        target_path = self._target_path()
        with connect(target_path) as connection:
            row = connection.execute(
                "SELECT board_state_json FROM boards WHERE id = ?",
                (board_id,),
            ).fetchone()

        if row is None:
            return copy.deepcopy(DEFAULT_BOARD_STATE)

        return json.loads(row["board_state_json"])

    def update_active_board(self, username: str, board_state: dict) -> dict:
        user_id = self._get_or_create_user_id(username)
        board_id = self._get_or_create_active_board_id(user_id)

        target_path = self._target_path()
        with connect(target_path) as connection:
            connection.execute(
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
