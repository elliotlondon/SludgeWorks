from __future__ import annotations

import copy
import json
import logging
import random
from typing import Tuple, Iterator, List, TYPE_CHECKING

import numpy as np

import config.colour
import maps.tiles
import parts.entity
from config.exceptions import MapGenError, FatalMapGenError
from data.item_factory import create_item_from_json
from data.monster_factory import create_monster_from_json
from data.object_factory import create_static_object_from_json
from maps.game_map import SimpleGameMap

if TYPE_CHECKING:
    from core.engine import Engine

import tcod

max_items_by_floor = [
    (1, 20),
    (2, 25),
    (4, 30),
    (6, 35)
]

max_plants_by_floor = [
    (1, 35),
    (3, 45),
    (4, 65),
    (6, 35)
]

max_monsters_by_floor = [
    (1, 30),
    (3, 40),
    (4, 50),
]


# item_chances = {
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


def get_max_value_for_floor(max_value_by_floor: List[Tuple[int, int]], floor: int) -> int:
    current_value = 0

    for floor_minimum, value in max_value_by_floor:
        if floor_minimum > floor:
            break
        else:
            current_value = value

    return current_value


def get_monsters_at_random(engine: Engine, path: str, number_of_entities: int) -> [List[str], List[str]]:
    # Load drop table for current floor
    f = open(path)
    spawn_table = json.load(f)[0]

    # Current final floor is FLOOR 8. Keep spawning unchanged for floors beyond this.
    if engine.game_world.current_floor > 8:
        floor_value = 8
    else:
        floor_value = engine.game_world.current_floor
    spawn_table = spawn_table[f"{floor_value}"]

    entity_types = []
    entity_weighted_chances = {}
    for key, value in spawn_table.items():
        entity_types.append(value[0])
        entity_weighted_chances[key] = value[1]

    entities = list(entity_weighted_chances.keys())
    entity_weighted_chance_values = list(entity_weighted_chances.values())

    # Generate a random selection across the item and item type arrays simultaneously
    idx = random.choices(np.arange(len(entities)),
                         weights=entity_weighted_chance_values, k=number_of_entities)
    # Now construct the lists of item and type
    chosen_monsters = []
    chosen_types = []
    for i in idx:
        chosen_monsters.append(entities[i])
        chosen_types.append(entity_types[i])

    return chosen_monsters, chosen_types


def get_items_at_random(engine: Engine, path: str, number_of_entities: int) -> [List[str], List[str]]:
    # Load drop table for current floor
    f = open(path)
    spawn_table = json.load(f)[0]

    # Current final floor is FLOOR 8. Keep spawning unchanged for floors beyond this.
    if engine.game_world.current_floor > 8:
        floor_value = 8
    else:
        floor_value = engine.game_world.current_floor
    spawn_table = spawn_table[f"{floor_value}"]

    entity_types = []
    entity_weighted_chances = {}
    for key, value in spawn_table.items():
        entity_types.append(value[0])
        entity_weighted_chances[key] = value[1]

    entities = list(entity_weighted_chances.keys())
    entity_weighted_chance_values = list(entity_weighted_chances.values())

    # Generate a random selection across the item and item type arrays simultaneously
    idx = random.choices(np.arange(len(entities)),
                         weights=entity_weighted_chance_values, k=number_of_entities)
    # Now construct the lists of item and type
    chosen_items = []
    chosen_types = []
    for i in idx:
        chosen_items.append(entities[i])
        chosen_types.append(entity_types[i])

    return chosen_items, chosen_types


def get_static_objects_at_random(engine: Engine, path: str, floor_number: int) -> List[parts.entity.StaticObject]:
    # Load drop table for current floor
    f = open(path)
    spawn_table = json.load(f)[0]
    return spawn_table


