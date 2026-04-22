from slowapi import Limiter
from slowapi.util import get_remote_address

from backend.app.board_repository import BoardRepository

limiter = Limiter(key_func=get_remote_address)
board_repository = BoardRepository()
