from django.db import models
from accounts.models import User


class Location(models.Model):
    name = models.CharField("Название локации", max_length=100)
    description = models.TextField("Описание", blank=True)
    image = models.ImageField("Карта локации", upload_to="locations/")

    def __str__(self):
        return self.name


class MapToken(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Игрок", null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='tokens')
    label = models.CharField("Подпись", max_length=100, blank=True)
    x = models.FloatField("X (%)", help_text="Позиция по горизонтали, в процентах")
    y = models.FloatField("Y (%)", help_text="Позиция по вертикали, в процентах")
    color = models.CharField("Цвет токена", max_length=7, default="#ff0000", help_text="Цвет в формате #rrggbb")
    is_gm_only = models.BooleanField("Только для ГМа", default=False)

    def __str__(self):
        return self.label or f"Токен #{self.pk}"
