from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
import mimetypes

# Register audio/video MIME types that Windows may not know
mimetypes.add_type('audio/webm', '.webm', strict=True)
mimetypes.add_type('audio/ogg', '.ogg', strict=True)
mimetypes.add_type('audio/mp4', '.m4a', strict=True)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
    path('', include('tickets.urls')),
    path('', include('messaging.urls')),
]

# Serve media files in all environments
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Static files in dev only (production uses whitenoise)
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
