from rest_framework import serializers
from .models import User
from django.utils import timezone
import re
from rest_framework.exceptions import ValidationError
from django_redis import get_redis_connection


def phone_validator(value):
    """
    简单的自定义手机号验证器
    """

    if not re.match(r"^(1[3|456789])\d{9}$", value):
        raise ValidationError('手机号格式错误')


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'gender', 'avatar', 'phone', 'email']
        read_only_fields = ['id', 'username']

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        if instance.avatar:
            avatar_url = self.context['request'].build_absolute_uri(instance.avatar.url)
        else:
            if instance.gender == 'M':
                avatar_url = self.context['request'].build_absolute_uri('/static/avatar/default_ava_mail.png')
            else:
                avatar_url = self.context['request'].build_absolute_uri('/static/avatar/default_ava_femail.png')
        representation['avatar'] = avatar_url

        # 计算用户使用天数
        representation['used_days'] = (timezone.now() - instance.date_joined).days

        representation['role'] = instance.is_staff and 'admin' or 'user'

        return representation

    def validate(self, data):
        cur_pwd = self.context['request'].data.get('current_password', None)
        new_pwd = self.context['request'].data.get('new_password', None)

        if new_pwd:
            if not cur_pwd:
                raise serializers.ValidationError({'current_password': '请输入当前密码'})

            if not self.instance.check_password(cur_pwd):
                raise serializers.ValidationError({'current_password': '当前密码错误'})
        return data

    def update(self, instance, validated_data):
        new_pwd = self.context['request'].data.get('new_password', None)

        if new_pwd:
            instance.set_password(new_pwd)

        return super().update(instance, validated_data)


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    phone = serializers.CharField(label='手机号', validators=[phone_validator, ])
    code = serializers.CharField(label='短信验证码')

    class Meta:
        model = User
        fields = ['username', 'password', 'phone', 'code']

    def create(self, validated_data):
        validated_data.pop('code')
        return User.objects.create_user(**validated_data)

    def validate_phone(self, value):
        if User.objects.filter(phone=value).exists():
            raise ValidationError('该手机号已被注册')
        return value

    def validate_code(self, value):
        if len(value) != 4:
            raise ValidationError('验证码格式错误')
        if not value.isdecimal():
            raise ValidationError('验证码格式错误')

        phone = self.initial_data['phone']
        conn = get_redis_connection()
        code = conn.get(phone)

        if not code:
            raise ValidationError('验证码已过期')
        if value != code.decode('utf-8'):
            raise ValidationError('验证码错误')

        return value


class MessageSerializer(serializers.Serializer):
    """
    用于给手机发送短信时验证手机号是否正确的序列化类
    """

    phone = serializers.CharField(label='phone', validators=[phone_validator, ])
