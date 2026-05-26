from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from phonenumber_field.modelfields import PhoneNumberField


class User(AbstractUser):
    phone = PhoneNumberField(null=True, blank=True, verbose_name="Телефон")
    age = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(17), MaxValueValidator(100)],
        null=True, blank=True,
        verbose_name="Возраст",
    )
    avatar = models.ImageField(
        upload_to="avatar_images/", null=True, blank=True, verbose_name="Аватар"
    )
    bio = models.TextField(null=True, blank=True, verbose_name="О себе")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата регистрации")

    def __str__(self):
        return self.username


class Category(models.Model):
    name = models.CharField(max_length=20, unique=True, verbose_name="Название категории")
    slug = models.SlugField(max_length=32, unique=True, null=True, blank=True, verbose_name="Слаг")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"


class Post(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Черновик'),
        ('published', 'Опубликован'),
    ]

    title = models.CharField(max_length=100, verbose_name="Заголовок")
    text = models.TextField(verbose_name="Текст")
    image = models.ImageField(
        upload_to="post_images/", null=True, blank=True, verbose_name="Обложка"
    )
    author = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name="posts", verbose_name="Автор"
    )
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True,
        related_name="posts", verbose_name="Категория"
    )
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES,
        default='draft', verbose_name="Статус"
    )
    views = models.PositiveIntegerField(default=0, verbose_name="Просмотры")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Пост"
        verbose_name_plural = "Посты"


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE,
        related_name="comments", verbose_name="Пост"
    )
    author = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name="comments", verbose_name="Автор"
    )
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE,
        null=True, blank=True,
        related_name="replies", verbose_name="Ответ на"
    )
    text = models.TextField(verbose_name="Текст комментария")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    def __str__(self):
        author = self.author.username if self.author else "Удалённый пользователь"
        return f"Комментарий от {author} к посту «{self.post.title}»"

    class Meta:
        ordering = ['created_at']
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} сохранил «{self.post.title}»"

    class Meta:
        unique_together = ('user', 'post')
        verbose_name = "Избранное"
        verbose_name_plural = "Избранное"


class Message(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_messages"
    )
    recipient = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="received_messages"
    )
    text = models.TextField(verbose_name="Текст")
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"От {self.sender.username} к {self.recipient.username}"

    class Meta:
        ordering = ['created_at']
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"