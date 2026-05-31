from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Безопасные методы (GET, HEAD, OPTIONS) — разрешены всем.
    Изменение/удаление — только автору объекта.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        # Для моделей с полем author
        return getattr(obj, 'author', None) == request.user


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Для объектов где поле называется `user`, а не `author`.
    Используется для Favorite, Message и т.д.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return getattr(obj, 'user', None) == request.user


class IsOwner(permissions.BasePermission):
    """
    Доступ только к своим объектам — без исключений.
    Используется для профиля, избранного, сообщений.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # Если объект — сам пользователь
        if obj == request.user:
            return True
        # Проверяем оба варианта владельца: user и author
        owner = getattr(obj, "user", None) or getattr(obj, "author", None)
        return owner == request.user


class IsSenderOrRecipient(permissions.BasePermission):
    """
    Доступ к сообщению — только отправитель или получатель.
    """

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.sender == request.user or obj.recipient == request.user


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Безопасные методы — для всех.
    Создание/редактирование/удаление — только администратор.
    Используется для категорий.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff