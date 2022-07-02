from enum import Enum, auto


class GameStates(Enum):
    PLAYERS_TURN = auto()
    ENEMY_TURN = auto()
    PLAYER_DEAD = auto()
    SHOW_INVENTORY = auto()
    DROP_INVENTORY = auto()
    SHOW_LOADOUT = auto()
    DROP_LOADOUT = auto()
    LOOK = auto()
    TARGETING = auto()
    LEVEL_UP = auto()
    CHARACTER_SCREEN = auto()
    ABILITY_SCREEN = auto()
    ESC_MENU = auto()
    HELP_MENU = auto()

    def __init__(self, current_state=PLAYERS_TURN, previous_game_state=PLAYERS_TURN):
        self._current_state = current_state
        self._previous_game_state = previous_game_state

    @property
    def current_state(self):
        return self._current_state

    @property
    def previous_game_state(self):
        return self._previous_game_state

    @current_state.setter
    def current_state(self, state):
        self._previous_game_state = self._current_state
        self._current_state = state
