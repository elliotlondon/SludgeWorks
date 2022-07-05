from __future__ import annotations

from typing import TYPE_CHECKING

from parts.equipment_types import EquipmentType

if TYPE_CHECKING:
    pass


class Equippable:
    def __init__(self,
                 equipment_type: EquipmentType,
                 damage_dice: int = 0,
                 damage_sides: int = 0,
                 strength_bonus: int = 0,
                 dexterity_bonus: int = 0,
                 vitality_bonus: int = 0,
                 intellect_bonus: int = 0,
                 armour_bonus: int = 0, ):
        self.equipment_type = equipment_type
        self.damage_dice = damage_dice
        self.damage_sides = damage_sides
        self.strength_bonus = strength_bonus
        self.dexterity_bonus = dexterity_bonus
        self.vitality_bonus = vitality_bonus
        self.intellect_bonus = intellect_bonus
        self.armour_bonus = armour_bonus

    def __iter__(self):
        for attr in self.__dict__.items():
            yield attr

    @staticmethod
    def to_string(slot):
        """Pass in a slot object and get its name as a nice string in return"""
        string = str(slot).replace('EquipmentType.', '').replace('_', ' ')
        return string


class Dagger(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.Main_Hand, damage_dice=1, damage_sides=3)


class LongSword(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.Main_Hand, damage_dice=1, damage_sides=4, strength_bonus=1)


class LeatherArmour(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.Head, armour_bonus=1)


class Cuirass(Equippable):
    def __init__(self) -> None:
        super().__init__(equipment_type=EquipmentType.Torso, armour_bonus=3)
