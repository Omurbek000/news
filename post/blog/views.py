# from django.shortcuts import get_object_or_404
# from django_filters.rest_framework import DjangoFilterBackend
# from rest_framework import filters, generics, permissions, status, viewsets
# from rest_framework.decorators import action
# from rest_framework.response import Response
# from rest_framework_simplejwt.tokens import RefreshToken
# from rest_framework_simplejwt.views import TokenRefreshView

# from .models import Category, Comment, Favorite, Message, Post, User
# from .serializers import (
#     CategorySerializer,
#     ChangePasswordSerializer,
#     CommentSerializer,
#     FavoriteSerializer,
#     LoginSerializer,
#     MessageListSerializer,
#     MessageSerializer,
#     PostCreateUpdateSerializer,
#     PostDetailSerializer,
#     PostListSerializer,
#     RegisterSerializer,
#     UserProfileSerializer,
#     UserUpdateSerializer,
# )


# # ───────────────────────────── AUTH ─────────────────────────────

# class RegisterView(generics.CreateAPIView):
#     """POST /api/auth/register/ — регистрация."""

#     queryset = User.objects.all()
#     serializer_class = RegisterSerializer
#     permission_classes = [permissions.AllowAny]


# class LoginView(generics.GenericAPIView):
#     """POST /api/auth/login/ — вход, возвращает access + refresh токены."""

#     serializer_class = LoginSerializer
#     permission_classes = [permissions.AllowAny]

#     def post(self, request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         return Response(serializer.validated_data, status=status.HTTP_200_OK)


# class LogoutView(generics.GenericAPIView):
#     """POST /api/auth/logout/ — выход, помещает refresh-токен в blacklist."""

#     permission_classes = [permissions.IsAuthenticated]

#     def post(self, request):
#         try:
#             refresh_token = request.data["refresh"]
#             token = RefreshToken(refresh_token)
#             token.blacklist()
#             return Response(
#                 {"detail": "Вы успешно вышли из системы."},
#                 status=status.HTTP_205_RESET_CONTENT,
#             )
#         except Exception:
#             return Response(
#                 {"detail": "Неверный или уже использованный токен."},
#                 status=status.HTTP_400_BAD_REQUEST,
#             )


# class ChangePasswordView(generics.UpdateAPIView):
#     """PUT /api/auth/change-password/ — смена пароля."""

#     serializer_class = ChangePasswordSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def update(self, request, *args, **kwargs):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(
#             {"detail": "Пароль успешно изменён."},
#             status=status.HTTP_200_OK,
#         )


# # ───────────────────────────── USER ─────────────────────────────

# class UserProfileView(generics.RetrieveAPIView):
#     """GET /api/users/<id>/ — публичный профиль любого пользователя."""

#     queryset = User.objects.all()
#     serializer_class = UserProfileSerializer
#     permission_classes = [permissions.AllowAny]


# class MeView(generics.RetrieveUpdateAPIView):
#     """
#     GET  /api/users/me/ — свой профиль.
#     PUT  /api/users/me/ — редактирование профиля.
#     PATCH /api/users/me/ — частичное редактирование.
#     """

#     permission_classes = [permissions.IsAuthenticated]

#     def get_object(self):
#         return self.request.user

#     def get_serializer_class(self):
#         if self.request.method in ("PUT", "PATCH"):
#             return UserUpdateSerializer
#         return UserProfileSerializer


# # ─────────────────────────── CATEGORY ───────────────────────────

# class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
#     """
#     GET /api/categories/      — список категорий.
#     GET /api/categories/<id>/ — одна категория.
#     (только чтение — создаёт администратор через /admin/)
#     """

#     queryset = Category.objects.all()
#     serializer_class = CategorySerializer
#     permission_classes = [permissions.AllowAny]


# # ──────────────────────────── POST ──────────────────────────────

# class PostViewSet(viewsets.ModelViewSet):
#     """
#     GET    /api/posts/       — список опубликованных постов.
#     POST   /api/posts/       — создать пост (авторизация обязательна).
#     GET    /api/posts/<id>/  — детали поста (счётчик просмотров ++).
#     PUT    /api/posts/<id>/  — редактировать (только автор).
#     PATCH  /api/posts/<id>/  — частично редактировать (только автор).
#     DELETE /api/posts/<id>/  — удалить (только автор).
#     GET    /api/posts/my/    — мои посты (все статусы).
#     """

#     filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
#     filterset_fields = ["category", "status", "author"]
#     search_fields = ["title", "text"]
#     ordering_fields = ["created_at", "views"]
#     ordering = ["-created_at"]

#     def get_queryset(self):
#         # В списке — только опубликованные, кроме экшена "my"
#         if self.action == "my":
#             return Post.objects.filter(author=self.request.user)
#         return Post.objects.filter(status="published").select_related(
#             "author", "category"
#         )

#     def get_serializer_class(self):
#         if self.action in ("create", "update", "partial_update"):
#             return PostCreateUpdateSerializer
#         if self.action == "retrieve":
#             return PostDetailSerializer
#         return PostListSerializer

