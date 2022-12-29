from __future__ import annotations

import random
from typing import TYPE_CHECKING, Optional

import config.colour
import core.g
import parts.entity
from parts.base_component import BaseComponent
from utils.random_utils import roll_dice

if TYPE_CHECKING:
    from entity import Item, Actor


class ItemModifier(BaseComponent):
    """A constructor for modifiers that can be applied to an item."""
    parent: Item

    def __iter__(self):
        for x in self.__dict__:
            yield x


class PoisonModifier(ItemModifier):
    """Modifier which deals X damage over Y turns, with a given difficulty save."""

    def __init__(
            self,
            damage: int,
            turns: int,
            difficulty: int
    ):
        self.damage = damage
        self.turns = turns
        self.difficulty = difficulty


class Effect(BaseComponent):
    """Over-time effects that are applied to Actors."""
    parent: Actor

    def __iter__(self):
        for x in self.__dict__:
            yield x

    def expiry_message(self):
        """Print a message to the log when the effect is removed."""
        raise NotImplementedError()

    def tick(self):
        """On the passing of a turn, apply this effect."""
        raise NotImplementedError()

    def get_colour(self):
        """Provide an array of bg colours for use in visually animating entities under this effect."""
        raise NotImplementedError()


class PoisonEffect(Effect):
    """Poison an entity, dealing X damage for Y turns"""

    def __init__(self,
                 damage: int,
                 turns: int,
                 parent: Optional[parts.entity.Actor] = None,
                 ):
        self.damage = damage
        self.turns = turns
        if parent:
            # If parent isn't provided now then it will be set later.
            self.parent = parent

    def tick(self):
        self.parent.fighter.hp -= self.damage
        if self.parent.name == "Player":
                core.g.engine.message_log.add_message(f"You takes {self.damage} damage from the poison.",
                                                      config.colour.poison)
        else:
            core.g.engine.message_log.add_message(f"The {self.parent.name} takes {self.damage} damage from the poison.",
                                                  config.colour.poison)
        self.turns -= 1

    def expiry_message(self):
        if self.parent.name == "Player":
            core.g.engine.message_log.add_message(f"You recover from the poison.", config.colour.poison)
        else:
            core.g.engine.message_log.add_message(f"The {self.parent.name} recovers from the poison.",
                                                  config.colour.poison)

    def get_colour(self):
        if not core.g.global_clock.current_tic() + 1 % 16:
            return config.colour.poison
        else:
            return None


class BleedEffect(Effect):
    """Start a bleed on an entity, dealing X damage while a Y vit save fails, for up to Z turns"""

    def __init__(self,
                 damage: int,
                 turns: int,
                 difficulty: int,
                 parent: Optional[parts.entity.Actor] = None,
                 ):
        self.damage = damage
        self.turns = turns
        self.difficulty = difficulty
        if parent:
            # If parent isn't provided now then it will be set later.
            self.parent = parent

    def tick(self):
        # Check if this turn the bleeding is resisted
        if not roll_dice(1, 20) + self.parent.fighter.vitality_modifier > self.difficulty:
            self.parent.fighter.hp -= self.damage

            # If it bleeds, add blood to the floor
            if self.parent.blood == "Blood":
                core.g.engine.game_map.stain_tile(self.parent.x, self.parent.y,
                                                  light_fg=config.colour.blood, modifiers="Bloody")
            # Messages
            if self.parent.name == "Player":
                core.g.engine.message_log.add_message(f"You bleed for {self.damage} damage.",
                                                      config.colour.bleed)
            else:
                core.g.engine.message_log.add_message(
                    f"The {self.parent.name} takes {self.damage} damage from bleeding.",
                    config.colour.bleed)
        self.turns -= 1

    def expiry_message(self):
        if self.parent.name == "Player":
            core.g.engine.message_log.add_message(f"You stop bleeding.", config.colour.bleed_end)
        else:
            core.g.engine.message_log.add_message(f"The {self.parent.name} stops bleeding.",
                                                  config.colour.bleed_end)

    def get_colour(self):
        if not core.g.global_clock.current_tic() % 16:
            return config.colour.bleed
        else:
            return None


class BurningEffect(Effect):
    """Cause an entity to catch fire, dealing unavoidable X damage per turn and causing them to panic
    for an indefinite number of turns until the entity makes a successful save"""

    def __init__(self,
                 turns: int,
                 parent: Optional[parts.entity.Actor] = None,
                 ):
        self.turns = turns
        if parent:
            # If parent isn't provided now then it will be set later.
            self.parent = parent
        self.first_turn = True

    def tick(self):
        # Check if the entity is able to put out the flames
        if self.first_turn or not roll_dice(1, 20) > 14:
            self.turns = 1
            damage = random.randint(1, 3)
            self.parent.fighter.hp -= damage
            # Messages
            if self.parent.name == "Player":
                core.g.engine.message_log.add_message(f"You are on fire! You burn for {damage} damage!",
                                                      config.colour.on_fire)
            else:
                core.g.engine.message_log.add_message(
                    f"The {self.parent.name} takes {damage} damage from the flames.",
                    config.colour.on_fire)
            self.first_turn = False
        else:
            self.turns = 0

    def expiry_message(self):
        if self.parent.name == "Player":
            core.g.engine.message_log.add_message(f"You are no longer on fire.", config.colour.on_fire_end)
        else:
            core.g.engine.message_log.add_message(f"The {self.parent.name} is no longer on fire.",
                                                  config.colour.on_fire_end)

    def get_colour(self):
        if not core.g.global_clock.current_tic() % 6:
            return config.colour.on_fire
        elif not core.g.global_clock.current_tic() % 4:
            return config.colour.on_fire_2
        else:
            return None


class StunEffect(Effect):
    """Stun an entity for X turns. Stun immunity is added for 3 turns after the stun expires."""

    def __init__(self,
                 turns: int,
                 parent: Optional[parts.entity.Actor] = None,
                 ):
        self.turns = turns
        if parent:
            # If parent isn't provided now then it will be set later.
            self.parent = parent

    def tick(self):
        # Add stun immunity if there is one turn left
        if self.turns == 1:
            immunity = parts.effects.SecondWindEffect(turns=3)

        # Messages
        if self.parent.name == "Player":
            core.g.engine.message_log.add_message(f"You are stunned!", config.colour.stun)
        self.turns -= 1

    def expiry_message(self):
        if self.parent.name == "Player":
            core.g.engine.message_log.add_message(f"You are no longer stunned.", config.colour.stun_end)
        else:
            core.g.engine.message_log.add_message(f"The {self.parent.name} is no longer stunned.",
                                                  config.colour.stun_end)

    def get_colour(self):
        if not core.g.global_clock.current_tic() % 8:
            return config.colour.stun
        else:
            return None


class SecondWindEffect(Effect):
    """Prevents the entity under this effect from being stunned for X turns."""

    def __init__(self,
                 turns: int,
                 parent: Optional[parts.entity.Actor] = None,
                 ):
        self.turns = turns
        if parent:
            # If parent isn't provided now then it will be set later.
            self.parent = parent

    def tick(self):
        # Simply count down, this effect does nothing.
        self.turns -= 1

    def expiry_message(self):
        pass

    def get_colour(self):
        return None