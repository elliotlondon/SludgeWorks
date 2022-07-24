from __future__ import annotations

import logging
import random
from random import randint
from typing import Optional, List, Tuple, TYPE_CHECKING

import numpy as np  # type: ignore
import tcod

import core.actions
import core.g

if TYPE_CHECKING:
    from parts.entity import Actor


class BaseAI(core.actions.Action):
    def perform(self) -> None:
        raise NotImplementedError()

    def get_path_to(self, dest_x: int, dest_y: int) -> List[Tuple[int, int]]:
        """
        Compute and return a path to the target position.
        If there is no valid path then returns an empty list.
        """
        # Copy the walkable array.
        cost = np.array(self.entity.gamemap.tiles["walkable"], dtype=np.int8)

        for entity in self.entity.gamemap.entities:
            # Check that an enitiy blocks movement and the cost isn't zero (blocking.)
            if entity.blocks_movement and cost[entity.x, entity.y]:
                # Add to the cost of a blocked position.
                # A lower number means more enemies will crowd behind each other in
                # hallways.  A higher number means enemies will take longer paths in
                # order to surround the player.
                cost[entity.x, entity.y] += 10

        # Create a graph from the cost array and pass that graph to a new pathfinder.
        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)

        pathfinder.add_root((self.entity.x, self.entity.y))  # Start position.

        # Compute the path to the destination and remove the starting point.
        path: List[List[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()

        # Convert from List[List[int]] to List[Tuple[int, int]].
        return [(index[0], index[1]) for index in path]

    def path_isvalid(self, path) -> bool:
        """Helper tool to find out whether a path is valid. This is important as teleportation
        and forced movement actions can cause the path to move entities to incorrect tiles."""

        next_x = abs(self.entity.x - path[0][0])
        next_y = abs(self.entity.y - path[0][1])

        if next_x > 1 or next_y > 1:
            return False
        else:
            return True


class HostileEnemy(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []

    def perform(self) -> None:
        # If player in fov, path towards or attack them.
        target = core.g.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = max(abs(dx), abs(dy))  # Chebyshev distance.

        # Attack player if they are visible
        if core.g.engine.game_map.visible[self.entity.x, self.entity.y]:
            if distance <= 1:
                return core.actions.MeleeAction(self.entity, dx, dy).perform()
            self.path = self.get_path_to(target.x, target.y)

        # If player not visible, check if a valid path exists and follow it
        if self.path:
            if not self.path_isvalid(self.path):
                self.path = None
            else:
                dest_x, dest_y = self.path.pop(0)
                return core.actions.MovementAction(
                    self.entity, dest_x - self.entity.x, dest_y - self.entity.y,
                ).perform()
        # If no valid path exists
        else:
            # 50% chance to do nothing
            if randint(0, 100) <= 50:
                return core.actions.WaitAction(self.entity).perform()
            # 40% chance to move to a random nearby tile
            elif randint(0, 100) <= 90:
                dest_x = self.entity.x + randint(-1, 1)
                dest_y = self.entity.y + randint(-1, 1)
                if (dest_x < core.g.engine.game_map.width) and (dest_y < core.g.engine.game_map.height):
                    if dest_x != 0 and dest_y != 0:
                        return core.actions.MovementAction(self.entity, dest_x - self.entity.x,
                                                           dest_y - self.entity.y).perform()
                else:
                    return core.actions.WaitAction(self.entity).perform()
            # 10% chance to path to a random nearby tile up to 6 tiles away
            else:
                # Make a new path for a tile somewhere nearby
                dest_x, dest_y = core.g.engine.game_map.get_random_nearby_tile(self.entity.x, self.entity.y,
                                                                               random.randint(2, 6))
                if dest_x != 0 and dest_y != 0:
                    return core.actions.MovementAction(self.entity, dest_x - self.entity.x,
                                                       dest_y - self.entity.y).perform()
                else:
                    return core.actions.WaitAction(self.entity).perform()


class HostileStationary(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []

    def perform(self) -> None:
        target = core.g.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = max(abs(dx), abs(dy))  # Chebyshev distance.

        if core.g.engine.game_map.visible[self.entity.x, self.entity.y]:
            if distance <= 1:
                return core.actions.MeleeAction(self.entity, dx, dy).perform()

        else:
            return core.actions.WaitAction(self.entity).perform()


class PassiveStationary(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []

    def perform(self) -> None:
        return core.actions.WaitAction(self.entity).perform()


class NPC(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []

    def perform(self) -> None:
        # NPCs currently do nothing
        return core.actions.WaitAction(self.entity).perform()


class BrainRaker(HostileEnemy):
    """Enemy variation where on every hit a random variation of explored, non-FOV tiles are purged from memory."""

    def perform(self) -> None:
        target = core.g.engine.player
        dx = target.x - self.entity.x
        dy = target.y - self.entity.y
        distance = max(abs(dx), abs(dy))  # Chebyshev distance.

        if core.g.engine.game_map.visible[self.entity.x, self.entity.y]:
            if distance <= 1:
                return core.actions.BrainRakerAction(self.entity, dx, dy).perform()

            self.path = self.get_path_to(target.x, target.y)

        if self.path:
            if not self.path_isvalid(self.path):
                self.path = None
            else:
                dest_x, dest_y = self.path.pop(0)
                return core.actions.MovementAction(
                    self.entity, dest_x - self.entity.x, dest_y - self.entity.y,
                ).perform()


class ConfusedEnemy(BaseAI):
    """
    A confused enemy will stumble around aimlessly for a given number of turns, then revert to its previous AI.
    If an actor occupies a tile it is randomly moving into, it will attack.
    """

    def __init__(self, entity: Actor, previous_ai: Optional[BaseAI], turns_remaining: int):
        super().__init__(entity)

        self.previous_ai = previous_ai
        self.turns_remaining = turns_remaining

        if logging.DEBUG >= logging.root.level:
            core.g.engine.message_log.add_message(f"{self.entity.name} has {self.turns_remaining} of confusion.")

    def perform(self) -> None:
        # Revert the AI back to the original state if the effect has run its course.
        if self.turns_remaining <= 0:
            core.g.engine.message_log.add_message(f"The {self.entity.name} is no longer confused.")
            self.entity.ai = self.previous_ai
        else:
            # Pick a random direction
            direction_x, direction_y = random.choice(
                [
                    (-1, -1),  # Northwest
                    (0, -1),  # North
                    (1, -1),  # Northeast
                    (-1, 0),  # West
                    (1, 0),  # East
                    (-1, 1),  # Southwest
                    (0, 1),  # South
                    (1, 1),  # Southeast
                ]
            )

            self.turns_remaining -= 1

            # The actor will either try to move or attack in the chosen random direction.
            # Its possible the actor will just bump into the wall, wasting a turn.
            return core.actions.BumpAction(self.entity, direction_x, direction_y, ).perform()
