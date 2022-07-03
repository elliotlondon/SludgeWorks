from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from lib.base_component import BaseComponent
from lib.equipment_types import EquipmentType
import core.g

if TYPE_CHECKING:
    from entity import Actor, Item


class Equipment(BaseComponent):
    parent: Actor

    def __init__(self,
                 main_hand: Optional[Item] = None,
                 off_hand: Optional[Item] = None,
                 head: Optional[Item] = None,
                 torso: Optional[Item] = None,
                 hands: Optional[Item] = None,
                 legs: Optional[Item] = None,
                 feet: Optional[Item] = None,
                 left_hand: Optional[Item] = None,
                 right_hand: Optional[Item] = None):
        self.main_hand = main_hand
        self.off_hand = off_hand
        self.head = head
        self.torso = torso
        self.hands = hands
        self.legs = legs
        self.feet = feet
        self.left_hand = left_hand
        self.right_hand = right_hand

    def __iter__(self):
        for attr in self.__dict__.items():
            yield attr

    @property
    def total(self):
        methods = 0
        for i in self:
            methods += 1
        return methods

    @property
    def damage_dice(self):
        damage_dice = 0
        if self.main_hand and self.main_hand.equippable:
            damage_dice = self.main_hand.equippable.damage_dice
        return damage_dice

    @property
    def damage_sides(self):
        damage_sides = 0
        if self.main_hand and self.main_hand.equippable:
            damage_sides = self.main_hand.equippable.damage_sides
        return damage_sides

    @property
    def strength_bonus(self) -> int:
        bonus = 0
        for x in self.__dict__:
            if getattr(self, x) and self.__dict__[x].equippable:
                bonus += self.__dict__[x].equippable.strength_bonus
        return bonus

    @property
    def dexterity_bonus(self):
        bonus = 0
        for x in self.__dict__:
            if getattr(self, x) and self.__dict__[x].equippable:
                bonus += self.__dict__[x].equippable.dexterity_bonus
        return bonus

    @property
    def vitality_bonus(self):
        bonus = 0
        for x in self.__dict__:
            if getattr(self, x) and self.__dict__[x].equippable:
                bonus += self.__dict__[x].equippable.vitality_bonus
        return bonus

    @property
    def intellect_bonus(self):
        bonus = 0
        for x in self.__dict__:
            if getattr(self, x) and self.__dict__[x].equippable:
                bonus += self.__dict__[x].equippable.intellect_bonus
        return bonus

    @property
    def armour_bonus(self):
        bonus = 0
        for x in self.__dict__:
            if getattr(self, x) and self.__dict__[x].equippable:
                bonus += self.__dict__[x].equippable.armour_bonus
        return bonus

    def item_is_equipped(self, item: Item) -> bool:
        return self.main_hand == item or self.off_hand == item or \
               self.head == item or self.torso == item or self.legs == item or self.feet == item or \
               self.left_hand == item or self.right_hand == item

    def unequip_message(self, item_name: str) -> None:
        core.g.engine.message_log.add_message(f"You remove the {item_name}.")

    def equip_message(self, item_name: str) -> None:
        core.g.engine.message_log.add_message(f"You equip the {item_name}.")

    def equip_to_slot(self, slot: str, item: Item, add_message: bool) -> None:
        current_item = getattr(self, slot)

        if current_item is not None:
            self.unequip_from_slot(slot, add_message)

        setattr(self, slot, item)

        if add_message:
            self.equip_message(item.name)

    def unequip_from_slot(self, slot: str, add_message: bool) -> None:
        current_item = getattr(self, slot)

        if add_message:
            self.unequip_message(current_item.name)

        setattr(self, slot, None)

    def toggle_equip(self, equippable_item: Item, add_message: bool = True) -> None:
        if equippable_item.equippable:
            type = equippable_item.equippable.equipment_type
            if type == EquipmentType.Main_Hand:
                slot = "main_hand"
            elif type == EquipmentType.Off_Hand:
                slot = "off_hand"
            elif type == EquipmentType.Head:
                slot = "head"
            elif type == EquipmentType.Torso:
                slot = "torso"
            elif type == EquipmentType.Legs:
                slot = "legs"
            elif type == EquipmentType.Hands:
                slot = "hands"
            elif type == EquipmentType.Feet:
                slot = "feet"
            elif type == EquipmentType.Left_Hand:
                slot = "left_hand"
            elif type == EquipmentType.Right_Hand:
                slot = "right_hand"

        if getattr(self, slot) == equippable_item:
            self.unequip_from_slot(slot, add_message)
        else:
            self.equip_to_slot(slot, equippable_item, add_message)

    @staticmethod
    def check_if_occupied(entity, equippable_entity):
        """This function formally swaps the object attributes of two items, or assigns one if there's no current one."""
        slot = equippable_entity.equippable.slot
        for x in vars(EquipmentType):
            if getattr(EquipmentType, x) == slot:
                if getattr(entity.equipment, x.lower()):
                    return True
                else:
                    return False

    # @staticmethod
    # def toggle_equip(entity, equippable_entity):
    #     """This function formally swaps the object attributes of two items, or assigns one if there's no current one."""
    #     slot = equippable_entity.equippable.slot
    #     for x in vars(EquipmentType):
    #         if getattr(EquipmentType, x) == slot:
    #             if getattr(entity.equipment, x.lower()) == equippable_entity:
    #                 setattr(entity.equipment, x.lower(), None)
    #             else:
    #                 setattr(entity.equipment, x.lower(), equippable_entity)

