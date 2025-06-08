import csv
from io import TextIOWrapper
from django.db import transaction
from quizzes.models import Test, Question, TestQuestion


class CSVTestImporter:
    REQUIRED_FIELDS = ['test_title', 'question_text', 'question_type', 'choices', 'correct_answers']

    def __init__(self, update_existing=False):
        self.update_existing = update_existing
        self.stats = {
            'tests_created': 0,
            'tests_updated': 0,
            'questions_created': 0,
            'questions_reused': 0,
            'questions_removed': 0,
            'duplicates_resolved': 0
        }

    def process_csv(self, file):
        """Основной метод для обработки CSV."""
        if isinstance(file, TextIOWrapper):
            reader = csv.DictReader(file, delimiter=';')
        else:
            reader = csv.DictReader(file.read().decode('utf-8-sig').splitlines(), delimiter=';')

        with transaction.atomic():
            # Группируем вопросы по тестам
            tests_data = {}
            for row in reader:
                self._validate_row(row)
                test_title = row['test_title'].strip()
                if test_title not in tests_data:
                    tests_data[test_title] = {
                        'description': row.get('test_description', '').strip(),
                        'questions': []
                    }

                question_data = {
                    'text': row['question_text'].strip(),
                    'type': row['question_type'].strip(),
                    'choices': sorted([c.strip() for c in row['choices'].split('|')]),
                    'correct_answers': sorted([c.strip() for c in row['correct_answers'].split('|')]),
                    'order': int(row.get('question_order', 0)) if str(row.get('question_order', 0)).isdigit() else 0
                }
                tests_data[test_title]['questions'].append(question_data)

            # Обрабатываем каждый тест
            for test_title, data in tests_data.items():
                test, created = self._process_test(test_title, data['description'])

                if created:
                    self.stats['tests_created'] += 1
                else:
                    self.stats['tests_updated'] += 1
                    if self.update_existing:
                        self._cleanup_old_questions(test, data['questions'])

                # Обрабатываем вопросы теста
                for q_data in data['questions']:
                    question = self._process_question(q_data)
                    self._link_test_question(test, question, q_data['order'])

        return self.stats

    def _cleanup_old_questions(self, test, new_questions):
        """Удаляет вопросы, которых нет в новых данных."""
        # Получаем уникальные идентификаторы новых вопросов
        new_question_ids = set()
        for q in new_questions:
            existing = Question.objects.filter(
                text=q['text'],
                question_type=q['type'],
                choices=q['choices'],
                correct_answers=q['correct_answers']
            ).first()  # Берем первый попавшийся дубликат
            if existing:
                new_question_ids.add(existing.id)

        # Находим вопросы теста, которых нет в новых данных
        old_test_questions = TestQuestion.objects.filter(test=test).exclude(
            question_id__in=new_question_ids
        )

        # Удаляем связки тест-вопрос и сами вопросы, если они больше нигде не используются
        for tq in old_test_questions:
            question = tq.question
            tq.delete()
            if not TestQuestion.objects.filter(question=question).exists():
                question.delete()
                self.stats['questions_removed'] += 1

    def _process_question(self, q_data):
        """Создает или находит существующий вопрос."""
        # Ищем все подходящие вопросы (может быть несколько дубликатов)
        existing_questions = Question.objects.filter(
            text=q_data['text'],
            question_type=q_data['type'],
            choices=q_data['choices'],
            correct_answers=q_data['correct_answers']
        ).order_by('id')  # Сортируем по ID для детерминированности

        if existing_questions.exists():
            # Если нашли дубликаты - берем самый старый вопрос
            question = existing_questions.first()

            # Если дубликатов несколько - отмечаем в статистике
            if existing_questions.count() > 1:
                self.stats['duplicates_resolved'] += existing_questions.count() - 1

            self.stats['questions_reused'] += 1
            return question
        # Если вопрос не найден - создаем новый
        question = Question.objects.create(
            text=q_data['text'],
            question_type=q_data['type'],
            choices=q_data['choices'],
            correct_answers=q_data['correct_answers']
        )
        self.stats['questions_created'] += 1
        return question

    def _validate_row(self, row):
        """Проверяет, что в строке есть все обязательные поля."""
        missing_fields = [f for f in self.REQUIRED_FIELDS if f not in row]
        if missing_fields:
            raise ValueError(f"Отсутствуют обязательные поля: {', '.join(missing_fields)}")

    def _process_test(self, test_title, description):
        """Создает или обновляет тест."""
        defaults = {'description': description}
        if self.update_existing:
            return Test.objects.update_or_create(
                title=test_title,
                defaults=defaults
            )
        return Test.objects.get_or_create(
            title=test_title,
            defaults=defaults
        )

    def _link_test_question(self, test, question, order):
        """Связывает тест и вопрос."""
        TestQuestion.objects.get_or_create(
            test=test,
            question=question,
            defaults={'order': order}
        )