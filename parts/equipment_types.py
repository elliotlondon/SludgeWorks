from enum import Enum, auto

ARMOUR_LIST = ['Head', 'Torso', 'Hands', 'Legs', 'Feet', 'Ring', 'Neck']
WEAPON_LIST = ['Main_Hand', 'Off_Hand']


class EquipmentType(Enum):
    # Weapons
    Main_Hand = auto()
    Off_Hand = auto()
    # Armour
    Head = auto()
    Torso = auto()
    Hands = auto()
    Legs = auto()
    Feet = auto()
    Ring = auto()
    Neck = auto()
