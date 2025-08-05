from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg, Count
from django.utils import timezone

from .consts import MAX_RATE

RATE_CHOICES = [(x, str(x)) for x in range(0, MAX_RATE + 1)]

CATEGORY = (
    ('business', 'ビジネス'),
    ('life', '生活'),
    ('hobby', '趣味'),
    ('other', 'その他'),
)

class Shelf(models.Model):
    title = models.CharField(max_length=100)
    text = models.TextField()
    thumbnail = models.ImageField(null=True, blank=True)
    category = models.CharField(
        max_length=100,
        choices = CATEGORY,
        )
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    favorites = models.ManyToManyField(User, related_name='favorite_books', blank=True)

    def __str__(self):
        return self.title
    
    def get_average_rating(self):
        """平均評価を取得"""
        return self.review_set.aggregate(Avg('rate'))['rate__avg'] or 0
    
    def get_review_count(self):
        """レビュー数を取得"""
        return self.review_set.count()
    
    def is_favorited_by(self, user):
        """ユーザーがお気に入り登録しているかチェック"""
        if user.is_authenticated:
            return self.favorites.filter(id=user.id).exists()
        return False
    
    def get_similar_books(self):
        """類似書籍を取得（同じカテゴリで評価の高いもの）"""
        return Shelf.objects.filter(
            category=self.category
        ).exclude(id=self.id).annotate(
            avg_rating=Avg('review__rate')
        ).order_by('-avg_rating')[:3]

class Review(models.Model):
    book = models.ForeignKey(Shelf, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    text = models.TextField()
    rate = models.IntegerField(choices=RATE_CHOICES)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['-created_at']
    
