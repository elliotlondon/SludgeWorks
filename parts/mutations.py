from typing import List, Optional

import core.abilities
from parts.base_component import BaseComponent
from parts.entity import Actor, Entity
import core.abilities


class Mutation(BaseComponent):
    """Effects which can be inherent or added, constant or continuous, which are assigned to an Actor
    and may be updated through effects, such as a level-up. Mutations can be thought of as abilities."""
    parent: Actor

    def __init__(self,
                 name: str = "<Undefined>",
                 description: str  = "<Undefined>",
                 req_target: bool = False,
                 continuous: bool = False
                 ):
        self.name = name
        self.description = description
        self.req_target = req_target
        self.continuous = continuous

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
        raise NotImplementedError()


class Shove(Mutation):
    parent: Actor

    def __init__(self):
        super().__init__(
            name="Shove",
            description="Attempt to push an entity away from you. Deals no damage.",
            req_target=True,
            continuous=False
        )
        self.action = core.abilities.ShoveAction

    def activate(self, caster: Actor, target: Entity, x: int, y: int) -> Optional[core.abilities.ShoveAction]:
        return core.abilities.ShoveAction(caster, target, x, y)
