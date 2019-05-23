import tcod as libtcod
import random
from game_messages import Message


class Fighter:
    def __init__(self, current_hp, max_hp, damage_dice, damage_sides, strength, agility, vitality, intellect,
                 perception, xp=0):
        self.base_max_hp = max_hp
        self.current_hp = current_hp
        self.damage_dice = damage_dice
        self.damage_sides = damage_sides
        self.base_strength = strength
        self.base_agility = agility
        self.base_vitality = vitality
        self.base_intellect = intellect
        self.base_perception = perception
        self.xp = xp

    @property
    def max_hp(self):
        bonus = 0

        if self.owner and self.owner.equippable:
            bonus += self.owner.equippable.vitality_bonus

        return self.base_max_hp + bonus

    @property
    def damage(self):
        if self.owner and self.owner.equipment:
            damage = roll_dice(self.owner.equipment.damage_dice, self.owner.equipment.damage_sides)
        else:
            damage = roll_dice(self.damage_dice, self.damage_sides)

        return damage

    @property
    def total_strength(self):
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.strength_bonus
        else:
            bonus = 0
        return self.base_strength + bonus

    @property
    def total_agility(self):
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.agility_bonus
        else:
            bonus = 0
        return self.base_agility + bonus

    @property
    def total_vitality(self):
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.vitality_bonus
        else:
            bonus = 0
        return self.base_vitality + bonus

    @property
    def total_intellect(self):
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.intellect_bonus
        else:
            bonus = 0
        return self.base_intellect + bonus

    @property
    def total_perception(self):
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.perception_bonus
        else:
            bonus = 0
        return self.base_perception + bonus

    def take_damage(self, amount):
        results = []

        self.current_hp -= amount
        if self.current_hp <= 0:
            self.current_hp = 0
            results.append({'dead': self.owner, 'xp': self.xp})
        return results

    def heal(self, amount):
        self.current_hp += amount
        if self.current_hp > self.max_hp:
            self.current_hp = self.max_hp

    def attack(self, target):
        results = []

        # Roll to see if hit
        attack_roll = roll_dice(1, 20) + self.total_strength
        defence_roll = roll_dice(1, 20) + target.fighter.total_agility
        damage = self.damage

        if attack_roll > defence_roll:
            if damage > 0:
                results.append({'message': Message('{0} attacks {1} for {2} hit points. ([{3} vs. {4}])'.format(
                    self.owner.name.capitalize(), target.name, str(damage), attack_roll, defence_roll), libtcod.white)})
                results.extend(target.fighter.take_damage(damage))
                # # Debug to see enemy HP
                # if target.name != 'Player':
                #     results.append({'message': Message('{0} has hit {1} points left.'.format(
                #         target.name.capitalize(), target.fighter.current_hp), libtcod.orange)})
            else:
                results.append({'message': Message('{0} attacks {1} but does no damage. ([{2} vs. {3}])'.format(
                    self.owner.name.capitalize(), target.name, attack_roll, defence_roll), libtcod.grey)})
        else:
            results.append({'message': Message('{0} attacks {1} and misses. ([{2} vs. {3}])'.format(
                self.owner.name.capitalize(), target.name, attack_roll, defence_roll), libtcod.grey)})

        return results


def roll_dice(num, dice):  # rolls dice, returns the sum of all rolls
    roll = 0
    for x in range(0, num):
        n = random.randint(1, dice)
        roll = roll + n

    return roll
