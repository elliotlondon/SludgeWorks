import tcod as libtcod
from lib.equipment import Equipment, Equippable
from lib.fighter import Fighter
from lib.inventory import Inventory
from maps.level import Level
from lib.entity import Entity
from lib.equipment_slots import EquipmentSlots
from gui.game_messages import MessageLog
from engine.game_states import GameStates
from maps.game_map import GameMap
from engine.render_functions import RenderOrder


def get_constants():
    window_title = 'SludgeWorks'

    # Define the size for the game window as a whole
    root_width = 72
    root_height = 45

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

    map_width = game_window_width
    map_height = game_window_height

    fov_algorithm = 0
    fov_light_walls = True
    fov_radius = 5

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
        'fov_radius': fov_radius
    }
    return constants


def get_game_variables(constants):
    fighter = Fighter(current_hp=20, max_hp=20,
                      damage_dice=1, damage_sides=2,
                      strength=12, dexterity=12, vitality=12, intellect=12, perception=12,
                      level=1, armour=0, dodges=True)
    inventory = Inventory(26)
    level = Level()
    slot = ()
    equipment = Equipment(slot)
    player = Entity(0, 0, ord('@'.encode('cp437')), libtcod.white, 'Player', 'This is you.', blocks=True,
                    render_order=RenderOrder.ACTOR, fighter=fighter, inventory=inventory,
                    level=level, equipment=equipment)
    entities = [player]

    equippable = Equippable(EquipmentSlots.Main_Hand,
                            damage_dice=1, damage_sides=3)
    dagger = Entity(0, 0, '-', libtcod.light_grey,
                    'Iron Dagger', 'A short blade ideal for swift stabbing attacks.',
                    equippable=equippable)
    equippable = Equippable(EquipmentSlots.Torso,
                            armour_bonus=1)
    leather_armour = Entity(0, 0, '-', libtcod.light_grey,
                            'Leather Armour', 'Basic leather armour covering the torso, providing modest protection. '
                                              'This was the best you could find...',
                            equippable=equippable)
    player.inventory.spawn_with(player, dagger)
    player.inventory.spawn_with(player, leather_armour)

    # Create the first floor map
    game_map = GameMap('near_surface', constants['map_width'], constants['map_height'])
    game_map.make_map(player, entities)
    game_map.place_entities(constants['map_width'], constants['map_height'], entities)

    message_log = MessageLog(constants['comments_x'], constants['comments_width'], constants['comments_height'])
    game_state = GameStates.PLAYERS_TURN
    return player, entities, game_map, message_log, game_state
