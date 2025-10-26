# characters/admin.py

from django.contrib import admin
from .models import Character, InventoryItem, Equipment, CharacterClass, Talent, HomeInventoryItem
from unfold.admin import ModelAdmin, TabularInline, StackedInline


@admin.register(Talent)
class TalentAdmin(ModelAdmin):
    list_display = ("name", "approve")
    list_editable = ("approve",)


@admin.register(CharacterClass)
class CharacterClassAdmin(ModelAdmin):
    list_display = ("name", "approve")
    list_editable = ("approve",)


class InventoryItemInline(TabularInline):
    model = InventoryItem
    extra = 1
    verbose_name = "Позиция в инвентаре"
    verbose_name_plural = "Позиции в инвентаре"
    fields = ("item", "quantity")
    autocomplete_fields = ("item",)


class HomeInventoryItemInline(TabularInline):
    model = HomeInventoryItem
    extra = 0
    verbose_name = "Предмет в хранилище"
    verbose_name_plural = "Домашнее хранилище"
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
        "name",
        "is_npc",
        "race", "gender",
        "str_stat", "dex_stat", "con_stat", "int_stat",
        "carry_capacity", "max_weapon_weight", "max_armor_weight", "can_trade", "home_storage_enabled"
    )
    list_display_links = ("name",)
    readonly_fields = (
        "max_hp", "concentration", "carry_capacity",
        "max_weapon_weight", "max_armor_weight",
    )
    list_filter = ("race", "gender", "world", "is_npc", "world",)
    list_editable = ("can_trade", "home_storage_enabled")
    search_fields = ("name",)
    fieldsets = (
        (None, {
            "fields": ("owner", "world",
                       'image',
                       "name", "gender", "race", "character_class", "character_talent", "is_alive", "can_trade", "home_storage_enabled")
        }),
        ("RP-данные", {
            "fields": ("background", "notes"),
            "classes": ("collapse",),
        }),
        ("Характеристики", {
            "fields": (
                ("ability_points", "str_stat", "dex_stat", "con_stat", "int_stat"),
                ("wis_stat", "cha_stat", "acc_stat", "lck_stat"),
            )
        }),
        ("Производные", {
            "fields": (
                "max_hp", "current_hp", "concentration",
                "carry_capacity", "max_weapon_weight", "max_armor_weight",
            )
        }),
        ("Поля для НПС", {
            "fields": (
                "is_npc", "visible_to_players", "known_name", "known_background", "known_notes", "known_equipment",
                "known_stats"
            )
        }),

    )
    inlines = (InventoryItemInline, HomeInventoryItemInline, EquipmentInline)  # Управление инвентарём через отдельный раздел InventoryAdmin
