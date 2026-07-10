import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import Config


def test_config_attributes_exist() -> None:
    """Тест наличия всех атрибутов конфигурации."""
    assert hasattr(Config, "DB_NAME")
    assert hasattr(Config, "DB_USER")
    assert hasattr(Config, "DB_PASSWORD")
    assert hasattr(Config, "DB_HOST")
    assert hasattr(Config, "DB_PORT")
    assert hasattr(Config, "COMPANIES")
    assert hasattr(Config, "validate")


@patch.dict(
    os.environ,
    {
        "DB_NAME": "test_db",
        "DB_USER": "test_user",
        "DB_PASSWORD": "test_pass",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
    },
)
def test_config_with_all_env_vars() -> None:
    """Тест загрузки всех переменных окружения."""
    import importlib

    import src.config

    importlib.reload(src.config)
    from src.config import Config as ReloadedConfig

    assert ReloadedConfig.DB_NAME == "test_db"
    assert ReloadedConfig.DB_USER == "test_user"
    assert ReloadedConfig.DB_PASSWORD == "test_pass"
    assert ReloadedConfig.DB_HOST == "localhost"
    assert ReloadedConfig.DB_PORT == "5432"


@patch.dict(os.environ, {"DB_NAME": "", "DB_USER": "", "DB_PASSWORD": "", "DB_HOST": "", "DB_PORT": ""})
def test_config_with_empty_env_vars() -> None:
    """Тест загрузки пустых переменных окружения."""
    import importlib

    import src.config

    importlib.reload(src.config)
    from src.config import Config as ReloadedConfig

    assert ReloadedConfig.DB_NAME == ""
    assert ReloadedConfig.DB_USER == ""
    assert ReloadedConfig.DB_PASSWORD == ""
    assert ReloadedConfig.DB_HOST == ""
    assert ReloadedConfig.DB_PORT == ""


@patch.dict(os.environ, {"DB_NAME": "test_db", "DB_USER": "test_user", "DB_PASSWORD": "test_pass"})
def test_config_validate_success() -> None:
    """Тест успешной валидации конфигурации."""
    import importlib

    import src.config

    importlib.reload(src.config)
    from src.config import Config as ReloadedConfig

    # Проверяем, что валидация не вызывает ошибку
    ReloadedConfig.validate()


@patch.dict(os.environ, {"DB_NAME": "", "DB_USER": "test_user", "DB_PASSWORD": "test_pass"})
def test_config_validate_missing_db_name() -> None:
    """Тест валидации при отсутствии DB_NAME."""
    import importlib

    import src.config

    importlib.reload(src.config)
    from src.config import Config as ReloadedConfig

    with pytest.raises(ValueError, match="Не все переменные окружения для БД заданы в файле .env"):
        ReloadedConfig.validate()


@patch.dict(os.environ, {"DB_NAME": "test_db", "DB_USER": "", "DB_PASSWORD": "test_pass"})
def test_config_validate_missing_db_user() -> None:
    """Тест валидации при отсутствии DB_USER."""
    import importlib

    import src.config

    importlib.reload(src.config)
    from src.config import Config as ReloadedConfig

    with pytest.raises(ValueError, match="Не все переменные окружения для БД заданы в файле .env"):
        ReloadedConfig.validate()


@patch.dict(os.environ, {"DB_NAME": "test_db", "DB_USER": "test_user", "DB_PASSWORD": ""})
def test_config_validate_missing_db_password() -> None:
    """Тест валидации при отсутствии DB_PASSWORD."""
    import importlib

    import src.config

    importlib.reload(src.config)
    from src.config import Config as ReloadedConfig

    with pytest.raises(ValueError, match="Не все переменные окружения для БД заданы в файле .env"):
        ReloadedConfig.validate()


