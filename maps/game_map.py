from __future__ import annotations

import random
from typing import Iterable, Iterator, Optional, TYPE_CHECKING, Tuple, Dict, List

import numpy as np

import parts.entity
from maps import tiles
from parts.ai import PassiveStationary, NPC
from parts.entity import Item
from utils.math_utils import Graph

if TYPE_CHECKING:
    from core.engine import Engine
    from parts.entity import Entity

import maps.tiles


class SimpleGameMap:
    def __init__(
            self, engine: Engine, width: int, height: int, entities: Iterable[Entity] = ()):
        self.engine = engine
        self.width, self.height = width, height
        self.entities = set(entities)
        self.exiles = []
        self.tiles = np.full((width, height), fill_value=maps.tiles.wall, order="F")
        self.tile_modifiers = np.full((width, height), fill_value=[None], order="F")
        self.rooms = []
        self.room_zone = np.full((width, height), fill_value=False, order="F")  # Areas which are rooms
        self.doors = np.full((width, height), fill_value=False, order="F")  # Tiles which have a door at their location
        self.tunnel = np.full((width, height), fill_value=False, order="F")  # Tunnel tiles
        self.visible = np.full((width, height), fill_value=False, order="F")  # Tiles the player can currently see
        self.explored = np.full((width, height), fill_value=False, order="F")  # Tiles the player has seen before
        self.accessible = np.full((width, height), fill_value=False, order="F")  # Tiles the player can access by foot

        self.downstairs_location = (0, 0)

    @property
    def gamemap(self) -> SimpleGameMap:
        return self

    @property
    def actors(self) -> Iterator[parts.entity.Actor]:
        """Iterate over this maps living actors."""
        yield from (
            entity
            for entity in self.entities
            if isinstance(entity, parts.entity.Actor) and entity.is_alive
        )

    @property
    def dangerous_actors(self) -> Iterator[parts.entity.Actor]:
        """Iterate over this maps living actors that are able to harm the player."""
        yield from (
            entity
            for entity in self.entities
            if
            isinstance(entity, parts.entity.Actor) and entity.is_alive and not isinstance(entity.ai, PassiveStationary)
            and not isinstance(entity.ai, NPC) and not entity.name == "Player"
        )

    @property
    def items(self) -> Iterator[Item]:
        yield from (entity for entity in self.entities if isinstance(entity, parts.entity.Item))

    def get_tile_at_explored_location(self, location_x: int, location_y: int) -> Optional[maps.tiles.tile_dt]:
        """Returns a tile within the explored array."""
        if self.explored[location_x, location_y]:
            return self.tiles[location_x, location_y]

    def get_all_entities_at_location(self, location_x: int, location_y: int) -> Optional[List[Entity]]:
        """Returns all entities at a given tile location x, y."""
        entities = []
        for entity in self.entities:
            if entity.x == location_x and entity.y == location_y:
                entities.append(entity)
        return entities

    def get_all_visible_entities(self, location_x: int, location_y: int) -> Optional[List[Entity]]:
        """Returns all enemies within the FOV."""
        entities = []
        for entity in self.entities:
            if entity.x == location_x and entity.y == location_y and self.visible[location_x, location_y]:
                entities.append(entity)
        return entities

    def get_blocking_entity_at_location(self, location_x: int, location_y: int) -> Optional[Entity]:
        """Returns the entity if it is at location x, y."""
        for entity in self.entities:
            if entity.blocks_movement and entity.x == location_x and entity.y == location_y:
                return entity

        return None

    def get_surrounding_interactables(self, location_x: int, location_y: int) -> Optional[List[Entity]]:
        """Get list of all entities that can be interacted with surrounding a selected tile, including diagonals."""
        x_values = [location_x - 1, location_x, location_x + 1]
        y_values = [location_y - 1, location_y, location_y + 1]
        interactables = []
        for x in x_values:
            for y in y_values:
                for entity in self.entities:
                    if (entity.x == x and entity.y == y) and (isinstance(entity, parts.entity.StaticObject) or \
                                                              isinstance(entity.ai, parts.ai.NPC)):
                        interactables.append(entity)
        return interactables

    def get_actor_at_location(self, x: int, y: int) -> Optional[parts.entity.Actor]:
        """Returns the Actor at location x, y."""
        for actor in self.actors:
            if actor.x == x and actor.y == y:
                return actor

        return None

    def get_occupied(self):
        """Return all tiles which have an entity at their coordinates."""
        tiles = np.full((self.width, self.height), fill_value=False, order="F")
        for actor in self.actors:
            tiles[actor.x, actor.y] = True
        return tiles

    def in_bounds(self, x: int, y: int) -> bool:
        """Return True if x and y are within map bounds."""
        return 0 <= x < self.width and 0 <= y < self.height

    def find_neighbours(self, x, y):
        xi = (0, -1, 1) if 0 < x < self.width - 1 else ((0, -1) if x > 0 else (0, 1))
        yi = (0, -1, 1) if 0 < y < self.height - 1 else ((0, -1) if y > 0 else (0, 1))
        for a in xi:
            for b in yi:
                if a == b == 0:
                    continue
                yield (x + a, y + b)

    def get_random_walkable_tile(self) -> Tuple[int, int]:
        """Return the coordinates of a random walkable tile within the current floor."""
        walkable = np.nonzero(
            np.logical_and(self.tiles['walkable'], self.tiles['name'] != 'hole')
        )
        index = random.randint(0, len(walkable[0]) - 1)
        x = walkable[0][index]
        y = walkable[1][index]

        return (x, y)

    def get_random_unoccupied_nonfov_tile(self) -> Tuple[int, int]:
        """Return the coordinates of a random walkable tile within the current floor."""
        walkable = np.logical_and(self.tiles['walkable'], self.tiles['name'] != 'hole')
        unoccupied = np.nonzero(np.logical_xor(walkable, self.get_occupied()))
        index = random.randint(0, len(unoccupied[0]) - 1)
        x = unoccupied[0][index]
        y = unoccupied[1][index]

        return (x, y)

    def get_random_nearby_tile(self, location_x: int, location_y: int, radius: int) -> Tuple[int, int]:
        """Return the coordinates of a random tile of radius away from location x, y."""
        walkable = np.logical_and(self.tiles['walkable'], self.tiles['name'] != 'hole')
        unoccupied = np.nonzero(np.logical_xor(walkable, self.get_occupied()))
        x_region = list(np.unique(unoccupied[0])[location_x - radius:location_x + radius])
        y_region = list(np.unique(unoccupied[1])[location_y - radius:location_y + radius])
        if x_region == []:
            x_region = [location_x]
        if y_region == []:
            y_region = [location_y]
        x = random.choice(x_region)
        y = random.choice(y_region)

        return (x, y)

    def get_random_walkable_nontunnel_tile(self) -> Tuple[int, int]:
        """Return the coordinates of a random walkable tile that is not a tunnel within the current floor."""
        walkable = np.nonzero(
            np.logical_xor(np.logical_and(self.tiles['walkable'], self.tiles['name'] != 'hole'),
                           self.tunnel)
        )
        index = random.randint(0, len(walkable[0]) - 1)
        x = walkable[0][index]
        y = walkable[1][index]

        return (x, y)

    def calc_accessible(self):
        """Calculate which tiles within the walkable map are accessible to the player."""
        player = self.engine.player
        walkable = self.tiles['walkable']

        graph = Graph(self.width, self.height, walkable)
        accessible = graph.find_connected_area(player.x, player.y)

        # Tiles with blocking objects are inaccessible
        for entity in self.entities:
            if isinstance(entity, parts.entity.StaticObject):
                accessible[entity.x, entity.y] = False

        return accessible

    def prune_inaccessible(self, tile: maps.tiles.tile_dt):
        """Turns inaccessible tiles into the given tile variety."""
        for x in range(self.width):
            for y in range(self.height):
                if not self.accessible[x, y]:
                    self.tiles[x, y] = tile

    def stain_tile(self, x: int, y: int, **kwargs):
        """Change the colour of a tile at the current game map position"""
        name = self.tiles[x, y][0]
        walkable = self.tiles[x, y][1]
        transparent = self.tiles[x, y][2]
        dark_char = self.tiles[x, y][3][0]
        dark_fg = self.tiles[x, y][3][1]
        dark_bg = self.tiles[x, y][3][2]
        light_char = self.tiles[x, y][4][0]
        light_fg = self.tiles[x, y][4][1]
        light_bg = self.tiles[x, y][4][2]
        description = self.tiles[x, y][5]
        modifiers = []
        for key in kwargs:
            if key == "name":
                name = kwargs[key]
            elif key == "light_char":
                light_char = kwargs[key]
            elif key == "light_fg":
                light_fg = kwargs[key]
            elif key == "light_bg":
                light_bg = kwargs[key]
            elif key == "modifiers":
                modifiers.append(kwargs[key])

        # Make new tile from kwargs and parent inheritance
        self.tiles[x, y] = maps.tiles.new_tile(name=name,
                                               walkable=walkable,
                                               transparent=transparent,
                                               dark=(dark_char, dark_fg, dark_bg),
                                               light=(light_char, light_fg, light_bg),
                                               description=description
                                               )
        self.tile_modifiers[x, y] = list(np.unique(modifiers))

    def splatter_tiles(self, x: int, y: int, **kwargs):
        """Change the colour of some random tiles. Chooses 2-4 random tiles around the given location to change."""
        coords = [(1, 1,), (1, 0), (1, -1),
                  (0, 1), (0, 1), (0, -1),
                  (-1, 1), (-1, 0), (-1, -1)]

        coords = random.sample(coords, k=random.randint(1, 3))
        for coord in coords:
            light_fg = self.tiles[coord[0], coord[1]][4][1]
            light_bg = self.tiles[coord[0], coord[1]][4][2]
            modifiers = []
            for key in kwargs:
                if key == "light_fg":
                    light_fg = kwargs[key]
                elif key == "light_bg":
                    light_bg = kwargs[key]
                elif key == "modifiers":
                    modifiers = kwargs[key]
            self.stain_tile(x + coord[0], y + coord[1],
                            light_fg=light_fg, light_bg=light_bg,
                            modifiers=modifiers)

    def remove_entity_at_location(self, name: str, x: int, y: int):
        """Removes all entities corresponding to the given key from the dungeon. Used during mapgen if
        something was placed on a tile which is no longer valid."""
        for entity in self.entities:
            if entity.x == x and entity.y == y and name in entity.name:
                self.entities.remove(entity)