def generate_dungeon(max_rooms: int, room_min_size: int, room_max_size: int, map_width: int, map_height: int,
                     engine: Engine) -> SimpleGameMap:
    """
    Generate a new dungeon map.
    """
    player = engine.player
    cave_smoothing = engine.game_world.cave_smoothing
    cave_p = engine.game_world.cave_p

    tries = 1
    while tries <= 10:
        # Initialize map
        dungeon = SimpleGameMap(engine, map_width, map_height, entities=[player])
        if engine.game_world.caves:
            dungeon = add_caves(dungeon, smoothing=cave_smoothing, p=cave_p)
        if engine.game_world.rooms:
            dungeon = add_rooms(dungeon, max_rooms, room_min_size, room_max_size)
        if engine.game_world.erode:
            dungeon = erode(dungeon, 1)

        # Add rocks/water
        dungeon = add_rubble(dungeon, events=7)
        dungeon = add_hazards(dungeon, floods=5, holes=3)
        dungeon = add_features(dungeon)

        # Place player
        engine.player.place(*dungeon.get_random_walkable_nontunnel_tile(), dungeon)

        # Populate dungeon
        place_flora(dungeon, engine, areas=3)
        place_fauna(dungeon, engine)
        place_npcs(dungeon, engine)
        place_items(dungeon, engine)
        place_static_objects(dungeon, engine)

        # Finally, add stairs
        dungeon = add_stairs(dungeon)
        if isinstance(dungeon, SimpleGameMap):
            # Mapgen successful, use this floor
            dungeon.accessible = dungeon.calc_accessible()
            return dungeon
        elif isinstance(dungeon, MapGenError):
            # Mapgen unsuccessful, try again until max tries are reached
            if logging.DEBUG >= logging.root.level:
                print(f"DEBUG: Floor generation failed. Attempt: {tries}.", config.colour.debug)
            tries += 1
            continue

    # Something went wrong with mapgen, sysexit
    raise FatalMapGenError(f"Dungeon generation failed! Reason: floor attempts exceeded.")


def place_flora(dungeon: SimpleGameMap, engine: Engine, areas: int) -> None:
    """
    Fill the current floor with plants, both hostile and decorative.
    A cellular automata method is used to generate an area that plants may spawn in, which is then placed onto the
    floor and populated.
    """
    current_floor = engine.game_world.current_floor
    max_plants = get_max_value_for_floor(max_plants_by_floor, current_floor)
    number_of_plants = random.randint(int(max_plants / 2), max_plants)

    plants, plant_types = get_monsters_at_random(engine, 'data/monsters/spawn_table_plants.json', number_of_plants)

    # Generate cellular automata areas
    area_size = random.randint(5, 10)
    p = 40
    verdant_array = []
    for area in range(areas):
        # Get a random walkable tile within the dungeon
        walkable = np.nonzero(dungeon.tiles['walkable'])
        index = random.randint(0, len(walkable[0]) - 1)
        start_x = walkable[0][index]
        start_y = walkable[1][index]
        x_arr = np.arange(start_x - int(area_size / 2), (start_x + int(area_size / 2)))
        y_arr = np.arange(start_y - int(area_size / 2), (start_y + int(area_size / 2)))

        # Make sure that values are within the game map
        x_arr = x_arr[np.where(np.logical_and(x_arr > 0, x_arr < dungeon.width))]
        y_arr = y_arr[np.where(np.logical_and(y_arr > 0, y_arr < dungeon.height))]

        # Randomly populate with greenery
        for x in x_arr:
            for y in y_arr:
                if random.randint(0, 100) > p:
                    # Select a few random locations to become verdant
                    if not dungeon.tiles[x, y]['name'] == 'hole' and not dungeon.tiles[x, y]['name'] == 'water':
                        dungeon.tiles[x, y] = random.choice(maps.tiles.verdant_tiles_1)
                        verdant_array.append([x, y])

        for x in range(dungeon.width):
            for y in range(dungeon.height):
                verdant = 0
                for nx, ny in dungeon.find_neighbours(x, y):
                    if 'verdant' in dungeon.tiles[nx, ny]['name']:
                        verdant += 1
                if verdant >= 5:
                    dungeon.tiles[x, y] = random.choice(maps.tiles.verdant_tiles_1)

    for i in range(len(plants)):
        # Random verdant tile
        x, y = random.choice(verdant_array)

        # Find Euclidean distance between monster spawn and player
        player_x = int(dungeon.engine.player.x)
        player_y = int(dungeon.engine.player.y)
        spawn_dist = np.sqrt((x - player_x) ** 2 + (y - player_y) ** 2)

        # Enemies should not spawn in player pov!
        if spawn_dist <= 10:
            continue

        # Spawn in free, non-blocked location
        if not any(entity.x == x and entity.y == y for entity in dungeon.entities) and dungeon.tiles[x, y]['walkable']:
            plant = copy.deepcopy(create_monster_from_json(f"data/monsters/{plant_types[i]}.json", plants[i]))
            plant.spawn(dungeon, x, y)


