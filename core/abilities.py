from typing import Tuple, Optional

import config.colour
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
        # Work out new entity postition
        dx = self.target.x - self.caster.x
        dy = self.target.y - self.caster.y
        new_x = dx * 2
        new_y = dy * 2

        # Check if new coords hit a wall or are oob
        if new_x >= core.g.console.width or new_y >= core.g.console.height:
            "You cannot shove the enemy there!"

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

        core.g.engine.message_log.add_message("This action would have no effect.", config.colour.impossible)
        return None
