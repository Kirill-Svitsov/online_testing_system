from django.urls import path
from .views import (
    TestListView,
    TestDetailView,
    QuestionListView, QuestionDetailView, QuestionUserAnswersView, UserTestsView, UserTestDetailView,
    UserAnswerCreateView, SubmitTestAnswersView,
)

urlpatterns = [
    path('quizzes/api/v1/', TestListView.as_view(), name='test-list'),
    path('quizzes/api/v1/<int:test_id>/', TestDetailView.as_view(), name='test-detail'),
    path('quizzes/api/v1/questions/', QuestionListView.as_view(), name='question-list'),
    path('quizzes/api/v1/questions/<int:id>/', QuestionDetailView.as_view(), name='question-detail'),
    path('quizzes/api/v1/questions/<int:question_id>/user-answers/', QuestionUserAnswersView.as_view(),
         name='question-user-answers'),
    path('quizzes/api/v1/user/tests/', UserTestsView.as_view(), name='user-tests'),
    path('quizzes/api/v1/user/tests/<int:test_id>/', UserTestDetailView.as_view(), name='user-test-detail'),
    path(
        'quizzes/api/v1/save-answer/',
        UserAnswerCreateView.as_view(),
        name='save-answer'
    ),
    path(
        'quizzes/api/v1/submit-test-answers/<int:test_id>/',
        SubmitTestAnswersView.as_view(),
        name='submit-test-answers'
    ),
]
