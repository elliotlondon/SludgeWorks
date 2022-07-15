import tcod

# Basic colours
white = (0xFF, 0xFF, 0xFF)
black = (0x0, 0x0, 0x0)
red = (0xFF, 0x0, 0x0)
green = (0x0, 0xFF, 0x0)
blue = (0x0, 0x0, 0xFF)
yellow = (0xFF, 0xFF, 0x0)

# System decorators
debug = red
invalid = (0xFF, 0xFF, 0x00)
impossible = (0x80, 0x80, 0x80)
error = (0xFF, 0x40, 0x40)

# Combat
player_atk = tcod.light_blue
player_crit = tcod.dark_blue
player_evade = tcod.grey
enemy_atk = tcod.light_pink
enemy_crit = tcod.purple
enemy_evade = tcod.lightest_pink
player_die = (0xFF, 0x30, 0x30)
enemy_die = (0xFF, 0xA0, 0x30)

# Item str colours
hp_consumable = tcod.light_green
twigs = tcod.light_amber
weapons = tcod.gray
armour = tcod.dark_gray

# Item effects and use
use = yellow
needs_target = (0x3F, 0xFF, 0xFF)
status_effect_applied = (0x3F, 0xFF, 0x3F)
teleported = tcod.cyan
health_recovered = tcod.light_green
descend = (0x9F, 0x3F, 0xFF)

# Status effects
poison = tcod.dark_green
poison_end = tcod.green

# Screen info
bar_text = white
hp_bar_filled = (0x0, 0x60, 0x0)
hp_bar_empty = tcod.darkest_red
xp_bar_filled = tcod.dark_blue
xp_bar_empty = tcod.darkest_blue

# Menus
menu_title = (255, 255, 63)
menu_text = white

# Misc
welcome_text = (0x20, 0xA0, 0xFF)