# TODO: Add saved gamemaps to gameworld
class GameWorld:
    """
    Holds the settings for the GameMap, and generates new maps when moving down the stairs.
    """

    def __init__(
            self,
            *,
            engine: Engine,
            max_rooms: int,
            room_max_size: int,
            room_min_size: int,
            map_width: int,
            map_height: int,
            cave_smoothing: int = 1,
            cave_p: int = 50,
            caves: bool = True,
            rooms: bool = True,
            erode: bool = False,
            floors: Dict[str, SimpleGameMap] = None,
            current_floor: int = 0
    ):
        if floors is None:
            floors = {}
        # Floor params
        self.max_rooms = max_rooms
        self.room_max_size = room_max_size
        self.room_min_size = room_min_size
        self.map_width = map_width
        self.map_height = map_height
        # Biome params
        self.cave_smoothing = cave_smoothing
        self.cave_p = cave_p
        self.caves = caves
        self.rooms = rooms
        self.erode = erode

        self.engine = engine
        self.floors = floors
        self.current_floor = current_floor

    def generate_floor(self) -> None:
        from maps.procgen import generate_dungeon

        # Logic for floor generation
        self.current_floor += 1
        if self.current_floor == 1:
            # First floor, unique scenario
            new_floor = generate_dungeon(
                max_rooms=self.max_rooms,
                room_min_size=self.room_min_size,
                room_max_size=self.room_max_size,
                map_width=self.map_width,
                map_height=self.map_height,
                engine=self.engine,
            )
        elif 2 <= self.current_floor <= 4:
            # 3 floors of surface caves. Caves get broader as you descend
            self.room_max_size = 4
            self.room_min_size = 1
            self.cave_smoothing += 1
            self.cave_p -= 5
            self.rooms = True
            self.erode = True
            new_floor = generate_dungeon(
                max_rooms=self.max_rooms,
                room_min_size=self.room_min_size,
                room_max_size=self.room_max_size,
                map_width=self.map_width,
                map_height=self.map_height,
                engine=self.engine,
            )
        elif self.current_floor == 5:
            # 4th floor suddenly breaks into tunnels
            self.max_rooms = 25
            self.room_max_size = 4
            self.room_min_size = 1
            self.cave_smoothing = 1
            self.cave_p += 10
            self.rooms = True
            self.erode = False
            new_floor = generate_dungeon(
                max_rooms=self.max_rooms,
                room_min_size=self.room_min_size,
                room_max_size=self.room_max_size,
                map_width=self.map_width,
                map_height=self.map_height,
                engine=self.engine,
            )
        elif 6 <= self.current_floor <= 7:
            # 5th and 6th floors are progressively narrowing tunnels
            self.max_rooms += 5
            self.room_min_size -= 1
            self.room_max_size -= 1
            new_floor = generate_dungeon(
                max_rooms=self.max_rooms,
                room_min_size=self.room_min_size,
                room_max_size=self.room_max_size,
                map_width=self.map_width,
                map_height=self.map_height,
                engine=self.engine,
            )
        else:
            # Not yet implemented
            new_floor = generate_dungeon(
                max_rooms=self.max_rooms,
                room_min_size=self.room_min_size,
                room_max_size=self.room_max_size,
                map_width=self.map_width,
                map_height=self.map_height,
                engine=self.engine,
            )

        self.engine.game_map = new_floor
        self.floors[f'level_{self.current_floor}'] = new_floor


