import tcod as libtcod
import math, random

from random import randint

from ai import Aggressive, Stationary
from equipment import EquipmentSlots, Equippable
from fighter import Fighter
from item import Item
from stairs import Stairs
from entity import Entity
from game_messages import Message
from item_functions import cast_confuse, cast_fireball, cast_lightning, heal
from random_utils import from_dungeon_level, random_choice_from_dict
from render_functions import RenderOrder


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

            # TODO: Stop monsters and items being placed within blocked tiles!!!

            # self.place_entities(entire_dungeon, entities)
        elif self.dungeon_level == 2:
            # Chamber 2: Eroded rooms
            max_rooms = 40
            max_room_size = 10
            min_room_size = 4
            self.rooms_chamber(max_rooms, min_room_size, max_room_size, map_width, map_height, player,
                               entities)
            self.caves_chamber(map_width, map_height, 80, 1)
            self.erode(map_width, map_height, 1)
        elif self.dungeon_level == 3:
            # Chamber 3: Caves
            max_rooms = 30
            max_room_size = 26
            min_room_size = 6
            self.rooms_chamber(max_rooms, min_room_size, max_room_size, map_width, map_height, player,
                               entities)
            self.caves_chamber(map_width, map_height, 60, 4)
            self.erode(map_width, map_height, 1)
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
        else:
            # TODO: other chambers
            max_rooms = 30
            max_room_size = 10
            min_room_size = 6
            self.rooms_chamber(max_rooms, min_room_size, max_room_size, map_width, map_height, player,
                               entities)
            self.caves_chamber(map_width, map_height, 60, 4)
            self.erode(map_width, map_height, 1)

    def place_entities(self, room, entities):
        max_monsters = from_dungeon_level([[2, 1], [3, 4], [5, 6]], self.dungeon_level)
        max_plants = from_dungeon_level([[2, 1], [3, 4], [2, 6]], self.dungeon_level)
        max_items = from_dungeon_level([[2, 1], [3, 4]], self.dungeon_level)
        # Get a random number of monsters
        number_of_monsters = randint(round(max_monsters*0.75), max_monsters)
        number_of_plants = randint(round(max_plants*0.75), max_plants)
        number_of_items = randint(round(max_items*0.75), max_items)

        monster_chances = {
            'Wretch': 80,
            'Hunchback': from_dungeon_level([[10, 2], [25, 4], [80, 6], [40, 10]], self.dungeon_level),
            'Thresher': from_dungeon_level([[5, 4], [15, 6], [30, 8], [50, 10]], self.dungeon_level)
        }

        # Item dictionary
        item_chances = {
            'healing_potion': 35,
            'sword': from_dungeon_level([[10, 0]], self.dungeon_level),
            'helm': from_dungeon_level([[5, 0], [10, 3]], self.dungeon_level),
            'shield': from_dungeon_level([[10, 0]], self.dungeon_level),
            'lightning_scroll': from_dungeon_level([[25, 4]], self.dungeon_level),
            'fireball_scroll': from_dungeon_level([[25, 6]], self.dungeon_level),
            'confusion_scroll': from_dungeon_level([[10, 2]], self.dungeon_level)
        }

        # Place stationary monsters (plants) independent of monster number
        for i in range(number_of_plants):
            # Choose a random location in within the dungeon that isn't blocked
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)

            if not any([entity for entity in entities if entity.x == x and entity.y == y]):
                # if not any([Tile in self.tiles if self.tiles[x][y] == self.blocked]):
                    fighter_component = Fighter(current_hp=8, max_hp=8,
                                                damage_dice=1, damage_sides=2,
                                                strength=3, agility=1, vitality=1, intellect=1, perception=1,
                                                xp=25)
                    ai_component = Stationary()
                    monster = Entity(x, y, 'V', libtcod.light_grey, 'Whip Vine',
                                     'What at first appears to be no more than a dead, waist-height bush in actuality' 
                                     'represents a highly specialized carnivorous flayer',
                                     blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component,
                                     ai=ai_component, faction='Plants')

                    entities.append(monster)

        # Place monsters with random spawning chances
        for i in range(number_of_monsters):
            # Choose a random location in the room
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)

            if not any([entity for entity in entities if entity.x == x and entity.y == y]):
                monster_choice = random_choice_from_dict(monster_chances)

                if monster_choice == 'Wretch':
                    fighter_component = Fighter(current_hp=6, max_hp=6,
                                                damage_dice=1, damage_sides=3,
                                                strength=3, agility=0, vitality=1, intellect=1, perception=1,
                                                xp=50)
                    ai_component = Aggressive()
                    monster = Entity(x, y, 'w', libtcod.darker_red, 'Wretch',
                                     'A stunted human swaddled in filthy rags and long since driven feral by the '
                                     'SludgeWorks.',
                                     blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component,
                                     ai=ai_component, faction='Scavengers')
                elif monster_choice == 'Hunchback':
                    fighter_component = Fighter(current_hp=12, max_hp=12,
                                                damage_dice=2, damage_sides=6,
                                                strength=7, agility=1, vitality=1, intellect=1, perception=1,
                                                xp=125)
                    ai_component = Aggressive()
                    monster = Entity(x, y, 'H', libtcod.brass, 'Hunchback',
                                     'A humanoid figure draped in dark, hooded robes. It\'s face is completely '
                                     'concealed and it carries a wicked, curved dagger. It moves with purpose and '
                                     'chants in an ancient, guttural tongue.',
                                     blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component,
                                     ai=ai_component, faction='Horrors')
                else:
                    fighter_component = Fighter(current_hp=26, max_hp=26,
                                                damage_dice=3, damage_sides=4,
                                                strength=5, agility=4, vitality=1, intellect=1, perception=1,
                                                xp=225)
                    ai_component = Aggressive()
                    monster = Entity(x, y, 'T', libtcod.dark_azure, 'Thresher',
                                     'A colossal ogre-like ape covered in patches of matted hair and littered with '
                                     'scars. This creature tirelessly searches it\'s surroundings for new objects to '
                                     'smash together with a joyous, childlike expression.',
                                     blocks=True, fighter=fighter_component, render_order=RenderOrder.ACTOR,
                                     ai=ai_component, faction='Scavengers')

                entities.append(monster)

        # Place items
        for i in range(number_of_items):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)

            if not any([entity for entity in entities if entity.x == x and entity.y == y]):
                item_choice = random_choice_from_dict(item_chances)

                # Weapons and armour
                if item_choice == 'sword':
                    equippable_component = Equippable(EquipmentSlots.MAIN_HAND,
                                                      damage_dice=1, damage_sides=6,
                                                      strength_bonus=3)
                    item = Entity(x, y, '/', libtcod.sky, 'Rusted Longsword',
                                  'An iron longsword with an edge that has been significantly corroded by rust. ' +
                                  'It\'s fairly blunt, but much better than ' +
                                  'nothing.',
                                  equippable=equippable_component)
                elif item_choice == 'shield':
                    equippable_component = Equippable(EquipmentSlots.OFF_HAND, agility_bonus=1)
                    item = Entity(x, y, '[', libtcod.darker_orange, 'Shield',
                                  'A small buckler that can be attached to the arm and used to deflect attacks.',
                                  equippable=equippable_component)
                elif item_choice == 'helm':
                    equippable_component = Equippable(EquipmentSlots.HEAD, agility_bonus=1)
                    item = Entity(x, y, '[', libtcod.darker_orange, 'Helm',
                                  'A leather helmet designed to help minimise head wounds.',
                                  equippable=equippable_component)

                # Consumables
                elif item_choice == 'healing_potion':
                    heal_amount = 40
                    item_component = Item(use_function=heal, amount=heal_amount)
                    item = Entity(x, y, '!', libtcod.violet, 'Healing Potion',
                                  'A violet flask that you recognise to be a healing potion. This will help '
                                  'heal your wounds. ' + str(heal_amount) + ' HP',
                                  render_order=RenderOrder.ITEM,
                                  item=item_component)
                elif item_choice == 'fireball_scroll':
                    fireball_damage = 25
                    fireball_range = 3
                    item_component = Item(use_function=cast_fireball, targeting=True, targeting_message=Message(
                        'Left-click a target tile for the fireball, or right-click to cancel.', libtcod.light_cyan),
                                          damage=fireball_damage, radius=fireball_range)
                    item = Entity(x, y, '#', libtcod.red, 'Fireball Scroll',
                                  'A scroll containing an ancient text that you somehow understand the meaning ' +
                                  'of. When invoked, envelopes an area with fire, causing ' + str(fireball_damage) +
                                  ' damage to all creatures within ' + str(fireball_range) + 'tiles.',
                                  render_order=RenderOrder.ITEM,
                                  item=item_component)
                elif item_choice == 'confusion_scroll':
                    item_component = Item(use_function=cast_confuse, targeting=True, targeting_message=Message(
                        'Left-click an enemy to confuse it, or right-click to cancel.', libtcod.light_cyan))
                    item = Entity(x, y, '#', libtcod.light_pink, 'Confusion Scroll',
                                  'A scroll containing an ancient text that you somehow understand the meaning ' +
                                  'of. When invoked, this scroll will cause an enemy to wander aimlessly for 10 turns.',
                                  render_order=RenderOrder.ITEM,
                                  item=item_component)
                else:
                    lightning_damage = 40
                    item_component = Item(use_function=cast_lightning, damage=lightning_damage, maximum_range=5)
                    item = Entity(x, y, '#', libtcod.yellow, 'Lightning Scroll',
                                  'A scroll containing an ancient text that you somehow understand the meaning ' +
                                  'of. When invoked, deals ' + str(lightning_damage) + ' damage.',
                                  render_order=RenderOrder.ITEM,
                                  item=item_component)
                entities.append(item)

    def is_blocked(self, x, y):
        if self.tiles[x][y].blocked:
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
        # go through the tiles in the rectangle and make them passable
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
        """
        Finds all cells that touch a cell in a 2D grid
        Args:
            x and y: integer, indices for the cell to search around
        Returns:
            returns a generator object with the x,y indices of cell neighbours
        """
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
            # Random width and height
            w = randint(min_room_size, max_room_size)
            h = randint(min_room_size, max_room_size)
            # Random position without going out of the boundaries of the map
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
                self.place_entities(new_room, entities)
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
