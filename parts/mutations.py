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
        pass


class Shove(Mutation):
    parent: Actor

    def __init__(self):
        super().__init__(
            name="Shove",
            description="Attempt to push an entity away from you. Deals no damage.",
            req_target=True,
            continuous=False,
            cooldown=0,
            range=1
        )
        self.action = core.abilities.ShoveAction

    def tick(self):
        """On the passing of a turn, apply this effect."""
        if self.cooldown > 0:
            self.cooldown -= 1

    def activate(self, caster: Actor, target: Actor, x: int, y: int) -> Optional[core.abilities.ShoveAction]:
        if self.cooldown > 0:
            core.g.engine.message_log.add_message("You cannot perform this ability yet.", config.colour.impossible)
            return None
        else:
            self.cooldown = 6
            return core.abilities.ShoveAction(caster, target, x, y)
