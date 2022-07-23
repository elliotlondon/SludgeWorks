from typing import List

from parts.base_component import BaseComponent
from parts.entity import Actor


class Mutation(BaseComponent):
    """Effects which can be inherent or added, constant or continuous, which are assigned to an Actor
    and may be updated through effects, such as a level-up. Mutations can be thought of as abilities."""
    parent: Actor

    def __iter__(self):
        for x in self.__dict__:
            yield x

    def activate(self):
        """Activate this ability."""
        raise NotImplementedError()

    def expiry_message(self):
        """Print a message to the log when the effect is removed."""
        raise NotImplementedError()

    def tick(self):
        """On the passing of a turn, apply this effect."""
        raise NotImplementedError()
