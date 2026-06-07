from dataclasses import dataclass, field

from src.data.items_data import ITEMS


@dataclass
class Item:
    item_id: str
    name: str
    type: str
    category: str
    description: str
    price: int = 0
    stackable: bool = True
    max_stack: int = 99
    icon_color: tuple[int, int, int] = (255, 255, 255)
    data: dict = field(default_factory=dict)

    @classmethod
    def from_id(cls, item_id: str) -> "Item":
        raw = ITEMS[item_id].copy()
        return cls(
            item_id=item_id,
            name=raw.get("name", item_id),
            type=raw.get("type", "material"),
            category=raw.get("category", "Materiais"),
            description=raw.get("description", ""),
            price=raw.get("price", 0),
            stackable=raw.get("stackable", True),
            max_stack=raw.get("max_stack", 1 if not raw.get("stackable", True) else 99),
            icon_color=raw.get("icon_color", (255, 255, 255)),
            data=raw,
        )

    @property
    def damage(self) -> int:
        return int(self.data.get("damage", 1))

    @property
    def range(self) -> int:
        return int(self.data.get("range", 48))

    @property
    def energy_cost(self) -> int:
        return int(self.data.get("energy_cost", 0))

    @property
    def mana_cost(self) -> int:
        return int(self.data.get("mana_cost", 0))

    @property
    def tool_type(self) -> str | None:
        return self.data.get("tool_type")

    def is_weapon_like(self) -> bool:
        return self.type in {"weapon", "tool"}

    def is_consumable(self) -> bool:
        return self.type in {"food", "drink", "potion"}

    def is_building(self) -> bool:
        return self.type == "building"


class Weapon(Item):
    pass


class Tool(Item):
    pass


class Food(Item):
    pass


class Material(Item):
    pass


class Potion(Item):
    pass


def make_item(item_id: str) -> Item:
    item = Item.from_id(item_id)
    if item.type == "weapon":
        item.__class__ = Weapon
    elif item.type == "tool":
        item.__class__ = Tool
    elif item.type == "food":
        item.__class__ = Food
    elif item.type == "drink":
        item.__class__ = Food
    elif item.type == "material":
        item.__class__ = Material
    elif item.type == "potion":
        item.__class__ = Potion
    return item
