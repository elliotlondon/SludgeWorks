from __future__ import annotations

from dataclasses import dataclass
import copy
import math
from random import randint
from typing import Optional, Tuple, Type, TypeVar, TYPE_CHECKING, Union

import tcod

from core.render_functions import RenderOrder
from parts.level import Level

if TYPE_CHECKING:
    from parts.ai import BaseAI
    from parts.fighter import Fighter
    from parts.consumable import Consumable
    from parts.equipment import Equipment
    from parts.equippable import Equippable
    from parts.inventory import Inventory
    from maps.game_map import SimpleGameMap

T = TypeVar("T", bound="Entity")


class Entity:
    """
    A generic object to represent players, enemies, items, etc.
    """

    parent: Union[SimpleGameMap, Inventory]

    def __init__(self,
                 parent: Optional[SimpleGameMap] = None,
                 x: int = 0,
                 y: int = 0,
                 char: str = "?",
                 colour: Tuple[int, int, int] = (255, 255, 255),
                 name: str = "<Unnamed>",
                 blocks_movement: bool = False,
                 description="<Blank>",
                 render_order=RenderOrder.CORPSE,
                 fighter=None, ai=None, item=None, inventory=None, loadout=None,
                 equipment=None, equippable=None):
        self.x = x
        self.y = y
        self.char = char
        self.colour = colour
        self.name = name
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
        self.loadout = loadout
        self.equipment = equipment
        self.equippable = equippable

        if self.fighter:
            self.fighter.owner = self
        if self.ai:
            self.ai.owner = self
        if self.item:
            self.item.owner = self
        if self.inventory:
            self.inventory.owner = self
        if self.loadout:
            self.loadout.owner = self
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

    @property
    def gamemap(self) -> SimpleGameMap:
        return self.parent.gamemap

    def spawn(self: T, gamemap: SimpleGameMap, x: int, y: int) -> T:
        """Spawn a copy of this instance at the given location."""
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.parent = gamemap
        gamemap.entities.add(clone)
        return clone

    def place(self, x: int, y: int, gamemap: Optional[SimpleGameMap] = None) -> None:
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


class Actor(Entity):
    def __init__(
            self,
            *,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            colour: Tuple[int, int, int] = (255, 255, 255),
            name: str = "<Unnamed>",
            ai_cls: Type[BaseAI],
            equipment: Equipment,
            fighter: Fighter,
            inventory: Inventory,
            level: Level,
            description: str
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            colour=colour,
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
        self.inventory = inventory
        self.inventory.parent = self
        self.level = level
        self.level.parent = self
        self.description = description

    @property
    def is_alive(self) -> bool:
        """Returns True as long as this actor can perform actions."""
        return bool(self.ai)


class Item(Entity):
    def __init__(
            self,
            *,
            x: int = 0,
            y: int = 0,
            char: str = "?",
            colour: Tuple[int, int, int] = (255, 255, 255),
            name: str = "<Unnamed>",
            consumable: Optional[Consumable] = None,
            equippable: Optional[Equippable] = None,
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

        # Item string colour when viewed in a menu. Defaults to object colour
        self.str_colour = colour

        # Quality
        self.depth = depth
        self.rarity = rarity

        self.usetext = usetext
        self.description = description

tcod.light_sky


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
            name: str = "<Unnamed>",
            interact_message: str = "<Undefined>",
            description: str
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            colour=colour,
            name=name,
            blocks_movement=True,
            render_order=RenderOrder.STATIC_OBJECT,
            description=description
        )

        self.interact_message = interact_message



def get_blocking_entities_at_location(entities, destination_x, destination_y):
    for entity in entities:
        if entity.blocks and entity.x == destination_x and entity.y == destination_y:
            return entity

    return None
