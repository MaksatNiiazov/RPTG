from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm

from .models import Rarity, Type, Item


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
class ItemAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm
    list_display = ("name", "type", "rarity", "bonus", "weight", "legendary_buff")
    list_filter = ("type", "rarity")
    list_editable = ("bonus", "weight","legendary_buff")
    search_fields = ("name", "bonus")
    prepopulated_fields = {"slug": ("name",)}
