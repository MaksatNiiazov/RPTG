from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Shop, ShopItem


# ===============================
# INLINE: Товары в магазине
# ===============================

class ShopItemInline(TabularInline):
    model = ShopItem
    extra = 0

    fields = (
        "item",
        "quantity",
        "price",
        "final_price_display",
        "availability_display",
    )

    readonly_fields = (
        "final_price_display",
        "availability_display",
    )

    def final_price_display(self, obj):
        return obj.get_final_price()
    final_price_display.short_description = "Итоговая цена"

    def availability_display(self, obj):
        return "∞" if obj.quantity == 0 else obj.quantity
    availability_display.short_description = "В наличии"


# ===============================
# SHOP ADMIN
# ===============================

@admin.register(Shop)
class ShopAdmin(ModelAdmin):
    list_display = (
        "name",
        "world",
        "is_open",
        "price_multiplier",
        "items_count",
    )

    list_filter = (
        "world",
        "is_open",
    )

    search_fields = (
        "name",
    )

    inlines = (ShopItemInline,)

    def items_count(self, obj):
        return obj.items.count()
    items_count.short_description = "Товаров"


# ===============================
# SHOP ITEM ADMIN
# ===============================

@admin.register(ShopItem)
class ShopItemAdmin(ModelAdmin):
    list_display = (
        "item",
        "shop",
        "quantity_display",
        "price",
        "final_price_display",
    )

    list_filter = (
        "shop",
    )

    search_fields = (
        "item__name",
    )

    readonly_fields = (
        "final_price_display",
    )

    def quantity_display(self, obj):
        return "∞" if obj.quantity == 0 else obj.quantity
    quantity_display.short_description = "Количество"

    def final_price_display(self, obj):
        return obj.get_final_price()
    final_price_display.short_description = "Итоговая цена"
