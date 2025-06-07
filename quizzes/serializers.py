from rest_framework import serializers
from .models import Test, Question, UserAnswer, TestResult, TestQuestion


class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = ['id', 'title', 'description', 'created_at']


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = ['id', 'text', 'question_type', 'choices']


class TestQuestionSerializer(serializers.ModelSerializer):
    question = QuestionSerializer()

    class Meta:
        model = TestQuestion
        fields = ['order', 'question']


class UserAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnswer
        fields = ['question', 'answer', 'is_verified', 'is_correct']
        read_only_fields = ['is_verified', 'is_correct']

    def validate_answer(self, value):
        question_id = self.context.get('question_id')
        if not question_id:
            raise serializers.ValidationError("Question ID is required in context.")
        question = Question.objects.get(id=question_id)
        if question.question_type == 'single':
            if not isinstance(value, str):
                raise serializers.ValidationError("Для вопроса с одним ответом требуется строковый ответ.")
        elif question.question_type == 'multiple':
            if not isinstance(value, list):
                raise serializers.ValidationError("Для вопроса с несколькими ответами требуется список ответов.")
        elif question.question_type == 'text':
            if not isinstance(value, str):
                raise serializers.ValidationError("Для текстового вопроса требуется строковый ответ.")
        return value


class TestResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestResult
        fields = ['test', 'score', 'completed_at', 'is_completed']
        read_only_fields = ['score', 'completed_at', 'is_completed']
