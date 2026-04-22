from backend.app.board_repository import BoardRepository


def test_get_active_board_creates_default_board(tmp_path) -> None:
    repository = BoardRepository(tmp_path / "repo-test.db")

    board = repository.get_active_board("user")

    assert isinstance(board["columns"], list)
    assert isinstance(board["cards"], dict)
    assert len(board["columns"]) == 5


def test_concurrent_board_updates_are_safe(tmp_path) -> None:
    import concurrent.futures

    repository = BoardRepository(tmp_path / "concurrent.db")
    repository.get_active_board("user")

    def do_update(index: int) -> dict:
        state = {
            "columns": [{"id": "col-backlog", "title": "Backlog", "cardIds": [f"card-{index}"]}],
            "cards": {f"card-{index}": {"id": f"card-{index}", "title": f"Card {index}", "details": ""}},
        }
        return repository.update_active_board("user", state)

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        list(executor.map(do_update, range(10)))

    final = repository.get_active_board("user")
    assert isinstance(final["columns"], list)
    assert isinstance(final["cards"], dict)


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
