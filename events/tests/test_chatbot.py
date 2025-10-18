import pytest
from unittest.mock import Mock, patch

from events.chatbot.core import ChatbotEngine
from events.chatbot.intents import EventSearchIntent, RegistrationIntent


class ChatbotEngineTest:
    def setup_method(self):
        self.chatbot = ChatbotEngine()
        self.mock_user = Mock()
        self.mock_user.id = 1
        self.mock_user.username = 'testuser'

    def test_welcome_message(self):
        response = self.chatbot.process_message('привет', self.mock_user)
        assert any(word in response.lower() for word in ['привет', 'здравствуйте', 'добро пожаловать'])

    def test_event_search_intent(self):
        response = self.chatbot.process_message(
            'найди концерты в москве', 
            self.mock_user
        )
        assert any(word in response.lower() for word in ['мероприятия', 'концерт', 'найден'])

    def test_registration_intent(self):
        response = self.chatbot.process_message(
            'хочу зарегистрироваться на мероприятие',
            self.mock_user
        )
        assert any(word in response.lower() for word in ['регистрация', 'зарегистрироваться', 'мероприятие'])

    def test_help_intent(self):
        response = self.chatbot.process_message('помощь', self.mock_user)
        assert any(word in response.lower() for word in ['помощь', 'команды', 'поддержка'])

    @patch('events.chatbot.intents.EventSearchIntent.execute')
    def test_event_search_with_mock(self, mock_execute):
        mock_execute.return_value = "Найдено 5 мероприятий в Москве"
        
        response = self.chatbot.process_message(
            'мероприятия в москве',
            self.mock_user
        )
        assert response == "Найдено 5 мероприятий в Москве"

    def test_unknown_intent(self):
        response = self.chatbot.process_message(
            'случайный текст который бот не понимает',
            self.mock_user
        )
        assert any(word in response.lower() for word in ['понять', 'помощь', 'поддержка'])


class EventSearchIntentTest:
    def test_event_search_parsing(self):
        intent = EventSearchIntent()
        
        # Тестовое извлечение локации
        location = intent._extract_location('концерты в москве на завтра')
        assert location == 'москве'
        
        # Тестовое извлечение даты
        date_info = intent._extract_date('мероприятия на следующей неделе')
        assert date_info is not None

    @patch('events.models.Event.objects.filter')
    def test_event_search_execution(self, mock_filter):
        mock_filter.return_value = [
            Mock(title='Test Concert', location='Moscow'),
            Mock(title='Test Exhibition', location='Moscow')
        ]
        
        intent = EventSearchIntent()
        result = intent.execute('концерты в москве')
        
        assert 'Test Concert' in result
        assert '2 мероприятий' in result


class RegistrationIntentTest:
    @patch('events.models.Event.objects.get')
    @patch('events.models.Registration.objects.create')
    def test_registration_execution(self, mock_create, mock_get):
        mock_event = Mock()
        mock_event.title = 'Test Event'
        mock_get.return_value = mock_event
        
        mock_registration = Mock()
        mock_create.return_value = mock_registration
        
        intent = RegistrationIntent()
        result = intent.execute('зарегистрироваться на test event', Mock())
        
        assert 'зарегистрирован' in result.lower()
        assert 'test event' in result.lower()