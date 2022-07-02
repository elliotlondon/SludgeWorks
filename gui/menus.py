import tcod


def menu(con, header, options, width, screen_width, screen_height):
    if len(options) > 26:
        raise ValueError('Cannot have a menu with more than 26 options.')

    # Calculate total height for the header (after auto-wrap) and one line per option
    header_height = tcod.console_get_height_rect(con, 0, 0, width, screen_height, header)
    height = len(options) + header_height

    # Create an off-screen console that represents the menu's window
    window = tcod.console_new(width, height)

    # Print the header, with auto-wrap
    tcod.console_set_default_foreground(window, tcod.white)
    tcod.console_set_default_background(window, tcod.black)
    tcod.console_print_rect_ex(window, 0, 0, width, height, tcod.BKGND_NONE, tcod.LEFT, header)

    # Print all the options
    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = '(' + chr(letter_index) + ') ' + option_text
        tcod.console_print_ex(window, 0, y, tcod.BKGND_NONE, tcod.LEFT, text)
        y += 1
        letter_index += 1

    # Blit the contents of "window" to the root console
    x = int(screen_width / 2 - width / 2)
    y = int(screen_height / 2 - height / 2)
    tcod.console_blit(window, 0, 0, width, height, con, x, y, 1, 0)


def inventory_menu(con, header, player, inventory_width, screen_width, screen_height):
    window = tcod.console_new(screen_width, screen_height)
    tcod.console_set_default_foreground(window, tcod.white)

    # Show a menu with each item of the inventory as an option
    if len(player.inventory.inv_items) == 0:
        options = ['Your inventory is empty.']
    else:
        options = []
        for item in player.inventory.inv_items:
            options.append(item.name)
    menu(con, header, options, inventory_width, screen_width, screen_height)


def loadout_menu(con, header, player, inventory_width, screen_width, screen_height):
    window = tcod.console_new(screen_width, screen_height)
    tcod.console_set_default_foreground(window, tcod.white)

    # Make sure that everything is sorted in the right order, according to the list in equipment_slots

    # Show a menu with each item of the loadout
    if len(player.inventory.equip_items) == 0:
        options = ['You have nothing equipped.']
    else:
        options = []
        for item in player.inventory.equip_items:
            options.append(f'{item.name} ({item.equippable.to_string(item.equippable.slot)})')
    menu(con, header, options, inventory_width, screen_width, screen_height)


def main_menu(con, background_image, screen_width, screen_height):
    tcod.image_blit_2x(background_image, con, 0, 0, 0, -1, -1)
    tcod.console_set_default_foreground(con, tcod.light_yellow)
    tcod.console_print_ex(con, int(screen_width / 2), int(screen_height / 2) - 4, tcod.BKGND_NONE, tcod.CENTER,
                          'SludgeWorks')
    tcod.console_print_ex(con, int(screen_width / 2), int(screen_height - 2), tcod.BKGND_NONE, tcod.CENTER,
                          'designed by the Supreme Peasant')
    menu(con, '', ['New game', 'Continue', 'Quit'], 24, screen_width, screen_height)


def level_up_menu(con, header, player, menu_width, screen_width, screen_height):
    window = tcod.console_new(menu_width, screen_height)
    tcod.console_set_default_foreground(window, tcod.white)
    tcod.console_set_default_background(window, tcod.black)

    options = ['Strength (+1 attack, currently {0})'.format(player.fighter.base_strength),
               'Dexterity (+1 defense, currently {0})'.format(player.fighter.base_dexterity)]

    menu(con, header, options, menu_width, screen_width, screen_height)


def character_screen(con, player, menu_width, menu_height, screen_width, screen_height):
    window = tcod.console_new(menu_width, menu_height)
    tcod.console_set_default_foreground(window, tcod.white)

    tcod.console_print_rect_ex(window, 0, 1, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'Character Information')
    tcod.console_print_rect_ex(window, 0, 2, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'Level: {0}'.format(player.level.current_level))
    tcod.console_print_rect_ex(window, 0, 3, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'Experience: {0}'.format(player.level.current_xp))
    tcod.console_print_rect_ex(window, 0, 4, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'Experience to Level: {0}'
                               .format(player.level.experience_to_next_level))
    tcod.console_print_rect_ex(window, 0, 6, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'Strength: \t{0} [+{1}]'.format(player.fighter.base_strength,
                                                                          player.fighter.strength_modifier))
    tcod.console_print_rect_ex(window, 0, 7, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'Dexterity: \t{0} [+{1}]'.format(player.fighter.base_dexterity,
                                                                           player.fighter.dexterity_modifier))
    tcod.console_print_rect_ex(window, 0, 8, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'Vitality: \t{0} [+{1}]'.format(player.fighter.base_vitality,
                                                                          player.fighter.vitality_modifier))
    tcod.console_print_rect_ex(window, 0, 9, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'Intellect: \t{0} [+{1}]'.format(player.fighter.base_intellect,
                                                                           player.fighter.intellect_modifier))
    tcod.console_print_rect_ex(window, 0, 10, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'Perception: \t{0} [+{1}]'.format(player.fighter.base_perception,
                                                                            player.fighter.perception_modifier))
    tcod.console_print_rect_ex(window, 0, 12, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'Armour Rating: \t{0}'.format(player.fighter.armour_total))

    x = screen_width // 2 - menu_width // 2
    y = screen_height // 2 - menu_height // 2
    tcod.console_blit(window, 0, 0, menu_width, menu_height, con, x, y, 1, 1)


