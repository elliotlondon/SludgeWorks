from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from parts.entity import Entity
    from maps.game_map import GameMap


class BaseComponent:
    parent: Entity  # Owning entity instance.

    @property
    def gamemap(self) -> GameMap:
        return self.parent.gamemap