#     def get_permissions(self):
#         if self.action in ("list", "retrieve"):
#             return [permissions.AllowAny()]
#         return [permissions.IsAuthenticated()]

#     def retrieve(self, request, *args, **kwargs):
#         instance = self.get_object()
#         # Увеличиваем счётчик просмотров
#         Post.objects.filter(pk=instance.pk).update(views=instance.views + 1)
#         instance.refresh_from_db()
#         serializer = self.get_serializer(instance)
#         return Response(serializer.data)

#     def update(self, request, *args, **kwargs):
#         instance = self.get_object()
#         if instance.author != request.user:
#             return Response(
#                 {"detail": "Вы не являетесь автором этого поста."},
#                 status=status.HTTP_403_FORBIDDEN,
#             )
#         return super().update(request, *args, **kwargs)

#     def destroy(self, request, *args, **kwargs):
#         instance = self.get_object()
#         if instance.author != request.user:
#             return Response(
#                 {"detail": "Вы не являетесь автором этого поста."},
#                 status=status.HTTP_403_FORBIDDEN,
#             )
#         return super().destroy(request, *args, **kwargs)

#     @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
#     def my(self, request):
#         """GET /api/posts/my/ — все мои посты включая черновики."""
#         queryset = self.get_queryset()
#         serializer = PostListSerializer(queryset, many=True, context={"request": request})
#         return Response(serializer.data)


# # ─────────────────────────── COMMENT ────────────────────────────

# class CommentViewSet(viewsets.ModelViewSet):
#     """
#     GET    /api/posts/<post_id>/comments/       — комментарии к посту.
#     POST   /api/posts/<post_id>/comments/       — добавить комментарий.
#     PUT    /api/posts/<post_id>/comments/<id>/  — редактировать (только автор).
#     DELETE /api/posts/<post_id>/comments/<id>/  — удалить (только автор).
#     """

#     serializer_class = CommentSerializer
#     permission_classes = [permissions.IsAuthenticatedOrReadOnly]

#     def get_queryset(self):
#         return Comment.objects.filter(
#             post_id=self.kwargs["post_pk"],
#             parent=None,  # только корневые, replies вложены через сериализатор
#         ).select_related("author")

#     def perform_create(self, serializer):
#         post = get_object_or_404(Post, pk=self.kwargs["post_pk"])
#         serializer.save(author=self.request.user, post=post)

#     def update(self, request, *args, **kwargs):
#         instance = self.get_object()
#         if instance.author != request.user:
#             return Response(
#                 {"detail": "Вы не являетесь автором этого комментария."},
#                 status=status.HTTP_403_FORBIDDEN,
#             )
#         return super().update(request, *args, **kwargs)

#     def destroy(self, request, *args, **kwargs):
#         instance = self.get_object()
#         if instance.author != request.user:
#             return Response(
#                 {"detail": "Вы не являетесь автором этого комментария."},
#                 status=status.HTTP_403_FORBIDDEN,
#             )
#         return super().destroy(request, *args, **kwargs)


# # ─────────────────────────── FAVORITE ───────────────────────────

# class FavoriteViewSet(viewsets.GenericViewSet):
#     """
#     GET    /api/favorites/         — мои избранные посты.
#     POST   /api/favorites/         — добавить пост в избранное.
#     DELETE /api/favorites/<id>/    — убрать из избранного.
#     """

#     serializer_class = FavoriteSerializer
#     permission_classes = [permissions.IsAuthenticated]

#     def get_queryset(self):
#         return Favorite.objects.filter(user=self.request.user).select_related("post")

#     def list(self, request):
#         serializer = self.get_serializer(self.get_queryset(), many=True)
#         return Response(serializer.data)

#     def create(self, request):
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)

#     def destroy(self, request, pk=None):
#         favorite = get_object_or_404(Favorite, pk=pk, user=request.user)
#         favorite.delete()
#         return Response(
#             {"detail": "Пост убран из избранного."},
#             status=status.HTTP_204_NO_CONTENT,
#         )


# # ─────────────────────────── MESSAGE ────────────────────────────

# class MessageViewSet(viewsets.GenericViewSet):
#     """
#     GET  /api/messages/                      — все мои диалоги (входящие + исходящие).
#     GET  /api/messages/dialog/<user_id>/     — диалог с конкретным пользователем.
#     POST /api/messages/                      — отправить сообщение.
#     POST /api/messages/<id>/read/            — отметить сообщение прочитанным.
#     """

#     permission_classes = [permissions.IsAuthenticated]

#     def get_serializer_class(self):
#         if self.action == "list":
#             return MessageListSerializer
#         return MessageSerializer

#     def list(self, request):
#         """Все входящие и исходящие сообщения текущего пользователя."""
#         messages = Message.objects.filter(
#             sender=request.user
#         ) | Message.objects.filter(
#             recipient=request.user
#         )
#         messages = messages.order_by("-created_at")
#         serializer = MessageListSerializer(messages, many=True)
#         return Response(serializer.data)

