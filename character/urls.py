from django.urls import path

from .views import CharacterCreateView, CharacterDetailView, CharacterInventoryView, \
    UnequipSlotView, EquipItemView, DropItemView, LevelUpView, CharacterUpdateView, ChestDetailView, ToggleNpcFlagView, \
    AjaxAdjustHpView, AjaxAdjustCpView, AjaxAdjustTokenView, CharacterDeleteView, ClassListView, TalentListView

app_name = "characters"

urlpatterns = [
    path('classes/', ClassListView.as_view(), name='class_list'),
    path('talents/', TalentListView.as_view(), name='talent_list'),

    path("create/<int:world_pk>/", CharacterCreateView.as_view(), name="character_create"),
    path("update/<int:pk>/", CharacterUpdateView.as_view(), name='character_update'),
    path("<int:pk>/", CharacterDetailView.as_view(), name="character_detail"),
    path('characters/<int:pk>/delete/', CharacterDeleteView.as_view(), name='character_delete'),
    path("characters/<int:character_id>/inventory/", CharacterInventoryView.as_view(), name="character-inventory"),
    path("characters/<int:character_id>/equip/<int:item_id>/", EquipItemView.as_view(), name="equip-item"),
    path("characters/<int:character_id>/unequip/<str:slot>/", UnequipSlotView.as_view(), name="unequip-slot"),
    path("characters/<int:character_id>/drop/<int:item_id>/", DropItemView.as_view(), name="drop-item"),
    path('level-up/<int:character_id>/', LevelUpView.as_view(), name='level-up'),

    path('chest/<int:instance_pk>/', ChestDetailView.as_view(), name='chest-detail'),
    path('npc-settings/<int:char_id>/', ToggleNpcFlagView.as_view(), name='toggle-npc-flag'),
    path('characters/<int:pk>/adjust-hp/', AjaxAdjustHpView.as_view(), name='ajax_adjust_hp'),
    path('characters/<int:pk>/adjust-cp/', AjaxAdjustCpView.as_view(), name='ajax_adjust_cp'),
    path('character/<int:pk>/adjust-token/', AjaxAdjustTokenView.as_view(), name='ajax_adjust_token'),

]
