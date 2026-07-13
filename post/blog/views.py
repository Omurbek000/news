from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Category, Comment, CommentLike, Favorite, Message, Post, User
from .permissions import (
    IsAdminOrReadOnly,
    IsAuthorOrReadOnly,
    IsOwner,
    IsOwnerOrReadOnly,
    IsSenderOrRecipient,
)
from .serializers import (
    CategorySerializer,
    ChangePasswordSerializer,
    CommentSerializer,
    FavoriteSerializer,
    LoginSerializer,
    MessageListSerializer,
    MessageSerializer,
    PostCreateUpdateSerializer,
    PostDetailSerializer,
    PostListSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
)


# ───────────────────────────── AUTH ─────────────────────────────

class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — регистрация."""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(generics.GenericAPIView):
    """POST /api/auth/login/ — вход, возвращает access + refresh токены."""
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    """POST /api/auth/logout/ — выход, помещает refresh-токен в blacklist."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            token = RefreshToken(request.data["refresh"])
            token.blacklist()
            return Response(
                {"detail": "Вы успешно вышли из системы."},
                status=status.HTTP_205_RESET_CONTENT,
            )
        except Exception:
            return Response(
                {"detail": "Неверный или уже использованный токен."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ChangePasswordView(generics.UpdateAPIView):
    """PUT /api/auth/change-password/ — смена пароля."""
    serializer_class = ChangePasswordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def update(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"detail": "Пароль успешно изменён."},
            status=status.HTTP_200_OK,
        )


# ───────────────────────────── USER ─────────────────────────────

class UserProfileView(generics.RetrieveAPIView):
    """GET /api/users/<id>/ — публичный профиль любого пользователя."""
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.AllowAny]


class MeView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/users/me/ — свой профиль.
    PUT    /api/users/me/ — редактировать профиль.
    PATCH  /api/users/me/ — частично редактировать.
    DELETE /api/users/me/ — удалить аккаунт.
    """
    permission_classes = [IsOwner]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserProfileSerializer

    def perform_destroy(self, instance):
        instance.delete()


# ─────────────────────────── CATEGORY ───────────────────────────

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    GET /api/categories/      — список категорий (все).
    GET /api/categories/<id>/ — одна категория (все).
    Создание/удаление — только через /admin/ (IsAdminOrReadOnly).
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


# ──────────────────────────── POST ──────────────────────────────

class PostViewSet(viewsets.ModelViewSet):
    """Посты: список, создание, детали, обновление, удаление, мои посты."""
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "status", "author"]
    search_fields = ["title", "text"]
    ordering_fields = ["created_at", "views"]
    ordering = ["-created_at"]

    def get_queryset(self):
        if self.action == "my":
            return Post.objects.filter(author=self.request.user)
        return Post.objects.filter(status="published").select_related(
            "author", "category"
        )

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return PostCreateUpdateSerializer
        if self.action == "retrieve":
            return PostDetailSerializer
        return PostListSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        if self.action == "create":
            return [permissions.IsAuthenticated()]
        # update / partial_update / destroy — только автор поста
        return [IsAuthorOrReadOnly()]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        Post.objects.filter(pk=instance.pk).update(views=F("views") + 1)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=["get"],
        permission_classes=[permissions.IsAuthenticated],
    )
    def my(self, request):
        """GET /api/posts/my/ — все мои посты включая черновики."""
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# ─────────────────────────── COMMENT ────────────────────────────

class CommentViewSet(viewsets.ModelViewSet):
    """Комментарии к конкретному посту (вложенный роутер)."""
    serializer_class = CommentSerializer
    permission_classes = [IsAuthorOrReadOnly]

    def get_queryset(self):
        return Comment.objects.filter(
            post_id=self.kwargs["post_pk"],
            parent=None,
        ).select_related("author")

    def perform_create(self, serializer):
        post = get_object_or_404(Post, pk=self.kwargs["post_pk"])
        serializer.save(author=self.request.user, post=post)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None, post_pk=None):
        """POST /api/posts/<post_pk>/comments/<id>/like/ — лайк/анлайк комментария."""
        comment = get_object_or_404(Comment, pk=pk, post_id=post_pk)
        like, created = CommentLike.objects.get_or_create(user=request.user, comment=comment)
        if not created:
            like.delete()
            return Response({"detail": "Лайк убран.", "is_liked": False, "likes_count": comment.likes.count()})
        return Response({"detail": "Лайк поставлен.", "is_liked": True, "likes_count": comment.likes.count()})


# ─────────────────────────── FAVORITE ───────────────────────────

class FavoriteViewSet(viewsets.GenericViewSet):
    """Избранные посты текущего пользователя."""
    serializer_class = FavoriteSerializer
    permission_classes = [IsOwnerOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Favorite.objects.filter(user=self.request.user).select_related("post")
        return Favorite.objects.none()

    def list(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        favorite = get_object_or_404(Favorite, pk=pk, user=request.user)
        self.check_object_permissions(request, favorite)
        favorite.delete()
        return Response(
            {"detail": "Пост убран из избранного."},
            status=status.HTTP_204_NO_CONTENT,
        )


# ─────────────────────────── MESSAGE ────────────────────────────

class MessageViewSet(viewsets.GenericViewSet):
    """Личные сообщения: список диалогов, переписка, отправка, пометка прочитанным."""
    permission_classes = [IsSenderOrRecipient]

    def get_serializer_class(self):
        if self.action == "list":
            return MessageListSerializer
        return MessageSerializer

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Message.objects.filter(
                Q(sender=self.request.user) | Q(recipient=self.request.user)
            )
        return Message.objects.none()

    def list(self, request):
        """Все входящие и исходящие сообщения текущего пользователя."""
        queryset = self.get_queryset().order_by("-created_at")
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = MessageListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = MessageListSerializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = MessageSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"], url_path="dialog/(?P<user_id>[^/.]+)")
    def dialog(self, request, user_id=None):
        """GET /api/messages/dialog/<user_id>/ — переписка с пользователем."""
        other_user = get_object_or_404(User, pk=user_id)
        messages = Message.objects.filter(
            Q(sender=request.user, recipient=other_user) |
            Q(sender=other_user, recipient=request.user)
        ).order_by("created_at")
        messages.filter(recipient=request.user, is_read=False).update(is_read=True)
        page = self.paginate_queryset(messages)
        if page is not None:
            serializer = MessageListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = MessageListSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        """POST /api/messages/<id>/read/ — отметить одно сообщение прочитанным."""
        message = get_object_or_404(Message, pk=pk, recipient=request.user)
        self.check_object_permissions(request, message)
        message.is_read = True
        message.save()
        return Response({"detail": "Сообщение отмечено как прочитанное."})