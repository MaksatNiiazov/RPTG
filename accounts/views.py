from django.contrib import messages
from django.contrib.auth import login, logout
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, RedirectView, TemplateView

from character.models import Character
from worlds.models import World
from .forms import RegisterForm, LoginForm


class RegisterView(CreateView):
    form_class = RegisterForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("accounts:login")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Регистрация прошла успешно! Войдите, пожалуйста.")
        return response


class LoginView(FormView):
    form_class = LoginForm
    template_name = "accounts/login.html"
    success_url = reverse_lazy("accounts:profile")

    def form_valid(self, form):
        login(self.request, form.get_user())
        messages.success(self.request, f"Добро пожаловать, {self.request.user.first_name or self.request.user.email}!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Неправильные данные входа.")
        print(form.cleaned_data)
        print(form.errors)
        return super().form_invalid(form)

    def get(self, request, *args, **kwargs):
        # если уже залогинен, сразу на профиль
        if request.user.is_authenticated:
            return redirect(self.get_success_url())
        return super().get(request, *args, **kwargs)


class LogoutView(RedirectView):
    pattern_name = "accounts:login"

    def get(self, request, *args, **kwargs):
        logout(request)
        messages.info(request, "Вы вышли из системы.")
        return super().get(request, *args, **kwargs)


class ProfileView(TemplateView):
    template_name = "accounts/profile.html"

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        user = self.request.user
        print(user)
        ctx["user"] = user
        ctx["worlds"] = World.objects.filter(players=user).exclude(creator=user)
        ctx["created_worlds"] = World.objects.filter(creator=user)
        return ctx


