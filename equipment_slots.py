from enum import Enum, auto


class EquipmentSlots(Enum):
    # Weapons
    MAIN_HAND = auto()
    OFF_HAND = auto()
    # Armour
    HEAD = auto()
    TORSO = auto()
    HANDS = auto()
    LEGS = auto()
    FEET = auto()
    # Jewellery
    LEFT_HAND = auto()
    RIGHT_HAND = auto()
