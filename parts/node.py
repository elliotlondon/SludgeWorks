from __future__ import annotations

import logging
from typing import Any, Iterator, Optional, Set, Type, TypeVar

TNode = TypeVar("TNode", bound="Node")

logger = logging.getLogger(__name__)


class Node:
    """A mixin that allows instances to be organized into a scene graph."""

    def __init__(self, *, parent: Optional[Node] = None) -> None:
        super().__init__()
        self._parent: Optional[Node] = None
        self._children: Set[Any] = set()
        if parent is not None:
            self.parent = parent

    @property
    def parent(self) -> Optional[Node]:
        """This nodes parent node or None if this node is the root.
        This can be set to re-parent the node.
        """
        return self._parent

    @parent.setter
    def parent(self, new_parent: Optional[Node]) -> None:
        assert hasattr(self, "_parent"), f"Make sure that subclasses of Node call super().__init__()\n{self!r}"
        if self._parent is new_parent:
            logger.debug("%r is already assigned to %r", self, new_parent)
            return
        if self._parent is not None:
            if new_parent is None:
                logger.debug("Removing %r from %r", self, self._parent)
            else:
                logger.debug("Moving %r from %r to %r", self, self._parent, new_parent)
            # Remove self from the current parent.
            self._parent._children.remove(self)
            self._parent = None
        else:
            logger.debug("Added %r to %r", self, new_parent)
        if new_parent is not None:
            # Add self to new_parent.
            self._parent = new_parent
            new_parent._children.add(self)

    def get_parent(self, kind: Type[TNode]) -> TNode:
        """Get an ancestor of a specific class, if the parent isn't that class then check the next one recursively."""
        while True:
            assert self._parent is not None
            self = self._parent
            if isinstance(self, kind):
                return self

    def try_get(self, kind: Type[TNode]) -> Optional[TNode]:
        """Return a child node of `kind` if it exists, otherwise returns None."""
        for n in self._children:
            if isinstance(n, kind):
                return n
        return None

    def __getitem__(self, kind: Type[TNode]) -> TNode:
        """Return a single child of type `kind`.  Assumes the child exists."""
        for n in self._children:
            if isinstance(n, kind):
                return n
        raise TypeError(f"This node has no {kind!r} instances.")

    def __setitem__(self, kind: Type[TNode], node: Optional[TNode]) -> None:
        """Set a child node, this replaces any other children of the same type with the new node."""
        self._children = {n for n in self._children if not isinstance(n, kind)}
        if node is not None:
            node.parent = self

    def get_children(self, kind: Type[TNode]) -> Iterator[TNode]:
        """Iterate over all the children of the given type."""
        for n in self._children:
            if isinstance(n, kind):
                yield n


if __name__ == "__main__":
    n = Node()
