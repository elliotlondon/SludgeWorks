import libtcodpy as libtcod

from random import randint


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


def roll_for(list):
    roll_total = 0

    # For i in range of the list's first value (which should be the number of dice)
    for i in range(0, list[0], 1):
        # Roll for a number between 1 and the second value (which should be the sides)
        roll_total += libtcod.random_get_int(0, 1, list[1])

    return roll_total
