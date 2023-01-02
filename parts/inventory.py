from __future__ import annotations

import copy
from typing import List, TYPE_CHECKING

import core.g
from parts.base_component import BaseComponent

if TYPE_CHECKING:
    from parts.entity import Actor, Item, Entity
    from parts.effects import ItemModifier


class Inventory(BaseComponent):
    parent: Actor

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.items: List[Entity] = []
        self.quantities: List[int] = []

    # @staticmethod
    # def spawn_with(entity, item_entity):
    #     """Add an item to an entity's inventory (not from the floor) and equip it, if possible."""
    #     results = []
    #     # TODO: Take equipment strength into consideration, so that monsters automatically equip the best possible
    #     #  armour. When implemented, this could also be used as an auto-equipper!!!
    #     if item_entity.item.use_function is None:
    #         # Can you equip it? Let's do it!
    #         if item_entity.equippable.slot is not None:
    #             entity.inventory.equip_items.append(item_entity)
    #             entity.equipment.toggle_equip(entity, item_entity)
    #             if entity.name == 'Player':
    #                 results.append({'equip': item_entity})
    #         else:
    #             results.append({'message': Message(f'The {item_entity.name} cannot be used', tcod.white)})
    #     return results

    # @staticmethod
    # def equip(entity, item):
    #     """Equips an item, moving it to the equipment inventory."""
    #     results = []
    #     if item in entity.inventory.inv_items:
    #         entity.equipment.toggle_equip(entity, item)
    #         entity.inventory.equip_items.insert(0, item)
    #         entity.inventory.inv_items.remove(item)
    #         if entity.name == 'Player':
    #             results.append({'equipped': item, 'message': Message(f'{item.name} equipped', tcod.white)})
    #         else:
    #             results.append({'equipped': item, 'message': Message(f'{entity} equips the {item.name}',
    #                                                                  tcod.white)})
    #         print(f'entity damage dice: {entity.equipment.main_hand, entity.equipment.strength_bonus}')
    #         print(f'')
    #     return results

    # @staticmethod
    # def dequip(entity, item):
    #     """Un-equips an item and places it in the inventory. The player gets a message because they're special."""
    #     results = []
    #     if item in entity.inventory.equip_items:
    #         entity.equipment.toggle_equip(entity, item)
    #         entity.inventory.inv_items.append(item)
    #         entity.inventory.equip_items.remove(item)
    #         if entity.name == 'Player':
    #             results.append({'dequipped': item, 'message': Message(f'{item.name} un-equipped', tcod.grey)})
    #         else:
    #             results.append({'dequipped': item, 'message': Message(f'{entity} un-equips the {item.name}',
    #                                                                   tcod.grey)})
    #         if len(entity.inventory.inv_items) == entity.inventory.capacity:
    #             entity.inventory.drop_item(entity, item)
    #             if entity.name == 'Player':
    #                 results.append({'message': Message('Inventory full, {0} dropped'.format(item.name), tcod.grey)})
    #     return results

    def is_full(self) -> bool:
        """Returns true if inventory is at capacity"""
        if len(self.items) >= self.capacity:
            return True
        else:
            return False

    def sanity_check(self):
        """Check if the items and quantities are the same length"""
        if not len(self.items) == len(self.quantities):
            raise TypeError(f"Inventory crash. {len(self.items)} and {len(self.quantities)}.")

    def remove(self, item: Item):
        """Redefined list method to handle stackable items"""
        index = self.items.index(item)
        if item.stackable:
            if self.quantities[index] == 1:
                # Just one left, so pop it and the corresponding index
                self.items.pop(index)
                self.quantities.pop(index)
            elif self.quantities[index] <= 0:
                raise IndexError(f"Inventory item {item.name}, {item} has quantity {self.quantities[index]}."
                                 f"Something went wrong.")
            else:
                self.quantities[index] -= 1
        else:
            self.items.pop(index)
            self.quantities.pop(index)
        self.sanity_check()

    def drop(self, item: Item) -> None:
        """Removes an item from an inventory and restores it to the game map at the drop location."""

        # Place on map and remove from inventory
        dropped_item = copy.deepcopy(item)
        dropped_item.place(self.parent.x, self.parent.y, self.gamemap)
        self.remove(item)
        # Check to see if the item is a stack
        if item.stackable:
            if self.parent.name == 'Player':
                core.g.engine.message_log.add_message(f"You drop a {item.name}.")
            else:
                core.g.engine.message_log.add_message(f"{self.parent.name} drops a {item.name}.")
        else:
            if self.parent.name == 'Player':
                core.g.engine.message_log.add_message(f"You drop the {item.name}.")
            else:
                core.g.engine.message_log.add_message(f"{self.parent.name} drops the {item.name}.")
        self.sanity_check()


    def drop_all(self):
        """Drops everything at your current location, including equipped items."""

        for item in self.items:
            if item.equipment.item_is_equipped():
                item.equipment.unequip_from_slot()

            self.remove(item)
            item.place(self.parent.x, self.parent.y, self.gamemap)

            if self.parent.name == 'Player':
                core.g.engine.message_log.add_message(f"You drop the {item.name}.")
            else:
                core.g.engine.message_log.add_message(f"{self.parent.name} drops the {item.name}.")


    def autosort(self):
        """Automatically sorts the items and quantities according to item values and types."""

        # First sort list into consumables and weapons/armour
        equipment = []
        consumables = []
        equipment_quantities = []
        consumables_quantities = []
        for item in self.items:
            index = self.items.index(item)
            if item.equippable:
                equipment.append(item)
                equipment_quantities.append(self.quantities[index])
            else:
                consumables.append(item)
                consumables_quantities.append(self.quantities[index])

        # Now split weapons/armour lists
        weapons = []
        armour = []
        weapon_quantities = []
        armour_quantities = []
        for item in equipment:
            index = self.items.index(item)
            if item.equippable.damage_dice:
                weapons.append(item)
                weapon_quantities.append(self.quantities[index])
            else:
                armour.append(item)
                armour_quantities.append(self.quantities[index])

        # Sort all lists according to item depth and rarity
        sorted(weapons, key=lambda x: (x.depth, x.rarity))
        sorted(armour, key=lambda x: (x.depth, x.rarity))
        sorted(consumables, key=lambda x: (x.depth, x.rarity))
        new_quantities = []
        for element in (weapons + armour + consumables):
            index = self.items.index(element)
            new_quantities.append(self.quantities[index])
        self.quantities = new_quantities
        self.items = weapons + armour + consumables
