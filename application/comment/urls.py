from django.urls import path
from application.comment import views
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'comment', views.CommentViewSet, basename='评论')
router.register(r'notice', views.NoticeViewSet, basename='通知')

urlpatterns = router.urls