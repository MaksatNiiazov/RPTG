from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView

from items.models import Item
from worlds.models import PendingLoot, World
from .forms import CharacterForm, CharacterKnowledgeForm
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

    def get_success_url(self):
        return reverse_lazy("characters:character_detail", kwargs={"pk": self.object.pk})


class CharacterDetailView(LoginRequiredMixin, DetailView):
    model = Character
    template_name = "characters/character_detail.html"
    context_object_name = "char"
    login_url = reverse_lazy("accounts:login")

    def get_queryset(self):
        # Смотрим только своих персонажей
        return Character.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        character = self.object

        # если нет связанной экипировки — создаём
        if not hasattr(character, "equipment"):
            Equipment.objects.create(character=character)

        context["equipment"] = character.equipment
        context["legendary_bonuses"] = character.get_legendary_bonuses()

        context["slot_names"] = SLOT_NAMES
        return context


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


class ManageKnowledgeView(LoginRequiredMixin, View):
    """
    ГМ отмечает, кого знает конкретный персонаж.
    """
    template_name = "characters/manage_knowledge.html"

    def dispatch(self, request, *args, **kwargs):
        self.char = get_object_or_404(Character, pk=kwargs["char_pk"])
        # Проверяем, что пользователь — гейммастер этого мира
        if request.user != self.char.world.creator:
            return redirect("worlds:detail", pk=self.char.world.pk)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, char_pk):
        form = CharacterKnowledgeForm(instance=self.char)
        return render(request, self.template_name, {
            "char": self.char,
            "form": form,
        })

    def post(self, request, char_pk):
        form = CharacterKnowledgeForm(request.POST, instance=self.char)
        if form.is_valid():
            form.save()
            return redirect("worlds:detail", pk=self.char.world.pk)
        return render(request, self.template_name, {
            "char": self.char,
            "form": form,
        })


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
            data = {}

        if is_ajax:
            print(data)
            return JsonResponse({"status": status, "message": message, "data": data})
        # fallback обычный
        messages_method = messages.success if status=="ok" else messages.error
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
            data = {}

        if is_ajax:
            return JsonResponse({"status": status, "message": message, "data": data})
        messages_method = messages.success if status=="ok" else messages.error
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
        messages_method = messages.success if status=="ok" else messages.error
        messages_method(request, message)
        return redirect("characters:character-inventory", character_id)
