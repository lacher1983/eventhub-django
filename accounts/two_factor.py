import pyotp
import qrcode
from io import BytesIO
import base64
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import secrets

class TwoFactorAuth:
    """Система двухфакторной аутентификации"""
    
    def __init__(self, user):
        self.user = user
    
    def generate_secret(self):
        """Генерация секретного ключа для 2FA"""
        secret = pyotp.random_base32()
        
        # Сохраняем секрет в профиле пользователя
        if hasattr(self.user, 'profile'):
            self.user.profile.totp_secret = secret
            self.user.profile.save()
        else:
            # Создаем временное хранение
            from django.core.cache import cache
            cache_key = f"2fa_setup_{self.user.id}"
            cache.set(cache_key, secret, 3600)  # Храним 1 час
        
        return secret
    
    def generate_qr_code(self, secret, issuer_name="EventHub"):
        """Генерация QR-кода для приложения аутентификатора"""
        totp = pyotp.TOTP(secret)
        provisioning_url = totp.provisioning_uri(
            name=self.user.email,
            issuer_name=issuer_name
        )
        
        # Генерируем QR-код
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        
        return base64.b64encode(buffer.getvalue()).decode()
    
    def verify_code(self, code, secret=None):
        """Проверка кода аутентификатора"""
        if secret is None:
            if hasattr(self.user, 'profile') and self.user.profile.totp_secret:
                secret = self.user.profile.totp_secret
            else:
                return False
        
        totp = pyotp.TOTP(secret)
        return totp.verify(code)
    
    def generate_backup_codes(self, count=10):
        """Генерация резервных кодов"""
        backup_codes = [secrets.token_hex(4).upper() for _ in range(count)]
        
        # Сохраняем захешированные коды
        if hasattr(self.user, 'profile'):
            import hashlib
            hashed_codes = [hashlib.sha256(code.encode()).hexdigest() for code in backup_codes]
            self.user.profile.backup_codes = hashed_codes
            self.user.profile.save()
        
        return backup_codes
    
    def verify_backup_code(self, code):
        """Проверка резервного кода"""
        if not hasattr(self.user, 'profile') or not self.user.profile.backup_codes:
            return False
        
        import hashlib
        hashed_code = hashlib.sha256(code.encode()).hexdigest()
        
        if hashed_code in self.user.profile.backup_codes:
            # Удаляем использованный код
            self.user.profile.backup_codes.remove(hashed_code)
            self.user.profile.save()
            return True
        
        return False

class Email2FA:
    """Двухфакторная аутентификация через email"""
    
    def __init__(self, user):
        self.user = user
    
    def send_code(self):
        """Отправка кода на email"""
        code = ''.join([str(secrets.randbelow(10)) for _ in range(6)])
        
        # Сохраняем код в кэш
        from django.core.cache import cache
        cache_key = f"email_2fa_{self.user.id}"
        cache.set(cache_key, code, 300)  # 5 минут
        
        # Отправляем email
        send_mail(
            'Код подтверждения для EventHub',
            f'Ваш код подтверждения: {code}\nКод действителен в течение 5 минут.',
            settings.DEFAULT_FROM_EMAIL,
            [self.user.email],
            fail_silently=False,
        )
        
        return True
    
    def verify_code(self, code):
        """Проверка кода из email"""
        from django.core.cache import cache
        cache_key = f"email_2fa_{self.user.id}"
        stored_code = cache.get(cache_key)
        
        if stored_code and stored_code == code:
            cache.delete(cache_key)
            return True
        
        return False