# class GameMap:
#     dark_wall = tcod.dark_grey
#     light_wall = tcod.Color(150, 100, 50)
#     dark_ground = tcod.black
#     light_ground = tcod.dark_grey
#     floor_chars = [' ', '.', ',', '`']
#
#     def __init__(self, current_biome, width: int, height: int, max_room_size=10, min_room_size=6, max_rooms=25,
#                  dungeon_level=1):
#         self.current_biome = current_biome
#         self.width, self.height = width, height
#         self.min_room_size, self.max_room_size, max_rooms = min_room_size, max_room_size, max_rooms
#         self.tiles = self.initialize_tiles()
#         self.dungeon_level = dungeon_level
#
#     def __iter__(self):
#         for xi in range(self.width):
#             for yi in range(self.height):
#                 yield xi, yi, self.tiles[xi][yi]
#
#     def initialize_tiles(self):
#         tiles = [[Tile(True) for y in range(self.height)] for x in range(self.width)]
#         return tiles
#
#     def place_entities(self, map_width, map_height, entities):
#         room = Rect(0, 0, map_width, map_height)  # Room is the entire dungeon
#         max_monsters = from_dungeon_level([[50, 1], [75, 2], [85, 4], [100, 6]], self.dungeon_level)
#         max_plants = from_dungeon_level([[25, 1], [35, 3], [50, 4], [35, 6]], self.dungeon_level)
#         max_items = from_dungeon_level([[20, 1], [25, 3], [30, 4]], self.dungeon_level)

