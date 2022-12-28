from __future__ import annotations

import random
from typing import Optional, TYPE_CHECKING

import config.colour
import core.g
import core.input_handlers
import parts.ai
import parts.inventory
from config.exceptions import Impossible
from core.actions import ItemAction
from parts.base_component import BaseComponent
from parts.effects import BurningEffect
from utils.random_utils import dnd_bonus_calc

if TYPE_CHECKING:
    from entity import Actor, Item


class Consumable(BaseComponent):
    parent: Item

    def item(self) -> parts.entity.Item:
        assert isinstance(self.parent, parts.entity.Item)
        return self.parent

    def get_action(self, consumer: Actor) -> Optional[core.input_handlers.ActionOrHandler]:
        """Try to return the action for this item."""
        return ItemAction(consumer, self.parent)

    def activate(self, action: ItemAction) -> None:
        """Invoke this items ability. 'action' is the context for this activation."""
        raise NotImplementedError()

    def consume(self) -> None:
        """Remove the consumed item from its containing inventory."""
        entity = self.parent
        inventory = entity.parent

        # Remove Item from inventory, unless stackable, then reduce stack by 1
        if isinstance(inventory, parts.inventory.Inventory):
            if entity.stackable:
                index = inventory.items.index(entity)
                if inventory.quantities[index] == 1:
                    inventory.remove(entity)
                else:
                    inventory.quantities[index] -= 1
            else:
                inventory.remove(entity)
            inventory.sanity_check()


class Junk(Consumable):
    """Class for items which have no use."""

    def activate(self, action: ItemAction):
        pass


class HealingConsumable(Consumable):
    def __init__(self, amount: int):
        self.amount = amount

    def activate(self, action: ItemAction) -> None:
        consumer = action.entity
        amount_recovered = consumer.fighter.heal(self.amount)

        if amount_recovered > 0:
            # Display message for use whenever Item is consumed
            core.g.engine.message_log.add_message(self.parent.usetext, config.colour.use)
            core.g.engine.message_log.add_message(
                f"You recover {amount_recovered} HP!", config.colour.health_recovered)
            self.consume()
        else:
            raise Impossible(f"Your health is already full.")


class RandomHealConsumable(Consumable):
    def __init__(self, lower_bound: int, upper_bound: int):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound

    @property
    def random_heal(self):
        return random.randint(self.lower_bound, self.upper_bound)

    def activate(self, action: ItemAction) -> None:
        consumer = action.entity
        amount_recovered = consumer.fighter.heal(self.random_heal)

        if amount_recovered > 0:
            # Display message for use whenever Item is consumed
            core.g.engine.message_log.add_message(self.parent.usetext, config.colour.use)
            core.g.engine.message_log.add_message(
                f"You recover {amount_recovered} HP!", config.colour.health_recovered)
            self.consume()
        else:
            raise Impossible(f"Your health is already full.")