def place_fauna(dungeon: SimpleGameMap, engine: Engine) -> None:
    current_floor = engine.game_world.current_floor
    max_monsters = get_max_value_for_floor(max_monsters_by_floor, current_floor)
    number_of_monsters = random.randint(int(max_monsters / 2), max_monsters)

    # Spawn monsters
    monsters, monster_types = get_monsters_at_random(engine, 'data/monsters/spawn_table_monsters.json',
                                                     number_of_monsters)
    for i in range(len(monsters)):
        # Get the indices of tiles which are walkable
        x, y = dungeon.get_random_walkable_tile()

        # Find Euclidean distance between monster spawn and player
        player_x = int(dungeon.engine.player.x)
        player_y = int(dungeon.engine.player.y)
        spawn_dist = np.sqrt((x - player_x) ** 2 + (y - player_y) ** 2)

        # Enemies should not spawn in player pov!
        if spawn_dist <= 10:
            continue

        # Spawn in free, non-blocked location
        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            monster = copy.deepcopy(create_monster_from_json(f"data/monsters/{monster_types[i]}.json", monsters[i]))
            if monster.name == "Risen Sacrifice":
                monster.fighter.hp = random.randint(4, 8)
            monster.spawn(dungeon, x, y)


def place_npcs(dungeon: SimpleGameMap, engine: Engine) -> None:
    # Spawn NPCs depending upon floor conditions
    if engine.game_world.current_floor == 1:
        x, y = dungeon.get_random_walkable_nontunnel_tile()
        npc = copy.deepcopy(create_monster_from_json(f"data/monsters/npcs.json", "gilbert"))
        npc.spawn(dungeon, x, y)


def place_items(dungeon: SimpleGameMap, engine: Engine) -> None:
    current_floor = engine.game_world.current_floor
    max_items = get_max_value_for_floor(max_items_by_floor, current_floor)
    number_of_items = random.randint(int(max_items / 2), max_items)

    items, item_types = get_items_at_random(engine, 'data/items/spawn_table_items.json', number_of_items)

    for i in range(len(items)):
        # Get random walkable tile
        x, y = dungeon.get_random_walkable_tile()

        # Spawn in free, non-blocked location
        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            item = copy.deepcopy(create_item_from_json(f"data/items/{item_types[i]}.json", items[i]))
            item.spawn(dungeon, x, y)


def place_static_objects(dungeon: SimpleGameMap, engine: Engine) -> None:
    current_floor = engine.game_world.current_floor
    static_objects = get_static_objects_at_random(engine, 'data/static_objects/spawn_table_objects.json', current_floor)

    # For now simply spawn one sludge fountain per floor
    x, y = dungeon.get_random_unoccupied_nonfov_tile()

    static_object = copy.deepcopy(
        create_static_object_from_json(f"data/static_objects/core_objects.json", 'sludge_fountain'))
    static_object.spawn(dungeon, x, y)


