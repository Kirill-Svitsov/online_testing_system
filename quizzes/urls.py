from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'quizzes'

urlpatterns = [
    path('', views.AllTestsView.as_view(), name='home'),
    path('quizzes/<int:pk>/', views.quizz_detail, name='detail'),
    path('quizzes/<int:pk>/result/', views.quizz_result, name='test_result'),
    path('quizzes/completed/', views.CompletedTestsView.as_view(), name='completed_tests'),
    path('upload-csv/', views.UploadCSVView.as_view(), name='upload_csv'),
    path('search/', views.search_tests, name='search'),
    path('login/', auth_views.LoginView.as_view(template_name='quizzes/auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
]
