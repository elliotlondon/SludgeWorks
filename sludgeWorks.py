import custrender
from random import randint
from death_functions import kill_monster, kill_player
from entity import get_blocking_entities_at_location
from fov_functions import *
from game_messages import Message
from game_states import GameStates
from game_map import GameMap
from input_handlers import handle_keys, handle_mouse, handle_main_menu
from initialise_new_game import get_constants, get_game_variables
from data_loaders import load_game, save_game
from menus import main_menu, message_box
from render_functions import clear_all, render_all, entity_in_fov, entities_in_fov


def main():
    libtcod.sys_set_fps(60)
    constants = get_constants()

    player = None
    entities = []
    game_map = None
    message_log = None
    game_state = None
    show_main_menu = True
    show_load_error_message = False

    key = libtcod.Key()
    mouse = libtcod.Mouse()

    libtcod.console_set_custom_font('Fonts/terminal8x8_gs_ro.png', libtcod.FONT_TYPE_GRAYSCALE |
                                    libtcod.FONT_LAYOUT_ASCII_INROW)
    panel = libtcod.console.Console(constants['screen_width'], constants['panel_height'])
    main_menu_background_image = libtcod.image_load('sludge2.png')

    with libtcod.console_init_root(constants['screen_width'], constants['screen_height'],
                                   constants['window_title'], True, libtcod.RENDERER_SDL2) as root_console:
        while True:
            libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)

            if show_main_menu:
                main_menu(root_console, main_menu_background_image, constants['screen_width'],
                          constants['screen_height'])

                if show_load_error_message:
                    message_box(root_console, 'No save game to load', 50, constants['screen_width'],
                                constants['screen_height'])

                custrender.clear((0, 0, 0))
                custrender.accumulate(root_console, custrender.get_viewport(root_console, True, True))
                custrender.present()
                root_console.clear(fg=(255, 255, 255))

                action = handle_main_menu(key)

                new_game = action.get('new_game')
                load_saved_game = action.get('load_game')
                exit_game = action.get('exit')

                if show_load_error_message and (new_game or load_saved_game or exit_game):
                    show_load_error_message = False
                elif new_game:
                    player, entities, game_map, message_log, game_state = get_game_variables(constants)
                    game_state = GameStates.PLAYERS_TURN

                    show_main_menu = False
                elif load_saved_game:
                    try:
                        player, entities, game_map, message_log, game_state = load_game()
                        show_main_menu = False
                    except FileNotFoundError:
                        show_load_error_message = True
                elif exit_game:
                    break

            else:
                root_console.clear(fg=(255, 255, 255))
                play_game(player, entities, game_map, message_log, game_state, root_console, panel, constants)

                show_main_menu = True


