"""URL configuration for UniRV_Django project."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # django-health-check — library-based checks (DB, Redis, storage)
    path("ht/", include("health_check.urls")),
    # django-anymail — inbound/tracking webhooks
    path("anymail/", include("anymail.urls")),
    path("admin/", admin.site.urls),
    path("", include("editais.urls")),
]

# Silk profiling panel (only when enabled)
if getattr(settings, "ENABLE_SILK", False):
    urlpatterns += [path("silk/", include("silk.urls", namespace="silk"))]

# Include django_browser_reload URLs only in DEBUG mode and not during testing
if settings.DEBUG and not getattr(settings, "TESTING", False):
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
    # Serve media files in DEBUG mode (thumbnails, user uploads)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
