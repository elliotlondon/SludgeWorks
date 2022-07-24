"""Frequently accessed globals are declared here."""
from __future__ import annotations

import numpy as np

from typing import TYPE_CHECKING, Iterator, List

import tcod

if TYPE_CHECKING:
    import core.engine
    import core.input_handlers.BaseEventHandler

context: tcod.context.Context
console: tcod.Console
engine: core.engine.Engine
