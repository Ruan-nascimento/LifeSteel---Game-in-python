from src.data.items_data import ITEMS


class EconomySystem:
    def __init__(self) -> None:
        self.market_mood = 1.0

    def buy_price(self, item_id: str, base_price: int, player) -> int:
        discount = player.skills.communication_discount()
        if player.class_id == "diplomat":
            discount += 0.06
        return max(1, round(base_price * self.market_mood * (1 - min(discount, 0.35))))

    def sell_price(self, item_id: str, player) -> int:
        base = int(ITEMS[item_id].get("price", 1))
        bonus = player.skills.commerce_sell_bonus()
        if player.class_id == "diplomat":
            bonus += 0.08
        return max(1, round(base * 0.55 * (1 + min(bonus, 0.45))))
