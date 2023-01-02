from __future__ import annotations

import logging
import copy
from typing import TYPE_CHECKING

import tcod
from tcod.map import compute_fov

from config.exceptions import DataLoadError
import parts.effects
from config.exceptions import Impossible
from gui.message_log import MessageLog
from core.quests import QuestTracker
from data.item_factory import create_all_items_from_json
from data.monster_factory import create_all_monsters_from_json
from data.object_factory import create_all_static_objects_from_json

if TYPE_CHECKING:
    from parts.entity import Actor, Entity
    from maps.game_map import GameMap, GameWorld


class Engine:
    game_map: GameMap
    game_world: GameWorld

    def __init__(self, player: Actor):
        self.turn_number: int = 0
        self.message_log = MessageLog()
        self.mouse_location = (0, 0)
        self.player = player
        self.last_actor: Actor
        self.quests = QuestTracker()
        self.entities = []

        # During init load all entities so that they can be deepcopied easily in future from all other locations.
        # Load items
        self.entities.extend(create_all_items_from_json('data/items/armour.json'))
        # self.entities.extend(create_all_items_from_json('data/items/artefacts.json'))
        self.entities.extend(create_all_items_from_json('data/items/healing.json'))
        self.entities.extend(create_all_items_from_json('data/items/other.json'))
        self.entities.extend(create_all_items_from_json('data/items/quest.json'))
        self.entities.extend(create_all_items_from_json('data/items/twigs.json'))
        self.entities.extend(create_all_items_from_json('data/items/weapons.json'))
        # # Load entities
        self.entities.extend(create_all_monsters_from_json('data/monsters/bosses.json'))
        self.entities.extend(create_all_monsters_from_json('data/monsters/crusaders.json'))
        self.entities.extend(create_all_monsters_from_json('data/monsters/cultists.json'))
        self.entities.extend(create_all_monsters_from_json('data/monsters/horrors.json'))
        self.entities.extend(create_all_monsters_from_json('data/monsters/npcs.json'))
        self.entities.extend(create_all_monsters_from_json('data/monsters/plants.json'))
        self.entities.extend(create_all_monsters_from_json('data/monsters/scavengers.json'))
        # Load static objects
        self.entities.extend(create_all_static_objects_from_json('data/static_objects/core_objects.json'))

    def clone(self, name: str) -> Entity:
        """Return a deepcopy of an entity with the same name as that which is specified"""
        for entity in self.entities:
            if entity.tag == name:
                return copy.deepcopy(entity)
        raise DataLoadError(f"Entity {name} could not be copied from engine.")

    def handle_enemy_turns(self) -> None:
        # Iterate over all enemy turns
        for entity in set(self.game_map.actors) - {self.player}:
            if entity.ai:
                entity.trigger_active_effects()
                if entity.abilities:
                    for ability in entity.abilities:
                        ability.tick()
                # If stunned skip turn by default after ticking the effect
                if not entity.is_stunned():
                    try:
                        entity.ai.perform()
                    except Impossible:
                        pass  # Ignore impossible action exceptions from AI.
                else:
                    pass
        self.turn_number += 1

        # When enemy turn starts, first tick all player abilities/mutations
        if self.player.abilities:
            for ability in self.player.abilities:
                if ability.cooldown > 0:
                    ability.tick()
        # if self.player.mutations:
        #     for mutation in self.player.mutations:
        #         if mutation.cooldown > 0:
        #             mutation.tick()
        self.player.trigger_active_effects()

    def update_fov(self) -> None:
        """Recompute the visible area based on the players point of view."""
        # First handle open/closed door changing fov algo
        for entity in self.game_map.entities:
            if 'Door' in entity.name:
                if 'Open' in entity.properties or 'Seethrough' in entity.properties:
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

        if 5 >= logging.root.level < 1:
            self.game_map.visible[:] = self.game_map
