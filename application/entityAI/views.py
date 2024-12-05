from django.db.models import Count
from django.db.models.functions import Substr
from rest_framework.views import APIView
from rest_framework import status, viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend

from application.entityAI.models import EntityAI, EntityAIType, EntityAITag
from application.user.models import Like

from .serializers import EntityAISerializer, EntityAITypeSerializer, EntityAITagSerializer

from utils.api_utils import success_response, fail_response

from rest_framework.pagination import PageNumberPagination

class CustomPageNumberPagination(PageNumberPagination):
    page_size = 10  # 默认每页数据量
    page_size_query_param = 'page_size'  # 允许前端传递的参数名
    max_page_size = 100  # 限制每页的最大数据量

    def paginate_queryset(self, queryset, request, view=None):
        # 如果没有传入 `page` 参数，返回全部数据
        if 'page' not in request.query_params or request.query_params['page'] == '':
            return None  # 禁用分页
        return super().paginate_queryset(queryset, request, view)


class LikeView(APIView):
    def post(self, request, *args, **kwargs):
        user = request.user
        entity_id = kwargs.get('entity_id')
        try:
            entity = EntityAI.objects.get(id=entity_id)
        except EntityAI.DoesNotExist:
            return fail_response(message="实体不存在", status_code=status.HTTP_400_BAD_REQUEST)

        if Like.objects.filter(user=user, entityAI=entity).exists():
            return fail_response(message="已经点赞", status_code=status.HTTP_400_BAD_REQUEST)

        Like.objects.create(user=user, entityAI=entity)
        return success_response(message="点赞成功")

    def delete(self, request, *args, **kwargs):
        user = request.user
        entity_id = kwargs.get('entity_id')
        try:
            entity = EntityAI.objects.get(id=entity_id)
        except EntityAI.DoesNotExist:
            return fail_response(message="实体不存在", status_code=status.HTTP_400_BAD_REQUEST)

        like = Like.objects.filter(user=user, entityAI=entity).first()
        if like:
            like.delete()
            return success_response(message="取消点赞成功")
        return fail_response(message="未点赞", status_code=status.HTTP_400_BAD_REQUEST)


class EntityAITypeViewSet(viewsets.ModelViewSet):
    queryset = EntityAIType.objects.all()
    serializer_class = EntityAITypeSerializer


class EntityAITagViewSet(viewsets.ModelViewSet):
    queryset = EntityAITag.objects.all()
    serializer_class = EntityAITagSerializer

    filter_backends = [DjangoFilterBackend]
    filterset_fields = []

    def get_queryset(self):
        queryset = super().get_queryset()
        entityAI_id = self.request.query_params.get('entityAI')

        # 检查 entityAI_id 是否为有效的整数值
        if entityAI_id and entityAI_id.isdigit():
            entityAI_id = int(entityAI_id)
            # 筛选与指定 entityAI 关联的 Tags
            queryset = queryset.filter(entityAI__id=entityAI_id)

        return queryset

class EntityAIViewSet(viewsets.ModelViewSet):
    queryset = EntityAI.objects.all().annotate(
        first_letter=Substr('name', 1, 1)
    ).annotate(
        like_count=Count('like_entityAI')
    )
    serializer_class = EntityAISerializer
    pagination_class = CustomPageNumberPagination

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['type']
    ordering_fields = ['average_score', 'like_count', 'first_letter']

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return success_response(message="删除成功")

