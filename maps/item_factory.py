import tcod

import lib.consumable
import lib.equippable
from lib.entity import Item

# Consumables
healing_mud = Item(
    char="‼",
    colour=tcod.orange,
    name="Healing Mud",
    consumable=lib.consumable.RandomHealConsumable(8, 12),
    usetext="You slather yourself in the healing mud..."
)

lightning_twig = Item(
    char="√",
    colour=tcod.dark_yellow,
    name="Crackling Imbued Twig",
    consumable=lib.consumable.LightningDamageConsumable(damage=20, maximum_range=5),
    usetext="You snap the twig..."
)

confusing_twig = Item(
    char="√",
    colour=tcod.dark_fuchsia,
    name="Warping Imbued Twig",
    consumable=lib.consumable.ConfusionConsumable(number_of_turns=6),
    usetext="You snap the twig..."
)

fireball_twig = Item(
    char="√",
    colour=tcod.dark_red,
    name="Burnt Imbued Twig",
    consumable=lib.consumable.FireballDamageConsumable(damage=12, radius=3),
    usetext="You snap the twig..."
)

# Equipment
dagger = Item(
    char="/",
    colour=tcod.light_grey,
    name="Dagger",
    equippable=lib.equippable.Dagger()
)

longsword = Item(
    char="/",
    colour=tcod.light_grey,
    name="Sword",
    equippable=lib.equippable.LongSword()
)

leather_armor = Item(
    char="]",
    colour=tcod.dark_orange,
    name="Leather Armor",
    equippable=lib.equippable.LeatherArmour(),
)

cuirass = Item(
    char="]",
    colour=tcod.silver,
    name="Steel Cuirass",
    equippable=lib.equippable.Cuirass()
)

