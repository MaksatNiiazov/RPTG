from django.urls import path
from . import views
from .views import (
    LocationCreateView, LocationUpdateView, LocationDeleteView
)



app_name = "maps"

urlpatterns = [
    path('create/<int:world_id>/', LocationCreateView.as_view(), name='create'),
    path('<int:pk>/update/<int:world_id>/', LocationUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', LocationDeleteView.as_view(), name='delete'),
    path("<int:pk>/", views.map_view, name="map_view"),
]


