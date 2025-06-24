from django.urls import path, include
from interactions.views import FollowViewSet, LikeViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("follows", FollowViewSet)
router.register("likes", LikeViewSet)
urlpatterns = [path("", include(router.urls))]

app_name = "interactions"
