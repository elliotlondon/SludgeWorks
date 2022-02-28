from enum import Enum, auto
from random import Random, choice
from engine.game_states import GameStates
from gui.menus import *
from gui.game_messages import Message


class RenderOrder(Enum):
    CORPSE = auto()
    ITEM = auto()
    STAIRS = auto()
    PLANT = auto()
    ACTOR = auto()


def get_names_under_mouse(mouse, entities, fov_map):
    (x, y) = (mouse.cx, mouse.cy)

    names = [entity.name for entity in entities
             if entity.x == x and entity.y == y and libtcod.map_is_in_fov(fov_map, entity.x, entity.y)]
    names = ', '.join(names)

    return names.capitalize()


def get_names_under_char(player, entities, fov_map):
    (x, y) = (player.x, player.y)

    names = [entity.name for entity in entities
             if entity.x == x and entity.y == y and libtcod.map_is_in_fov(fov_map, entity.x, entity.y)
             and entity.name != 'Player']
    names = ', '.join(names)

    return names.capitalize()


def get_names_at_look(look_cursor, entities, fov_map):
    (x, y) = (look_cursor.x, look_cursor.y)

    names = [entity.name for entity in entities if entity.x == x and entity.y == y
             and libtcod.map_is_in_fov(fov_map, entity.x, entity.y)]
    names = ', '.join(names)

    return names.capitalize()


def render_bar(panel, x, y, total_width, name, value, maximum, bar_colour, back_colour):
    bar_width = int(float(value) / maximum * total_width)

    libtcod.console_set_default_background(panel, back_colour)
    libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_OVERLAY)

    libtcod.console_set_default_background(panel, bar_colour)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)

    libtcod.console_set_default_foreground(panel, libtcod.white)
    libtcod.console_print_ex(panel, int(total_width / 2), y, libtcod.BKGND_NONE, libtcod.CENTER,
                             '{0}: {1}/{2}'.format(name, value, maximum))


def render_all(con, panel, hp_bar, xp_bar, entities, player, game_map, fov_map, message_log, root_width, root_height,
               game_window_width, game_window_height, panel_width, panel_height, stat_bar_width,
               stat_bar_height, fx_panel_width, fx_panel_height, camera_width, camera_height, game_state, turn_number):
    seed = Random(1337)  # Randomise randint to prevent d&d roll changes

    # Render the game window area
    camera_x, camera_y = move_camera(player, game_map, game_window_width, game_window_height)
    if game_map.width < game_window_width:
        camera_x = 0
        camera_width = game_map.width
    if game_map.height < game_window_height:
        camera_y = 0
        camera_height = game_map.height
    for y in range(camera_height):
        for x in range(camera_width):
            map_x = int(camera_x + x)
            map_y = int(camera_y + y)

            visible = libtcod.map_is_in_fov(fov_map, map_x, map_y)
            wall = game_map.tiles[map_x][map_y].block_sight

            # Using randint without seed here causes a 'disco' effect. Great for hallucinations!!!
            floor_char = game_map.floor_chars
            floor_char = floor_char[Random.randint(seed, 0, len(floor_char)-1)]

            if visible:
                if wall:
                    libtcod.console_put_char_ex(con, x, y, ord('▓'.encode('cp437')), game_map.light_wall,
                                               game_map.dark_ground)
                    game_map.tiles[map_x][map_y].explored = True
                else:
                    libtcod.console_put_char_ex(con, x, y, floor_char, game_map.light_ground,
                                                game_map.dark_ground)
                    game_map.tiles[map_x][map_y].explored = True

            elif game_map.tiles[map_x][map_y].explored:
                if wall:
                    libtcod.console_put_char_ex(con, x, y, ord('▒'.encode('cp437')), game_map.dark_wall,
                                                game_map.dark_ground)
                    game_map.tiles[map_x][map_y].blocks_sight = True
                else:
                    libtcod.console_put_char_ex(con, x, y, ord('.'.encode('cp437')), game_map.dark_ground,
                                                game_map.dark_ground)

    # Draw all entities in the list
    entities_in_render_order = sorted(entities, key=lambda z: z.render_order.value)
    for entity in entities_in_render_order:
        if entity.name == 'Moire Beast':
            moire_colour = [libtcod.light_grey, libtcod.lighter_grey, libtcod.lightest_gray, libtcod.grey,
                            libtcod.dark_grey,
                            libtcod.darkest_gray]
            entity.colour = choice(moire_colour)
        draw_entity(con, entity, fov_map, game_map, camera_x, camera_y, camera_width, camera_height)

    # Display the selected item
    libtcod.console_set_default_foreground(con, libtcod.white)
    libtcod.console_print_ex(con, 0, game_window_height - 1, libtcod.BKGND_NONE, libtcod.LEFT,
                             get_names_under_char(player, entities, fov_map))
    libtcod.console_blit(con, 0, 0, root_width, root_height, con, 0, 0)

    # Render all of the panels here
    panel.clear(fg=(255, 255, 255))
    hp_bar.clear(fg=(255, 255, 255))
    xp_bar.clear(fg=(255, 255, 255))

    # Print the game messages, one line at a time
    y = 0   # Start at zero for no empty space between message log and HP/XP bars.
    for message in message_log.messages:
        libtcod.console_set_default_foreground(panel, message.colour)
        libtcod.console_print_ex(panel, message_log.x, y, libtcod.BKGND_NONE, libtcod.LEFT, message.text)
        y += 1

    libtcod.console_blit(panel, 0, 0, panel_width, panel_height, con, 0, root_height - panel_height)

    # HP bar
    render_bar(hp_bar, 0, 0, stat_bar_width, 'HP', player.fighter.current_hp, player.fighter.max_hp,
               libtcod.light_red, libtcod.darkest_red)
    libtcod.console_blit(hp_bar, 0, 0, stat_bar_width, stat_bar_height, con, 0, root_height - panel_height - 2)

    # XP bar
    render_bar(xp_bar, 0, 0, stat_bar_width, 'XP', player.level.current_xp, player.level.experience_to_next_level,
               libtcod.amber, libtcod.black)
    libtcod.console_blit(xp_bar, 0, 0, stat_bar_width, stat_bar_height, con, 0, root_height - panel_height - 1)

    if game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
        if game_state == GameStates.SHOW_INVENTORY:
            inventory_title = 'Press the key next to an item to use it, or Esc to cancel.\n'
        else:
            inventory_title = 'Press the key next to an item to drop it, or Esc to cancel.\n'
        inventory_menu(con, inventory_title, player, 50, game_window_width, game_window_height)

    if game_state == GameStates.SHOW_LOADOUT:
        loadout_title = 'EQUIPMENT. Press the key next to an item to use it, or Esc to cancel.\n'
        loadout_menu(con, loadout_title, player, 50, game_window_width, game_window_height)

    elif game_state == GameStates.LEVEL_UP:
        level_up_menu(con, 'Choose a stat to increase:', player, 50, game_window_width, game_window_height)
    elif game_state == GameStates.CHARACTER_SCREEN:
        character_screen(con, player, 30, 15, game_window_width, game_window_height)
    elif game_state == GameStates.ABILITY_SCREEN:
        ability_screen(con, player, 30, 10, game_window_width, game_window_height)
    elif game_state == GameStates.ESC_MENU:
        esc_menu(con, 40, 10, root_width, root_height, turn_number)
    elif game_state == GameStates.HELP_MENU:
        help_menu(con, root_width, root_height, root_width, root_height)


