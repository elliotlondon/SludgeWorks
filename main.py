from engine import custrender
from random import choice
from lib.death_functions import kill_monster, kill_player
from lib.entity import get_blocking_entities_at_location
from engine.fov_functions import *
from gui.game_messages import Message
from engine.game_states import GameStates
from maps.game_map import GameMap
from engine.input_handlers import handle_keys, handle_mouse, handle_main_menu
from init import get_constants, get_game_variables
from engine.data_loaders import load_game, save_game, delete_char_save
from gui.menus import main_menu, message_box, target_overlay
from engine.render_functions import clear_all, render_all, entity_in_fov, entities_in_fov
from utils.random_utils import roll_dice


def main():
    # libtcod.sys_set_fps(30)
    constants = get_constants()

    player = None
    entities = []
    game_map = None
    message_log = None
    show_main_menu = True
    show_load_error_message = False

    key = libtcod.Key()
    mouse = libtcod.Mouse()

    libtcod.console_set_custom_font('fonts/terminal8x8_gs_ro.png', libtcod.FONT_TYPE_GRAYSCALE |
                                    libtcod.FONT_LAYOUT_ASCII_INROW)
    hp_bar = libtcod.console.Console(constants['stat_bar_width'], constants['stat_bar_height'])
    xp_bar = libtcod.console.Console(constants['stat_bar_width'], constants['stat_bar_height'])
    panel = libtcod.console.Console(constants['panel_width'], constants['panel_height'])
    main_menu_background_image = libtcod.image_load('sludge2.png')

    with libtcod.console_init_root(constants['root_width'], constants['root_height'],
                                   constants['window_title'], True, libtcod.RENDERER_SDL2, vsync=True) as root_console:
        while True:
            libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)

            if show_main_menu:
                main_menu(root_console, main_menu_background_image, constants['root_width'],
                          constants['root_height'])

                if show_load_error_message:
                    message_box(root_console, 'No save game to load', 50, constants['root_width'],
                                constants['root_height'])

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
                    raise SystemExit()

            else:
                play_game(player, entities, game_map, message_log, root_console, panel, hp_bar, xp_bar, constants)

                show_main_menu = True


