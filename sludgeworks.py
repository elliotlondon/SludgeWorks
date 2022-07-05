#!/usr/bin/env python3
import traceback
from logging import basicConfig, DEBUG

import tcod
from pathlib import Path

import core.g
import config.colour
import config.exceptions
import config.setup_game
import core.input_handlers

# Enable global debug
# basicConfig(level=DEBUG)


def main() -> None:
    screen_width = 80
    screen_height = 50

    tileset = tcod.tileset.load_tilesheet("fonts/DB-curses-12x12.PNG", 16, 16, tcod.tileset.CHARMAP_CP437)

    handler: core.input_handlers.BaseEventHandler = config.setup_game.MainMenu()

    with tcod.context.new_window(screen_width * 16, screen_height * 16, tileset=tileset, title="SludgeWorks",
                                 vsync=True) \
            as core.g.context:
        root_console = tcod.Console(screen_width, screen_height, order="F")
        try:
            while True:
                root_console.clear()
                handler.on_render(console=root_console)
                core.g.context.present(root_console)

                try:
                    for event in tcod.event.wait():
                        core.g.context.convert_event(event)
                        handler = handler.handle_events(event)
                except Exception:  # Handle exceptions in game.
                    traceback.print_exc()  # Print error to stderr.
                    # Then print the error to the message log.
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
