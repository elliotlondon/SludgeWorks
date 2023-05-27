import tcod

from typing import List

import parts.entity


def get_debuff_colours(player: parts.entity.Entity) -> List:
    """Return an array of colours for each skill, depending upon whether it is currently being buffed or debuffed."""
    # Str
    if player.fighter.modified_strength > player.fighter.base_strength:
        str_colour = tcod.green
    elif player.fighter.modified_strength < player.fighter.base_strength:
        str_colour = tcod.red
    else:
        str_colour = tcod.white
    # Dex
    if player.fighter.modified_dexterity > player.fighter.base_dexterity:
        dex_colour = tcod.green
    elif player.fighter.modified_dexterity < player.fighter.base_dexterity:
        dex_colour = tcod.red
    else:
        dex_colour = tcod.white
    # Vit
    if player.fighter.modified_vitality > player.fighter.base_vitality:
        vit_colour = tcod.green
    elif player.fighter.modified_vitality < player.fighter.base_vitality:
        vit_colour = tcod.red
    else:
        vit_colour = tcod.white
    # Int
    if player.fighter.modified_intellect > player.fighter.base_intellect:
        int_colour = tcod.green
    elif player.fighter.modified_intellect < player.fighter.base_intellect:
        int_colour = tcod.red
    else:
        int_colour = tcod.white

    return [str_colour, dex_colour, vit_colour, int_colour]


# Basic colours
white = (0xFF, 0xFF, 0xFF)
grey = tcod.grey
black = (0x0, 0x0, 0x0)
red = (0xFF, 0x0, 0x0)
orange = tcod.orange
green = (0x0, 0xFF, 0x0)
blue = (0x0, 0x0, 0xFF)
cyan = tcod.cyan
yellow = (0xFF, 0xFF, 0x0)

# System decorators
debug = red
invalid = (0xFF, 0xFF, 0x00)
impossible = (0x80, 0x80, 0x80)
error = (0xFF, 0x40, 0x40)
warning = tcod.orange

# Combat
player_atk = tcod.light_blue
player_crit = tcod.dark_blue
player_evade = tcod.grey
enemy_atk = tcod.light_pink
enemy_crit = tcod.purple
enemy_evade = tcod.lightest_pink
player_die = (0xFF, 0x30, 0x30)
enemy_die = (0xFF, 0xA0, 0x30)

# Mutations and abilities
ability_used = tcod.orange

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
bleed = tcod.light_red
bleed_end = tcod.lightest_red
on_fire = tcod.orange
on_fire_2 = tcod.yellow
on_fire_end = tcod.light_flame
enrage = tcod.dark_red
stun = tcod.cyan
stun_end = tcod.light_cyan
dazzle = tcod.light_grey
wither = tcod.grey
feared = tcod.light_purple

# Liquids
blood = tcod.darker_crimson
sap = tcod.dark_yellow

# Screen info
bar_text = white
hp_bar_filled = (0x0, 0x60, 0x0)
hp_bar_withered = tcod.grey
hp_bar_empty = tcod.darkest_red
xp_bar_filled = tcod.dark_blue
xp_bar_empty = tcod.darkest_blue

# Menus
menu_title = (255, 255, 63)
menu_text = white

# Misc
welcome_text = (0x20, 0xA0, 0xFF)
