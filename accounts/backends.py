from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from .models_security import SecurityProfile, LoginHistory
import requests

User = get_user_model()

class SecureAuthenticationBackend(ModelBackend):
    """Безопасный бэкенд аутентификации с дополнительными проверками"""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            # Логируем попытку входа с несуществующим пользователем
            self.log_login_attempt(request, username, success=False)
            return None
        
        # Проверяем блокировку аккаунта
        security_profile, created = SecurityProfile.objects.get_or_create(user=user)
        
        if security_profile.is_account_locked():
            self.log_login_attempt(request, username, success=False, reason="Account locked")
            return None
        
        # Проверяем пароль
        if user.check_password(password):
            # Проверяем срок действия пароля
            if security_profile.is_password_expired():
                self.log_login_attempt(request, username, success=False, reason="Password expired")
                return None
            
            # Проверяем подозрительную активность
            if self.is_suspicious_login(request, user):
                self.send_security_alert(user, 'suspicious_login', request)
            
            # Сбрасываем счетчик неудачных попыток
            security_profile.reset_failed_attempts()
            
            # Логируем успешный вход
            self.log_login_attempt(request, username, success=True)
            
            return user
        else:
            # Увеличиваем счетчик неудачных попыток
            security_profile.increment_failed_attempts()
            
            # Логируем неудачную попытку
            self.log_login_attempt(request, username, success=False)
            
            return None
    
    def log_login_attempt(self, request, username, success, reason=""):
        """Логирование попытки входа"""
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = None
        
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Определяем местоположение по IP
        location = self.get_location_from_ip(ip_address)
        
        LoginHistory.objects.create(
            user=user,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            location=location
        )
    
    def is_suspicious_login(self, request, user):
        """Проверка на подозрительную активность"""
        ip_address = self.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Проверяем историю входов
        recent_logins = LoginHistory.objects.filter(
            user=user,
            success=True
        ).order_by('-timestamp')[:5]
        
        if recent_logins:
            last_login = recent_logins[0]
            
            # Проверяем смену IP
            if last_login.ip_address != ip_address:
                return True
            
            # Проверяем смену User-Agent
            if last_login.user_agent != user_agent:
                return True
        
        return False
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_location_from_ip(self, ip_address):
        """Определение местоположения по IP"""
        try:
            if ip_address in ['127.0.0.1', 'localhost']:
                return 'Localhost'
            
            response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=2)
            data = response.json()
            
            if data['status'] == 'success':
                return f"{data['city']}, {data['country']}"
            else:
                return 'Unknown'
                
        except requests.RequestException:
            return 'Unknown'
    
    def send_security_alert(self, user, alert_type, request):
        """Отправка оповещения о безопасности"""
        from .models_security import SecurityAlert
        
        messages = {
            'suspicious_login': f'Подозрительный вход с IP {self.get_client_ip(request)}',
            'password_change': 'Пароль был изменен',
            '2fa_enabled': 'Включена двухфакторная аутентификация',
            'new_device': 'Обнаружен вход с нового устройства',
        }
        
        SecurityAlert.objects.create(
            user=user,
            alert_type=alert_type,
            message=messages.get(alert_type, 'Событие безопасности'),
            ip_address=self.get_client_ip(request)
        )