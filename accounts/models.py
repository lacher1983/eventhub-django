from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('user', _('Обычный пользователь')),
        ('organizer', _('Организатор')),
        ('admin', _('Администратор')),
    ]
    
    role = models.CharField(_('роль'), max_length=10, choices=ROLE_CHOICES, default='user')
    phone = models.CharField(_('телефон'), max_length=15, blank=True)
    avatar = models.ImageField(_('аватар'), upload_to='avatars/', blank=True, null=True)

    def is_admin(self):
        return self.role == 'admin' or self.is_superuser
            
    def is_moderator(self):
        return self.role == 'moderator' or self.is_admin()