from __future__ import annotations

import random
from typing import TYPE_CHECKING

import core.g
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
                 perception, armour, xp=0, level=1, dodges=False):
        self._hp = hp
        self.base_max_hp = max_hp
        self.damage_dice = damage_dice
        self.damage_sides = damage_sides
        self.base_strength = strength
        self.base_dexterity = dexterity
        self.base_vitality = vitality
        self.base_intellect = intellect
        self.base_perception = perception
        self.base_armour = armour
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
        return dnd_bonus_calc(self.base_strength) + self.parent.equipment.strength_bonus

    @property
    def dexterity_modifier(self):
        return dnd_bonus_calc(self.base_dexterity) + self.parent.equipment.dexterity_bonus

    @property
    def vitality_modifier(self):
        return dnd_bonus_calc(self.base_vitality) + self.parent.equipment.vitality_bonus

    @property
    def intellect_modifier(self):
        return dnd_bonus_calc(self.base_intellect) + self.parent.equipment.intellect_bonus

    @property
    def armour_total(self):
        return self.base_armour + self.parent.equipment.armour_bonus

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
        self.hp -= amount

    def die(self) -> None:
        xp = self.parent.level.xp_given

        # Plants do not have a corpse
        if isinstance(self.parent.ai, HostileStationary) or isinstance(self.parent.ai, PassiveStationary):
            if self.parent.name.endswith("s"):
                death_message = f"The {self.parent.name} are destroyed!"
            else:
                death_message = f"The {self.parent.name} dies!"
            death_message_color = enemy_die

            # Generate floor in its place
            self.parent.char = random.choice(verdant_chars)
        else:
            if core.g.engine.player is self.parent:
                death_message = 'YOU DIED'
                death_message_color = player_die
                self.parent.ai = None
            else:
                death_message = f"The {self.parent.name} dies!"
                death_message_color = enemy_die

        # Add to exiles list
        core.g.engine.game_map.exiles.append(self.parent)
        core.g.engine.game_map.entities = set([x for x in core.g.engine.game_map.entities
                                               if x not in core.g.engine.game_map.exiles])

        # Load corpse object if not plant
        if not isinstance(self.parent.ai, HostileStationary) and not isinstance(self.parent.ai, PassiveStationary):
            corpse = self.parent.corpse
            corpse.spawn(core.g.engine.game_map, self.parent.x, self.parent.y)

        # Death message
        core.g.engine.message_log.add_message(death_message, death_message_color)

        # Award xp to whoever performed the last action. Perhaps needs edge case investigation?
        core.g.engine.last_actor.level.add_xp(xp)
