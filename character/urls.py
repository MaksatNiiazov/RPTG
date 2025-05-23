from django.urls import path
from .views import CharacterCreateView, CharacterDetailView, ManageKnowledgeView, PickLootView, CharacterInventoryView, \
    UnequipSlotView, EquipItemView, DropItemView, LevelUpView

app_name = "characters"

urlpatterns = [
    path("create/<int:world_pk>/", CharacterCreateView.as_view(), name="character_create"),
    path("<int:pk>/", CharacterDetailView.as_view(), name="character_detail"),
    path("<int:char_pk>/manage_knowledge/", ManageKnowledgeView.as_view(), name="manage_knowledge"),
    path("pick-loot/", PickLootView.as_view(), name="pick_loot_list"),
    # Обработчик выбора конкретного сундука:
    path("pick-loot/<int:loot_pk>/", PickLootView.as_view(), name="pick_loot"),
    path("characters/<int:character_id>/inventory/", CharacterInventoryView.as_view(), name="character-inventory"),
    path("characters/<int:character_id>/equip/<int:item_id>/", EquipItemView.as_view(), name="equip-item"),
    path("characters/<int:character_id>/unequip/<str:slot>/", UnequipSlotView.as_view(), name="unequip-slot"),
    path("characters/<int:character_id>/drop/<int:item_id>/", DropItemView.as_view(), name="drop-item"),
    path('level-up/<int:character_id>/', LevelUpView.as_view(), name='level-up'),

]
