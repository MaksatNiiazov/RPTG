from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import ListView, DetailView, CreateView
from django.shortcuts import get_object_or_404, redirect, render

from character.models import Character
from items.forms import LootConfigForm
from .forms import WorldForm
from .loot import open_chest_in_world
from .models import World, PendingLoot


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


class GMLootView(LoginRequiredMixin, View):
    """
    GM открывает сундук для выбранного персонажа.
    """

    def get(self, request, world_pk, char_pk):
        world = get_object_or_404(World, pk=world_pk)
        if world.creator != request.user:
            return redirect("worlds:detail", pk=world_pk)
        form = LootConfigForm()
        return render(request, "worlds/gm_open_chest.html", {"world": world, "form": form})

    def post(self, request, world_pk, char_pk):
        world = get_object_or_404(World, pk=world_pk)
        if world.creator != request.user:
            return redirect("worlds:detail", pk=world_pk)
        from character.models import Character
        char = get_object_or_404(Character, pk=char_pk, world=world)
        form = LootConfigForm(request.POST)
        if not form.is_valid():
            return render(request, "worlds/gm_open_chest.html", {"world": world, "form": form})
        cd = form.cleaned_data
        loot_items = open_chest_in_world(
            world=world,
            luck=cd["luck"],
            chest_rarity=cd["chest_rarity"].lvl,
            count=cd["count"],
            rare_count=cd.get("rare_count") or 0,
            rare_rarity=cd.get("rare_rarity"),
            type_bias=cd.get("type_bias"),
            type_bias_count=cd.get("type_bias_count") or 0,
        )
        pl = PendingLoot.objects.create(world=world, character=char)
        pl.items.set(loot_items)
        return redirect("worlds:detail", pk=world_pk)


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
