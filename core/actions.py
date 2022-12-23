from __future__ import annotations

import logging
import random
from math import hypot
from typing import Optional, Tuple, TYPE_CHECKING, List

import numpy as np
import tcod

import config.colour
import core.g
import parts.effects
from config.exceptions import Impossible
from core.action import Action, ItemAction
from utils.random_utils import roll_dice

if TYPE_CHECKING:
    from parts.entity import Entity, Actor, Item


class PickupAction(Action):
    """
    Pickup an item and add it to the inventory, if there is room for it.
    """

    def __init__(self, entity: Actor):
        super().__init__(entity)

    def perform(self) -> None:
        actor_location_x = self.entity.x
        actor_location_y = self.entity.y
        inventory = self.entity.inventory

        for item in core.g.engine.game_map.items:
            if actor_location_x == item.x and actor_location_y == item.y:
                if len(inventory.items) >= inventory.capacity:
                    raise Impossible("Your inventory is full.")

                core.g.engine.game_map.entities.remove(item)
                item.parent = self.entity.inventory
                inventory.items.append(item)

                core.g.engine.message_log.add_message(f"You pick up the {item.name}!")
                return

        raise Impossible("There is nothing here to pick up.")


class DropItem(ItemAction):
    def perform(self) -> None:
        if self.entity.equipment.item_is_equipped(self.item):
            self.entity.equipment.toggle_equip(self.item)

        self.entity.inventory.drop(self.item)


class EquipAction(Action):
    def __init__(self, entity: Actor, item: Item):
        super().__init__(entity)

        self.item = item

    def perform(self) -> None:
        self.entity.equipment.toggle_equip(self.item)


class WaitAction(Action):
    def perform(self) -> None:
        pass


class FallDownHole(Action):
    def perform(self) -> None:
        """
        Fall down a hole/chasm and generate the next floor, taking some damage
        """

        core.g.engine.game_world.generate_floor()
        damage = round(core.g.engine.player.fighter.base_max_hp / 4)
        self.entity.fighter.take_damage(damage)
        core.g.engine.message_log.add_message(
            f"You fall down the hole to the next floor, taking {damage} damage! Ouch!", config.colour.descend
        )


