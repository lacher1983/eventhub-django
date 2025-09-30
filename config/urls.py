"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from .admin_customization import admin_site
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from events.views import custom_logout
from events.views import CustomLogoutView
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin_site.urls),
    path('', include('events.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('events/', include('events.urls')),
    path('accounts/logout/', CustomLogoutView.as_view(), name='logout'),
    path('accounts/logout/', custom_logout, name='logout'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='events/login.html'), name='login'),
    # Выход с разрешением GET запросов
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='event_list', http_method_names=['get', 'post']), name='logout'),
    # Вход
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    # Перенаправление с корня на мероприятия
    path('', RedirectView.as_view(pattern_name='event_list'), name='home'),
    path('api/', include('events.api.urls')),
    path('favicon.ico', RedirectView.as_view(url=static('favicon.ico'))),
    # Восстановление пароля
    path('accounts/password-reset/', 
         auth_views.PasswordResetView.as_view(
             template_name='events/password_reset.html',
             email_template_name='events/emails/password_reset_email.html',
             subject_template_name='events/emails/password_reset_subject.txt'
         ), 
         name='password_reset'),
    
    path('accounts/password-reset/done/', 
         auth_views.PasswordResetDoneView.as_view(
             template_name='events/password_reset_done.html'
         ), 
         name='password_reset_done'),
    
    path('accounts/password-reset-confirm/<uidb64>/<token>/', 
         auth_views.PasswordResetConfirmView.as_view(
             template_name='events/password_reset_confirm.html'
         ), 
         name='password_reset_confirm'),
    
    path('accounts/password-reset-complete/', 
         auth_views.PasswordResetCompleteView.as_view(
             template_name='events/password_reset_complete.html'
         ), 
         name='password_reset_complete'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)