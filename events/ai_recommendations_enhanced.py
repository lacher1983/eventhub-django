import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import pandas as pd
from django.db.models import Count, Q, Avg, F
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
import logging
from .models import Event, Favorite, Registration, Review, User
import joblib
import os
from django.conf import settings

logger = logging.getLogger(__name__)

class EnhancedAIRecommendationEngine:
    """Улучшенная система рекомендаций с машинным обучением"""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words=['и', 'в', 'на', 'с', 'по', 'для'],  # Русские стоп-слова
            max_features=2000,
            min_df=2,
            max_df=0.85,
            ngram_range=(1, 2)  # Учитываем словосочетания
        )
        self.model_path = os.path.join(settings.BASE_DIR, 'ai_models')
        os.makedirs(self.model_path, exist_ok=True)
        
    def train_user_clustering(self, users_limit=1000):
        """Кластеризация пользователей для коллаборативной фильтрации"""
        try:
            # Собираем данные о пользователях
            user_data = []
            users = User.objects.all()[:users_limit]
            
            for user in users:
                user_features = {
                    'user_id': user.id,
                    'favorite_categories': [],
                    'avg_rating_given': 0,
                    'events_attended': 0,
                    'preferred_price_range': 0,
                    'location_preference': ''
                }
                
                # Анализ избранного
                favorites = Favorite.objects.filter(user=user).select_related('event')
                for fav in favorites:
                    if fav.event.category:
                        user_features['favorite_categories'].append(fav.event.category.name)
                
                # Анализ отзывов
                reviews = Review.objects.filter(user=user)
                if reviews.exists():
                    user_features['avg_rating_given'] = reviews.aggregate(Avg('rating'))['rating__avg']
                
                # Анализ регистраций
                registrations = Registration.objects.filter(user=user)
                user_features['events_attended'] = registrations.count()
                
                user_data.append(user_features)
            
            # Преобразуем в DataFrame для ML
            df = pd.DataFrame(user_data)
            
            # Обучаем K-means кластеризацию
            if len(df) > 10:  # Минимум пользователей для кластеризации
                kmeans = KMeans(n_clusters=min(5, len(df)//2), random_state=42)
                
                # Подготавливаем фичи для кластеризации
                cluster_features = pd.get_dummies(df['favorite_categories'].explode()).groupby(level=0).sum()
                cluster_features['avg_rating'] = df['avg_rating_given']
                cluster_features['events_attended'] = df['events_attended']
                
                user_clusters = kmeans.fit_predict(cluster_features)
                
                # Сохраняем модель
                joblib.dump(kmeans, os.path.join(self.model_path, 'user_clustering.pkl'))
                
                return user_clusters
                
        except Exception as e:
            logger.error(f"User clustering training failed: {e}")
        
        return None
    
    def get_context_aware_recommendations(self, user, context=None):
        """Контекстно-aware рекомендации с учетом времени, погоды, местоположения"""
        context = context or {}
        
        try:
            base_query = Event.objects.filter(is_active=True)
            
            # Фильтрация по местоположению
            user_location = context.get('user_location')
            if user_location and hasattr(user_location, 'coords'):
                user_point = Point(user_location.coords)
                base_query = base_query.annotate(
                    distance=Distance('location_point', user_point)
                ).order_by('distance')[:50]  # Ближайшие 50 мероприятий
            
            # Фильтрация по времени суток
            current_hour = context.get('current_hour', 12)
            if 6 <= current_hour <= 12:
                # Утренние мероприятия
                base_query = base_query.filter(
                    Q(event_type__in=['training', 'yoga', 'breakfast']) | 
                    Q(title__icontains='утрен') |
                    Q(description__icontains='завтрак')
                )
            elif 18 <= current_hour <= 23:
                # Вечерние мероприятия
                base_query = base_query.filter(
                    Q(event_type__in=['concert', 'party', 'networking']) |
                    Q(title__icontains='вечер') |
                    Q(description__icontains='ужин')
                )
            
            # Учет погодных условий
            weather = context.get('weather')
            if weather and weather.lower() in ['rain', 'snow']:
                # Рекомендуем indoor мероприятия в плохую погоду
                base_query = base_query.filter(
                    Q(event_format='online') |
                    Q(location__icontains='центр') |
                    Q(location__icontains='помещен') |
                    Q(tags__name__in=['в помещении', 'онлайн'])
                )
            
            return self.get_hybrid_recommendations(user, base_query, limit=6)
            
        except Exception as e:
            logger.error(f"Context-aware recommendations failed: {e}")
            return self.get_hybrid_recommendations(user, limit=6)
    
    def get_trending_events(self, days=7, limit=10):
        """Трендовые мероприятия на основе алгоритма Hacker News"""
        from django.utils import timezone
        from datetime import timedelta
        
        time_threshold = timezone.now() - timedelta(days=days)
        
        trending_events = Event.objects.filter(
            created_at__gte=time_threshold,
            is_active=True
        ).annotate(
            registrations_count=Count('registrations'),
            favorites_count=Count('favorited_by'),
            views_count=Count('eventstatistic__views_count'),
            # Алгоритм популярности подобный Hacker News
            popularity_score=(
                F('registrations_count') * 2 + 
                F('favorites_count') * 1.5 + 
                F('views_count') * 0.5
            ) / (
                (timezone.now() - F('created_at')).total_seconds() / 3600 + 2
            ) ** 1.8
        ).order_by('-popularity_score')[:limit]
        
        return trending_events
    
    def get_serendipity_recommendations(self, user, limit=5):
        """Рекомендации для открытия новых интересов (серендипити)"""
        try:
            # Получаем обычные рекомендации
            usual_recommendations = self.get_hybrid_recommendations(user, limit=20)
            
            if not usual_recommendations:
                return []
            
            # Анализируем разнообразие категорий
            categories_count = {}
            for event in usual_recommendations:
                cat = event.category.name if event.category else 'other'
                categories_count[cat] = categories_count.get(cat, 0) + 1
            
            # Ищем мероприятия из непредставленных категорий
            all_categories = set(Event.objects.values_list('category__name', flat=True).distinct())
            user_categories = set(categories_count.keys())
            unexplored_categories = all_categories - user_categories
            
            serendipity_events = []
            if unexplored_categories:
                serendipity_events = Event.objects.filter(
                    category__name__in=list(unexplored_categories)[:3],
                    is_active=True
                ).order_by('?')[:2]  # Случайные 2 мероприятия
            
            # Добавляем немного случайности
            random_events = Event.objects.filter(
                is_active=True
            ).exclude(
                id__in=[e.id for e in usual_recommendations]
            ).order_by('?')[:3]
            
            return list(serendipity_events) + list(random_events)
            
        except Exception as e:
            logger.error(f"Serendipity recommendations failed: {e}")
            return []

# Глобальный экземпляр улучшенного движка
enhanced_recommendation_engine = EnhancedAIRecommendationEngine()