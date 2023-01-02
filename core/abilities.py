from typing import Optional

import random
import numpy as np

import config.colour
import core.actions
import core.g
import parts.ai
import parts.effects
import parts.mutations
from core.action import AbilityAction
from parts.entity import Actor
from utils.random_utils import roll_dice


class ShoveAction(AbilityAction):
    """Spend a turn to push an enemy away from you. Has no effect if a wall is behind the enemy."""

    def __init__(self, caster: Actor, target: Actor, x: int, y: int):
        super().__init__(
            entity=caster,
            target=target,
            x=x,
            y=y
        )

    def perform(self) -> Optional[Exception]:
        # Work out new entity postition
        dx = self.target.x - self.caster.x
        dy = self.target.y - self.caster.y

        # First check for selection errors
        if dx == 0 and dy == 0:
            core.g.engine.message_log.add_message("You cannot perform this action upon yourself.",
                                                  config.colour.impossible)
            return None
        if isinstance(self.target.ai, parts.ai.PassiveStationary) or \
                isinstance(self.target.ai, parts.ai.HostileStationary):
            core.g.engine.message_log.add_message("That target cannot be moved.",
                                                  config.colour.impossible)
            return None

        # Check if another entity is at the destination, don't attack, but deal damage to one or both
        extra_target = core.g.engine.game_map.get_blocking_entity_at_location(self.target.x + dx, self.target.y + dy)
        if extra_target:
            core.g.engine.message_log.add_message(f"You push the {self.target.name} and "
                                                  f"it collides with the {extra_target.name}!",
                                                  config.colour.ability_used)
            if roll_dice(1, 20) + self.target.fighter.strength_modifier > 8:
                if self.target.fighter.hp > 1:
                    core.g.engine.message_log.add_message(f"The {self.target.name} takes 1 damage from the collision.",
                                                          config.colour.enemy_atk)
                    self.target.fighter.hp -= 1
            if roll_dice(1, 20) + extra_target.fighter.strength_modifier > 8:
                if extra_target.fighter.hp > 1:
                    core.g.engine.message_log.add_message(f"The {extra_target.name} takes 1 damage from the collision.",
                                                          config.colour.enemy_atk)
                    extra_target.fighter.hp -= 1
            return None

        # Check if new coords hit a wall or are oob
        if self.target.x + dx >= core.g.console.width or self.target.y + dy >= core.g.console.height or \
                self.target.x + dx <= 0 or self.target.y + dy <= 0:
            core.g.engine.message_log.add_message("The target cannot be pushed into the destination",
                                                  config.colour.impossible)
            return None
        elif not core.g.engine.game_map.tiles['walkable'][self.target.x + dx, self.target.y + dy]:
            core.g.engine.message_log.add_message(f"You push the {self.target.name}, but it has no space to move away.",
                                                  config.colour.enemy_evade)
            return None
        else:
            # Calculate if push lands successfully
            attack_roll = roll_dice(1, 20) + self.caster.fighter.strength_modifier
            defend_roll = roll_dice(1, 20) + self.target.fighter.strength_modifier
            if attack_roll > defend_roll:
                core.g.engine.message_log.add_message(f"You push the {self.target.name} and it stumbles backwards!",
                                                      config.colour.ability_used)
                return core.actions.BumpAction(self.target, dx, dy).perform()
            else:
                core.g.engine.message_log.add_message(f"The {self.target.name} resists your shove!",
                                                      config.colour.enemy_evade)
                return None

        core.g.engine.message_log.add_message("This action would have no effect.", config.colour.impossible)
        return None


