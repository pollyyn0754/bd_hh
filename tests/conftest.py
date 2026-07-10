from unittest.mock import MagicMock, Mock

import pytest

from src.api import HeadHunterAPI
from src.db_manager import DBManager


@pytest.fixture
def api() -> HeadHunterAPI:
    """Фикстура для создания экземплята API."""
    return HeadHunterAPI()


@pytest.fixture
def mock_response() -> Mock:
    """Фикстура для мока ответа requests."""
    mock = Mock()
    mock.raise_for_status = Mock()
    return mock


@pytest.fixture
def db_manager() -> DBManager:
    """Фикстура для создания экземпляра DBManager."""
    return DBManager(db_name="test_db", user="test_user", password="test_pass", host="localhost", port="5432")


@pytest.fixture
def mock_cursor() -> MagicMock:
    """Фикстура для мока курсора."""
    mock = MagicMock()  # Настраиваем для работы с контекстным менеджером
    mock.__enter__ = Mock(return_value=mock)
    mock.__exit__ = Mock(return_value=None)
    return mock


@pytest.fixture
def mock_connection(mock_cursor: Mock) -> Mock:
    """Фикстура для мока соединения с БД."""
    mock_conn = Mock()
    # Настраиваем cursor так, чтобы он возвращал курсор и работал с контекстным менеджером
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    mock_conn.cursor.return_value.__exit__.return_value = None
    return mock_conn
