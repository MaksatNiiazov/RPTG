from django.db import models

from items.models import Item
from worlds.models import World


# Create your models here.

class Shop(models.Model):
    name = models.CharField("Название", max_length=100)
    world = models.ForeignKey(World, on_delete=models.CASCADE, related_name="shops")
    price_multiplier = models.FloatField("Множитель цен", default=1.0)
    is_open = models.BooleanField("Открыт", default=False)

    def __str__(self):
        return self.name


class ShopItem(models.Model):
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField("Количество", null=True, blank=True)  # null = бесконечно
    price = models.PositiveIntegerField("Цена", default=0)

    class Meta:
        unique_together = ('shop', 'item')

    def __str__(self):
        return f"{self.item.name} (×{self.quantity or '∞'})"

    def is_available(self):
        return self.quantity is None or self.quantity > 0

    def get_final_price(self):
        return round(self.price * self.shop.price_multiplier) if self.price else round(self.item.price * self.shop.price_multiplier)