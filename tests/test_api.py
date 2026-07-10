import time
from unittest.mock import Mock, patch

from src.api import HeadHunterAPI


def test_init(api: HeadHunterAPI) -> None:
    """Тест инициализации API."""
    assert api.base_url == "https://api.hh.ru/"
    assert api.headers == {"User-Agent": "HH-Parser-Project/1.0 (my-email@example.com)"}


@patch("src.api.requests.get")
def test_get_success(mock_get: Mock, api: HeadHunterAPI) -> None:
    """Тест успешного GET-запроса."""
    # Подготовка
    mock_response = Mock()
    mock_response.json.return_value = {"key": "value"}
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    # Выполнение
    result = api._get("https://api.hh.ru/test")

    # Проверка
    mock_get.assert_called_once_with("https://api.hh.ru/test", headers=api.headers, params=None)
    assert result == {"key": "value"}


@patch("src.api.requests.get")
def test_get_with_params(mock_get: Mock, api: HeadHunterAPI) -> None:
    """Тест GET-запроса с параметрами."""
    # Подготовка
    mock_response = Mock()
    mock_response.json.return_value = {"items": []}
    mock_response.raise_for_status = Mock()
    mock_get.return_value = mock_response

    params = {"param1": "value1", "param2": "value2"}

    # Выполнение
    result = api._get("https://api.hh.ru/test", params)

    # Проверка
    mock_get.assert_called_once_with("https://api.hh.ru/test", headers=api.headers, params=params)
    assert result == {"items": []}


@patch("src.api.requests.get")
def test_get_request_exception(mock_get: Mock, api: HeadHunterAPI, capsys) -> None:
    """Тест GET-запроса с ошибкой запроса."""
    # Подготовка
    from requests.exceptions import RequestException

    mock_get.side_effect = RequestException("Connection error")

    # Выполнение
    result = api._get("https://api.hh.ru/test")

    # Проверка
    assert result == {}
    captured = capsys.readouterr()
    assert "Ошибка при запросе к API" in captured.out


@patch("src.api.requests.get")
def test_get_general_exception(mock_get: Mock, api: HeadHunterAPI, capsys) -> None:
    """Тест GET-запроса с общей ошибкой."""
    # Подготовка
    mock_get.side_effect = Exception("Unknown error")

    # Выполнение
    result = api._get("https://api.hh.ru/test")

    # Проверка
    assert result == {}
    captured = capsys.readouterr()
    assert "Неизвестная ошибка" in captured.out


@patch("src.api.HeadHunterAPI._get")
def test_get_employer_success(mock_get: Mock, api: HeadHunterAPI) -> None:
    """Тест успешного получения информации о работодателе."""
    # Подготовка
    expected_data = {"id": 123, "name": "Test Company", "description": "Test Description"}
    mock_get.return_value = expected_data

    # Выполнение
    result = api.get_employer(123)

    # Проверка
    mock_get.assert_called_once_with("https://api.hh.ru/employers/123")
    assert result == expected_data


@patch("src.api.HeadHunterAPI._get")
def test_get_employer_empty(mock_get: Mock, api: HeadHunterAPI) -> None:
    """Тест получения информации о несуществующем работодателе."""
    # Подготовка
    mock_get.return_value = {}

    # Выполнение
    result = api.get_employer(999)

    # Проверка
    assert result == {}


@patch("src.api.HeadHunterAPI._get")
def test_get_employer_vacancies_success(mock_get: Mock, api: HeadHunterAPI) -> None:
    """Тест успешного получения вакансий работодателя."""
    # Подготовка
    expected_vacancies = [{"id": 1, "name": "Vacancy 1"}, {"id": 2, "name": "Vacancy 2"}]
    mock_get.return_value = {"items": expected_vacancies}

    # Выполнение
    result = api.get_employer_vacancies(123, page=1, per_page=10)

    # Проверка
    mock_get.assert_called_once_with("https://api.hh.ru/vacancies", {"employer_id": 123, "page": 0, "per_page": 10})
    assert result == expected_vacancies


@patch("src.api.HeadHunterAPI._get")
def test_get_employer_vacancies_empty(mock_get: Mock, api: HeadHunterAPI) -> None:
    """Тест получения вакансий без результатов."""
    # Подготовка
    mock_get.return_value = {}

    # Выполнение
    result = api.get_employer_vacancies(123)

    # Проверка
    assert result == []


@patch("src.api.HeadHunterAPI.get_employer_vacancies")
def test_get_all_vacancies_from_employer_single_page(mock_get_vacancies: Mock, api: HeadHunterAPI) -> None:
    """Тест получения всех вакансий при одной странице."""
    # Подготовка
    vacancies_page = [{"id": 1, "name": "Vacancy 1"}, {"id": 2, "name": "Vacancy 2"}, {"id": 3, "name": "Vacancy 3"}]
    mock_get_vacancies.return_value = vacancies_page

    # Выполнение
    result = api.get_all_vacancies_from_employer(123)

    # Проверка
    mock_get_vacancies.assert_called_once_with(123, 1, 100)
    assert result == vacancies_page
    assert len(result) == 3


