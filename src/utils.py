from typing import Optional

import psycopg2
from psycopg2 import sql


def create_database(db_name: str, user: str, password: str, host: str, port: str) -> None:
    """
    Создание базы данных, если она не существует.

    Args:
        db_name: Имя создаваемой БД
        user: Пользователь PostgreSQL
        password: Пароль пользователя
        host: Хост PostgreSQL
        port: Порт PostgreSQL
    """
    try:
        # Подключаемся к стандартной базе 'postgres'
        conn = psycopg2.connect(dbname="postgres", user=user, password=password, host=host, port=port)
        conn.autocommit = True

        with conn.cursor() as cur:
            # Проверяем, существует ли уже такая база
            cur.execute("SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (db_name,))
            exists = cur.fetchone()

            if not exists:
                cur.execute(sql.SQL("CREATE DATABASE {} ENCODING 'UTF8'").format(sql.Identifier(db_name)))
                print(f"База данных '{db_name}' успешно создана.")
            else:
                print(f"База данных '{db_name}' уже существует.")

        conn.close()
    except Exception as e:
        print(f"Ошибка при создании базы данных: {e}")
        raise


def format_salary(salary: Optional[dict]) -> str:
    """
    Форматирует зарплату из API hh.ru в читаемый вид.

    Args:
        salary: Словарь с данными о зарплате из вакансии

    Returns:
        str: Отформатированная строка зарплаты
    """
    if not salary:
        return "Не указана"

    salary_from = salary.get("from")
    salary_to = salary.get("to")
    currency = salary.get("currency", "rub")

    # Проверяем что значения не None (0 - валидное значение)
    if salary_from is not None and salary_to is not None:
        return f"от {salary_from} до {salary_to} {currency}"
    elif salary_from is not None:
        return f"от {salary_from} {currency}"
    elif salary_to is not None:
        return f"до {salary_to} {currency}"
    else:
        return "Не указана"
