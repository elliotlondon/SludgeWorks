from __future__ import annotations

import math
from typing import TYPE_CHECKING

from parts.base_component import BaseComponent
import core.g

if TYPE_CHECKING:
    from entity import Actor


class Level(BaseComponent):
    parent: Actor

    def __init__(
            self,
            current_level: int = 1,
            current_xp: int = 0,
            level_up_base: int = 0,
            xp_given: int = 0,
    ):
        self.current_level = current_level
        self.current_xp = current_xp
        self.level_up_base = level_up_base
        self.xp_given = xp_given

    @property
    def experience_to_next_level(self) -> int:
        return math.floor(self.level_up_base * 2 * self.current_level * math.exp(1) / 3 +
                          self.current_level * math.exp(1))

    @property
    def requires_level_up(self) -> bool:
        return self.current_xp > self.experience_to_next_level

    def add_xp(self, xp: int) -> None:
        if xp == 0 or self.level_up_base == 0:
            return

        self.current_xp += xp

        if self.parent.name == 'Player':
            core.g.engine.message_log.add_message(f"You gain {xp} experience points.")
        if self.requires_level_up:
            core.g.engine.message_log.add_message(f"You advance to level {self.current_level + 1}!")

    def increase_level(self) -> None:
        self.current_xp -= self.experience_to_next_level
        self.current_level += 1

    def increase_max_hp(self) -> None:
        # Increase hp by vitality level
        amount = self.parent.fighter.base_vitality

        self.parent.fighter.base_max_hp += amount
        self.parent.fighter.hp += amount

        core.g.engine.message_log.add_message(f"Your health and maximum health increase by {amount}.")

        self.increase_level()

    def increase_power(self, amount: int = 1) -> None:
        self.parent.fighter.base_strength += amount

        core.g.engine.message_log.add_message(f"Your strength skill improves by {amount}.")

        self.increase_level()

    def increase_defense(self, amount: int = 1) -> None:
        self.parent.fighter.base_dexterity += amount

        core.g.engine.message_log.add_message(f"Your dexterity skill improves by {amount}.")

        self.increase_level()
