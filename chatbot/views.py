from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import logging
import uuid

logger = logging.getLogger(__name__)

def chat_interface(request):
    """Основной интерфейс чата"""
    return render(request, 'chatbot/chat_interface.html')

@csrf_exempt
@require_http_methods(["POST"])
def chat_api(request):
    """API endpoint для обработки сообщений чатбота"""
    print("=== CHAT API CALLED ===")  # Это ДОЛЖНО появиться в консоли Django
    
    if request.method == 'POST':
        try:
            # Проверяем, что тело запроса не пустое
            if not request.body:
                print("Empty request body")
                return JsonResponse({'error': 'Пустой запрос'}, status=400)
            
            data = json.loads(request.body)
            message = data.get('message', '').strip()
            session_id = data.get('session_id', '')
            
            print(f"Received message: '{message}'")  # Должно появиться в консоли
            print(f"Session ID: {session_id}")
            
            if not message:
                print("Empty message")
                return JsonResponse({'error': 'Пустое сообщение'}, status=400)
            
            # Упрощенная логика ответов
            message_lower = message.lower()
            
            if any(word in message_lower for word in ['привет', 'здравствуй', 'hello', 'hi']):
                response_text = "Привет! Я ваш помощник EventHub. 🤖\n\nЯ могу помочь вам найти мероприятия, подобрать события по интересам или ответить на вопросы о регистрации. Чем могу помочь?"
                suggestions = ["Найди мероприятия", "Помощь", "Что сегодня?"]
                events = []
            
            elif any(word in message_lower for word in ['мероприятия', 'события', 'events', 'ивенты']):
                response_text = "Отлично! Ищу мероприятия для вас... 🎯\n\nВот что нашлось:"
                suggestions = ["Концерты", "Конференции", "Бесплатные мероприятия"]
                events = [
                    {
                        'id': 1,
                        'title': 'Технологическая конференция Future Tech',
                        'date': '25.09.2024',
                        'location': 'Москва',
                        'price': 0,
                        'type': 'Конференция',
                        'description': 'Конференция о будущем технологий и инноваций'
                    },
                    {
                        'id': 2,
                        'title': 'Джазовый вечер в City Club',
                        'date': '28.09.2024', 
                        'location': 'Санкт-Петербург',
                        'price': 1500,
                        'type': 'Концерт',
                        'description': 'Вечер живой джазовой музыки'
                    }
                ]
            
            elif any(word in message_lower for word in ['бесплатные', 'бесплатно', 'free']):
                response_text = "Вот бесплатные мероприятия: 🆓"
                suggestions = ["Все бесплатные", "Мастер-классы", "Волонтерские"]
                events = [
                    {
                        'id': 3,
                        'title': 'Бесплатный мастер-класс по маркетингу',
                        'date': '26.09.2024',
                        'location': 'Онлайн',
                        'price': 0,
                        'type': 'Мастер-класс',
                        'description': 'Онлайн мастер-класс по digital маркетингу'
                    }
                ]
            
            elif any(word in message_lower for word in ['помощь', 'help', 'умеешь']):
                response_text = "Я помогу вам:\n• Найти мероприятия 🎯\n• Подобрать события по интересам\n• Ответить на вопросы\n\nПросто спросите о мероприятиях!"
                suggestions = ["Что сегодня?", "Конференции", "Как найти события?"]
                events = []
            
            else:
                response_text = f"Вы спросили: '{message}'\n\nЯ специализируюсь на поиске мероприятий. Попробуйте спросить о событиях, концертах или конференциях! 🎪"
                suggestions = ["Найди мероприятия", "Что ты умеешь?", "Бесплатные события"]
                events = []
            
            print(f"Response: {response_text[:50]}...")  # Логируем начало ответа
            
            return JsonResponse({
                'response': response_text,
                'suggestions': suggestions,
                'events': events,
                'session_id': session_id or 'default_session'
            })
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            return JsonResponse({'error': 'Неверный формат JSON'}, status=400)
        except Exception as e:
            print(f"General error: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return JsonResponse({'error': f'Внутренняя ошибка: {str(e)}'}, status=500)
    
    print("GET request received")
    return JsonResponse({'error': 'Only POST allowed'}, status=405)