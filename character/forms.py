from django import forms
from .models import Character


class CharacterForm(forms.ModelForm):
    class Meta:
        model = Character
        fields = [
            "name", "race", "gender", "background", "notes",
            "str_stat", "dex_stat", "con_stat", "int_stat",
            "wis_stat", "cha_stat", "acc_stat", "lck_stat",
        ]
        widgets = {
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


class CharacterKnowledgeForm(forms.ModelForm):
    knows = forms.ModelMultipleChoiceField(
        queryset=Character.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Знает персонажей"
    )

    class Meta:
        model = Character
        fields = ["knows"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ограничиваем список всех других персонажей мира
        if self.instance and self.instance.pk:
            world_chars = Character.objects.filter(world=self.instance.world).exclude(pk=self.instance.pk)
            self.fields["knows"].queryset = world_chars
            # Начальные значения — текущие связи
            self.fields["knows"].initial = self.instance.knows.all()
