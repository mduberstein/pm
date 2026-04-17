from backend.app.board_repository import BoardRepository


def test_get_active_board_creates_default_board(tmp_path) -> None:
    repository = BoardRepository(tmp_path / "repo-test.db")

    board = repository.get_active_board("user")

    assert isinstance(board["columns"], list)
    assert isinstance(board["cards"], dict)
    assert len(board["columns"]) == 5


def test_update_active_board_persists_state(tmp_path) -> None:
    repository = BoardRepository(tmp_path / "repo-test.db")

    updated = {
        "columns": [
            {
                "id": "col-backlog",
                "title": "Backlog",
                "cardIds": ["card-1"],
            }
        ],
        "cards": {
            "card-1": {
                "id": "card-1",
                "title": "Persisted title",
                "details": "Persisted details",
            }
        },
    }

    repository.update_active_board("user", updated)
    loaded = repository.get_active_board("user")

    assert loaded == updated
