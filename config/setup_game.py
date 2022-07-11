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
from core.engine import Engine
from data.item_factory import create_item_from_json
from data.monster_factory import create_monster_from_json
from maps.game_map import GameWorld


def new_game() -> Engine:
    """Return a brand new game session as an Engine instance."""
    player = copy.deepcopy(create_monster_from_json('data/monsters/player.json', 'player'))
    engine = Engine(player=player)

    # Settings for the first floor go here
    engine.game_world = GameWorld(
        max_rooms=25,
        room_min_size=6,
        room_max_size=10,
        map_width=80,
        map_height=43,
        engine=engine
    )
    engine.game_world.generate_floor()
    engine.update_fov()

    engine.message_log.add_message(
        "You enter the Sludgeworks, unable to climb back out. "
        "Your only choice is to descend...", config.colour.welcome_text
    )

    # Spawn starting player equipment
    dagger = copy.deepcopy(create_item_from_json('data/items/weapons.json', 'dagger'))
    leather_armor = copy.deepcopy(create_item_from_json('data/items/armour.json', 'leather_armour'))
    medkit = copy.deepcopy(create_item_from_json('data/items/healing.json', 'medkit'))

    dagger.parent = player.inventory
    leather_armor.parent = player.inventory
    medkit.parent = player.inventory

    player.inventory.items.append(dagger)
    player.equipment.toggle_equip(dagger, add_message=False)

    player.inventory.items.append(leather_armor)
    player.equipment.toggle_equip(leather_armor, add_message=False)

    player.inventory.items.extend([medkit, medkit])

    # # Debug stuff
    # twig = copy.deepcopy(maps.item_factory.teleother_twig)
    # twig.parent = player.inventory
    # player.inventory.items.append(twig)

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
        background_image = tcod.image.load("assets/menu_image.png")[:, :, :3]
        console.draw_semigraphics(background_image, 0, 0)

        menu_width = 14
        for i, text in enumerate(
                ["[N] New game", "", "[C] Continue", "", "[Q] Quit"]
        ):
            console.print(
                18,
                22 + i,
                text.ljust(menu_width),
                fg=config.colour.menu_text,
                bg=(0, 0, 0),
                alignment=tcod.CENTER
            )

        console.print(
            11,
            console.height - 2,
            "https://github.com/elliotlondon/Sludgeworks",
            fg=config.colour.menu_text,
            bg=(0, 0, 0),
            alignment=tcod.LEFT
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