class BiteAction(AbilityAction):
    """Attack an enemy, dealing 1d4 and causing bleeding if a vit 12 roll fails."""

    def __init__(self, caster: Actor, target: Actor, x: int, y: int, damage: int, turns: int, difficulty: 12):
        super().__init__(
            entity=caster,
            target=target,
            x=x,
            y=y,
        )
        self.damage = damage
        self.turns = turns
        self.difficulty = difficulty

    def perform(self) -> Optional[Exception]:
        attacker = self.caster
        defender = self.target

        crit_chance = 0.10  # Critical hit chance in %
        max_crit_chance = 0.33  # Define max chance to stop overflows!

        damage = None
        crit = False

        # Check if target is already bleeding, or has a stronger bleed already active
        bleeding = False
        for effect in defender.active_effects:
            if isinstance(effect, parts.effects.BleedEffect):
                if effect.damage > self.damage:
                    bleeding = True

        # Calculate strength-weighted damage roll
        damage_roll = attacker.fighter.damage + attacker.fighter.strength_modifier
        if defender.fighter.armour_total > 0:
            defence_roll = roll_dice(1, defender.fighter.armour_total)
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
            if roll_dice(1, np.floor(1 / crit_chance)) == np.floor(1 / crit_chance):
                crit = True
                damage = attacker.fighter.crit_damage - defence_roll
            else:
                damage = attacker.fighter.damage - defence_roll

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
                if roll_dice(1, np.floor(1 / crit_chance)) == np.floor(1 / crit_chance):
                    crit = True
                    damage = attacker.fighter.crit_damage - defence_roll
                else:
                    damage = 0

        # Check for damage and display chat messages
        if damage > 0:
            if crit:
                if defender.blood == "Blood":
                    core.g.engine.game_map.splatter_tiles(defender.x, defender.y,
                                                          light_fg=config.colour.blood, modifiers="Bloody")
                # Always bleed on crit.
                if not bleeding:
                    effect = parts.effects.BleedEffect(self.damage, self.turns, self.difficulty)
                    effect.parent = defender
                    defender.active_effects.append(effect)

                if defender.name.capitalize() == 'Player':
                    core.g.engine.message_log.add_message(f'The {attacker.name} critically bites you for '
                                                          f'{str(damage)} damage!', config.colour.ability_used)
                    core.g.engine.message_log.add_message(f'You start bleeding!',
                                                          config.colour.bleed)
                elif attacker.name.capitalize() == 'Player':
                    core.g.engine.message_log.add_message(f'You critically bite the {defender.name} for '
                                                          f'{str(damage)} damage!', config.colour.ability_used)
                    core.g.engine.message_log.add_message(f'The {defender.name} starts bleeding!',
                                                          config.colour.bleed)
                else:
                    core.g.engine.message_log.add_message(f'The {attacker.name} critically bites the {defender.name} '
                                                          f'for {str(damage)} damage!', config.colour.enemy_crit)
                    core.g.engine.message_log.add_message(f"The {defender.name.capitalize()} starts bleeding!",
                                                          config.colour.enemy_crit)
            else:
                if not bleeding:
                    if roll_dice(1, 20) + defender.fighter.vitality_modifier < self.difficulty:
                        effect = parts.effects.BleedEffect(self.damage, self.turns, self.difficulty)
                        effect.parent = defender
                        defender.active_effects.append(effect)
                        bleeding = True
                if defender.name.capitalize() == 'Player':
                    core.g.engine.message_log.add_message(f'The {attacker.name} bites you for '
                                                          f'{str(damage)} damage.', config.colour.ability_used)
                    if bleeding:
                        core.g.engine.message_log.add_message(f'You start bleeding!', config.colour.bleed)
                elif attacker.name.capitalize() == 'Player':
                    core.g.engine.message_log.add_message(f'You bite the {defender.name} for '
                                                          f'{str(damage)} damage.', config.colour.ability_used)
                else:
                    core.g.engine.message_log.add_message(f'The {attacker.name} bites the {defender.name} '
                                                          f'for {str(damage)} damage.', config.colour.enemy_atk)
                if bleeding:
                    core.g.engine.message_log.add_message(f'The {defender.name} starts bleeding!',
                                                          config.colour.ability_used)
            defender.fighter.hp -= damage
        else:
            if defender.name.capitalize() == 'Player':
                core.g.engine.message_log.add_message(f'The {attacker.name} bites you '
                                                      f'but does no damage.', config.colour.player_evade)
            elif attacker.name.capitalize() == 'Player':
                core.g.engine.message_log.add_message(f'You bite the {defender.name} '
                                                      f'but do no damage.', config.colour.player_evade)
            else:
                core.g.engine.message_log.add_message(f'The {attacker.name} bites the {defender.name}, '
                                                      f'but does no damage.', config.colour.enemy_evade)

        return None


