from django import forms
from .models import Character


class CharacterForm(forms.ModelForm):
    class Meta:
        model = Character
        fields = [
            "image",
            "name", "race", "gender", "background", "notes",
            "str_stat", "dex_stat", "con_stat", "int_stat",
            "wis_stat", "cha_stat", "acc_stat", "lck_stat",
            "is_npc", "visible_to_players"
        ]
        widgets = {
            "image": forms.ClearableFileInput(),
            "background": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
            "gender": forms.Select(),
        }
        labels = {
            "str_stat": "Сила",
            "dex_stat": "Ловкость",
            "con_stat": "Телосложение",
            "int_stat": "Интеллект",
            "wis_stat": "Мудрость",
            "cha_stat": "Харизма",
            "acc_stat": "Меткость",
            "lck_stat": "Удача",
        }
        help_texts = {
            "lck_stat": "Влияет на выпадение редких предметов",
        }


class CharacterUpdateForm(forms.ModelForm):
    class Meta:
        model = Character
        fields = [
            "image", "name", "race", "gender", "background", "notes",
        ]
        widgets = {
            "image": forms.ClearableFileInput(),
            "background": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
            "gender": forms.Select(),
        }


class LevelUpForm(forms.Form):
    STAT_CHOICES = [
        ('str_stat', 'Сила'),
        ('dex_stat', 'Ловкость'),
        ('con_stat', 'Телосложение'),
        ('int_stat', 'Интеллект'),
        ('wis_stat', 'Мудрость'),
        ('cha_stat', 'Харизма'),
        ('acc_stat', 'Меткость'),
        ('lck_stat', 'Удача'),
    ]
    stat = forms.ChoiceField(choices=STAT_CHOICES, label="Характеристика")
    points = forms.IntegerField(min_value=1, label="Очков для прокачки")
