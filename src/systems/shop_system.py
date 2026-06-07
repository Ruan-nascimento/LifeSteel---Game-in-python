from __future__ import annotations

import unicodedata

from src.data.items_data import ITEMS
from src.data.shop_data import SHOP_STOCK


DEFAULT_SELLERS = {
    "vendedor geral",
    "cozinheiro",
    "pescador",
    "agricultor",
    "alquimista",
    "ferreiro",
    "cacador",
}


def seller_key(value: str | None) -> str:
    if not value:
        return ""
    normalized = unicodedata.normalize("NFKD", value)
    return normalized.encode("ascii", "ignore").decode("ascii").lower()


class ShopSystem:
    def __init__(self, economy) -> None:
        self.economy = economy
        self.stock = [entry.copy() for entry in SHOP_STOCK]
        self.message = "Bem-vindo ao mercador da clareira."

    def available_stock(self, player, seller: str | None = None) -> list[dict]:
        result = []
        compatible_sellers = {seller_key(seller)} if seller else DEFAULT_SELLERS
        for entry in self.stock:
            if entry.get("seller") and seller_key(entry["seller"]) not in compatible_sellers:
                continue
            entry = entry.copy()
            entry["locked"] = player.level.level < entry.get("required_level", 1)
            entry["final_price"] = self.economy.buy_price(entry["id"], entry["price"], player)
            result.append(entry)
        return result

    def buy(self, player, item_id: str, seller: str | None = None) -> bool:
        compatible_sellers = {seller_key(seller)} if seller else DEFAULT_SELLERS
        for entry in self.stock:
            if entry["id"] != item_id:
                continue
            if entry.get("seller") and seller_key(entry["seller"]) not in compatible_sellers:
                self.message = "Este vendedor nao trabalha com esse item."
                return False
            if player.level.level < entry.get("required_level", 1):
                self.message = "Este item ainda esta bloqueado por level."
                return False
            if entry.get("stock", 0) <= 0:
                self.message = "O estoque acabou."
                return False
            price = self.economy.buy_price(item_id, int(entry["price"]), player)
            if player.coins < price:
                self.message = "ZyraCoins insuficientes."
                return False
            leftover = player.add_item(item_id, 1) if hasattr(player, "add_item") else player.inventory.add_item(item_id, 1)
            if leftover:
                self.message = "Inventario cheio."
                return False
            player.coins -= price
            entry["stock"] -= 1
            player.skills.add_xp("Comercio", 3)
            player.skills.add_xp("Comunicacao", 2)
            self.message = f"Comprou {ITEMS[item_id]['name']} por {price} ZC."
            return True
        self.message = "Item nao encontrado."
        return False

    def sell_from_slot(self, player, slot_index: int) -> bool:
        slot = player.inventory.remove_from_slot(slot_index, 1)
        if not slot:
            self.message = "Nada para vender."
            return False
        price = self.economy.sell_price(slot.item_id, player)
        player.coins += price
        player.skills.add_xp("Comercio", 4)
        self.message = f"Vendeu {ITEMS[slot.item_id]['name']} por {price} ZC."
        return True

    def to_dict(self) -> dict:
        return {"stock": self.stock}

    def load_dict(self, data: dict) -> None:
        if data.get("stock"):
            self.stock = data["stock"]
