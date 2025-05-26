from django import forms

from items.models import Item, Type
from .models import World


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