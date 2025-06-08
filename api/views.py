from django.http import Http404
from rest_framework import generics
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .serializers import *
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

User = get_user_model()


class TestListView(generics.ListAPIView):
    serializer_class = TestSerializer
    permission_classes = [IsAuthenticated]
    queryset = Test.objects.all()


class TestDetailView(generics.RetrieveAPIView):
    serializer_class = TestSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        test_id = self.kwargs.get('test_id')
        return get_object_or_404(Test, id=test_id)


class QuestionListView(generics.ListAPIView):
    serializer_class = QuestionSerializer
    permission_classes = [IsAuthenticated]
    queryset = Question.objects.all()


class QuestionDetailView(generics.RetrieveAPIView):
    """
    Вью возвращающая ответы на конкретный вопрос.
    Суперпользователь может передать параметр user_id,
    и получить ответ другого пользователя
    """
    serializer_class = QuestionDetailSerializer
    permission_classes = [IsAuthenticated]
    queryset = Question.objects.all()
    lookup_field = 'id'


class QuestionUserAnswersView(generics.RetrieveAPIView):
    serializer_class = QuestionWithUserAnswersSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        question_id = self.kwargs['question_id']
        return get_object_or_404(Question, id=question_id)

    def get_queryset(self):
        request_user = self.request.user
        target_user_id = self.request.query_params.get('user_id')
        question = self.get_object()

        # Базовый queryset - все ответы на этот вопрос
        queryset = UserAnswer.objects.filter(
            question=question
        ).select_related('user', 'test').order_by('-created_at')

        # Если user_id не указан - возвращаем только свои ответы
        if not target_user_id:
            return queryset.filter(user=request_user)

        # Проверяем права (админ или запрашивает свои данные)
        target_user = get_object_or_404(User, id=target_user_id)
        if not (request_user.is_staff or request_user == target_user):
            raise PermissionDenied("У вас нет прав для просмотра результатов этого пользователя")

        return queryset.filter(user=target_user)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        # Если указан user_id - добавляем целевого пользователя в контекст
        target_user_id = self.request.query_params.get('user_id')
        if target_user_id:
            context['target_user'] = get_object_or_404(User, id=target_user_id)
        return context

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_QUERY,
                description="ID пользователя (только для админов)",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        question = self.get_object()
        answers = self.get_queryset()

        data = {
            'question': question,
            'answers': answers
        }

        serializer = self.get_serializer(data)
        return Response(serializer.data)


class UserTestsView(generics.ListAPIView):
    serializer_class = TestWithUserAnswersSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        request_user = self.request.user
        target_user_id = self.request.query_params.get('user_id')

        # Если user_id не указан — возвращаем свои тесты
        if not target_user_id:
            return Test.objects.filter(test_questions__question__useranswer__user=request_user).distinct()

        # Проверяем права (админ или запрашивает свои данные)
        target_user = get_object_or_404(User, id=target_user_id)
        if not (request_user.is_staff or request_user == target_user):
            raise PermissionDenied("У вас нет прав для просмотра результатов этого пользователя")

        return Test.objects.filter(test_questions__question__useranswer__user=target_user).distinct()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        # Если указан user_id — добавляем целевого пользователя в контекст
        target_user_id = self.request.query_params.get('user_id')
        if target_user_id:
            context['target_user'] = get_object_or_404(User, id=target_user_id)
        return context

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_QUERY,
                description="ID пользователя (только для админов)",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class UserTestDetailView(generics.RetrieveAPIView):
    serializer_class = TestWithUserAnswersSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        test_id = self.kwargs.get('test_id')
        target_user_id = self.request.query_params.get('user_id', self.request.user.id)
        target_user = get_object_or_404(User, id=target_user_id)

        # Проверка прав
        if not (self.request.user.is_staff or self.request.user == target_user):
            raise PermissionDenied("У вас нет прав для просмотра этого теста")

        test = get_object_or_404(Test, id=test_id)
        if not UserAnswer.objects.filter(user=target_user, test=test).exists():
            raise Http404("Пользователь еще не начинал этот тест")

        return test

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        target_user_id = self.request.query_params.get('user_id')
        if target_user_id:
            context['target_user'] = get_object_or_404(User, id=target_user_id)
        return context

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                'user_id',
                openapi.IN_QUERY,
                description="ID пользователя (только для админов)",
                type=openapi.TYPE_INTEGER,
                required=False
            ),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class UserAnswerCreateView(generics.CreateAPIView):
    serializer_class = UserAnswerCreateSerializer
    permission_classes = [IsAuthenticated]
    queryset = UserAnswer.objects.all()

    def perform_create(self, serializer):
        instance = serializer.save(user=self.request.user)
        test = instance.test

        # Обновляем результат теста
        test_result, _ = TestResult.objects.get_or_create(
            user=self.request.user,
            test=test,
            defaults={'score': 0, 'is_completed': False}
        )
        test_result.calculate_score()

    @swagger_auto_schema(
        operation_description="Сохранить ответ пользователя на вопрос",
        request_body=UserAnswerCreateSerializer,
        responses={
            201: "Ответ сохранен",
            400: "Неверные данные",
            403: "Доступ запрещен"
        }
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class SubmitTestAnswersView(generics.CreateAPIView):
    serializer_class = TestSubmissionSerializer
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Отправить ответы на тест и получить результаты",
        request_body=TestSubmissionSerializer
    )
    def create(self, request, *args, **kwargs):
        test_id = self.kwargs.get('test_id')
        user = request.user
        test = get_object_or_404(Test, id=test_id)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Сохраняем ответы пользователя
        for answer_data in serializer.validated_data['answers']:
            question_id = answer_data['question_id']
            answer = answer_data['answer']
            question = get_object_or_404(Question, id=question_id)

            if not TestQuestion.objects.filter(test=test, question=question).exists():
                return Response(
                    {"error": f"Вопрос с ID {question_id} не принадлежит тесту с ID {test_id}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            UserAnswer.objects.update_or_create(
                user=user,
                test=test,
                question=question,
                defaults={'answer': answer}
            )

        # Обновляем или создаем результат теста
        test_result, created = TestResult.objects.get_or_create(
            user=user,
            test=test,
            defaults={'score': 0, 'is_completed': True}
        )

        if not created:
            test_result.is_completed = True
            test_result.save()

        # Получаем и форматируем результаты
        raw_results = test_result.calculate_score()
        detailed_results = []

        for result in raw_results:
            question = result.get('question')
            detailed_results.append({
                "question_id": question.id if question else None,
                "question_text": question.text if question else "",
                "user_answer": result.get('user_answer', []),
                "correct_answer": result.get('correct_answer', []),
                "is_correct": result.get('is_correct', False),
                "question_type": question.type if hasattr(question, 'type') else
                question.question_type if hasattr(question, 'question_type') else
                "unknown"
            })

        # Формируем финальный ответ
        response_data = {
            "test_id": test.id,
            "test_title": test.title,
            "score": float(test_result.score) if test_result.score is not None else 0,
            "is_completed": test_result.is_completed,
            "completed_at": test_result.completed_at.isoformat() if test_result.completed_at else None,
            "detailed_results": detailed_results
        }

        return Response(response_data, status=status.HTTP_200_OK)