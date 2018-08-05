import libtcodpy as libtcod


def menu(con, header, options, width, screen_width, screen_height):
    if len(options) > 26:
        raise ValueError('Cannot have a menu with more than 26 options.')

    # calculate total height for the header (after auto-wrap) and one line per option
    header_height = libtcod.console_get_height_rect(con, 0, 0, width, screen_height, header)
    height = len(options) + header_height

    # create an off-screen console that represents the menu's window
    window = libtcod.console_new(width, height)

    # print the header, with auto-wrap
    libtcod.console_set_default_foreground(window, libtcod.white)
    libtcod.console_print_rect_ex(window, 0, 0, width, height, libtcod.BKGND_NONE, libtcod.LEFT, header)

    # print all the options
    y = header_height
    letter_index = ord('a')
    for option_text in options:
        text = '(' + chr(letter_index) + ') ' + option_text
        libtcod.console_print_ex(window, 0, y, libtcod.BKGND_NONE, libtcod.LEFT, text)
        y += 1
        letter_index += 1

    # blit the contents of "window" to the root console
    x = int(screen_width / 2 - width / 2)
    y = int(screen_height / 2 - height / 2)
    libtcod.console_blit(window, 0, 0, width, height, 0, x, y, 1, 0)


def inventory_menu(con, header, player, inventory_width, screen_width, screen_height):
    # show a menu with each item of the inventory as an option
    if len(player.inventory.items) == 0:
        options = ['Inventory is empty.']
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
            elif player.equipment.left_hand == item:
                options.append('{0} (left hand)'.format(item.name))
            elif player.equipment.right_hand == item:
                options.append('{0} (right hand)'.format(item.name))
            else:
                options.append(item.name)

    menu(con, header, options, inventory_width, screen_width, screen_height)


def main_menu(con, background_image, screen_width, screen_height):
    libtcod.image_blit_2x(background_image, 0, 0, 0, 0, -1, -1)

    libtcod.console_set_default_foreground(0, libtcod.light_yellow)
    libtcod.console_print_ex(0, int(screen_width / 2), int(screen_height / 2) - 4, libtcod.BKGND_NONE, libtcod.CENTER,
                             'SludgeQuest')
    libtcod.console_print_ex(0, int(screen_width / 2), int(screen_height - 2), libtcod.BKGND_NONE, libtcod.CENTER,
                             'designed by the Supreme Peasant')

    menu(con, '', ['New game', 'Continue', 'Quit'], 24, screen_width, screen_height)


def level_up_menu(con, header, player, menu_width, screen_width, screen_height):
    options = ['Strength (+1 attack, from {0})'.format(player.fighter.strength),
               'Agility (+1 defense, from {0})'.format(player.fighter.agility),
               'Vitality (+10 HP, from {0})'.format(player.fighter.max_hp)]

    menu(con, header, options, menu_width, screen_width, screen_height)


def character_screen(player, menu_width, menu_height, screen_width, screen_height):
    window = libtcod.console_new(menu_width, menu_height)

    libtcod.console_set_default_foreground(window, libtcod.white)

    libtcod.console_print_rect_ex(window, 0, 1, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Character Information')
    libtcod.console_print_rect_ex(window, 0, 2, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Level: {0}'.format(player.level.current_level))
    libtcod.console_print_rect_ex(window, 0, 3, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Experience: {0}'.format(player.level.current_xp))
    libtcod.console_print_rect_ex(window, 0, 4, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Experience to Level: {0}'.format(player.level.experience_to_next_level))
    libtcod.console_print_rect_ex(window, 0, 6, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Maximum HP: {0}'.format(player.fighter.max_hp))
    libtcod.console_print_rect_ex(window, 0, 7, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Attack: {0}'.format(player.fighter.strength))
    libtcod.console_print_rect_ex(window, 0, 8, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Defence: {0}'.format(player.fighter.agility))

    x = screen_width // 2 - menu_width // 2
    y = screen_height // 2 - menu_height // 2
    libtcod.console_blit(window, 0, 0, menu_width, menu_height, 0, x, y, 1.0, 0.7)


def esc_menu(colours, menu_width, menu_height, screen_width, screen_height):
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

    x = screen_width // 2 - menu_width // 2
    y = screen_height // 2 - menu_height
    libtcod.console_blit(window, 0, 0, menu_width, int(menu_height/2 + 2), 0, x, y, 1.0, 0.75)


def help_menu(menu_width, menu_height, screen_width, screen_height):
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
    libtcod.console_print_rect_ex(window, 0, 5, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Commands:')
    libtcod.console_print_rect_ex(window, 0, 6, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'g: Get, i: Inventory, d: Drop, c: Character Info, >: Use Stairs')
    libtcod.console_print_rect_ex(window, 0, 7, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Press F11 at any time to toggle fullscreen mode.')
    libtcod.console_print_rect_ex(window, 0, 8, menu_width, menu_height, libtcod.BKGND_NONE,
                                  libtcod.LEFT, 'Press Escape to leave this menu.')

    x = screen_width // 2 - menu_width // 2
    y = screen_height // 2 - menu_height // 2
    libtcod.console_blit(window, 0, 0, menu_width, menu_height, 0, x, y, 1.0, 1.0)


def message_box(con, header, width, screen_width, screen_height):
    menu(con, header, [], width, screen_width, screen_height)
