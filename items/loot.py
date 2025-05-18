# catalog/loot.py

import random
import math
from typing import List, Optional
from .models import Item, Rarity, Type

def _base_weight(item: Item) -> float:
    """1/(rarity+1)"""
    return 1 / (item.rarity.lvl + 1)

def generate_loot_items(
    luck: int,
    chest_rarity: Rarity,
    count: int = 3,
    rare_count: int = 0,
    rare_rarity: Optional[Rarity] = None,
    chest_type: Optional[Type] = None
) -> List[Item]:
    """
    Генерирует список из count предметов с учётом:
      - luck (1–10)
      - chest_rarity  (Rarity)
      - rare_count и rare_rarity — гарантия выпада rare_count штук именно rare_rarity
      - chest_type — если указан, то большинство (ceil(count/2)) предметов этого типа
    """
    all_items = list(Item.objects.select_related("type", "rarity").all())
    if not all_items:
        return []

    # 1) Если chest_type — выбираем половину
    result = []
    remaining = count
    if chest_type:
        half = math.ceil(count / 2)
        pool = [i for i in all_items if i.type_id == chest_type.id]
        if pool:
            weights = []
            for i in pool:
                weights.append(_base_weight(i) * (chest_rarity.lvl+1) * (1 + luck/10))
            picks = random.choices(pool, weights=weights, k=half)
            result.extend(picks)
        remaining -= half

    # 2) Гарантированные rare_count
    if rare_count and rare_rarity:
        pool = [i for i in all_items if i.rarity_id == rare_rarity.id]
        if pool:
            k = min(rare_count, remaining)
            picks = random.choices(pool, k=k)
            result.extend(picks)
            remaining -= k

    # 3) Остаток — обычная генерация
    if remaining > 0:
        # общий вес для каждого
        weights = [
            _base_weight(i) * (chest_rarity.lvl+1) * (1 + luck/10)
            for i in all_items
        ]
        picks = random.choices(all_items, weights=weights, k=remaining)
        result.extend(picks)

    # Всегда возвращаем ровно count
    return result[:count]
