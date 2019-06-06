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

    # Define the size for the game window as a whole
    root_width = 80
    root_height = 48

    # Define the size of the stat bar (HP and XP)
    stat_bar_width = root_width
    stat_bar_height = 1

    # Define the size of the comments panel
    comments_width = 50
    comments_height = 8
    comments_x = root_width - comments_width

    # Define the size of the status effects panel
    fx_panel_width = root_width - comments_width
    fx_panel_height = comments_height

    # Define the size of all of the combined panels
    panel_width = root_width
    panel_height = comments_height

    # Define the size of the game_window area of the root console
    game_window_width = root_width
    game_window_height = root_height - panel_height - 2*stat_bar_height

    # Camera width and height should be identical to the game window size
    camera_width = game_window_width
    camera_height = game_window_height

    # TODO: Have this change depending upon what the dungeon level is and the dungeon level structure
    map_width = 80
    map_height = 42

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
        'root_width': root_width,
        'root_height': root_height,
        'game_window_width': game_window_width,
        'game_window_height': game_window_height,
        'panel_width': panel_width,
        'panel_height': panel_height,
        'stat_bar_width': stat_bar_width,
        'stat_bar_height': stat_bar_height,
        'comments_width': comments_width,
        'comments_height': comments_height,
        'comments_x': comments_x,
        'fx_panel_width': fx_panel_width,
        'fx_panel_height': fx_panel_height,
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

    message_log = MessageLog(constants['comments_x'], constants['comments_width'], constants['comments_height'])

    game_state = GameStates.PLAYERS_TURN

    return player, entities, game_map, message_log, game_state
