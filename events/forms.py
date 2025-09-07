from django import forms
from django.conf import settings 
from .models import Event, Category, Registration, Review
from django.utils import timezone

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'short_description', 'description', 'date', 
                 'location', 'event_type', 'category', 'image', 
                 'price', 'capacity', 'is_free', 'tickets_available']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'short_description': forms.Textarea(attrs={'rows': 2}),
            'tickets_available': forms.NumberInput(attrs={'min': 1})
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