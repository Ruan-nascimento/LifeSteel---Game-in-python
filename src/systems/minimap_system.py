class MinimapSystem:
    def __init__(self, scale: int = 3) -> None:
        self.scale = scale
        self.show_enemies = False

    def toggle_enemy_radar(self) -> None:
        self.show_enemies = not self.show_enemies
