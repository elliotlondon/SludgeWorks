from typing import Optional
import random

import config.colour
import core.abilities
import core.abilities
import core.g
from parts.base_component import BaseComponent
from parts.entity import Actor


def select_mutation(player: Actor):
    """
    Function to be used to select a mutation to be given to a player when a mutating action occurs.
    As of right now, simply choose a mutation which the player does not have, and is valid
    For them to be given. TODO: More sophisticated mutation selection.
    """
    choices = ["Bite", "Bludgeon", "Immolate"]
    random.shuffle(choices)
    for choice in choices:
        if choice == "Bite":
            mutation = Bite(damage=1, turns=4, difficulty=12, cooldown=10)
        elif choice == "Bludgeon":
            mutation = Bludgeon(damage=2, sides=3, turns=1, difficulty=16, cooldown=16)
        elif choice == 'Immolate':
            mutation = Immolate(turns=3, cooldown=22)
        if check_existing(player, mutation.name):
            continue
        return mutation


def check_existing(entity: Actor, name: str) -> bool:
    """Check whether an entity already has a given mutation"""
    if len(entity.mutations) > 0:
        for existing in entity.mutations:
            if existing.name == name:
                return True
        return False
    else:
        return False


class Mutation(BaseComponent):
    """Effects which can be inherent or added, constant or continuous, which are assigned to an Actor
    and may be updated through effects, such as a level-up. Mutations can be thought of as abilities."""
    parent: Actor

    def __init__(self,
                 name: str = "<Undefined>",
                 message: str = "<Undefined>",
                 description: str = "<Undefined>",
                 req_target: bool = False,
                 continuous: bool = False,
                 cooldown: int = 0,
                 range: int = 0
                 ):
        self.name = name
        self.message = message
        self.description = description
        self.req_target = req_target
        self.continuous = continuous
        self.cooldown = cooldown
        self.range = range

    def __iter__(self):
        for x in self.__dict__:
            yield x

    def activate(self, *args):
        """Activate this ability."""
        raise NotImplementedError()

    def expiry_message(self):
        """Print a message to the log when the effect is removed."""
        raise NotImplementedError()

    def tick(self):
        """On the passing of a turn, apply this effect."""
        if self.cooldown > 0:
            self.cooldown -= 1


class Shove(Mutation):
    """Push a hostile entity away. Deals no damage.
    Entities can collide and suffer 1 point of damage (str roll, difficulty 8)"""
    parent: Actor

    def __init__(self):
        super().__init__(
            name="Shove",
            description="Attempt to push a creature away from you. "
                        "Can deal minor damage if the target collides with another enemy",
            req_target=True,
            continuous=False,
            cooldown=0,
            range=1
        )
        self.action = core.abilities.ShoveAction

    def activate(self, caster: Actor, target: Actor, x: int, y: int) -> Optional[core.abilities.ShoveAction]:
        if self.cooldown > 0 and self.parent.name == "Player":
            core.g.engine.message_log.add_message("You cannot perform this ability yet.", config.colour.impossible)
            return None
        else:
            self.cooldown = 6
            return core.abilities.ShoveAction(caster, target, x, y)


class Bite(Mutation):
    """Bite the target. Cannot be dodged but damage can be resisted. Can cause bleeding if vit check 12 fails."""
    parent: Actor

    def __init__(self, damage: int, turns: int, difficulty: int, cooldown: int):
        super().__init__(
            name="Bite",
            message="Your teeth grow into a set of wickedly sharp, animalistic fangs!",
            description="Bite a neaby creature. Deals 1d4, and can cause minor bleeding on hit.",
            req_target=True,
            continuous=False,
            cooldown=0,
            range=1
        )
        self.action = core.abilities.ShoveAction
        self.damage = damage
        self.turns = turns
        self.difficulty = difficulty
        self.cooldown_max = cooldown

    def activate(self, caster: Actor, target: Actor, x: int, y: int) -> \
            Optional[core.abilities.BiteAction]:
        if self.cooldown > 0 and self.parent.name == "Player":
            core.g.engine.message_log.add_message("You cannot perform this ability yet.", config.colour.impossible)
            return None
        else:
            self.cooldown = self.cooldown_max
            return core.abilities.BiteAction(caster, target, x, y, self.damage, self.turns, self.difficulty)


class Bludgeon(Mutation):
    """Brutally attack the target, stunning them if the attack lands successfully."""
    parent: Actor

    def __init__(self, damage: int, sides: int, turns: int, difficulty: int, cooldown: int):
        super().__init__(
            name="Bludgeon",
            description="Pummel a nearby creature, dealing 2d4 and stunning on a successful hit. Smash them!!!",
            req_target=True,
            continuous=False,
            cooldown=0,
            range=1
        )
        self.action = core.abilities.BludgeonAction
        self.damage = damage
        self.sides = sides
        self.turns = turns
        self.difficulty = difficulty
        self.cooldown_max = cooldown

    def activate(self, caster: Actor, target: Actor, x: int, y: int) -> \
            Optional[core.abilities.BludgeonAction]:
        if self.cooldown > 0 and self.parent.name == "Player":
            core.g.engine.message_log.add_message("You cannot perform this ability yet.", config.colour.impossible)
            return None
        else:
            self.cooldown = self.cooldown_max
            return core.abilities.BludgeonAction(caster, target, x, y, self.damage, self.sides,
                                                 self.turns, self.difficulty)


