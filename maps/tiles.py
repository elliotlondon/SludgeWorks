from string import digits
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
        ("name", "U", 64),  # Name of the tile for ease of access
        ("walkable", np.bool),  # True if this tile can be walked over.
        ("transparent", np.bool),  # True if this tile doesn"t block FOV.
        ("dark", graphic_dt),  # Graphics for when this tile is not in FOV.
        ("light", graphic_dt),  # Graphics for when the tile is in FOV.
        ("description", list),  # Description of the tile for the look menu
    ]
)


def new_tile(*, name: str,
             walkable: bool, transparent: bool,
             dark: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
             light: Tuple[int, Tuple[int, int, int], Tuple[int, int, int]],
             description: list) -> np.ndarray:
    """Helper function for defining individual tile types"""
    return np.array((name, walkable, transparent, dark, light, description), dtype=tile_dt)


def get_clean_name(tile: tile_dt) -> str:
    """Return the information of a selected tile without decoration, for use in the look menu."""
    name = tile[0]
    name = name.replace('_', '').capitalize()
    name = name.translate({ord(k): None for k in digits})

    name = name.replace("Dirt", "Cave Floor")
    name = name.replace("dirt", "Cave Floor")
    name = name.replace("Verdant", "Verdant Cave Floor")
    name = name.replace("verdant", "Verdant Cave Floor")
    name = name.replace("Down stairs", "Next Floor")
    name = name.replace("down stairs", "Next Floor")
    name = name.replace("Hole", "Chasm")
    name = name.replace("hole", "Chasm")

    return name


# SHROUD represents unexplored, unseen tiles
SHROUD = np.array((ord(" "), (255, 255, 255), (0, 0, 0)), dtype=graphic_dt)

# Floors
dirt_1 = new_tile(name="dirt_1",
                  walkable=True, transparent=True,
                  dark=(ord(" "), (255, 255, 255), (0, 0, 0)),
                  light=(ord("∙"), tcod.grey, (0, 0, 0)),
                  description=list("The dirt beneath your feet is soft and dampened by the humidity of the cave. "
                                   "Decomposing plant matter is mixed into the soil."))
dirt_2 = new_tile(name="dirt_2",
                  walkable=True, transparent=True,
                  dark=(ord(" "), (255, 255, 255), (0, 0, 0)),
                  light=(ord("'"), tcod.grey, (0, 0, 0)),
                  description=list("The dirt beneath your feet is soft and dampened by the humidity of the cave. "
                                   "Decomposing plant matter is mixed into the soil."))
dirt_3 = new_tile(name="dirt_3",
                  walkable=True, transparent=True,
                  dark=(ord(" "), (255, 255, 255), (0, 0, 0)),
                  light=(ord(","), tcod.grey, (0, 0, 0)),
                  description=list("The dirt beneath your feet is soft and dampened by the humidity of the cave. "
                                   "Decomposing plant matter is mixed into the soil."))
dirt_4 = new_tile(name="dirt_4",
                  walkable=True, transparent=True,
                  dark=(ord(" "), (255, 255, 255), (0, 0, 0)),
                  light=(ord("`"), tcod.grey, (0, 0, 0)),
                  description=list("The dirt beneath your feet is soft and dampened by the humidity of the cave. "
                                   "Decomposing plant matter is mixed into the soil."))
floor_tiles_1 = [dirt_1, dirt_2, dirt_3, dirt_4]

verdant_1 = new_tile(name="verdant_1",
                     walkable=True, transparent=True,
                     dark=(ord(" "), (255, 255, 255), (0, 0, 0)),
                     light=(ord(","), tcod.green, (0, 0, 0)),
                     description=list("Unusual tufted grass, fractal succulents and dainty flowers have sprouted here, "
                                      "abandoning photosynthesis in lieu of the sustaining properties of "
                                      "the mud they spring from."))
verdant_2 = new_tile(name="verdant_2",
                     walkable=True, transparent=True,
                     dark=(ord(" "), (255, 255, 255), (0, 0, 0)),
                     light=(ord("∙"), tcod.light_green, (0, 0, 0)),
                     description=list("Unusual tufted grass, fractal succulents and dainty flowers have sprouted here, "
                                      "abandoning photosynthesis in lieu of the sustaining properties of "
                                      "the mud they spring from."))
