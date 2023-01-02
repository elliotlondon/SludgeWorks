from __future__ import annotations

import copy
import math
from typing import Optional, Tuple, Type, TypeVar, TYPE_CHECKING, Union, List

import tcod

import parts.effects
import core.g
from core.render_functions import RenderOrder
from parts.level import Level

if TYPE_CHECKING:
    from parts.ai import BaseAI
    from parts.fighter import Fighter
    from parts.consumable import Consumable
    from parts.equipment import Equipment
    from parts.equippable import Equippable
    from parts.inventory import Inventory
    from maps.game_map import GameMap
    from parts.mutations import Mutation

T = TypeVar("T", bound="Entity")


class Entity:
    """A generic parent object to represent players, enemies, items, etc."""

    parent: Union[GameMap, Inventory]

    def __init__(self,
                 parent: Optional[GameMap] = None,
                 x: int = 0,
                 y: int = 0,
                 char: str = "?",
                 colour: Tuple[int, int, int] = (255, 255, 255),
                 tag: str = "<Undefined>",
                 name: str = "<Undefined>",
                 blocks_movement: bool = False,
                 description="<Blank>",
                 render_order=RenderOrder.CORPSE,
                 fighter: Optional[parts.fighter.Fighter] = None,
                 ai: Optional[parts.ai.BaseAI] = None,
                 item: Optional[parts.entity.Item] = None,
                 inventory: Optional[parts.inventory.Inventory] = None,
                 equipment: Optional[parts.equipment.Equipment] = None,
                 equippable: Optional[parts.equippable.Equippable] = None,
                 active_effects: Optional[List[parts.effects.Effect]] = None,
                 ):
        if active_effects is None:
            active_effects = []
        self.x = x
        self.y = y
        self.char = char
        self.colour = colour
        self.name = name
        self.tag = tag
        self.description = description
        self.blocks_movement = blocks_movement
        if parent:
            # If parent isn't provided now then it will be set later.
            self.parent = parent
            parent.entities.add(self)
        self.render_order = render_order
        self.fighter = fighter
        self.ai = ai
        self.item = item
        self.inventory = inventory
        self.equipment = equipment
        self.equippable = equippable
        self.active_effects = active_effects

        if self.fighter:
            self.fighter.owner = self
        if self.ai:
            self.ai.owner = self
        if self.item:
            self.item.owner = self
        if self.inventory:
            self.inventory.owner = self
        if self.equipment:
            self.equipment.owner = self
        if self.equippable:
            self.equippable.owner = self
            if not self.item:
                item = Item(
                    description="<Undefined>"
                )
                self.item = item
                self.item.owner = self
        if self.active_effects:
            self.active_effects.owner = self

    @property
    def gamemap(self) -> GameMap:
        return self.parent.gamemap

    def spawn(self: T, gamemap: GameMap, x: int, y: int) -> T:
        """Spawn a copy of this instance at the given location."""
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.parent = gamemap
        gamemap.entities.add(clone)
        return clone

    def spawn_quietly(self: T, gamemap: GameMap, x: int, y: int):
        """As above but does not return."""
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.parent = gamemap
        gamemap.entities.add(clone)

    def place(self, x: int, y: int, gamemap: Optional[GameMap] = None) -> None:
        """Place this entity at a new location.  Handles moving across GameMaps."""
        self.x = x
        self.y = y
        if gamemap:
            if hasattr(self, "parent"):  # Possibly uninitialized.
                if self.parent is self.gamemap:
                    self.gamemap.entities.remove(self)
            self.parent = gamemap
            gamemap.entities.add(self)

    def distance(self, x: int, y: int) -> float:
        """
        Return the distance between the current entity and the given (x, y) coordinate.
        """
        return math.sqrt((x - self.x) ** 2 + (y - self.y) ** 2)

    def move(self, dx, dy) -> None:
        self.y += dy
        self.x += dx

    def teleport(self, x, y) -> None:
        self.y = y
        self.x = x

    def move_towards(self, target_x, target_y, game_map, entities):
        dx = target_x - self.x
        dy = target_y - self.y
        if dx > 0:
            dx = 1
        if dx < 0:
            dx = -1
        if dy > 0:
            dy = 1
        if dy < 0:
            dy = -1
        if not (game_map.is_blocked(self.x + dx, self.y + dy) or
                get_blocking_entities_at_location(entities, self.x + dx, self.y + dy)):
            self.move(dx, dy)

    def move_astar(self, target, entities, game_map):
        # Create a FOV map that has the dimensions of the map
        fov = tcod.map_new(game_map.width, game_map.height)

        # Scan the current map each turn and set all the walls as un-walkable
        for y1 in range(game_map.height):
            for x1 in range(game_map.width):
                tcod.map_set_properties(fov, x1, y1, not game_map.tiles[x1][y1].block_sight,
                                        not game_map.tiles[x1][y1].blocked)

        # Scan all the objects to see if there are objects that must be navigated around (and obj != self/target)
        for entity in entities:
            if entity.blocks and entity != self and entity != target:
                tcod.map_set_properties(fov, entity.x, entity.y, True, False)

        # Allocate an A* path
        my_path = tcod.path_new_using_map(fov, 1.41)

        # Compute the path between self's coordinates and the target's coordinates
        tcod.path_compute(my_path, self.x, self.y, target.x, target.y)

        # Check if the path exists, and in this case, also the path is shorter than 25
        if not tcod.path_is_empty(my_path) and tcod.path_size(my_path) < 25:
            # Find the next coordinates in the computed full path
            x, y = tcod.path_walk(my_path, True)
            if x or y:
                # Set self's coordinates to the next path tile
                self.x = x
                self.y = y
        else:
            # Keep the old move function as a backup so that if there are no paths
            self.move_towards(target.x, target.y, game_map, entities)

        tcod.path_delete(my_path)

    def distance_to(self, other):
        dx = other.x - self.x
        dy = other.y - self.y
        return math.hypot(dx, dy)

    def get_effect_colours(self):
        # Return an array of all colours and rest frames for use in animation.
        if self.active_effects == []:
            return None
        elif len(self.active_effects) > 4:
            raise NotImplementedError('Visual Error: Too many applied effects for the scheduler to currently handle!')
        else:
            colours = []
            for effect in self.active_effects:
                try:
                    colours.append(tuple(effect.get_colour()))
                except TypeError:
                    pass
            return colours

