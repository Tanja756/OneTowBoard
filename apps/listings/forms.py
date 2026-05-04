from django import forms
from .models import Listing

class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = ['title', 'description', 'price']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например: Продам двухкомнатную квартиру'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Подробное описание, характеристики, состояние...'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Например: 1500'}),
        }