verdant_3 = new_tile(name="verdant_3",
                     walkable=True, transparent=True,
                     dark=(ord(" "), (255, 255, 255), (0, 0, 0)),
                     light=(ord("'"), tcod.dark_green, (0, 0, 0)),
                     description=list("Unusual tufted grass, fractal succulents and dainty flowers have sprouted here, "
                                      "abandoning photosynthesis in lieu of the sustaining properties of "
                                      "the mud they spring from."))
verdant_4 = new_tile(name="verdant_4",
                     walkable=True, transparent=True,
                     dark=(ord(" "), (255, 255, 255), (0, 0, 0)),
                     light=(ord("∙"), tcod.dark_green, (0, 0, 0)),
                     description=list("Unusual tufted grass, fractal succulents and dainty flowers have sprouted here, "
                                      "abandoning photosynthesis in lieu of the sustaining properties of "
                                      "the mud they spring from."))
verdant_chars = [",", ".", "'", "∙"]
verdant_tiles_1 = [verdant_1, verdant_2, verdant_3, verdant_4]

# Walls
wall = new_tile(name="wall",
                walkable=False, transparent=False,
                dark=(ord("▓"), tcod.grey, (0, 0, 0)),
                light=(ord("▓"), (150, 100, 50), (0, 0, 0)),
                description=list("The cave walls are made of rugged brown rock, and slick with condensation. "
                                 "Marks like writing appear in clusters, "
                                 "partially obscured by fluorescent moss."))
rubble = new_tile(name="rubble",
                  walkable=False, transparent=True,
                  dark=(ord("▲"), tcod.grey, (0, 0, 0)),
                  light=(ord("▲"), (150, 100, 50), (0, 0, 0)),
                  description=list("The instability of the SludgeWorks is obvious by the sheer quantity of "
                                   "rubble found even within the upper caves. "
                                   "Gigantic boulders embedded with unknown fossils block your path. "))

# Liquids
water = new_tile(name="water",
                 walkable=False, transparent=True,
                 dark=(ord("≈"), tcod.grey, (0, 0, 0)),
                 light=(ord("≈"), tcod.light_blue, (0, 0, 0)),
                 description=list("Deep, murky water covered with glowing green algae forms pools that twist and "
                                  "flow, pulled lower into the caves by tiny, hidden whirlpools. Fresh water "
                                  "trickles from cracks in the ceiling, balancing the equilibrium."))
blood = new_tile(name="blood",
                 walkable=False, transparent=True,
                 dark=(ord("≈"), tcod.grey, (0, 0, 0)),
                 light=(ord("≈"), tcod.crimson, (0, 0, 0)),
                 description=list("You have never seen this much blood in one place before. A thin coagulated layer "
                                  "sits on the surface, but the liquid flows enough to never fully solidify. The stench "
                                  "is cloying and revolting."))

# Stairs
down_stairs = new_tile(
    name="down_stairs",
    walkable=True,
    transparent=True,
    dark=(ord(">"), (255, 255, 255), (0, 0, 0)),
    light=(ord(">"), (255, 255, 255), (0, 0, 0)),
    description=list("A huge, roughly circular hole in the ground stands here, well-lit by luminous greenery. "
                     "Air from the surface rushes towards the rift, carried to another unknown cavern. "
                     "You feel an impulse to continue down this route. ")
)
hole = new_tile(
    name="hole",
    walkable=False,
    transparent=True,
    dark=(ord("░"), (0, 0, 0), (36, 36, 36)),
    light=(ord("░"), (0, 0, 0), (36, 36, 36)),
    description=list("This area of the cave has recently collapsed, leaving a gigantic void, with the cave floor "
                     "serving as a cliff edge. You could jump down here, but you're certain that you would hurt "
                     "yourself on jagged cliff edge as you descend.")
)
waterfall = new_tile(
    name="waterfall",
    walkable=False,
    transparent=True,
    dark=(ord("░"), (0, 0, 0), (36, 36, 36)),
    light=(ord("↓"), tcod.light_blue, (0, 0, 0)),
    description=list("A rushing waterfall is created from a deep chasm in the ground meeting a nearby body of water, "
                     "falling into the dark depths beneath.")
)

# Other
debug = new_tile(
    name="debug",
    walkable=False,
    transparent=True,
    dark=(ord("░"), tcod.fuchsia, (0, 0, 0)),
    light=(ord("░"), tcod.fuchsia, (0, 0, 0)),
    description=list("This tile is used for debugging purposes. If you see this in game, please inform the developer.")
)
