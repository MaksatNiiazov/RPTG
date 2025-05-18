from django.contrib import admin
from .models import Rarity, Type, Item
from unfold.admin import ModelAdmin


@admin.register(Rarity)
class RarityAdmin(ModelAdmin):
    list_display = ("name", "lvl", "legendary", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Type)
class TypeAdmin(ModelAdmin):
    list_display = ("name", "rarity", "slug")
    list_filter = ("rarity",)
    list_editable = ("rarity",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Item)
class ItemAdmin(ModelAdmin):
    list_display = ("name", "type", "rarity", "bonus", "created_at")
    list_filter = ("type", "rarity")
    list_editable = ("type", "rarity", "bonus",)
    search_fields = ("name", "bonus")
    prepopulated_fields = {"slug": ("name",)}
