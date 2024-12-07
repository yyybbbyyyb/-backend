from rest_framework import serializers
from .models import Comment, Notice
from application.entityAI.models import EntityAI
from application.user.models import User


class CommentSerializer(serializers.ModelSerializer):
    entityAI_id = serializers.PrimaryKeyRelatedField(
        queryset=EntityAI.objects.all(), source='entityAI', write_only=True
    )

    entityAI = serializers.SerializerMethodField()  # 替代嵌套序列化，返回所需字段
    author = serializers.SerializerMethodField()  # 替代嵌套序列化，返回所需字段

    created_time = serializers.DateTimeField(format='%Y-%m-%d %H:%M:%S', read_only=True)

    average_score = serializers.FloatField(read_only=True)

    class Meta:
        model = Comment
        fields = '__all__'

    def get_entityAI(self, obj):
        return {"id": obj.entityAI.id, "name": obj.entityAI.name}

    def get_author(self, obj):
        return {"id": obj.author.id, "username": obj.author.username}


class NoticeSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()  # 替代嵌套序列化，返回所需字段

    class Meta:
        model = Notice
        fields = '__all__'

    def get_author(self, obj):
        return {"id": obj.author.id, "username": obj.author.username}
