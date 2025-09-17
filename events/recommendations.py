from .models import Event, User, Favorite, Review
from django.db.models import Count, Q

def get_recommended_events(user, limit=6):
    """
    Получаем рекомендованные мероприятия для пользователя на основе его предпочтений и поведения
    """
    if not user.is_authenticated:
        # Для неавторизованных - популярные мероприятия
        return get_popular_events(limit)
    
    recommendations = []
    
    # 1. На основе избранного
    favorite_categories = get_recommendations_from_favorites(user)
    if favorite_categories:
        recommendations.extend(favorite_categories)
    
    # 2. На основе отзывов (высокие оценки)
    reviewed_recommendations = get_recommendations_from_reviews(user)
    if reviewed_recommendations:
        recommendations.extend(reviewed_recommendations)
    
    # 3. Популярные в его городе
    location_recommendations = get_location_recommendations(user)
    if location_recommendations:
        recommendations.extend(location_recommendations)
    
    # Убираем дубликаты и уже посещенные
    seen_events = set()
    unique_recommendations = []
    
    for event in recommendations:
        if (event.id not in seen_events and 
            not user.registrations.filter(event=event).exists() and
            not Favorite.objects.filter(user=user, event=event).exists()):
            unique_recommendations.append(event)
            seen_events.add(event.id)
    
    # Если рекомендаций мало, добавляем популярные
    if len(unique_recommendations) < limit:
        additional = get_popular_events(limit - len(unique_recommendations))
        for event in additional:
            if event.id not in seen_events:
                unique_recommendations.append(event)
                seen_events.add(event.id)
    
    return unique_recommendations