def tunnel_between(start: Tuple[int, int], end: Tuple[int, int]) -> Iterator[Tuple[int, int]]:
    """
    Return an L-shaped tunnel between these two points.
    """
    x1, y1 = start
    x2, y2 = end
    if random.random() < 0.5:  # 50% chance.
        # Move horizontally, then vertically.
        corner_x, corner_y = x2, y1
    else:
        # Move vertically, then horizontally.
        corner_x, corner_y = x1, y2

    # Generate the coordinates for this tunnel.
    for x, y in tcod.los.bresenham((x1, y1), (corner_x, corner_y)).tolist():
        yield x, y
    for x, y in tcod.los.bresenham((corner_x, corner_y), (x2, y2)).tolist():
        yield x, y


def add_rooms(dungeon: SimpleGameMap, max_rooms: int,
              room_min_size: int, room_max_size: int) -> SimpleGameMap:
    rooms: List[RectangularRoom] = []

    for r in range(max_rooms):
        room_width = random.randint(room_min_size, room_max_size)
        room_height = random.randint(room_min_size, room_max_size)

        x = random.randint(0, dungeon.width - room_width - 1)
        y = random.randint(0, dungeon.height - room_height - 1)

        # "RectangularRoom" class makes rectangles easier to work with
        new_room = RectangularRoom(x, y, room_width, room_height)

        # Run through the other rooms and see if they intersect with this one.
        if any(new_room.intersects(other_room) for other_room in rooms):
            continue  # This room intersects, so go to the next attempt.
        # If there are no intersections then the room is valid.

        # Dig out this rooms inner area.
        for tile_i in range(new_room.x1, new_room.x2):
            for tile_j in range(new_room.y1, new_room.y2):
                dungeon.tiles[tile_i, tile_j] = random.choice(maps.tiles.floor_tiles_1)

        # if len(rooms) == 0:
        # The first room, where the player starts.
        # engine.player.place(*new_room.center, dungeon)
        # else:  # All rooms after the first.

        if not len(rooms) == 0:
            # Dig out a tunnel between this room and the previous one.
            for x, y in tunnel_between(rooms[-1].center, new_room.center):
                dungeon.tunnel[x, y] = True
                dungeon.tiles[x, y] = random.choice(maps.tiles.floor_tiles_1)

        # Provide room/corridor indexing to gamemap for later use (exclude player room)
        dungeon.rooms.append(new_room.tile_indices)

        # Finally, append the new room to the list.
        rooms.append(new_room)

    return dungeon


def add_caves(dungeon: SimpleGameMap, smoothing: int, p: int) -> SimpleGameMap:
    """
    A chamber filled with random-sized, sprawling cave rooms, generated using an automata technique.
    p is the probability of a cave sector being created. Smoothing values about 4 do nothing, below 4 cause
    more rugged caves.
    """
    map_width = dungeon.width
    map_height = dungeon.height
    for x in range(map_width):
        for y in range(map_height):
            if random.randint(0, 100) > p:
                # Select a few random locations to be turned into a floor
                dungeon.tiles[x, y] = random.choice(maps.tiles.floor_tiles_1)

    for i in range(smoothing):
        for x in range(map_width):
            for y in range(map_height):
                if x == 0 or x == map_width - 1 or y == 0 or y == map_height - 1:
                    dungeon.tiles[x, y] = maps.tiles.wall
                touching_empty_space = 0
                for nx, ny in dungeon.find_neighbours(x, y):
                    if not dungeon.tiles[nx, ny]['walkable']:
                        touching_empty_space += 1
                if touching_empty_space >= 5 and not dungeon.tunnel[x, y]:
                    dungeon.tiles[x, y] = maps.tiles.wall
                elif touching_empty_space <= 2:
                    dungeon.tiles[x, y] = random.choice(maps.tiles.floor_tiles_1)
                if x == 0 or x == map_width - 1 or y == 0 or y == map_height - 1:
                    dungeon.tiles[x, y] = maps.tiles.wall

    return dungeon