class BludgeonAction(AbilityAction):
    """Bludgeon an enemy, dealing XdY and stunning if a vit 16 roll fails."""

    def __init__(self, caster: Actor, target: Actor, x: int, y: int, damage: int, sides: int,
                 turns: int, difficulty: 16):
        super().__init__(
            entity=caster,
            target=target,
            x=x,
            y=y,
        )
        self.damage = damage
        self.sides = sides
        self.turns = turns
        self.difficulty = difficulty

    def perform(self) -> Optional[Exception]:
        attacker = self.caster
        defender = self.target

        crit_chance = 0.10  # Critical hit chance in %
        max_crit_chance = 0.33  # Define max chance to stop overflows!

        damage = None
        crit = False

        # Check if target is already stunned, or has stun immunity
        immune = False
        for effect in defender.active_effects:
            if isinstance(effect, parts.effects.StunEffect) or isinstance(effect, parts.effects.SecondWindEffect):
                immune = True

        # Calculate strength-weighted damage roll
        damage_roll = attacker.fighter.damage + attacker.fighter.strength_modifier
        if defender.fighter.armour_total > 0:
            defence_roll = roll_dice(1, defender.fighter.armour_total)
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
            if roll_dice(1, np.floor(1 / crit_chance)) == np.floor(1 / crit_chance):
                crit = True
                damage = attacker.fighter.crit_damage - defence_roll
            else:
                damage = attacker.fighter.damage - defence_roll

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
                if roll_dice(1, np.floor(1 / crit_chance)) == np.floor(1 / crit_chance):
                    crit = True
                    damage = attacker.fighter.crit_damage - defence_roll
                else:
                    damage = 0

        # Check for damage and display chat messages
        stunned = False
        if damage > 0:
            if crit:
                if defender.blood == "Blood":
                    core.g.engine.game_map.splatter_tiles(defender.x, defender.y,
                                                          light_fg=config.colour.blood, modifiers="Bloody")
                # Always stun on crit.
                if not immune:
                    effect = parts.effects.StunEffect(self.turns)
                    effect.parent = defender
                    defender.active_effects.append(effect)
                if defender.name.capitalize() == 'Player':
                    core.g.engine.message_log.add_message(f'The {attacker.name} brutally bludgeons you for '
                                                          f'{str(damage)} damage!', config.colour.ability_used)
                    core.g.engine.message_log.add_message(f'You are stunned!',
                                                          config.colour.stun)
                elif attacker.name.capitalize() == 'Player':
                    core.g.engine.message_log.add_message(f'You brutally bludgeon the {defender.name} for '
                                                          f'{str(damage)} damage!', config.colour.ability_used)
                    core.g.engine.message_log.add_message(f'The {defender.name} is stunned!',
                                                          config.colour.stun)
                else:
                    core.g.engine.message_log.add_message(f'The {attacker.name} brutally bludgeons the {defender.name} '
                                                          f'for {str(damage)} damage!', config.colour.enemy_crit)
                    core.g.engine.message_log.add_message(f"The {defender.name.capitalize()} is stunned!",
                                                          config.colour.enemy_crit)
            else:
                if not immune:
                    if roll_dice(1, 20) + defender.fighter.vitality_modifier < self.difficulty:
                        effect = parts.effects.StunEffect(self.turns)
                        effect.parent = defender
                        defender.active_effects.append(effect)
                        stunned = True
                if defender.name.capitalize() == 'Player':
                    core.g.engine.message_log.add_message(f'The {attacker.name} bludgeons you for '
                                                          f'{str(damage)} damage!', config.colour.ability_used)
                    if stunned:
                        core.g.engine.message_log.add_message(f'You are stunned from the blow!', config.colour.stun)
                elif attacker.name.capitalize() == 'Player':
                    core.g.engine.message_log.add_message(f'You bludgeon the {defender.name} for '
                                                          f'{str(damage)} damage!', config.colour.ability_used)
                    if stunned:
                        core.g.engine.message_log.add_message(f'The {defender.name} is stunned!',
                                                              config.colour.stun)
                else:
                    core.g.engine.message_log.add_message(f'The {attacker.name} bludgeons the {defender.name} '
                                                          f'for {str(damage)} damage.', config.colour.enemy_atk)
            defender.fighter.hp -= damage
        else:
            if defender.name.capitalize() == 'Player':
                core.g.engine.message_log.add_message(f'The {attacker.name} bludgeons you '
                                                      f'but does no damage.', config.colour.player_evade)
            if attacker.name.capitalize() == 'Player':
                core.g.engine.message_log.add_message(f'You bludgeon the {defender.name}, '
                                                      f'but do no damage.', config.colour.player_evade)
            else:
                core.g.engine.message_log.add_message(f'The {attacker.name} bludgeons the {defender.name}, '
                                                      f'but does no damage.', config.colour.enemy_evade)

        return None


