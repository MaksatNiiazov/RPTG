from django.contrib import admin
from .models import World
from unfold.admin import ModelAdmin
# Register your models here.

@admin.register(World)
class WorldAdmin(ModelAdmin):
    filter_horizontal = ("players",)

