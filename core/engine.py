from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import tcod
from tcod.map import compute_fov

import core.input_handlers
import core.render_functions
from config import colour
from config.exceptions import Impossible
from gui.message_log import MessageLog
from maps.tiles import SHROUD

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
        self.convos: dict[str, core.input_handlers.ConversationEventHandler] = {}

    def handle_enemy_turns(self) -> None:
        # When enemy turn starts, first tick all player abilities/mutations
        if self.player.abilities:
            for ability in self.player.abilities:
                if ability.cooldown > 0:
                    ability.tick()
        if self.player.mutations:
            for mutation in self.player.mutations:
                if mutation.cooldown > 0:
                    mutation.tick()
        self.player.trigger_active_effects()
        # Iterate over all enemy turns
        for entity in set(self.game_map.actors) - {self.player}:
            if entity.ai:
                entity.trigger_active_effects()
                if entity.abilities:
                    for ability in entity.abilities:
                        ability.tick()
                try:
                    entity.ai.perform()
                except Impossible:
                    pass  # Ignore impossible action exceptions from AI.
        self.turn_number += 1

    def update_fov(self) -> None:
        """Recompute the visible area based on the players point of view."""
        # First handle open/closed door changing fov algo
        for entity in self.game_map.entities:
            if 'Door' in entity.name:
                if 'Open' in entity.properties:
                    self.game_map.tiles[entity.x, entity.y]['transparent'] = True
                elif 'Closed' in entity.properties:
                    self.game_map.tiles[entity.x, entity.y]['transparent'] = False

        # Derive all other fov from tile properties
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],
            (self.player.x, self.player.y),
            radius=6, algorithm=tcod.FOV_BASIC
        )
        # If a tile is "visible" it should be added to "explored".
        self.game_map.explored |= self.game_map.visible

        # # if logging.DEBUG >= logging.root.level:
        # self.game_map.visible[:] = self.game_map

    def render(self) -> None:
        """Render everything on the screen when called"""
        from core.g import console

        # First render the game map
        console.tiles_rgb[0:self.game_map.width, 0:self.game_map.height] = self.game_map.tiles["dark"]
        screen_shape = core.g.console.width, core.g.console.height
        # cam_x, cam_y =

        # If a tile is in the "visible" array, then draw it with the "light" colors.
        # If it isn't, but it's in the "explored" array, then draw it with the "dark" colors.
        # Otherwise, the default graphic is "SHROUD".
        console.tiles_rgb[0:self.game_map.width, 0:self.game_map.height] = np.select(
            condlist=[self.game_map.visible, self.game_map.explored],
            choicelist=[self.game_map.tiles["light"], self.game_map.tiles["dark"]],
            default=SHROUD
        )

        # Draw entities
        for entity in sorted(self.game_map.entities, key=lambda x: x.render_order.value):
            if not self.game_map.visible[entity.x, entity.y]:
                continue  # Skip entities that are not in the FOV.
            console.print(entity.x, entity.y, entity.char, fg=entity.colour)

        # Now render the ui components
        self.message_log.render(console=console, x=21, y=45, width=55, height=5)

        # Render hp bar
        core.render_functions.render_bar(
            console=console,
            current_value=self.player.fighter.hp,
            max_value=self.player.fighter.max_hp,
            x=1,
            y=core.g.screen_height - 5,
            bg_empty=colour.hp_bar_empty,
            bg_full=colour.hp_bar_filled,
            text=f"HP: {self.player.fighter.hp}/{self.player.fighter.max_hp}",
            total_width=20,
        )

        # Render xp bar
        core.render_functions.render_bar(
            console=console,
            current_value=self.player.level.current_xp,
            max_value=self.player.level.experience_to_next_level,
            x=1,
            y=core.g.screen_height - 4,
            bg_empty=colour.xp_bar_empty,
            bg_full=colour.xp_bar_filled,
            text=f"XP: {self.player.level.current_xp}/{self.player.level.experience_to_next_level}",
            total_width=20,
        )

        core.render_functions.render_dungeon_level(
            console=console,
            dungeon_level=self.game_world.current_floor,
            location=(0, core.g.screen_height - 3),
        )

        core.render_functions.render_turn_number(
            console=console,
            turn_number=self.turn_number,
            location=(0, core.g.screen_height - 2)
        )
