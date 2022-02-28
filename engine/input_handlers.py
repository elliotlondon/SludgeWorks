import tcod as libtcod
from engine.game_states import GameStates


def handle_keys(key, game_state):
    if game_state == GameStates.PLAYERS_TURN:
        return handle_player_turn_keys(key)
    elif game_state == GameStates.PLAYER_DEAD:
        return handle_player_dead_keys(key)
    elif game_state == GameStates.TARGETING:
        return handle_targeting_keys(key)
    elif game_state in (GameStates.SHOW_INVENTORY, GameStates.DROP_INVENTORY):
        return handle_inventory_keys(key)
    elif game_state == GameStates.SHOW_LOADOUT:
        return handle_loadout_keys(key)
    elif game_state == GameStates.LOOK:
        return handle_look_screen_keys(key)
    elif game_state == GameStates.LEVEL_UP:
        return handle_level_up_menu(key)
    elif game_state == GameStates.CHARACTER_SCREEN or game_state == GameStates.ABILITY_SCREEN:
        return handle_character_screen(key)
    elif game_state == GameStates.ESC_MENU:
        return handle_esc_menu_keys(key)
    elif game_state == GameStates.HELP_MENU:
        return handle_help_menu_keys(key)
    return {}


def handle_targeting_keys(key):
    if key.vk == libtcod.KEY_ESCAPE:
        return {'exit': True}
    if key.vk == libtcod.KEY_F11:
        return {'fullscreen': True}
    return {}


def handle_player_turn_keys(key):
    key_char = chr(key.c)

    # Movement keys
    if key.vk == libtcod.KEY_UP or key_char == 'k':
        return {'move': (0, -1)}
    elif key.vk == libtcod.KEY_DOWN or key_char == 'j':
        return {'move': (0, 1)}
    elif key.vk == libtcod.KEY_LEFT or key_char == 'h':
        return {'move': (-1, 0)}
    elif key.vk == libtcod.KEY_RIGHT or key_char == 'l':
        return {'move': (1, 0)}
    elif key_char == 'y':
        return {'move': (-1, -1)}
    elif key_char == 'u':
        return {'move': (1, -1)}
    elif key_char == 'b':
        return {'move': (-1, 1)}
    elif key_char == 'n':
        return {'move': (1, 1)}
    elif key_char == '.':
        return {'wait': True}
    elif key_char == ';':
        return {'rest': True}
    elif key_char == '#':
        return {'auto_explore': True}

    if key_char == 'g':
        return {'pickup': True}
    elif key_char == 'i':
        return {'show_inventory': True}
    elif key_char == 'e':
        return {'show_loadout': True}
    elif key_char == 'd':
        return {'drop_inventory': True}
    elif key_char == 'c':
        return {'show_character_screen': True}
    elif key_char == 'a':
        return {'show_ability_screen': True}
    elif key_char == 'e':
        return {'show_look_screen': True}

    elif key.vk == libtcod.KEY_TEXT:
        ch = key.text
        if ch == '>':
            return {'take_stairs': True}

    if key.vk == libtcod.KEY_F11:
        return {'fullscreen': True}
    elif key.vk == libtcod.KEY_ESCAPE:
        return {'esc_menu': True}
    return {}


def handle_inventory_keys(key):
    index = key.c - ord('a')
    if index >= 0:
        return {'inventory_index': index}
    elif key.vk == libtcod.KEY_ESCAPE:
        return {'exit': True}
    if key.vk == libtcod.KEY_F11:
        return {'fullscreen': True}
    return {}


def handle_loadout_keys(key):
    index = key.c - ord('a')
    if index >= 0:
        return {'loadout_index': index}
    elif key.vk == libtcod.KEY_ESCAPE:
        return {'exit': True}
    if key.vk == libtcod.KEY_F11:
        return {'fullscreen': True}
    return {}


def handle_look_screen_keys(key):
    key_char = chr(key.c)
    if key.vk == libtcod.KEY_UP or key_char == 'k':
        return {'look': (0, -1)}
    elif key.vk == libtcod.KEY_DOWN or key_char == 'j':
        return {'look': (0, 1)}
    elif key.vk == libtcod.KEY_LEFT or key_char == 'h':
        return {'look': (-1, 0)}
    elif key.vk == libtcod.KEY_RIGHT or key_char == 'l':
        return {'look': (1, 0)}
    elif key_char == 'y':
        return {'look': (-1, -1)}
    elif key_char == 'u':
        return {'look': (1, -1)}
    elif key_char == 'b':
        return {'look': (-1, 1)}
    elif key_char == 'n':
        return {'look': (1, 1)}

    if key.vk == libtcod.KEY_F11:
        # fullscreen = F11
        return {'fullscreen': True}
    elif key.vk == libtcod.KEY_ESCAPE:
        # Exit the menu
        return {'exit': True}
    return {}


def handle_player_dead_keys(key):
    key_char = chr(key.c)
    if key_char == 'i':
        return {'show_inventory': True}
    elif key.vk == libtcod.KEY_ESCAPE:
        # Exit the menu
        return {'quit': True}
    if key.vk == libtcod.KEY_F11:
        # fullscreen = F11
        return {'fullscreen': True}
    return {}


def handle_main_menu(key):
    key_char = chr(key.c)
    if key_char == 'a':
        return {'new_game': True}
    elif key_char == 'b':
        return {'load_game': True}
    elif key_char == 'c' or key_char == 'q' or key.vk == libtcod.KEY_ESCAPE:
        return {'exit': True}
    if key.vk == libtcod.KEY_F11:
        # fullscreen = F11
        return {'fullscreen': True}
    return {}


def handle_level_up_menu(key):
    if key:
        key_char = chr(key.c)
        if key_char == 'a':
            return {'level_up': 'str'}
        elif key_char == 'b':
            return {'level_up': 'agi'}
    if key.vk == libtcod.KEY_F11:
        return {'fullscreen': True}
    return {}


def handle_character_screen(key):
    if key.vk == libtcod.KEY_ESCAPE:
        return {'exit': True}
    if key.vk == libtcod.KEY_F11:
        return {'fullscreen': True}
    return {}


def handle_esc_menu_keys(key):
    if key:
        key_char = chr(key.c)
        if key_char == 'H' or key_char == 'h' or key_char == 'a':
            return {'help': True}
        if key_char == 'R' or key_char == 'r' or key_char == 'b':
            return {'exit': True}
        if key_char == 'Q' or key_char == 'q' or key_char == 'c':
            return {'quit': True}
    if key.vk == libtcod.KEY_ESCAPE:
        return {'exit': True}
    if key.vk == libtcod.KEY_F11:
        return {'fullscreen': True}
    return {}


def handle_help_menu_keys(key):
    if key.vk == libtcod.KEY_ESCAPE:
        return {'exit': True}
    if key.vk == libtcod.KEY_F11:
        return {'fullscreen': True}
    return {}


def handle_mouse(mouse):
    (x, y) = (mouse.cx, mouse.cy)
    if mouse.lbutton_pressed:
        return {'left_click': (x, y)}
    elif mouse.rbutton_pressed:
        return {'right_click': (x, y)}
    return {}
