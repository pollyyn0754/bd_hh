import sys
from src.api import HeadHunterAPI
from src.db_manager import DBManager
from src.config import Config
from src.utils import create_database, format_salary


def print_header(title: str):
    """Выводит заголовок раздела."""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def print_vacancies(vacancies: list):
    """Красивый вывод списка вакансий."""
    if not vacancies:
        print("  Вакансии не найдены.")
        return

    for i, vac in enumerate(vacancies, 1):
        # Распаковываем кортеж в зависимости от того, какой метод его вернул
        if len(vac) == 5:
            company, name, salary_from, salary_to, url = vac
            salary_str = format_salary({'from': salary_from, 'to': salary_to, 'currency': 'руб'})
        else:
            # Запасной вариант, если структура изменится
            print(vac)
            continue

        print(f"{i}. {company} — {name}")
        print(f"   Зарплата: {salary_str}")
        print(f"   Ссылка: {url}\n")


def main():
    """Главная функция программы."""
    print_header("ПАРСЕР ВАКАНСИЙ С HH.RU")

    # 1. Валидация конфигурации
    try:
        Config.validate()
    except ValueError as e:
        print(f"Ошибка конфигурации: {e}")
        print("Пожалуйста, создайте и заполните файл .env на основе .env.example")
        sys.exit(1)

    # 2. Создание базы данных
    print("Шаг 1. Подготовка базы данных...")
    create_database(
        Config.DB_NAME,
        Config.DB_USER,
        Config.DB_PASSWORD,
        Config.DB_HOST,
        Config.DB_PORT
    )

    # 3. Инициализация менеджера БД и создание таблиц
    db_manager = DBManager(
        Config.DB_NAME,
        Config.DB_USER,
        Config.DB_PASSWORD,
        Config.DB_HOST,
        Config.DB_PORT
    )
    db_manager.create_tables()
    print("✓ База данных и таблицы готовы.")

    # 4. Загрузка данных с hh.ru
    print("\nШаг 2. Загрузка данных о компаниях и вакансиях...")
    hh_api = HeadHunterAPI()

    for company_id in Config.COMPANIES:
        print(f"\nОбработка компании ID: {company_id}...")
        try:
            # Получаем и сохраняем информацию о компании
            company = hh_api.get_employer(company_id)
            if not company:
                print(f"  Не удалось получить данные о компании {company_id}, пропускаем...")
                continue

            db_manager.insert_company(company)
            print(f"  ✓ Компания: {company.get('name')}")

            # Получаем и сохраняем все вакансии компании
            vacancies = hh_api.get_all_vacancies_from_employer(company_id)
            vac_count = 0
            for vacancy in vacancies:
                db_manager.insert_vacancy(vacancy)
                vac_count += 1

            print(f"  ✓ Загружено вакансий: {vac_count}")

        except Exception as e:
            print(f"  ✗ Ошибка при обработке компании {company_id}: {e}")

    print("\n✓ Загрузка данных завершена.")

    # 5. Взаимодействие с пользователем
    while True:
        print_header("ГЛАВНОЕ МЕНЮ")
        print("1. Список компаний и количество вакансий")
        print("2. Список всех вакансий")
        print("3. Средняя зарплата")
        print("4. Вакансии с зарплатой выше средней")
        print("5. Поиск вакансий по ключевому слову")
        print("0. Выход")

        choice = input("\nВыберите действие: ").strip()

        if choice == '1':
            print_header("КОМПАНИИ И КОЛИЧЕСТВО ВАКАНСИЙ")
            companies = db_manager.get_companies_and_vacancies_count()
            for company, count in companies:
                print(f"• {company}: {count} вакансий")

        elif choice == '2':
            print_header("ВСЕ ВАКАНСИИ")
            vacancies = db_manager.get_all_vacancies()
            print_vacancies(vacancies[:20])  # Показываем только первые 20
            if len(vacancies) > 20:
                print(f"... и еще {len(vacancies) - 20} вакансий (всего {len(vacancies)})")

        elif choice == '3':
            print_header("СРЕДНЯЯ ЗАРПЛАТА")
            avg = db_manager.get_avg_salary()
            print(f"Средняя зарплата по всем вакансиям: {avg} руб.")

        elif choice == '4':
            print_header("ВАКАНСИИ С ЗАРПЛАТОЙ ВЫШЕ СРЕДНЕЙ")
            vacancies = db_manager.get_vacancies_with_higher_salary()
            print_vacancies(vacancies)

        elif choice == '5':
            keyword = input("Введите ключевое слово для поиска: ").strip().lower()
            if keyword:
                print_header(f"ПОИСК ПО КЛЮЧЕВОМУ СЛОВУ: {keyword}")
                vacancies = db_manager.get_vacancies_with_keyword(keyword)
                print_vacancies(vacancies)
            else:
                print("Ключевое слово не может быть пустым.")

        elif choice == '0':
            print("До свидания!")
            db_manager.disconnect()
            sys.exit(0)

        else:
            print("Неверный выбор. Пожалуйста, введите число от 0 до 5.")

        input("\nНажмите Enter, чтобы продолжить...")


if __name__ == "__main__":
    main()