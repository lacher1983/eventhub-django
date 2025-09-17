from django.http import JsonResponse
from django.core.exceptions import ValidationError, PermissionDenied
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def handle_ajax_errors(view_func):
    """Декоратор для обработки ошибок в AJAX запросах"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                return view_func(request, *args, **kwargs)
            except ValidationError as e:
                return JsonResponse({'success': False, 'message': str(e)}, status=400)
            except PermissionDenied as e:
                return JsonResponse({'success': False, 'message': 'Доступ запрещен'}, status=403)
            except Exception as e:
                logger.error(f"Error in {view_func.__name__}: {str(e)}")
                return JsonResponse({'success': False, 'message': 'Внутренняя ошибка сервера'}, status=500)
        return view_func(request, *args, **kwargs)
    return wrapper

def organizer_required(view_func):
    """Декоратор для проверки прав организатора"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'organizer':
            from django.contrib import messages
            messages.error(request, "Требуются права организатора")
            from django.shortcuts import redirect
            return redirect('events:event_list')
        return view_func(request, *args, **kwargs)
    return wrapper