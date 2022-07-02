class Impossible(Exception):
    """Exception raised when an action is impossible to be performed.
    The reason is given as the exception message. """


class MapGenError(Exception):
    """Exception raised when something fails during map generation"""


class FatalMapGenError(SystemExit):
    """Exception raised when something fails catastrophically during map generation"""


class QuitWithoutSaving(SystemExit):
    """Can be raised to exit the game without automatically saving."""
