from __future__ import annotations

import copy
import json
import logging
import random
from typing import Tuple, Iterator, List, TYPE_CHECKING, Optional

import numpy as np

import config.colour
import maps.tiles
import parts.entity
from config.exceptions import MapGenError, FatalMapGenError
from maps.game_map import GameMap
from maps.maploader import MapLoader
from utils.math_utils import find_neighbours, Graph
from utils.random_utils import rotate_array

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


def get_monsters_at_random(engine: Engine, path: str, number_of_entities: int) -> List[str]:
    # Load drop table for current floor
    f = open(path)
    spawn_table = json.load(f)[0]

    # Current final floor is FLOOR 8. Keep spawning unchanged for floors beyond this.
    if engine.game_world.current_floor > 8:
        floor_value = 8
    else:
        floor_value = engine.game_world.current_floor
    spawn_table = spawn_table[f"{floor_value}"]

    entity_weighted_chances = {}
    for key, value in spawn_table.items():
        entity_weighted_chances[key] = value

    entities = list(entity_weighted_chances.keys())
    entity_weighted_chance_values = list(entity_weighted_chances.values())

    # Generate a random selection across the item and item type arrays simultaneously
    idx = random.choices(np.arange(len(entities)),
                         weights=entity_weighted_chance_values, k=number_of_entities)
    # Now construct the lists of item and type
    chosen_monsters = []
    for i in idx:
        chosen_monsters.append(entities[i])

    return chosen_monsters


def get_items_at_random(engine: Engine, path: str, number_of_entities: int) -> List[str]:
    # Load drop table for current floor
    f = open(path)
    spawn_table = json.load(f)[0]

    # Current final floor is FLOOR 8. Keep spawning unchanged for floors beyond this.
    if engine.game_world.current_floor > 8:
        floor_value = 8
    else:
        floor_value = engine.game_world.current_floor
    spawn_table = spawn_table[f"{floor_value}"]

    entity_weighted_chances = {}
    for key, value in spawn_table.items():
        entity_weighted_chances[key] = value

    entities = list(entity_weighted_chances.keys())
    entity_weighted_chance_values = list(entity_weighted_chances.values())

    # Generate a random selection across the item and item type arrays simultaneously
    idx = random.choices(np.arange(len(entities)),
                         weights=entity_weighted_chance_values, k=number_of_entities)
    # Now construct the lists of item and type
    chosen_items = []
    for i in idx:
        chosen_items.append(entities[i])

    return chosen_items


def get_static_objects_at_random(engine: Engine, path: str, floor_number: int) -> List[parts.entity.StaticObject]:
    # Load drop table for current floor
    f = open(path)
    spawn_table = json.load(f)[0]
    return spawn_table


