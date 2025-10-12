from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import json

@require_POST
@csrf_exempt
def set_theme(request):
    """API для установки темы"""
    try:
        data = json.loads(request.body)
        theme = data.get('theme')
        
        if theme in ['light', 'dark']:
            if request.user.is_authenticated:
                # Сохраняем в профиль пользователя
                if hasattr(request.user, 'profile'):
                    request.user.profile.theme = theme
                    request.user.profile.save()
            
            response = JsonResponse({'status': 'success', 'theme': theme})
            response.set_cookie('eventhub-theme', theme, max_age=365*24*60*60)
            return response
        else:
            return JsonResponse({'status': 'error', 'message': 'Invalid theme'}, status=400)
            
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

def get_theme(request):
    """API для получения текущей темы"""
    theme = 'light'
    
    # Приоритеты: куки -> профиль пользователя -> системные настройки
    if 'eventhub-theme' in request.COOKIES:
        theme = request.COOKIES['eventhub-theme']
    elif request.user.is_authenticated and hasattr(request.user, 'profile'):
        theme = getattr(request.user.profile, 'theme', 'light')
    
    return JsonResponse({'theme': theme})
