from rest_framework import serializers
from .models import EntityAI, EntityAIType, EntityAITag
from application.user.models import Like


class EntityAITypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityAIType
        fields = '__all__'


class EntityAITagSerializer(serializers.ModelSerializer):
    entityAI = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=EntityAI.objects.all(),
        required=False  # 不强制在创建或更新时提供
    )

    class Meta:
        model = EntityAITag
        fields = '__all__'


class EntityAISerializer(serializers.ModelSerializer):
    type_id = serializers.PrimaryKeyRelatedField(
        queryset=EntityAIType.objects.all(), source='type', write_only=True
    )
    tags_id = serializers.PrimaryKeyRelatedField(
        queryset=EntityAITag.objects.all(), many=True, write_only=True, source='entityAI_tags', required=False
    )

    type = serializers.SerializerMethodField()

    entityAI_tags = serializers.SerializerMethodField()

    like_count = serializers.IntegerField(read_only=True)

    is_liked = serializers.SerializerMethodField()

    def get_type(self, obj):
        return {"id": obj.type.id, "name": obj.type.name}

    def get_entityAI_tags(self, obj):
        return [{"id": tag.id, "name": tag.name} for tag in obj.entityAI_tags.all()]

    def get_is_liked(self, obj):
        """判断当前用户是否已点赞"""
        user = self.context['request'].user
        return Like.objects.filter(user=user, entityAI=obj).exists()

    class Meta:
        model = EntityAI
        fields = '__all__'
        extra_fields = ['is_liked']  # 声明动态字段