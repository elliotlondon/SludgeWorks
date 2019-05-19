from equipment_slots import EquipmentSlots
from equipment import Equippable
from entity import Entity
from item import Item
from item_functions import *
from render_functions import RenderOrder


# Weapons and shields (main-hand and off-hand)
def iron_longsword(x, y):
    equippable_component = Equippable(EquipmentSlots.MAIN_HAND,
                                      damage_dice=1, damage_sides=4,
                                      strength_bonus=3)
    return Entity(x, y, '/', libtcod.sky, 'Iron Longsword',
                  'A medieval-style iron longsword which appears to have seen much use. You ponder '
                  'whether this weapon is the remnant of some ancient expedition, or if some unusual '
                  'intelligence gripped the SludgeWork\'s inhabitants to forge weapons of war.',
                  equippable=equippable_component)


def iron_buckler(x, y):
    equippable_component = Equippable(EquipmentSlots.OFF_HAND, agility_bonus=1)
    return Entity(x, y, '[', libtcod.darker_orange, 'Shield',
                  'A small buckler that can be attached to the arm and used to deflect attacks.',
                  equippable=equippable_component)


# Armour
def iron_helmet(x, y):
    equippable_component = Equippable(EquipmentSlots.HEAD, agility_bonus=1)
    return Entity(x, y, '[', libtcod.darker_orange, 'Helm',
                  'An iron helmet designed to help minimise head wounds.',
                  equippable=equippable_component)


# Consumables
def healing_potion(x, y):
    heal_amount = 40
    item_component = Item(use_function=heal, amount=heal_amount)
    return Entity(x, y, '!', libtcod.violet, 'Healing Potion',
                  'A violet flask that you recognise to be a healing potion. This will help '
                  'heal your wounds. ' + str(heal_amount) + ' HP',
                  render_order=RenderOrder.ITEM,
                  item=item_component)


def fireball_scroll(x, y):
    fireball_damage = 25
    fireball_range = 3
    item_component = Item(use_function=cast_fireball, targeting=True, targeting_message=Message(
        'Left-click a target tile for the fireball, or right-click to cancel.', libtcod.light_cyan),
                          damage=fireball_damage, radius=fireball_range)
    return Entity(x, y, '#', libtcod.red, 'Fireball Scroll',
                  'A scroll containing an ancient text that you somehow understand the meaning ' +
                  'of. When invoked, envelopes an area with fire, causing ' + str(fireball_damage) +
                  ' damage to all creatures within ' + str(fireball_range) + 'tiles.',
                  render_order=RenderOrder.ITEM,
                  item=item_component)


def confusion_scroll(x, y):
    item_component = Item(use_function=cast_confuse, targeting=True, targeting_message=Message(
        'Left-click an enemy to confuse it, or right-click to cancel.', libtcod.light_cyan))
    return Entity(x, y, '#', libtcod.light_pink, 'Confusion Scroll',
                  'A scroll containing an ancient text that you somehow understand the meaning ' +
                  'of. When invoked, this scroll will cause an enemy to wander aimlessly for 10 turns.',
                  render_order=RenderOrder.ITEM,
                  item=item_component)


def lightning_scroll(x, y):
    lightning_damage = 40
    item_component = Item(use_function=cast_lightning, damage=lightning_damage, maximum_range=5)
    return Entity(x, y, '#', libtcod.yellow, 'Lightning Scroll',
                  'A scroll containing an ancient text that you somehow understand the meaning ' +
                  'of. When invoked, deals ' + str(lightning_damage) + ' damage.',
                  render_order=RenderOrder.ITEM,
                  item=item_component)
