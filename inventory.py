import tcod as libtcod
from game_messages import Message


class Inventory:
    def __init__(self, capacity):
        self.capacity = capacity
        self.inv_items = []
        self.equip_items = []

    @staticmethod
    def spawn_with(entity, item_entity):
        """Add an item to an entity's inventory (not from the floor) and equip it, if possible."""
        results = []
        # TODO: Take equipment strength into consideration, so that monsters automatically equip the best possible
        #  armour. When implemented, this could also be used as an auto-equipper!!!
        if item_entity.item.use_function is None:
            # Can you equip it? Let's do it!
            if item_entity.equippable.slot is not None:
                entity.inventory.equip_items.append(item_entity)
                entity.equipment.toggle_equip(entity, item_entity)
                if entity.name == 'Player':
                    results.append({'equip': item_entity})
            else:
                results.append({'message': Message(f'The {item_entity.name} cannot be used', libtcod.white)})
        return results

    @staticmethod
    def pick_up(entity, item):
        results = []
        if len(entity.inventory.inv_items) >= entity.inventory.capacity:
            if entity.name == 'Player':
                results.append({
                    'item_added': None,
                    'message': Message('You cannot carry any more, your inventory is full', libtcod.yellow)})
        else:
            if entity.name == 'Player':
                results.append({
                    'item_added': item,
                    'message': Message(f'{entity.name} picks up the {item.name}!', libtcod.blue)})
            entity.inventory.inv_items.append(item)
        return results

    @staticmethod
    def use(entity, item_entity, **kwargs):
        results = []
        # First, consider the case where the item is in the inventory
        if item_entity in entity.inventory.inv_items:
            if item_entity.item.use_function is None:
                # Can you equip it? Let's do it!
                if item_entity.equippable.slot is not None:
                    # Check if there's already something occupying the slot
                    for item in entity.inventory.equip_items:
                        if item.equippable.slot == item_entity.equippable.slot:
                            entity.inventory.equip(entity, item_entity)
                            if entity.name == 'Player':
                                entity.inventory.dequip(entity, item)
                                entity.inventory.equip(entity, item_entity)
                        else:
                            entity.inventory.equip(entity, item_entity)
                else:
                    results.append({'message': Message(f'The {item_entity.name} cannot be used', libtcod.white)})
            else:
                if item_entity.item.targeting and not (kwargs.get('target_x') or kwargs.get('target_y')):
                    results.append({'targeting': item_entity})
                # If it's a consumable, let's consume it!
                else:
                    kwargs = {**item_entity.item.function_kwargs, **kwargs}
                    item_use_results = item_entity.item.use_function(entity, **kwargs)
                    for item_use_result in item_use_results:
                        if item_use_result.get('consumed'):
                            entity.inventory.remove_item(entity, item_entity)
                    results.extend(item_use_results)
        # For now, equipped items can only be un-equipped
        elif item_entity in entity.inventory.equip_items:
            entity.inventory.dequip(entity, item_entity)
        return results

    @staticmethod
    def equip(entity, item):
        """Equips an item, moving it to the equipment inventory."""
        results = []
        if item in entity.inventory.inv_items:
            entity.equipment.toggle_equip(entity, item)
            entity.inventory.equip_items.append(item)
            entity.inventory.inv_items.remove(item)
            if entity.name == 'Player':
                results.append({'equipped': item, 'message': Message(f'{item.name} equipped', libtcod.white)})
                print('equip message triggered')
            else:
                results.append({'equipped': item, 'message': Message(f'{entity} equips the {item.name}',
                                                                     libtcod.white)})
        return results

    @staticmethod
    def dequip(entity, item):
        """Un-equips an item and places it in the inventory. The player gets a message because they're special."""
        results = []
        if item in entity.inventory.equip_items:
            entity.equipment.toggle_equip(entity, item)
            entity.inventory.inv_items.append(item)
            entity.inventory.equip_items.remove(item)
            if entity.name == 'Player':
                results.append({'dequipped': item, 'message': Message('{0} un-equipped'.format(item.name),
                                                                      libtcod.white)})
            else:
                results.append({'dequipped': item, 'message': Message(f'{entity} un-equips the {item.name}',
                                                                     libtcod.white)})
            if len(entity.inventory.inv_items) == entity.inventory.capacity:
                entity.inventory.drop_item(entity, item)
                if entity.name == 'Player':
                    results.append({'message': Message('Inventory full, {0} dropped'.format(item.name), libtcod.white)})
        return results

    @staticmethod
    def remove_item(entity, item):
        """Completely removes an object from existence directly from the equipment or inventory."""
        if item in entity.inventory.inv_items:
            entity.inventory.inv_items.remove(item)
        elif item in entity.inventory.equip_items:
            entity.inventory.equip_items.remove(item)

    @staticmethod
    def drop_item(entity, item):
        """Removes an item from the game and places it at the feet of whatever dropped it."""
        results = []
        item.x = entity.x
        item.y = entity.y
        if item in entity.inventory.equip_items:
            entity.inventory.dequip(entity, item)
        entity.inventory.remove_item(entity, item)
        if entity.name == 'Player':
            results.append({'item_dropped': item, 'message': Message('{0} dropped'.format(item.name),
                                                                     libtcod.white)})
        return results

    @staticmethod
    def drop_all(entity, entities):
        """I've fallen and I can't get up! (drops everything at your current location, including equipped items)"""
        results = []
        for item in entity.inventory.equip_items:
            entity.equipment.toggle_equip(entity, item)
        for item in entity.inventory.inv_items:
            entity.inventory.drop_item(entity, item)
            x = entity.x
            y = entity.y
            entities.append(item(x, y))
        if entity.name == 'Player':
            results.append({'message': Message('You remove all of your armour and drop it', libtcod.white)})
        return results
