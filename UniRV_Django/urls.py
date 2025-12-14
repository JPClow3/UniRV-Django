"""URL configuration for UniRV_Django project."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('editais.urls')),
]

# Include django_browser_reload URLs only in DEBUG mode and not during testing
# TESTING mode disables django_browser_reload to avoid namespace issues in test environment
if settings.DEBUG and not getattr(settings, 'TESTING', False):
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
    # Serve media files in DEBUG mode (thumbnails, user uploads)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