def add_rubble(dungeon: SimpleGameMap, events: int) -> SimpleGameMap:
    """
    Add tiles of impassable rubble which may be removed via explosions, digging, etc.
    """

    tries = 0
    while tries < events:
        x = random.choice(range(dungeon.width))
        y = random.choice(range(dungeon.height))
        if x == dungeon.engine.player.x and y == dungeon.engine.player.y:
            continue
        if dungeon.tiles[x, y]['walkable'] and not dungeon.tunnel[x, y]:
            # Choose n random tiles within 5x5 area
            pile_area = random.randint(3, 5)
            pile_size = random.randint((int(pile_area ** 2 / 2)), pile_area ** 2)
            x_arr = np.arange(x - 2, x + 2)
            y_arr = np.arange(y - 2, y + 2)

            for placement in range(pile_size):
                try:
                    dungeon.tiles[random.choice(x_arr), random.choice(y_arr)] = maps.tiles.rubble
                except IndexError:
                    continue

            tries += 1

    return dungeon


def add_stairs(dungeon: SimpleGameMap):
    """
    Place stairs in random tile in random room that the player can access.
    """

    attempts = 0
    # Attempt to place stairs in accessible location n times before throwing an error.
    while attempts < 25:
        # Get random walkable tile
        stairs_location = dungeon.get_random_walkable_nontunnel_tile()

        # Check if there exists a path to the stairs
        cost = np.array(dungeon.tiles["walkable"], dtype=np.int8)

        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)

        pathfinder.add_root((dungeon.engine.player.x, dungeon.engine.player.y))  # Start position.
        path: List[List[int]] = pathfinder.path_to(stairs_location)[1:].tolist()

        if len(path) > 20:
            if logging.DEBUG >= logging.root.level:
                dungeon.engine.message_log.add_message(f"DEBUG: Stairs placed at ({stairs_location}).",
                                                       config.colour.debug)
            dungeon.tiles[stairs_location] = maps.tiles.down_stairs
            dungeon.downstairs_location = stairs_location
            return dungeon
        elif 0 > len(path) <= 20:
            attempts += 1
            if logging.DEBUG >= logging.root.level:
                dungeon.engine.message_log.add_message(f"DEBUG: Stair placement failed. Tile too close. "
                                                       f"(Attempt {attempts}).", config.colour.debug)
            continue
        else:
            attempts += 1
            if logging.DEBUG >= logging.root.level:
                dungeon.engine.message_log.add_message(f"DEBUG: Stair placement failed. Invalid tile. "
                                                       f"(Attempt {attempts}).", config.colour.debug)
            continue

    return MapGenError("MapGen aborted. Reason: Could not place stairs (Maximum attempts exceeded).",
                       config.colour.debug)


def erode(dungeon: SimpleGameMap, smoothing: int) -> SimpleGameMap:
    """
    A tool for helping to increase the erosion of an already-generated map.
    """
    for i in range(smoothing):
        for x in range(dungeon.width):
            for y in range(dungeon.height):
                touching_empty_space = 0
                for nx, ny in dungeon.find_neighbours(x, y):
                    if not dungeon.tiles[nx][ny]['walkable'] and not dungeon.tiles[nx][ny]['transparent']:
                        touching_empty_space += 1
                if touching_empty_space >= 5 and not dungeon.tunnel[x, y]:
                    dungeon.tiles[x][y] = maps.tiles.wall
                elif touching_empty_space <= 3:
                    dungeon.tiles[x][y] = random.choice(maps.tiles.floor_tiles_1)
                if x == 0 or x == dungeon.width - 1 or y == 0 or y == dungeon.height - 1:
                    dungeon.tiles[x][y] = maps.tiles.wall

    return dungeon


