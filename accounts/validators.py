import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
import hashlib
import requests

class PasswordValidator:
    """Расширенная валидация паролей"""
    
    def __init__(self):
        self.min_length = 8
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_numbers = True
        self.require_special_chars = True
        self.special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    
    def validate(self, password, user=None):
        errors = []
        
        if len(password) < self.min_length:
            errors.append(_(
                f'Пароль должен содержать минимум {self.min_length} символов.'
            ))
        
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append(_(
                'Пароль должен содержать хотя бы одну заглавную букву.'
            ))
        
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append(_(
                'Пароль должен содержать хотя бы одну строчную букву.'
            ))
        
        if self.require_numbers and not re.search(r'[0-9]', password):
            errors.append(_(
                'Пароль должен содержать хотя бы одну цифру.'
            ))
        
        if self.require_special_chars and not any(char in self.special_chars for char in password):
            errors.append(_(
                f'Пароль должен содержать хотя бы один специальный символ: {self.special_chars}'
            ))
        
        # Проверка на распространенные пароли
        if self.is_common_password(password):
            errors.append(_(
                'Этот пароль слишком распространен. Выберите другой.'
            ))
        
        # Проверка на последовательности
        if self.has_sequential_chars(password):
            errors.append(_(
                'Пароль не должен содержать последовательные символы (abc, 123 и т.д.).'
            ))
        
        if errors:
            raise ValidationError(errors)
    
    def is_common_password(self, password):
        """Проверка на распространенные пароли"""
        common_passwords = {
            'password', '123456', '12345678', '123456789', 'qwerty',
            'abc123', 'password1', '12345', '1234567', '111111',
            '1234567890', 'admin', 'letmein', 'welcome', 'monkey'
        }
        return password.lower() in common_passwords
    
    def has_sequential_chars(self, password):
        """Проверка на последовательные символы"""
        sequences = [
            'abcdefghijklmnopqrstuvwxyz',
            'zyxwvutsrqponmlkjihgfedcba',
            '0123456789',
            '9876543210',
            'qwertyuiop',
            'poiuytrewq'
        ]
        
        password_lower = password.lower()
        
        for seq in sequences:
            for i in range(len(seq) - 2):
                if seq[i:i+3] in password_lower:
                    return True
        
        return False
    
    def get_help_text(self):
        return _(
            f"Ваш пароль должен содержать:\n"
            f"- Не менее {self.min_length} символов\n"
            f"- Заглавные и строчные буквы\n"
            f"- Цифры\n"
            f"- Специальные символы: {self.special_chars}\n"
            f"- Не быть распространенным паролем\n"
            f"- Не содержать последовательных символов"
        )

class HaveIBeenPwnedValidator:
    """Проверка пароля через Have I Been Pwned API"""
    
    def validate(self, password, user=None):
        try:
            # Хешируем пароль
            password_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
            prefix = password_hash[:5]
            suffix = password_hash[5:]
            
            # Делаем запрос к API
            url = f'https://api.pwnedpasswords.com/range/{prefix}'
            response = requests.get(url, timeout=2)
            
            if response.status_code == 200:
                hashes = response.text.split('\n')
                for h in hashes:
                    if h.startswith(suffix):
                        count = int(h.split(':')[1])
                        raise ValidationError(_(
                            f'Этот пароль был скомпрометирован в {count} утечках данных. '
                            'Пожалуйста, выберите другой пароль.'
                        ))
        
        except (requests.RequestException, ValueError):
            # В случае ошибки подключения пропускаем проверку
            pass
    
    def get_help_text(self):
        return _('Пароль проверяется на наличие в известных утечках данных.')
    

def validate_image_file(image):
    if not image.content_type.startswith('image/'):
        raise ValidationError("Файл должен быть изображением.")