from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, UpdateView

from items.models import Item
from worlds.models import World
from .forms import CharacterForm, LevelUpForm, CharacterUpdateForm
from .models import Character, InventoryItem, Equipment, ChestInstance


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
        world = World.objects.get(pk=self.kwargs["world_pk"])
        user = self.request.user
        ctx = super().get_context_data(**kwargs)
        ctx['initial_points'] = 16 if world.creator != user else 80
        ctx['world'] = world.pk
        ctx["is_gm"] = (world.creator == user)

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
        ctx['world'] = self.kwargs["pk"]
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
        ctx["spells"] = c.spells.select_related("school", "category").order_by("level", "school__name", "name")

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
        ctx["npc_flags"] = {
            'known_name': c.known_name,
            'known_background': c.known_background,
            'known_stats': c.known_stats,
            'known_equipment': c.known_equipment,
            'known_notes': c.known_notes,
        }
        stat_roll_bonuses = {
            'str': c.get_stat_roll_bonus(c.str_stat),
            'dex': c.get_stat_roll_bonus(c.dex_stat),
            'con': c.get_stat_roll_bonus(c.con_stat),
            'int': c.get_stat_roll_bonus(c.int_stat),
            'wis': c.get_stat_roll_bonus(c.wis_stat),
            'cha': c.get_stat_roll_bonus(c.cha_stat),
            'acc': c.get_stat_roll_bonus(c.acc_stat),
            'lck': c.get_stat_roll_bonus(c.lck_stat),
        }
        ctx['stat_roll_bonuses'] = stat_roll_bonuses
        return ctx


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

    #
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.owner != request.user:
            messages.error(request, "Нет доступа")
            return redirect("characters:character_detail", pk=obj.pk)
        return super().get(request, *args, **kwargs)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")

        return super().dispatch(request, *args, **kwargs)

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


class ChestDetailView(LoginRequiredMixin, View):
    """
    Показывает сундук: игрок выбирает предметы и подтверждает.
    После подтверждения переносит выбранные в инвентарь и удаляет сам сундук.
    """
    template_name = 'characters/chest_detail.html'

    def get(self, request, instance_pk):
        chest = get_object_or_404(ChestInstance, pk=instance_pk,
                                  character__owner=request.user)
        return render(request, self.template_name, {
            'chest': chest,
            'items': chest.items.all(),
            'user': request.user
        })

    def post(self, request, instance_pk):
        chest = get_object_or_404(ChestInstance, pk=instance_pk,
                                  character__owner=request.user)
        selected_ids = request.POST.getlist('items')
        if not selected_ids:
            messages.error(request, "Выберите хотя бы один предмет.")
            return redirect('worlds:chest-detail', instance_pk=instance_pk)

        # переносим выбранные предметы
        for item in chest.items.filter(pk__in=selected_ids):
            inv_entry, created = InventoryItem.objects.get_or_create(
                character=chest.character,
                item=item,
                defaults={'quantity': 1}
            )
            if not created:
                inv_entry.quantity += 1
                inv_entry.save()

        # удаляем сундук целиком (и все его связи)
        chest.delete()

        messages.success(request, f"Вы забрали {len(selected_ids)} предмет(ов). Сундук исчез.")
        return redirect('characters:character-inventory', character_id=chest.character.pk)


@method_decorator(require_POST, name="dispatch")
class ToggleNpcFlagView(LoginRequiredMixin, View):
    def post(self, request, char_id):
        if not request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return HttpResponseBadRequest("Только AJAX")

        c = get_object_or_404(Character, pk=char_id)
        user = request.user

        # Check permissions - user must be owner or world creator
        if not (user == c.owner or (c.world and user == c.world.creator)):
            return HttpResponseForbidden("Нет прав")

        flag = request.POST.get("flag")
        valid_flags = {
            'known_name',
            'known_background',
            'known_stats',
            'known_equipment',
            'known_notes',
            'visible_to_players',
        }

        if flag not in valid_flags:
            return JsonResponse({'status': 'error', 'message': 'Неверный флаг'}, status=400)

        # Toggle the flag
        current = getattr(c, flag)
        setattr(c, flag, not current)
        c.save()

        return JsonResponse({
            'status': 'ok',
            'flag': flag,
            'newValue': not current
        })


@method_decorator(require_POST, name="dispatch")
class AjaxAdjustHpView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return HttpResponseBadRequest("Только AJAX")
        char = get_object_or_404(Character, pk=pk)
        user = request.user
        if not (char.owner == user or (char.world and char.world.creator == user)):
            return HttpResponseForbidden("Нет прав")
        try:
            delta = int(request.POST.get('delta'))
        except (TypeError, ValueError):
            return JsonResponse({'status': 'error', 'message': 'Неверная дельта'})
        try:
            new_hp = char.adjust_hp(delta)
        except ValidationError as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
        return JsonResponse({'status': 'ok', 'current_hp': new_hp})


@method_decorator(require_POST, name="dispatch")
class AjaxAdjustCpView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return HttpResponseBadRequest("Только AJAX")
        char = get_object_or_404(Character, pk=pk)
        user = request.user
        if not (char.owner == user or (char.world and char.world.creator == user)):
            return HttpResponseForbidden("Нет прав")
        action = request.POST.get('action')
        try:
            new_cp = char.adjust_cp(action)
        except ValidationError as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
        return JsonResponse({'status': 'ok', 'current_concentration': new_cp})
