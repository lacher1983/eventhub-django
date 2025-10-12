from django.urls import path
from . import views

app_name = 'chatbot'

urlpatterns = [
    path('', views.chat_interface, name='chat_interface'),
    path('api/chat/', views.chat_api, name='chat_api'),
    path('api/history/<str:session_id>/', views.chat_history, name='chat_history'),
]