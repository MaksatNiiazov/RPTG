from django.urls import path
from django.views.generic import TemplateView

from .views import (
    SchoolListView, SchoolDetailView,
    CategoryListView, CategoryDetailView,
    SpellListView, SpellDetailView
)

app_name = "magic"

urlpatterns = [
    path('', TemplateView.as_view(template_name='magic/magic-main.html'), name='magic_main'),
    # Школы
    path("schools/", SchoolListView.as_view(), name="school_list"),
    path("schools/<slug:slug>/", SchoolDetailView.as_view(), name="school_detail"),

    # Категории
    path("categories/", CategoryListView.as_view(), name="category_list"),
    path("categories/<slug:slug>/", CategoryDetailView.as_view(), name="category_detail"),

    # Спеллы
    path("spells/", SpellListView.as_view(), name="spell_list"),
    path("spell/<slug:slug>/", SpellDetailView.as_view(), name="spell_detail"),
]
