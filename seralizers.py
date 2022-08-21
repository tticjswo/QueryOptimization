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
