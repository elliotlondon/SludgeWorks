from __future__ import annotations

from typing import Optional, Tuple, TYPE_CHECKING

import core.g

if TYPE_CHECKING:
    from parts.entity import Actor, Item


class Action:
    def __init__(self, entity: Actor) -> None:
        super().__init__()
        self.entity = entity

    def perform(self) -> None:
        """
        Perform this action with the objects needed to determine its scope.
        This method must be overridden by Action subclasses.
        """
        raise NotImplementedError()


class ItemAction(Action):
    def __init__(
            self, entity: Actor, item: Item, target_xy: Optional[Tuple[int, int]] = None
    ):
        super().__init__(entity)
        self.item = item
        if not target_xy:
            target_xy = entity.x, entity.y
        self.target_xy = target_xy

    @property
    def target_actor(self) -> Optional[Actor]:
        """Return the actor at this actions destination."""
        return core.g.engine.game_map.get_actor_at_location(*self.target_xy)

    def perform(self) -> None:
        """Invoke the items ability, this action will be given to provide context."""
        if self.item.consumable:
            self.item.consumable.activate(self)
