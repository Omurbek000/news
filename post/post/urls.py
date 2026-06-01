# from django.conf import settings
# from django.conf.urls.static import static
# from django.contrib import admin
# from django.urls import include, path


# from drf_spectacular.views import (
#     SpectacularAPIView,
#     SpectacularSwaggerView,
#     SpectacularRedocView,
# )

# urlpatterns = [
#     # ── Admin ─────────────────────────────────────────────
#     path("admin/", admin.site.urls),

#     # ── API (blog приложение) ─────────────────────────────
#     path('api/', include('blog.urls')),

#     # ── OpenAPI Schema ────────────────────────────────────
#     path("api/schema/", SpectacularAPIView.as_view(), name="schema"),

#     # ── Swagger UI ─────────────────────────────────────────
#     path("swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),

#     # ── ReDoc (опционально) ───────────────────────────────
#     path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
# ]

# # Медиа-файлы в режиме разработки
# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('blog.urls')),   # все маршруты блога будут доступны по /api/...
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)