"""Frequently accessed globals are declared here."""
from __future__ import annotations

from typing import TYPE_CHECKING

import tcod

if TYPE_CHECKING:
    import core.engine
    import core.input_handlers.BaseEventHandler

screen_width = 80
screen_height = 50

context: tcod.context.Context
console: tcod.Console
engine: core.engine.Engine
