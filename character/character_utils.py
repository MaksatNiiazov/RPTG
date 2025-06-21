import math

from django.db import models


class CharacterCalculationsMixin(models.Model):
    """Миксин для вычисления характеристик персонажа с учетом бонусов класса"""

    class Meta:
        abstract = True

    _stat_cache = {}

    def clear_cache(self):
        """Очистка кэша характеристик"""
        self._stat_cache.clear()

    def _get_class_bonus(self, attr_name, default=0):
        """Безопасное получение бонуса от класса"""
        if hasattr(self, 'character_class') and self.character_class:
            bonus = getattr(self.character_class, attr_name, default)
            return bonus() if callable(bonus) else bonus
        return default

    # --- Основные характеристики с бонусами класса ---
    @property
    def effective_str(self):
        """Сила с учетом бонусов класса"""
        base_stat = getattr(self, 'str_stat', 0) or 0
        class_bonus = self._get_class_bonus('str_bonus')
        return base_stat + (class_bonus if isinstance(class_bonus, (int, float)) else 0)

    @property
    def effective_dex(self):
        """Ловкость с учетом бонусов класса"""
        base_stat = getattr(self, 'dex_stat', 0) or 0
        class_bonus = self._get_class_bonus('dex_bonus')
        return base_stat + (class_bonus if isinstance(class_bonus, (int, float)) else 0)

    @property
    def effective_con(self):
        """Телосложение с учетом бонусов класса"""
        base_stat = getattr(self, 'con_stat', 0) or 0
        class_bonus = self._get_class_bonus('con_bonus')
        return base_stat + (class_bonus if isinstance(class_bonus, (int, float)) else 0)

    @property
    def effective_int(self):
        """Интеллект с учетом бонусов класса"""
        base_stat = getattr(self, 'int_stat', 0) or 0
        class_bonus = self._get_class_bonus('int_bonus')
        return base_stat + (class_bonus if isinstance(class_bonus, (int, float)) else 0)

    @property
    def effective_wis(self):
        """Мудрость с учетом бонусов класса"""
        base_stat = getattr(self, 'wis_stat', 0) or 0
        class_bonus = self._get_class_bonus('wis_bonus')
        return base_stat + (class_bonus if isinstance(class_bonus, (int, float)) else 0)

    @property
    def effective_cha(self):
        """Харизма с учетом бонусов класса"""
        base_stat = getattr(self, 'cha_stat', 0) or 0
        class_bonus = self._get_class_bonus('cha_bonus')
        return base_stat + (class_bonus if isinstance(class_bonus, (int, float)) else 0)

    @property
    def effective_acc(self):
        """Меткость с учетом бонусов класса"""
        base_stat = getattr(self, 'acc_stat', 0) or 0
        class_bonus = self._get_class_bonus('acc_bonus')
        return base_stat + (class_bonus if isinstance(class_bonus, (int, float)) else 0)

    @property
    def effective_lck(self):
        """Удача с учетом бонусов класса"""
        base_stat = getattr(self, 'lck_stat', 0) or 0
        class_bonus = self._get_class_bonus('lck_bonus')
        return base_stat + (class_bonus if isinstance(class_bonus, (int, float)) else 0)

    # --- Боевые характеристики ---
    @property
    def max_hp_calculated(self):
        """Макс. HP с учетом бонуса класса"""
        return 10 + 10 * self.effective_con + self._get_class_bonus('hp_bonus')

    @property
    def concentration_calculated(self):
        """Макс. CP с учетом бонуса класса"""
        return self.effective_int - 5 + self._get_class_bonus('cp_bonus')

    @property
    def carry_capacity_calculated(self):
        """Грузоподъемность"""
        return self.effective_str * 10

    @property
    def max_weapon_weight_calculated(self):
        """Макс. вес оружия"""
        return round(self.carry_capacity_calculated * 0.2, 1)

    @property
    def max_armor_weight_calculated(self):
        """Макс. вес брони"""
        return round(self.carry_capacity_calculated * 0.5, 1)

    # --- Боевые расчеты ---
    @staticmethod
    def get_stat_roll_bonus(stat: int) -> int:
        """Бонус к броску на основе характеристики"""
        if stat == 0: return -2
        if stat == 1: return -1
        return math.ceil(stat / 2) - 1

    @property
    def total_defense(self):
        """Общая защита с учетом брони"""
        cache_key = f'char_{self.id}_defense'
        if cache_key not in self._stat_cache:
            defense = self._get_class_bonus('default_armor')

            if hasattr(self, "equipment"):
                armor_slots = ["head", "neck", "chest", "hands", "waist", "legs", "feet", "cloak"]
                for slot in armor_slots:
                    item = getattr(self.equipment, slot, None)
                    if item and hasattr(item, 'bonus'):
                        defense += item.bonus

                shield = getattr(self.equipment, "off_hand", None)
                if shield and getattr(shield, 'equipment_slot', None) == "SHIELD":
                    defense += shield.bonus

            self._stat_cache[cache_key] = defense
        return self._stat_cache[cache_key]

    @property
    def total_attack(self):
        """Общий урон с учетом оружия"""
        cache_key = f'char_{self.id}_attack'
        if cache_key not in self._stat_cache:
            attack = self._get_class_bonus('default_damage') + self.effective_str

            if hasattr(self, "equipment"):
                weapon_slots = ["main_hand", "off_hand", "two_hands"]
                for slot in weapon_slots:
                    item = getattr(self.equipment, slot, None)
                    if item and hasattr(item, 'bonus'):
                        attack += item.bonus

            self._stat_cache[cache_key] = attack
        return self._stat_cache[cache_key]

    @property
    def critical_hit(self):
        """Критический удар"""
        base = self.total_attack
        multiplier = 1 + (self.effective_str / 5) + (self._get_class_bonus('crit_multiplier_bonus') / 100)
        return int(base * multiplier)

    # --- Тактические параметры ---
    @property
    def action_points(self):
        """Очки действий"""
        base_actions = self._get_class_bonus('action_count', default=1 if not hasattr(self,
                                                                                      'character_class') or not self.character_class else 0)
        dex_bonus = 1 if self.effective_dex == 10 else 0
        return max(base_actions + dex_bonus, 1)

    @property
    def possible_reactions(self):
        """Доступные реакции"""
        base_reactions = self._get_class_bonus('reaction_count', default=1 if not hasattr(self,
                                                                                          'character_class') or not self.character_class else 0)
        wis_bonus = 1 if self.effective_wis >= 7 else 0
        dex_bonus = 1 if self.effective_dex >= 7 else 0
        return max(base_reactions + wis_bonus + dex_bonus, 1)

    @property
    def possible_chain_attacks(self):
        """Цепные атаки"""
        if self.effective_dex == 0: return 0
        if self.effective_dex < 4: return 1
        if self.effective_dex < 8: return 2
        return 3

    # --- Ресурсы ---
    @property
    def max_inspiration_tokens(self):
        """Макс. токены вдохновения"""
        cha = self.effective_cha
        if cha == 0: return 0
        if cha <= 4: return 1
        if cha <= 6: return 2
        if cha <= 9: return 3
        return 4

    @property
    def max_precision_tokens(self):
        """Макс. токены точности"""
        wis = self.effective_wis
        if wis == 0: return 0
        if wis <= 4: return 1
        if wis <= 6: return 2
        if wis <= 8: return 3
        if wis <= 9: return 4
        return 5

    # --- Экипировка ---
    def can_wield_two_h_as_one(self):
        """Может использовать двуручное оружие одной рукой"""
        return self.effective_str >= 8

    def can_wield_2_two_h(self):
        """Может использовать два двуручных оружия"""
        return self.effective_str >= 10

    def get_legendary_bonuses(self):
        """Легендарные бонусы экипировки"""
        bonuses = []
        if hasattr(self, "equipment"):
            for field in self.equipment._meta.fields:
                if isinstance(field, models.ForeignKey) and field.name != "character":
                    item = getattr(self.equipment, field.name)
                    if item and getattr(item, 'rarity', None) and getattr(item.rarity, 'legendary', False) and hasattr(
                            item, 'legendary_buff'):
                        bonuses.append(item.legendary_buff)
        return bonuses