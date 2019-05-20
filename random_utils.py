from random import randint
import numpy as np


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


def distance_to(start_x, start_y, target_x, target_y):
    distance_x = abs(target_x - start_x)
    distance_y = abs(target_y - start_y)
    return np.sqrt((distance_x**2 + distance_y**2))