# # Item dictionary
# item_chances = {
#     'healing_potion': 35,
#     'iron_longsword': from_dungeon_level([[10, 1], [5, 3], [0, 4]], self.dungeon_level),
#     'steel_longsword': from_dungeon_level([[5, 2], [10, 3], [15, 4], [10, 5], [5, 6], [0, 7]],
#                                           self.dungeon_level),
#     'steel_dagger': from_dungeon_level([[5, 1], [10, 3], [5, 4], [0, 5]], self.dungeon_level),
#     'steel_mace': from_dungeon_level([[5, 3], [10, 4], [15, 5], [0, 6]], self.dungeon_level),
#     'influenced_hatchet': from_dungeon_level([[1, 4], [5, 5], [3, 6], [1, 7]], self.dungeon_level),
#     'iron_buckler': from_dungeon_level([[5, 1], [10, 2], [5, 3], [0, 4]], self.dungeon_level),
#     'steel_greatshield': from_dungeon_level([[5, 2], [10, 3], [5, 5], [0, 6]], self.dungeon_level),
#     'iron_helmet': from_dungeon_level([[5, 1], [10, 2], [5, 3], [0, 4]], self.dungeon_level),
#     'steel_bascinet': from_dungeon_level([[1, 2], [5, 3], [10, 4], [5, 5], [0, 6]], self.dungeon_level),
#     'steel_cuirass': from_dungeon_level([[1, 3], [5, 5], [10, 6], [5, 7], [0, 8]], self.dungeon_level),
#     'trickster_gloves': from_dungeon_level([[3, 1], [5, 2], [10, 3], [5, 4], [0, 5]], self.dungeon_level),
#     'steel_platelegs': from_dungeon_level([[3, 3], [5, 4], [10, 5], [5, 6], [1, 7], [0, 8]],
#                                           self.dungeon_level),
#     'wax_coated_ring': from_dungeon_level([[1, 0]], self.dungeon_level),
#     'lightning_scroll': from_dungeon_level([[5, 2], [10, 4], [15, 6]], self.dungeon_level),
#     'fireball_scroll': from_dungeon_level([[5, 4], [10, 6]], self.dungeon_level),
#     'confusion_scroll': from_dungeon_level([[5, 0], [10, 4]], self.dungeon_level)
# }
#
# def returncoordinatesinmap(self, coord_x, coord_y):
#     if coord_x >= 0 and coord_x < self.width:
#         if coord_y >= 0 and coord_y < self.height:
#             return True
#         return False
#
# @staticmethod
# def variable_width(previous_width):
#     """This function returns a Quasi-Markov chain map width value, based upon the width of the previous map."""
#     # Hardcoded min/max
#     minimum_width = 72
#     maximum_width = 72 * 2
#     variable_width = previous_width
#     variable_width += np.normal(0, 5)
#
#     # Ensure the width does not clip through the max/min
#     if variable_width % 2 != 0:
#         variable_width += 1
#     if variable_width < minimum_width:
#         variable_width = minimum_width
#     elif variable_width > maximum_width:
#         variable_width = maximum_width
#     return int(variable_width)
#
# @staticmethod
# def variable_height(previous_height):
#     """This function returns a Quasi-Markov chain map height value, based upon the width of the previous map."""
#     # Hardcoded min/max
#     minimum_height = 35
#     maximum_height = 72 * 2
#     variable_height = previous_height
#     variable_height += np.normal(0, 5)
#
#     # Ensure that the height does not clip through the max/min
#     if variable_height % 2 != 0:
#         variable_height += 1
#     if variable_height < minimum_height:
#         variable_height = minimum_height
#     elif variable_height > maximum_height:
#         variable_height = maximum_height
#     return int(variable_height)
#
# def next_floor(self, player):
#     self.dungeon_level += 1
#     entities = [player]
#
#     # Define randomly the new game map size
#     variable_width = self.variable_width(self.width)
#     variable_height = self.variable_height(self.height)
#     # Write the new sizes
#     self.width = variable_width
#     self.height = variable_height
#
#     # Make the new floor
#     self.tiles = self.initialize_tiles()
#     self.make_map(player, entities)
#     self.place_entities(self.width, self.height, entities)
#
#     # Heal on change of floors?
#     # player.fighter.heal(player.fighter.max_hp // 2)
#     return entities
#
# def make_map(self, player, entities):
#     # Generate each floor's map by calling the appropriate chamber creation function.
#     x = uniform(0, 1)
#     if self.dungeon_level == 1:
#         self.rooms_chamber(self.max_room_size, self.min_room_size, self.max_rooms, player, entities)
#         self.erode(1)
#         return
#     if self.current_biome == 'near_surface':
#         if x >= 0.25:
#             self.rooms_chamber(self.max_room_size, self.min_room_size, self.max_rooms, player, entities)
#             self.erode(1)
#         elif x >= 0.5:
#             self.current_biome = 'ice_caves'
#             self.light_wall = tcod.white
#             self.floor_chars = ['~', ' ', ',', '`', ' ']
#             self.caves_chamber(45, 1)
#             self.erode(1)
#             self.rooms_chamber(16, 8, 75, player, entities)
#             self.erode(1)
#         else:
#             self.current_biome = 'chasms'
#             self.light_wall = tcod.dark_grey
#             self.floor_chars = [' ', '.', ',', '`']
#             self.rooms_chamber(8, 4, 50, player, entities)
#             self.caves_chamber(60, 2)
#             self.erode(1)
#     elif self.current_biome == 'ice_caves':
#         if x >= 0.8:
#             self.current_biome = 'near_surface'
#             self.rooms_chamber(self.max_room_size, self.min_room_size, self.max_rooms, player, entities)
#             self.erode(1)
#         elif 0.8 > x >= 0.2:
#             self.caves_chamber(45, 1)
#             self.erode(1)
#             self.rooms_chamber(16, 8, 75, player, entities)
#             self.erode(1)
#         else:
#             self.current_biome = 'chasms'
#             self.light_ground = tcod.dark_grey
#             self.floor_chars = [' ', '.', ',', '`']
#             self.rooms_chamber(8, 4, 50, player, entities)
#             self.caves_chamber(60, 2)
#             self.erode(1)
#     elif self.current_biome == 'chasms':
#         if x >= 0.75:
#             self.current_biome = 'near_surface'
#             self.rooms_chamber(self.max_room_size, self.min_room_size, self.max_rooms, player, entities)
#             self.erode(1)
#         else:
#             self.rooms_chamber(8, 4, 50, player, entities)
#             self.caves_chamber(60, 2)
#             self.erode(1)


class Tile:
    def __init__(self, blocked, block_sight=None):
        self.blocked = blocked
        self.tunnel = False

        # By default, if a tile is blocked, it also blocks sight
        if block_sight is None:
            block_sight = blocked

        self.block_sight = block_sight
        self.explored = False


class Rect:
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self):
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)
        return center_x, center_y

    def intersect(self, other):
        # returns true if this rectangle intersects with another one
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)
