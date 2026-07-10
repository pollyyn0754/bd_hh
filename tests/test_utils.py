from unittest.mock import MagicMock, patch

import psycopg2
import pytest

from src.utils import create_database, format_salary

# --- Тесты для format_salary ---


def test_format_salary_with_from_and_to():
    """Тест форматирования зарплаты с от и до."""
    salary = {"from": 100000, "to": 150000, "currency": "RUR"}
    result = format_salary(salary)
    assert result == "от 100000 до 150000 RUR"


def test_format_salary_with_from_only():
    """Тест форматирования зарплаты только с от."""
    salary = {"from": 100000, "to": None, "currency": "RUR"}
    result = format_salary(salary)
    assert result == "от 100000 RUR"


def test_format_salary_with_to_only():
    """Тест форматирования зарплаты только с до."""
    salary = {"from": None, "to": 150000, "currency": "RUR"}
    result = format_salary(salary)
    assert result == "до 150000 RUR"


def test_format_salary_without_currency():
    """Тест форматирования зарплаты без валюты."""
    salary = {"from": 100000, "to": 150000}
    result = format_salary(salary)
    assert result == "от 100000 до 150000 rub"


def test_format_salary_empty():
    """Тест форматирования пустой зарплаты."""
    salary = None
    result = format_salary(salary)
    assert result == "Не указана"


def test_format_salary_empty_dict():
    """Тест форматирования пустого словаря."""
    salary = {}
    result = format_salary(salary)
    assert result == "Не указана"


def test_format_salary_with_zero_values():
    """Тест форматирования зарплаты с нулевыми значениями."""
    salary = {"from": 0, "to": 0, "currency": "RUR"}
    result = format_salary(salary)
    assert result == "от 0 до 0 RUR"


def test_format_salary_with_from_zero_to_none():
    """Тест форматирования зарплаты с от 0 и до None."""
    salary = {"from": 0, "to": None, "currency": "RUR"}
    result = format_salary(salary)
    assert result == "от 0 RUR"


def test_format_salary_with_from_none_to_zero():
    """Тест форматирования зарплаты с от None и до 0."""
    salary = {"from": None, "to": 0, "currency": "RUR"}
    result = format_salary(salary)
    assert result == "до 0 RUR"


def test_format_salary_with_large_numbers():
    """Тест форматирования зарплаты с большими числами."""
    salary = {"from": 1000000, "to": 1500000, "currency": "USD"}
    result = format_salary(salary)
    assert result == "от 1000000 до 1500000 USD"


def test_format_salary_with_negative_values():
    """Тест форматирования зарплаты с отрицательными значениями."""
    salary = {"from": -10000, "to": -5000, "currency": "RUR"}
    result = format_salary(salary)
    assert result == "от -10000 до -5000 RUR"


def test_format_salary_with_string_numbers():
    """Тест форматирования зарплаты с числами в виде строк."""
    salary = {"from": "100", "to": "200", "currency": "RUR"}
    result = format_salary(salary)
    assert result == "от 100 до 200 RUR"


# --- Тесты для create_database ---


def test_create_database_connection_error():
    """Тест ошибки подключения при создании базы."""
    with patch("src.utils.psycopg2.connect") as mock_connect:
        mock_connect.side_effect = psycopg2.OperationalError("Connection failed")

        with pytest.raises(psycopg2.OperationalError, match="Connection failed"):
            create_database(db_name="test_db", user="test_user", password="test_pass", host="localhost", port="5432")


def test_create_database_general_error():
    """Тест общей ошибки при создании базы."""
    with patch("src.utils.psycopg2.connect") as mock_connect:
        mock_connect.side_effect = Exception("Some error occurred")

        with pytest.raises(Exception, match="Some error occurred"):
            create_database(db_name="test_db", user="test_user", password="test_pass", host="localhost", port="5432")


def test_create_database_with_custom_params():
    """Тест создания базы с кастомными параметрами."""
    with patch("src.utils.psycopg2.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        mock_connect.return_value = mock_conn

        create_database(
            db_name="custom_db", user="custom_user", password="custom_pass", host="192.168.1.100", port="5433"
        )

        mock_connect.assert_called_once_with(
            dbname="postgres", user="custom_user", password="custom_pass", host="192.168.1.100", port="5433"
        )


def test_create_database_autocommit_set():
    """Тест что autocommit устанавливается в True."""
    with patch("src.utils.psycopg2.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.fetchone.return_value = None
        mock_connect.return_value = mock_conn

        create_database(db_name="test_db", user="test_user", password="test_pass", host="localhost", port="5432")

        assert mock_conn.autocommit is True


# --- Параметризованные тесты для format_salary ---


@pytest.mark.parametrize(
    "salary,expected",
    [
        ({"from": 100, "to": 200, "currency": "USD"}, "от 100 до 200 USD"),
        ({"from": 100, "currency": "EUR"}, "от 100 EUR"),
        ({"to": 200, "currency": "GBP"}, "до 200 GBP"),
        ({}, "Не указана"),
        ({"from": None, "to": None, "currency": "RUR"}, "Не указана"),
        ({"from": 0, "to": 0}, "от 0 до 0 rub"),
    ],
)
def test_format_salary_parametrized(salary, expected):
    """Параметризованный тест форматирования зарплаты."""
    result = format_salary(salary)
    assert result == expected


# --- Интеграционные тесты ---


def test_format_salary_integration():
    """Интеграционный тест форматирования зарплаты."""
    test_cases = [
        ({"from": 100000, "to": 150000, "currency": "RUR"}, "от 100000 до 150000 RUR"),
        ({"from": 80000, "currency": "RUR"}, "от 80000 RUR"),
        ({"to": 120000, "currency": "RUR"}, "до 120000 RUR"),
        ({"from": None, "to": None}, "Не указана"),
        ({"from": 0, "to": 0, "currency": "USD"}, "от 0 до 0 USD"),
    ]

    for salary, expected in test_cases:
        assert format_salary(salary) == expected


def test_create_database_integration():
    """Интеграционный тест создания базы (пропускается если нет PostgreSQL)."""
    import sys

    # Устанавливаем кодировку для корректного вывода
    if sys.stdout.encoding != "utf-8":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    try:
        with patch("builtins.print") as mock_print:
            create_database(
                db_name="test_integration_db", user="postgres", password="postgres", host="localhost", port="5432"
            )
        assert mock_print.called
    except psycopg2.OperationalError as e:
        if "connection" in str(e).lower() or "could not connect" in str(e).lower():
            pytest.skip("PostgreSQL не доступен для интеграционного теста")
        else:
            raise
    except UnicodeDecodeError:
        pytest.skip("Проблемы с кодировкой при выполнении интеграционного теста")
    except Exception as e:
        if "Connection" not in str(e) and "connect" not in str(e).lower():
            raise
        pytest.skip("PostgreSQL не доступен для интеграционного теста")


# --- Дополнительные тесты для format_salary ---


def test_format_salary_with_from_zero_to_large():
    """Тест форматирования зарплаты с от 0 и до большого числа."""
    salary = {"from": 0, "to": 1000000, "currency": "RUR"}
    result = format_salary(salary)
    assert result == "от 0 до 1000000 RUR"


def test_format_salary_with_from_large_to_zero():
    """Тест форматирования зарплаты с от большого числа и до 0."""
    salary = {"from": 1000000, "to": 0, "currency": "RUR"}
    result = format_salary(salary)
    assert result == "от 1000000 до 0 RUR"
