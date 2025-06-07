from django.http import JsonResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

# Простая функция-представление на чистом Django
def hello_world(request):
    return JsonResponse({'message': 'Привет, это тестовая система квизов!'})

# Вариант с DRF (если используете Django REST Framework)
@api_view(['GET'])
def hello_world_drf(request):
    return Response({'message': 'Привет от DRF! Готов к квизам!'})
