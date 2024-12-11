from haystack import indexes
from .models import EntityAI
from jieba.analyse import ChineseAnalyzer

class EntityAIIndex(indexes.SearchIndex, indexes.Indexable):
    # 定义索引字段

    # 定义主要用于全文检索的字段
    text = indexes.CharField(document=True, use_template=True, analyzer=ChineseAnalyzer())  # 使用模板进行索引

    # 定义可选字段，用于精确匹配或过滤
    name = indexes.CharField(model_attr='name')
    description = indexes.CharField(model_attr='description')
    type = indexes.CharField(model_attr='type__name')  # 索引类型名称
    tags = indexes.MultiValueField()  # 用于存储标签信息

    def get_model(self):
        return EntityAI

    def index_queryset(self, using=None):
        """定义要被索引的查询集"""
        return self.get_model().objects.all()

    def prepare_tags(self, obj):
        """提取标签信息"""
        return [tag.name for tag in obj.entityAI_tags.all()]