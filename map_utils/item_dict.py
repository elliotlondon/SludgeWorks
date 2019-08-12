from equipment_slots import EquipmentSlots
from equipment import Equippable
from entity import Entity
from item import Item
from item_functions import *
from render_functions import RenderOrder
from random import randint


# Weapons and shields (main-hand and off-hand)
def iron_dagger(x, y):
    equippable_component = Equippable(EquipmentSlots.MAIN_HAND,
                                      damage_dice=1, damage_sides=3)
    return Entity(x, y, '-', libtcod.light_grey,
                    'Iron Dagger', 'A short blade ideal for swift stabbing attacks.',
                    equippable=equippable_component)


def iron_longsword(x, y):
    equippable_component = Equippable(EquipmentSlots.MAIN_HAND,
                                      damage_dice=1, damage_sides=4,
                                      strength_bonus=1)
    return Entity(x, y, '/', libtcod.light_grey, 'Iron Longsword',
                  'A medieval-style iron longsword which appears to have seen much use. You ponder '
                  'whether this weapon is the remnant of some ancient expedition, or if some unusual '
                  'intelligence gripped the SludgeWork\'s inhabitants to forge weapons of war.',
                  equippable=equippable_component)


def steel_longsword(x, y):
    equippable_component = Equippable(EquipmentSlots.MAIN_HAND,
                                      damage_dice=1, damage_sides=6,
                                      strength_bonus=1)
    return Entity(x, y, '/', libtcod.lighter_grey, 'Steel Longsword',
                  'A highly polished, sharp steel longsword with an engraved hilt made of bone. Judging by the chirped '
                  'chevrons processing up the blade\'s body, this is undoubtedly a weapon belonging to the Cleansing '
                  'Hand, discarded either as a result of a hasty slaughter or the gentle caress of insanity.',
                  equippable=equippable_component)


def steel_dagger(x, y):
    equippable_component = Equippable(EquipmentSlots.MAIN_HAND,
                                      damage_dice=1, damage_sides=3,
                                      dexterity_bonus=1)
    return Entity(x, y, '-', libtcod.lighter_grey, 'Steel Dagger',
                  'A wicked, slightly curved steel dagger with an ivory hilt embezzled with eastern filigree. Although'
                  'not as dangerous as a longsword, you feel more able to avoid attacks when wielding this weapon.',
                  equippable=equippable_component)


def steel_mace(x, y):
    equippable_component = Equippable(EquipmentSlots.MAIN_HAND,
                                      damage_dice=2, damage_sides=3,
                                      strength_bonus=2)
    return Entity(x, y, '*', libtcod.lighter_grey, 'Steel Mace',
                  'A heavy, flanged steel mace half as long as you are tall. Designed for use against heavily armoured'
                  'opponents, a square hit from this behemoth is enough to dent chestpieces, ribcages and all '
                  'manner of mutated chitin',
                  equippable=equippable_component)


def influenced_hatchet(x, y):
    equippable_component = Equippable(EquipmentSlots.MAIN_HAND,
                                      damage_dice=3, damage_sides=3,
                                      strength_bonus=3, dexterity_bonus=3)
    return Entity(x, y, '|', libtcod.light_lime, 'Influenced Hatchet',
                  'Undeniably tainted by the SludgeWorks, what used to be a woodsman\'s tool for chopping wood (or,'
                  'perhaps, the local writhing vegetation) has began to turn into a part of the scenery in its own'
                  'right. Vines trail from a bundled counterweight at the hilt of the weapon, and the axe\'s edge'
                  'remains impossibly sharp, despite years of use. Your instincts feel unnervingly and unnaturally '
                  'heightened when holding this weapon.',
                  equippable=equippable_component)


def iron_buckler(x, y):
    equippable_component = Equippable(EquipmentSlots.OFF_HAND, armour_bonus=1)
    return Entity(x, y, ']', libtcod.light_grey, 'Iron Buckler',
                  'A small buckler that can be attached to the arm and used to deflect attacks.',
                  equippable=equippable_component)


