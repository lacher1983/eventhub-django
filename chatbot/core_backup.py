# import re
# import json
# import logging
# from datetime import datetime, timedelta
# from typing import Dict, List, Any, Optional
# import spacy
# from django.apps import apps

# logger = logging.getLogger(__name__)

# class EventHubChatBot:
#     """Продвинутый чатбот для поиска мероприятий"""
    
#     def __init__(self):
#         self.nlp = None
#         self.load_nlp_model()
        
#     def load_nlp_model(self):
#         """Загрузка NLP модели"""
#         try:
#             self.nlp = spacy.load("ru_core_news_sm")
#             logger.info("SpaCy model loaded successfully")
#         except OSError:
#             logger.warning("SpaCy model not found. Using simple text processing.")
#             self.nlp = None
    
#     def process_message(self, message: str, user=None, session_id: str = None) -> Dict[str, Any]:
#         """Основной метод обработки сообщения"""
#         try:
#             # Анализ интента
#             intent = self.detect_intent(message)
            
#             # Извлечение сущностей
#             entities = self.extract_entities(message)
            
#             # Обработка в зависимости от интента
#             response_data = self.handle_intent(intent, entities, user)
            
#             return {
#                 'response': response_data['response'],
#                 'intent': intent,
#                 'suggestions': response_data.get('suggestions', []),
#                 'events': response_data.get('events', []),
#                 'entities': entities,
#                 'session_id': session_id
#             }
            
#         except Exception as e:
#             logger.error(f"Error processing message: {e}")
#             return {
#                 'response': "Извините, произошла ошибка при обработке вашего запроса.",
#                 'intent': 'error',
#                 'suggestions': ['Попробовать снова', 'Помощь'],
#                 'events': [],
#                 'session_id': session_id
#             }
    
#     def detect_intent(self, message: str) -> str:
#         """Определение намерения пользователя"""
#         message_lower = message.lower()
        
#         intent_patterns = {
#             'greeting': ['привет', 'здравствуй', 'hello', 'hi', 'добрый', 'здорово'],
#             'search_events': ['найди', 'ищи', 'поиск', 'мероприятия', 'события', 'ивенты', 'концерт', 'фестиваль'],
#             'free_events': ['бесплатные', 'бесплатно', 'free', 'даром'],
#             'help': ['помощь', 'help', 'умеешь', 'можешь', 'функции'],
#             'today_events': ['сегодня', 'сейчас', 'в этот день'],
#             'weekend_events': ['выходные', 'суббота', 'воскресенье', 'уикенд'],
#             'location_events': ['москв', 'питер', 'спб', 'online', 'онлайн'],
#             'event_types': ['конференц', 'концерт', 'выставк', 'мастер-класс', 'вебинар', 'фестиваль']
#         }
        
#         for intent, patterns in intent_patterns.items():
#             if any(pattern in message_lower for pattern in patterns):
#                 return intent
        
#         return 'unknown'
    
#     def extract_entities(self, message: str) -> Dict[str, Any]:
#         """Извлечение сущностей из сообщения"""
#         entities = {
#             'event_type': None,
#             'location': None,
#             'date': None,
#             'price_range': None,
#             'category': None
#         }
        
#         # Простая логика извлечения (можно заменить на spaCy)
#         message_lower = message.lower()
        
#         # Типы мероприятий
#         event_types = {
#             'конференц': 'conference',
#             'концерт': 'concert', 
#             'выставк': 'exhibition',
#             'мастер-класс': 'masterclass',
#             'вебинар': 'webinar',
#             'фестиваль': 'festival',
#             'встреч': 'meetup'
#         }
        
#         for pattern, event_type in event_types.items():
#             if pattern in message_lower:
#                 entities['event_type'] = event_type
#                 break
        
#         # Локации
#         locations = {
#             'москв': 'Москва',
#             'питер': 'Санкт-Петербург',
#             'спб': 'Санкт-Петербург',
#             'онлайн': 'online',
#             'online': 'online'
#         }
        
