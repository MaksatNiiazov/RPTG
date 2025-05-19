from django import forms
from .models import Rarity, Type


class LootConfigForm(forms.Form):
    LUCK_CHOICES = [(i, str(i)) for i in range(1, 11)]

    luck = forms.ChoiceField(
        choices=LUCK_CHOICES,
        label="Удача",
        widget=forms.RadioSelect,
        initial=5
    )
    chest_rarity = forms.ModelChoiceField(
        label="Редкость сундука",
        queryset=Rarity.objects.order_by("name")
    )
    count = forms.IntegerField(
        label="Всего предметов", min_value=1, initial=3
    )

    rare_count = forms.IntegerField(
        label="Сколько специальных (точно редких) предметов",
        min_value=0, required=False, initial=0
    )
    rare_rarity = forms.ModelChoiceField(
        label="Редкость этих специальных",
        queryset=Rarity.objects.order_by("name"),
        required=False
    )

    type_bias = forms.ModelChoiceField(
        label="Тип, который должен преобладать",
        queryset=Type.objects.order_by("name"),
        required=False
    )
    type_bias_count = forms.IntegerField(
        label="Сколько предметов этого типа",
        min_value=0, required=False, initial=0
    )
