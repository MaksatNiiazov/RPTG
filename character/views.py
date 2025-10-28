from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView, ListView

from items.models import Item
from worlds.models import World
from shops.utils.economy import get_sell_price
from .forms import CharacterForm, LevelUpForm, CharacterUpdateForm, GoldDeltaForm
from .models import (
    Character,
    InventoryItem,
    Equipment,
    ChestInstance,
    CharacterClass,
    Talent,
    HomeInventoryItem,
)


class ClassListView(LoginRequiredMixin, ListView):
    model = CharacterClass
    template_name = 'characters/class_list.html'
    context_object_name = 'classes'

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')

        if search_query:
            queryset = queryset.filter(name__icontains=search_query)

        return queryset.order_by('name')


class TalentListView(LoginRequiredMixin, ListView):
    model = Talent
    template_name = 'characters/talent_list.html'
    context_object_name = 'talents'

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')

        if search_query:
            queryset = queryset.filter(name__icontains=search_query)

        return queryset.order_by('name')


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

        # Получаем выбранный класс из GET параметров (если есть)
        selected_class_id = self.request.GET.get('character_class')

        if world.creator == user:
            # Для ГМ всегда 80 очков
            ctx['initial_points'] = 80
        else:
            if selected_class_id:
                try:
                    # Для игроков: берем очки из выбранного класса
                    cls = CharacterClass.objects.get(id=selected_class_id, approve=True)
                    ctx['initial_points'] = cls.base_ability_points
                except CharacterClass.DoesNotExist:
                    # Если класс не найден - 10 очков
                    ctx['initial_points'] = 10
            else:
                # Если класс не выбран - 10 очков
                ctx['initial_points'] = 10

        ctx['world'] = world.pk
        ctx["is_gm"] = (world.creator == user)
        ctx["classes"] = CharacterClass.objects.filter(approve=True)
        ctx["talents"] = Talent.objects.filter(approve=True)

        return ctx

    def get_success_url(self):
        return reverse_lazy("characters:character_detail", kwargs={"pk": self.object.pk})

    # Добавим обработку AJAX запроса для получения информации о классе
    def get(self, request, *args, **kwargs):
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' and 'class_id' in request.GET:
            try:
                cls = CharacterClass.objects.get(id=request.GET.get('class_id'), approve=True)
                return JsonResponse({
                    'base_points': cls.base_ability_points,
                    'str_bonus': cls.str_bonus,
                    'dex_bonus': cls.dex_bonus,
                    'con_bonus': cls.con_bonus,
                    'int_bonus': cls.int_bonus,
                    'wis_bonus': cls.wis_bonus,
                    'cha_bonus': cls.cha_bonus,
                    'acc_bonus': cls.acc_bonus,
                    'lck_bonus': cls.lck_bonus
                })
            except CharacterClass.DoesNotExist:
                return JsonResponse({'error': 'Class not found'}, status=404)
        return super().get(request, *args, **kwargs)


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

        # Основные данные
        ctx["equipment"] = c.equipment
        ctx["legendary_bonuses"] = c.get_legendary_bonuses()
        ctx["spells"] = c.spells.select_related("school", "category").order_by("level", "school__name", "name")
        ctx["slot_names"] = [
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

        # Права доступа
        is_gm = c.world and c.world.creator == user
        is_owner = (c.owner == user)
        ctx["is_gm"] = is_gm
        ctx["is_owner"] = is_owner

        # Фильтрация видимости для NPC
        ctx["show_name"] = (not c.is_npc) or is_gm or c.known_name
        ctx["show_background"] = (not c.is_npc) or is_gm or c.known_background
        ctx["show_stats"] = (not c.is_npc) or is_gm or c.known_stats
        ctx["show_equipment"] = (not c.is_npc) or is_gm or c.known_equipment
        ctx["show_notes"] = (not c.is_npc) or is_gm or c.known_notes

        # === ДОБАВЛЕННЫЕ ПАРАМЕТРЫ ===
        # Токены
        ctx["tokens"] = {
            'inspiration': {
                'current': c.inspiration_tokens,
                'max': c.max_inspiration_tokens,
            },
            'precision': {
                'current': c.precision_tokens,
                'max': c.max_precision_tokens,
            }
        }

        # Боевые характеристики
        ctx["combat_stats"] = {
            'total_attack': c.total_attack,
            'total_defense': c.total_defense,
            'critical_hit': c.critical_hit,
            'action_points': c.action_points,
            'possible_chain_attacks': c.possible_chain_attacks,
            'possible_reactions': c.possible_reactions,
        }

        # Эффективные характеристики (с бонусами класса)
        ctx["effective_stats"] = {
            'str': c.effective_str,
            'dex': c.effective_dex,
            'con': c.effective_con,
            'int': c.effective_int,
            'wis': c.effective_wis,
            'cha': c.effective_cha,
            'acc': c.effective_acc,
            'lck': c.effective_lck,
        }

        # Дополнительные данные
        ctx["world"] = c.world.pk if c.world else None
        ctx["npc_flags"] = {
            'known_name': c.known_name,
            'known_background': c.known_background,
            'known_stats': c.known_stats,
            'known_equipment': c.known_equipment,
            'known_notes': c.known_notes,
        }

        # Бонусы к броскам
        stat_roll_bonuses = {
            'str': c.get_stat_roll_bonus(c.effective_str),
            'dex': c.get_stat_roll_bonus(c.effective_dex),
            'con': c.get_stat_roll_bonus(c.effective_con),
            'int': c.get_stat_roll_bonus(c.effective_int),
            'wis': c.get_stat_roll_bonus(c.effective_wis),
            'cha': c.get_stat_roll_bonus(c.effective_cha),
            'acc': c.get_stat_roll_bonus(c.effective_acc),
            'lck': c.get_stat_roll_bonus(c.effective_lck),
        }
        ctx['stat_roll_bonuses'] = stat_roll_bonuses

        return ctx


class CharacterDeleteView(LoginRequiredMixin, DeleteView):
    model = Character
    template_name = "characters/character_confirm_delete.html"  # Новый шаблон
    context_object_name = "char"
    success_url = reverse_lazy("accounts:profile")  # URL после удаления

    def get(self, request, *args, **kwargs):
        """Проверка прав доступа при GET-запросе"""
        obj = self.get_object()
        if obj.owner != request.user:
            messages.error(request, "У вас нет прав для удаления этого персонажа")
            return redirect("characters:character_detail", pk=obj.pk)
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        """Проверка прав доступа при POST-запросе"""
        obj = self.get_object()
        if obj.owner != request.user:
            messages.error(request, "У вас нет прав для удаления этого персонажа")
            return redirect("characters:character_detail", pk=obj.pk)

        messages.success(request, f"Персонаж {obj.name} был успешно удален")
        return super().post(request, *args, **kwargs)


class CharacterInventoryView(LoginRequiredMixin, DetailView):
    model = Character
    template_name = "characters/inventory.html"
    context_object_name = "char"
    pk_url_kwarg = "character_id"

    #
    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        if not (obj.owner == request.user or (obj.world and obj.world.creator == request.user)):
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
        is_owner = self.request.user == char.owner
        is_gm = bool(char.world and char.world.creator == self.request.user)
        context["is_owner"] = is_owner
        context["home_storage_enabled"] = char.home_storage_enabled
        context["can_toggle_home_storage"] = is_gm
        context["can_use_home_storage"] = char.home_storage_enabled and (is_owner or is_gm)
        if char.home_storage_enabled:
            context["home_storage_items"] = char.home_storage_items.select_related("item").order_by("item__name")
        else:
            context["home_storage_items"] = []
        context["slot_names"] = [
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
                "item": {
                    "id": item.id,
                    "name": item.name,
                    "bonus": item.bonus,
                    "weight": item.weight,
                    "legendary_buff": item.legendary_buff or "",
                    "rarity_color": getattr(item.rarity, "color", "#a57c52"),
                    "sell_price": get_sell_price(item, character) if character.can_trade else None,
                },
                "load": character.get_current_load(),
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
        character = get_object_or_404(Character, id=character_id)
        is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

        try:
            item = character.unequip_slot(slot)
            message = f"{item.name} снят."
            status = "ok"
            data = {
                "slot": slot,
                "item": {
                    "id": item.id,
                    "name": item.name,
                    "bonus": item.bonus,
                    "weight": item.weight,
                    "legendary_buff": item.legendary_buff or "",
                    "rarity_color": getattr(item.rarity, "color", "#a57c52"),
                    "sell_price": get_sell_price(item, character) if character.can_trade else None,
                },
                "load": character.get_current_load(),
            }
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
        character = get_object_or_404(Character, id=character_id)
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
            data = {
                "item_id": item.id,
                "remaining": remaining,
                "load": character.get_current_load(),
            }

        if is_ajax:
            return JsonResponse({"status": status, "message": message, "data": data})
        from django.contrib import messages
        messages_method = messages.success if status == "ok" else messages.error
        messages_method(request, message)
        return redirect("characters:character-inventory", character_id)


@method_decorator(require_POST, name="dispatch")
class StoreItemInHomeView(LoginRequiredMixin, View):
    def post(self, request, character_id, item_id):
        character = get_object_or_404(Character, id=character_id)
        user = request.user
        is_owner = user == character.owner
        is_gm = bool(character.world and character.world.creator == user)

        if not (is_owner or is_gm):
            return HttpResponseForbidden("Нет прав")

        if not character.home_storage_enabled and not is_gm:
            msg = "Домашнее хранилище пока не разрешено ГМ."
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({'status': 'error', 'message': msg}, status=403)
            messages.error(request, msg)
            return redirect("characters:character-inventory", character_id)

        inv_entry = (
            InventoryItem.objects
            .select_related("item")
            .filter(character=character, item_id=item_id)
            .first()
        )
        if not inv_entry:
            msg = "В инвентаре нет такого предмета."
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({'status': 'error', 'message': msg}, status=404)
            messages.error(request, msg)
            return redirect("characters:character-inventory", character_id)

        item = inv_entry.item
        quantity_moved = 1  # Since you're moving one at a time
        if inv_entry.quantity <= quantity_moved:
            inv_entry.delete()
            inventory_quantity = 0
        else:
            inv_entry.quantity -= quantity_moved
            inv_entry.save(update_fields=["quantity"])
            inventory_quantity = inv_entry.quantity

        storage_entry, created = HomeInventoryItem.objects.get_or_create(
            character=character,
            item=item,
            defaults={"quantity": quantity_moved},
        )
        if not created:
            storage_entry.quantity += quantity_moved
            storage_entry.save(update_fields=["quantity"])
        storage_quantity = storage_entry.quantity

        msg = f"{item.name} перемещён в домашнее хранилище."
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            item_data = {
                'id': item.id,
                'name': item.name,
                'bonus': item.bonus,
                'weight': item.weight,
                'legendary_buff': item.legendary_buff if hasattr(item, 'legendary_buff') else "",
                'rarity_color': item.rarity_color if hasattr(item, 'rarity_color') else "#a57c52",
                'sell_price': item.sell_price if hasattr(item, 'sell_price') else None,
            }
            return JsonResponse({
                'status': 'ok',
                'action': 'store',
                'item': item_data,
                'inventory_quantity': inventory_quantity,
                'storage_quantity': storage_quantity,
                'load': character.get_current_load(),
                'message': msg
            })
        messages.success(request, msg)
        return redirect("characters:character-inventory", character_id)


@method_decorator(require_POST, name="dispatch")
class RetrieveItemFromHomeView(LoginRequiredMixin, View):
    def post(self, request, character_id, item_id):
        character = get_object_or_404(Character, id=character_id)
        user = request.user
        is_owner = user == character.owner
        is_gm = bool(character.world and character.world.creator == user)

        if not (is_owner or is_gm):
            return HttpResponseForbidden("Нет прав")

        if not character.home_storage_enabled and not is_gm:
            msg = "Домашнее хранилище пока не разрешено ГМ."
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({'status': 'error', 'message': msg}, status=403)
            messages.error(request, msg)
            return redirect("characters:character-inventory", character_id)

        storage_entry = (
            HomeInventoryItem.objects
            .select_related("item")
            .filter(character=character, item_id=item_id)
            .first()
        )
        if not storage_entry:
            msg = "В хранилище нет такого предмета."
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({'status': 'error', 'message': msg}, status=404)
            messages.error(request, msg)
            return redirect("characters:character-inventory", character_id)

        item = storage_entry.item
        quantity_moved = 1  # Since you're moving one at a time
        if storage_entry.quantity <= quantity_moved:
            storage_entry.delete()
            storage_quantity = 0
        else:
            storage_entry.quantity -= quantity_moved
            storage_entry.save(update_fields=["quantity"])
            storage_quantity = storage_entry.quantity

        inv_entry, created = InventoryItem.objects.get_or_create(
            character=character,
            item=item,
            defaults={"quantity": quantity_moved},
        )
        if not created:
            inv_entry.quantity += quantity_moved
            inv_entry.save(update_fields=["quantity"])
        inventory_quantity = inv_entry.quantity

        msg = f"{item.name} возвращён из домашнего хранилища."
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            item_data = {
                'id': item.id,
                'name': item.name,
                'bonus': item.bonus,
                'weight': item.weight,
                'legendary_buff': item.legendary_buff if hasattr(item, 'legendary_buff') else "",
                'rarity_color': item.rarity_color if hasattr(item, 'rarity_color') else "#a57c52",
                'sell_price': item.sell_price if hasattr(item, 'sell_price') else None,
            }
            return JsonResponse({
                'status': 'ok',
                'action': 'retrieve',
                'item': item_data,
                'inventory_quantity': inventory_quantity,
                'storage_quantity': storage_quantity,
                'load': character.get_current_load(),
                'message': msg
            })
        messages.success(request, msg)
        return redirect("characters:character-inventory", character_id)


@method_decorator(require_POST, name="dispatch")
class ToggleHomeStorageView(LoginRequiredMixin, View):
    def post(self, request, character_id):
        character = get_object_or_404(Character, pk=character_id)
        user = request.user
        if not (character.world and character.world.creator == user):
            return HttpResponseForbidden("Нет прав")

        character.home_storage_enabled = not character.home_storage_enabled
        character.save(update_fields=["home_storage_enabled"])

        if character.home_storage_enabled:
            messages.success(request, "Домашнее хранилище включено.")
        else:
            messages.info(request,
                          "Домашнее хранилище отключено. Игроки не смогут им пользоваться до повторного включения.")

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
        if request.headers.get("X-Requested-With") != "XMLHttpRequest":
            return HttpResponseBadRequest("Только AJAX")

        c = get_object_or_404(Character, pk=char_id)
        user = request.user
        if not (user == c.owner or (c.world and user == c.world.creator)):
            return HttpResponseForbidden("Нет прав")

        flag = request.POST.get("flag")
        # Добавляем visible_to_players
        valid = {
            'known_name',
            'known_background',
            'known_stats',
            'known_equipment',
            'known_notes',
            'visible_to_players',
        }
        if flag not in valid:
            return JsonResponse({'status': 'error', 'message': 'Неверный флаг'}, status=400)

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


@method_decorator(require_POST, name="dispatch")
class AjaxAdjustTokenView(LoginRequiredMixin, View):
    def post(self, request, pk):
        if request.headers.get('X-Requested-With') != 'XMLHttpRequest':
            return HttpResponseBadRequest("Только AJAX")

        char = get_object_or_404(Character, pk=pk)
        if not (char.owner == request.user or
                (char.world and char.world.creator == request.user)):
            return HttpResponseForbidden("Нет прав")

        token_type = request.POST.get('token_type')
        action = request.POST.get('action')

        current = getattr(char, f'{token_type}_tokens')
        max_value = getattr(char, f'max_{token_type}_tokens')

        if action == 'inc' and current < max_value:
            setattr(char, f'{token_type}_tokens', current + 1)
            char.save()
        elif action == 'dec' and current > 0:
            setattr(char, f'{token_type}_tokens', current - 1)
            char.save()
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Достигнут максимум/минимум'
            })

        return JsonResponse({
            'status': 'ok',
            'current': getattr(char, f'{token_type}_tokens'),
            'max': max_value
        })