# def steel_cuirass(x, y):
#     equippable_component = Equippable(EquipmentSlots.Torso, armour_bonus=3)
#     return Entity(x, y, ']', tcod.white, 'Steel Cuirass',
#                   'A medieval steel chestplate, frayed with rust and various unusual discolourations. Despite the'
#                   'moderate lack of structural integrity, this will still provide ample protection against most'
#                   'conventional weaponry.', equippable=equippable_component)
#
#
# def trickster_gloves(x, y):
#     equippable_component = Equippable(EquipmentSlots.Hands, armour_bonus=1, dexterity_bonus=2)
#     return Entity(x, y, ')', tcod.darker_orange, 'Trickster\'s Gloves',
#                   'These dark, leather gloves which extend to the elbow not only provide safety against any intruding '
#                   'fangs, but cause you to question whether the nagging sense of kleptomania you are experiencing '
#                   'has always been an inherent aspect of your personality.', equippable=equippable_component)
#
#
# def steel_platelegs(x, y):
#     equippable_component = Equippable(EquipmentSlots.Legs, armour_bonus=2)
#     return Entity(x, y, '}', tcod.white, 'Steel Platelegs',
#                   'All the components of a solid, medieval-style set of plated leg armour stand before you; tassets, '
#                   'cuisses and greaves all made from dented, but reasonable quality steel.',
#                   equippable=equippable_component)
#
#
# def wax_coated_ring(x, y):
#     equippable_component = Equippable(EquipmentSlots.Left_Hand, dexterity_bonus=2, vitality_bonus=2)
#     return Entity(x, y, '.', tcod.dark_yellow, 'Wax-Coated Ring',
#                   'A ring completely covered in a darkened yellow wax which is impossible to remove. You surmise that '
#                   'this material exists not to prevent damage to the ring, but to impart permanence to the inherent '
#                   'power within this object and protect it from the natural corruption of the SludgeWorks. Just by '
#                   'holding the ring, the impending doom of your certain demise feels slightly lifted.',
#                   equippable=equippable_component)
#
# def iron_helmet(x, y):
#     equippable_component = Equippable(EquipmentSlots.Head, armour_bonus=1)
#     return Entity(x, y, '^', tcod.light_grey, 'Iron Helmet', 'An iron helmet designed to help minimise head wounds.',
#                   equippable=equippable_component)
#
#
# def steel_bascinet(x, y):
#     equippable_component = Equippable(EquipmentSlots.Head, armour_bonus=2)
#     return Entity(x, y, '^', tcod.lighter_grey, 'Steel Bascinet',
#                   'A crescent-moon shaped slot is cut into the front of this helmet made of interlocking plate. The '
#                   'front of the faceguard protrudes confidently in the assurance that all but the most mortal of wounds'
#                   'will simply glance off harmlessly.', equippable=equippable_component)
# def steel_longsword(x, y):
#     equippable_component = Equippable(EquipmentSlots.Main_Hand,
#                                       damage_dice=1, damage_sides=6,
#                                       strength_bonus=1)
#     return Entity(x, y, '/', tcod.lighter_grey, 'Steel Longsword',
#                   'A highly polished, sharp steel longsword with an engraved hilt made of bone. Judging by the chirped '
#                   'chevrons processing up the blade\'s body, this is undoubtedly a weapon belonging to the Cleansing '
#                   'Hand, discarded either as a result of a hasty slaughter or the gentle caress of insanity.',
#                   equippable=equippable_component)
#
#
# def steel_dagger(x, y):
#     equippable_component = Equippable(EquipmentSlots.Main_Hand,
#                                       damage_dice=1, damage_sides=3,
#                                       dexterity_bonus=1)
#     return Entity(x, y, '-', tcod.lighter_grey, 'Steel Dagger',
#                   'A wicked, slightly curved steel dagger with an ivory hilt embezzled with eastern filigree. Although'
#                   'not as dangerous as a longsword, you feel more able to avoid attacks when wielding this weapon.',
#                   equippable=equippable_component)
#
#
# def steel_mace(x, y):
#     equippable_component = Equippable(EquipmentSlots.Main_Hand,
#                                       damage_dice=2, damage_sides=3,
#                                       strength_bonus=2)
#     return Entity(x, y, '*', tcod.lighter_grey, 'Steel Mace',
#                   'A heavy, flanged steel mace half as long as you are tall. Designed for use against heavily armoured'
#                   'opponents, a square hit from this behemoth is enough to dent chestpieces, ribcages and all '
#                   'manner of mutated chitin', equippable=equippable_component)
#
#
# def influenced_hatchet(x, y):
#     equippable_component = Equippable(EquipmentSlots.Main_Hand,
#                                       damage_dice=3, damage_sides=3,
#                                       strength_bonus=3, dexterity_bonus=3)
#     return Entity(x, y, '|', tcod.light_lime, 'Influenced Hatchet',
#                   'Undeniably tainted by the SludgeWorks, what used to be a woodsman\'s tool for chopping wood (or,'
#                   'perhaps, the local writhing vegetation) has began to turn into a part of the scenery in its own'
#                   'right. Vines trail from a bundled counterweight at the hilt of the weapon, and the axe\'s edge'
#                   'remains impossibly sharp, despite years of use. Your instincts feel unnervingly and unnaturally '
#                   'heightened when holding this weapon.', equippable=equippable_component)
#
#
# def iron_buckler(x, y):
#     equippable_component = Equippable(EquipmentSlots.Off_Hand, armour_bonus=1)
#     return Entity(x, y, ']', tcod.light_grey, 'Iron Buckler',
#                   'A small buckler that can be attached to the arm and used to deflect attacks.',
#                   equippable=equippable_component)
#
#
# def steel_greatshield(x, y):
#     equippable_component = Equippable(EquipmentSlots.Off_Hand, armour_bonus=2)
#     return Entity(x, y, ')', tcod.lighter_grey, 'Steel Heraldic Greatshield',
#                   'A steel greatshield once emblazoned with the heraldry of an ancient house. Although the image is'
#                   'mostly concealed by time, you are still able to make out what appears to be a crowned, upright'
#                   'bear dancing on a blood-stained field of wheat.', equippable=equippable_component)