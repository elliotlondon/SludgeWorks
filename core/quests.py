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
        self.active_convos = {}

        # Init quests

        # Init convos
        self.active_convos['gilbert'] = {}
        self.active_convos['gilbert']['step'] = 0

    def get_current_convo(self, interactee: str):
        """For NPCs which are tied to the questing system, the step of the current quest can be returned from here
        to provide context."""
        try:
            return self.active_convos.get(interactee)['step']
        except KeyError:
            raise DataLoadError(f"Interactee {interactee} was not found within the conversation tracker.")

    def get_quest_step_name(self, questline):
        for quest in self.active_quests:
            if questline in quest.name:
                return quest.get_step_name(quest.step)

    def start_quest(self, questline: str):
        # Check that the quest hasn't already been started.
        if len(self.active_quests) != 0:
            for quest in self.active_quests:
                if quest['questline'] == questline:
                    return None

        # Start the quest.
        if questline.lower() == "gilbertquest":
            quest = GilbertQuest
            quest.name = 'gilbertquest'
            quest.step = 0
            self.active_quests.append(GilbertQuest)
            self.active_convos.get('gilbert')['step'] = 1

        # Give the player a notication that the quest has been started.

        # Add the quest to the quest journal

    # def advance_quest(self):
    #
    # def fail_quest(self):
    #
    # def finish_quest(self):
    #
    # def give_rewards(self):


class GilbertQuest():
    """Questline started by meeting Gilbert."""
    # Step 1: Bring moirehide
    # Step 2: Meet at the Liminus
    # Step 3: Meet the administrator

    def start_quest(self):
        self.name = "gilbertquest"
        self.step = 0

    @staticmethod
    def get_step_name(step):
        if step == 0:
            return "Gilbert's Boots"
        elif step == 1:
            return "Accessing the Liminus"

    def complete_step(self):
        # if core.g.engine.player.inventory.items
        pass
