from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse
from django.utils import timezone
from users.models import User
from posts.models import Post
from PIL import Image
import io


def create_test_image():
    """Створює тестове зображення для upload."""
    image = Image.new("RGB", (100, 100))
    temp_file = io.BytesIO()
    image.save(temp_file, format="JPEG")
    temp_file.name = "test.jpg"
    temp_file.seek(0)
    return temp_file


class PostAPITests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", password="testpass123"
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.list_url = reverse("posts:posts-list")

    def test_create_post(self):
        """Перевірка звичайного створення посту."""
        data = {"content": "This is a test post"}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Post.objects.count(), 1)

    def test_create_post_with_image(self):
        """Створення посту з зображенням."""
        image = create_test_image()
        data = {"content": "Post with image", "image": image}
        response = self.client.post(self.list_url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Post.objects.first().image)

    def test_create_scheduled_post(self):
        """Запланований пост через 1 хвилину."""
        future_time = timezone.now() + timezone.timedelta(minutes=1)
        data = {"content": "Scheduled post", "scheduled_at": future_time.isoformat()}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertIn("detail", response.data)
        self.assertEqual(
            response.data["detail"], "The publication has been successfully scheduled."
        )

    def test_retrieve_post_list(self):
        Post.objects.create(author=self.user, content="Post 1")
        Post.objects.create(author=self.user, content="Post 2")
        response = self.client.get(self.list_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_retrieve_single_post(self):
        post = Post.objects.create(author=self.user, content="Unique post")
        url = reverse("posts:posts-detail", args=[post.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["content"], "Unique post")

    def test_update_post(self):
        post = Post.objects.create(author=self.user, content="Old content")
        url = reverse("posts:posts-detail", args=[post.id])
        data = {"content": "Updated content"}
        response = self.client.patch(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.content, "Updated content")

    def test_delete_post(self):
        post = Post.objects.create(author=self.user, content="To be deleted")
        url = reverse("posts:posts-detail", args=[post.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), 0)

    def test_unauthenticated_post_creation(self):
        """Пост без авторизації — має повернути 401."""
        self.client.logout()
        data = {"content": "Unauthorized post"}
        response = self.client.post(self.list_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
