from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, FormView

from .forms import  LootConfigForm
from .loot import generate_loot_items
from .models import Rarity, Type, Item


class RarityListView(ListView):
    model = Rarity
    template_name = "items/rarity_list.html"
    context_object_name = "rarities"


class TypeListView(ListView):
    model = Type
    template_name = "items/type_list.html"
    context_object_name = "types"

    def get_queryset(self):
        return Type.objects.select_related("rarity").order_by("rarity__name", "name")


class ItemListView(ListView):
    model = Item
    template_name = "items/item_list.html"
    context_object_name = "items"
    paginate_by = 50

    def get_queryset(self):
        qs = Item.objects.select_related("type", "rarity")
        type_slug = self.request.GET.get("type")
        rarity_slug = self.request.GET.get("rarity")
        if type_slug:
            qs = qs.filter(type__slug=type_slug)
        if rarity_slug:
            qs = qs.filter(rarity__slug=rarity_slug)
        return qs.order_by('type__name', 'name')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["types"] = Type.objects.order_by("rarity__lvl")
        ctx["rarities"] = Rarity.objects.order_by("lvl")
        return ctx


class LootConfigView(View):
    template_name = "items/loot_config.html"

    def get(self, request):
        form = LootConfigForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = LootConfigForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        cd = form.cleaned_data
        # сохраняем только числовые и id-поля
        request.session["loot_params"] = {
            "luck": cd["luck"],
            "chest_rarity_id": cd["chest_rarity"].pk,
            "count": cd["count"],
            "rare_count": cd.get("rare_count") or 0,
            "rare_rarity_id": (cd.get("rare_rarity").pk
                               if cd.get("rare_rarity") else None),
            "type_bias_id": (cd.get("type_bias").pk
                             if cd.get("type_bias") else None),
            "type_bias_count": cd.get("type_bias_count") or 0,
        }
        return redirect("items:loot_result")

class LootResultView(View):
    template_name = "items/loot_result.html"

    def get(self, request):
        params = request.session.get("loot_params")
        if not params:
            return redirect("items:loot_config")

        # получаем объекты по сохранённым id
        chest_rarity = get_object_or_404(Rarity, pk=params["chest_rarity_id"])
        rare_rarity  = (get_object_or_404(Rarity, pk=params["rare_rarity_id"])
                        if params["rare_rarity_id"] else None)
        type_bias    = (get_object_or_404(Type, pk=params["type_bias_id"])
                        if params["type_bias_id"] else None)

        items = generate_loot_items(
            luck=params["luck"],
            chest_rarity=chest_rarity.lvl,
            count=params["count"],
            rare_count=params["rare_count"],
            rare_rarity=rare_rarity,
            type_bias=type_bias,
            type_bias_count=params["type_bias_count"]
        )
        return render(request, self.template_name, {
            "items": items,
            "params": params,
            "chest_rarity": chest_rarity,
            "rare_rarity": rare_rarity,
            "type_bias": type_bias,
        })

    def post(self, request):
        # кнопка «Сбросить»
        request.session.pop("loot_params", None)
        return redirect("items:loot_config")
