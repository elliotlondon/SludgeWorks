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
            self.active_convos.get('gilbert')['step'] = 1


class Quest():
    def __init__(self,
                 name: str = '<Undefined>',
                 step: int = 0):
        self.name = name
        self.step = step


class GilbertQuest(Quest):
    """Questline started by meeting Gilbert."""
    # Step 1: Bring moirehide
    # Step 2: Meet at the Liminus
    # Step 3: Meet the administrator

    def __init__(self):
        super().__init__(
            name='gilbertquest',
            step=0
        )

    @staticmethod
    def get_step_name(step):
        if step == 0:
            return "Gilbert's Boots"
        elif step == 1:
            return "Accessing the Liminus"

    @staticmethod
    def get_step_description(step):
        if step == 0:
            return "Gilbert has asked me to kill a Moire Beast and collect its hide in exchange for a pair of" \
                   "leather boots."
        elif step == 1:
            return "Gilbert spoke about a safe place called 'The Liminus' which can be reached by continuing down these" \
                   "caverns. He says he can help me further if I meet him there."

    def complete_step(self):
        # if core.g.engine.player.inventory.items
        pass
