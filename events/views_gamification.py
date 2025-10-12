from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .gamification.core import gamification_engine
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import DetailView
from .models import Event

class EventListView(ListView):
    model = Event
    template_name = 'events/event_list.html'
    context_object_name = 'events'
    paginate_by = 12
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Добавляем геймификацию для авторизованных пользователей
        if self.request.user.is_authenticated:
            from .gamification.core import gamification_engine
            progress = gamification_engine.get_user_progress(self.request.user)
            
            context['level_progress'] = progress['level_progress'] * 100
            context['next_level'] = progress['next_level']
        
        return context

@login_required
@require_http_methods(["GET"])
def user_progress(request):
    """
    Получение прогресса пользователя в геймификации
    """
    try:
        user_progress_data = {
            'user_id': request.user.id,
            'level': 1,
            'points': 150,
            'next_level_points': 200,
            'completed_achievements': 3,
            'total_achievements': 10,
            'rank': 'Новичок',
            'progress_percentage': 75
        }
        
        return JsonResponse({
            'success': True,
            'progress': user_progress_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@require_http_methods(["GET"])
def leaderboard(request):
    """
    Получение таблицы лидеров
    """
    try:
        leaderboard_data = [
            {
                'rank': 1,
                'user_id': 1,
                'username': 'Лидер',
                'points': 1000,
                'level': 5
            },
            {
                'rank': 2,
                'user_id': 2,
                'username': 'Второй',
                'points': 800,
                'level': 4
            },
            {
                'rank': 3,
                'user_id': 3,
                'username': 'Третий',
                'points': 600,
                'level': 3
            }
        ]
        
        return JsonResponse({
            'success': True,
            'leaderboard': leaderboard_data,
            'total_players': len(leaderboard_data)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@csrf_exempt
@login_required
@require_http_methods(["POST"])
def claim_quest_reward(request, quest_id):
    """
    Получение награды за выполненный квест
    """
    try:
        # Заглушка для получения награды
        # В реальном проекте здесь будет логика проверки выполнения квеста и выдачи награды
        
        reward_data = {
            'quest_id': quest_id,
            'quest_name': f'Квест #{quest_id}',
            'reward_points': 50,
            'reward_type': 'points',
            'message': f'Награда за квест #{quest_id} успешно получена!'
        }
        
        return JsonResponse({
            'success': True,
            'reward': reward_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
    

class GameProfileView(LoginRequiredMixin, TemplateView):
    """Страница игрового профиля"""
    template_name = 'events/gamification/user_profile.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        progress = gamification_engine.get_user_progress(self.request.user)
        context.update(progress)
        return context

class LeaderboardView(TemplateView):
    """Страница таблицы лидеров"""
    template_name = 'events/gamification/leaderboard.html'
    
    def get_context_data(self, **kwargs):
        from .models import Leaderboard
        
        context = super().get_context_data(**kwargs)
        
        # Получаем топ-50 игроков
        leaders = Leaderboard.objects.select_related('user').order_by('position')[:50]
        
        context['leaders'] = leaders
        context['total_players'] = Leaderboard.objects.count()
        
        # Позиция текущего пользователя если авторизован
        if self.request.user.is_authenticated:
            try:
                user_position = Leaderboard.objects.get(user=self.request.user)
                context['user_position'] = user_position
            except Leaderboard.DoesNotExist:
                pass
        
        return context