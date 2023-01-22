from __future__ import annotations

from typing import TYPE_CHECKING

import core.g
from config.exceptions import DataLoadError

if TYPE_CHECKING:
    pass


class QuestTracker():
    """Class/Engine for tracking the statuses of all quests, linked to the save state."""

    def __init__(self):
        self.active_quests = []

    def get_quest_step_name(self, questline):
        for quest in self.active_quests:
            if questline in quest.name:
                return quest.get_step_name(quest.step)

    def get_quest_step_description(self, questline):
        for quest in self.active_quests:
            if questline in quest.name:
                return quest.get_step_description(quest.step)

    def start_quest(self, questline: str):
        # Check that the quest hasn't already been started.
        if len(self.active_quests) != 0:
            for quest in self.active_quests:
                if quest['questline'] == questline:
                    return None

        # Start the quest.
        if questline.lower() == "gilbertquest":
            self.active_quests.append(GilbertQuest())

    def advance_quest(self, interactee: str):
        """Move to the next step of the quest."""
        if interactee == "gilbert":
            for quest in self.active_quests:
                if quest.name == 'gilbertquest':
                    quest.step += 1

    def complete_quest(self, interactee: str):
        """Finish this part of the quest line."""
        if interactee == "gilbert":
            for quest in self.active_quests:
                if quest.name == 'gilbertquest':
                    quest.completed = True

    def continue_quest(self, interactee: str):
        """Revive this previously completed or failed quest line."""
        if interactee == "gilbert":
            for quest in self.active_quests:
                if quest.name == 'gilbertquest':
                    quest.failed = False
                    quest.completed = False
                    quest.step += 1

    def fail_quest(self, interactee: str):
        """Quest is marked as failed within the tracker."""
        if interactee.lower() == "gilbert":
            for quest in self.active_quests:
                if quest.name == 'gilbertquest':
                    quest.failed = True


class Quest():
    def __init__(self,
                 name: str = '<Undefined>',
                 step: int = 0,
                 completed: bool = False,
                 failed: bool = False):
        self.name = name
        self.step = step
        self.completed = completed
        self.failed = failed


class GilbertQuest(Quest):
    """Questline started by meeting Gilbert."""
    # Step 1: Bring moirehide
    # Step 2: Meet at the Liminus
    # Step 3: Meet the administrator

    def __init__(self):
        super().__init__(
            name='gilbertquest',
            step=0,
            completed=False,
            failed=False
        )

    @staticmethod
    def get_step_name(step):
        if step == 0:
            return "Gilbert's Boots"
        elif step == 1:
            return "Floral Removal"
        elif step == 2:
            return "Accessing the Liminus"

    @staticmethod
    def get_step_description(step):
        if step == 0:
            return "Gilbert has asked me to kill a Moire Beast and collect its hide in exchange for a pair of" \
                   "leather boots."
        elif step == 1:
            return "I have been tasked by Gilbert to find and slay the creature which is making the plant life grow " \
                   "out of control in this section of the cave. He has given me a Withering Blade to help me achieve " \
                   "this."
        elif step == 2:
            return "Gilbert spoke about a safe place called 'The Liminus' which can be reached by continuing down these" \
                   "caverns. He says he can help me further if I meet him there."

    def complete_step(self):
        # if core.g.engine.player.inventory.items
        pass
