from rest_framework.decorators import api_view
from django.db.models import Count, Avg, Sum
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
    page_size = 8  # 默认每页数据量
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
    ).annotate(
        average_score=(
                              Sum('total_score1') +
                              Sum('total_score2') +
                              Sum('total_score3') +
                              Sum('total_score4')
                      ) / 4
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

    def get_queryset(self):
        queryset = super().get_queryset()

        # 检查是否有 `liked_by_user` 参数
        liked_by_user = self.request.query_params.get('liked_by_user')
        if liked_by_user == 'true':
            queryset = queryset.filter(like_entityAI__user=self.request.user)

        return queryset


@api_view(['GET'])
def entityAI_recommend(request):
    """
    推荐实体AI
    """

    high_score_entityAIs = (
        EntityAI.objects.all()
        .order_by('-average_score')
        .select_related('type')
    )

    high_score_recommend = []
    seen_types = set()

    for entityAI in high_score_entityAIs:
        if len(high_score_recommend) >= 3:
            break
        if entityAI.type not in seen_types:
            high_score_recommend.append({
                'title': f'{entityAI.type.name}高评分模型',
                'entityAI': entityAI
            })
            seen_types.add(entityAI.type)

    high_like_entityAIs = (
        EntityAI.objects.annotate(like_count=Count('like_entityAI'))
        .order_by('-like_count')
        .select_related('type')
    )

    high_like_recommend = []
    seen_types = set()

    for entityAI in high_like_entityAIs:
        if len(high_like_recommend) >= 3:
            break
        if entityAI.type not in seen_types:
            high_like_recommend.append({
                'title': f'{entityAI.type.name}高点赞模型',
                'entityAI': entityAI
            })
            seen_types.add(entityAI.type)

    recommendations = high_score_recommend + high_like_recommend

    serialized_recommendations = [
        {
            "title": rec["title"],
            "entity": EntityAISerializer(rec["entityAI"], context={"request": request}).data
        }
        for rec in recommendations
    ]

    return success_response(data=serialized_recommendations)


@api_view(['GET'])
def entityAI_statistics(request):
    """
    获取 EntityAI 的统计数据
    """
    # 1. 总评分对比（前 10）
    total_scores = EntityAI.objects.annotate(
        total_score=(
                            Sum('total_score1') +
                            Sum('total_score2') +
                            Sum('total_score3') +
                            Sum('total_score4')
                    ) / 4
    ).values('name', 'total_score').order_by('-total_score')[:10]

    # 2. 点赞量对比（前 10）
    like_counts = EntityAI.objects.annotate(like_count=Count('like_entityAI')).values('name', 'like_count').order_by(
        '-like_count')[:10]

    # 3. 各类型的数量、平均评分和点赞量
    type_statistics = EntityAIType.objects.annotate(
        entity_count=Count('entityai'),
    ).values('name', 'entity_count').order_by('-entity_count')

    # 4. 评分细则前五
    score_details = EntityAI.objects.annotate(
        average_score=(
                              Sum('total_score1') +
                              Sum('total_score2') +
                              Sum('total_score3') +
                              Sum('total_score4')
                      ) / 4
    ).values('name', 'total_score1', 'total_score2', 'total_score3', 'total_score4', 'average_score').order_by(
        '-average_score')[:5]

    # 5. 点赞细则前五
    like_details = EntityAI.objects.annotate(
        like_count=Count('like_entityAI')
    ).values(
        'name', 'total_score1', 'total_score2', 'total_score3', 'total_score4'
    ).order_by('-like_count')[:5]

    # 6. 每个维度的前三名
    top_score1 = EntityAI.objects.values('name', 'total_score1').order_by('-total_score1')[:3]
    top_score2 = EntityAI.objects.values('name', 'total_score2').order_by('-total_score2')[:3]
    top_score3 = EntityAI.objects.values('name', 'total_score3').order_by('-total_score3')[:3]
    top_score4 = EntityAI.objects.values('name', 'total_score4').order_by('-total_score4')[:3]

    return success_response(data={
        "total_scores": list(total_scores),
        "like_counts": list(like_counts),
        "type_statistics": list(type_statistics),
        "score_details": list(score_details),
        "like_details": list(like_details),
        "top_scores": {
            "math_ability": list(top_score1),
            "language_ability": list(top_score2),
            "image_ability": list(top_score3),
            "text_ability": list(top_score4),
        }
    })
