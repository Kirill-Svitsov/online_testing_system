from django.contrib import admin
from django.urls import path, include
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="Quizzes API",
        default_version='v1',
        description="Online testing system",
    ),
    public=True,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('quizzes.urls', namespace='quizzes')),
    # Апи добавим позже.
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0)),
]
