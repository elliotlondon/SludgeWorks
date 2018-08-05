import libtcodpy as libtcod

from components.equipment import Equipment, Equippable
from components.fighter import Fighter
from components.inventory import Inventory
from components.level import Level
from entity import Entity
from equipment_slots import EquipmentSlots
from game_messages import MessageLog
from game_states import GameStates
from game_map import GameMap
from render_functions import RenderOrder


def get_constants():
    window_title = 'sludgeWorks'

    screen_width = 80
    screen_height = 50

    bar_width = int(screen_width / 4)
    panel_height = round(screen_height / 8)
    panel_y = screen_height - panel_height

    message_x = int(bar_width + 2)
    message_width = screen_width - bar_width - 2
    message_height = panel_height - 1

    map_width = int(screen_width)
    map_height = int(screen_height - panel_height)

    fov_algorithm = 0
    fov_light_walls = True
    fov_radius = 10

    max_monsters_per_room = 4
    max_items_per_room = 2

    colours = {
        'dark_wall': libtcod.dark_grey,
        'light_wall': libtcod.Color(150, 100, 50),
        'dark_ground': libtcod.black,
        'light_ground': libtcod.dark_grey,
    }

    constants = {
        'window_title': window_title,
        'screen_width': screen_width,
        'screen_height': screen_height,
        'bar_width': bar_width,
        'panel_height': panel_height,
        'panel_y': panel_y,
        'message_x': message_x,
        'message_width': message_width,
        'message_height': message_height,
        'map_width': map_width,
        'map_height': map_height,
        'fov_algorithm': fov_algorithm,
        'fov_light_walls': fov_light_walls,
        'fov_radius': fov_radius,
        'max_monsters_per_room': max_monsters_per_room,
        'max_items_per_room': max_items_per_room,
        'colours': colours
    }

    return constants


def get_game_variables(constants):
    fighter_component = Fighter(hp=100,
                                damage_dice=1, damage_sides=2,
                                strength=1, agility=1, vitality=1, intellect=1, perception=1)
    inventory_component = Inventory(26)
    level_component = Level()
    slot = ()
    equipment_component = Equipment(slot)
    player = Entity(0, 0, ord('@'.encode('cp437')), libtcod.white, 'Player', 'This is you.', blocks=True,
                    render_order=RenderOrder.ACTOR, fighter=fighter_component, inventory=inventory_component,
                    level=level_component, equipment=equipment_component)
    entities = [player]

    equippable_component = Equippable(EquipmentSlots.MAIN_HAND,
                                      damage_dice=1, damage_sides=4,
                                      strength_bonus=2)
    dagger = Entity(0, 0, '-', libtcod.sky,
                    'Dagger (1d4)', 'A short blade ideal for swift stabbing attacks. ' + '+2 STR, [1d4]',
                    equippable=equippable_component)
    player.inventory.add_item(dagger)
    player.equipment.toggle_equip(dagger)

    game_map = GameMap(constants['map_width'], constants['map_height'])
    game_map.make_map(constants['map_width'], constants['map_height'], player, entities)

    message_log = MessageLog(constants['message_x'], constants['message_width'], constants['message_height'])

    game_state = GameStates.PLAYERS_TURN

    return player, entities, game_map, message_log, game_state
