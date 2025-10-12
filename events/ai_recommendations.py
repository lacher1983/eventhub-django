import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from django.db.models import Count, Q, Avg
import logging
from .models import Event, Favorite, Registration, Review

logger = logging.getLogger(__name__)

class AIRecommendationEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words='english', 
            max_features=1000,
            min_df=2,
            max_df=0.8
        )
    
    def get_user_preferences(self, user):
        """Анализ предпочтений пользователя"""
        preferences = {
            'categories': [],
            'event_types': [],
            'price_range': None,
            'favorite_organizers': []
        }
        
        # Анализ избранного
        favorites = Favorite.objects.filter(user=user).select_related('event')
        for favorite in favorites:
            if favorite.event.category:
                preferences['categories'].append(favorite.event.category.name)
            preferences['event_types'].append(favorite.event.event_type)
            preferences['favorite_organizers'].append(favorite.event.organizer.username)
        
        # Анализ регистраций
        registrations = Registration.objects.filter(user=user).select_related('event')
        for registration in registrations:
            if registration.event.category:
                preferences['categories'].append(registration.event.category.name)
            preferences['event_types'].append(registration.event.event_type)
        
        return preferences
    
    def get_content_based_recommendations(self, user, events, limit=6):
        """Рекомендации на основе контента с использованием ML"""
        try:
            if not events:
                return []
            
            event_texts = []
            event_ids = []
            
            for event in events:
                # Собираем текстовые признаки
                text_parts = [
                    event.title or '',
                    event.description or '',
                    event.short_description or '',
                    event.get_category_display() or '',
                    event.get_event_type_display() or '',
                    event.location or ''
                ]
                text = ' '.join([part for part in text_parts if part])
                event_texts.append(text)
                event_ids.append(event.id)
            
            if len(event_texts) < 2:
                return events[:limit]
            
            # Создаем TF-IDF матрицу
            tfidf_matrix = self.vectorizer.fit_transform(event_texts)
            
            # Вычисляем косинусное сходство
            cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
            
            # Получаем рекомендации
            sim_scores = list(enumerate(cosine_sim[0]))
            sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:limit+1]
            
            recommended_indices = [i[0] for i in sim_scores]
            return [events[i] for i in recommended_indices]
            
        except Exception as e:
            logger.error(f"AI recommendation failed: {e}")
            return self.get_fallback_recommendations(user, limit)
    
    def get_collaborative_recommendations(self, user, limit=6):
        """Коллаборативная фильтрация на основе похожих пользователей"""
        try:
            # Находим пользователей с похожими интересами
            user_favorites = set(Favorite.objects.filter(user=user).values_list('event_id', flat=True))
            
            similar_users = Favorite.objects.filter(
                event__in=user_favorites
            ).exclude(user=user).values('user').annotate(
                common_events=Count('event')
            ).order_by('-common_events')[:10]
            
            if not similar_users:
                return []
            
            similar_user_ids = [item['user'] for item in similar_users]
            
            # Находим мероприятия, которые нравятся похожим пользователям
            recommended_events = Favorite.objects.filter(
                user__in=similar_user_ids
            ).exclude(
                event__in=user_favorites
            ).values('event').annotate(
                score=Count('user')
            ).order_by('-score')[:limit]
            
            event_ids = [item['event'] for item in recommended_events]
            return Event.objects.filter(id__in=event_ids, is_active=True)
            
        except Exception as e:
            logger.error(f"Collaborative filtering failed: {e}")
            return []
    
    def get_hybrid_recommendations(self, user, limit=6):
        """Гибридная система рекомендаций"""
        if not user.is_authenticated:
            return self.get_popular_events(limit)
        
        # 1. Контентные рекомендации
        user_events = Event.objects.filter(is_active=True)
        content_based = self.get_content_based_recommendations(user, list(user_events), limit//2)
        
        # 2. Коллаборативные рекомендации
        collaborative = self.get_collaborative_recommendations(user, limit//2)
        
        # 3. Рекомендации на основе предпочтений
        preference_based = self.get_preference_based_recommendations(user, limit//2)
        
        # Объединяем все подходы
        all_recommendations = list(content_based) + list(collaborative) + list(preference_based)
        
        # Убираем дубликаты и уже посещенные
        seen_ids = set()
        final_recommendations = []
        
        user_registered_ids = Registration.objects.filter(user=user).values_list('event_id', flat=True)
        user_favorite_ids = Favorite.objects.filter(user=user).values_list('event_id', flat=True)
        
        for event in all_recommendations:
            if (event.id not in seen_ids and 
                event.id not in user_registered_ids and
                event.id not in user_favorite_ids):
                final_recommendations.append(event)
                seen_ids.add(event.id)
        
        # Если рекомендаций мало, добавляем популярные
        if len(final_recommendations) < limit:
            additional = self.get_popular_events(limit - len(final_recommendations))
            for event in additional:
                if event.id not in seen_ids:
                    final_recommendations.append(event)
                    seen_ids.add(event.id)
        
        return final_recommendations[:limit]
    
    def get_preference_based_recommendations(self, user, limit=6):
        """Рекомендации на основе предпочтений пользователя"""
        preferences = self.get_user_preferences(user)
        
        if not preferences['categories'] and not preferences['event_types']:
            return self.get_popular_events(limit)
        
        query = Q(is_active=True)
        
        if preferences['categories']:
            # Берем самую популярную категорию
            from collections import Counter
            category_counter = Counter(preferences['categories'])
            most_common_category = category_counter.most_common(1)[0][0]
            query &= Q(category__name=most_common_category)
        
        if preferences['event_types']:
            event_type_counter = Counter(preferences['event_types'])
            most_common_type = event_type_counter.most_common(1)[0][0]
            query &= Q(event_type=most_common_type)
        
        return Event.objects.filter(query).exclude(
            registrations__user=user
        ).order_by('-created_at')[:limit]
    
    def get_popular_events(self, limit=6):
        """Популярные мероприятия"""
        return Event.objects.filter(
            is_active=True
        ).annotate(
            registrations_count=Count('registrations'),
            avg_rating=Avg('reviews__rating')
        ).order_by('-registrations_count', '-avg_rating')[:limit]
    
    def get_fallback_recommendations(self, user, limit=6):
        """Резервные рекомендации"""
        return self.get_popular_events(limit)

# Глобальный экземпляр движка
recommendation_engine = AIRecommendationEngine()