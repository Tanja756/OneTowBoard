from django.db import models
from django.contrib.auth.models import User
from django.db.models import Avg


class Rating(models.Model):
    rater = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='ratings_given',
        verbose_name='Оценивший'
    )
    rated_user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='ratings_received',
        verbose_name='Оценённый пользователь'
    )
    score = models.PositiveSmallIntegerField(
        choices=[(1, '★'), (2, '★★'), (3, '★★★'), (4, '★★★★'), (5, '★★★★★')],
        verbose_name='Оценка'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('rater', 'rated_user')
        verbose_name = 'Оценка'
        verbose_name_plural = 'Оценки'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.rater.username} → {self.rated_user.username}: {self.score}'

    @staticmethod
    def get_average_for_user(user):
        """Возвращает средний рейтинг пользователя (число с 1 знаком) или None."""
        result = Rating.objects.filter(rated_user=user).aggregate(avg=Avg('score'))
        if result['avg'] is not None:
            return round(result['avg'], 1)
        return None

    @staticmethod
    def get_count_for_user(user):
        """Возвращает количество оценок пользователя."""
        return Rating.objects.filter(rated_user=user).count()

    @staticmethod
    def get_user_rating(user, rater):
        """Возвращает оценку, которую rater поставил user, или None."""
        try:
            return Rating.objects.get(rater=rater, rated_user=user).score
        except Rating.DoesNotExist:
            return None
