from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.conf import settings 
from .models import Event, Tag, Category, Registration, Review
from django.utils import timezone
from django.contrib.auth import get_user_model

# Используем кастомную модель пользователя
User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your@email.com'})
    )
    # first_name = forms.CharField(max_length=30, required=True, label='Имя')
    # last_name = forms.CharField(max_length=30, required=True, label='Фамилия')
    
    class Meta:
        model = User  # Используем кастомную модель
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Имя пользователя'
            }),
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
                'placeholder': 'Введите название мероприятия'
            }),
            'short_description': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Краткое описание (до 300 символов)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Полное описание мероприятия'
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
                'placeholder': 'Место проведения или ссылка'
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Что участникам нужно взять с собой...'
            }),
            'capacity': forms.NumberInput(attrs={'class': 'form-control'}),
            'tickets_available': forms.NumberInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Динамическое обновление списка типов в зависимости от категории
        if 'category' in self.data:
            try:
                category = self.data.get('category')
                # Можно добавить фильтрацию типов по категориям
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
            raise forms.ValidationError("Дата мероприятия не может быть в прошлом!")
        return date
    
class EventFilterForm(forms.Form):
    category = forms.ChoiceField(
        choices=[('', 'Все категории')] + list(Event.EVENT_CATEGORIES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    event_type = forms.ChoiceField(
        choices=[('', 'Все типы')] + list(Event.EVENT_TYPES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    event_format = forms.ChoiceField(
        choices=[('', 'Любой формат')] + list(Event.EVENT_FORMATS),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    difficulty_level = forms.ChoiceField(
        choices=[('', 'Любой уровень')] + list(Event.DIFFICULTY_LEVELS),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    price_type = forms.ChoiceField(
        choices=[
            ('', 'Любая цена'),
            ('free', 'Бесплатные'),
            ('paid', 'Платные')
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
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
                'placeholder': 'Поделитесь вашими впечатлениями о мероприятии...'
            })
        }
        labels = {
            'rating': 'Ваша оценка',
            'comment': 'Комментарий'
        }

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = []  # формочка только для создания регистрации


from django import forms
from .models import CartItem, Order

class AddToCartForm(forms.ModelForm):
    quantity = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'style': 'width: 80px'})
    )

    class Meta:
        model = CartItem
        fields = ['quantity']

class CheckoutForm(forms.ModelForm):
    payment_method = forms.ChoiceField(
        choices=Order.PAYMENT_METHODS,
        widget=forms.RadioSelect,
        initial='card'
    )

    class Meta:
        model = Order
        fields = ['payment_method']

class PaymentForm(forms.Form):
    card_number = forms.CharField(
        max_length=19,
        widget=forms.TextInput(attrs={'placeholder': '1234 5678 9012 3456'})
    )
    expiry_date = forms.CharField(
        max_length=5,
        widget=forms.TextInput(attrs={'placeholder': 'MM/YY'})
    )
    cvv = forms.CharField(
        max_length=3,
        widget=forms.TextInput(attrs={'placeholder': '123'})
    )
    cardholder_name = forms.CharField(max_length=100)


