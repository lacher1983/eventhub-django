from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

def send_registration_confirmation(registration):
    """Отправка подтверждения регистрации на мероприятие"""
    subject = f"Подтверждение регистрации: {registration.event.title}"
    
    # HTML версия письма
    html_message = render_to_string('emails/registration_confirmation.html', {
        'registration': registration,
        'user': registration.user,
        'event': registration.event
    })
    
    # Текстовая версия письма
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[registration.user.email],
            html_message=html_message,
            fail_silently=False
        )
        return True
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        return False

def send_order_confirmation(order):
    """Отправка подтверждения заказа"""
    subject = f"Подтверждение заказа #{order.order_number}"
    
    html_message = render_to_string('emails/order_confirmation.html', {
        'order': order,
        'user': order.user
    })
    
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[order.user.email],
            html_message=html_message,
            fail_silently=False
        )
        return True
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        return False