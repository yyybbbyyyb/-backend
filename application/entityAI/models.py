from django.db import models


class EntityAI(models.Model):
    """
    实体AI模型
    """

    # 基础信息
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='entityAI/', default='entityAI/default.png', verbose_name='实体AI图片')
    cover = models.ImageField(upload_to='entityAI/', default='entityAI/default.png', verbose_name='实体AI封面')
    url = models.URLField(max_length=200, verbose_name='实体AI链接')
    description = models.TextField(max_length=200, verbose_name='实体AI描述', blank=True, default='这个实体AI很懒，什么都没有留下……')

    # AI类型
    type = models.ForeignKey('EntityAIType', on_delete=models.CASCADE, verbose_name='实体AI类型')

    # 评分细则
    total_score1 = models.FloatField(verbose_name='评分细则1-数理能力', default=0)
    total_score2 = models.FloatField(verbose_name='评分细则2-语言能力', default=0)
    total_score3 = models.FloatField(verbose_name='评分细则3-图片能力', default=0)
    total_score4 = models.FloatField(verbose_name='评分细则4-文本能力', default=0)


    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '实体AI'
        verbose_name_plural = verbose_name



class EntityAIType(models.Model):
    """
    实体AI类型模型
    """
    name = models.CharField(max_length=50, verbose_name='实体AI类型名称', unique=True)
    description = models.TextField(max_length=200, verbose_name='实体AI类型描述', blank=True, default='这个实体AI类型很懒，什么都没有留下……')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '实体AI类型'
        verbose_name_plural = verbose_name


class EntityAITag(models.Model):
    """
    实体AI标签模型
    """
    name = models.CharField(max_length=50, verbose_name='实体AI标签名称', unique=True)
    entityAI = models.ManyToManyField('EntityAI', related_name='entityAI_tags', verbose_name='实体AI标签')


    def __str__(self):
        return self.name

    class Meta:
        verbose_name = '实体AI标签'
        verbose_name_plural = verbose_name