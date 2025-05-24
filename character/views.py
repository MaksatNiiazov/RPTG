from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, UpdateView

from items.models import Item
from worlds.models import PendingLoot, World
from .forms import CharacterForm, LevelUpForm, CharacterUpdateForm
from .models import Character, InventoryItem, Equipment


class CharacterCreateView(LoginRequiredMixin, CreateView):
    model = Character
    form_class = CharacterForm
    template_name = "characters/character_form.html"
    login_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.world = World.objects.get(pk=self.kwargs["world_pk"])

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['initial_points'] = 10
        ctx['world'] = World.objects.get(pk=self.kwargs["world_pk"]).pk
        return ctx

    def get_success_url(self):
        return reverse_lazy("characters:character_detail", kwargs={"pk": self.object.pk})


class CharacterUpdateView(LoginRequiredMixin, UpdateView):
    model = Character
    form_class = CharacterUpdateForm
    template_name = "characters/character_update_form.html"
    login_url = reverse_lazy("accounts:login")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['world'] = World.objects.get(pk=self.kwargs["world_pk"]).pk
        return ctx

    def get_success_url(self):
        return reverse_lazy("characters:character_detail", kwargs={"pk": self.object.pk})


class CharacterDetailView(LoginRequiredMixin, DetailView):
    model = Character
    template_name = "characters/character_detail.html"
    context_object_name = "char"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        c = self.object
        user = self.request.user

        # Если ещё нет записи Equipment
        if not hasattr(c, "equipment"):
            Equipment.objects.create(character=c)

        ctx["equipment"] = c.equipment
        ctx["legendary_bonuses"] = c.get_legendary_bonuses()
        ctx["slot_names"] = SLOT_NAMES

        # Кто смотрит?
        is_gm = (c.owner == user) or (c.world and c.world.creator == user)
        is_owner = (c.owner == user)
        ctx["is_gm"] = is_gm
        ctx["is_owner"] = is_owner

        # Если NPC и смотрит не GM/владелец — скрываем неподозволенные поля
        ctx["show_name"] = (not c.is_npc) or is_gm or c.known_name
        ctx["show_background"] = (not c.is_npc) or is_gm or c.known_background
        ctx["show_stats"] = (not c.is_npc) or is_gm or c.known_stats
        ctx["show_equipment"] = (not c.is_npc) or is_gm or c.known_equipment
        ctx["show_notes"] = (not c.is_npc) or is_gm or c.known_notes
        ctx["world"] = c.world.pk

        return ctx


class PickLootView(LoginRequiredMixin, View):
    """
    Персонаж видит свои pending_loots и выбирает, какие предметы положить в инвентарь.
    """
    template_name = "characters/pick_loot.html"

    def get(self, request):
        chars = request.user.characters.all()
        # агрегируем все незабранные луты
        loots = PendingLoot.objects.filter(character__in=chars, picked_up=False)
        return render(request, self.template_name, {"loots": loots})

    def post(self, request, loot_pk):
        pl = get_object_or_404(PendingLoot, pk=loot_pk, character__owner=request.user, picked_up=False)
        # в POST придут id выбранных items: loot_item_1, loot_item_2...
        chosen_ids = [int(v.split("_")[-1]) for k, v in request.POST.items() if k.startswith("item_")]
        items = pl.items.filter(pk__in=chosen_ids)
        # переносим в инвентарь
        inv = pl.character.inventory
        for it in items:
            inv_item, _ = inv.items.get_or_create(item=it)
            inv_item.quantity += 1
            inv_item.save()
        pl.picked_up = True
        pl.save()
        return redirect("characters:character_detail", pk=pl.character.pk)


SLOT_NAMES = [
    {"head": 'Голова'},
    {"neck": 'Шея'},
    {"chest": 'Туловище'},
    {"hands": 'Руки'},
    {"waist": 'Пояс'},
    {"legs": 'Ноги'},
    {"feet": 'Ступни'},
    {"cloak": 'Мантия'},
    {"ring_left": 'Кольцо на левую руку'},
    {"ring_right": 'Кольцо на правую руку'},
    {"main_hand": 'Основная рука'},
    {"off_hand": 'Второстепенная рука'},
    {"two_hands": 'Две руки'},
]


