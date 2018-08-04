import libtcodpy as libtcod

from entity import Entity
from game_messages import Message
from game_states import GameStates
from render_functions import RenderOrder


def kill_player(player):
    player.char = '%'
    player.colour = libtcod.dark_red

    return Message('You did not survive.', libtcod.red), GameStates.PLAYER_DEAD


def kill_monster(monster, entities):
    death_message = Message('The {0} dies!'.format(monster.name.capitalize()), libtcod.orange)

    monster.blocks = False
    monster.fighter = None
    monster.ai = None
    monster.char = ' '

    # Generate a corpse as an item
    if monster.name[0].lower() in 'aeiou':
        monster.corpse_name = 'An ' + monster.name + ' corpse'
    else:
        monster.corpse_name = 'A ' + monster.name + ' corpse'
    item_component = ()
    item = Entity(monster.x, monster.y, '%', libtcod.dark_red, monster.corpse_name,
                  'The remains of a vanquished inhabitant of these caverns.',
                  render_order=RenderOrder.ITEM, item=item_component)

    entities.remove(monster)
    entities.append(item)

    monster.render_order = RenderOrder.CORPSE

    return death_message
