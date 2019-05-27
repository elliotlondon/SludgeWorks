import tcod as libtcod


def menu(con, header, options, width, screen_width, screen_height):
    if len(options) > 26:
        raise ValueError('Cannot have a menu with more than 26 options.')

    # Calculate total height for the header (after auto-wrap) and one line per option
    header_height = libtcod.console_get_height_rect(con, 0, 0, width, screen_height, header)
    height = len(options) + header_height

    # Create an off-screen console that represents the menu's window
    window = libtcod.console_new(width, height)

    # Print the header, with auto-wrap
    libtcod.console_set_default_foreground(window, libtcod.white)
    libtcod.console_set_default_background(window, libtcod.black)
    libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)

    # Print all the options
    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = '(' + chr(letter_index) + ') ' + option_text
        libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
        y += 1
        letter_index += 1

    # Blit the contents of "window" to the root console
    x = int(screen_width / 2 - width / 2)
    y = int(screen_height / 2 - height / 2)
    libtcod.console_blit(window, 0, 0, width, height, con, x, y, 1, 0)


def inventory_menu(con, header, player, inventory_width, screen_width, screen_height):
    window = libtcod.console_new(screen_width, screen_height)
    libtcod.console_set_default_foreground(window, libtcod.white)

    # Show a menu with each item of the inventory as an option
    if len(player.inventory.items) == 0:
        options = ['Your inventory is empty.']
    else:
        options = []

        for item in player.inventory.items:
            if player.equipment.main_hand == item:
                options.append('{0} (main hand)'.format(item.name))
            elif player.equipment.off_hand == item:
                options.append('{0} (off hand)'.format(item.name))
            elif player.equipment.head == item:
                options.append('{0} (head)'.format(item.name))
            elif player.equipment.torso == item:
                options.append('{0} (torso)'.format(item.name))
            elif player.equipment.hands == item:
                options.append('{0} (hands)'.format(item.name))
            elif player.equipment.legs == item:
                options.append('{0} (legs)'.format(item.name))
            elif player.equipment.feet == item:
                options.append('{0} (feet)'.format(item.name))
            else:
                options.append(item.name)

    menu(con, header, options, inventory_width, screen_width, screen_height)


def main_menu(con, background_image, screen_width, screen_height):
    libtcod.image_blit_2x(background_image, con, 0, 0, 0, -1, -1)
    libtcod.console_set_default_foreground(con, libtcod.light_yellow)
    libtcod.console_print_ex(con, int(screen_width / 2), int(screen_height / 2) - 4, libtcod.BKGND_NONE, libtcod.CENTER,
                             'SludgeWorks')
    libtcod.console_print_ex(con, int(screen_width / 2), int(screen_height - 2), libtcod.BKGND_NONE, libtcod.CENTER,
                             'designed by the Supreme Peasant')
    menu(con, '', ['New game', 'Continue', 'Quit'], 24, screen_width, screen_height)


def level_up_menu(con, header, player, menu_width, screen_width, screen_height):
    window = libtcod.console_new(menu_width, screen_height)
    libtcod.console_set_default_foreground(window, libtcod.white)
    libtcod.console_set_default_background(window, libtcod.black)

    options = ['Strength (+1 attack, from {0})'.format(player.fighter.base_strength),
               'Dexterity (+1 defense, from {0})'.format(player.fighter.base_dexterity)]

    menu(con, header, options, menu_width, screen_width, screen_height)


