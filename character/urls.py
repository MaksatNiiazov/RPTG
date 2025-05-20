from django.urls import path
from .views import CharacterCreateView, CharacterDetailView

app_name = "characters"

urlpatterns = [
    path("create/", CharacterCreateView.as_view(), name="character_create"),
    path("<int:pk>/", CharacterDetailView.as_view(), name="character_detail"),
]
