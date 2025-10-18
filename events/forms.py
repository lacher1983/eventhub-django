from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.conf import settings
from .models import Event, Tag, Category, Registration, Review, PromoVideo, ProjectPromoVideo
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import os
# from .models import BuddyRequest


# Используем кастомную модель пользователя
User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(
        required=True, 
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('your@email.com')
        })
    )
    # first_name = forms.CharField(max_length=30, required=True, label='Имя')
    # last_name = forms.CharField(max_length=30, required=True, label='Фамилия')
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Имя пользователя')
            }),
        }
        labels = {
            'username': _('Имя пользователя'),
            'password1': _('Пароль'),
            'password2': _('Подтверждение пароля'),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Упрощаем подсказки для пароля
        self.fields['password1'].help_text = None
        self.fields['password2'].help_text = None

        # Добавляем классы ко всем полям
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs['class'] = 'form-control'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        # user.first_name = self.cleaned_data['first_name']
        # user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user

class EventForm(forms.ModelForm):
    def clean_date(self):
        date = self.cleaned_data['date']
        if date < timezone.now():
            raise ValidationError("Дата не может быть в прошлом")
        return date

    class Meta:
        model = Event
        fields = [
            'title', 'short_description', 'description', 'image',
            'category', 'event_type', 'event_format', 'difficulty_level',
            'date', 'location', 'requirements', 'tags',
            'organizer', 'capacity', 'tickets_available',
            'price', 'is_free', 'is_active'
        ]
        
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Введите название мероприятия')
            }),
            'short_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Краткое описание (до 300 символов)')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Полное описание мероприятия')
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'event_type': forms.Select(attrs={'class': 'form-control'}),
            'event_format': forms.Select(attrs={'class': 'form-control'}),
            'difficulty_level': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Место проведения или ссылка')
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('Что участникам нужно взять с собой...')
            }),
            'tags': forms.SelectMultiple(attrs={
                'class': 'form-control',
                'data-placeholder': _('Выберите теги')
            }),
            'capacity': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1'
            }),
            'tickets_available': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'is_free': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'onchange': 'togglePriceField()'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        
        labels = {
            'title': _('Название мероприятия'),
            'short_description': _('Краткое описание'),
            'description': _('Полное описание'),
            'image': _('Изображение'),
            'category': _('Категория'),
            'event_type': _('Тип мероприятия'),
            'event_format': _('Формат'),
            'difficulty_level': _('Уровень сложности'),
            'date': _('Дата и время'),
            'location': _('Место проведения'),
            'requirements': _('Требования к участникам'),
            'tags': _('Теги'),
            'organizer': _('Организатор'),
            'capacity': _('Вместимость'),
            'tickets_available': _('Доступно билетов'),
            'price': _('Цена (₽)'),
            'is_free': _('Бесплатное мероприятие'),
            'is_active': _('Активно'),
        }
        
        help_texts = {
            'short_description': _('Краткое описание, которое будет отображаться в списке мероприятий'),
            'tickets_available': _('Количество билетов, доступных для покупки'),
            'is_free': _('Если отмечено, цена будет установлена в 0'),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Скрываем поле организатора - оно будет установлено автоматически
        if 'organizer' in self.fields:
            self.fields['organizer'].widget = forms.HiddenInput()
        
        # Динамическое обновление списка типов в зависимости от категории
        if 'category' in self.data:
            try:
                category = self.data.get('category')
                self.fields['event_type'].choices = self.get_filtered_types(category)
            except (ValueError, TypeError):
                pass
    
    def get_filtered_types(self, category):
        """Фильтрует типы мероприятий по категории"""
        TYPE_GROUPS = {
            'education': ['webinar', 'workshop', 'course', 'lecture', 'training'],
            'business': ['conference', 'business_meeting', 'networking', 'exhibition'],
            'entertainment': ['concert', 'party', 'festival', 'show'],
            'culture': ['exhibition_culture', 'tour', 'master_class'],
            'sport': ['competition', 'sport_event', 'tournament'],
            'social': ['charity', 'volunteering', 'community'],
        }
        
        if category in TYPE_GROUPS:
            return [(key, value) for key, value in Event.EVENT_TYPES 
                    if key in TYPE_GROUPS[category]]
        return Event.EVENT_TYPES

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date < timezone.now():
            raise forms.ValidationError(_("Дата мероприятия не может быть в прошлом!"))
        return date

    def clean(self):
        cleaned_data = super().clean()
        is_free = cleaned_data.get('is_free')
        price = cleaned_data.get('price')
        
        # Если мероприятие бесплатное, устанавливаем цену в 0
        if is_free and price:
            cleaned_data['price'] = 0
        
        # Проверяем, что доступно не больше билетов, чем вместимость
        capacity = cleaned_data.get('capacity')
        tickets_available = cleaned_data.get('tickets_available')
        
        if capacity and tickets_available and tickets_available > capacity:
            raise forms.ValidationError({
                'tickets_available': _('Доступное количество билетов не может превышать вместимость')
            })
        
        return cleaned_data
    
class EventFilterForm(forms.Form):
    category = forms.ChoiceField(
        choices=[('', _('Все категории'))] + list(Event.EVENT_CATEGORIES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    event_type = forms.ChoiceField(
        choices=[('', _('Все типы'))] + list(Event.EVENT_TYPES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    event_format = forms.ChoiceField(
        choices=[('', _('Любой формат'))] + list(Event.EVENT_FORMATS),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    difficulty_level = forms.ChoiceField(
        choices=[('', _('Любой уровень'))] + list(Event.DIFFICULTY_LEVELS),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    price_type = forms.ChoiceField(
        choices=[
            ('', _('Любая цена')),
            ('free', _('Бесплатные')),
            ('paid', _('Платные'))
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Поиск мероприятий...')
        })
    )

class ReviewForm(forms.ModelForm):
    """Форма для добавления/редактирования отзывов"""
    class Meta:
        model = Review
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.Select(attrs={
                'class': 'form-select',
                'id': 'rating-select'
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Поделитесь вашими впечатлениями о мероприятии...')
            })
        }
        labels = {
            'rating': _('Ваша оценка'),
            'comment': _('Комментарий')
        }
        help_texts = {
            'comment': _('Максимум 1000 символов')
        }

    def clean_comment(self):
        comment = self.cleaned_data.get('comment', '')
        if len(comment) > 1000:
            raise forms.ValidationError(_('Комментарий не может превышать 1000 символов'))
        return comment

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = ['notes']  # Добавляем поле для заметок
        
        widgets = {
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('Дополнительная информация (необязательно)')
            })
        }
        labels = {
            'notes': _('Дополнительные заметки')
        }

from django import forms
from .models import CartItem, Order

class AddToCartForm(forms.ModelForm):
    quantity = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'style': 'width: 80px',
            'min': '1'
        })
    )

    class Meta:
        model = CartItem
        fields = ['quantity']
        labels = {
            'quantity': _('Количество')
        }

    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity < 1:
            raise forms.ValidationError(_('Количество не может быть меньше 1'))
        return quantity

