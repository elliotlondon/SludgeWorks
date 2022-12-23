class Impossible(Exception):
    """Exception raised when an action is impossible to be performed.
    The reason is given as the exception message. """


class MapGenError(Exception):
    """Exception raised when something fails during map generation"""


class QuestError(Exception):
    """Exception raised when something went wrong during quest internals"""


class FatalMapGenError(SystemExit):
    """Exception raised when something fails catastrophically during map generation"""


class DataLoadError(SystemExit):
    """Exception raised when data could not be loaded from a given request."""


class QuitWithoutSaving(SystemExit):
    """Can be raised to exit the game without automatically saving."""
