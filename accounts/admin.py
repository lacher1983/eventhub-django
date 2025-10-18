from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User
from config.admin_customization import admin_site


@admin.register(User, site=admin_site)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'date_joined')
    list_filter = ('role', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    # Добавляем add_fieldsets для формы создания пользователя
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Дополнительная информация', {
            'fields': ('role', 'phone', 'avatar')
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Безопасная проверка наличия поля
        if 'role' in form.base_fields:
            form.base_fields['role'].initial = 'user'
        return form