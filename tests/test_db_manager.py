from unittest.mock import MagicMock, Mock, patch

import pytest

from src.db_manager import DBManager


def test_init(db_manager: DBManager) -> None:
    """Тест инициализации DBManager."""
    assert db_manager.connection_params["dbname"] == "test_db"
    assert db_manager.connection_params["user"] == "test_user"
    assert db_manager.connection_params["password"] == "test_pass"
    assert db_manager.connection_params["host"] == "localhost"
    assert db_manager.connection_params["port"] == "5432"
    assert db_manager.conn is None


@patch("src.db_manager.psycopg2.connect")
def test_connect_success(mock_connect: Mock, db_manager: DBManager) -> None:
    """Тест успешного подключения к БД."""
    mock_conn = Mock()
    mock_connect.return_value = mock_conn

    db_manager._connect()

    mock_connect.assert_called_once_with(
        dbname="test_db", user="test_user", password="test_pass", host="localhost", port="5432"
    )
    assert db_manager.conn == mock_conn


@patch("src.db_manager.psycopg2.connect")
def test_connect_already_connected(mock_connect: Mock, db_manager: DBManager) -> None:
    """Тест повторного подключения когда уже есть соединение."""
    mock_conn = Mock()
    mock_conn.closed = False
    db_manager.conn = mock_conn

    db_manager._connect()

    mock_connect.assert_not_called()


@patch("src.db_manager.psycopg2.connect")
def test_ensure_connection_success(mock_connect: Mock, db_manager: DBManager) -> None:
    """Тест _ensure_connection при успешном подключении."""
    mock_conn = Mock()
    mock_connect.return_value = mock_conn

    result = db_manager._ensure_connection()

    assert result == mock_conn
    mock_connect.assert_called_once()


def test_ensure_connection_failure(db_manager: DBManager) -> None:
    """Тест _ensure_connection при ошибке подключения."""
    with patch.object(db_manager, "_connect") as mock_connect:
        mock_connect.return_value = None
        db_manager.conn = None

        with pytest.raises(RuntimeError, match="Не удалось установить соединение с БД"):
            db_manager._ensure_connection()


@patch("src.db_manager.psycopg2.connect")
def test_disconnect(mock_connect: Mock, db_manager: DBManager) -> None:
    """Тест закрытия соединения."""
    mock_conn = Mock()
    mock_conn.closed = False
    db_manager.conn = mock_conn

    db_manager.disconnect()

    mock_conn.close.assert_called_once()


def test_disconnect_already_closed(db_manager: DBManager) -> None:
    """Тест закрытия уже закрытого соединения."""
    mock_conn = Mock()
    mock_conn.closed = True
    db_manager.conn = mock_conn

    db_manager.disconnect()

    mock_conn.close.assert_not_called()


@patch("src.db_manager.DBManager._ensure_connection")
def test_create_tables(mock_ensure_conn: Mock, db_manager: DBManager, mock_cursor: MagicMock) -> None:
    """Тест создания таблиц."""
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_ensure_conn.return_value = mock_conn

    with patch("builtins.print") as mock_print:
        db_manager.create_tables()

    assert mock_cursor.execute.call_count == 2
    mock_conn.commit.assert_called_once()
    mock_print.assert_called_with("Таблицы успешно созданы.")


@patch("src.db_manager.DBManager._ensure_connection")
def test_insert_company(mock_ensure_conn: Mock, db_manager: DBManager, mock_cursor: MagicMock) -> None:
    """Тест вставки компании."""
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_ensure_conn.return_value = mock_conn

    company_data = {
        "id": 123,
        "name": "Test Company",
        "description": "Test Description",
        "site_url": "https://test.com",
        "alternate_url": "https://hh.ru/test",
    }

    db_manager.insert_company(company_data)

    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


@patch("src.db_manager.DBManager._ensure_connection")
def test_insert_vacancy_success(mock_ensure_conn: Mock, db_manager: DBManager, mock_cursor: MagicMock) -> None:
    """Тест успешной вставки вакансии."""
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_ensure_conn.return_value = mock_conn

    vacancy_data = {
        "id": 456,
        "name": "Python Developer",
        "employer": {"id": 123},
        "salary": {"from": 100000, "to": 150000, "currency": "RUR"},
        "snippet": {"requirement": "Python experience"},
        "alternate_url": "https://hh.ru/vacancy/456",
        "published_at": "2024-01-01T00:00:00",
    }

    db_manager.insert_vacancy(vacancy_data)

    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


@patch("src.db_manager.DBManager._ensure_connection")
def test_insert_vacancy_without_employer(
    mock_ensure_conn: Mock, db_manager: DBManager, mock_cursor: MagicMock
) -> None:
    """Тест пропуска вакансии без работодателя."""
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_ensure_conn.return_value = mock_conn

    vacancy_data = {"id": 456, "name": "Python Developer", "employer": {}}

    db_manager.insert_vacancy(vacancy_data)

    mock_cursor.execute.assert_not_called()
    mock_conn.commit.assert_not_called()


@patch("src.db_manager.DBManager._ensure_connection")
def test_insert_vacancy_without_salary(mock_ensure_conn: Mock, db_manager: DBManager, mock_cursor: MagicMock) -> None:
    """Тест вставки вакансии без зарплаты."""
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_ensure_conn.return_value = mock_conn

    vacancy_data = {
        "id": 456,
        "name": "Python Developer",
        "employer": {"id": 123},
        "salary": None,
        "snippet": {"requirement": "Python experience"},
        "alternate_url": "https://hh.ru/vacancy/456",
        "published_at": "2024-01-01T00:00:00",
    }

    db_manager.insert_vacancy(vacancy_data)

    mock_cursor.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