def generate_dungeon(engine: Engine,
                     from_file: str = None,
                     max_rooms: int = 25, room_min_size: int = 6, room_max_size: int = 10,
                     map_width: int = 100, map_height: int = 60
                     ) -> GameMap:
    """
    Generate a new dungeon map. Either a filename can be supplied to be constructed with the MapLoader object, or
    the parameters/flags can be given manually to generate a random map.
    """
    player = engine.player

    if from_file:
        # Load the map layout from the str supplied
        dungeon = MapLoader()
        dungeon.load_map_from_file(from_file)
        dungeon = dungeon.convert_mapfile(engine)
        return dungeon
    else:
        # Generate the map from the given flags
        cave_smoothing = engine.game_world.cave_smoothing
        cave_p = engine.game_world.cave_p
        tries = 1
        while tries <= 10:
            # Initialize map
            dungeon = GameMap(engine, map_width, map_height, entities=[player])
            # if engine.game_world.caves:
            #     dungeon = add_caves(dungeon, smoothing=cave_smoothing, p=cave_p)
            # if engine.game_world.rooms:
            #     dungeon = add_rooms(dungeon, max_rooms, room_min_size, room_max_size)
            # if engine.game_world.erode:
            #     dungeon = erode(dungeon, 1)

            # First create the underlying caves.
            dungeon = maps.procgen.add_caves(dungeon, smoothing=1, p=42)
            random_x, random_y = dungeon.get_random_walkable_nontunnel_tile()
            graph = Graph(map_width, map_height, dungeon.tiles['walkable'])
            dungeon.accessible = graph.find_connected_area(random_x, random_y)

            # If too few accessible tiles, retry
            if len(dungeon.accessible.nonzero()[0]) < 80 * 43 / 4:
                if logging.DEBUG >= logging.root.level:
                    engine.message_log.add_message(
                        f"Too few accessible tiles ({len(dungeon.accessible.nonzero()[0])}).",
                        config.colour.debug)
                tries += 1
                continue
            dungeon.prune_inaccessible(maps.tiles.muddy_wall)

            # Randomly add some rooms to the dungeon.
            extra_rooms = 4
            maps.procgen.place_random_rooms(dungeon, extra_rooms)
            dungeon.prune_inaccessible(maps.tiles.muddy_wall)

            # Place player
            engine.player.place(*dungeon.get_random_walkable_nontunnel_tile(), dungeon)

            # Add some random rooms in accessible locations
            for room in range(extra_rooms):
                if isinstance(maps.procgen.place_congruous_room(dungeon, engine), config.exceptions.MapGenError):
                    if logging.DEBUG >= logging.root.level:
                        engine.message_log.add_message("Could not add new room...", config.colour.debug)

            # Add rocks/water
            dungeon = add_rubble(dungeon, events=4)
            dungeon = add_hazards(dungeon, engine, floods=4, holes=3)
            dungeon = add_features(dungeon)

            # Populate dungeon
            place_flora(dungeon, engine, areas=5)
            place_fauna(dungeon, engine)
            place_npcs(dungeon, engine)
            place_items(dungeon, engine)
            place_static_objects(dungeon, engine)

            # Finally, add stairs
            dungeon = add_stairs(dungeon)
            if isinstance(dungeon, GameMap):
                # Mapgen successful, use this floor
                dungeon.accessible = dungeon.calc_accessible()

                # As a failsafe, make all of the outer border a wall tile
                for x in range(dungeon.width):
                    for y in range(dungeon.height):
                        if x == 0 or x == map_width - 1 or y == 0 or y == map_height - 1:
                            dungeon.tiles[x, y] = maps.tiles.muddy_wall
                return dungeon
            elif isinstance(dungeon, MapGenError):
                # Mapgen unsuccessful, try again until max tries are reached
                if logging.DEBUG >= logging.root.level:
                    print(f"DEBUG: Floor generation failed. Attempt: {tries}.", config.colour.debug)
                tries += 1
                continue

    # Something went wrong with mapgen, sysexit
    raise FatalMapGenError(f"Dungeon generation failed! Reason: floor attempts exceeded.")


def place_flora(dungeon: GameMap, engine: Engine, areas: int) -> None:
    """
    Fill the current floor with plants, both hostile and decorative.
    A cellular automata method is used to generate an area that plants may spawn in, which is then placed onto the
    floor and populated.
    """
    current_floor = engine.game_world.current_floor
    max_plants = get_max_value_for_floor(max_plants_by_floor, current_floor)
    # number_of_plants = random.randint(int(max_plants / 2), max_plants)
    number_of_plants = max_plants * 2

    plants = get_monsters_at_random(engine, 'data/monsters/spawn_table_plants.json', number_of_plants)

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
        x_arr = x_arr[np.where(np.logical_and(x_arr > 1, x_arr < dungeon.width - 1))]
        y_arr = y_arr[np.where(np.logical_and(y_arr > 1, y_arr < dungeon.height - 1))]

        # Randomly populate with greenery
        for x in x_arr:
            for y in y_arr:
                if random.randint(0, 100) > p:
                    # Select a few random locations to become verdant
                    if not 'hole' in dungeon.tiles[x, y]['name'] and not 'water' in dungeon.tiles[x, y]['name'] \
                            and not dungeon.room_zone[x, y]:
                        dungeon.tiles[x, y] = random.choice(maps.tiles.verdant_tiles_1)
                        verdant_array.append([x, y])

        for x in range(1, dungeon.width - 1):
            for y in range(1, dungeon.height - 1):
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
            plant = dungeon.engine.clone(plants[i])
            plant.spawn(dungeon, x, y)


