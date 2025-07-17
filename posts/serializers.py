from rest_framework import serializers
from django.utils import timezone
from posts.models import Post


class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.CharField(source="author.username", read_only=True)
    like_count = serializers.SerializerMethodField()
    scheduled_at = serializers.DateTimeField(
        required=False,
        write_only=True,
        allow_null=True,
        help_text="Date and time for scheduled post. Format: '2025-07-11T01:45:00' (local time) or '2025-07-10T22:45:00Z' (UTC)."
        " If specified and in the future, the post will be scheduled.",
    )

    class Meta:
        model = Post
        fields = [
            "id",
            "author",
            "author_username",
            "content",
            "image",
            "created_at",
            "updated_at",
            "like_count",
            "scheduled_at",
        ]
        read_only_fields = ["author", "created_at", "updated_at"]

    def get_like_count(self, obj):
        return obj.like_count if hasattr(obj, "like_count") else 0

    def create(self, validated_data):
        scheduled_at = validated_data.pop("scheduled_at", None)
        author = self.context["request"].user

        image_file = validated_data.pop("image", None)
        image_path_for_celery = None

        if image_file:
            from django.core.files.storage import default_storage
            from django.core.files.base import ContentFile
            import os

            filename = default_storage.get_available_name(
                os.path.join("post_images", image_file.name)
            )
            image_path_for_celery = default_storage.save(
                filename, ContentFile(image_file.read())
            )

        if scheduled_at:
            """CORRECT WORKING WITH TIME ZONES"""
            from django.conf import settings
            import pytz

            """Obtaining the current time in the local time zone"""
            local_tz = pytz.timezone(settings.TIME_ZONE)
            now = timezone.now()

            print(f" System time Django: {now}")
            print(f" Local time: {now.astimezone(local_tz)}")

            """Make sure that scheduled_at has a time zone"""
            if scheduled_at.tzinfo is None:
                """If the time zone is not specified, assume that it is local time"""
                scheduled_at = local_tz.localize(scheduled_at)
                print(f" Scheduled time (localized): {scheduled_at}")

            """Convert to UTC for Celery"""
            now_utc = now.astimezone(pytz.UTC)
            scheduled_at_utc = scheduled_at.astimezone(pytz.UTC)

            print(f" Current time (UTC): {now_utc}")
            print(f" Scheduled time (UTC): {scheduled_at_utc}")

            """Check if the time is in the future"""
            if scheduled_at_utc > now_utc:
                delay_seconds = (scheduled_at_utc - now_utc).total_seconds()

                print(
                    f" Delay: {delay_seconds} seconds ({delay_seconds / 60:.1f} minutes)"
                )

                """CHECK: minimum delay"""
                if delay_seconds < 5:
                    print("⚠️ Delay less than 5 seconds, create a post now")

                    post_data = {"author": author, "content": validated_data["content"]}
                    if image_file:
                        post_data["image"] = image_file
                    post = Post.objects.create(**post_data)
                    return post

                from posts.tasks import create_scheduled_post

                """USE COUNTDOWN with rounding"""
                task = create_scheduled_post.apply_async(
                    args=[author.id, validated_data["content"], image_path_for_celery],
                    countdown=max(1, int(delay_seconds)),
                )

                return {
                    "detail": "The publication has been successfully scheduled.",
                    "status": "scheduled",
                    "task_id": task.id,
                    "scheduled_time_local": scheduled_at.astimezone(local_tz).strftime(
                        "%Y-%m-%d %H:%M:%S %Z"
                    ),
                    "scheduled_time_utc": scheduled_at_utc.strftime(
                        "%Y-%m-%d %H:%M:%S UTC"
                    ),
                    "current_time_local": now.astimezone(local_tz).strftime(
                        "%Y-%m-%d %H:%M:%S %Z"
                    ),
                    "current_time_utc": now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "delay_seconds": delay_seconds,
                    "delay_minutes": round(delay_seconds / 60, 1),
                    "author": author.username,
                    "content_preview": (
                        validated_data["content"][:100] + "..."
                        if len(validated_data["content"]) > 100
                        else validated_data["content"]
                    ),
                }
            else:
                print("Scheduled time in the past, create post now")

        """Create post now"""
        post_data = {"author": author, "content": validated_data["content"]}
        if image_file:
            post_data["image"] = image_file

        post = Post.objects.create(**post_data)
        return post
