from __future__ import annotations

import os
import logging
from typing import Callable, Optional, Tuple, TYPE_CHECKING, Union, List

import tcod
import numpy as np
import math
import random
import time

import config.colour
import config.inputs
import core.actions
from config.exceptions import Impossible

if TYPE_CHECKING:
    from engine import Engine
    from lib.entity import Item

ActionOrHandler = Union[core.actions.Action, "BaseEventHandler"]
"""
An event handler return value which can trigger an action or switch active handlers.
If a handler is returned then it will become the active handler for future events.
If an action is returned it will be attempted and if it's valid then
MainGameEventHandler will become the active handler.
"""


class BaseEventHandler(tcod.event.EventDispatch[ActionOrHandler]):
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle an event and return the next active event handler."""
        state = self.dispatch(event)
        if isinstance(state, BaseEventHandler):
            return state
        assert not isinstance(state, core.actions.Action), f"{self!r} can not handle actions."
        return self

    def on_render(self, console: tcod.Console) -> None:
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit) -> Optional[core.actions.Action]:
        raise SystemExit()


class PopupMessage(BaseEventHandler):
    """Display a popup text window."""

    def __init__(self, parent_handler: BaseEventHandler, text: str):
        self.parent = parent_handler
        self.text = text

    def on_render(self, console: tcod.Console) -> None:
        """Render the parent and dim the result, then print the message on top."""
        self.parent.on_render(console)
        console.tiles_rgb["fg"] //= 8
        console.tiles_rgb["bg"] //= 8

        width = len(self.text) + 4
        x = console.width // 2 - int(width / 2)
        y = console.height // 2

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=7,
            title='',
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
            decoration="╔═╗║ ║╚═╝"
        )

        console.print(x=x + 1, y=y + 1, string=self.text)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[BaseEventHandler]:
        """Any key returns to the parent handler."""
        return self.parent


class EventHandler(BaseEventHandler):
    def __init__(self, engine: Engine):
        self.engine = engine

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle events for input handlers with an engine."""
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        if self.handle_action(action_or_state):
            # A valid action was performed.
            if not self.engine.player.is_alive:
                # The player was killed sometime during or after the action.
                return GameOverEventHandler(self.engine)
            elif self.engine.player.level.requires_level_up:
                return LevelUpEventHandler(self.engine)
            return MainGameEventHandler(self.engine)  # Return to the main handler.
        return self

    def handle_action(self, action: Optional[core.actions.Action]) -> bool:
        """Handle actions returned from event methods. Returns True if the action will advance a turn.
        """
        if action is None:
            return False

        try:
            action.perform()
        except Impossible as exc:
            self.engine.message_log.add_message(exc.args[0], config.colour.impossible)
            return False  # Skip enemy turn on exceptions.

        self.engine.handle_enemy_turns()
        self.engine.update_fov()
        return True

    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        if self.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            self.engine.mouse_location = event.tile.x, event.tile.y

    def on_render(self, console: tcod.Console) -> None:
        self.engine.render(console)