def place_fauna(dungeon: GameMap, engine: Engine) -> None:
    current_floor = engine.game_world.current_floor
    max_monsters = get_max_value_for_floor(max_monsters_by_floor, current_floor)
    number_of_monsters = random.randint(int(max_monsters / 2), max_monsters)

    # Spawn monsters
    monsters = get_monsters_at_random(engine, 'data/monsters/spawn_table_monsters.json', number_of_monsters)
    for i in range(len(monsters)):
        # Get the indices of tiles which are walkable
        x, y = dungeon.get_random_walkable_nonfov_tile()

        # Find Euclidean distance between monster spawn and player
        player_x = int(dungeon.engine.player.x)
        player_y = int(dungeon.engine.player.y)
        spawn_dist = np.sqrt((x - player_x) ** 2 + (y - player_y) ** 2)

        # Enemies should not spawn in player pov!
        if spawn_dist <= 10:
            continue

        # Spawn in free, non-blocked location
        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            monster = dungeon.engine.clone(monsters[i])
            # Randomised effects go here
            if monster.name == "Risen Sacrifice":
                monster.fighter.hp = random.randint(4, 8)
            monster.spawn(dungeon, x, y)

    # Debug stuff
    if current_floor == 1:
        x, y = dungeon.get_random_walkable_nonfov_tile()
        moire_beast = dungeon.engine.clone('moire_beast')
        moire_beast.spawn(dungeon, x, y)
        x, y = dungeon.get_random_walkable_nonfov_tile()
        moire_beast = dungeon.engine.clone('moire_beast')
        moire_beast.spawn(dungeon, x, y)


def place_npcs(dungeon: GameMap, engine: Engine) -> None:
    # Spawn NPCs depending upon floor conditions
    counter = 0
    if engine.game_world.current_floor == 1:
        while counter < 100:
            counter += 1
            x, y = dungeon.get_random_walkable_nontunnel_tile()
            spawn_dist = np.sqrt((x - dungeon.engine.player.x) ** 2 + (y - dungeon.engine.player.y) ** 2)
            if spawn_dist <= 10:
                continue
            else:
                npc = dungeon.engine.clone('gilbert')
                npc.spawn(dungeon, x, y)
                break
        if counter > 100:
            raise MapGenError(f"NPC{npc.name} could not be placed: maximum attempts exceeded.")


def place_items(dungeon: GameMap, engine: Engine) -> None:
    current_floor = engine.game_world.current_floor
    max_items = get_max_value_for_floor(max_items_by_floor, current_floor)
    number_of_items = random.randint(int(max_items / 2), max_items)

    items = get_items_at_random(engine, 'data/items/spawn_table_items.json', number_of_items)

    for i in range(len(items)):
        # Get random walkable tile
        x, y = dungeon.get_random_walkable_tile()

        # Spawn in free, non-blocked location
        if not any(entity.x == x and entity.y == y for entity in dungeon.entities):
            item = dungeon.engine.clone(items[i])
            item.spawn(dungeon, x, y)


def place_static_objects(dungeon: GameMap, engine: Engine) -> None:
    current_floor = engine.game_world.current_floor
    static_objects = get_static_objects_at_random(engine, 'data/static_objects/spawn_table_objects.json', current_floor)

    # For now simply spawn one sludge fountain per floor
    x, y = dungeon.get_random_walkable_nonfov_tile()

    static_object = dungeon.engine.clone('sludge_fountain')
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


def add_rooms(dungeon: GameMap, max_rooms: int,
              room_min_size: int, room_max_size: int) -> GameMap:
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


