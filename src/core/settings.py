from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
ASSETS_DIR = BASE_DIR / "assets"
SAVES_DIR = BASE_DIR / "saves"


class Settings:
    TITLE = "LifeSteel"
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720
    MIN_WIDTH = 960
    MIN_HEIGHT = 540
    FPS = 60

    TILE_SIZE = 32
    WORLD_WIDTH = 160
    WORLD_HEIGHT = 160
    CHUNK_SIZE = 16

    PLAYER_SIZE = (30, 40)
    PLAYER_BASE_SPEED = 165
    PLAYER_RUN_MULTIPLIER = 1.55
    INTERACTION_RANGE = 58
    ATTACK_COOLDOWN = 0.38

    REAL_SECONDS_PER_GAME_DAY = 10 * 60
    START_HOUR = 8
    START_MINUTE = 30

    SAVE_SLOT = SAVES_DIR / "save_01.json"

    HOTBAR_SIZE = 5
    STARTING_COINS = 1000
    STARTING_APPLES = 5

    UI_FONT = "consolas"
    UI_FONT_SIZE = 18
    UI_SMALL_FONT_SIZE = 14
    UI_BIG_FONT_SIZE = 42

    SHOW_FPS = False
    MAX_PARTICLES = 150
    ENABLE_LIGHT_FLICKER = True
    LIGHTING_UPDATE_EVERY_FRAMES = 1
    LOW_PERFORMANCE_MODE = False
    RENDER_MARGIN = 96
    MAX_VISIBLE_SHOP_ROWS = 8
    MAX_VISIBLE_QUEST_ROWS = 8


COLORS = {
    "white": (242, 244, 235),
    "black": (12, 14, 13),
    "panel": (24, 29, 30),
    "panel_light": (43, 50, 48),
    "panel_dark": (15, 18, 18),
    "accent": (224, 181, 74),
    "accent_2": (96, 191, 136),
    "danger": (209, 82, 72),
    "hp": (213, 65, 75),
    "xp": (96, 160, 226),
    "hunger": (218, 159, 67),
    "thirst": (80, 174, 220),
    "energy": (229, 205, 90),
    "mana": (124, 100, 226),
    "grass": (68, 132, 73),
    "grass_dark": (47, 103, 61),
    "grass_light": (89, 154, 79),
    "water": (50, 119, 167),
    "soil": (113, 84, 55),
    "path": (130, 113, 75),
    "stone": (111, 119, 123),
    "wood": (118, 75, 42),
    "fog": (4, 8, 9),
}


CONTROL_HELP = [
    "WASD mover",
    "Shift correr",
    "Mouse E usar/atacar",
    "E interagir",
    "I inventario",
    "C status",
    "M mapa",
    "J missoes",
    "Q consumir",
    "B construir",
    "K skills",
    "F3 debug",
    "F5 salvar",
]
