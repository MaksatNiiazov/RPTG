from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

from accounts.models import User
from character.character_utils import CharacterGetUtils
from items.loot import generate_loot_items
from items.models import Item
from magic.models import Spell
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


class CharacterClass(models.Model):
    name = models.CharField("Название", max_length=100)
    description = models.TextField("Описание", blank=True, null=True)
    approve = models.BooleanField("Одобрено", default=False)
    action_count = models.PositiveSmallIntegerField("Количество действий", default=0)
    reaction_count = models.PositiveSmallIntegerField("Количество реакций", default=0)
    str_bonus = models.PositiveSmallIntegerField("Сила", default=0)
    dex_bonus = models.PositiveSmallIntegerField("Ловкость", default=0)
    con_bonus = models.PositiveSmallIntegerField("Телосложение", default=0)
    int_bonus = models.PositiveSmallIntegerField("Интеллект", default=0)
    wis_bonus = models.PositiveSmallIntegerField("Мудрость", default=0)
    cha_bonus = models.PositiveSmallIntegerField("Харизма", default=0)
    acc_bonus = models.PositiveSmallIntegerField("Меткость", default=0)
    lck_bonus = models.PositiveSmallIntegerField("Удача", default=0)
    hp_bonus = models.PositiveSmallIntegerField("Макс. HP", default=0)
    cp_bonus = models.PositiveSmallIntegerField("Макс. CP", default=0)
    default_armor = models.PositiveSmallIntegerField("Дефолтная броня", default=0)
    default_damage = models.PositiveSmallIntegerField("Дефолтный урон", default=0)
    crit_multiplier_bonus = models.PositiveSmallIntegerField("Множитель критического урона", default=0)
    base_ability_points = models.IntegerField("Базовые очки способностей", default=0)

    def __str__(self):
        return self.name


class Talent(models.Model):
    approve = models.BooleanField("Одобрено", default=False)
    name = models.CharField("Название", max_length=100)
    description = models.TextField("Описание", blank=True)

    def __str__(self):
        return self.name


