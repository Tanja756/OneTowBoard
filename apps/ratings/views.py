from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Rating


@login_required
def rate_user_view(request, username):
    """POST-эндпоинт: поставить/изменить оценку пользователю. Возвращает JSON."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Метод не разрешён'}, status=405)

    # Проверка подтверждения email
    if not request.user.profile.email_verified:
        return JsonResponse(
            {'error': 'Только пользователи с подтверждённым email могут ставить оценки'},
            status=403
        )

    rated_user = get_object_or_404(User, username=username)

    # Нельзя оценить самого себя
    if request.user == rated_user:
        return JsonResponse({'error': 'Нельзя оценить самого себя'}, status=400)

    # Получаем оценку из тела запроса
    try:
        import json
        data = json.loads(request.body)
        score = int(data.get('score', 0))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'error': 'Некорректные данные'}, status=400)

    if score < 1 or score > 5:
        return JsonResponse({'error': 'Оценка должна быть от 1 до 5'}, status=400)

    # Создаём или обновляем оценку (upsert)
    rating, created = Rating.objects.update_or_create(
        rater=request.user,
        rated_user=rated_user,
        defaults={'score': score}
    )

    average = Rating.get_average_for_user(rated_user)
    count = Rating.get_count_for_user(rated_user)

    return JsonResponse({
        'average': average,
        'count': count,
        'my_rating': score,
        'created': created,
    })


def get_rating_view(request, username):
    """GET-эндпоинт: получить рейтинг пользователя."""
    rated_user = get_object_or_404(User, username=username)

    average = Rating.get_average_for_user(rated_user)
    count = Rating.get_count_for_user(rated_user)

    my_rating = None
    if request.user.is_authenticated:
        my_rating = Rating.get_user_rating(rated_user, request.user)

    return JsonResponse({
        'average': average,
        'count': count,
        'my_rating': my_rating,
    })
