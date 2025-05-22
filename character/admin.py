# characters/admin.py

from django.contrib import admin
from .models import Character, Inventory, InventoryItem, EquippedItem
from unfold.admin import ModelAdmin, TabularInline


class InventoryItemInline(TabularInline):
    model = InventoryItem
    extra = 1
    verbose_name = "Позиция в инвентаре"
    verbose_name_plural = "Позиции в инвентаре"
    fields = ("item", "quantity")
    autocomplete_fields = ("item",)


class EquippedItemInline(TabularInline):
    model = EquippedItem
    extra = 0
    verbose_name = "Надетый предмет"
    verbose_name_plural = "Надетые предметы"
    fields = ("slot", "item", "equipped_at")
    readonly_fields = ("equipped_at",)
    autocomplete_fields = ("item",)


@admin.register(Inventory)
class InventoryAdmin(ModelAdmin):
    list_display = ("character",)
    search_fields = ("character__name",)
    inlines = (InventoryItemInline, EquippedItemInline)


@admin.register(Character)
class CharacterAdmin(ModelAdmin):
    list_display = (
        "world",
        "name", "race", "gender",
        "str_stat", "dex_stat", "con_stat", "int_stat",
        "carry_capacity", "max_weapon_weight", "max_armor_weight",
    )
    list_display_links = ("name",)
    readonly_fields = (
        "max_hp", "concentration", "carry_capacity",
        "max_weapon_weight", "max_armor_weight",
    )
    list_filter = ("race", "gender", "world",
                   )
    search_fields = ("name",)
    fieldsets = (
        (None, {
            "fields": ("world",
                       "name", "gender", "race")
        }),
        ("RP-данные", {
            "fields": ("background", "notes"),
            "classes": ("collapse",),
        }),
        ("Характеристики", {
            "fields": (
                ("str_stat", "dex_stat", "con_stat", "int_stat"),
                ("wis_stat", "cha_stat", "acc_stat", "lck_stat"),
            )
        }),
        ("Производные", {
            "fields": (
                "max_hp", "current_hp", "concentration",
                "carry_capacity", "max_weapon_weight", "max_armor_weight",
            )
        }),
    )
    inlines = ()  # Управление инвентарём через отдельный раздел InventoryAdmin

# (Если нужно, можно зарегистрировать InventoryItem и EquippedItem отдельно)
# admin.site.register(InventoryItem)
# admin.site.register(EquippedItem)
