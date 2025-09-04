from django import forms
from django.conf import settings 
from .models import Event, Category, Registration, Review
from django.utils import timezone

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'short_description', 'description', 'date', 
                 'location', 'event_type', 'category', 'image', 
                 'price', 'capacity']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'short_description': forms.Textarea(attrs={'rows': 2}),
        }
        labels = {
            'title': 'Название мероприятия',
            'short_description': 'Краткое описание',
            'description': 'Полное описание',
            'date': 'Дата и время',
            'location': 'Место проведения',
            'event_type': 'Тип мероприятия',
            'category': 'Категория',
            'image': 'Изображение',
            'price': 'Цена (₽)',
            'capacity': 'Вместимость',
        }

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date < timezone.now():
            raise forms.ValidationError("Дата мероприятия не может быть в прошлом!")
        return date

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