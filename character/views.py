from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView

from .forms import CharacterForm
from .models import Character


class CharacterCreateView(LoginRequiredMixin, CreateView):
    model = Character
    form_class = CharacterForm
    template_name = "characters/character_form.html"
    login_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        form.instance.account = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("characters:character_detail", kwargs={"pk": self.object.pk})

class CharacterDetailView(LoginRequiredMixin, DetailView):
    model = Character
    template_name = "characters/character_detail.html"
    context_object_name = "char"
    login_url = reverse_lazy("accounts:login")

    def get_queryset(self):
        # Смотрим только своих персонажей
        return Character.objects.filter(account=self.request.user)
