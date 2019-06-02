import tcod as libtcod
from equipment import Equipment, Equippable
from fighter import Fighter
from inventory import Inventory
from level import Level
from entity import Entity
from equipment_slots import EquipmentSlots
from game_messages import MessageLog
from game_states import GameStates
from game_map import GameMap
from render_functions import RenderOrder


def get_constants():
    window_title = 'SludgeWorks'

    screen_width = 80
    screen_height = 46

    bar_width = 20
    panel_height = 8
    panel_y = 38

    message_x = 22
    message_width = 58
    message_height = panel_height

    camera_width = screen_width
    camera_height = screen_height

    map_width = 80
    map_height = 80

    fov_algorithm = 0
    fov_light_walls = True
    fov_radius = 5

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
        'camera_width': camera_width,
        'camera_height': camera_height,
        'fov_algorithm': fov_algorithm,
        'fov_light_walls': fov_light_walls,
        'fov_radius': fov_radius,
        'colours': colours
    }

    return constants


def get_game_variables(constants):
    fighter_component = Fighter(current_hp=20, max_hp=20,
                                damage_dice=1, damage_sides=2,
                                strength=12, dexterity=12, vitality=12, intellect=12, perception=12,
                                level=1, armour=0, dodges=True)
    inventory_component = Inventory(26)
    level_component = Level()
    slot = ()
    equipment_component = Equipment(slot)
    player = Entity(0, 0, ord('@'.encode('cp437')), libtcod.white, 'Player', 'This is you.', blocks=True,
                    render_order=RenderOrder.ACTOR, fighter=fighter_component, inventory=inventory_component,
                    level=level_component, equipment=equipment_component)
    entities = [player]

    equippable_component = Equippable(EquipmentSlots.MAIN_HAND,
                                      damage_dice=1, damage_sides=3)
    dagger = Entity(0, 0, '-', libtcod.light_grey,
                    'Iron Dagger', 'A short blade ideal for swift stabbing attacks.',
                    equippable=equippable_component)
    equippable_component = Equippable(EquipmentSlots.TORSO,
                                      armour_bonus=1)
    leather_armour = Entity(0, 0, '-', libtcod.light_grey,
                            'Leather Armour', 'Basic leather armour covering the torso, providing modest protection. '
                                              'This was the best you could find...',
                            equippable=equippable_component)
    player.inventory.add_item(dagger)
    player.inventory.add_item(leather_armour)
    player.equipment.toggle_equip(dagger)
    player.equipment.toggle_equip(leather_armour)

    game_map = GameMap(constants['map_width'], constants['map_height'])
    game_map.make_map(constants['map_width'], constants['map_height'], player, entities)

    message_log = MessageLog(constants['message_x'], constants['message_width'], constants['message_height'])

    game_state = GameStates.PLAYERS_TURN

    return player, entities, game_map, message_log, game_state
