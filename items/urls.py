from django.urls import path
from django.views.generic import TemplateView

from .views import RarityListView, TypeListView, ItemListView, LootConfigView, LootResultView

app_name = "items"

urlpatterns = [
    path('', TemplateView.as_view(template_name='items/items-main.html'), name='items_main'),
    path("rarities/", RarityListView.as_view(), name="rarity_list"),
    path("types/",     TypeListView.as_view(),    name="type_list"),
    path("list/",     ItemListView.as_view(),    name="item_list"),
    path("loot/config/", LootConfigView.as_view(), name="loot_config"),
    path("loot/result/", LootResultView.as_view(), name="loot_result"),
]
