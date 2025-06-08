from django.core.management.base import BaseCommand
from quizzes.services.csv_importer import CSVTestImporter
import os


class Command(BaseCommand):
    """
        Django management-команда для импорта тестов из CSV-файлов.

        Команда позволяет загружать тесты и вопросы из CSV-файлов в базу данных.
        Должна выполняться внутри Docker-контейнера командой:
        docker exec -it online_testing_system-quizzes_web-1 bash
        python3 manage.py import_tests path/to/tests.csv

        Основные возможности:
        - Проверяет существование указанного CSV-файла
        - Обрабатывает файл через сервис CSVTestImporter
        - Поддерживает как создание новых тестов, так и обновление существующих
        - Предоставляет обратную связь о процессе импорта через stdout/stderr

        Примеры использования:
        1. Базовый импорт:
           python3 manage.py import_tests /app/data/tests.csv

        2. Импорт с обновлением существующих тестов:
           python3 manage.py import_tests /app/data/tests.csv --update

        Обработка ошибок:
        - Сообщает если файл не найден
        - Отлавливает и выводит любые исключения при обработке
    """
    help = 'Импорт тестов и вопросов из CSV файла'

    def add_arguments(self, parser):
        """
        Добавляет аргументы для командной строки.

        Args:
            parser: Парсер аргументов, к которому добавляются параметры.

        Определенные аргументы:
            csv_file (str): Обязательный. Путь к CSV-файлу с тестами.
            --update (флаг): Опциональный. Если указан, существующие тесты
                             будут обновляться вместо пропуска.
        """
        parser.add_argument('csv_file', type=str, help='Путь к CSV файлу с тестами')
        parser.add_argument('--update', action='store_true', help='Обновлять существующие тесты')

    def handle(self, *args, **options):
        """
        Основной метод выполнения команды.

        Логика работы:
        1. Проверяет существование CSV-файла
        2. Открывает файл с кодировкой UTF-8-SIG (поддерживает BOM)
        3. Инициализирует CSVTestImporter с флагом обновления
        4. Обрабатывает файл и выводит результаты

        Args:
            *args: Произвольные позиционные аргументы.
            **options: Именованные аргументы с параметрами команды.

        Поведение:
            - Выводит ошибки в stderr если:
              - Файл не найден
              - Возникают исключения при обработке
            - Выводит сообщение об успехе в stdout по завершении
              с количеством созданных/обновленных тестов
        """
        csv_path = options['csv_file']
        if not os.path.exists(csv_path):
            self.stderr.write(self.style.ERROR(f"Файл не найден: {csv_path}"))
            return

        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as file:
                importer = CSVTestImporter(update_existing=options['update'])
                created_count = importer.process_csv(file)
                self.stdout.write(self.style.SUCCESS(f"Успешно обработано! Создано/обновлено тестов: {created_count}"))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Ошибка: {str(e)}"))
