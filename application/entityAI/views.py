from rest_framework.decorators import api_view, permission_classes
from django.db.models import Count, Avg, Sum, FloatField
from django.db.models import OuterRef, Subquery
from django.db.models.functions import Substr, Round, Cast
from rest_framework.views import APIView
from rest_framework import status, viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from pypinyin import lazy_pinyin, Style
from rest_framework.filters import OrderingFilter
from haystack.query import SearchQuerySet
from rest_framework.permissions import AllowAny

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

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
    queryset = EntityAI.objects.annotate(
        like_count=Count('like_entityAI'),
        average_score=Round(
            Subquery(
                EntityAI.objects.filter(id=OuterRef('id')).annotate(
                    total_avg=(
                                      Sum('total_score1', output_field=FloatField()) +
                                      Sum('total_score2', output_field=FloatField()) +
                                      Sum('total_score3', output_field=FloatField()) +
                                      Sum('total_score4', output_field=FloatField())
                              ) / 4
                ).values('total_avg')[:1],
                output_field=FloatField()
            ), 2
        )
    )

    serializer_class = EntityAISerializer
    pagination_class = CustomPageNumberPagination

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['type']
    ordering_fields = ['average_score', 'like_count', 'pinyin_name']

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
        EntityAI.objects.all().annotate(
            average_score=Round((
                                        Sum('total_score1', output_field=FloatField()) +
                                        Sum('total_score2', output_field=FloatField()) +
                                        Sum('total_score3', output_field=FloatField()) +
                                        Sum('total_score4', output_field=FloatField())
                                ) / 4, 2)  # 保留两位小数
        ).order_by('-average_score').select_related('type')
    )

    high_score_recommend = []
    seen_types = set()

    for entityAI in high_score_entityAIs:
        if len(high_score_recommend) >= 2:
            break
        if entityAI.type not in seen_types:
            high_score_recommend.append({
                'title': f'{entityAI.type.name}高评分模型',
                'entityAI': entityAI
            })
            seen_types.add(entityAI.type)

    high_like_entityAIs = (
        EntityAI.objects.annotate(
            like_count=Count('like_entityAI'),
            average_score=Round(
                Subquery(
                    EntityAI.objects.filter(id=OuterRef('id')).annotate(
                        total_avg=(
                                          Sum('total_score1', output_field=FloatField()) +
                                          Sum('total_score2', output_field=FloatField()) +
                                          Sum('total_score3', output_field=FloatField()) +
                                          Sum('total_score4', output_field=FloatField())
                                  ) / 4
                    ).values('total_avg')[:1],
                    output_field=FloatField()
                ), 2
            )
        )
        .order_by('-like_count')
        .select_related('type')
    )

    high_like_recommend = []
    seen_types = set()

    for entityAI in high_like_entityAIs:
        if len(high_like_recommend) >= 2:
            break
        if entityAI.type not in seen_types:
            high_like_recommend.append({
                'title': f'{entityAI.type.name}高收藏模型',
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
    获取 entityAI 的统计数据
    """
    # 1. 总评分对比（前 10）
    total_scores = EntityAI.objects.annotate(
        total_score=Round((
                                  Sum('total_score1', output_field=FloatField()) +
                                  Sum('total_score2', output_field=FloatField()) +
                                  Sum('total_score3', output_field=FloatField()) +
                                  Sum('total_score4', output_field=FloatField())
                          ) / 4, 2)  # 保留两位小数
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
        total_score1_rounded=Round(Cast(Sum('total_score1', output_field=FloatField()), FloatField()), 2),
        total_score2_rounded=Round(Cast(Sum('total_score2', output_field=FloatField()), FloatField()), 2),
        total_score3_rounded=Round(Cast(Sum('total_score3', output_field=FloatField()), FloatField()), 2),
        total_score4_rounded=Round(Cast(Sum('total_score4', output_field=FloatField()), FloatField()), 2),
        average_score=Round((
                                    Sum('total_score1', output_field=FloatField()) +
                                    Sum('total_score2', output_field=FloatField()) +
                                    Sum('total_score3', output_field=FloatField()) +
                                    Sum('total_score4', output_field=FloatField())
                            ) / 4, 2)
    ).values(
        'name',
        'total_score1_rounded',
        'total_score2_rounded',
        'total_score3_rounded',
        'total_score4_rounded',
        'average_score'
    ).order_by('-average_score')[:5]

    # 5. 点赞细则前五
    like_details = EntityAI.objects.annotate(
        total_score1_rounded=Round(
            Subquery(
                EntityAI.objects.filter(id=OuterRef('id')).annotate(
                    total=Sum('total_score1', output_field=FloatField())
                ).values('total')[:1],
                output_field=FloatField()
            ), 2
        ),
        total_score2_rounded=Round(
            Subquery(
                EntityAI.objects.filter(id=OuterRef('id')).annotate(
                    total=Sum('total_score2', output_field=FloatField())
                ).values('total')[:1],
                output_field=FloatField()
            ), 2
        ),
        total_score3_rounded=Round(
            Subquery(
                EntityAI.objects.filter(id=OuterRef('id')).annotate(
                    total=Sum('total_score3', output_field=FloatField())
                ).values('total')[:1],
                output_field=FloatField()
            ), 2
        ),
        total_score4_rounded=Round(
            Subquery(
                EntityAI.objects.filter(id=OuterRef('id')).annotate(
                    total=Sum('total_score4', output_field=FloatField())
                ).values('total')[:1],
                output_field=FloatField()
            ), 2
        ),
        like_count=Subquery(
            EntityAI.objects.filter(id=OuterRef('id')).annotate(
                count=Count('like_entityAI')
            ).values('count')[:1],
            output_field=FloatField()
        )
    ).values(
        'name',
        'total_score1_rounded',
        'total_score2_rounded',
        'total_score3_rounded',
        'total_score4_rounded',
        'like_count'
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


@api_view(['GET'])
@permission_classes([AllowAny])
def search(request):
    query = request.GET.get('q', '')
    if not query:
        return fail_response(message="请输入搜索关键词", status_code=status.HTTP_400_BAD_REQUEST)

    # 搜索结果
    sqs = SearchQuerySet().filter(content=query)
    ids = [result.object.id for result in sqs if result.object]  # 获取搜索结果中对应的实体 ID

    # 查询数据库，计算评分和点赞量
    queryset = EntityAI.objects.filter(id__in=ids).annotate(
        like_count=Count('like_entityAI'),  # 点赞量
        average_score=Round(  # 平均评分
            Subquery(
                EntityAI.objects.filter(id=OuterRef('id')).annotate(
                    total_avg=(
                                      Sum('total_score1', output_field=FloatField()) +
                                      Sum('total_score2', output_field=FloatField()) +
                                      Sum('total_score3', output_field=FloatField()) +
                                      Sum('total_score4', output_field=FloatField())
                              ) / 4
                ).values('total_avg')[:1],
                output_field=FloatField()
            ), 2
        )
    )

    # 通过 `type` 过滤
    type_id = request.GET.get('type', None)
    if type_id:
        queryset = queryset.filter(type__id=type_id)

    # 排序支持
    ordering = request.GET.get('ordering', None)
    if ordering in ['average_score', '-average_score', 'like_count', '-like_count', 'pinyin_name', '-pinyin_name']:
        queryset = queryset.order_by(ordering)

    # 使用分页器对结果进行分页
    paginator = CustomPageNumberPagination()
    page = paginator.paginate_queryset(queryset, request)

    if page is not None:
        serializer = EntityAISerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)

    # 如果没有分页，返回所有结果
    serializer = EntityAISerializer(queryset, many=True, context={'request': request})
    return success_response(data=serializer.data)

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
import numpy as np
from rest_framework.decorators import api_view
from rest_framework.response import Response
from application.entityAI.models import EntityAI
from application.user.models import Like
from .serializers import EntityAISerializer


@api_view(['GET'])
def recommend_similar_entityAI(request):
    """
    基于当前 AI 信息和用户收藏推荐类似的 3 个 AI
    """
    entity_id = request.GET.get('entityAI')

    try:
        # 获取当前 AI
        all_entities = EntityAI.objects.all()
        current_entity = EntityAI.objects.get(id=entity_id)
    except EntityAI.DoesNotExist:
        return fail_response(message="AI 不存在", status_code=404)

    # 获取用户收藏的 AI
    user = request.user
    if user.is_authenticated:
        user_liked_entities = EntityAI.objects.filter(like_entityAI__user=user)
    else:
        user_liked_entities = EntityAI.objects.none()

    # 文本特征：名称和描述
    text_data = [f"{entity.name} {entity.description}" for entity in all_entities]

    # 数值特征：评分、点赞量、用户是否收藏
    scores = np.array([
        [
            entity.total_score1 + entity.total_score2 + entity.total_score3 + entity.total_score4,
            entity.like_entityAI.count(),
            1 if entity in user_liked_entities else 0  # 收藏特征
        ] for entity in all_entities
    ])

    # 标准化数值特征
    scaler = MinMaxScaler()
    normalized_scores = scaler.fit_transform(scores)

    # 文本特征向量化
    vectorizer = TfidfVectorizer()
    text_vectors = vectorizer.fit_transform(text_data)

    # 合并文本向量和数值特征向量
    combined_vectors = np.hstack([text_vectors.toarray(), normalized_scores])

    # 获取当前实体的索引
    current_index = list(all_entities).index(current_entity)

    # 计算相似度
    similarities = cosine_similarity([combined_vectors[current_index]], combined_vectors)[0]

    # 排序并获取最相似的 3 个实体
    similar_indices = similarities.argsort()[::-1][1:4]  # 排除当前实体

    # 获取推荐的实体
    # 将 numpy.int64 转换为标准的 int
    recommended_entities = [all_entities[int(i)] for i in similar_indices]

    # 序列化推荐结果
    serializer = EntityAISerializer(recommended_entities, many=True, context={'request': request})
    return success_response(data=serializer.data)

