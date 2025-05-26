from django.urls import path
from .views import WorldDetailView, GMLootView, WorldCreateView, GrantAbilityPointsView, GrantItemView

app_name = "worlds"

urlpatterns = [
    path("<int:pk>/", WorldDetailView.as_view(), name="detail"),
    path("create/", WorldCreateView.as_view(), name="create"),

    path(
        "<int:world_pk>/character/<int:char_pk>/gm-loot/",
        GMLootView.as_view(),
        name="gm_open_chest"
    ),
    path(
        "world/<int:world_pk>/character/<int:char_pk>/grant-points/",
        GrantAbilityPointsView.as_view(),
        name="world-grant-points"
    ),
    path(
        "world/<int:world_pk>/character/<int:char_pk>/grant-item/",
        GrantItemView.as_view(),
        name="world-grant-item"
    ),

]
