from django.urls import path
from .views import WorldDetailView, GMLootView, WorldCreateView

app_name = "worlds"

urlpatterns = [
    path("<int:pk>/", WorldDetailView.as_view(), name="detail"),
    path("create/", WorldCreateView.as_view(), name="create"),

    path(
        "<int:world_pk>/character/<int:char_pk>/gm-loot/",
        GMLootView.as_view(),
        name="gm_open_chest"
    ),

]
