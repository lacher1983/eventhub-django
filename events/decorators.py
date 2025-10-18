
from functools import wraps
from django.core.exceptions import PermissionDenied

def organizer_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role in ['organizer', 'admin']:
            return view_func(request, *args, **kwargs)
        raise PermissionDenied  ("Только организаторы и администраторы могут выполнить это действие.")
    return _wrapped_view

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if request.user.is_authenticated and request.user.role == 'admin':
            return view_func(request, *args, **kwargs)
        raise PermissionDenied ("Только администраторы могут выполнить это действие.")
    return _wrapped_view