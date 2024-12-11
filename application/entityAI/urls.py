from django.urls import path
from application.entityAI import views
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'entity-ai', views.EntityAIViewSet, basename='实体AI')
router.register(r'entity-ai-type', views.EntityAITypeViewSet, basename='实体AI类型')
router.register(r'entity-ai-tag', views.EntityAITagViewSet, basename='实体AI标签')

urlpatterns = [
    path('like/<int:entity_id>/', views.LikeView.as_view(), name='点赞'),
    path('recommend/', views.entityAI_recommend, name='推荐实体AI'),
    path('statistics/', views.entityAI_statistics, name='实体AI统计'),
    path('search/', views.search, name='实体AI搜索'),
    path('recommend-similar/', views.recommend_similar_entityAI, name='推荐实体AI'),
] + router.urls