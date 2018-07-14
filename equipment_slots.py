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
    FINGER_1 = auto()
    FINGER_2 = auto()