def ability_screen(con, player, menu_width, menu_height, screen_width, screen_height):
    window = tcod.console_new(menu_width, menu_height)
    tcod.console_set_default_foreground(window, tcod.white)

    tcod.console_print_rect_ex(window, 0, 1, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'Placeholder until abilities are implemented!')

    x = screen_width // 2 - menu_width // 2
    y = screen_height // 2 - menu_height // 2
    tcod.console_blit(window, 0, 0, menu_width, menu_height, con, x, y, 1, 1)


def esc_menu(con, menu_width, menu_height, screen_width, screen_height, turn_number):
    window = tcod.console_new(menu_width, menu_height)
    tcod.console_set_default_foreground(window, tcod.white)
    tcod.console_set_color_control(tcod.COLCTRL_1, tcod.light_yellow, tcod.white)

    tcod.console_print_rect_ex(window, 0, 1, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'Options')
    tcod.console_print_rect_ex(window, 0, 3, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'a.) %c%s%celp' % (tcod.COLCTRL_1, 'H', tcod.COLCTRL_STOP))
    tcod.console_print_rect_ex(window, 0, 4, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'b.) %c%s%cesume' % (tcod.COLCTRL_1, 'R', tcod.COLCTRL_STOP))
    tcod.console_print_rect_ex(window, 0, 5, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'c.) Save & %c%s%cuit' % (tcod.COLCTRL_1, 'Q', tcod.COLCTRL_STOP))
    tcod.console_print_rect_ex(window, 0, 6, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, '\nTurns passed: {0}'.format(turn_number))

    x = screen_width // 2 - menu_width // 2
    y = screen_height // 2 - menu_height
    tcod.console_blit(window, 0, 0, menu_width, int(menu_height / 2 + 6), con, x, y, 1, 1)


def help_menu(con, menu_width, menu_height, screen_width, screen_height):
    window = tcod.console_new(menu_width, menu_height)
    tcod.console_set_default_foreground(window, tcod.white)

    tcod.console_print_rect_ex(window, 0, 1, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'Help')
    tcod.console_print_rect_ex(window, 0, 2, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'Movement:')
    tcod.console_print_rect_ex(window, 0, 3, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'Move around using either the arrow keys,')
    tcod.console_print_rect_ex(window, 0, 4, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'or y u i, h j k l, b n m.')
    tcod.console_print_rect_ex(window, 0, 6, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'Commands:')
    tcod.console_print_rect_ex(window, 0, 7, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'g: Get')
    tcod.console_print_rect_ex(window, 0, 8, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'i: Inventory')
    tcod.console_print_rect_ex(window, 0, 9, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'd: Drop')
    tcod.console_print_rect_ex(window, 0, 10, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'c: Character Info')
    tcod.console_print_rect_ex(window, 0, 11, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, '>: Use Stairs')
    tcod.console_print_rect_ex(window, 0, 12, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, '.: Wait 1 turn')
    tcod.console_print_rect_ex(window, 0, 13, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, ';: Rest until healed')
    tcod.console_print_rect_ex(window, 0, 14, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, '#: Autoexplore the map (interrupted by enemies)')
    tcod.console_print_rect_ex(window, 0, 16, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'Press F11 at any time to toggle fullscreen mode.')
    tcod.console_print_rect_ex(window, 0, 17, menu_width, menu_height, tcod.BKGND_NONE,
                               tcod.LEFT, 'Press Escape to leave this menu.')

    x = screen_width // 2 - menu_width // 2
    y = screen_height // 2 - menu_height // 2
    tcod.console_blit(window, 0, 0, menu_width, menu_height, con, x, y, 1, 1)


def message_box(con, header, width, screen_width, screen_height):
    menu(con, header, [], width, screen_width, screen_height)


def target_overlay(con, menu_width, menu_height, target_x, target_y):
    window = tcod.console_new(menu_width, menu_height)
    tcod.console_put_char_ex(window, 0, 0, 'X', tcod.grey, tcod.black)
    tcod.console_blit(window, 0, 0, menu_width, menu_height, con, target_x, target_y, 1, 1)
