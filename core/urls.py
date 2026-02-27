from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    # Admin Django
    path('admin/', admin.site.urls),

    # Todas as rotas do app
    path('', include('myapp.urls')),
]


# Servir imagens durante desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)