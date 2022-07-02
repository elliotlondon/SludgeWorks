from typing import Tuple

import numpy as np
import tcod

# Tile graphics structured type compatible with Console.tiles_rgb.
graphic_dt = np.dtype([
    ("ch", np.int32),  # Unicode codepoint.
    ("fg", "3B"),  # 3 unsigned bytes, for RGB colors.
    ("bg", "3B"),
]
)

# Tile struct used for statically defined tile data.
tile_dt = np.dtype(
    [
        ("name", "U", 16),  # Name of the tile for ease of access
        ("walkable", np.bool),  # True if this tile can be walked over.
        ("transparent", np.bool),  # True if this tile doesn"t block FOV.
        ("dark", graphic_dt),  # Graphics for when this tile is not in FOV.
        ("light", graphic_dt),  # Graphics for when the tile is in FOV.
    ]
)


def new_tile(*, name: str, walkable: bool, transparent: bool,
             dark: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
             light: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]]) -> np.ndarray:
    """
    Helper function for defining individual tile types
    """
    return np.array((name, walkable, transparent, dark, light), dtype=tile_dt)


# SHROUD represents unexplored, unseen tiles
SHROUD = np.array((ord(" "), (255, 255, 255), (0, 0, 0)), dtype=graphic_dt)

# Floors
dirt_1 = new_tile(name="dirt_1", walkable=True, transparent=True,
                  dark=(ord(" "), (255, 255, 255), (0, 0, 0)),
                  light=(ord("∙"), tcod.grey, (0, 0, 0)))
dirt_2 = new_tile(name="dirt_2", walkable=True, transparent=True,
                  dark=(ord(" "), (255, 255, 255), (0, 0, 0)),
                  light=(ord("'"), tcod.grey, (0, 0, 0)))
dirt_3 = new_tile(name="dirt_3", walkable=True, transparent=True,
                  dark=(ord(" "), (255, 255, 255), (0, 0, 0)),
                  light=(ord(","), tcod.grey, (0, 0, 0)))
dirt_4 = new_tile(name="dirt_4", walkable=True, transparent=True,
                  dark=(ord(" "), (255, 255, 255), (0, 0, 0)),
                  light=(ord("`"), tcod.grey, (0, 0, 0)))
floor_tiles_1 = [dirt_1, dirt_2, dirt_3, dirt_4]

verdant_1 = new_tile(name="verdant_1", walkable=True, transparent=True,
                     dark=(ord(" "), (255, 255, 255), (0, 0, 0)),
                     light=(ord(","), tcod.green, (0, 0, 0)))
verdant_2 = new_tile(name="verdant_2", walkable=True, transparent=True,
                     dark=(ord(" "), (255, 255, 255), (0, 0, 0)),
                     light=(ord("∙"), tcod.light_green, (0, 0, 0)))
verdant_3 = new_tile(name="verdant_3", walkable=True, transparent=True,
                     dark=(ord(" "), (255, 255, 255), (0, 0, 0)),
                     light=(ord("'"), tcod.dark_green, (0, 0, 0)))
verdant_4 = new_tile(name="verdant_4", walkable=True, transparent=True,
                     dark=(ord(" "), (255, 255, 255), (0, 0, 0)),
                     light=(ord("∙"), tcod.dark_green, (0, 0, 0)))
verdant_tiles_1 = [verdant_1, verdant_2, verdant_3, verdant_4]

# Walls
wall = new_tile(name="wall", walkable=False, transparent=False,
                dark=(ord("▓"), tcod.grey, (0, 0, 0)),
                light=(ord("▓"), (150, 100, 50), (0, 0, 0)))
rubble = new_tile(name="rubble", walkable=False, transparent=True,
                  dark=(ord("▲"), tcod.grey, (0, 0, 0)),
                  light=(ord("▲"), (150, 100, 50), (0, 0, 0)))

# Liquids
water = new_tile(name="water", walkable=False, transparent=True,
                 dark=(ord("≈"), tcod.grey, (0, 0, 0)),
                 light=(ord("≈"), tcod.light_blue, (0, 0, 0)))

# Stairs
down_stairs = new_tile(
    name="down_stairs",
    walkable=True,
    transparent=True,
    dark=(ord(">"), (255, 255, 255), (0, 0, 0)),
    light=(ord(">"), (255, 255, 255), (0, 0, 0)),
)
hole = new_tile(
    name="hole",
    walkable=False,
    transparent=True,
    dark=(ord("░"), (0, 0, 0), (36, 36, 36)),
    light=(ord("░"), (0, 0, 0), (36, 36, 36)),
)
waterfall = new_tile(
    name="waterfall",
    walkable=False,
    transparent=True,
    dark=(ord("░"), (0, 0, 0), (36, 36, 36)),
    light=(ord("↓"), tcod.light_blue, (0, 0, 0)),
)
