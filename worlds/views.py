from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, FormView, TemplateView
from django.shortcuts import get_object_or_404, redirect, render

from character.models import Character, InventoryItem, ChestInstance
from items.forms import LootConfigForm
from items.loot import generate_loot_items
from items.models import Item
from .forms import WorldForm, GrantAbilityPointsForm, GrantItemForm, QuickChestForm
from .loot import open_chest_in_world
from .models import World, WorldItemPool, WorldInvitation


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
        npcs = world.characters.filter(is_npc=True)
        is_gm = (world.creator == user)

        ctx["is_gm"] = is_gm

        if is_gm:
            inv, _ = WorldInvitation.objects.get_or_create(
                world=world, invited_by=user
            )
            ctx["invite_link"] = self.request.build_absolute_uri(
                reverse("worlds:accept-invite", kwargs={"token": str(inv.token)})
            )

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


class AcceptInviteView(View):
    def get(self, request, token):
        inv = get_object_or_404(WorldInvitation, token=token, accepted=False)
        # если пользователь не залогинен — перенаправляем на логин, с next на эту страницу
        if not request.user.is_authenticated:
            return redirect(f"{reverse_lazy('accounts:login')}?next={request.path}")
        # связываем пользователя с миром
        inv.world.players.add(request.user)
        inv.accepted = True
        inv.save()
        messages.success(request, f"Вы присоединились к миру «{inv.world.name}»")
        return redirect("worlds:detail", pk=inv.world.pk)


class WorldInviteLinkView(LoginRequiredMixin, TemplateView):
    template_name = "worlds/world_invite_link.html"
    login_url = "accounts:login"

    def dispatch(self, request, *args, **kwargs):
        # только ГМ
        self.world = get_object_or_404(World, pk=kwargs["pk"], creator=request.user)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **ctx):
        ctx = super().get_context_data(**ctx)
        # либо существующее, либо создаём новое приглашение
        inv, created = WorldInvitation.objects.get_or_create(
            world=self.world,
            invited_by=self.request.user,
        )
        # URL для копирования
        link = self.request.build_absolute_uri(
            reverse_lazy("worlds:accept-invite", kwargs={"token": str(inv.token)})
        )
        ctx["invite_link"] = link
        ctx["accepted"] = inv.accepted
        return ctx
