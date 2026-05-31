from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from django.conf import settings
from django.conf.urls.static import static

from . import views

router = DefaultRouter()
router.register(r"categories", views.CategoryViewSet, basename="category")
router.register(r"posts", views.PostViewSet, basename="post")
router.register(
    r"posts/(?P<post_pk>[^/.]+)/comments",
    views.CommentViewSet,
    basename="comment",
)
router.register(r"favorites", views.FavoriteViewSet, basename="favorite")
router.register(r"messages", views.MessageViewSet, basename="message")

# Основные маршруты API (без префикса /api/, так как он добавлен в корневом urls.py)
urlpatterns = [
    # Auth
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/change-password/", views.ChangePasswordView.as_view(), name="change_password"),

    # Users
    path("users/me/", views.MeView.as_view(), name="me"),
    path("users/<int:pk>/", views.UserProfileView.as_view(), name="user_profile"),

    # Router (posts, comments, categories, favorites, messages)
    path("", include(router.urls)),
]

# Swagger/ReDoc – вынесены отдельно (чтобы не мешались, но можно оставить)
if settings.DEBUG:
    urlpatterns += [
        path("schema/", SpectacularAPIView.as_view(), name="schema"),
        path("swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
        path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)