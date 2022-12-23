from typing import Optional

import config.colour
import core.abilities
import core.abilities
import core.g
from parts.base_component import BaseComponent
from parts.entity import Actor


class Mutation(BaseComponent):
    """Effects which can be inherent or added, constant or continuous, which are assigned to an Actor
    and may be updated through effects, such as a level-up. Mutations can be thought of as abilities."""
    parent: Actor

    def __init__(self,
                 name: str = "<Undefined>",
                 description: str = "<Undefined>",
                 req_target: bool = False,
                 continuous: bool = False,
                 cooldown: int = 0,
                 range: int = 0
                 ):
        self.name = name
        self.description = description
        self.req_target = req_target
        self.continuous = continuous
        self.cooldown = cooldown
        self.range = range

    def __iter__(self):
        for x in self.__dict__:
            yield x

    def activate(self, *args):
        """Activate this ability."""
        raise NotImplementedError()

    def expiry_message(self):
        """Print a message to the log when the effect is removed."""
        raise NotImplementedError()

    def tick(self):
        """On the passing of a turn, apply this effect."""
        if self.cooldown > 0:
            self.cooldown -= 1


class Shove(Mutation):
    """Push a hostile entity away. Deals no damage.
    Entities can collide and suffer 1 point of damage (str roll, difficulty 8)"""
    parent: Actor

    def __init__(self):
        super().__init__(
            name="Shove",
            description="Attempt to push a creature away from you. "
                        "Can deal minor damage if the target collides with another enemy",
            req_target=True,
            continuous=False,
            cooldown=0,
            range=1
        )
        self.action = core.abilities.ShoveAction

    def activate(self, caster: Actor, target: Actor, x: int, y: int) -> Optional[core.abilities.ShoveAction]:
        if self.cooldown > 0 and self.parent.name == "Player":
            core.g.engine.message_log.add_message("You cannot perform this ability yet.", config.colour.impossible)
            return None
        else:
            self.cooldown = 6
            return core.abilities.ShoveAction(caster, target, x, y)


class Bite(Mutation):
    """Bite the target. Cannot be dodged but damage can be resisted. Can cause bleeding if vit check 12 fails."""
    parent: Actor

    def __init__(self, damage: int, turns: int, difficulty: int, cooldown: int):
        super().__init__(
            name="Shove",
            description="Bite a neaby creature. Deals 1d4, and can cause minor bleeding on hit.",
            req_target=True,
            continuous=False,
            cooldown=0,
            range=1
        )
        self.action = core.abilities.ShoveAction
        self.damage = damage
        self.turns = turns
        self.difficulty = difficulty
        self.cooldown_max = cooldown

    def activate(self, caster: Actor, target: Actor, x: int, y: int) -> \
            Optional[core.abilities.BiteAction]:
        if self.cooldown > 0 and self.parent.name == "Player":
            core.g.engine.message_log.add_message("You cannot perform this ability yet.", config.colour.impossible)
            return None
        else:
            self.cooldown = self.cooldown_max
            return core.abilities.BiteAction(caster, target, x, y, self.damage, self.turns, self.difficulty)


class MemoryWipe(Mutation):
    """Attack the target with a memory wiping mental attack."""
    parent: Actor

    def __init__(self, cooldown: int):
        super().__init__(
            name="Shove",
            description="Savagely attack the mind of a neaby creature, performing a mental attack and "
                        "wiping memories on crit.",
            req_target=True,
            continuous=False,
            cooldown=5,
            range=1
        )
        self.action = core.abilities.MemoryWipeAction
        self.cooldown_max = cooldown

    def activate(self, caster: Actor, target: Actor, x: int, y: int) -> \
            Optional[core.abilities.MemoryWipeAction]:
        if self.cooldown > 0 and self.parent.name == "Player":
            core.g.engine.message_log.add_message("You cannot perform this ability yet.", config.colour.impossible)
            return None
        else:
            self.cooldown = self.cooldown_max
            return core.abilities.MemoryWipeAction(caster, target, x, y)
