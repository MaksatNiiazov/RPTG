from django.db import models


class CharacterGetUtils:
    @staticmethod
    def get_stat_roll_bonus(stat: int) -> int:

        if stat == 0:
            return -2
        elif stat == 1:
            return -1
        else:
            return int((stat // 2) - 1)

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
        total += self.str_stat
        return total

    def get_critical_hit(self):
        base_damage = self.get_total_attack()
        multiplier = 1 + self.str_stat / 5  # плавный рост урона
        return int(base_damage * multiplier)

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

    def get_action_points(self):
        points = 3

        if self.dex_stat == 10:
            points += 1

        return points

    def get_possible_chain_attacks(self):
        if self.dex_stat == 0:
            return 0
        elif 0 < self.dex_stat < 4:
            return 1
        elif 4 < self.dex_stat < 8:
            return 2
        elif self.dex_stat > 8:
            return 3

    def get_possible_reactions(self):
        reactions = 1
        if self.wis_stat >= 7:
            reactions += 1
        if self.dex_stat >= 7:
            reactions += 1
        return reactions

    def get_max_inspiration_tokens(self):
        if self.char_stat == 0:
            return 0
        elif self.char_stat <= 4:
            return 1
        elif self.char_stat <= 6:
            return 2
        elif self.char_stat <= 9:
            return 3
        elif self.char_stat == 10:
            return 4

    def precision_surge_tokens(self):
        if self.char_stat == 0:
            return 0
        elif self.char_stat <= 4:
            return 1
        elif self.char_stat <= 6:
            return 2
        elif self.char_stat <= 8:
            return 3
        elif self.char_stat <= 9:
            return 4
        elif self.char_stat == 10:
            return 5

    def get_some(self):
        pass

