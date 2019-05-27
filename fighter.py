import tcod as libtcod
from random_utils import roll_dice, dnd_bonus_calc
from game_messages import Message


class Fighter:
    def __init__(self, current_hp, max_hp, damage_dice, damage_sides, strength, dexterity, vitality, intellect,
                 perception, xp=0, level=1):
        self.base_max_hp = max_hp
        self.current_hp = current_hp
        self.damage_dice = damage_dice
        self.damage_sides = damage_sides
        self.base_strength = strength
        self.base_dexterity = dexterity
        self.base_vitality = vitality
        self.base_intellect = intellect
        self.base_perception = perception
        self.xp = xp
        self.level = level

    @property
    def max_hp(self):
        bonus = 0

        return self.base_max_hp + bonus

    @property
    def damage(self):
        if self.owner and self.owner.equipment:
            damage = roll_dice(self.owner.equipment.damage_dice, self.owner.equipment.damage_sides)
        else:
            damage = roll_dice(self.damage_dice, self.damage_sides)

        return damage

    @property
    def strength_modifier(self):
        bonus = 0
        if self.owner and self.owner.equipment:
            bonus += self.owner.equipment.strength_bonus

        strength_bonus = dnd_bonus_calc(self.base_strength)

        return strength_bonus + bonus

    @property
    def dexterity_modifier(self):
        bonus = 0
        if self.owner and self.owner.equipment:
            bonus += self.owner.equipment.dexterity_bonus

        dexterity_bonus = dnd_bonus_calc(self.base_dexterity)

        return dexterity_bonus + bonus

    @property
    def vitality_modifier(self):
        bonus = 0
        if self.owner and self.owner.equipment:
            bonus += self.owner.equipment.vitality_bonus

        vitality_bonus = dnd_bonus_calc(self.base_vitality)

        return vitality_bonus + bonus

    @property
    def intellect_modifier(self):
        bonus = 0
        if self.owner and self.owner.equipment:
            bonus += self.owner.equipment.intellect_bonus

        intellect_bonus = dnd_bonus_calc(self.base_intellect)

        return intellect_bonus + bonus

    @property
    def perception_modifier(self):
        bonus = 0
        if self.owner and self.owner.equipment:
            bonus = self.owner.equipment.perception_bonus

        perception_bonus = dnd_bonus_calc(self.base_perception)

        return perception_bonus + bonus

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
        attack_roll = roll_dice(1, 20) + self.strength_modifier
        defence_roll = roll_dice(1, 20) + target.fighter.dexterity_modifier
        damage = self.damage

        if attack_roll > defence_roll:
            if damage > 0:
                results.append({'message': Message('{0} attacks {1} for {2} hit points. ([{3} vs. {4}])'.format(
                    self.owner.name.capitalize(), target.name, str(damage), attack_roll, defence_roll), libtcod.white)})
                results.extend(target.fighter.take_damage(damage))
                # Debug to see enemy HP
                # if target.name == 'Risen Sacrifice':
                #     results.append({'message': Message('{0} has hit {1} points left.'.format(
                #         target.name.capitalize(), target.fighter.current_hp), libtcod.orange)})
            else:
                results.append({'message': Message('{0} attacks {1} but does no damage. ([{2} vs. {3}])'.format(
                    self.owner.name.capitalize(), target.name, attack_roll, defence_roll), libtcod.grey)})
        else:
            results.append({'message': Message('{0} attacks {1} and misses. ([{2} vs. {3}])'.format(
                self.owner.name.capitalize(), target.name, attack_roll, defence_roll), libtcod.grey)})

        return results
