from typing import Optional

import config.colour
import core.actions
import core.g
import parts.ai
import parts.mutations
from core.action import AbilityAction
from parts.entity import Actor
from utils.random_utils import roll_dice


class ShoveAction(AbilityAction):
    """Spend a turn to push an enemy away from you. Has no effect if a wall is behind the enemy."""

    def __init__(self, caster: Actor, target: Actor, x: int, y: int):
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

        # First check for selection errors
        if dx == 0 and dy == 0:
            core.g.engine.message_log.add_message("You cannot perform this action upon yourself.",
                                                  config.colour.impossible)
            return None
        if abs(dx) >= 1.5 or abs(dy) >= 1.5:
            core.g.engine.message_log.add_message("You must select a tile no more than 1 square away.",
                                                  config.colour.impossible)
            return None
        if not self.target.fighter:
            core.g.engine.message_log.add_message("That is not a valid target.",
                                                  config.colour.impossible)
            return None
        if isinstance(self.target.ai, parts.ai.PassiveStationary) or \
                isinstance(self.target.ai, parts.ai.HostileStationary):
            core.g.engine.message_log.add_message("That target cannot be moved.",
                                                  config.colour.impossible)
            return None

        # Check if new coords hit a wall or are oob
        if self.target.x + dx >= core.g.console.width or self.target.y + dy >= core.g.console.height or \
                self.target.x + dx <= 0 or self.target.y + dy <= 0:
            core.g.engine.message_log.add_message("The target cannot be pushed into the destination",
                                                  config.colour.impossible)
            return None
        elif not core.g.engine.game_map.tiles['walkable'][self.target.x + dx, self.target.y + dy]:
            core.g.engine.message_log.add_message(f"You push the {self.target.name}, but it has no space to move away.",
                                                  config.colour.enemy_evade)
            return None
        else:
            # Calculate if push lands successfully
            attack_roll = roll_dice(1, 20) + self.caster.fighter.strength_modifier
            defend_roll = roll_dice(1, 20) + self.target.fighter.strength_modifier
            # if attack_roll > defend_roll:
            core.g.engine.message_log.add_message(f"You push the {self.target.name} and it stumbles backwards!",
                                                  config.colour.ability_used)
            return core.actions.BumpAction(self.target, dx, dy).perform()
            # else:
            # core.g.engine.message_log.add_message(f"The {self.target.name} resists your shove!",
            #                                       config.colour.enemy_evade)

        core.g.engine.message_log.add_message("This action would have no effect.", config.colour.impossible)
        return None
