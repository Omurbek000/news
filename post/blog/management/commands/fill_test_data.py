from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import timedelta
from blog.models import User, Category, Post, Comment, Favorite, Message


class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми данными: 10 пользователей, категории, посты, комментарии, избранное, сообщения'

    def handle(self, *args, **options):
        self.stdout.write("Начинаю заполнение базы данных...")

        # --- 1. Создаём 10 обычных пользователей + суперпользователь ---
        users_data = [
            {"username": "alex", "email": "alex@example.com", "first_name": "Алексей", "last_name": "Иванов", "age": 25, "phone": "+996700111111", "bio": "Люблю программирование"},
            {"username": "maria", "email": "maria@example.com", "first_name": "Мария", "last_name": "Петрова", "age": 30, "phone": "+996700222222", "bio": "Фотограф и путешественница"},
            {"username": "ivan", "email": "ivan@example.com", "first_name": "Иван", "last_name": "Сидоров", "age": 22, "phone": "+996700333333", "bio": "Студент, увлекаюсь спортом"},
            {"username": "olga", "email": "olga@example.com", "first_name": "Ольга", "last_name": "Кузнецова", "age": 28, "phone": "+996700444444", "bio": "Дизайнер интерьеров"},
            {"username": "dmitry", "email": "dmitry@example.com", "first_name": "Дмитрий", "last_name": "Соколов", "age": 35, "phone": "+996700555555", "bio": "Предприниматель"},
            {"username": "elena", "email": "elena@example.com", "first_name": "Елена", "last_name": "Волкова", "age": 27, "phone": "+996700666666", "bio": "Маркетолог"},
            {"username": "sergey", "email": "sergey@example.com", "first_name": "Сергей", "last_name": "Морозов", "age": 32, "phone": "+996700777777", "bio": "Водитель"},
            {"username": "anna", "email": "anna@example.com", "first_name": "Анна", "last_name": "Новикова", "age": 24, "phone": "+996700888888", "bio": "Врач"},
            {"username": "pavel", "email": "pavel@example.com", "first_name": "Павел", "last_name": "Козлов", "age": 29, "phone": "+996700999999", "bio": "Юрист"},
            {"username": "tatyana", "email": "tatyana@example.com", "first_name": "Татьяна", "last_name": "Лебедева", "age": 31, "phone": "+996701000000", "bio": "Учитель"},
        ]

        users = []
        for data in users_data:
            user, created = User.objects.get_or_create(
                username=data["username"],
                defaults={
                    "email": data["email"],
                    "first_name": data["first_name"],
                    "last_name": data["last_name"],
                    "age": data["age"],
                    "phone": data["phone"],
                    "bio": data["bio"],
                    "password": make_password("admin"),
                    "is_active": True,
                }
            )
            users.append(user)
            self.stdout.write(f"Пользователь {user.username} создан/найден")

        # Суперпользователь
        admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "first_name": "Admin",
                "last_name": "Adminov",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
                "password": make_password("admin"),
            }
        )
        self.stdout.write("Суперпользователь admin создан/найден (пароль: admin)")

        # --- 2. Категории (10 штук) ---
        categories_data = [
            "Технологии", "Путешествия", "Кулинария", "Спорт", "Кино",
            "Музыка", "Искусство", "Наука", "Бизнес", "Мода"
        ]
        categories = []
        for idx, name in enumerate(categories_data, start=1):
            cat, created = Category.objects.get_or_create(
                name=name,
                defaults={"slug": name.lower().replace(" ", "-")}
            )
            categories.append(cat)
            self.stdout.write(f"Категория {cat.name} создана")

        # --- 3. Посты (по 1-2 на категорию, всего 10-15) ---
        posts_data = [
            {"title": "Новый iPhone 15 Pro: обзор", "text": "Смартфон с новым процессором и отличной камерой...", "category": categories[0], "author": users[0], "status": "published"},
            {"title": "Путешествие в Бали", "text": "Как я съездил на райский остров: советы и впечатления...", "category": categories[1], "author": users[1], "status": "published"},
            {"title": "Рецепт идеального борща", "text": "Пошаговый рецепт с секретным ингредиентом...", "category": categories[2], "author": users[2], "status": "published"},
            {"title": "Правильный бег для похудения", "text": "Советы тренера: как бегать, чтобы не навредить...", "category": categories[3], "author": users[3], "status": "published"},
            {"title": "Топ-5 фильмов 2024 года", "text": "Собрали лучшие киноленты года...", "category": categories[4], "author": users[4], "status": "published"},
            {"title": "Как научиться играть на гитаре", "text": "С нуля до первых аккордов за месяц...", "category": categories[5], "author": users[5], "status": "published"},
            {"title": "Современная живопись: тренды", "text": "Что сейчас в моде у художников...", "category": categories[6], "author": users[6], "status": "published"},
            {"title": "Квантовые вычисления для чайников", "text": "Простым языком о сложном...", "category": categories[7], "author": users[7], "status": "published"},
            {"title": "Как открыть свой бизнес с нуля", "text": "Пошаговая инструкция для начинающих...", "category": categories[8], "author": users[8], "status": "published"},
            {"title": "Весенний гардероб 2025", "text": "Модные тенденции и базовые вещи...", "category": categories[9], "author": users[9], "status": "published"},
            {"title": "Черновик: Мои планы", "text": "Этот пост пока не опубликован", "category": categories[0], "author": users[0], "status": "draft"},
            {"title": "Личное: почему я пишу блог", "text": "Размышления вслух...", "category": categories[1], "author": users[1], "status": "draft"},
        ]
        posts = []
        for post_data in posts_data:
            post, created = Post.objects.get_or_create(
                title=post_data["title"],
                defaults={
                    "text": post_data["text"],
                    "category": post_data["category"],
                    "author": post_data["author"],
                    "status": post_data["status"],
                    "views": 0,
                }
            )
            posts.append(post)
            self.stdout.write(f"Пост '{post.title}' создан (статус: {post.status})")

        # --- 4. Комментарии (корневые и ответы) ---
        # Корневые комментарии к первым 5 постам
        for i, post in enumerate(posts[:5]):
            # По 2 корневых комментария на пост
            for j in range(2):
                user = users[(i + j) % len(users)]
                Comment.objects.get_or_create(
                    post=post,
                    author=user,
                    parent=None,
                    defaults={"text": f"Отличный пост! Спасибо автору. (#{j+1})"}
                )
        # Ответы на первые комментарии
        first_comment = Comment.objects.first()
        if first_comment:
            user = users[1]
            Comment.objects.get_or_create(
                post=first_comment.post,
                author=user,
                parent=first_comment,
                defaults={"text": "Согласен! Очень интересная тема."}
            )
        self.stdout.write("Комментарии добавлены")

        # --- 5. Избранное (каждый пользователь добавил несколько постов) ---
        for idx, user in enumerate(users[:5]):
            # Каждый из первых 5 пользователей добавляет 3 поста в избранное
            for p in posts[idx:idx+3]:
                Favorite.objects.get_or_create(user=user, post=p)
        self.stdout.write("Избранное добавлено")

        # --- 6. Сообщения между пользователями ---
        for i in range(5):
            sender = users[i]
            recipient = users[(i+1) % len(users)]
            Message.objects.get_or_create(
                sender=sender,
                recipient=recipient,
                defaults={"text": f"Привет! Это тестовое сообщение #{i+1}. Как дела?", "is_read": i % 2 == 0}
            )
            # Ответное сообщение
            Message.objects.get_or_create(
                sender=recipient,
                recipient=sender,
                defaults={"text": f"Привет! Всё отлично, а у тебя? (ответ #{i+1})", "is_read": i % 2 == 1}
            )
        self.stdout.write("Сообщения добавлены")

        self.stdout.write(self.style.SUCCESS("База данных успешно заполнена тестовыми данными!"))