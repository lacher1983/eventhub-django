from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class ChatIntent(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    patterns = models.JSONField(default=list, help_text="Список паттернов для интента")
    responses = models.JSONField(default=list, help_text="Список ответов бота")
    action = models.CharField(max_length=100, blank=True, help_text="Действие для выполнения")
    required_entities = models.JSONField(default=list, help_text="Обязательные сущности")
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Интент чатбота"
        verbose_name_plural = "Интенты чатбота"


class ChatEntity(models.Model):
    name = models.CharField(max_length=100)
    intent = models.ForeignKey(ChatIntent, on_delete=models.CASCADE, related_name='entities')
    patterns = models.JSONField(default=list, help_text="Паттерны для извлечения сущности")
    entity_type = models.CharField(max_length=50, choices=[
        ('category', 'Категория'),
        ('date', 'Дата'),
        ('price', 'Цена'),
        ('location', 'Местоположение'),
        ('event_type', 'Тип мероприятия'),
    ])
    
    def __str__(self):
        return f"{self.name} ({self.entity_type})"

    class Meta:
        verbose_name = "Сущность чатбота"
        verbose_name_plural = "Сущности чатбота"


class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Сессия {self.session_id}"

    class Meta:
        verbose_name = "Сессия чата"
        verbose_name_plural = "Сессии чатов"


class ChatMessage(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    message_type = models.CharField(max_length=20, choices=[
        ('user', 'Пользователь'),
        ('assistant', 'Ассистент')
    ])
    content = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.message_type}: {self.content[:50]}..."

    class Meta:
        verbose_name = "Сообщение чата"
        verbose_name_plural = "Сообщения чатов"
        ordering = ['created_at']


