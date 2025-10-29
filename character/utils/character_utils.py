from django.db import models


class CharacterGetUtils:
    """Набор оптимизированных методов для расчетов с учетом бонусов класса"""

    _stat_cache = {}

    def clear_cache(self):
        """Очистка кэша характеристик"""
        self._stat_cache.clear()

    def _get_class_bonus(self, attr_name, default=0):
        """Вспомогательный метод для получения бонуса класса"""
        return getattr(self.character_class, attr_name, default) if self.character_class else default

    # --- Основные характеристики с бонусами класса ---
    @property
    def effective_str(self):
        return self.str_stat + self._get_class_bonus('str_bonus')

    @property
    def effective_dex(self):
        return self.dex_stat + self._get_class_bonus('dex_bonus')

    @property
    def effective_con(self):
        return self.con_stat + self._get_class_bonus('con_bonus')

    @property
    def effective_int(self):
        return self.int_stat + self._get_class_bonus('int_bonus')

    @property
    def effective_wis(self):
        return self.wis_stat + self._get_class_bonus('wis_bonus')

    @property
    def effective_cha(self):
        return self.cha_stat + self._get_class_bonus('cha_bonus')

    @property
    def effective_acc(self):
        return self.acc_stat + self._get_class_bonus('acc_bonus')

    @property
    def effective_lck(self):
        return self.lck_stat + self._get_class_bonus('lck_bonus')

    # --- Боевые характеристики ---
    @property
    def max_hp(self):
        """Макс. HP с учетом бонуса класса"""
        return 10 + 10 * self.effective_con + self._get_class_bonus('hp_bonus')

    @property
    def get_concentration(self):
        """Макс. CP с учетом бонуса класса"""
        return self.effective_int - 5 + self._get_class_bonus('cp_bonus')

    @property
    def get_carry_capacity(self):
        return 10 + self.effective_str * 10

    @property
    def max_weapon_weight(self):
        return round(self.get_carry_capacity * 0.2, 1)

    @property
    def max_armor_weight(self):
        return round(self.get_carry_capacity * 0.5, 1)

    # --- Боевые расчеты ---
    @staticmethod
    def get_stat_roll_bonus(stat: int) -> int:
        return -2 if stat == 0 else -1 if stat == 1 else (stat // 2) - 1

    @property
    def total_defense(self):
        """Общая защита с учетом базовой брони класса"""
        cache_key = f'char_{self.id}_defense'
        if cache_key not in self._stat_cache:
            defense = self._get_class_bonus('default_armor', 0)
            armor_slots = ["head", "neck", "chest", "hands", "waist", "legs", "feet", "cloak"]

            if hasattr(self, "equipment"):
                defense += sum(
                    item.bonus for slot in armor_slots
                    if (item := getattr(self.equipment, slot)) is not None
                )

                if (shield := getattr(self.equipment, "off_hand")) and getattr(shield, 'equipment_slot', None) == "SHIELD":
                    defense += getattr(shield, 'bonus', 0)

            self._stat_cache[cache_key] = defense
        return self._stat_cache[cache_key]

    @property
    def total_attack(self):
        """Общий урон с учетом базового урона класса"""
        cache_key = f'char_{self.id}_attack'
        if cache_key not in self._stat_cache:
            attack = self._get_class_bonus('default_damage', 0) + self.effective_str

            if hasattr(self, "equipment"):
                weapon_slots = ["main_hand", "off_hand", "two_hands"]
                attack += sum(
                    item.bonus for slot in weapon_slots
                    if (item := getattr(self.equipment, slot)) is not None
                )

            self._stat_cache[cache_key] = attack
        return self._stat_cache[cache_key]

    @property
    def critical_hit(self):
        """Критический удар с учетом бонуса класса"""
        base = self.total_attack
        multiplier = 1 + (self.effective_str / 5) + (self._get_class_bonus('crit_multiplier_bonus', 0) / 100)
        return int(base * multiplier)

    # --- Тактические параметры ---
    @property
    def action_points(self):
        """Очки действий с учетом перегрузки"""
        base = self._get_class_bonus('action_count', 1)
        if self.effective_dex == 9:
            base += 1
        penalty = self.overload_penalties["actions"]
        return max(0, base - penalty)

    @property
    def possible_reactions(self):
        """Реакции с учетом перегрузки"""
        base = self._get_class_bonus('reaction_count', 1)
        if self.effective_wis >= 9:
            base += 1
        if self.effective_dex >= 7:
            base += 1
        penalty = self.overload_penalties["reactions"]
        return max(0, base - penalty)

    @property
    def possible_chain_attacks(self):
        """Цепные атаки с учетом перегрузки"""
        base = 0
        if self.effective_dex >= 8:
            base = 3
        elif self.effective_dex >= 4:
            base = 2
        elif self.effective_dex > 0:
            base = 1
        penalty = self.overload_penalties["chains"]
        return max(0, base - penalty)
    # --- Ресурсы ---
    @property
    def max_inspiration_tokens(self):
        if self.effective_cha == 0:
            return 0
        elif self.effective_cha <= 4:
            return 1
        elif self.effective_cha <= 6:
            return 2
        elif self.effective_cha <= 9:
            return 3
        return 4

    @property
    def max_precision_tokens(self):
        if self.effective_wis == 0:
            return 0
        elif self.effective_wis <= 4:
            return 1
        elif self.effective_wis <= 6:
            return 2
        elif self.effective_wis <= 8:
            return 3
        elif self.effective_wis <= 9:
            return 4
        return 5

    # --- Экипировка ---
    def can_wield_two_h_as_one(self):
        return self.effective_str >= 8

    def can_wield_2_two_h(self):
        return self.effective_str >= 10

    def get_legendary_bonuses(self):
        """
        Возвращает список легендарных бонусов от всех экипированных предметов.
        """
        bonuses = []
        if hasattr(self, "equipment"):
            for field in self.equipment._meta.fields:
                if isinstance(field, models.ForeignKey) and field.name != "character":
                    item = getattr(self.equipment, field.name)
                    if item and getattr(item, 'rarity', None) and getattr(item.rarity, 'legendary', False) and getattr(item, 'legendary_buff', None):
                        bonuses.append(item.legendary_buff)
        return bonuses

    def get_current_load(self, exclude_item=None) -> dict:
        """
        Возвращает информацию о текущей нагрузке персонажа.
        :param exclude_item: исключает указанный предмет из расчета (для валидации)
        """
        equipment_weight = 0
        if hasattr(self, "equipment"):
            equipment_weight = getattr(self.equipment, 'get_total_weight', lambda: 0)()

        # Считаем вес инвентаря, исключая указанный предмет если нужно
        inventory_weight = 0
        if hasattr(self, 'items'):
            for item in self.items.all():
                if item == exclude_item:
                    continue
                item_weight = getattr(getattr(item, 'item', None), 'weight', 0) or 0
                inventory_weight += item_weight * getattr(item, 'quantity', 1)

        total_weight = equipment_weight + inventory_weight
        carry_capacity = self.get_carry_capacity

        return {
            "equipment_weight": equipment_weight,
            "inventory_weight": inventory_weight,
            "total_weight": total_weight,
            "carry_capacity": carry_capacity,
            "is_overloaded": total_weight > carry_capacity,
            "overload_percentage": round((total_weight / carry_capacity) * 100, 1) if carry_capacity > 0 else 0,
        }

    @property
    def overload_penalties(self):
        """Штрафы от перегрузки"""
        overload = self.get_current_load().get("overload_percentage", 0)

        if overload <= 50:
            return {"actions": 0, "reactions": 0, "chains": 0}
        elif overload <= 100:
            return {"actions": 1, "reactions": 1, "chains": 1}
        elif overload <= 150:
            return {"actions": 2, "reactions": 2, "chains": 2}
        else:
            return {"actions": 99, "reactions": 99, "chains": 99}