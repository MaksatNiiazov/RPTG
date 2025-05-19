from django.contrib import admin
from .models import School, SpellCategory, Spell


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(SpellCategory)
class SpellCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Spell)
class SpellAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "school", "category", "action_cost", "requires_check")
    list_filter = ("level", "school", "category", "action_cost")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}
