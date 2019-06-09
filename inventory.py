import tcod as libtcod
from game_messages import Message


class Inventory:
    def __init__(self, capacity):
        self.capacity = capacity
        self.items = []

    def add_item(self, item):
        results = []

        if len(self.items) >= self.capacity:
            if self.owner.name == 'Player':
                results.append({
                    'item_added': None,
                    'message': Message('You cannot carry any more, your inventory is full', libtcod.yellow)
                })
        else:
            if self.owner.name == 'Player':
                results.append({
                    'item_added': item,
                    'message': Message('You pick up the {0}!'.format(item.name), libtcod.blue)
                })

            self.items.append(item)

        return results

    def use(self, item_entity, **kwargs):
        results = []

        item_component = item_entity.item

        if item_component.use_function is None:
            if item_entity.equippable.slot is not None:
                results.append({'equip': item_entity})
            else:
                results.append({'message': Message('The {0} cannot be used'.format(item_entity.name), libtcod.yellow)})
        else:
            if item_component.targeting and not (kwargs.get('target_x') or kwargs.get('target_y')):
                results.append({'targeting': item_entity})
            else:
                kwargs = {**item_component.function_kwargs, **kwargs}
                item_use_results = item_component.use_function(self.owner, **kwargs)

                for item_use_result in item_use_results:
                    if item_use_result.get('consumed'):
                        self.remove_item(item_entity)

                results.extend(item_use_results)

        return results

    def remove_item(self, item):
        self.items.remove(item)

    def drop_item(self, item, entity):
        results = []

        if entity.equipment:
            for i in vars(entity.equipment):                # Get a list of all attributes in the object
                if getattr(entity.equipment, i) == item:    # Check if attr. == item
                    entity.equipment.toggle_equip(item)     # Dequip

        item.x = entity.x
        item.y = entity.y
        self.remove_item(item)

        if entity.name == 'Player':
            results.append({'item_dropped': item, 'message': Message('{0} dropped'.format(item.name),
                                                                     libtcod.yellow)})

        return results

    def drop_all(self, entities):
        for item in self.items:
            if self.owner.equipment:
                for i in vars(self.owner.equipment):                # Get a list of all attributes in the object
                    if getattr(self.owner.equipment, i) == item:    # Check if attr. == item
                        self.owner.equipment.toggle_equip(item)     # Dequip

            item.x = self.owner.x
            item.y = self.owner.y
            entities.append(item)
