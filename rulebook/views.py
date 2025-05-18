# docs/views.py
from django.shortcuts import get_object_or_404, render
from django.views.generic import ListView, DetailView
from .models import Folder, Article

class FolderListView(ListView):
    """
    Отображает дерево всех папок.
    """
    model = Folder
    template_name = "folder_list.html"
    context_object_name = "folders"

class ArticleListView(ListView):
    """
    Список статей в конкретной папке.
    """
    model = Article
    template_name = "article_list.html"
    context_object_name = "articles"

    def get_queryset(self):
        self.folder = get_object_or_404(Folder, slug=self.kwargs["slug"])
        return Article.objects.filter(folder=self.folder).order_by("order")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["folder"] = self.folder
        return ctx

class ArticleDetailView(DetailView):
    """
    Детальная страница статьи.
    """
    model = Article
    template_name = "article_detail.html"
    context_object_name = "article"
    slug_field = "slug"
    slug_url_kwarg = "slug"