@patch("src.db_manager.DBManager._ensure_connection")
def test_get_companies_and_vacancies_count(
    mock_ensure_conn: Mock, db_manager: DBManager, mock_cursor: MagicMock
) -> None:
    """Тест получения количества вакансий по компаниям."""
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_ensure_conn.return_value = mock_conn

    mock_cursor.fetchall.return_value = [("Company A", 5), ("Company B", 3), ("Company C", 0)]

    result = db_manager.get_companies_and_vacancies_count()

    mock_cursor.execute.assert_called_once()
    assert result == [("Company A", 5), ("Company B", 3), ("Company C", 0)]
    assert isinstance(result[0][0], str)
    assert isinstance(result[0][1], int)


@patch("src.db_manager.DBManager._ensure_connection")
def test_get_all_vacancies(mock_ensure_conn: Mock, db_manager: DBManager, mock_cursor: MagicMock) -> None:
    """Тест получения всех вакансий."""
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_ensure_conn.return_value = mock_conn

    mock_cursor.fetchall.return_value = [
        ("Company A", "Developer", 100000, 150000, "https://hh.ru/1"),
        ("Company B", "Manager", 80000, 120000, "https://hh.ru/2"),
    ]

    result = db_manager.get_all_vacancies()

    mock_cursor.execute.assert_called_once()
    assert len(result) == 2
    assert result[0][0] == "Company A"
    assert result[0][1] == "Developer"
    assert result[0][2] == 100000
    assert result[0][3] == 150000


@patch("src.db_manager.DBManager._ensure_connection")
def test_get_avg_salary_with_data(mock_ensure_conn: Mock, db_manager: DBManager, mock_cursor: MagicMock) -> None:
    """Тест получения средней зарплаты при наличии данных."""
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_ensure_conn.return_value = mock_conn

    mock_cursor.fetchone.return_value = (125000.0,)

    result = db_manager.get_avg_salary()

    mock_cursor.execute.assert_called_once()
    assert result == 125000.0


@patch("src.db_manager.DBManager._ensure_connection")
def test_get_avg_salary_no_data(mock_ensure_conn: Mock, db_manager: DBManager, mock_cursor: MagicMock) -> None:
    """Тест получения средней зарплаты когда нет данных."""
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_ensure_conn.return_value = mock_conn

    mock_cursor.fetchone.return_value = (None,)

    result = db_manager.get_avg_salary()

    assert result == 0.0


@patch("src.db_manager.DBManager._ensure_connection")
def test_get_avg_salary_empty_result(mock_ensure_conn: Mock, db_manager: DBManager, mock_cursor: MagicMock) -> None:
    """Тест получения средней зарплаты при пустом результате."""
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_ensure_conn.return_value = mock_conn

    mock_cursor.fetchone.return_value = None

    result = db_manager.get_avg_salary()

    assert result == 0.0


@patch("src.db_manager.DBManager.get_avg_salary")
@patch("src.db_manager.DBManager._ensure_connection")
def test_get_vacancies_with_higher_salary(
    mock_ensure_conn: Mock, mock_get_avg: Mock, db_manager: DBManager, mock_cursor: MagicMock
) -> None:
    """Тест получения вакансий с зарплатой выше средней."""
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_ensure_conn.return_value = mock_conn
    mock_get_avg.return_value = 100000.0

    mock_cursor.fetchall.return_value = [
        ("Company A", "Senior Developer", 200000, 250000, "https://hh.ru/1"),
        ("Company B", "Lead Manager", 150000, 200000, "https://hh.ru/2"),
    ]

    result = db_manager.get_vacancies_with_higher_salary()

    mock_cursor.execute.assert_called_once()
    assert len(result) == 2
    assert result[0][1] == "Senior Developer"


@patch("src.db_manager.DBManager._ensure_connection")
def test_get_vacancies_with_keyword(mock_ensure_conn: Mock, db_manager: DBManager, mock_cursor: MagicMock) -> None:
    """Тест поиска вакансий по ключевому слову."""
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_ensure_conn.return_value = mock_conn

    mock_cursor.fetchall.return_value = [
        ("Company A", "Python Developer", 100000, 150000, "https://hh.ru/1"),
        ("Company B", "Python Backend", 120000, 160000, "https://hh.ru/2"),
    ]

    result = db_manager.get_vacancies_with_keyword("python")

    mock_cursor.execute.assert_called_once()
    assert len(result) == 2
    assert "Python" in result[0][1] or "python" in result[0][1]


@patch("src.db_manager.DBManager._ensure_connection")
def test_get_vacancies_with_keyword_no_results(
    mock_ensure_conn: Mock, db_manager: DBManager, mock_cursor: MagicMock
) -> None:
    """Тест поиска вакансий по ключевому слову без результатов."""
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_ensure_conn.return_value = mock_conn

    mock_cursor.fetchall.return_value = []

    result = db_manager.get_vacancies_with_keyword("java")

    assert result == []


def test_disconnect_called_in_methods(db_manager: DBManager) -> None:
    """Тест что disconnect можно вызвать."""
    mock_conn = Mock()
    mock_conn.closed = False
    db_manager.conn = mock_conn

    db_manager.disconnect()

    mock_conn.close.assert_called_once()
