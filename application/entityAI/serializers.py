from rest_framework import serializers
from .models import EntityAI, EntityAIType, EntityAITag


class EntityAITypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityAIType
        fields = '__all__'


class EntityAITagSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityAITag
        fields = '__all__'


class EntityAISerializer(serializers.ModelSerializer):
    type = EntityAITypeSerializer(read_only=True)
    type_id = serializers.PrimaryKeyRelatedField(
        queryset=EntityAIType.objects.all(), source='type', write_only=True
    )
    entityAI_tags = EntityAITagSerializer(many=True, read_only=True)
    tags_id = serializers.PrimaryKeyRelatedField(
        queryset=EntityAITag.objects.all(), many=True, write_only=True, source='entityAI_tags'
    )

    class Meta:
        model = EntityAI
        fields = '__all__'