class ActionWithDirection(Action):
    def __init__(self, entity: Actor, dx: int, dy: int):
        super().__init__(entity)

        self.dx = dx
        self.dy = dy

    @property
    def dest_xy(self) -> Tuple[int, int]:
        """Returns this actions destination."""
        return self.entity.x + self.dx, self.entity.y + self.dy

    @property
    def blocking_entity(self) -> Optional[Entity]:
        """Return the blocking entity at this action's destination."""
        return core.g.engine.game_map.get_blocking_entity_at_location(*self.dest_xy)

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at the destination of this action."""
        return core.g.engine.game_map.get_actor_at_location(*self.dest_xy)

    def perform(self) -> None:
        raise NotImplementedError()


class MeleeAction(ActionWithDirection):
    def __init__(self,
                 entity: Actor,
                 dx: int,
                 dy: int,
                 crit_chance: float = 0.05,
                 max_crit_chance: float = 0.33
                 ):
        super().__init__(
            entity,
            dx=dx,
            dy=dy
        )
        self.crit_chance = crit_chance
        self.max_crit_chance = max_crit_chance

    def perform(self) -> None:
        attacker = self.entity
        defender = self.target_actor
        core.g.engine.last_actor = self.entity
        if not defender:
            raise Impossible("Nothing to attack.")

        # Get and apply modifiers for action
        modifiers = self.entity.equipment.get_active_modifiers()

        # Roll to see if hit
        attack_roll = roll_dice(1, 20) + attacker.fighter.dexterity_modifier
        if defender.fighter.dodges:
            dodge_roll = roll_dice(1, 20) + defender.fighter.dexterity_modifier
        else:
            dodge_roll = 0

        damage = None
        crit = False
        if attack_roll > dodge_roll:  # Attack hits
            # Calculate strength-weighted damage roll
            damage_roll = attacker.fighter.damage + attacker.fighter.strength_modifier
            if defender.fighter.armour_total > 0:
                defence_roll = roll_dice(1, defender.fighter.armour_total)
            else:
                defence_roll = 0

            # Check if entity penetrates target's armour
            penetration_int = abs(damage_roll - defence_roll)
            if (damage_roll - defence_roll) > 0:
                # Calculate modified (positive) crit chance
                while penetration_int > 0 and self.crit_chance <= self.max_crit_chance:
                    self.crit_chance += 0.01
                    penetration_int -= 1
                # Check if crit
                if roll_dice(1, np.floor(1 / self.crit_chance)) == np.floor(1 / self.crit_chance):
                    crit = True
                    damage = attacker.fighter.crit_damage - defence_roll
                else:
                    damage = attacker.fighter.damage - defence_roll

            # Crits can penetrate otherwise impervious armour!
            elif (damage_roll - defence_roll) <= 0:
                # Calculate modified (negative) crit chance
                while penetration_int > 0 and self.crit_chance > 0:
                    self.crit_chance -= 0.01
                    penetration_int -= 1
                # Check if crit
                if self.crit_chance <= 0:
                    damage = 0
                else:
                    if roll_dice(1, np.floor(1 / self.crit_chance)) == np.floor(1 / self.crit_chance):
                        crit = True
                        damage = attacker.fighter.crit_damage - defence_roll
                    else:
                        damage = 0

            # Check for damage and display chat messages
            if damage > 0:
                if crit:
                    if defender.blood == "Blood":
                        core.g.engine.game_map.splatter_tiles(defender.x, defender.y,
                                                              light_fg=config.colour.blood, modifiers="Bloody")
                    if attacker.name.capitalize() == 'Player':
                        core.g.engine.message_log.add_message(f'You crit the {defender.name.capitalize()} for '
                                                              f'{str(damage)} damage!', config.colour.player_atk)
                    elif defender.name.capitalize() == 'Player':
                        core.g.engine.message_log.add_message(f'The {attacker.name} crits you for '
                                                              f'{str(damage)} damage!', config.colour.enemy_crit)
                    else:
                        core.g.engine.message_log.add_message(f'The {attacker.name} crits the {defender.name}'
                                                              f'{str(damage)} damage!', config.colour.enemy_crit)
                    # Always apply poison on crit
                    for modifier in modifiers:
                        if isinstance(modifier, parts.effects.PoisonModifier):
                            effect = parts.effects.PoisonEffect(damage=modifier.damage, turns=modifier.turns)
                            effect.parent = defender

                            # Poison message only if not already poisoned
                            if len(defender.active_effects) == 0:
                                core.g.engine.message_log.add_message(f"The {defender.name.capitalize()} is poisoned!",
                                                                      config.colour.poison)
                            defender.active_effects.append(effect)
                else:
                    if attacker.name.capitalize() == 'Player':
                        core.g.engine.message_log.add_message(f'You attack the {defender.name.capitalize()} for '
                                                              f'{str(damage)} damage.', config.colour.player_atk)
                    elif defender.name.capitalize() == 'Player':
                        core.g.engine.message_log.add_message(f'The {attacker.name} attacks you for '
                                                              f'{str(damage)} damage.', config.colour.enemy_atk)
                    else:
                        core.g.engine.message_log.add_message(f'The {attacker.name} attacks the {defender.name}'
                                                              f'{str(damage)} damage.', config.colour.enemy_atk)
                    # Roll for poison if damage is dealt!
                    for modifier in modifiers:
                        if isinstance(modifier, parts.effects.PoisonModifier):
                            if roll_dice(1, defender.fighter.base_vitality) < modifier.difficulty:
                                effect = parts.effects.PoisonEffect(damage=modifier.damage, turns=modifier.turns)
                                effect.parent = defender

                                # Poison message only if not already poisoned
                                if len(defender.active_effects) == 0:
                                    core.g.engine.message_log.add_message(
                                        f"The {defender.name.capitalize()} is poisoned!", config.colour.poison)
                                defender.active_effects.append(effect)
                defender.fighter.hp -= damage
            else:
                if attacker.name.capitalize() == 'Player':
                    core.g.engine.message_log.add_message(f'You attack the {defender.name.capitalize()} '
                                                          f'but do no damage.', config.colour.enemy_evade)
                elif defender.name.capitalize() == 'Player':
                    core.g.engine.message_log.add_message(f'The {attacker.name} attacks you '
                                                          f'but does no damage!', config.colour.player_evade)
                else:
                    core.g.engine.message_log.add_message(f'The {attacker.name} attacks the {defender.name}'
                                                          f'but does no damage.', config.colour.enemy_evade)
                if logging.DEBUG >= logging.root.level:
                    core.g.engine.message_log.add_message(f"DEBUG: Roll [{attack_roll} vs. {defence_roll}].",
                                                          config.colour.debug)
        else:
            if attacker.name.capitalize() == 'Player':
                core.g.engine.message_log.add_message(f'You attack the {defender.name.capitalize()} '
                                                      f'but the attack is evaded.', config.colour.enemy_evade)
            elif defender.name.capitalize() == 'Player':
                core.g.engine.message_log.add_message(f'You evade the {attacker.name.capitalize()}\'s attack.',
                                                      config.colour.player_evade)
            else:
                core.g.engine.message_log.add_message(f'The {attacker.name} attacks the {defender.name}'
                                                      f'but the attack is evaded.', config.colour.enemy_evade)
            if logging.DEBUG >= logging.root.level:
                core.g.engine.message_log.add_message(f"DEBUG: Roll [{attack_roll} vs. {dodge_roll}].",
                                                      config.colour.debug)


class BumpAction(ActionWithDirection):
    """Bump action to move in a single cardinal direction"""

    def perform(self) -> None:
        from parts.ai import NPC
        if self.dx > 1 or self.dx < -1 or self.dy > 1 or self.dy < -1:
            raise Impossible(f"Movement coords for {self.entity.name} are invalid for cardinal movement. "
                             f"({self.dx, self.dy})", config.colour.debug)
        if self.target_actor:
            if isinstance(self.target_actor.ai, parts.ai.NPC):
                return SwapAction(self.entity, self.target_actor, self.dx, self.dy).perform()
            else:
                return MeleeAction(self.entity, self.dx, self.dy).perform()
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()


class MovementAction(ActionWithDirection):
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy

        # Various oob checks
        if not core.g.engine.game_map.in_bounds(dest_x, dest_y):
            raise Impossible("That way is blocked.")
        if not core.g.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            raise Impossible("That way is blocked.")

        blocking = core.g.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y)
        if blocking:
            if 'Door' in blocking.name:
                DoorAction(self.entity, blocking, self.dx, self.dy).perform()
            else:
                raise Impossible("That way is blocked.")
        else:
            self.entity.move(self.dx, self.dy)


class DoorAction(ActionWithDirection):
    """Action for when an entity attempts to pass through a door"""

    def __init__(self, entity: Actor, door: parts.entity.StaticObject, dx: int, dy: int):
        super().__init__(entity, dx, dy)
        self.door = door

    def perform(self) -> None:
        if "Unlocked" in self.door.properties:
            if "Closed" in self.door.properties:
                self.door.blocks_movement = False
                self.door.colour = tcod.grey
                self.door.properties.remove("Closed")
                self.door.properties.append("Open")
                if self.entity.name == "Player":
                    core.g.engine.message_log.add_message("You open the door.", config.colour.use)
            elif "Open" in self.door.properties:
                self.door.blocks_movement = True
                self.door.colour = self.door.base_colour
                self.door.properties.remove("Open")
                self.door.properties.append("Closed")
                if self.entity.name == "Player":
                    core.g.engine.message_log.add_message("You close the door.", config.colour.use)
            core.g.engine.update_fov()
        elif "Locked" in self.door.properties:
            if self.entity.name == "Player":
                core.g.engine.message_log.add_message("This door is locked.", config.colour.impossible)


class SwapAction(ActionWithDirection):
    """Swap the positions of two entities."""

    def __init__(self, entity: Actor, target: Actor, dx: int, dy: int):
        super().__init__(entity, dx, dy)
        self.target = target

    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy

        if not core.g.engine.game_map.in_bounds(dest_x, dest_y):
            # Destination is out of bounds.
            raise Impossible("That way is blocked.")
        if not core.g.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            # Destination is blocked by a tile.
            raise Impossible("That way is blocked.")

        x1 = self.entity.x
        y1 = self.entity.y
        x2 = self.target_actor.x
        y2 = self.target_actor.y
        self.entity.move(x2 - x1, y2 - y1)
        self.target.move(x1 - x2, y1 - y2)


class ExploreAction(Action):
    def __init__(self, entity: Actor, unexplored_coords=None):
        super().__init__(entity)
        self.path = []
        self.unexplored_coords = unexplored_coords

    def possible(self) -> bool:
        """Check whether this action is possible."""
        if self.enemy_in_fov():
            return False

        self.init_coords()
        if len(self.unexplored_coords) == 0:
            return False

        return True

    def init_coords(self):
        self.unexplored_coords = []
        for y in range(core.g.engine.game_map.height):
            for x in range(core.g.engine.game_map.width):
                if not core.g.engine.game_map.explored[x, y] and core.g.engine.game_map.accessible[x, y]:
                    self.unexplored_coords.append((y, x))

    def enemy_in_fov(self) -> str:
        """Checks if there in an enemy in player FOV which will interrupt the explore action."""
        visible_x, visible_y = np.nonzero(core.g.engine.game_map.visible)
        for tile_x, tile_y in zip(visible_x, visible_y):
            for entity in core.g.engine.game_map.get_all_visible_entities(tile_x, tile_y):
                if entity in core.g.engine.game_map.dangerous_actors:
                    return entity.name

    def path_isvalid(self):
        """Helper tool to find out whether a path is valid. This is important as teleportation
        and forced movement actions can cause the path to move entities to incorrect tiles."""
        if core.g.engine.player.x == self.path[0][0] and core.g.engine.player.y == self.path[0][1]:
            return False

        if not core.g.engine.game_map.tiles['walkable'][self.path[0][0], self.path[0][1]]:
            return False

        next_x = abs(self.entity.x - self.path[0][0])
        next_y = abs(self.entity.y - self.path[0][1])
        if next_x > 1 or next_y > 1:
            return False

        return True

    def perform(self) -> Optional[None | str]:
        """Use a dijkstra map to navigate the player towards the nearest unexplored tile."""
        player = core.g.engine.player

        # First check whether exploring is possible and init unexplored coords
        in_fov = self.enemy_in_fov()
        if in_fov:
            core.g.engine.message_log.add_message(f"You spot a {in_fov} and stop exploring.",
                                                  config.colour.yellow)
            return None

        # Recalculate unexplored coords
        self.init_coords()
        if len(self.unexplored_coords) == 0:
            core.g.engine.message_log.add_message("There is nowhere else to explore.", config.colour.yellow)
            return None

        # If a path already exists, finish it before moving to another coord
        if self.path and self.path_isvalid():
            BumpAction(player, self.path[0][0] - player.x, self.path[0][1] - player.y).perform()
            self.path.pop(0)
            return "continuous"
        else:
            # Find the nearest unexplored coords
            closest_distance = 10000
            closest_coord = None
            for y, x in self.unexplored_coords:
                new_distance = hypot(x - player.x, y - player.y)
                if new_distance < closest_distance:
                    closest_distance = new_distance
                    closest_coord = (x, y)

            # Try simple A*
            if closest_coord:
                cost = np.array(core.g.engine.game_map.accessible, dtype=np.int8)

                # Create a graph from the cost array and pass that graph to a new pathfinder.
                graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
                pathfinder = tcod.path.Pathfinder(graph)
                pathfinder.add_root((core.g.engine.player.x, core.g.engine.player.y))  # Start position.

                # Compute the path to the destination and remove the starting point.
                self.path: List[List[int]] = pathfinder.path_to(closest_coord)[1:].tolist()
                if not self.path:
                    core.g.engine.message_log.add_message("You cannot explore the remaining tiles.",
                                                          config.colour.yellow)
                    return None
                else:
                    BumpAction(player, self.path[0][0] - player.x, self.path[0][1] - player.y).perform()
                    return "continuous"


class TakeStairsAction(Action):
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path = []

    def possible(self) -> bool:
        """Check whether this action is possible."""
        if self.enemy_in_fov():
            return False

        # Check if stairs have been found
        stairs_x = core.g.engine.game_map.downstairs_location[0]
        stairs_y = core.g.engine.game_map.downstairs_location[1]
        if core.g.engine.game_map.explored[stairs_x, stairs_y]:
            return True
        else:
            core.g.engine.message_log.add_message("You cannot descend here.", config.colour.yellow)
            return False

    def enemy_in_fov(self):
        """Checks if there in an enemy in player FOV which will interrupt the pathing to the stairs."""
        visible_x, visible_y = np.nonzero(core.g.engine.game_map.visible)
        for tile_x, tile_y in zip(visible_x, visible_y):
            for entity in core.g.engine.game_map.get_all_visible_entities(tile_x, tile_y):
                if entity in core.g.engine.game_map.dangerous_actors:
                    core.g.engine.message_log.add_message(f"You spot a {entity.name} and stop exploring.",
                                                          config.colour.yellow)

    def path_isvalid(self):
        """Helper tool to find out whether a path is valid. This is important as teleportation
        and forced movement actions can cause the path to move entities to incorrect tiles."""
        if core.g.engine.player.x == self.path[0][0] and core.g.engine.player.y == self.path[0][1]:
            return False

        if not core.g.engine.game_map.tiles['walkable'][self.path[0][0], self.path[0][1]]:
            return False

        next_x = abs(self.entity.x - self.path[0][0])
        next_y = abs(self.entity.y - self.path[0][1])
        if next_x > 1 or next_y > 1:
            return False

        return True

    def perform(self) -> Optional[None | str]:
        """Use a dijkstra map to navigate the player towards the down stairs location."""
        player = core.g.engine.player

        # Check if there is an enemy in the FOV
        if self.enemy_in_fov():
            return None
        # If path exists, take the next step
        elif self.path and self.path_isvalid():
            BumpAction(player, self.path[0][0] - player.x, self.path[0][1] - player.y).perform()
            self.path.pop(0)
            return "continuous"
        else:
            cost = np.array(core.g.engine.game_map.accessible, dtype=np.int8)

            # Create a graph from the cost array and pass that graph to a new pathfinder.
            graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
            pathfinder = tcod.path.Pathfinder(graph)
            pathfinder.add_root((core.g.engine.player.x, core.g.engine.player.y))  # Start position.

            # Compute the path to the destination and remove the starting point.
            self.path: List[List[int]] = pathfinder.path_to(core.g.engine.game_map.downstairs_location)[1:].tolist()
            if core.g.engine.player.x == core.g.engine.game_map.downstairs_location[0] and \
                    core.g.engine.player.y == core.g.engine.game_map.downstairs_location[1]:
                return None
            elif not self.path:
                core.g.engine.message_log.add_message("You cannot find a clear path to the exit.",
                                                      config.colour.yellow)
                return None
            else:
                BumpAction(player, self.path[0][0] - player.x, self.path[0][1] - player.y).perform()
                return "continuous"


class DescendAction(Action):
    """Action for descending to the next floor, including generating the map."""

    def perform(self) -> Optional[None]:
        core.g.engine.game_world.generate_floor()
        core.g.engine.message_log.add_message(
            "You slide down the tunnel, descending deeper into the Sludgeworks.", config.colour.descend
        )
