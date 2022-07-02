#!/usr/bin/env python3
import traceback
from logging import basicConfig, DEBUG

import tcod

import config.colour
import config.exceptions
import config.setup_game
import core.input_handlers

# Enable global debug
basicConfig(level=DEBUG)


def save_game(handler: core.input_handlers.BaseEventHandler, filename: str) -> None:
    """If the current event handler has an active Engine then save it."""
    if isinstance(handler, core.input_handlers.EventHandler):
        handler.engine.save_as(filename)
        print("Game saved.")


def main() -> None:
    screen_width = 80
    screen_height = 50

    tileset = tcod.tileset.load_tilesheet("fonts/DB-curses-12x12.PNG", 16, 16, tcod.tileset.CHARMAP_CP437)

    handler: core.input_handlers.BaseEventHandler = config.setup_game.MainMenu()

    with tcod.context.new_window(screen_width * 16, screen_height * 16, tileset=tileset, title="SludgeWorks",
                                 vsync=True) \
            as context:
        root_console = tcod.Console(screen_width, screen_height, order="F")
        try:
            while True:
                root_console.clear()
                handler.on_render(console=root_console)
                context.present(root_console)

                try:
                    for event in tcod.event.wait():
                        context.convert_event(event)
                        handler = handler.handle_events(event)
                except Exception:  # Handle exceptions in game.
                    traceback.print_exc()  # Print error to stderr.
                    # Then print the error to the message log.
                    if isinstance(handler, core.input_handlers.EventHandler):
                        handler.engine.message_log.add_message(traceback.format_exc(), config.colour.error)
        except config.exceptions.QuitWithoutSaving:
            raise
        except SystemExit:  # Save and quit.
            save_game(handler, "savegames/savegame.sav")
            raise
        except BaseException:  # Save on any other unexpected exception.
            save_game(handler, "savegames/savegame.sav")
            raise


if __name__ == "__main__":
    main()
