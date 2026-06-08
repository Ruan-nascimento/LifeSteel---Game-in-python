from __future__ import annotations

import random
from time import perf_counter

import pygame

if not hasattr(pygame, "Vector2") and hasattr(pygame, "math"):
    pygame.Vector2 = pygame.math.Vector2

from src.core.asset_loader import AssetLoader
from src.core.camera import Camera
from src.core.input_handler import InputHandler
from src.core.save_manager import SaveManager
from src.core.settings import COLORS, Settings
from src.data.animals_data import ANIMAL_ORDER
from src.data.enemies_data import ENEMY_ORDER
from src.data.food_data import friendly_station_name
from src.data.items_data import ITEMS
from src.entities.animal import Animal
from src.entities.enemy import Enemy
from src.entities.npc import NPC
from src.entities.player import Player
from src.systems.building_system import BUILDING_COSTS, BuildingSystem
from src.systems.combat_system import CombatSystem
from src.systems.consumable_system import ConsumableSystem
from src.systems.cooking_system import CookingSystem
from src.systems.crafting_system import CraftingSystem
from src.systems.drop_system import DropSystem
from src.systems.economy_system import EconomySystem
from src.systems.inventory_system import Inventory, InventorySlot
from src.systems.lighting_system import LightingSystem
from src.systems.map_exploration_system import MapExplorationSystem
from src.systems.particle_system import ParticleManager
from src.systems.quest_system import QuestSystem
from src.systems.reading_system import ReadingSystem
from src.systems.shop_system import ShopSystem
from src.systems.time_system import TimeSystem
from src.systems.weather_system import WeatherSystem
from src.ui.character_creation_ui import CharacterCreationMenu
from src.ui.character_ui import CharacterUI
from src.ui.dialogue_ui import DialogueUI
from src.ui.hud import HUD
from src.ui.inventory_ui import InventoryUI
from src.ui.main_menu import MainMenu
from src.ui.minimap_ui import MinimapUI
from src.ui.notification_ui import NotificationUI
from src.ui.quest_ui import QuestUI
from src.ui.settings_ui import SettingsMenu
from src.ui.shop_ui import ShopUI
from src.ui.widgets import Button, draw_panel, draw_text, draw_wrapped
from src.world.world import World