def clear_all(con, entities):
    for entity in entities:
        clear_entity(con, entity)


def move_camera(player, game_map, game_window_width, game_window_height):
    if player.x < int(game_window_width / 2):
        camera_x = 0
    elif player.x >= game_map.width - int(game_window_width / 2):
        camera_x = game_map.width - game_window_width
    else:
        camera_x = player.x - game_window_width / 2

    if player.y < game_window_height / 2:
        camera_y = 0
    elif player.y >= game_map.height - int(game_window_height / 2):
        camera_y = game_map.height - game_window_height
    else:
        camera_y = player.y - int(game_window_height / 2)

    return camera_x, camera_y


def to_camera_coordinates(x, y, camera_x, camera_y, camera_width, camera_height):
    x = int(x - camera_x)
    y = int(y - camera_y)

    if x < 0 or y < 0 or x >= camera_width or y >= camera_height:
        return None, None

    return x, y


def draw_entity(con, entity, fov_map, game_map, camera_x, camera_y, camera_width, camera_height):
    if libtcod.map_is_in_fov(fov_map, entity.x, entity.y) or (entity.stairs and
                                                              game_map.tiles[entity.x][entity.y].explored):
        x, y = to_camera_coordinates(entity.x, entity.y, camera_x, camera_y, camera_width, camera_height)
        if x is not None and y is not None:
            libtcod.console_set_default_foreground(con, entity.colour)
            libtcod.console_put_char(con, x, y, entity.char, libtcod.BKGND_NONE)


def clear_entity(con, entity):
    libtcod.console_put_char(con, entity.x, entity.y, ' ', libtcod.BKGND_NONE)


def entity_in_fov(entities, fov_map):
    for entity in entities:
        if entity.ai and entity.name != 'Player' \
                and not entity.fighter.damage_dice == 0:
            if libtcod.map_is_in_fov(fov_map, entity.x, entity.y):
                return True
    return False


def entities_in_fov(entities, fov_map, message_log):
    seen_monsters = []
    for entity in entities:
        if entity.ai and entity.name != 'Player' \
                and not entity.fighter.damage_dice == 0:    # Harmless enemies do not interrupt continuous actions
            if libtcod.map_is_in_fov(fov_map, entity.x, entity.y):
                seen_monsters.append(entity.name)
                message_log.add_message(Message('You spot a {0} and stop your current action.'
                                                .format(seen_monsters[0]), libtcod.yellow))
                return True
    return False