class Character(models.Model, CharacterGetUtils):
    STAT_CHOICES = [
        ('str_stat', 'Сила'),
        ('dex_stat', 'Ловкость'),
        ('con_stat', 'Телосложение'),
        ('int_stat', 'Интеллект'),
        ('wis_stat', 'Мудрость'),
        ('cha_stat', 'Харизма'),
        ('acc_stat', 'Меткость'),
        ('lck_stat', 'Удача')
    ]

    GENDER_CHOICES = [('M', 'Мужской'), ('F', 'Женский'), ('O', 'Другой')]

    # Основные поля
    character_class = models.ForeignKey(CharacterClass, on_delete=models.CASCADE,
                                        related_name="characters", verbose_name="Класс", blank=True, null=True)
    character_talent = models.ForeignKey(Talent, on_delete=models.SET_NULL,
                                         related_name="characters", verbose_name="Талант",
                                         blank=True, null=True)
    world = models.ForeignKey(World, on_delete=models.CASCADE,
                              related_name="characters", verbose_name="Мир",
                              blank=True, null=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name="characters", verbose_name="Владелец",
                              blank=True, null=True)

    # Внешность и информация
    image = models.ImageField("Изображение", upload_to="characters/", blank=True, null=True)
    name = models.CharField("Имя", max_length=100)
    gender = models.CharField("Пол", max_length=1, choices=GENDER_CHOICES, blank=True)
    age = models.PositiveSmallIntegerField("Возраст", default=20)
    race = models.CharField("Раса", max_length=50, blank=True)
    background = models.TextField("Предыстория", blank=True)
    notes = models.TextField("Заметки (RP)", blank=True)

    # Статы
    str_stat = models.PositiveSmallIntegerField("Сила", default=0,
                                                validators=[MinValueValidator(0), MaxValueValidator(10)])
    dex_stat = models.PositiveSmallIntegerField("Ловкость", default=0,
                                                validators=[MinValueValidator(0), MaxValueValidator(10)])
    con_stat = models.PositiveSmallIntegerField("Телосложение", default=0,
                                                validators=[MinValueValidator(0), MaxValueValidator(10)])
    int_stat = models.PositiveSmallIntegerField("Интеллект", default=0,
                                                validators=[MinValueValidator(0), MaxValueValidator(10)])
    wis_stat = models.PositiveSmallIntegerField("Мудрость", default=0,
                                                validators=[MinValueValidator(0), MaxValueValidator(10)])
    cha_stat = models.PositiveSmallIntegerField("Харизма", default=0,
                                                validators=[MinValueValidator(0), MaxValueValidator(10)])
    acc_stat = models.PositiveSmallIntegerField("Меткость", default=0,
                                                validators=[MinValueValidator(0), MaxValueValidator(10)])
    lck_stat = models.PositiveSmallIntegerField("Удача", default=0,
                                                validators=[MinValueValidator(0), MaxValueValidator(10)])

    # Боевые параметры
    max_hp = models.PositiveIntegerField("Макс. HP", editable=False)
    current_hp = models.PositiveIntegerField("Текущие HP", default=0,
                                             validators=[MinValueValidator(0)])
    is_alive = models.BooleanField("Жив", default=True)
    concentration = models.IntegerField("CP", editable=False)
    current_concentration = models.IntegerField("Текущие CP", null=True, default=None)
    inspiration_tokens = models.PositiveSmallIntegerField("Токены вдохновения", default=0)
    precision_tokens = models.PositiveSmallIntegerField("Токены точности", default=0)

    # Инвентарь
    carry_capacity = models.PositiveIntegerField("Грузоподъёмность (кг)", editable=False)
    max_weapon_weight = models.FloatField("Макс. вес оружия", editable=False)
    max_armor_weight = models.FloatField("Макс. вес доспехов", editable=False)
    gold = models.PositiveIntegerField("Золото", default=0)

    # Системные поля
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ability_points = models.PositiveSmallIntegerField('Доступные очки прокачки', default=0)

    # Флаги NPC
    is_npc = models.BooleanField("NPC", default=False)
    visible_to_players = models.BooleanField(
        "NPC видим всем игрокам", default=False,
        help_text="Если включено, NPC появится в списке у всех игроков"
    )

    # Флаги знаний об NPC
    known_name = models.BooleanField("Игроки знают имя", default=False)
    known_background = models.BooleanField("Игроки знают предысторию", default=False)
    known_stats = models.BooleanField("Игроки знают статы", default=False)
    known_equipment = models.BooleanField("Игроки знают экипировку", default=False)
    known_notes = models.BooleanField("Игроки знают заметки", default=False)

    # Заклинания
    spells = models.ManyToManyField(
        Spell,
        verbose_name="Выученные заклинания",
        blank=True,
        related_name="casters"
    )

    class Meta:
        verbose_name = "Персонаж"
        verbose_name_plural = "Персонажи"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({'NPC' if self.is_npc else 'PC'})"

    def save(self, *args, **kwargs):
        self.max_hp = 10 + 10 * self.con_stat
        self.concentration = self.int_stat - 5

        if self.current_concentration is None:
            self.current_concentration = self.concentration

        self.carry_capacity = self.str_stat * 10
        self.max_weapon_weight = round(self.carry_capacity * 0.2, 1)
        self.max_armor_weight = round(self.carry_capacity * 0.5, 1)

        # Автоматическая проверка жив/мертв
        if self.current_hp <= 0 and self.is_alive:
            self.die(silent=True)
        elif self.current_hp > 0 and not self.is_alive:
            self.is_alive = True

        super().save(*args, **kwargs)

    def clean(self):
        """Валидация модели"""
        super().clean()

        # Устанавливаем значения по умолчанию для None
        current_hp = self.current_hp if self.current_hp is not None else 0
        con_stat = self.con_stat if self.con_stat is not None else 0
        int_stat = self.int_stat if self.int_stat is not None else 0
        max_hp = self.max_hp if self.max_hp is not None else 0
        character_class = self.character_class

        # Проверка HP
        if max_hp is not None and current_hp > max_hp:
            raise ValidationError(
                f"Текущее HP ({current_hp}) не может превышать максимальное ({max_hp})"
            )

        # Проверка концентрации
        if self.current_concentration is not None:
            # Вычисляем максимальную концентрацию с проверкой на None
            class_cp_bonus = character_class.cp_bonus if character_class and character_class.cp_bonus is not None else 0
            max_cp = (int_stat * 2) + class_cp_bonus

            if max_cp is not None and self.current_concentration > max_cp:
                raise ValidationError(
                    f"Текущая концентрация ({self.current_concentration}) не может превышать максимум ({max_cp})"
                )
    def die(self, silent=False):
        """Помечает персонажа как мертвого"""
        if not self.is_alive:
            return

        self.is_alive = False
        if not silent:
            self.save(update_fields=['is_alive'])

    def lvlup(self, stat: str, points: int = 1):
        """Улучшение характеристики"""
        if stat not in dict(self.STAT_CHOICES):
            raise ValidationError("Неизвестная характеристика")

        if self.ability_points < points:
            raise ValidationError("Недостаточно очков прокачки")

        setattr(self, stat, getattr(self, stat) + points)
        self.ability_points -= points
        self.save()

    def adjust_hp(self, delta: int) -> int:
        """Изменение HP с автоматической проверкой смерти"""
        self.current_hp = max(0, min(self.current_hp + delta, self.max_hp))

        if self.current_hp <= 0:
            self.die()
        elif self.current_hp > 0 and not self.is_alive:
            self.is_alive = True

        self.save(update_fields=['current_hp', 'is_alive'])
        return self.current_hp

    def adjust_cp(self, action: str) -> int:
        """Изменение концентрации"""
        if action not in ('inc', 'dec'):
            raise ValidationError("Действие должно быть 'inc' или 'dec'")

        delta = 1 if action == 'inc' else -1
        self.current_concentration = max(-5, min(self.current_concentration + delta, self.concentration))
        self.save(update_fields=['current_concentration'])
        return self.current_concentration

    # Методы экипировки
    def can_wield_two_h_as_one(self):
        return self.str_stat >= 8

    def can_wield_2_two_h(self):
        return self.str_stat >= 10

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
        if chosen_slot == "two_hands" and (equipment.main_hand or equipment.off_hand):
            raise ValidationError(
                "Нельзя надеть двуручное оружие в режиме two_hands, "
                "пока руки заняты."
            )
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

    def add_inspiration_token(self):
        """Добавить токен вдохновения с проверкой максимума"""
        if self.inspiration_tokens < self.max_inspiration_tokens:
            self.inspiration_tokens += 1
            self.save(update_fields=['inspiration_tokens'])
            return True
        return False

    def spend_inspiration_token(self):
        """Потратить токен вдохновения"""
        if self.inspiration_tokens > 0:
            self.inspiration_tokens -= 1
            self.save(update_fields=['inspiration_tokens'])
            return True
        return False

    def add_precision_token(self):
        """Добавить токен точности с проверкой максимума"""
        if self.precision_tokens < self.max_precision_tokens:
            self.precision_tokens += 1
            self.save(update_fields=['precision_tokens'])
            return True
        return False

    def spend_precision_token(self):
        """Потратить токен точности"""
        if self.precision_tokens > 0:
            self.precision_tokens -= 1
            self.save(update_fields=['precision_tokens'])
            return True
        return False


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


class ChestInstance(models.Model):
    """
    Живой сундук, выданный ГМом конкретному персонажу.
    После того как игрок забрал всё — запись удаляется.
    """
    # config = models.ForeignKey(ChestConfig, ...)  -- убрал
    character = models.ForeignKey(
        Character,
        on_delete=models.CASCADE,
        related_name='chests',
        verbose_name="Персонаж",
    )
    items = models.ManyToManyField(
        'items.Item',
        verbose_name="Содержимое сундука",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Сундук → {self.character.name} ({self.created_at:%Y-%m-%d %H:%M})"

    @classmethod
    def create_for_character(cls, *, character, **loot_kwargs):
        """
        На лету генерим лут и создаём инстанс.
        Все аргументы передаются дальше в generate_loot_items.
        """
        from items.loot import generate_loot_items
        loot = generate_loot_items(**loot_kwargs)
        inst = cls.objects.create(character=character)
        inst.items.set(loot)
        return inst
