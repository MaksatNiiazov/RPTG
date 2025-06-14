# accounts/models.py

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group, Permission
from django.db import models
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField("Email", unique=True)
    first_name = models.CharField("Имя", max_length=30, blank=True)
    last_name = models.CharField("Фамилия", max_length=30, blank=True)
    is_staff = models.BooleanField("Статус персонала", default=False)
    is_active = models.BooleanField("Активен", default=True)
    date_joined = models.DateTimeField("Дата регистрации", auto_now_add=True)

    # Переопределяем группы и права с уникальными related_name
    groups = models.ManyToManyField(
        Group,
        verbose_name="Группы",
        blank=True,
        related_name="accounts_user_set",  # <-- своё related_name
        related_query_name="accounts_user"
    )
    user_permissions = models.ManyToManyField(
        Permission,
        verbose_name="Права пользователя",
        blank=True,
        related_name="accounts_user_permissions",  # <-- своё related_name
        related_query_name="accounts_user_perm"
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.email

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
