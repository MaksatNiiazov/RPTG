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
    Генерирует общий пул предметов:
      - count всего
      - rare_count из rare_rarity (если указан)
      - type_bias_count из type_bias (если указан)
    Остальные (count - rare_count - type_bias_count) ― обычным алгоритмом.
    """
    # Общий список
    all_items = list(Item.objects.select_related("type", "rarity"))
    if not all_items:
        return []

    loot = []

    # 1) Сначала редкие, если заданы
    if rare_count and rare_rarity:
        pool = [i for i in all_items if i.rarity == rare_rarity]
        loot += random.choices(pool or all_items, k=rare_count)

    # 2) Типовые, если заданы
    if type_bias_count and type_bias:
        pool = [i for i in all_items if i.type == type_bias]
        loot += random.choices(pool or all_items, k=type_bias_count)

    # 3) Остальные
    remaining = count - len(loot)
    if remaining > 0:
        # рассчитываем веса для всего списка
        weights = []
        for item in all_items:
            r = item.rarity.lvl
            base_w = 1 / (r + 1)
            chest_mod = chest_rarity + 1
            luck_mod = 1 + (int(luck) / 10)
            w = base_w * chest_mod * luck_mod
            # если bias по типу, слегка усиливаем вес в пуле
            if type_bias and item.type == type_bias:
                w *= 1.5
            weights.append(w)
        loot += random.choices(all_items, weights=weights, k=remaining)

    # Финальный shuffle, чтобы редкие/билды не шли группами
    random.shuffle(loot)
    return loot
