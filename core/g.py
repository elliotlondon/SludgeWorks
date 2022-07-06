"""Frequently accessed globals are declared here."""
from __future__ import annotations

from typing import TYPE_CHECKING

import tcod

if TYPE_CHECKING:
    import core.engine

context: tcod.context.Context
engine: core.engine.Engine
