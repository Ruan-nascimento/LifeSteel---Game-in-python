from __future__ import annotations

import pygame

from src.core.settings import Settings
from src.data.classes_data import CLASSES
from src.data.items_data import ITEMS
from src.entities.entity import Entity
from src.items.item import make_item
from src.systems.consumable_system import ConsumableSystem
from src.systems.inventory_system import Inventory, InventorySlot
from src.systems.item_system import ItemSystem
from src.systems.level_system import LevelSystem
from src.systems.skill_system import SkillTree


FACING = {
    "up": pygame.Vector2(0, -1),
    "down": pygame.Vector2(0, 1),
    "left": pygame.Vector2(-1, 0),
    "right": pygame.Vector2(1, 0),
}


class Player(Entity):
    def __init__(self, name: str, class_id: str, pos, asset_loader) -> None:
        class_data = CLASSES[class_id]
        max_hp = 100 + int(class_data.get("hp_bonus", 0))
        super().__init__(pos, Settings.PLAYER_SIZE, max_hp)
        self.name = name or "Viajante"
        self.class_id = class_id
        self.assets = asset_loader
        self.base_speed = Settings.PLAYER_BASE_SPEED + int(class_data.get("speed_bonus", 0))
        self.defense = max(0, int(class_data.get("defense_bonus", 0)))
        self.hunger = 100.0
        self.max_hunger = 100
        self.thirst = 100.0
        self.max_thirst = 100
        self.energy = 100.0
        self.max_energy = 100
        self.mana = float(class_data.get("mana", 30))
        self.max_mana = float(class_data.get("mana", 30))
        self.coins = Settings.STARTING_COINS
        self.inventory = Inventory(capacity=20)
        self.level = LevelSystem()
        self.skills = SkillTree()
        self.skills.apply_class_affinity(class_data.get("skills", []))
        self.attack_timer = 0.0
        self.status_effects: list[str] = []
        self.animation_state = "idle"
        self.animation_timer = 0.0
        self.animation_frame = 0
        self.moved_this_frame = False
        self.is_running = False
        self.equipped_backpack_slot: int | None = None
        self.equipped_items: dict[str, str | None] = {"hand": None}
        self.read_books: set[str] = set()
        self.current_reading: dict | None = None
        self.unlocked_recipes: set[str] = set()
        self.unlocked_abilities: set[str] = set()
        self.passive_bonuses: dict[str, int | float] = {}
        self.passive_bonus_sources: set[str] = set()
        self.upgrades_applied: set[str] = set()
        self.growth_level_applied = 1
        self._zero_need_damage_timer = 0.0
        self.last_consumable_result: dict | None = None
        self._give_starting_items()

    def _give_starting_items(self) -> None:
        class_data = CLASSES[self.class_id]
        self.inventory.add_item(class_data["weapon"], 1)
        tool = class_data.get("tool")
        if tool and tool != class_data["weapon"]:
            self.inventory.add_item(tool, 1)
        self.inventory.add_item("apple", Settings.STARTING_APPLES)
        self.inventory.add_item("small_backpack", 1)
        self.inventory.add_item("blank_map", 1)

    def update(self, dt: float, input_handler, world, weather, particles) -> None:
        self.attack_timer = max(0, self.attack_timer - dt)
        self._move(dt, input_handler, world, weather, particles)
        self._update_survival(dt)
        self._update_animation(dt)

    def _move(self, dt: float, input_handler, world, weather, particles) -> None:
        direction = input_handler.movement_vector()
        self.moved_this_frame = direction.length_squared() > 0
        self.is_running = False
        if not self.moved_this_frame:
            self.animation_state = "idle" if self.attack_timer <= 0 else "attack"
            self.energy = min(self.max_energy, self.energy + 5 * dt)
            return

        if abs(direction.x) > abs(direction.y):
            self.direction = "right" if direction.x > 0 else "left"
        else:
            self.direction = "down" if direction.y > 0 else "up"
        self.facing_vector = FACING[self.direction]

        low_needs_modifier = 0.82 if self.hunger < 15 or self.thirst < 15 else 1.0
        speed = self.base_speed * weather.movement_modifier() * low_needs_modifier
        if hasattr(world, "is_water_at") and world.is_water_at(self.center):
            speed *= Settings.WATER_MOVE_SPEED_MULTIPLIER
        running = input_handler.sprinting() and self.energy > 3 and self.hunger >= 30 and self.thirst >= 30
        if running:
            speed *= Settings.PLAYER_RUN_MULTIPLIER
            self.energy = max(0, self.energy - 22 * dt)
            self.animation_state = "run"
            self.is_running = True
            particles.trail(self.pos + pygame.Vector2(0, self.size[1] * 0.35))
        else:
            self.energy = min(self.max_energy, self.energy + 5 * dt)
            self.animation_state = "walk"

        delta = direction * speed * dt
        self._move_axis(delta.x, 0, world)
        self._move_axis(0, delta.y, world)

    def _move_axis(self, dx: float, dy: float, world) -> None:
        if dx == 0 and dy == 0:
            return
        self.pos.x += dx
        if world.collides(self.collision_rect, allow_water=True):
            self.pos.x -= dx
        self.pos.y += dy
        if world.collides(self.collision_rect, allow_water=True):
            self.pos.y -= dy

    def _update_survival(self, dt: float) -> None:
        hunger_rate = (4 if self.is_running else 1) / 10
        thirst_rate = (5 if self.is_running else 2) / 10
        self.hunger = max(0.0, self.hunger - hunger_rate * dt)
        self.thirst = max(0.0, self.thirst - thirst_rate * dt)
        self.mana = min(self.max_mana, self.mana + 3.0 * dt)
        self.status_effects = []
        if self.hunger < 30:
            self.status_effects.append("Com fome")
        if self.thirst < 30:
            self.status_effects.append("Com sede")
        if self.energy < 18:
            self.status_effects.append("Cansado")
        if self.hp < self.max_hp and self.hunger > 55 and self.thirst > 55:
            self.heal(dt * 0.8)
            self.status_effects.append("Regenerando")
        if self.hunger <= 0 or self.thirst <= 0:
            self._zero_need_damage_timer += dt
            if self._zero_need_damage_timer >= 2.0:
                self.take_damage(max(1, self.max_hp * 0.05))
                self._zero_need_damage_timer = 0.0
        else:
            self._zero_need_damage_timer = 0.0

    def _update_animation(self, dt: float) -> None:
        if self.attack_timer > 0:
            self.animation_state = "attack"
        frame_speed = 0.10 if self.animation_state == "run" else 0.16
        if self.animation_state == "idle":
            frame_speed = 0.32
        self.animation_timer += dt
        if self.animation_timer >= frame_speed:
            self.animation_timer = 0
            self.animation_frame = (self.animation_frame + 1) % 4

    def set_attack_direction(self, target_pos) -> None:
        vector = pygame.Vector2(target_pos) - self.center
        if vector.length_squared() > 0:
            if abs(vector.x) > abs(vector.y):
                self.direction = "right" if vector.x > 0 else "left"
            else:
                self.direction = "down" if vector.y > 0 else "up"
            self.facing_vector = FACING[self.direction]

    def equipped_item(self):
        return self.inventory.selected_item()

    def passive_bonus(self, key: str, default: int | float = 0):
        return self.passive_bonuses.get(key, default)

    @property
    def health(self) -> float:
        return self.hp

    @health.setter
    def health(self, value: float) -> None:
        self.hp = max(0.0, min(self.max_hp, float(value)))
        if self.hp <= 0:
            self.alive = False

    @property
    def max_health(self) -> float:
        return self.max_hp

    @max_health.setter
    def max_health(self, value: float) -> None:
        self.max_hp = max(1, int(value))
        self.hp = min(self.hp, self.max_hp)

    def equipped_backpack(self) -> InventorySlot | None:
        if self.equipped_backpack_slot is None:
            return None
        if not (0 <= self.equipped_backpack_slot < self.inventory.capacity):
            self.equipped_backpack_slot = None
            return None
        slot = self.inventory.slots[self.equipped_backpack_slot]
        if not slot or not slot.is_container():
            self.equipped_backpack_slot = None
            return None
        slot.ensure_contents()
        return slot

    def backpack_contents(self) -> list[InventorySlot | None] | None:
        backpack = self.equipped_backpack()
        return backpack.ensure_contents() if backpack else None

    def equip_backpack(self, index: int) -> bool:
        if not (0 <= index < self.inventory.capacity):
            return False
        slot = self.inventory.slots[index]
        if not slot or not slot.is_container():
            return False
        slot.ensure_contents()
        self.equipped_backpack_slot = index
        return True

    def add_item(self, item_id: str, quantity: int = 1) -> int:
        leftover = self.inventory.add_item(item_id, quantity)
        backpack_slots = self.backpack_contents()
        if leftover > 0 and backpack_slots is not None:
            temp = Inventory(len(backpack_slots))
            temp.slots = backpack_slots
            temp.capacity = len(backpack_slots)
            leftover = temp.add_item(item_id, leftover)
        return leftover

    def can_receive_item(self, item_id: str, quantity: int = 1) -> bool:
        space = self.inventory.free_space_for(item_id)
        backpack_slots = self.backpack_contents()
        if backpack_slots is not None:
            temp = Inventory(len(backpack_slots))
            temp.slots = backpack_slots
            temp.capacity = len(backpack_slots)
            space += temp.free_space_for(item_id)
        return space >= quantity

    def add_slot(self, slot: InventorySlot) -> bool:
        if self.inventory.add_slot(slot):
            return True
        backpack_slots = self.backpack_contents()
        if backpack_slots is None:
            return False
        temp = Inventory(len(backpack_slots))
        temp.slots = backpack_slots
        temp.capacity = len(backpack_slots)
        return temp.add_slot(slot)

    def count_item(self, item_id: str) -> int:
        total = self.inventory.count(item_id)
        backpack_slots = self.backpack_contents()
        if backpack_slots is not None:
            total += sum(slot.quantity for slot in backpack_slots if slot and slot.item_id == item_id)
        return total

    def can_pay_items(self, costs: dict[str, int]) -> bool:
        return all(self.count_item(item_id) >= amount for item_id, amount in costs.items())

    def pay_items(self, costs: dict[str, int]) -> bool:
        if not self.can_pay_items(costs):
            return False
        for item_id, amount in costs.items():
            remaining = amount
            for index, slot in enumerate(self.inventory.slots):
                if remaining <= 0:
                    break
                if slot and slot.item_id == item_id:
                    take = min(slot.quantity, remaining)
                    self.inventory.remove_from_slot(index, take)
                    remaining -= take
            backpack_slots = self.backpack_contents()
            if remaining > 0 and backpack_slots is not None:
                temp = Inventory(len(backpack_slots))
                temp.slots = backpack_slots
                temp.capacity = len(backpack_slots)
                for index, slot in enumerate(list(temp.slots)):
                    if remaining <= 0:
                        break
                    if slot and slot.item_id == item_id:
                        take = min(slot.quantity, remaining)
                        temp.remove_from_slot(index, take)
                        remaining -= take
        return True

    def combat_damage(self, item) -> int:
        class_bonus = int(CLASSES[self.class_id].get("damage_bonus", 0))
        skill_bonus = max(0, self.skills.level("Combate") - 1) * 2
        if item.data.get("damage_type") == "magico":
            skill_bonus += max(0, self.skills.level("Magia") - 1) * 3
        return max(1, item.damage + class_bonus + skill_bonus)

    def tool_power(self, item, resource) -> int:
        power = max(1, item.damage)
        if resource.kind == "tree":
            power += max(0, self.skills.level("Lenhador") - 1) * 3
            if self.class_id == "lumberjack":
                power += 6
        if resource.kind in {"stone", "ore"}:
            power += max(0, self.skills.level("Mineracao") - 1) * 3
        if resource.kind == "soil":
            power += max(0, self.skills.level("Agricultura") - 1) * 2
        return power

    def use_quick_apple(self) -> bool:
        return self.use_item_id("apple")

    def use_item_id(self, item_id: str) -> bool:
        index = self.inventory.first_slot_with(item_id)
        if index is None:
            return False
        return self.use_slot(index)

    def use_slot(self, index: int) -> bool:
        return self.use_inventory_slot(self.inventory, index)

    def use_inventory_slot(self, inventory: Inventory, index: int) -> bool:
        self.last_consumable_result = None
        if index < 0 or index >= inventory.capacity:
            return False
        slot = inventory.slots[index]
        if not slot:
            return False
        item = make_item(slot.item_id)
        if slot.is_container():
            if inventory is self.inventory:
                return self.equip_backpack(index)
            return False
        if item.type in {"book", "upgrade"}:
            self.last_consumable_result = ItemSystem().use_item(self, inventory, item.item_id, index)
            return bool(self.last_consumable_result.get("success"))
        if not item.is_consumable():
            if inventory is self.inventory:
                self.inventory.selected_slot = index
                self.equipped_items["hand"] = item.item_id
            self.last_consumable_result = {"success": True, "message": "Item equipado."}
            return True
        self.last_consumable_result = ConsumableSystem().consume(self, inventory, item.item_id, index)
        if not self.last_consumable_result["success"]:
            return False
        self.skills.add_xp("Sobrevivencia", 2)
        return True

    def drop_all_items(self, world) -> None:
        for index, slot in enumerate(list(self.inventory.slots)):
            if not slot:
                continue
            offset = pygame.Vector2((index % 5 - 2) * 14, (index // 5) * 10)
            world.spawn_ground_drop(self.center + offset, slot.item_id, slot.quantity, contents=slot.contents)
            self.inventory.slots[index] = None
        self.equipped_backpack_slot = None

    def draw(self, surface: pygame.Surface, camera) -> None:
        image = self.assets.player_frame(self.class_id, self.animation_state, self.direction, self.animation_frame)
        draw_pos = self.pos - camera.offset - pygame.Vector2(image.get_width() / 2, image.get_height() - 5)
        surface.blit(image, draw_pos)
        self._draw_equipped_item(surface, camera)
        self._draw_name_and_health(surface, camera)

    def _draw_equipped_item(self, surface: pygame.Surface, camera) -> None:
        item = self.equipped_item()
        if not item:
            return
        icon = self.assets.item_icon(item.item_id, 18)
        hand_offsets = {
            "down": pygame.Vector2(13, -12),
            "up": pygame.Vector2(-18, -25),
            "left": pygame.Vector2(-28, -16),
            "right": pygame.Vector2(13, -16),
        }
        pos = self.center - camera.offset + hand_offsets.get(self.direction, pygame.Vector2(12, -14))
        surface.blit(icon, pos)

    def _draw_name_and_health(self, surface: pygame.Surface, camera) -> None:
        sprite_top = self.pos.y - 46 + 5 - camera.offset.y
        screen_x = self.pos.x - camera.offset.x
        font = pygame.font.SysFont(Settings.UI_FONT, 12, bold=True)
        name_image = font.render(self.name, True, (242, 244, 235))
        name_rect = name_image.get_rect(center=(screen_x, sprite_top - 22))
        shadow = name_rect.move(1, 1)
        surface.blit(font.render(self.name, True, (10, 12, 11)), shadow)
        surface.blit(name_image, name_rect)
        bar = pygame.Rect(int(screen_x - 24), int(sprite_top - 10), 48, 5)
        pygame.draw.rect(surface, (45, 18, 18), bar)
        fill = bar.copy()
        fill.width = max(1, int(bar.width * (self.hp / self.max_hp)))
        pygame.draw.rect(surface, (213, 65, 75), fill)
        pygame.draw.rect(surface, (18, 20, 18), bar, 1)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "class_id": self.class_id,
            "pos": [self.pos.x, self.pos.y],
            "hp": self.hp,
            "max_hp": self.max_hp,
            "hunger": self.hunger,
            "max_hunger": self.max_hunger,
            "thirst": self.thirst,
            "max_thirst": self.max_thirst,
            "energy": self.energy,
            "max_energy": self.max_energy,
            "mana": self.mana,
            "max_mana": self.max_mana,
            "coins": self.coins,
            "inventory": self.inventory.to_list(),
            "selected_slot": self.inventory.selected_slot,
            "equipped_backpack_slot": self.equipped_backpack_slot,
            "equipped_items": self.equipped_items,
            "read_books": sorted(self.read_books),
            "current_reading": self.current_reading,
            "unlocked_recipes": sorted(self.unlocked_recipes),
            "unlocked_abilities": sorted(self.unlocked_abilities),
            "passive_bonuses": self.passive_bonuses,
            "passive_bonus_sources": sorted(self.passive_bonus_sources),
            "upgrades_applied": sorted(self.upgrades_applied),
            "growth_level_applied": self.growth_level_applied,
            "level": self.level.to_dict(),
            "skills": self.skills.to_dict(),
        }

    @classmethod
    def from_dict(cls, data: dict, asset_loader) -> "Player":
        player = cls(data.get("name", "Viajante"), data.get("class_id", "warrior"), data.get("pos", [0, 0]), asset_loader)
        player.hp = float(data.get("hp", player.hp))
        player.max_hp = int(data.get("max_hp", player.max_hp))
        player.hunger = float(data.get("hunger", 100))
        player.max_hunger = int(data.get("max_hunger", 100))
        player.thirst = float(data.get("thirst", 100))
        player.max_thirst = int(data.get("max_thirst", 100))
        player.energy = float(data.get("energy", 100))
        player.max_energy = int(data.get("max_energy", player.max_energy))
        player.mana = float(data.get("mana", player.mana))
        player.max_mana = float(data.get("max_mana", player.max_mana))
        player.coins = int(data.get("coins", Settings.STARTING_COINS))
        player.inventory = Inventory.from_list(data.get("inventory", []), capacity=20)
        player.inventory.selected_slot = int(data.get("selected_slot", 0))
        equipped_backpack_slot = data.get("equipped_backpack_slot")
        player.equipped_backpack_slot = int(equipped_backpack_slot) if equipped_backpack_slot is not None else None
        player.equipped_items = dict(data.get("equipped_items", {"hand": None}))
        player.read_books = set(data.get("read_books", []))
        player.current_reading = data.get("current_reading")
        player.unlocked_recipes = set(data.get("unlocked_recipes", []))
        player.unlocked_abilities = set(data.get("unlocked_abilities", []))
        player.passive_bonuses = dict(data.get("passive_bonuses", {}))
        player.passive_bonus_sources = set(data.get("passive_bonus_sources", []))
        player.upgrades_applied = set(data.get("upgrades_applied", []))
        player.level = LevelSystem.from_dict(data.get("level", {}))
        player.growth_level_applied = int(data.get("growth_level_applied", player.level.level))
        player.skills = SkillTree.from_dict(data.get("skills", {}))
        return player
