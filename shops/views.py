import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import F
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, UpdateView, DetailView

from character.models import Character, InventoryItem
from items.models import Item
from shops.forms import ShopForm
from shops.models import Shop, ShopItem
from worlds.models import World


class ShopCreateView(CreateView):
    model = Shop
    form_class = ShopForm
    template_name = "shops/shop_form.html"

    def form_valid(self, form):
        form.instance.world = get_object_or_404(World, pk=self.kwargs["world_id"])
        form.instance.owner = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("shops:shop-detail", kwargs={"pk": self.object.pk})


class ShopUpdateView(UpdateView):
    model = Shop
    form_class = ShopForm
    template_name = "shops/shop_form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["edit_mode"] = True
        return ctx

    def get_success_url(self):
        return reverse_lazy("shops:shop-detail", kwargs={"pk": self.object.pk})


class ShopDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        shop = get_object_or_404(Shop, pk=pk)
        world = shop.world
        is_gm = (world.creator == request.user)

        if request.user.is_authenticated and not is_gm:
            available_characters = Character.objects.filter(
                owner=request.user,
                world=world,
                is_alive=True,
                can_trade=True
            )
        else:
            available_characters = []

        all_items = Item.objects.all().order_by("type__name", "name") if is_gm else None

        return render(request, "shops/shop_detail.html", {
            "shop": shop,
            "is_gm": is_gm,
            "player_characters": available_characters,
            "all_items": all_items,
        })

    @require_POST
    def post(self, request, pk):
        shop = get_object_or_404(Shop, pk=pk)
        if shop.world.creator != request.user:
            return HttpResponseForbidden("Нет прав")

        item_id = request.POST.get("item_id")
        quantity = request.POST.get("quantity")
        delete = request.POST.get("delete")

        try:
            shop_item = ShopItem.objects.get(shop=shop, item_id=item_id)
            if delete:
                shop_item.delete()
            else:
                shop_item.quantity = int(quantity)
                shop_item.save()
        except ShopItem.DoesNotExist:
            messages.error(request, "Предмет не найден.")
        return redirect("shops:shop-detail", pk=pk)


@require_POST
@login_required
def update_price_multiplier(request, pk):
    shop = get_object_or_404(Shop, pk=pk)
    if shop.world.creator != request.user:
        return JsonResponse({"status": "error", "message": "Нет прав"}, status=403)

    try:
        data = json.loads(request.body)
        multiplier = float(data.get("multiplier"))
        if multiplier <= 0:
            raise ValueError("Множитель должен быть положительным числом")

        shop.price_multiplier = multiplier
        shop.save()
        return JsonResponse({"status": "ok"})
    except (ValueError, TypeError) as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@require_POST
@login_required
def add_item_to_shop(request, pk):
    shop = get_object_or_404(Shop, pk=pk)
    if shop.world.creator != request.user:
        return JsonResponse({"status": "error", "message": "Нет прав"}, status=403)

    try:
        data = json.loads(request.body)
        item_id = data.get("item_id")
        item = get_object_or_404(Item, pk=item_id)

        # Check if item already exists in shop
        if ShopItem.objects.filter(shop=shop, item=item).exists():
            return JsonResponse({"status": "error", "message": "Этот предмет уже есть в магазине"}, status=400)

        ShopItem.objects.create(shop=shop, item=item)
        return JsonResponse({"status": "ok"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@require_POST
@login_required
def update_item_price(request, entry_id):
    entry = get_object_or_404(ShopItem, pk=entry_id)
    if entry.shop.world.creator != request.user:
        return JsonResponse({"status": "error", "message": "Нет прав"}, status=403)

    try:
        data = json.loads(request.body)
        price = int(data.get("price"))
        if price <= 0:
            raise ValueError("Цена должна быть положительным числом")

        entry.price = price
        entry.save()
        return JsonResponse({"status": "ok"})
    except (ValueError, TypeError) as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@require_POST
@login_required
def update_item_quantity(request, entry_id):
    entry = get_object_or_404(ShopItem, pk=entry_id)
    if entry.shop.world.creator != request.user:
        return JsonResponse({"status": "error", "message": "Нет прав"}, status=403)

    try:
        data = json.loads(request.body)
        quantity = data.get("quantity")

        if quantity == "" or quantity is None:
            entry.quantity = None
        else:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError("Количество должно быть положительным числом")
            entry.quantity = quantity

        entry.save()
        return JsonResponse({"status": "ok"})
    except (ValueError, TypeError) as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@require_POST
@login_required
def remove_item_from_shop(request, entry_id):
    entry = get_object_or_404(ShopItem, pk=entry_id)
    if entry.shop.world.creator != request.user:
        return JsonResponse({"status": "error", "message": "Нет прав"}, status=403)

    entry.delete()
    return JsonResponse({"status": "ok"})


@require_POST
@login_required
def buy_item_from_shop(request, item_id):
    try:
        shop = get_object_or_404(Shop, pk=request.POST.get('shop_id'))
        character = get_object_or_404(Character, pk=request.POST.get('character_id'), owner=request.user)
        entry = get_object_or_404(ShopItem, shop=shop, item_id=item_id)

        # Проверка доступности товара
        if entry.quantity is not None and entry.quantity <= 0:
            return JsonResponse({'status': 'error', 'message': 'Товар закончился'})

        # Расчет цены
        price = entry.price if entry.price is not None else entry.item.price
        final_price = int(price * shop.price_multiplier)

        # Проверка денег
        if character.gold < final_price:
            return JsonResponse({'status': 'error', 'message': 'Недостаточно золота'})

        # Процесс покупки
        with transaction.atomic():
            character.gold -= final_price
            character.save()

            InventoryItem.objects.update_or_create(
                character=character,
                item=entry.item,
                defaults={'quantity': F('quantity') + 1}
            )

            if entry.quantity is not None:
                entry.quantity = F('quantity') - 1
                entry.save()
                remaining = entry.quantity - 1
            else:
                remaining = None

        return JsonResponse({
            'status': 'ok',
            'message': f'Вы купили {entry.item.name} за {final_price} Ꞩ',
            'new_gold': character.gold,
            'remaining': remaining
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})
@require_POST
@login_required
def ajax_sell_item(request, character_id, item_id):
    if not request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse({"status": "error", "message": "Только AJAX"}, status=400)

    character = get_object_or_404(Character, id=character_id, owner=request.user)
    if not character.can_trade:
        return JsonResponse({"status": "error", "message": "Торговля недоступна."}, status=403)

    inv_entry = get_object_or_404(InventoryItem, character=character, item_id=item_id)
    if inv_entry.quantity < 1:
        return JsonResponse({"status": "error", "message": "Предмет отсутствует."}, status=400)

    # Расчёт цены
    from shops.utils.economy import get_sell_price
    price = get_sell_price(inv_entry.item, character)

    # Обновления
    inv_entry.quantity -= 1
    if inv_entry.quantity == 0:
        inv_entry.delete()
    else:
        inv_entry.save()

    character.gold += price
    character.save(update_fields=["gold"])

    return JsonResponse({
        "status": "ok",
        "message": f"Продан {inv_entry.item.name} за {price} Ꞩ",
        "item_id": item_id,
        "remaining": inv_entry.quantity if inv_entry.quantity > 0 else 0,
        "new_gold": character.gold,
    })