class ExploreEventHandler(EventHandler):
    def __init__(self, engine: Engine):
        super().__init__(engine)
        # Init message
        self.engine.message_log.add_message(f"You begin exploring.", config.colour.yellow)
        self.path = []

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle events for input handlers with an engine."""
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        if self.handle_action(action_or_state):
            # A valid action was performed.
            if not self.engine.player.is_alive:
                # The player was killed sometime during or after the action.
                return GameOverEventHandler(self.engine)
            elif self.engine.player.level.requires_level_up:
                return LevelUpEventHandler(self.engine)
            return MainGameEventHandler(self.engine)  # Return to the main handler.
        return self

    def handle_action(self, action: Optional[core.actions.Action]):
        """Handle actions returned from event methods. Returns True if the action will advance a turn."""
        player = self.engine.player

        if action is not tcod.event.KeyDown:
            if self.actor_in_fov():
                return MainGameEventHandler(self.engine)
            try:
                path = self.explore()
                if path is not None:
                    action = core.actions.BumpAction(player, path[0] - player.x, path[1] - player.y)
                    action.perform()
                    self.engine.handle_enemy_turns()
                    self.engine.update_fov()
                    if self.actor_in_fov():
                        return MainGameEventHandler(self.engine)
                else:
                    return MainGameEventHandler(self.engine)
            except Impossible as exc:
                self.engine.message_log.add_message(exc.args[0], config.colour.impossible)
                return True  # Skip enemy turn on exceptions.
        else:
            return MainGameEventHandler(self.engine)

    def actor_in_fov(self) -> bool:
        """Check if there are any enemies in the FOV."""
        visible_tiles = np.nonzero(self.engine.game_map.visible)
        for actor in self.engine.game_map.dangerous_actors:
            if actor.x in visible_tiles[0] and actor.y in visible_tiles[1] and actor.name != 'Player':
                self.engine.message_log.add_message(f"You spot a {actor.name} and stop exploring.", config.colour.yellow)
                return True
        return False

    def explore(self) -> Optional[List]:
        """Use a dijkstra map to navigate the player towards the nearest unexplored tile."""
        game_map = self.engine.game_map
        player = self.engine.player

        unexplored_coords = []
        for y in range(self.engine.game_map.height):
            for x in range(self.engine.game_map.width):
                if not self.engine.game_map.explored[x, y] and self.engine.game_map.accessible[x, y]:
                    unexplored_coords.append((y, x))

        if logging.DEBUG >= logging.root.level:
            self.engine.message_log.add_message(f"DEBUG: Unexplored coords = {len(unexplored_coords)}", config.colour.debug)

        if len(unexplored_coords) == 0:
            self.engine.message_log.add_message("There is nowhere else to explore.", config.colour.yellow)
            return None

        # Find the nearest unexplored coords
        closest_distance = 10000

        closest_coord = None
        for y, x in unexplored_coords:
            new_distance = math.hypot(x - player.x, y - player.y)

            if new_distance < closest_distance:
                closest_distance = new_distance
                closest_coord = (x, y)

        # Try simple A*
        if closest_coord:
            if len(self.path) <= 1:
                # No path exists, so make one
                cost = np.array(self.engine.game_map.accessible, dtype=np.int8)

                # Create a graph from the cost array and pass that graph to a new pathfinder.
                graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
                pathfinder = tcod.path.Pathfinder(graph)
                pathfinder.add_root((self.engine.player.x, self.engine.player.y))  # Start position.

                # Compute the path to the destination and remove the starting point.
                self.path: List[List[int]] = pathfinder.path_to(closest_coord)[1:].tolist()
                if not self.path:
                    self.engine.message_log.add_message("You cannot explore the remaining tiles.", config.colour.yellow)
                    return None
                return self.path[0]
            else:
                # Path already exists: use it and prune it
                self.path.pop(0)
                new_coords = self.path[0]
                return new_coords

        # path_to_closest_coord = []
        #
        # if closest_coord:
        #     my_map = tcod.map_new(game_map.width, game_map.height)
        #     for y in range(game_map.height):
        #         for x in range(game_map.width):
        #             if game_map.tiles[x, y]['walkable']:
        #                 tcod.map_set_properties(my_map, x, y, True, True)
        #
        #     dij_path = tcod.dijkstra_new(my_map)
        #     tcod.dijkstra_compute(dij_path, player.x, player.y)
        #     tcod.dijkstra_path_set(dij_path, closest_coord[0], closest_coord[1])
        #
        #     # Get the path
        #     if not tcod.dijkstra_is_empty(dij_path):
        #         x, y = tcod.dijkstra_path_walk(dij_path)
        #         path_to_closest_coord.append((x, y))
        #
        #         # Move player along the path
        #         if not path_to_closest_coord:
        #             self.engine.message_log.add_message("You cannot explore the remaining tiles.", config.colour.yellow)
        #             return None
        #         else:
        #             if logging.DEBUG >= logging.root.level:
        #                 self.engine.message_log.add_message(f"DEBUG: Move position = {x, y}",
        #                                                     config.colour.debug)
        #
        #             # Return the list of walkable tiles to be performed in parent action handler
        #             return path_to_closest_coord

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """By default any key exits this input handler."""
        self.engine.message_log.add_message(f"You stop exploring.", config.colour.yellow)
        return self.on_exit()

    def on_render(self, console: tcod.Console) -> None:
        self.engine.render(console)

    def on_exit(self) -> Optional[ActionOrHandler]:
        """Called when the user is trying to exit or cancel an action.
        By default this returns to the main event handler."""
        return MainGameEventHandler(self.engine)



class MainGameEventHandler(EventHandler):
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        action: Optional[core.actions.Action] = None

        key = event.sym
        modifier = event.mod
        player = self.engine.player

        if key == tcod.event.K_PERIOD and modifier & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
            return core.actions.TakeStairsAction(player)

        if key in config.inputs.MOVE_KEYS:
            dx, dy = config.inputs.MOVE_KEYS[key]

            # Failsafe OOB check
            if not self.engine.game_map.in_bounds(player.x + dx, player.y + dy):
                self.engine.message_log.add_message("That way is blocked.", config.colour.impossible)
            elif self.engine.game_map.tiles[player.x + dx, player.y + dy]['name'] == 'hole':
                return HoleJumpEventHandler(self.engine)
            else:
                action = core.actions.BumpAction(player, dx, dy)
        elif key in config.inputs.WAIT_KEYS:
            action = core.actions.WaitAction(player)

        elif key == tcod.event.K_ESCAPE:
            raise SystemExit()
        # elif key == tcod.event.K_F11:
        #     self.engine.event_handler.toggle_fullscreen()

        elif key == tcod.event.K_m:
            return HistoryViewer(self.engine)
        elif key == tcod.event.K_SEMICOLON:
            return LookHandler(self.engine)
        elif key == tcod.event.K_c:
            return CharacterScreenEventHandler(self.engine)

        elif key == tcod.event.K_g:
            action = core.actions.PickupAction(player)
        elif key == tcod.event.K_i:
            return InventoryActivateHandler(self.engine)
        elif key == tcod.event.K_d:
            return InventoryDropHandler(self.engine)

        elif key == tcod.event.K_HASH or key == tcod.event.K_SLASH:
            return ExploreEventHandler(self.engine)

        return action

    def toggle_fullscreen(self, context: tcod.context.Context) -> None:
        """Toggle a context window between fullscreen and windowed modes."""
        if not context.sdl_window_p:
            return
        fullscreen = tcod.lib.SDL_GetWindowFlags(context.sdl_window_p) & (
                tcod.lib.SDL_WINDOW_FULLSCREEN | tcod.lib.SDL_WINDOW_FULLSCREEN_DESKTOP
        )
        tcod.lib.SDL_SetWindowFullscreen(
            context.sdl_window_p,
            0 if fullscreen else tcod.lib.SDL_WINDOW_FULLSCREEN_DESKTOP,
        )


class AskUserEventHandler(EventHandler):
    """Handles user input for actions which require special input."""

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """By default any key exits this input handler."""
        if event.sym in {  # Ignore modifier keys.
            tcod.event.K_LSHIFT,
            tcod.event.K_RSHIFT,
            tcod.event.K_LCTRL,
            tcod.event.K_RCTRL,
            tcod.event.K_LALT,
            tcod.event.K_RALT,
        }:
            return None
        return self.on_exit()

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        """By default any mouse click exits this input handler."""
        return self.on_exit()

    def on_exit(self) -> Optional[ActionOrHandler]:
        """Called when the user is trying to exit or cancel an action.

        By default this returns to the main event handler.
        """
        return MainGameEventHandler(self.engine)


# TODO: User input for username
class UsernameEventHandler(AskUserEventHandler):
    TITLE = "Please input a character name. Press # for default"


class CharacterScreenEventHandler(AskUserEventHandler):
    TITLE = "Character Sheet"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        level_str = f"Level: {self.engine.player.level.current_level}"
        xp_str = f"XP: {self.engine.player.level.current_xp}"
        xp_next_str = f"XP for next level: {self.engine.player.level.experience_to_next_level}"

        width = len(xp_next_str) + 2
        x = console.width // 2 - int(width / 2)
        y = console.height // 2

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=7,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        console.print(x=x + 1, y=y + 1, string=level_str)
        console.print(x=x + 1, y=y + 2, string=xp_str)
        console.print(x=x + 1, y=y + 3, string=xp_next_str)

        console.print(x=x + 1, y=y + 4, string=f"Strength: {self.engine.player.fighter.base_strength}")
        console.print(x=x + 1, y=y + 5, string=f"Dexterity: {self.engine.player.fighter.base_dexterity}")


class LevelUpEventHandler(AskUserEventHandler):
    TITLE = "Level Up"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        attr_str = "You have gained a level! Select an attribute to increase."

        width = len(attr_str) + 4
        x = console.width // 2 - int(width / 2)
        y = console.height // 2 - 4

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=8,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        console.print(x=x + 1, y=y + 1, string="You channel the power of your slain foes...")
        console.print(x=x + 1, y=y + 2, string=attr_str)

        console.print(
            x=x + 1,
            y=y + 4,
            string=f"a) Vitality (+20 HP, from {self.engine.player.fighter.max_hp})",
        )
        console.print(
            x=x + 1,
            y=y + 5,
            string=f"b) Strength (+1 attack, from {self.engine.player.fighter.base_strength})",
        )
        console.print(
            x=x + 1,
            y=y + 6,
            string=f"c) Dexterity (+1 defense, from {self.engine.player.fighter.base_dexterity})",
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 2:
            if index == 0:
                player.level.increase_max_hp()
            elif index == 1:
                player.level.increase_power()
            else:
                player.level.increase_defense()
        else:
            self.engine.message_log.add_message("Invalid entry.", config.colour.invalid)

            return None

        return super().ev_keydown(event)

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        """
        Don't allow the player to click to exit the menu, like normal.
        """
        return None


class InventoryEventHandler(AskUserEventHandler):
    """
    This handler lets the user select an item.
    What happens then depends on the subclass.
    """

    TITLE = "<missing title>"

    def on_render(self, console: tcod.Console) -> None:
        """
        Render an inventory menu, which displays the items in the inventory, and the letter to select them.
        Will move to a different position based on where the player is located, so the player can always see where
        they are.
        """
        super().on_render(console)
        number_of_items_in_inventory = len(self.engine.player.inventory.items)

        height = number_of_items_in_inventory + 2

        if height <= 3:
            height = 3

        width = len(self.TITLE) + 16
        x = console.width // 2 - int(width / 2)
        y = console.height // 2

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        if number_of_items_in_inventory > 0:
            for i, item in enumerate(self.engine.player.inventory.items):
                item_key = chr(ord("a") + i)
                is_equipped = self.engine.player.equipment.item_is_equipped(item)

                item_string = f"({item_key}) {item.name}"

                if is_equipped:
                    item_string = f"{item_string} (E)"

                console.print(x + 1, y + i + 1, item_string)
        else:
            console.print(x + 1, y + 1, "(Empty)")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = self.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 26:
            try:
                selected_item = player.inventory.items[index]
            except IndexError:
                self.engine.message_log.add_message("Invalid entry.", config.colour.invalid)
                return None
            return self.on_item_selected(selected_item)
        return super().ev_keydown(event)

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Called when the user selects a valid item."""
        raise NotImplementedError()


