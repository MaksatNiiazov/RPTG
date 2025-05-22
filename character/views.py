from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView

from worlds.models import PendingLoot, World
from .forms import CharacterForm, CharacterKnowledgeForm
from .models import Character, InventoryItem


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


class CharacterInventoryView(DetailView):
    model = Character
    template_name = "characters/inventory.html"
    context_object_name = "character"

    def get_object(self, queryset=None):
        object = super().get_object(queryset)
        if not object.has_inventory():
            object.inventory = object.create_inventory()
        return Character.objects.get(pk=self.kwargs["pk"], owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        inventory = self.object.inventory
        context["equipped"] = {
            item.slot: item for item in inventory.equipped.select_related("item")
        }
        context["inventory_items"] = inventory.items.select_related("item")
        return context




@require_POST
def equip_item(request, character_id, item_id):
    character = get_object_or_404(Character, id=character_id)
    inventory = character.inventory
    item = get_object_or_404(InventoryItem, inventory=inventory, item_id=item_id)
    try:
        inventory.equip_item(item.item)
        messages.success(request, f"Экипирован предмет: {item.item.name}")
    except Exception as e:
        messages.error(request, f"Ошибка экипировки: {e}")
    return redirect("characters:character-inventory", pk=character_id)


@require_POST
def unequip_item(request, character_id, slot):
    character = get_object_or_404(Character, id=character_id)
    inventory = character.inventory
    try:
        inventory.unequip_slot(slot)
        messages.success(request, f"Слот {slot} освобождён.")
    except Exception as e:
        messages.error(request, f"Ошибка снятия: {e}")
    return redirect("characters:character-inventory", pk=character_id)


@require_POST
def drop_item(request, character_id, item_id):
    character = get_object_or_404(Character, id=character_id)
    inventory = character.inventory
    try:
        inventory.drop_item(item_id)
        messages.success(request, "Предмет удалён из инвентаря.")
    except Exception as e:
        messages.error(request, f"Ошибка удаления: {e}")
    return redirect("characters:character-inventory", pk=character_id)