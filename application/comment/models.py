from django.db import models

class Comment(models.Model):
    """
    评论模型
    """

    # 基础信息
    entityAI = models.ForeignKey('entityAI.EntityAI', on_delete=models.CASCADE, related_name='所属实体AI')
    author = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='评论作者')

    content = models.TextField(max_length=500, verbose_name='帖子内容')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    # 评论类型
    ChoicesF = (
        (0, "短评"),
        (1, "长评"),
    )
    type = models.IntegerField(choices=ChoicesF, default=0, verbose_name='评论类型')




    # 评分细则
    score1 = models.FloatField(default=0, verbose_name='评分细则1-数理能力')
    score2 = models.FloatField(default=0, verbose_name='评分细则2-语言能力')
    score3 = models.FloatField(default=0, verbose_name='评分细则3-图片能力')
    score4 = models.FloatField(default=0, verbose_name='评分细则4-文本能力')

    class Meta:
        verbose_name = '帖子'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.content


class Notice(models.Model):
    """
    通知模型
    """

    # 基础信息
    author = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name='通知作者')

    title = models.CharField(max_length=50, verbose_name='通知标题')
    content = models.TextField(max_length=500, verbose_name='通知内容')
    created_time = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')

    class Meta:
        verbose_name = '通知'
        verbose_name_plural = verbose_name

    def __str__(self):
        return self.content

