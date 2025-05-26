from django.urls import path

from .views import CharacterCreateView, CharacterDetailView, CharacterInventoryView, \
    UnequipSlotView, EquipItemView, DropItemView, LevelUpView, CharacterUpdateView, ChestDetailView, ToggleNpcFlagView

app_name = "characters"

urlpatterns = [
    path("create/<int:world_pk>/", CharacterCreateView.as_view(), name="character_create"),
    path("update/<int:pk>/", CharacterUpdateView.as_view(), name='character_update'),
    path("<int:pk>/", CharacterDetailView.as_view(), name="character_detail"),
    path("characters/<int:character_id>/inventory/", CharacterInventoryView.as_view(), name="character-inventory"),
    path("characters/<int:character_id>/equip/<int:item_id>/", EquipItemView.as_view(), name="equip-item"),
    path("characters/<int:character_id>/unequip/<str:slot>/", UnequipSlotView.as_view(), name="unequip-slot"),
    path("characters/<int:character_id>/drop/<int:item_id>/", DropItemView.as_view(), name="drop-item"),
    path('level-up/<int:character_id>/', LevelUpView.as_view(), name='level-up'),

    path('chest/<int:instance_pk>/', ChestDetailView.as_view(), name='chest-detail'),
    path('npc-settings/<int:char_id>/', ToggleNpcFlagView.as_view(), name='toggle-npc-flag'),


]
