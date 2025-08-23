from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

# Importar las vistas de error
from quizzes.views import custom_404_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('quizzes.urls')),
]

# Servir archivos media y static en desarrollo (también funciona con Daphne)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # En producción, asegurar que static y media funcionen
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Configurar handlers de error (funcionan tanto con DEBUG=True como DEBUG=False)
handler404 = 'quizzes.views.custom_404_view'
