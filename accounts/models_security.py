from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import secrets

User = get_user_model()

class SecurityProfile(models.Model):
    """Расширенный профиль безопасности пользователя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='security_profile')
    totp_secret = models.CharField(max_length=32, blank=True, null=True)  # Для 2FA
    backup_codes = models.JSONField(default=list, blank=True)  # Резервные коды
    is_2fa_enabled = models.BooleanField(default=False)
    last_password_change = models.DateTimeField(auto_now_add=True)
    password_expiry_date = models.DateTimeField(blank=True, null=True)
    failed_login_attempts = models.PositiveIntegerField(default=0)
    account_locked_until = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        verbose_name = 'Профиль безопасности'
        verbose_name_plural = 'Профили безопасности'
    
    def __str__(self):
        return f"Security profile for {self.user.username}"
    
    def is_account_locked(self):
        """Проверка заблокирован ли аккаунт"""
        if self.account_locked_until and timezone.now() < self.account_locked_until:
            return True
        return False
    
    def increment_failed_attempts(self):
        """Увеличение счетчика неудачных попыток входа"""
        self.failed_login_attempts += 1
        
        # Блокировка после 5 неудачных попыток
        if self.failed_login_attempts >= 5:
            self.account_locked_until = timezone.now() + timedelta(minutes=30)
        
        self.save()
    
    def reset_failed_attempts(self):
        """Сброс счетчика неудачных попыток"""
        self.failed_login_attempts = 0
        self.account_locked_until = None
        self.save()
    
    def is_password_expired(self):
        """Проверка истек ли срок действия пароля"""
        if self.password_expiry_date:
            return timezone.now() > self.password_expiry_date
        return False
    
    def set_password_expiry(self, days=90):
        """Установка срока действия пароля"""
        self.password_expiry_date = timezone.now() + timedelta(days=days)
        self.save()

class LoginHistory(models.Model):
    """История входов пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
    location = models.CharField(max_length=100, blank=True)
    
    class Meta:
        verbose_name = 'История входа'
        verbose_name_plural = 'История входов'
        ordering = ['-timestamp']
    
    def __str__(self):
        status = "Успешно" if self.success else "Неудачно"
        return f"{self.user.username} - {self.ip_address} - {status}"

class APIToken(models.Model):
    """API токены для внешних интеграций"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='api_tokens')
    name = models.CharField(max_length=100)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    permissions = models.JSONField(default=dict)  # Разрешения токена
    
    class Meta:
        verbose_name = 'API Токен'
        verbose_name_plural = 'API Токены'
    
    def __str__(self):
        return f"{self.name} - {self.user.username}"
    
    def generate_token(self):
        """Генерация безопасного токена"""
        self.token = secrets.token_urlsafe(32)
        return self.token
    
    def is_expired(self):
        """Проверка истек ли срок действия токена"""
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

class SecurityAlert(models.Model):
    """Система оповещений о безопасности"""
    ALERT_TYPES = [
        ('suspicious_login', 'Подозрительный вход'),
        ('password_change', 'Смена пароля'),
        ('2fa_enabled', 'Включена 2FA'),
        ('new_device', 'Новое устройство'),
        ('data_export', 'Экспорт данных'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='security_alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    message = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'Оповещение безопасности'
        verbose_name_plural = 'Оповещения безопасности'
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.get_alert_type_display()} - {self.user.username}"