#     def create(self, request):
#         serializer = MessageSerializer(data=request.data, context={"request": request})
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data, status=status.HTTP_201_CREATED)

#     @action(detail=False, methods=["get"], url_path="dialog/(?P<user_id>[^/.]+)")
#     def dialog(self, request, user_id=None):
#         """GET /api/messages/dialog/<user_id>/ — переписка с пользователем."""
#         other_user = get_object_or_404(User, pk=user_id)
#         messages = Message.objects.filter(
#             sender=request.user, recipient=other_user
#         ) | Message.objects.filter(
#             sender=other_user, recipient=request.user
#         )
#         messages = messages.order_by("created_at")

#         # Помечаем входящие как прочитанные
#         messages.filter(recipient=request.user, is_read=False).update(is_read=True)

#         serializer = MessageListSerializer(messages, many=True)
#         return Response(serializer.data)

#     @action(detail=True, methods=["post"])
#     def read(self, request, pk=None):
#         """POST /api/messages/<id>/read/ — отметить одно сообщение прочитанным."""
#         message = get_object_or_404(Message, pk=pk, recipient=request.user)
#         message.is_read = True
#         message.save()
#         return Response({"detail": "Сообщение отмечено как прочитанное."})













# произали не которые изминение 
from django.shortcuts import get_object_or_404
from django.db.models import F, Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import Category, Comment, Favorite, Message, Post, User
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
    # serializer_class больше не требуется

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
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


class MeView(generics.RetrieveUpdateAPIView):
    """GET /api/users/me/ — свой профиль. PUT/PATCH — редактирование."""
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return UserUpdateSerializer
        return UserProfileSerializer


# ─────────────────────────── CATEGORY ───────────────────────────

class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/categories/ — список и детали категорий."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


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
        return [permissions.IsAuthenticated()]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Атомарное увеличение счётчика просмотров
        Post.objects.filter(pk=instance.pk).update(views=F('views') + 1)
        instance.refresh_from_db()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            return Response(
                {"detail": "Вы не являетесь автором этого поста."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            return Response(
                {"detail": "Вы не являетесь автором этого поста."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def my(self, request):
        """GET /api/posts/my/ — все мои посты включая черновики."""
        queryset = self.get_queryset()
        serializer = PostListSerializer(queryset, many=True, context={"request": request})
        return Response(serializer.data)


# ─────────────────────────── COMMENT ────────────────────────────

class CommentViewSet(viewsets.ModelViewSet):
    """Комментарии к конкретному посту (вложенный роутер)."""
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        # Убран swagger_fake_view – теперь drf-spectacular всё делает сам
        return Comment.objects.filter(
            post_id=self.kwargs["post_pk"],
            parent=None,
        ).select_related("author")

    def perform_create(self, serializer):
        post = get_object_or_404(Post, pk=self.kwargs["post_pk"])
        serializer.save(author=self.request.user, post=post)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            return Response(
                {"detail": "Вы не являетесь автором этого комментария."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            return Response(
                {"detail": "Вы не являетесь автором этого комментария."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().destroy(request, *args, **kwargs)


# ─────────────────────────── FAVORITE ───────────────────────────

class FavoriteViewSet(viewsets.GenericViewSet):
    """Избранные посты текущего пользователя."""
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Favorite.objects.none()  # обязательно для swagger

    def get_queryset(self):
        # Убран swagger_fake_view
        return Favorite.objects.filter(user=self.request.user).select_related("post")

    def list(self, request):
        serializer = self.get_serializer(self.get_queryset(), many=True)
        return Response(serializer.data)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, pk=None):
        favorite = get_object_or_404(Favorite, pk=pk, user=request.user)
        favorite.delete()
        return Response(
            {"detail": "Пост убран из избранного."},
            status=status.HTTP_204_NO_CONTENT,
        )


# ─────────────────────────── MESSAGE ────────────────────────────

class MessageViewSet(viewsets.GenericViewSet):
    """Личные сообщения: список диалогов, переписка, отправка, пометка прочитанным."""
    permission_classes = [permissions.IsAuthenticated]
    queryset = Message.objects.none()  # обязательно для swagger
    # Убран get_queryset, он не нужен – queryset строится в методах

    def get_serializer_class(self):
        if self.action == "list":
            return MessageListSerializer
        return MessageSerializer

    def list(self, request):
        """Все входящие и исходящие сообщения текущего пользователя."""
        messages = Message.objects.filter(
            Q(sender=request.user) | Q(recipient=request.user)
        ).order_by("-created_at")
        serializer = MessageListSerializer(messages, many=True)
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
        # Помечаем входящие как прочитанные
        messages.filter(recipient=request.user, is_read=False).update(is_read=True)
        serializer = MessageListSerializer(messages, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        """POST /api/messages/<id>/read/ — отметить одно сообщение прочитанным."""
        message = get_object_or_404(Message, pk=pk, recipient=request.user)
        message.is_read = True
        message.save()
        return Response({"detail": "Сообщение отмечено как прочитанное."})