def add_caves(dungeon: GameMap, smoothing: int, p: int) -> GameMap:
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
                    dungeon.tiles[x, y] = maps.tiles.muddy_wall
                touching_empty_space = 0
                for nx, ny in dungeon.find_neighbours(x, y):
                    if not dungeon.tiles[nx, ny]['walkable']:
                        touching_empty_space += 1
                if touching_empty_space >= 5 and not dungeon.tunnel[x, y]:
                    dungeon.tiles[x, y] = maps.tiles.muddy_wall
                    dungeon.remove_entity_at_location('Door', x, y)
                elif touching_empty_space <= 2:
                    dungeon.tiles[x, y] = random.choice(maps.tiles.floor_tiles_1)
                if x == 0 or x == map_width - 1 or y == 0 or y == map_height - 1:
                    dungeon.tiles[x, y] = maps.tiles.muddy_wall
                    dungeon.remove_entity_at_location('Door', x, y)

    return dungeon


def add_rubble(dungeon: GameMap, events: int) -> GameMap:
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
                    x = random.choice(x_arr)
                    y = random.choice(y_arr)
                    dungeon.tiles[x, y] = maps.tiles.rubble
                    dungeon.tiles[x, y]['walkable'] = False
                    dungeon.remove_entity_at_location('Door', x, y)
                except IndexError:
                    continue

            tries += 1

    return dungeon


def add_stairs(dungeon: GameMap):
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


def erode(dungeon: GameMap, smoothing: int) -> GameMap:
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
                    dungeon.tiles[x][y] = maps.tiles.muddy_wall
                    dungeon.remove_entity_at_location('Door', x, y)
                elif touching_empty_space <= 3:
                    dungeon.tiles[x][y] = random.choice(maps.tiles.floor_tiles_1)
                if x == 0 or x == dungeon.width - 1 or y == 0 or y == dungeon.height - 1:
                    dungeon.tiles[x][y] = maps.tiles.muddy_wall
                    dungeon.remove_entity_at_location('Door', x, y)

    return dungeon


def spill_liquid(dungeon: GameMap, smoothing: int) -> GameMap:
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
                    dungeon.remove_entity_at_location('Door', x, y)

    return dungeon


def add_hazards(dungeon: GameMap, engine: Engine, floods: int, holes: int) -> GameMap:
    """
    Add hazards such as liquids to the map
    """

    # Add water to some rooms
    i = 0
    while i <= floods:
        # Random walkable tile
        start_x, start_y = dungeon.get_random_walkable_nontunnel_tile()
        if start_x == engine.player.x and start_y == engine.player.y:
            continue

        # Create first water tile
        dungeon.tiles[start_x, start_y] = maps.tiles.water
        dungeon.remove_entity_at_location('Door', start_x, start_y)

        # Decide spill size
        spill_size = random.randint(4, 16)
        j = 0
        new_x = start_x
        new_y = start_y
        while j <= spill_size:
            # Spill to a tile next to initial tile
            new_x += random.randint(-1, 1)
            new_y += random.randint(-1, 1)
            if new_x == engine.player.x and new_y == engine.player.y:
                continue
            try:
                dungeon.tiles[new_x, new_y] = maps.tiles.water
                dungeon.remove_entity_at_location('Door', new_x, new_y)
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
                    if hole_x == engine.player.x and hole_y == engine.player.y:
                        continue
                    dungeon.tiles[hole_x, hole_y] = maps.tiles.hole
                    dungeon.remove_entity_at_location('Door', hole_x, hole_y)
                except IndexError:
                    continue

            tries += 1

    return dungeon


def add_features(dungeon: GameMap) -> GameMap:
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


