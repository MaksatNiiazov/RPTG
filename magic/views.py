from django.views.generic import ListView, DetailView
from .models import Spell, School, SpellCategory


# Список всех школ
class SchoolListView(ListView):
    model = School
    template_name = "magic/school_list.html"
    context_object_name = "schools"
    paginate_by = 20


# Деталка школы (например, список спеллов в ней)
class SchoolDetailView(DetailView):
    model = School
    template_name = "magic/school_detail.html"
    context_object_name = "school"

    def get_context_data(self, **ctx):
        ctx = super().get_context_data(**ctx)
        ctx["spells"] = self.object.spell_set.order_by("level", "name")
        return ctx


# Список всех категорий
class CategoryListView(ListView):
    model = SpellCategory
    template_name = "magic/category_list.html"
    context_object_name = "categories"
    paginate_by = 20


# Деталка категории (спеллы заданного типа)
class CategoryDetailView(DetailView):
    model = SpellCategory
    template_name = "magic/category_detail.html"
    context_object_name = "category"

    def get_context_data(self, **ctx):
        ctx = super().get_context_data(**ctx)
        ctx["spells"] = self.object.spells.order_by("level", "name")
        return ctx


# Список спеллов с фильтрацией по школе и категории
class SpellListView(ListView):
    model = Spell
    template_name = "magic/spell_list.html"
    context_object_name = "spells"
    paginate_by = 30

    def get_queryset(self):
        qs = Spell.objects.select_related("school", "category")
        school = self.request.GET.get("school")
        category = self.request.GET.get("category")
        level = self.request.GET.get("level")
        if school:
            qs = qs.filter(school__slug=school)
        if category:
            qs = qs.filter(category__slug=category)
        if level:
            qs = qs.filter(level=level)
        return qs.order_by("level", "school__name", "name")

    def get_context_data(self, **ctx):
        ctx = super().get_context_data(**ctx)
        ctx["schools"] = School.objects.all()
        ctx["categories"] = SpellCategory.objects.all()
        ctx["levels"] = range(1, 10)
        return ctx


# Деталка одного спелла
class SpellDetailView(DetailView):
    model = Spell
    template_name = "magic/spell_detail.html"
    context_object_name = "spell"
