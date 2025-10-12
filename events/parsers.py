import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class BaseParser:
    """Базовый класс парсера"""
    
    def __init__(self, source):
        self.source = source
        self.config = source.parser_config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def parse_events(self):
        """Основной метод парсинга событий"""
        raise NotImplementedError
    
    def normalize_date(self, date_str):
        """Нормализация даты"""
        try:
            # Удаляем лишние пробелы и приводим к нижнему регистру
            date_str = re.sub(r'\s+', ' ', date_str).strip().lower()
            
            # Парсим различные форматы дат
            formats = [
                '%d.%m.%Y %H:%M',
                '%Y-%m-%d %H:%M:%S',
                '%d %B %Y %H:%M',
                '%B %d, %Y %H:%M',
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            
            # Если не удалось распарсить, возвращаем текущую дату
            return timezone.now()
        except Exception as e:
            logger.error(f"Error parsing date {date_str}: {e}")
            return timezone.now()

class BezkassiraParser(BaseParser):
    """Парсер для bezkassira.by"""
    
    def parse_events(self):
        try:
            response = self.session.get(self.source.url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            events = []
            
            # Поиск карточек мероприятий - адаптируйте под актуальную структуру
            event_cards = soup.find_all('div', class_=lambda x: x and any(cls in x for cls in ['event', 'card', 'ticket', 'item']))
            
            for card in event_cards[:10]:  # Ограничим первыми 10 для теста
                try:
                    event_data = self.parse_event_card(card)
                    if event_data:
                        events.append(event_data)
                except Exception as e:
                    logger.error(f"Error parsing event card: {e}")
                    continue
            
            return events
        except Exception as e:
            logger.error(f"Error parsing bezkassira: {e}")
            return []
    
    def parse_event_card(self, card):
        """Парсит отдельную карточку мероприятия"""
        try:
            # Поиск заголовка
            title_elem = card.find(['h1', 'h2', 'h3', 'h4', '.title', '.event-title'])
            title = title_elem.get_text().strip() if title_elem else "Неизвестное мероприятие"
            
            # Поиск ссылки
            link_elem = card.find('a')
            event_url = link_elem.get('href') if link_elem else self.source.url
            if event_url and not event_url.startswith('http'):
                event_url = self.source.url.rstrip('/') + event_url
            
            return {
                'external_id': f"bezkassira_{hash(title)}",
                'title': title,
                'description': f"Мероприятие с Bezkassira.by: {title}",
                'short_description': title[:200],
                'date': timezone.now() + timedelta(days=1),  # Завтрашняя дата для примера
                'location': 'Минск, Беларусь',
                'price': 0,
                'is_free': True,
                'image_url': '',
                'external_url': event_url,
                'category': 'Развлечения',
                'raw_data': {'title': title, 'source': 'bezkassira'}
            }
        except Exception as e:
            logger.error(f"Error in parse_event_card: {e}")
            return None

class RelaxAfishaParser(BaseParser):
    """Парсер для afisha.relax.by"""
    
    def parse_events(self):
        try:
            response = self.session.get(self.source.url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            events = []
            
            # Базовый парсинг для теста
            event_elements = soup.find_all('div', class_=lambda x: x and any(cls in x for cls in ['event', 'afisha', 'item']))
            
            for element in event_elements[:10]:
                try:
                    event_data = self.parse_event_element(element)
                    if event_data:
                        events.append(event_data)
                except Exception as e:
                    logger.error(f"Error parsing relax event: {e}")
                    continue
            
            return events
        except Exception as e:
            logger.error(f"Error parsing relax.by: {e}")
            return []
    
    def parse_event_element(self, element):
        """Парсит элемент мероприятия с relax.by"""
        try:
            title_elem = element.find(['h1', 'h2', 'h3', 'h4', '.title'])
            title = title_elem.get_text().strip() if title_elem else "Событие с Relax.by"
            
            return {
                'external_id': f"relax_{hash(str(element))}",
                'title': title,
                'description': f"Мероприятие с Relax.by: {title}",
                'short_description': title[:200],
                'date': timezone.now() + timedelta(days=2),
                'location': 'Минск, Беларусь',
                'price': 0,
                'is_free': True,
                'image_url': '',
                'external_url': self.source.url,
                'category': 'Культура',
                'raw_data': {'title': title, 'source': 'relax'}
            }
        except Exception as e:
            logger.error(f"Error in parse_event_element: {e}")
            return None

class CultureRuParser(BaseParser):
    """Парсер для culture.ru"""
    
    def parse_events(self):
        try:
            response = self.session.get(self.source.url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            events = []
            
            # Базовый парсинг
            event_elements = soup.find_all('div', class_=lambda x: x and any(cls in x for cls in ['event', 'card', 'item']))
            
            for element in event_elements[:10]:
                try:
                    event_data = self.parse_culture_event(element)
                    if event_data:
                        events.append(event_data)
                except Exception as e:
                    logger.error(f"Error parsing culture.ru event: {e}")
                    continue
            
            return events
        except Exception as e:
            logger.error(f"Error parsing culture.ru: {e}")
            return []
    
    def parse_culture_event(self, element):
        """Парсит мероприятие с culture.ru"""
        try:
            title_elem = element.find(['h1', 'h2', 'h3', 'h4', '.title'])
            title = title_elem.get_text().strip() if title_elem else "Культурное событие"
            
            return {
                'external_id': f"culture_{hash(str(element))}",
                'title': title,
                'description': f"Культурное мероприятие с Culture.ru: {title}",
                'short_description': title[:200],
                'date': timezone.now() + timedelta(days=3),
                'location': 'Москва, Россия',
                'price': 0,
                'is_free': True,
                'image_url': '',
                'external_url': self.source.url,
                'category': 'Культура',
                'raw_data': {'title': title, 'source': 'culture'}
            }
        except Exception as e:
            logger.error(f"Error in parse_culture_event: {e}")
            return None

class EventsInRussiaParser(BaseParser):
    """Парсер для eventsinrussia.com"""
    
    def parse_events(self):
        try:
            response = self.session.get(self.source.url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            events = []
            
            # Базовый парсинг
            event_elements = soup.find_all('div', class_=lambda x: x and any(cls in x for cls in ['event', 'card', 'item']))
            
            for element in event_elements[:10]:
                try:
                    event_data = self.parse_russia_event(element)
                    if event_data:
                        events.append(event_data)
                except Exception as e:
                    logger.error(f"Error parsing eventsinrussia event: {e}")
                    continue
            
            return events
        except Exception as e:
            logger.error(f"Error parsing eventsinrussia.com: {e}")
            return []
    
    def parse_russia_event(self, element):
        """Парсит мероприятие с eventsinrussia.com"""
        try:
            title_elem = element.find(['h1', 'h2', 'h3', 'h4', '.title'])
            title = title_elem.get_text().strip() if title_elem else "Событие в России"
            
            return {
                'external_id': f"russia_{hash(str(element))}",
                'title': title,
                'description': f"Мероприятие в России: {title}",
                'short_description': title[:200],
                'date': timezone.now() + timedelta(days=4),
                'location': 'Россия',
                'price': 0,
                'is_free': True,
                'image_url': '',
                'external_url': self.source.url,
                'category': 'Развлечения',
                'raw_data': {'title': title, 'source': 'russia'}
            }
        except Exception as e:
            logger.error(f"Error in parse_russia_event: {e}")
            return None

PARSER_MAPPING = {
    'bezkassira.by': BezkassiraParser,
    'relax.by': RelaxAfishaParser,
    'culture.ru': CultureRuParser,
    'eventsinrussia.com': EventsInRussiaParser,
}

def get_parser(source):
    """Фабрика парсеров"""
    for domain, parser_class in PARSER_MAPPING.items():
        if domain in source.url:
            return parser_class(source)
    return BaseParser(source)