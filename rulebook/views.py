# docs/views.py

from django.shortcuts import get_object_or_404, render, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView

from .forms import SuggestionForm
from .models import Folder, Article, ImprovementProposal


class FolderListView(ListView):
    """
    Отображает дерево всех папок.
    """
    model = Folder
    template_name = "rulebook/folder_list.html"
    context_object_name = "folders"


class ArticleListView(ListView):
    """
    Список статей в конкретной папке.
    """
    model = Article
    template_name = "rulebook/article_list.html"
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
    template_name = "rulebook/article_detail.html"
    context_object_name = "article"
    slug_field = "slug"
    slug_url_kwarg = "slug"



class SuggestionView(View):
    """
    Обрабатывает POST из инклюда SuggestionForm.
    При успехе — редирект обратно с параметром ?suggestion=ok
    """
    def post(self, request, *args, **kwargs):
        form = SuggestionForm(request.POST)
        if not form.is_valid():
            # возвращаем тот же include с ошибками
            return render(request, "suggestions/suggestion_form.html", {"form": form})

        cd = form.cleaned_data
        # создаём предложение
        ImprovementProposal.objects.create(
            article=(None if not cd["article_slug"]
                     else ImprovementProposal._meta.get_field("article").related_model.objects.get(slug=cd["article_slug"])),
            suggestion=cd["suggestion"],
            submitter_name=cd["submitter_name"],
            submitter_email=cd["submitter_email"],
            submitted_at=timezone.now(),
        )
        # редирект обратно и сигнал успеха
        referer = request.META.get("HTTP_REFERER", "/")
        sep = "&" if "?" in referer else "?"
        return redirect(f"{referer}{sep}suggestion=ok")