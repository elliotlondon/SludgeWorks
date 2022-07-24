from __future__ import annotations

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
