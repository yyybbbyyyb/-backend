from django.db import models
from django.contrib.auth.models import AbstractUser
import os
from django.conf import settings

class User(AbstractUser):

    # 性别字段
    GENDER_CHOICES = (
        ('M', '男'),
        ('F', '女'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name='性别', default='M')

    avatar = models.ImageField(upload_to='avatar/', verbose_name='头像', blank=True, null=True)

    phone = models.CharField(max_length=11, verbose_name='手机号', unique=True, blank=True, null=True)

    class Meta:
        default_permissions = ()
        db_table = 'user'
        verbose_name = '用户'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.username

    def save(self, *args, **kwargs):
        try:
            this = User.objects.get(id=self.id)
            if this.avatar != self.avatar:
                if this.avatar:
                    old_avatar_path = os.path.join(settings.MEDIA_ROOT, this.avatar.name)
                    if os.path.exists(old_avatar_path):
                        os.remove(old_avatar_path)
        except User.DoesNotExist:
            pass

        super(User, self).save(*args, **kwargs)


class Like(models.Model):
    """
    点赞模型
    """

    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='like_user')
    entityAI = models.ForeignKey('entityAI.EntityAI', on_delete=models.CASCADE, related_name='like_entityAI')

    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '点赞'
        verbose_name_plural = verbose_name
        unique_together = ('user', 'entityAI')

    def __str__(self):
        return self.user.username + '点赞了' + self.entityAI.name