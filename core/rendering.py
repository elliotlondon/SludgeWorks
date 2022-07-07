from __future__ import annotations

import numpy as np
import tcod

import config.colour
import core.engine
import core.render_functions
import maps.game_map
from maps.tiles import SHROUD


# tile_graphics: NDArray[Any] = np.array(
#     [
#         (ord("#"), (0x80, 0x80, 0x80), (0x40, 0x40, 0x40)),  # wall
#         (ord("."), (0x40, 0x40, 0x40), (0x18, 0x18, 0x18)),  # floor
#         (ord(">"), (0xFF, 0xFF, 0xFF), (0x18, 0x18, 0x18)),  # down stairs
#     ],
#     dtype=tcod.console.rgb_graphic,
# )


def render_map(console: tcod.Console, gamemap: maps.game_map.SimpleGameMap) -> None:
    console.tiles_rgb[0:gamemap.width, 0:gamemap.height] = gamemap.tiles["dark"]
    # light = tile_graphics[gamemap.tiles]
    #
    # # Apply effects to create a darkened map of tile graphics.
    # dark = light.copy()
    # dark["fg"] //= 2
    # dark["bg"] //= 8

    # If a tile is in the "visible" array, then draw it with the "light" colors.
    # If it isn't, but it's in the "explored" array, then draw it with the "dark" colors.
    # Otherwise, the default graphic is "SHROUD".
    console.tiles_rgb[0:gamemap.width, 0:gamemap.height] = np.select(
        condlist=[gamemap.visible, gamemap.explored],
        choicelist=[gamemap.tiles["light"], gamemap.tiles["dark"]],
        default=SHROUD
    )

    for entity in sorted(gamemap.entities, key=lambda x: x.render_order.value):
        if not gamemap.visible[entity.x, entity.y]:
            continue  # Skip entities that are not in the FOV.
        console.print(entity.x, entity.y, entity.char, fg=entity.colour)


def render_ui(console: tcod.Console, engine: core.engine.Engine) -> None:
    engine.message_log.render(console=console, x=21, y=45, width=40, height=5)

    # Render hp bar
    core.render_functions.render_bar(
        console=console,
        current_value=engine.player.fighter.hp,
        max_value=engine.player.fighter.max_hp,
        x=1,
        y=45,
        bg_empty=config.colour.hp_bar_empty,
        bg_full=config.colour.hp_bar_filled,
        text=f"HP: {engine.player.fighter.hp}/{engine.player.fighter.max_hp}",
        total_width=20,
    )

    # Render xp bar
    core.render_functions.render_bar(
        console=console,
        current_value=engine.player.level.current_xp,
        max_value=engine.player.level.experience_to_next_level,
        x=1,
        y=46,
        bg_empty=config.colour.xp_bar_empty,
        bg_full=config.colour.xp_bar_filled,
        text=f"XP: {engine.player.level.current_xp}/{engine.player.level.experience_to_next_level}",
        total_width=20,
    )

    core.render_functions.render_dungeon_level(
        console=console,
        dungeon_level=engine.game_world.current_floor,
        location=(0, 47),
    )

    core.render_functions.render_names_at_mouse_location(console=console, x=21, y=44, engine=engine)