class InventoryActivateHandler(InventoryEventHandler):
    """Handle using an inventory item."""

    TITLE = "Select an item to use"

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        if item.consumable:
            # Return the action for the selected item.
            return item.consumable.get_action(self.engine.player)
        elif item.equippable:
            return core.actions.EquipAction(self.engine.player, item)
        else:
            return None


class InventoryDropHandler(InventoryEventHandler):
    """Handle dropping an inventory item."""

    TITLE = "Select an item to drop"

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Drop this item."""
        return core.actions.DropItem(self.engine.player, item)


class SelectIndexHandler(AskUserEventHandler):
    """Handles asking the user for an index on the map."""

    def __init__(self, engine: Engine):
        """Sets the cursor to the player when this handler is constructed."""
        super().__init__(engine)
        player = self.engine.player
        engine.mouse_location = player.x, player.y

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)
        x, y = self.engine.mouse_location
        console.tiles_rgb["bg"][x, y] = config.colour.white
        console.tiles_rgb["fg"][x, y] = config.colour.black

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """Check for key movement or confirmation keys."""
        key = event.sym
        if key in config.inputs.MOVE_KEYS:
            modifier = 1  # Holding modifier keys will speed up key movement.
            if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
                modifier *= 5
            if event.mod & (tcod.event.KMOD_LCTRL | tcod.event.KMOD_RCTRL):
                modifier *= 10
            if event.mod & (tcod.event.KMOD_LALT | tcod.event.KMOD_RALT):
                modifier *= 20

            x, y = self.engine.mouse_location
            dx, dy = config.inputs.MOVE_KEYS[key]
            x += dx * modifier
            y += dy * modifier
            # Clamp the cursor index to the map size.
            x = max(0, min(x, self.engine.game_map.width - 1))
            y = max(0, min(y, self.engine.game_map.height - 1))
            self.engine.mouse_location = x, y
            return None
        elif key in config.inputs.CONFIRM_KEYS:
            return self.on_index_selected(*self.engine.mouse_location)
        return super().ev_keydown(event)

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        """Left click confirms a selection."""
        if self.engine.game_map.in_bounds(*event.tile):
            if event.button == 1:
                return self.on_index_selected(*event.tile)
        return super().ev_mousebuttondown(event)

    def on_index_selected(self, x: int, y: int) -> Optional[ActionOrHandler]:
        """Called when an index is selected."""
        raise NotImplementedError()


class LookHandler(SelectIndexHandler):
    """
    Lets the player look around using the keyboard.
    """

    def on_index_selected(self, x: int, y: int) -> MainGameEventHandler:
        """Return to main handler."""
        return MainGameEventHandler(self.engine)


class SingleRangedAttackHandler(SelectIndexHandler):
    """Handles targeting a single enemy. Only the enemy selected will be affected."""

    def __init__(
            self, engine: Engine, callback: Callable[[Tuple[int, int]], Optional[core.actions.Action]]
    ):
        super().__init__(engine)

        self.callback = callback

    def on_index_selected(self, x: int, y: int) -> Optional[core.actions.Action]:
        return self.callback((x, y))


class AreaRangedAttackHandler(SelectIndexHandler):
    """Handles targeting an area within a given radius. Any entity within the area will be affected."""

    def __init__(
            self,
            engine: Engine,
            radius: int,
            callback: Callable[[Tuple[int, int]], Optional[core.actions.Action]],
    ):
        super().__init__(engine)

        self.radius = radius
        self.callback = callback

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)

        x, y = self.engine.mouse_location

        # Draw a rectangle around the targeted area, so the player can see the affected tiles.
        console.draw_frame(
            x=x - self.radius - 1,
            y=y - self.radius - 1,
            width=self.radius ** 2 - 1,
            height=self.radius ** 2 - 1,
            fg=config.colour.red,
            clear=False,
            decoration="/-\\| |\\-/"
        )

    def on_index_selected(self, x: int, y: int) -> Optional[core.actions.Action]:
        return self.callback((x, y))


class HoleJumpEventHandler(AskUserEventHandler):
    TITLE = "You stand on the edge of a deep chasm."

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[MainGameEventHandler]:
        if event.sym in config.inputs.YESNO_KEYS:
            if event.sym not in (tcod.event.K_n, tcod.event.K_ESCAPE):
                core.actions.FallDownHole(self.engine.player).perform()
                self.engine.update_fov()
            return MainGameEventHandler(self.engine)
        return None

    def on_render(self, console: tcod.Console) -> None:
        """Create the popup window allowing the user to choose whether to descend"""
        super().on_render(console)

        # x = round(self.engine.game_map.width / 2)
        # y = round(self.engine.game_map.height)

        width = len(self.TITLE) + 6
        x = console.width // 2 - int(width / 2)
        y = console.height // 2

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=4,
            title=self.TITLE,
            clear=True,
            fg=(255, 255, 255),
            bg=(0, 0, 0),
        )

        console.print(x=x + 1, y=y + 1, string=f"Are you sure you want to jump down the hole?")
        console.print(x=x + int(width / 4), y=y + 3, string=f"[Y]: Yes")
        console.print(x=x + int(width / 2), y=y + 3, string=f"[N]: No")


class GameOverEventHandler(EventHandler):
    def on_quit(self) -> None:
        """Handle exiting out of a finished game."""
        if os.path.exists("savegames/savegame.sav"):
            os.remove("savegames/savegame.sav")  # Deletes the active save file.
        raise config.exceptions.QuitWithoutSaving()  # Avoid saving a finished game.

    def ev_quit(self, event: tcod.event.Quit) -> None:
        self.on_quit()

    def ev_keydown(self, event: tcod.event.KeyDown) -> None:
        if event.sym == tcod.event.K_ESCAPE:
            self.on_quit()


class HistoryViewer(EventHandler):
    """Print the history on a larger window which can be navigated."""

    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.log_length = len(engine.message_log.messages)
        self.cursor = self.log_length - 1

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)  # Draw the main state as the background.

        log_console = tcod.Console(console.width - 6, console.height - 6)

        # Draw a frame with a custom banner title.
        log_console.draw_frame(0, 0, log_console.width, log_console.height)
        log_console.print_box(0, 0, log_console.width, 1, "┤Message history├", alignment=tcod.CENTER)

        # Render the message log using the cursor parameter.
        self.engine.message_log.render_messages(
            log_console,
            1,
            1,
            log_console.width - 2,
            log_console.height - 2,
            self.engine.message_log.messages[: self.cursor + 1],
        )
        log_console.blit(console, 3, 3)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[MainGameEventHandler]:
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
            return MainGameEventHandler(self.engine)
        return None


# TODO: Restore autoexplore
# TODO: Restore resting
# TODO: Restore autostairs
def handle_event():
    """
    For every player event, first determine the game state in order to provide the context for the actions, and then
    act accordingly.
    """
    pass

# TODO: Show inventory and message log on player death
# TODO: Show library of highscores for single player
# def handle_player_dead_events(event):
#     match event:
#         case tcod.event.K_i:
#             return {'show_inventory': True}
#         case tcod.event.K_ESCAPE:
#             return {'quit': True}
#         case tcod.event.K_F11:
#             return {'fullscreen': True}
#     return {}

# TODO: Main menu
# def handle_main_menu(event):
#     match event:
#         case tcod.event.K_a:
#             return {'new_game': True}
#         case tcod.event.K_b:
#             return {'load_game': True}
#         case (tcod.event.K_c, tcod.event.K_q, tcod.event.K_ESCAPE):
#             return {'exit': True}
#         case tcod.event.K_F11:
#             return {'fullscreen': True}
#     return {}

# TODO: Level-up menu
# def handle_level_up_menu(event):
#     match event:
#         case tcod.event.K_a:
#             return {'level_up': 'str'}
#         case tcod.event.K_b:
#             return {'level_up': 'agi'}
#         case tcod.event.K_F11:
#             return {'fullscreen': True}
#     return {}

# TODO: Display character sheet
# def handle_character_screen(event):
#     match event:
#         case tcod.event.K_ESCAPE:
#             return {'exit': True}
#         case tcod.event.K_F11:
#             return {'fullscreen': True}
#     return {}

# TODO: Esc menu
# def handle_esc_menu_events(event):
#     match event:
#         case (tcod.event.K_h, tcod.event.K_a):
#             return {'help': True}
#         case (tcod.event.K_r, tcod.event.K_b):
#             return {'exit': True}
#         case (tcod.event.K_q, tcod.event.K_c):
#             return {'quit': True}
#         case tcod.event.K_ESCAPE:
#             return {'exit': True}
#         case tcod.event.K_F11:
#             return {'fullscreen': True}
#     return {}

# TODO: Help menu
# def handle_help_menu_events(event):
#     match event:
#         case tcod.event.K_ESCAPE:
#             return {'exit': True}
#         case tcod.event.K_F11:
#             return {'fullscreen': True}
#     return {}
