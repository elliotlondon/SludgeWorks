from __future__ import annotations

from typing import TYPE_CHECKING

import tcod
from tcod.map import compute_fov

import core.input_handlers
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
