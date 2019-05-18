from enum import Enum, auto
from random import Random
from game_states import GameStates
from menus import *


class RenderOrder(Enum):
    STAIRS = auto()
    CORPSE = auto()
    ITEM = auto()
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


def render_bar(panel, x, y, total_width, name, value, maximum, bar_colour, back_colour):
    bar_width = int(float(value) / maximum * total_width)

    libtcod.console_set_default_background(panel, back_colour)
    libtcod.console_rect(panel, x, y, total_width, 1, False, libtcod.BKGND_SCREEN)

    libtcod.console_set_default_background(panel, bar_colour)
    if bar_width > 0:
        libtcod.console_rect(panel, x, y, bar_width, 1, False, libtcod.BKGND_SCREEN)

    libtcod.console_set_default_foreground(panel, libtcod.white)
    libtcod.console_print_ex(panel, int(x + total_width / 2), y, libtcod.BKGND_NONE, libtcod.CENTER,
                             '{0}: {1}/{2}'.format(name, value, maximum))


def render_all(con, panel, entities, player, game_map, fov_map, fov_recompute, message_log, screen_width, screen_height,
               bar_width, panel_height, panel_y, colours, game_state):
    seed = Random(1337)  # Randomise randint yourself to prevent d&d roll changes
    if fov_recompute:
        for y in range(game_map.height):
            for x in range(game_map.width):
                visible = libtcod.map_is_in_fov(fov_map, x, y)
                wall = game_map.tiles[x][y].block_sight

                # Using randint without seed here causes a 'disco' effect. Great for hallucinations!!!
                floor_char = [' ', '.', ',', '`']
                floor_char = floor_char[Random.randint(seed, 0, len(floor_char)-1)]

                if visible:
                    if wall:
                        libtcod.console_put_char_ex(con, x, y, ord('▓'.encode('cp437')), colours.get('light_wall'),
                                                    colours.get('dark_ground'))
                        game_map.tiles[x][y].explored = True

                    else:
                        libtcod.console_put_char_ex(con, x, y, floor_char, colours.get('light_ground'),
                                                    colours.get('dark_ground'))
                        game_map.tiles[x][y].explored = True

                elif game_map.tiles[x][y].explored:
                    if wall:
                        libtcod.console_put_char_ex(con, x, y, ord('▒'.encode('cp437')), colours.get('dark_wall'),
                                                    colours.get('dark_ground'))
                    else:
                        libtcod.console_put_char_ex(con, x, y, ord('.'.encode('cp437')), colours.get('dark_ground'),
                                                    colours.get('dark_ground'))

    entities_in_render_order = sorted(entities, key=lambda z: z.render_order.value)

    # Draw all entities in the list
    for entity in entities_in_render_order:
        draw_entity(con, entity, fov_map, game_map)

    libtcod.console_set_default_foreground(con, libtcod.white)
    libtcod.console_print_ex(con, 1, screen_height - 2, libtcod.BKGND_NONE, libtcod.LEFT,
                             'HP: {0:02}/{1:02}'.format(player.fighter.current_hp, player.fighter.max_hp))

    libtcod.console_blit(con, 0, 0, screen_width, screen_height, con, 0, 0)

    libtcod.console_set_default_background(panel, libtcod.black)
    panel.clear(fg=(255, 255, 63))

    # Print the game messages, one line at a time
    y = 1
    for message in message_log.messages:
        libtcod.console_set_default_foreground(panel, message.colour)
        libtcod.console_print_ex(panel, message_log.x, y, libtcod.BKGND_NONE, libtcod.LEFT, message.text)
        y += 1

    render_bar(panel, 1, 1, bar_width, 'HP', player.fighter.current_hp, player.fighter.max_hp,
               libtcod.light_red, libtcod.darker_red)

    libtcod.console_set_default_foreground(panel, libtcod.light_gray)
    libtcod.console_print_ex(panel, 1, 0, libtcod.BKGND_NONE, libtcod.LEFT,
                             get_names_under_char(player, entities, fov_map))

    libtcod.console_blit(panel, 0, 0, screen_width, panel_height, con, 0, panel_y)

    if game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
        if game_state == GameStates.SHOW_INVENTORY:
            inventory_title = 'Press the key next to an item to use it, or Esc to cancel.\n'
        else:
            inventory_title = 'Press the key next to an item to drop it, or Esc to cancel.\n'

        inventory_menu(con, inventory_title, player, 50, screen_width, screen_height)

    elif game_state == GameStates.LEVEL_UP:
        level_up_menu(con, 'Choose a stat to increase:', player, 40, screen_width, screen_height)

    elif game_state == GameStates.CHARACTER_SCREEN:
        character_screen(con, player, 30, 10, screen_width, screen_height)

    elif game_state == GameStates.ESC_MENU:
        esc_menu(con, 40, 10, screen_width, screen_height)

    elif game_state == GameStates.HELP_MENU:
        help_menu(con, 50, 10, screen_width, screen_height)


def clear_all(con, entities):
    for entity in entities:
        clear_entity(con, entity)


def draw_entity(con, entity, fov_map, game_map):
    if libtcod.map_is_in_fov(fov_map, entity.x, entity.y) or (entity.stairs and
                                                              game_map.tiles[entity.x][entity.y].explored):
        libtcod.console_set_default_foreground(con, entity.colour)
        libtcod.console_put_char(con, entity.x, entity.y, entity.char, libtcod.BKGND_NONE)


def clear_entity(con, entity):
    libtcod.console_put_char(con, entity.x, entity.y, ' ', libtcod.BKGND_NONE)
