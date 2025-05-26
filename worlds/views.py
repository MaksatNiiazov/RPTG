from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView
from django.shortcuts import get_object_or_404, redirect, render

from character.models import Character, InventoryItem, ChestInstance
from items.forms import LootConfigForm
from items.loot import generate_loot_items
from items.models import Item
from .forms import WorldForm, GrantAbilityPointsForm, GrantItemForm, QuickChestForm
from .loot import open_chest_in_world
from .models import World, WorldItemPool


class WorldDetailView(LoginRequiredMixin, DetailView):
    model = World
    template_name = "worlds/world_detail.html"
    context_object_name = "world"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        world = self.object
        user = self.request.user

        # Все игровые персонажи (не-NPC)
        players = world.characters.filter(is_npc=False)
        # NPC, отмеченные как видимые игрокам
        npcs = world.characters.filter(is_npc=True, visible_to_players=True)

        ctx["is_gm"] = (world.creator == user)
        ctx["player_chars"] = players
        ctx["npc_chars"] = npcs
        return ctx


class WorldCreateView(LoginRequiredMixin, CreateView):
    model = World
    form_class = WorldForm
    template_name = "worlds/world_form.html"
    login_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        # Назначаем текущего пользователя гейммастером
        form.instance.creator = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("worlds:detail", kwargs={"pk": self.object.pk})


class GrantAbilityPointsView(LoginRequiredMixin, View):
    def get(self, request, world_pk, char_pk):
        world = get_object_or_404(World, pk=world_pk)
        if world.creator != request.user:
            return redirect("worlds:detail", pk=world_pk)
        char = get_object_or_404(Character, pk=char_pk, world=world)
        form = GrantAbilityPointsForm()
        return render(request, "worlds/grant_points.html", {
            "world": world,
            "char": char,
            "form": form,
        })

    def post(self, request, world_pk, char_pk):
        world = get_object_or_404(World, pk=world_pk)
        if world.creator != request.user:
            return redirect("worlds:detail", pk=world_pk)
        char = get_object_or_404(Character, pk=char_pk, world=world)
        form = GrantAbilityPointsForm(request.POST)
        if form.is_valid():
            pts = form.cleaned_data["points"]
            char.ability_points += pts
            char.save()
            messages.success(request, f"Выдано {pts} очков {char.name}.")
            return redirect("worlds:detail", pk=world_pk)
        return render(request, "worlds/grant_points.html", {
            "world": world,
            "char": char,
            "form": form,
        })


class GrantItemView(LoginRequiredMixin, View):
    def get(self, request, world_pk, char_pk):
        world = get_object_or_404(World, pk=world_pk)
        if world.creator != request.user:
            return redirect("worlds:detail", pk=world_pk)
        char = get_object_or_404(Character, pk=char_pk, world=world)
        form = GrantItemForm()
        return render(request, "worlds/grant_item.html", {
            "world": world, "char": char, "form": form
        })

    def post(self, request, world_pk, char_pk):
        world = get_object_or_404(World, pk=world_pk)
        if world.creator != request.user:
            return redirect("worlds:detail", pk=world_pk)
        char = get_object_or_404(Character, pk=char_pk, world=world)
        form = GrantItemForm(request.POST)
        if not form.is_valid():
            return render(request, "worlds/grant_item.html", {
                "world": world, "char": char, "form": form
            })
        item = Item.objects.get(pk=form.cleaned_data["item"])
        qty = form.cleaned_data["quantity"]

        # Проверим наличие в пуле мира
        pool = WorldItemPool.objects.filter(world=world, item=item).first()
        if pool and pool.remaining is not None:
            if pool.remaining < qty:
                messages.error(request, "В мире осталось меньше предметов, чем вы запросили.")
                return redirect("worlds:grant-item", world_pk=world.pk, char_pk=char.pk)
            pool.remaining -= qty
            pool.save()

        # Добавляем в инвентарь персонажа
        inv_entry, created = InventoryItem.objects.get_or_create(
            character=char, item=item,
            defaults={"quantity": qty}
        )
        if not created:
            inv_entry.quantity += qty
            inv_entry.save()

        messages.success(request, f"{char.name} получил {qty}× «{item.name}»")
        return redirect("worlds:detail", pk=world_pk)


# worlds/views.py

class QuickGiveChestView(LoginRequiredMixin, View):
    template_name = "worlds/quick_give_chest.html"

    def get(self, request, world_pk):
        world = get_object_or_404(World, pk=world_pk, creator=request.user)
        form = QuickChestForm(world=world)

        return render(request, self.template_name, {"world": world, "form": form})

    def post(self, request, world_pk):
        world = get_object_or_404(World, pk=world_pk, creator=request.user)
        form = QuickChestForm(world, request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"world": world, "form": form})

        cd = form.cleaned_data
        char = Character.objects.get(pk=cd["character"].pk, world=world)
        # сразу создаём сундук для персонажа
        ChestInstance.create_for_character(
            character=cd["character"],
            luck=char.lck_stat,
            chest_rarity=cd["chest_rarity"].lvl,
            count=cd["count"],
            rare_count=cd.get("rare_count") or 0,
            rare_rarity=cd.get("rare_rarity"),
            type_bias=cd.get("type_bias"),
            type_bias_count=cd.get("type_bias_count") or 0,
        )
        messages.success(request, f"Сундук выдан {cd['character'].name}.")
        return redirect("worlds:detail", pk=world_pk)
