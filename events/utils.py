from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings

def handle_ajax_request(view_func):
    """Декоратор для обработки AJAX запросов"""
    def wrapper(request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            try:
                response = view_func(request, *args, **kwargs)
                if not isinstance(response, JsonResponse):
                    return JsonResponse({'error': 'Invalid response type'})
                return response
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=400)
        return view_func(request, *args, **kwargs)
    return wrapper

def organizer_required(view_func):
    """Декоратор для проверки прав организатора"""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'organizer':
            messages.error(request, "Требуются права организатора")
            return redirect('events:event_list')
        return view_func(request, *args, **kwargs)
    return wrapper

def send_registration_confirmation(registration):
    subject = f"Подтверждение регистрации: {registration.event.title}"
    html_message = render_to_string('emails/registration_confirmation.html', {
        'registration': registration,
        'user': registration.user
    })
    
    send_mail(
        subject,
        strip_tags(html_message),
        settings.DEFAULT_FROM_EMAIL,
        [registration.user.email],
        html_message=html_message
    )