from django.db import IntegrityError
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory

from interactions.models import Follow, Like, Comment
from posts.models import Post
from interactions.serializers import FollowSerializer

User = get_user_model()


class FollowTests(TestCase):
    def setUp(self):
        self.follower = User.objects.create_user(
            username="follower", email="follower@test", password="pass"
        )
        self.following = User.objects.create_user(
            username="following", email="following@test", password="pass"
        )
        self.factory = APIRequestFactory()

    def test_create_follow(self):
        follow = Follow.objects.create(follower=self.follower, following=self.following)
        self.assertEqual(follow.follower, self.follower)
        self.assertEqual(follow.following, self.following)

    def test_follow_self_not_allowed(self):
        data = {"follower": self.follower.id, "following": self.follower.id}
        request = self.factory.post("/fake-url/")
        request.user = self.follower
        serializer = FollowSerializer(data=data, context={"request": request})

        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("You cannot follow yourself.", str(context.exception))

    def test_follow_requires_following_user(self):
        data = {"follower": self.follower.id}
        request = self.factory.post("/fake-url/")
        request.user = self.follower
        serializer = FollowSerializer(data=data, context={"request": request})

        with self.assertRaises(ValidationError) as context:
            serializer.is_valid(raise_exception=True)
        self.assertIn("This field is required.", str(context.exception))

    def test_duplicate_follow_not_allowed(self):
        Follow.objects.create(follower=self.follower, following=self.following)
        with self.assertRaises(Exception):
            Follow.objects.create(follower=self.follower, following=self.following)

    def test_serializer_output_fields(self):
        follow = Follow.objects.create(follower=self.follower, following=self.following)
        serializer = FollowSerializer(follow)
        self.assertEqual(serializer.data["follower"], self.follower.id)
        self.assertEqual(serializer.data["follower_username"], self.follower.username)
        self.assertEqual(serializer.data["following_username"], self.following.username)


class LikeTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="likeuser", email="likeuser@test", password="pass"
        )
        self.post = Post.objects.create(
            author=self.user,
            content="This is a test post",
        )

    def test_create_like(self):
        """
        Check that the like is created successfully
        """
        like = Like.objects.create(user=self.user, post=self.post)
        self.assertEqual(like.post, self.post)
        self.assertEqual(like.user, self.user)

    def test_unique_user_post_like(self):
        """
        Check that a single user cannot like the same post twice
        """
        Like.objects.create(user=self.user, post=self.post)
        with self.assertRaises(IntegrityError):
            Like.objects.create(user=self.user, post=self.post)


class CommentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="commentuser", email="commentuser@test", password="pass"
        )
        self.post = Post.objects.create(
            author=self.user,
            content="This is a test post for comments.",
        )

    def test_create_comment(self):
        comment = Comment.objects.create(
            user=self.user,
            post=self.post,
            content="This is a test post for comments.",
        )
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.content, "This is a test post for comments.")

    def test_duplicate_comment_raises_error(self):
        """
        The same user cannot leave two comments on the same post
        """
        Comment.objects.create(user=self.user, post=self.post, content="First comment.")
        with self.assertRaises(IntegrityError):
            Comment.objects.create(
                user=self.user, post=self.post, content="Second comment."
            )
