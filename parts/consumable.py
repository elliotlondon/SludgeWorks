from __future__ import annotations

import random
from typing import Optional, TYPE_CHECKING

from utils.random_utils import dnd_bonus_calc
import config.colour
import parts.ai
import parts.inventory
from config.exceptions import Impossible
from core.actions import ItemAction
from core.input_handlers import ActionOrHandler, AreaRangedAttackHandler, SingleRangedAttackHandler
from parts.base_component import BaseComponent
import core.g

if TYPE_CHECKING:
    from entity import Actor, Item


class Consumable(BaseComponent):
    parent: Item

    def item(self) -> parts.entity.Item:
        assert isinstance(self.parent, parts.entity.Item)
        return self.parent

    def get_action(self, consumer: Actor) -> Optional[ActionOrHandler]:
        """Try to return the action for this item."""
        return ItemAction(consumer, self.parent)

    def activate(self, action: ItemAction) -> None:
        """Invoke this items ability. 'action' is the context for this activation."""
        raise NotImplementedError()

    def consume(self) -> None:
        """Remove the consumed item from its containing inventory."""
        entity = self.parent
        inventory = entity.parent

        # Remove Item from inventory
        if isinstance(inventory, parts.inventory.Inventory):
            inventory.items.remove(entity)


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

    def get_action(self, consumer: Actor) -> AreaRangedAttackHandler:
        core.g.engine.message_log.add_message(
            "Select a target location.", config.colour.needs_target
        )
        return AreaRangedAttackHandler(
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

        if not targets_hit:
            core.g.engine.message_log.add_message("It has seems to have no effect...", config.colour.invalid)
        self.consume()


class LightningDamageConsumable(Consumable):
    def __init__(self, damage: int, maximum_range: int):
        self.damage = damage
        self.maximum_range = maximum_range

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

    def get_action(self, consumer: Actor) -> SingleRangedAttackHandler:
        core.g.engine.message_log.add_message("Select a target location.", config.colour.needs_target)
        return SingleRangedAttackHandler(callback=lambda xy: ItemAction(consumer, self.parent, xy))

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
        if isinstance(target.ai, parts.ai.PassiveStationary):
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
