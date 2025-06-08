import json

from rest_framework import serializers
from quizzes.models import Test, Question, TestQuestion, UserAnswer, TestResult
from django.contrib.auth import get_user_model

User = get_user_model()


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'choices', 'correct_answers']


class QuestionDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'choices', 'correct_answers']


class TestQuestionSerializer(serializers.ModelSerializer):
    question = QuestionSerializer()

    class Meta:
        model = TestQuestion
        fields = ['order', 'question']


class TestSerializer(serializers.ModelSerializer):
    questions = TestQuestionSerializer(source='test_questions', many=True)

    class Meta:
        model = Test
        fields = ['id', 'title', 'description', 'questions']


class QuestionWithUserAnswersSerializer(serializers.Serializer):
    """
    Сериализатор вопроса, с ответами пользователя.
    """
    question = serializers.SerializerMethodField()
    user_answers = serializers.SerializerMethodField()

    def get_question(self, obj):
        return {
            'id': obj['question'].id,
            'text': obj['question'].text,
            'correct_answers': obj['question'].correct_answers,
            'question_type': obj['question'].question_type
        }

    def get_user_answers(self, obj):
        return [
            {
                'user_id': answer.user.id,
                'username': answer.user.username,
                'answer': answer.answer,
                'created_at': answer.created_at,
                'test_id': answer.test.id,
                'test_title': answer.test.title
            }
            for answer in obj['answers']
        ]


class UserAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnswer
        fields = ['question', 'answer', 'created_at']


class TestWithUserAnswersSerializer(serializers.ModelSerializer):
    """
    Сериализатор теста с ответами пользователя на вопросы.
    """
    questions = serializers.SerializerMethodField()
    user_answers = serializers.SerializerMethodField()
    test_result = serializers.SerializerMethodField()
    user_id = serializers.IntegerField(source='user.id', read_only=True)

    class Meta:
        model = Test
        fields = ['id', 'title', 'description', 'questions', 'user_answers', 'test_result', 'user_id']

    def get_questions(self, obj):
        questions = obj.test_questions.all().order_by('order').select_related('question')
        return TestQuestionSerializer(questions, many=True).data

    def get_user_answers(self, obj):
        user = self.context.get('target_user', self.context['request'].user)
        answers = UserAnswer.objects.filter(user=user, test=obj).select_related('question')
        return UserAnswerSerializer(answers, many=True).data

    def get_test_result(self, obj):
        user = self.context.get('target_user', self.context['request'].user)
        result = TestResult.objects.filter(user=user, test=obj).first()
        if result:
            return {
                'score': result.score,
                'is_completed': result.is_completed,
                'completed_at': result.completed_at
            }
        return None


class UserAnswerCreateSerializer(serializers.ModelSerializer):
    """
    Сериализатор для записи ответа на вопрос пользователя.
    """
    answer = serializers.ListField(
        child=serializers.CharField(),
        help_text="Список строковых ответов (даже для одного ответа)"
    )

    class Meta:
        model = UserAnswer
        fields = ['test', 'question', 'answer']

    def validate_answer(self, value):
        """Дополнительная валидация ответов"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Ответ должен быть списком")
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        test = validated_data['test']
        question = validated_data['question']
        answer = validated_data['answer']

        # Убедимся, что answer - это список
        if not isinstance(answer, list):
            answer = [answer]

        # Ищем существующий ответ
        instance, created = UserAnswer.objects.get_or_create(
            user=user,
            test=test,
            question=question,
            defaults={'answer': answer}
        )

        # Если ответ уже существовал - обновляем его
        if not created:
            instance.answer = answer
            instance.save()

        return instance


class TestAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    answer = serializers.ListField(
        child=serializers.CharField(),
        help_text="Массив ответов"
    )


class TestSubmissionSerializer(serializers.Serializer):
    """
    Сериализатор отправки ответов на тест пользователем.
    """
    answers = TestAnswerSerializer(many=True)

    def create(self, validated_data):
        # Логика создания уже реализована во вьюсете,
        # поэтому здесь можно просто вернуть пустой словарь
        return {}