class CheckoutForm(forms.ModelForm):
    payment_method = forms.ChoiceField(
        choices=Order.PAYMENT_METHODS,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='card',
        label=_('Способ оплаты')
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('your@email.com')
        }),
        label=_('Email для чека')
    )
    
    agree_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Я согласен с условиями покупки')
    )

    class Meta:
        model = Order
        fields = ['payment_method', 'email', 'agree_terms']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Устанавливаем начальное значение email из пользователя
        if 'initial' in kwargs and 'user' in kwargs['initial']:
            user = kwargs['initial']['user']
            if user.is_authenticated:
                self.fields['email'].initial = user.email

class PaymentForm(forms.Form):
    card_number = forms.CharField(
        max_length=19,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('1234 5678 9012 3456'),
            'data-mask': '0000 0000 0000 0000'
        }),
        label=_('Номер карты')
    )
    
    expiry_date = forms.CharField(
        max_length=5,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('MM/ГГ'),
            'data-mask': '00/00'
        }),
        label=_('Срок действия')
    )
    
    cvv = forms.CharField(
        max_length=3,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('123'),
            'data-mask': '000',
            'maxlength': '3'
        }),
        label=_('CVV код')
    )
    
    cardholder_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('IVAN IVANOV')
        }),
        label=_('Имя владельца карты')
    )
    
    save_card = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Сохранить карту для будущих платежей')
    )

    def clean_card_number(self):
        card_number = self.cleaned_data.get('card_number', '').replace(' ', '')
        if not card_number.isdigit() or len(card_number) not in [15, 16]:
            raise forms.ValidationError(_('Введите корректный номер карты'))
        return card_number

    def clean_expiry_date(self):
        expiry_date = self.cleaned_data.get('expiry_date', '')
        try:
            month, year = expiry_date.split('/')
            month = int(month)
            year = int(year)
            
            if month < 1 or month > 12:
                raise forms.ValidationError(_('Неверный месяц'))
                
            current_year = timezone.now().year % 100
            current_month = timezone.now().month
            
            if year < current_year or (year == current_year and month < current_month):
                raise forms.ValidationError(_('Срок действия карты истек'))
                
        except (ValueError, IndexError):
            raise forms.ValidationError(_('Введите дату в формате ММ/ГГ'))
        
        return expiry_date

    def clean_cvv(self):
        cvv = self.cleaned_data.get('cvv', '')
        if not cvv.isdigit() or len(cvv) not in [3, 4]:
            raise forms.ValidationError(_('Введите корректный CVV код'))
        return cvv
    
