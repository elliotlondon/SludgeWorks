from __future__ import annotations

import logging
import math
import os
from typing import Callable, Optional, Tuple, TYPE_CHECKING, Union, List

import numpy as np
import tcod

import config.colour
import config.inputs
import core.actions
import core.g
import parts.inventory
from config.exceptions import Impossible
from core.actions import Action
from core.rendering import render_map, render_ui

if TYPE_CHECKING:
    from parts.entity import Item

ActionOrHandler = Union[Action, "BaseEventHandler"]
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
        assert not isinstance(state, Action), f"{self!r} can not handle actions."
        return self

    def on_render(self, console: tcod.Console) -> None:
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
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
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle an event, perform any actions, then return the next active event handler."""
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, EventHandler):
            return action_or_state
        if isinstance(action_or_state, Action) and self.handle_action(action_or_state):
            if not core.g.engine.player.is_alive:
                return GameOverEventHandler()
            elif core.g.engine.player.level.requires_level_up:
                return LevelUpEventHandler()
            return MainGameEventHandler()  # Return to the main handler.

        # Failsafe for recursion
        if not core.g.engine.player.is_alive:
            return GameOverEventHandler()
        elif core.g.engine.player.level.requires_level_up:
            return LevelUpEventHandler()

        # Garbage collection for exiled entities
        exiles = []
        for entity in core.g.engine.game_map.entities:
            if entity.name == ' ':
                exiles.append(entity)
        core.g.engine.game_map.entities = set([x for x in core.g.engine.game_map.entities
                                               if x not in exiles])

        return self

    def handle_action(self, action: Action) -> EventHandler:
        """Handle actions returned from event methods."""
        try:
            action.perform()
        except Impossible as exc:
            core.g.engine.message_log.add_message(exc.args[0], config.colour.impossible)
            return self  # Skip enemy turn on exceptions.

        # Action was successfully performed and a turn was advanced
        core.g.engine.handle_enemy_turns()
        core.g.engine.update_fov()

    def ev_quit(self, event: tcod.event.Quit) -> Optional[ActionOrHandler]:
        raise SystemExit()

    def ev_mousemotion(self, event: tcod.event.MouseMotion) -> None:
        if core.g.engine.game_map.in_bounds(event.tile.x, event.tile.y):
            core.g.engine.mouse_location = event.tile.x, event.tile.y

    def on_render(self, console: tcod.Console) -> None:
        render_map(console, core.g.engine.game_map)
        render_ui(console, core.g.engine)


class ExploreEventHandler(EventHandler):
    def __init__(self):
        super().__init__()
        # Init message
        core.g.engine.message_log.add_message(f"You begin exploring.", config.colour.yellow)
        self.path = []

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle events for input handlers with an engine."""
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        if self.handle_action(action_or_state):
            # A valid action was performed.
            if not core.g.engine.player.is_alive:
                # The player was killed sometime during or after the action.
                return GameOverEventHandler()
            elif core.g.engine.player.level.requires_level_up:
                return LevelUpEventHandler()
            return MainGameEventHandler()  # Return to the main handler.

        # Failsafe for recursion
        if not core.g.engine.player.is_alive:
            return GameOverEventHandler()
        elif core.g.engine.player.level.requires_level_up:
            return LevelUpEventHandler()

        # Garbage collection for exiled entities
        exiles = []
        for entity in core.g.engine.game_map.entities:
            if entity.name == ' ':
                exiles.append(entity)
        core.g.engine.game_map.entities = set([x for x in core.g.engine.game_map.entities
                                               if x not in exiles])

        return self

    def handle_action(self, action: Optional[Action]):
        """Handle actions returned from event methods. Returns True if the action will advance a turn."""
        player = core.g.engine.player

        if action is not tcod.event.KeyDown:
            if self.actor_in_fov():
                return MainGameEventHandler()
            try:
                path = self.explore()
                if path is not None:
                    action = core.actions.BumpAction(player, path[0] - player.x, path[1] - player.y)
                    action.perform()
                    core.g.engine.handle_enemy_turns()
                    core.g.engine.update_fov()
                    # if self.actor_in_fov():
                    #     return MainGameEventHandler()
                    return MainGameEventHandler()
                else:
                    return MainGameEventHandler()
            except Impossible as exc:
                core.g.engine.message_log.add_message(exc.args[0], config.colour.impossible)
                return True  # Skip enemy turn on exceptions.
        else:
            return MainGameEventHandler()

    def actor_in_fov(self) -> bool:
        """Check if there are any enemies in the FOV."""
        visible_tiles = np.nonzero(core.g.engine.game_map.visible)
        for actor in core.g.engine.game_map.dangerous_actors:
            if actor.x in visible_tiles[0] and actor.y in visible_tiles[1] and actor.name != 'Player':
                core.g.engine.message_log.add_message(f"You spot a {actor.name} and stop exploring.",
                                                      config.colour.yellow)
                return True
        return False

    def explore(self) -> Optional[List]:
        """Use a dijkstra map to navigate the player towards the nearest unexplored tile."""
        player = core.g.engine.player

        unexplored_coords = []
        for y in range(core.g.engine.game_map.height):
            for x in range(core.g.engine.game_map.width):
                if not core.g.engine.game_map.explored[x, y] and core.g.engine.game_map.accessible[x, y]:
                    unexplored_coords.append((y, x))

        if logging.DEBUG >= logging.root.level:
            core.g.engine.message_log.add_message(f"DEBUG: Unexplored coords = {len(unexplored_coords)}",
                                                  config.colour.debug)

        if len(unexplored_coords) == 0:
            core.g.engine.message_log.add_message("There is nowhere else to explore.", config.colour.yellow)
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
                cost = np.array(core.g.engine.game_map.accessible, dtype=np.int8)

                # Create a graph from the cost array and pass that graph to a new pathfinder.
                graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
                pathfinder = tcod.path.Pathfinder(graph)
                pathfinder.add_root((core.g.engine.player.x, core.g.engine.player.y))  # Start position.

                # Compute the path to the destination and remove the starting point.
                self.path: List[List[int]] = pathfinder.path_to(closest_coord)[1:].tolist()
                if not self.path:
                    core.g.engine.message_log.add_message("You cannot explore the remaining tiles.",
                                                          config.colour.yellow)
                    return None
                return self.path[0]
            else:
                # Path already exists: use it and prune it
                self.path.pop(0)
                new_coords = self.path[0]
                return new_coords

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        """By default any key exits this input handler."""
        core.g.engine.message_log.add_message(f"You stop exploring.", config.colour.yellow)
        return self.on_exit()

    def on_render(self, console: tcod.Console) -> None:
        render_map(console, core.g.engine.game_map)
        render_ui(console, core.g.engine)

    def on_exit(self) -> Optional[ActionOrHandler]:
        """Called when the user is trying to exit or cancel an action.
        By default this returns to the main event handler."""
        return MainGameEventHandler()