@patch("src.api.HeadHunterAPI.get_employer_vacancies")
def test_get_all_vacancies_from_employer_multiple_pages(mock_get_vacancies: Mock, api: HeadHunterAPI) -> None:
    """Тест получения всех вакансий при нескольких страницах."""
    # Подготовка
    page1 = [{"id": i, "name": f"Vacancy {i}"} for i in range(1, 101)]
    page2 = [{"id": i, "name": f"Vacancy {i}"} for i in range(101, 151)]

    def mock_vacancies_side_effect(emp_id, page, per_page):
        if page == 1:
            return page1
        elif page == 2:
            return page2
        else:
            return []

    mock_get_vacancies.side_effect = mock_vacancies_side_effect

    # Выполнение
    result = api.get_all_vacancies_from_employer(123)

    # Проверка
    assert len(result) == 150
    assert mock_get_vacancies.call_count == 2


@patch("src.api.HeadHunterAPI.get_employer_vacancies")
def test_get_all_vacancies_from_employer_empty(mock_get_vacancies: Mock, api: HeadHunterAPI) -> None:
    """Тест получения всех вакансий когда их нет."""
    # Подготовка
    mock_get_vacancies.return_value = []

    # Выполнение
    result = api.get_all_vacancies_from_employer(123)

    # Проверка
    assert result == []
    mock_get_vacancies.assert_called_once_with(123, 1, 100)


@patch("src.api.HeadHunterAPI.get_employer_vacancies")
def test_get_all_vacancies_from_employer_rate_limit(mock_get_vacancies: Mock, api: HeadHunterAPI) -> None:
    """Тест что есть задержка между запросами."""
    # Подготовка
    page1 = [{"id": i, "name": f"Vacancy {i}"} for i in range(1, 101)]
    page2 = [{"id": 101, "name": "Vacancy 101"}]

    def mock_vacancies_side_effect(emp_id, page, per_page):
        if page == 1:
            return page1
        elif page == 2:
            return page2
        else:
            return []

    mock_get_vacancies.side_effect = mock_vacancies_side_effect

    # Выполнение
    start_time = time.time()
    result = api.get_all_vacancies_from_employer(123)
    elapsed_time = time.time() - start_time

    # Проверка
    assert len(result) == 101
    assert elapsed_time >= 0.2


@patch("src.api.HeadHunterAPI.get_employer_vacancies")
def test_get_all_vacancies_from_employer_exact_boundary(mock_get_vacancies: Mock, api: HeadHunterAPI) -> None:
    """Тест получения всех вакансий когда последняя страница содержит ровно 100 записей."""
    # Подготовка
    page1 = [{"id": i, "name": f"Vacancy {i}"} for i in range(1, 101)]
    page2 = [{"id": i, "name": f"Vacancy {i}"} for i in range(101, 201)]

    def mock_vacancies_side_effect(emp_id, page, per_page):
        if page == 1:
            return page1
        elif page == 2:
            return page2
        else:
            return []

    mock_get_vacancies.side_effect = mock_vacancies_side_effect

    # Выполнение
    result = api.get_all_vacancies_from_employer(123)

    # Проверка
    assert len(result) == 200
    assert mock_get_vacancies.call_count == 3


def test_get_employer_vacancies_pagination_parameters(api: HeadHunterAPI) -> None:
    """Тест параметров пагинации."""
    with patch.object(api, "_get") as mock_get:
        mock_get.return_value = {"items": []}

        # Вызов с параметрами по умолчанию
        api.get_employer_vacancies(123)
        mock_get.assert_called_with("https://api.hh.ru/vacancies", {"employer_id": 123, "page": 0, "per_page": 100})

        # Вызов с кастомными параметрами
        api.get_employer_vacancies(123, page=3, per_page=50)
        mock_get.assert_called_with("https://api.hh.ru/vacancies", {"employer_id": 123, "page": 2, "per_page": 50})


@patch("src.api.HeadHunterAPI._get")
def test_get_employer_vacancies_with_real_data_structure(mock_get: Mock, api: HeadHunterAPI) -> None:
    """Тест структуры данных вакансий."""
    # Подготовка
    mock_response = {
        "items": [
            {
                "id": 123456,
                "name": "Python Developer",
                "employer": {"id": 123, "name": "Test Company"},
                "salary": {"from": 100000, "to": 150000, "currency": "RUR"},
                "alternate_url": "https://hh.ru/vacancy/123456",
            }
        ]
    }
    mock_get.return_value = mock_response

    # Выполнение
    result = api.get_employer_vacancies(123)

    # Проверка
    assert len(result) == 1
    vacancy = result[0]
    assert vacancy["id"] == 123456
    assert vacancy["name"] == "Python Developer"
    assert vacancy["employer"]["id"] == 123
    assert vacancy["salary"]["from"] == 100000


@patch("src.api.HeadHunterAPI.get_employer_vacancies")
def test_get_all_vacancies_from_employer_stops_on_empty_page(mock_get_vacancies: Mock, api: HeadHunterAPI) -> None:
    """Тест что цикл останавливается при пустой странице."""
    # Подготовка
    page1 = [{"id": i, "name": f"Vacancy {i}"} for i in range(1, 101)]

    def mock_vacancies_side_effect(emp_id, page, per_page):
        if page == 1:
            return page1
        else:
            return []

    mock_get_vacancies.side_effect = mock_vacancies_side_effect

    # Выполнение
    result = api.get_all_vacancies_from_employer(123)

    # Проверка
    assert len(result) == 100
    assert mock_get_vacancies.call_count == 2  # 1 успешный + 1 пустой


def test_api_headers_are_correct(api: HeadHunterAPI) -> None:
    """Тест правильности заголовков API."""
    expected_headers = {"User-Agent": "HH-Parser-Project/1.0 (my-email@example.com)"}
    assert api.headers == expected_headers
