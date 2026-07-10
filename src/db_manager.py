from typing import List, Optional, Tuple, Any

import psycopg2
from psycopg2.extensions import connection


class DBManager:
    """Класс для управления данными в базе данных PostgreSQL."""

    def __init__(self, db_name: str, user: str, password: str, host: str, port: str):
        """
        Инициализация подключения к базе данных.

        Args:
            db_name: Имя базы данных
            user: Имя пользователя
            password: Пароль
            host: Хост
            port: Порт
        """
        self.connection_params: dict[str, str] = {
            "dbname": db_name,
            "user": user,
            "password": password,
            "host": host,
            "port": port
        }
        self.conn: Optional[connection] = None

    def _connect(self) -> None:
        """Внутренний метод для подключения к БД."""
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(
                dbname=self.connection_params["dbname"],
                user=self.connection_params["user"],
                password=self.connection_params["password"],
                host=self.connection_params["host"],
                port=self.connection_params["port"]
            )

    def disconnect(self) -> None:
        """Закрытие соединения с БД."""
        if self.conn and not self.conn.closed:
            self.conn.close()

    def _ensure_connection(self) -> connection:
        """
        Обеспечивает наличие активного соединения.

        Returns:
            connection: Активное соединение с БД

        Raises:
            RuntimeError: Если не удалось установить соединение
        """
        self._connect()
        if self.conn is None:
            raise RuntimeError("Не удалось установить соединение с БД")
        return self.conn

    def create_tables(self) -> None:
        """Создание таблиц companies и vacancies в БД."""
        conn = self._ensure_connection()
        with conn.cursor() as cur:
            # Таблица компаний
            cur.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    site_url TEXT,
                    alternate_url TEXT
                )
            """)

            # Таблица вакансий с внешним ключом на companies
            cur.execute("""
                CREATE TABLE IF NOT EXISTS vacancies (
                    id INTEGER PRIMARY KEY,
                    company_id INTEGER NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
                    name VARCHAR(255) NOT NULL,
                    salary_from INTEGER,
                    salary_to INTEGER,
                    currency VARCHAR(10),
                    description TEXT,
                    url TEXT,
                    published_at TIMESTAMP
                )
            """)
            conn.commit()
        print("Таблицы успешно созданы.")

    def insert_company(self, company_data: dict) -> None:
        """
        Вставка или обновление данных компании в таблицу.

        Args:
            company_data: Данные компании от API hh.ru
        """
        conn = self._ensure_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO companies (id, name, description, site_url, alternate_url)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    site_url = EXCLUDED.site_url,
                    alternate_url = EXCLUDED.alternate_url
            """,
                (
                    company_data["id"],
                    company_data["name"],
                    company_data.get("description"),
                    company_data.get("site_url"),
                    company_data.get("alternate_url"),
                ),
            )
            conn.commit()

    def insert_vacancy(self, vacancy_data: dict) -> None:
        """
        Вставка данных вакансии в таблицу.

        Args:
            vacancy_data: Данные вакансии от API hh.ru
        """
        salary = vacancy_data.get("salary")
        company = vacancy_data.get("employer", {})

        # Пропускаем вакансии без ID работодателя
        if not company or "id" not in company:
            return

        conn = self._ensure_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO vacancies (
                    id, company_id, name, salary_from, salary_to, currency,
                    description, url, published_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """,
                (
                    vacancy_data["id"],
                    int(company["id"]),
                    vacancy_data["name"],
                    salary.get("from") if salary else None,
                    salary.get("to") if salary else None,
                    salary.get("currency") if salary else None,
                    vacancy_data.get("snippet", {}).get("requirement"),
                    vacancy_data["alternate_url"],
                    vacancy_data["published_at"],
                ),
            )
            conn.commit()

    # --- Методы для анализа данных ---

    def get_companies_and_vacancies_count(self) -> List[Tuple[str, int]]:
        """
        Получает список всех компаний и количество вакансий у каждой.

        Returns:
            List[Tuple[str, int]]: Список кортежей (название компании, количество вакансий)
        """
        conn = self._ensure_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.name, COUNT(v.id) as vacancies_count
                FROM companies c
                LEFT JOIN vacancies v ON c.id = v.company_id
                GROUP BY c.id, c.name
                ORDER BY vacancies_count DESC
            """)
            result = cur.fetchall()
            return [(str(row[0]), int(row[1])) for row in result]

    def get_all_vacancies(self) -> List[Tuple[str, str, Optional[int], Optional[int], str]]:
        """
        Получает список всех вакансий с деталями.

        Returns:
            List[Tuple]: Список кортежей (компания, вакансия, зарплата от, зарплата до, ссылка)
        """
        conn = self._ensure_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    c.name AS company_name,
                    v.name AS vacancy_name,
                    v.salary_from,
                    v.salary_to,
                    v.url
                FROM vacancies v
                JOIN companies c ON v.company_id = c.id
                ORDER BY c.name, v.name
            """)
            result = cur.fetchall()
            return [
                (str(row[0]), str(row[1]), row[2], row[3], str(row[4]))
                for row in result
            ]

    def get_avg_salary(self) -> float:
        """
        Получает среднюю зарплату по всем вакансиям.

        Returns:
            float: Средняя зарплата
        """
        conn = self._ensure_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT AVG((COALESCE(salary_from, 0) + COALESCE(salary_to, 0)) / 2)
                FROM vacancies
                WHERE salary_from IS NOT NULL OR salary_to IS NOT NULL
            """)
            result = cur.fetchone()
            # Проверяем, что результат не None
            if result is None or result[0] is None:
                return 0.0
            return float(result[0])

    def get_vacancies_with_higher_salary(self) -> List[Tuple[Any, ...]]:
        """
        Получает список вакансий с зарплатой выше средней.

        Returns:
            List[Tuple]: Список вакансий (компания, вакансия, зарплата от, зарплата до, ссылка)
        """
        avg_salary = self.get_avg_salary()
        conn = self._ensure_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    c.name AS company_name,
                    v.name AS vacancy_name,
                    v.salary_from,
                    v.salary_to,
                    v.url
                FROM vacancies v
                JOIN companies c ON v.company_id = c.id
                WHERE (COALESCE(v.salary_from, 0) + COALESCE(v.salary_to, 0)) / 2 > %s
                ORDER BY (COALESCE(v.salary_from, 0) + COALESCE(v.salary_to, 0)) / 2 DESC
            """,
                (avg_salary,),
            )
            return cur.fetchall()

    def get_vacancies_with_keyword(self, keyword: str) -> List[Tuple[Any, ...]]:
        """
        Получает список вакансий, в названии которых содержится ключевое слово.

        Args:
            keyword: Ключевое слово для поиска

        Returns:
            List[Tuple]: Список вакансий (компания, вакансия, зарплата от, зарплата до, ссылка)
        """
        conn = self._ensure_connection()
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    c.name AS company_name,
                    v.name AS vacancy_name,
                    v.salary_from,
                    v.salary_to,
                    v.url
                FROM vacancies v
                JOIN companies c ON v.company_id = c.id
                WHERE LOWER(v.name) LIKE %s
                ORDER BY c.name, v.name
            """,
                (f"%{keyword.lower()}%",),
            )
            return cur.fetchall()
