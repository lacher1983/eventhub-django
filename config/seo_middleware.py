from django.utils.deprecation import MiddlewareMixin
from django.utils.html import strip_tags
import re

class SEOMiddleware(MiddlewareMixin):
    """Middleware для SEO оптимизации"""
    
    def process_response(self, request, response):
        if hasattr(response, 'content') and 'text/html' in response.get('Content-Type', ''):
            content = response.content.decode('utf-8')
            
            # Добавляем микроразметку для мероприятий
            if '/event/' in request.path and request.method == 'GET':
                content = self.add_event_structured_data(content, request)
            
            # Оптимизация мета-тегов
            content = self.optimize_meta_tags(content, request)
            
            # Добавляем канонические ссылки
            content = self.add_canonical_url(content, request)
            
            # Оптимизация заголовков
            content = self.optimize_headers(content)
            
            response.content = content.encode('utf-8')
        
        return response
    
    def add_event_structured_data(self, content, request):
        """Добавление structured data для мероприятий"""
        # Эта функция будет дополнена в views
        if '<!-- EVENT_STRUCTURED_DATA -->' in content:
            # Заменяем placeholder на реальные данные
            structured_data = self.generate_event_structured_data(request)
            content = content.replace('<!-- EVENT_STRUCTURED_DATA -->', structured_data)
        
        return content
    
    def generate_event_structured_data(self, request):
        """Генерация JSON-LD разметки для мероприятия"""
        # Данные будут добавляться в view
        return '''
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "Event",
            "name": "{{ event.title }}",
            "description": "{{ event.short_description }}",
            "startDate": "{{ event.date|date:'c' }}",
            "endDate": "{{ event.end_date|date:'c' }}",
            "location": {
                "@type": "Place",
                "name": "{{ event.location }}",
                "address": "{{ event.location }}"
            },
            "organizer": {
                "@type": "Organization",
                "name": "{{ event.organizer.username }}"
            }
        }
        </script>
        '''
    
    def optimize_meta_tags(self, content, request):
        """Оптимизация мета-тегов"""
        title_match = re.search(r'<title>(.*?)</title>', content)
        if title_match:
            title = title_match.group(1)
            # Убедимся что title не слишком длинный
            if len(title) > 60:
                title = title[:57] + '...'
                content = content.replace(title_match.group(0), f'<title>{title}</title>')
        
        # Добавляем meta description если его нет
        if '<meta name="description"' not in content:
            description = self.generate_meta_description(content)
            meta_description = f'<meta name="description" content="{description}">'
            head_end = content.find('</head>')
            if head_end != -1:
                content = content[:head_end] + meta_description + content[head_end:]
        
        # Добавляем Open Graph разметку
        og_tags = self.generate_og_tags(request, content)
        head_end = content.find('</head>')
        if head_end != -1:
            content = content[:head_end] + og_tags + content[head_end:]
        
        return content
    
    def generate_meta_description(self, content, max_length=160):
        """Генерация meta description из контента"""
        # Извлекаем текст из контента
        text = strip_tags(content)
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Берем первую осмысленную часть текста
        sentences = re.split(r'[.!?]', text)
        description = ''
        
        for sentence in sentences:
            if len(sentence.strip()) > 20:
                description = sentence.strip()
                break
        
        if not description:
            description = text[:max_length]
        
        # Обрезаем до максимальной длины
        if len(description) > max_length:
            description = description[:max_length-3] + '...'
        
        return description
    
    def generate_og_tags(self, request, content):
        """Генерация Open Graph разметки"""
        base_url = f"https://{request.get_host()}"
        
        og_tags = f'''
        <meta property="og:type" content="website">
        <meta property="og:site_name" content="EventHub">
        <meta property="og:url" content="{base_url}{request.path}">
        '''
        
        # Добавляем title
        title_match = re.search(r'<title>(.*?)</title>', content)
        if title_match:
            title = title_match.group(1)
            og_tags += f'<meta property="og:title" content="{title}">\n'
        
        # Добавляем description
        description_match = re.search(r'<meta name="description" content="(.*?)"', content)
        if description_match:
            description = description_match.group(1)
            og_tags += f'<meta property="og:description" content="{description}">\n'
        
        # Добавляем image
        image_match = re.search(r'<img[^>]*src="([^"]*)"[^>]*>', content)
        if image_match:
            image_url = image_match.group(1)
            if not image_url.startswith(('http', '//')):
                image_url = base_url + image_url
            og_tags += f'<meta property="og:image" content="{image_url}">\n'
        
        return og_tags
    
    def add_canonical_url(self, content, request):
        """Добавление канонической ссылки"""
        base_url = f"https://{request.get_host()}"
        canonical_url = base_url + request.path
        
        canonical_tag = f'<link rel="canonical" href="{canonical_url}">'
        
        if '<link rel="canonical"' not in content:
            head_end = content.find('</head>')
            if head_end != -1:
                content = content[:head_end] + canonical_tag + content[head_end:]
        
        return content
    
    def optimize_headers(self, content):
        """Оптимизация заголовков h1-h6"""
        # Убедимся что есть только один h1 на странице
        h1_count = len(re.findall(r'<h1[^>]*>', content))
        if h1_count > 1:
            # Заменяем лишние h1 на h2
            h1_tags = re.finditer(r'<h1[^>]*>', content)
            for i, match in enumerate(h1_tags):
                if i > 0:  # Оставляем первый h1
                    content = content.replace(match.group(0), '<h2>')
                    # Закрывающий тег
                    content = content.replace('</h1>', '</h2>', 1)
        
        return content