class MemoryWipeAction(AbilityAction):
    """Attack an enemy, dealing 2d3 and randomly wiping known tiles if a will 14 roll fails."""

    def __init__(self, caster: Actor, target: Actor, x: int, y: int):
        super().__init__(
            entity=caster,
            target=target,
            x=x,
            y=y,
        )

    def perform(self) -> Optional[Exception]:
        attacker = self.caster
        defender = self.target

        crit_chance = 0.10  # Critical hit chance in %
        max_crit_chance = 0.33  # Define max chance to stop overflows!

        # Roll to see if hit. Mental attack so rolls off INT
        attack_roll = roll_dice(1, 20) + attacker.fighter.dexterity_modifier
        if defender.fighter.dodges:
            dodge_roll = roll_dice(1, 20) + defender.fighter.intellect_modifier
        else:
            dodge_roll = 0

        damage = None
        crit = False
        if attack_roll > dodge_roll:  # Attack hits
            # Calculate strength-weighted damage roll. Ignores armour as mental attack
            damage_roll = attacker.fighter.damage + attacker.fighter.strength_modifier

            # Calculate mental armour
            defence_roll = roll_dice(1, defender.fighter.intellect_modifier)

            # Check if entity penetrates target's armour
            penetration_int = abs(damage_roll - defence_roll)
            if (damage_roll - defence_roll) > 0:
                # Calculate modified (positive) crit chance
                while penetration_int > 0 and crit_chance <= max_crit_chance:
                    crit_chance += 0.01
                    penetration_int -= 1
                # Check if crit
                if roll_dice(1, np.floor(1 / crit_chance)) == np.floor(1 / crit_chance):
                    crit = True
                    # For mindrakers crits do not do double damage, they do small extra damage and an effect
                    damage = attacker.fighter.damage + 2 - defence_roll
                else:
                    damage = attacker.fighter.damage - defence_roll

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
                    if roll_dice(1, np.floor(1 / crit_chance)) == np.floor(1 / crit_chance):
                        crit = True
                        damage = attacker.fighter.crit_damage - defence_roll
                    else:
                        damage = 0

            # Ability used notification
            if not attacker.name == "Player":
                core.g.engine.message_log.add_message(f'The {attacker.name} lunges at the skull!',
                                                      config.colour.ability_used)

            # Check for damage and display chat messages
            if damage > 0:
                if crit:
                    if defender.name.capitalize() == 'Player':
                        core.g.engine.message_log.add_message(f'The {attacker.name} crits you for '
                                                              f'{str(damage)} damage!', config.colour.enemy_crit)
                        core.g.engine.message_log.add_message(f'* Your brain hurts and you feel nauseous! Augh! *',
                                                              config.colour.red)
                    else:
                        core.g.engine.message_log.add_message(f'The {attacker.name} crits the {defender.name} for '
                                                              f'{str(damage)} damage!', config.colour.enemy_crit)
                else:
                    if defender.name.capitalize() == 'Player':
                        core.g.engine.message_log.add_message(f'The {attacker.name} attacks you for '
                                                              f'{str(damage)} damage.', config.colour.enemy_atk)
                        core.g.engine.message_log.add_message(f'* Your brain hurts and you feel nauseous! Augh! *',
                                                              config.colour.red)
                    else:
                        core.g.engine.message_log.add_message(f'The {attacker.name} attacks the {defender.name} '
                                                              f'{str(damage)} damage.', config.colour.enemy_atk)
                defender.fighter.hp -= damage
            else:
                if defender.name.capitalize() == 'Player':
                    core.g.engine.message_log.add_message(f'The {attacker.name} attacks you '
                                                          f'but does no damage!', config.colour.player_evade)
                else:
                    core.g.engine.message_log.add_message(f'The {attacker.name} attacks the {defender.name} '
                                                          f'but does no damage.', config.colour.enemy_evade)

            # Remove random tiles from explored tiles!
            explored_nonfov = np.logical_xor(self.entity.gamemap.explored, self.entity.gamemap.visible)
            num_explored = np.count_nonzero(explored_nonfov)

            if not num_explored <= len(self.entity.gamemap.visible):
                to_remove = round(num_explored / 4)
                while to_remove > 0:
                    x = random.choice(np.where(explored_nonfov == True)[0])
                    y = random.choice(np.where(explored_nonfov == True)[1])
                    self.entity.gamemap.explored[x, y] = False
                    to_remove -= 1
        else:
            if defender.name.capitalize() == 'Player':
                core.g.engine.message_log.add_message(f'You evade the {attacker.name.capitalize()}\'s attack.',
                                                      config.colour.player_evade)
            else:
                core.g.engine.message_log.add_message(f'The {attacker.name} attacks the {defender.name} '
                                                      f'but the attack is evaded.', config.colour.enemy_evade)

        return None


