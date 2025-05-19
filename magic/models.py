from django.db import models
from django.utils.text import slugify
from unidecode import unidecode


class School(models.Model):
    name = models.CharField("Название школы", max_length=50, unique=True)
    slug = models.SlugField("URL-имя", max_length=50, unique=True, blank=True)

    class Meta:
        verbose_name = "Школа магии"
        verbose_name_plural = "Школы магии"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(unidecode(self.name))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class SpellCategory(models.Model):
    """
    Категория заклинания: Урон, Лечение, Контроль и т.д.
    """
    name = models.CharField("Категория", max_length=50, unique=True)
    slug = models.SlugField("URL-имя", max_length=50, unique=True, blank=True)

    class Meta:
        verbose_name = "Категория заклинания"
        verbose_name_plural = "Категории заклинаний"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(unidecode(self.name))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Spell(models.Model):
    LEVEL_CHOICES = [(i, str(i)) for i in range(1, 11)]
    TYPE_CHOICES = [
        ("BA", "Bonus Action"),
        ("1A", "1 Action"),
        ("2A", "2 Actions"),
        ("3A", "3 Actions (Charge)"),
        ("REA", "Reaction"),
    ]

    name = models.CharField("Название", max_length=100)
    slug = models.SlugField("URL-имя", max_length=100, unique=True, blank=True)
    school = models.ForeignKey(School, verbose_name="Школа", on_delete=models.PROTECT)
    category = models.ForeignKey(
        SpellCategory, verbose_name="Тип заклинания",
        on_delete=models.PROTECT, related_name="spells"
    )
    level = models.PositiveSmallIntegerField("Уровень", choices=LEVEL_CHOICES)
    action_cost = models.CharField("Тип действия", max_length=3, choices=TYPE_CHOICES)
    requires_check = models.BooleanField("Нужен Concentration Check", default=False)
    description = models.TextField("Эффект заклинания")

    class Meta:
        verbose_name = "Заклинание"
        verbose_name_plural = "Заклинания"
        ordering = ["level", "school__name", "name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(unidecode(self.name))
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.level}] {self.name}"
