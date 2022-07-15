from __future__ import annotations

import random
from typing import TYPE_CHECKING

from tcod import FOV_SYMMETRIC_SHADOWCAST
from tcod.map import compute_fov

import config.colour
from config.exceptions import Impossible
from gui.message_log import MessageLog

if TYPE_CHECKING:
    from parts.entity import Actor
    from maps.game_map import SimpleGameMap, GameWorld


class Engine:
    game_map: SimpleGameMap
    game_world: GameWorld

    def __init__(self, player: Actor):
        self.turn_number: int = 0
        self.message_log = MessageLog()
        self.mouse_location = (0, 0)
        self.player = player
        self.last_actor: Actor

    def handle_enemy_turns(self) -> None:
        for entity in set(self.game_map.actors) - {self.player}:
            if entity.ai:
                try:
                    entity.ai.perform()
                except Impossible:
                    pass  # Ignore impossible action exceptions from AI.
        self.turn_number += 1

    def update_fov(self) -> None:
        """Recompute the visible area based on the players point of view."""
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],
            (self.player.x, self.player.y),
            radius=6, algorithm=FOV_SYMMETRIC_SHADOWCAST
        )
        # If a tile is "visible" it should be added to "explored".
        self.game_map.explored |= self.game_map.visible

        # # if logging.DEBUG >= logging.root.level:
        # self.game_map.visible[:] = self.game_map
