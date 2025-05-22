from django import forms
from .models import World


class WorldForm(forms.ModelForm):
    class Meta:
        model = World
        fields = ["name", "setting", "history"]
        widgets = {
            "setting": forms.TextInput(attrs={"placeholder": "Краткое описание мира"}),
            "history": forms.Textarea(attrs={"rows": 4, "placeholder": "Подробная предыстория"}),
        }
