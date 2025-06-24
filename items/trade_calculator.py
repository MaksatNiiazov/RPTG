class PriceCalculator:
    def __init__(self, *, base_price: int, cha: float = 4.0, trade_modifier: float = 1.0):
        self.base_price = base_price
        self.cha = cha
        self.trade_modifier = trade_modifier

    def _get_charisma_multiplier(self) -> float:
        """
        Базовая шкала:
        - CHA 4 = 1.0
        - Каждое +1 CHA от 4 → +0.058
        - Каждое –1 CHA от 4 → –0.058
        Без ограничений сверху
        """
        return 1.0 + ((self.cha - 4) / 6) * 0.35

    def get_sell_price(self) -> int:
        return round(self.base_price * self._get_charisma_multiplier() * self.trade_modifier)

