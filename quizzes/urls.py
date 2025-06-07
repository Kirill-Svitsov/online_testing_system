from django.urls import path
from . import views

app_name = 'quizzes'

urlpatterns = [
    path('', views.AllTestsView.as_view(), name='home'),
    path('quizzes/<int:pk>/', views.quizz_detail, name='detail'),
    path('quizzes/<int:pk>/result/', views.quizz_result, name='test_result'),
    path('quizzes/completed/', views.CompletedTestsView.as_view(), name='completed_tests'),
    path('search/', views.search_tests, name='search'),
]
