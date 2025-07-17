import os
from django.conf import settings
from posts.models import Post
from users.models import User
from celery import shared_task
from celery.utils.log import get_task_logger

"""Logger settings"""
logger = get_task_logger(__name__)


@shared_task
def create_scheduled_post(author_id, content, image_path=None):
    """
    Celery task to create a scheduled publication.

    Args:
        author_id: ID author of the post.
        content: Content of the post.
        image_path: Path to the image. (optional)
    """
    logger.info("=== START EXECUTING THE TASK ===")
    logger.info(f"Author ID: {author_id}")
    logger.info(f"Content: {content[:50]}...")
    logger.info(f"Image path: {image_path}")

    try:
        """Check if the author exists"""
        logger.info(f"Search for the author by ID: {author_id}")
        try:
            author = User.objects.get(id=author_id)
            logger.info(f"Author found: {author.email}")
        except User.DoesNotExist:
            error_msg = f"Author with ID {author_id} not found"
            logger.error(error_msg)
            raise Exception(error_msg)

        """Prepare data for creating a post"""
        post_data = {
            "author": author,
            "content": content,
        }

        """Image processing"""
        if image_path:
            logger.info(f"Image processing: {image_path}")
            """Check if the file exists"""
            full_path = os.path.join(settings.MEDIA_ROOT, image_path)
            if os.path.exists(full_path):
                post_data["image"] = image_path
                logger.info(f"Image added to post: {image_path}")
            else:
                logger.warning(f"Image file not found: {full_path}")

        """Creating a post"""
        logger.info("Creating a post...")
        post = Post.objects.create(**post_data)
        logger.info(f"Post created successfully! ID: {post.id}")

        result = {
            "status": "success",
            "post_id": post.id,
            "author_email": author.email,
            "content_preview": content[:50],
            "created_at": post.created_at.isoformat(),
        }

        logger.info("=== TASK COMPLETED SUCCESSFULLY ===")
        logger.info(f"Результат: {result}")

        return result

    except Exception as e:
        error_msg = f"Error creating scheduled post: {str(e)}"
        logger.error("=== ERROR IN TASK ===")
        logger.error(error_msg)
        logger.error(
            f"Data: author_id={author_id}, content='{content[:50]}...', image_path={image_path}"
        )
        raise e
