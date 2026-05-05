import re
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Profile

class UserLoginForm(forms.Form):
    username = forms.CharField(
        label='Имя пользователя',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Логин'})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Пароль'})
    )

class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        label='Email',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    phone = forms.CharField(
        required=True,
        label='Телефон',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+7 (___) ___-__-__',
            'data-inputmask': "'mask': '+7 (999) 999-99-99'",
            'id': 'id_phone'
        })
    )
    city = forms.CharField(
        max_length=100,
        required=False,
        label='Город',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Город'})
    )
    profile_type = forms.ChoiceField(
        choices=Profile.USER_TYPE_CHOICES,
        label='Тип аккаунта',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    display_name = forms.CharField(
        max_length=100,
        required=False,
        label='Отображаемое имя',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Как вас показывать? (необязательно)'})
    )

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

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) != 11 or digits[0] != '7':
            raise forms.ValidationError('Введите номер в формате +7 (999) 999-99-99')
        return digits

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            profile = user.profile
            profile.phone = self.cleaned_data['phone']
            profile.city = self.cleaned_data.get('city', '')
            profile.profile_type = self.cleaned_data['profile_type']
            display_name = self.cleaned_data.get('display_name', '').strip()
            if not display_name:
                display_name = user.username
            profile.display_name = display_name
            profile.save()
        return user
    
    def clean_display_name(self):
        name = self.cleaned_data.get('display_name', '').strip()
        if not name:
            return name
        # Запрещаем строки, похожие на email или телефон
        if re.search(r'@', name) or re.search(r'^\s*\+?\d[\d\s\-\(\)]{5,}\s*$', name):
            raise forms.ValidationError('Отображаемое имя не может быть адресом электронной почты или номером телефона.')
        return name


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['city', 'profile_type', 'display_name', 'avatar']
        widgets = {
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'display_name': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_type': forms.Select(attrs={'class': 'form-select'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone', '')
        digits = ''.join(filter(str.isdigit, phone))
        if len(digits) != 11 or digits[0] != '7':
            raise forms.ValidationError('Номер должен быть в формате +7 (999) 999-99-99')
        return digits

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            user = profile.user
            user.email = self.cleaned_data['email']
            user.save()
            profile.phone = self.cleaned_data['phone']
            profile.save()
        return profile

    def clean_display_name(self):
        name = self.cleaned_data.get('display_name', '').strip()
        if not name:
            return name
        if re.search(r'@', name) or re.search(r'^\s*\+?\d[\d\s\-\(\)]{5,}\s*$', name):
            raise forms.ValidationError('Отображаемое имя не может быть адресом электронной почты или номером телефона.')
        return name