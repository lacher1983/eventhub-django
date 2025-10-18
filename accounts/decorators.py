from django.http import HttpResponseForbidden
from functools import wraps

def role_required(allowed_roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return HttpResponseForbidden("Authentication required")
            if request.user.role not in allowed_roles and not request.user.is_superuser:
                return HttpResponseForbidden("Insufficient permissions")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator

admin_required = role_required(['admin'])
moderator_required = role_required(['moderator', 'admin'])