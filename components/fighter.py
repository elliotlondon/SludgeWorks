import libtcodpy as libtcod

from random import randint

from game_messages import Message


class Fighter:
    def __init__(self, hp, damage_dice, damage_sides, strength, agility, vitality, intellect, perception, xp=0):
        self.base_max_hp = hp
        self.hp = hp
        self.base_damage_dice = damage_dice
        self.base_damage_sides = damage_sides
        self.base_strength = strength
        self.base_agility = agility
        self.base_vitality = vitality
        self.base_intellect = intellect
        self.base_perception = perception
        self.xp = xp

    @property
    def max_hp(self):
        if self.owner and self.owner.equipment:
            # Max hp is proportional to vitality
            bonus = self.owner.equipment.vitality_bonus
        else:
            bonus = 0

        return self.base_max_hp + bonus

    @property
    def damage(self):
        if self.owner and self.owner.equipment:
            damage = randint(self.owner.equipment.damage_dice,
                             self.owner.equipment.damage_dice*self.owner.equipment.damage_sides)
        else:
            damage = randint(self.base_damage_dice, self.base_damage_dice*self.base_damage_sides)

        return damage

    @property
    def strength(self):
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.strength_bonus
        else:
            bonus = 0

        return self.base_strength + bonus

    @property
    def agility(self):
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.agility_bonus
        else:
            bonus = 0

        return self.base_agility + bonus

    @property
    def vitality(self):
        if self.owner and self.ownder.equipment:
            bonus = self.ownder.equipment.vitality_bonus
        else:
            bonus = 0

        return self.base_vitality + bonus

    @property
    def intellect(self):
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.intellect_bonus
        else:
            bonus = 0

        return self.base_intellect + bonus

    @property
    def perception(self):
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.perception_bonus
        else:
            bonus = 0

        return self.base_perception + bonus

    def take_damage(self, amount):
        results = []

        self.hp -= amount

        if self.hp <= 0:
            self.hp = 0
            results.append({'dead': self.owner, 'xp': self.xp})

        return results

    def heal(self, amount):
        self.hp += amount

        if self.hp > self.max_hp:
            self.hp = self.max_hp

    def attack(self, target):
        results = []

        # Roll to see if hit
        attack_roll = randint(1, 20) + self.strength
        defence_roll = randint(1, 20) + target.fighter.agility

        if attack_roll > defence_roll:
            damage = self.damage
            if damage > 0:
                results.append({'message': Message('{0} attacks {1} for {2} hit points. ([{3} vs. {4}])'.format(
                    self.owner.name.capitalize(), target.name, str(damage), attack_roll, defence_roll), libtcod.white)})
                results.extend(target.fighter.take_damage(damage))
            else:
                results.append({'message': Message('{0} attacks {1} but does no damage. ([{2} vs. {3}])'.format(
                    self.owner.name.capitalize(), target.name, attack_roll, defence_roll), libtcod.grey)})
        else:
            results.append({'message': Message('{0} attacks {1} and misses. ([{2} vs. {3}])'.format(
                self.owner.name.capitalize(), target.name, attack_roll, defence_roll), libtcod.grey)})

        return results