class FireballDamageConsumable(Consumable):
    def __init__(self, lower_bound: int, upper_bound, radius: int):
        self.lower_bound = lower_bound
        self.upper_bound = upper_bound
        self.radius = radius

    @property
    def damage(self):
        return random.randint(self.lower_bound, self.upper_bound)

    def get_action(self, consumer: Actor) -> core.input_handlers.AreaRangedAttackHandler:
        core.g.engine.message_log.add_message(
            "Select a target location.", config.colour.needs_target
        )
        return core.input_handlers.AreaRangedAttackHandler(
            radius=self.radius,
            callback=lambda xy: ItemAction(consumer, self.parent, xy),
        )

    def activate(self, action: ItemAction) -> None:
        target_xy = action.target_xy

        if not core.g.engine.game_map.visible[target_xy]:
            raise Impossible("You cannot target an area that you cannot see.")

        # Display message for use whenever Item is consumed
        core.g.engine.message_log.add_message(self.parent.usetext, config.colour.use)

        targets_hit = False
        for actor in core.g.engine.game_map.actors:
            if actor.distance(*target_xy) <= self.radius:
                if actor.name == "Player":
                    core.g.engine.message_log.add_message(
                        f"You are engulfed in a fiery explosion, taking {self.damage} damage!"
                    )
                elif actor.name.endswith('s'):
                    core.g.engine.message_log.add_message(
                        f"The {actor.name} are engulfed in a fiery explosion, taking {self.damage} damage!"
                    )
                else:
                    core.g.engine.message_log.add_message(
                        f"The {actor.name} is engulfed in a fiery explosion, taking {self.damage} damage!"
                    )
                actor.fighter.take_damage(self.damage)
                targets_hit = True

                # # This attack aggravates passive entities
                # if isinstance(actor.ai, parts.ai.NPC) or isinstance(actor.ai, parts.ai.PlantKeeper):
                #     actor.ai = parts.ai.HostileEnemy(entity=actor)

                # 50% chance to add a burning effect to the target (if it didn't die)
                if actor.fighter.hp > 0:
                    if random.randint(1, 100) >= 50:
                        effect = BurningEffect(turns=1)
                        effect.parent = actor
                        actor.active_effects.append(effect)

                        # Make sure that rooted enemies don't wander around
                        if not isinstance(actor.ai, parts.ai.PassiveStationary) or isinstance(actor.ai,
                                                                                              parts.ai.HostileStationary):
                            actor.ai = parts.ai.BurningEnemy(entity=actor, previous_ai=actor.ai)

                        if actor.name == 'Player':
                            core.g.engine.message_log.add_message(f"You are set on fire by the explosion!")
                        elif actor.name.endswith('s'):
                            core.g.engine.message_log.add_message(f"The {actor.name} catch fire!")
                        else:
                            core.g.engine.message_log.add_message(f"The {actor.name} catches fire!")

        if not targets_hit:
            core.g.engine.message_log.add_message("It has seems to have no effect...", config.colour.invalid)
        self.consume()


class LightningDamageConsumable(Consumable):
    def __init__(self, upper_bound: int, lower_bound: int, maximum_range: int):
        self.upper_bound = upper_bound
        self.lower_bound = lower_bound
        self.maximum_range = maximum_range

    @property
    def damage(self):
        return random.randint(self.lower_bound, self.upper_bound)

    def activate(self, action: ItemAction) -> None:
        consumer = action.entity
        target = None
        closest_distance = self.maximum_range + 1.0

        for actor in core.g.engine.game_map.actors:
            if actor is not consumer and self.parent.gamemap.visible[actor.x, actor.y]:
                distance = consumer.distance(actor.x, actor.y)

                if distance < closest_distance:
                    target = actor
                    closest_distance = distance

        if target:
            # Display message for use whenever Item is consumed
            core.g.engine.message_log.add_message(self.parent.usetext, config.colour.use)
            core.g.engine.message_log.add_message(
                f"A lighting bolt strikes the {target.name} for {self.damage} damage!"
            )
            target.fighter.take_damage(self.damage)
            self.consume()
        else:
            raise Impossible("No enemy is close enough to strike.")


class ConfusionConsumable(Consumable):
    def __init__(self, number_of_turns: int):
        self.base_turns = number_of_turns

    @property
    def calc_turns(self):
        # Return a random number of turns between the save roll and the max
        if self.save_bonus < 0:
            self.save_bonus = 0
        return self.base_turns - self.save_bonus

    def get_action(self, consumer: Actor) -> core.input_handlers.SingleRangedAttackHandler:
        core.g.engine.message_log.add_message("Select a target location.", config.colour.needs_target)
        return core.input_handlers.SingleRangedAttackHandler(callback=lambda xy: ItemAction(consumer, self.parent, xy))

    def activate(self, action: ItemAction) -> None:
        consumer = action.entity
        target = action.target_actor

        if not core.g.engine.game_map.visible[action.target_xy]:
            raise Impossible("You cannot target an area that you cannot see.")
        if not target:
            raise Impossible("No enemy at location (You must select an enemy to target).")
        if target is consumer:
            raise Impossible("You can't bring yourself to target yourself.")

        # Display message for use whenever Item is consumed
        core.g.engine.message_log.add_message(self.parent.usetext, config.colour.use)

        # Logic for whether enemy can be confused
        if isinstance(target.ai, parts.ai.PassiveStationary) or isinstance(target.ai, parts.ai.HostileStationary):
            core.g.engine.message_log.add_message(
                f"The {self.parent.name} has no effect...",
                config.colour.enemy_evade,
            )
        else:
            core.g.engine.message_log.add_message(
                f"The {target.name} becomes confused and starts to stumble around!",
                config.colour.status_effect_applied,
            )

            self.save_bonus = dnd_bonus_calc(target.fighter.intellect_modifier)
            target.ai = parts.ai.ConfusedEnemy(
                entity=target, previous_ai=target.ai, turns_remaining=self.calc_turns,
            )
        self.consume()


