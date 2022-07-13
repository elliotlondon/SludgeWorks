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
from config.inputs import YESNO_KEYS
from core.engine import Engine
from data.item_factory import create_item_from_json
from data.monster_factory import create_monster_from_json
from maps.game_map import GameWorld


save_location = Path("savegames/savegame.sav")


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
                load_game(save_location)
                return core.input_handlers.MainGameEventHandler()
            except FileNotFoundError:
                return MainMenuPopupMessage(self, "No saved game to load.")
            except Exception as exc:
                traceback.print_exc()  # Print to stderr.
                return MainMenuPopupMessage(self, f"Failed to load save:\n{exc}")
        elif event.sym == tcod.event.K_n:
            if Path.exists(save_location):
                return SaveExistsEventHandler(self)
            else:
                new_game()
                return core.input_handlers.MainGameEventHandler()
        return None


class MainMenuPopupMessage(core.input_handlers.BaseEventHandler):
    """Display a popup text window."""

    def __init__(self, parent_handler: core.input_handlers.BaseEventHandler, text: str):
        self.parent = parent_handler
        self.text = text

    def on_render(self, console: tcod.Console) -> None:
        """Render the parent and dim the result, then print the message on top."""
        self.parent.on_render(console)

        width = len(self.text) + 4
        height = 6
        x = console.width // 2 - int(width / 2)
        y = console.height // 2 - int(height / 2)

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title='',
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0)
        )
        console.print(x=x + int(width / 2), y=y + 2, string=self.text, alignment=tcod.CENTER)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[core.input_handlers.BaseEventHandler]:
        """Any key returns to the parent handler."""
        return self.parent


class SaveExistsEventHandler(core.input_handlers.BaseEventHandler):
    """Check to see if a saved game already exists. If so, return a popup confirming whether to proceed."""
    def __init__(self, parent_handler: core.input_handlers.BaseEventHandler):
        self.parent = parent_handler

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[core.input_handlers.MainGameEventHandler or MainMenu]:
        if event.sym in config.inputs.YESNO_KEYS:
            if event.sym not in (tcod.event.K_n, tcod.event.K_ESCAPE):
                new_game()
                return core.input_handlers.MainGameEventHandler()
            else:
                return MainMenu()

    def on_render(self, console: tcod.Console) -> None:
        """Create the popup window allowing the user to choose whether to descend"""
        title = "┤WARNING: Saved game already exists!├"
        self.parent.on_render(console)
        width = len(title) + 6
        height = 8
        x = console.width // 2 - int(width / 2)
        y = console.height // 2 - height

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title='',
            clear=True,
            fg=tcod.white,
            bg=(0, 0, 0),
        )
        console.print(console.width // 2, y, title,
                      alignment=tcod.constants.CENTER, fg=tcod.white)
        console.print(console.width // 2, y + 2, f"Starting a new game will",
                      alignment=tcod.constants.CENTER, fg=tcod.white)
        console.print(console.width // 2, y + 3, f"overwrite your existing save.",
                      alignment=tcod.constants.CENTER, fg=tcod.white)
        console.print(console.width // 2, y + 5, f"Start new game?",
                      alignment=tcod.constants.CENTER, fg=tcod.white)
        console.print(x=console.width // 2 - 6, y=y + 7, string=f"[Y]: Yes",
                      alignment=tcod.constants.CENTER, fg=tcod.white)
        console.print(x=console.width // 2 + 6, y=y + 7, string=f"[N]: No",
                      alignment=tcod.constants.CENTER, fg=tcod.white)