class Actor(Entity):
    """An entity with an AI which may move and act within the game map."""

    def __init__(
            self,
            *,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            colour: Tuple[int, int, int] = (255, 255, 255),
            tag: str = "<Undefined>",
            name: str = "<Undefined>",
            ai_cls: Type[BaseAI],
            equipment: Equipment,
            fighter: Fighter,
            corpse: Corpse,
            inventory: Inventory,
            drop_table = Optional[dict],
            level: Level,
            description: str,
            blood: str,
            abilities: Optional[List[Mutation]] = None,  # Inherent abilities
            mutations: Optional[List[Mutation]] = None  # Added mutations/abilities
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            colour=colour,
            tag=tag,
            name=name,
            description=description,
            blocks_movement=True,
            render_order=RenderOrder.ACTOR,
        )

        self.ai: Optional[BaseAI] = ai_cls(self)
        self.equipment: Equipment = equipment
        self.equipment.parent = self
        self.fighter = fighter
        self.fighter.parent = self
        self.corpse = corpse
        self.corpse.parent = self
        self.inventory = inventory
        self.inventory.parent = self
        self.drop_table = drop_table
        self.level = level
        self.level.parent = self
        self.description = description
        self.blood = blood

        self.abilities = abilities
        if not self.abilities:
            self.abilities = []
        self.mutations = mutations
        if not self.mutations:
            self.mutations = []

    def is_stunned(self) -> bool:
        """Returns true if there is an active stun effect upon the entity."""
        for effect in self.active_effects:
            if isinstance(effect, parts.effects.StunEffect):
                return True
        return False

    @property
    def is_alive(self) -> bool:
        """Returns True as long as this actor can perform actions."""
        return bool(self.ai)

    def is_immobile(self):
        """Returns True if the actor cannot move."""
        return False

    def trigger_active_effects(self):
        """Function to be performed at the end of a turn. All active effects currently applied to the Actor are
        cycled through, and their effects are performed."""
        if self.active_effects:
            for effect in self.active_effects:
                if self.is_alive:
                    if effect.turns > 0:
                            effect.tick()
                    else:
                        effect.expiry_message()
                        self.active_effects.remove(effect)

    def mutate(self, mutation: parts.mutations.Mutation) -> Optional[str]:
        """Function to add a mutation to an Actor."""
        for i in self.mutations:
            if i.name == mutation.name:
                raise AttributeError(f"Attempted to add mutation {mutation.name} to {self.name}, but"
                                     f"this entity already has this mutation.")
        self.mutations.append(mutation)
        self.abilities.append(mutation)

        if self.name == 'Player':
            if mutation.message != "<Undefined>":
                return mutation.message + ' '
            else:
                return ''


class Item(Entity):
    """Items which may be placed upon the game map, found in inventories, and can be used or equipped."""

    def __init__(
            self,
            *,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            colour: Tuple[int, int, int] = (255, 255, 255),
            tag: str = "<Undefined>",
            name: str = "<Undefined>",
            consumable: Optional[Consumable] = None,
            equippable: Optional[Equippable] = None,
            stackable: Optional[bool] = False,
            depth=0,
            rarity=None,
            usetext: str = "<Undefined>",
            description: str
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            colour=colour,
            name=name,
            tag=tag,
            blocks_movement=False,
            render_order=RenderOrder.ITEM,
            description=description
        )

        self.consumable = consumable
        if self.consumable:
            self.consumable.parent = self

        self.equippable = equippable
        if self.equippable:
            self.equippable.parent = self

        self.stackable = stackable
        if self.stackable:
            self.stackable.parent = self

        # Item string colour when viewed in a menu. Defaults to object colour
        self.str_colour = colour

        # Quality
        self.depth = depth
        self.rarity = rarity

        self.usetext = usetext
        self.description = description


class Corpse(Entity):
    """An entity which is spawned upon the death of its parent."""

    def __init__(
            self,
            *,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            colour: Tuple[int, int, int] = (255, 255, 255),
            name: str = "<Unnamed>",
            description: str
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            colour=colour,
            name=name,
            blocks_movement=False,
            render_order=RenderOrder.CORPSE,
            description=description
        )

        self.description = description


class StaticObject(Entity):
    """An entity which exists in place on the game map and can be interacted with, but blocks movement and cannot
    be picked up or stored in an inventory like an item."""

    def __init__(
            self,
            *,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            colour: Tuple[int, int, int] = (255, 255, 255),
            tag: str = "<Undefined>",
            name: str = "<Undefined>",
            interact_message: str = "<Undefined>",
            description: str = "<Undefined>",
            properties: Optional[List],
            used: bool = False
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            colour=colour,
            name=name,
            tag=tag,
            blocks_movement=True,
            render_order=RenderOrder.STATIC_OBJECT,
            description=description
        )

        self.base_colour = colour
        self.interact_message = interact_message
        self.properties = properties
        self.used = used


def get_blocking_entities_at_location(entities, destination_x, destination_y):
    for entity in entities:
        if entity.blocks and entity.x == destination_x and entity.y == destination_y:
            return entity

    return None
