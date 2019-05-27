from random import randint
from math import floor


def from_dungeon_level(table, dungeon_level):
    for (value, level) in reversed(table):
        if dungeon_level >= level:
            return value

    return 0


def random_choice_index(chances):
    random_chance = randint(1, sum(chances))

    running_sum = 0
    choice = 0
    for w in chances:
        running_sum += w

        if random_chance <= running_sum:
            return choice
        choice += 1


def random_choice_from_dict(choice_dict):
    choices = list(choice_dict.keys())
    chances = list(choice_dict.values())

    return choices[random_choice_index(chances)]


def roll_dice(num, dice):  # rolls dice, returns the sum of all rolls
    roll = 0
    for x in range(0, num):
        n = randint(1, dice)
        roll = roll + n

    return roll


def dnd_bonus_calc(value):
    bonus = floor((value - 10)/2)

    return bonus