def place_random_rooms(dungeon: GameMap, rooms: int) -> Optional[Exception]:
    """Place some rooms in random locations for the current map, without any regard for whether there is already
    something generated at the placement site."""

    for room in range(rooms):
        # Choose location in dungeon to add random rooms
        room_width = random.randint(5, 9)
        room_height = random.randint(5, 9)
        room_xy = (random.randint(0, dungeon.width - room_width - 1),
                   random.randint(0, dungeon.height - room_height - 1))

        # Check if new cluster overlaps existing cluster
        for x in range(room_xy[0], room_width):
            for y in range(room_xy[1], room_height):
                if dungeon.room_zone[x, y]:
                    continue

        # Choose randomly from all appropriate room generation algorithms
        new_room = random.choice([
            create_ca_room(room_width, room_height, p=40),
            # maps.procgen.RectangularRoom(room_location[0], room_location[1], room_width, room_height)
        ])
        if not True in new_room:
            continue

        # Randomly rotate new room
        _, new_room = rotate_array(new_room)

        # Slap it down
        for x in range(0, np.size(new_room, 0) - 1):
            for y in range(0, np.size(new_room, 1) - 1):
                if new_room[x, y] == True:
                    try:
                        dungeon.tiles[room_xy[0] + x, room_xy[1] + y] = random.choice(maps.tiles.floor_tiles_1)
                    except IndexError:
                        # For now, skip if there's an OOB
                        continue

    return MapGenError()


