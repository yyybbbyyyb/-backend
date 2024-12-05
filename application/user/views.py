from PIL.ImagePalette import random
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes, permission_classes, authentication_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.views import APIView
from .serializers import UserSerializer, UserRegisterSerializer, MessageSerializer
from utils.api_utils import success_response, fail_response
from utils.sms_utils import send_sms
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
import random
from django_redis import get_redis_connection
from django.conf import settings
from .models import User


@api_view(['GET'])
@authentication_classes([])
@permission_classes([AllowAny])
def get_phone_code(request):
    ser = MessageSerializer(data=request.query_params)
    if not ser.is_valid():
        return fail_response(errors=ser.errors, message="手机号格式错误", status_code=status.HTTP_400_BAD_REQUEST)


    phone = ser.validated_data.get('phone')
    code = str(random.randint(1000, 9999))

    result = send_sms(phone, {"code": code})
    if result.get("Code") != "OK":
        return fail_response(errors=result.get("Message"), message="获取手机验证码失败", status_code=status.HTTP_400_BAD_REQUEST)

    conn = get_redis_connection()
    conn.set(phone, code, ex=60 * settings.ALIYUN_SMS_LIMIT_TIME)

    return success_response(message="获取手机验证码成功")




@api_view(['POST'])
@authentication_classes([])  # 不要求JWT认证
@permission_classes([AllowAny])
def register(request):
    serializer = UserRegisterSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return success_response(message="用户注册成功", status_code=status.HTTP_201_CREATED)
    return fail_response(errors=serializer.errors, message="用户注册失败", status_code=status.HTTP_400_BAD_REQUEST)


# 继承TokenObtainPairView
class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)  # 调用父类方法
        data = response.data

        # 使用自定义的success_response格式返回
        return success_response(data=data, message="登录成功", status_code=status.HTTP_200_OK)

@api_view(['POST'])
@authentication_classes([])  # 不要求JWT认证
@permission_classes([AllowAny])
def login_with_code(request):
    phone = request.data.get('phone')
    code = request.data.get('code')

    if not phone or not code:
        return fail_response(message="手机号或验证码不能为空", status_code=status.HTTP_400_BAD_REQUEST)

    conn = get_redis_connection()
    saved_code = conn.get(phone)

    user = User.objects.filter(phone=phone).first()

    if not user:
        return fail_response(message="用户不存在", status_code=status.HTTP_400_BAD_REQUEST)

    if not saved_code:
        return fail_response(message="验证码已过期", status_code=status.HTTP_400_BAD_REQUEST)

    if int(saved_code.decode()) != int(code):
        print(saved_code, code)
        return fail_response(message="验证码错误", status_code=status.HTTP_400_BAD_REQUEST)

    refresh = RefreshToken.for_user(user)

    data = {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

    conn.delete(phone)

    return success_response(data=data, message="登录成功", status_code=status.HTTP_200_OK)


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)  # 调用父类方法
        data = response.data

        # 使用自定义的success_response格式返回
        return success_response(data=data, message="Token刷新成功", status_code=status.HTTP_200_OK)


class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return success_response(message="用户登出成功", status_code=status.HTTP_200_OK)
        except Exception as e:
            return fail_response(errors=str(e), message="用户登出失败", status_code=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def token_check(request):
    return success_response(message="Token有效", status_code=status.HTTP_200_OK)


@api_view(['GET', 'PUT'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def user_info(request):
    user = request.user

    if request.method == 'GET':
        serializer = UserSerializer(user, context={'request': request})
        return success_response(data=serializer.data)

    else:
        serializer = UserSerializer(user, data=request.data, partial=True, context={'request': request})

        if serializer.is_valid():
            serializer.save()
            return success_response(message="用户信息修改成功")
        return fail_response(errors=serializer.errors, message="用户信息修改失败")
