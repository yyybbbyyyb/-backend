from rest_framework import viewsets, status
from django.db import transaction
from django.db.models import Avg, F, FloatField, Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models.functions import Round
from rest_framework.exceptions import PermissionDenied

from .models import Comment, Notice
from .serializers import CommentSerializer, NoticeSerializer

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


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by('-created_time').annotate(
        average_score=Round((
                                    Sum('score1', output_field=FloatField()) +
                                    Sum('score2', output_field=FloatField()) +
                                    Sum('score3', output_field=FloatField()) +
                                    Sum('score4', output_field=FloatField())
                            ) / 4, 2)  # 保留两位小数
    )
    serializer_class = CommentSerializer

    pagination_class = CustomPageNumberPagination  # 自定义分页器
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['entityAI', 'is_special', 'type', 'author']

    def perform_create(self, serializer):
        """
        在创建评论时，更新 EntityAI 的评分。
        """
        with transaction.atomic():
            comment = serializer.save(author=self.request.user)  # 保存评论并设置作者
            self.update_entityAI_scores(comment.entityAI)

    def perform_update(self, serializer):
        """
        在更新评论时，重新计算并更新 EntityAI 的评分。
        """
        with transaction.atomic():
            comment = serializer.save()  # 更新评论
            self.update_entityAI_scores(comment.entityAI)

    def perform_destroy(self, instance):
        """
        在删除评论时，重新计算并更新 EntityAI 的评分。
        """
        with transaction.atomic():
            entityAI = instance.entityAI  # 获取相关的实体AI
            instance.delete()  # 删除评论
            self.update_entityAI_scores(entityAI)

    def update_entityAI_scores(self, entityAI):
        """
        重新计算并更新 EntityAI 的评分。
        """
        scores = Comment.objects.filter(entityAI=entityAI).aggregate(
            avg_score1=Avg('score1'),
            avg_score2=Avg('score2'),
            avg_score3=Avg('score3'),
            avg_score4=Avg('score4')
        )

        # 更新 EntityAI 的评分细则和平均分
        entityAI.total_score1 = scores['avg_score1'] or 0
        entityAI.total_score2 = scores['avg_score2'] or 0
        entityAI.total_score3 = scores['avg_score3'] or 0
        entityAI.total_score4 = scores['avg_score4'] or 0
        entityAI.save()

class NoticeViewSet(viewsets.ModelViewSet):
    queryset = Notice.objects.all().order_by('-created_time')  # 按时间倒序排列
    serializer_class = NoticeSerializer

    pagination_class = CustomPageNumberPagination  # 自定义分页器

    def perform_create(self, serializer):
        """
        在创建通知时，设置作者。
        """
        if not self.request.user.is_staff:
            raise PermissionDenied('只有管理员才能创建通知')  # 抛出权限异常
        serializer.save(author=self.request.user)

    def perform_update(self, serializer):
        """
        在更新通知时，确保只有管理员能操作。
        """
        if not self.request.user.is_staff:
            raise PermissionDenied('只有管理员才能更新通知')  # 抛出权限异常
        serializer.save()

    def perform_destroy(self, instance):
        """
        在删除通知时，确保只有管理员能操作。
        """
        if not self.request.user.is_staff:
            raise PermissionDenied('只有管理员才能删除通知')  # 抛出权限异常
        instance.delete()