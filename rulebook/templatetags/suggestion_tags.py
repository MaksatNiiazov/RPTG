from django import template
from rulebook.forms import SuggestionForm

register = template.Library()


@register.inclusion_tag("suggestion_form.html", takes_context=True)
def suggestion_form(context, article_slug=""):
    """
    Рендерит форму предложения.
    Если передаётся article_slug, подставляет его в скрытое поле.
    """
    request = context["request"]
    # Если в GET есть ?suggestion=ok, передадим флаг успеха
    success = request.GET.get("suggestion") == "ok"
    # Инициализируем форму
    form = SuggestionForm(initial={"article_slug": article_slug})
    return {
        "form": form,
        "success": success,
    }
