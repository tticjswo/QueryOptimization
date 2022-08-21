# QueryOptimization

Django ORM 을 이용해서 SQL을 작성하면 많은 데이터를 검색하거나 할 때 매우 긴 시간에 좌절하고 내문제라고 치부했었다.
찾아본결과 ORM이 SQL에 작동하는 원리를 알아야했다.

이에 도전해보려는 것은 쿼리 최적화 이다.

아래는 첨부한 2개의 모델이다.

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
 

위 문제를 해결하기위해서 '쿼리 최적화'라는 성능에 아주 큰 영향을 미치는 높은 산을 마주했다.. 이걸 넘을 차례다
