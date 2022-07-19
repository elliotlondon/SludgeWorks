from __future__ import annotations

import logging
import textwrap
import itertools
from json import load
from math import hypot
from pathlib import Path
from typing import Callable, Optional, Tuple, TYPE_CHECKING, Union, List, Iterable

import numpy as np
import tcod

import config.colour
import config.inputs
import core.actions
import core.g
import parts.inventory
from config.exceptions import Impossible
from core.actions import Action
from core.render_functions import RenderOrder
from core.rendering import render_map, render_ui
from maps.tiles import get_clean_name
from parts.ai import NPC
from parts.entity import Actor

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


class EventHandler(BaseEventHandler):
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle an event, perform any actions, then return the next active event handler."""
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, EventHandler) or isinstance(action_or_state, BaseEventHandler):
            return action_or_state
        if isinstance(action_or_state, Action) and self.handle_action(action_or_state):
            if not core.g.engine.player.is_alive:
                from core.events.death import GameOverEventHandler
                return GameOverEventHandler()
            elif core.g.engine.player.level.requires_level_up:
                return LevelUpEventHandler()
            return MainGameEventHandler()  # Return to the main handler.

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


class PopupMessage(EventHandler):
    TITLE = "<Untitled>"

    def __init__(self, text: str):
        self.text = text

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[MainGameEventHandler]:
        if event.sym == tcod.event.K_ESCAPE:
            return MainGameEventHandler()

    def on_render(self, console: tcod.Console) -> None:
        """Create the popup window with a message within."""
        super().on_render(console)
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
        console.print(x=x + int(width / 2), y=y + height - 1, string="[OK]", alignment=tcod.CENTER)


class ExploreEventHandler(EventHandler):
    """Handler to initiate the explore sequence. Stops if an enemy is in the fov. Continues until interrupted by
    a keypress, or if there are no more tiles that can be explored."""
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

        if not isinstance(self.handle_action(action_or_state), ExploreEventHandler):
            # A valid action was performed.
            if not core.g.engine.player.is_alive:
                from core.events.death import GameOverEventHandler
                return GameOverEventHandler()
            elif core.g.engine.player.level.requires_level_up:
                return LevelUpEventHandler()
            return MainGameEventHandler()  # Return to the main handler.

        return self

    def handle_action(self, action: Optional[Action]):
        """Handle actions returned from event methods. Returns True if the action will advance a turn."""
        # First check whether exploring is possible.
        visible_tiles = np.nonzero(core.g.engine.game_map.visible)
        for actor in core.g.engine.game_map.dangerous_actors:
            if actor.x in visible_tiles[0] and actor.y in visible_tiles[1] and actor.name != 'Player':
                core.g.engine.message_log.add_message(f"You spot a {actor.name} and stop exploring.",
                                                      config.colour.yellow)
                return MainGameEventHandler()
        try:
            # If path exists, perform next step without halting
            if self.path:
                self.explore_move()
            elif not self.path:
                self.explore()
                self.explore_move()
        except Impossible as exc:
            core.g.engine.message_log.add_message(exc.args[0], config.colour.impossible)
            return MainGameEventHandler()
        self.on_render(core.g.console)
        return self

    def explore(self) -> Optional[List | None]:
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
            new_distance = hypot(x - player.x, y - player.y)

            if new_distance < closest_distance:
                closest_distance = new_distance
                closest_coord = (x, y)

        # Try simple A*
        if closest_coord:
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

    def explore_move(self):
        """Perform an action to move the player, update fov and the renderer"""
        # Move player
        action = core.actions.BumpAction(core.g.engine.player,
                                         self.path[0][0] - core.g.engine.player.x,
                                         self.path[0][1] - core.g.engine.player.y)
        # Remove the tile moved to from the path
        action.perform()
        self.path.pop(0)

        # Handle enemy turns
        core.g.engine.handle_enemy_turns()
        core.g.engine.update_fov()

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
    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle an event, perform any actions, then return the next active event handler."""
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, EventHandler):
            return action_or_state
        if isinstance(action_or_state, Action) and self.handle_action(action_or_state):
            if not core.g.engine.player.is_alive:
                from core.events.death import GameOverEventHandler
                return GameOverEventHandler()
            elif core.g.engine.player.level.requires_level_up:
                return LevelUpEventHandler()
            return MainGameEventHandler()  # Return to the main handler.

        # Failsafe for recursion
        if not core.g.engine.player.is_alive:
            from core.events.death import GameOverEventHandler
            return GameOverEventHandler()
        elif core.g.engine.player.level.requires_level_up:
            return LevelUpEventHandler()

        return self

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[ActionOrHandler]:
        action: Optional[Action] = None

        key = event.sym
        modifier = event.mod
        player = core.g.engine.player

        if key == tcod.event.K_PERIOD and modifier & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT) \
                or key == tcod.event.K_KP_ENTER:
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

        elif key == tcod.event.K_m:
            return HistoryViewer()
        elif key == tcod.event.K_c:
            return CharacterScreenEventHandler()

        elif key == tcod.event.K_g:
            action = core.actions.PickupAction(player)
        elif key == tcod.event.K_i:
            return InventoryActivateHandler()
        elif key == tcod.event.K_d:
            return InventoryDropHandler()

        elif key == tcod.event.K_SEMICOLON:
            return LookHandler()
        elif key == tcod.event.K_HASH or key == tcod.event.K_BACKSLASH:
            return ExploreEventHandler()

        # Space-to-interact. If nothing around, create popup. If something, interact. If multiple, prompt user.
        elif key == tcod.event.K_SPACE or key == tcod.event.K_KP_SPACE:
            interactables = core.g.engine.game_map.get_surrounding_interactables(player.x, player.y)
            if len(interactables) == 0:
                return PopupMessage("There is nothing nearby to interact with.")
            elif len(interactables) == 1:
                # Decide which interaction to return, depending upon context.
                if isinstance(interactables[0].ai, parts.ai.NPC):
                    # Check if convo has been started before in engine, if not, start a new one
                    if interactables[0].name in core.g.engine.convos:
                        return core.g.engine.convos[interactables[0].name]
                    else:
                        return ConversationEventHandler(interactables[0])
                elif isinstance(interactables[0], parts.entity.StaticObject):
                    if interactables[0].name == "Fountain of Sludge":
                        return SludgeFountainEventHandler(interactables[0])
            else:
                raise NotImplementedError("Too may objects to interact with surrounding the player.")

        elif key == tcod.event.K_ESCAPE:
            raise SystemExit()
        # elif key == tcod.event.K_F11:
        #     self.toggle_fullscreen()

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
    TITLE = "<Untitled>"

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)

        attr_str = "Select an attribute to increase."

        width = len(attr_str) + 15
        x = console.width // 2 - int(width / 2)
        y = console.height // 2 - 4

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=9,
            title='',
            clear=True,
            fg=tcod.yellow,
            bg=(0, 0, 0),
        )
        console.print(x=console.width // 2, y=y, string="┤Level Up!├", alignment=tcod.constants.CENTER)

        console.print(x=console.width // 2, y=y + 2, string="You channel the power of your slain foes...",
                      fg=tcod.white, alignment=tcod.constants.CENTER)
        console.print(x=console.width // 2, y=y + 3, string=attr_str,
                      fg=tcod.white, alignment=tcod.constants.CENTER)

        console.print(
            x=x + 1,
            y=y + 5,
            string=f"a) Vitality (+{core.g.engine.player.fighter.base_vitality}, "
                   f"from {core.g.engine.player.fighter.max_hp})",
            fg=tcod.light_pink,
        )
        console.print(
            x=x + 1,
            y=y + 6,
            string=f"b) Strength (+1 attack, from {core.g.engine.player.fighter.base_strength})",
            fg=tcod.light_red,
        )
        console.print(
            x=x + 1,
            y=y + 7,
            string=f"c) Dexterity (+1 defense, from {core.g.engine.player.fighter.base_dexterity})",
            fg=tcod.light_green,
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
            core.g.engine.message_log.add_message("You reorganize your inventory.",
                                                  config.colour.use)
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


class ConversationEventHandler(AskUserEventHandler):
    """Handle space-to-interact with entities around the character."""

    def __init__(self, interactee: parts.entity.Actor):
        super().__init__(),
        self.interactee = interactee
        self.width: int
        self.height: int
        self.y_offset: int
        self.len_replies: int = 0
        self.current_screen: str = "0"
        self.new_screen: int
        self.leave = True
        self.leave_str = "Goodbye."
        self.convo_json = self.get_convo_from_json(self.interactee.name.lower())
        self.speech = []
        self.replies = []

    @staticmethod
    def wrap(string: str, width: int) -> Iterable[str]:
        """Return a wrapped text message."""
        for line in string.splitlines():
            yield from textwrap.wrap(line, width, expand_tabs=True)

    def get_convo_from_json(self, convo: str) -> dict:
        """Load a conversation json file for a specified character."""
        path = Path(f"data/convos/{convo}.json")
        f = open(path, 'r', encoding='utf-8')
        return load(f)

    def init_convo(self, index: str):
        """Logic to set up the conversation with the player on first interaction."""
        self.speech = self.convo_json[index]["speech"]
        replies = []
        for i in self.convo_json[index]:
            if i != "speech":
                replies.append(self.convo_json[index][f'{i}'])
        self.replies = replies

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[MainGameEventHandler, PopupMessage]:
        key = event.sym
        index = key - tcod.event.K_a

        if 0 <= index < self.len_replies:
            selected = list(self.convo_json[self.current_screen])[index + 1]
            self.new_screen = selected
            # If first interaction, provide init
            for element in self.convo_json[f"{self.current_screen}"]:
                if element == "speech":
                    continue
                elif element == self.new_screen:
                    self.current_screen = self.new_screen
                    self.speech = self.convo_json[f"{self.current_screen}"]['speech']
                    replies = []
                    for i in self.convo_json[f"{self.current_screen}"]:
                        if i != "speech":
                            replies.append(self.convo_json[f"{self.current_screen}"][f'{i}'])
                    self.replies = replies
                    break
            return self
        elif key == tcod.event.K_ESCAPE or index == self.len_replies:
            # Make it so that the next interaction returns the generic interaction
            self.init_convo("-1")

            # Save to engine on exit
            core.g.engine.convos[self.interactee.name] = self
            return MainGameEventHandler()

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)
        # Populate speech and replies
        if not self.speech or not self.replies:
            self.init_convo("0")

        # Init console sizing
        self.len_replies = len(self.replies)
        self.width = console.width // 2 + 20
        self.len_speech = len(list(self.wrap(self.speech, self.width - 2)))
        self.height = 4 + self.len_speech + self.len_replies
        x = console.width // 2 - int(self.width / 2)
        y = console.height // 3  # Clamp height so that extra text moves downwards

        console.draw_frame(
            x=x,
            y=y,
            width=self.width,
            height=self.height,
            title='',
            clear=True,
            fg=tcod.white,
            bg=(0, 0, 0),
        )
        console.print(console.width // 2, y, f"┤{self.interactee.name}├",
                      alignment=tcod.constants.CENTER, fg=self.interactee.colour)

        self.draw_speech(console, self.speech, x + 1, y)
        self.draw_replies(console, self.replies, x + 1, y + self.y_offset + 3)

    def draw_speech(self, console: tcod.console, speech: List[str] | str, x: int, y: int) -> int:
        """Draws the text spoken by the Actor to the main part of the message menu."""
        to_draw = ''.join(speech)

        # Loop over all paragraphs
        self.y_offset = 0
        for line in list(self.wrap(to_draw, self.width - 2)):
            console.print(x=x, y=y + 2 + self.y_offset, string=line, alignment=tcod.constants.LEFT, fg=tcod.white)
            self.y_offset += 1

    def draw_replies(self, console: tcod.console, replies: List[str], x: int, y: int):
        """Draws the replies that may be chosen by the player for a given speech option."""
        self.len_replies = len(replies)

        i = 0
        for i, reply in enumerate(replies):
            reply_key = chr(ord("a") + i)
            reply_str = f"[{reply_key}]: {reply}"
            console.print(x, y + i, reply_str, fg=tcod.white)

        # Goodbye message
        if self.leave:
            console.print(x=x, y=y + i + 1, string=f"[{chr(ord('a') + i + 1)}]: {self.leave_str}",
                      alignment=tcod.constants.LEFT, fg=tcod.white)


class SludgeFountainEventHandler(AskUserEventHandler):
    """Handle space-to-interact with entities around the character."""

    def __init__(self, interactee: parts.entity.StaticObject):
        super().__init__(),
        self.interactee = interactee

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[MainGameEventHandler, PopupMessage]:
        if event.sym in config.inputs.YESNO_KEYS or event.sym == tcod.event.K_SPACE:
            if event.sym not in (tcod.event.K_n, tcod.event.K_ESCAPE, tcod.event.K_SPACE):
                return PopupMessage("You bathe in the sludge...")
            return MainGameEventHandler()
        return None

    def on_render(self, console: tcod.Console) -> None:
        super().on_render(console)
        width = len(self.interactee.interact_message) + 4
        height = 6
        x = console.width // 2 - int(width / 2)
        y = console.height // 2 - height

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title='',
            clear=True,
            fg=self.interactee.colour,
            bg=(0, 0, 0),
        )
        console.print(console.width // 2, y, f"┤{self.interactee.name}├",
                      alignment=tcod.constants.CENTER, fg=self.interactee.colour)
        console.print(x=console.width // 2, y=y + 2, string=self.interactee.interact_message,
                      alignment=tcod.constants.CENTER, fg=tcod.white)
        console.print(x=console.width // 2 - 6, y=y + 5, string=f"[Y]: Yes",
                      alignment=tcod.constants.CENTER, fg=self.interactee.colour)
        console.print(x=console.width // 2 + 6, y=y + 5, string=f"[N]: No",
                      alignment=tcod.constants.CENTER, fg=self.interactee.colour)


