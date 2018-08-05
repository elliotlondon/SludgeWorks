import libtcodpy as libtcod
from random import randint

from components.ai import Aggressive, Stationary
from components.equipment import EquipmentSlots, Equippable
from components.fighter import Fighter
from components.item import Item
from components.stairs import Stairs
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
        if self.dungeon_level == 1:
            # Chamber 1: Rooms
            max_rooms = 50
            max_room_size = round(map_width / 5)
            min_room_size = round(map_width / 10)
            self.rooms_chamber(max_rooms, min_room_size, max_room_size, map_width, map_height, player, entities)
        elif 2 <= self.dungeon_level <= 4:
            # Chamber 2, 3: Caves
            print('caves')

    def place_entities(self, room, entities):
        max_monsters_per_room = from_dungeon_level([[2, 1], [3, 4], [5, 6]], self.dungeon_level)
        max_plants_per_room = 0
        max_items_per_room = from_dungeon_level([[1, 1], [2, 4]], self.dungeon_level)
        # Get a random number of monsters
        number_of_monsters = randint(0, max_monsters_per_room)
        number_of_plants = randint(0, max_plants_per_room)
        number_of_items = randint(0, max_items_per_room)

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
            'shield': from_dungeon_level([[5, 3], [10, 6]], self.dungeon_level),
            'lightning_scroll': from_dungeon_level([[25, 4]], self.dungeon_level),
            'fireball_scroll': from_dungeon_level([[25, 6]], self.dungeon_level),
            'confusion_scroll': from_dungeon_level([[10, 2]], self.dungeon_level)
        }

        # Place stationary monsters (plants) independent of monster number
        for i in range(number_of_plants):
            # Choose a random location in the room around the edges
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)

            if not any([entity for entity in entities if entity.x == x and entity.y == y]):
                fighter_component = Fighter(hp=10, strength=3, agility=1, vitality=1, intellect=1, perception=1, xp=20)
                ai_component = Stationary()
                monster = Entity(x, y, 'V', libtcod.light_grey, 'Whip Vine', blocks=True,
                                 render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component)

                entities.append(monster)

        # Place monsters with random spawning chances
        for i in range(number_of_monsters):
            # Choose a random location in the room
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)

            if not any([entity for entity in entities if entity.x == x and entity.y == y]):
                monster_choice = random_choice_from_dict(monster_chances)

                if monster_choice == 'Wretch':
                    fighter_component = Fighter(hp=10,
                                                damage_dice=1, damage_sides=4,
                                                strength=4, agility=0, vitality=1, intellect=1, perception=1, xp=30)
                    ai_component = Aggressive()
                    monster = Entity(x, y, 'w', libtcod.darker_red, 'Wretch',
                                     'A stunted human wrapped in filthy rags and long since driven feral by the '
                                     'SludgeWorks.',
                                     blocks=True,
                                     render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component)
                elif monster_choice == 'Hunchback':
                    fighter_component = Fighter(hp=20,
                                                damage_dice=2, damage_sides=6,
                                                strength=7, agility=1, vitality=1, intellect=1, perception=1, xp=75)
                    ai_component = Aggressive()
                    monster = Entity(x, y, 'H', libtcod.brass, 'Hunchback',
                                     'A humanoid figure draped in dark, hooded robes. It\'s face is completely '
                                     'concealed and it carries a wicked, curved dagger. It moves with purpose and '
                                     'chants in an ancient, guttural tongue.',
                                     blocks=True,
                                     render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component)
                else:
                    fighter_component = Fighter(hp=50,
                                                damage_dice=3, damage_sides=4,
                                                strength=5, agility=4, vitality=1, intellect=1, perception=1, xp=150)
                    ai_component = Aggressive()
                    monster = Entity(x, y, 'T', libtcod.dark_azure, 'Thresher',
                                     'A colossal ogre-like ape covered in patches of matted hair and littered with '
                                     'scars. This creature tirelessly searches it\'s surroundings for new objects to '
                                     'smash together with a joyous, childlike expression.',
                                     blocks=True,
                                     fighter=fighter_component,
                                     render_order=RenderOrder.ACTOR, ai=ai_component)

                entities.append(monster)

        # Place items
        equipment = 0
        for i in range(number_of_items):
            x = randint(room.x1 + 1, room.x2 - 1)
            y = randint(room.y1 + 1, room.y2 - 1)

            if not any([entity for entity in entities if entity.x == x and entity.y == y]):
                item_choice = random_choice_from_dict(item_chances)

                # Weapons and armour
                if item_choice == 'sword' and equipment <= 3:
                    equippable_component = Equippable(EquipmentSlots.MAIN_HAND,
                                                      damage_dice=1, damage_sides=6,
                                                      strength_bonus=3)
                    item = Entity(x, y, '/', libtcod.sky, 'Sword (1d6)',
                                  'A rusted and dirt-caked longsword. It\'s fairly blunt, but much better than ' +
                                  'nothing. +3 STR [1d6]',
                                  equippable=equippable_component)
                    equipment = equipment + 1
                elif item_choice == 'shield' and equipment <= 3:
                    equippable_component = Equippable(EquipmentSlots.OFF_HAND, agility_bonus=1)
                    item = Entity(x, y, '[', libtcod.darker_orange, 'Shield',
                                  'A small buckler that can be attached to the arm and used to deflect attacks.',
                                  equippable=equippable_component)
                    equipment = equipment + 1
                elif item_choice == 'helm' and equipment <= 3:
                    equippable_component = Equippable(EquipmentSlots.HEAD, agility_bonus=1)
                    item = Entity(x, y, '[', libtcod.darker_orange, 'Helm',
                                  'A leather helmet designed to help minimise head wounds. +1 AGI',
                                  equippable=equippable_component)
                    equipment = equipment + 1

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
                                  ' damage to all creatures within ' + str(fireball_range) + 'tiles.'
                                  , render_order=RenderOrder.ITEM,
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

    def create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False

    def rooms_chamber(self, max_rooms, min_room_size, max_room_size, map_width, map_height, player, entities):
        # A chamber which is filled with rectangular rooms of random sizes, joined with single-jointed corridors.
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

                self.place_entities(new_room, entities)
                rooms.append(new_room)
                num_rooms += 1

        stairs_component = Stairs(self.dungeon_level + 1)
        down_stairs = Entity(center_of_last_room_x, center_of_last_room_y, '>', libtcod.white, 'Stairs',
                             'There\'s a dark chasm here which will allow you to take a one-way trip to'
                             'the next chamber of the SludgeWorks.',
                             render_order=RenderOrder.STAIRS, stairs=stairs_component)
        entities.append(down_stairs)


class Tile:
    def __init__(self, blocked, block_sight=None):
        self.blocked = blocked

        # By default, if a tile is blocked, it also blocks sight
        if block_sight is None:
            block_sight = blocked

        self.block_sight = block_sight

        # Change this if you wish to see everything!
        self.explored = True


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
