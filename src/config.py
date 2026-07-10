import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Класс для хранения конфигурационных параметров."""

    # Параметры базы данных (берутся из .env файла)
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")  # Значение по умолчанию
    DB_PORT = os.getenv("DB_PORT")

    # Список ID компаний для парсинга (более 10, включая Сбер и Т-Банк)
    COMPANIES = [
        3529,  # Сбер
        78638,  # Т-Банк (Тинькофф)
        1740,  # Яндекс
        3776,  # VK (Mail.ru Group)
        2180,  # Ozon
        87021,  # Wildberries
        85512,  # Avito
        84585,  # 2ГИС
        80,  # Альфа-Банк
        845,  # РЖД
        423,  # Ростелеком
        1122462,  # Skyeng
    ]

    # Проверка, что все необходимые переменные окружения заданы
    @classmethod
    def validate(cls) -> None:
        if not all([cls.DB_NAME, cls.DB_USER, cls.DB_PASSWORD]):
            raise ValueError("Не все переменные окружения для БД заданы в файле .env")
