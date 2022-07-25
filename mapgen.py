"""Utility script for checking, debugging and iterating map generation"""
from typing import Optional

import lzma
import pickle
import traceback
from pathlib import Path

import tcod

from maps.game_map import GameWorld
import copy
from data.monster_factory import create_monster_from_json
from core.engine import Engine
import config.inputs
import config.colour
import config.exceptions
import config.setup_game
import core.g
import core.input_handlers
from core.actions import Action


def main():
    screen_width = core.g.screen_width
    screen_height = core.g.screen_height

    tileset = tcod.tileset.load_tilesheet("fonts/DB-curses-12x12.PNG", 16, 16, tcod.tileset.CHARMAP_CP437)
    handler: core.input_handlers.BaseEventHandler = MapGenMainMenu()

    with tcod.context.new_window(screen_width * 16, screen_height * 16, tileset=tileset, title="SludgeWorks",
                                 vsync=True) \
            as core.g.context:
        core.g.console = tcod.Console(screen_width, screen_height, order="F")
        try:
            while True:
                core.g.console.clear()
                handler.on_render(console=core.g.console)
                core.g.context.present(core.g.console)

                try:
                    for event in tcod.event.get():
                        core.g.context.convert_event(event)
                        handler = handler.handle_events(event)
                except Exception:
                    traceback.print_exc()
                    if isinstance(handler, core.input_handlers.EventHandler):
                        core.g.engine.message_log.add_message(traceback.format_exc(), config.colour.error)
        except SystemExit:
            raise


class MapGenMainMenu(core.input_handlers.BaseEventHandler):
    """Main menu for mapgen."""

    def on_render(self, console: tcod.Console) -> None:
        """Render the main menu on a background image."""
        background_image = tcod.image.load("assets/mapgen_image.png")[:, :, :3]
        console.draw_semigraphics(background_image, 0, 0)

        width = 32
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
        console.print(x=x + int(width / 2), y=y, string="┤SludgeWorks MapGen├",
                      fg=config.colour.menu_text, alignment=tcod.CENTER)

        console.print(x=x + 1, y=y + 2, string="[N] Generate new GameWorld",
                      fg=config.colour.menu_text, alignment=tcod.LEFT)
        console.print(x=x + 1, y=y + 4, string="[Q / Esc] Quit",
                      fg=config.colour.menu_text, alignment=tcod.LEFT)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[core.input_handlers.BaseEventHandler]:
        if event.sym == tcod.event.K_n:
            new_gameworld()
            return MapGenEventHandler()
        elif event.sym == tcod.event.K_ESCAPE or event.sym == tcod.event.K_q:
            raise SystemExit()

        return None


class MapGenEventHandler(core.input_handlers.EventHandler):
    def handle_events(self, event: tcod.event.Event) -> core.input_handlers.BaseEventHandler:
        """Handle an event, perform any actions, then return the next active event handler."""
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, core.input_handlers.EventHandler):
            return action_or_state
        if isinstance(action_or_state, Action) and self.handle_action(action_or_state):
            return self

        return self

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[core.input_handlers.ActionOrHandler]:
        action: Optional[Action] = None

        key = event.sym
        modifier = event.mod

        # Settings
        if key == tcod.event.K_ESCAPE:
            return MapGenEscMenuHandler()
        elif key == tcod.event.K_r:
            new_gameworld()
            return self

        return action


class MapGenEscMenuHandler(core.input_handlers.AskUserEventHandler):
    """Handler for the menu which appears when the user presses Esc while inside the main game loop."""

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)
        width = 34
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
            fg=tcod.white,
            bg=(0, 0, 0),
        )
        console.print(console.width // 2, y, f"┤Esc. Menu├",
                      alignment=tcod.constants.CENTER, fg=tcod.white)
        console.print(x=x + 1, y=y + 2, string=f"[S]: Save map",
                      alignment=tcod.constants.LEFT, fg=tcod.white)
        console.print(x=x + 1, y=y + 3, string=f"[Q]: Save & Quit to Main Menu",
                      alignment=tcod.constants.LEFT, fg=tcod.white)
        console.print(x=x + 1, y=y + 4, string=f"[Esc]: Quit without Saving",
                      alignment=tcod.constants.LEFT, fg=tcod.white)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[core.input_handlers.ActionOrHandler]:
        key = event.sym
        if key == tcod.event.K_s:
            save_map(Path("maps/map.sav"))
            return config.setup_game.MainMenuPopupMessage(self, "GameWorld saved.")
        elif key == tcod.event.K_q:
            save_map(Path("maps/map.sav"))
            return MapGenMainMenu()
        elif key == tcod.event.K_ESCAPE:
            raise SystemExit()


def new_gameworld():
    """Create a new GameWorld object and generate the first floor."""
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
    for x in range(engine.game_map.width):
        for y in range(engine.game_map.height):
            engine.game_map.explored[x, y] = True
    engine.update_fov()

    core.g.engine = engine
    engine.message_log.add_message(f"MapGen successful: floor {core.g.engine.game_world.current_floor}",
                                   config.colour.use)
    return engine


def save_map(path: Path) -> None:
    """If an engine is active then save it."""
    if not hasattr(core.g, "engine"):
        return  # If called before a new game is started then g.engine is not assigned.
    path.write_bytes(lzma.compress(pickle.dumps(core.g.engine.game_world)))
    print("GameWorld saved.")


if __name__ == "__main__":
    main()
