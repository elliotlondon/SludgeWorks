import tcod as libtcod
from fighter import Fighter
from ai import *
from entity import Entity
from render_functions import RenderOrder


def whip_vine(x, y):
    # Whip Vine
    fighter_component = Fighter(current_hp=8, max_hp=8, damage_dice=1, damage_sides=2,
                                strength=3, agility=1, vitality=1, intellect=1, perception=1, xp=25)
    ai_component = Stationary()
    return Entity(x, y, 'V', libtcod.light_grey, 'Whip Vine',
                  'What at first appears to be no more than a dead, waist-height bush in actuality '
                  'represents a highly specialized carnivorous plant that flays the skin off any creature '
                  'that wanders into its path.',
                  blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component,
                  faction='Plants')


def wretch(x, y):
    fighter_component = Fighter(current_hp=6, max_hp=6, damage_dice=1, damage_sides=3,
                                strength=3, agility=0, vitality=1, intellect=1, perception=1, xp=50)
    ai_component = Aggressive()
    return Entity(x, y, 'w', libtcod.darker_red, 'Wretch',
                  'A stunted human swaddled in filthy rags and long since driven feral by the SludgeWorks.',
                  blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component, ai=ai_component,
                  faction='Scavengers')


def hunchback(x, y):
    fighter_component = Fighter(current_hp=12, max_hp=12, damage_dice=1, damage_sides=12,
                                strength=4, agility=0, vitality=1, intellect=1, perception=1, xp=125)
    ai_component = Aggressive()
    return Entity(x, y, 'H', libtcod.brass, 'Hunchback',
                  'A stunted and broken humanoid draped in tattered linen stained with the characteristic ochre'
                  'of dried blood. It\'s face is completely concealed by a tapered hood, and the glint of a wicked '
                  'kirpan scatters the all nearby light. Echoes of guttural chanting reverberate off the cave '
                  'walls as it glacially stumbles forward towards its next target.',
                  blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component,
                  ai=ai_component, faction='Horrors')


def moire_beast(x, y):
    fighter_component = Fighter(current_hp=18, max_hp=18, damage_dice=3, damage_sides=3,
                                strength=3, agility=8, vitality=1, intellect=1, perception=1, xp=325)
    ai_component = Aggressive()
    return Entity(x, y, 'M', libtcod.light_grey, 'Moire Beast',
                  'The hide of this squat quadruped is an affront to the senses; dense and intricate greyscale '
                  'patterns constantly shift epileptically upon the beast\'s surface like a zebra beyond all '
                  'imagination. The gleam of it\'s fluorescent yellow, feline irises serve as the only ubiquitous '
                  'reference point on this monster\'s migraine-inducing form.',
                  blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component,
                  ai=ai_component, faction='Scavengers')


def thresher(x, y):
        fighter_component = Fighter(current_hp=26, max_hp=26, damage_dice=3, damage_sides=4,
                                    strength=5, agility=4, vitality=1, intellect=1, perception=1, xp=225)
        ai_component = Aggressive()
        return Entity(x, y, 'T', libtcod.dark_azure, 'Thresher',
                      'A colossal ogre-like ape covered in patches of matted hair and littered with scars. This '
                      'creature tirelessly searches it\'s surroundings for new objects to smash together with a '
                      'joyous, childlike expression.',
                      blocks=True, fighter=fighter_component, render_order=RenderOrder.ACTOR, ai=ai_component,
                      faction='Scavengers')


def bloodseeker(x, y):
    fighter_component = Fighter(current_hp=50, max_hp=50, damage_dice=4, damage_sides=6,
                                strength=6, agility=3, vitality=1, intellect=1, perception=1, xp=500)
    ai_component = Aggressive()
    return Entity(x, y, 'B', libtcod.light_crimson, 'Bloodseeker',
                  'An asymmetric monstrosity the size of a bear with a grinning, skinless snout. Rusted weaponry from '
                  'previous encounters juts from it\'s hide like gruesome jewellery, with pale, twisted flesh creeping '
                  'up the hilts. The creature\'s eyes are consumed by feral rage as it prowls the caverns, twitching '
                  'from the eternal	state of pain inflicted by its inherent regeneration.',
                  blocks=True, render_order=RenderOrder.ACTOR, fighter=fighter_component,
                  ai=ai_component, faction='Scavengers')
