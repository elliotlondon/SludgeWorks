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
