from django.contrib import admin

# Register your models here.
from .models import User, Like

admin.site.register(User)
admin.site.register(Like)

admin.site.site_header = '管理平台'
admin.site.site_title = '管理平台'

