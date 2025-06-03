from django.contrib import admin
from .models import Location, MapToken
from unfold.admin import ModelAdmin

@admin.register(Location)
class LocationAdmin(ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(MapToken)
class MapTokenAdmin(ModelAdmin):
    list_display = ("label", "location", "owner", "x", "y", "color", "is_gm_only")
    list_filter = ("location", "is_gm_only")
    search_fields = ("label",)
