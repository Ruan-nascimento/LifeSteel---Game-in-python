from __future__ import annotations

import unicodedata

from src.data.items_data import ITEMS
from src.data.shop_data import SHOP_STOCK
from src.systems.item_system import ITEM_DATABASE, ItemDatabase


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
    def __init__(self, economy, database: ItemDatabase | None = None) -> None:
        self.economy = economy
        self.database = database or ITEM_DATABASE
        self.stock = self._build_initial_stock()
        self.message = "Bem-vindo ao mercador da clareira."
        self.active_vendor = ShopVendor(self.database.get_vendor() or {})

    def _build_initial_stock(self) -> list[dict]:
        by_id: dict[str, dict] = {}
        for entry in SHOP_STOCK:
            by_id[entry["id"]] = entry.copy()
        for item in self.database.get_buyable_items("vendor_milo_root", player_level=99):
            item_id = item["id"]
            data = self.database.normalize_item(item_id)
            by_id.setdefault(
                item_id,
                {
                    "id": item_id,
                    "price": int(data.get("buy_price", data.get("price", 1))),
                    "required_level": int(data.get("required_level", 1)),
                    "stock": self._stock_for_rarity(data.get("rarity", "common")),
                    "seller": "vendedor geral",
                },
            )
        return list(by_id.values())

    def _stock_for_rarity(self, rarity: str) -> int:
        return {
            "common": 12,
            "uncommon": 7,
            "rare": 4,
            "epic": 2,
            "legendary": 1,
        }.get(rarity, 6)

    def available_stock(
        self,
        player,
        seller: str | None = None,
        search: str = "",
        category: str = "Todos",
        offset: int = 0,
        limit: int | None = None,
    ) -> list[dict]:
        result = []
        compatible_sellers = {seller_key(seller)} if seller else DEFAULT_SELLERS
        for entry in self.stock:
            if entry.get("seller") and seller_key(entry["seller"]) not in compatible_sellers:
                continue
            item_id = entry["id"]
            if item_id not in ITEMS:
                continue
            if not ITEMS[item_id].get("buyable", True) and entry.get("source") == "items.json":
                continue
            if category != "Todos" and ITEMS[item_id].get("type") != category and ITEMS[item_id].get("category") != category:
                continue
            if search and not self._matches_search(ITEMS[item_id], search):
                continue
            entry = entry.copy()
            entry["locked"] = player.level.level < entry.get("required_level", 1)
            entry["final_price"] = self.economy.buy_price(entry["id"], entry["price"], player)
            result.append(entry)
        result.sort(key=lambda entry: (entry.get("locked", False), entry.get("required_level", 1), ITEMS[entry["id"]]["name"]))
        if offset:
            result = result[max(0, offset):]
        if limit is not None:
            result = result[:limit]
        return result

    def _matches_search(self, item: dict, query: str) -> bool:
        needle = seller_key(query)
        haystack = " ".join(
            str(item.get(key, ""))
            for key in ("name", "id", "type", "category", "description", "rarity")
        )
        return needle in seller_key(haystack)

    def categories(self) -> list[tuple[str, str]]:
        return [
            ("Todos", "Todos"),
            ("weapon", "Armas"),
            ("tool", "Ferramentas"),
            ("food", "Comidas"),
            ("material", "Materiais"),
            ("book", "Livros"),
            ("building", "Estacoes"),
            ("utility", "Utilitarios"),
            ("upgrade", "Melhorias"),
        ]

    def buy(self, player, item_id: str, seller: str | None = None, quantity: int = 1) -> bool:
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
            if entry.get("stock", 0) < quantity:
                self.message = "O estoque acabou."
                return False
            if item_id in ITEMS and not ITEMS[item_id].get("buyable", True):
                self.message = "Este item nao pode ser comprado."
                return False
            price = self.economy.buy_price(item_id, int(entry["price"]), player) * quantity
            if player.coins < price:
                self.message = "ZyraCoins insuficientes."
                return False
            leftover = player.add_item(item_id, quantity) if hasattr(player, "add_item") else player.inventory.add_item(item_id, quantity)
            if leftover:
                self.message = "Inventario cheio."
                return False
            player.coins -= price
            entry["stock"] -= quantity
            player.skills.add_xp("Comercio", 3)
            player.skills.add_xp("Comunicacao", 2)
            self.message = f"Voce comprou {ITEMS[item_id]['name']} por {price} ZC."
            return True
        self.message = "Item nao encontrado."
        return False

    def sell_item(self, player, inventory, item_id: str, quantity: int = 1) -> bool:
        if item_id not in ITEMS:
            self.message = "Item nao encontrado."
            return False
        if not ITEMS[item_id].get("sellable", True):
            self.message = "Este item nao pode ser vendido."
            return False
        if not inventory.has_item(item_id, quantity):
            self.message = "Voce nao possui quantidade suficiente."
            return False
        if not inventory.remove_item(item_id, quantity):
            self.message = "Nao foi possivel vender."
            return False
        price = self.economy.sell_price(item_id, player) * quantity
        player.coins += price
        player.skills.add_xp("Comercio", 4)
        self.message = f"Voce vendeu {ITEMS[item_id]['name']} por {price} ZC."
        return True

    def sell_from_slot(self, player, slot_index: int, quantity: int = 1) -> bool:
        slot = player.inventory.slots[slot_index] if 0 <= slot_index < player.inventory.capacity else None
        if not slot:
            self.message = "Nada para vender."
            return False
        if not ITEMS[slot.item_id].get("sellable", True):
            self.message = "Este item nao pode ser vendido."
            return False
        removed = player.inventory.remove_from_slot(slot_index, quantity)
        if not removed:
            self.message = "Nada para vender."
            return False
        price = self.economy.sell_price(removed.item_id, player) * removed.quantity
        player.coins += price
        player.skills.add_xp("Comercio", 4)
        self.message = f"Voce vendeu {ITEMS[removed.item_id]['name']} por {price} ZC."
        return True

    def to_dict(self) -> dict:
        return {"stock": self.stock}

    def load_dict(self, data: dict) -> None:
        if data.get("stock"):
            self.stock = data["stock"]


class ShopVendor:
    def __init__(self, vendor_data: dict) -> None:
        self.data = vendor_data or {}
        self.id = self.data.get("id", "vendor_milo_root")
        self.name = self.data.get("name", "Milo Raizforte")
        self.title = self.data.get("title", "Mercador da Clareira")
        self.shop_id = self.data.get("shop_id", "forest_general_store")
        self.categories_sold = set(self.data.get("categories_sold", []))

    def get_available_items(self, player) -> list[dict]:
        return ITEM_DATABASE.get_buyable_items(self.id, player.level.level)

    def can_sell_item(self, item_id: str) -> bool:
        if item_id not in ITEMS:
            return False
        item_type = ITEMS[item_id].get("type")
        return not self.categories_sold or item_type in self.categories_sold
