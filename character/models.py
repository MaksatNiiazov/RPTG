from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import User
from items.models import Item
from worlds.models import World

EQUIPMENT_SLOT_MAP = {
    "HEAD": "head",
    "NECK": "neck",
    "CHEST": "chest",
    "HAND": "hands",
    "WAIST": "waist",
    "LEGS": "legs",
    "FEET": "feet",
    "CLOAK": "cloak",
    "RING": ["ring_left", "ring_right"],
    "SHIELD": "off_hand",
    "1H": "main_hand",
    "2H": ["two_hands", "main_hand"],  # в зависимости от силы
    "DAG": ["main_hand", "off_hand"],
    "WAND": "main_hand",
    "ORB": "off_hand",
    "OFFH": "off_hand",
    "BOW": "two_hands",
    "XBW": "two_hands",
    "STAFF": "two_hands",
}


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

    max_hp = models.PositiveIntegerField("Макс. HP", editable=False)
    current_hp = models.PositiveIntegerField("Текущие HP", default=0)
    concentration = models.PositiveSmallIntegerField("CP", editable=False)
    carry_capacity = models.PositiveIntegerField("Грузоподъёмность (кг)", editable=False)
    max_weapon_weight = models.FloatField("Макс. вес оружия", editable=False)
    max_armor_weight = models.FloatField("Макс. вес доспехов", editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    knows = models.ManyToManyField('self', symmetrical=False, related_name='known_by', blank=True, verbose_name="Знает")

    def save(self, *args, **kwargs):
        self.max_hp = 10 + 10 * self.con_stat
        self.current_hp = self.current_hp or self.max_hp
        self.concentration = self.int_stat
        self.carry_capacity = self.str_stat * 10
        self.max_weapon_weight = round(self.carry_capacity * 0.2, 1)
        self.max_armor_weight = round(self.carry_capacity * 0.5, 1)
        super().save(*args, **kwargs)

    def can_wield_two_h_as_one(self):
        return self.str_stat >= 8

    def can_wield_2_two_h(self):
        return self.str_stat >= 10

    def get_total_defense(self):
        """
        Общая броня — сумма бонусов от экипированных доспехов и щита.
        """
        armor_slots = ["head", "neck", "chest", "hands", "waist", "legs", "feet", "cloak"]
        total = 0

        if hasattr(self, "equipment"):
            for slot in armor_slots:
                item = getattr(self.equipment, slot, None)
                if item:
                    total += item.bonus

            # Добавляем бонус от щита, если он есть
            shield_item = getattr(self.equipment, "off_hand", None)
            if shield_item and shield_item.equipment_slot == "SHIELD":
                total += shield_item.bonus

        return total

    def get_total_attack(self):
        """
        Общий урон — сумма бонусов от экипированного оружия.
        """
        weapon_slots = ["main_hand", "off_hand", "two_hands"]
        total = 0
        if hasattr(self, "equipment"):
            for slot in weapon_slots:
                item = getattr(self.equipment, slot, None)
                if item:
                    total += item.bonus
        return total

    def get_legendary_bonuses(self):
        """
        Возвращает список легендарных бонусов от всех экипированных предметов.
        """
        bonuses = []
        if hasattr(self, "equipment"):
            for field in self.equipment._meta.fields:
                if isinstance(field, models.ForeignKey) and field.name != "character":
                    item = getattr(self.equipment, field.name)
                    if item and item.rarity.legendary and item.legendary_buff:
                        bonuses.append(item.legendary_buff)
        return bonuses

    def equip_item(self, item):
        # Проверка наличия в инвентаре
        inv_entry = self.items.filter(item=item).first()
        if not inv_entry or inv_entry.quantity < 1:
            raise ValidationError("У персонажа нет такого предмета в инвентаре.")

        if item.equipment_slot == "OTR":
            raise ValidationError("Этот предмет нельзя экипировать.")

        if not hasattr(self, "equipment"):
            Equipment.objects.create(character=self)

        equipment = self.equipment
        equip_key = item.equipment_slot

        # Ищем свободные слоты в зависимости от типа экипировки
        slot_candidates = []

        if equip_key == "2H":
            equipped_2h = [
                s for s in ["main_hand", "off_hand", "two_hands"]
                if getattr(equipment, s) and getattr(equipment, s).equipment_slot == "2H"
            ]
            if len(equipped_2h) >= 2:
                raise ValidationError("Нельзя экипировать более двух двуручных предметов.")

            if len(equipped_2h) == 1 and not self.can_wield_2_two_h():
                raise ValidationError("STR недостаточно для второго двуручного оружия (нужно ≥ 10).")

            # Распределение
            if self.can_wield_2_two_h():
                if equipment.main_hand is None:
                    slot_candidates.append("main_hand")
                if equipment.off_hand is None:
                    slot_candidates.append("off_hand")
                if equipment.two_hands is None:
                    slot_candidates.append("two_hands")
            elif self.can_wield_two_h_as_one():
                if equipment.main_hand is None:
                    slot_candidates.append("main_hand")
                elif equipment.two_hands is None:
                    slot_candidates.append("two_hands")
            else:
                if equipment.two_hands is None:
                    slot_candidates.append("two_hands")

        elif equip_key in ["1H", "DAG"]:
            if equipment.main_hand is None:
                slot_candidates.append("main_hand")
            if equipment.off_hand is None:
                slot_candidates.append("off_hand")

        elif equip_key == "RING":
            if equipment.ring_left is None:
                slot_candidates.append("ring_left")
            if equipment.ring_right is None:
                slot_candidates.append("ring_right")
            if equipment.ring_left == item or equipment.ring_right == item:
                raise ValidationError("Такое кольцо уже надето.")

        else:
            slot = EQUIPMENT_SLOT_MAP.get(equip_key)
            if not slot:
                raise ValidationError(f"Неизвестный слот для экипировки: {equip_key}")
            if getattr(equipment, slot) is None:
                slot_candidates.append(slot)

        if not slot_candidates:
            raise ValidationError(f"Нет свободного слота для экипировки {item.name}.")

        # Конфликты
        if "two_hands" in slot_candidates and not self.can_wield_2_two_h():
            if equipment.main_hand or equipment.off_hand:
                raise ValidationError("Нельзя экипировать: руки заняты.")

        if any(s in slot_candidates for s in ["main_hand", "off_hand"]):
            if equipment.two_hands:
                raise ValidationError("Нельзя экипировать: уже есть двуручное оружие.")

        # Проверка по весу
        total_weight = self.equipment.get_total_weight() + item.weight
        if total_weight > self.carry_capacity:
            raise ValidationError("Грузоподъёмность превышена.")

        if any(s in slot_candidates for s in ["main_hand", "off_hand", "two_hands"]):
            if item.weight > self.max_weapon_weight:
                raise ValidationError("Слишком тяжёлое оружие.")

        if any(s in slot_candidates for s in [
            "head", "neck", "chest", "hands", "waist", "legs", "feet", "cloak"
        ]):
            if item.weight > self.max_armor_weight:
                raise ValidationError("Слишком тяжёлый доспех.")

        # Экипировка в первый подходящий слот
        chosen_slot = slot_candidates[0]
        setattr(equipment, chosen_slot, item)
        equipment.save()

        # Обновление инвентаря
        inv_entry.quantity -= 1
        if inv_entry.quantity == 0:
            inv_entry.delete()
        else:
            inv_entry.save()

        return chosen_slot

    def unequip_slot(self, slot: str):
        """
        Снимает предмет из указанного слота экипировки и возвращает его в инвентарь.
        """
        if not hasattr(self, "equipment"):
            raise ValidationError("У персонажа нет экипировки.")

        equipment = self.equipment

        # Получим список допустимых слотов
        valid_slots = [
            f.name for f in equipment._meta.fields
            if isinstance(f, models.ForeignKey) and f.name != "character"
        ]

        if slot not in valid_slots:
            raise ValidationError(f"Слот '{slot}' не существует.")

        item = getattr(equipment, slot)

        if item is None:
            raise ValidationError(f"Слот '{slot}' уже пуст.")

        # Возвращаем в инвентарь
        inventory_entry, created = self.items.get_or_create(item=item)
        if not created:
            inventory_entry.quantity += 1
            inventory_entry.save()

        # Очищаем слот
        setattr(equipment, slot, None)
        equipment.save()

        return item

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='+')
    quantity = models.PositiveIntegerField("Кол-во", default=1)

    class Meta:
        verbose_name = "Позиция в инвентаре"
        verbose_name_plural = "Позиции в инвентаре"

    def __str__(self):
        return f"{self.character.name}: {self.quantity}× {self.item.name}"


