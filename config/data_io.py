from pathlib import Path
import pickle
import core.g
from core.engine import Engine


def save_game(path: Path) -> None:
    """If an engine is active then save it."""
    if not hasattr(core.g, "engine"):
        return  # If called before a new game is started then g.engine is not assigned.
    path.write_bytes(pickle.dumps(core.g.engine))


def load_game(path: Path) -> Engine:
    """Load an Engine instance from a file."""
    engine = pickle.loads(path.read_bytes())
    assert isinstance(engine, Engine)
    core.g.engine = engine
    return engine
