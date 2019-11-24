import tcod as libtcod
from random_utils import roll_dice, dnd_bonus_calc
from game_messages import Message
from math import floor


class Fighter:
    def __init__(self, current_hp, max_hp, damage_dice, damage_sides, strength, dexterity, vitality, intellect,
                 perception, armour, xp=0, level=1, dodges=False):
        self.base_max_hp = max_hp
        self.current_hp = current_hp
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
    def crit_damage(self):
        if self.owner and self.owner.equipment:
            damage = roll_dice(2*self.owner.equipment.damage_dice, self.owner.equipment.damage_sides)
        else:
            damage = roll_dice(2*self.damage_dice, self.damage_sides)

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
            bonus += self.owner.equipment.perception_bonus

        perception_bonus = dnd_bonus_calc(self.base_perception)

        return perception_bonus + bonus

    @property
    def armour_total(self):
        bonus = 0
        if self.owner and self.owner.equipment:
            bonus += self.owner.equipment.armour_bonus

        return self.base_armour + bonus

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
        damage = None
        crit = False
        crit_chance = 0.05   # Critical hit chance in %
        max_crit_chance = 0.25  # Define max chance to stop overflows!

        # Roll to see if hit
        attack_roll = roll_dice(1, 20) + self.dexterity_modifier
        if target.fighter.dodges:
            dodge_roll = roll_dice(1, 20) + target.fighter.dexterity_modifier
        else:
            dodge_roll = 0

        if attack_roll > dodge_roll:    # Attack hits
            # Calculate strength-weighted damage roll
            damage_roll = self.damage + self.strength_modifier
            if target.fighter.armour_total > 0:
                defence_roll = roll_dice(1, target.fighter.armour_total)
            else:
                defence_roll = 0

            # Check if entity penetrates target's armour
            penetration_int = abs(damage_roll - defence_roll)
            if (damage_roll - defence_roll) > 0:

                # Calculate modified (positive) crit chance
                while penetration_int > 0 and crit_chance <= max_crit_chance:
                    crit_chance += 0.01
                    penetration_int -= 1

                # Check if crit
                if roll_dice(1, floor(1/crit_chance)) == floor(1/crit_chance):
                    crit = True
                    damage = self.crit_damage - defence_roll
                else:
                    damage = self.damage - defence_roll

            # Crits can penetrate otherwise impervious armour!
            elif (damage_roll - defence_roll) <= 0:

                # Calculate modified (negative) crit chance
                while penetration_int > 0 and crit_chance > 0:
                    crit_chance -= 0.01
                    penetration_int -= 1

                # Check if crit
                if crit_chance <= 0:
                    damage = 0
                else:
                    if roll_dice(1, floor(1 / crit_chance)) == floor(1 / crit_chance):
                        crit = True
                        damage = self.crit_damage - defence_roll
                    else:
                        damage = 0

            # Check for damage and display chat messages
            if damage > 0:
                if crit:
                    results.append({'message': Message('{0} crits {1} for {2} damage.'.
                                                       format(self.owner.name.capitalize(), target.name,
                                                              str(damage)), libtcod.light_red)})
                    results.extend(target.fighter.take_damage(damage))
                else:
                    results.append({'message': Message('{0} attacks {1} for {2} damage.'.
                                    format(self.owner.name.capitalize(), target.name, str(damage)), libtcod.white)})
                    results.extend(target.fighter.take_damage(damage))
                # Debug to see enemy HP
                # if target.name == 'Risen Sacrifice':
                #     results.append({'message': Message('{0} has hit {1} points left.'.format(
                #         target.name.capitalize(), target.fighter.current_hp), libtcod.orange)})
            else:
                results.append({'message': Message('{0} attacks {1} but does no damage.'.
                                                   format(self.owner.name.capitalize(), target.name),
                                                   libtcod.grey)})
        else:
            results.append({'message': Message('{0} attacks {1} and misses. ([{2} vs. {3}])'.format(
                self.owner.name.capitalize(), target.name, attack_roll, dodge_roll), libtcod.grey)})

        return results
