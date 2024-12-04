from rest_framework import serializers
from .models import Comment, Notice
from application.entityAI.models import EntityAI


class CommentSerializer(serializers.ModelSerializer):
    entityAI_id = serializers.PrimaryKeyRelatedField(
        queryset=EntityAI.objects.all(), source='entityAI', write_only=True
    )

    entityAI = serializers.SerializerMethodField()  # 替代嵌套序列化，返回所需字段
    author = serializers.SerializerMethodField()  # 替代嵌套序列化，返回所需字段

    class Meta:
        model = Comment
        fields = '__all__'

    def get_entityAI(self, obj):
        return {"id": obj.entityAI.id, "name": obj.entityAI.name}

    def get_author(self, obj):
        return {"id": obj.author.id, "username": obj.author.username}

    def validate_score1(self, value):
        if value != int(value):
            raise serializers.ValidationError("评分1必须是整数")

        if not (0 <= value <= 5):
            raise serializers.ValidationError("评分1必须在 0 到 5 之间")

        return value

    def validate_score2(self, value):
        if value != int(value):
            raise serializers.ValidationError("评分2必须是整数")

        if not (0 <= value <= 5):
            raise serializers.ValidationError("评分2必须在 0 到 5 之间")

        return value

    def validate_score3(self, value):
        if value != int(value):
            raise serializers.ValidationError("评分3必须是整数")

        if not (0 <= value <= 5):
            raise serializers.ValidationError("评分3必须在 0 到 5 之间")

        return value

    def validate_score4(self, value):
        if value != int(value):
            raise serializers.ValidationError("评分4必须是整数")

        if not (0 <= value <= 5):
            raise serializers.ValidationError("评分4必须在 0 到 5 之间")

        return value


class NoticeSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()  # 替代嵌套序列化，返回所需字段

    class Meta:
        model = Notice
        fields = '__all__'

    def get_author(self, obj):
        return {"id": obj.author.id, "username": obj.author.username}
