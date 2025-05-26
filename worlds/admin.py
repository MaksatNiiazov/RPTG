from django.contrib import admin
from .models import World, WorldInvitation
from unfold.admin import ModelAdmin



@admin.register(World)
class WorldAdmin(ModelAdmin):
    filter_horizontal = ("players",)


@admin.register(WorldInvitation)
class WorldInvitationAdmin(ModelAdmin):
    pass
