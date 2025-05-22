# characters/admin.py

from django.contrib import admin
from .models import Character, InventoryItem, Equipment
from unfold.admin import ModelAdmin, TabularInline, StackedInline


class InventoryItemInline(TabularInline):
    model = InventoryItem
    extra = 1
    verbose_name = "Позиция в инвентаре"
    verbose_name_plural = "Позиции в инвентаре"
    fields = ("item", "quantity")
    autocomplete_fields = ("item",)


class EquipmentInline(StackedInline):
    model = Equipment
    extra = 0
    verbose_name = "Экипировка"
    verbose_name_plural = "Экипировка"

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
    inlines = (InventoryItemInline, EquipmentInline)  # Управление инвентарём через отдельный раздел InventoryAdmin

# (Если нужно, можно зарегистрировать InventoryItem и EquippedItem отдельно)
# admin.site.register(InventoryItem)
# admin.site.register(EquippedItem)
