from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Category, Comment, Favorite, Message, Post, User


# ───────────────────────────── AUTH ─────────────────────────────

class RegisterSerializer(serializers.ModelSerializer):
    """Регистрация нового пользователя."""

    password = serializers.CharField(
        write_only=True, required=True, validators=[validate_password]
    )
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            "id", "username", "email",
            "password", "password2",
            "phone", "age", "avatar", "bio",
        )

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Пароли не совпадают."})
        # Дополнительная проверка пароля (validate_password уже вызван, но можно и явно)
        # validate_password(attrs["password"], user=None)
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    """Вход по username + password, возвращает JWT-токены."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs["username"], password=attrs["password"])
        if not user:
            raise serializers.ValidationError("Неверный логин или пароль.")
        if not user.is_active:
            raise serializers.ValidationError("Аккаунт заблокирован.")

        refresh = RefreshToken.for_user(user)
        return {
            "user_id": user.id,
            "username": user.username,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


class ChangePasswordSerializer(serializers.Serializer):
    """Смена пароля авторизованным пользователем."""

    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Старый пароль указан неверно.")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password2"]:
            raise serializers.ValidationError({"new_password": "Пароли не совпадают."})
        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.save()
        return user


# ───────────────────────────── USER ─────────────────────────────

class UserShortSerializer(serializers.ModelSerializer):
    """Краткая информация об авторе (для вложения в посты/комментарии)."""

    class Meta:
        model = User
        fields = ("id", "username", "avatar")


class UserProfileSerializer(serializers.ModelSerializer):
    """Полный профиль пользователя (чтение)."""

    posts_count = serializers.IntegerField(source="posts.count", read_only=True)

    class Meta:
        model = User
        fields = (
            "id", "username", "email", "phone",
            "age", "avatar", "bio",
            "created_at", "posts_count",
        )
        read_only_fields = ("id", "created_at", "posts_count")


class UserUpdateSerializer(serializers.ModelSerializer):
    """Редактирование профиля (только своё)."""

    class Meta:
        model = User
        fields = ("username", "email", "phone", "age", "avatar", "bio")

    def validate_email(self, value):
        user = self.context["request"].user
        if User.objects.filter(email=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("Этот email уже занят.")
        return value


# ─────────────────────────── CATEGORY ───────────────────────────

class CategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = Category
        fields = ("id", "name", "slug")


# ──────────────────────────── POST ──────────────────────────────

class PostListSerializer(serializers.ModelSerializer):
    """Список постов — краткое представление."""

    author = UserShortSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    favorites_count = serializers.IntegerField(
        source="favorited_by.count", read_only=True
    )
    comments_count = serializers.IntegerField(
        source="comments.count", read_only=True
    )

    class Meta:
        model = Post
        fields = (
            "id", "title", "image", "author", "category",
            "status", "views", "favorites_count", "comments_count",
            "created_at",
        )


class PostDetailSerializer(serializers.ModelSerializer):
    """Детальный просмотр поста."""

    author = UserShortSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    favorites_count = serializers.IntegerField(
        source="favorited_by.count", read_only=True
    )
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = (
            "id", "title", "text", "image", "author", "category",
            "status", "views", "favorites_count", "is_favorited",
            "created_at", "updated_at",
        )

    def get_is_favorited(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.favorited_by.filter(user=request.user).exists()
        return False


class PostCreateUpdateSerializer(serializers.ModelSerializer):
    """Создание и редактирование поста."""

    class Meta:
        model = Post
        fields = ("id", "title", "text", "image", "category", "status")

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        return super().create(validated_data)


# ─────────────────────────── COMMENT ────────────────────────────

class CommentSerializer(serializers.ModelSerializer):
    """Комментарий с вложенными ответами."""

    author = UserShortSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ("id", "author", "parent", "text", "created_at", "replies")
        read_only_fields = ("id", "author", "created_at")

    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(
                obj.replies.all(), many=True, context=self.context
            ).data
        return []

    def validate_parent(self, value):
        """Проверяем, что parent относится к тому же посту."""
        if value:
            # self.context['view'] содержит kwargs['post_pk']
            post_id = self.context['view'].kwargs.get('post_pk')
            if value.post_id != post_id:
                raise serializers.ValidationError("Ответ должен быть к комментарию этого же поста.")
        return value

    def create(self, validated_data):
        validated_data["author"] = self.context["request"].user
        return super().create(validated_data)


# ─────────────────────────── FAVORITE ───────────────────────────

class FavoriteSerializer(serializers.ModelSerializer):
    """Добавление/удаление поста из избранного."""

    class Meta:
        model = Favorite
        fields = ("id", "post", "created_at")
        read_only_fields = ("id", "created_at")

    def validate(self, attrs):
        user = self.context["request"].user
        if Favorite.objects.filter(user=user, post=attrs["post"]).exists():
            raise serializers.ValidationError("Этот пост уже в избранном.")
        return attrs

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


# ─────────────────────────── MESSAGE ────────────────────────────

class MessageSerializer(serializers.ModelSerializer):
    """Личное сообщение между пользователями."""

    sender = UserShortSerializer(read_only=True)

    class Meta:
        model = Message
        fields = ("id", "sender", "recipient", "text", "created_at", "is_read")
        read_only_fields = ("id", "sender", "created_at", "is_read")

    def validate_recipient(self, value):
        user = self.context["request"].user
        if value == user:
            raise serializers.ValidationError("Нельзя отправить сообщение самому себе.")
        return value

    def create(self, validated_data):
        validated_data["sender"] = self.context["request"].user
        return super().create(validated_data)


class MessageListSerializer(serializers.ModelSerializer):
    """Список сообщений в диалоге (без вложенного sender для скорости)."""

    sender_username = serializers.CharField(source="sender.username", read_only=True)
    recipient_username = serializers.CharField(source="recipient.username", read_only=True)

    class Meta:
        model = Message
        fields = (
            "id", "sender_username", "recipient_username",
            "text", "created_at", "is_read",
        )