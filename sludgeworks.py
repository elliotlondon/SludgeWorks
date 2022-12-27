#!/usr/bin/env python3
import traceback
from pathlib import Path

import tcod
from tcod.event import _SDL_TO_CLASS_TABLE, ffi, lib

import config.colour
import config.exceptions
import config.setup_game
import core.g
import core.input_handlers
import core.clock


# Enable global debug
# basicConfig(level=DEBUG)


def main() -> None:
    # Init console variables
    screen_width = core.g.screen_width
    screen_height = core.g.screen_height
    tileset = tcod.tileset.load_tilesheet("fonts/DB-curses-12x12.PNG", 16, 16, tcod.tileset.CHARMAP_CP437)

    # Init event handler and main menu
    handler: core.input_handlers.BaseEventHandler = config.setup_game.MainMenu()

    # Create the console and context
    with tcod.context.new_window(screen_width * 16, screen_height * 16, tileset=tileset, title="SludgeWorks",
                                 vsync=True) \
            as core.g.context:
        core.g.console = tcod.Console(screen_width, screen_height, order="F")
        core.g.global_clock = core.clock.GlobalClock()

        # Main game loop. After every tick and event the screen is wiped and re-rendered.
        try:
            while True:
                core.g.console.clear()
                handler.on_render(console=core.g.console)
                core.g.context.present(core.g.console)

                # Check for any events with SDL with a timeout, so that animated tiles can be refreshed.
                try:
                    sdl_event = ffi.new("SDL_Event*")
                    while lib.SDL_WaitEventTimeout(sdl_event, 4):
                        if sdl_event.type in _SDL_TO_CLASS_TABLE:
                            event = _SDL_TO_CLASS_TABLE[sdl_event.type].from_sdl_event(sdl_event)
                            core.g.context.convert_event(event)
                            handler = handler.handle_events(event)
                    core.g.global_clock.toc()
                except Exception:
                    # Print errors to sdterror and then to the in-game message log
                    traceback.print_exc()
                    if isinstance(handler, core.input_handlers.EventHandler):
                        core.g.engine.message_log.add_message(traceback.format_exc(), config.colour.error)
        except config.exceptions.QuitWithoutSaving:
            raise SystemExit()
        except SystemExit:  # Save and quit.
            config.setup_game.save_game(Path("savegames/savegame.sav"))
            raise
        except BaseException:  # Save on any other unexpected exception.
            config.setup_game.save_game(Path("savegames/savegame.sav"))
            raise


if __name__ == "__main__":
    main()
