from django import forms
from .models import Listing

class ListingForm(forms.ModelForm):
    DURATION_CHOICES = [
        (1, '1 сутки'),
        (7, '1 неделя'),
        (14, '2 недели'),
        (30, '1 месяц'),
    ]
    duration = forms.ChoiceField(
        choices=DURATION_CHOICES,
        initial=30,
        label='Срок публикации',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Listing
        fields = ['title', 'description', 'price']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Продам двухкомнатную квартиру'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Подробное описание, характеристики, состояние...'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Например: 1500'}),
        }