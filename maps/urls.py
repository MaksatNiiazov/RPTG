from django.urls import path
from . import views

app_name = "maps"

urlpatterns = [
    path("<int:pk>/", views.map_view, name="map_view"),
]
