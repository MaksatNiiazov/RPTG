
def get_sell_price(item, character, trade_modifier=1.0):
    """
    Возвращает итоговую цену продажи предмета с учётом CHA и модификатора торговли.
    CHA 4 = 100% цены, CHA 0 = –35%, CHA 10 = +35% и выше.
    """
    cha = character.cha_stat
    base_price = item.price

    multiplier = 1.0 + ((cha - 4) / 6) * 0.35
    final_price = round(base_price * multiplier * trade_modifier)

    return max(final_price, 0)


def get_buy_price(item, character, trade_modifier=1.0, base_price=None):
    cha = character.cha_stat
    base = base_price or item.price
    multiplier = 1.0 - ((cha - 4) / 6) * 0.35
    return round(base * multiplier * trade_modifier)