from django.db.models import Count, F, Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
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
    DialogSerializer,
    FavoriteSerializer,
    LoginSerializer,
    MessageListSerializer,
    MessageSerializer,
    PostCreateUpdateSerializer,
    PostDetailSerializer,
    PostListSerializer,
    RegisterSerializer,
    UserProfileSerializer,
    UserPublicProfileSerializer,
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
        user = serializer.save()
        for token in OutstandingToken.objects.filter(user=user):
            BlacklistedToken.objects.get_or_create(token=token)
        return Response(
            {"detail": "Пароль успешно изменён."},
            status=status.HTTP_200_OK,
        )


# ───────────────────────────── USER ─────────────────────────────

class UserProfileView(generics.RetrieveAPIView):
    """GET /api/users/<id>/ — публичный профиль любого пользователя."""
    queryset = User.objects.all()
    serializer_class = UserPublicProfileSerializer
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
    queryset = Category.objects.order_by("name")
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]


# ──────────────────────────── POST ──────────────────────────────

class PostViewSet(viewsets.ModelViewSet):
    """Посты: список, создание, детали, обновление, удаление, мои посты."""
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["category", "status", "author"]
    search_fields = ["title", "text"]
    ordering_fields = ["created_at", "views", "favorites_count"]
    ordering = ["-created_at"]

    def get_queryset(self):
        queryset = (
            Post.objects.select_related("author", "category")
            .annotate(
                favorites_count=Count("favorited_by", distinct=True),
                comments_count=Count("comments", distinct=True),
            )
            .order_by("-created_at")
        )
        user = self.request.user
        if self.action == "my":
            return queryset.filter(author=user)
        if self.action == "list" or not user.is_authenticated:
            return queryset.filter(status="published")
        return queryset.filter(Q(status="published") | Q(author=user))

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return PostCreateUpdateSerializer
        if self.action == "retrieve":
            return PostDetailSerializer
        return PostListSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        if self.action in ("create", "my"):
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

    def get_post(self):
        """Пост из URL; черновик доступен только его автору."""
        if getattr(self, "swagger_fake_view", False):
            raise Http404
        try:
            post_id = int(self.kwargs.get("post_pk"))
        except (TypeError, ValueError):
            raise Http404
        post = get_object_or_404(Post, pk=post_id)
        if post.status != "published" and post.author != self.request.user:
            raise Http404
        return post

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Comment.objects.none()
        post = self.get_post()
        return Comment.objects.filter(
            post=post,
            parent=None,
        ).select_related("author")

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, post=self.get_post())

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated])
    def like(self, request, pk=None, post_pk=None):
        """POST /api/posts/<post_pk>/comments/<id>/like/ — лайк/анлайк комментария."""
        comment = get_object_or_404(Comment, pk=pk, post=self.get_post())
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
            return Favorite.objects.filter(
                user=self.request.user, post__status="published"
            ).select_related("post").order_by("-created_at")
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
    dialog_default_limit = 50
    dialog_max_limit = 100

    def get_serializer_class(self):
        if self.action == "list":
            return MessageListSerializer
        if self.action == "dialogs":
            return DialogSerializer
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

    @extend_schema(responses=DialogSerializer(many=True))
    @action(detail=False, methods=["get"])
    def dialogs(self, request):
        """GET /api/messages/dialogs/ — список диалогов с числом непрочитанных."""
        messages = (
            Message.objects.filter(
                Q(sender=request.user) | Q(recipient=request.user)
            )
            .select_related("sender", "recipient")
            .order_by("-created_at", "-id")
        )
        dialogs = {}
        for message in messages:
            other = (
                message.recipient
                if message.sender_id == request.user.id
                else message.sender
            )
            dialog = dialogs.get(other.id)
            if dialog is None:
                dialog = {
                    "user_id": other.id,
                    "username": other.username,
                    "avatar": other.avatar,
                    "last_message": message.text,
                    "last_message_at": message.created_at,
                    "unread_count": 0,
                }
                dialogs[other.id] = dialog
            if message.recipient_id == request.user.id and not message.is_read:
                dialog["unread_count"] += 1
        serializer = DialogSerializer(
            list(dialogs.values()), many=True, context={"request": request}
        )
        return Response(serializer.data)

    @extend_schema(
        parameters=[
            OpenApiParameter("user_id", OpenApiTypes.INT, OpenApiParameter.PATH),
            OpenApiParameter("limit", OpenApiTypes.INT, OpenApiParameter.QUERY),
        ],
        responses=MessageListSerializer(many=True),
    )
    @action(detail=False, methods=["get"], url_path="dialog/(?P<user_id>[^/.]+)")
    def dialog(self, request, user_id=None):
        """GET /api/messages/dialog/<user_id>/?limit=N — последние сообщения переписки."""
        other_user = get_object_or_404(User, pk=user_id)
        try:
            limit = int(request.query_params.get("limit", self.dialog_default_limit))
        except (TypeError, ValueError):
            limit = self.dialog_default_limit
        limit = max(1, min(limit, self.dialog_max_limit))
        messages = list(
            Message.objects.filter(
                Q(sender=request.user, recipient=other_user) |
                Q(sender=other_user, recipient=request.user)
            )
            .select_related("sender", "recipient")
            .order_by("-created_at", "-id")[:limit]
        )
        messages.reverse()
        serializer = MessageListSerializer(messages, many=True)
        return Response(serializer.data)

    @extend_schema(
        parameters=[OpenApiParameter("user_id", OpenApiTypes.INT, OpenApiParameter.PATH)],
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="dialog/(?P<user_id>[^/.]+)/read",
    )
    def dialog_read(self, request, user_id=None):
        """POST /api/messages/dialog/<user_id>/read/ — прочитать все входящие."""
        other_user = get_object_or_404(User, pk=user_id)
        marked_read = Message.objects.filter(
            sender=other_user, recipient=request.user, is_read=False
        ).update(is_read=True)
        return Response(
            {"detail": "Сообщения отмечены как прочитанные.", "marked_read": marked_read}
        )

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        """POST /api/messages/<id>/read/ — отметить одно сообщение прочитанным."""
        message = get_object_or_404(Message, pk=pk, recipient=request.user)
        self.check_object_permissions(request, message)
        message.is_read = True
        message.save()
        return Response({"detail": "Сообщение отмечено как прочитанное."})