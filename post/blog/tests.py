from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from .models import Category, Comment, Favorite, Message, Post

User = get_user_model()


class AuthTests(TestCase):
    """Тесты регистрации, входа, logout."""

    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse("register")
        self.login_url = reverse("login")

    def test_register_success(self):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
        }
        res = self.client.post(self.register_url, data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_register_password_mismatch(self):
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "StrongPass123!",
            "password2": "DifferentPass123!",
        }
        res = self.client.post(self.register_url, data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_email(self):
        User.objects.create_user(username="existing", email="dup@example.com", password="pass1234")
        data = {
            "username": "newuser",
            "email": "dup@example.com",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
        }
        res = self.client.post(self.register_url, data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        User.objects.create_user(username="testuser", password="testpass123")
        data = {"username": "testuser", "password": "testpass123"}
        res = self.client.post(self.login_url, data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)

    def test_login_wrong_credentials(self):
        data = {"username": "nobody", "password": "wrongpass"}
        res = self.client.post(self.login_url, data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout(self):
        user = User.objects.create_user(username="testuser", password="testpass123")
        self.client.force_authenticate(user=user)
        # Get refresh token first
        login_res = self.client.post(self.login_url, {"username": "testuser", "password": "testpass123"})
        refresh = login_res.data["refresh"]
        res = self.client.post(reverse("logout"), {"refresh": refresh})
        self.assertIn(res.status_code, [status.HTTP_205_RESET_CONTENT, status.HTTP_400_BAD_REQUEST])


class UserTests(TestCase):
    """Тесты профиля пользователя."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123", bio="Test bio"
        )

    def test_get_me(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get(reverse("me"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["username"], "testuser")

    def test_update_me(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.patch(reverse("me"), {"bio": "Updated bio"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, "Updated bio")

    def test_me_requires_auth(self):
        res = self.client.get(reverse("me"))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_user_profile_public(self):
        res = self.client.get(reverse("user_profile", args=[self.user.id]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class CategoryTests(TestCase):
    """Тесты категорий."""

    def setUp(self):
        self.client = APIClient()
        self.category = Category.objects.create(name="Технологии", slug="tech")

    def test_list_categories(self):
        res = self.client.get(reverse("category-list"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_category(self):
        res = self.client.get(reverse("category-detail", args=[self.category.id]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_category_requires_admin(self):
        user = User.objects.create_user(username="user1", password="pass1234")
        self.client.force_authenticate(user=user)
        res = self.client.post(reverse("category-list"), {"name": "New"})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


class PostTests(TestCase):
    """Тесты постов."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="author", password="testpass123")
        self.category = Category.objects.create(name="Технологии", slug="tech")
        self.post = Post.objects.create(
            title="Test Post", text="Test content", author=self.user,
            category=self.category, status="published"
        )

    def test_list_posts(self):
        res = self.client.get(reverse("post-list"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_retrieve_post(self):
        res = self.client.get(reverse("post-detail", args=[self.post.id]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["title"], "Test Post")

    def test_create_post_requires_auth(self):
        res = self.client.post(reverse("post-list"), {"title": "New", "text": "Content"})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_post(self):
        self.client.force_authenticate(user=self.user)
        data = {"title": "New Post", "text": "New content", "category": self.category.id, "status": "published"}
        res = self.client.post(reverse("post-list"), data)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 2)

    def test_update_post_author_only(self):
        other_user = User.objects.create_user(username="other", password="testpass123")
        self.client.force_authenticate(user=other_user)
        res = self.client.patch(reverse("post-detail", args=[self.post.id]), {"title": "Hacked"})
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_own_post(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.patch(reverse("post-detail", args=[self.post.id]), {"title": "Updated"})
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_delete_own_post(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.delete(reverse("post-detail", args=[self.post.id]))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_views_increment(self):
        self.client.get(reverse("post-detail", args=[self.post.id]))
        self.post.refresh_from_db()
        self.assertEqual(self.post.views, 1)

    def test_my_posts(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get(reverse("post-my"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_search_posts(self):
        res = self.client.get(f"{reverse('post-list')}?search=Test")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_filter_by_category(self):
        res = self.client.get(f"{reverse('post-list')}?category={self.category.id}")
        self.assertEqual(res.status_code, status.HTTP_200_OK)


class CommentTests(TestCase):
    """Тесты комментариев."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="commenter", password="testpass123")
        self.post = Post.objects.create(title="Post", text="Text", author=self.user, status="published")

    def test_list_comments(self):
        res = self.client.get(f"/api/posts/{self.post.id}/comments/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_comment(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post(f"/api/posts/{self.post.id}/comments/", {"text": "Great post!"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_create_comment_requires_auth(self):
        res = self.client.post(f"/api/posts/{self.post.id}/comments/", {"text": "Great post!"})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class FavoriteTests(TestCase):
    """Тесты избранного."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="fan", password="testpass123")
        self.post = Post.objects.create(title="Post", text="Text", author=self.user, status="published")

    def test_add_favorite(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post(reverse("favorite-list"), {"post": self.post.id})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_list_favorites(self):
        self.client.force_authenticate(user=self.user)
        Favorite.objects.create(user=self.user, post=self.post)
        res = self.client.get(reverse("favorite-list"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_remove_favorite(self):
        self.client.force_authenticate(user=self.user)
        fav = Favorite.objects.create(user=self.user, post=self.post)
        res = self.client.delete(reverse("favorite-detail", args=[fav.id]))
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

    def test_duplicate_favorite(self):
        self.client.force_authenticate(user=self.user)
        self.client.post(reverse("favorite-list"), {"post": self.post.id})
        res = self.client.post(reverse("favorite-list"), {"post": self.post.id})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)


class MessageTests(TestCase):
    """Тесты сообщений."""

    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username="alice", password="testpass123")
        self.user2 = User.objects.create_user(username="bob", password="testpass123")

    def test_send_message(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.post(reverse("message-list"), {"recipient": self.user2.id, "text": "Hello!"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_list_messages(self):
        self.client.force_authenticate(user=self.user1)
        Message.objects.create(sender=self.user1, recipient=self.user2, text="Hi!")
        res = self.client.get(reverse("message-list"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_dialog(self):
        self.client.force_authenticate(user=self.user1)
        Message.objects.create(sender=self.user1, recipient=self.user2, text="Hello!")
        Message.objects.create(sender=self.user2, recipient=self.user1, text="Hi back!")
        res = self.client.get(f"/api/messages/dialog/{self.user2.id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_send_message_to_self(self):
        self.client.force_authenticate(user=self.user1)
        res = self.client.post(reverse("message-list"), {"recipient": self.user1.id, "text": "Self!"})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_read_message(self):
        self.client.force_authenticate(user=self.user1)
        msg = Message.objects.create(sender=self.user2, recipient=self.user1, text="Read me", is_read=False)
        res = self.client.post(f"/api/messages/{msg.id}/read/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        msg.refresh_from_db()
        self.assertTrue(msg.is_read)


class ChangePasswordTests(TestCase):
    """Тесты смены пароля."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", password="oldpass123")

    def test_change_password(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "old_password": "oldpass123",
            "new_password": "NewStrongPass123!",
            "new_password2": "NewStrongPass123!",
        }
        res = self.client.put(reverse("change_password"), data, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPass123!"))

    def test_wrong_old_password(self):
        self.client.force_authenticate(user=self.user)
        data = {
            "old_password": "wrongpass",
            "new_password": "NewStrongPass123!",
            "new_password2": "NewStrongPass123!",
        }
        res = self.client.put(reverse("change_password"), data, format="json")
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
