from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Test(models.Model):
    """
    Модель теста
    """
    title = models.CharField(
        max_length=255,
        unique=True,
        verbose_name='Название теста'
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Описание теста'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Тест'
        verbose_name_plural = 'Тесты'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class Question(models.Model):
    """
    Модель вопроса
    """
    QUESTION_TYPES = (
        ('single', 'Один правильный ответ'),
        ('multiple', 'Несколько правильных ответов'),
        ('text', 'Текстовый ответ'),
    )
    text = models.TextField(verbose_name='Текст вопроса')
    question_type = models.CharField(
        max_length=10,
        choices=QUESTION_TYPES,
        verbose_name='Тип вопроса'
    )
    choices = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Варианты ответов',
        help_text='JSON-массив вариантов для single/multiple вопросов'
    )
    correct_answers = models.JSONField(
        blank=True,
        null=True,
        verbose_name='Правильные ответы',
        help_text='JSON-массив правильных ответов'
    )

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'

    def __str__(self):
        return self.text[:20] + '...' if len(self.text) > 20 else self.text


class TestQuestion(models.Model):
    """
    Промежуточная модель для определения позиции вопроса в тесте.
    Автоматически смещает вопросы при конфликте порядка.
    """
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name='test_questions')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='question_tests')
    order = models.PositiveSmallIntegerField(default=0, verbose_name='Порядковый номер')

    class Meta:
        ordering = ['order']
        unique_together = ['test', 'question']
        verbose_name = 'Вопрос в тесте'
        verbose_name_plural = 'Вопросы в тестах'

    def __str__(self):
        return f"Вопрос {self.question.id} в тесте {self.test.id} (порядок: {self.order})"

    def save(self, *args, **kwargs):
        """
        Реализована проверка на случай, если в существующий тест хотят добавить вопрос на позицию,
        которая уже занята. В таком случае добавляемый вопрос встанет на указанную позицию,
        остальные вопросы сместятся на 1 вправо.
        :param args:
        :param kwargs:
        :return:
        """
        # Проверяем, существует ли уже вопрос с таким порядком в этом тесте
        conflicting_questions = TestQuestion.objects.filter(
            test=self.test,
            order=self.order
        ).exclude(pk=self.pk if self.pk else None)
        if conflicting_questions.exists():
            # Находим максимальный порядковый номер в этом тесте
            max_order = TestQuestion.objects.filter(
                test=self.test
            ).aggregate(models.Max('order'))['order__max'] or 0

            # Смещаем все вопросы, начиная с текущего порядка
            questions_to_update = TestQuestion.objects.filter(
                test=self.test,
                order__gte=self.order
            ).exclude(pk=self.pk if self.pk else None)
            updated_questions = []
            for q in questions_to_update:
                q.order += 1
                updated_questions.append(q)
            TestQuestion.objects.bulk_update(updated_questions, ['order'])
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Реализована проверка на случай, если из существующего теста хотят удалить вопрос.
        В таком случае вопросы, стоящие после удаляемого смещаются влево.
        :param args:
        :param kwargs:
        :return:
        """
        test_id = self.test_id
        order = self.order
        super().delete(*args, **kwargs)
        questions_to_update = TestQuestion.objects.filter(
            test_id=test_id,
            order__gt=order
        )
        updated_questions = []
        for q in questions_to_update:
            q.order -= 1
            updated_questions.append(q)
        TestQuestion.objects.bulk_update(updated_questions, ['order'])


class UserAnswer(models.Model):
    """
    Модель ответа пользователя
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        verbose_name='Тест'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        verbose_name='Вопрос'
    )
    answer = models.JSONField(verbose_name='Ответ пользователя')
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата ответа'
    )

    class Meta:
        verbose_name = 'Ответ пользователя'
        verbose_name_plural = 'Ответы пользователей'
        unique_together = ['user', 'test', 'question']

    def __str__(self):
        return f"Ответ {self.user.username} на вопрос #{self.question.order} в тесте '{self.test.title}'"


class TestResult(models.Model):
    """
    Модель результатов тестирования
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь'
    )
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        verbose_name='Тест'
    )
    score = models.FloatField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        verbose_name='Результат в %'
    )
    completed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата завершения'
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name='Тест завершен'
    )

    class Meta:
        verbose_name = 'Результат теста'
        verbose_name_plural = 'Результаты тестов'
        unique_together = ['user', 'test']

    def __str__(self):
        return f"Результат {self.user.username} по тесту '{self.test.title}': {self.score}%"

    def calculate_score(self):
        """
        Метод для подсчета правильных ответов
        """
        total_questions = self.test.questions.count()
        if total_questions == 0:
            self.score = 0
            self.save()
            return 0

        correct_answers = 0
        user_answers = UserAnswer.objects.filter(
            user=self.user,
            test=self.test
        ).select_related('question')
        for user_answer in user_answers:
            question = user_answer.question
            if question.question_type in ['single', 'multiple']:
                if set(user_answer.answer) == set(question.correct_answers):
                    correct_answers += 1
                    user_answer.is_correct = True
                else:
                    user_answer.is_correct = False
                user_answer.save()
            # Для текстовых ответов учитываем только проверенные вручную
            elif question.question_type == 'text' and user_answer.is_verified and user_answer.is_correct:
                correct_answers += 1

        self.score = round((correct_answers / total_questions) * 100, 2)
        self.is_completed = True
        self.save()
        return self.score
