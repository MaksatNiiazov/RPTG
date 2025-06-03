from django import forms
from .models import Location


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['name', 'description', 'image', 'is_opened']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        labels = {
            'name': 'Название локации',
            'description': 'Описание',
            'image': 'Карта локации',
            'is_opened': 'Открыта',
        }
