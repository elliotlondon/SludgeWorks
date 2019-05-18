import tcod as libtcod

from entity import Entity
from game_messages import Message
from game_states import GameStates
from render_functions import RenderOrder


def kill_player(player):
    player.char = '%'
    player.colour = libtcod.white

    return Message('YOU DIED', libtcod.red), GameStates.PLAYER_DEAD


def kill_monster(monster, entities):
    monster.blocks = False
    monster.fighter = None
    monster.char = ' '
    # Death condition for plant enemies
    if monster.faction == 'Plants':
        death_message = Message('The {0} dies!'.format(monster.name.capitalize()), libtcod.orange)
        monster.ai = None
    else:
        death_message = Message('The {0} dies!'.format(monster.name.capitalize()), libtcod.orange)
        monster.ai = None

        # Generate a corpse as an item
        if monster.name[0].lower() in 'aeiou':
            monster.corpse_name = 'An ' + monster.name + ' corpse'
        else:
            monster.corpse_name = 'A ' + monster.name + ' corpse'
        item_component = ()
        item = Entity(monster.x, monster.y, '%', libtcod.dark_red, monster.corpse_name,
                      'The grotesque remains of an unfortunate inhabitant of the SludgeWorks.',
                      render_order=RenderOrder.ITEM, item=item_component)
        entities.append(item)

    monster.render_order = RenderOrder.CORPSE
    entities.remove(monster)

    return death_message