class Game:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption(Settings.TITLE)
        self.screen = pygame.display.set_mode((Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "main_menu"
        self.previous_state = "main_menu"

        self.assets = AssetLoader()
        self.input = InputHandler()
        self.save_manager = SaveManager()

        self.main_menu = MainMenu(self.save_manager)
        self.settings_menu = SettingsMenu()
        self.character_creation = CharacterCreationMenu(self.assets)
        self.hud = HUD(self.assets)
        self.inventory_ui = InventoryUI(self.assets)
        self.shop_ui = ShopUI(self.assets)
        self.character_ui = CharacterUI()
        self.dialogue_ui = DialogueUI()
        self.quest_ui = QuestUI()
        self.notifications = NotificationUI()
        self.expanded_minimap = MinimapUI()

        self.world: World | None = None
        self.player: Player | None = None
        self.camera: Camera | None = None
        self.npcs: list[NPC] = []
        self.enemies: list[Enemy] = []
        self.animals: list[Animal] = []
        self._rng = random.Random(42)

        self.economy = EconomySystem()
        self.shop_system = ShopSystem(self.economy)
        self.combat_system = CombatSystem()
        self.consumable_system = ConsumableSystem()
        self.cooking_system = CookingSystem()
        self.drop_system = DropSystem(self._rng)
        self.time_system = TimeSystem()
        self.weather_system = WeatherSystem()
        self.lighting_system = LightingSystem(self.screen.get_size())
        self.particles = ParticleManager()
        self.exploration: MapExplorationSystem | None = None
        self.crafting_system = CraftingSystem()
        self.building_system = BuildingSystem()
        self.quest_system = QuestSystem()

        self.active_panel: str | None = None
        self.pause_buttons: list[Button] = []
        self.build_buttons: list[Button] = []
        self.craft_buttons: list[Button] = []
        self.cooking_buttons: list[Button] = []
        self.chest_buttons: list[Button] = []
        self.chest_slot_rects: dict[tuple[str, int], pygame.Rect] = {}
        self.chest_selected_ref: tuple[str, int] | None = ("main", 0)
        self.chest_dragging_ref: tuple[str, int] | None = None
        self.selected_recipe_id: str | None = None
        self.craft_search = ""
        self.active_structure = None
        self.death_message_timer = 0.0
        self.show_performance_debug = False
        self.performance_stats = {
            "update_ms": 0.0,
            "render_ms": 0.0,
            "rendered_entities": 0,
            "updated_entities": 0,
            "drawn_particles": 0,
            "processed_lights": 0,
        }

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(Settings.FPS) / 1000
            self._handle_events()
            self._update(dt)
            self._draw()
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                continue
            if event.type == pygame.VIDEORESIZE:
                width = max(Settings.MIN_WIDTH, event.w)
                height = max(Settings.MIN_HEIGHT, event.h)
                self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
                if self.camera:
                    self.camera.resize((width, height))
                self.lighting_system.resize((width, height))
                continue

            if self.state == "main_menu":
                self._handle_main_menu_event(event)
            elif self.state == "settings":
                self._handle_settings_event(event)
            elif self.state == "character_creation":
                self._handle_character_creation_event(event)
            elif self.state == "playing":
                self._handle_playing_event(event)

    def _handle_main_menu_event(self, event) -> None:
        action = self.main_menu.handle_event(event)
        if action == "new_game":
            self.state = "character_creation"
        elif action == "continue":
            if not self.load_game():
                self.notifications.push("Nenhum save encontrado.")
        elif action == "settings":
            self.previous_state = "main_menu"
            self.state = "settings"
        elif action == "quit":
            self.running = False

    def _handle_settings_event(self, event) -> None:
        action = self.settings_menu.handle_event(event)
        if action == "back":
            self.state = self.previous_state

    def _handle_character_creation_event(self, event) -> None:
        action = self.character_creation.handle_event(event)
        if action == "back":
            self.state = "main_menu"
        elif isinstance(action, tuple) and action[0] == "start_game":
            _, name, class_id = action
            self.new_game(name, class_id)

    def _handle_playing_event(self, event) -> None:
        if not self.player or not self.world:
            return

        if self.active_panel == "inventory":
            action = self.inventory_ui.handle_event(event, self.player)
            self._handle_inventory_action(action)
        elif self.active_panel == "shop":
            action = self.shop_ui.handle_event(event)
            self._handle_shop_action(action)
        elif self.active_panel == "quests":
            action = self.quest_ui.handle_event(event, self.quest_system)
            self._handle_quest_action(action)
        elif self.active_panel == "character":
            self.character_ui.handle_event(event)
        elif self.active_panel == "dialogue":
            action = self.dialogue_ui.handle_event(event)
            if action == "close_dialogue":
                self.active_panel = None
                self.dialogue_ui.close()
        elif self.active_panel == "pause":
            self._handle_pause_event(event)
        elif self.active_panel == "building":
            self._handle_building_event(event)
        elif self.active_panel == "crafting":
            self._handle_crafting_event(event)
        elif self.active_panel == "cooking":
            self._handle_cooking_event(event)
        elif self.active_panel == "chest":
            self._handle_chest_event(event)

        if event.type == pygame.KEYDOWN:
            self._handle_playing_key(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.active_panel is None:
            mouse_world = self.camera.screen_to_world(event.pos)
            if self._try_break_chest(mouse_world):
                return
            if self._try_open_structure_by_click(mouse_world):
                return
            if not self._try_fishing(mouse_world):
                self.combat_system.player_attack(
                    self.player,
                    self.world,
                    self.enemies,
                    mouse_world,
                    self.particles,
                    self.notifications,
                    self.animals,
                    self.drop_system,
                    self.quest_system,
                    self.time_system.is_night(),
                )
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and self.active_panel is None:
            mouse_world = self.camera.screen_to_world(event.pos)
            self._try_place_equipped_building(mouse_world)

    def _handle_playing_key(self, key: int) -> None:
        if not self.player:
            return
        if key == pygame.K_ESCAPE:
            if self.active_panel is None:
                self.active_panel = "pause"
            elif self.active_panel == "pause":
                self.active_panel = None
            else:
                self.active_panel = None
                self.dialogue_ui.close()
            return
        if key == pygame.K_F5:
            self.save_game()
            return
        if key == pygame.K_F9:
            self.load_game()
            return
        if key == pygame.K_F3:
            self.show_performance_debug = not self.show_performance_debug
            return

        if pygame.K_1 <= key <= pygame.K_5:
            self.player.inventory.selected_slot = key - pygame.K_1
            return
        if key == pygame.K_i:
            self._toggle_panel("inventory")
        elif key == pygame.K_c:
            self._toggle_panel("character")
        elif key == pygame.K_m:
            self._toggle_panel("map")
        elif key == pygame.K_b:
            self._toggle_panel("building")
        elif key == pygame.K_k:
            self._toggle_panel("skills")
        elif key == pygame.K_j:
            self._toggle_panel("quests")
        elif key == pygame.K_TAB:
            self._cycle_panel()
        elif key == pygame.K_q:
            self._use_equipped_consumable()
        elif key == pygame.K_f:
            self._pickup_drops()
        elif key == pygame.K_e and self.active_panel is None:
            self._interact()

    def _toggle_panel(self, panel: str) -> None:
        if self.active_panel is None:
            self.active_panel = panel
        elif self.active_panel == panel:
            self.active_panel = None

    def _cycle_panel(self) -> None:
        order = [None, "inventory", "character", "skills", "quests", "map"]
        current_index = order.index(self.active_panel) if self.active_panel in order else 0
        self.active_panel = order[(current_index + 1) % len(order)]

    def _handle_quest_action(self, action) -> None:
        if not action or not self.player:
            return
        if action == "close_quests":
            self.active_panel = None
            return
        if isinstance(action, tuple) and action[0] == "accept_quest":
            ok, message = self.quest_system.accept_quest(action[1])
            self.notifications.push(message)
            return
        if isinstance(action, tuple) and action[0] == "claim_quest":
            ok, messages = self.quest_system.claim_reward(self.player, action[1])
            for message in messages:
                self.notifications.push(message)

    def _quest_event(self, event_type: str, target_id: str | None = None, amount: int = 1, metadata: dict | None = None) -> None:
        if not self.quest_system:
            return
        for message in self.quest_system.update_objective(event_type, target_id, amount, metadata or {}):
            self.notifications.push(message)

    def _drain_quest_messages(self) -> None:
        if not self.quest_system:
            return
        for message in self.quest_system.drain_messages():
            self.notifications.push(message)

    def _use_equipped_consumable(self) -> None:
        if not self.player:
            return
        slot_index = self.player.inventory.selected_slot
        slot = self.player.inventory.selected()
        if not slot:
            self.notifications.push("Nenhum item consumivel equipado.")
            return
        item = slot.item
        if not item.is_consumable():
            self.notifications.push("Item equipado nao e consumivel.")
            return
        self._consume_inventory_slot("main", slot_index)

    def _handle_inventory_action(self, action) -> None:
        if not action or not self.player or not self.world:
            return
        kind = action[0]
        if kind == "use_slot":
            _, source, index = action
            inventory = self._inventory_for_source(source)
            if not inventory or not (0 <= index < inventory.capacity):
                return
            slot = inventory.slots[index]
            if slot and slot.item.is_consumable():
                self._consume_inventory_slot(source, index)
            elif inventory and self.player.use_inventory_slot(inventory, index):
                used_item_id = slot.item_id if slot else None
                used_item_type = slot.item.data.get("type") if slot else None
                result = self.player.last_consumable_result or {}
                self.notifications.push(result.get("message", "Item usado."))
                for reward in result.get("rewards", []):
                    self.notifications.push(reward)
                if used_item_id and used_item_type == "book":
                    self._quest_event("read_book", used_item_id, 1, {"category": ITEMS.get(used_item_id, {}).get("category", "")})
        elif kind == "equip_slot":
            _, source, index = action
            if source != "main":
                self.notifications.push("Mova para o inventario principal para equipar.")
                return
            slot = self.player.inventory.slots[index]
            if slot and slot.is_container():
                if self.player.equip_backpack(index):
                    self.notifications.push("Mochila equipada.")
            else:
                self.player.inventory.selected_slot = index
                self.notifications.push("Item equipado.")
        elif kind == "drop_slot":
            _, source, index = action
            inventory = self._inventory_for_source(source)
            if not inventory:
                return
            if source == "main" and index == self.player.equipped_backpack_slot:
                self.player.equipped_backpack_slot = None
            slot = inventory.remove_from_slot(index, 1)
            if slot:
                drop_pos = self.player.center + self.player.facing_vector * 36
                self.world.spawn_ground_drop(drop_pos, slot.item_id, slot.quantity, contents=slot.contents)
                self.notifications.push(f"Dropou {ITEMS[slot.item_id]['name']}.")
        elif kind == "move_slot":
            _, from_source, from_index, to_source, to_index = action
            self._move_between_inventories(from_source, from_index, to_source, to_index)
        elif kind == "shift_click_slot":
            _, source, index = action
            self._handle_shift_click(source, index)

    def _consume_inventory_slot(self, source: str, index: int) -> bool:
        if not self.player:
            return False
        inventory = self._inventory_for_source(source)
        if not inventory or not (0 <= index < inventory.capacity):
            self.notifications.push("Item nao encontrado.")
            return False
        slot = inventory.slots[index]
        if not slot:
            self.notifications.push("Nenhum item consumivel equipado.")
            return False
        consumed_item_id = slot.item_id
        result = self.consumable_system.consume(self.player, inventory, slot.item_id, index)
        self.notifications.push(result["message"])
        if not result["success"]:
            return False
        for line in result.get("effect_lines", [])[:5]:
            self.notifications.push(line)
        color = ITEMS[slot.item_id].get("icon_color", COLORS["accent_2"])
        if self.world:
            self.particles.emit(self.player.center, color=color, amount=9, speed=55, lifetime=0.45, radius=3)
        self.player.skills.add_xp("Sobrevivencia", 2)
        self._quest_event("consume", consumed_item_id, 1)
        return True

    def _inventory_for_source(self, source: str):
        if not self.player:
            return None
        if source == "main":
            return self.player.inventory
        if source == "backpack":
            slots = self.player.backpack_contents()
            if slots is None:
                return None
            temp = Inventory(len(slots))
            temp.slots = slots
            temp.capacity = len(slots)
            return temp
        if source == "chest":
            slots = self._active_chest_contents()
            if slots is None:
                return None
            temp = Inventory(len(slots))
            temp.slots = slots
            temp.capacity = len(slots)
            return temp
        return None

    def _active_chest_contents(self) -> list[InventorySlot | None] | None:
        return self._structure_chest_contents(self.active_structure)

    def _structure_chest_contents(self, structure) -> list[InventorySlot | None] | None:
        if not structure or structure.interface_kind() != "chest":
            return None
        if structure.state is None:
            structure.state = {}
        capacity = 12
        contents = structure.state.get("contents")
        if contents is None:
            contents = [None for _ in range(capacity)]
        else:
            contents = list(contents)
            for index, slot in enumerate(contents):
                if isinstance(slot, dict):
                    contents[index] = InventorySlot.from_dict(slot)
            if len(contents) < capacity:
                contents.extend([None for _ in range(capacity - len(contents))])
            elif len(contents) > capacity:
                contents = contents[:capacity]
        structure.state["contents"] = contents
        return contents

    def _move_between_inventories(self, from_source: str, from_index: int, to_source: str, to_index: int) -> None:
        if not self.player:
            return
        from_inventory = self._inventory_for_source(from_source)
        to_inventory = self._inventory_for_source(to_source)
        if not from_inventory or not to_inventory:
            return
        if from_source == to_source:
            from_inventory.move_slot(from_index, to_index)
        else:
            if not (0 <= from_index < from_inventory.capacity and 0 <= to_index < to_inventory.capacity):
                return
            from_inventory.slots[from_index], to_inventory.slots[to_index] = to_inventory.slots[to_index], from_inventory.slots[from_index]
        if self.player.equipped_backpack_slot is not None:
            slot = self.player.inventory.slots[self.player.equipped_backpack_slot]
            if not slot or not slot.is_container():
                self.player.equipped_backpack_slot = None

    def _handle_shift_click(self, source: str, index: int) -> None:
        if not self.player:
            return
        
        inventory = self._inventory_for_source(source)
        if not inventory or not (0 <= index < inventory.capacity):
            return
        slot = inventory.slots[index]
        if not slot:
            return

        def _try_add_to_range(target_inv, start_idx, end_idx) -> bool:
            if not target_inv:
                return False
            data = ITEMS.get(slot.item_id, {})
            stackable = bool(data.get("stackable", True)) and slot.contents is None
            max_stack = int(data.get("max_stack", 1 if not stackable else 99))
            
            if stackable:
                for i in range(start_idx, end_idx):
                    if target_inv.slots is inventory.slots and i == index:
                        continue
                    target_slot = target_inv.slots[i]
                    if target_slot and target_slot.item_id == slot.item_id and target_slot.contents is None and target_slot.quantity < max_stack:
                        moved = min(slot.quantity, max_stack - target_slot.quantity)
                        target_slot.quantity += moved
                        slot.quantity -= moved
                        if slot.quantity <= 0:
                            inventory.slots[index] = None
                            return True
            
            for i in range(start_idx, end_idx):
                if target_inv.slots is inventory.slots and i == index:
                    continue
                if target_inv.slots[i] is None:
                    target_inv.slots[i] = slot
                    inventory.slots[index] = None
                    if inventory.slots is self.player.inventory.slots and index == self.player.equipped_backpack_slot:
                        self.player.equipped_backpack_slot = None
                    return True
            return False

        if source == "main":
            if index < 5:
                _try_add_to_range(self.player.inventory, 5, self.player.inventory.capacity)
            else:
                backpack_inv = self._inventory_for_source("backpack")
                moved = False
                if backpack_inv:
                    moved = _try_add_to_range(backpack_inv, 0, backpack_inv.capacity)
                if not moved:
                    _try_add_to_range(self.player.inventory, 0, 5)
        elif source == "backpack":
            if not _try_add_to_range(self.player.inventory, 0, 5):
                if not _try_add_to_range(self.player.inventory, 5, self.player.inventory.capacity):
                    _try_add_to_range(inventory, 0, inventory.capacity)

    def _handle_shop_action(self, action) -> None:
        if not action or not self.player:
            return
        kind, value = action
        if kind == "buy":
            success = self.shop_system.buy(self.player, value)
            self.notifications.push(self.shop_system.message)
            if success and self.shop_system.last_transaction:
                tx = self.shop_system.last_transaction
                self._quest_event("buy", tx["item_id"], int(tx.get("quantity", 1)), {"coins_spent": int(tx.get("coins", 0))})
        elif kind == "sell":
            success = self.shop_system.sell_from_slot(self.player, value)
            self.notifications.push(self.shop_system.message)
            if success and self.shop_system.last_transaction:
                tx = self.shop_system.last_transaction
                quantity = int(tx.get("quantity", 1))
                coins = int(tx.get("coins", 0))
                self._quest_event("sell", tx["item_id"], quantity, {"coins_earned": coins})
                self._quest_event("earn_coins", "sell", coins, {"coins_earned": coins})

    def _handle_pause_event(self, event) -> None:
        if event.type not in {pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION}:
            return
        for button in self.pause_buttons:
            action = button.handle_event(event)
            if action == "resume":
                self.active_panel = None
            elif action == "save":
                self.save_game()
            elif action == "settings":
                self.previous_state = "playing"
                self.state = "settings"
                self.active_panel = None
            elif action == "main_menu":
                self.state = "main_menu"
                self.active_panel = None
            elif action == "quit":
                self.running = False

    def _handle_building_event(self, event) -> None:
        if not self.player or not self.world or not self.camera:
            return
        if event.type == pygame.MOUSEMOTION:
            for button in self.build_buttons:
                button.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.build_buttons:
                action = button.handle_event(event)
                if action:
                    if action == "close_build":
                        self.active_panel = None
                    elif isinstance(action, tuple) and action[0] == "select_build":
                        self.building_system.selected_building = action[1]
                    return
            world_pos = self.camera.screen_to_world(event.pos)
            building_id = self.building_system.selected_building
            if self.building_system.build(self.player, self.world, building_id, world_pos):
                self._quest_event("build", building_id, 1)
                if building_id in {"torch", "campfire", "stone_stove"}:
                    self._quest_event("use_light", building_id, 1)
                self.notifications.push(self.building_system.message)
                self.particles.emit(world_pos, color=COLORS["accent"], amount=12, speed=70, lifetime=0.55, radius=3)
            else:
                self.notifications.push(self.building_system.message)

    def _handle_crafting_event(self, event) -> None:
        if not self.player:
            return
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.craft_search = self.craft_search[:-1]
            elif event.key == pygame.K_ESCAPE:
                self.active_panel = None
            elif event.unicode and event.unicode.isprintable() and len(self.craft_search) < 24:
                self.craft_search += event.unicode
            return
        if event.type in {pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION}:
            for button in self.craft_buttons:
                action = button.handle_event(event)
                if not action:
                    continue
                if action == "close_crafting":
                    self.active_panel = None
                elif action == "clear_search":
                    self.craft_search = ""
                elif isinstance(action, tuple) and action[0] == "select_recipe":
                    self.selected_recipe_id = action[1]
                elif isinstance(action, tuple) and action[0] == "craft":
                    success = self.crafting_system.craft(self.player, action[1], station_id=self._active_station_id())
                    self.notifications.push(self.crafting_system.message)
                    if success:
                        recipe = self.crafting_system.recipes.get(action[1], {})
                        output_id, amount = recipe.get("output", (action[1], 1))
                        self._quest_event("craft", output_id, int(amount))

    def _handle_cooking_event(self, event) -> None:
        if not self.player:
            return
        if event.type in {pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION}:
            for button in self.cooking_buttons:
                action = button.handle_event(event)
                if not action:
                    continue
                if action == "close_cooking":
                    self.active_panel = None
                elif isinstance(action, tuple) and action[0] == "cook":
                    self._cook_item(action[1])
                elif isinstance(action, tuple) and action[0] == "craft_food":
                    success = self.crafting_system.craft(self.player, action[1], station_id=self._active_station_id())
                    self.notifications.push(self.crafting_system.message)
                    if success:
                        recipe = self.crafting_system.recipes.get(action[1], {})
                        output_id, amount = recipe.get("output", (action[1], 1))
                        self._quest_event("craft", output_id, int(amount))
                    if self.crafting_system.message.startswith("Criou"):
                        self.particles.emit(self.player.center, color=COLORS["accent_2"], amount=10, speed=60, lifetime=0.45, radius=3)

    def _handle_chest_event(self, event) -> None:
        if not self.player:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for button in self.chest_buttons:
                action = button.handle_event(event)
                if not action:
                    continue
                if action == "close_chest":
                    self.active_panel = None
                    self.active_structure = None
                else:
                    self._handle_inventory_action(action)
                return
            for ref, rect in self.chest_slot_rects.items():
                if rect.collidepoint(event.pos):
                    self.chest_selected_ref = ref
                    self.chest_dragging_ref = ref
                    return
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.chest_dragging_ref:
            target = self._chest_slot_at(event.pos)
            source = self.chest_dragging_ref
            self.chest_dragging_ref = None
            if target and target != source:
                self.chest_selected_ref = target
                self._move_between_inventories(source[0], source[1], target[0], target[1])
        if event.type == pygame.MOUSEMOTION:
            for button in self.chest_buttons:
                button.handle_event(event)

    def _chest_slot_at(self, pos) -> tuple[str, int] | None:
        for ref, rect in self.chest_slot_rects.items():
            if rect.collidepoint(pos):
                return ref
        return None

    def _cook_item(self, raw_id: str) -> None:
        if not self.player:
            return
        result = self.cooking_system.start_cooking(self.player, self.player.inventory, raw_id, self._active_station_id())
        self.notifications.push(result["message"])
        if result.get("success"):
            self.particles.emit(self.player.center, color=(233, 125, 57), amount=11, speed=62, lifetime=0.5, radius=3)

    def _active_station_id(self) -> str | None:
        if self.active_structure:
            return self.active_structure.building_id
        return None

    def new_game(self, name: str, class_id: str) -> None:
        self.world = World(self.assets)
        self._place_initial_camp()
        self.player = Player(name, class_id, self.world.spawn_pos, self.assets)
        self.camera = Camera(self.screen.get_size(), (self.world.pixel_width, self.world.pixel_height))
        self.npcs = [NPC("Mira", "Vendedora", self.world.vendor_pos, self.assets, vendor=True)]
        self.enemies = self._spawn_initial_enemies()
        self.animals = self._spawn_initial_animals()
        self.economy = EconomySystem()
        self.shop_system = ShopSystem(self.economy)
        self.combat_system = CombatSystem()
        self.consumable_system = ConsumableSystem()
        self.cooking_system = CookingSystem()
        self.drop_system = DropSystem(self._rng)
        self.time_system = TimeSystem()
        self.weather_system = WeatherSystem()
        self.lighting_system = LightingSystem(self.screen.get_size())
        self.particles = ParticleManager()
        self.exploration = MapExplorationSystem(self.world)
        self.crafting_system = CraftingSystem()
        self.building_system = BuildingSystem()
        self.quest_system = QuestSystem(player=self.player)
        self.active_panel = None
        self.state = "playing"
        self.notifications.push("Voce acordou perdido na floresta.")
        self.notifications.push("Use E na bancada inicial para craftar itens.")
        self.notifications.push("Encontre Mira para comprar ferramentas.")

    def _place_initial_camp(self) -> None:
        if not self.world:
            return
        sx, sy = self.world.spawn_tile
        for building_id, tile in [
            ("workbench", (sx + 2, sy + 1)),
            ("campfire", (sx - 2, sy + 1)),
        ]:
            if self.world.can_place_structure(tile):
                self.world.add_structure(building_id, tile)

    def _spawn_initial_enemies(self) -> list[Enemy]:
        if not self.world:
            return []
        enemies: list[Enemy] = []
        spawn = self.world.spawn_tile
        offsets = [
            (9, 8), (-10, 11), (14, -10), (-17, -8), (24, 5), (5, 23), (-22, 19),
            (30, -14), (38, 7), (-36, -15), (17, 34), (-28, 32), (42, -28), (-44, 12),
        ]
        for index, (ox, oy) in enumerate(offsets):
            tile = (spawn[0] + ox, spawn[1] + oy)
            if self.world.can_place_structure(tile):
                pos = pygame.Vector2((tile[0] + 0.5) * Settings.TILE_SIZE, (tile[1] + 0.5) * Settings.TILE_SIZE)
                kind = ENEMY_ORDER[index % len(ENEMY_ORDER)]
                base_level = 1 + (index % 5)
                enemies.append(Enemy(kind, pos, self.assets, base_level=base_level))
        return enemies

    def _spawn_initial_animals(self) -> list[Animal]:
        if not self.world:
            return []
        animals: list[Animal] = []
        spawn = self.world.spawn_tile
        offsets = [(-7, 4), (-8, -5), (6, -6), (8, 5), (12, 11), (-13, 10), (15, -3), (-15, -9), (4, 14)]
        for index, (ox, oy) in enumerate(offsets):
            tile = (spawn[0] + ox, spawn[1] + oy)
            if self.world.can_place_structure(tile):
                pos = pygame.Vector2((tile[0] + 0.5) * Settings.TILE_SIZE, (tile[1] + 0.5) * Settings.TILE_SIZE)
                animals.append(Animal(ANIMAL_ORDER[index % len(ANIMAL_ORDER)], pos, self.assets))
        return animals

    def _update(self, dt: float) -> None:
        update_start = perf_counter()
        self.input.refresh()
        self.death_message_timer = max(0.0, self.death_message_timer - dt)
        if self.state == "main_menu":
            self.main_menu.update(dt)
        elif self.state == "playing":
            self._update_playing(dt)
        self.notifications.update(dt)
        self.performance_stats["update_ms"] = (perf_counter() - update_start) * 1000

    def _update_playing(self, dt: float) -> None:
        if not all([self.player, self.world, self.camera, self.exploration]):
            return
        ui_open = self.active_panel in {"inventory", "shop", "character", "skills", "map", "building", "crafting", "cooking", "chest", "dialogue", "quests"}
        paused = self.active_panel == "pause"
        updated_entities = 0
        
        if not paused:
            if not ui_open:
                self.player.update(dt, self.input, self.world, self.weather_system, self.particles)
            self.world.update(dt)
            for npc in self.npcs:
                npc.update(dt)
                updated_entities += 1
            for animal in self.animals:
                animal.update(dt, self.world)
                updated_entities += 1
            for enemy in self.enemies:
                enemy.update(dt, self.player, self.world)
                updated_entities += 1
                attack_range = enemy.attack_range if enemy.ranged else 34
                if enemy.alive and enemy.center.distance_to(self.player.center) <= attack_range and enemy.attack_cooldown <= 0:
                    self.combat_system.enemy_attack_player(enemy, self.player, self.particles, self.notifications)
                    enemy.attack_cooldown = 1.8 if enemy.ranged else 1.2
            was_night = self.time_system.is_night()
            new_day = self.time_system.update(dt)
            self.weather_system.update(dt, new_day)
            for result in self.cooking_system.update(dt, self.player):
                self.notifications.push(result["message"])
                if result.get("success") and result.get("output_id"):
                    self._quest_event("cook", result["output_id"], 1)
            if new_day:
                reading = ReadingSystem().read_day_progress(self.player)
                if reading.get("success"):
                    self.notifications.push(reading["message"])
                    for reward in reading.get("rewards", []):
                        self.notifications.push(reward)
                    if reading.get("book_id"):
                        self._quest_event("read_book", reading["book_id"], 1, {"skill": reading.get("target_skill", "")})
                    if int(reading.get("skill_xp", 0) or 0) > 0:
                        self._quest_event(
                            "skill_xp",
                            reading.get("target_skill", ""),
                            int(reading.get("skill_xp", 0) or 0),
                            {"skill": reading.get("target_skill", ""), "xp": int(reading.get("skill_xp", 0) or 0)},
                        )
            if was_night and not self.time_system.is_night():
                self._quest_event("survive_night", "night", 1)
            reveal_radius = 170 + self.player.skills.exploration_radius_bonus()
            if self.player.class_id == "explorer":
                reveal_radius += 48
            self.exploration.reveal_around(self.player.center, reveal_radius)
            if self.time_system.is_night():
                self._quest_event("explore", "night", 1, {"is_night": True})
            if self.player.center.distance_to(self.world.spawn_pos) <= 130:
                self._quest_event("return", "camp", 1)
            self.quest_system.update(dt, self.player)
            self._drain_quest_messages()
            if not self.player.alive:
                self._handle_player_death()
        self.particles.update(dt)
        self.camera.update(self.player.center)
        self.performance_stats["updated_entities"] = updated_entities

    def _handle_player_death(self) -> None:
        if not self.player or not self.world:
            return
        self.player.drop_all_items(self.world)
        self.player.alive = True
        self.player.pos = self.world.spawn_pos.copy()
        self.player.hp = self.player.max_hp
        self.player.hunger = 55
        self.player.thirst = 55
        self.player.energy = 45
        self.death_message_timer = 3.2
        self.notifications.push("Voce morreu.")

    def _draw(self) -> None:
        render_start = perf_counter()
        if self.state == "main_menu":
            self.main_menu.draw(self.screen)
        elif self.state == "settings":
            self.settings_menu.draw(self.screen)
        elif self.state == "character_creation":
            self.character_creation.draw(self.screen)
        elif self.state == "playing":
            self._draw_playing()
        pygame.display.flip()
        self.performance_stats["render_ms"] = (perf_counter() - render_start) * 1000

    def _draw_playing(self) -> None:
        if not all([self.player, self.world, self.camera, self.exploration]):
            self.screen.fill(COLORS["black"])
            return
        self.world.draw(self.screen, self.camera, self.exploration)
        visible_rect = pygame.Rect(
            self.camera.offset.x - Settings.RENDER_MARGIN,
            self.camera.offset.y - Settings.RENDER_MARGIN,
            self.camera.screen_width + Settings.RENDER_MARGIN * 2,
            self.camera.screen_height + Settings.RENDER_MARGIN * 2,
        )
        drawables = []
        for npc in self.npcs:
            if npc.rect.colliderect(visible_rect):
                drawables.append((npc.rect.bottom, npc))
        for enemy in self.enemies:
            if enemy.alive and enemy.rect.colliderect(visible_rect):
                drawables.append((enemy.rect.bottom, enemy))
        for animal in self.animals:
            if animal.alive and animal.rect.colliderect(visible_rect):
                drawables.append((animal.rect.bottom, animal))
        drawables.append((self.player.rect.bottom, self.player))
        rendered_entities = 0
        for _, entity in sorted(drawables, key=lambda item: item[0]):
            entity.draw(self.screen, self.camera)
            rendered_entities += 1
        drawn_particles = self.particles.draw(self.screen, self.camera)
        self.performance_stats["rendered_entities"] = rendered_entities
        self.performance_stats["drawn_particles"] = drawn_particles
        self._draw_world_overlays()

        interaction_text = self._interaction_text()
        self.hud.draw(
            self.screen,
            self.player,
            self.world,
            self.exploration,
            self.npcs,
            self.enemies,
            self.time_system,
            self.weather_system,
            interaction_text,
            self.notifications,
            self.quest_system,
            self.settings_menu.show_fps,
            self.clock.get_fps(),
        )
        self._draw_active_panel()
        if self.death_message_timer > 0:
            self._draw_death_message()
        if self.show_performance_debug:
            self._draw_performance_debug()

    def _draw_death_message(self) -> None:
        alpha = max(0, min(255, int(255 * min(1, self.death_message_timer / 0.7))))
        overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, min(150, alpha)))
        self.screen.blit(overlay, (0, 0))
        font = pygame.font.SysFont(Settings.UI_FONT, 52, bold=True)
        text = "Voce morreu"
        image = font.render(text, True, (230, 70, 70))
        shadow = font.render(text, True, (20, 8, 8))
        rect = image.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))
        self.screen.blit(shadow, rect.move(3, 3))
        self.screen.blit(image, rect)

    def _draw_performance_debug(self) -> None:
        lines = [
            f"FPS: {self.clock.get_fps():.0f}",
            f"Update: {self.performance_stats['update_ms']:.2f} ms",
            f"Render: {self.performance_stats['render_ms']:.2f} ms",
            f"Entidades draw/update: {self.performance_stats['rendered_entities']}/{self.performance_stats['updated_entities']}",
            f"Particulas: {len(self.particles.particles)} total, {self.performance_stats['drawn_particles']} visiveis",
            f"Luzes processadas: {self.performance_stats['processed_lights']}",
            f"Fase: {self.time_system.get_day_phase()} alpha {self.time_system.get_darkness_alpha()}",
        ]
        panel = pygame.Rect(14, self.screen.get_height() - 178, 330, 158)
        pygame.draw.rect(self.screen, (8, 10, 10, 210), panel, border_radius=6)
        pygame.draw.rect(self.screen, (76, 88, 80), panel, 1, border_radius=6)
        for index, line in enumerate(lines):
            draw_text(self.screen, line, (panel.x + 12, panel.y + 10 + index * 20), COLORS["white"], 13)

    def _draw_world_overlays(self) -> None:
        color, w_alpha = self.weather_system.overlay()
        if w_alpha > 0:
            overlay = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
            overlay.fill((color[0], color[1], color[2], w_alpha))
            self.screen.blit(overlay, (0, 0))
        if self.world and self.camera and self.player:
            processed = self.lighting_system.render(
                self.screen,
                self.camera,
                self.time_system,
                self.world.light_sources(self.weather_system),
                self.player,
                self.weather_system,
            )
            self.performance_stats["processed_lights"] = processed

    def _draw_active_panel(self) -> None:
        if not self.active_panel or not self.player or not self.world or not self.exploration:
            return
        shade = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        shade.fill((0, 0, 0, 92))
        if self.active_panel not in {"building"}:
            self.screen.blit(shade, (0, 0))
        if self.active_panel == "inventory":
            self.inventory_ui.draw(self.screen, self.player)
        elif self.active_panel == "shop":
            self.shop_ui.draw(self.screen, self.player, self.shop_system)
        elif self.active_panel == "character":
            self.character_ui.draw(self.screen, self.player, self.quest_system)
        elif self.active_panel == "quests":
            self.quest_ui.draw(self.screen, self.player, self.quest_system)
        elif self.active_panel == "skills":
            self.character_ui.draw_skills_only(self.screen, self.player)
        elif self.active_panel == "map":
            rect = pygame.Rect(90, 54, self.screen.get_width() - 180, self.screen.get_height() - 108)
            self.expanded_minimap.draw(self.screen, self.world, self.exploration, self.player, self.npcs, self.enemies, rect, expanded=True)
        elif self.active_panel == "pause":
            self._draw_pause_panel()
        elif self.active_panel == "building":
            self._draw_building_panel()
        elif self.active_panel == "crafting":
            self._draw_crafting_panel()
        elif self.active_panel == "cooking":
            self._draw_cooking_panel()
        elif self.active_panel == "chest":
            self._draw_chest_panel()
        elif self.active_panel == "dialogue":
            self.dialogue_ui.draw(self.screen)

    def _draw_pause_panel(self) -> None:
        panel = pygame.Rect(self.screen.get_width() // 2 - 170, self.screen.get_height() // 2 - 180, 340, 360)
        draw_panel(self.screen, panel, "Pausa")
        specs = [
            ("Continuar", "resume"),
            ("Salvar", "save"),
            ("Configuracoes", "settings"),
            ("Menu Inicial", "main_menu"),
            ("Sair", "quit"),
        ]
        self.pause_buttons = []
        for index, (label, action) in enumerate(specs):
            button = Button((panel.x + 55, panel.y + 70 + index * 52, 230, 38), label, action)
            button.draw(self.screen)
            self.pause_buttons.append(button)

    def _draw_building_panel(self) -> None:
        if not self.player:
            return
        panel = pygame.Rect(18, 154, 310, 430)
        draw_panel(self.screen, panel, "Construcao")
        draw_text(self.screen, "Clique no mundo para posicionar.", (panel.x + 16, panel.y + 46), (183, 190, 178), 13)
        self.build_buttons = []
        y = panel.y + 78
        for building_id in self.building_system.unlocked(self.player):
            label = ITEMS.get(building_id, {}).get("name", building_id)
            selected = building_id == self.building_system.selected_building
            button = Button((panel.x + 14, y, 132, 30), label[:18], ("select_build", building_id))
            button.hovered = selected
            button.draw(self.screen)
            self.build_buttons.append(button)
            costs = self.building_system.adjusted_cost(self.player, building_id)
            cost_text = ", ".join(f"{amt} {ITEMS[item]['name']}" for item, amt in costs.items())
            draw_text(self.screen, cost_text[:32], (panel.x + 156, y + 8), COLORS["white"], 12)
            y += 38
            if y > panel.bottom - 52:
                break
        close = Button((panel.x + 86, panel.bottom - 42, 140, 32), "Fechar", "close_build")
        close.draw(self.screen)
        self.build_buttons.append(close)
        selected = self.building_system.selected_building
        draw_text(self.screen, self.building_system.message, (panel.x + 16, panel.bottom - 72), COLORS["white"], 12)
        draw_text(self.screen, f"Selecionado: {ITEMS.get(selected, {}).get('name', selected)}", (panel.x + 16, panel.bottom - 96), COLORS["accent"], 13, bold=True)

    def _draw_crafting_panel(self) -> None:
        if not self.player:
            return
        panel = pygame.Rect(self.screen.get_width() // 2 - 520, self.screen.get_height() // 2 - 315, 1040, 630)
        draw_panel(self.screen, panel, "Crafting")
        recipes = self.crafting_system.unlocked_recipes(self.player)
        query = self.craft_search.lower().strip()
        filtered = [
            (recipe_id, recipe)
            for recipe_id, recipe in recipes.items()
            if not query or query in recipe["name"].lower()
        ]
        filtered.sort(key=lambda item: item[1]["name"])
        filtered_ids = {recipe_id for recipe_id, _ in filtered}
        if self.selected_recipe_id not in filtered_ids:
            self.selected_recipe_id = filtered[0][0] if filtered else None
        self.craft_buttons = []

        search_rect = pygame.Rect(panel.x + 90, panel.y + 48, 450, 34)
        pygame.draw.rect(self.screen, COLORS["panel_dark"], search_rect, border_radius=5)
        pygame.draw.rect(self.screen, (78, 89, 82), search_rect, 1, border_radius=5)
        draw_text(self.screen, self.craft_search or "Tudo liberado", (search_rect.x + 12, search_rect.y + 8), (216, 208, 178), 14, bold=True)
        clear = Button((search_rect.right + 10, search_rect.y, 74, 34), "Limpar", "clear_search")
        clear.draw(self.screen)
        self.craft_buttons.append(clear)

        grid_rect = pygame.Rect(panel.x + 24, panel.y + 96, 640, 420)
        detail_rect = pygame.Rect(panel.x + 684, panel.y + 96, 332, 470)
        pygame.draw.rect(self.screen, (43, 31, 23), grid_rect, border_radius=5)
        pygame.draw.rect(self.screen, (94, 71, 45), grid_rect, 2, border_radius=5)
        pygame.draw.rect(self.screen, COLORS["panel_dark"], detail_rect, border_radius=6)
        pygame.draw.rect(self.screen, (94, 71, 45), detail_rect, 2, border_radius=6)

        cell = 58
        gap = 10
        cols = 9
        start_x = grid_rect.x + 18
        start_y = grid_rect.y + 18
        mouse_pos = pygame.mouse.get_pos()
        hovered_recipe_output = None

        for index, (recipe_id, recipe) in enumerate(filtered[:54]):
            col = index % cols
            row = index // cols
            rect = pygame.Rect(start_x + col * (cell + gap), start_y + row * (cell + gap), cell, cell)
            output_id, amount = recipe["output"]
            if rect.collidepoint(mouse_pos):
                hovered_recipe_output = output_id
            can_materials = self.player.can_pay_items(recipe["ingredients"]) if hasattr(self.player, "can_pay_items") else self.player.inventory.can_pay(recipe["ingredients"])
            can_space = self.player.can_receive_item(output_id, amount) if hasattr(self.player, "can_receive_item") else self.player.inventory.can_accept_item(output_id, amount)
            selected = recipe_id == self.selected_recipe_id
            bg = (72, 55, 36) if selected else (31, 34, 31)
            border = COLORS["accent"] if selected else (118, 91, 55)
            if not can_materials:
                border = (111, 76, 66)
            elif can_space:
                border = (93, 154, 89)
            pygame.draw.rect(self.screen, bg, rect, border_radius=4)
            pygame.draw.rect(self.screen, border, rect, 2, border_radius=4)
            icon = self.assets.item_icon(output_id, 38)
            self.screen.blit(icon, (rect.centerx - 19, rect.centery - 20))
            if amount > 1:
                draw_text(self.screen, str(amount), (rect.right - 18, rect.bottom - 18), COLORS["white"], 12, bold=True)
            button = Button(rect, "", ("select_recipe", recipe_id))
            self.craft_buttons.append(button)

        if not filtered:
            draw_text(self.screen, "Nenhuma receita encontrada.", grid_rect.center, COLORS["white"], 18, center=True)

        selected = recipes.get(self.selected_recipe_id) if self.selected_recipe_id else None
        if selected:
            output_id, amount = selected["output"]
            item_data = ITEMS.get(output_id, {})
            item_name = item_data.get("name", output_id)
            surface_icon = self.assets.item_icon(output_id, 56)
            self.screen.blit(surface_icon, (detail_rect.x + 18, detail_rect.y + 18))
            draw_text(self.screen, selected.get("name", item_name), (detail_rect.x + 88, detail_rect.y + 18), COLORS["accent"], 21, bold=True)
            draw_text(self.screen, f"Cria: {amount}x {item_name}", (detail_rect.x + 88, detail_rect.y + 48), COLORS["white"], 13)
            draw_wrapped(self.screen, item_data.get("description", ""), pygame.Rect(detail_rect.x + 18, detail_rect.y + 86, detail_rect.width - 36, 58), COLORS["white"], 13)

            draw_text(self.screen, "Materiais", (detail_rect.x + 18, detail_rect.y + 152), COLORS["accent"], 17, bold=True)
            y = detail_rect.y + 182
            can_materials = True
            for item_id, needed in selected["ingredients"].items():
                owned = self.player.count_item(item_id) if hasattr(self.player, "count_item") else self.player.inventory.count(item_id)
                ok = owned >= needed
                can_materials = can_materials and ok
                color = COLORS["accent_2"] if ok else COLORS["danger"]
                self.screen.blit(self.assets.item_icon(item_id, 24), (detail_rect.x + 20, y - 3))
                ingredient_name = ITEMS.get(item_id, {}).get("name", item_id)
                draw_text(self.screen, f"{ingredient_name}: {owned}/{needed}", (detail_rect.x + 52, y), color, 15, bold=True)
                y += 32

            draw_text(self.screen, "Pode fazer", (detail_rect.x + 18, y + 10), COLORS["accent"], 17, bold=True)
            y += 40
            for line in self._craft_usage_lines(output_id)[:5]:
                draw_wrapped(self.screen, f"- {line}", pygame.Rect(detail_rect.x + 22, y, detail_rect.width - 44, 34), COLORS["white"], 13)
                y += 28

            can_space = self.player.can_receive_item(output_id, amount) if hasattr(self.player, "can_receive_item") else self.player.inventory.can_accept_item(output_id, amount)
            can_station = self.crafting_system.station_ok(selected, self._active_station_id())
            can_craft = can_materials and can_space and can_station
            if not can_space:
                draw_text(self.screen, "Inventario cheio", (detail_rect.x + 18, detail_rect.bottom - 86), COLORS["danger"], 14, bold=True)
            elif not can_station:
                required = friendly_station_name(selected.get("required_station"))
                draw_text(self.screen, f"Requer: {required}", (detail_rect.x + 18, detail_rect.bottom - 86), COLORS["danger"], 14, bold=True)
            create = Button((detail_rect.x + 18, detail_rect.bottom - 54, 120, 36), "Criar", ("craft", self.selected_recipe_id), disabled=not can_craft)
            create.draw(self.screen)
            self.craft_buttons.append(create)
            draw_wrapped(self.screen, self.crafting_system.message, pygame.Rect(detail_rect.x + 154, detail_rect.bottom - 54, detail_rect.width - 170, 42), COLORS["white"], 13)
        else:
            draw_text(self.screen, "Nenhuma receita encontrada.", (detail_rect.x + 20, detail_rect.y + 22), COLORS["white"], 16)

        draw_text(self.screen, "Clique em uma receita. Digite para pesquisar. Botao direito no chao coloca construcoes equipadas.", (grid_rect.x + 8, panel.bottom - 78), (190, 181, 148), 13)
        close = Button((panel.centerx - 70, panel.bottom - 48, 140, 34), "Fechar", "close_crafting")
        close.draw(self.screen)
        self.craft_buttons.append(close)

        if hovered_recipe_output:
            from src.items.item import make_item
            from src.ui.widgets import draw_item_tooltip
            draw_item_tooltip(self.screen, make_item(hovered_recipe_output), mouse_pos)

    def _craft_usage_lines(self, item_id: str) -> list[str]:
        data = ITEMS[item_id]
        lines: list[str] = []
        if data.get("type") == "building":
            lines.append("Pode ser equipado e colocado no chao com botao direito.")
            building = data.get("building", item_id)
            if building == "workbench":
                lines.append("Depois de colocado, use E para abrir crafting.")
            elif building == "stone_stove":
                lines.append("Depois de colocado, use E para assar carnes e peixes.")
            elif building in {"torch", "campfire"}:
                lines.append("Ilumina a area ao redor durante a noite.")
            elif building in {"chest", "small_chest"}:
                lines.append("Guarda itens, abre com E e pode ser quebrado com machado.")
        elif data.get("type") in {"weapon", "tool"}:
            lines.append("Pode ser equipado na hotbar para combate, coleta ou interacao.")
            if data.get("tool_type"):
                lines.append(f"Ferramenta do tipo {data['tool_type']}.")
        elif data.get("type") in {"food", "potion"}:
            lines.append("Uso proprio: consuma pelo inventario ou pela hotbar com Q.")
        elif data.get("type") == "drink":
            lines.append("Bebida consumivel pela hotbar com Q.")
        else:
            lines.append("Material ou item de suporte para receitas futuras.")
        recipe = data.get("recipe") or {}
        if recipe.get("required_station"):
            lines.append(f"Estacao: {friendly_station_name(recipe['required_station'])}.")
        effects = data.get("effects") or {}
        if effects:
            for key, label in [("health", "Vida"), ("hunger", "Fome"), ("thirst", "Sede"), ("energy", "Energia"), ("mana", "Mana"), ("mana_percent", "Mana max")]:
                value = effects.get(key)
                if value:
                    prefix = "+" if value > 0 else ""
                    suffix = "%" if key == "mana_percent" else ""
                    lines.append(f"{prefix}{value}{suffix} {label}.")
        if effects:
            return lines
        if data.get("heal"):
            lines.append(f"Recupera {data['heal']} HP.")
        if data.get("hunger"):
            lines.append(f"Sacia {data['hunger']} de fome.")
        if data.get("thirst"):
            lines.append(f"Recupera {data['thirst']} de sede.")
        return lines

    def _draw_cooking_panel(self) -> None:
        if not self.player:
            return
        panel = pygame.Rect(self.screen.get_width() // 2 - 370, self.screen.get_height() // 2 - 290, 740, 580)
        draw_panel(self.screen, panel, "Cozinha")
        draw_text(self.screen, "Assar alimentos crus", (panel.x + 24, panel.y + 58), COLORS["accent"], 16, bold=True)
        self.cooking_buttons = []
        y = panel.y + 88
        station_id = self._active_station_id()
        recipes = self.cooking_system.available_recipes(self.player, station_id)
        recipe_items = sorted(
            recipes.items(),
            key=lambda item: (self.player.count_item(item[0]) <= 0, ITEMS[item[0]]["name"]),
        )
        mouse_pos = pygame.mouse.get_pos()
        hovered_cooking_item = None
        for raw_id, recipe in recipe_items[:5]:
            owned = self.player.inventory.count(raw_id)
            backpack = self.player.backpack_contents()
            if backpack is not None:
                owned += sum(slot.quantity for slot in backpack if slot and slot.item_id == raw_id)
            row = pygame.Rect(panel.x + 24, y, panel.width - 48, 42)
            if row.collidepoint(mouse_pos):
                hovered_cooking_item = recipe["output"]
            pygame.draw.rect(self.screen, COLORS["panel_dark"], row, border_radius=5)
            self.screen.blit(self.assets.item_icon(raw_id, 26), (row.x + 8, row.y + 8))
            self.screen.blit(self.assets.item_icon(recipe["output"], 26), (row.x + 274, row.y + 8))
            draw_text(self.screen, f"{ITEMS[raw_id]['name']} x{owned}", (row.x + 44, row.y + 12), COLORS["white"], 13, bold=True)
            draw_text(self.screen, "->", (row.x + 244, row.y + 12), COLORS["accent"], 13, bold=True)
            draw_text(self.screen, ITEMS[recipe["output"]]["name"], (row.x + 310, row.y + 12), COLORS["white"], 13, bold=True)
            button = Button((row.right - 86, row.y + 6, 74, 30), "Assar", ("cook", raw_id), disabled=owned <= 0)
            button.draw(self.screen)
            self.cooking_buttons.append(button)
            y += 48
        if not recipes:
            draw_text(self.screen, "Nenhuma receita valida nesta estacao.", (panel.x + 24, y + 8), COLORS["white"], 14)

        y = panel.y + 350
        draw_text(self.screen, "Preparos, sucos e pocoes", (panel.x + 24, y), COLORS["accent"], 16, bold=True)
        y += 30
        craft_recipes = [
            (recipe_id, recipe)
            for recipe_id, recipe in self.crafting_system.unlocked_recipes(self.player).items()
            if recipe.get("source") == "foods.json" and self.crafting_system.station_ok(recipe, station_id)
        ]
        craft_recipes.sort(key=lambda item: ITEMS[item[1]["output"][0]]["name"])
        for recipe_id, recipe in craft_recipes[:3]:
            output_id, amount = recipe["output"]
            ingredients = recipe["ingredients"]
            can_materials = self.player.can_pay_items(ingredients)
            can_space = self.player.can_receive_item(output_id, amount)
            row = pygame.Rect(panel.x + 24, y, panel.width - 48, 42)
            if row.collidepoint(mouse_pos):
                hovered_cooking_item = output_id
            pygame.draw.rect(self.screen, COLORS["panel_dark"], row, border_radius=5)
            self.screen.blit(self.assets.item_icon(output_id, 26), (row.x + 8, row.y + 8))
            draw_text(self.screen, f"{ITEMS[output_id]['name']} x{amount}", (row.x + 44, row.y + 6), COLORS["white"], 13, bold=True)
            cost = ", ".join(f"{qty} {ITEMS[item_id]['name']}" for item_id, qty in ingredients.items())
            draw_text(self.screen, cost[:52], (row.x + 44, row.y + 23), (185, 192, 180), 11)
            button = Button((row.right - 92, row.y + 6, 80, 30), "Criar", ("craft_food", recipe_id), disabled=not (can_materials and can_space))
            button.draw(self.screen)
            self.cooking_buttons.append(button)
            y += 48
        if not craft_recipes:
            draw_text(self.screen, "Sem preparos liberados nesta estacao.", (panel.x + 24, y + 8), COLORS["white"], 14)
        task_y = panel.bottom - 112
        if self.cooking_system.tasks:
            draw_text(self.screen, "Em preparo", (panel.x + 24, task_y), COLORS["accent"], 15, bold=True)
            task = self.cooking_system.tasks[0]
            progress = 1 - max(0, task.remaining_time) / max(0.1, task.total_time)
            bar = pygame.Rect(panel.x + 120, task_y + 2, 220, 12)
            pygame.draw.rect(self.screen, (49, 54, 49), bar, border_radius=4)
            fill = bar.copy()
            fill.width = max(1, int(bar.width * progress))
            pygame.draw.rect(self.screen, (233, 125, 57), fill, border_radius=4)
            draw_text(self.screen, f"{ITEMS[task.result_item_id]['name']} {max(0, task.remaining_time):.1f}s", (bar.right + 12, task_y - 2), COLORS["white"], 13)
        close = Button((panel.centerx - 70, panel.bottom - 48, 140, 34), "Fechar", "close_cooking")
        close.draw(self.screen)
        self.cooking_buttons.append(close)

        if hovered_cooking_item:
            from src.items.item import make_item
            from src.ui.widgets import draw_item_tooltip
            draw_item_tooltip(self.screen, make_item(hovered_cooking_item), mouse_pos)

    def _draw_chest_panel(self) -> None:
        if not self.player:
            return
        contents = self._active_chest_contents()
        if contents is None:
            self.active_panel = None
            self.active_structure = None
            return
        width = min(1100, self.screen.get_width() - 48)
        height = min(620, self.screen.get_height() - 44)
        panel = pygame.Rect(self.screen.get_width() // 2 - width // 2, self.screen.get_height() // 2 - height // 2, width, height)
        draw_panel(self.screen, panel, "Bau Pequeno")
        self.chest_buttons = []
        self.chest_slot_rects = {}

        left_x = panel.x + 24
        chest_x = panel.x + 390
        details = pygame.Rect(panel.right - 330, panel.y + 84, 306, panel.height - 142)
        main_used = sum(1 for slot in self.player.inventory.slots if slot)
        chest_used = sum(1 for slot in contents if slot)
        draw_text(self.screen, f"Inventario: {main_used}/{self.player.inventory.capacity}", (left_x, panel.y + 50), COLORS["white"], 14)
        draw_text(self.screen, "Hotbar", (left_x, panel.y + 82), COLORS["accent"], 16, bold=True)
        self._draw_chest_grid(self.screen, self.player.inventory.slots[:5], "main", 0, left_x, panel.y + 108, 5)
        draw_text(self.screen, "Inventario", (left_x, panel.y + 176), COLORS["accent"], 16, bold=True)
        self._draw_chest_grid(self.screen, self.player.inventory.slots[5:], "main", 5, left_x, panel.y + 202, 5)

        backpack_slots = self.player.backpack_contents()
        backpack_y = panel.y + 406
        draw_text(self.screen, "Mochila", (left_x, backpack_y - 26), COLORS["accent"], 16, bold=True)
        if backpack_slots is not None:
            used = sum(1 for slot in backpack_slots if slot)
            draw_text(self.screen, f"{used}/{len(backpack_slots)}", (left_x + 94, backpack_y - 22), COLORS["white"], 13)
            self._draw_chest_grid(self.screen, backpack_slots, "backpack", 0, left_x, backpack_y, 4)
        else:
            empty = pygame.Rect(left_x, backpack_y, 262, 74)
            pygame.draw.rect(self.screen, COLORS["panel_dark"], empty, border_radius=6)
            pygame.draw.rect(self.screen, (71, 82, 76), empty, 1, border_radius=6)
            draw_wrapped(self.screen, "Sem mochila equipada.", empty.inflate(-14, -14), COLORS["white"], 13)

        draw_text(self.screen, f"Bau: {chest_used}/{len(contents)}", (chest_x, panel.y + 50), COLORS["white"], 14)
        draw_text(self.screen, "Armazenamento", (chest_x, panel.y + 82), COLORS["accent"], 16, bold=True)
        self._draw_chest_grid(self.screen, contents, "chest", 0, chest_x, panel.y + 108, 4)

        self._draw_chest_details(details)
        close = Button((panel.centerx - 70, panel.bottom - 46, 140, 34), "Fechar", "close_chest")
        close.draw(self.screen)
        self.chest_buttons.append(close)

        mouse_pos = pygame.mouse.get_pos()
        hovered_ref = self._chest_slot_at(mouse_pos)
        if hovered_ref:
            source, index = hovered_ref
            inventory = self._inventory_for_source(source)
            if inventory and index < inventory.capacity:
                slot = inventory.slots[index]
                if slot:
                    from src.ui.widgets import draw_item_tooltip
                    draw_item_tooltip(self.screen, slot.item, mouse_pos, slot)

    def _draw_chest_grid(self, surface, slots, source: str, start_index: int, x: int, y: int, columns: int) -> None:
        slot_size = 52
        gap = 8
        rows = max(1, (len(slots) + columns - 1) // columns)
        for local_index in range(len(slots)):
            col = local_index % columns
            row = local_index // columns
            rect = pygame.Rect(x + col * (slot_size + gap), y + row * (slot_size + gap), slot_size, slot_size)
            absolute_index = start_index + local_index
            ref = (source, absolute_index)
            self.chest_slot_rects[ref] = rect
            selected = self.chest_selected_ref == ref
            slot = slots[local_index]
            pygame.draw.rect(surface, (64, 76, 70) if selected else COLORS["panel_dark"], rect, border_radius=6)
            border = COLORS["accent"] if selected else (75, 85, 78)
            if source == "main" and absolute_index == self.player.inventory.selected_slot:
                border = (235, 218, 120)
            if source == "main" and absolute_index == self.player.equipped_backpack_slot:
                border = (105, 190, 230)
            pygame.draw.rect(surface, border, rect, 2, border_radius=6)
            if source == "main" and absolute_index < 5:
                draw_text(surface, str(absolute_index + 1), (rect.x + 5, rect.y + 3), (187, 194, 183), 11, bold=True)
            if slot:
                icon = self.assets.item_icon(slot.item_id, 34)
                surface.blit(icon, (rect.centerx - 17, rect.centery - 17))
                if slot.quantity > 1:
                    draw_text(surface, str(slot.quantity), (rect.right - 18, rect.bottom - 18), COLORS["white"], 12, bold=True)
                if slot.is_container() and slot.contents is not None:
                    used = sum(1 for content in slot.contents if content)
                    draw_text(surface, str(used), (rect.x + 5, rect.bottom - 17), (105, 190, 230), 11, bold=True)
        total_width = columns * slot_size + (columns - 1) * gap
        total_height = rows * slot_size + (rows - 1) * gap
        pygame.draw.rect(surface, (48, 56, 52), (x - 6, y - 6, total_width + 12, total_height + 12), 1, border_radius=8)

    def _draw_chest_details(self, details: pygame.Rect) -> None:
        pygame.draw.rect(self.screen, COLORS["panel_dark"], details, border_radius=6)
        pygame.draw.rect(self.screen, (75, 86, 80), details, 1, border_radius=6)
        slot = self._selected_chest_slot()
        if not slot:
            draw_text(self.screen, "Nenhum item selecionado.", (details.x + 18, details.y + 18), COLORS["white"], 16)
            return
        item = slot.item
        self.screen.blit(self.assets.item_icon(item.item_id, 48), (details.x + 18, details.y + 18))
        draw_text(self.screen, item.name, (details.x + 78, details.y + 18), COLORS["accent"], 18, bold=True)
        draw_text(self.screen, f"{item.category} | Qtd: {slot.quantity}", (details.x + 78, details.y + 44), COLORS["white"], 13)
        draw_wrapped(self.screen, item.description, pygame.Rect(details.x + 18, details.y + 86, details.width - 36, 116), COLORS["white"], 14)
        y = details.y + 218
        if slot.is_container():
            contents = slot.ensure_contents()
            used = sum(1 for content in contents if content)
            draw_text(self.screen, f"Espaco interno: {used}/{len(contents)}", (details.x + 18, y), (105, 190, 230), 14, bold=True)
            y += 24
        if item.tool_type:
            draw_text(self.screen, f"Ferramenta: {item.tool_type}", (details.x + 18, y), COLORS["white"], 14)
            y += 24
        if item.is_weapon_like():
            draw_text(self.screen, f"Dano {item.damage} | Alcance {item.range}", (details.x + 18, y), COLORS["white"], 14)
        self._draw_chest_action_buttons(details, item)

    def _selected_chest_slot(self) -> InventorySlot | None:
        if not self.chest_selected_ref:
            return None
        source, index = self.chest_selected_ref
        inventory = self._inventory_for_source(source)
        if inventory and 0 <= index < inventory.capacity:
            return inventory.slots[index]
        return None

    def _draw_chest_action_buttons(self, details: pygame.Rect, item) -> None:
        if not self.chest_selected_ref:
            return
        source, index = self.chest_selected_ref
        can_equip = source == "main" and (item.is_weapon_like() or item.is_building() or item.data.get("container_slots"))
        actions = [
            ("Usar", ("use_slot", source, index), not item.is_consumable()),
            ("Equipar", ("equip_slot", source, index), not can_equip),
            ("Dropar", ("drop_slot", source, index), False),
        ]
        x = details.x + 18
        y = details.bottom - 48
        for label, action, disabled in actions:
            button = Button((x, y, 86, 32), label, action, disabled)
            button.draw(self.screen)
            self.chest_buttons.append(button)
            x += 96

    def _interaction_text(self) -> str | None:
        if not self.player or not self.world:
            return None
        equipped = self.player.equipped_item()
        if equipped and equipped.item_id == "empty_cup" and self.world.is_water_near(self.player.center, 58):
            return "E - encher copo vazio"
        drops = [drop for drop in self.world.drops if drop.pos.distance_to(self.player.center) <= 42]
        if drops:
            return "F - pegar item do chao"
        npc = self._nearest_npc(76)
        if npc:
            if npc.vendor and self.time_system.shop_is_open():
                return "E - abrir loja de Mira"
            return "E - conversar"
        structure = self.world.nearby_structure_with_interface(self.player.center, 64)
        if structure:
            if structure.interface_kind() == "crafting":
                return "E/clique - abrir bancada de crafting"
            if structure.interface_kind() == "cooking":
                return "E/clique - abrir cozinha"
            if structure.interface_kind() == "chest":
                return "E/clique - abrir bau"
            return "E/clique - abrir interface"
        nearby = [node for node in self.world.resources if node.center.distance_to(self.player.center) < Settings.INTERACTION_RANGE]
        if nearby:
            return "Mouse esquerdo - usar ferramenta/atacar recurso"
        return None

    def _nearest_npc(self, distance: int) -> NPC | None:
        if not self.player:
            return None
        nearby = [npc for npc in self.npcs if npc.center.distance_to(self.player.center) <= distance]
        return min(nearby, key=lambda npc: npc.center.distance_to(self.player.center)) if nearby else None

    def _nearest_structure(self, building_id: str, distance: int):
        if not self.player or not self.world:
            return None
        matches = [
            structure
            for structure in self.world.structures
            if structure.building_id == building_id and pygame.Vector2(structure.rect.center).distance_to(self.player.center) <= distance
        ]
        return min(matches, key=lambda structure: pygame.Vector2(structure.rect.center).distance_to(self.player.center)) if matches else None

    def _interact(self) -> None:
        if not self.player:
            return
        if self._try_fill_empty_cup():
            return
        structure = self.world.nearby_structure_with_interface(self.player.center, 64) if self.world else None
        if structure:
            self._open_structure_interface(structure)
            return
        npc = self._nearest_npc(76)
        if npc:
            target_id = "vendor_milo_root" if npc.vendor else "npc"
            self._quest_event("talk", target_id, 1)
            if npc.vendor and self.time_system.shop_is_open():
                self.active_panel = "shop"
                self.notifications.push("Loja aberta.")
                self._quest_event("open_shop", "vendor_milo_root", 1)
            else:
                self.dialogue_ui.open(npc)
                self.active_panel = "dialogue"
            return
        self.notifications.push("Nada proximo para interagir.")

    def _try_fill_empty_cup(self) -> bool:
        if not self.player or not self.world:
            return False
        slot_index = self.player.inventory.selected_slot
        slot = self.player.inventory.selected()
        if not slot or slot.item_id != "empty_cup":
            return False
        if not self.world.is_water_near(self.player.center, 58):
            self.notifications.push("Chegue perto de um rio ou lago para encher o copo.")
            return True
        removed = self.player.inventory.remove_from_slot(slot_index, 1)
        if not removed:
            return False
        leftover = self.player.add_item("water_cup", 1)
        if leftover:
            self.player.add_item("empty_cup", 1)
            self.notifications.push("Inventario cheio para encher o copo.")
            return True
        self.particles.emit(self.player.center, color=COLORS["water"], amount=10, speed=55, lifetime=0.45, radius=3)
        self.notifications.push("Copo cheio com agua.")
        self._quest_event("collect", "water_cup", 1)
        return True

    def _try_open_structure_by_click(self, mouse_world) -> bool:
        if not self.player or not self.world:
            return False
        structure = self.world.structure_at_point(mouse_world, self.player.center, 78)
        if not structure or not structure.has_interface():
            return False
        self._open_structure_interface(structure)
        return True

    def _try_break_chest(self, mouse_world) -> bool:
        if not self.player or not self.world:
            return False
        item = self.player.equipped_item()
        if not item or item.tool_type != "axe":
            return False
        structure = self.world.structure_at_point(mouse_world, self.player.center, max(78, item.range + 28))
        if not structure or structure.interface_kind() != "chest":
            return False
        if self.player.attack_timer > 0:
            return True
        if self.player.energy < item.energy_cost:
            self.notifications.push("Energia insuficiente para quebrar o bau.")
            return True

        self.player.energy = max(0, self.player.energy - item.energy_cost)
        self.player.attack_timer = max(Settings.ATTACK_COOLDOWN, float(item.data.get("speed", 0.45)))
        self.player.set_attack_direction(mouse_world)
        drop_pos = pygame.Vector2(structure.rect.center)
        for slot in self._structure_chest_contents(structure) or []:
            if slot:
                self.world.spawn_ground_drop(drop_pos, slot.item_id, slot.quantity, contents=slot.contents)
        self.world.spawn_ground_drop(drop_pos, "small_chest", 1)
        if structure in self.world.structures:
            self.world.structures.remove(structure)
        if self.active_structure is structure:
            self.active_structure = None
            self.active_panel = None
        self.player.skills.add_xp("Construcao", 3)
        self.particles.emit(drop_pos, color=ITEMS["small_chest"].get("icon_color", COLORS["accent"]), amount=14, speed=80, lifetime=0.55, radius=3)
        self.notifications.push("Bau quebrado. Conteudo dropado.")
        return True

    def _open_structure_interface(self, structure) -> None:
        self.active_structure = structure
        interface = structure.interface_kind()
        if interface == "crafting":
            self.active_panel = "crafting"
            recipes = self.crafting_system.unlocked_recipes(self.player)
            if self.selected_recipe_id not in recipes:
                self.selected_recipe_id = next(iter(recipes), None)
        elif interface == "cooking":
            self.active_panel = "cooking"
        elif interface == "chest":
            self._structure_chest_contents(structure)
            self.active_panel = "chest"
            self.chest_selected_ref = ("chest", 0)

    def _try_place_equipped_building(self, mouse_world) -> bool:
        if not self.player or not self.world:
            return False
        slot = self.player.inventory.selected()
        item = self.player.equipped_item()
        if not slot or not item or not item.is_building():
            return False
        if self.player.center.distance_to(mouse_world) > 210:
            self.notifications.push("Muito longe para construir.")
            return True
        tile = self.world.pixel_to_tile(mouse_world)
        if not self.world.can_place_structure(tile):
            self.notifications.push("Local invalido para colocar construcao.")
            return True
        building_id = item.item_id
        self.world.add_structure(building_id, tile)
        self.player.inventory.remove_from_slot(self.player.inventory.selected_slot, 1)
        self.player.skills.add_xp("Construcao", 6)
        self._quest_event("build", building_id, 1)
        if building_id in {"torch", "campfire", "stone_stove"}:
            self._quest_event("use_light", building_id, 1)
        self.particles.emit(mouse_world, color=ITEMS[item.item_id].get("icon_color", COLORS["accent"]), amount=12, speed=70, lifetime=0.55, radius=3)
        self.notifications.push(f"Colocou {item.name}.")
        return True

    def _pickup_drops(self) -> None:
        if not self.player or not self.world:
            return
        drops = self.world.pick_drops_near(self.player.center)
        if not drops:
            self.notifications.push("Nenhum item no alcance.")
            return
        for drop in drops:
            if drop.contents is not None:
                from src.systems.inventory_system import InventorySlot

                accepted = self.player.add_slot(InventorySlot(drop.item_id, drop.quantity, contents=drop.contents))
                if accepted:
                    self._quest_event("collect", drop.item_id, drop.quantity)
                    self.notifications.push(f"Pegou {ITEMS[drop.item_id]['name']} com conteudo.")
                    self.particles.emit(drop.pos, color=ITEMS[drop.item_id].get("icon_color", COLORS["white"]), amount=7, speed=55, lifetime=0.4, radius=3)
                else:
                    self.world.spawn_ground_drop(drop.pos, drop.item_id, drop.quantity, contents=drop.contents)
                    self.notifications.push("Inventario cheio.")
                continue
            leftover = self.player.add_item(drop.item_id, drop.quantity)
            collected = drop.quantity - leftover
            if collected > 0:
                self._quest_event("collect", drop.item_id, collected)
                self.notifications.push(f"Pegou {collected} {ITEMS[drop.item_id]['name']}.")
                self.particles.emit(drop.pos, color=ITEMS[drop.item_id].get("icon_color", COLORS["white"]), amount=7, speed=55, lifetime=0.4, radius=3)
            if leftover > 0:
                self.world.spawn_ground_drop(drop.pos, drop.item_id, leftover)
                self.notifications.push("Inventario cheio.")

    def _try_fishing(self, mouse_world) -> bool:
        if not self.player or not self.world:
            return False
        item = self.player.equipped_item()
        if not item or item.tool_type != "fishing_rod":
            return False
        if self.player.center.distance_to(mouse_world) > item.range:
            return False
        if not self.world.is_water_near(mouse_world, 34):
            return False
        if self.player.energy < item.energy_cost:
            self.notifications.push("Energia insuficiente para pescar.")
            return True
        self.player.energy -= item.energy_cost
        caught = "small_fish" if self._rng.random() < 0.72 * self.weather_system.fishing_bonus() else "water_flask"
        self.world.spawn_ground_drop(mouse_world, caught, 1)
        self.player.skills.add_xp("Pescar", 8)
        self.player.level.add_xp(4)
        self.particles.emit(mouse_world, color=COLORS["water"], amount=12, speed=70, lifetime=0.55, radius=3)
        self.notifications.push(f"Pescou: {ITEMS[caught]['name']}.")
        self._quest_event("fish", caught, 1)
        return True

    def save_game(self) -> None:
        if not all([self.player, self.world, self.exploration]):
            self.notifications.push("Nada para salvar ainda.")
            return
        data = {
            "player": self.player.to_dict(),
            "world": self.world.to_dict(),
            "exploration": self.exploration.to_list(),
            "time": self.time_system.to_dict(),
            "weather": self.weather_system.to_dict(),
            "shop": self.shop_system.to_dict(),
            "cooking": self.cooking_system.to_dict(),
            "quests": self.quest_system.to_dict(),
            "enemies": [
                {
                    "kind": enemy.kind,
                    "base_level": enemy.base_level,
                    "level": enemy.level,
                    "pos": [enemy.pos.x, enemy.pos.y],
                    "hp": enemy.hp,
                    "alive": enemy.alive,
                }
                for enemy in self.enemies
            ],
            "animals": [
                {
                    "kind": animal.kind,
                    "pos": [animal.pos.x, animal.pos.y],
                    "hp": animal.hp,
                    "alive": animal.alive,
                }
                for animal in self.animals
            ],
            "npcs": [
                {
                    "name": npc.name,
                    "profession": npc.profession,
                    "pos": [npc.pos.x, npc.pos.y],
                    "vendor": npc.vendor,
                    "friendship": npc.friendship,
                    "romance": npc.romance,
                }
                for npc in self.npcs
            ],
        }
        self.save_manager.save(data)
        self.notifications.push("Jogo salvo em saves/save_01.json.")

    def load_game(self) -> bool:
        data = self.save_manager.load()
        if not data:
            return False
        world_seed = int(data.get("world", {}).get("seed", 1337))
        self.world = World(self.assets, seed=world_seed)
        self.world.load_dict(data.get("world", {}))
        self.player = Player.from_dict(data.get("player", {}), self.assets)
        self.camera = Camera(self.screen.get_size(), (self.world.pixel_width, self.world.pixel_height))
        self.exploration = MapExplorationSystem(self.world)
        self.exploration.from_list(data.get("exploration", []))
        self.time_system = TimeSystem.from_dict(data.get("time", {}))
        self.weather_system = WeatherSystem.from_dict(data.get("weather", {}))
        self.lighting_system = LightingSystem(self.screen.get_size())
        self.economy = EconomySystem()
        self.shop_system = ShopSystem(self.economy)
        self.shop_system.load_dict(data.get("shop", {}))
        self.quest_system = QuestSystem.from_dict(data.get("quests", {}), player=self.player)
        self.crafting_system = CraftingSystem()
        self.building_system = BuildingSystem()
        self.particles = ParticleManager()
        self.combat_system = CombatSystem()
        self.consumable_system = ConsumableSystem()
        self.cooking_system = CookingSystem.from_dict(data.get("cooking", {}))
        self.drop_system = DropSystem(self._rng)
        self.npcs = []
        for raw in data.get("npcs", []):
            npc = NPC(raw.get("name", "Mira"), raw.get("profession", "Vendedora"), raw.get("pos", self.world.vendor_pos), self.assets, bool(raw.get("vendor", False)))
            npc.friendship = int(raw.get("friendship", 0))
            npc.romance = int(raw.get("romance", 0))
            self.npcs.append(npc)
        if not self.npcs:
            self.npcs = [NPC("Mira", "Vendedora", self.world.vendor_pos, self.assets, vendor=True)]
        self.enemies = []
        for raw in data.get("enemies", []):
            enemy = Enemy(raw.get("kind", "forest_slime"), raw.get("pos", self.world.spawn_pos), self.assets, int(raw.get("base_level", raw.get("level", 1))))
            enemy.level = int(raw.get("level", enemy.base_level))
            enemy.max_hp = enemy._scaled_hp(enemy.level)
            enemy.damage = enemy._scaled_damage(enemy.level)
            enemy.hp = float(raw.get("hp", enemy.hp))
            enemy.alive = bool(raw.get("alive", enemy.hp > 0))
            self.enemies.append(enemy)
        if not self.enemies:
            self.enemies = self._spawn_initial_enemies()
        self.animals = []
        for raw in data.get("animals", []):
            animal = Animal(raw.get("kind", "pig"), raw.get("pos", self.world.spawn_pos), self.assets)
            animal.hp = float(raw.get("hp", animal.hp))
            animal.alive = bool(raw.get("alive", animal.hp > 0))
            self.animals.append(animal)
        if not self.animals:
            self.animals = self._spawn_initial_animals()
        self.active_panel = None
        self.state = "playing"
        self.notifications.push("Save carregado.")
        return True