class MainGameEventHandler(EventHandler):
    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        action: Optional[Action] = None

        key = event.sym
        modifier = event.mod
        player = core.g.engine.player

        if key == tcod.event.K_PERIOD and modifier & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
            return core.actions.TakeStairsAction(player)

        if key in config.inputs.MOVE_KEYS:
            dx, dy = config.inputs.MOVE_KEYS[key]

            # Failsafe OOB check
            if not core.g.engine.game_map.in_bounds(player.x + dx, player.y + dy):
                core.g.engine.message_log.add_message("That way is blocked.", config.colour.impossible)
            elif core.g.engine.game_map.tiles[player.x + dx, player.y + dy]['name'] == 'hole':
                return HoleJumpEventHandler()
            else:
                action = core.actions.BumpAction(player, dx, dy)
        elif key in config.inputs.WAIT_KEYS:
            action = core.actions.WaitAction(player)

        elif key == tcod.event.K_ESCAPE:
            raise SystemExit()
        # elif key == tcod.event.K_F11:
        #     self.engine.event_handler.toggle_fullscreen()

        elif key == tcod.event.K_m:
            return HistoryViewer()
        elif key == tcod.event.K_SEMICOLON:
            return LookHandler()
        elif key == tcod.event.K_c:
            return CharacterScreenEventHandler()

        elif key == tcod.event.K_g:
            action = core.actions.PickupAction(player)
        elif key == tcod.event.K_i:
            return InventoryActivateHandler()
        elif key == tcod.event.K_d:
            return InventoryDropHandler()

        elif key == tcod.event.K_HASH or key == tcod.event.K_SLASH:
            return ExploreEventHandler()

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
            tcod.event.K_LGUI,
            tcod.event.K_RGUI,
            tcod.event.K_MODE,
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
        return MainGameEventHandler()


