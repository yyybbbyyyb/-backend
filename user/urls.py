from django.urls import path
from user import views

urlpatterns = [
    path('phone-code/', views.get_phone_code , name='send_phone_code'),  # 获得手机验证码
    path('login/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'), # 用户登录
    path('login-with-code/', views.login_with_code, name='token_obtain_pair'),  # 用户登录
    path('token/refresh/', views.CustomTokenRefreshView.as_view(), name='token_refresh'),  # 刷新Token
    path('token/check/', views.token_check, name='token_check'),  # Token
    path('register/', views.register, name='register'),  # 用户注册
    path('user/', views.user_info, name='get_user_info'),  # 获取用户信息
    path('logout/', views.LogoutView.as_view(), name='logout'),  # 用户登出
]
