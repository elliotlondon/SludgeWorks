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


def simple_distance(start_x, start_y, final_x, final_y):
    # A function that returns the distance between two points on a grid, weighting diagonals equally
    distance_x = abs(final_x - start_x)
    distance_y = abs(final_y - start_y)
    return distance_x + distance_y
