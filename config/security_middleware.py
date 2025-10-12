import re
from django.http import HttpResponseForbidden, HttpResponse
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
import time
import hashlib

class SecurityHeadersMiddleware(MiddlewareMixin):
    """Middleware для добавления security headers"""
    
    def process_response(self, request, response):
        # CSP (Content Security Policy)
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://api-maps.yandex.ru; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "img-src 'self' data: https: http:; "
            "font-src 'self' https://fonts.gstatic.com; "
            "connect-src 'self' https://api-maps.yandex.ru; "
            "frame-ancestors 'self';"
        )
        
        response.headers['Content-Security-Policy'] = csp
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Убираем информацию о сервере
        if 'Server' in response.headers:
            del response.headers['Server']
        
        return response

class RateLimitMiddleware(MiddlewareMixin):
    """Middleware для ограничения запросов"""
    
    def process_request(self, request):
        # Игнорируем статические файлы и админку
        if request.path.startswith('/static/') or request.path.startswith('/admin/'):
            return None
        
        # Генерируем ключ на основе IP и пути
        ip = self.get_client_ip(request)
        path = request.path
        key = f"ratelimit:{ip}:{path}"
        
        # Проверяем лимит
        current = cache.get(key, 0)
        
        if current >= 100:  # 100 запросов в минуту
            return HttpResponse('Too Many Requests', status=429)
        
        cache.set(key, current + 1, 60)  # Сбрасываем каждую минуту
        return None
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class SQLInjectionProtectionMiddleware(MiddlewareMixin):
    """Защита от SQL инъекций"""
    
    SQL_KEYWORDS = [
        'union', 'select', 'insert', 'update', 'delete', 'drop', 
        'create', 'alter', 'exec', 'execute', 'script', 'javascript'
    ]
    
    def process_request(self, request):
        # Проверяем GET параметры
        for key, value in request.GET.items():
            if self.check_sql_injection(str(value)):
                return HttpResponseForbidden('Invalid request')
        
        # Проверяем POST данные
        if request.method == 'POST':
            for key, value in request.POST.items():
                if self.check_sql_injection(str(value)):
                    return HttpResponseForbidden('Invalid request')
        
        return None
    
    def check_sql_injection(self, value):
        value_lower = value.lower()
        
        # Проверяем SQL ключевые слова
        for keyword in self.SQL_KEYWORDS:
            if keyword in value_lower and len(value) < 100:  # Игнорируем длинные легитимные тексты
                # Проверяем контекст - если это часть слова, пропускаем
                pattern = r'\b' + re.escape(keyword) + r'\b'
                if re.search(pattern, value_lower):
                    return True
        
        # Проверяем SQL-specific символы в опасных комбинациях
        dangerous_patterns = [
            r"'.*--",
            r"'.*;",
            r"'.*union.*select",
            r"'.*drop.*table"
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, value_lower, re.IGNORECASE):
                return True
        
        return False

class XSSProtectionMiddleware(MiddlewareMixin):
    """Базовая защита от XSS"""
    
    def process_request(self, request):
        suspicious_patterns = [
            r'<script.*?>',
            r'javascript:',
            r'onload=',
            r'onerror=',
            r'onclick=',
            r'vbscript:'
        ]
        
        # Проверяем все параметры
        all_params = []
        all_params.extend(request.GET.values())
        if request.method == 'POST':
            all_params.extend(request.POST.values())
        
        for param in all_params:
            param_str = str(param)
            for pattern in suspicious_patterns:
                if re.search(pattern, param_str, re.IGNORECASE):
                    return HttpResponseForbidden('Invalid request')
        
        return None