from __future__ import annotations

from typing import Tuple, TYPE_CHECKING

import config.colour

if TYPE_CHECKING:
    from tcod import Console
    from core.engine import Engine
    from maps.game_map import SimpleGameMap

from enum import Enum, auto
from random import Random

from core.game_states import GameStates
from gui.menus import *


class RenderOrder(Enum):
    CORPSE = auto()
    ITEM = auto()
    STAIRS = auto()
    PLANT = auto()
    ACTOR = auto()


def render_bar(console: Console, current_value: int, max_value: int, text: str,
               x: int, y: int, total_width: int, bg_empty: Tuple[int, int, int], bg_full: Tuple[int, int, int]) -> None:
    if current_value > max_value:
        bar_width = total_width
    else:
        bar_width = int(float(current_value) / max_value * total_width)

    console.draw_rect(x=x - 1, y=y, width=total_width, height=1, ch=1, bg=bg_empty)

    if bar_width > 0:
        console.draw_rect(x=x - 1, y=y, width=bar_width, height=1, ch=1, bg=bg_full)

    console.print(x=x, y=y, string=text, fg=config.colour.bar_text)


def render_dungeon_level(console: Console, dungeon_level: int, location: Tuple[int, int]) -> None:
    """
    Render the level the player is currently on, at the given location.
    """
    x, y = location

    console.print(x=x, y=y, string=f"Dungeon level: {dungeon_level}")


def render_names_at_mouse_location(console: Console, x: int, y: int, engine: Engine) -> None:
    mouse_x, mouse_y = engine.mouse_location

    names_at_mouse_location = get_names_at_location(x=mouse_x, y=mouse_y, game_map=engine.game_map)

    console.print(x=x, y=y, string=names_at_mouse_location)


def get_names_at_location(x: int, y: int, game_map: SimpleGameMap) -> str:
    if not game_map.in_bounds(x, y) or not game_map.visible[x, y]:
        return ""

    names = ", ".join(entity.name for entity in game_map.entities if entity.x == x and entity.y == y)

    return names.capitalize()


# def get_names_under_mouse(mouse, entities, fov_map):
#     (x, y) = (mouse.cx, mouse.cy)
#
#     names = [entity.name for entity in entities
#              if entity.x == x and entity.y == y and tcod.map_is_in_fov(fov_map, entity.x, entity.y)]
#     names = ', '.join(names)
#
#     return names.capitalize()
#
#
# def get_names_under_char(player, entities, fov_map):
#     (x, y) = (player.x, player.y)
#
#     names = [entity.name for entity in entities
#              if entity.x == x and entity.y == y and tcod.map_is_in_fov(fov_map, entity.x, entity.y)
#              and entity.name != 'Player']
#     names = ', '.join(names)
#
#     return names.capitalize()
#
#
# def render_bar(panel, x, y, total_width, name, value, maximum, bar_colour, back_colour):
#     bar_width = int(float(value) / maximum * total_width)
#
#     tcod.console_set_default_background(panel, back_colour)
#     tcod.console_rect(panel, x, y, total_width, 1, False, tcod.BKGND_OVERLAY)
#
#     tcod.console_set_default_background(panel, bar_colour)
#     if bar_width > 0:
#         tcod.console_rect(panel, x, y, bar_width, 1, False, tcod.BKGND_SCREEN)
#
#     tcod.console_set_default_foreground(panel, tcod.white)
#     tcod.console_print_ex(panel, int(total_width / 2), y, tcod.BKGND_NONE, tcod.CENTER,
#                              '{0}: {1}/{2}'.format(name, value, maximum))