#         for pattern, location in locations.items():
#             if pattern in message_lower:
#                 entities['location'] = location
#                 break
        
#         # Дата
#         date_patterns = {
#             'сегодня': datetime.now().date(),
#             'завтра': (datetime.now() + timedelta(days=1)).date(),
#             'послезавтра': (datetime.now() + timedelta(days=2)).date(),
#             'недел': (datetime.now() + timedelta(days=7)).date()
#         }
        
#         for pattern, date in date_patterns.items():
#             if pattern in message_lower:
#                 entities['date'] = date.strftime('%Y-%m-%d')
#                 break
        
#         # Цена
#         if 'бесплат' in message_lower:
#             entities['price_range'] = 'free'
#         elif 'платн' in message_lower or 'билет' in message_lower:
#             entities['price_range'] = 'paid'
        
#         return entities
    
#     def handle_intent(self, intent: str, entities: Dict, user=None) -> Dict[str, Any]:
#         """Обработка конкретного интента"""
#         if intent == 'greeting':
#             return self.handle_greeting()
#         elif intent == 'search_events':
#             return self.handle_search_events(entities, user)
#         elif intent == 'free_events':
#             return self.handle_free_events(entities, user)
#         elif intent == 'help':
#             return self.handle_help()
#         elif intent == 'today_events':
#             return self.handle_today_events(entities, user)
#         else:
#             return self.handle_unknown()
    
#     def handle_greeting(self) -> Dict[str, Any]:
#         """Обработка приветствия"""
#         return {
#             'response': "Привет! Я ваш помощник EventHub! 🤖\n\nЯ могу помочь вам найти мероприятия, подобрать события по интересам или ответить на вопросы. Чем могу помочь?",
#             'suggestions': [
#                 "Найди мероприятия на неделе",
#                 "Покажи бесплатные события", 
#                 "Какие концерты есть?",
#                 "Помощь"
#             ]
#         }
    
#     def handle_search_events(self, entities: Dict, user=None) -> Dict[str, Any]:
#         """Поиск мероприятий"""
#         # Здесь будет реальный поиск в БД
#         # Пока используем заглушку
        
#         events = self.search_events_in_db(entities)
        
#         if events:
#             response = f"🎯 Нашел для вас мероприятия!\n\n"
#             for event in events[:3]:  # Показываем первые 3
#                 response += f"• {event['title']} ({event['date']})\n"
            
#             if len(events) > 3:
#                 response += f"\n... и еще {len(events) - 3} мероприятий"
#         else:
#             response = "К сожалению, по вашему запросу ничего не найдено. 😔\n\nПопробуйте изменить параметры поиска."
        
#         return {
#             'response': response,
#             'events': events,
#             'suggestions': [
#                 "Бесплатные мероприятия",
#                 "События на сегодня",
#                 "Концерты в Москве"
#             ]
#         }
    
#     def handle_free_events(self, entities: Dict, user=None) -> Dict[str, Any]:
#         """Поиск бесплатных мероприятий"""
#         entities['price_range'] = 'free'
#         events = self.search_events_in_db(entities)
        
#         if events:
#             response = "🆓 Вот бесплатные мероприятия:\n\n"
#             for event in events[:5]:
#                 price_info = "Бесплатно" if event['price'] == 0 else f"{event['price']}₽"
#                 response += f"• {event['title']} - {price_info}\n"
#         else:
#             response = "К сожалению, бесплатных мероприятий не найдено. 😔"
        
#         return {
#             'response': response,
#             'events': events,
#             'suggestions': [
#                 "Все мероприятия",
#                 "События на выходные", 
#                 "Мастер-классы"
#             ]
#         }
    
#     def handle_help(self) -> Dict[str, Any]:
#         """Справка по возможностям"""
#         response = """🛠️ **Мои возможности:**

