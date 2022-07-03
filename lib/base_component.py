from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lib.entity import Entity
    from maps.game_map import SimpleGameMap


class BaseComponent:
    parent: Entity  # Owning entity instance.

    @property
    def gamemap(self) -> SimpleGameMap:
        return self.parent.gamemap