class TeleportOtherConsumable(Consumable):
    def get_action(self, consumer: Actor) -> core.input_handlers.TeleotherEventHandler:
        core.g.engine.message_log.add_message("Select a target location.", config.colour.needs_target)
        return core.input_handlers.TeleotherEventHandler(callback=lambda xy: ItemAction(consumer, self.parent, xy))

    def activate(self, action: ItemAction) -> None:
        consumer = action.entity
        target = action.target_actor

        if not core.g.engine.game_map.visible[action.target_xy]:
            raise Impossible("You cannot target an area that you cannot see.")
        if not target:
            raise Impossible("No enemy at location (You must select an enemy to target).")

        # Display message for use whenever Item is consumed
        core.g.engine.message_log.add_message(self.parent.usetext, config.colour.use)

        # Logic for whether enemy can be teleported
        if isinstance(target.ai, parts.ai.PassiveStationary) or isinstance(target.ai, parts.ai.HostileStationary):
            core.g.engine.message_log.add_message(
                f"The {self.parent.name} has no effect...",
                config.colour.enemy_evade,
            )
        else:
            if target.name == 'Player':
                core.g.engine.message_log.add_message(
                    f"The space around you warps and soon after you emerge in a different place!",
                    config.colour.status_effect_applied,
                    )
            else:
                core.g.engine.message_log.add_message(
                    f"The space around {target.name} warps and it disappears from view!",
                    config.colour.status_effect_applied,
                    )

            # Get a random walkable tile that is not in the player's FOV
            random_x, random_y = core.g.engine.game_map.get_random_walkable_nonfov_tile()
            target.teleport(random_x, random_y)
        self.consume()


class ImmolateConsumable(Consumable):
    def get_action(self, consumer: Actor) -> core.input_handlers.SingleRangedAttackHandler:
        core.g.engine.message_log.add_message("Select a target location.", config.colour.needs_target)
        return core.input_handlers.SingleRangedAttackHandler(callback=lambda xy: ItemAction(consumer, self.parent, xy))

    def activate(self, action: ItemAction) -> None:
        target = action.target_actor

        if not core.g.engine.game_map.visible[action.target_xy]:
            raise Impossible("You cannot target an area that you cannot see.")
        if not target:
            raise Impossible("No enemy at location (You must select an enemy to target).")

        # Display message for use whenever Item is consumed
        core.g.engine.message_log.add_message(self.parent.usetext, config.colour.use)
        if action.target_actor.name == "Player":
            core.g.engine.message_log.add_message(
                f"Your body is engulfed in searing heat and you burst into flames!",
                config.colour.on_fire,
            )
        else:
            core.g.engine.message_log.add_message(
                f"The {target.name} bursts into flames!",
                config.colour.on_fire,
            )

        # Add burning effect to target
        effect = BurningEffect(turns=1)
        effect.parent = action.target_actor
        target.active_effects.append(effect)

        # Flip the switch so that docile entities will become hostile after being hit by this effect
        if isinstance(target.ai, parts.ai.NPC) or isinstance(target.ai, parts.ai.PlantKeeper):
            target.ai = parts.ai.HostileEnemy(entity=target)

        # Make sure that rooted enemies don't wander around
        if not isinstance(target.ai, parts.ai.PassiveStationary) or isinstance(target.ai, parts.ai.HostileStationary):
            target.ai = parts.ai.BurningEnemy(entity=target, previous_ai=target.ai)
        self.consume()