def character_screen(con, player, menu_width, menu_height, screen_width, screen_height):
    window = libtcod.console_new(menu_width, menu_height)
    libtcod.console_set_default_foreground(window, libtcod.white)

    libtcod.console_print_rect_ex(window, 0, 1, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Character Information')
    libtcod.console_print_rect_ex(window, 0, 2, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Level: {0}'.format(player.level.current_level))
    libtcod.console_print_rect_ex(window, 0, 3, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Experience: {0}'.format(player.level.current_xp))
    libtcod.console_print_rect_ex(window, 0, 4, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Experience to Level: {0}'
                                  .format(player.level.experience_to_next_level))
    libtcod.console_print_rect_ex(window, 0, 6, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Maximum HP: {0}'.format(player.fighter.max_hp))
    libtcod.console_print_rect_ex(window, 0, 7, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Strength: {0} [+{1}]'.format(player.fighter.base_strength,
                                                                              player.fighter.strength_modifier))
    libtcod.console_print_rect_ex(window, 0, 8, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Defence: {0} [+{1}]'.format(player.fighter.base_dexterity,
                                                                             player.fighter.dexterity_modifier))

    x = screen_width // 2 - menu_width // 2
    y = screen_height // 2 - menu_height // 2
    libtcod.console_blit(window, 0, 0, menu_width, menu_height, con, x, y, 1, 1)


def ability_screen(con, player, menu_width, menu_height, screen_width, screen_height):
    window = libtcod.console_new(menu_width, menu_height)
    libtcod.console_set_default_foreground(window, libtcod.white)

    libtcod.console_print_rect_ex(window, 0, 1, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Placeholder until abilities are implemented!')

    x = screen_width // 2 - menu_width // 2
    y = screen_height // 2 - menu_height // 2
    libtcod.console_blit(window, 0, 0, menu_width, menu_height, con, x, y, 1, 1)


def esc_menu(con, menu_width, menu_height, screen_width, screen_height, turn_number):
    window = libtcod.console_new(menu_width, menu_height)
    libtcod.console_set_default_foreground(window, libtcod.white)
    libtcod.console_set_color_control(libtcod.COLCTRL_1, libtcod.light_yellow, libtcod.white)

    libtcod.console_print_rect_ex(window, 0, 1, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Options')
    libtcod.console_print_rect_ex(window, 0, 3, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'a.) %c%s%celp' % (libtcod.COLCTRL_1, 'H', libtcod.COLCTRL_STOP))
    libtcod.console_print_rect_ex(window, 0, 4, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'b.) %c%s%cesume' % (libtcod.COLCTRL_1, 'R', libtcod.COLCTRL_STOP))
    libtcod.console_print_rect_ex(window, 0, 5, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'c.) Save & %c%s%cuit' % (libtcod.COLCTRL_1, 'Q', libtcod.COLCTRL_STOP))
    libtcod.console_print_rect_ex(window, 0, 6, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, '\nTurns passed: {0}'.format(turn_number))

    x = screen_width // 2 - menu_width // 2
    y = screen_height // 2 - menu_height
    libtcod.console_blit(window, 0, 0, menu_width, int(menu_height/2 + 6), con, x, y, 1, 1)


def help_menu(con, menu_width, menu_height, screen_width, screen_height):
    window = libtcod.console_new(menu_width, menu_height)
    libtcod.console_set_default_foreground(window, libtcod.white)

    libtcod.console_print_rect_ex(window, 0, 1, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Help')
    libtcod.console_print_rect_ex(window, 0, 2, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Movement:')
    libtcod.console_print_rect_ex(window, 0, 3, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Move around using either the arrow keys,')
    libtcod.console_print_rect_ex(window, 0, 4, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'or y u i, h j k l, b n m.')
    libtcod.console_print_rect_ex(window, 0, 6, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Commands:')
    libtcod.console_print_rect_ex(window, 0, 7, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'g: Get')
    libtcod.console_print_rect_ex(window, 0, 8, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'i: Inventory')
    libtcod.console_print_rect_ex(window, 0, 9, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'd: Drop')
    libtcod.console_print_rect_ex(window, 0, 10, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'c: Character Info')
    libtcod.console_print_rect_ex(window, 0, 11, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, '>: Use Stairs')
    libtcod.console_print_rect_ex(window, 0, 12, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, '.: Wait 1 turn')
    libtcod.console_print_rect_ex(window, 0, 13, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, ';: Rest until healed')
    libtcod.console_print_rect_ex(window, 0, 14, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, '#: Autoexplore the map (interrupted by enemies)')
    libtcod.console_print_rect_ex(window, 0, 16, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Press F11 at any time to toggle fullscreen mode.')
    libtcod.console_print_rect_ex(window, 0, 17, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Press Escape to leave this menu.')

    x = screen_width // 2 - menu_width // 2
    y = screen_height // 2 - menu_height // 2
    libtcod.console_blit(window, 0, 0, menu_width, menu_height, con, x, y, 1, 1)


def message_box(con, header, width, screen_width, screen_height):
    menu(con, header, [], width, screen_width, screen_height)
