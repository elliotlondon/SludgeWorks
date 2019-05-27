import tcod as libtcod
from random import randint
from game_messages import Message


class Aggressive:
    def take_turn(self, target, fov_map, game_map, entities):
        results = []

        if libtcod.map_is_in_fov(fov_map, self.owner.x, self.owner.y):
            if self.owner.distance_to(target) >= 2:
                self.owner.move_astar(target, entities, game_map)
            elif target.fighter.current_hp > 0:
                attack_results = self.owner.fighter.attack(target)
                results.extend(attack_results)

        return results


class AimlessWanderer:
    def take_turn(self, target, fov_map, game_map, entities):
        results = []

        if libtcod.map_is_in_fov(fov_map, self.owner.x, self.owner.y):
            if self.owner.distance_to(target) >= 2:
                self.owner.move_astar(target, entities, game_map)
            elif target.fighter.current_hp > 0:
                attack_results = self.owner.fighter.attack(target)
                results.extend(attack_results)
        else:
            self.owner.move_random(game_map)

        return results


class Stationary:
    # Monster which does not move, but attacks when enemies are in range
    def take_turn(self, target, fov_map, game_map, entities):
        results = []

        if libtcod.map_is_in_fov(fov_map, self.owner.x, self.owner.y):
            if (target.fighter.current_hp > 0) and (self.owner.distance_to(target) == 1):
                attack_results = self.owner.fighter.attack(target)
                results.extend(attack_results)

        return results


class PassiveStationary:
    # Monster which neither moves nor attacks
    def take_turn(self, target, fov_map, game_map, entities):
        results = []
        # Plants are friends :)
        return results


class ConfusedMonster:
    # Enemy which wanders around (able to attack) until the confusion has worn off
    def __init__(self, previous_ai, number_of_turns=10):
        self.previous_ai = previous_ai
        self.number_of_turns = number_of_turns

    def take_turn(self, target, fov_map, game_map, entities):
        results = []

        if self.number_of_turns > 0:
            random_x = self.owner.x + randint(0, 2) - 1
            random_y = self.owner.y + randint(0, 2) - 1

            if random_x != self.owner.x and random_y != self.owner.y:
                self.owner.move_towards(random_x, random_y, game_map, entities)

            self.number_of_turns -= 1

        else:
            self.owner.ai = self.previous_ai
            results.append({'message': Message('The {0} is no longer confused!'.format(self.owner.name), libtcod.red)})

        return results
