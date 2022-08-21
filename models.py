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
