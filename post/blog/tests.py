from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

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

    def test_public_profile_hides_private_fields(self):
        res = self.client.get(reverse("user_profile", args=[self.user.id]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn("email", res.data)
        self.assertNotIn("phone", res.data)
        self.assertNotIn("age", res.data)

    def test_me_returns_private_fields(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get(reverse("me"))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("email", res.data)
        self.assertIn("phone", res.data)


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

    def test_ordering_by_favorites_count(self):
        other = User.objects.create_user(username="fan2", password="testpass123")
        low = Post.objects.create(
            title="Low", text="Text", author=self.user, status="published"
        )
        high = Post.objects.create(
            title="High", text="Text", author=self.user, status="published"
        )
        Favorite.objects.create(user=self.user, post=low)
        Favorite.objects.create(user=self.user, post=high)
        Favorite.objects.create(user=other, post=high)

        res = self.client.get(f"{reverse('post-list')}?ordering=-favorites_count")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        results = res.data["results"]
        ids = [post["id"] for post in results]
        self.assertEqual(results[0]["id"], high.id)
        self.assertEqual(results[0]["favorites_count"], 2)
        self.assertEqual(results[1]["id"], low.id)
        self.assertEqual(results[1]["favorites_count"], 1)

    def test_detail_returns_favorite_id(self):
        self.client.force_authenticate(user=self.user)
        favorite = Favorite.objects.create(user=self.user, post=self.post)
        res = self.client.get(reverse("post-detail", args=[self.post.id]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["favorite_id"], favorite.id)
        self.assertTrue(res.data["is_favorited"])
        self.assertEqual(res.data["favorites_count"], 1)

    def test_detail_favorite_id_is_null_when_not_favorited(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get(reverse("post-detail", args=[self.post.id]))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIsNone(res.data["favorite_id"])
        self.assertFalse(res.data["is_favorited"])


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
        self.user3 = User.objects.create_user(username="carol", password="testpass123")

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

    def test_dialogs_requires_auth(self):
        res = self.client.get("/api/messages/dialogs/")
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_dialogs_lists_peers_with_unread_and_last_message(self):
        self.client.force_authenticate(user=self.user1)
        Message.objects.create(sender=self.user1, recipient=self.user2, text="First")
        Message.objects.create(sender=self.user2, recipient=self.user1, text="Unread 1")
        Message.objects.create(sender=self.user2, recipient=self.user1, text="Unread 2")
        Message.objects.create(sender=self.user3, recipient=self.user1, text="From carol", is_read=True)

        res = self.client.get("/api/messages/dialogs/")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        dialogs = {dialog["username"]: dialog for dialog in res.data}
        self.assertEqual(set(dialogs), {"bob", "carol"})
        self.assertEqual(dialogs["bob"]["user_id"], self.user2.id)
        self.assertEqual(dialogs["bob"]["unread_count"], 2)
        self.assertEqual(dialogs["bob"]["last_message"], "Unread 2")
        self.assertEqual(dialogs["carol"]["unread_count"], 0)
        self.assertEqual(dialogs["carol"]["last_message"], "From carol")

    def test_dialog_returns_latest_messages_with_limit(self):
        self.client.force_authenticate(user=self.user1)
        for index in range(12):
            sender, recipient = (
                (self.user1, self.user2) if index % 2 == 0 else (self.user2, self.user1)
            )
            Message.objects.create(sender=sender, recipient=recipient, text=f"msg {index}")

        res = self.client.get(f"/api/messages/dialog/{self.user2.id}/?limit=5")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 5)
        self.assertEqual(
            [message["text"] for message in res.data],
            ["msg 7", "msg 8", "msg 9", "msg 10", "msg 11"],
        )

    def test_dialog_does_not_mark_messages_read(self):
        self.client.force_authenticate(user=self.user1)
        msg = Message.objects.create(
            sender=self.user2, recipient=self.user1, text="Unread", is_read=False
        )

        res = self.client.get(f"/api/messages/dialog/{self.user2.id}/")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        msg.refresh_from_db()
        self.assertFalse(msg.is_read)

    def test_dialog_read_marks_all_incoming(self):
        self.client.force_authenticate(user=self.user1)
        incoming = [
            Message.objects.create(
                sender=self.user2, recipient=self.user1, text=f"in {index}"
            )
            for index in range(3)
        ]
        outgoing = Message.objects.create(
            sender=self.user1, recipient=self.user2, text="out"
        )
        foreign = Message.objects.create(
            sender=self.user2, recipient=self.user3, text="not mine"
        )

        res = self.client.post(f"/api/messages/dialog/{self.user2.id}/read/")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["marked_read"], 3)
        for msg in incoming:
            msg.refresh_from_db()
            self.assertTrue(msg.is_read)
        outgoing.refresh_from_db()
        self.assertFalse(outgoing.is_read)
        foreign.refresh_from_db()
        self.assertFalse(foreign.is_read)


class DraftAccessTests(TestCase):
    """Доступ к черновикам и защита от невалидных id."""

    def setUp(self):
        self.client = APIClient()
        self.author = User.objects.create_user(username="draft_author", password="testpass123")
        self.other = User.objects.create_user(username="other_user", password="testpass123")
        self.draft = Post.objects.create(
            title="Draft", text="Secret", author=self.author, status="draft"
        )
        self.published = Post.objects.create(
            title="Published", text="Public", author=self.author, status="published"
        )

    def test_my_posts_requires_auth(self):
        res = self.client.get(reverse("post-my"))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_author_can_retrieve_own_draft(self):
        self.client.force_authenticate(user=self.author)
        res = self.client.get(f"/api/posts/{self.draft.id}/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data["title"], "Draft")

    def test_other_user_cannot_retrieve_draft(self):
        self.client.force_authenticate(user=self.other)
        res = self.client.get(f"/api/posts/{self.draft.id}/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_cannot_retrieve_draft(self):
        res = self.client.get(f"/api/posts/{self.draft.id}/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_draft_not_in_public_list(self):
        res = self.client.get(reverse("post-list"))
        ids = [post["id"] for post in res.data["results"]]
        self.assertNotIn(self.draft.id, ids)

    def test_other_user_cannot_list_draft_comments(self):
        self.client.force_authenticate(user=self.other)
        res = self.client.get(f"/api/posts/{self.draft.id}/comments/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_anonymous_cannot_list_draft_comments(self):
        res = self.client.get(f"/api/posts/{self.draft.id}/comments/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_author_can_list_draft_comments(self):
        self.client.force_authenticate(user=self.author)
        res = self.client.get(f"/api/posts/{self.draft.id}/comments/")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_other_user_cannot_comment_on_draft(self):
        self.client.force_authenticate(user=self.other)
        res = self.client.post(f"/api/posts/{self.draft.id}/comments/", {"text": "Hack"})
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_author_can_comment_on_own_draft(self):
        self.client.force_authenticate(user=self.author)
        res = self.client.post(f"/api/posts/{self.draft.id}/comments/", {"text": "Note"})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

    def test_non_numeric_post_id_returns_404(self):
        res = self.client.get("/api/posts/abc/comments/")
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_favorite_draft(self):
        self.client.force_authenticate(user=self.other)
        res = self.client.post(reverse("favorite-list"), {"post": self.draft.id})
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_can_favorite_published_post(self):
        self.client.force_authenticate(user=self.other)
        res = self.client.post(reverse("favorite-list"), {"post": self.published.id})
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)


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

    def test_change_password_blacklists_old_refresh_tokens(self):
        old_refresh = RefreshToken.for_user(self.user)
        self.client.force_authenticate(user=self.user)
        data = {
            "old_password": "oldpass123",
            "new_password": "NewStrongPass123!",
            "new_password2": "NewStrongPass123!",
        }
        res = self.client.put(reverse("change_password"), data, format="json")
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.client.force_authenticate(user=None)
        res = self.client.post(
            reverse("token_refresh"), {"refresh": str(old_refresh)}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        new_refresh = RefreshToken.for_user(self.user)
        res = self.client.post(
            reverse("token_refresh"), {"refresh": str(new_refresh)}, format="json"
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
