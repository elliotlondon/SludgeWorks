from __future__ import annotations

import random
from typing import TYPE_CHECKING

import numpy as np

import config.colour
import core.g
import parts.ai
from config.colour import player_die, enemy_die
from maps.tiles import verdant_chars
from parts.ai import HostileStationary, PassiveStationary
from parts.base_component import BaseComponent
from utils.random_utils import roll_dice, dnd_bonus_calc

if TYPE_CHECKING:
    from entity import Actor


class Fighter(BaseComponent):
    parent: Actor

    def __init__(self, hp, max_hp, damage_dice, damage_sides, strength, dexterity, vitality, intellect,
                 armour, xp=0, level=1, dodges=False):
        self._hp = hp
        self.base_max_hp = max_hp
        self.damage_dice = damage_dice
        self.damage_sides = damage_sides
        self.base_strength = strength
        self.base_dexterity = dexterity
        self.base_vitality = vitality
        self.base_intellect = intellect
        self.base_armour = armour
        self.modified_strength = self.base_strength
        self.modified_dexterity = self.base_dexterity
        self.modified_vitality = self.base_vitality
        self.modified_intellect = self.base_intellect
        self.modified_armour = self.base_armour
        self.xp = xp
        self.level = level
        self.dodges = dodges

    @property
    def hp(self) -> int:
        return self._hp

    @hp.setter
    def hp(self, value: int) -> None:
        self._hp = max(0, min(value, self.max_hp))
        if self._hp == 0 and self.parent.ai:
            self.die()

    @property
    def max_hp(self):
        bonus = 0

        return self.base_max_hp + bonus

    @property
    def damage(self):
        if self.parent and self.parent.equipment.damage_dice != 0:
            damage = roll_dice(self.parent.equipment.damage_dice, self.parent.equipment.damage_sides)
        else:
            damage = roll_dice(self.damage_dice, self.damage_sides)

        return damage

    @property
    def crit_damage(self):
        if self.parent and self.parent.equipment.damage_dice != 0:
            damage = roll_dice(2 * self.parent.equipment.damage_dice, self.parent.equipment.damage_sides)
        else:
            damage = roll_dice(2 * self.damage_dice, self.damage_sides)

        return damage

    @property
    def strength_modifier(self):
        return dnd_bonus_calc(self.modified_strength) + self.parent.equipment.strength_bonus

    @property
    def dexterity_modifier(self):
        return dnd_bonus_calc(self.modified_dexterity) + self.parent.equipment.dexterity_bonus

    @property
    def vitality_modifier(self):
        return dnd_bonus_calc(self.modified_vitality) + self.parent.equipment.vitality_bonus

    @property
    def intellect_modifier(self):
        return dnd_bonus_calc(self.modified_intellect) + self.parent.equipment.intellect_bonus

    @property
    def armour_total(self):
        return self.modified_armour + self.parent.equipment.armour_bonus

    def heal(self, amount: int) -> int:
        if self.hp == self.max_hp:
            return 0

        new_hp_value = self.hp + amount

        if new_hp_value > self.max_hp:
            new_hp_value = self.max_hp

        amount_recovered = new_hp_value - self.hp

        self.hp = new_hp_value

        return amount_recovered

    def take_damage(self, amount: int) -> None:
        # Passive entities become hostile when they take damage
        if isinstance(self.parent.ai, parts.ai.NPC) or isinstance(self.parent.ai, parts.ai.PlantKeeper):
            self.parent.ai = parts.ai.HostileEnemy(entity=self.parent)
        self.hp -= amount

    def die(self) -> None:
        xp = self.parent.level.xp_given

        # First, if the creature is not the player and has items in its inventory or equipped, drop them.
        if len(self.parent.inventory.items) > 0 and not self.parent.name == 'Player':
            self.parent.inventory.drop_all()

        # Next, if the creature has an associated drop table, make an appropriate number of rolls on it, and drop
        # The items which are rolled for
        if hasattr(self.parent, 'drop_table'):
            if not len(self.parent.drop_table) == 0:
                # Import magic to grab drop table programmatically
                from importlib import import_module
                module = import_module(f'data.drop_tables', package=None)
                main_table = getattr(module, self.parent.drop_table)

                # Process subtables
                selection = random.choices(list(main_table.keys()), weights=list(main_table.values()))
                if 'table' in selection[0]:
                    sub_table = getattr(module, selection[0])
                    selection = random.choices(list(sub_table.keys()), weights=list(sub_table.values()))
                    new_item = core.g.engine.clone(selection[0])
                    new_item.place(self.parent.x, self.parent.y, self.gamemap)
                elif 'nothing' in selection[0]:
                    pass
                else:
                    new_item = core.g.engine.clone(selection[0])
                    new_item.place(self.parent.x, self.parent.y, self.gamemap)

        # Plants do not have a corpse
        if isinstance(self.parent.ai, HostileStationary) or isinstance(self.parent.ai, PassiveStationary):
            if self.parent.name.endswith("s"):
                death_message = f"The {self.parent.name} are destroyed!"
            else:
                death_message = f"The {self.parent.name} dies!"
            death_message_color = enemy_die

            # Generate floor in its place
            self.parent.char = random.choice(verdant_chars)

            # Death message
            core.g.engine.message_log.add_message(death_message, death_message_color)

            # If a plant is killed within 5 tiles of a PlantKeeper, enrage it
            for entity in core.g.engine.game_map.entities:
                if isinstance(entity.ai, parts.ai.PlantKeeper):
                    if np.sqrt((self.parent.x - entity.x) ** 2 + (self.parent.y - entity.y) ** 2) <= 5:
                        core.g.engine.message_log.add_message(f"A nearby {entity.name} becomes enraged!",
                                                              config.colour.enrage)
                        new_ai = parts.ai.HostileEnemy(entity)
                        entity.ai = new_ai
        else:
            if core.g.engine.player is self.parent:
                death_message = 'YOU DIED'
                death_message_color = player_die
                self.parent.ai = None
            else:
                death_message = f"The {self.parent.name} dies!"
                death_message_color = enemy_die
            # Death message
            core.g.engine.message_log.add_message(death_message, death_message_color)

        # Add to exiles list
        core.g.engine.game_map.exiles.append(self.parent)
        core.g.engine.game_map.entities = set([x for x in core.g.engine.game_map.entities
                                               if x not in core.g.engine.game_map.exiles])

        # Load corpse object if not plant
        if not isinstance(self.parent.ai, HostileStationary) and not isinstance(self.parent.ai, PassiveStationary):
            corpse = self.parent.corpse
            corpse.spawn(core.g.engine.game_map, self.parent.x, self.parent.y)

        # TODO: Smarter xp allocation
        # # Award xp to whoever performed the last action. Perhaps needs edge case investigation?
        # if hasattr(core.g.engine, 'last_actor'):
        #     core.g.engine.last_actor.level.add_xp(xp)
        if not self.parent.name == 'Player':
            core.g.engine.player.level.add_xp(xp)
