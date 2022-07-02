from __future__ import annotations

from typing import List, TYPE_CHECKING

from lib.base_component import BaseComponent

if TYPE_CHECKING:
    from lib.entity import Actor, Item


class Inventory(BaseComponent):
    parent: Actor

    def __init__(self, capacity: int):
        self.capacity = capacity
        self.items: List[Item] = []
        # self.inv_items: List[Item] = []
        # self.equip_items = []

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
    # def pick_up(entity, item):
    #     results = []
    #     if len(entity.inventory.inv_items) >= entity.inventory.capacity:
    #         if entity.name == 'Player':
    #             results.append({
    #                 'item_added': None,
    #                 'message': Message('You cannot carry any more, your inventory is full', tcod.yellow)})
    #     else:
    #         if entity.name == 'Player':
    #             results.append({
    #                 'item_added': item,
    #                 'message': Message(f'{entity.name} picks up the {item.name}!', tcod.blue)})
    #         entity.inventory.inv_items.append(item)
    #     return results

    # @staticmethod
    # def use(entity, item_entity, **kwargs):
    #     results = []
    #     # First, consider the case where the item is in the inventory
    #     if item_entity in entity.inventory.inv_items:
    #         if item_entity.item.use_function is None:
    #             # Can you equip it? Let's do it!
    #             if item_entity.equippable.slot:
    #                 # Check if there's already something occupying the slot
    #                 if entity.equipment.check_if_occupied(entity, item_entity):
    #                     for item in entity.inventory.equip_items:
    #                         if item.equippable.slot == item_entity.equippable.slot:
    #                             entity.inventory.dequip(entity, item)
    #                             entity.inventory.equip(entity, item_entity)
    #                             results.append(
    #                                 {'equipped': item_entity, 'message': Message(f'{item_entity.name} equipped',
    #                                                                              tcod.white)})
    #                         else:
    #                             results = entity.inventory.equip(entity, item_entity)
    #                 else:
    #                     results = entity.inventory.equip(entity, item_entity)
    #             else:
    #                 results.append({'message': Message(f'The {item_entity.name} cannot be used', tcod.white)})
    #         else:
    #             if item_entity.item.targeting and not (kwargs.get('target_x') or kwargs.get('target_y')):
    #                 results.append({'targeting': item_entity})
    #             # If it's a consumable, let's consume it!
    #             else:
    #                 kwargs = {**item_entity.item.function_kwargs, **kwargs}
    #                 item_use_results = item_entity.item.use_function(entity, **kwargs)
    #                 for item_use_result in item_use_results:
    #                     if item_use_result.get('consumed'):
    #                         entity.inventory.remove_item(entity, item_entity)
    #                 results.extend(item_use_results)
    #     # For now, equipped items can only be un-equipped
    #     elif item_entity in entity.inventory.equip_items:
    #         entity.inventory.dequip(entity, item_entity)
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

    # @staticmethod
    # def remove_item(entity, item):
    #     """Completely removes an object from existence directly from the equipment or inventory."""
    #     if item in entity.inventory.inv_items:
    #         entity.inventory.inv_items.remove(item)
    #     elif item in entity.inventory.equip_items:
    #         entity.inventory.equip_items.remove(item)

    def drop(self, item: Item) -> None:
        """
        Removes an item from an inventory and restores it to the game map at the drop location.
        """
        # if item in entity.inventory.equip_items:
        #     entity.inventory.dequip(entity, item)

        self.items.remove(item)
        item.place(self.parent.x, self.parent.y, self.gamemap)

        if self.parent.name == 'Player':
            self.engine.message_log.add_message(f"You drop the {item.name}.")
        else:
            self.engine.message_log.add_message(f"{self.parent.name} drops the {item.name}.")

    # @staticmethod
    # def drop_all(entity, entities):
    #     """Drops everything at your current location, including equipped items"""
    #     for item in entity.inventory.equip_items:
    #         entity.inventory.dequip(entity, item)
    #     for item in entity.inventory.inv_items:
    #         item.x = entity.x
    #         item.y = entity.y
    #         entities.append(item)