@require_POST
@login_required
def toggle_can_trade(request, char_id):
    if request.headers.get("x-requested-with") != "XMLHttpRequest":
        return JsonResponse({"status": "error", "message": "Только AJAX"}, status=400)

    character = get_object_or_404(Character, pk=char_id)
    if not character.world or character.world.creator != request.user:
        return JsonResponse({"status": "error", "message": "Нет прав"}, status=403)

    character.can_trade = not character.can_trade
    character.save(update_fields=["can_trade"])

    return JsonResponse({
        "status": "ok",
        "new_value": character.can_trade
    })


class CharacterGoldDeltaView(LoginRequiredMixin, View):
    template_name = "characters/edit_gold_delta.html"

    def get(self, request, pk):
        char = get_object_or_404(Character, pk=pk)
        if not self._has_access(request.user, char):
            messages.error(request, "Нет доступа к изменению золота.")
            return redirect("characters:character_detail", pk=pk)

        form = GoldDeltaForm()
        return render(request, self.template_name, {"form": form, "char": char})

    def post(self, request, pk):
        char = get_object_or_404(Character, pk=pk)
        if not self._has_access(request.user, char):
            messages.error(request, "Нет доступа к изменению золота.")
            return redirect("characters:character_detail", pk=pk)

        form = GoldDeltaForm(request.POST)
        if form.is_valid():
            delta = form.cleaned_data["delta"]
            char.gold = max(0, char.gold + delta)
            char.save(update_fields=["gold"])
            messages.success(request, f"Золото успешно изменено. Теперь у {char.name} {char.gold} золота.")
            return redirect("characters:character_detail", pk=char.pk)

        return render(request, self.template_name, {"form": form, "char": char})

    def _has_access(self, user, char):
        return char.owner == user or (char.world and char.world.creator == user)