class CharacterInventoryView(LoginRequiredMixin, DetailView):
    model = Character
    template_name = "characters/inventory.html"
    context_object_name = "char"
    pk_url_kwarg = "character_id"

    def get(self, request, *args, **kwargs):
        if self.get_object().owner != request.user:
            messages.error(request, "Нет доступа")
            return redirect("characters:character_detail", pk=self.object.pk)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return Character.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        char = self.object

        # Гарантированно получаем или создаём экипировку
        equipment, created = Equipment.objects.get_or_create(character=char)

        context["equipment"] = equipment
        context["inventory_items"] = char.items.select_related("item")
        context["slot_names"] = SLOT_NAMES
        return context


class EquipItemView(LoginRequiredMixin, View):
    def post(self, request, character_id, item_id):
        character = get_object_or_404(Character, id=character_id, owner=request.user)
        item = get_object_or_404(Item, id=item_id)

        # выполнится ли AJAX?
        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

        try:
            eq = character.equip_item(item)
            print(eq)
            message = f"{item.name} экипирован."
            status = "ok"
            data = {
                "slot": eq,
                "item": {"id": item.id, "name": item.name, "bonus": item.bonus, "weight": item.weight}
            }
        except Exception as e:
            message = str(e)
            status = "error"
            data = {'message': message}

        if is_ajax:
            print(data)
            return JsonResponse({"status": status, "message": message, "data": data})
        # fallback обычный
        messages_method = messages.success if status == "ok" else messages.error
        messages_method(request, message)
        return redirect("characters:character-inventory", character_id)


class UnequipSlotView(LoginRequiredMixin, View):
    def post(self, request, character_id, slot):
        character = get_object_or_404(Character, id=character_id, owner=request.user)
        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

        try:
            item = character.unequip_slot(slot)
            message = f"{item.name} снят."
            status = "ok"
            data = {"slot": slot, "item": {"id": item.id, "name": item.name,
                                           "bonus": item.bonus, "weight": item.weight}}
        except Exception as e:
            message = str(e)
            status = "error"
            data = {'message': message}

        if is_ajax:
            return JsonResponse({"status": status, "message": message, "data": data})
        messages_method = messages.success if status == "ok" else messages.error
        messages_method(request, message)
        return redirect("characters:character-inventory", character_id)


class DropItemView(LoginRequiredMixin, View):
    def post(self, request, character_id, item_id):
        character = get_object_or_404(Character, id=character_id, owner=request.user)
        item = get_object_or_404(Item, id=item_id)
        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

        inv_item = InventoryItem.objects.filter(character=character, item=item).first()
        if not inv_item:
            message = "У персонажа нет такого предмета."
            status = "error"
            data = {}
        else:
            inv_item.quantity -= 1
            if inv_item.quantity <= 0:
                inv_item.delete()
                remaining = 0
            else:
                inv_item.save()
                remaining = inv_item.quantity
            message = f"{item.name} выброшен."
            status = "ok"
            data = {"item_id": item.id, "remaining": remaining}

        if is_ajax:
            return JsonResponse({"status": status, "message": message, "data": data})
        from django.contrib import messages
        messages_method = messages.success if status == "ok" else messages.error
        messages_method(request, message)
        return redirect("characters:character-inventory", character_id)


class LevelUpView(View):
    template_name = "characters/level_up.html"

    def get(self, request, character_id):
        character = get_object_or_404(Character, id=character_id, owner=request.user)
        form = LevelUpForm()
        return render(request, self.template_name, {
            "char": character,
            "form": form,
        })

    def post(self, request, character_id):
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return HttpResponseBadRequest("Только AJAX")

        char = get_object_or_404(Character, id=character_id, owner=request.user)
        stat = request.POST.get('stat')
        # всегда тратим ровно 1 очко
        try:
            char.lvlup(stat, 1)
            char.save()
        except ValidationError as e:
            return JsonResponse({'status': 'error', 'message': e.message})

        # отдаем новые значения
        data = {
            'status': 'ok',
            'stat': stat,
            'new_value': getattr(char, stat),
            'remaining': char.ability_points,
        }
        return JsonResponse(data)
