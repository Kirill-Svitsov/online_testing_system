from django.urls import path
from . import views

urlpatterns = [
    path('', views.hello_world, name='hello-world'),
    path('hello-drf/', views.hello_world_drf, name='hello-world-drf'),
]