class EventSearchForm(forms.Form):
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Поиск по названию, описанию...')
        }),
        label=_('Поиск')
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('С даты')
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('По дату')
    )
    
    price_min = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('От'),
            'min': '0'
        }),
        label=_('Цена от')
    )
    
    price_max = forms.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('До'),
            'min': '0'
        }),
        label=_('Цена до')
    )

    def clean(self):
        cleaned_data = super().clean()
        price_min = cleaned_data.get('price_min')
        price_max = cleaned_data.get('price_max')
        
        if price_min and price_max and price_min > price_max:
            raise forms.ValidationError(_('Минимальная цена не может быть больше максимальной'))
        
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError(_('Дата "с" не может быть больше даты "по"'))
        
        return cleaned_data
    
class ContactOrganizerForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ваше имя')
        }),
        label=_('Имя')
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': _('your@email.com')
        }),
        label=_('Email')
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': _('Ваше сообщение организатору...')
        }),
        label=_('Сообщение')
    )
    
    copy_to_me = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label=_('Отправить копию мне')
    )


class PromoVideoForm(forms.ModelForm):
    """Форма для загрузки промо-видео"""
    
    class Meta:
        model = PromoVideo
        fields = [
            'title', 'description', 'video_source', 'youtube_url', 
            'vimeo_url', 'external_url', 'uploaded_video', 'thumbnail',
            'is_main_promo', 'display_order', 'autoplay'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название промо-ролика'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание видео'
            }),
            'video_source': forms.Select(attrs={
                'class': 'form-control',
                'onchange': 'toggleVideoFields()'
            }),
            'youtube_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.youtube.com/watch?v=...'
            }),
            'vimeo_url': forms.URLInput(attrs={
                'class': 'form-control', 
                'placeholder': 'https://vimeo.com/...'
            }),
            'external_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ссылка на видео'
            }),
            'uploaded_video': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'video/mp4,video/x-m4v,video/*'
            }),
            'is_main_promo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'autoplay': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'is_main_promo': 'Сделать главным промо-роликом',
            'autoplay': 'Автовоспроизведение'
        }
    
    def clean(self):
        cleaned_data = super().clean()
        video_source = cleaned_data.get('video_source')
        
        # Валидация в зависимости от источника видео
        if video_source == 'youtube' and not cleaned_data.get('youtube_url'):
            raise forms.ValidationError("Для YouTube необходимо указать ссылку")
        elif video_source == 'vimeo' and not cleaned_data.get('vimeo_url'):
            raise forms.ValidationError("Для Vimeo необходимо указать ссылку")
        elif video_source == 'upload' and not cleaned_data.get('uploaded_video'):
            raise forms.ValidationError("Необходимо загрузить видео файл")
        elif video_source == 'external' and not cleaned_data.get('external_url'):
            raise forms.ValidationError("Необходимо указать внешнюю ссылку")
        
        return cleaned_data
    
    def clean_uploaded_video(self):
        """Валидация загружаемого видео"""
        video = self.cleaned_data.get('uploaded_video')
        if video:
            # Проверка размера файла (максимум 100MB)
            if video.size > 100 * 1024 * 1024:
                raise forms.ValidationError("Размер видео не должен превышать 100MB")
            
            # Проверка расширения
            ext = os.path.splitext(video.name)[1].lower()
            if ext not in ['.mp4', '.mov', '.avi', '.webm']:
                raise forms.ValidationError("Поддерживаются только MP4, MOV, AVI, WebM форматы")
        
        return video
    
class ProjectPromoVideoForm(forms.ModelForm):
    """Форма для промороликов проекта"""
    
    class Meta:
        model = ProjectPromoVideo
        fields = [
            'title', 'description', 'video_type', 'youtube_url', 'video_file', 'thumbnail',
            'is_active', 'show_on_homepage', 'show_on_landing', 'autoplay', 'display_order'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название проморолика проекта'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Описание проморолика'
            }),
            'video_type': forms.Select(attrs={'class': 'form-control'}),
            'youtube_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.youtube.com/watch?v=...'
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_on_homepage': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_on_landing': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'autoplay': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'is_active': 'Активный',
            'show_on_homepage': 'Показывать на главной',
            'show_on_landing': 'Показывать в лендинге',
            'autoplay': 'Автовоспроизведение'
        }

# class BuddyRequestForm(forms.ModelForm):
#     class Meta:
#         model = BuddyRequest
#         fields = ['message', 'preferred_gender', 'max_buddies']
#         widgets = {
#             'message': forms.Textarea(attrs={
#                 'rows': 4,
#                 'placeholder': 'Опишите, кого вы ищете и ваши предпочтения...'
#             }),
#         }
