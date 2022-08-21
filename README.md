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
[최적화 전]
여기서 creator,  favorite_count,  only_superuser를 가져오는데 엄청난 중복 쿼리가 발생한다
get_creator 함수에서 obj.category를 할 때마다, obj.creator를 할 때마다 쿼리문이 실행된다.

![image](https://user-images.githubusercontent.com/66824080/185779395-f3f6c4f1-44cd-4aa4-8efc-25db8919d3a0.png)


![image](https://user-images.githubusercontent.com/66824080/185779430-343e14a4-066c-4a81-bd88-d45b4db7763d.png)


[최적화 후]

```python
from django.db.models import Q, F
from django.db.models.aggregates import Count

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

...

class CategoryManageApi(ApiAuthMixin, APIView):
    def get(self, request, *args, **kwargs):
        """
        cate_id에 맞는 게시판의 글을 모두 보여준다.
        """
        pk = kwargs['cate_id']
        
        if not pk:
            return Response({
                "message": "Select a board type"
            }, status=status.HTTP_400_BAD_REQUEST)
            
        category = get_object_or_404(Category, pk=pk)
        
        postlist = Post.objects.select_related(
            'creator'
        ).annotate(
            nickname=F('creator__profile__nickname'),
            favorite_count=Count('favorite_user'),
        ).filter(
            Q(category__pk=pk)
        )
        
        data = []
        data.append(
            {
                'category': category.title,
                'only_superuser': category.only_superuser,
            }
        )
        
        for post in postlist:
            try:
                imageurl = post.thumbnail.url
            except:
                imageurl = ''
            
            context = {
                'id': post.id,
                'title': post.title,
                'content': post.content,
                'thumbnail': imageurl,
                'hits': post.hits,
                'favorite_count': post.favorite_count,
                'created_date': post.created_date,
                'modified_date': post.modified_date,
                'creator': post.nickname,
            }
            data.append(context)
        
        return Response(data, status=status.HTTP_200_OK)
```

먼저 select_related로 'creator' 를 설정했다. 이는 Post 객체를 선택할 때 객체와 외래키로 연결된 creator에 있는 정보들도 같이 가져오겠다는 뜻이다.

 

annotate는 쿼리를 가져오면서 필드명을 임의로 지정해준다고 생각하면 편하다.

nickname=F('creator__profile__nickname')  <- 코드를 통해서 post.nickname 에 접근할 수 있게된다.

post.nickname은 (post와 연결된 creator에 연결된 profile)의 필드인 nickname을 의미한다.

favorite_count도 nickname과 마찬가지로 post.favorite_count로 참조가 가능하다.

 

**여기서 django의 aggregate를 사용했는데 연결된 외래키 또는 many-to-many키의 갯수를 반환해주는 Count를 사용했다. Count는 쿼리를 따로 호출하지 않고 Post객체들을 가져올 때 한번에 계산해서 가져온다! (시간 절약)

 

마지막으로 filter의 Q는 SQL의 where문과 같다고 생각하면 된다. 코드 Q(category__pk=pk) 의 뜻은 Post를 가져오는데 post객체와 외래키로 연결된 category의 pk값이 pk(멤버변수)와 같다면 가져온다 라는 뜻이다.

 

그럼 위 코드를 간략히 풀어서 설명하자면 post객체와 외래키로 연결된 category의 pk값이 pk와 같다면 다 가져오는데, 가져올 때 post와 연결된 creator의 모든 정보를 가져오고, nickname과 favorite_count를 annotate와 F를 사용해서 db를 조회할 때 한번에 가져오게 한다. 



![image](https://user-images.githubusercontent.com/66824080/185779478-a19ce1a6-85ab-470b-8b94-22d34ddf0536.png)


쿼리 시간이 70배 가까이 빨라졌다.  337ms -> 4.65ms

cpu 시간은 20배 이상 차이가 난다.  83714ms -> 339ms

어느정도 최적화 성공!