def steel_greatshield(x, y):
    equippable_component = Equippable(EquipmentSlots.OFF_HAND, armour_bonus=2)
    return Entity(x, y, ')', libtcod.lighter_grey, 'Steel Heraldic Greatshield',
                  'A steel greatshield once emblazoned with the heraldry of an ancient house. Although the image is'
                  'mostly concealed by time, you are still able to make out what appears to be a crowned, upright'
                  'bear dancing on a blood-stained field of wheat.',
                  equippable=equippable_component)


# Armour
def iron_helmet(x, y):
    equippable_component = Equippable(EquipmentSlots.HEAD, armour_bonus=1)
    return Entity(x, y, '^', libtcod.light_grey, 'Iron Helmet',
                  'An iron helmet designed to help minimise head wounds.',
                  equippable=equippable_component)


def steel_bascinet(x, y):
    equippable_component = Equippable(EquipmentSlots.HEAD, armour_bonus=2)
    return Entity(x, y, '^', libtcod.lighter_grey, 'Steel Bascinet',
                  'A crescent-moon shaped slot is cut into the front of this helmet made of interlocking plate. The '
                  'front of the faceguard protrudes confidently in the assurance that all but the most mortal of wounds'
                  'will simply glance off harmlessly.',
                  equippable=equippable_component)


def leather_armour(x, y):
    equippable_component = Equippable(EquipmentSlots.TORSO, armour_bonus=1)
    return Entity(x, y, ']', libtcod.dark_orange, 'Leather Armour',
                  'Basic leather armour covering the torso, providing modest protection. This was the best you could '
                  'find...',
                  equippable=equippable_component)


def steel_cuirass(x, y):
    equippable_component = Equippable(EquipmentSlots.TORSO, armour_bonus=3)
    return Entity(x, y, ']', libtcod.white, 'Steel Cuirass',
                  'A medieval steel chestplate, frayed with rust and various unusual discolourations. Despite the'
                  'moderate lack of structural integrity, this will still provide ample protection against most'
                  'conventional weaponry.',
                  equippable=equippable_component)


def trickster_gloves(x, y):
    equippable_component = Equippable(EquipmentSlots.HANDS, armour_bonus=1, dexterity_bonus=2)
    return Entity(x, y, ')', libtcod.darker_orange, 'Trickster\'s Gloves',
                  'These dark, leather gloves which extend to the elbow not only provide safety against any intruding '
                  'fangs, but cause you to question whether the nagging sense of kleptomania you are experiencing '
                  'has always been an inherent aspect of your personality.',
                  equippable=equippable_component)


def steel_platelegs(x, y):
    equippable_component = Equippable(EquipmentSlots.LEGS, armour_bonus=2)
    return Entity(x, y, '}', libtcod.white, 'Steel Platelegs',
                  'All the components of a solid, medieval-style set of plated leg armour stand before you; tassets, '
                  'cuisses and greaves all made from dented, but reasonable quality steel.',
                  equippable=equippable_component)


def wax_coated_ring(x, y):
    equippable_component = Equippable(EquipmentSlots.LEFT_HAND, dexterity_bonus=2, vitality_bonus=2)
    return Entity(x, y, '.', libtcod.dark_yellow, 'Wax-Coated Ring',
                  'A ring completely covered in a darkened yellow wax which is impossible to remove. You surmise that '
                  'this material exists not to prevent damage to the ring, but to impart permanence to the inherent '
                  'power within this object and protect it from the natural corruption of the SludgeWorks. Just by '
                  'holding the ring, the impending doom of your certain demise feels slightly lifted.',
                  equippable=equippable_component)


# Consumables
def healing_potion(x, y):
    heal_amount = randint(15, 25)
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
    return Entity(x, y, '#', libtcod.dark_red, 'Fireball Scroll',
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
    lightning_damage = 24
    item_component = Item(use_function=cast_lightning, damage=lightning_damage, maximum_range=5)
    return Entity(x, y, '#', libtcod.yellow, 'Lightning Scroll',
                  'A scroll containing an ancient text that you somehow understand the meaning ' +
                  'of. When invoked, deals ' + str(lightning_damage) + ' damage.',
                  render_order=RenderOrder.ITEM,
                  item=item_component)
