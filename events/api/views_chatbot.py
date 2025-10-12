from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
import uuid
import json

# from ..chatbot.core import chatbot

@api_view(['POST'])
@permission_classes([])
@csrf_exempt
def chat_message(request):
    """Обработка сообщений чатбота"""
    try:
        data = request.data
        message = data.get('message', '').strip()
        session_id = data.get('session_id')
        
        if not message:
            return Response(
                {'error': 'Message is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Создаем session_id если не предоставлен
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # Обрабатываем сообщение
        user = request.user if request.user.is_authenticated else None
        result = chatbot.process_message(message, user, session_id)
        
        response_data = {
            'session_id': session_id,
            'response': result['response'],
            'intent': result['intent'],
            'suggestions': result['suggestions'],
            'timestamp': result.get('timestamp')
        }
        
        # Добавляем данные мероприятий если есть
        if result.get('action_result') and 'events' in result['action_result']:
            response_data['events'] = result['action_result']['events']
        
        return Response(response_data)
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

@api_view(['GET'])
def chat_history(request, session_id):
    """Получение истории чата"""
    from ..models import ChatSession, ChatMessage
    
    try:
        session = ChatSession.objects.get(session_id=session_id, user=request.user)
        messages = ChatMessage.objects.filter(session=session).order_by('timestamp')
        
        history = [
            {
                'type': msg.message_type,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'metadata': msg.metadata
            }
            for msg in messages
        ]
        
        return Response({'history': history})
        
    except ChatSession.DoesNotExist:
        return Response({'history': []})

@api_view(['POST'])
def clear_chat_history(request, session_id):
    """Очистка истории чата"""
    from ..models import ChatSession
    
    try:
        session = ChatSession.objects.get(session_id=session_id, user=request.user)
        session.messages.all().delete()
        
        return Response({'status': 'success'})
        
    except ChatSession.DoesNotExist:
        return Response(
            {'error': 'Session not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )