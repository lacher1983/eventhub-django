from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from ..gamification.core import gamification_engine

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_progress(request):
    """Получение прогресса пользователя"""
    try:
        progress = gamification_engine.get_user_progress(request.user)
        
        response_data = {
            'level': {
                'current': {
                    'level': progress['level'].level if progress['level'] else 1,
                    'name': progress['level'].level_name if progress['level'] else 'Новичок',
                    'icon': progress['level'].badge_icon if progress['level'] else '🌱',
                    'color': progress['level'].color if progress['level'] else '#95a5a6'
                },
                'next': {
                    'level': progress['next_level'].level if progress['next_level'] else None,
                    'name': progress['next_level'].level_name if progress['next_level'] else None,
                    'points_required': progress['next_level'].min_points - progress['profile'].total_points if progress['next_level'] else 0
                },
                'progress': progress['level_progress'],
                'total_points': progress['profile'].total_points
            },
            'achievements': [
                {
                    'name': ach.achievement.name,
                    'description': ach.achievement.description,
                    'icon': ach.achievement.icon,
                    'points': ach.achievement.points,
                    'unlocked': ach.is_unlocked,
                    'progress': ach.progress,
                    'unlocked_at': ach.unlocked_at.isoformat() if ach.unlocked_at else None
                }
                for ach in progress['achievements']
            ],
            'quests': {
                'active': [
                    {
                        'name': quest.quest.name,
                        'description': quest.quest.description,
                        'type': quest.quest.quest_type,
                        'points_reward': quest.quest.points_reward,
                        'progress': quest.progress,
                        'expires_at': quest.quest.expires_at.isoformat() if quest.quest.expires_at else None
                    }
                    for quest in progress['active_quests']
                ],
                'completed': [
                    {
                        'name': quest.quest.name,
                        'description': quest.quest.description,
                        'points_reward': quest.quest.points_reward,
                        'completed_at': quest.completed_at.isoformat() if quest.completed_at else None
                    }
                    for quest in progress['completed_quests']
                ]
            },
            'leaderboard': {
                'position': progress['leaderboard_position'],
                'total_players': progress.get('total_players', 0)
            },
            'stats': progress['stats']
        }
        
        return Response(response_data)
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def leaderboard(request):
    """Получение таблицы лидеров"""
    from ..models import Leaderboard
    
    try:
        limit = int(request.GET.get('limit', 10))
        offset = int(request.GET.get('offset', 0))
        
        entries = Leaderboard.objects.select_related('user').order_by('position')[
            offset:offset + limit
        ]
        
        leaderboard_data = []
        for entry in entries:
            leaderboard_data.append({
                'position': entry.position,
                'username': entry.user.username,
                'points': entry.points,
                'level': entry.user.game_profile.current_level.level if hasattr(entry.user, 'game_profile') and entry.user.game_profile.current_level else 1,
                'avatar': entry.user.avatar.url if entry.user.avatar else None
            })
        
        return Response({
            'leaderboard': leaderboard_data,
            'total_players': Leaderboard.objects.count()
        })
        
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def claim_quest_reward(request, quest_id):
    """Получение награды за задание"""
    from ..models import UserQuest
    
    try:
        user_quest = UserQuest.objects.get(
            id=quest_id,
            user=request.user,
            is_completed=True
        )
        
        # Помечаем награду как полученную
        user_quest.delete()  # Или помечаем другим способом (грамоту дадим)
        
        return Response({
            'status': 'success',
            'points': user_quest.quest.points_reward,
            'message': f'Награда получена: {user_quest.quest.points_reward} очков!'
        })
        
    except UserQuest.DoesNotExist:
        return Response(
            {'error': 'Задание не найдено или еще не выполнено'},
            status=status.HTTP_404_NOT_FOUND
        )