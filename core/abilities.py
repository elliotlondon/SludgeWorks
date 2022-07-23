from typing import Tuple, Optional

from config.exceptions import Impossible

import core.g

from config.exceptions import Impossible
from parts.entity import Actor, Entity
from core.action import AbilityAction
import parts.mutations


class ShoveAction(AbilityAction):
    """Spend a turn to push an enemy away from you. Has no effect if a wall is behind the enemy."""

    def __init__(self, caster: Actor, target: Entity, x: int, y: int):
        super().__init__(
            entity=caster,
            target=target,
            x=x,
            y=y
        )

    def perform(self) -> Optional[Exception]:
        # Check if valid first
        # if

        # Work out new entity postition

        # for item in core.g.engine.game_map.items:
        #     if actor_location_x == item.x and actor_location_y == item.y:
        #         if len(inventory.items) >= inventory.capacity:
        #             raise Impossible("Your inventory is full.")
        #
        #         core.g.engine.game_map.entities.remove(item)
        #         item.parent = self.entity.inventory
        #         inventory.items.append(item)
        #
        #         core.g.engine.message_log.add_message(f"You pick up the {item.name}!")
        #         return

        raise Impossible("This action would have no effect.")