# 🎯 **Поиск мероприятий** - найду события по категориям, дате, местоположению
# 📅 **Расписание** - покажу что происходит сегодня, завтра или на неделе  
# 💰 **Фильтрация** - бесплатные/платные мероприятия
# 👥 **Рекомендации** - подберу события по интересам
# 🎫 **Регистрация** - помогу с билетами

# **Примеры запросов:**
# • "Найди концерты в Москве"
# • "Что сегодня интересного?"
# • "Бесплатные мастер-классы"
# • "IT конференции на следующей неделе" """
        
#         return {
#             'response': response,
#             'suggestions': [
#                 "Найди мероприятия",
#                 "Бесплатные события",
#                 "Что сегодня?"
#             ]
#         }
    
#     def handle_today_events(self, entities: Dict, user=None) -> Dict[str, Any]:
#         """События на сегодня"""
#         entities['date'] = datetime.now().date().strftime('%Y-%m-%d')
#         events = self.search_events_in_db(entities)
        
#         if events:
#             response = "📅 **События на сегодня:**\n\n"
#             for event in events:
#                 response += f"• {event['title']} в {event['location']}\n"
#         else:
#             response = "На сегодня мероприятий не запланировано. Может посмотрим на другие дни? 📆"
        
#         return {
#             'response': response,
#             'events': events,
#             'suggestions': [
#                 "На завтра",
#                 "На неделе",
#                 "Все мероприятия"
#             ]
#         }
    
#     def handle_unknown(self) -> Dict[str, Any]:
#         """Обработка неизвестного запроса"""
#         return {
#             'response': "Не совсем понял ваш вопрос. 🤔\n\nЯ специализируюсь на поиске мероприятий. Попробуйте спросить о событиях, концертах, конференциях или использовать кнопки ниже!",
#             'suggestions': [
#                 "Найди мероприятия",
#                 "Что ты умеешь?",
#                 "Бесплатные события",
#                 "События сегодня"
#             ]
#         }
    
#     def search_events_in_db(self, entities: Dict) -> List[Dict]:
#         """Поиск мероприятий в базе данных (заглушка)"""
#         # В реальном приложении здесь будет запрос к моделям Event
#         # Пока возвращаем тестовые данные
        
#         sample_events = [
#             {
#                 'id': 1,
#                 'title': 'Технологическая конференция Future Tech',
#                 'date': '2024-09-25',
#                 'location': 'Москва',
#                 'price': 0,
#                 'type': 'conference',
#                 'description': 'Конференция о будущем технологий и инноваций'
#             },
#             {
#                 'id': 2, 
#                 'title': 'Джазовый вечер в City Club',
#                 'date': '2024-09-28',
#                 'location': 'Санкт-Петербург',
#                 'price': 1500,
#                 'type': 'concert',
#                 'description': 'Вечер живой джазовой музыки'
#             },
#             {
#                 'id': 3,
#                 'title': 'Бесплатный мастер-класс по маркетингу',
#                 'date': '2024-09-26', 
#                 'location': 'Онлайн',
#                 'price': 0,
#                 'type': 'masterclass',
#                 'description': 'Онлайн мастер-класс по digital маркетингу'
#             }
#         ]
        
#         # Простая фильтрация (в реальном приложении будет сложнее)
#         filtered_events = []
        
#         for event in sample_events:
#             include = True
            
#             if entities.get('price_range') == 'free' and event['price'] > 0:
#                 include = False
#             if entities.get('location') and entities['location'].lower() not in event['location'].lower():
#                 include = False
#             if entities.get('event_type') and entities['event_type'] != event['type']:
#                 include = False
            
#             if include:
#                 filtered_events.append(event)
        
#         return filtered_events if filtered_events else sample_events[:1]  # Если ничего не найдено, возвращаем хотя бы одно

# # Создаем глобальный экземпляр бота
# chatbot = EventHubChatBot()