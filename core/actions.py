from __future__ import annotations

import logging
from typing import Optional, Tuple, TYPE_CHECKING

import numpy as np

from core.action import Action, ItemAction
import config.colour
from config.exceptions import Impossible
from utils.random_utils import roll_dice
import core.g

if TYPE_CHECKING:
    from lib.entity import Entity, Actor, Item


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

                core.g.engine.message_log.add_message(f"You picked up the {item.name}!")
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


class TakeStairsAction(Action):
    def perform(self) -> None:
        """
        Take the stairs, if any exist at the entity's location.
        """
        if (self.entity.x, self.entity.y) == core.g.engine.game_map.downstairs_location:
            core.g.engine.game_world.generate_floor()
            core.g.engine.message_log.add_message(
                "You slide down the tunnel, descending deeper into the Sludgeworks.", config.colour.descend
            )
        else:
            raise Impossible("You cannot descend here.")


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
    def perform(self) -> None:
        attacker = self.entity
        defender = self.target_actor
        if not defender:
            raise Impossible("Nothing to attack.")

        crit_chance = 0.05  # Critical hit chance in %
        max_crit_chance = 0.33  # Define max chance to stop overflows!

        # Roll to see if hit
        # attack_roll = roll_dice(1, 20) + attacker.fighter.dexterity_modifier
        attack_roll = roll_dice(1, 20)
        if defender.fighter.dodges:
            # dodge_roll = roll_dice(1, 20) + defender.fighter.dexterity_modifier
            dodge_roll = roll_dice(1, 20)
        else:
            dodge_roll = 0

        damage = None
        crit = False
        if attack_roll > dodge_roll:  # Attack hits
            # Calculate strength-weighted damage roll
            # damage_roll = attacker.fighter.damage + attacker.fighter.strength_modifier
            damage_roll = attacker.fighter.damage
            if defender.fighter.armour_total > 0:
                defence_roll = roll_dice(1, defender.fighter.armour_total)
            else:
                defence_roll = 0

            # Check if entity penetrates target's armour
            penetration_int = abs(damage_roll - defence_roll)
            if (damage_roll - defence_roll) > 0:
                # Calculate modified (positive) crit chance
                while penetration_int > 0 and crit_chance <= max_crit_chance:
                    crit_chance += 0.01
                    penetration_int -= 1
                # Check if crit
                if roll_dice(1, np.floor(1 / crit_chance)) == np.floor(1 / crit_chance):
                    crit = True
                    damage = attacker.fighter.crit_damage - defence_roll
                else:
                    damage = attacker.fighter.damage - defence_roll

            # Crits can penetrate otherwise impervious armour!
            elif (damage_roll - defence_roll) <= 0:
                # Calculate modified (negative) crit chance
                while penetration_int > 0 and crit_chance > 0:
                    crit_chance -= 0.01
                    penetration_int -= 1
                # Check if crit
                if crit_chance <= 0:
                    damage = 0
                else:
                    if roll_dice(1, np.floor(1 / crit_chance)) == np.floor(1 / crit_chance):
                        crit = True
                        damage = attacker.fighter.crit_damage - defence_roll
                    else:
                        damage = 0

            # Check for damage and display chat messages
            if damage > 0:
                if crit:
                    if attacker.name.capitalize() == 'Player':
                        core.g.engine.message_log.add_message(f'You crit the {defender.name.capitalize()} for '
                                                            f'{str(damage)} damage!', config.colour.player_atk)
                    elif defender.name.capitalize() == 'Player':
                        core.g.engine.message_log.add_message(f'The {attacker.name} crits you for '
                                                            f'{str(damage)} damage!', config.colour.enemy_crit)
                    else:
                        core.g.engine.message_log.add_message(f'The {attacker.name} crits the {defender.name}'
                                                            f'{str(damage)} damage!', config.colour.enemy_crit)
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


class MovementAction(ActionWithDirection):
    def perform(self) -> None:
        dest_x, dest_y = self.dest_xy

        if not core.g.engine.game_map.in_bounds(dest_x, dest_y):
            # Destination is out of bounds.
            raise Impossible("That way is blocked.")
        if not core.g.engine.game_map.tiles["walkable"][dest_x, dest_y]:
            # Destination is blocked by a tile.
            raise Impossible("That way is blocked.")
        if core.g.engine.game_map.get_blocking_entity_at_location(dest_x, dest_y):
            # Destination is blocked by a tile.
            raise Impossible("That way is blocked.")

        self.entity.move(self.dx, self.dy)


class BumpAction(ActionWithDirection):
    """Bump action to move in a single cardinal direction"""

    def perform(self) -> None:
        if self.dx > 1 or self.dx < -1 or self.dy > 1 or self.dy < -1:
            raise Impossible(f"Movement coords for {self.entity.name} are invalid for cardinal movement. "
                             f"({self.dx, self.dy})", config.colour.debug)
        if self.target_actor:
            return MeleeAction(self.entity, self.dx, self.dy).perform()
        else:
            return MovementAction(self.entity, self.dx, self.dy).perform()