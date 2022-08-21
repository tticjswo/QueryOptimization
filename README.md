# QueryOptimization

Django ORM 을 이용해서 SQL을 작성하면 많은 데이터를 검색하거나 할 때 매우 긴 시간에 좌절하고 내문제라고 치부했었다.
찾아본결과 ORM이 SQL에 작동하는 원리를 알아야했다.

이에 도전해보려는 것은 쿼리 최적화 이다.

아래는 첨부한 models.py 내부의 2개의 모델이다.
```python
# models.py

class Category(models.Model):
    title = models.CharField(max_length=128, unique=True, null=True, blank=False)
    is_anonymous = models.BooleanField(default=False)
    created_date = models.DateTimeField(default=timezone.now)
    top_fixed = models.BooleanField(default=False)
    only_superuser = models.BooleanField(default=False)
    
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="category")
    
    class Meta:
        verbose_name = '게시판 종류'
        verbose_name_plural = '게시판 종류 모음'
        ordering = ['-created_date', ]
        
    def __str__(self):
        return self.title
    

class Post(models.Model):
    title = models.CharField(max_length=128, null=True, blank=False)
    content = models.TextField(default='')
    thumbnail = models.ImageField(upload_to='post_thumbnail/', null=True, blank=True)
    
    hits = models.PositiveIntegerField(default=0)
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(auto_now=True)
    top_fixed = models.BooleanField(default=False)
    
    category = models.ForeignKey(Category, null=True, on_delete=models.CASCADE, related_name="post")
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="post")
    
    class Meta:
        verbose_name = '게시글'
        verbose_name_plural = '게시글 모음'
        ordering = ['-created_date', ]
        
    def __str__(self):
        return self.title
``` 

아래는Post들을 Serialize하는 코드이다.

SerializerMethodField를 적극 활용했었다..(prefatch_related X)

```python
// serializer.py
// PostListSerializer 부분만 추출

from rest_framework import serializers
from rest_framework.fields import SerializerMethodField

...

class PostListSerializer(serializers.ModelSerializer):
    thumbnail = serializers.SerializerMethodField(read_only=True)
    creator = serializers.SerializerMethodField(read_only=True)
    favorite_count = serializers.SerializerMethodField(read_only=True)
    only_superuser = serializers.BooleanField(source="category.only_superuser", read_only=True)
    
    class Meta:
        model = Post
        fields = (
            'id', 'category', 'title', 'content', 'thumbnail', 
            'hits', 'created_date', 'modified_date', 'top_fixed',
            'creator', 'favorite_count', 'only_superuser',
        )
    
    def get_creator(self, obj):
        try:
            category = obj.category
            creator = obj.creator
            is_anonymous = category.is_anonymous
            if is_anonymous:
                return "익명"
            else:
                return creator.profile.nickname
        except:
            return ''
    
    def get_thumbnail(self, obj):
        try:
            return obj.thumbnail.url
        except:
            return ''
    
    def get_favorite_count(self, obj):
        try:
            return obj.favorite_user.count()
        except:
            return 0
```
위 문제를 해결하기위해서 '쿼리 최적화'라는 성능에 아주 큰 영향을 미치는 높은 산을 마주했다.. 이걸 넘을 차례다
