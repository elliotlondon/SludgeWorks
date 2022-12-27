"""Utility script for checking, debugging and iterating map generation"""
import copy
import lzma
import pickle
import traceback
from pathlib import Path
from typing import Optional

import tcod
from tcod.event import _SDL_TO_CLASS_TABLE, ffi, lib

import config.colour
import config.exceptions
import config.inputs
import config.setup_game
import core.g
import core.input_handlers
import maps.procgen
import maps.tiles
import core.clock
from core.actions import Action
from core.engine import Engine
from data.monster_factory import create_monster_from_json
from maps.game_map import GameWorld, GameMap
from utils.math_utils import Graph


def main():
    screen_width = core.g.screen_width
    screen_height = core.g.screen_height

    tileset = tcod.tileset.load_tilesheet("fonts/DB-curses-12x12.PNG", 16, 16, tcod.tileset.CHARMAP_CP437)
    handler: core.input_handlers.BaseEventHandler = MapGenMainMenu()

    with tcod.context.new_window(screen_width * 16, screen_height * 16, tileset=tileset, title="SludgeWorks",
                                 vsync=True) \
            as core.g.context:
        core.g.console = tcod.Console(screen_width, screen_height, order="F")
        core.g.global_clock = core.clock.GlobalClock()
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

    def __init__(self):
        super(MapGenEventHandler, self).__init__()
        self.position = (core.g.screen_width // 2, core.g.screen_height // 2)

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

        # Settings
        if key == tcod.event.K_ESCAPE:
            return MapGenEscMenuHandler()
        elif key == tcod.event.K_r:
            new_gameworld()
            return self
        elif key == tcod.event.K_m:
            return MapGenHistoryViewer()
        elif key == tcod.event.K_c:
            core.g.engine.player.x, core.g.engine.player.y = self.position
        elif key in config.inputs.MOVE_KEYS:
            modifier = 1  # Holding modifier keys will speed up key movement.
            if event.mod & (tcod.event.KMOD_LSHIFT | tcod.event.KMOD_RSHIFT):
                modifier *= 5
            if event.mod & (tcod.event.KMOD_LCTRL | tcod.event.KMOD_RCTRL):
                modifier *= 10
            if event.mod & (tcod.event.KMOD_LALT | tcod.event.KMOD_RALT):
                modifier *= 20
            dx, dy = config.inputs.MOVE_KEYS[key]
            dx *= modifier
            dy *= modifier
            core.g.engine.player.move(dx, dy)
        return action


class MapGenHistoryViewer(core.input_handlers.EventHandler):
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

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[MapGenEventHandler]:
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
            return MapGenEventHandler()
        return None


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
    dungeon = generate_debug_floor(engine)
    engine.game_map = dungeon
    engine.game_world.floors[f'level_{engine.game_world.current_floor}'] = dungeon

    for x in range(engine.game_map.width):
        for y in range(engine.game_map.height):
            engine.game_map.explored[x, y] = True

    core.g.engine = engine
    core.g.engine.game_map.visible[:] = core.g.engine.game_map
    engine.message_log.add_message(f"MapGen successful: floor {core.g.engine.game_world.current_floor}",
                                   config.colour.use)
    return engine


def save_map(path: Path) -> None:
    """If an engine is active then save it."""
    if not hasattr(core.g, "engine"):
        return  # If called before a new game is started then g.engine is not assigned.
    path.write_bytes(lzma.compress(pickle.dumps(core.g.engine.game_world)))
    print("GameWorld saved.")


def generate_debug_floor(engine: Engine):
    """Create a new floor in a stepwise manner which continues only when the user presses a key."""
    engine.game_world.current_floor += 1
    floor_width = engine.game_world.map_width
    floor_height = engine.game_world.map_height
    tries = 1
    while tries <= 25:
        engine.message_log.add_message(f"FloorGen attempt {tries}", config.colour.use)

        # Initialize map
        dungeon = GameMap(engine, floor_width, floor_height, entities=[engine.player])

        # First create the underlying caves.
        dungeon = maps.procgen.add_caves(dungeon, smoothing=1, p=42)
        random_x, random_y = dungeon.get_random_walkable_nontunnel_tile()
        graph = Graph(floor_width, floor_height, dungeon.tiles['walkable'])
        dungeon.accessible = graph.find_connected_area(random_x, random_y)

        # If too few accessible tiles, retry
        if len(dungeon.accessible.nonzero()[0]) < 80 * 43 / 4:
            engine.message_log.add_message(f"Too few accessible tiles ({len(dungeon.accessible.nonzero()[0])}).",
                                           config.colour.debug)
            tries += 1
            continue
        dungeon.prune_inaccessible(maps.tiles.wall)

        # Randomly add some rooms to the dungeon.
        extra_rooms = 4
        maps.procgen.place_random_rooms(dungeon, extra_rooms)
        dungeon.prune_inaccessible(maps.tiles.wall)

        # Place player
        engine.player.place(*dungeon.get_random_walkable_nontunnel_tile(), dungeon)
        graph = Graph(floor_width, floor_height, dungeon.tiles['walkable'])
        dungeon.accessible = graph.find_connected_area(engine.player.x, engine.player.y)

        # Add some random rooms in accessible locations
        for room in range(5):
            try:
                maps.procgen.place_congruous_room(dungeon, engine)
            except config.exceptions.MapGenError:
                continue
        # dungeon.prune_inaccessible(maps.tiles.wall)

        # dungeon = maps.procgen.add_rooms(dungeon, 25, 6, 10)
        # dungeon = maps.procgen.erode(dungeon, 1)

        # Add rocks/water
        dungeon = maps.procgen.add_rubble(dungeon, events=7)
        dungeon = maps.procgen.add_hazards(dungeon, engine, floods=5, holes=3)
        dungeon = maps.procgen.add_features(dungeon)

        # Populate dungeon
        maps.procgen.place_flora(dungeon, engine, areas=3)
        maps.procgen.place_fauna(dungeon, engine)
        maps.procgen.place_npcs(dungeon, engine)
        maps.procgen.place_items(dungeon, engine)
        maps.procgen.place_static_objects(dungeon, engine)

        # Finally, add stairs
        dungeon = maps.procgen.add_stairs(dungeon)
        if isinstance(dungeon, GameMap):
            # Mapgen successful, use this floor
            dungeon.accessible = dungeon.calc_accessible()
            return dungeon
        else:
            print(f"Floor generation failed.", config.colour.debug)
            tries += 1
            continue
    else:
        # Something went wrong with mapgen, sysexit
        raise config.exceptions.FatalMapGenError(f"Dungeon generation failed! Reason: floor attempts exceeded.")


if __name__ == "__main__":
    main()
