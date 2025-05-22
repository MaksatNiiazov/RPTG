# characters/models.py

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils import timezone
from items.models import Item
from accounts.models import User
from worlds.models import World


class Character(models.Model):
    world = models.ForeignKey(World, on_delete=models.CASCADE, related_name="characters", verbose_name="Мир",
                              blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="characters", verbose_name="Владелец",
                              blank=True, null=True)
    GENDER_CHOICES = [('M', 'Мужской'), ('F', 'Женский'), ('O', 'Другой')]

    name = models.CharField("Имя", max_length=100)
    gender = models.CharField("Пол", max_length=1, choices=GENDER_CHOICES, blank=True)
    race = models.CharField("Раса", max_length=50, blank=True)
    background = models.TextField("Предыстория", blank=True)
    notes = models.TextField("Заметки (RP)", blank=True)

    # Статы 1–10
    str_stat = models.PositiveSmallIntegerField("Сила", default=1)
    dex_stat = models.PositiveSmallIntegerField("Ловкость", default=1)
    con_stat = models.PositiveSmallIntegerField("Телосложение", default=1)
    int_stat = models.PositiveSmallIntegerField("Интеллект", default=1)
    wis_stat = models.PositiveSmallIntegerField("Мудрость", default=1)
    cha_stat = models.PositiveSmallIntegerField("Харизма", default=1)
    acc_stat = models.PositiveSmallIntegerField("Меткость", default=1)
    lck_stat = models.PositiveSmallIntegerField("Удача", default=1)

    # Производные
    max_hp = models.PositiveIntegerField("Макс. HP", editable=False)
    current_hp = models.PositiveIntegerField("Текущие HP", default=0)
    concentration = models.PositiveSmallIntegerField("CP", editable=False)
    carry_capacity = models.PositiveIntegerField("Грузоподъёмность (кг)", editable=False)
    max_weapon_weight = models.FloatField("Макс. вес оружия", editable=False)
    max_armor_weight = models.FloatField("Макс. вес доспехов", editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    knows = models.ManyToManyField(
        'self', symmetrical=False,
        related_name='known_by',
        blank=True,
        verbose_name="Знает"
    )

    def save(self, *args, **kwargs):
        # HP и CP
        self.max_hp = 10 + 10 * self.con_stat
        self.current_hp = self.current_hp or self.max_hp
        self.concentration = self.int_stat
        # Грузоподъёмность
        self.carry_capacity = self.str_stat * 10
        # Ограничения по весу
        self.max_weapon_weight = round(self.carry_capacity * 0.2, 1)
        self.max_armor_weight = round(self.carry_capacity * 0.5, 1)
        super().save(*args, **kwargs)

    def can_wield_two_h_as_one(self):
        # Сильные персонажи (STR ≥ 8) могут использовать 2H как main_hand
        return self.str_stat >= 8

    def has_inventory(self):
        return Inventory.objects.filter(character=self).exists()

    def create_inventory(self):
        return Inventory.objects.create(character=self)

    def __str__(self):
        return self.name


class Inventory(models.Model):
    character = models.OneToOneField(
        Character, on_delete=models.CASCADE, related_name="inventory"
    )

    class Meta:
        verbose_name = "Инвентарь"
        verbose_name_plural = "Инвентари"

    def __str__(self):
        return f"Инвентарь {self.character.name}"

    def equip_item(self, item):
        # Проверка: есть ли в инвентаре
        inv_item = InventoryItem.objects.filter(inventory=self, item=item).first()
        if not inv_item or inv_item.quantity < 1:
            raise ValidationError("Предмет отсутствует в инвентаре.")

        # Нельзя экипировать неэкипируемые предметы
        if item.equipment_slot == 'OTR':
            raise ValidationError(f"{item.name} нельзя экипировать.")

        # Запрет повторной экипировки
        if EquippedItem.objects.filter(inventory=self, item=item).exists():
            raise ValidationError(f"{item.name} уже экипирован.")

        et = item.equipment_slot
        slots = [et]

        # Особые типы предметов
        if et == '2H' and self.character.can_wield_two_h_as_one():
            slots.append('main_hand')
        elif et == 'RING':
            slots = ['ring_left', 'ring_right']
        elif et == 'DAG':
            slots = ['main_hand', 'off_hand']

        # Найти свободный слот
        chosen = None
        for slot in slots:
            if not EquippedItem.objects.filter(inventory=self, slot=slot).exists():
                chosen = slot
                break

        if not chosen:
            raise ValidationError(f"Нет свободного слота из {slots} для {item.name}.")

        # Конфликт: уже экипировано двуручное
        if chosen in ('main_hand', 'off_hand'):
            if EquippedItem.objects.filter(inventory=self, slot='two_hands').exists():
                raise ValidationError("Уже экипировано двуручное оружие.")

        # Конфликт: экипировка 2H, но руки заняты
        if et == '2H':
            if chosen == 'two_hands':
                if EquippedItem.objects.filter(inventory=self, slot__in=['main_hand', 'off_hand']).exists():
                    raise ValidationError("Руки заняты — снимите main_hand или off_hand.")
            elif chosen == 'main_hand':
                if EquippedItem.objects.filter(inventory=self, slot='off_hand').exists():
                    raise ValidationError("Левая рука занята — невозможно использовать двуручное оружие в правой руке.")

        # Ограничение: нельзя надеть одинаковые кольца
        if et == 'RING':
            if EquippedItem.objects.filter(inventory=self, item=item, slot__in=['ring_left', 'ring_right']).exists():
                raise ValidationError(f"{item.name} уже надето как кольцо.")

        # Ограничение: только один легендарный предмет (если нужно)
        # if item.rarity.legendary and self.equipped.filter(item__rarity__legendary=True).exists():
        #     raise ValidationError("Можно носить только один легендарный предмет.")

        # Проверка веса
        w = item.weight
        char = self.character

        if chosen in ('main_hand', 'off_hand', 'two_hands') and w > char.max_weapon_weight:
            raise ValidationError(f"{item.name} слишком тяжёлое для оружия (> {char.max_weapon_weight} кг).")

        if chosen in ('HEAD', 'NECK', 'CHEST', 'HAND', 'WAIST', 'LEGS', 'FEET', 'CLOAK') and w > char.max_armor_weight:
            raise ValidationError(f"{item.name} слишком тяжёлое для доспехов (> {char.max_armor_weight} кг).")

        projected_weight = self.get_total_weight() + item.weight
        if projected_weight > char.carry_capacity:
            raise ValidationError(
                f"Экипировка превысит грузоподъёмность персонажа ({projected_weight} > {char.carry_capacity} кг)."
            )

        # Надеваем
        with transaction.atomic():
            inv_item.quantity -= 1
            if inv_item.quantity == 0:
                inv_item.delete()
            else:
                inv_item.save()

            eq = EquippedItem.objects.create(inventory=self, item=item, slot=chosen)

        return eq

    def unequip_slot(self, slot):
        eq = EquippedItem.objects.filter(inventory=self, slot=slot).first()
        if not eq:
            raise ValidationError(f"Слот {slot} пуст.")
        with transaction.atomic():
            eq.delete()
            inv, created = InventoryItem.objects.get_or_create(
                inventory=self, item=eq.item, defaults={'quantity': 1}
            )
            if not created:
                inv.quantity += 1
                inv.save()

    def drop_item(self, item, quantity=1):
        inv_item = InventoryItem.objects.filter(inventory=self, item=item).first()
        if not inv_item or inv_item.quantity < quantity:
            raise ValidationError("Недостаточно предметов.")
        inv_item.quantity -= quantity
        if inv_item.quantity == 0:
            inv_item.delete()
        else:
            inv_item.save()

    def transfer_item(self, target_inventory, item, quantity=1):
        inv_item = InventoryItem.objects.filter(inventory=self, item=item).first()
        if not inv_item or inv_item.quantity < quantity:
            raise ValidationError("Недостаточно предметов.")
        with transaction.atomic():
            inv_item.quantity -= quantity
            if inv_item.quantity == 0:
                inv_item.delete()
            else:
                inv_item.save()
            tgt, created = InventoryItem.objects.get_or_create(
                inventory=target_inventory, item=item, defaults={'quantity': quantity}
            )
            if not created:
                tgt.quantity += quantity
                tgt.save()

    def get_total_weight(self):
        """
        Общий вес всех предметов в инвентаре и экипировке.
        """
        weight = sum(i.item.weight * i.quantity for i in self.items.select_related('item'))
        weight += sum(e.item.weight for e in self.equipped.select_related('item'))
        return weight


class InventoryItem(models.Model):
    inventory = models.ForeignKey(
        Inventory, on_delete=models.CASCADE, related_name="items"
    )
    item = models.ForeignKey(
        'items.Item', on_delete=models.CASCADE, related_name='+'
    )
    quantity = models.PositiveIntegerField("Кол-во", default=1)

    class Meta:
        verbose_name = "Позиция в инвентаре"
        verbose_name_plural = "Позиции в инвентаре"
        unique_together = ('inventory', 'item')

    def __str__(self):
        return f"{self.inventory.character.name}: {self.quantity}× {self.item.name}"


class EquippedItem(models.Model):
    SLOT_CHOICES = [
        ("HEAD", "Шлем / Головной убор"),
        ("NECK", "Ожерелье / Амулет"),
        ("CHEST", "Нагрудник / Доспех"),
        ("HAND", "Перчатки / Наручи"),
        ("WAIST", "Пояс"),
        ("LEGS", "Наголенники / Поножи"),
        ("FEET", "Ботинки / Сапоги"),
        ("RING", "Кольцо"),
        ("CLOAK", "Плащ / Накидка"),
        ("SHIELD", "Щит"),
        ("1H", "Одноручное оружие"),
        ("2H", "Двуручное оружие"),
        ("DAG", "Кинжал"),
        ("BOW", "Лук"),
        ("XBW", "Арбалет"),
        ("STAFF", "Посох"),
        ("WAND", "Жезл"),
        ("ORB", "Сфера / Фокус"),
        ("OFFH", "Доп. в руке (торговый фонарь и т.д.)"),
        ("OTR", "Прочее"),
    ]

    inventory = models.ForeignKey(
        Inventory, on_delete=models.CASCADE, related_name="equipped"
    )
    item = models.ForeignKey(
        'items.Item', on_delete=models.CASCADE, related_name='+'
    )
    slot = models.CharField("Слот", max_length=12, choices=SLOT_CHOICES)
    equipped_at = models.DateTimeField("Надето в", default=timezone.now)

    class Meta:
        verbose_name = "Надетый предмет"
        verbose_name_plural = "Надетые предметы"
        unique_together = ('inventory', 'slot')

    def clean(self):
        if self.slot.upper() != self.item.equipment_slot:
            raise ValidationError(f"Нельзя надеть {self.item.name} в слот {self.get_slot_display()}.")
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.inventory.character.name}: {self.get_slot_display()} → {self.item.name}"
