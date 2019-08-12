import math
from random import uniform
from numpy.random import normal, seed
from map_utils.stairs import Stairs
from random_utils import from_dungeon_level, random_choice_from_dict
from map_utils.monster_dict import *
from map_utils.item_dict import *


class GameMap:
    def __init__(self, current_biome, width, height, max_room_size=10, min_room_size=6, max_rooms=25,
                 dark_wall=libtcod.dark_grey, light_wall=libtcod.Color(150, 100, 50), dark_ground=libtcod.black,
                 light_ground=libtcod.dark_grey, dungeon_level=1, floor_chars=[' ', '.', ',', '`']):
        self.current_biome = current_biome
        self.width = width
        self.height = height
        self.max_room_size = max_room_size
        self.min_room_size = min_room_size
        self.max_rooms = max_rooms
        self.dark_wall = dark_wall
        self.light_wall = light_wall
        self.dark_ground = dark_ground
        self.light_ground = light_ground
        self.tiles = self.initialize_tiles()
        self.dungeon_level = dungeon_level
        self.floor_chars = floor_chars

    def __iter__(self):
        for xi in range(self.width):
            for yi in range(self.height):
                yield xi, yi, self.tiles[xi][yi]

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def initialize_tiles(self):
        tiles = [[Tile(True) for y in range(self.height)] for x in range(self.width)]
        return tiles

    def make_map(self, player, entities):
        # Generate each floor's map by calling the appropriate chamber creation function.
        if self.dungeon_level == 1:
            self.rooms_chamber(self.max_room_size, self.min_room_size, self.max_rooms, player, entities)
            self.erode(1)
            return
        if self.current_biome == 'near_surface':
            if uniform(0, 1) >= 0.5:
                self.rooms_chamber(self.max_room_size, self.min_room_size, self.max_rooms, player, entities)
                self.erode(1)
            elif uniform(0, 1) >= 0.5:
                self.current_biome = 'ice_caves'
                self.light_wall = libtcod.white
                self.floor_chars = ['~', ' ', ',', '`', ' ']
                self.caves_chamber(45, 1)
                self.erode(1)
                self.rooms_chamber(16, 8, 75, player, entities)
                self.erode(1)
            else:
                self.current_biome = 'chasms'
                self.light_ground = libtcod.dark_grey
                self.floor_chars = [' ', '.', ',', '`']
                self.rooms_chamber(24, 16, 50, player, entities)
                self.caves_chamber(60, 4)
                self.erode(1)
        elif self.current_biome == 'ice_caves':
            if uniform(0, 1) >= 0.8:
                self.current_biome = 'near_surface'
                self.rooms_chamber(self.max_room_size, self.min_room_size, self.max_rooms, player, entities)
                self.erode(1)
            elif uniform(0, 1) >= 0.2:
                self.caves_chamber(45, 1)
                self.erode(1)
                self.rooms_chamber(16, 8, 75, player, entities)
                self.erode(1)
            else:
                self.current_biome = 'chasms'
                self.light_ground = libtcod.dark_grey
                self.floor_chars = [' ', '.', ',', '`']
                self.rooms_chamber(24, 16, 50, player, entities)
                self.caves_chamber(60, 4)
                self.erode(1)
        elif self.current_biome == 'chasms':
            if uniform(0, 1) >= 0.75:
                self.current_biome = 'near_surface'
                self.rooms_chamber(self.max_room_size, self.min_room_size, self.max_rooms, player, entities)
                self.erode(1)
            else:
                self.rooms_chamber(24, 16, 50, player, entities)
                self.caves_chamber(60, 4)
                self.erode(1)

    def place_entities(self, map_width, map_height, entities):
        room = Rect(0, 0, map_width, map_height)    # Room is the entire dungeon
        max_monsters = from_dungeon_level([[50, 1], [75, 2], [85, 4], [100, 6]], self.dungeon_level)
        max_plants = from_dungeon_level([[25, 1], [35, 3], [50, 4], [35, 6]], self.dungeon_level)
        max_items = from_dungeon_level([[20, 1], [25, 3], [30, 4]], self.dungeon_level)
        number_of_monsters = randint(round(max_monsters*0.75), max_monsters)
        number_of_plants = randint(round(max_plants*0.75), max_plants)
        number_of_items = randint(round(max_items*0.75), max_items)

        plant_chances = {
            'Whip Vine': from_dungeon_level([[50, 1], [35, 4], [20, 6], [20, 8]], self.dungeon_level),
            'Phosphorescent Dahlia': from_dungeon_level([[50, 1], [35, 4], [20, 6], [20, 8]], self.dungeon_level)
        }

        monster_chances = {
            # Scavengers
            'Wretch': from_dungeon_level([[50, 1], [35, 4], [20, 6], [10, 8], [0, 10]], self.dungeon_level),
            'Sludge Fiend': from_dungeon_level([[35, 1], [50, 4], [35, 6], [10, 8], [0, 10]], self.dungeon_level),
            'Thresher': from_dungeon_level([[5, 4], [15, 6], [30, 8], [50, 10]], self.dungeon_level),
            # Beasts
            'Moire Beast': from_dungeon_level([[5, 2], [10, 3], [20, 4], [30, 6], [20, 8]], self.dungeon_level),
            'Lupine Terror': from_dungeon_level([[1, 2], [5, 3], [10, 4], [25, 6], [30, 8]], self.dungeon_level),
            'Bloodseeker': from_dungeon_level([[1, 4], [3, 6], [5, 8]], self.dungeon_level),
            # Horrors
            'Hunchback': from_dungeon_level([[10, 2], [30, 4], [50, 6], [40, 8]], self.dungeon_level),
            # Cultists
            'Risen Sacrifice': from_dungeon_level([[10, 1], [25, 3], [30, 6], [15, 7]], self.dungeon_level),
            'Eternal Celebrant': from_dungeon_level([[10, 2], [25, 3], [30, 6], [15, 7]], self.dungeon_level),
            'Eternal Cult Kidnapper': from_dungeon_level([[10, 2], [20, 4], [40, 6], [20, 8]], self.dungeon_level),
            # Cleansing Hand
            'Cleansing Hand Crusader': from_dungeon_level([[5, 4], [15, 6], [30, 8], [50, 10]], self.dungeon_level),
            'Cleansing Hand Purifier': from_dungeon_level([[5, 5], [10, 6], [20, 8], [50, 10]], self.dungeon_level),
            'Cleansing Hand Duelist': from_dungeon_level([[5, 5], [10, 7], [25, 8], [50, 10]], self.dungeon_level),
            # Minibosses
            'Alfonrice, the Spinning Blade': from_dungeon_level([[1, 4], [3, 6], [5, 8]], self.dungeon_level)
        }

        # Item dictionary
        item_chances = {
            'healing_potion': 35,
            'iron_longsword': from_dungeon_level([[10, 1], [5, 3], [0, 4]], self.dungeon_level),
            'steel_longsword': from_dungeon_level([[5, 2], [10, 3], [15, 4], [10, 5], [5, 6], [0, 7]],
                                                  self.dungeon_level),
            'steel_dagger': from_dungeon_level([[5, 1], [10, 3], [5, 4], [0, 5]], self.dungeon_level),
            'steel_mace': from_dungeon_level([[5, 3], [10, 4], [15, 5], [0, 6]], self.dungeon_level),
            'influenced_hatchet': from_dungeon_level([[1, 4], [5, 5], [3, 6], [10, 7]], self.dungeon_level),
            'iron_buckler': from_dungeon_level([[5, 1], [10, 2], [5, 3], [0, 4]], self.dungeon_level),
            'steel_greatshield': from_dungeon_level([[5, 2], [10, 3], [5, 5], [0, 6]], self.dungeon_level),
            'iron_helmet': from_dungeon_level([[5, 1], [10, 2], [5, 3], [0, 4]], self.dungeon_level),
            'steel_bascinet': from_dungeon_level([[1, 2], [5, 3], [10, 4], [5, 5], [0, 6]], self.dungeon_level),
            'steel_cuirass': from_dungeon_level([[1, 3], [5, 5], [10, 6], [5, 7], [0, 8]], self.dungeon_level),
            'trickster_gloves': from_dungeon_level([[3, 1], [5, 2], [10, 3], [5, 4], [0, 5]], self.dungeon_level),
            'steel_platelegs': from_dungeon_level([[3, 3], [5, 4], [10, 5], [5, 6], [1, 7], [0, 8]],
                                                  self.dungeon_level),
            'wax_coated_ring': from_dungeon_level([[1, 0]], self.dungeon_level),
            'lightning_scroll': from_dungeon_level([[5, 3], [10, 4], [15, 6]], self.dungeon_level),
            'fireball_scroll': from_dungeon_level([[5, 4], [10, 6]], self.dungeon_level),
            'confusion_scroll': from_dungeon_level([[5, 2], [10, 4]], self.dungeon_level)
        }

        # Place stationary monsters (plants) independent of monster number
        for i in range(number_of_plants):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            if not any([entity for entity in entities if entity.x == x and entity.y == y]) \
                    and not self.is_blocked(x, y):
                plant_choice = random_choice_from_dict(plant_chances)
                if plant_choice == 'Whip Vine':
                    entities.append(whip_vine(x, y))
                elif plant_choice == 'Phosphorescent Dahlia':
                    entities.append(phosphorescent_dahlia(x, y))

        # Place monsters with random spawning chances
        for i in range(number_of_monsters):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)
            if not any([entity for entity in entities if entity.x == x and entity.y == y])\
                    and not self.is_blocked(x, y):
                monster_choice = random_choice_from_dict(monster_chances)
                if monster_choice == 'Wretch':
                    entities.append(wretch(x, y))
                elif monster_choice == 'Sludge Fiend':
                    entities.append(sludge_fiend(x, y))
                elif monster_choice == 'Thresher':
                    entities.append(thresher(x, y))
                elif monster_choice == 'Moire Beast':
                    entities.append(moire_beast(x, y))
                elif monster_choice == 'Lupine Terror':
                    entities.append(lupine_terror(x, y))
                elif monster_choice == 'Bloodseeker':
                    entities.append(bloodseeker(x, y))
                elif monster_choice == 'Hunchback':
                    entities.append(hunchback(x, y))
                elif monster_choice == 'Risen Sacrifice':
                    entities.append(risen_sacrifice(x, y))
                elif monster_choice == 'Eternal Celebrant':
                    entities.append(eternal_celebrant(x, y))
                elif monster_choice == 'Eternal Cult Kidnapper':
                    entities.append(eternal_kidnapper(x, y))
                elif monster_choice == 'Cleansing Hand Crusader':
                    entities.append(cleansing_hand_crusader(x, y))
                elif monster_choice == 'Cleansing Hand Purifier':
                    entities.append(cleansing_hand_purifier(x, y))
                elif monster_choice == 'Alfonrice, the Spinning Blade':
                    entities.append(alfonrice(x, y))
                    monster_chances.pop('Alfonrice, the Spinning Blade')

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
                elif item_choice == 'steel_longsword':
                    entities.append(steel_longsword(x, y))
                elif item_choice == 'steel_dagger':
                    entities.append(steel_dagger(x, y))
                elif item_choice == 'steel_mace':
                    entities.append(steel_mace(x, y))
                elif item_choice == 'influenced_hatchet':
                    entities.append(influenced_hatchet(x, y))
                elif item_choice == 'iron_buckler':
                    entities.append(iron_buckler(x, y))
                elif item_choice == 'steel_greatshield':
                    entities.append(steel_greatshield(x, y))

                # Armour
                elif item_choice == 'iron_helmet':
                    entities.append(iron_helmet(x, y))
                elif item_choice == 'steel_bascinet':
                    entities.append(steel_bascinet(x, y))
                elif item_choice == 'steel_cuirass':
                    entities.append(steel_cuirass(x, y))
                elif item_choice == 'trickster_gloves':
                    entities.append(trickster_gloves(x, y))
                elif item_choice == 'steel_platelegs':
                    entities.append(steel_platelegs(x, y))
                elif item_choice == 'wax_coated_ring':
                    entities.append(wax_coated_ring(x, y))
                    item_chances.update({'wax_coated_ring:': 0})

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

    @staticmethod
    def variable_width(previous_width):
        """This function returns a Quasi-Markov chain map width value, based upon the width of the previous map."""
        # Hardcoded min/max
        minimum_width = 72
        maximum_width = 72 * 2
        seed()      # Seed the random number generator randomly
        if previous_width == minimum_width:
            variable_width = round(previous_width + (previous_width - normal(previous_width, 10)))
        elif previous_width == maximum_width:
            variable_width = round(previous_width + (previous_width - normal(previous_width, 10)))
        else:
            variable_width = normal(previous_width, 10)

        # Ensure the width does not clip through the max/min
        if variable_width % 2 != 0:
            variable_width += 1
        if variable_width < minimum_width:
            variable_width = minimum_width
        elif variable_width > maximum_width:
            variable_width = maximum_width
        return int(variable_width)

    @staticmethod
    def variable_height(previous_height):
        """This function returns a Quasi-Markov chain map height value, based upon the width of the previous map."""
        # Hardcoded min/max
        minimum_height = 35
        maximum_height = 72 * 2
        seed()      # Seed the random number generator randomly
        # Height does not stay the same if max or min, only increases/decreases
        if previous_height == minimum_height:
            variable_height = round(previous_height + (previous_height + normal(previous_height, 10)))
        elif previous_height == maximum_height:
            variable_height = round(previous_height + (previous_height - normal(previous_height, 10)))
        else:
            variable_height = normal(previous_height, 10)

        # Ensure that the height does not clip through the max/min
        if variable_height % 2 != 0:
            variable_height += 1
        if variable_height < minimum_height:
            variable_height = minimum_height
        elif variable_height > maximum_height:
            variable_height = maximum_height

        return int(variable_height)

    def next_floor(self, player):
        self.dungeon_level += 1
        entities = [player]

        # Define randomly the new game map size
        variable_width = self.variable_width(self.width)
        variable_height = self.variable_height(self.height)
        # Write the new sizes
        self.width = variable_width
        self.height = variable_height

        # Make the new floor
        self.tiles = self.initialize_tiles()
        self.make_map(player, entities)
        self.place_entities(self.width, self.height, entities)

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

    def rooms_chamber(self, max_room_size, min_room_size, max_rooms, player, entities):
        # A chamber which is filled with rectangular rooms of random sizes, joined with single-jointed corridors.
        rooms = []
        num_rooms = 0
        map_width = self.width
        map_height = self.height
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

                rooms.append(new_room)
                num_rooms += 1

        if num_rooms > 0:
            stairs_component = Stairs(self.dungeon_level + 1)
            down_stairs = Entity(center_of_last_room_x, center_of_last_room_y, '>', libtcod.white, 'Down Stairs',
                                 'There\'s a dark chasm here which will allow you to take a one-way trip to'
                                 'the next chamber of the SludgeWorks.',
                                 render_order=RenderOrder.STAIRS, stairs=stairs_component)
            entities.append(down_stairs)
        else:
            print('Map generation failed: No rooms generated.')

    def caves_chamber(self, p, smoothing):
        """A chamber filled with random-sized, sprawling cave rooms, generated using an automata technique.
        p is the probability of a cave sector being created. Smoothing values about 4 do nothing, below 4 cause
        more rugged caves."""
        map_width = self.width
        map_height = self.height
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

    def erode(self, smoothing):
        """A tool for helping to increase the erosion of an already-generated map."""
        map_width = self.width
        map_height = self.height
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

    def explore(self, player, message_log):
        """This function uses a dijkstra map to navigate the player towards the nearest unexplored tile. Interrupted by
        monsters entering FoV."""
        unexplored_coords = []

        # Loop over the map to find all unexplored tiles
        for y in range(self.height):
            for x in range(self.width):
                if not self.tiles[x][y].explored and not self.tiles[x][y].blocked:
                    unexplored_coords.append((y, x))

        if len(unexplored_coords) == 0:
            message_log.add_message(Message('There is nowhere else to explore.', libtcod.yellow))
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

    def to_down_stairs(self, player, entities, message_log):
        """Create a Dijkstra path to the down stairs. Dijkstra was chosen over A* because libtcod's built-in dijkstra
        seems much faster."""
        stairs_found = False
        for entity in entities:
            if entity.name == 'Down Stairs':
                if self.tiles[entity.x][entity.y].explored:
                    stairs_x = entity.x
                    stairs_y = entity.y
                    stairs_found = True

        if stairs_found:
            my_map = libtcod.map_new(self.width, self.height)

            for y in range(self.height):
                for x in range(self.width):
                    if self.tiles[x][y].explored:
                        libtcod.map_set_properties(my_map, x, y, not self.tiles[x][y].block_sight,
                                                   not self.tiles[x][y].blocked)

            dij_path = libtcod.dijkstra_new(my_map)
            libtcod.dijkstra_compute(dij_path, player.x, player.y)
            libtcod.dijkstra_path_set(dij_path, stairs_x, stairs_y)

            if not libtcod.dijkstra_is_empty(dij_path):
                x, y = libtcod.dijkstra_path_walk(dij_path)

                # Move player along the path
                if not x and not y:
                    message_log.add_message(
                        Message('You cannot safely reach the next set of down stairs from here.',
                                libtcod.yellow))
                    return False
                else:
                    player.x = x
                    player.y = y
                    return True
            elif player.x == stairs_x and player.y == stairs_y:
                return False
            else:
                message_log.add_message(Message('Path to stairs does not exist.', libtcod.yellow))
                return False
        else:
            message_log.add_message(Message('You have not yet discovered the path to the next floor.', libtcod.yellow))
            return False


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