class SelectIndexHandler(AskUserEventHandler):
    """Handles asking the user for an index on the map."""

    def __init__(self):
        """Sets the cursor to the player when this handler is constructed."""
        super().__init__()
        player = core.g.engine.player
        core.g.engine.mouse_location = player.x, player.y

    def handle_events(self, event: tcod.event.Event) -> BaseEventHandler:
        """Handle an event, perform any actions, then return the next active event handler."""
        action_or_state = self.dispatch(event)
        if isinstance(action_or_state, EventHandler):
            return action_or_state
        if isinstance(action_or_state, Action) and self.handle_action(action_or_state):
            if not core.g.engine.player.is_alive:
                return core.events.death.GameOverEventHandler()
            elif core.g.engine.player.level.requires_level_up:
                return LevelUpEventHandler()
            return MainGameEventHandler()  # Return to the main handler.

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
        return self

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
    """Lets the player look around using the keyboard. Draws a box with details about the selected tile, and
    its occupants."""

    def __init__(self):
        """Additionally keep track of items to render in tile stack."""
        super().__init__()
        self.stack: List = []

    @staticmethod
    def wrap(string: str, width: int) -> Iterable[str]:
        """Return a wrapped text message."""
        for line in string.splitlines():
            yield from textwrap.wrap(line, width, expand_tabs=True)

    def on_render(self, console: tcod.Console) -> None:
        """Highlight the tile under the cursor."""
        super().on_render(console)
        x, y = core.g.engine.mouse_location
        console.tiles_rgb["bg"][x, y] = config.colour.white
        console.tiles_rgb["fg"][x, y] = config.colour.black

        self.create_look_box(x, y, console)

    def create_look_box(self, x_pos: int, y_pos: int, console: tcod.Console) -> None:
        """Render the parent and dim the result, then print the message on top.
        x_pos: x index of selected tile
        y_pos: y index of selected tile
        """
        self.stack = []

        # Get necessary info at the specified tile
        tile = core.g.engine.game_map.get_tile_at_explored_location(x_pos, y_pos)
        visible = core.g.engine.game_map.visible[x_pos, y_pos]
        if tile:
            # Make a dictionary containing all necessary content
            tile_content = {}
            tile_content['name'] = get_clean_name(tile)
            tile_content['description'] = ''.join(tile[5])
            tile_content['footer'] = 'FLOOR TILE'
            tile_content['footer_colour'] = tcod.grey
            if visible:
                tile_content['colour'] = list(tile[4][1])
            else:
                tile_content['colour'] = list(tile[4][1])

            # Look box size
            width = console.width // 4 + 2
            height = len(tile_content['description']) // (console.width // 4) + 8

            # Calculate whether the box should be rendered above or below the selected tile
            if x_pos >= console.width // 2:
                box_x = x_pos - width - 2
            else:
                box_x = x_pos + 2
            if y_pos >= console.height // 2:
                box_y = y_pos - height - 2
            else:
                box_y = y_pos + 2

            # First draw a box for the tile
            self.stack.append(self.draw_look_box(tile_content, box_x, box_y, width, height, console))

            # Now make a box for each entity at the location. Only consider visible entities
            entities = core.g.engine.game_map.get_all_visible_entities(x_pos, y_pos)
            if entities:
                entity_content = {}
                i = 1
                for entity in sorted(entities, key=lambda x: x.render_order.value):
                    # Get entity info
                    entity_content['name'] = entity.name.capitalize()
                    entity_content['colour'] = entity.colour
                    entity_content['description'] = entity.description
                    if entity.name == "Player":
                        entity_content['footer'] = ''
                        entity_content['footer_colour'] = tcod.white
                    elif isinstance(entity, parts.entity.Item):
                        entity_content['footer'] = "ITEM"
                        entity_content['footer_colour'] = tcod.yellow
                    elif isinstance(entity, parts.entity.StaticObject):
                        entity_content['footer'] = "OBJECT"
                        entity_content['footer_colour'] = tcod.light_sky
                    elif isinstance(entity.ai, parts.ai.NPC):
                        entity_content['footer'] = "NPC"
                        entity_content['footer_colour'] = tcod.blue
                    elif isinstance(entity.ai, parts.ai.HostileStationary) or \
                            isinstance(entity.ai, parts.ai.PassiveStationary):
                        entity_content["footer"] = "PLANT"
                        entity_content['footer_colour'] = tcod.green
                    elif entity.render_order == RenderOrder.CORPSE:
                        entity_content["footer"] = "CORPSE"
                        entity_content['footer_colour'] = tcod.grey
                    else:
                        entity_content["footer"] = "ENEMY"
                        entity_content['footer_colour'] = tcod.red

                    # Look box size
                    width = console.width // 4 + 2
                    height = len(entity_content['description']) // (console.width // 4) + 8
                    # Scale width in case of long item names
                    if len(entity_content['name']) > width:
                        width = len(entity_content['name']) + 4
                    self.stack.append(self.draw_look_box(entity_content, box_x + i, box_y + i, width, height, console))
                    i += 1

    def draw_look_box(self, content_dict: dict, x: int, y: int, width: int, height: int, console: tcod.Console) -> None:
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
        # Add white bg to title if item colour is too dark
        if sum(content_dict['colour']) < 121:
            bg = (255, 255, 255)
        else:
            bg = (0, 0, 0)
        console.print(x=x + 1, y=y, string=f"{content_dict['name']}", fg=content_dict['colour'], bg=bg,
                      alignment=tcod.constants.LEFT)

        # Break up description string into sub-strings if it is longer than the box width.
        y_offset = 2
        content_dict['description'] = content_dict['description'].replace(".", ".\n")
        for line in list(self.wrap(content_dict['description'], width - 2)):
            console.print(x=x + 1, y=y + y_offset, string=line, fg=tcod.white)
            y_offset += 1

        console.print(x=x + 1, y=y + height - 1, string=content_dict['footer'], fg=content_dict['footer_colour'],
                      alignment=tcod.constants.LEFT)

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


