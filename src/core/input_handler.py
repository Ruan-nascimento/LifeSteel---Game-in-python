import pygame


class InputHandler:
    def __init__(self) -> None:
        self.keys = pygame.key.get_pressed()
        self.mouse_pos = pygame.Vector2(0, 0)

    def refresh(self) -> None:
        self.keys = pygame.key.get_pressed()
        self.mouse_pos = pygame.Vector2(pygame.mouse.get_pos())

    def movement_vector(self) -> pygame.Vector2:
        direction = pygame.Vector2(0, 0)
        if self.keys[pygame.K_w]:
            direction.y -= 1
        if self.keys[pygame.K_s]:
            direction.y += 1
        if self.keys[pygame.K_a]:
            direction.x -= 1
        if self.keys[pygame.K_d]:
            direction.x += 1
        if direction.length_squared() > 0:
            direction = direction.normalize()
        return direction

    def sprinting(self) -> bool:
        return self.keys[pygame.K_LSHIFT] or self.keys[pygame.K_RSHIFT]