class MoireDazzleAction(AbilityAction):
    """Dazzle an enemy for 20 turns, reducing their str and dex. Stackable debuff."""

    def __init__(self, caster: Actor, target: Actor, x: int, y: int, difficulty: int):
        super().__init__(
            entity=caster,
            target=target,
            x=x,
            y=y
        )
        self.difficulty = difficulty

    def perform(self) -> Optional[Exception]:
        attacker = self.caster
        defender = self.target

        # See if the defender resists the attack. Always resisted if defender has visual shielding.
        if roll_dice(1, 20) + defender.fighter.vitality_modifier > self.difficulty:
            core.g.engine.message_log.add_message(f'The hide of the {attacker.name} flashes rhythmically...',
                                                  config.colour.ability_used)
            core.g.engine.message_log.add_message(f'But you manage to resist the dazzling effect!',
                                                  config.colour.warning)

        if defender.name.capitalize() == 'Player':
            core.g.engine.message_log.add_message(f'The hide of the {attacker.name} flashes rhythmically...',
                                                  config.colour.ability_used)
            core.g.engine.message_log.add_message(f'The strobes are sickening! You feel slow and weak!',
                                                  config.colour.warning)
            effect = parts.effects.DazzleEffect(turns=10, difficulty=self.difficulty, parent=self.target)
            effect.parent = defender
            defender.active_effects.append(effect)

        return None


class ImmolateAction(AbilityAction):
    """Meantally attack an enemy, setting them on fire on a successful hit. If the target is already on fire,
    increase the number of turns on fire by the turns of this effect."""

    def __init__(self, caster: Actor, target: Actor, x: int, y: int, turns: int):
        super().__init__(
            entity=caster,
            target=target,
            x=x,
            y=y,
        )
        self.turns = turns

    def perform(self) -> Optional[Exception]:
        attacker = self.caster
        defender = self.target

        # Check if target is already on fire
        on_fire = False
        existing_burn = None
        for effect in defender.active_effects:
            if isinstance(effect, parts.effects.BurningEffect):
                existing_burn = effect
                on_fire = True

        # Calculate mental armour and attacker chance
        attack_roll = roll_dice(1, 20) + attacker.fighter.intellect_modifier
        # Consider that enemies may be stupid enough to have negative modifiers
        if defender.fighter.intellect_modifier > 0:
            defence_roll = roll_dice(1, defender.fighter.intellect_modifier)
        else:
            defence_roll = 0

        if attack_roll > defence_roll:
            if not on_fire:
                effect = parts.effects.BurningEffect(self.turns)
                effect.parent = defender
                defender.active_effects.append(effect)
                if not isinstance(defender.ai, parts.ai.PassiveStationary) or \
                        isinstance(defender.ai, parts.ai.HostileStationary):
                    defender.ai = parts.ai.BurningEnemy(entity=defender, previous_ai=defender.ai)
                if defender.name.capitalize() == 'Player':
                    core.g.engine.message_log.add_message(f'The {attacker.name} sets you on fire with '
                                                          f'the power of their mind!', config.colour.ability_used)
                elif attacker.name.capitalize() == 'Player':
                    core.g.engine.message_log.add_message(f'You set the {defender.name} on fire with '
                                                          f'the power of your mind!', config.colour.ability_used)
                else:
                    core.g.engine.message_log.add_message(f'The {attacker.name} sets the {defender.name} on fire with '
                                                          f'the power of their mind!', config.colour.enemy_atk)
            else:
                existing_burn.turns += self.turns
                if defender.name.capitalize() == 'Player':
                    core.g.engine.message_log.add_message(f'The {attacker.name} stokes the flames on your body!',
                                                          config.colour.player_evade)
                elif attacker.name.capitalize() == 'Player':
                    core.g.engine.message_log.add_message(f'You stoke the flames on the {defender.name}! ',
                                                          config.colour.ability_used)
                else:
                    core.g.engine.message_log.add_message(f'The {attacker.name} stokes the flames on the '
                                                          f'{defender.name}!', config.colour.enemy_evade)

        return None
