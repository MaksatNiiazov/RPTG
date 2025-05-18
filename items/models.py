# catalog/models.py
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify
from unidecode import unidecode


class Rarity(models.Model):
    name = models.CharField("Название редкости", max_length=50)
    lvl = models.PositiveIntegerField("Уровень редкости", unique=True)
    legendary = models.BooleanField("Легендарная", default=False)
    slug = models.SlugField("URL-имя", max_length=50, unique=True, blank=True)
    color = models.CharField("Цвет", max_length=7, default="#000000")

    class Meta:
        verbose_name = "Редкость"
        verbose_name_plural = "Редкости"
        ordering = [ "lvl"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(unidecode(self.name))[:50]
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} (ур. {self.lvl})"


class Type(models.Model):
    name = models.CharField("Название типа", max_length=50)
    slug = models.SlugField("URL-имя", max_length=50, unique=True, blank=True)
    rarity = models.ForeignKey(
        Rarity, verbose_name="Редкость",
        related_name="types", on_delete=models.PROTECT
    )

    class Meta:
        verbose_name = "Тип предмета"
        verbose_name_plural = "Типы предметов"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(unidecode(self.name))[:50]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Item(models.Model):
    name = models.CharField("Название предмета", max_length=50)
    slug = models.SlugField("URL-имя", max_length=60, unique=True, blank=True)
    type = models.ForeignKey(
        Type, verbose_name="Тип предмета",
        related_name="items", on_delete=models.PROTECT
    )
    rarity = models.ForeignKey(
        Rarity, verbose_name="Редкость",
        related_name="items", on_delete=models.PROTECT
    )
    bonus = models.PositiveIntegerField("Бонус", default=0)
    weight = models.PositiveIntegerField("Вес", default=0)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Обновлено", auto_now=True)

    legendary_buff = models.CharField("Легендарный бонус", max_length=200, null=True, blank=True, default=None)

    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"
        ordering = ["type__name", "name"]
        unique_together = (("type", "name"),)  # в рамках одного типа имена не дублируются

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(unidecode(self.name))[:60]
        super().save(*args, **kwargs)

    def clean(self):
        if self.rarity.legendary and not self.legendary_buff:
            raise ValidationError("Поле 'Легендарный бонус' обязательно для легендарных предметов.")
        if not self.rarity.legendary and self.legendary_buff:
            raise ValidationError("Поле 'Легендарный бонус' не может быть заполнено для обычных предметов.")

    def __str__(self):
        return self.name