class Equipment(models.Model):
    character = models.OneToOneField(Character, on_delete=models.CASCADE, related_name="equipment")

    head = models.ForeignKey(Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
                             verbose_name="Голова")
    neck = models.ForeignKey(Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
                             verbose_name="Шея")
    chest = models.ForeignKey(Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
                              verbose_name="Грудь")
    hands = models.ForeignKey(Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
                              verbose_name="Руки")
    waist = models.ForeignKey(Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
                              verbose_name="Пояс")
    legs = models.ForeignKey(Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
                             verbose_name="Ноги")
    feet = models.ForeignKey(Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
                             verbose_name="Ступни")
    cloak = models.ForeignKey(Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
                              verbose_name="Плащ")

    ring_left = models.ForeignKey(Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
                                  verbose_name="Кольцо 1")
    ring_right = models.ForeignKey(Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
                                   verbose_name="Кольцо 2")

    main_hand = models.ForeignKey(Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
                                  verbose_name="Оружие")
    off_hand = models.ForeignKey(Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
                                 verbose_name="Второе оружие")
    two_hands = models.ForeignKey(Item, null=True, blank=True, on_delete=models.SET_NULL, related_name='+',
                                  verbose_name="Двуручное оружие")

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Экипировка"
        verbose_name_plural = "Экипировка"

    def __str__(self):
        return f"Экипировка {self.character.name}"

    def get_total_weight(self) -> float:
        total = 0
        for field in self._meta.fields:
            if isinstance(field, models.ForeignKey):
                item = getattr(self, field.name)
                if item and hasattr(item, "weight") and item.weight is not None:
                    total += item.weight
        return total

    def get_equipped_items(self) -> dict:
        equipped = {}
        for field in self._meta.fields:
            if isinstance(field, models.ForeignKey) and field.name != 'inventory':
                item = getattr(self, field.name)
                if item:
                    equipped[field.name] = item
        return equipped