class MemoryWipe(Mutation):
    """Attack the target with a memory wiping mental attack."""
    parent: Actor

    def __init__(self, cooldown: int):
        super().__init__(
            name="Wipe Memory",
            description="Savagely attack the mind of a nearby creature, performing a mental attack and "
                        "wiping memories on crit.",
            req_target=True,
            continuous=False,
            cooldown=5,
            range=1
        )
        self.action = core.abilities.MemoryWipeAction
        self.cooldown_max = cooldown

    def activate(self, caster: Actor, target: Actor, x: int, y: int) -> \
            Optional[core.abilities.MemoryWipeAction]:
        if self.cooldown > 0 and self.parent.name == "Player":
            core.g.engine.message_log.add_message("You cannot perform this ability yet.", config.colour.impossible)
            return None
        else:
            self.cooldown = self.cooldown_max
            return core.abilities.MemoryWipeAction(caster, target, x, y)


class Immolate(Mutation):
    """Set a target on fire with your mind."""
    parent: Actor

    def __init__(self, cooldown: int, turns: int):
        super().__init__(
            name="Immolate",
            message='Images of dancing, white-gold flames rush through your mind...',
            description="Set an enemy on fire with the power of your mind!",
            req_target=True,
            continuous=False,
            cooldown=cooldown,
            range=8
        )
        self.action = core.abilities.ImmolateAction
        self.cooldown_max = cooldown
        self.turns = turns

    def activate(self, caster: Actor, target: Actor, x: int, y: int) -> \
            Optional[core.abilities.ImmolateAction]:
        if self.cooldown > 0 and self.parent.name == "Player":
            core.g.engine.message_log.add_message("You cannot perform this ability yet.", config.colour.impossible)
            return None
        else:
            self.cooldown = self.cooldown_max
            return core.abilities.ImmolateAction(caster, target, x, y, self.turns)


class MoireBeastHide(Mutation):
    """Dazzle an opponent, weakening them."""
    parent: Actor

    def __init__(self, cooldown: int, turns: int, difficulty: int):
        super().__init__(
            name="Dazzle",
            message='You gain the ability to emit brief but intense pulses of light from your skin!',
            description="Reduce the STR and DEX of an enemy by dazzling them with flashes of light.",
            req_target=True,
            continuous=False,
            cooldown=cooldown,
            range=1
        )
        self.action = core.abilities.MoireDazzleAction
        self.cooldown_max = cooldown
        self.turns = turns
        self.difficulty = difficulty

    def activate(self, caster: Actor, target: Actor, x: int, y: int) -> \
            Optional[core.abilities.MoireDazzleAction]:
        if self.cooldown > 0 and self.parent.name == "Player":
            core.g.engine.message_log.add_message("You cannot perform this ability yet.", config.colour.impossible)
            return None
        else:
            self.cooldown = self.cooldown_max
            return core.abilities.MoireDazzleAction(caster, target, x, y, self.turns)


class Wither(Mutation):
    """Enfeeble the opponent, causing a permanent max hp reduction that persists until it is removed from
    other sources, such as a sludge fountain, or rare enfeeble removal items."""
    parent: Actor

    def __init__(self, hp_reduction: int, cooldown: int):
        super().__init__(
            name="Wither",
            message='The world around you feels almost imperceptibly less corporeal, '
                    'like you are truly the only thing that is real...',
            description=f"Enfeeble an enemy, permanently reducing their max hp by {hp_reduction}. Does not stack.",
            req_target=True,
            continuous=False,
            cooldown=cooldown,
            range=1
        )
        self.action = core.abilities.WitherAction
        self.cooldown_max = cooldown
        self.hp_reduction = hp_reduction

    def activate(self, caster: Actor, target: Actor, x: int, y: int) -> \
            Optional[core.abilities.WitherAction]:
        if self.cooldown > 0 and self.parent.name == "Player":
            core.g.engine.message_log.add_message("You cannot perform this ability yet.", config.colour.impossible)
            return None
        else:
            self.cooldown = self.cooldown_max
            return core.abilities.WitherAction(caster, target, x, y, self.hp_reduction)


class Fear(Mutation):
    """Fear an entity at close range, causing them to flee for a given number of turns. Can be resisted with INT.
    Direct damage taken may break the effect"""
    parent: Actor

    def __init__(self, turns: int, difficulty: int, cooldown: int):
        super().__init__(
            name="Fear",
            message='You begin to comprehend primordial sensations that created this place. It is horrifying!',
            description=f"Inflict Fear upon an enemy near you, causing them to run from you for {turns}.",
            req_target=True,
            continuous=False,
            cooldown=cooldown,
            range=1
        )
        self.action = core.abilities.WitherAction
        self.cooldown_max = cooldown
        self.turns = turns
        self.difficulty = difficulty

    def activate(self, caster: Actor, target: Actor, x: int, y: int) -> \
            Optional[core.abilities.WitherAction]:
        if self.cooldown > 0 and self.parent.name == "Player":
            core.g.engine.message_log.add_message("You cannot perform this ability yet.", config.colour.impossible)
            return None
        else:
            self.cooldown = self.cooldown_max
            return core.abilities.FearAction(caster, target, x, y, self.turns, self.difficulty)
