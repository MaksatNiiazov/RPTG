# worlds/loot.py

import random
from typing import List
from items.loot import generate_loot_items
from worlds.models import WorldItemPool, World

def open_chest_in_world(
    world: World,
    luck: int,
    chest_rarity: int,
    count: int = 3,
    rare_count: int = 0,
    rare_rarity=None,
    type_bias=None,
    type_bias_count: int = 0
) -> List["catalog.models.Item"]:
    """
    Открыть сундук в мире:
      - Учитывает остатки world.item_pools.remaining.
      - Генерирует кандидатов через generate_loot_items.
      - Фильтрует и дополняет до count.
      - Списывает remaining для ограниченных.
      - Возвращает список Item.
    """
    # 1) Собираем пул доступных предметов
    pools = WorldItemPool.objects.select_related("item").filter(world=world)
    available_items = [p.item for p in pools if p.remaining is None or p.remaining > 0]
    if not available_items:
        return []

    # 2) Генерируем первичный лут (на полном наборе) и фильтруем
    raw_loot = generate_loot_items(
        luck=luck,
        chest_rarity=chest_rarity,
        count=count,
        rare_count=rare_count,
        rare_rarity=rare_rarity,
        type_bias=type_bias,
        type_bias_count=type_bias_count
    )
    # Оставляем только доступные
    loot = [it for it in raw_loot if it in available_items]

    # 3) Если после фильтрации меньше, докупаем случайные
    if len(loot) < count:
        extra = random.choices(available_items, k=count - len(loot))
        loot += extra

    # 4) Списываем из пула мира
    for item in loot:
        pool = WorldItemPool.objects.get(world=world, item=item)
        if pool.remaining is not None:
            pool.remaining = max(0, pool.remaining - 1)
            pool.save(update_fields=["remaining"])

    # 5) Перемешиваем и возвращаем
    random.shuffle(loot)
    return loot