def play_game(player, entities, game_map, message_log, root_console, panel, hp_bar, xp_bar, constants):
    root_console.clear(fg=(255, 255, 255))
    fov_map = initialize_fov(game_map)
    fov_recompute = True

    key = libtcod.Key()
    mouse = libtcod.Mouse()

    game_state = GameStates.PLAYERS_TURN
    turn_number = 0
    turns_passed = 0
    start_turn = 0
    previous_game_state = game_state

    targeting_item = None
    exploring = False
    resting = False
    to_down_stairs = False

    while True:
        libtcod.sys_check_for_event(libtcod.EVENT_KEY_PRESS | libtcod.EVENT_MOUSE, key, mouse)

        if fov_recompute:
            recompute_fov(fov_map, player.x, player.y, constants['fov_radius'], constants['fov_light_walls'],
                          constants['fov_algorithm'])
            render_all(root_console, panel, hp_bar, xp_bar, entities, player, game_map, fov_map, message_log,
                       constants['root_width'], constants['root_height'], constants['game_window_width'],
                       constants['game_window_height'], constants['panel_width'], constants['panel_height'],
                       constants['stat_bar_width'], constants['stat_bar_height'], constants['fx_panel_width'],
                       constants['fx_panel_height'], constants['camera_width'], constants['camera_height'],
                       game_state, turn_number)
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
        show_loadout = action.get('show_loadout')
        look = action.get('look')
        inventory_index = action.get('inventory_index')
        loadout_index = action.get('loadout_index')
        take_stairs = action.get('take_stairs')
        level_up = action.get('level_up')
        show_character_screen = action.get('show_character_screen')
        show_ability_screen = action.get('show_ability_screen')
        esc_menu = action.get('esc_menu')
        help = action.get('help')
        exit = action.get('exit')
        quit = action.get('quit')
        fullscreen = action.get('fullscreen')
        auto_explore = action.get('auto_explore')
        left_click = mouse_action.get('left_click')
        right_click = mouse_action.get('right_click')

        target_x = player.x
        target_y = player.y
        player_turn_results = []

        # For all actions that do not return to the main menu, recompute fov (prevents off-screen window drawing errors)
        if action != quit and action != fullscreen and not resting:
            fov_recompute = True
            root_console.clear(fg=(255, 255, 255))

        if move and game_state == GameStates.PLAYERS_TURN:
            if exploring:
                exploring = False
                previous_game_state = game_state
                message_log.add_message(Message('Autoexploration cancelled.', libtcod.yellow))
            elif resting:
                resting = False
                previous_game_state = game_state
                message_log.add_message(Message('You stop resting.', libtcod.yellow))
            elif to_down_stairs:
                to_down_stairs = False
                previous_game_state = game_state
                message_log.add_message(Message('You stop heading towards the stairs.', libtcod.yellow))

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
            elif GameMap.explore(game_map, player, message_log) is True:
                game_state = GameStates.ENEMY_TURN
                exploring = True
            else:
                exploring = False

        if exploring and game_state == GameStates.PLAYERS_TURN:
            if entities_in_fov(entities, fov_map, message_log):
                game_state = GameStates.PLAYERS_TURN
                exploring = False
            elif GameMap.explore(game_map, player, message_log) is True:
                game_state = GameStates.ENEMY_TURN
                exploring = True
            else:
                exploring = False

        elif wait:
            game_state = GameStates.ENEMY_TURN

        elif rest and game_state == GameStates.PLAYERS_TURN:
            if player.fighter.current_hp == player.fighter.base_max_hp:
                message_log.add_message(Message('You are already at full health.', libtcod.yellow))
            elif entity_in_fov(entities, fov_map):
                message_log.add_message(Message('You cannot rest when enemies are nearby.', libtcod.yellow))
            elif player.fighter.current_hp < player.fighter.base_max_hp:
                game_state = GameStates.ENEMY_TURN
                resting = True
                start_turn = turn_number
            else:
                resting = False

        if resting and game_state == GameStates.PLAYERS_TURN:
            if player.fighter.current_hp == player.fighter.base_max_hp:
                resting = False
                message_log.add_message(Message('You rest for {0} turns, returning to max HP.'.format(turns_passed),
                                                libtcod.yellow))
            elif entities_in_fov(entities, fov_map, message_log):
                message_log.add_message(Message('You rested for a total of {0} turns.'.format(turns_passed),
                                                libtcod.yellow))
                resting = False
                fov_recompute = True
            else:
                turns_passed = turn_number - start_turn
                game_state = GameStates.ENEMY_TURN

        elif pickup and game_state == GameStates.PLAYERS_TURN:
            for entity in entities:
                if entity.item and entity.x == player.x and entity.y == player.y:
                    pickup_results = player.inventory.pick_up(player, entity)
                    entities.remove(entity)
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
                player.inventory.inv_items):
            item = player.inventory.inv_items[inventory_index]

            if game_state == GameStates.SHOW_INVENTORY:
                player_turn_results.extend(player.inventory.use(player, item, entities=entities, fov_map=fov_map))
            elif game_state == GameStates.DROP_INVENTORY:
                player_turn_results.extend(player.inventory.drop_item(player, item))

        if show_loadout:
            previous_game_state = game_state
            game_state = GameStates.SHOW_LOADOUT

        if loadout_index is not None and previous_game_state != GameStates.PLAYER_DEAD and loadout_index < len(
                player.inventory.equip_items):
            item = player.inventory.equip_items[loadout_index]
            if game_state == GameStates.SHOW_LOADOUT:
                player_turn_results.extend(player.inventory.dequip(player, item))
            elif game_state == GameStates.DROP_INVENTORY:
                player_turn_results.extend(player.inventory.drop_item(player, item))

        if look:
            previous_game_state = game_state
            game_state = GameStates.LOOK

        if take_stairs and game_state == GameStates.PLAYERS_TURN:
            for entity in entities:
                if entity.stairs and entity.x == player.x and entity.y == player.y:
                    entities = game_map.next_floor(player)
                    fov_map = initialize_fov(game_map)
                    message_log.add_message(Message(f'You descend to level {game_map.dungeon_level} of the '
                                                    f'SludgeWorks...', libtcod.yellow))
                    break
            else:
                if entities_in_fov(entities, fov_map, message_log):
                    game_state = GameStates.PLAYERS_TURN
                elif GameMap.to_down_stairs(game_map, player, entities, message_log) is True:
                    game_state = GameStates.ENEMY_TURN
                    to_down_stairs = True

        if to_down_stairs and game_state == GameStates.PLAYERS_TURN:
            if entities_in_fov(entities, fov_map, message_log):
                game_state = GameStates.PLAYERS_TURN
                to_down_stairs = False
            elif GameMap.to_down_stairs(game_map, player, entities, message_log) is True:
                game_state = GameStates.ENEMY_TURN
            else:
                to_down_stairs = False

        if level_up:
            hit_dice = roll_dice(1, 8)
            player.fighter.level += 1
            player.fighter.base_max_hp += roll_dice(1, hit_dice + player.fighter.vitality_modifier)
            if level_up == 'str':
                player.fighter.base_strength += 1
            elif level_up == 'agi':
                player.fighter.base_dexterity += 1
            game_state = previous_game_state

        if show_character_screen:
            previous_game_state = game_state
            game_state = GameStates.CHARACTER_SCREEN

        if show_ability_screen:
            previous_game_state = game_state
            game_state = GameStates.ABILITY_SCREEN

        if game_state == GameStates.TARGETING:
            libtcod.console_wait_for_keypress(True)
            target_overlay(root_console, constants['game_window_width'], constants['game_window_height'], target_x,
                           target_y)
            if move:
                dx, dy = move
                target_x += dx
                target_y += dy
            if left_click:
                target_x, target_y = left_click
                item_use_results = player.inventory.use(player, targeting_item, entities=entities, fov_map=fov_map,
                                                        target_x=target_x, target_y=target_y)
                player_turn_results.extend(item_use_results)
            elif right_click:
                player_turn_results.append({'targeting_cancelled': True})

        if esc_menu:
            if exploring:
                exploring = False
                previous_game_state = game_state
                message_log.add_message(Message('Autoexploration cancelled.', libtcod.yellow))
            elif resting:
                resting = False
                previous_game_state = game_state
                message_log.add_message(Message('You stop resting.', libtcod.yellow))
            elif to_down_stairs:
                to_down_stairs = False
                previous_game_state = game_state
                message_log.add_message(Message('You stop heading towards the stairs.', libtcod.yellow))
            else:
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

        if quit and not game_state == GameStates.PLAYER_DEAD:
            save_game(player, entities, game_map, message_log, game_state)
            return True
        elif quit:
            delete_char_save()
            return True

        if fullscreen:
            libtcod.console_set_fullscreen(not libtcod.console_is_fullscreen())

        for player_turn_result in player_turn_results:
            message = player_turn_result.get('message')
            dead_entity = player_turn_result.get('dead')
            item_added = player_turn_result.get('item_added')
            item_consumed = player_turn_result.get('consumed')
            item_dropped = player_turn_result.get('item_dropped')
            equipped = player_turn_result.get('equipped')
            dequipped = player_turn_result.get('dequipped')
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

            if item_added or item_consumed or equipped or dequipped:
                game_state = GameStates.ENEMY_TURN

            if item_dropped:
                entities.append(item_dropped)
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
                if entity.name == 'Phosphorescent Dahlia' and entity_in_fov(entities, fov_map):
                    # Cycle through colours for the phosphorescent dahlia
                    dahlia_colour = [libtcod.light_azure, libtcod.azure, libtcod.dark_azure]
                    entity.colour = choice(dahlia_colour)
                if entity.ai:
                    if entity.regenerates:
                        # Heal-over time effect for enemies that regenerate
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
