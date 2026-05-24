from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    phone = PhoneNumberField(null=True, blank=True, verbose_name="Телефон")
    age = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(17), MaxValueValidator(100)],
        verbose_name="Возраст",
    )
    avatar = models.ImageField(
        upload_to="avatar_images/", null=True, blank=True, verbose_name="Аватар"
    )
    bio = models.TextField(null=True, blank=True, verbose_name="О себе")
    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата регистрации"
    )

    def __str__(self) -> str:
        return self.username


class Category(models.Model):
    name = models.CharField(
        max_length=20, unique=True, verbose_name="Название Категории"
    )
    slug = models.SlugField(max_length=32, null=True, blank=True, verbose_name="Слаг")

    def __str__(self) -> str:
        return self.name


class Post(models.Model):
    title = models.CharField(max_length=100, verbose_name="Заголовок")
    text = models.TextField(verbose_name="Текст")
    author = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, verbose_name="Автор"
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, verbose_name="Категория"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return self.title


class Comments(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.SET_NULL, null=True, verbose_name="Пост"
    )
    author = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, verbose_name="Автор"
    )
    text = models.TextField(verbose_name="Текст Комментария")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        return f"Комментарий от {self.author.username} к посту {self.post.title}"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="favorited_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} лайкнул {self.post.title}"


class Message(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_messages"
    )
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"От {self.sender.username} к {self.recipient.username}"
