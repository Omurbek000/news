from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html

from .models import Category, Comment, Favorite, Message, Post, User


# ───────────────────────────── USER ─────────────────────────────

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("id", "username", "email", "phone", "age", "avatar_preview", "is_staff", "created_at")
    list_display_links = ("id", "username")
    list_filter = ("is_staff", "is_active", "is_superuser")
    search_fields = ("username", "email", "phone")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "avatar_preview")

    # Добавляем наши поля в форму редактирования
    fieldsets = UserAdmin.fieldsets + (
        ("Дополнительно", {
            "fields": ("phone", "age", "avatar", "avatar_preview", "bio", "created_at")
        }),
    )

    # Добавляем поля при создании пользователя
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Дополнительно", {
            "fields": ("email", "phone", "age", "avatar", "bio")
        }),
    )

    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%; object-fit: cover;" />',
                obj.avatar.url,
            )
        return "—"
    avatar_preview.short_description = "Аватар"


# ─────────────────────────── CATEGORY ───────────────────────────

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "posts_count")
    list_display_links = ("id", "name")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}  # авто-заполнение slug из name

    def posts_count(self, obj):
        return obj.posts.count()
    posts_count.short_description = "Постов"


# ──────────────────────────── POST ──────────────────────────────

class CommentInline(admin.TabularInline):
    """Показываем комментарии прямо внутри поста."""
    model = Comment
    extra = 0
    readonly_fields = ("author", "text", "created_at")
    can_delete = True
    show_change_link = True
    fields = ("author", "text", "created_at")


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        "id", "title", "author", "category",
        "status", "views", "comments_count",
        "favorites_count", "created_at",
    )
    list_display_links = ("id", "title")
    list_filter = ("status", "category", "created_at")
    search_fields = ("title", "text", "author__username")
    ordering = ("-created_at",)
    readonly_fields = ("views", "created_at", "updated_at")
    autocomplete_fields = ("author", "category")
    inlines = [CommentInline]

    fieldsets = (
        ("Основное", {
            "fields": ("title", "text", "image", "author", "category", "status")
        }),
        ("Статистика", {
            "fields": ("views", "created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    def comments_count(self, obj):
        return obj.comments.count()
    comments_count.short_description = "Комментариев"

    def favorites_count(self, obj):
        return obj.favorited_by.count()
    favorites_count.short_description = "В избранном"


# ─────────────────────────── COMMENT ────────────────────────────

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "author", "post", "short_text", "parent", "created_at")
    list_display_links = ("id", "short_text")
    list_filter = ("created_at",)
    search_fields = ("text", "author__username", "post__title")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    autocomplete_fields = ("author", "post")

    def short_text(self, obj):
        return obj.text[:60] + "..." if len(obj.text) > 60 else obj.text
    short_text.short_description = "Текст"


# ─────────────────────────── FAVORITE ───────────────────────────

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "post", "created_at")
    list_display_links = ("id",)
    list_filter = ("created_at",)
    search_fields = ("user__username", "post__title")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    autocomplete_fields = ("user", "post")


# ─────────────────────────── MESSAGE ────────────────────────────

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "sender", "recipient", "short_text", "is_read", "created_at")
    list_display_links = ("id",)
    list_filter = ("is_read", "created_at")
    search_fields = ("sender__username", "recipient__username", "text")
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)
    autocomplete_fields = ("sender", "recipient")

    def short_text(self, obj):
        return obj.text[:60] + "..." if len(obj.text) > 60 else obj.text
    short_text.short_description = "Сообщение"
