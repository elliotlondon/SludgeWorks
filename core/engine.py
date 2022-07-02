from __future__ import annotations

import lzma
import pickle
from typing import TYPE_CHECKING

from tcod.console import Console
from tcod.map import compute_fov

import config.colour
import core.render_functions
from config.exceptions import Impossible
from gui.message_log import MessageLog

if TYPE_CHECKING:
    from lib.entity import Actor
    from maps.game_map import SimpleGameMap, GameWorld


class Engine:
    game_map: SimpleGameMap
    game_world: GameWorld

    def __init__(self, player: Actor):
        self.message_log = MessageLog()
        self.mouse_location = (0, 0)
        self.player = player

    def handle_enemy_turns(self) -> None:
        for entity in set(self.game_map.actors) - {self.player}:
            if entity.ai:
                try:
                    entity.ai.perform()
                except Impossible:
                    pass  # Ignore impossible action exceptions from AI.

    def update_fov(self) -> None:
        """Recompute the visible area based on the players point of view."""
        # if logging.DEBUG >= logging.root.level:
        # self.game_map.visible[:] = self.game_map
        # else:
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],
            (self.player.x, self.player.y),
            radius=5,
        )
        # If a tile is "visible" it should be added to "explored".
        self.game_map.explored |= self.game_map.visible

    def render(self, console: Console) -> None:
        self.game_map.render(console)

        self.message_log.render(console=console, x=21, y=45, width=55, height=5)

        # Render hp bar
        core.render_functions.render_bar(
            console=console,
            current_value=self.player.fighter.hp,
            max_value=self.player.fighter.max_hp,
            x=1,
            y=45,
            bg_empty=config.colour.hp_bar_empty,
            bg_full=config.colour.hp_bar_filled,
            text=f"HP: {self.player.fighter.hp}/{self.player.fighter.max_hp}",
            total_width=20,
        )

        # Render xp bar
        core.render_functions.render_bar(
            console=console,
            current_value=self.player.level.current_xp,
            max_value=self.player.level.experience_to_next_level,
            x=1,
            y=46,
            bg_empty=config.colour.xp_bar_empty,
            bg_full=config.colour.xp_bar_filled,
            text=f"XP: {self.player.level.current_xp}/{self.player.level.experience_to_next_level}",
            total_width=20,
        )

        core.render_functions.render_dungeon_level(
            console=console,
            dungeon_level=self.game_world.current_floor,
            location=(0, 47),
        )

        core.render_functions.render_names_at_mouse_location(console=console, x=21, y=44, engine=self)

    def save_as(self, filename: str) -> None:
        """Save this Engine instance as a compressed file."""
        save_data = lzma.compress(pickle.dumps(self))
        with open(filename, "wb") as f:
            f.write(save_data)
