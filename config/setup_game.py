"""Handle the loading and initialization of game sessions."""
from __future__ import annotations

import copy
import lzma
import pickle
import traceback
from pathlib import Path
from typing import Optional

import tcod

import config.colour
import core.g
import core.input_handlers
import maps.item_factory
import maps.monster_factory
from core.engine import Engine
from maps.game_map import GameWorld

# Load the background image and remove the alpha channel.
background_image = tcod.image.load("assets/sludge_background.png")[:, :, :3]


def new_game() -> Engine:
    """Return a brand new game session as an Engine instance."""
    map_width = 80
    map_height = 43

    room_max_size = 10
    room_min_size = 6
    max_rooms = 25

    player = copy.deepcopy(maps.monster_factory.player)

    engine = Engine(player=player)

    engine.game_world = GameWorld(
        engine=engine,
        max_rooms=max_rooms,
        room_min_size=room_min_size,
        room_max_size=room_max_size,
        map_width=map_width,
        map_height=map_height,
    )
    engine.game_world.generate_floor()
    engine.update_fov()

    engine.message_log.add_message(
        "You enter the Sludgeworks, unable to climb back out. You must progress deeper...", config.colour.welcome_text
    )

    # Spawn starting player equipment
    dagger = copy.deepcopy(maps.item_factory.dagger)
    leather_armor = copy.deepcopy(maps.item_factory.leather_armor)

    dagger.parent = player.inventory
    leather_armor.parent = player.inventory

    player.inventory.items.append(dagger)
    player.equipment.toggle_equip(dagger, add_message=False)

    player.inventory.items.append(leather_armor)
    player.equipment.toggle_equip(leather_armor, add_message=False)

    core.g.engine = engine
    return engine


def save_game(path: Path) -> None:
    """If an engine is active then save it."""
    if not hasattr(core.g, "engine"):
        return  # If called before a new game is started then g.engine is not assigned.
    path.write_bytes(lzma.compress(pickle.dumps(core.g.engine)))
    print("Game saved.")


def load_game(path: Path) -> Engine:
    """Load an Engine instance from a file."""
    engine = pickle.loads(lzma.decompress(path.read_bytes()))
    assert isinstance(engine, Engine)
    core.g.engine = engine
    return engine


class MainMenu(core.input_handlers.BaseEventHandler):
    """Handle the main menu rendering and input."""

    def on_render(self, console: tcod.Console) -> None:
        """Render the main menu on a background image."""
        console.draw_semigraphics(background_image, 0, 0)

        console.print(
            console.width // 2,
            console.height // 2 - 4,
            "SLUDGEWORKS",
            fg=config.colour.menu_title,
            alignment=tcod.CENTER,
        )

        menu_width = 24
        for i, text in enumerate(
                ["[N] New game", "[C] Continue", "[Q] Quit"]
        ):
            console.print(
                console.width // 2,
                console.height // 2 - 2 + i,
                text.ljust(menu_width),
                fg=config.colour.menu_text,
                bg=config.colour.black,
                alignment=tcod.CENTER,
                bg_blend=tcod.BKGND_ALPHA(64),
            )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[core.input_handlers.BaseEventHandler]:
        if event.sym in (tcod.event.K_q, tcod.event.K_ESCAPE):
            raise SystemExit()
        elif event.sym == tcod.event.K_c:
            try:
                load_game(Path("savegames/savegame.sav"))
                return core.input_handlers.MainGameEventHandler()
            except FileNotFoundError:
                return core.input_handlers.PopupMessage(self, "No saved game to load.")
            except Exception as exc:
                traceback.print_exc()  # Print to stderr.
                return core.input_handlers.PopupMessage(self, f"Failed to load save:\n{exc}")
        elif event.sym == tcod.event.K_n:
            new_game()
            return core.input_handlers.MainGameEventHandler()

        return None
