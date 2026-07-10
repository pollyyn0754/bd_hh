import time
from typing import Any, Dict, List, Optional, cast

import requests


class HeadHunterAPI:
    """Класс для взаимодействия с API hh.ru."""

    def __init__(self) -> None:
        """Инициализация API клиента."""
        self.base_url = "https://api.hh.ru/"
        # Обязательный заголовок для работы с API hh.ru
        self.headers = {"User-Agent": "HH-Parser-Project/1.0 (my-email@example.com)"}

    def _get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Внутренний метод для выполнения GET-запросов.

        Args:
            url: URL для запроса
            params: Параметры запроса

        Returns:
            Dict: Ответ API в виде словаря
        """
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            # Используем cast для явного указания типа
            return cast(Dict[str, Any], response.json())
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе к API: {e}")
            return {}
        except Exception as e:
            print(f"Неизвестная ошибка: {e}")
            return {}

    def get_employer(self, employer_id: int) -> Dict[str, Any]:
        """
        Получение информации о работодателе по ID.

        Args:
            employer_id: ID работодателя на hh.ru

        Returns:
            Dict: Данные о работодателе
        """
        url = f"{self.base_url}employers/{employer_id}"
        return self._get(url)

    def get_employer_vacancies(self, employer_id: int, page: int = 1, per_page: int = 100) -> List[Dict[str, Any]]:
        """
        Получение списка вакансий для конкретного работодателя.

        Args:
            employer_id: ID работодателя
            page: Номер страницы (начиная с 1)
            per_page: Количество вакансий на странице (макс. 100)

        Returns:
            List[Dict]: Список вакансий
        """
        url = f"{self.base_url}vacancies"
        params: Dict[str, Any] = {
            "employer_id": employer_id,
            "page": page - 1,  # API hh.ru использует нумерацию страниц с 0
            "per_page": per_page,
        }
        data = self._get(url, params)
        # Используем cast для явного указания типа
        return cast(List[Dict[str, Any]], data.get("items", []))

    def get_all_vacancies_from_employer(self, employer_id: int) -> List[Dict[str, Any]]:
        """
        Получение ВСЕХ вакансий работодателя с обработкой пагинации.

        Args:
            employer_id: ID работодателя

        Returns:
            List[Dict]: Полный список всех вакансий
        """
        all_vacancies: List[Dict[str, Any]] = []
        page = 1
        per_page = 100  # Максимально допустимое значение

        while True:
            vacancies = self.get_employer_vacancies(employer_id, page, per_page)
            if not vacancies:
                break

            all_vacancies.extend(vacancies)

            # Если получено меньше вакансий, чем запрашивали, значит это последняя страница
            if len(vacancies) < per_page:
                break

            page += 1
            time.sleep(0.2)  # Небольшая задержка, чтобы не нагружать API

        return all_vacancies
