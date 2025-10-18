from django.contrib import admin
from django.conf import settings
import os

class CustomAdminSite(admin.AdminSite):
    site_header = "EventHub DarkSide Administration"
    site_title = "EventHub Admin Portal"
    index_title = "Добро пожаловать в DarkSide админку"
    
    def each_context(self, request):
        context = super().each_context(request)
        context['site_header'] = self.site_header
        context['site_title'] = self.site_title
        context['index_title'] = self.index_title
        return context

# Заменяем стандартную админку
admin_site = CustomAdminSite(name='custom_admin')