from django import forms
from .models import User
from .validators import PwnedPasswordValidator

class CustomUserCreationForm(forms.ModelForm):
    password1 = forms.CharField(widget=forms.PasswordInput, validators=[PwnedPasswordValidator()])
    password2 = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'email')

    def clean(self):
        cleaned = super().clean()
        if cleaned['password1'] != cleaned['password2']:
            raise forms.ValidationError("Пароли не совпадают")
        return cleaned