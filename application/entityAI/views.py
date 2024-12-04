from rest_framework.decorators import api_view
from rest_framework.views import APIView
from rest_framework import status, viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from application.entityAI.models import EntityAI, EntityAIType, EntityAITag
from application.user.models import Like

from .serializers import EntityAISerializer, EntityAITypeSerializer, EntityAITagSerializer

from utils.api_utils import success_response, fail_response


class LikeView(APIView):
    def post(self, request, *args, **kwargs):
        user = request.user
        entity_id = request.data.get('entity_id')
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
        entity_id = request.query_params.get('entity_id')
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


class EntityAIViewSet(viewsets.ModelViewSet):
    queryset = EntityAI.objects.all()
    serializer_class = EntityAISerializer

    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['type']
    ordering_fields = ['average_score']

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return success_response(message="删除成功")

