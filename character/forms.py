from django import forms
from .models import Character, CharacterClass, Talent


class CharacterForm(forms.ModelForm):
    class Meta:
        model = Character
        fields = [
            "image",
            "name", "race", "age", "gender", "background", "notes",
            "str_stat", "dex_stat", "con_stat", "int_stat",
            "wis_stat", "cha_stat", "acc_stat", "lck_stat",
            "is_npc", "visible_to_players", 'character_class',
            "character_talent",
        ]
        widgets = {
            "image": forms.ClearableFileInput(),
            "background": forms.Textarea(attrs={"rows": 3}),
            "notes": forms.Textarea(attrs={"rows": 3}),
            "gender": forms.Select(),
            "character_class": forms.Select(),
            "character_talent": forms.Select(),
            "age": forms.NumberInput(attrs={"min": 1, "max": 1000}),
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
            "character_class": "Класс",
            "character_talent": "Талант",
        }
        help_texts = {
            "lck_stat": "Влияет на выпадение редких предметов",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Фильтрация классов - только одобренные
        self.fields['character_class'].queryset = CharacterClass.objects.filter(approve=True)

        # Фильтрация талантов - только одобренные
        self.fields['character_talent'].queryset = Talent.objects.filter(approve=True)

        # Добавляем пустой выбор для таланта (так как он не обязательный)
        self.fields['character_class'].empty_label = "Без класса"

        self.fields['character_talent'].empty_label = "Без таланта"

        # Можно добавить классы CSS для стилизации полей
        self.fields['character_class'].widget.attrs.update({'class': 'form-control'})
        self.fields['character_talent'].widget.attrs.update({'class': 'form-control'})


class CharacterUpdateForm(forms.ModelForm):
    class Meta:
        model = Character
        fields = [
            "image", "name", "age", "gender", "background", "notes",
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