class TeleotherEventHandler(SelectIndexHandler):
    """Handles targeting a single enemy. Only the enemy selected will be affected."""

    def __init__(self, callback: Callable[[Tuple[int, int]], Optional[Action]]):
        super().__init__()
        self.callback = callback

    def on_index_selected(self, x: int, y: int) -> Optional[Action]:
        return self.callback((x, y))


class HoleJumpEventHandler(AskUserEventHandler):
    TITLE = "<Untitled>"

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
        width = len(self.TITLE) + 34
        height = 6
        x = console.width // 2 - int(width / 2)
        y = console.height // 2 - height

        console.draw_frame(
            x=x,
            y=y,
            width=width,
            height=height,
            title='',
            clear=True,
            fg=tcod.gray,
            bg=(0, 0, 0),
        )
        console.print(console.width // 2, y, f"┤You stand on the edge of a deep chasm.├",
                      alignment=tcod.constants.CENTER, fg=tcod.gray)

        console.print(x=console.width // 2, y=y + 2, string=f"Are you sure you want to",
                      alignment=tcod.constants.CENTER, fg=tcod.white)
        console.print(x=console.width // 2, y=y + 3, string=f"jump down the hole?",
                      alignment=tcod.constants.CENTER, fg=tcod.white)
        console.print(x=console.width // 2 - 6, y=y + 5, string=f"[Y]: Yes",
                      alignment=tcod.constants.CENTER, fg=tcod.white)
        console.print(x=console.width // 2 + 6, y=y + 5, string=f"[N]: No",
                      alignment=tcod.constants.CENTER, fg=tcod.white)


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
