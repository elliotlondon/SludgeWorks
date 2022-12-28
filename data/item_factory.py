from typing import Optional

import json
from typing import List

import parts.consumable
import parts.effects
import parts.equippable
from config.exceptions import DataLoadError
from parts.entity import Item
from parts.equipment_types import EquipmentType
from parts.equippable import Equippable


def create_item_from_json(path: str, request: str) -> Item:
    f = open(path, 'r', encoding='utf-8')
    item_dict = json.load(f)

    for i in range(len(item_dict)):
        if request in item_dict[i]:
            data = item_dict[i][request]

            # Determine item type
            if 'equipment_type' in data:
                item = create_equipment(data)
            elif 'consumable' in data:
                item = create_consumable(data)
            else:
                raise DataLoadError
            return item

def create_all_items_from_json(path: str) -> List[Item]:
    f = open(path, 'r', encoding='utf-8')
    item_dict = json.load(f)

    items = []
    for i in range(len(item_dict)):
        name = list(item_dict[i].keys())[0]
        data = item_dict[i][name]

        # Determine item type
        if 'equipment_type' in data:
            item = create_equipment(data)
        elif 'consumable' in data:
            item = create_consumable(data)
        else:
            raise DataLoadError
        items.append(item)
    return items

def create_equipment(data) -> Item:
    # Find out which slot the item goes in
    equipment_type = data['equipment_type']
    if "MainHand" in equipment_type:
        equipment_type = EquipmentType.Main_Hand
    elif "OffHand" in equipment_type:
        equipment_type = EquipmentType.Off_Hand
    elif "Head" in equipment_type:
        equipment_type = EquipmentType.Head
    elif "Torso" in equipment_type:
        equipment_type = EquipmentType.Torso
    elif "Hands" in equipment_type:
        equipment_type = EquipmentType.Hands
    elif "Legs" in equipment_type:
        equipment_type = EquipmentType.Legs
    elif "Feet" in equipment_type:
        equipment_type = EquipmentType.Feet
    elif "Left_Ring" in equipment_type:
        equipment_type = EquipmentType.Left_Ring
    elif "Right_Ring" in equipment_type:
        equipment_type = EquipmentType.Right_Ring

    # Check modifiers if present
    if 'modifiers' in data['equipment']:
        modifiers = get_modifiers_from_dict(data['equipment']['modifiers'])
    else:
        modifiers = None

    item = Item(
        char=data['char'],
        colour=(data['colour'][0], data['colour'][1], data['colour'][2]),
        tag=data['tag'],
        name=data['name'],
        equippable=Equippable(
            equipment_type=equipment_type,
            modifiers=modifiers,
            damage_dice=data['equipment']['damage_dice'],
            damage_sides=data['equipment']['damage_sides'],
            strength_bonus=data['equipment']['strength_bonus'],
            dexterity_bonus=data['equipment']['dexterity_bonus'],
            vitality_bonus=data['equipment']['vitality_bonus'],
            intellect_bonus=data['equipment']['intellect_bonus'],
            armour_bonus=data['equipment']['armour_bonus']
        ),
        depth=data['depth'],
        rarity=data['rarity'],
        description=data['description']
    )

    return item


def get_modifiers_from_dict(input_dict: dict) -> List[parts.effects.ItemModifier]:
    """Return a populated list of object modifiers depending upon the ones supplied."""
    output_list = []
    if 'poison' in input_dict:
        effect = parts.effects.PoisonModifier(
            damage=input_dict['poison']['damage'],
            turns=input_dict['poison']['turns'],
            difficulty=input_dict['poison']['difficulty']
        )
        output_list.append(effect)

    return output_list


def create_consumable(data: dict) -> Item:
    # Unpack non-json values
    if "Healing" in data['consumable']['type']:
        consumable = parts.consumable.HealingConsumable(data['consumable']['amount'])
    elif "RandomHeal" in data['consumable']['type']:
        consumable = parts.consumable.RandomHealConsumable(data['consumable']['upper_bound'],
                                                           data['consumable']['lower_bound'])
    elif "Lightning" in data['consumable']['type']:
        consumable = parts.consumable.LightningDamageConsumable(data['consumable']['upper_bound'],
                                                                data['consumable']['lower_bound'],
                                                                data['consumable']['range'])
    elif "Confusion" in data['consumable']['type']:
        consumable = parts.consumable.ConfusionConsumable(data['consumable']['number_of_turns'])
    elif "Fireball" in data['consumable']['type']:
        consumable = parts.consumable.FireballDamageConsumable(data['consumable']['upper_bound'],
                                                               data['consumable']['lower_bound'],
                                                               data['consumable']['radius'])
    elif "Teleother" in data['consumable']['type']:
        consumable = parts.consumable.TeleportOtherConsumable()
    elif "Immolation" in data['consumable']['type']:
        consumable = parts.consumable.ImmolateConsumable()
    else:
        consumable = parts.consumable.Junk()
        NotImplementedError()

    item = Item(
        char=data['char'],
        colour=(data['colour'][0], data['colour'][1], data['colour'][2]),
        tag=data['tag'],
        name=data['name'],
        consumable=consumable,
        depth=data['depth'],
        rarity=data['rarity'],
        usetext=data['usetext'],
        description=data['description']
    )

    if 'stackable' in data:
        item.stackable = True

    return item

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
#                   'All the lib of a solid, medieval-style set of plated leg armour stand before you; tassets, '
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
