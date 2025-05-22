# worlds/models.py

from django.db import models
from items.models import Item

from accounts.models import User


class World(models.Model):
    """
    Сессия — мир, в котором играют персонажи.
    """
    creator = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="created_worlds",
        verbose_name="Гейм-мастер",
        blank=True,
        null=True
    )
    players = models.ManyToManyField(
        User,
        related_name="worlds",
        verbose_name="Участники",
        blank=True
    )
    name = models.CharField("Название мира", max_length=100, unique=True)
    setting = models.CharField("Сеттинг", max_length=200, blank=True,
                               help_text="Краткое описание мира")
    history = models.TextField("История мира", blank=True,
                               help_text="Подробное описание предыстории и ключевых событий")
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        verbose_name = "Мир"
        verbose_name_plural = "Миры"
        ordering = ["name"]

    def __str__(self):
        return self.name


class WorldItemPool(models.Model):
    """
    Запас каждого предмета в рамках конкретного мира.
    Если remaining=None — неограниченно, иначе — сколько штук осталось.
    """
    world = models.ForeignKey(
        World, on_delete=models.CASCADE,
        related_name="item_pools", verbose_name="Мир"
    )
    item = models.ForeignKey(
        Item, on_delete=models.PROTECT,
        related_name="+", verbose_name="Предмет"
    )
    remaining = models.PositiveIntegerField(
        "Осталось в мире", null=True, blank=True,
        help_text="NULL = без ограничений; число = остаток"
    )

    class Meta:
        unique_together = ("world", "item")
        verbose_name = "Пул предметов мира"
        verbose_name_plural = "Пулы предметов мира"
        ordering = ["world__name", "item__name"]

    def save(self, *args, **kwargs):
        # при первом сохранении, если remaining не задан, берём из item.initial_quantity
        if self.pk is None and self.remaining is None:
            self.remaining = self.item.initial_quantity
        super().save(*args, **kwargs)

    def __str__(self):
        qty = "∞" if self.remaining is None else self.remaining
        return f"{self.world.name}: {self.item.name} ({qty})"


class PendingLoot(models.Model):
    """
    Лут, открытый ГМом для конкретного персонажа, ждущий выбора.
    """
    world = models.ForeignKey(World, on_delete=models.CASCADE, related_name="pending_loots")
    character = models.ForeignKey(
        'character.Character',
        on_delete=models.CASCADE, related_name="pending_loots"
    )
    items = models.ManyToManyField(Item, verbose_name="Сгенерированные предметы")
    created_at = models.DateTimeField(auto_now_add=True)
    picked_up = models.BooleanField("Забран игроком", default=False)

    class Meta:
        verbose_name = "Ожидаемый лут"
        verbose_name_plural = "Ожидаемые луты"

    def __str__(self):
        return f"Loot {self.pk} → {self.character.name}"