class CharacterScreenEventHandler(AskUserEventHandler):
    TITLE = "Character Sheet"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        level_str = f"Level: {core.g.engine.player.level.current_level}"
        xp_str = f"XP: {core.g.engine.player.level.current_xp}"
        xp_next_str = f"XP for next level: {core.g.engine.player.level.experience_to_next_level}"

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

        console.print(x=x + 1, y=y + 4, string=f"Strength: {core.g.engine.player.fighter.base_strength}")
        console.print(x=x + 1, y=y + 5, string=f"Dexterity: {core.g.engine.player.fighter.base_dexterity}")


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
            string=f"a) Vitality (+20 HP, from {core.g.engine.player.fighter.max_hp})",
        )
        console.print(
            x=x + 1,
            y=y + 5,
            string=f"b) Strength (+1 attack, from {core.g.engine.player.fighter.base_strength})",
        )
        console.print(
            x=x + 1,
            y=y + 6,
            string=f"c) Dexterity (+1 defense, from {core.g.engine.player.fighter.base_dexterity})",
        )

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = core.g.engine.player
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
            core.g.engine.message_log.add_message("Invalid entry.", config.colour.invalid)

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
        number_of_items_in_inventory = len(core.g.engine.player.inventory.items)

        height = number_of_items_in_inventory + 2

        if height <= 3:
            height = 3

        width = len(self.TITLE) + 20
        x = console.width // 2 - int(width / 2)
        y = console.height // 2

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
        console.print(x + 1, y, f" {self.TITLE}. TAB to sort ")

        if number_of_items_in_inventory > 0:
            for i, item in enumerate(core.g.engine.player.inventory.items):
                item_key = chr(ord("a") + i)
                is_equipped = core.g.engine.player.equipment.item_is_equipped(item)

                item_string = f"({item_key}) {item.name}"
                if is_equipped:
                    item_string = f"{item_string} (E)"

                console.print(x + 1, y + i + 1, item_string, fg=item.str_colour)
        else:
            console.print(x + 1, y + 1, "(Empty)")

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        player = core.g.engine.player
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index <= 26:
            try:
                selected_item = player.inventory.items[index]
            except IndexError:
                core.g.engine.message_log.add_message("Invalid entry.", config.colour.invalid)
                return None
            return self.on_item_selected(selected_item)
        elif key == tcod.event.KeySym.TAB:
            player.inventory.items = parts.inventory.autosort(player.inventory.items)
            return None
        return super().ev_keydown(event)

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Called when the user selects a valid item."""
        raise NotImplementedError()


class InventoryActivateHandler(InventoryEventHandler):
    """Handle using an inventory item."""

    TITLE = "Select an item to use:"

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        if item.consumable:
            # Return the action for the selected item.
            return item.consumable.get_action(core.g.engine.player)
        elif item.equippable:
            return core.actions.EquipAction(core.g.engine.player, item)
        else:
            return None


class InventoryDropHandler(InventoryEventHandler):
    """Handle dropping an inventory item."""

    TITLE = "Select an item to drop"

    def on_item_selected(self, item: Item) -> Optional[ActionOrHandler]:
        """Drop this item."""
        return core.actions.DropItem(core.g.engine.player, item)


class SelectIndexHandler(AskUserEventHandler):
    """Handles asking the user for an index on the map."""

    def __init__(self):
        """Sets the cursor to the player when this handler is constructed."""
        super().__init__()
        player = core.g.engine.player
        core.g.engine.mouse_location = player.x, player.y

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)
        x, y = core.g.engine.mouse_location
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

            x, y = core.g.engine.mouse_location
            dx, dy = config.inputs.MOVE_KEYS[key]
            x += dx * modifier
            y += dy * modifier
            # Clamp the cursor index to the map size.
            x = max(0, min(x, core.g.engine.game_map.width - 1))
            y = max(0, min(y, core.g.engine.game_map.height - 1))
            core.g.engine.mouse_location = x, y
            return None
        elif key in config.inputs.CONFIRM_KEYS:
            return self.on_index_selected(*core.g.engine.mouse_location)
        return super().ev_keydown(event)

    def ev_mousebuttondown(self, event: tcod.event.MouseButtonDown) -> Optional[ActionOrHandler]:
        """Left click confirms a selection."""
        if core.g.engine.game_map.in_bounds(*event.tile):
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
        return MainGameEventHandler()


class SingleRangedAttackHandler(SelectIndexHandler):
    """Handles targeting a single enemy. Only the enemy selected will be affected."""

    def __init__(self, callback: Callable[[Tuple[int, int]], Optional[Action]]):
        super().__init__()

        self.callback = callback

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))


class AreaRangedAttackHandler(SelectIndexHandler):
    """Handles targeting an area within a given radius. Any entity within the area will be affected."""

    def __init__(self, radius: int, callback: Callable[[Tuple[int, int]], Optional[Action]]):
        super().__init__()

        self.radius = radius
        self.callback = callback

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)

        x, y = core.g.engine.mouse_location

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

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))


class HoleJumpEventHandler(AskUserEventHandler):
    TITLE = "You stand on the edge of a deep chasm."

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[MainGameEventHandler]:
        if event.sym in config.inputs.YESNO_KEYS:
            if event.sym not in (tcod.event.K_n, tcod.event.K_ESCAPE):
                core.actions.FallDownHole(core.g.engine.player).perform()
                core.g.engine.update_fov()
            return MainGameEventHandler()
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
            return MainGameEventHandler()
        return None


# TODO: Restore autoexplore
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
