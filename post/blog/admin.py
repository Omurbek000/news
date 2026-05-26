# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse

from .models import User, Category, Post, Comment, Favorite, Message


# ============================
#  INLINE-МОДЕЛИ
# ============================

class PostInline(admin.TabularInline):
    """Посты пользователя внутри карточки User."""
    model = Post
    extra = 0
    fields = ('title', 'status', 'category', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True
    can_delete = False


class CommentInline(admin.TabularInline):
    """Комментарии пользователя (для UserAdmin)."""
    model = Comment
    fk_name = 'author'
    extra = 0
    fields = ('post', 'text_preview', 'created_at')
    readonly_fields = ('created_at', 'text_preview')
    show_change_link = True
    can_delete = False

    def text_preview(self, obj):
        return obj.text[:75] + '...' if len(obj.text) > 75 else obj.text
    text_preview.short_description = 'Текст'


class FavoriteInline(admin.TabularInline):
    """Избранные посты пользователя."""
    model = Favorite
    extra = 0
    fields = ('post', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True
    can_delete = False


class SentMessageInline(admin.TabularInline):
    """Отправленные сообщения."""
    model = Message
    fk_name = 'sender'
    extra = 0
    fields = ('recipient', 'short_text', 'is_read', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True
    can_delete = False

    def short_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    short_text.short_description = 'Текст'


class ReceivedMessageInline(admin.TabularInline):
    """Полученные сообщения."""
    model = Message
    fk_name = 'recipient'
    extra = 0
    fields = ('sender', 'short_text', 'is_read', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True
    can_delete = False

    def short_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    short_text.short_description = 'Текст'


# Новый inline для комментариев внутри поста (правильный FK)
class PostCommentInline(admin.TabularInline):
    """Комментарии к посту на странице редактирования поста."""
    model = Comment
    # fk_name не нужен, т.к. связь через поле post
    extra = 0
    fields = ('author', 'text_preview', 'parent', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True
    can_delete = False

    def text_preview(self, obj):
        return obj.text[:60] + '...' if len(obj.text) > 60 else obj.text
    text_preview.short_description = 'Текст'


class CommentRepliesInline(admin.TabularInline):
    """Ответы на комментарий (внутри родительского комментария)."""
    model = Comment
    fk_name = 'parent'
    extra = 0
    fields = ('author', 'text_preview', 'created_at')
    readonly_fields = ('created_at',)
    show_change_link = True
    can_delete = False

    def text_preview(self, obj):
        return obj.text[:60] + '...' if len(obj.text) > 60 else obj.text
    text_preview.short_description = 'Текст'


# ============================
#  АДМИНКИ МОДЕЛЕЙ
# ============================

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = (
        'username', 'email', 'phone', 'age', 'avatar_preview',
        'is_staff', 'is_active', 'created_at'
    )
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'age')
    search_fields = ('username', 'email', 'phone', 'bio')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Персональная информация', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'age', 'avatar', 'bio')
        }),
        ('Права доступа', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Важные даты', {'fields': ('last_login', 'date_joined', 'created_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone', 'age', 'password1', 'password2'),
        }),
    )

    readonly_fields = ('created_at', 'last_login', 'date_joined')
    inlines = [PostInline, CommentInline, FavoriteInline, SentMessageInline, ReceivedMessageInline]

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" width="40" height="40" style="border-radius:50%; object-fit:cover;" />',
                obj.avatar.url
            )
        return '—'
    avatar_preview.short_description = 'Аватар'


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'post_count')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('name',)

    def post_count(self, obj):
        count = obj.posts.count()
        url = reverse('admin:blog_post_changelist')  # замените blog, если приложение иначе
        return format_html('<a href="{}?category__id={}">{}</a>', url, obj.id, count)
    post_count.short_description = 'Постов'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'author_link', 'category', 'status_badge',
        'views', 'image_preview', 'created_at', 'updated_at'
    )
    list_filter = ('status', 'category', 'author', 'created_at')
    search_fields = ('title', 'text', 'author__username')
    date_hierarchy = 'created_at'
    raw_id_fields = ('author', 'category')
    readonly_fields = ('views', 'created_at', 'updated_at')
    actions = ['make_published', 'make_draft']
    list_per_page = 20

    fieldsets = (
        (None, {
            'fields': ('title', 'text', 'image', 'image_preview_large')
        }),
        ('Автор и категория', {
            'fields': ('author', 'category')
        }),
        ('Состояние', {
            'fields': ('status', 'views')
        }),
        ('Даты', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    # Убираем inlines уровня класса, чтобы избежать ошибки валидации.
    # inlines = []  # просто не указываем

    def get_inlines(self, request, obj=None):
        """Показываем комментарии только для существующего поста."""
        if obj:
            return [PostCommentInline]  # Используем специальный inline для связи post
        return []

    def author_link(self, obj):
        if obj.author:
            url = reverse('admin:blog_user_change', args=[obj.author.id])  # blog — имя приложения
            return format_html('<a href="{}">{}</a>', url, obj.author.username)
        return '—'
    author_link.short_description = 'Автор'

    def status_badge(self, obj):
        if obj.status == 'published':
            return format_html(
                '<span style="color:white; background-color:green; padding:2px 8px; border-radius:10px;">Опубликован</span>'
            )
        return format_html(
            '<span style="color:white; background-color:orange; padding:2px 8px; border-radius:10px;">Черновик</span>'
        )
    status_badge.short_description = 'Статус'

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" style="border-radius:5px;" />', obj.image.url)
        return '—'
    image_preview.short_description = 'Обложка'

    def image_preview_large(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="300" style="border-radius:10px;" />', obj.image.url)
        return 'Нет изображения'
    image_preview_large.short_description = 'Предпросмотр обложки'

    @admin.action(description='Опубликовать выбранные посты')
    def make_published(self, request, queryset):
        updated = queryset.update(status='published')
        self.message_user(request, f'Опубликовано постов: {updated}')

    @admin.action(description='Сделать черновиками')
    def make_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'Переведено в черновики: {updated}')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'post_link', 'author_link', 'text_preview', 'parent_id', 'created_at')
    list_filter = ('created_at', 'post__category')
    search_fields = ('text', 'author__username', 'post__title')
    raw_id_fields = ('author', 'post', 'parent')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)

    fieldsets = (
        (None, {
            'fields': ('post', 'author', 'parent', 'text')
        }),
        ('Дата', {
            'fields': ('created_at',),
        }),
    )

    inlines = [CommentRepliesInline]  # Ответы на комментарий (через parent)

    def post_link(self, obj):
        url = reverse('admin:blog_post_change', args=[obj.post.id])
        return format_html('<a href="{}">{}</a>', url, obj.post.title)
    post_link.short_description = 'Пост'

    def author_link(self, obj):
        if obj.author:
            url = reverse('admin:blog_user_change', args=[obj.author.id])
            return format_html('<a href="{}">{}</a>', url, obj.author.username)
        return 'Удалён'
    author_link.short_description = 'Автор'

    def text_preview(self, obj):
        return obj.text[:60] + '...' if len(obj.text) > 60 else obj.text
    text_preview.short_description = 'Текст'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'post_link', 'created_at')
    search_fields = ('user__username', 'post__title')
    raw_id_fields = ('user', 'post')
    list_filter = ('created_at',)
    date_hierarchy = 'created_at'

    def user_link(self, obj):
        url = reverse('admin:blog_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Пользователь'

    def post_link(self, obj):
        url = reverse('admin:blog_post_change', args=[obj.post.id])
        return format_html('<a href="{}">{}</a>', url, obj.post.title)
    post_link.short_description = 'Пост'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender_link', 'recipient_link', 'text_preview', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('sender__username', 'recipient__username', 'text')
    raw_id_fields = ('sender', 'recipient')
    date_hierarchy = 'created_at'
    actions = ['mark_as_read', 'mark_as_unread']

    fieldsets = (
        (None, {
            'fields': ('sender', 'recipient', 'text', 'is_read')
        }),
        ('Дата', {
            'fields': ('created_at',),
        }),
    )

    readonly_fields = ('created_at',)

    def sender_link(self, obj):
        url = reverse('admin:blog_user_change', args=[obj.sender.id])
        return format_html('<a href="{}">{}</a>', url, obj.sender.username)
    sender_link.short_description = 'Отправитель'

    def recipient_link(self, obj):
        url = reverse('admin:blog_user_change', args=[obj.recipient.id])
        return format_html('<a href="{}">{}</a>', url, obj.recipient.username)
    recipient_link.short_description = 'Получатель'

    def text_preview(self, obj):
        return obj.text[:60] + '...' if len(obj.text) > 60 else obj.text
    text_preview.short_description = 'Текст'

    @admin.action(description='Отметить как прочитанные')
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, f'Помечено как прочитанное: {updated}')

    @admin.action(description='Отметить как непрочитанные')
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(request, f'Помечено как непрочитанное: {updated}')