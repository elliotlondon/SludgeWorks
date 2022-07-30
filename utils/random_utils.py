from logging import getLogger, DEBUG
from math import floor
from random import randint, choice, Random

import numpy as np

# Initialize random number generator
Random(1337)


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


def random_choice_from_list(list):
    return choice(list)


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
    bonus = floor((value - 10) / 2)

    return bonus


def is_debug():
    return getLogger("my_logger").getEffectiveLevel() == DEBUG


def rotate_array(array: np.ndarray([])) -> [int, np.ndarray([])]:
    """Randomly rotate an array 90, 180, 270 or 360 degrees."""
    angle = 0
    rot_int = randint(0, 3)
    if rot_int == 0:
        array = np.rot90(array, 1)
    elif rot_int == 1:
        array = np.rot90(array, 2)
    elif rot_int == 2:
        array = np.rot90(array, 3)

    return angle, array
