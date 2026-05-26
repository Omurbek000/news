from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

# from django.views.generic import TemplateView

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

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────
    path("auth/register/", views.RegisterView.as_view(), name="register"),
    path("auth/login/", views.LoginView.as_view(), name="login"),
    path("auth/logout/", views.LogoutView.as_view(), name="logout"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/change-password/", views.ChangePasswordView.as_view(), name="change_password"),
    
    # path('test/', TemplateView.as_view(template_name='test_api.html')),

    # ── Users ─────────────────────────────────────────────
    path("users/me/", views.MeView.as_view(), name="me"),
    path("users/<int:pk>/", views.UserProfileView.as_view(), name="user_profile"),

    # ── Router (posts, comments, categories, favorites, messages) ──
    path("", include(router.urls)),
]
