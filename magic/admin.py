from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from unfold.admin import ModelAdmin
from unfold.contrib.import_export.forms import ExportForm, ImportForm

from .models import School, SpellCategory, Spell


@admin.register(School)
class SchoolAdmin(ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(SpellCategory)
class SpellCategoryAdmin(ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Spell)
class SpellAdmin(ModelAdmin, ImportExportModelAdmin):
    import_form_class = ImportForm
    export_form_class = ExportForm
    list_display = ("name", "level", "school", "category", "action_cost", "description")
    list_filter = ("level", "school", "category", "action_cost")
    list_editable = ("level", "action_cost", "description")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
