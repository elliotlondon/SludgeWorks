import math
from stairs import Stairs
from random_utils import from_dungeon_level, random_choice_from_dict
from monster_dict import *
from item_dict import *


class GameMap:
    def __init__(self, width, height, dungeon_level=1):
        self.width = width
        self.height = height
        self.tiles = self.initialize_tiles()
        self.dungeon_level = dungeon_level

    def __iter__(self):
        for xi in range(self.width):
            for yi in range(self.height):
                yield xi, yi, self.tiles[xi][yi]

    def initialize_tiles(self):
        tiles = [[Tile(True) for y in range(self.height)] for x in range(self.width)]
        return tiles

    def make_map(self, map_width, map_height, player, entities):
        # Generate each floor's map by calling the appropriate chamber creation function.
        entire_dungeon = Rect(0, 0, map_width, map_height)
        if self.dungeon_level == 1:
            # Chamber 1: Large, straightforward (barely eroded) rooms
            max_rooms = 50
            max_room_size = 10
            min_room_size = 4
            self.rooms_chamber(max_rooms, min_room_size, max_room_size, map_width, map_height, player,
                               entities)
            self.erode(map_width, map_height, 1)
            self.place_entities(entire_dungeon, entities)
        elif self.dungeon_level == 2:
            # Chamber 2: Eroded rooms
            max_rooms = 40
            max_room_size = 10
            min_room_size = 4
            self.rooms_chamber(max_rooms, min_room_size, max_room_size, map_width, map_height, player,
                               entities)
            self.caves_chamber(map_width, map_height, 80, 1)
            self.erode(map_width, map_height, 1)
            self.place_entities(entire_dungeon, entities)
        elif self.dungeon_level == 3:
            # Chamber 3: Caves
            max_rooms = 30
            max_room_size = 26
            min_room_size = 6
            self.rooms_chamber(max_rooms, min_room_size, max_room_size, map_width, map_height, player,
                               entities)
            self.caves_chamber(map_width, map_height, 60, 4)
            self.erode(map_width, map_height, 1)
            self.place_entities(entire_dungeon, entities)
        elif self.dungeon_level == 4:
            # Chamber 4: Narrow Caves
            max_rooms = 20
            max_room_size = 6
            min_room_size = 2
            self.caves_chamber(map_width, map_height, 45, 1)
            self.erode(map_width, map_height, 1)
            self.rooms_chamber(max_rooms, min_room_size, max_room_size, map_width, map_height, player,
                               entities)
            self.erode(map_width, map_height, 1)
            self.place_entities(entire_dungeon, entities)
        else:
            # TODO: other chambers
            max_rooms = 30
            max_room_size = 10
            min_room_size = 6
            self.rooms_chamber(max_rooms, min_room_size, max_room_size, map_width, map_height, player,
                               entities)
            self.caves_chamber(map_width, map_height, 60, 4)
            self.erode(map_width, map_height, 1)
            self.place_entities(entire_dungeon, entities)

    def place_entities(self, room, entities):
        max_monsters = from_dungeon_level([[50, 1], [75, 2], [100, 4], [125, 6]], self.dungeon_level)
        max_plants = from_dungeon_level([[25, 1], [35, 3], [50, 4], [35, 6]], self.dungeon_level)
        max_items = from_dungeon_level([[20, 1], [25, 3], [30, 4]], self.dungeon_level)
        # Get a random number of monsters
        number_of_monsters = randint(round(max_monsters*0.75), max_monsters)
        number_of_plants = randint(round(max_plants*0.75), max_plants)
        number_of_items = randint(round(max_items*0.75), max_items)

        monster_chances = {
            'Wretch': from_dungeon_level([[50, 1], [35, 4], [20, 6], [20, 8]], self.dungeon_level),
            'Hunchback': from_dungeon_level([[10, 2], [30, 4], [50, 6], [40, 8]], self.dungeon_level),
            'Moire Beast': from_dungeon_level([[10, 2], [20, 4], [40, 6], [20, 8]], self.dungeon_level),
            'Thresher': from_dungeon_level([[5, 4], [15, 6], [30, 8], [50, 10]], self.dungeon_level),
            'Bloodseeker': from_dungeon_level([[1, 4], [3, 6], [5, 8]], self.dungeon_level)
        }

        # Item dictionary
        item_chances = {
            'healing_potion': 35,
            'iron_longsword': from_dungeon_level([[10, 0]], self.dungeon_level),
            'iron_helmet': from_dungeon_level([[5, 0], [10, 3]], self.dungeon_level),
            'iron_buckler': from_dungeon_level([[10, 0]], self.dungeon_level),
            'lightning_scroll': from_dungeon_level([[25, 4]], self.dungeon_level),
            'fireball_scroll': from_dungeon_level([[25, 6]], self.dungeon_level),
            'confusion_scroll': from_dungeon_level([[10, 2]], self.dungeon_level)
        }

        # Place stationary monsters (plants) independent of monster number
        for i in range(number_of_plants):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            if not any([entity for entity in entities if entity.x == x and entity.y == y]) \
                    and not self.is_blocked(x, y):
                    entities.append(whip_vine(x, y))

        # Place monsters with random spawning chances
        for i in range(number_of_monsters):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            if not any([entity for entity in entities if entity.x == x and entity.y == y])\
                    and not self.is_blocked(x, y):
                monster_choice = random_choice_from_dict(monster_chances)
                if monster_choice == 'Wretch':
                    entities.append(wretch(x, y))
                elif monster_choice == 'Hunchback':
                    entities.append(hunchback(x, y))
                elif monster_choice == 'Thresher':
                    entities.append(thresher(x, y))
                elif monster_choice == 'Moire Beast':
                    entities.append(moire_beast(x, y))

        # Place items
        for i in range(number_of_items):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            if not any([entity for entity in entities if entity.x == x and entity.y == y]) \
                    and not self.is_blocked(x, y):
                item_choice = random_choice_from_dict(item_chances)

                # Weapons and shields (main-hand and off-hand)
                if item_choice == 'iron_longsword':
                    entities.append(iron_longsword(x, y))
                elif item_choice == 'iron_buckler':
                    entities.append(iron_buckler(x, y))

                # Armour
                elif item_choice == 'iron_helmet':
                    entities.append(iron_helmet(x, y))

                # Consumables
                elif item_choice == 'healing_potion':
                    entities.append(healing_potion(x, y))
                elif item_choice == 'fireball_scroll':
                    entities.append(fireball_scroll(x, y))
                elif item_choice == 'confusion_scroll':
                    entities.append(confusion_scroll(x, y))
                elif item_choice == 'lightning_scroll':
                    entities.append(lightning_scroll(x, y))

    def is_blocked(self, x, y):
        if self.tiles[x][y].blocked:
            return True

        return False

    def returncoordinatesinmap(self, coord_x, coord_y):
        if coord_x >= 0 and coord_x < self.width:
            if coord_y >= 0 and coord_y < self.height:
                return True
            return False

    def next_floor(self, player, constants):
        self.dungeon_level += 1
        entities = [player]

        self.tiles = self.initialize_tiles()
        self.make_map(constants['map_width'], constants['map_height'], player, entities)

        # Heal on change of floors?
        # player.fighter.heal(player.fighter.max_hp // 2)

        return entities

    def create_room(self, room):
        # Go through the tiles in the rectangle and make them passable
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self.tiles[x][y].blocked = False
                self.tiles[x][y].block_sight = False

    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False
            self.tiles[x][y].tunnel = True

    def create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False
            self.tiles[x][y].tunnel = True

    def find_neighbours(self, x, y):
        xi = (0, -1, 1) if 0 < x < self.width - 1 else ((0, -1) if x > 0 else (0, 1))
        yi = (0, -1, 1) if 0 < y < self.height - 1 else ((0, -1) if y > 0 else (0, 1))
        for a in xi:
            for b in yi:
                if a == b == 0:
                    continue
                yield (x + a, y + b)

    def rooms_chamber(self, max_rooms, min_room_size, max_room_size, map_width, map_height, player, entities):
        # A chamber which is filled with rectangular rooms of random sizes, joined with single-jointed corridors.
        free_tiles = []
        rooms = []
        num_rooms = 0
        for r in range(max_rooms):
            w = randint(min_room_size, max_room_size)
            h = randint(min_room_size, max_room_size)
            x = randint(0, map_width - w - 1)
            y = randint(0, map_height - h - 1)

            # "Rect" class makes rectangles easier to work with
            new_room = Rect(x, y, w, h)

            # Run through the other rooms and see if they intersect with this one
            for other_room in rooms:
                if new_room.intersect(other_room):
                    break
            else:
                self.create_room(new_room)
                (new_x, new_y) = new_room.center()
                center_of_last_room_x = new_x
                center_of_last_room_y = new_y

                if num_rooms == 0:
                    player.x = new_x
                    player.y = new_y
                else:
                    # center coordinates of previous room
                    (prev_x, prev_y) = rooms[num_rooms - 1].center()

                    if randint(0, 1) == 1:
                        # first move horizontally, then vertically
                        self.create_h_tunnel(prev_x, new_x, prev_y)
                        self.create_v_tunnel(prev_y, new_y, new_x)
                    else:
                        # first move vertically, then horizontally
                        self.create_v_tunnel(prev_y, new_y, prev_x)
                        self.create_h_tunnel(prev_x, new_x, new_y)

                # Make a list of all the free tiles to be sent to object placement
                for x in range(map_width):
                    for y in range(map_height):
                        if not self.tiles[x][y].block_sight and not self.tiles[x][y].blocked:
                            free_tiles.append(self.tiles[x][y])
                # Use this if you wish to place actors on a room-by-room basis
                # self.place_entities(new_room, entities)
                rooms.append(new_room)
                num_rooms += 1

        if num_rooms > 0:
            stairs_component = Stairs(self.dungeon_level + 1)
            down_stairs = Entity(center_of_last_room_x, center_of_last_room_y, '>', libtcod.white, 'Stairs',
                                 'There\'s a dark chasm here which will allow you to take a one-way trip to'
                                 'the next chamber of the SludgeWorks.',
                                 render_order=RenderOrder.STAIRS, stairs=stairs_component)
            entities.append(down_stairs)
        else:
            print('Map generation failed: No rooms generated.')

    def caves_chamber(self, map_width, map_height, p, smoothing):
        """
        A chamber filled with random-sized, sprawling cave rooms, generated using an automata technique.
        p is the probability of a cave sector being created. Smoothing values about 4 do nothing, below 4 cause
        more rugged caves.
        """
        for x in range(map_width):
            for y in range(map_height):
                if randint(0, 100) > p:
                    # Select a few random locations to be turned into a floor
                    self.tiles[x][y].blocked = False
                    self.tiles[x][y].block_sight = False

        for i in range(smoothing):
            for x in range(map_width):
                for y in range(map_height):
                    if x == 0 or x == map_width - 1 or y == 0 or y == map_height - 1:
                        self.tiles[x][y].blocked = True
                        self.tiles[x][y].block_sight = True
                    touching_empty_space = 0
                    for nx, ny in self.find_neighbours(x, y):
                        if self.tiles[nx][ny].blocked:
                            touching_empty_space += 1
                    if touching_empty_space >= 5 and not self.tiles[x][y].tunnel:
                        self.tiles[x][y].blocked = True
                        self.tiles[x][y].block_sight = True
                    elif touching_empty_space <= 1:
                        self.tiles[x][y].blocked = False
                        self.tiles[x][y].block_sight = False
                    if x == 0 or x == map_width - 1 or y == 0 or y == map_height - 1:
                        self.tiles[x][y].blocked = True
                        self.tiles[x][y].block_sight = True

    def erode(self, map_width, map_height, smoothing):
        """
        A tool for helping to increase the erosion of an already-generated map
        """
        for i in range(smoothing):
            for x in range(map_width):
                for y in range(map_height):
                    touching_empty_space = 0
                    for nx, ny in self.find_neighbours(x, y):
                        if self.tiles[nx][ny].blocked:
                            touching_empty_space += 1
                    if touching_empty_space >= 5 and not self.tiles[x][y].tunnel:
                        self.tiles[x][y].blocked = True
                        self.tiles[x][y].block_sight = True
                    elif touching_empty_space <= 3:
                        self.tiles[x][y].blocked = False
                        self.tiles[x][y].block_sight = False
                    if x == 0 or x == map_width - 1 or y == 0 or y == map_height - 1:
                        self.tiles[x][y].blocked = True
                        self.tiles[x][y].block_sight = True

    # This function uses a dijkstra map to navigate the player towards the nearest unexplored tile. Interrupted by
    # monsters entering FoV.
    def explore(self, player, entities, message_log):
        unexplored_coords = []

        # Loop over the map to find all unexplored tiles
        for y in range(self.height):
            for x in range(self.width):
                if not self.tiles[x][y].explored and not self.tiles[x][y].blocked:
                    unexplored_coords.append((y, x))

        if len(unexplored_coords) == 0:
            message_log.add_message(Message('There is nowhere else to explore.', libtcod.orange))
            return False

        # Find the nearest unexplored coords
        starting_distance = 100000
        closest_coord = None

        for y, x in unexplored_coords:
            new_distance = math.hypot(x - player.x, y - player.y)

            if new_distance < starting_distance:
                starting_distance = new_distance
                closest_coord = (x, y)

        path_to_closest_coord = []

        if closest_coord:
            my_map = libtcod.map_new(self.width, self.height)

            for y in range(self.height):
                for x in range(self.width):
                    if not self.tiles[x][y].blocked:
                        libtcod.map_set_properties(my_map, x, y, True, True)

            # Create a new dijkstra map
            dij_pather = libtcod.dijkstra_new(my_map)

            # Compute the dijkstra map
            libtcod.dijkstra_compute(dij_pather, player.x, player.y)

            # Make a path to target
            libtcod.dijkstra_path_set(dij_pather, closest_coord[0], closest_coord[1])

            # Get the path
            if not libtcod.dijkstra_is_empty(dij_pather):
                x, y = libtcod.dijkstra_path_walk(dij_pather)
                path_to_closest_coord.append((x, y))

                # Move player along the path
                if not path_to_closest_coord:
                    message_log.add_message(Message('You cannot explore the remaining tiles', libtcod.yellow))
                    return False

                else:
                    player.x = x
                    player.y = y

        return True


class Tile:
    def __init__(self, blocked, block_sight=None):
        self.blocked = blocked
        self.tunnel = False

        # By default, if a tile is blocked, it also blocks sight
        if block_sight is None:
            block_sight = blocked

        self.block_sight = block_sight

        # Change this if you wish to see everything!
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