def play_game(player, entities, game_map, message_log, game_state, root_console, panel, constants):
    root_console.clear(fg=(255, 255, 255))
    fov_recompute = True

    fov_map = initialize_fov(game_map)

    key = libtcod.Key()
    mouse = libtcod.Mouse()

    game_state = GameStates.PLAYERS_TURN
    turn_number = 0
    previous_game_state = game_state

    targeting_item = None
    exploring = False

    while True:
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)

        if fov_recompute:
            recompute_fov(fov_map, player.x, player.y, constants['fov_radius'], constants['fov_light_walls'],
                          constants['fov_algorithm'])

        render_all(root_console, panel, entities, player, game_map, fov_map, fov_recompute, message_log,
                   constants['screen_width'], constants['screen_height'], constants['bar_width'],
                   constants['panel_height'], constants['panel_y'], constants['colours'], game_state, turn_number)

        fov_recompute = False
        custrender.clear((0, 0, 0))
        custrender.accumulate(root_console, custrender.get_viewport(root_console, True, True))
        custrender.present()
        clear_all(root_console, entities)

        action = handle_keys(key, game_state)
        mouse_action = handle_mouse(mouse)

        move = action.get('move')
        wait = action.get('wait')
        rest = action.get('rest')
        pickup = action.get('pickup')
        show_inventory = action.get('show_inventory')
        drop_inventory = action.get('drop_inventory')
        look = action.get('look')
        inventory_index = action.get('inventory_index')
        take_stairs = action.get('take_stairs')
        level_up = action.get('level_up')
        show_character_screen = action.get('show_character_screen')
        esc_menu = action.get('esc_menu')
        help = action.get('help')
        exit = action.get('exit')
        quit = action.get('quit')
        fullscreen = action.get('fullscreen')
        auto_explore = action.get('auto_explore')

        left_click = mouse_action.get('left_click')
        right_click = mouse_action.get('right_click')

        player_turn_results = []

        # For all actions that do not return to the main menu, recompute fov (prevents off-screen window drawing errors)
        if action != quit and action != fullscreen:
            fov_recompute = True
            root_console.clear(fg=(255, 255, 255))

        if move and game_state == GameStates.PLAYERS_TURN:
            dx, dy = move
            destination_x = player.x + dx
            destination_y = player.y + dy

            if not game_map.is_blocked(destination_x, destination_y):
                target = get_blocking_entities_at_location(entities, destination_x, destination_y)
                if target:
                    attack_results = player.fighter.attack(target)
                    player_turn_results.extend(attack_results)
                else:
                    player.move(dx, dy, game_map)
                game_state = GameStates.ENEMY_TURN

        if auto_explore and game_state == GameStates.PLAYERS_TURN:
            if entities_in_fov(entities, fov_map, message_log):
                game_state = GameStates.PLAYERS_TURN
            elif GameMap.explore(game_map, player, entities, message_log) is True:
                game_state = GameStates.ENEMY_TURN
                exploring = True
            else:
                exploring = False

        if exploring and game_state == GameStates.PLAYERS_TURN:
            if entities_in_fov(entities, fov_map, message_log):
                game_state = GameStates.PLAYERS_TURN
                exploring = False
            elif GameMap.explore(game_map, player, entities, message_log) is True:
                game_state = GameStates.ENEMY_TURN
                exploring = True
            else:
                exploring = False

        elif wait:
            game_state = GameStates.ENEMY_TURN

        elif rest and game_state == GameStates.PLAYERS_TURN:
            if player.fighter.current_hp == player.fighter.base_max_hp:
                message_log.add_message(Message('You are already at full health.', libtcod.yellow))
            elif entity_in_fov(game_map, entities, fov_map):
                message_log.add_message(Message('You cannot rest when enemies are nearby.', libtcod.yellow))
            else:
                start_turn = turn_number
                while player.fighter.current_hp < player.fighter.base_max_hp:
                    if turn_number % 4 == 0:
                        player.fighter.current_hp += 1
                        turn_number += 1
                    else:
                        turn_number += 1
                turns_passed = turn_number - start_turn
                message_log.add_message(Message('You rest for {0} turns, returning to max HP.'.format(turns_passed),
                                                libtcod.yellow))

        elif pickup and game_state == GameStates.PLAYERS_TURN:
            for entity in entities:
                if entity.item and entity.x == player.x and entity.y == player.y:
                    pickup_results = player.inventory.add_item(entity)
                    player_turn_results.extend(pickup_results)
                    break
            else:
                message_log.add_message(Message('There is nothing here to pick up.', libtcod.yellow))

        if show_inventory:
            previous_game_state = game_state
            game_state = GameStates.SHOW_INVENTORY

        if drop_inventory:
            previous_game_state = game_state
            game_state = GameStates.DROP_INVENTORY

        if inventory_index is not None and previous_game_state != GameStates.PLAYER_DEAD and inventory_index < len(
                player.inventory.items):
            item = player.inventory.items[inventory_index]

            if game_state == GameStates.SHOW_INVENTORY:
                player_turn_results.extend(player.inventory.use(item, entities=entities, fov_map=fov_map))
            elif game_state == GameStates.DROP_INVENTORY:
                player_turn_results.extend(player.inventory.drop_item(item))

        if look:
            previous_game_state = game_state
            game_state = GameStates.LOOK

        if take_stairs and game_state == GameStates.PLAYERS_TURN:
            for entity in entities:
                if entity.stairs and entity.x == player.x and entity.y == player.y:
                    entities = game_map.next_floor(player, constants)
                    fov_map = initialize_fov(game_map)
                    break
            else:
                message_log.add_message(Message('There are no stairs here.', libtcod.yellow))

        if level_up:
            if level_up == 'hp':
                hit_dice_roll = randint(0, round(player.fighter.base_vitality/4))
                player.fighter.base_max_hp += 10 + hit_dice_roll
                player.fighter.current_hp += 10 + hit_dice_roll
            elif level_up == 'str':
                player.fighter.base_strength += 1
            elif level_up == 'agi':
                player.fighter.base_agility += 1
            game_state = previous_game_state

        if show_character_screen:
            previous_game_state = game_state
            game_state = GameStates.CHARACTER_SCREEN

        if game_state == GameStates.TARGETING:
            if left_click:
                target_x, target_y = left_click
                item_use_results = player.inventory.use(targeting_item, entities=entities, fov_map=fov_map,
                                                        target_x=target_x, target_y=target_y)
                player_turn_results.extend(item_use_results)
            elif right_click:
                player_turn_results.append({'targeting_cancelled': True})

        if esc_menu:
            previous_game_state = game_state
            game_state = GameStates.ESC_MENU

        if help:
            game_state = GameStates.HELP_MENU

        if exit:
            if game_state == GameStates.TARGETING:
                player_turn_results.append({'targeting_cancelled': True})
                return True
            else:
                game_state = previous_game_state

        if quit:
            save_game(player, entities, game_map, message_log, game_state)
            return True

        if fullscreen:
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

        for player_turn_result in player_turn_results:
            message = player_turn_result.get('message')
            dead_entity = player_turn_result.get('dead')
            item_added = player_turn_result.get('item_added')
            item_consumed = player_turn_result.get('consumed')
            item_dropped = player_turn_result.get('item_dropped')
            equip = player_turn_result.get('equip')
            targeting = player_turn_result.get('targeting')
            targeting_cancelled = player_turn_result.get('targeting_cancelled')
            xp = player_turn_result.get('xp')

            if message:
                message_log.add_message(message)

            if dead_entity:
                if dead_entity == player:
                    message, game_state = kill_player(dead_entity)
                else:
                    message = kill_monster(dead_entity, entities)

                message_log.add_message(message)

            if item_added:
                entities.remove(item_added)
                game_state = GameStates.ENEMY_TURN

            if item_consumed:
                game_state = GameStates.ENEMY_TURN

            if item_dropped:
                entities.append(item_dropped)
                game_state = GameStates.ENEMY_TURN

            if equip:
                equip_results = player.equipment.toggle_equip(equip)
                for equip_result in equip_results:
                    equipped = equip_result.get('equipped')
                    dequipped = equip_result.get('dequipped')

                    if equipped:
                        message_log.add_message(Message('You equipped the {0}'.format(equipped.name)))

                    if dequipped:
                        message_log.add_message(Message('You dequipped the {0}'.format(dequipped.name)))
                game_state = GameStates.ENEMY_TURN

            if targeting:
                previous_game_state = GameStates.PLAYERS_TURN
                game_state = GameStates.TARGETING
                targeting_item = targeting
                message_log.add_message(targeting_item.item.targeting_message)

            if targeting_cancelled:
                game_state = previous_game_state
                message_log.add_message(Message('Targeting cancelled'))

            if xp:
                leveled_up = player.level.add_xp(xp)
                message_log.add_message(Message('You gain {0} experience points.'.format(xp)))
                if leveled_up:
                    message_log.add_message(Message(
                        'You level up! You are now level {0}'.format(
                            player.level.current_level) + '!', libtcod.yellow))
                    previous_game_state = game_state
                    game_state = GameStates.LEVEL_UP

        if game_state == GameStates.ENEMY_TURN:
            for entity in entities:
                if entity.ai:
                    # Heal-over time effect for enemies
                    if turn_number % 4 == 0:
                        if entity.fighter.current_hp < entity.fighter.base_max_hp:
                            entity.fighter.current_hp += 1
                    enemy_turn_results = entity.ai.take_turn(player, fov_map, game_map, entities)

                    for enemy_turn_result in enemy_turn_results:
                        message = enemy_turn_result.get('message')
                        dead_entity = enemy_turn_result.get('dead')

                        if message:
                            message_log.add_message(message)

                        if dead_entity:
                            if dead_entity == player:
                                message, game_state = kill_player(dead_entity)
                            else:
                                message = kill_monster(dead_entity, entities)

                            message_log.add_message(message)

                            if game_state == GameStates.PLAYER_DEAD:
                                break

                    if game_state == GameStates.PLAYER_DEAD:
                        break
            else:
                # Heal-over time effect for the player
                if turn_number % 4 == 0:
                    if player.fighter.current_hp < player.fighter.base_max_hp:
                        player.fighter.current_hp += 1
                turn_number += 1
                game_state = GameStates.PLAYERS_TURN


if __name__ == '__main__':
    main()