def test_config_companies_list() -> None:
    """Тест списка компаний."""
    # Проверяем что список компаний не пустой
    assert len(Config.COMPANIES) > 0

    # Проверяем что все ID - целые числа
    for company_id in Config.COMPANIES:
        assert isinstance(company_id, int)
        assert company_id > 0

    # Проверяем наличие ключевых компаний
    expected_companies = [3529, 78638, 1740, 3776]  # Сбер, Т-Банк, Яндекс, VK
    for company_id in expected_companies:
        assert company_id in Config.COMPANIES

    # Проверяем что нет дубликатов
    assert len(Config.COMPANIES) == len(set(Config.COMPANIES))


@patch.dict(
    os.environ,
    {
        "DB_NAME": "my_database",
        "DB_USER": "my_user",
        "DB_PASSWORD": "my_password",
        "DB_HOST": "my_host",
        "DB_PORT": "my_port",
    },
)
def test_config_all_env_vars_set_correctly() -> None:
    """Тест корректной установки всех переменных окружения."""
    import importlib

    import src.config

    importlib.reload(src.config)
    from src.config import Config as ReloadedConfig

    assert ReloadedConfig.DB_NAME == "my_database"
    assert ReloadedConfig.DB_USER == "my_user"
    assert ReloadedConfig.DB_PASSWORD == "my_password"
    assert ReloadedConfig.DB_HOST == "my_host"
    assert ReloadedConfig.DB_PORT == "my_port"


@patch.dict(os.environ, {"DB_NAME": "test_db", "DB_USER": "test_user", "DB_PASSWORD": "test_pass"})
def test_config_validate_with_all_required_vars() -> None:
    """Тест что validate не выбрасывает исключение при всех переменных."""
    import importlib

    import src.config

    importlib.reload(src.config)
    from src.config import Config as ReloadedConfig

    # Должно пройти без ошибок
    ReloadedConfig.validate()


@patch.dict(
    os.environ,
    {
        "DB_NAME": "test_db",
        "DB_USER": "test_user",
        "DB_PASSWORD": "test_pass",
        "DB_HOST": "test_host",
        "DB_PORT": "test_port",
    },
)
def test_config_validate_only_requires_three_vars() -> None:
    """Тест что validate требует только DB_NAME, DB_USER, DB_PASSWORD."""
    import importlib

    import src.config

    importlib.reload(src.config)
    from src.config import Config as ReloadedConfig

    # Проверяем, что все переменные установлены
    assert ReloadedConfig.DB_HOST == "test_host"
    assert ReloadedConfig.DB_PORT == "test_port"
    # validate требует только DB_NAME, DB_USER, DB_PASSWORD
    ReloadedConfig.validate()  # Должно пройти без ошибок


def test_config_companies_contains_specific_ids() -> None:
    """Тест что список COMPANIES содержит ожидаемые ID."""
    expected_ids = {
        3529,  # Сбер
        78638,  # Т-Банк
        1740,  # Яндекс
        3776,  # VK
        2180,  # Ozon
        87021,  # Wildberries
        85512,  # Avito
        84585,  # 2ГИС
        80,  # Альфа-Банк
        845,  # РЖД
        423,  # Ростелеком
        1122462,  # Skyeng
    }

    assert set(Config.COMPANIES) == expected_ids
    assert len(Config.COMPANIES) == len(expected_ids)


@patch.dict(
    os.environ,
    {
        "DB_NAME": "test_db",
        "DB_USER": "test_user",
        "DB_PASSWORD": "test_pass",
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
    },
)
def test_config_loads_env_variables_with_dotenv() -> None:
    """Тест загрузки переменных через python-dotenv."""
    import importlib

    import src.config

    importlib.reload(src.config)
    from src.config import Config as ReloadedConfig

    assert ReloadedConfig.DB_NAME == "test_db"
    assert ReloadedConfig.DB_USER == "test_user"
    assert ReloadedConfig.DB_PASSWORD == "test_pass"
    assert ReloadedConfig.DB_HOST == "localhost"
    assert ReloadedConfig.DB_PORT == "5432"
