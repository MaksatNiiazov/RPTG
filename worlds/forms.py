from django import forms

from character.models import Character
from items.models import Item, Type, Rarity
from .models import World, WorldInvitation


class WorldForm(forms.ModelForm):
    class Meta:
        model = World
        fields = ["name", "setting", "history"]
        widgets = {
            "setting": forms.TextInput(attrs={"placeholder": "Краткое описание мира"}),
            "history": forms.Textarea(attrs={"rows": 4, "placeholder": "Подробная предыстория"}),
        }


class GrantAbilityPointsForm(forms.Form):
    points = forms.IntegerField(
        label="Количество очков",
        min_value=1,
        help_text="Сколько очков выдать персонажу"
    )


class GrantItemForm(forms.Form):
    item = forms.ChoiceField(
        label="Предмет",
        widget=forms.Select(attrs={
            "id": "id_item_select",
            "class": "form-control"
        })
    )
    quantity = forms.IntegerField(
        label="Количество",
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "style": "width: 5em;"
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        grouped = []
        # Берём все типы, для каждого строим optgroup
        for t in Type.objects.order_by("name").prefetch_related("items"):
            # Сортировка предметов: сначала по убыванию rarity.lvl, потом по name
            items = t.items.select_related("rarity") \
                .order_by("-rarity__lvl", "name")
            if not items.exists():
                continue
            choices = []
            for itm in items:
                label = f"{itm.name} [{itm.rarity.name}]"
                choices.append((str(itm.pk), label))
            grouped.append((t.name, choices))
        self.fields["item"].choices = grouped


# worlds/forms.py

class QuickChestForm(forms.Form):
    character = forms.ModelChoiceField(
        queryset=Character.objects.filter(is_npc=False),
        label="Персонаж"
    )
    chest_rarity = forms.ModelChoiceField(
        queryset=Rarity.objects.all(),
        label="Редкость сундука"
    )
    count = forms.IntegerField(min_value=1, initial=3, label="Кол-во предметов")
    rare_count = forms.IntegerField(min_value=0, initial=0, required=False, label="Кол-во редких")
    rare_rarity = forms.ModelChoiceField(
        queryset=Rarity.objects.filter(legendary=False),
        required=False,
        label="Редкая редкость"
    )
    type_bias = forms.ModelChoiceField(
        queryset=Type.objects.all(),
        required=False,
        label="Слотовой приоритет (тип)"
    )
    type_bias_count = forms.IntegerField(
        min_value=0, initial=0, required=False, label="Кол-во предметов приор. типа"
    )

    def __init__(self, world, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # показываем только персонажей этого мира
        self.fields['character'].queryset = world.characters.all()
        # rare_rarity имеет смысл только если rare_count > 0
        self.fields['rare_rarity'].widget.attrs['disabled'] = True
        self.fields['rare_count'].widget.attrs['class'] = 'js-rare-count'
        self.fields['rare_rarity'].widget.attrs['class'] = 'js-rare-rarity'



class WorldInvitationForm(forms.ModelForm):
    class Meta:
        model = WorldInvitation
        fields = ("email",)
        widgets = {
            "email": forms.EmailInput(attrs={"placeholder": "email@example.com"}),
        }