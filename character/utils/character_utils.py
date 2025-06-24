from django.db import models


class CharacterGetUtils:
    """Набор оптимизированных методов для расчетов с учетом бонусов класса"""

    _stat_cache = {}

    def clear_cache(self):
        """Очистка кэша характеристик"""
        self._stat_cache.clear()

    # --- Основные характеристики с бонусами класса ---
    @property
    def effective_str(self):
        return self.str_stat + self.character_class.str_bonus

    @property
    def effective_dex(self):
        return self.dex_stat + self.character_class.dex_bonus

    @property
    def effective_con(self):
        return self.con_stat + self.character_class.con_bonus

    @property
    def effective_int(self):
        return self.int_stat + self.character_class.int_bonus

    @property
    def effective_wis(self):
        return self.wis_stat + self.character_class.wis_bonus

    @property
    def effective_cha(self):
        return self.cha_stat + self.character_class.cha_bonus

    @property
    def effective_acc(self):
        return self.acc_stat + self.character_class.acc_bonus

    @property
    def effective_lck(self):
        return self.lck_stat + self.character_class.lck_bonus

    # --- Боевые характеристики ---
    @property
    def max_hp(self):
        """Макс. HP с учетом бонуса класса"""
        return 10 + 10 * self.effective_con + self.character_class.hp_bonus

    @property
    def concentration(self):
        """Макс. CP с учетом бонуса класса"""
        return self.effective_int - 5 + self.character_class.cp_bonus

    @property
    def carry_capacity(self):
        return self.effective_str * 10

    @property
    def max_weapon_weight(self):
        return round(self.carry_capacity * 0.2, 1)

    @property
    def max_armor_weight(self):
        return round(self.carry_capacity * 0.5, 1)

    # --- Боевые расчеты ---
    @staticmethod
    def get_stat_roll_bonus(stat: int) -> int:
        return -2 if stat == 0 else -1 if stat == 1 else (stat // 2) - 1

    @property
    def total_defense(self):
        """Общая защита с учетом базовой брони класса"""
        cache_key = f'char_{self.id}_defense'
        if cache_key not in self._stat_cache:
            defense = self.character_class.default_armor
            armor_slots = ["head", "neck", "chest", "hands", "waist", "legs", "feet", "cloak"]

            if hasattr(self, "equipment"):
                defense += sum(
                    item.bonus for slot in armor_slots
                    if (item := getattr(self.equipment, slot)) is not None
                )

                if (shield := getattr(self.equipment, "off_hand")) and shield.equipment_slot == "SHIELD":
                    defense += shield.bonus

            self._stat_cache[cache_key] = defense
        return self._stat_cache[cache_key]

    @property
    def total_attack(self):
        """Общий урон с учетом базового урона класса"""
        cache_key = f'char_{self.id}_attack'
        if cache_key not in self._stat_cache:
            attack = self.character_class.default_damage + self.effective_str

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
        multiplier = 1 + (self.effective_str / 5) + (self.character_class.crit_multiplier_bonus / 100)
        return int(base * multiplier)

    # --- Тактические параметры ---
    @property
    def action_points(self):
        """Очки действий с учетом класса"""
        return self.character_class.action_count + (1 if self.effective_dex == 10 else 0)

    @property
    def possible_reactions(self):
        """Реакции с учетом класса"""
        return self.character_class.reaction_count + (1 if self.effective_wis >= 7 else 0) + (
            1 if self.effective_dex >= 7 else 0)

    @property
    def possible_chain_attacks(self):
        if self.effective_dex == 0:
            return 0
        elif self.effective_dex < 4:
            return 1
        elif self.effective_dex < 8:
            return 2
        return 3

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
                    if item and item.rarity.legendary and item.legendary_buff:
                        bonuses.append(item.legendary_buff)
        return bonuses
