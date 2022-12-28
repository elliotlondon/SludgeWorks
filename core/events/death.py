import os
import random
from typing import Optional
import numpy as np

import tcod

import config.exceptions
import config.inputs
import core.g
from core.input_handlers import EventHandler, BaseEventHandler

idiocy_messages = [
                "their own foolishness",
                "poor life decisions",
                "knowing too little about too much",
                "natural selection"
]
np.random.seed(random.randint(1, 100))
idiocy_message = np.random.choice(idiocy_messages)


class GameOverEventHandler(EventHandler):
    # Savegame removed immediately at the time of death.
    def __init__(self):
        if os.path.exists("savegames/savegame.sav"):
            os.remove("savegames/savegame.sav")  # Deletes the active save file.

    def on_quit(self) -> None:
        """Handle exiting out of a finished game."""
        raise config.exceptions.QuitWithoutSaving()  # Avoid saving a finished game.

    def on_render(self, console: tcod.Console) -> None:
        """Create a popup window informing the player of their death."""
        super().on_render(console)

        turns_survived = f"You survived for {core.g.engine.turn_number} turns."

        if not core.g.engine.last_actor.name or core.g.engine.last_actor.name == 'Player':
            death_message = f"Killed by {idiocy_message}."
            killer = ''
        else:
            death_message = "Killed by a "
            try:
                killer = core.g.engine.last_actor.name
            except:
                killer = "<Undefined>"

        max_len = max([len(i) for i in [death_message, turns_survived]])
        width = max_len + 10
        height = 9
        x = console.width // 2 - int(width / 2)
        y = console.height // 2 - height

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title='',
            clear=True,
            fg=tcod.dark_red,
            bg=(0, 0, 0),
        )
        console.print(x + int(width / 2), y, f"┤YOU DIED├",
                      alignment=tcod.constants.CENTER, fg=tcod.dark_red)

        console.print(x=x + 1, y=y + 2, string=death_message,
                      alignment=tcod.constants.LEFT, fg=tcod.white)
        console.print(x=x + 13, y=y + 2, string=killer,
                      alignment=tcod.constants.LEFT, fg=core.g.engine.last_actor.colour)
        console.print(x=x + 1, y=y + 3, string=turns_survived,
                      alignment=tcod.constants.LEFT, fg=tcod.white)

        console.print(x=x + 1, y=y + 5, string=f"[I]: View inventory",
                      alignment=tcod.constants.LEFT, fg=tcod.white)
        console.print(x=x + 1, y=y + 6, string=f"[M]: View message log",
                      alignment=tcod.constants.LEFT, fg=tcod.white)
        console.print(x=x + 1, y=y + 8, string=f"[ESC]: Quit",
                      alignment=tcod.constants.LEFT, fg=tcod.white)

    def ev_quit(self, event: tcod.event.Quit) -> None:
        if os.path.exists("savegames/savegame.sav"):
            os.remove("savegames/savegame.sav")  # Deletes the active save file.
        self.on_quit()

    def ev_keydown(self, event: tcod.event.KeyDown) -> BaseEventHandler:
        if event.sym == tcod.event.K_ESCAPE:
            from config.setup_game import MainMenu
            return MainMenu()
        elif event.sym == tcod.event.K_m:
            return DeadHistoryViewer()
        elif event.sym == tcod.event.K_i:
            return DeadInventoryEventHandler()


class DeadHistoryViewer(core.input_handlers.EventHandler):
    """Print the history on a larger window which can be navigated. Player is dead, so no return to main game."""

    def __init__(self):
        super().__init__()
        self.log_length = len(core.g.engine.message_log.messages)
        self.cursor = self.log_length - 1

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)  # Draw the main state as the background.

        log_console = tcod.Console(console.width - 6, console.height - 6)

        # Draw a frame with a custom banner title.
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(0, 0, log_console.width, 1, "┤Message history├", alignment=tcod.CENTER)

        # Render the message log using the cursor parameter.
        core.g.engine.message_log.render_messages(
            log_console,
            1,
            1,
            log_console.width - 2,
            log_console.height - 2,
            core.g.engine.message_log.messages[: self.cursor + 1],
        )
        log_console.blit(console, 3, 3)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[GameOverEventHandler]:
        # Fancy conditional movement to make it feel right.
        if event.sym in config.inputs.CURSOR_Y_KEYS:
            adjust = config.inputs.CURSOR_Y_KEYS[event.sym]
            if adjust < 0 and self.cursor == 0:
                # Only move from the top to the bottom when you're on the edge.
                self.cursor = self.log_length - 1
            elif adjust > 0 and self.cursor == self.log_length - 1:
                # Same with bottom to top movement.
                self.cursor = 0
            else:
                # Otherwise move while staying clamped to the bounds of the history log.
                self.cursor = max(0, min(self.cursor + adjust, self.log_length - 1))
        elif event.sym == tcod.event.K_HOME:
            self.cursor = 0  # Move directly to the top message.
        elif event.sym == tcod.event.K_END:
            self.cursor = self.log_length - 1  # Move directly to the last message.
        else:  # Any other key moves back to the main game state.
            return GameOverEventHandler()
        return None


class DeadInventoryEventHandler(core.input_handlers.AskUserEventHandler):
    """
    This handler lets the user select an item.
    What happens then depends on the subclass.
    """
    TITLE = "Your final inventory"

    def on_render(self, console: tcod.Console) -> None:
        """
        Render an inventory menu, which displays the items in the inventory. Selection not possible due to death.
        Will move to a different position based on where the player is located, so the player can always see where
        they are.
        """
        super().on_render(console)
        number_of_items_in_inventory = len(core.g.engine.player.inventory.items)

        height = number_of_items_in_inventory + 2

        if height <= 3:
            height = 3

        width = len(self.TITLE) + 20
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
            bg=(0, 0, 0),
        )
        console.print(x + 1, y, f"┤{self.TITLE}. TAB to sort├")

        if number_of_items_in_inventory > 0:
            for i, item in enumerate(core.g.engine.player.inventory.items):
                is_equipped = core.g.engine.player.equipment.item_is_equipped(item)
                item_string = f"· {item.name}"
                if is_equipped:
                    item_string = f"{item_string} (E)"

                console.print(x + 1, y + i + 1, item_string, fg=item.str_colour)
        else:
            console.print(x + 1, y + 1, "(Empty)")

    def on_exit(self) -> Optional[GameOverEventHandler]:
        """Called when the user is trying to exit or cancel an action. Return to death menu.
        """
        return GameOverEventHandler()