def place_congruous_room(dungeon: GameMap, engine: Engine) -> Optional[None | Exception]:
    """
    Place a room according to the following procedure:
    - Calculate all tiles at the edges of the currently accessible area for the player
    - Choose a tile at random from this list
    - Evaluate whether a room of the specified size can be placed in any of the cardinal directions, offset by 1 from
    the starting tile.
    - If this does not succeed, continue
    - If this does succeed, update the list of room locations in the game_map
    - If the room could not be placed, raise a mapgen error.
    """

    edges = np.full((dungeon.width, dungeon.height), fill_value=False, order="F")

    # First define the edges
    for x in range(len(dungeon.tiles[:, 0])):
        for y in range(len(dungeon.tiles[0, :])):
            for nx, ny in dungeon.find_neighbours(x, y):
                if dungeon.tiles[x, y]['name'] == 'muddy_wall' and dungeon.accessible[nx, ny]:
                    edges[x, y] = True

    # Define room size
    room_width = random.randint(5, 7)
    room_height = random.randint(5, 8)

    # Remove overlapping rooms_zone to prevent rooms from being stacked
    for x in range(len(dungeon.tiles[:, 0])):
        for y in range(len(dungeon.tiles[0, :])):
            if dungeon.room_zone[x, y]:
                edges[x, y] = False

    # Find somewhere to start trying to place the room and trim edges so there's no OOB
    edges[0:room_width + 2, :] = False  # First rows
    edges[dungeon.width - room_width - 3:dungeon.width, :] = False  # Last rows
    edges[:, 0:room_width + 2] = False  # First columns
    edges[:, dungeon.height - room_height - 3:dungeon.height] = False  # Last columns
    edges[engine.player.x, engine.player.y] = True

    tries = 0
    while True in edges:
        if logging.DEBUG >= logging.root.level:
            engine.message_log.add_message(f"Placing random rect. room. Attempt {tries + 1}", config.colour.debug)
        try_index = random.choice(np.argwhere(edges == True))

        # Check if there is an available area to place the room NESW by evaluating neighbours
        # North
        if not True in edges[try_index[0] - room_height:try_index[0],
                       try_index[1] - room_width // 2 + 1:try_index[1] + room_width // 2 + 1]:
            indices_x = np.arange(try_index[0] - room_height - 1 + 2, try_index[0] + 2)
            indices_y = np.arange(try_index[1] - room_width // 2 - 1, try_index[1] + room_width // 2 + 1)
            if not True in dungeon.room_zone[indices_x[0]:indices_x[-1] - 1, indices_y[0]:indices_y[-1]]:
                break
        # East
        elif not True in edges[try_index[0] - room_width // 2:try_index[0] + room_width // 2 + 1,
                         try_index[1] + 1:try_index[1] + room_height + 1]:
            indices_x = np.arange(try_index[0] - room_width // 2, try_index[0] + room_width // 2 + 1)
            indices_y = np.arange(try_index[1] - 1, try_index[1] + room_height + 1)
            if not True in dungeon.room_zone[indices_x[0]:indices_x[-1], indices_y[0]:indices_y[-1] - 1]:
                break
        # South
        elif not True in edges[try_index[0] + 1:try_index[0] + room_height + 1,
                         try_index[1] - room_width // 2:try_index[1] + room_width // 2]:
            indices_x = np.arange(try_index[0], try_index[0] + room_height + 1)
            indices_y = np.arange(try_index[1] - room_width // 2, try_index[1] + room_width // 2 + 1)
            if not True in dungeon.room_zone[indices_x[0] - 1:indices_x[-1], indices_y[0]:indices_y[-1]]:
                break
        # # West
        elif not True in edges[try_index[0] - room_width // 2:try_index[0] + room_width // 2,
                         try_index[1] - room_height:try_index[1]]:
            indices_x = np.arange(try_index[0] - room_width // 2 - 1, try_index[0] + room_width // 2 + 1)
            indices_y = np.arange(try_index[1] + 1 - room_height, try_index[1] + 2)
            if not True in dungeon.room_zone[indices_x[0] + 1:indices_x[-1], indices_y[0]:indices_y[-1]]:
                break
        else:
            edges[try_index[0], try_index[1]] = False
            tries += 1
            continue

    # Find center and add to rooms array, then tell dungeon where the room is
    center = (indices_x[len(indices_x) // 2], indices_y[len(indices_y) // 2])
    dungeon.rooms.append(center)
    dungeon.room_zone[indices_x[0] - 1:indices_x[-1] + 1, indices_y[0] - 1:indices_y[-1] + 1] = True

    # Create the array of border tiles and calculate the length of the perimeter
    n_border = []
    e_border = []
    s_border = []
    w_border = []
    for i in np.arange(indices_x[0], indices_x[-1]):
        n_border.append((i, indices_y[0]))
    for i in np.arange(indices_x[0], indices_x[-1]):
        e_border.append((i, indices_y[-1]))
    for i in np.arange(indices_y[0], indices_y[-1] + 1):
        s_border.append((indices_x[-1], i))
    for i in np.arange(indices_y[0], indices_y[-1]):
        w_border.append((indices_x[0], i))

    # Find the number of bordering walkable tiles along each room edge
    n_ext = []
    e_ext = []
    s_ext = []
    w_ext = []
    for i in np.arange(indices_x[0] + 1, indices_x[-1]):
        n_ext.append((i, indices_y[0] - 1))
    for i in np.arange(indices_x[0] + 2, indices_x[-1] + 1):
        e_ext.append((i - 1, indices_y[-1] + 1))
    for i in np.arange(indices_y[0], indices_y[-1] - 1):
        s_ext.append((indices_x[-1] + 1, i + 1))
    for i in np.arange(indices_y[0], indices_y[-1] - 1):
        w_ext.append((indices_x[0] - 1, i + 1))

    # Calculate number of tiles around the room which are walkable
    n_bordering = []
    e_bordering = []
    s_bordering = []
    w_bordering = []
    total_bordering = 0
    for ext_tile in n_ext:
        if dungeon.tiles['walkable'][ext_tile]:
            int_tile = (ext_tile[0], ext_tile[1] + 1)
            n_bordering.append(int_tile)
            total_bordering += 1
    for ext_tile in e_ext:
        if dungeon.tiles['walkable'][ext_tile]:
            int_tile = (ext_tile[0], ext_tile[1] - 1)
            e_bordering.append(int_tile)
            total_bordering += 1
    for ext_tile in s_ext:
        try:
            if dungeon.tiles['walkable'][ext_tile]:
                int_tile = (ext_tile[0] - 1, ext_tile[1])
                s_bordering.append(int_tile)
                total_bordering += 1
        except IndexError:
            continue
    for ext_tile in w_ext:
        if dungeon.tiles['walkable'][ext_tile]:
            int_tile = (ext_tile[0] + 1, ext_tile[1])
            w_bordering.append(int_tile)
            total_bordering += 1

    # Calculate number of doors to be added based on the total amount of space which surrounds the rooms
    if total_bordering <= 4:
        doors = 1
    elif total_bordering <= 8:
        doors = 2
    else:
        doors = random.choice([3, 4])

    selections = []
    if n_bordering != []:
        selections.append("n")
    if e_bordering != []:
        selections.append("e")
    if s_bordering != []:
        selections.append("s")
    if w_bordering != []:
        selections.append("w")
    if n_bordering == [] and e_bordering == [] and s_bordering == [] and w_bordering == []:
        return None

    # Interior as floor
    for x in np.arange(indices_x[0], indices_x[-1]):
        for y in np.arange(indices_y[0], indices_y[-1]):
            dungeon.tiles[x, y] = random.choice(maps.tiles.floor_tiles_1)

    # Perimeter as walls. Invalid if the wall would be placed at the player spawn location
    player_xy = (engine.player.x, engine.player.y)
    for n_tile in n_border:
        if player_xy == n_tile:
            return None
        dungeon.tiles[n_tile[0], n_tile[1]] = maps.tiles.wooden_wall
    for e_tile in e_border:
        if player_xy == e_tile:
            return None
        dungeon.tiles[e_tile[0], e_tile[1]] = maps.tiles.wooden_wall
    for s_tile in s_border:
        if player_xy == s_tile:
            return None
        dungeon.tiles[s_tile[0], s_tile[1]] = maps.tiles.wooden_wall
    for w_tile in w_border:
        if player_xy == w_tile:
            return None
        dungeon.tiles[w_tile[0], w_tile[1]] = maps.tiles.wooden_wall

    # Add doors as static objects with appropriate face
    door_top = dungeon.engine.clone('shanty_door_top')
    door_side = dungeon.engine.clone('shanty_door_side')
    while doors > 0:
        if selections == []:
            if logging.DEBUG >= logging.root.level:
                return MapGenError("Could not place room: No tiles available to place entry/exit")
            return
        selection = random.choice(selections)
        if selection == "n":
            selections.remove("n")
            door_tile = random.choice(n_bordering)
            dungeon.tiles[door_tile] = random.choice(maps.tiles.floor_tiles_1)
            door_top.spawn(dungeon, door_tile[0], door_tile[1])
        elif selection == "e":
            selections.remove("e")
            door_tile = random.choice(e_bordering)
            dungeon.tiles[door_tile] = random.choice(maps.tiles.floor_tiles_1)
            door_top.spawn(dungeon, door_tile[0], door_tile[1])
        elif selection == "s":
            selections.remove("s")
            door_tile = random.choice(s_bordering)
            dungeon.tiles[door_tile] = random.choice(maps.tiles.floor_tiles_1)
            door_side.spawn(dungeon, door_tile[0], door_tile[1])
        elif selection == "w":
            selections.remove("w")
            door_tile = random.choice(w_bordering)
            dungeon.tiles[door_tile] = random.choice(maps.tiles.floor_tiles_1)
            door_side.spawn(dungeon, door_tile[0], door_tile[1])
        doors -= 1

    return None


def create_ca_room(width: int, height: int, p: int) -> np.array([]):
    """Create a room which is a shape made from a cellular automata algorithm.
    Room: True for floor tile, False for wall tile."""
    # Init room array
    room = np.full((width, height), fill_value=False, order="F")

    # Select a few random locations to be turned into a floor
    for x in range(width):
        for y in range(height):
            if random.randint(0, 100) > p:
                room[x, y] = True

    # Perform algorithm
    for x in range(width):
        for y in range(height):
            if x == 0 or x == width - 1 or y == 0 or y == height - 1:
                room[x, y] = False

    for x in range(width):
        for y in range(height):
            touching_empty_space = 0
            for nx, ny in find_neighbours(width, height, x, y):
                if not room[nx, ny]:
                    touching_empty_space += 1
            if touching_empty_space >= 7:
                room[x, y] = False
            elif touching_empty_space <= 2:
                room[x, y] = True

    return room


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
