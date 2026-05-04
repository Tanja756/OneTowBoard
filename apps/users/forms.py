from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email', widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Введите email'}))
    phone = forms.CharField(max_length=20, required=False, label='Телефон', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Номер телефона'}))
    city = forms.CharField(max_length=100, required=False, label='Город', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ваш город'}))
    profile_type = forms.ChoiceField(choices=Profile.USER_TYPE_CHOICES, label='Тип аккаунта', widget=forms.Select(attrs={'class': 'form-select'}))
    display_name = forms.CharField(max_length=100, required=False, label='Отображаемое имя', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Как вас показывать? (необязательно)'}))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Придумайте логин'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Пароль'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Подтверждение пароля'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            user.profile.phone = self.cleaned_data.get('phone', '')
            user.profile.city = self.cleaned_data.get('city', '')
            user.profile.profile_type = self.cleaned_data['profile_type']
            display_name = self.cleaned_data.get('display_name', '').strip()
            if not display_name:
                display_name = user.username
            user.profile.display_name = display_name
            user.profile.save()
        return user

class UserLoginForm(forms.Form):
    username = forms.CharField(label='Имя пользователя', widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Логин'}))
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль'}))
