from django.urls import path
from application.entityAI import views
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'entity-ai', views.EntityAIViewSet, basename='实体AI')
router.register(r'entity-ai-type', views.EntityAITypeViewSet, basename='实体AI类型')
router.register(r'entity-ai-tag', views.EntityAITagViewSet, basename='实体AI标签')

urlpatterns = [
    path('like/<int:entity_id>/', views.LikeView.as_view(), name='点赞'),
] + router.urls