def spill_liquid(dungeon: SimpleGameMap, smoothing: int) -> SimpleGameMap:
    """
    Erosion tool for liquids to make bodies of liquid more uniform in their distribution.
    """
    for i in range(smoothing):
        for x in range(dungeon.width):
            for y in range(dungeon.height):
                touching_liquid = 0
                for nx, ny in dungeon.find_neighbours(x, y):
                    if dungeon.tiles[nx, ny]['name'] == 'water':
                        touching_liquid += 1
                if touching_liquid >= 4 and not dungeon.tunnel[x, y]:
                    dungeon.tiles[x][y] = maps.tiles.water

    return dungeon


def add_hazards(dungeon: SimpleGameMap, floods: int, holes: int) -> SimpleGameMap:
    """
    Add hazards such as liquids to the map
    """

    # Add water to some rooms
    i = 0
    while i <= floods:
        # Random walkable tile
        start_x, start_y = dungeon.get_random_walkable_nontunnel_tile()

        # Create first water tile
        dungeon.tiles[start_x, start_y] = maps.tiles.water

        # Decide spill size
        spill_size = random.randint(4, 16)
        j = 0
        new_x = start_x
        new_y = start_y
        while j <= spill_size:
            # Spill to a tile next to initial tile
            new_x += random.randint(-1, 1)
            new_y += random.randint(-1, 1)
            try:
                dungeon.tiles[new_x, new_y] = maps.tiles.water
            except IndexError:
                pass
            j += 1
        i += 1

    # Make bodies of water more uniform
    dungeon = spill_liquid(dungeon, smoothing=1)

    # Add holes across the dungeon
    tries = 0
    while tries < holes:
        x = random.choice(range(dungeon.width))
        y = random.choice(range(dungeon.height))

        if dungeon.tiles[x, y]['walkable'] and not dungeon.tunnel[x, y]:
            # Choose n random tiles within 5x5 area
            hole_area = random.randint(3, 5)
            hole_size = random.randint((int(hole_area ** 2 / 4)), hole_area ** 2)
            x_arr = np.arange(x - 2, x + 2)
            y_arr = np.arange(y - 2, y + 2)

            for placement in range(hole_size):
                try:
                    hole_x = random.choice(x_arr)
                    hole_y = random.choice(y_arr)
                    dungeon.tiles[hole_x, hole_y] = maps.tiles.hole
                except IndexError:
                    continue

            tries += 1

    return dungeon


def add_features(dungeon: SimpleGameMap) -> SimpleGameMap:
    """
    Adds cosmetic features to the map to make it feel more alive
    """

    # If water touches a hole, turn it into a waterfall
    for x in range(dungeon.width):
        for y in range(dungeon.height):
            for nx, ny in dungeon.find_neighbours(x, y):
                if dungeon.tiles[x, y]['name'] == 'water' and dungeon.tiles[nx, ny]['name'] == 'hole':
                    dungeon.tiles[x, y] = maps.tiles.waterfall

    return dungeon


class RectangularRoom:
    def __init__(self, x: int, y: int, width: int, height: int):
        self.x1 = x
        self.y1 = y
        self.x2 = x + width
        self.y2 = y + height

    @property
    def center(self) -> Tuple[int, int]:
        """
        Provide coordinates of the center of the room
        """
        center_x = int((self.x1 + self.x2) / 2)
        center_y = int((self.y1 + self.y2) / 2)

        return center_x, center_y

    @property
    def inner(self) -> Tuple[slice, slice]:
        """
        Return the inner area of this room as a 2D array index.
        """
        return slice(self.x1 + 1, self.x2), slice(self.y1 + 1, self.y2)

    @property
    def tile_indices(self) -> List[np.ndarray, np.ndarray]:
        """
        Return the inner area of this room as a 2D array index.
        """
        return [np.arange(self.x1 + 1, self.x2), np.arange(self.y1 + 1, self.y2)]

    def intersects(self, other: RectangularRoom) -> bool:
        """
        Return True if this room overlaps with another RectangularRoom.
        """
        return (
                self.x1 <= other.x2
                and self.x2 >= other.x1
                and self.y1 <= other.y2
                and self.y2 >= other.y1
        )
