from __future__ import annotations

import pygame

from src.core.settings import Settings


class CombatSystem:
    def __init__(self) -> None:
        self.message = "Combate pronto."

    def player_attack(self, player, world, enemies, mouse_world_pos, particles, notifications, animals=None) -> None:
        if player.attack_timer > 0:
            return
        item = player.equipped_item()
        if not item or not item.is_weapon_like():
            notifications.push("Equipe uma arma ou ferramenta.")
            return

        if player.energy < item.energy_cost:
            notifications.push("Energia insuficiente.")
            return
        if player.mana < item.mana_cost:
            notifications.push("Mana insuficiente.")
            return

        player.energy = max(0, player.energy - item.energy_cost)
        player.mana = max(0, player.mana - item.mana_cost)
        player.attack_timer = max(Settings.ATTACK_COOLDOWN, float(item.data.get("speed", 0.35)))
        player.set_attack_direction(mouse_world_pos)

        target_resource = world.resource_near_point(mouse_world_pos, item.range, player.center)
        if target_resource:
            self._attack_resource(player, target_resource, item, world, particles, notifications)
            return

        hit_any = False
        for enemy in enemies:
            if not enemy.alive:
                continue
            distance = enemy.center.distance_to(player.center)
            if distance <= item.range:
                damage = player.combat_damage(item)
                enemy.take_damage(damage)
                particles.emit(enemy.center, color=(219, 68, 64), amount=10, speed=90, lifetime=0.42, radius=3)
                notifications.push(f"Causou {damage} dano.")
                player.skills.add_xp("Combate", 6)
                hit_any = True
                if not enemy.alive:
                    xp = enemy.reward_xp() + (4 if player.class_id == "warrior" else 0)
                    coins = enemy.reward_coins()
                    player.level.add_xp(xp)
                    player.coins += coins
                    player.skills.add_xp("Coragem", 4)
                    for item_id, amount in enemy.drop_items().items():
                        world.spawn_ground_drop(enemy.center, item_id, amount)
                    notifications.push(f"{enemy.name} derrotado: +{xp} XP +{coins} ZC.")
        for animal in animals or []:
            if not animal.alive:
                continue
            distance = animal.center.distance_to(player.center)
            if distance <= item.range:
                damage = player.combat_damage(item)
                animal.take_damage(damage)
                particles.emit(animal.center, color=(205, 116, 83), amount=8, speed=70, lifetime=0.34, radius=3)
                hit_any = True
                if not animal.alive:
                    player.skills.add_xp("Caca", 8)
                    player.level.add_xp(8)
                    for item_id, amount in animal.drop_items().items():
                        world.spawn_ground_drop(animal.center, item_id, amount)
                        notifications.push(f"Drop: {amount} {world.item_name(item_id)}")
        if not hit_any:
            swing_pos = player.center + player.facing_vector * min(item.range, 48)
            particles.emit(swing_pos, color=(224, 221, 185), amount=5, speed=55, lifetime=0.22, radius=2)

    def _attack_resource(self, player, resource, item, world, particles, notifications) -> None:
        if not resource.can_harvest_with(item):
            required = resource.required_tool or "ferramenta certa"
            notifications.push(f"Requer {required}.")
            particles.emit(resource.center, color=(140, 140, 140), amount=4, speed=35, lifetime=0.25, radius=2)
            return

        damage = player.tool_power(item, resource)
        drops = resource.harvest(damage)
        color = resource.particle_color
        particles.emit(resource.center, color=color, amount=9, speed=95, lifetime=0.5, radius=3)
        skill_name = resource.skill_name
        player.skills.add_xp(skill_name, 5)
        player.skills.add_xp("Coleta", 2)
        if drops:
            for item_id, amount in drops.items():
                world.spawn_ground_drop(resource.center, item_id, amount)
                notifications.push(f"Drop: {amount} {world.item_name(item_id)}")
            player.level.add_xp(resource.xp_reward)
            world.remove_resource(resource)
        self.message = f"Usou {item.name}."

    def enemy_attack_player(self, enemy, player, particles, notifications) -> None:
        raw_damage = enemy.damage
        damage = max(1, raw_damage - player.defense)
        player.take_damage(damage)
        player.skills.add_xp("Defesa", 3)
        color = (120, 196, 235) if getattr(enemy, "ranged", False) else (210, 61, 62)
        particles.emit(player.center, color=color, amount=8, speed=75, lifetime=0.38, radius=3)
        attack_text = "atingiu a distancia" if getattr(enemy, "ranged", False) else "causou"
        notifications.push(f"{enemy.name} {attack_text} {damage} dano.")
