# catalog/loot.py

import random
from typing import List, Optional
from .models import Item, Rarity, Type

def generate_loot_items(
    luck: int,
    chest_rarity: int,
    count: int = 3,
    rare_count: int = 0,
    rare_rarity: Optional[Rarity] = None,
    type_bias: Optional[Type] = None,
    type_bias_count: int = 0
) -> List[Item]:
    """
    Генерирует список предметов с усиленным шансом редких:
    - Усиленный модификатор сундука (квадрат от (rarity+1))
    - Премия за предметы не ниже редкости сундука
    - Смягчённый базовый вес через экспоненту 0.9
    """
    all_items = list(Item.objects.select_related("type", "rarity"))
    if not all_items:
        return []

    loot: List[Item] = []

    # 1) Гарантированные редкие
    if rare_count and rare_rarity:
        pool = [i for i in all_items if i.rarity == rare_rarity]
        loot += random.choices(pool or all_items, k=rare_count)

    # 2) Гарантированные по типу
    if type_bias_count and type_bias:
        pool = [i for i in all_items if i.type == type_bias]
        loot += random.choices(pool or all_items, k=type_bias_count)

    # 3) Оставшиеся предметы
    remaining = count - len(loot)
    if remaining > 0:
        weights = []
        chest_mod = (chest_rarity + 1) ** 2      # усиление сундука
        luck_mod = 1 + (luck / 10)

        for item in all_items:
            r = item.rarity.lvl
            # чуть сглаживаем базовый вес
            base_w = (1 / (r + 1)) ** 0.9
            w = base_w * chest_mod * luck_mod

            # бонус, если rarity предмета >= chest_rarity
            if item.rarity.lvl >= chest_rarity:
                w *= 1.2

            # бонус по типу
            if type_bias and item.type == type_bias:
                w *= 1.5

            weights.append(w)

        loot += random.choices(all_items, weights=weights, k=remaining)

    random.shuffle(loot)
    return loot