def render_all(con, panel, player, entities, game_map, message_log, hp_bar, xp_bar, fov_map, root_width, root_height,
               game_window_width, game_window_height, panel_width, panel_height, stat_bar_width, stat_bar_height,
               fx_panel_width, fx_panel_height, camera_width, camera_height):
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

            visible = tcod.map_is_in_fov(fov_map, map_x, map_y)
            wall = game_map.tiles[map_x][map_y].block_sight

            # Using randint without seed here causes a 'disco' effect. Great for hallucinations!!!
            floor_char = game_map.floor_chars
            floor_char = floor_char[Random.randint(seed, 0, len(floor_char) - 1)]

            if visible:
                if wall:
                    tcod.console_put_char_ex(con, x, y, ord('▓'.encode('cp437')), game_map.light_wall,
                                             game_map.dark_ground)
                    game_map.tiles[map_x][map_y].explored = True
                else:
                    tcod.console_put_char_ex(con, x, y, floor_char, game_map.light_ground,
                                             game_map.dark_ground)
                    game_map.tiles[map_x][map_y].explored = True

            elif game_map.tiles[map_x][map_y].explored:
                if wall:
                    tcod.console_put_char_ex(con, x, y, ord('▒'.encode('cp437')), game_map.dark_wall,
                                             game_map.dark_ground)
                    game_map.tiles[map_x][map_y].blocks_sight = True
                else:
                    tcod.console_put_char_ex(con, x, y, ord('.'.encode('cp437')), game_map.dark_ground,
                                             game_map.dark_ground)

    # Draw all entities in the list
    # entities_in_render_order = sorted(entities, key=lambda z: z.render_order.value)
    # draw_entity(con, entity, fov_map, game_map, camera_x, camera_y, camera_width, camera_height)

    # Display the selected item
    tcod.console_set_default_foreground(con, tcod.white)
    # tcod.console_print_ex(con, 0, game_window_height - 1, tcod.BKGND_NONE, tcod.LEFT,
    #                          get_names_under_char(player, entities, fov_map))
    tcod.console_blit(con, 0, 0, root_width, root_height, con, 0, 0)

    # Render all of the panels here
    panel.clear(fg=(255, 255, 255))
    hp_bar.clear(fg=(255, 255, 255))
    xp_bar.clear(fg=(255, 255, 255))

    # Print the game messages, one line at a time
    y = 0  # Start at zero for no empty space between message log and HP/XP bars.
    for message in message_log.messages:
        tcod.console_set_default_foreground(panel, message.colour)
        tcod.console_print_ex(panel, message_log.x, y, tcod.BKGND_NONE, tcod.LEFT, message.text)
        y += 1

    tcod.console_blit(panel, 0, 0, panel_width, panel_height, con, 0, root_height - panel_height)

    if GameStates.current_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
        if GameStates.current_state == GameStates.SHOW_INVENTORY:
            inventory_title = 'Press the key next to an item to use it, or Esc to cancel.\n'
        else:
            inventory_title = 'Press the key next to an item to drop it, or Esc to cancel.\n'
        inventory_menu(con, inventory_title, player, 50, game_window_width, game_window_height)

    if GameStates.current_state == GameStates.SHOW_LOADOUT:
        loadout_title = 'EQUIPMENT. Press the key next to an item to use it, or Esc to cancel.\n'
        loadout_menu(con, loadout_title, player, 50, game_window_width, game_window_height)
    elif GameStates.current_state == GameStates.LEVEL_UP:
        level_up_menu(con, 'Choose a stat to increase:', player, 50, game_window_width, game_window_height)
    elif GameStates.current_state == GameStates.CHARACTER_SCREEN:
        character_screen(con, player, 30, 15, game_window_width, game_window_height)
    elif GameStates.current_state == GameStates.ABILITY_SCREEN:
        ability_screen(con, player, 30, 10, game_window_width, game_window_height)
    elif GameStates.current_state == GameStates.ESC_MENU:
        esc_menu(con, 40, 10, root_width, root_height, player.turn_number)
    elif GameStates.current_state == GameStates.HELP_MENU:
        help_menu(con, root_width, root_height, root_width, root_height)

# TODO: Implement movable screen depending upon map size
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
